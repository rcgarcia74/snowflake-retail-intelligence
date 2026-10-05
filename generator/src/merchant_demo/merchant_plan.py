from __future__ import annotations

from datetime import timedelta
from typing import Any

from .cohort import Cohort
from .config import ScenarioConfig


def build_merchant_plan(cohort: Cohort, config: ScenarioConfig) -> list[dict[str, Any]]:
    first_day = cohort.simulation_date - timedelta(days=config.hot_days - 1)
    sales_by_store: dict[int, float] = {}
    margin_by_store: dict[int, float] = {}
    for pair in cohort.pairs:
        store_sk = int(pair["store_sk"])
        sales_by_store[store_sk] = sales_by_store.get(store_sk, 0.0) + float(
            pair["avg_daily_sales"]
        )
        margin_by_store[store_sk] = margin_by_store.get(store_sk, 0.0) + float(
            pair["avg_daily_margin"]
        )

    category = str(cohort.scenario["category"])
    rows: list[dict[str, Any]] = []
    for store_sk in sorted(sales_by_store):
        for offset in range(config.hot_days):
            plan_date = first_day + timedelta(days=offset)
            rows.append(
                {
                    "plan_id": f"PLAN-{store_sk}-{plan_date:%Y%m%d}",
                    "plan_date": plan_date,
                    "store_sk": store_sk,
                    "category": category,
                    "sales_plan": round(
                        sales_by_store[store_sk] * (1 + config.plan_growth_rate), 2
                    ),
                    "margin_plan": round(
                        margin_by_store[store_sk] * (1 + config.plan_growth_rate), 2
                    ),
                    "updated_at": f"{plan_date.isoformat()}T00:05:00",
                }
            )
    return rows
