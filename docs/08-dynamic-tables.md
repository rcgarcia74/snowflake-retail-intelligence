# 08 — Build Dynamic Tables

Create the pipeline after historical, Openflow, and healthy-checkpoint event data is present:

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" -f sql/05_dynamic_tables/01_dynamic_tables.sql
snow sql -c "$SNOWFLAKE_CONNECTION" -f sql/06_serving/01_serving_views.sql
```

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
