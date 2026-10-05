# 13 — Cleanup

Cleanup is split so an accidental command cannot silently erase Snowflake, S3, Openflow, and local
files together. Confirm each fixed target before running its step.

## 1. Stop compute first

Stop Openflow processors, suspend the tutorial runtime, stop Metabase, and suspend the warehouse.

```bash
docker compose -f metabase/docker-compose.yml down
snow sql -c "$SNOWFLAKE_CONNECTION" -q \
  'ALTER WAREHOUSE IF EXISTS RETAIL_DEMO_WH SUSPEND;'
```

Export any sanitized Openflow flow definition you intend to retain. Runtime-local flow state can be
lost when the runtime is removed.

## 2. Remove Openflow resources

Review and run the fixed-name script:

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" -f openflow/config/99_cleanup.sql
```

Remove the tutorial's S3 external access integration separately only if no other runtime uses it.

## 3. Remove Snowflake objects

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" -f sql/99_cleanup/01_cleanup.sql
```

This drops only fixed `RETAIL_DEMO*` objects. Snowflake must drop Iceberg tables before the external
volume can be removed; dropping the database first satisfies that dependency.

## 4. Remove S3 objects explicitly

List both prefixes and verify the bucket and account before deletion:

```bash
aws s3 ls "s3://$S3_BUCKET/$S3_ROOT/" --recursive --summarize
aws s3 rm "s3://$S3_BUCKET/$S3_ROOT/landing/" --recursive
aws s3 rm "s3://$S3_BUCKET/$S3_ROOT/iceberg/" --recursive
```

Delete the dedicated IAM role and bucket only if they were created solely for this tutorial. If
versioning is enabled, delete markers do not remove older billable versions; follow your AWS retention
policy.

## 5. Remove local generated files

```bash
python scripts/clean_local.py --output generated --yes
```

The local cleanup script refuses paths outside the repository and directory names other than
`generated` or `build`. Remove `data/cohort/`, the ignored streaming profile, private-key references,
and `metabase/metabase-data/` manually after verifying they are no longer needed.
