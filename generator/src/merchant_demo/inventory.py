from __future__ import annotations

from datetime import timedelta
from typing import Any

from .cohort import Cohort
from .config import ScenarioConfig
from .io_utils import stable_unit


def build_inventory_history(cohort: Cohort, config: ScenarioConfig) -> list[dict[str, Any]]:
    first_day = cohort.simulation_date - timedelta(days=config.hot_days + config.history_days)
    rows: list[dict[str, Any]] = []
    for pair in _sorted_pairs(cohort):
        units = float(pair["avg_daily_units"])
        for offset in range(config.history_days):
            snapshot_date = first_day + timedelta(days=offset)
            cycle_days = 7 + 7 * stable_unit(
                config.seed, "cycle", pair["store_sk"], pair["item_sk"]
            )
            on_hand = max(1, round(units * (cycle_days - (offset % 7) + 4)))
            on_order = round(units * 7) if offset % 7 in (5, 6) else 0
            in_transit = round(on_order * 0.55) if offset % 7 == 6 else 0
            rows.append(
                {
                    "snapshot_date": snapshot_date,
                    "store_sk": int(pair["store_sk"]),
                    "item_sk": int(pair["item_sk"]),
                    "on_hand_qty": on_hand,
                    "on_order_qty": on_order,
                    "in_transit_qty": in_transit,
                    "days_of_supply": round(on_hand / units, 3),
                }
            )
    return rows


def _sorted_pairs(cohort: Cohort) -> list[dict[str, Any]]:
    return sorted(cohort.pairs, key=lambda row: (int(row["store_sk"]), int(row["item_sk"])))
