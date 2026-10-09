# 06 — Ingest operational files with Openflow

Use Openflow for the four low-frequency operational feeds. Do not route POS or inventory event files
through this flow; those demonstrate Snowpipe Streaming in the next step.

This is a custom process group on a Gen 2 Snowflake deployment/runtime, not a schema-level Gen 2
`OPENFLOW CONNECTOR` object. Follow the complete [Openflow runbook](../openflow/README.md); the summary
below does not replace its AWS trust-policy, controller-service, failure-queue, or rerun rules.

1. Verify that the four staged JSONL objects match `generated/manifest.json` and that the four target
   tables are empty.
2. With explicit approval, bootstrap the roles through the PAT-restricted administrative connection:

   ```bash
   snow sql -c retail_demo_admin \
     -f openflow/config/00_gen2_roles.sql \
     -D "openflow_user_name=YOUR_NON_ACCOUNTADMIN_OPENFLOW_USER"
   ```

3. Create a separate PAT restricted to `OPENFLOW_ADMIN`, store it outside the repository, and
   configure `retail_demo_openflow_admin` with an absolute token-file path. Role-restricted PAT
   sessions cannot switch roles or use secondary roles.
4. Through that connection and with explicit approval, create the control schema, WIF secret,
   S3/STS egress integration, and deployment. This phase does not create a runtime:

   ```bash
   snow sql -c retail_demo_openflow_admin \
     -f openflow/config/01_gen2_objects.sql \
     -D "aws_region=us-east-2"
   ```

5. Use the returned WIF issuer and subject to configure the AWS OIDC provider and the prefix-scoped,
   read-only IAM role. Do not store AWS keys in Openflow.
6. After the AWS trust exchange is configured and with explicit approval, create the S1/one-node
   runtime:

   ```bash
   snow sql -c retail_demo_openflow_admin -f openflow/config/02_gen2_runtime.sql
   ```

7. Build the custom process group from `openflow/config/flow-spec.yaml`. `JsonTreeReader` is a
   controller service shared by the four `PutDatabaseRecord` processors, not a processor in the flow.
   Apply the contract's `CLIENT_TIMESTAMP_TYPE_MAPPING = TIMESTAMP_NTZ` pre-processing SQL to every
   writer so JDBC preserves the source wall-clock timestamps.
8. Start the process group once. Require zero queued failures and exact row counts matching
   `generated/manifest.json`, then run:

   ```bash
   snow sql -c retail_demo_openflow_admin -f openflow/config/03_validate_load.sql
   ```

9. Stop the process group and suspend the runtime after evidence capture. Active runtimes consume
   credits.

The runtime's execute-as role has insert/select only on the four target tables. Openflow authenticates
to Snowflake with a Snowflake Managed Token. AWS access uses Snowflake workload identity federation
to obtain short-lived, read-only credentials.

Business-event dates remain anchored to the TPC-DS scenario clock. `INGESTED_AT` is the only wall-clock
field and is operational metadata. Because custom-flow exports can contain processor IDs, account
identifiers, and encrypted properties, the repository stores the semantic contract until a sanitized
versioned export has been inspected.

Next: [Snowpipe Streaming](07-snowpipe-streaming.md).
