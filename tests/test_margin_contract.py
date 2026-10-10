from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_margin_impact_and_margin_at_risk_are_distinct_contracts() -> None:
    dynamic_sql = (ROOT / "sql/05_dynamic_tables/01_dynamic_tables.sql").read_text(
        encoding="utf-8"
    )
    validation_sql = (ROOT / "sql/07_validation/01_demo_readiness.sql").read_text(
        encoding="utf-8"
    )

    assert "AS ESTIMATED_MARGIN_IMPACT" in dynamic_sql
    assert "GREATEST(UNIT_MARGIN, 0)" in dynamic_sql
    assert "AS MARGIN_AT_RISK" in dynamic_sql
    assert dynamic_sql.count("ESTIMATED_MARGIN_IMPACT") >= 4
    assert dynamic_sql.count("MARGIN_AT_RISK") >= 4
    assert "margin-at-risk-positive" in validation_sql
    assert "MARGIN_AT_RISK" in validation_sql
    assert "ESTIMATED_MARGIN_IMPACT" in validation_sql
