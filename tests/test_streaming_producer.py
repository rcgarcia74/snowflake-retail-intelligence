from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[1]
PRODUCER_PATH = ROOT / "streaming/producer/produce.py"


def load_producer():
    spec = importlib.util.spec_from_file_location("streaming_producer", PRODUCER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_streams(input_dir: Path, row_count: int = 5) -> None:
    input_dir.mkdir()
    for stream in ("store_sales_events.jsonl", "store_inventory_events.jsonl"):
        rows = [
            {
                "event_id": f"event-{offset}",
                "event_ts": f"2026-01-{offset:02d}T12:00:00",
            }
            for offset in range(1, row_count + 1)
        ]
        (input_dir / stream).write_text(
            "".join(json.dumps(row) + "\n" for row in rows),
            encoding="utf-8",
        )


def install_streaming_sdk(monkeypatch, client_factory) -> None:
    snowflake = types.ModuleType("snowflake")
    ingest = types.ModuleType("snowflake.ingest")
    streaming = types.ModuleType("snowflake.ingest.streaming")
    streaming.StreamingIngestClient = client_factory

    monkeypatch.setitem(sys.modules, "snowflake", snowflake)
    monkeypatch.setitem(sys.modules, "snowflake.ingest", ingest)
    monkeypatch.setitem(sys.modules, "snowflake.ingest.streaming", streaming)


def test_parse_offset_contract() -> None:
    producer = load_producer()

    assert producer.parse_offset(None) == 0
    assert producer.parse_offset("0") == 0
    assert producer.parse_offset("2500") == 2500

    with pytest.raises(RuntimeError, match="expected numeric"):
        producer.parse_offset("not-a-number")

    with pytest.raises(RuntimeError, match="expected non-negative"):
        producer.parse_offset("-1")


def test_resume_skips_committed_rows(monkeypatch, tmp_path: Path) -> None:
    producer = load_producer()
    input_dir = tmp_path / "streaming"
    write_streams(input_dir)

    channels = []
    clients = []

    def client_factory(**_kwargs):
        channel = MagicMock()
        channel.wait_for_commit.side_effect = lambda predicate, **_kwargs: predicate("5")
        channels.append(channel)

        client = MagicMock()
        client.open_channel.return_value = (
            channel,
            SimpleNamespace(latest_committed_offset_token="3"),
        )
        clients.append(client)
        return client

    install_streaming_sdk(monkeypatch, client_factory)

    assert producer.publish(input_dir, tmp_path / "profile.json", 0, None) == 0

    for channel in channels:
        assert [call.args[1] for call in channel.append_row.call_args_list] == ["4", "5"]
    assert [client.open_channel.call_args.args for client in clients] == [
        ("MDI_SALES_CHANNEL",),
        ("MDI_INVENTORY_CHANNEL",),
    ]


def test_fully_committed_restart_is_noop(monkeypatch, tmp_path: Path) -> None:
    producer = load_producer()
    input_dir = tmp_path / "streaming"
    write_streams(input_dir)

    channels = []

    def client_factory(**_kwargs):
        channel = MagicMock()
        channels.append(channel)

        client = MagicMock()
        client.open_channel.return_value = (
            channel,
            SimpleNamespace(latest_committed_offset_token="5"),
        )
        return client

    install_streaming_sdk(monkeypatch, client_factory)

    assert producer.publish(input_dir, tmp_path / "profile.json", 0, None) == 0

    for channel in channels:
        channel.append_row.assert_not_called()
        channel.wait_for_commit.assert_not_called()


def test_through_date_stops_at_chronological_prefix(monkeypatch, tmp_path: Path) -> None:
    producer = load_producer()
    input_dir = tmp_path / "streaming"
    write_streams(input_dir)

    channels = []

    def client_factory(**_kwargs):
        channel = MagicMock()
        channel.wait_for_commit.side_effect = lambda predicate, **_kwargs: predicate("3")
        channels.append(channel)

        client = MagicMock()
        client.open_channel.return_value = (
            channel,
            SimpleNamespace(latest_committed_offset_token=None),
        )
        return client

    install_streaming_sdk(monkeypatch, client_factory)

    assert producer.publish(input_dir, tmp_path / "profile.json", 0, "2026-01-03") == 0

    for channel in channels:
        assert [call.args[1] for call in channel.append_row.call_args_list] == ["1", "2", "3"]


def test_resources_close_when_append_fails(monkeypatch, tmp_path: Path) -> None:
    producer = load_producer()
    input_dir = tmp_path / "streaming"
    write_streams(input_dir)

    channel = MagicMock()
    channel.append_row.side_effect = RuntimeError("append failed")

    client = MagicMock()
    client.open_channel.return_value = (
        channel,
        SimpleNamespace(latest_committed_offset_token=None),
    )

    install_streaming_sdk(monkeypatch, lambda **_kwargs: client)

    with pytest.raises(RuntimeError, match="append failed"):
        producer.publish(input_dir, tmp_path / "profile.json", 0, None)

    channel.close.assert_called_once_with()
    client.close.assert_called_once_with()
