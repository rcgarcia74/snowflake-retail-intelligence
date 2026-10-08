# CoCo implementation prompt: Openflow operational ingestion

Use this after creating the raw tables and a gen 2 runtime. Review every proposed change before
execution.

```text
You are implementing the Openflow portion of the RETAIL_DEMO tutorial.

Read openflow/config/flow-spec.yaml and parameters.example.yaml. Build or review one versioned
Openflow process group that reads only the four documented JSONL prefixes from the tutorial S3
bucket and writes supplier, purchase order, receipt, and merchant plan records to the matching
RETAIL_DEMO.RAW tables.

Requirements:
- use the custom-flow canvas on the existing gen 2 RETAIL_DEMO_RUNTIME; do not create a schema-level
  OPENFLOW CONNECTOR object;
- configure the five named controller services in flow-spec.yaml and verify each service where the UI
  supports verification;
- use Snowflake Managed Token for Snowflake writes;
- use the documented Snowflake WIF secret and read-only AWS role through
  SnowflakeWorkloadIdentityTokenProvider and AWSCredentialsProviderControllerService; never embed
  credentials;
- use ListS3 state tracking so processed objects are not listed from the beginning on restart;
- route the four unique filenames with the exact RouteOnAttribute expressions in flow-spec.yaml;
- use JsonTreeReader as a controller service for the four PutDatabaseRecord branches, not as a
  processor in the chain;
- use strict JSON parsing and fail on unmatched fields;
- retain failed FlowFiles in a bounded dead-letter path and stop the readiness gate on errors;
- use insert behavior only after confirming the four target tables are empty;
- do not clear ListS3 state, replace staged objects, or rerun against nonempty targets;
- start with one S1 node and do not scale without evidence;
- report controller-service verification, processor state, queued FlowFiles, manifest-to-table row
  counts, scenario-clock checks, and errors after the run;
- do not generate or modify fixture data;
- do not create any object outside the fixed tutorial deployment, runtime, bucket prefix, database,
  and schemas.

Before starting the flow, show the exact processors, controller services, parameters, target tables,
route expressions, failure connections, and authentication modes. After ingestion, run
openflow/config/03_validate_load.sql and suspend the runtime after evidence capture.
```
