# Openflow ingestion

Openflow ingests four low-frequency operational feeds—supplier, current purchase order, receipt,
and merchant plan—from S3 JSONL files. POS and inventory events use the separate Snowpipe Streaming
producer. Keeping those paths distinct gives each service a credible job.

All new deployments use gen 2 objects. Deployment and runtime objects are generally available;
connector configuration and some setup surfaces may still be preview features in your region. Check
the [gen 2 quickstart](https://docs.snowflake.com/en/user-guide/data-integration/openflow/gen2/quickstart)
before running this section.

## Build

1. Create an S3 external access integration for the bucket endpoint, and grant its `USAGE` to the
   fixed execute-as role. Prefer workload identity; otherwise reference an external secret. Do not
   store AWS keys in the flow.
2. Create the gen 2 deployment and single-node S1 runtime with `01_gen2_objects.sql`.
3. Upload `generated/openflow/` to `s3://<bucket>/retail-demo/landing/openflow/`.
4. Use `flow-spec.yaml` as the checked-in contract and the CoCo prompt as the implementation aid.
   Create a versioned custom process group in the Openflow canvas with:

   ```text
   ListS3 -> FetchS3Object -> RouteOnAttribute -> JsonTreeReader -> PutDatabaseRecord
   ```

5. Bind the four routes to the exact target tables. Use `SNOWFLAKE_MANAGED` authentication.
6. Confirm the raw tables are empty, start the process group, and monitor queues and bulletins.
7. Stop the process group when all four files have succeeded; then run:

   ```sql
   SELECT 'SUPPLIER', COUNT(*) FROM RETAIL_DEMO.RAW.SUPPLIER
   UNION ALL SELECT 'PURCHASE_ORDER', COUNT(*) FROM RETAIL_DEMO.RAW.PURCHASE_ORDER
   UNION ALL SELECT 'RECEIPT', COUNT(*) FROM RETAIL_DEMO.RAW.RECEIPT
   UNION ALL SELECT 'MERCHANT_PLAN', COUNT(*) FROM RETAIL_DEMO.RAW.MERCHANT_PLAN;
   ```

The flow is intentionally not exported with processor IDs or encrypted properties: those are tied to
a specific Openflow runtime/version and can accidentally carry environment details. The YAML contract
and versioned flow in your runtime remain the reproducible sources. Export a sanitized flow only if
you can prove it contains no controller-service secrets or account identifiers.

The processor choices are documented in Snowflake's [Openflow processor reference](https://docs.snowflake.com/en/user-guide/data-integration/openflow/processors/index),
including `ListS3`, `FetchS3Object`, and `PutDatabaseRecord`.
