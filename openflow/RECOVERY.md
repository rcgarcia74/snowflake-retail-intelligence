# Openflow recovery and live-demo restoration

Use this runbook only after the one-time load in `README.md` has passed. The exported custom flow is
a recovery artifact, not a replay-safe ingestion package: its `ListS3` state can be absent after
import, and the four Snowflake targets use insert-only writes with unenforced primary keys.

Current Snowflake documentation says a deployment alone has no separate charge and active runtimes
consume credits. Account billing evidence remains authoritative, so this tutorial's cost-safe state
removes both the runtime and deployment between demonstrations while retaining the WIF secret,
external access integration, roles, loaded data, and private recovery bundle.

## 1. Create the private recovery bundle before removal

Set an absolute directory outside the repository. Never put the export or live parameter values in
Git:

```bash
RECOVERY_DIR="$HOME/.snowflake/recovery/retail-demo-$(date +%F)"
mkdir -p "$RECOVERY_DIR"/{canvas,private-parameters,snowflake,evidence,repository}
chmod 700 "$RECOVERY_DIR" "$RECOVERY_DIR"/*
```

Capture these items without recording PATs, private keys, AWS credentials, or WIF token values:

1. Stop all seven processors and require all 12 queues to show `0 FlowFiles / 0 bytes`.
2. Record the process-group name, parameter-context name, five controller-service names and types,
   seven processor names and states, 12 connection relationships, and runtime/deployment
   descriptions.
3. Copy the 12 non-secret parameter names and their current values into
   `private-parameters/live-parameters.yaml`. Restrict it to mode `600`.
4. Disable all five controller services. Openflow blocks component-state export while a referenced
   service is enabled.
5. Select `Retail Staged Feeds`, use its **Manage assets** action to export/download the flow
   definition, and save it as `canvas/Retail_Staged_Feeds.json`. UI labels can change; do not choose
   Delete or clear component state.
6. Copy the fixed repository contracts listed in `evidence/repository-checksums.sha256` into the
   bundle's `repository/` tree. They are the recovery-time reference, not a substitute for reviewing
   the current checkout.

Create and verify checksums from inside the bundle:

```bash
cd "$RECOVERY_DIR"
shasum -a 256 canvas/Retail_Staged_Feeds.json > evidence/flow-export.sha256
find canvas private-parameters snowflake repository -type f -print0 \
  | sort -z \
  | xargs -0 shasum -a 256 > evidence/bundle-checksums.sha256
shasum -a 256 -c evidence/flow-export.sha256
shasum -a 256 -c evidence/bundle-checksums.sha256
```

Every line must end in `OK`. Keep the bundle until a restoration has reached the stopped-flow gate
below.

## 2. Choose the restoration mode before creating compute

Choose exactly one mode:

- **Evidence-only repeat demonstration:** restore the canvas stopped, show the flow plus preserved
  Snowflake load evidence, and never start the process group. This is the normal repeat-demo path.
- **Clean first load:** start the process group once only when all four target tables are empty and
  the four S3 source objects match `generated/manifest.json`.

If the targets already contain 5 suppliers, 500 purchase orders, 500 receipts, and 175 merchant-plan
rows, the clean-first-load precondition is false. Do not truncate, delete, or reload them merely to
demonstrate restoration.

## 3. Verify the bundle and retained objects

```bash
cd "$RECOVERY_DIR"
shasum -a 256 -c evidence/flow-export.sha256
shasum -a 256 -c evidence/bundle-checksums.sha256
```

Then use the role-restricted connections for read-only inventory:

```bash
snow sql -c retail_demo_openflow_admin -q "
  SHOW OPENFLOW DEPLOYMENTS LIKE 'RETAIL_DEMO_OPENFLOW';
  SHOW OPENFLOW RUNTIMES LIKE 'RETAIL_DEMO_RUNTIME'
    IN SCHEMA RETAIL_DEMO_OPENFLOW_CONTROL.RUNTIME;
  DESC SECRET RETAIL_DEMO_OPENFLOW_CONTROL.RUNTIME.RETAIL_DEMO_AWS_WIF;
  DESC EXTERNAL ACCESS INTEGRATION RETAIL_DEMO_OPENFLOW_S3_EAI;
"
snow sql -c retail_demo_openflow_admin -f openflow/config/03_validate_load.sql
```

For the evidence-only path, the load gate must still return 15 `PASS` rows before restoration. Do
not copy the WIF issuer or subject into committed files.

## 4. Recreate the deployment and revalidate AWS trust

Obtain explicit approval before any live mutation. Re-run phase 1; its `IF NOT EXISTS` clauses keep
the retained WIF secret and EAI while recreating the absent deployment:

```bash
snow sql -c retail_demo_openflow_admin \
  -f openflow/config/01_gen2_objects.sql \
  -D "aws_region=$AWS_REGION"
```

Require the deployment wait to return `TRUE`. Compare the retained secret's issuer and subject with
the AWS OIDC provider and IAM role trust policy. Require exact `sub` and `aud` matches, the expected
provider-path prefixes, audience `snowflake`, and the prefix-scoped read-only S3 policy. If the IAM
trust policy uses `sf_rnm`, its value must be `OPENFLOW_RETAIL_DEMO_EXECUTE_AS_RL`. Stop if the WIF
subject changed or any comparison fails.

## 5. Create the billable runtime

This step starts S1/one-node compute and requires separate explicit approval:

```bash
snow sql -c retail_demo_openflow_admin -f openflow/config/02_gen2_runtime.sql
```

Require `RETAIL_DEMO_OPENFLOW_CONTROL.RUNTIME.RETAIL_DEMO_RUNTIME` to reach `ACTIVE` with deployment
`RETAIL_DEMO_OPENFLOW`, node type/tier `SMALL`/`S1`, one minimum and maximum node, execute-as role
`OPENFLOW_RETAIL_DEMO_EXECUTE_AS_RL`, and `RETAIL_DEMO_OPENFLOW_S3_EAI` attached.

## 6. Import and bind the stopped flow

1. Launch the runtime canvas and use the canvas **Upload flow definition** / import control to upload
   `canvas/Retail_Staged_Feeds.json`. If the current UI nests import under **Manage assets**, use that
   action. Stop if the only visible action would overwrite or delete another process group.
2. Open **Edit process group → Settings** for `Retail Staged Feeds`. Create or select parameter
   context `Retail Demo Openflow`; the current UI labels this tab **Settings**, not **General**.
3. Enter exactly the 12 values from `private-parameters/live-parameters.yaml`, apply them
   recursively, and compare names and values without displaying them publicly. Require no unexpected
   parameters and no unresolved placeholders.
4. Keep every processor stopped. Imported controller services must remain disabled until their
   properties are reviewed against the private inventory.
5. Verify and enable controller services in dependency order:
   `RetailDemoSnowflakeConnection`, `RetailDemoSnowflakeWifToken`,
   `RetailDemoAwsCredentials`, `RetailDemoSchemaCache`, then `RetailDemoJsonReader`.
6. Recheck all seven processors, all 12 relationships and connection limits, timestamp
   pre-processing SQL, failure routing, and `0 FlowFiles / 0 bytes` in every queue.

The stopped-flow gate passes only when the parameter context has 12 expected values, all five
controller services are valid, all seven processors are valid and stopped, and all queues are empty.

## 7. Demonstrate without duplicating data

For an evidence-only repeat demonstration, do not start the flow. Show:

- the valid stopped canvas and empty queues;
- the verified export and repository checksums;
- the 15 passing rows from `03_validate_load.sql`; and
- the expected target counts already present in Snowflake.

For a clean first load only, repeat every precondition and execution gate in `README.md` sections 1
and 7. Any nonempty target, changed S3 object, invalid component, or queued FlowFile is a stop
condition.

## 8. Roll back to the cost-safe state

Stop processors, require empty queues, disable controller services, and export/checksum a new flow
only if an approved configuration changed. Then follow `docs/13-cleanup.md` to remove the runtime and
deployment while preserving the retained recovery objects. Confirm `RETAIL_DEMO_WH` is suspended,
`AUTO_RESUME = FALSE`, and no Openflow runtime remains active.

References: [Gen 2 runtime lifecycle](https://docs.snowflake.com/en/user-guide/data-integration/openflow/gen2/openflow-generations),
[WIF for Openflow](https://docs.snowflake.com/en/user-guide/data-integration/openflow/security/workload-identity-federation),
and [custom-flow version control](https://docs.snowflake.com/en/user-guide/data-integration/openflow/version-control-custom-flows).
