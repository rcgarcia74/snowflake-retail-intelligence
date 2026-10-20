# CoCo Plan-mode prompt: business-date contract incident

Use this only after the sandbox fault validation has completed. Plan mode must not change objects,
start Openflow processors, alter data, or resume a warehouse.

```text
Investigate the controlled cross-product data-quality incident in RETAIL_DEMO_COCO_LAB using
read-only inspection only.

The source Openflow load remains correct: merchant-plan row counts and PLAN_DATE values match the
locked scenario clock. However, VALIDATION.BUSINESS_DATE_CONTRACT reports a failure for
source-plan-to-serving-date.

Trace the path from the verified Openflow merchant-plan contract through RAW.MERCHANT_PLAN,
ANALYTICS.CATEGORY_STORE_DAY, SERVING.CATEGORY_SALES_TO_PLAN_TREND, and the corresponding
Metabase trend query. Identify whether any layer uses INGESTED_AT as a business date instead of
PLAN_DATE.

Separate confirmed evidence from hypotheses. Propose the smallest sandbox-only correction,
the validation commands to prove recovery, cost controls, and rollback steps. Do not modify
objects, start processors, change data, or access RETAIL_DEMO production-demo objects.
```
