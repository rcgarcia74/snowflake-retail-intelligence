#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from merchant_demo.validation import validate  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate generated merchant demo data")
    parser.add_argument("--config", type=Path, default=Path("config/scenario.yaml"))
    parser.add_argument("--cohort", type=Path, default=Path("data/cohort"))
    parser.add_argument("--output", type=Path, default=Path("generated"))
    args = parser.parse_args()
    report = validate(args.config, args.cohort, args.output)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
