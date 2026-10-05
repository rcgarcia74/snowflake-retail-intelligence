# 05 — Upload history and create Iceberg tables

## 1. Upload only validated files

```bash
test "$(python -c 'import json; print(json.load(open("generated/validation_report.json"))["status"])')" = PASS

aws s3 sync generated/history/ \
  "s3://$S3_BUCKET/$S3_ROOT/landing/history/" \
  --exclude "*" --include "*.parquet" --sse AES256 --no-progress

aws s3 sync generated/openflow/ \
  "s3://$S3_BUCKET/$S3_ROOT/landing/openflow/" \
  --exclude "*" --include "*.jsonl" --sse AES256 --no-progress
```

List and compare object counts and byte totals. Do not sync anything to `iceberg/`.

## 2. Create and load Snowflake-managed Iceberg

Ask CoCo to review column casts and external-volume access, then run:

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" \
  -f sql/03_iceberg/01_create_iceberg_tables.sql \
  -D "external_volume=RETAIL_DEMO_EXT_VOL"
```

The DDL sets `CATALOG = 'SNOWFLAKE'` and a distinct `BASE_LOCATION` for each table. `COPY INTO`
reads the landing Parquet; Snowflake writes valid Iceberg metadata and Parquet to the external
volume.

## 3. Verify

```sql
SHOW ICEBERG TABLES IN SCHEMA RETAIL_DEMO.LAKEHOUSE;

SELECT 'INVENTORY_HISTORY', COUNT(*), MIN(SNAPSHOT_DATE), MAX(SNAPSHOT_DATE)
FROM RETAIL_DEMO.LAKEHOUSE.INVENTORY_HISTORY
UNION ALL
SELECT 'PURCHASE_ORDER_HISTORY', COUNT(*), MIN(ORDER_DATE), MAX(ORDER_DATE)
FROM RETAIL_DEMO.LAKEHOUSE.PURCHASE_ORDER_HISTORY
UNION ALL
SELECT 'SUPPLIER_PERFORMANCE_HISTORY', COUNT(*), MIN(PERFORMANCE_DATE), MAX(PERFORMANCE_DATE)
FROM RETAIL_DEMO.LAKEHOUSE.SUPPLIER_PERFORMANCE_HISTORY;
```

Inventory and supplier history must span exactly 90 dates. Re-running `COPY INTO` without `FORCE`
uses load history to avoid reloading the same files; do not use `FORCE = TRUE` as a reset strategy.

Snowflake's [first Iceberg table tutorial](https://docs.snowflake.com/en/user-guide/tutorials/create-your-first-iceberg-table)
shows the same Snowflake-catalog/external-volume pattern.

Next: [Openflow](06-openflow.md).
