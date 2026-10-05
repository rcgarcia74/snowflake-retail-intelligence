from __future__ import annotations

from pathlib import Path

from merchant_demo.pipeline import generate
from merchant_demo.validation import validate


def test_generation_is_logically_deterministic(
    tmp_path: Path, config_path: Path, cohort_dir: Path
) -> None:
    first = generate(config_path, cohort_dir, tmp_path / "first")
    second = generate(config_path, cohort_dir, tmp_path / "second")

    first_digests = {row["path"]: row["logical_sha256"] for row in first["datasets"]}
    second_digests = {row["path"]: row["logical_sha256"] for row in second["datasets"]}
    assert first_digests == second_digests
    assert first["total_bytes"] < 100_000_000


def test_generated_data_passes_readiness(
    tmp_path: Path, config_path: Path, cohort_dir: Path
) -> None:
    output = tmp_path / "generated"
    generate(config_path, cohort_dir, output)
    report = validate(config_path, cohort_dir, output)
    assert report["status"] == "PASS", report
    assert all(row["status"] == "PASS" for row in report["checks"])
