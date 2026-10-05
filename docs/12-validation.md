# 12 — Validation and readiness

## Repository checks

```bash
make check
```

This runs unit/integration-style fixture tests plus repository hygiene. The generator tests create an
offline, complete 20-by-25 cohort in a temporary directory; no committed file pretends to be a real
TPC-DS export.

## Local data checks

```bash
python generator/validate.py --config config/scenario.yaml \
  --cohort data/cohort --output generated
```

The report verifies logical checksums, known keys, 90-day history, PO/receipt reconciliation,
seven-day plan/event coverage, the intended degraded supplier, risk cohort, healthy controls, and
the 100 MB limit.

## Snowflake checks

Create and inspect the readiness view:

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" -f sql/07_validation/01_demo_readiness.sql
```

Every row must be `PASS`. Then execute the assertion, which raises an error on any failure:

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" -f sql/07_validation/02_assert_readiness.sql
```

The SQL gate checks cohort qualification, Iceberg retention, Openflow row/reconciliation state,
streaming coverage and keys, healthy and failed populations, temporal business evidence, and
scorecard-to-detail reconciliation.

Capture the readiness result, generator manifest, package versions, Snowflake current version, and
Git commit in your demo evidence. Do not commit account identifiers or query URLs.

Next: [cleanup](13-cleanup.md).
