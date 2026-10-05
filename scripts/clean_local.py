#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove only this tutorial's generated local data")
    parser.add_argument("--output", type=Path, default=Path("generated"))
    parser.add_argument("--yes", action="store_true", help="confirm deletion")
    args = parser.parse_args()
    target = args.output.resolve()
    repository = Path(__file__).resolve().parents[1]
    if repository not in target.parents or target == repository:
        raise SystemExit(f"refusing to remove a path outside the repository: {target}")
    if target.name not in {"generated", "build"}:
        raise SystemExit("refusing to remove a directory not named generated or build")
    if not args.yes:
        raise SystemExit(f"would remove {target}; rerun with --yes")
    if target.exists():
        shutil.rmtree(target)
        print(f"removed {target}")
    else:
        print(f"nothing to remove at {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
