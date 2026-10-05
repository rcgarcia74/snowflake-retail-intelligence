# 00 — Architecture and execution map

The demo is one decision journey, not a tour of unrelated products:

> Sustained demand plus supplier under-fill prevents replenishment, inventory falls below two days
> of supply, and the merchant sees the item/store exposure with evidence while action is still useful.

## Storage and ingestion boundaries

| Data | System | Reason |
|---|---|---|
| TPC-DS sales, items, stores, dates | Existing Snowflake sample database | Governed analytical foundation and scale proof |
| 90-day inventory, PO, supplier history | Snowflake-managed Iceberg using the tutorial S3 external volume | Open historical storage controlled by Snowflake's Iceberg catalog |
| Current supplier, PO, receipt, plan | Snowflake native tables through Openflow | Low-frequency operational integration |
| Seven-day POS and inventory events | Snowflake native tables through Snowpipe Streaming | Low-latency hot path |
| Baselines, health, scorecard, problems, evidence | Dynamic Tables | Declarative, incrementally maintained products |
| Dashboard | Metabase over secure serving views | BI contains presentation, not hidden business logic |

Parquet and Iceberg are not synonyms. Parquet is the file representation. Iceberg adds table
metadata, snapshots, schema evolution, and transactional behavior. The generator's Parquet files
land under `landing/history/`; Snowflake loads them and writes its own data and metadata under the
separate `iceberg/` prefix.

## Data contract

The exported cohort is the only identity authority:

```text
CONFIG.DEMO_SCENARIO
CONFIG.DEMO_SCENARIO_ITEM
CONFIG.DEMO_SCENARIO_STORE
CONFIG.DEMO_SCENARIO_ITEM_STORE
        |
        v
data/cohort/{scenario.json,items.parquet,stores.parquet,item_store_baseline.parquet}
        |
        v
deterministic generator -> local validation -> upload
```

No supplemental row may invent an item or store key. The failure cohort is chosen from item groups
that share at least eight observed stores; it is not selected independently of TPC-DS.

## Readiness gates

1. `CONFIG.COHORT_QUALIFICATION`: stop unless every row is `PASS`.
2. `generator/validate.py`: stop unless every local integrity and scenario check is `PASS`.
3. Ingestion counts and processor/channel health: stop on rejected rows, dead-letter FlowFiles, or
   uncommitted offsets.
4. Dynamic Table refresh health: stop if a serving dependency is stale or failed.
5. `VALIDATION.ASSERT_DEMO_READY()`: mandatory final gate.

## Build order

Follow the numbered docs and SQL folders. The next step is [prerequisites](01-prerequisites.md).

Official references: [Iceberg table storage](https://docs.snowflake.com/en/user-guide/tables-iceberg-storage),
[Snowpipe Streaming concepts](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-overview),
[Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-about), and
[Openflow gen 2](https://docs.snowflake.com/en/user-guide/data-integration/openflow/gen2/index).
