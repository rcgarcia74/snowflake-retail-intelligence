from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest
import yaml
from merchant_demo.io_utils import read_jsonl_rows, write_jsonl
from merchant_demo.pipeline import generate

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_ROUTES = {
    "retail-demo/landing/openflow/supplier/": "RETAIL_DEMO.RAW.SUPPLIER",
    "retail-demo/landing/openflow/current_purchase_orders/": (
        "RETAIL_DEMO.RAW.PURCHASE_ORDER"
    ),
    "retail-demo/landing/openflow/current_receipts/": "RETAIL_DEMO.RAW.RECEIPT",
    "retail-demo/landing/openflow/merchant_plan/": "RETAIL_DEMO.RAW.MERCHANT_PLAN",
}


def test_openflow_sql_supports_role_restricted_pat_connections() -> None:
    bootstrap = (ROOT / "openflow/config/00_gen2_roles.sql").read_text(
        encoding="utf-8"
    )
    objects = (ROOT / "openflow/config/01_gen2_objects.sql").read_text(
        encoding="utf-8"
    )
    runtime = (ROOT / "openflow/config/02_gen2_runtime.sql").read_text(
        encoding="utf-8"
    )
    object_cleanup = (ROOT / "openflow/config/98_cleanup_objects.sql").read_text(
        encoding="utf-8"
    )
    role_cleanup = (ROOT / "openflow/config/99_cleanup.sql").read_text(
        encoding="utf-8"
    )

    assert "USE ROLE ACCOUNTADMIN" in bootstrap
    assert "CREATE ROLE IF NOT EXISTS OPENFLOW_ADMIN" in bootstrap
    assert not any(
        line.strip().startswith("USE ROLE") for line in objects.splitlines()
    )
    assert "CREATE ROLE IF NOT EXISTS" not in objects
    assert not any(
        line.strip().startswith("USE ROLE") for line in runtime.splitlines()
    )
    assert not any(
        line.strip().startswith("USE ROLE") for line in object_cleanup.splitlines()
    )
    assert "DROP OPENFLOW DEPLOYMENT" in object_cleanup
    assert "DROP ROLE" not in object_cleanup
    assert "USE ROLE ACCOUNTADMIN" in role_cleanup
    assert "DROP ROLE IF EXISTS OPENFLOW_ADMIN" in role_cleanup
    assert "DROP OPENFLOW DEPLOYMENT" not in role_cleanup


def test_openflow_contract_owns_only_staged_operational_feeds() -> None:
    path = ROOT / "openflow/config/flow-spec.yaml"
    contract = yaml.safe_load(path.read_text(encoding="utf-8"))
    routes = {route["prefix"]: route["table"] for route in contract["routes"]}
    services = {service["type"]: service for service in contract["controller_services"]}
    parameters = yaml.safe_load(
        (ROOT / "openflow/config/parameters.example.yaml").read_text(encoding="utf-8")
    )

    assert contract["implementation"] == {
        "deployment_generation": 2,
        "type": "custom-process-group",
        "connector_object": False,
        "note": "Custom canvas flows are not schema-level gen 2 OPENFLOW CONNECTOR objects.",
    }
    assert contract["source"]["listing_strategy"] == "tracking-timestamps"
    assert contract["source"]["initial_listing_target"] == "all-available"
    assert routes == EXPECTED_ROUTES
    assert all(route["statement_type"] == "INSERT" for route in contract["routes"])
    assert {route["filename"] for route in contract["routes"]} == {
        "supplier.jsonl",
        "purchase_orders.jsonl",
        "receipts.jsonl",
        "merchant_plan.jsonl",
    }
    assert {
        "SnowflakeConnectionService",
        "SnowflakeWorkloadIdentityTokenProvider",
        "AWSCredentialsProviderControllerService",
        "VolatileSchemaCache",
        "JsonTreeReader",
    } <= services.keys()
    aws_credentials = services["AWSCredentialsProviderControllerService"]
    assert aws_credentials["static_credentials_allowed"] is False
    assert parameters["SNOWFLAKE_AUTHENTICATION_STRATEGY"] == "SNOWFLAKE_MANAGED"
    assert "AWS_ACCESS_KEY_ID" not in parameters
    assert "AWS_SECRET_ACCESS_KEY" not in parameters
    assert contract["idempotency"]["require_empty_targets"] is True
    assert contract["readiness"]["queued_failures"] == 0
    assert contract["time_contract"]["business_event_clock"] == (
        "TPC-DS scenario simulation_date"
    )
    assert contract["time_contract"]["wall_clock_fields"] == ["INGESTED_AT"]
    assert "STORE_SALES_EVENTS" not in path.read_text(encoding="utf-8")
    assert "STORE_INVENTORY_EVENTS" not in path.read_text(encoding="utf-8")


def test_openflow_business_dates_use_locked_scenario_clock(
    tmp_path: Path, config_path: Path, cohort_dir: Path
) -> None:
    output = tmp_path / "generated"
    manifest = generate(config_path, cohort_dir, output)

    _assert_openflow_business_dates(output, manifest)

    plan_path = output / "openflow/merchant_plan/merchant_plan.jsonl"
    plans = read_jsonl_rows(plan_path)
    plans[0]["plan_date"] = "2099-01-01"
    write_jsonl(plan_path, plans)
    with pytest.raises(AssertionError):
        _assert_openflow_business_dates(output, manifest)


def _assert_openflow_business_dates(output: Path, manifest: dict[str, object]) -> None:
    simulation_date = date.fromisoformat(str(manifest["simulation_date"]))
    first_hot_date = simulation_date - timedelta(days=int(manifest["hot_days"]) - 1)

    orders = read_jsonl_rows(
        output / "openflow/current_purchase_orders/purchase_orders.jsonl"
    )
    receipts = read_jsonl_rows(output / "openflow/current_receipts/receipts.jsonl")
    plans = read_jsonl_rows(output / "openflow/merchant_plan/merchant_plan.jsonl")

    assert {date.fromisoformat(row["order_date"]) for row in orders} == {first_hot_date}
    assert {date.fromisoformat(row["expected_receipt_date"]) for row in orders} == {
        first_hot_date + timedelta(days=2)
    }
    assert {date.fromisoformat(row["receipt_date"]) for row in receipts} == {
        first_hot_date + timedelta(days=2)
    }
    assert {date.fromisoformat(row["plan_date"]) for row in plans} == {
        first_hot_date + timedelta(days=offset)
        for offset in range(int(manifest["hot_days"]))
    }
    assert all(row["updated_at"][:10] == row["expected_receipt_date"] for row in orders)
    assert all(row["updated_at"][:10] == row["receipt_date"] for row in receipts)
    assert all(row["updated_at"][:10] == row["plan_date"] for row in plans)
