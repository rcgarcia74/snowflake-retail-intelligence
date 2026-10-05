#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from datetime import date, datetime
from pathlib import Path

import pyarrow.parquet as pq


def normalize(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def normalize_unload_name(directory: Path, expected_name: str) -> Path:
    expected = directory / expected_name
    if expected.exists():
        return expected
    matches = sorted(directory.glob(f"{expected_name}*"))
    if len(matches) != 1:
        raise SystemExit(
            f"expected one Snowflake unload matching {expected_name!r}, found {len(matches)}"
        )
    shutil.move(matches[0], expected)
    return expected


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize Snowflake's cohort unload into the generator input contract"
    )
    parser.add_argument("directory", type=Path, nargs="?", default=Path("data/cohort"))
    args = parser.parse_args()
    scenario_path = normalize_unload_name(args.directory, "scenario.parquet")
    normalize_unload_name(args.directory, "items.parquet")
    normalize_unload_name(args.directory, "stores.parquet")
    normalize_unload_name(args.directory, "item_store_baseline.parquet")
    rows = pq.read_table(scenario_path).to_pylist()
    if len(rows) != 1:
        raise SystemExit(f"expected one scenario row in {scenario_path}, found {len(rows)}")
    scenario = {key.lower(): normalize(value) for key, value in rows[0].items()}
    (args.directory / "scenario.json").write_text(
        json.dumps(scenario, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"wrote {args.directory / 'scenario.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
