from __future__ import annotations

from itertools import combinations
from typing import Any

from .cohort import Cohort
from .config import ScenarioConfig


def build_suppliers(
    cohort: Cohort, config: ScenarioConfig
) -> tuple[list[dict[str, Any]], dict[int, str], set[int], set[int]]:
    affected_items, affected_stores = select_failure_cohort(cohort, config)
    ordered_items = sorted(int(row["item_sk"]) for row in cohort.items)
    suppliers = [
        {
            "supplier_id": f"SUP-{index:03d}",
            "supplier_name": f"Regional Supplier {index:02d}",
            "supplier_tier": "STRATEGIC" if index <= 2 else "STANDARD",
            "active": True,
        }
        for index in range(1, config.supplier_count + 1)
    ]

    assignment: dict[int, str] = {}
    for rank, item_sk in enumerate(ordered_items):
        if item_sk in affected_items:
            assignment[item_sk] = "SUP-001"
        else:
            assignment[item_sk] = f"SUP-{2 + (rank % max(1, config.supplier_count - 1)):03d}"
    return suppliers, assignment, affected_items, affected_stores


def select_failure_cohort(cohort: Cohort, config: ScenarioConfig) -> tuple[set[int], set[int]]:
    stores_by_item: dict[int, set[int]] = {}
    units_by_pair: dict[tuple[int, int], float] = {}
    for row in cohort.pairs:
        item_sk = int(row["item_sk"])
        store_sk = int(row["store_sk"])
        stores_by_item.setdefault(item_sk, set()).add(store_sk)
        units_by_pair[(item_sk, store_sk)] = float(row["avg_daily_units"])

    best: tuple[float, tuple[int, ...], set[int]] | None = None
    for item_group in combinations(sorted(stores_by_item), config.affected_item_count):
        common = set.intersection(*(stores_by_item[item] for item in item_group))
        if len(common) < config.affected_store_count:
            continue
        score = sum(units_by_pair[(item, store)] for item in item_group for store in common)
        candidate = (score, item_group, common)
        if (
            best is None
            or candidate[0] > best[0]
            or (candidate[0] == best[0] and candidate[1] < best[1])
        ):
            best = candidate

    if best is None:
        raise ValueError(
            "cohort qualification failed: no item group shares enough stores; "
            "select a denser TPC-DS cohort"
        )

    _, item_group, common_stores = best
    ranked_stores = sorted(
        common_stores,
        key=lambda store: (
            -sum(units_by_pair[(item, store)] for item in item_group),
            store,
        ),
    )
    return set(item_group), set(ranked_stores[: config.affected_store_count])
