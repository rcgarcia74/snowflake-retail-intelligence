from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .cohort import load_cohort
from .config import load_config
from .events import build_hot_events
from .inventory import build_inventory_history
from .io_utils import write_jsonl, write_parquet
from .merchant_plan import build_merchant_plan
from .purchase_orders import (
    build_hot_purchase_orders,
    build_purchase_order_history,
    build_supplier_performance_history,
)
from .suppliers import build_suppliers


def generate(
    config_path: Path, cohort_dir: Path, output_dir: Path, force: bool = False
) -> dict[str, Any]:
    if output_dir.exists():
        if not force:
            raise FileExistsError(
                f"output already exists: {output_dir}; pass --force to replace it"
            )
        shutil.rmtree(output_dir)

    config = load_config(config_path)
    cohort = load_cohort(cohort_dir, config)
    suppliers, assignment, affected_items, affected_stores = build_suppliers(cohort, config)
    history_inventory = build_inventory_history(cohort, config)
    history_pos = build_purchase_order_history(cohort, config, assignment)
    history_supplier = build_supplier_performance_history(
        cohort, config, [row["supplier_id"] for row in suppliers]
    )
    hot_orders, hot_receipts = build_hot_purchase_orders(
        cohort, config, assignment, affected_items, affected_stores
    )
    plan = build_merchant_plan(cohort, config)
    sales_events, inventory_events = build_hot_events(
        cohort, config, affected_items, affected_stores
    )

    datasets: list[dict[str, Any]] = []
    datasets.append(
        write_parquet(
            output_dir / "history/inventory_history/part-00000.parquet", history_inventory
        )
    )
    datasets.append(
        write_parquet(output_dir / "history/purchase_order_history/part-00000.parquet", history_pos)
    )
    datasets.append(
        write_parquet(
            output_dir / "history/supplier_performance_history/part-00000.parquet",
            history_supplier,
        )
    )
    datasets.append(write_jsonl(output_dir / "openflow/supplier/supplier.jsonl", suppliers))
    datasets.append(
        write_jsonl(
            output_dir / "openflow/current_purchase_orders/purchase_orders.jsonl", hot_orders
        )
    )
    datasets.append(
        write_jsonl(output_dir / "openflow/current_receipts/receipts.jsonl", hot_receipts)
    )
    datasets.append(write_jsonl(output_dir / "openflow/merchant_plan/merchant_plan.jsonl", plan))
    datasets.append(write_jsonl(output_dir / "streaming/store_sales_events.jsonl", sales_events))
    datasets.append(
        write_jsonl(output_dir / "streaming/store_inventory_events.jsonl", inventory_events)
    )

    for dataset in datasets:
        dataset["path"] = Path(dataset["path"]).relative_to(output_dir).as_posix()

    total_bytes = sum(int(dataset["bytes"]) for dataset in datasets)
    if total_bytes > config.max_generated_bytes:
        raise ValueError(
            f"generated output is {total_bytes:,} bytes, above the configured "
            f"{config.max_generated_bytes:,}-byte ceiling"
        )

    manifest = {
        "format_version": 1,
        "scenario_id": cohort.scenario["scenario_id"],
        "simulation_date": cohort.simulation_date.isoformat(),
        "seed": config.seed,
        "history_days": config.history_days,
        "hot_days": config.hot_days,
        "item_count": len(cohort.items),
        "store_count": len(cohort.stores),
        "item_store_pair_count": len(cohort.pairs),
        "affected_item_sks": sorted(affected_items),
        "affected_store_sks": sorted(affected_stores),
        "degraded_supplier_id": "SUP-001",
        "datasets": datasets,
        "total_bytes": total_bytes,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest
