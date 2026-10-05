#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from merchant_demo.pipeline import generate  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic supplemental retail data")
    parser.add_argument("--config", type=Path, default=Path("config/scenario.yaml"))
    parser.add_argument("--cohort", type=Path, default=Path("data/cohort"))
    parser.add_argument("--output", type=Path, default=Path("generated"))
    parser.add_argument("--force", action="store_true", help="replace an existing output directory")
    args = parser.parse_args()
    manifest = generate(args.config, args.cohort, args.output, force=args.force)
    print(json.dumps({"status": "PASS", **manifest}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
