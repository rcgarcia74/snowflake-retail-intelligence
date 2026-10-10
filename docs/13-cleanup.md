# 13 — Cleanup

Cleanup is split so an accidental command cannot silently erase Snowflake, S3, Openflow, and local
files together. Confirm each fixed target before running its step.

## 1. Stop compute first

Stop Openflow processors, suspend the tutorial runtime, stop Metabase, and suspend the warehouse.

```bash
docker compose --env-file .env -f metabase/docker-compose.yml down
snow sql -c "$SNOWFLAKE_CONNECTION" -q \
  'ALTER WAREHOUSE IF EXISTS RETAIL_DEMO_WH SUSPEND;'
```

Export any sanitized Openflow flow definition you intend to retain. Runtime-local flow state can be
lost when the runtime is removed.

## 2. Remove Openflow resources

Confirm all processors are stopped, every queue is empty, and `SHOW OPENFLOW CONNECTORS` returns no
unexpected connector objects. First inventory the fixed objects; this is read-only:

```bash
snow sql -c retail_demo_openflow_admin -q "
  SHOW OPENFLOW DEPLOYMENTS LIKE 'RETAIL_DEMO_OPENFLOW';
  SHOW OPENFLOW RUNTIMES LIKE 'RETAIL_DEMO_RUNTIME'
    IN SCHEMA RETAIL_DEMO_OPENFLOW_CONTROL.RUNTIME;
"
```

Then obtain explicit approval and use exactly one matching branch:

### Runtime exists

Run the full lifecycle script only when the runtime is present:

```bash
snow sql -c retail_demo_openflow_admin -f openflow/config/98_cleanup_objects.sql
```

### Deployment exists but runtime is absent

```bash
snow sql -c retail_demo_openflow_admin -q "
  ALTER OPENFLOW DEPLOYMENT RETAIL_DEMO_OPENFLOW TERMINATE;
  SELECT SYSTEM\$WAIT_FOR_STABLE_OPENFLOW_DEPLOYMENTS(900, 'RETAIL_DEMO_OPENFLOW');
  DROP OPENFLOW DEPLOYMENT RETAIL_DEMO_OPENFLOW;
  DROP EXTERNAL ACCESS INTEGRATION IF EXISTS RETAIL_DEMO_OPENFLOW_S3_EAI;
  DROP DATABASE IF EXISTS RETAIL_DEMO_OPENFLOW_CONTROL;
"
```

### Runtime and deployment are both absent

```bash
snow sql -c retail_demo_openflow_admin -q "
  DROP EXTERNAL ACCESS INTEGRATION IF EXISTS RETAIL_DEMO_OPENFLOW_S3_EAI;
  DROP DATABASE IF EXISTS RETAIL_DEMO_OPENFLOW_CONTROL;
"
```

After the selected branch succeeds, remove the two Openflow roles only if the tutorial will not be
restored:

```bash
snow sql -c retail_demo_admin -f openflow/config/99_cleanup.sql
```

The runtime-present branch performs the required Gen 2 runtime `SUSPEND → TERMINATE → DROP`
lifecycle before removing the deployment, EAI, and control database. The deployment-only branch
omits that impossible runtime lifecycle; the absent branch removes only retained control objects.
The final role script uses `ACCOUNTADMIN`. None of these branches delete target-table data or S3
objects.

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
