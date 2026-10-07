# 05 — Upload history and create Iceberg tables

## 0. Load and verify repository environment

Do not rely on inherited shell variables from another project.

```bash
set -a
source .env
set +a

printf 'S3_BUCKET=%s\nS3_ROOT=%s\nSNOWFLAKE_CONNECTION=%s\n' \
  "$S3_BUCKET" "$S3_ROOT" "$SNOWFLAKE_CONNECTION"

test "$S3_BUCKET" = "snowflake-retail-demo-rommelg" || {
  echo "ERROR: unexpected S3_BUCKET: $S3_BUCKET"
  exit 1
}

test "$S3_ROOT" = "retail-demo" || {
  echo "ERROR: unexpected S3_ROOT: $S3_ROOT"
  exit 1
}

test "$SNOWFLAKE_CONNECTION" = "retail_demo" || {
  echo "ERROR: unexpected SNOWFLAKE_CONNECTION: $SNOWFLAKE_CONNECTION"
  exit 1
}
```

Expected:

```text
S3_BUCKET=snowflake-retail-demo-rommelg
S3_ROOT=retail-demo
SNOWFLAKE_CONNECTION=retail_demo
```

Do not continue if any value differs.

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

Before executing the DDL, verify the external volume and review the SQL.

### 2.1 Verify the external-volume trust relationship

The storage integration and external volume are separate Snowflake-to-AWS trust relationships. Do not assume they use the same Snowflake IAM principal or external ID.

For `RETAIL_DEMO_EXT_VOL`, the AWS `SnowflakeExternalVolume` trust statement must match the current values returned by:

```sql
DESC EXTERNAL VOLUME RETAIL_DEMO_EXT_VOL;
```

Specifically verify:

- `STORAGE_AWS_IAM_USER_ARN` matches the AWS trust-policy `Principal.AWS`.
- `STORAGE_AWS_EXTERNAL_ID` matches the AWS trust-policy `sts:ExternalId`.
- The trust statement allows `sts:AssumeRole` on `SnowflakeRetailDemoRole`.

Do not copy the storage integration's external ID into the external-volume trust statement.

After the AWS trust policy is configured, verify Snowflake can use the external volume:

```bash
snow sql -c retail_demo_admin \
  -q "SELECT SYSTEM\$VERIFY_EXTERNAL_VOLUME('RETAIL_DEMO_EXT_VOL');"
```

Do not continue unless the result reports `"success": true` and the storage-location, write, read, list, delete, and AWS-role validation checks pass.

### 2.2 Review the Iceberg DDL

Ask CoCo to **review only** `sql/03_iceberg/01_create_iceberg_tables.sql`. Do not ask CoCo to execute the script.

Confirm that:

- Integer Iceberg columns and casts use explicit precision and scale, such as `NUMBER(38,0)`.
- No bare `NUMBER` or `DECIMAL` types remain in the Iceberg table definitions or load casts.
- Decimal measures retain their intended explicit precision and scale.
- All three tables use `CATALOG = 'SNOWFLAKE'`.
- Each table has a distinct `BASE_LOCATION`.
- `COPY INTO` reads only from the S3 landing stage.
- Raw source files are never written directly into the Iceberg-owned prefix.
- `FORCE = TRUE` is not used.

CoCo review is an engineering aid, not an execution or compatibility gate. Snowflake execution is authoritative.

### 2.3 Create and load the Iceberg tables

Execute the script with the engineer connection (`retail_demo`), not the role-restricted admin connection:

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" \
  -f sql/03_iceberg/01_create_iceberg_tables.sql \
  -D "external_volume=RETAIL_DEMO_EXT_VOL"
```

The DDL sets `CATALOG = 'SNOWFLAKE'` and a distinct `BASE_LOCATION` for each table. `COPY INTO`
reads the landing Parquet; Snowflake writes the managed Iceberg metadata and Parquet to the external
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
