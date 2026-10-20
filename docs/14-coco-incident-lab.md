# 14 — CoCo incident lab: business-date contract

This optional lab demonstrates a controlled data-pipeline defect without changing the working
`RETAIL_DEMO` demo. It uses a separate `RETAIL_DEMO_COCO_LAB` database and zero-copy snapshots of
the verified Openflow merchant-plan output and Snowpipe Streaming sales events.

Do not run the fault or repair scripts against `RETAIL_DEMO`.

## What the lab proves

The scenario is not a merchandising problem. It is a temporal data-contract failure:

```text
Openflow merchant-plan contract
  -> RAW.MERCHANT_PLAN
  -> Dynamic Table date join
  -> serving trend
  -> Metabase visualization
```

`PLAN_DATE` is the merchant-plan business date. `INGESTED_AT` is wall-clock operational metadata.
The deliberate lab defect joins plans to sales using `INGESTED_AT::DATE`, preserving source rows and
Openflow validation while breaking the source-to-serving date contract.

The main Openflow process group remains stopped. This lab does not create a second deployment,
runtime, S3 prefix, parameter context, or controller service.

## Preconditions

Before creating the lab, require all of the following:

1. The working demo readiness assertion passes.
2. `openflow/config/03_validate_load.sql` passes.
3. Snowpipe Streaming has committed both channels through the documented final offset.
4. `RETAIL_DEMO_WH` is X-Small, `AUTO_SUSPEND = 60`, and `AUTO_RESUME = FALSE`.
5. The user has explicitly approved the temporary sandbox database and short warehouse window.

The setup script creates a database, so it starts with `ACCOUNTADMIN` only to create and transfer
ownership of `RETAIL_DEMO_COCO_LAB` to `RETAIL_DEMO_ENGINEER`. No account-level role is used after
that transfer.

## 1. Create the isolated lab

Run once:

```bash
snow sql -c retail_demo_admin -f sql/08_coco_incident_lab/00_create_sandbox.sql
snow sql -c "$SNOWFLAKE_CONNECTION" \
  -f sql/08_coco_incident_lab/00a_clone_sandbox_inputs.sql
```

The script fails if the lab database already exists. Do not replace an existing lab; inspect it or
clean it up through the explicit cleanup step instead.

## 2. Establish the healthy sandbox baseline

This creates only two Dynamic Tables: the minimal sales-to-plan path and its serving view.

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" \
  -f sql/08_coco_incident_lab/01_create_healthy_pipeline.sql
snow sql -c "$SNOWFLAKE_CONNECTION" \
  -f sql/08_coco_incident_lab/02_validate_healthy.sql
```

Require both business-date checks to be `PASS` and the assertion to return:

```text
PASS: source business dates reconcile to the serving trend
```

Check Dynamic Table initialization before proceeding:

```sql
SHOW DYNAMIC TABLES IN SCHEMA RETAIL_DEMO_COCO_LAB.ANALYTICS;

SELECT NAME, STATE, STATE_CODE, REFRESH_ACTION, REFRESH_TRIGGER
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
  NAME_PREFIX => 'RETAIL_DEMO_COCO_LAB.ANALYTICS', RESULT_LIMIT => 20
))
ORDER BY REFRESH_START_TIME DESC;
```

## 3. Inject the controlled fault

Explain to the audience that the next command deliberately changes only the sandbox Dynamic Table.
It does not change the Openflow source contract or `RETAIL_DEMO`.

After explicit approval:

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" \
  -f sql/08_coco_incident_lab/03_inject_business_date_fault.sql
snow sql -c "$SNOWFLAKE_CONNECTION" \
  -f sql/08_coco_incident_lab/04_validate_fault_detected.sql
```

The first check, `source-plan-to-serving-date`, must be `FAIL`. The second check, which confirms the
locked scenario window at the source, must remain `PASS`. `ASSERT_EXPECTED_FAULT()` must return:

```text
PASS: controlled source-to-serving business-date fault detected
```

This distinction is the point of the exercise: row counts and source dates can be correct while a
downstream business-date join is wrong.

## 4. Investigate with CoCo

Open [`coco/plan-business-date-incident.md`](../coco/plan-business-date-incident.md) and use its
prompt in CoCo Plan mode. Verify that its plan is restricted to `RETAIL_DEMO_COCO_LAB`, identifies
the date-join expression, and includes the documented recovery checks.

Do not allow Agent mode until the plan has been reviewed and approved.

## 5. Apply and prove the recovery

After approval, use the bounded Agent-mode prompt in
[`coco/apply-approved-business-date-fix.md`](../coco/apply-approved-business-date-fix.md), or run the
deterministic repository repair directly:

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" \
  -f sql/08_coco_incident_lab/05_fix_business_date_contract.sql
snow sql -c "$SNOWFLAKE_CONNECTION" \
  -f sql/08_coco_incident_lab/06_validate_recovery.sql
```

The recovery assertion must return the healthy result. Query the sandbox serving view and compare it
with the working production trend before showing a separate, clearly labelled sandbox Metabase
question. Do not edit the production dashboard.

```sql
SELECT BUSINESS_DATE, CATEGORY, ROUND(SUM(SALES_SHORTFALL), 2) AS SALES_SHORTFALL
FROM RETAIL_DEMO_COCO_LAB.SERVING.CATEGORY_SALES_TO_PLAN_TREND
GROUP BY BUSINESS_DATE, CATEGORY
ORDER BY BUSINESS_DATE, CATEGORY;
```

## 6. Cost-safe shutdown

Suspend the two lab Dynamic Tables and then the warehouse after capturing evidence:

```sql
ALTER DYNAMIC TABLE RETAIL_DEMO_COCO_LAB.ANALYTICS.CATEGORY_STORE_DAY SUSPEND;
ALTER DYNAMIC TABLE RETAIL_DEMO_COCO_LAB.ANALYTICS.ITEM_STORE_DAY SUSPEND;
ALTER WAREHOUSE RETAIL_DEMO_WH SUSPEND;
```

Verify that the warehouse is suspended. The lab database remains available for the next scheduled
rehearsal until an explicit cleanup decision is made.

## 7. Delete the lab only with approval

Confirm the exact target first:

```sql
SHOW DATABASES LIKE 'RETAIL_DEMO_COCO_LAB';
```

Then, with explicit approval:

```bash
snow sql -c retail_demo_admin -f sql/08_coco_incident_lab/98_cleanup_sandbox.sql
```

This drops only `RETAIL_DEMO_COCO_LAB`; it does not remove `RETAIL_DEMO`, Openflow resources, S3
objects, or the working Metabase dashboard.
