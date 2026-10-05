# Security policy

This tutorial is designed for disposable demo infrastructure and synthetic data. Do not use
production credentials, customer data, or regulated data.

## Credential handling

- Use a named Snowflake CLI connection, key-pair authentication, workload identity, or a secret
  manager. Never commit passwords, private keys, access keys, tokens, or populated profile files.
- Use a dedicated AWS IAM role scoped to the single tutorial bucket and prefixes. Block public S3
  access, require TLS, and enable default encryption.
- Give the tutorial role only the documented database, schema, warehouse, stage, pipe, and table
  privileges. Do not run day-to-day steps as `ACCOUNTADMIN`.
- Use Openflow Snowflake Managed Authentication and secret references. Do not type secret values
  into flow definitions or parameter files.
- Create a read-only Metabase role. Do not reuse the engineering role in BI.

Run `python scripts/check_repo.py` before every commit. The check catches common credential
patterns, generated data, prohibited control files, and retailer-specific naming. It is a guardrail,
not a substitute for a dedicated secret scanner.

## Reporting

Do not open a public issue containing a credential or exploitable account detail. Revoke the secret
first, preserve only non-sensitive evidence, and contact the repository owner privately.
