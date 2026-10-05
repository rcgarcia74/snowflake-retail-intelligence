from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ScenarioConfig:
    seed: int
    history_days: int
    hot_days: int
    item_count: int
    store_count: int
    supplier_count: int
    affected_item_count: int
    affected_store_count: int
    degraded_fill_rate: float
    healthy_fill_rate: float
    risk_days_of_supply: float
    plan_growth_rate: float
    max_generated_bytes: int


def load_config(path: Path) -> ScenarioConfig:
    with path.open("r", encoding="utf-8") as handle:
        raw: dict[str, Any] = yaml.safe_load(handle)

    generation = raw["generation"]
    cohort = raw["cohort"]
    scenario = raw["failure_scenario"]
    thresholds = raw["thresholds"]
    config = ScenarioConfig(
        seed=int(generation["seed"]),
        history_days=int(generation["history_days"]),
        hot_days=int(generation["hot_days"]),
        item_count=int(cohort["item_count"]),
        store_count=int(cohort["store_count"]),
        supplier_count=int(generation["supplier_count"]),
        affected_item_count=int(scenario["affected_item_count"]),
        affected_store_count=int(scenario["affected_store_count"]),
        degraded_fill_rate=float(scenario["degraded_fill_rate"]),
        healthy_fill_rate=float(scenario["healthy_fill_rate"]),
        risk_days_of_supply=float(thresholds["risk_days_of_supply"]),
        plan_growth_rate=float(generation["plan_growth_rate"]),
        max_generated_bytes=int(thresholds["max_generated_bytes"]),
    )
    _validate(config)
    return config


def _validate(config: ScenarioConfig) -> None:
    if config.history_days != 90:
        raise ValueError("history_days must remain 90 for this tutorial")
    if config.hot_days != 7:
        raise ValueError("hot_days must remain 7 for this tutorial")
    if config.affected_item_count > config.item_count:
        raise ValueError("affected_item_count cannot exceed item_count")
    if config.affected_store_count > config.store_count:
        raise ValueError("affected_store_count cannot exceed store_count")
    for name, value in (
        ("degraded_fill_rate", config.degraded_fill_rate),
        ("healthy_fill_rate", config.healthy_fill_rate),
    ):
        if not 0 < value <= 1:
            raise ValueError(f"{name} must be in (0, 1]")
    if config.degraded_fill_rate >= config.healthy_fill_rate:
        raise ValueError("degraded_fill_rate must be below healthy_fill_rate")
