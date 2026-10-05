# 10 — Build the Metabase dashboard

Start the local service:

```bash
docker compose --env-file .env -f metabase/docker-compose.yml up -d
docker compose -f metabase/docker-compose.yml ps
```

Open `http://localhost:3000`. Connect Snowflake with a dedicated user whose active/default role is
`RETAIL_DEMO_METABASE` and warehouse is `RETAIL_DEMO_WH`. Do not use the engineering role.

Build one dashboard with:

- scorecards for at-risk item/store count, lost sales, and lost margin;
- a category exposure trend;
- a ranked problem table with days of supply and fill rate;
- a drill-through evidence table showing store, item, supplier, baseline demand, on-hand, on-order,
  and exposure;
- category, store, item, and supplier filters.

Use model metadata only for friendly labels, descriptions, formatting, and relationships. Do not
recreate thresholds, supplier classification, or exposure math in Metabase.

Verify the Metabase user cannot query `RAW`, `ANALYTICS`, `CONFIG`, or `LAKEHOUSE`. Then continue to
the [demo scenario](11-demo-scenario.md).
