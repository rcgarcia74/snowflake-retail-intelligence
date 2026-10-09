# 08 — Build Dynamic Tables

Create the pipeline after historical, Openflow, and healthy-checkpoint event data is present:

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" -f sql/05_dynamic_tables/01_dynamic_tables.sql
snow sql -c "$SNOWFLAKE_CONNECTION" -f sql/06_serving/01_serving_views.sql
```

Run the two files in that order. The first file creates and initializes the eight Dynamic Tables;
the second creates the three secure serving views. Both use `RETAIL_DEMO_WH`, so keep the warehouse
suspended until the preflight gate passes and suspend it again after validation.

The eight Dynamic Tables are:

1. `ITEM_STORE_BASELINE`
2. `ITEM_STORE_DAY`
3. `SUPPLIER_PERFORMANCE_CURRENT`
4. `ITEM_STORE_HEALTH`
5. `CATEGORY_STORE_DAY`
6. `MERCHANT_SCORECARD`
7. `MERCHANT_PROBLEMS`
8. `ROOT_CAUSE_EVIDENCE`

Intermediate tables use `TARGET_LAG = DOWNSTREAM`. The three consumer products use five minutes.
That makes the freshness contract explicit while avoiding independent refresh schedules at every
layer. An X-Small warehouse is sufficient for the tutorial's supplemental data; the TPC-DS baseline
scan remains the part to profile.

## Verification gates

### Before creation

Run the cohort gate before creating downstream objects:

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" -q "
  SELECT CHECK_NAME, STATUS, DETAIL
  FROM RETAIL_DEMO.CONFIG.COHORT_QUALIFICATION
  ORDER BY CHECK_NAME;
"
```

Require every cohort row to be `PASS`, plus the expected source counts: 5 suppliers, 500 purchase
orders, 500 receipts, 175 merchant-plan rows, and 3,500 sales plus 3,500 inventory events. Stop if
any source is missing or the cohort is not fully qualified.

### After Dynamic Table creation

Use the current metadata output rather than assuming that the configured refresh mode is the resolved
mode:

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" -q "
  SHOW DYNAMIC TABLES IN SCHEMA RETAIL_DEMO.ANALYTICS;
  SELECT \"name\", \"scheduling_state\", \"target_lag\", \"refresh_mode\"
  FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
  ORDER BY \"name\";
"
```

Require eight rows, `scheduling_state = ACTIVE`, five `DOWNSTREAM` intermediate target lags, three
five-minute serving target lags, and a successful refresh for every table:

```sql
SELECT NAME, STATE, STATE_CODE, REFRESH_ACTION, REFRESH_TRIGGER
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
  NAME_PREFIX => 'RETAIL_DEMO.ANALYTICS', RESULT_LIMIT => 50
))
ORDER BY REFRESH_START_TIME DESC;
```

The tutorial currently sets `REFRESH_MODE = AUTO`. In the validated workload, Snowflake resolved all
eight tables to `FULL` because the queries are complex and change tracking is not supported for those
full-refresh plans without a frozen region. Treat the resolved `SHOW DYNAMIC TABLES` value and refresh
history as the evidence; do not claim incremental refresh merely because the SQL says `AUTO`.

Require these initial row counts: `ITEM_STORE_BASELINE` 500, `ITEM_STORE_DAY` 3,500,
`SUPPLIER_PERFORMANCE_CURRENT` 500, `ITEM_STORE_HEALTH` 500, `CATEGORY_STORE_DAY` 175,
`MERCHANT_SCORECARD` 1, `MERCHANT_PROBLEMS` 24, and `ROOT_CAUSE_EVIDENCE` 24.

### After serving and readiness validation

Run the secure-view script and then:

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" -f sql/07_validation/01_demo_readiness.sql
snow sql -c "$SNOWFLAKE_CONNECTION" -f sql/07_validation/02_assert_readiness.sql
```

Require every readiness row to be `PASS` and `ASSERT_DEMO_READY()` to return
`PASS: all demo readiness checks succeeded`. The serving reconciliation must agree between
`MERCHANT_SCORECARD` and `MERCHANT_PROBLEMS`.

### Shutdown

After evidence capture, suspend all eight Dynamic Tables so their schedulers cannot request refresh
compute, then suspend the warehouse. Verify every Dynamic Table reports `SUSPENDED`, and verify
`RETAIL_DEMO_WH` reports `SUSPENDED`, X-Small, 60-second auto-suspend, 0 running, and 0 queued.
Suspension preserves the tables and views; it does not remove persistent Snowflake or S3 storage.

Ask CoCo to inspect refresh history and query profiles, not to change risk thresholds casually:

```text
Inspect the eight RETAIL_DEMO.ANALYTICS Dynamic Tables. Report refresh mode, last refresh status,
duration, bytes scanned, and dependency order. Explain any full refresh. Preserve the two-day risk
threshold and 0.80 supplier evidence threshold unless the scenario config and tests change together.
```

Validate health through Snowsight or the current Dynamic Tables monitoring functions. A target lag is
an objective, not a hard scheduler interval. Increase lag before increasing warehouse size when
freshness allows it.

The current syntax is documented in [CREATE DYNAMIC TABLE](https://docs.snowflake.com/en/sql-reference/sql/create-dynamic-table),
and Snowflake's [warehouse sizing guidance](https://docs.snowflake.com/en/user-guide/dynamic-tables/warehouse-selection)
explains the credit/freshness tradeoff.

Next: [merchant data products](09-merchant-data-products.md).
