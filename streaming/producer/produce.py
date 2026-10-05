#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

STREAMS = {
    "sales": {
        "file": "store_sales_events.jsonl",
        "pipe": "STORE_SALES_EVENTS_PIPE",
        "channel": "MDI_SALES_CHANNEL",
    },
    "inventory": {
        "file": "store_inventory_events.jsonl",
        "pipe": "STORE_INVENTORY_EVENTS_PIPE",
        "channel": "MDI_INVENTORY_CHANNEL",
    },
}


def read_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def selected(row: dict[str, Any], through_date: str | None) -> bool:
    return through_date is None or str(row["event_ts"])[:10] <= through_date


def dry_run(input_dir: Path, through_date: str | None) -> int:
    total = 0
    for name, stream in STREAMS.items():
        rows = [row for row in read_rows(input_dir / stream["file"]) if selected(row, through_date)]
        if not rows:
            raise SystemExit(f"no {name} rows matched the selected date range")
        total += len(rows)
        print(
            f"PASS {name}: {len(rows):,} rows; "
            f"first={rows[0]['event_id']}; last={rows[-1]['event_id']}"
        )
    print(f"PASS dry run: {total:,} rows ready; no network calls made")
    return 0


def publish(input_dir: Path, profile: Path, pace_ms: int, through_date: str | None) -> int:
    try:
        from snowflake.ingest.streaming import StreamingIngestClient
    except ImportError as error:
        raise SystemExit(
            "live mode requires the snowpipe-streaming package; "
            "install streaming/producer/requirements.txt"
        ) from error

    for name, stream in STREAMS.items():
        rows = read_rows(input_dir / stream["file"])
        client = StreamingIngestClient(
            client_name=f"mdi-{name}-producer",
            db_name="RETAIL_DEMO",
            schema_name="RAW",
            pipe_name=stream["pipe"],
            profile_json=str(profile),
        )
        channel, status = client.open_channel(stream["channel"], "0")
        committed = int(status.latest_committed_offset_token or "0")
        final_offset = committed
        for offset, row in enumerate(rows, start=1):
            if offset <= committed:
                continue
            if not selected(row, through_date):
                break
            channel.append_row(row, str(offset))
            final_offset = offset
            if pace_ms:
                time.sleep(pace_ms / 1000)
        if final_offset > committed:
            channel.wait_for_commit(
                lambda token: token is not None and int(token) >= final_offset,
                timeout_seconds=120,
            )
        channel.close()
        client.close()
        print(f"PASS {name}: committed through offset {final_offset:,}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay generated POS and inventory events")
    parser.add_argument("--input", type=Path, default=Path("generated/streaming"))
    parser.add_argument("--profile", type=Path, default=Path("streaming/producer/profile.json"))
    parser.add_argument("--live", action="store_true", help="send rows to Snowflake")
    parser.add_argument("--pace-ms", type=int, default=0, help="optional delay between events")
    parser.add_argument(
        "--through-date",
        help=(
            "send only the chronological source prefix through YYYY-MM-DD; "
            "rerun without it to resume"
        ),
    )
    args = parser.parse_args()
    if args.pace_ms < 0:
        raise SystemExit("--pace-ms cannot be negative")
    if not args.live:
        return dry_run(args.input, args.through_date)
    return publish(args.input, args.profile, args.pace_ms, args.through_date)


if __name__ == "__main__":
    raise SystemExit(main())
