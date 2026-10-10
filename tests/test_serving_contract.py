from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_category_sales_to_plan_trend_is_a_serving_contract() -> None:
    serving_sql = (ROOT / "sql/06_serving/01_serving_views.sql").read_text(
        encoding="utf-8"
    )

    assert "CREATE OR REPLACE SECURE VIEW CATEGORY_SALES_TO_PLAN_TREND" in serving_sql
    assert "FROM RETAIL_DEMO.ANALYTICS.CATEGORY_STORE_DAY" in serving_sql
    assert "AS SALES_SHORTFALL" in serving_sql
    assert (
        "GRANT SELECT ON VIEW CATEGORY_SALES_TO_PLAN_TREND "
        "TO ROLE RETAIL_DEMO_METABASE;"
    ) in serving_sql
