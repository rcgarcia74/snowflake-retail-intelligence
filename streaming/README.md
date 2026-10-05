# Snowpipe Streaming producer

The producer replays the generated seven-day POS and inventory event logs into two custom pipes
using Named Channels and monotonically increasing line-number offsets. Reopening a channel resumes
after its committed offset, so a rerun does not intentionally duplicate committed rows.

## Setup

1. Run `sql/04_streaming/01_streaming_pipes.sql` and the least-privilege access script.
2. Configure a dedicated Snowflake user for key-pair authentication.
3. Copy `profile.example.json` to `profile.json`, keep the private key outside this repository, and
   set restrictive file permissions on both.
4. Install the current high-performance SDK:

   ```bash
   pip install -r streaming/producer/requirements.txt
   ```

5. Test parsing without contacting Snowflake:

   ```bash
   python streaming/producer/produce.py
   ```

6. Stream the data. Add pacing only when it helps the live presentation. For a two-phase demo,
   first send the chronological prefix through the healthy checkpoint, then rerun without the date;
   the Named Channel resumes at its committed offset:

   ```bash
   python streaming/producer/produce.py --live --through-date 2002-03-23
   python streaming/producer/produce.py --live --pace-ms 5
   ```

   Replace the example checkpoint with the fifth hot date in `generated/manifest.json`.

The SDK batches internally. The producer waits for the final committed offset only at the end of
each stream; it does not serialize ingestion by waiting after every row.

See the official [Named Channels SDK tutorial](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-getting-started)
and [access-control requirements](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-access-control).
