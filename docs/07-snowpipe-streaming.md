# 07 — Stream POS and inventory events

The repository uses Snowpipe Streaming's high-performance Python SDK with custom `PIPE` objects.
Named Channels provide ordered offsets and a durable resume point between demo phases.

## Platform requirement

The high-performance SDK supports ARM64 macOS, Windows, ARM64 Linux, and x86_64 Linux. It does not
support x86_64 macOS. Use the repository's Docker image when the host platform cannot run the SDK
natively.

The Docker path is the documented default for this demo because it provides a reproducible
Linux/amd64 runtime.

## Create the Snowflake objects

Create the streaming pipes with the engineer connection:

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" -f sql/04_streaming/01_streaming_pipes.sql
```

Create the dedicated service user first. Do not assign its default role yet because the producer role
is created in the next step.

```sql
CREATE USER IF NOT EXISTS RETAIL_DEMO_STREAM_USER
  TYPE = SERVICE
  COMMENT = 'Dedicated Snowpipe Streaming producer for retail demo';
```

Run the least-privilege role and grant setup using the administrative connection:

```bash
snow sql -c retail_demo_admin \
  -f sql/04_streaming/02_streaming_access.sql \
  -D "streaming_user_name=RETAIL_DEMO_STREAM_USER"
```

The script creates `RETAIL_DEMO_STREAMER`, grants only the required database, schema, table, and
pipe privileges, and grants that role to the service user. Then set it as the user's default role:

```sql
ALTER USER RETAIL_DEMO_STREAM_USER SET DEFAULT_ROLE = RETAIL_DEMO_STREAMER;
```

Use RSA key-pair authentication. Keep the private key outside this repository and register only its
public key with Snowflake:

```sql
ALTER USER RETAIL_DEMO_STREAM_USER SET RSA_PUBLIC_KEY = '<public-key-without-PEM-delimiters>';
```

Do not put the private key or its contents in SQL, Snowflake, this repository, or the Docker build
context.

## Configure the producer

Copy the profile template:

```bash
cp streaming/producer/profile.example.json streaming/producer/profile.json
```

The runtime profile uses JWT key-pair authentication:

```json
{
  "account": "ORG-ACCOUNT",
  "authorization_type": "JWT",
  "private_key_file": "/absolute/path/outside/this/repository/rsa_key.p8",
  "role": "RETAIL_DEMO_STREAMER",
  "url": "https://ORG-ACCOUNT.snowflakecomputing.com",
  "user": "RETAIL_DEMO_STREAM_USER"
}
```

`streaming/producer/profile.json` is runtime configuration and must not be committed. Keep the
private key outside the repository.

## Build the producer

```bash
docker build \
  --platform linux/amd64 \
  -f streaming/producer/Dockerfile \
  -t retail-demo-streaming-producer \
  .
```

## Dry run

A dry run parses both generated event files and makes no Snowflake network calls:

```bash
docker run --rm \
  --platform linux/amd64 \
  -v "$PWD/generated:/app/generated:ro" \
  retail-demo-streaming-producer \
  --input /app/generated/streaming
```

The generated demo contains 3,500 sales events and 3,500 inventory events.

## Load a healthy checkpoint

TPC-DS is the scenario clock. Cohort selection sets `simulation_date` to the day after the TPC-DS
baseline ends, and all generated business-event dates derive from it. Do not substitute the current
calendar date; real current time is reserved for operational metadata such as ingestion and audit
timestamps.

Derive the healthy checkpoint from `generated/manifest.json`. For the seven-day hot window, the
checkpoint is the fifth hot date (`simulation_date - 2 days`):

```bash
HEALTHY_CHECKPOINT=$(python3 -c 'import json; from datetime import date,timedelta; m=json.load(open("generated/manifest.json")); print(date.fromisoformat(m["simulation_date"])-timedelta(days=2))')
echo "$HEALTHY_CHECKPOINT"
```

Mount both the runtime profile and private key read-only:

```bash
docker run --rm \
  --platform linux/amd64 \
  -v "$PWD/generated:/app/generated:ro" \
  -v "$PWD/streaming/producer/profile.json:/app/streaming/producer/profile.json:ro" \
  -v "/absolute/path/rsa_key.p8:/absolute/path/rsa_key.p8:ro" \
  retail-demo-streaming-producer \
  --input /app/generated/streaming \
  --profile /app/streaming/producer/profile.json \
  --live \
  --through-date "$HEALTHY_CHECKPOINT"
```

After Dynamic Tables exist, this checkpoint leaves the affected pairs above the two-day risk
threshold. The remaining two scenario dates push them below it.

## Resume into failure

Rerun the producer without `--through-date`:

```bash
docker run --rm \
  --platform linux/amd64 \
  -v "$PWD/generated:/app/generated:ro" \
  -v "$PWD/streaming/producer/profile.json:/app/streaming/producer/profile.json:ro" \
  -v "/absolute/path/rsa_key.p8:/absolute/path/rsa_key.p8:ro" \
  retail-demo-streaming-producer \
  --input /app/generated/streaming \
  --profile /app/streaming/producer/profile.json \
  --live \
  --pace-ms 5
```

The producer reopens each existing Named Channel without supplying a new initial offset token. It
reads `latest_committed_offset_token`, skips source rows at or below that committed offset, appends
only the remaining chronological source rows, and waits for the final offset to commit.

Do not reopen an existing channel with a forced initial offset such as `"0"` when resuming this
replay. Do not rename the channel unless another logical stream is intentionally being created.

## Verify restart and completion

After a checkpoint or restart, verify both table cardinality and channel offsets:

```sql
SELECT
  'SALES' AS STREAM,
  COUNT(*) AS ROW_COUNT,
  COUNT(DISTINCT EVENT_ID) AS DISTINCT_EVENTS
FROM RETAIL_DEMO.RAW.STORE_SALES_EVENTS

UNION ALL

SELECT
  'INVENTORY',
  COUNT(*),
  COUNT(DISTINCT EVENT_ID)
FROM RETAIL_DEMO.RAW.STORE_INVENTORY_EVENTS;

SHOW CHANNELS IN ACCOUNT;
```

A completed generated replay should contain 3,500 physical rows and 3,500 distinct event IDs in
each event table, with both Named Channels committed through offset `3500`.

Before continuing, rerun the producer at an already committed checkpoint and verify that table
counts do not increase. This is the restart/resume regression check.

See Snowflake's current
[Named Channels tutorial](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-getting-started),
[SDK configuration reference](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-configurations),
and
[SDK limitations](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-limitations).

Next: [Dynamic Tables](08-dynamic-tables.md).
