# Contributing

Keep contributions retailer-neutral, deterministic, and runnable from a clean clone.

1. Do not commit generated data or credentials.
2. Keep TPC-DS identities authoritative; supplemental records must use exported cohort keys.
3. Do not pre-seed merchant conclusions. Serving results must be derived by Snowflake SQL.
4. Add or update tests for generator and validation changes.
5. Run `make check` before opening a pull request.
6. Update documentation whenever a Snowflake object or execution step changes.

Product-version-specific instructions should link to the relevant official documentation and state
when a feature is in preview.
