# 02 — Snowflake setup

Snowflake CLI files use the standard `<% variable %>` template syntax. Review the rendered SQL and
execute only trusted repository files.

## 1. Bootstrap the workspace

Generate a dedicated unencrypted PKCS #8 key pair for the Metabase service user. The private key
stays outside the repository and is never passed to Snowflake:

```bash
mkdir -p "$HOME/.snowflake/keys"
umask 077
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -outform PEM \
  -out "$HOME/.snowflake/keys/retail_demo_metabase.p8" -nocrypt
openssl pkey -in "$HOME/.snowflake/keys/retail_demo_metabase.p8" -pubout \
  -out "$HOME/.snowflake/keys/retail_demo_metabase.pub"
chmod 600 "$HOME/.snowflake/keys/retail_demo_metabase.p8"
METABASE_RSA_PUBLIC_KEY="$(sed -e '1d' -e '$d' \
  "$HOME/.snowflake/keys/retail_demo_metabase.pub" | tr -d '\n')"
test -n "$METABASE_RSA_PUBLIC_KEY"
```

The final test must succeed. The shell variable contains only the public key; do not print the
private key or commit either file.

```bash
snow sql -c retail_demo_admin \
  -f sql/00_setup/00_bootstrap.sql \
  -D "user_name=YOUR_ENGINEERING_USER" \
  -D "metabase_user_name=RETAIL_DEMO_METABASE_USER" \
  -D "metabase_rsa_public_key=$METABASE_RSA_PUBLIC_KEY"
```

The script creates an X-Small, 60-second auto-suspend warehouse, a 25-credit resource monitor,
`RETAIL_DEMO`, seven schemas, an engineering role, a read-only BI role, and a dedicated key-pair
`TYPE=SERVICE` user for Metabase. The engineering user must already exist. If users are provisioned
by identity automation, replace the user creation and role grants with your normal process while
preserving the dedicated-user and least-privilege boundaries.

## 2. Create the S3 integrations

```bash
snow sql -c retail_demo_admin \
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
snow sql -c retail_demo \
  -f sql/00_setup/02_stage_objects.sql \
  -D "s3_landing_url=s3://$S3_BUCKET/$S3_ROOT/landing/"
```

Never use inline AWS credentials in `CREATE STAGE`. Validate the storage integration against a
throwaway path if your administrator permits `SYSTEM$VALIDATE_STORAGE_INTEGRATION`.

## 3. Create native raw tables

```bash
snow sql -c retail_demo -f sql/02_raw/01_raw_tables.sql
```

Do not create Dynamic Tables yet. Their first initialization should happen only after source
ingestion is complete.

The external volume follows Snowflake's current [S3 external-volume syntax](https://docs.snowflake.com/en/sql-reference/sql/create-external-volume),
and the stage uses a [storage integration](https://docs.snowflake.com/en/user-guide/data-load-s3-config-storage-integration).

Next: [select the TPC-DS cohort](03-tpcds-cohort.md).
