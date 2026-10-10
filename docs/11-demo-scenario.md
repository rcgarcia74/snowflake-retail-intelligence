# 11 — Run the controlled demo scenario

## Before the audience arrives

- Local generator validation is `PASS`.
- Openflow has loaded exactly four files with no dead-letter FlowFiles.
- The healthy streaming prefix is committed.
- All Dynamic Tables are refreshed successfully.
- Metabase connects only through the serving role.
- The warehouse is X-Small with 60-second auto-suspend and automatic resume disabled.
- `VALIDATION.DEMO_READINESS` is visible, but run the mandatory final assertion only after the
  failure phase is complete.

## Cost-safe build state and live-demo restoration

Do not keep Openflow management services running between build sessions. After a successful load,
preserve a private recovery bundle containing the custom-flow export, parameter inventory,
controller-service inventory, stopped-processor and empty-queue evidence, fixed repository inputs,
and checksums. Inspect the export locally and keep it outside the repository because it can contain
environment identifiers and encrypted properties.

The cost-safe build state is:

- the Openflow runtime and deployment are absent;
- the four loaded target tables and validation evidence remain in Snowflake;
- `RETAIL_DEMO_WH` is suspended with `AUTO_RESUME = FALSE`; and
- Metabase may remain local, but it cannot restart Snowflake compute automatically.

Restore Openflow only for a scheduled live rehearsal or audience demonstration. Use the documented
role-restricted provisioning sequence in [06 — Ingest staged feeds with Openflow](06-openflow.md),
then import the private custom-flow export, recreate the parameter context from the private inventory,
verify every controller-service property before enabling it, and leave all processors stopped until
the rehearsal begins. Restoration is a stop condition unless the deployment and S1/one-node runtime
match the documented fixed names and the imported flow has zero queued FlowFiles.

After the rehearsal, stop the processors, require empty queues, export any newly approved changes,
and return to the cost-safe build state. Do not delete the already loaded source rows merely to prove
that the flow can be restored.

## Storyboard

1. **Business question:** Which problems need merchant attention now, why, and for how much?
2. **Foundation:** show that item/store identities and demand come from TPC-DS.
3. **Open history:** show one Iceberg table and its S3-backed metadata location.
4. **Operational integration:** show completed Openflow processors and zero failures from the live
   restored runtime. If Openflow was intentionally not restored, show the preserved flow export,
   checksum evidence, and Snowflake load-verification results and label this as recorded evidence.
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
