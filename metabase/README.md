# Metabase

Metabase reads only `RETAIL_DEMO.SERVING` through the `RETAIL_DEMO_METABASE` role. Business logic
stays in Snowflake; dashboard questions do not reimplement thresholds or joins.

Start the pinned open-source image:

```bash
docker compose --env-file .env -f metabase/docker-compose.yml up -d
```

Before the first start, add two independently generated random values to the repository-root `.env`:

```dotenv
MB_ENCRYPTION_SECRET_KEY=<at-least-32-random-characters>
MB_SESSION_SECRET_KEY=<at-least-16-random-characters>
```

Generate and paste the values locally; do not print them in shared terminal output or put them in
Compose. The ignored `.env` should be mode `600`. The encryption key protects saved database
credentials at rest, and the session key signs login sessions. Keep both values stable after setup;
changing either one can invalidate stored credentials or active sessions.

### If Metabase was started before the encryption key was configured

Do not delete the application database or start over. Stop Metabase, make a local backup, release
any stale migration lock left by an interrupted startup, and encrypt the existing database offline:

```bash
docker compose --env-file .env -f metabase/docker-compose.yml down
cp -a metabase/metabase-data /tmp/retail-demo-metabase-before-encryption
docker compose --env-file .env -f metabase/docker-compose.yml run --rm \
  -e MB_DB_FILE=/metabase-data/metabase.db/metabase.db \
  --entrypoint java metabase \
  --add-opens java.base/java.nio=ALL-UNNAMED \
  -jar /app/metabase.jar migrate release-locks
docker compose --env-file .env -f metabase/docker-compose.yml run --rm \
  -e MB_DB_FILE=/metabase-data/metabase.db/metabase.db \
  --entrypoint java metabase \
  --add-opens java.base/java.nio=ALL-UNNAMED \
  -jar /app/metabase.jar enable-encryption
docker compose --env-file .env -f metabase/docker-compose.yml up -d
```

The encryption command must end with `Encryption enabled OK`. Then verify both runtime checks:

```bash
docker inspect --format '{{.State.Health.Status}}' retail-demo-metabase
curl --fail --silent http://localhost:3000/api/health
```

Expected results are `healthy` and `{"status":"ok"}`. The explicit `MB_DB_FILE` is required for
maintenance commands because this Compose layout stores the H2 database at the nested path shown
above. Keep the backup until Metabase starts successfully; it contains local application state and
must not be committed.

Open `http://localhost:3000`, add Snowflake, and use the dedicated `TYPE=SERVICE` user created by
the bootstrap command in `docs/02-snowflake-setup.md`. That command registers the RSA public key,
grants only `RETAIL_DEMO_METABASE`, and sets `DEFAULT_SECONDARY_ROLES = ()`. Configure the
connection with the matching private key stored outside the repository and these values:

- the Snowflake account identifier, such as `<organization>-<account>`, without the
  `.snowflakecomputing.com` suffix;
- `RETAIL_DEMO_WH`, `RETAIL_DEMO`, and only the `SERVING` schema;
- `RETAIL_DEMO_METABASE` as the role; and
- the local PKCS #8 PEM private-key file, leaving the password blank.

Metabase's Snowflake driver adds the hostname suffix. Supplying the full hostname duplicates that
suffix and causes a TLS certificate mismatch. Saving the connection briefly resumes the warehouse
for the connection test and metadata sync. Verify that only the four documented `SERVING` views
appear and that the warehouse is suspended after its 60-second idle interval with
`AUTO_RESUME = FALSE`. Resume it explicitly only for an active tutorial step. The role field in
Metabase selects a default role but does not remove privileges inherited from other roles granted
to the user.

Build the three number cards, ranked-problem table, and drill-through table from
`SERVING.ROOT_CAUSE_EVIDENCE`. That common grain lets Category, readable Store ID, readable Item ID,
and Supplier ID filter all five questions consistently. Build the sales-shortfall line chart from
`SERVING.CATEGORY_SALES_TO_PLAN_TREND`, using the distinct store mapping documented in
[`docs/10-metabase.md`](../docs/10-metabase.md) so Category and Store also filter the trend.

Filters pass values to Snowflake Field Filters; they must not encode the risk threshold. Follow the
question-by-question SQL, dashboard connection matrix, and deterministic verification values in
`docs/10-metabase.md`. Stop the container after the tutorial; local application state is ignored by
Git and may be removed during cleanup.

The image tag is pinned to the current version at repository creation. Review the official
[Metabase Docker guide](https://www.metabase.com/docs/latest/installation-and-operation/running-metabase-on-docker)
and security releases before exposing the service beyond localhost.

The file-backed application database is appropriate only for this disposable local tutorial. Do not
use it as a production Metabase application database.
