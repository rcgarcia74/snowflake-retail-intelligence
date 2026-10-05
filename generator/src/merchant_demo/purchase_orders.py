from __future__ import annotations

from datetime import timedelta
from typing import Any

from .cohort import Cohort
from .config import ScenarioConfig
from .io_utils import stable_unit


def build_purchase_order_history(
    cohort: Cohort, config: ScenarioConfig, assignment: dict[int, str]
) -> list[dict[str, Any]]:
    first_day = cohort.simulation_date - timedelta(days=config.hot_days + config.history_days)
    rows: list[dict[str, Any]] = []
    for pair in sorted(cohort.pairs, key=lambda row: (int(row["store_sk"]), int(row["item_sk"]))):
        item_sk = int(pair["item_sk"])
        store_sk = int(pair["store_sk"])
        weekly_units = max(7, round(float(pair["avg_daily_units"]) * 7.5))
        for offset in range(0, config.history_days, 7):
            order_date = first_day + timedelta(days=offset)
            fill_rate = 0.96 + 0.04 * stable_unit(
                config.seed, "hist-fill", item_sk, store_sk, offset
            )
            ordered = weekly_units
            received = min(ordered, round(ordered * fill_rate))
            po_id = f"H-{order_date:%Y%m%d}-{store_sk}-{item_sk}"
            rows.append(
                {
                    "po_id": po_id,
                    "supplier_id": assignment[item_sk],
                    "store_sk": store_sk,
                    "item_sk": item_sk,
                    "order_date": order_date,
                    "expected_receipt_date": order_date + timedelta(days=3),
                    "actual_receipt_date": order_date + timedelta(days=3),
                    "ordered_qty": ordered,
                    "received_qty": received,
                    "fill_rate": round(received / ordered, 4),
                    "on_time": True,
                }
            )
    return rows


def build_hot_purchase_orders(
    cohort: Cohort,
    config: ScenarioConfig,
    assignment: dict[int, str],
    affected_items: set[int],
    affected_stores: set[int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    first_day = cohort.simulation_date - timedelta(days=config.hot_days - 1)
    orders: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    for pair in sorted(cohort.pairs, key=lambda row: (int(row["store_sk"]), int(row["item_sk"]))):
        item_sk = int(pair["item_sk"])
        store_sk = int(pair["store_sk"])
        ordered = max(7, round(float(pair["avg_daily_units"]) * 7))
        # Supplier 001 degrades across its assigned items. Only the selected
        # stores begin the hot window with constrained inventory, so the
        # business impact remains an item/store cohort rather than every store.
        supplier_degraded = assignment[item_sk] == "SUP-001"
        fill_rate = config.degraded_fill_rate if supplier_degraded else config.healthy_fill_rate
        received = max(0, min(ordered, round(ordered * fill_rate)))
        po_id = f"C-{first_day:%Y%m%d}-{store_sk}-{item_sk}"
        receipt_date = first_day + timedelta(days=2)
        orders.append(
            {
                "po_id": po_id,
                "supplier_id": assignment[item_sk],
                "store_sk": store_sk,
                "item_sk": item_sk,
                "order_date": first_day,
                "expected_receipt_date": receipt_date,
                "ordered_qty": ordered,
                "status": "PARTIAL" if received < ordered else "RECEIVED",
                "updated_at": f"{receipt_date.isoformat()}T06:00:00",
            }
        )
        receipts.append(
            {
                "receipt_id": f"R-{po_id}",
                "po_id": po_id,
                "receipt_date": receipt_date,
                "received_qty": received,
                "rejected_qty": 0,
                "updated_at": f"{receipt_date.isoformat()}T06:05:00",
            }
        )
    return orders, receipts


def build_supplier_performance_history(
    cohort: Cohort, config: ScenarioConfig, supplier_ids: list[str]
) -> list[dict[str, Any]]:
    first_day = cohort.simulation_date - timedelta(days=config.hot_days + config.history_days)
    rows: list[dict[str, Any]] = []
    for supplier_id in sorted(supplier_ids):
        for offset in range(config.history_days):
            score = stable_unit(config.seed, "supplier", supplier_id, offset)
            rows.append(
                {
                    "performance_date": first_day + timedelta(days=offset),
                    "supplier_id": supplier_id,
                    "fill_rate": round(0.955 + score * 0.04, 4),
                    "on_time_rate": round(0.96 + score * 0.035, 4),
                    "open_po_count": int(2 + score * 8),
                    "avg_lead_time_days": round(2.5 + score * 1.5, 2),
                }
            )
    return rows
