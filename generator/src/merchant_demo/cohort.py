from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from .config import ScenarioConfig


@dataclass(frozen=True)
class Cohort:
    scenario: dict[str, Any]
    items: list[dict[str, Any]]
    stores: list[dict[str, Any]]
    pairs: list[dict[str, Any]]

    @property
    def simulation_date(self) -> date:
        value = self.scenario["simulation_date"]
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))


def load_cohort(directory: Path, config: ScenarioConfig) -> Cohort:
    scenario = _load_scenario(directory)
    cohort = Cohort(
        scenario=scenario,
        items=_lower_keys(pq.read_table(directory / "items.parquet").to_pylist()),
        stores=_lower_keys(pq.read_table(directory / "stores.parquet").to_pylist()),
        pairs=_lower_keys(pq.read_table(directory / "item_store_baseline.parquet").to_pylist()),
    )
    _validate(cohort, config)
    return cohort


def _load_scenario(directory: Path) -> dict[str, Any]:
    json_path = directory / "scenario.json"
    if json_path.exists():
        return json.loads(json_path.read_text(encoding="utf-8"))
    parquet_path = directory / "scenario.parquet"
    if parquet_path.exists():
        rows = pq.read_table(parquet_path).to_pylist()
        if len(rows) != 1:
            raise ValueError("scenario.parquet must contain exactly one row")
        return {str(key).lower(): value for key, value in rows[0].items()}
    raise FileNotFoundError("cohort needs scenario.json or scenario.parquet")


def _lower_keys(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{str(key).lower(): value for key, value in row.items()} for row in rows]


def _validate(cohort: Cohort, config: ScenarioConfig) -> None:
    if len(cohort.items) != config.item_count:
        raise ValueError(f"expected {config.item_count} items, found {len(cohort.items)}")
    if len(cohort.stores) != config.store_count:
        raise ValueError(f"expected {config.store_count} stores, found {len(cohort.stores)}")

    item_keys = {int(row["item_sk"]) for row in cohort.items}
    store_keys = {int(row["store_sk"]) for row in cohort.stores}
    pair_keys: set[tuple[int, int]] = set()
    for row in cohort.pairs:
        item_sk = int(row["item_sk"])
        store_sk = int(row["store_sk"])
        if item_sk not in item_keys or store_sk not in store_keys:
            raise ValueError(f"baseline pair references an unknown key: {(store_sk, item_sk)}")
        if float(row["avg_daily_units"]) <= 0:
            raise ValueError(f"baseline demand must be positive: {(store_sk, item_sk)}")
        key = (store_sk, item_sk)
        if key in pair_keys:
            raise ValueError(f"duplicate baseline pair: {key}")
        pair_keys.add(key)

    if len(pair_keys) < config.affected_item_count * config.affected_store_count:
        raise ValueError("cohort does not contain enough item/store pairs for the failure scenario")
