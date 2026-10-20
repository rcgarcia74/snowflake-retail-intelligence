from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "sql/08_coco_incident_lab"


def _read(name: str) -> str:
    return (LAB / name).read_text(encoding="utf-8")


def test_coco_incident_lab_isolated_from_the_working_demo() -> None:
    bootstrap = _read("00_create_sandbox.sql")
    inputs = _read("00a_clone_sandbox_inputs.sql")
    cleanup = _read("98_cleanup_sandbox.sql")

    assert "CREATE DATABASE RETAIL_DEMO_COCO_LAB" in bootstrap
    assert "USE ROLE RETAIL_DEMO_ENGINEER" not in bootstrap
    assert "CREATE TABLE RAW.MERCHANT_PLAN CLONE RETAIL_DEMO.RAW.MERCHANT_PLAN" in inputs
    assert "CREATE TABLE RAW.STORE_SALES_EVENTS CLONE RETAIL_DEMO.RAW.STORE_SALES_EVENTS" in inputs
    assert "DROP DATABASE IF EXISTS RETAIL_DEMO_COCO_LAB" in cleanup
    assert "DROP DATABASE RETAIL_DEMO;" not in cleanup


def test_coco_incident_lab_has_explicit_fault_and_recovery_contracts() -> None:
    fault = _read("03_inject_business_date_fault.sql")
    recovery = _read("05_fix_business_date_contract.sql")
    fault_validation = _read("04_validate_fault_detected.sql")
    recovery_validation = _read("06_validate_recovery.sql")

    assert "p.INGESTED_AT::DATE = d.BUSINESS_DATE" in fault
    assert "p.PLAN_DATE = d.BUSINESS_DATE" not in fault
    assert "p.PLAN_DATE = d.BUSINESS_DATE" in recovery
    assert "INGESTED_AT remains operational metadata" in recovery
    assert "ASSERT_EXPECTED_FAULT()" in fault_validation
    assert "ASSERT_BUSINESS_DATE_CONTRACT()" in recovery_validation

    for path in LAB.glob("*.sql"):
        assert "CONFIG_DEMO_SCENARIO_ITEM" not in path.read_text(encoding="utf-8"), path

    fault_expression = "p.INGESTED_AT::DATE = d.BUSINESS_DATE"
    for path in (ROOT / "sql").rglob("*.sql"):
        if path != LAB / "03_inject_business_date_fault.sql":
            assert fault_expression not in path.read_text(encoding="utf-8"), path


def test_coco_incident_lab_documentation_preserves_production_boundary() -> None:
    document = (ROOT / "docs/14-coco-incident-lab.md").read_text(encoding="utf-8")

    assert "RETAIL_DEMO_COCO_LAB" in document
    assert "Do not run the fault or repair scripts against `RETAIL_DEMO`." in document
    assert "Openflow process group remains stopped" in document
    assert "INGESTED_AT" in document


def test_coco_recovery_prompt_is_deterministic() -> None:
    prompt = (ROOT / "coco/apply-approved-business-date-fix.md").read_text(encoding="utf-8")

    assert "Do not create or revise a plan" in prompt
    assert "snow sql -c retail_demo" in prompt
    assert "05_fix_business_date_contract.sql" in prompt
    assert "06_validate_recovery.sql" in prompt
    assert "ALTER DYNAMIC TABLE RETAIL_DEMO_COCO_LAB.ANALYTICS.ITEM_STORE_DAY RESUME" in prompt
    assert "175 expected rows and 0 unmatched" in prompt
    assert "scheduling_state is `ACTIVE` or `RUNNING`" in prompt
    assert "Do not run `01_create_healthy_pipeline.sql`" in prompt
    assert "Do not run `03_inject_business_date_fault.sql`" in prompt
    assert "Do not run `98_cleanup_sandbox.sql`" in prompt
    assert "Do not suspend" in prompt


def test_phase_two_step_four_contains_the_deterministic_recovery_prompt() -> None:
    document = (ROOT / "docs/14-coco-incident-lab.md").read_text(encoding="utf-8")

    assert "Phase 2, Step 4" in document
    assert "Do not create or revise a plan" in document
    assert "05_fix_business_date_contract.sql" in document
    assert "06_validate_recovery.sql" in document
    assert "175 expected rows and 0 unmatched" in document
    assert "scheduling_state is ACTIVE or RUNNING" in document
    assert "Do not suspend" in document
