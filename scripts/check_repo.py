#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {".git", ".venv", "__pycache__", ".pytest_cache", "generated", "data"}
FORBIDDEN_NAMES = {"agents.md", "claude.md"}
FORBIDDEN_PARTS = {".codex", ".claude"}
RETAILER_TERM = "wal" + "mart"
SECRET_PATTERNS = {
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "assigned secret": re.compile(r"(?i)(password|secret|token)\s*[:=]\s*['\"][^<'\"]{8,}"),
}


def main() -> int:
    failures: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in IGNORED for part in path.parts):
            continue
        relative = path.relative_to(ROOT)
        if path.name.lower() in FORBIDDEN_NAMES or FORBIDDEN_PARTS.intersection(relative.parts):
            failures.append(f"agent-control file: {relative}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if RETAILER_TERM in text.lower():
            failures.append(f"retailer-specific reference: {relative}")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                failures.append(f"possible {label}: {relative}")
    if failures:
        print("FAIL")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    print("PASS: repository hygiene checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
