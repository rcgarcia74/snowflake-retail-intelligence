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

The tutorial warehouse has `AUTO_RESUME = FALSE`. Each readiness script resumes it immediately
before its compute statement so metadata compilation cannot consume the entire 60-second idle
window. Create and inspect the readiness view:

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" -f sql/07_validation/01_demo_readiness.sql
```

Every row must be `PASS`. Then execute the assertion, which raises an error on any failure:

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" -f sql/07_validation/02_assert_readiness.sql
```

The SQL gate checks cohort qualification, Iceberg retention, Openflow row/reconciliation state,
streaming coverage and keys, healthy and failed populations, temporal business evidence, and
scorecard-to-detail reconciliation for lost sales, signed margin impact, and positive margin at
risk. The margin-at-risk gate also requires a non-negative value on every problem row and a positive
aggregate for the failure scenario.

Check the warehouse immediately after the assertion, even when the assertion fails:

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" -q \
  "SHOW WAREHOUSES LIKE 'RETAIL_DEMO_WH';"
```

If its state is `STARTED`, run `ALTER WAREHOUSE RETAIL_DEMO_WH SUSPEND`, then run `SHOW WAREHOUSES`
again. If the 60-second timer already changed the state to `SUSPENDED`, do not issue a redundant
`SUSPEND`; Snowflake reports that as an invalid-state error.

Require `state = SUSPENDED`, `running = 0`, `queued = 0`, `auto_suspend = 60`, and
`auto_resume = false` before ending the validation window.

Capture the readiness result, generator manifest, package versions, Snowflake current version, and
Git commit in your demo evidence. Do not commit account identifiers or query URLs.

Next: [cleanup](13-cleanup.md).
