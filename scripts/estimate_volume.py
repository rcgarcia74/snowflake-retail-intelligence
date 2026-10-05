#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def human_bytes(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024 or unit == "GiB":
            return f"{value:.2f} {unit}"
        value /= 1024
    raise AssertionError("unreachable")


def main() -> int:
    parser = argparse.ArgumentParser(description="Report generated row and file volume")
    parser.add_argument("--output", type=Path, default=Path("generated"))
    args = parser.parse_args()
    manifest = json.loads((args.output / "manifest.json").read_text(encoding="utf-8"))
    print(
        f"Total: {sum(row['rows'] for row in manifest['datasets']):,} rows; "
        f"{human_bytes(manifest['total_bytes'])}"
    )
    for row in manifest["datasets"]:
        print(f"{row['path']}: {row['rows']:,} rows; {human_bytes(row['bytes'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
