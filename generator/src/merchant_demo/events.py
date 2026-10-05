from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any

from .cohort import Cohort
from .config import ScenarioConfig
from .io_utils import stable_unit


def build_hot_events(
    cohort: Cohort,
    config: ScenarioConfig,
    affected_items: set[int],
    affected_stores: set[int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    first_day = cohort.simulation_date - timedelta(days=config.hot_days - 1)
    sales_rows: list[dict[str, Any]] = []
    inventory_rows: list[dict[str, Any]] = []
    ordered_pairs = sorted(
        cohort.pairs, key=lambda row: (int(row["store_sk"]), int(row["item_sk"]))
    )

    for pair in ordered_pairs:
        item_sk = int(pair["item_sk"])
        store_sk = int(pair["store_sk"])
        demand = float(pair["avg_daily_units"])
        unit_price = float(pair["avg_daily_sales"]) / demand
        affected = item_sk in affected_items and store_sk in affected_stores
        on_hand = demand * (5.5 if affected else 9.0)
        receipt_qty = (
            demand
            * 7
            * (config.degraded_fill_rate if item_sk in affected_items else config.healthy_fill_rate)
        )

        for offset in range(config.hot_days):
            event_date = first_day + timedelta(days=offset)
            variance = 0.92 + 0.16 * stable_unit(config.seed, "sales", item_sk, store_sk, offset)
            units = max(1, round(demand * variance))
            if offset == 2:
                on_hand += receipt_qty
            on_hand = max(0.0, on_hand - units)
            event_ts = datetime.combine(event_date, time(hour=12, minute=offset))
            inventory_ts = datetime.combine(event_date, time(hour=23, minute=55))
            sales_rows.append(
                {
                    "event_id": f"SALE-{event_date:%Y%m%d}-{store_sk}-{item_sk}",
                    "event_ts": event_ts,
                    "store_sk": store_sk,
                    "item_sk": item_sk,
                    "units": units,
                    "sales_amount": round(units * unit_price, 2),
                    "discount_amount": 0.0,
                    "net_paid": round(units * unit_price, 2),
                }
            )
            inventory_rows.append(
                {
                    "event_id": f"INV-{event_date:%Y%m%d}-{store_sk}-{item_sk}",
                    "event_ts": inventory_ts,
                    "store_sk": store_sk,
                    "item_sk": item_sk,
                    "on_hand_qty": round(on_hand),
                    "on_order_qty": 0 if offset >= 2 else round(demand * 7),
                    "in_transit_qty": 0 if offset >= 2 else round(demand * 7),
                }
            )
    sales_rows.sort(key=lambda row: (row["event_ts"], row["store_sk"], row["item_sk"]))
    inventory_rows.sort(key=lambda row: (row["event_ts"], row["store_sk"], row["item_sk"]))
    return sales_rows, inventory_rows
