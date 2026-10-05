from __future__ import annotations

import json
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generator/src"))


@pytest.fixture()
def cohort_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "cohort"
    directory.mkdir()
    scenario = {
        "scenario_id": "TEST_SCENARIO",
        "category": "Test Category",
        "baseline_start_date": "2002-01-01",
        "baseline_end_date": "2002-03-25",
        "simulation_date": "2002-03-26",
    }
    (directory / "scenario.json").write_text(
        json.dumps(scenario, sort_keys=True) + "\n", encoding="utf-8"
    )
    items = [
        {
            "item_sk": index,
            "item_id": f"ITEM-{index:03d}",
            "item_desc": f"Test Item {index:03d}",
            "category": "Test Category",
            "class": "Test Class",
            "brand": f"Brand {index % 4}",
            "manufacturer_id": index % 5,
            "manufacturer_name": f"Maker {index % 5}",
            "current_price": 5.0 + index / 10,
            "wholesale_cost": 3.0 + index / 20,
        }
        for index in range(1, 21)
    ]
    stores = [
        {
            "store_sk": index,
            "store_id": f"STORE-{index:03d}",
            "store_name": f"Test Store {index:03d}",
            "city": "Test City",
            "state": "TS",
            "market_id": 1 + index % 3,
            "division_id": 1,
        }
        for index in range(1, 26)
    ]
    pairs = [
        {
            "store_sk": store,
            "item_sk": item,
            "avg_daily_units": float(3 + (item + store) % 7),
            "avg_daily_sales": float((3 + (item + store) % 7) * (5 + item / 10)),
            "avg_daily_margin": float((3 + (item + store) % 7) * 2.0),
            "active_days": 70,
        }
        for store in range(1, 26)
        for item in range(1, 21)
    ]
    pq.write_table(pa.Table.from_pylist(items), directory / "items.parquet")
    pq.write_table(pa.Table.from_pylist(stores), directory / "stores.parquet")
    pq.write_table(pa.Table.from_pylist(pairs), directory / "item_store_baseline.parquet")
    return directory


@pytest.fixture()
def config_path() -> Path:
    return ROOT / "config/scenario.yaml"
