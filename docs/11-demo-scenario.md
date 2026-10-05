# 11 — Run the controlled demo scenario

## Before the audience arrives

- Local generator validation is `PASS`.
- Openflow has loaded exactly four files with no dead-letter FlowFiles.
- The healthy streaming prefix is committed.
- All Dynamic Tables are refreshed successfully.
- Metabase connects only through the serving role.
- The warehouse is X-Small and the Openflow runtime is S1/one node.
- `VALIDATION.DEMO_READINESS` is visible, but run the mandatory final assertion only after the
  failure phase is complete.

## Storyboard

1. **Business question:** Which problems need merchant attention now, why, and for how much?
2. **Foundation:** show that item/store identities and demand come from TPC-DS.
3. **Open history:** show one Iceberg table and its S3-backed metadata location.
4. **Operational integration:** show completed Openflow processors and zero failures.
5. **Healthy state:** scorecard has healthy controls and no intended supplier-underfill problem.
6. **Change:** run the streaming producer without `--through-date` to commit the last two days.
7. **Freshness:** show channel offsets and Dynamic Table refresh status.
8. **Decision:** refresh Metabase; drill category → store → item.
9. **Evidence:** sustained demand, partial receipt, declining days of supply, positive exposure.
10. **Trust:** run the readiness procedure and show all checks pass.

## CoCo moments

Use CoCo to explain lineage, inspect refresh failures, or compare the healthy and failed queries.
Avoid an unbounded live prompt that changes schema or data. The strongest message is:

> CoCo accelerates the engineer; governed deterministic pipelines remain the source of truth.

Next: [validation](12-validation.md).
