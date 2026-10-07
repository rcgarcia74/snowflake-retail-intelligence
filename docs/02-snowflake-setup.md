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

Stop after `DESCRIBE`. The storage integration and external volume establish **separate AWS trust
relationships**, even when they use the same AWS IAM role.

From the setup-script output, record the trust values for each object separately:

- `RETAIL_DEMO_S3_INTEGRATION`: its Snowflake IAM principal and external ID.
- `RETAIL_DEMO_EXT_VOL`: its Snowflake IAM principal and external ID.

Configure the AWS role `SnowflakeRetailDemoRole` with separate trust-policy statements for the
storage integration and external volume. For each statement:

- `Principal.AWS` must exactly match that object's current Snowflake IAM principal.
- `sts:ExternalId` must exactly match that object's current Snowflake external ID.
- `Action` must allow `sts:AssumeRole`.

Do not reuse the storage integration's external ID for the external volume. Snowflake can generate
different principals and external IDs for these objects, and the AWS trust policy must match the
values currently returned by Snowflake.

After updating the AWS trust policy, verify the external volume before attempting to create Iceberg
tables:

```bash
snow sql -c retail_demo_admin \
  -q "SELECT SYSTEM\$VERIFY_EXTERNAL_VOLUME('RETAIL_DEMO_EXT_VOL');"
```

Do not continue unless the result reports `"success": true` and the storage-location, write, read,
list, delete, and AWS-role validation checks pass.

Then create and test the landing stage:

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
