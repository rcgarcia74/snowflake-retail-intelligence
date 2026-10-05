# 02 — Snowflake setup

Snowflake CLI files use the standard `<% variable %>` template syntax. Review the rendered SQL and
execute only trusted repository files.

## 1. Bootstrap the workspace

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" \
  -f sql/00_setup/00_bootstrap.sql \
  -D "user_name=YOUR_ENGINEERING_USER" \
  -D "metabase_user_name=YOUR_METABASE_USER"
```

The script creates an X-Small, 60-second auto-suspend warehouse, a 25-credit resource monitor,
`RETAIL_DEMO`, seven schemas, an engineering role, and a read-only BI role. If users are provisioned
by identity automation, replace the two user grants with your normal role-assignment process.

## 2. Create the S3 integrations

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" \
  -f sql/00_setup/01_storage_integrations.sql \
  -D "aws_role_arn=$AWS_ICEBERG_ROLE_ARN" \
  -D "s3_landing_url=s3://$S3_BUCKET/$S3_ROOT/landing/" \
  -D "s3_iceberg_url=s3://$S3_BUCKET/$S3_ROOT/iceberg/"
```

Stop after `DESCRIBE`. Add the returned Snowflake IAM principals and external IDs to the AWS role's
trust policy, while preserving the prefix-scoped permissions. Then create and test the stage:

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" \
  -f sql/00_setup/02_stage_objects.sql \
  -D "s3_landing_url=s3://$S3_BUCKET/$S3_ROOT/landing/"
```

Never use inline AWS credentials in `CREATE STAGE`. Validate the storage integration against a
throwaway path if your administrator permits `SYSTEM$VALIDATE_STORAGE_INTEGRATION`.

## 3. Create native raw tables

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" -f sql/02_raw/01_raw_tables.sql
```

Do not create Dynamic Tables yet. Their first initialization should happen only after source
ingestion is complete.

The external volume follows Snowflake's current [S3 external-volume syntax](https://docs.snowflake.com/en/sql-reference/sql/create-external-volume),
and the stage uses a [storage integration](https://docs.snowflake.com/en/user-guide/data-load-s3-config-storage-integration).

Next: [select the TPC-DS cohort](03-tpcds-cohort.md).
