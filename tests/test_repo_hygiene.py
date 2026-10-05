from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _tracked_candidates() -> list[Path]:
    ignored = {".git", ".venv", "__pycache__", ".pytest_cache", "generated", "data"}
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file() and not any(part in ignored for part in path.parts)
    ]


def test_no_agent_control_files() -> None:
    forbidden_names = {"agents.md", "claude.md"}
    forbidden_parts = {".codex", ".claude"}
    for path in _tracked_candidates():
        relative = path.relative_to(ROOT)
        assert path.name.lower() not in forbidden_names
        assert not forbidden_parts.intersection(relative.parts)


def test_no_retailer_specific_reference() -> None:
    # Constructed in two pieces so the public repository does not contain the
    # prohibited company name even inside its hygiene test.
    term = "wal" + "mart"
    for path in _tracked_candidates():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        assert term not in text.lower(), path


def test_no_obvious_secrets() -> None:
    patterns = [
        re.compile(r"AKIA[0-9A-Z]{16}"),
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        re.compile(r"(?i)(password|secret|token)\s*[:=]\s*['\"][^<'\"]{8,}"),
    ]
    for path in _tracked_candidates():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in patterns:
            assert not pattern.search(text), path
