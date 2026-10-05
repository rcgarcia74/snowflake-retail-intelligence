from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .cohort import load_cohort
from .config import load_config
from .io_utils import logical_digest, read_jsonl_rows, read_parquet_rows


def validate(config_path: Path, cohort_dir: Path, output_dir: Path) -> dict[str, Any]:
    config = load_config(config_path)
    cohort = load_cohort(cohort_dir, config)
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    checks: list[dict[str, str]] = []

    datasets = {item["path"]: item for item in manifest["datasets"]}
    inventory_history = read_parquet_rows(
        output_dir / "history/inventory_history/part-00000.parquet"
    )
    po_history = read_parquet_rows(output_dir / "history/purchase_order_history/part-00000.parquet")
    supplier_history = read_parquet_rows(
        output_dir / "history/supplier_performance_history/part-00000.parquet"
    )
    suppliers = read_jsonl_rows(output_dir / "openflow/supplier/supplier.jsonl")
    orders = read_jsonl_rows(output_dir / "openflow/current_purchase_orders/purchase_orders.jsonl")
    receipts = read_jsonl_rows(output_dir / "openflow/current_receipts/receipts.jsonl")
    plan = read_jsonl_rows(output_dir / "openflow/merchant_plan/merchant_plan.jsonl")
    sales = read_jsonl_rows(output_dir / "streaming/store_sales_events.jsonl")
    inventory = read_jsonl_rows(output_dir / "streaming/store_inventory_events.jsonl")

    item_keys = {int(row["item_sk"]) for row in cohort.items}
    store_keys = {int(row["store_sk"]) for row in cohort.stores}
    pair_keys = {(int(row["store_sk"]), int(row["item_sk"])) for row in cohort.pairs}
    supplier_ids = {row["supplier_id"] for row in suppliers}

    _check(
        checks,
        "manifest-digests",
        all(
            datasets[path]["logical_sha256"] == logical_digest(rows)
            for path, rows in (
                ("history/inventory_history/part-00000.parquet", inventory_history),
                ("history/purchase_order_history/part-00000.parquet", po_history),
                (
                    "history/supplier_performance_history/part-00000.parquet",
                    supplier_history,
                ),
                ("openflow/supplier/supplier.jsonl", suppliers),
                ("openflow/current_purchase_orders/purchase_orders.jsonl", orders),
                ("openflow/current_receipts/receipts.jsonl", receipts),
                ("openflow/merchant_plan/merchant_plan.jsonl", plan),
                ("streaming/store_sales_events.jsonl", sales),
                ("streaming/store_inventory_events.jsonl", inventory),
            )
        ),
        "logical checksums match the manifest",
    )

    _check(
        checks,
        "known-keys",
        all(
            int(row["item_sk"]) in item_keys and int(row["store_sk"]) in store_keys
            for row in orders + sales + inventory
        ),
        "all hot records use cohort item and store keys",
    )
    _check(
        checks,
        "inventory-history-coverage",
        len(inventory_history) == len(pair_keys) * config.history_days,
        "every cohort pair has exactly 90 historical inventory snapshots",
    )
    _check(
        checks,
        "po-history-valid",
        bool(po_history)
        and all(
            row["supplier_id"] in supplier_ids
            and int(row["received_qty"]) <= int(row["ordered_qty"])
            for row in po_history
        ),
        "historical purchase orders reference suppliers and reconcile quantities",
    )
    _check(
        checks,
        "supplier-history-coverage",
        len(supplier_history) == len(supplier_ids) * config.history_days,
        "every supplier has 90 days of performance history",
    )
    order_by_id = {row["po_id"]: row for row in orders}
    receipts_by_po = {row["po_id"]: row for row in receipts}
    _check(
        checks,
        "receipt-reconciliation",
        len(receipts) == len(orders)
        and all(
            row["po_id"] in order_by_id
            and int(row["received_qty"]) + int(row["rejected_qty"])
            <= int(order_by_id[row["po_id"]]["ordered_qty"])
            for row in receipts
        ),
        "every receipt has a valid purchase order and does not exceed ordered quantity",
    )
    _check(
        checks,
        "merchant-plan-coverage",
        len(plan) == len(store_keys) * config.hot_days,
        "merchant plan covers every cohort store for seven days",
    )
    _check(
        checks,
        "hot-event-coverage",
        len(sales) == len(pair_keys) * config.hot_days
        and len(inventory) == len(pair_keys) * config.hot_days,
        "POS and inventory events cover every pair for seven days",
    )

    sales_by_pair: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    inventory_by_pair: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in sales:
        sales_by_pair[(int(row["store_sk"]), int(row["item_sk"]))].append(row)
    for row in inventory:
        inventory_by_pair[(int(row["store_sk"]), int(row["item_sk"]))].append(row)
    receipt_by_pair = {
        (int(order["store_sk"]), int(order["item_sk"])): int(
            receipts_by_po[order["po_id"]]["received_qty"]
        )
        for order in orders
    }
    event_reconciliation = True
    for pair in pair_keys:
        pair_sales = sorted(sales_by_pair[pair], key=lambda row: row["event_ts"])
        pair_inventory = sorted(inventory_by_pair[pair], key=lambda row: row["event_ts"])
        inferred_start = int(pair_inventory[0]["on_hand_qty"]) + int(pair_sales[0]["units"])
        expected_end = max(
            0,
            inferred_start + receipt_by_pair[pair] - sum(int(row["units"]) for row in pair_sales),
        )
        if abs(expected_end - int(pair_inventory[-1]["on_hand_qty"])) > 1:
            event_reconciliation = False
            break
    _check(
        checks,
        "inventory-flow-reconciliation",
        event_reconciliation,
        "ending inventory reconciles to starting inventory plus receipts minus POS units",
    )

    latest_inventory: dict[tuple[int, int], dict[str, Any]] = {}
    units_by_pair = {
        (int(row["store_sk"]), int(row["item_sk"])): float(row["avg_daily_units"])
        for row in cohort.pairs
    }
    for row in inventory:
        latest_inventory[(int(row["store_sk"]), int(row["item_sk"]))] = row
    affected_items = set(manifest["affected_item_sks"])
    affected_stores = set(manifest["affected_store_sks"])
    risk: list[tuple[int, int]] = []
    control: list[tuple[int, int]] = []
    for pair, row in latest_inventory.items():
        days = float(row["on_hand_qty"]) / units_by_pair[pair]
        affected = pair[1] in affected_items and pair[0] in affected_stores
        if days <= config.risk_days_of_supply:
            risk.append(pair)
        elif not affected:
            control.append(pair)
    expected_affected = {
        (store_sk, item_sk)
        for store_sk in affected_stores
        for item_sk in affected_items
        if (store_sk, item_sk) in pair_keys
    }
    _check(
        checks,
        "intended-failure-cohort",
        expected_affected and expected_affected.issubset(set(risk)),
        "the configured supplier failure produces the intended stockout-risk cohort",
    )
    _check(
        checks, "healthy-controls", bool(control), "at least one non-affected pair remains healthy"
    )

    current_fill: dict[str, list[float]] = defaultdict(list)
    for order in orders:
        receipt = receipts_by_po[order["po_id"]]
        current_fill[order["supplier_id"]].append(
            float(receipt["received_qty"]) / float(order["ordered_qty"])
        )
    degraded = sum(current_fill[manifest["degraded_supplier_id"]]) / len(
        current_fill[manifest["degraded_supplier_id"]]
    )
    _check(
        checks,
        "degraded-supplier",
        degraded < 0.60,
        "the intended supplier has a current fill rate below 60 percent",
    )
    _check(
        checks,
        "volume-budget",
        int(manifest["total_bytes"]) <= config.max_generated_bytes,
        "generated files stay under the configured 100 MB ceiling",
    )

    report = {
        "status": "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL",
        "checks": checks,
        "total_bytes": manifest["total_bytes"],
        "total_rows": sum(int(item["rows"]) for item in manifest["datasets"]),
    }
    (output_dir / "validation_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def _check(checks: list[dict[str, str]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "status": "PASS" if passed else "FAIL", "detail": detail})
