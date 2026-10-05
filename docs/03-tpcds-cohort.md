# 03 — Select and export the TPC-DS cohort

This is the one intentionally large TPC-DS scan. Use CoCo to inspect the SQL and query profile, but
keep the deterministic selection logic in version control.

Suggested CoCo prompt:

```text
Review sql/01_cohort/01_select_cohort.sql against TPCDS_SF10TCL. Confirm it selects one category,
20 items, 25 stores, an 84-day baseline, and at least 100 observed item/store pairs. Estimate bytes
scanned before execution, use RETAIL_DEMO_WH, and do not change the output contract. Execute it only
after showing the exact SQL and stop if any COHORT_QUALIFICATION row fails.
```

Run the selection:

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" -f sql/01_cohort/01_select_cohort.sql
```

Inspect the gate separately:

```sql
SELECT *
FROM RETAIL_DEMO.CONFIG.COHORT_QUALIFICATION
ORDER BY CHECK_NAME;
```

Every row must be `PASS`. A failure means the actual TPC-DS slice is too sparse for the configured
scenario; adjust the documented selection criteria and rerun rather than fabricating keys.

## Export

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" -f sql/01_cohort/02_export_cohort.sql
mkdir -p data/cohort
aws s3 cp "s3://$S3_BUCKET/$S3_ROOT/landing/cohort/" data/cohort/ \
  --recursive --exclude "*" --include "*.parquet"
python scripts/prepare_cohort.py data/cohort
```

The resulting local contract is:

```text
data/cohort/
├── scenario.json
├── scenario.parquet
├── items.parquet
├── stores.parquet
└── item_store_baseline.parquet
```

`data/` is ignored by Git. Check the four required generator files locally, then continue to
[data generation](04-data-generation.md).
