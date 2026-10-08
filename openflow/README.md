# Openflow ingestion

Openflow ingests four low-frequency staged feeds—supplier, current purchase order, receipt, and
merchant plan—from S3 JSONL files. POS and inventory events remain on the completed Snowpipe
Streaming path. Do not add those event tables to this flow.

This implementation uses a **Gen 2 Snowflake deployment and runtime** with a custom process group on
the runtime canvas. The custom process group is not a schema-level Gen 2 `OPENFLOW CONNECTOR` object.
Gen 2 deployment/runtime SQL is generally available; Gen 2 connector-object configuration remains
Public Preview and is not required here. The product model was rechecked against Snowflake's
[Gen 2 quickstart](https://docs.snowflake.com/en/user-guide/data-integration/openflow/gen2/quickstart)
and [generation comparison](https://docs.snowflake.com/en/user-guide/data-integration/openflow/gen2/openflow-generations).

## Safety and current limitations

- `00_gen2_roles.sql` bootstraps privileges through `ACCOUNTADMIN`; `01_gen2_objects.sql` creates
  account objects and a deployment through `OPENFLOW_ADMIN`; `02_gen2_runtime.sql` starts an S1
  runtime that consumes credits. Run none of them without reviewing the active connection and role.
- A Snowflake external access integration controls network egress; it does not authenticate to AWS.
  This runbook uses workload identity federation (WIF) for short-lived AWS credentials and stores no
  AWS access key.
- The flow is an insert-only, one-time empty-table load. `ListS3` tracking prevents normal relisting,
  but clearing processor state or replacing source objects can cause duplicates. Snowflake standard
  table primary keys are not enforced.
- Each account can have at most three Snowflake Openflow deployments across generations. An active
  runtime consumes credits; suspend it after validation.
- A runtime user whose default role is `ACCOUNTADMIN` cannot log in to the runtime canvas. Use a user
  with a non-`ACCOUNTADMIN` default role and `DEFAULT_SECONDARY_ROLES = ('ALL')`.

## 1. Confirm the inputs without changing cloud state

The four target tables must exist and be empty. The S3 prefix must contain exactly these objects:

```text
retail-demo/landing/openflow/supplier/supplier.jsonl
retail-demo/landing/openflow/current_purchase_orders/purchase_orders.jsonl
retail-demo/landing/openflow/current_receipts/receipts.jsonl
retail-demo/landing/openflow/merchant_plan/merchant_plan.jsonl
```

Compare object sizes and row counts to `generated/manifest.json`. Do not continue if the target tables
contain rows or if the staged files differ from the validated local files.

## 2. Bootstrap the Openflow roles

Run only the role bootstrap through the administrative connection and only after approval:

```bash
snow sql -c retail_demo_admin \
  -f openflow/config/00_gen2_roles.sql \
  -D "openflow_user_name=YOUR_NON_ACCOUNTADMIN_OPENFLOW_USER"
```

If the administrative connection uses a PAT restricted to `ACCOUNTADMIN`, it cannot switch to
`OPENFLOW_ADMIN`, and secondary roles do not apply. Create a separate 30-day PAT restricted to the
new role:

```sql
ALTER USER YOUR_NON_ACCOUNTADMIN_OPENFLOW_USER
ADD PROGRAMMATIC ACCESS TOKEN RETAIL_DEMO_OPENFLOW_ADMIN
  ROLE_RESTRICTION = 'OPENFLOW_ADMIN'
  DAYS_TO_EXPIRY = 30
  COMMENT = 'Openflow administration for the retail intelligence tutorial';
```

Store the returned value outside the repository in a mode-600 file, and configure a
`retail_demo_openflow_admin` Snowflake CLI connection with an absolute `token_file_path` and
`role = "OPENFLOW_ADMIN"`. Never print or commit the token.

## 3. Create the control objects and WIF trust anchor

Run phase 1 through the role-restricted Openflow connection:

```bash
snow sql -c retail_demo_openflow_admin \
  -f openflow/config/01_gen2_objects.sql \
  -D "aws_region=us-east-2"
```

The script creates the control database/schema, WIF secret, exact S3/STS network rule, external
access integration, and Gen 2 deployment. It does not create a runtime. Save the
`workload_identity_federation_issuer` and `workload_identity_federation_subject` returned by
`DESC SECRET` in private deployment notes; do not commit account-specific values.

## 4. Configure AWS workload identity

In AWS, create an OIDC identity provider using the Snowflake issuer and audience `snowflake`. Create or
update a read-only IAM role whose trust policy contains this statement. Remove `https://` from the
issuer when building the provider ARN and condition keys.

```json
{
  "Effect": "Allow",
  "Principal": {
    "Federated": "arn:aws:iam::<AWS_ACCOUNT_ID>:oidc-provider/<ISSUER_HOST_AND_PATH>"
  },
  "Action": "sts:AssumeRoleWithWebIdentity",
  "Condition": {
    "StringEquals": {
      "<ISSUER_HOST_AND_PATH>:sub": "<WORKLOAD_IDENTITY_FEDERATION_SUBJECT>",
      "<ISSUER_HOST_AND_PATH>:aud": "snowflake",
      "<ISSUER_HOST_AND_PATH>:sf_rnm": "OPENFLOW_RETAIL_DEMO_EXECUTE_AS_RL"
    }
  }
}
```

Attach only the S3 permissions the flow needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::<BUCKET>",
      "Condition": {
        "StringLike": {
          "s3:prefix": ["retail-demo/landing/openflow/*"]
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::<BUCKET>/retail-demo/landing/openflow/*"
    }
  ]
}
```

Snowflake documents this exchange in
[Use Workload Identity Federation with Openflow](https://docs.snowflake.com/en/user-guide/data-integration/openflow/security/workload-identity-federation).

## 5. Create the runtime

After the AWS OIDC provider, trust conditions, and read policy are verified, run phase 2 only after
approval. This starts billable compute:

```bash
snow sql -c retail_demo_openflow_admin -f openflow/config/02_gen2_runtime.sql
```

The expected runtime is `RETAIL_DEMO_OPENFLOW_CONTROL.RUNTIME.RETAIL_DEMO_RUNTIME`, `SMALL`/`S1`,
one minimum node, one maximum node, with `RETAIL_DEMO_OPENFLOW_S3_EAI` attached.

## 6. Build the custom process group

Create a parameter context from `parameters.example.yaml`, replacing only the placeholders. These are
identifiers, not credentials. Use the exact non-secret values for the bucket, AWS role ARN, Snowflake
account identifier, and WIF secret FQN.

Create and enable these controller services:

1. `RetailDemoSnowflakeConnection` (`SnowflakeConnectionService`) with **Snowflake Managed Token**.
2. `RetailDemoSnowflakeWifToken` (`SnowflakeWorkloadIdentityTokenProvider`) referencing the connection,
   WIF secret, and `snowflake` audience.
3. `RetailDemoAwsCredentials` (`AWSCredentialsProviderControllerService`) referencing the WIF token
   provider, read-only IAM role ARN, session name, and bucket region.
4. `RetailDemoSchemaCache` (`VolatileSchemaCache`).
5. `RetailDemoJsonReader` (`JsonTreeReader`) using schema inference and the cache.

Select **Verify** where the controller-service UI offers it before enabling the service. The AWS
credential service performs its real STS exchange when an AWS processor runs.

Build this process group; `JsonTreeReader` is a controller service, not a processor:

```text
ListS3 -> FetchS3Object -> RouteOnAttribute
                                  |-> PutDatabaseRecord (SUPPLIER)
                                  |-> PutDatabaseRecord (PURCHASE_ORDER)
                                  |-> PutDatabaseRecord (RECEIPT)
                                  `-> PutDatabaseRecord (MERCHANT_PLAN)
```

Use the exact processor properties, route expressions, controller-service bindings, FIFO connection
prioritizer, and bounded failure queue in `flow-spec.yaml`. Never auto-terminate fetch, database,
retry-exhaustion, or unmatched failures. A queued failure blocks readiness and must retain the
original FlowFile for inspection.

## 7. Run once and validate

1. Reconfirm all four target tables are empty.
2. Start the process group and watch processor bulletins and queues.
3. Stop the group after the four source FlowFiles reach their success paths.
4. Require zero queued failures and run the read-only gate:

   ```bash
   snow sql -c retail_demo_admin -f openflow/config/03_validate_load.sql
   ```

5. Compare all row counts with `generated/manifest.json`; the locked cohort expects 5 suppliers,
   500 purchase orders, 500 receipts, and 175 merchant-plan rows.
6. Confirm `ORDER_DATE`, `EXPECTED_RECEIPT_DATE`, `RECEIPT_DATE`, `PLAN_DATE`, and `UPDATED_AT` remain
   within the TPC-DS scenario window. Only `INGESTED_AT` may use the operational wall clock.
7. Suspend the runtime after capturing validation evidence:

   ```sql
   ALTER OPENFLOW RUNTIME
     RETAIL_DEMO_OPENFLOW_CONTROL.RUNTIME.RETAIL_DEMO_RUNTIME SUSPEND;
   SELECT SYSTEM$WAIT_FOR_OPENFLOW_RUNTIME_STATUS(
     600,
     'SUSPENDED',
     'RETAIL_DEMO_OPENFLOW_CONTROL.RUNTIME.RETAIL_DEMO_RUNTIME'
   );
   ```

## Reproducibility boundary

`flow-spec.yaml` is the reviewed semantic contract. Custom-flow version control through an Openflow
registry is supported, but a runtime export can contain environment identifiers and encrypted
properties. Add a sanitized versioned export only after inspecting it for secrets and account data.
Until then, do not claim that the custom canvas flow is automatically deployed from this repository.

Processor and controller-service behavior is documented in Snowflake's
[processor reference](https://docs.snowflake.com/en/user-guide/data-integration/openflow/processors/index),
[controller-service reference](https://docs.snowflake.com/en/user-guide/data-integration/openflow/controllers),
and [custom-flow version-control guide](https://docs.snowflake.com/en/user-guide/data-integration/openflow/version-control-custom-flows).
