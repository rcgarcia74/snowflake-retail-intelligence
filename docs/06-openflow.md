# 06 — Ingest operational files with Openflow

Use Openflow for the four low-frequency operational feeds. Do not route POS or inventory event files
through this flow; those demonstrate Snowpipe Streaming in the next step.

1. Read [openflow/README.md](../openflow/README.md) and create the S3 external access integration.
2. Create the single-node gen 2 runtime:

   ```bash
   snow sql -c "$SNOWFLAKE_CONNECTION" \
     -f openflow/config/01_gen2_objects.sql \
     -D "openflow_user_name=YOUR_OPENFLOW_USER" \
     -D "s3_eai=YOUR_S3_EXTERNAL_ACCESS_INTEGRATION"
   ```

3. Build the versioned flow from `openflow/config/flow-spec.yaml`; the checked-in CoCo prompt is an
   optional implementation aid.
4. Verify that the four raw tables are empty. Start the flow once.
5. Require zero queued failures and exact row counts matching `generated/manifest.json`.
6. Stop the process group. An active runtime consumes credits; suspend it between build sessions.

The runtime's execute-as role has insert/select only on the four target tables. Openflow authenticates
to Snowflake with managed short-lived credentials. AWS access must use workload identity or a
secret-backed credentials provider.

Because Openflow connector/configuration capabilities can change, the repository stores a semantic
flow contract and not an environment-bound flow export containing processor IDs and encrypted
properties. Reconcile the contract with the current [processor reference](https://docs.snowflake.com/en/user-guide/data-integration/openflow/processors/index).

Next: [Snowpipe Streaming](07-snowpipe-streaming.md).
