# CoCo Agent-mode prompt: approved sandbox recovery

Use only after a human has reviewed the Plan-mode output and explicitly approved the recovery.

```text
Execute the approved sandbox recovery exactly as specified below. Do not create or revise a plan,
substitute commands, broaden scope, or apply an alternative remediation.

Use `snow sql -c retail_demo` with role RETAIL_DEMO_ENGINEER. The only permitted target is
RETAIL_DEMO_COCO_LAB. Run each numbered step only when the preceding step succeeds.

1. Repair the date contract by running exactly:

   snow sql -c retail_demo \
     -f sql/08_coco_incident_lab/05_fix_business_date_contract.sql

2. Run the recovery gate exactly:

   snow sql -c retail_demo \
     -f sql/08_coco_incident_lab/06_validate_recovery.sql

   Stop unless both contract checks are PASS with 175 expected rows and 0 unmatched, and the
   assertion returns `PASS: source business dates reconcile to the serving trend`.

3. Run read-only checks that prove all of the following:

   - GET_DDL for ANALYTICS.CATEGORY_STORE_DAY contains
     `ON p.PLAN_DATE = d.BUSINESS_DATE`; its merchant-plan join does not use INGESTED_AT.
   - DYNAMIC_TABLE_REFRESH_HISTORY shows a new SUCCEEDED refresh for CATEGORY_STORE_DAY after
     the repair.
   - SERVING.CATEGORY_SALES_TO_PLAN_TREND contains 7 distinct dates from 2002-12-28 through
     2003-01-03, 0 rows with a NULL SALES_PLAN, and 0 rows with a negative SALES_SHORTFALL.

4. Only after Steps 1-3 pass, run exactly:

   snow sql -c retail_demo -q "ALTER DYNAMIC TABLE RETAIL_DEMO_COCO_LAB.ANALYTICS.ITEM_STORE_DAY RESUME;"

5. Verify without changing state:

   - `SHOW DYNAMIC TABLES IN SCHEMA RETAIL_DEMO_COCO_LAB.ANALYTICS` reports that
     scheduling_state is `ACTIVE` or `RUNNING` for CATEGORY_STORE_DAY and ITEM_STORE_DAY.
     Snowflake behavior-change bundles can select either label; both mean scheduling is enabled.
     `SUSPENDED` or any other value fails this gate.
   - `SHOW WAREHOUSES LIKE 'RETAIL_DEMO_WH'` reports STARTED.

Stop immediately on any command error, failed assertion, unexpected row count, unexpected date
range, unsuccessful refresh, `SUSPENDED` Dynamic Table, or Dynamic Table state other than ACTIVE or
RUNNING. Report the exact failing output and take no additional action.

Do not run `01_create_healthy_pipeline.sql`.
Do not run `03_inject_business_date_fault.sql`.
Do not run `98_cleanup_sandbox.sql`.
Do not suspend a Dynamic Table or warehouse.
Do not modify RETAIL_DEMO, RAW or Openflow data, the Openflow deployment or runtime, S3, roles,
Metabase, or warehouse settings.

When all gates pass, report the commands run, the corrected join predicate, both contract results,
the assertion result, refresh result, trend summary, both Dynamic Table states, and warehouse state.
Stop there.
```
