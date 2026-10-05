# 01 — Prerequisites

## Accounts and features

- A Snowflake account with access to `SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL`.
- A role allowed to bootstrap custom roles, an X-Small warehouse, a database, a resource monitor,
  a storage integration, and an external volume.
- Openflow enabled. New deployments are gen 2. Confirm deployment/runtime availability and any
  preview status for connector configuration in your cloud and region.
- An AWS account and one S3 bucket in the same region as Snowflake when practical.
- Python 3.11 or later, Docker, the Snowflake CLI, and optionally the AWS CLI.
- CoCo if you want the AI-assisted engineering path. It is optional for repository execution.

## S3 layout

Create one private, encrypted bucket and reserve only these prefixes:

```text
retail-demo/
├── landing/
│   ├── cohort/
│   ├── history/
│   └── openflow/
├── iceberg/
│   ├── inventory_history/
│   ├── purchase_order_history/
│   └── supplier_performance_history/
└── archive/
```

Enable S3 Block Public Access, default encryption, and a bucket policy that denies non-TLS access.
The Snowflake IAM role needs list/read/write/delete only for the documented prefixes. Snowflake needs
write access under `iceberg/`; the operator needs write access under `landing/` and explicit cleanup
access. Do not use user access keys in files.

## Local preparation

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/check_repo.py
```

Populate only public identifiers in `.env`. Configure authentication in the Snowflake CLI connection,
AWS profile/workload identity, Openflow secret reference, and the ignored streaming profile.

## Availability and spend checkpoint

Before creating billable objects, confirm:

- the intended Snowflake cloud/region supports your Openflow and streaming path;
- the account administrator agrees with the 25-credit warehouse resource monitor;
- the Openflow runtime size is S1 with one node;
- S3 lifecycle and cleanup responsibilities are assigned;
- no production/customer data will be used.

Proceed to [Snowflake setup](02-snowflake-setup.md).
