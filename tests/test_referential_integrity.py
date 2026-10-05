from __future__ import annotations

import json
from pathlib import Path

from merchant_demo.io_utils import read_jsonl_rows
from merchant_demo.pipeline import generate


def test_hot_records_use_manifest_cohort(
    tmp_path: Path, config_path: Path, cohort_dir: Path
) -> None:
    output = tmp_path / "generated"
    manifest = generate(config_path, cohort_dir, output)
    item_keys = set(range(1, 21))
    store_keys = set(range(1, 26))
    for relative in (
        "streaming/store_sales_events.jsonl",
        "streaming/store_inventory_events.jsonl",
        "openflow/current_purchase_orders/purchase_orders.jsonl",
    ):
        for row in read_jsonl_rows(output / relative):
            assert row["item_sk"] in item_keys
            assert row["store_sk"] in store_keys

    assert len(manifest["affected_item_sks"]) == 3
    assert len(manifest["affected_store_sks"]) == 8
    json.loads((output / "manifest.json").read_text(encoding="utf-8"))
