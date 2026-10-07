# Snowpipe Streaming producer

The producer replays the generated seven-day POS and inventory event logs through Snowpipe
Streaming high-performance Named Channels. Source line numbers are used as monotonically increasing
offset tokens.

For the complete setup and demo walkthrough, see
[`docs/07-snowpipe-streaming.md`](../docs/07-snowpipe-streaming.md).

## Runtime

The repository uses Docker as the default producer runtime:

```bash
docker build \
  --platform linux/amd64 \
  -f streaming/producer/Dockerfile \
  -t retail-demo-streaming-producer \
  .
```

This also provides a supported Linux/amd64 runtime when the host cannot run the high-performance
SDK natively, including x86_64 macOS hosts.

## Authentication

Use a dedicated Snowflake service user with RSA key-pair authentication.

Copy the profile template:

```bash
cp streaming/producer/profile.example.json streaming/producer/profile.json
```

The profile must use:

```json
{
  "authorization_type": "JWT",
  "private_key_file": "/absolute/path/outside/this/repository/rsa_key.p8"
}
```

Keep `profile.json` uncommitted and the private key outside the repository. Mount both into the
container read-only.

## Dry run

Dry-run mode parses the generated files without contacting Snowflake:

```bash
docker run --rm \
  --platform linux/amd64 \
  -v "$PWD/generated:/app/generated:ro" \
  retail-demo-streaming-producer \
  --input /app/generated/streaming
```

The complete generated replay contains 3,500 sales events and 3,500 inventory events.

## Live replay

For the two-phase demo, first replay through the fifth hot date from the generated scenario, then
rerun without `--through-date` to send the remaining events.

TPC-DS is the scenario clock: `simulation_date` is the day after the selected TPC-DS baseline ends,
and all generated business-event dates derive from it. Do not replace it with the current calendar
date. Real current time is reserved for operational metadata such as ingestion and audit timestamps.

Do not hard-code the checkpoint date in reusable instructions. Derive it from the generated
scenario/manifest.

See [`docs/07-snowpipe-streaming.md`](../docs/07-snowpipe-streaming.md) for the complete Docker
commands, key mounts, checkpoint procedure, and verification queries.

## Resume contract

Each stream has a stable Named Channel and uses its source line number as the offset token.

When starting or restarting, the producer:

1. opens the existing Named Channel without forcing an initial offset token;
2. reads `latest_committed_offset_token`;
3. skips source rows at or below that offset;
4. appends only the remaining chronological source rows; and
5. waits for the final submitted offset to commit.

Do not change this to `open_channel(channel_name, "0")` for normal restart/resume behavior. Forcing
an initial offset can cause already processed source rows to be replayed.

Do not rename a channel unless a new logical stream is intentionally required.

A restart at an already committed checkpoint must leave both physical row counts and distinct
`EVENT_ID` counts unchanged.

## Batching

The SDK batches internally. The producer waits for the final committed offset only at the end of
each stream; it does not serialize ingestion by waiting after every row.

See Snowflake's current
[Named Channels SDK tutorial](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-getting-started)
and
[access-control requirements](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-access-control).
