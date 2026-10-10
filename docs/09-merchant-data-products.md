# 09 — Merchant data products

Metabase and downstream users receive only four secure views:

| View | Grain | Purpose |
|---|---|---|
| `SERVING.MERCHANT_SCORECARD` | business date, category | Portfolio health and exposure |
| `SERVING.MERCHANT_PROBLEMS` | current item/store problem | Ranked actions and derived cause |
| `SERVING.ROOT_CAUSE_EVIDENCE` | current item/store problem | Human-auditable supporting metrics |
| `SERVING.CATEGORY_SALES_TO_PLAN_TREND` | business date, store, category | Historical sales-to-plan trend and shortfall |

The products derive, rather than store, the conclusion:

```text
TPC-DS demand baseline
  + latest inventory
  + current PO receipt fill rate
  + item economics
  -> days of supply
  -> at-risk units
  -> lost sales, signed margin impact, and positive margin at risk
  -> root-cause evidence
```

`ESTIMATED_MARGIN_IMPACT` preserves the signed TPC-DS net-profit economics: negative values show
sales that would have reduced profit. `MARGIN_AT_RISK` floors negative unit margin at zero before
applying at-risk units, so it is the non-negative executive exposure KPI. Both measures are defined
in Snowflake and reconcile from problem detail to the scorecard; Metabase must not recompute them.

`SALES_SHORTFALL` is the non-negative portion of missed sales plan at the business-date, store, and
category grain. It remains `NULL` when no plan exists, so missing plan data is not presented as zero
shortfall. The secure trend view publishes this Snowflake-defined measure without exposing the rest
of the `ANALYTICS` schema.

Inspect the products with the engineering role:

```sql
SELECT * FROM RETAIL_DEMO.SERVING.MERCHANT_SCORECARD;

SELECT * FROM RETAIL_DEMO.SERVING.MERCHANT_PROBLEMS
ORDER BY IMPACT_RANK LIMIT 25;

SELECT * FROM RETAIL_DEMO.SERVING.ROOT_CAUSE_EVIDENCE
ORDER BY IMPACT_RANK LIMIT 25;

SELECT * FROM RETAIL_DEMO.SERVING.CATEGORY_SALES_TO_PLAN_TREND
ORDER BY BUSINESS_DATE, STORE_SK, CATEGORY;
```

At the healthy checkpoint, the affected cohort should not yet appear as supplier-underfill risk.
After the final two event dates, the same deterministic cohort should appear with lower inventory,
a fill rate below 60%, and positive exposure. Healthy controls must remain.

Do not add material business logic to a Metabase question. Change the version-controlled Dynamic
Table SQL, rerun validation, and let every consumer see the same definition.

Next: [Metabase](10-metabase.md).
