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
- use the existing gen 2 RETAIL_DEMO_RUNTIME;
- use Snowflake Managed Authentication for Snowflake writes;
- use workload identity or a secret-backed AWS credentials provider; never embed credentials;
- use ListS3 state tracking so processed objects are not listed from the beginning on restart;
- use strict JSON parsing and fail on unmatched fields;
- retain failed FlowFiles in a bounded dead-letter path and stop the readiness gate on errors;
- use insert behavior only after confirming the four target tables are empty;
- start with one S1 node and do not scale without evidence;
- report processor state, queued FlowFiles, row counts, and errors after the run;
- do not generate or modify fixture data;
- do not create any object outside the fixed tutorial deployment, runtime, bucket prefix, database,
  and schemas.

Before starting the flow, show the exact processors, controller services, parameters, target tables,
and authentication modes. After ingestion, run the Openflow validation queries from the tutorial.
```
