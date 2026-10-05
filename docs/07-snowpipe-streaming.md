# 07 — Stream POS and inventory events

The repository targets Snowpipe Streaming's high-performance SDK with custom `PIPE` objects. Named
Channels provide ordered offsets and a clean resume point between demo phases.

## Setup

```bash
snow sql -c "$SNOWFLAKE_CONNECTION" -f sql/04_streaming/01_streaming_pipes.sql
snow sql -c "$SNOWFLAKE_CONNECTION" \
  -f sql/04_streaming/02_streaming_access.sql \
  -D "streaming_user_name=YOUR_STREAMING_USER"

cp streaming/producer/profile.example.json streaming/producer/profile.json
pip install -r streaming/producer/requirements.txt
python streaming/producer/produce.py
```

Register the streaming user's public key in Snowflake and keep the private key outside the repository.
The dry run must parse both files and make no network calls.

## Load a healthy checkpoint

Read `simulation_date` from `generated/manifest.json`; the hot window begins six days earlier. Stream
through the fifth hot date:

```bash
python streaming/producer/produce.py --live --through-date YYYY-MM-DD
```

After Dynamic Tables exist, this checkpoint leaves the affected pairs above the two-day risk
threshold. The remaining two dates push them below it.

## Resume into failure

```bash
python streaming/producer/produce.py --live --pace-ms 5
```

The producer reopens each channel, reads the last committed line offset, skips that prefix, and waits
for the final offset to commit. Check table counts, `SHOW CHANNELS`, and event-table telemetry. Do not
rerun with a renamed channel unless you intentionally want another copy.

See Snowflake's current [SDK tutorial](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-getting-started)
and [best practices](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-best-practices).

Next: [Dynamic Tables](08-dynamic-tables.md).
