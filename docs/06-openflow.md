# 06 — Ingest operational files with Openflow

Use Openflow for the four low-frequency operational feeds. Do not route POS or inventory event files
through this flow; those demonstrate Snowpipe Streaming in the next step.

This is a custom process group on a Gen 2 Snowflake deployment/runtime, not a schema-level Gen 2
`OPENFLOW CONNECTOR` object. Follow the complete [Openflow runbook](../openflow/README.md); the summary
below does not replace its AWS trust-policy, controller-service, failure-queue, or rerun rules.

1. Verify that the four staged JSONL objects match `generated/manifest.json` and that the four target
   tables are empty.

   **Verification:** Require exactly four expected S3 keys, matching manifest sizes and row counts,
   and `0` rows in every target table. Stop on any mismatch or preexisting row.

2. With explicit approval, bootstrap the roles through the PAT-restricted administrative connection:

   ```bash
   snow sql -c retail_demo_admin \
     -f openflow/config/00_gen2_roles.sql \
     -D "openflow_user_name=YOUR_NON_ACCOUNTADMIN_OPENFLOW_USER"
   ```

   **Verification:** Inspect the grants. `OPENFLOW_ADMIN` must have the documented account creation
   privileges; the execute-as role must have database/schema usage, warehouse usage/operate, and
   insert/select on only the four target tables. No Openflow runtime exists or consumes compute yet.

3. Create a separate PAT restricted to `OPENFLOW_ADMIN`, store it outside the repository, and
   configure `retail_demo_openflow_admin` with an absolute token-file path. Role-restricted PAT
   sessions cannot switch roles or use secondary roles.

   **Verification:** `snow connection test -c retail_demo_openflow_admin` must succeed as
   `OPENFLOW_ADMIN` without printing the PAT. Stop if the PAT is unrestricted or appears in output,
   shell history, or a repository file.

4. Through that connection and with explicit approval, create the control schema, WIF secret,
   S3/STS egress integration, and deployment. This phase does not create a runtime:

   ```bash
   snow sql -c retail_demo_openflow_admin \
     -f openflow/config/01_gen2_objects.sql \
     -D "aws_region=us-east-2"
   ```

   **Verification:** The deployment wait must return `TRUE`; the deployment must be active; and the
   final WIF secret must return nonempty issuer and subject values. No Openflow runtime exists yet.

5. Use the returned WIF issuer and subject to configure the AWS OIDC provider and the prefix-scoped,
   read-only IAM role. Do not store AWS keys in Openflow.

   **Verification:** Require the exact provider ARN and host/path on all three trust keys, plus the
   final WIF `sub`, `aud = snowflake`, and
   `sf_rnm = OPENFLOW_RETAIL_DEMO_EXECUTE_AS_RL`. The attached policy must permit only prefix-scoped
   `ListBucket` and `GetObject`; the first `ListS3` run is the end-to-end STS test.

6. After the AWS trust exchange is configured and with explicit approval, create the S1/one-node
   runtime:

   ```bash
   snow sql -c retail_demo_openflow_admin -f openflow/config/02_gen2_runtime.sql
   ```

   **Verification:** The runtime wait must return `TRUE`, and its description must show `SMALL`/`S1`,
   one minimum and maximum node, the expected execute-as role, and the S3 external-access integration.
   The active runtime is now billable; suspend it if canvas work will not continue immediately.

7. Build the custom process group from `openflow/config/flow-spec.yaml`. `JsonTreeReader` is a
   controller service shared by the four `PutDatabaseRecord` processors, not a processor in the flow.
   Apply the contract's `CLIENT_TIMESTAMP_TYPE_MAPPING = TIMESTAMP_NTZ` pre-processing SQL to every
   writer so JDBC preserves the source wall-clock timestamps.

   **Verification:** Require five enabled/valid controller services, seven valid/stopped processors,
   all 12 contract connections, no unresolved placeholders, and every queue at
   `0 FlowFiles / 0 bytes` before starting.

8. Start the process group once. Require zero queued failures and exact row counts matching
   `generated/manifest.json`, then run:

   ```bash
   snow sql -c retail_demo_openflow_admin -f openflow/config/03_validate_load.sql
   ```

   **Verification:** Require 15 `PASS` rows: four feed counts, PO/receipt reconciliation, seven
   scenario-clock checks, and three timestamp-fidelity checks. The expected counts are 5, 500, 500,
   and 175, with 500 matched receipts and 0 missing.

9. Stop the process group and suspend the runtime after evidence capture. Active runtimes consume
   credits.

   **Verification:** Require seven stopped processors, all 12 queues empty, runtime status
   `SUSPENDED`, and warehouse state `SUSPENDED` with 0 running/queued queries. Persistent Snowflake
   tables and S3 files can still incur storage charges.

The runtime's execute-as role has insert/select only on the four target tables. Openflow authenticates
to Snowflake with a Snowflake Managed Token. AWS access uses Snowflake workload identity federation
to obtain short-lived, read-only credentials.

Business-event dates remain anchored to the TPC-DS scenario clock. `INGESTED_AT` is the only wall-clock
field and is operational metadata. Because custom-flow exports can contain processor IDs, account
identifiers, and encrypted properties, the repository stores the semantic contract until a sanitized
versioned export has been inspected.

Next: [Snowpipe Streaming](07-snowpipe-streaming.md).
