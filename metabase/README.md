# Metabase

Metabase reads only `RETAIL_DEMO.SERVING` through the `RETAIL_DEMO_METABASE` role. Business logic
stays in Snowflake; dashboard questions do not reimplement thresholds or joins.

Start the pinned open-source image:

```bash
docker compose --env-file ../.env -f metabase/docker-compose.yml up -d
```

Open `http://localhost:3000`, add Snowflake, and use a dedicated read-only user whose default role
is `RETAIL_DEMO_METABASE`. Enter the credential in the Metabase UI or a secret manager; do not put
it in Compose or Git.

Create three questions:

1. `SERVING.MERCHANT_SCORECARD`: number card for estimated lost sales and a trend by business date.
2. `SERVING.MERCHANT_PROBLEMS`: table ordered by `IMPACT_RANK`, with category, store, item, cause,
   days of supply, fill rate, and exposure.
3. `SERVING.ROOT_CAUSE_EVIDENCE`: drill-through detail for a selected item/store problem.

Filters should pass category, store, item, and supplier values to the views. They should not encode
the risk threshold. Stop the container after the tutorial; local application state is ignored by
Git and may be removed during cleanup.

The image tag is pinned to the current version at repository creation. Review the official
[Metabase Docker guide](https://www.metabase.com/docs/latest/installation-and-operation/running-metabase-on-docker)
and security releases before exposing the service beyond localhost.
