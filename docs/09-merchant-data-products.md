# 09 — Merchant data products

Metabase and downstream users receive only three secure views:

| View | Grain | Purpose |
|---|---|---|
| `SERVING.MERCHANT_SCORECARD` | business date, category | Portfolio health and exposure |
| `SERVING.MERCHANT_PROBLEMS` | current item/store problem | Ranked actions and derived cause |
| `SERVING.ROOT_CAUSE_EVIDENCE` | current item/store problem | Human-auditable supporting metrics |

The products derive, rather than store, the conclusion:

```text
TPC-DS demand baseline
  + latest inventory
  + current PO receipt fill rate
  + item economics
  -> days of supply
  -> at-risk units
  -> lost sales and margin exposure
  -> root-cause evidence
```

Inspect the products with the engineering role:

```sql
SELECT * FROM RETAIL_DEMO.SERVING.MERCHANT_SCORECARD;

SELECT * FROM RETAIL_DEMO.SERVING.MERCHANT_PROBLEMS
ORDER BY IMPACT_RANK LIMIT 25;

SELECT * FROM RETAIL_DEMO.SERVING.ROOT_CAUSE_EVIDENCE
ORDER BY IMPACT_RANK LIMIT 25;
```

At the healthy checkpoint, the affected cohort should not yet appear as supplier-underfill risk.
After the final two event dates, the same deterministic cohort should appear with lower inventory,
a fill rate below 60%, and positive exposure. Healthy controls must remain.

Do not add material business logic to a Metabase question. Change the version-controlled Dynamic
Table SQL, rerun validation, and let every consumer see the same definition.

Next: [Metabase](10-metabase.md).
