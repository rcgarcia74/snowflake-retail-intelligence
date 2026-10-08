# 01 — Prerequisites Verification

This document records the prerequisite setup that was actually completed and verified for the **Snowflake Merchant Decision Intelligence** demo repository.

It is written for someone who has **not used Snowflake CLI, AWS IAM, Amazon S3, or Snowflake storage integrations before**.

> **Current status:** Openflow Gen2 is enabled and read-only access is verified. No Openflow roles,
> deployment, runtime, AWS WIF trust, or ingestion flow has been created yet.

---

## 1. What this setup prepares

The demo uses:

- Snowflake sample TPC-DS data for historical retail facts.
- Amazon S3 for landing files and Snowflake-managed Iceberg storage.
- Snowflake native tables for the current/hot operational layer.
- Snowflake CLI for setup and validation.
- Python for deterministic local fixture generation and repository checks.
- Docker later for Metabase.
- Openflow Gen2 later for managed batch ingestion.

The **repository is the source of truth** for Snowflake object names, setup scripts, and execution order.

Do not create alternate object names without first checking the repository.

---

## 2. Canonical names — use these exact names

| Purpose | Canonical value |
|---|---|
| Snowflake admin CLI connection | `retail_demo_admin` |
| Snowflake engineering CLI connection | `retail_demo` |
| Snowflake database | `RETAIL_DEMO` |
| Snowflake warehouse | `RETAIL_DEMO_WH` |
| Resource monitor | `RETAIL_DEMO_MONITOR` |
| Engineering role | `RETAIL_DEMO_ENGINEER` |
| Metabase role | `RETAIL_DEMO_METABASE` |
| Storage integration | `RETAIL_DEMO_S3_INTEGRATION` |
| External volume | `RETAIL_DEMO_EXT_VOL` |
| Landing stage | `RETAIL_DEMO.SEED.S3_LANDING_STAGE` |
| Parquet file format | `RETAIL_DEMO.SEED.PARQUET_FORMAT` |
| JSONL file format | `RETAIL_DEMO.SEED.JSONL_FORMAT` |
| S3 bucket | `snowflake-retail-demo-rommelg` |
| S3 root prefix | `retail-demo/` |
| Base S3 URI | `s3://snowflake-retail-demo-rommelg/retail-demo/` |
| AWS IAM policy | `SnowflakeRetailDemoS3Policy` |
| AWS IAM role | `SnowflakeRetailDemoRole` |

> **Important:** Do not use `RETAIL_DEMO_S3_INT`.
>
> That was an earlier ad hoc test name and is **not** the integration name used by the repository.
>
> The correct repository-defined integration is:
>
> `RETAIL_DEMO_S3_INTEGRATION`

---

# Part A — Repository and local machine

## 3. Open a terminal and go to the repository

Open Terminal on the Mac.

Change into the repository directory.

Example:

```bash
cd ~/path/to/snowflake-retail-intelligence
```

Verify the current directory:

```bash
pwd
```

List the repository contents:

```bash
ls
```

You should see repository content similar to:

```text
README.md
config/
docs/
generator/
metabase/
openflow/
scripts/
sql/
streaming/
tests/
```

Unless explicitly stated otherwise, run all commands in this guide from the repository root.

---

# Part B — Snowflake CLI authentication

## 4. Why two Snowflake CLI connections are used

Two Snowflake CLI connections are used.

### Administrative connection

```text
retail_demo_admin
```

This connection is used only for Snowflake operations that require elevated privileges, such as:

- initial environment bootstrap
- storage integration creation
- external volume creation
- account-level grants

Its role is:

```text
ACCOUNTADMIN
```

### Engineering connection

```text
retail_demo
```

This is the normal connection used for demo engineering work.

Its role is restricted to:

```text
RETAIL_DEMO_ENGINEER
```

This separation prevents normal demo commands from unnecessarily running as `ACCOUNTADMIN`.

---

## 5. Snowflake Programmatic Access Tokens

The browser/SAML authentication method originally attempted in this environment failed with a SAML configuration error.

The Snowflake CLI connections were therefore configured using **Programmatic Access Tokens**, or PATs.

Three role-specific tokens are used after Openflow setup:

```text
Admin/bootstrap PAT
Engineering PAT
Openflow administration PAT
```

Do not put any token into the repository.

Do not put PAT values in:

```text
.env
README files
SQL files
shell scripts
Git
GitHub
```

---

## 6. Admin/bootstrap PAT

The administrative PAT is used by:

```text
retail_demo_admin
```

It is associated with administrative access required during setup.

Store the token value locally in:

```text
~/.snowflake/pat_bootstrap
```

Protect the file:

```bash
chmod 600 ~/.snowflake/pat_bootstrap
```

The administrative token should only be used when an operation genuinely requires the administrative connection.

---

## 7. Engineering PAT

The engineering PAT is restricted to:

```text
RETAIL_DEMO_ENGINEER
```

The Snowflake user used during this setup is:

```text
ROMMELG
```

The PAT was created with:

```sql
ALTER USER ROMMELG
ADD PROGRAMMATIC ACCESS TOKEN COCO_RETAIL_DEMO
  ROLE_RESTRICTION='RETAIL_DEMO_ENGINEER'
  DAYS_TO_EXPIRY=30
  COMMENT='Cortex Code retail intelligence tutorial';
```

Store the returned token in:

```text
~/.snowflake/pat_retail_demo
```

Protect the token file:

```bash
chmod 600 ~/.snowflake/pat_retail_demo
```

---

## 7A. Openflow administration PAT

Openflow provisioning uses a third connection:

```text
retail_demo_openflow_admin
```

Its PAT is restricted to `OPENFLOW_ADMIN` and stored outside the repository in an absolute,
mode-600 token file. This connection owns the Openflow control database, WIF secret, external access
integration, deployment, and runtime lifecycle. It does not replace the `ACCOUNTADMIN` bootstrap or
`RETAIL_DEMO_ENGINEER` connections.

---

## 8. Configure Snowflake CLI

Snowflake CLI connection configuration is stored in:

```text
~/.snowflake/connections.toml
```

A critical lesson from setup was that the PAT token file path should be an **absolute path**.

Do not use:

```toml
token_file_path = "~/.snowflake/pat_retail_demo"
```

In this environment, `~` was not expanded correctly by Snowflake CLI.

Use:

```toml
token_file_path = "/Users/administrator/.snowflake/pat_retail_demo"
```

---

## 9. Configure the engineering connection

The engineering connection should look similar to:

```toml
[retail_demo]
account = "<ORG>-<ACCOUNT>"
user = "ROMMELG"
authenticator = "PROGRAMMATIC_ACCESS_TOKEN"
token_file_path = "/Users/administrator/.snowflake/pat_retail_demo"
role = "RETAIL_DEMO_ENGINEER"
warehouse = "RETAIL_DEMO_WH"
database = "RETAIL_DEMO"
schema = "CONFIG"
```

Replace:

```text
<ORG>-<ACCOUNT>
```

with the Snowflake organization/account identifier for the environment.

---

## 10. Configure the administrative connection

Create another entry in:

```text
~/.snowflake/connections.toml
```

named:

```text
retail_demo_admin
```

It uses:

```text
ACCOUNTADMIN
```

and the administrative token stored at:

```text
/Users/administrator/.snowflake/pat_bootstrap
```

Use this connection only when the instructions explicitly call for:

```text
retail_demo_admin
```

---

## 11. Test the engineering CLI connection

Run:

```bash
snow connection test -c retail_demo
```

Expected result:

```text
Connection test succeeds
```

Then verify the active session context:

```bash
snow sql -c retail_demo -q "
SELECT
  CURRENT_USER(),
  CURRENT_ROLE(),
  CURRENT_WAREHOUSE(),
  CURRENT_DATABASE(),
  CURRENT_SCHEMA();
"
```

The important value is:

```text
CURRENT_ROLE() = RETAIL_DEMO_ENGINEER
```

---

# Part C — Snowflake workspace bootstrap

## 12. Repository bootstrap script

The canonical bootstrap script is:

```text
sql/00_setup/00_bootstrap.sql
```

This creates the primary Snowflake workspace used by the demo.

It creates or configures:

```text
RETAIL_DEMO
RETAIL_DEMO_WH
RETAIL_DEMO_MONITOR
RETAIL_DEMO_ENGINEER
RETAIL_DEMO_METABASE
```

It also creates the required database schemas.

---

## 13. Required schemas

The demo database contains these seven schemas:

```text
CONFIG
SEED
RAW
LAKEHOUSE
ANALYTICS
SERVING
VALIDATION
```

Their responsibilities are intentionally separated.

### CONFIG

Configuration and control objects.

### SEED

Seed/cohort data, file formats, and external stages.

### RAW

Native ingested source data.

### LAKEHOUSE

Iceberg/lakehouse objects.

### ANALYTICS

Derived analytical models and Dynamic Tables.

### SERVING

Curated objects presented to BI consumers such as Metabase.

### VALIDATION

Readiness checks and reconciliation logic.

---

## 14. Run the Snowflake bootstrap

Use the admin connection:

```bash
snow sql -c retail_demo_admin \
  -f sql/00_setup/00_bootstrap.sql \
  -D "user_name=ROMMELG" \
  -D "metabase_user_name=<YOUR_METABASE_USER>"
```

If the same Snowflake user is temporarily being used for both engineering and Metabase access, use that user for both parameters.

---

## 15. Important sample database permission behavior

The demo uses:

```text
SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL
```

`SNOWFLAKE_SAMPLE_DATA` is an imported/shared Snowflake database.

Do not attempt grants such as:

```sql
GRANT USAGE ON DATABASE SNOWFLAKE_SAMPLE_DATA ...;
GRANT USAGE ON SCHEMA SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL ...;
GRANT SELECT ON ALL TABLES IN SCHEMA ...;
```

Individual grants against the imported database caused an error during setup.

The correct grant is:

```sql
GRANT IMPORTED PRIVILEGES
ON DATABASE SNOWFLAKE_SAMPLE_DATA
TO ROLE RETAIL_DEMO_ENGINEER;
```

When `SHOW GRANTS` is run afterward, Snowflake may display the imported database access as `USAGE`.

The definitive validation is to query a TPC-DS table successfully.

---

# Part D — Verify Snowflake bootstrap

## 16. Verify the database

Run:

```bash
snow sql -c retail_demo_admin -q "
SHOW DATABASES LIKE 'RETAIL_DEMO';
"
```

Confirm:

```text
RETAIL_DEMO
```

exists.

---

## 17. Verify the warehouse

Run:

```bash
snow sql -c retail_demo_admin -q "
SHOW WAREHOUSES LIKE 'RETAIL_DEMO_WH';
"
```

Expected configuration:

```text
Warehouse: RETAIL_DEMO_WH
Size: XSMALL
Auto suspend: 60 seconds
Auto resume: enabled
```

---

## 18. Verify the roles

Run:

```bash
snow sql -c retail_demo_admin -q "
SHOW ROLES LIKE 'RETAIL_DEMO%';
"
```

Confirm at least:

```text
RETAIL_DEMO_ENGINEER
RETAIL_DEMO_METABASE
```

---

## 19. Verify the schemas

Run:

```bash
snow sql -c retail_demo -q "
SHOW SCHEMAS IN DATABASE RETAIL_DEMO;
"
```

Confirm:

```text
CONFIG
SEED
RAW
LAKEHOUSE
ANALYTICS
SERVING
VALIDATION
```

---

## 20. Verify TPC-DS access

Run:

```bash
snow sql -c retail_demo -q "
SELECT COUNT(*)
FROM SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.ITEM;
"
```

The query must return successfully.

The row count itself is not the purpose of this test.

This proves that:

```text
RETAIL_DEMO_ENGINEER
```

can read the Snowflake TPC-DS sample database.

---

## 21. Verify engineering object creation privileges

Run:

```bash
snow sql -c retail_demo -q "
CREATE TABLE RETAIL_DEMO.SEED.CONNECTION_TEST (
    ID NUMBER
);

DROP TABLE RETAIL_DEMO.SEED.CONNECTION_TEST;
"
```

Both statements must succeed.

This verifies that the engineering role can create demo objects without using `ACCOUNTADMIN`.

---

# Part E — Amazon S3

## 22. Create the S3 bucket

Open the AWS console.

Navigate to:

```text
S3
```

Create this bucket:

```text
snowflake-retail-demo-rommelg
```

The root demo S3 URI is:

```text
s3://snowflake-retail-demo-rommelg/retail-demo/
```

An S3 bucket name cannot contain `/`.

Therefore this would be invalid as a bucket name:

```text
snowflake/retail-demo
```

The correct model is:

```text
Bucket:
snowflake-retail-demo-rommelg

Prefix:
retail-demo/
```

---

## 23. Create the S3 folder/prefix layout

Inside:

```text
snowflake-retail-demo-rommelg
```

create:

```text
retail-demo/
```

The complete project layout is:

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

The two most important root locations are:

```text
s3://snowflake-retail-demo-rommelg/retail-demo/landing/
```

and:

```text
s3://snowflake-retail-demo-rommelg/retail-demo/iceberg/
```

Do not place raw Parquet files directly inside an Iceberg-owned table prefix.

The repository architecture separates:

```text
landing/
```

from:

```text
iceberg/
```

---

## 24. Verify S3 security settings

Open:

```text
AWS Console
→ S3
→ snowflake-retail-demo-rommelg
```

Verify:

```text
Block Public Access: enabled
Default encryption: enabled
Object Ownership: Bucket owner enforced
```

All Block Public Access options should be enabled.

---

## 25. Require encrypted HTTPS/TLS access

There is no "deny non-TLS access" checkbox in the standard S3 bucket creation workflow.

This must be added using a bucket policy.

Open:

```text
S3
→ snowflake-retail-demo-rommelg
→ Permissions
→ Bucket policy
```

Use:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyInsecureTransport",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::snowflake-retail-demo-rommelg",
        "arn:aws:s3:::snowflake-retail-demo-rommelg/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

Save the policy.

AWS accepted this policy successfully during the verified setup.

---

# Part F — AWS IAM policy for Snowflake

## 26. Why an IAM policy is required

Snowflake needs permission to:

```text
list files
read files
write files
delete files
```

within the project S3 prefix.

It should **not** receive broad S3 administrator privileges.

The IAM policy therefore restricts Snowflake to:

```text
s3://snowflake-retail-demo-rommelg/retail-demo/
```

---

## 27. Create the IAM policy

Open:

```text
AWS Console
→ IAM
→ Policies
→ Create policy
→ JSON
```

Use:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ManageRetailDemoObjects",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:DeleteObjectVersion"
      ],
      "Resource": "arn:aws:s3:::snowflake-retail-demo-rommelg/retail-demo/*"
    },
    {
      "Sid": "ListRetailDemoPrefix",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "arn:aws:s3:::snowflake-retail-demo-rommelg",
      "Condition": {
        "StringLike": {
          "s3:prefix": [
            "retail-demo",
            "retail-demo/*"
          ]
        }
      }
    }
  ]
}
```

Name the policy:

```text
SnowflakeRetailDemoS3Policy
```

Create the policy.

---

# Part G — AWS IAM role

## 28. Create the IAM role

Open:

```text
AWS Console
→ IAM
→ Roles
→ Create role
```

Create:

```text
SnowflakeRetailDemoRole
```

Attach:

```text
SnowflakeRetailDemoS3Policy
```

At this stage the permanent Snowflake trust relationship cannot yet be completed because Snowflake has not generated its IAM principal and external ID.

A temporary trust relationship can therefore be used only long enough to create the role.

After the role exists, record its ARN.

It looks like:

```text
arn:aws:iam::<AWS_ACCOUNT_ID>:role/SnowflakeRetailDemoRole
```

You will use this ARN when creating the Snowflake storage integration and external volume.

---

# Part H — Snowflake storage integration and external volume

## 29. Use the repository-defined setup script

The canonical repository script is:

```text
sql/00_setup/01_storage_integrations.sql
```

This is important because the repository creates **two different Snowflake objects** that use AWS:

```text
RETAIL_DEMO_S3_INTEGRATION
RETAIL_DEMO_EXT_VOL
```

The storage integration is used for staged S3 access.

The external volume is used for Snowflake-managed Iceberg storage.

Both require AWS trust configuration.

---

## 30. Run the canonical storage setup

From the repository root:

```bash
snow sql -c retail_demo_admin \
  -f sql/00_setup/01_storage_integrations.sql \
  -D "aws_role_arn=arn:aws:iam::<AWS_ACCOUNT_ID>:role/SnowflakeRetailDemoRole" \
  -D "s3_landing_url=s3://snowflake-retail-demo-rommelg/retail-demo/landing/" \
  -D "s3_iceberg_url=s3://snowflake-retail-demo-rommelg/retail-demo/iceberg/"
```

Replace:

```text
<AWS_ACCOUNT_ID>
```

with the AWS account ID contained in the IAM role ARN.

The repository script creates:

```text
RETAIL_DEMO_S3_INTEGRATION
RETAIL_DEMO_EXT_VOL
```

It also grants the required usage privileges to:

```text
RETAIL_DEMO_ENGINEER
```

---

## 31. Stop after the DESCRIBE commands

The repository setup intentionally ends by describing both Snowflake objects.

The relevant commands are:

```sql
DESCRIBE INTEGRATION RETAIL_DEMO_S3_INTEGRATION;

DESCRIBE EXTERNAL VOLUME RETAIL_DEMO_EXT_VOL;
```

Do **not** create the S3 stage until AWS trust has been updated.

---

## 32. Retrieve the Snowflake trust information

If necessary, run the descriptions again:

```bash
snow sql -c retail_demo_admin -q "
DESC INTEGRATION RETAIL_DEMO_S3_INTEGRATION;
DESC EXTERNAL VOLUME RETAIL_DEMO_EXT_VOL;
"
```

For the storage integration, identify:

```text
STORAGE_AWS_IAM_USER_ARN
STORAGE_AWS_EXTERNAL_ID
```

For the external volume, identify the equivalent Snowflake-generated AWS principal ARN and external ID values returned by:

```text
DESC EXTERNAL VOLUME RETAIL_DEMO_EXT_VOL
```

You do not need to publish these values.

You only need to copy them into the AWS trust policy.

---

# Part I — AWS trust relationship

## 33. Why two trust entries are required

The repository creates both:

```text
RETAIL_DEMO_S3_INTEGRATION
```

and:

```text
RETAIL_DEMO_EXT_VOL
```

Both need permission to assume:

```text
SnowflakeRetailDemoRole
```

Authorizing only the storage integration is insufficient because the Iceberg external volume also needs AWS access.

---

## 34. Update the IAM role trust policy

Open:

```text
AWS Console
→ IAM
→ Roles
→ SnowflakeRetailDemoRole
→ Trust relationships
→ Edit trust policy
```

Replace the temporary trust relationship with a policy that authorizes both Snowflake objects.

Template:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SnowflakeStorageIntegration",
      "Effect": "Allow",
      "Principal": {
        "AWS": "<INTEGRATION_STORAGE_AWS_IAM_USER_ARN>"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "<INTEGRATION_STORAGE_AWS_EXTERNAL_ID>"
        }
      }
    },
    {
      "Sid": "SnowflakeExternalVolume",
      "Effect": "Allow",
      "Principal": {
        "AWS": "<EXTERNAL_VOLUME_AWS_IAM_USER_ARN>"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "<EXTERNAL_VOLUME_AWS_EXTERNAL_ID>"
        }
      }
    }
  ]
}
```

Replace:

```text
<INTEGRATION_STORAGE_AWS_IAM_USER_ARN>
<INTEGRATION_STORAGE_AWS_EXTERNAL_ID>
<EXTERNAL_VOLUME_AWS_IAM_USER_ARN>
<EXTERNAL_VOLUME_AWS_EXTERNAL_ID>
```

with the values Snowflake returned.

Save the policy.

AWS accepted this trust configuration successfully during the verified setup.

---

# Part J — Create the Snowflake S3 stage

## 35. Repository stage script

The canonical stage script is:

```text
sql/00_setup/02_stage_objects.sql
```

It creates:

```text
RETAIL_DEMO.SEED.PARQUET_FORMAT
RETAIL_DEMO.SEED.JSONL_FORMAT
RETAIL_DEMO.SEED.S3_LANDING_STAGE
```

---

## 36. Run the stage creation script

Run:

```bash
snow sql -c retail_demo \
  -f sql/00_setup/02_stage_objects.sql \
  -D "s3_landing_url=s3://snowflake-retail-demo-rommelg/retail-demo/landing/"
```

The script uses the repository-defined storage integration:

```text
RETAIL_DEMO_S3_INTEGRATION
```

Do not change that name.

---

## 37. Verify the stage

The script finishes with:

```sql
LIST @SEED.S3_LANDING_STAGE;
```

At this point there may be no files in the landing location yet.

Therefore this is a successful result:

```text
No data
```

`No data` means:

```text
Snowflake found the stage
Snowflake authenticated to AWS
Snowflake accessed the S3 prefix
No objects currently exist under the prefix
```

It does **not** mean the connection failed.

---

## 38. Optional root-level S3 connectivity test

During troubleshooting, a temporary stage can be created against the root demo prefix.

Use the canonical integration name:

```bash
snow sql -c retail_demo -q "
USE ROLE RETAIL_DEMO_ENGINEER;
USE DATABASE RETAIL_DEMO;
USE SCHEMA CONFIG;

CREATE OR REPLACE STAGE S3_CONNECTION_TEST
    URL = 's3://snowflake-retail-demo-rommelg/retail-demo/'
    STORAGE_INTEGRATION = RETAIL_DEMO_S3_INTEGRATION;

LIST @S3_CONNECTION_TEST;
"
```

Again, this is valid:

```text
No data
```

because an empty S3 prefix is not an error.

Clean up the temporary test stage:

```bash
snow sql -c retail_demo -q "
DROP STAGE IF EXISTS RETAIL_DEMO.CONFIG.S3_CONNECTION_TEST;
"
```

---

# Part K — Snowflake raw tables

## 39. Create native raw tables

The canonical repository script is:

```text
sql/02_raw/01_raw_tables.sql
```

Run:

```bash
snow sql -c retail_demo \
  -f sql/02_raw/01_raw_tables.sql
```

This command completed successfully during setup.

The repository creates native raw tables including:

```text
RETAIL_DEMO.RAW.SUPPLIER
RETAIL_DEMO.RAW.PURCHASE_ORDER
RETAIL_DEMO.RAW.RECEIPT
RETAIL_DEMO.RAW.MERCHANT_PLAN
RETAIL_DEMO.RAW.STORE_SALES_EVENTS
RETAIL_DEMO.RAW.STORE_INVENTORY_EVENTS
```

Do not initialize the Dynamic Tables yet.

Their source data has not all been ingested.

---

# Part L — Local Python environment

## 40. Create the local environment file

From the repository root:

```bash
cp .env.example .env
```

The `.env` file is local only.

Do not commit it.

Do not put secret values inside it.

Examples of things that must **not** be stored in `.env`:

```text
Snowflake PAT values
AWS access keys
passwords
private keys
secret tokens
```

Public identifiers can be stored there.

For the verified environment, values should align with:

```dotenv
SNOWFLAKE_CONNECTION=retail_demo
SNOWFLAKE_ROLE=RETAIL_DEMO_ENGINEER
SNOWFLAKE_WAREHOUSE=RETAIL_DEMO_WH
SNOWFLAKE_DATABASE=RETAIL_DEMO
SNOWFLAKE_SCHEMA=RAW

AWS_REGION=<YOUR_AWS_REGION>
S3_BUCKET=snowflake-retail-demo-rommelg
S3_ROOT=retail-demo
AWS_ICEBERG_ROLE_ARN=arn:aws:iam::<AWS_ACCOUNT_ID>:role/SnowflakeRetailDemoRole
```

Use the actual AWS region for the environment.

---

## 41. Create a Python virtual environment

Run:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

After activation, the shell prompt should begin with something similar to:

```text
(.venv)
```

Example:

```text
(.venv) Administrators-MacBook-Pro-2:snowflake-retail-intelligence administrator$
```

---

## 42. Install development dependencies

Run:

```bash
pip install -r requirements-dev.txt
```

Do this while:

```text
(.venv)
```

is active.

---

# Part M — Repository verification

## 43. Run repository hygiene checks

Run:

```bash
python scripts/check_repo.py
```

Verified output:

```text
PASS: repository hygiene checks
```

This confirms the repository passed its built-in hygiene validation.

Do not continue if this script reports a failure.

Fix the reported repository problem first.

---

# Part N — Verify Python

## 44. Check Python version

Run:

```bash
python --version
```

The repository requires:

```text
Python 3.11+
```

Verified environment:

```text
Python 3.13.7
```

This satisfies the requirement.

---

# Part O — Verify Docker

## 45. Check Docker CLI

Run:

```bash
docker --version
```

Verified environment:

```text
Docker version 23.0.5
```

---

## 46. Verify Docker Desktop / Docker daemon

Run:

```bash
docker info
```

A valid result contains both:

```text
Client:
```

and:

```text
Server:
```

The verified environment returned a functioning Docker Desktop server.

If instead you see:

```text
Cannot connect to the Docker daemon
```

start Docker Desktop and run:

```bash
docker info
```

again.

Docker will be needed later for Metabase.

---

# Part P — Snowflake cost controls

## 47. Warehouse configuration

The demo intentionally starts with a small Snowflake warehouse:

```text
RETAIL_DEMO_WH
```

Configuration:

```text
Size: XSMALL
Auto-suspend: 60 seconds
Auto-resume: enabled
```

This prevents an idle warehouse from continuing to consume credits unnecessarily.

---

## 48. Resource monitor

The bootstrap creates:

```text
RETAIL_DEMO_MONITOR
```

with a quota of:

```text
25 credits
```

Configured behavior includes:

```text
80% usage: notification
100% usage: suspend immediately
```

This is an important demo cost-control safeguard.

---

# Part Q — Demo data safety

## 49. Do not use production/customer data

This environment is for interview/demo purposes.

Do not use:

```text
production customer data
customer credentials
private customer exports
production access keys
real customer PII
production secrets
```

The demo architecture intentionally uses:

```text
TPC-DS sample data
+
deterministically generated operational fixtures
```

TPC-DS provides the large historical retail dataset.

The local generator fills operational gaps such as:

```text
inventory
suppliers
purchase orders
receipts
merchant plans
sales events
inventory events
```

---

# Part R — Openflow Gen2 — enabled; implementation pending

## 50. Current status

On October 7, 2026, the administrative connection successfully ran the Gen 2 discovery commands:

```sql
SHOW OPENFLOW DEPLOYMENTS;
SHOW OPENFLOW RUNTIMES;
SHOW ROLES LIKE 'OPENFLOW%';
```

All three returned no rows. This proves that the account exposes the Gen 2 interfaces and that no
tutorial Openflow objects or roles existed at the checkpoint; it does not prove creation privileges or
runtime behavior.

The same read-only checkpoint established:

- `RETAIL_DEMO.RAW.SUPPLIER`, `PURCHASE_ORDER`, `RECEIPT`, and `MERCHANT_PLAN` exist with zero rows;
- the completed `STORE_SALES_EVENTS` and `STORE_INVENTORY_EVENTS` tables each retain 3,500 rows;
- the S3 landing prefix contains exactly the four expected Openflow JSONL objects; and
- their byte sizes match `generated/manifest.json`: 532, 112,544, 86,030, and 30,387 bytes.

---

## 51. Work completed before Openflow mutation

The following was completed independently and must not be reopened unless Openflow exposes a real
dependency:

```text
TPC-DS cohort selection
TPC-DS cohort qualification
cohort export
deterministic local fixture generation
fixture validation
S3 historical data upload
Snowflake-managed Iceberg work
Snowpipe Streaming implementation and validation
analytical SQL development
data quality checks
Metabase preparation
```

The remaining work begins with the explicitly approved account-object and AWS trust phases in
`openflow/README.md`.

---

## 52. Verified implementation contract

Current Snowflake documentation and the repository contract require:

```text
Openflow Gen2
Deployment type: Snowflake
Runtime size: S1
Nodes: 1
AWS authentication: workload identity federation
Snowflake authentication: Snowflake Managed Token
Flow type: custom process group, not an OPENFLOW CONNECTOR object
Feeds: supplier, purchase order, receipt, merchant plan only
```

The local implementation is split by both role and lifecycle so the WIF issuer and subject can be
used to configure AWS before billable runtime creation:

```text
openflow/config/00_gen2_roles.sql
openflow/config/01_gen2_objects.sql
openflow/config/02_gen2_runtime.sql
openflow/config/03_validate_load.sql
openflow/config/98_cleanup_objects.sql
openflow/config/99_cleanup.sql
```

Actual object creation, AWS trust, runtime creation, controller-service verification, execution, and
load results must be recorded here only after they have been performed successfully.

Do not document hypothetical Openflow steps as if they have already been verified.

---

# Part S — Final prerequisite checklist

## 53. Snowflake

- [x] Snowflake CLI installed and working.
- [x] Administrative Snowflake CLI connection configured.
- [x] Engineering Snowflake CLI connection configured.
- [x] Openflow administration CLI connection configured.
- [x] Programmatic Access Token authentication working.
- [x] Engineering PAT restricted to `RETAIL_DEMO_ENGINEER`.
- [x] Openflow administration PAT restricted to `OPENFLOW_ADMIN`.
- [x] `RETAIL_DEMO` database created.
- [x] `RETAIL_DEMO_WH` warehouse created.
- [x] `RETAIL_DEMO_MONITOR` resource monitor created.
- [x] `RETAIL_DEMO_ENGINEER` role created.
- [x] `RETAIL_DEMO_METABASE` role created.
- [x] Seven required schemas created.
- [x] `SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL` accessible.
- [x] Engineering role can create and drop demo objects.
- [x] `RETAIL_DEMO_S3_INTEGRATION` created.
- [x] `RETAIL_DEMO_EXT_VOL` created.
- [x] `RETAIL_DEMO.SEED.S3_LANDING_STAGE` created.
- [x] S3 `LIST` succeeds.
- [x] Native RAW tables created.

---

## 54. AWS / S3

- [x] `snowflake-retail-demo-rommelg` bucket created.
- [x] `retail-demo/` root prefix created.
- [x] Landing prefixes created.
- [x] Iceberg prefixes created.
- [x] Archive prefix created.
- [x] S3 Block Public Access enabled.
- [x] Default encryption enabled.
- [x] Bucket Owner Enforced configured.
- [x] Non-TLS S3 access denied.
- [x] `SnowflakeRetailDemoS3Policy` created.
- [x] IAM permissions limited to the demo prefix.
- [x] `SnowflakeRetailDemoRole` created.
- [x] Storage integration trust relationship configured.
- [x] External volume trust relationship configured.
- [x] Snowflake can access the S3 landing prefix.

---

## 55. Local environment

- [x] `.env` created from `.env.example`.
- [x] Python virtual environment created.
- [x] Virtual environment activated.
- [x] Development requirements installed.
- [x] Repository hygiene checks pass.
- [x] Python 3.11+ verified.
- [x] Python `3.13.7` verified.
- [x] Docker CLI installed.
- [x] Docker daemon running.
- [x] Docker Desktop functional.

---

## 56. Openflow checkpoint

- [x] Openflow Gen2 enabled.
- [x] Openflow read-only access verified.
- [x] Four staged JSONL objects and empty target tables verified.
- [x] Current Gen 2/WIF runbook and local configuration added.
- [x] Openflow roles, WIF secret, EAI, and deployment created.
- [x] Openflow deployment reached `ACTIVE` with no runtime created.
- [ ] AWS OIDC provider and prefix-scoped read role configured.
- [ ] Openflow S1 / one-node runtime created.
- [ ] Controller services and custom process group verified.
- [ ] Openflow execute-as permissions verified through the running flow.
- [ ] Openflow ingestion and read-only SQL gate verified.

---

# Part T — Problems encountered and how to avoid them

## 57. Wrong storage integration name

An early manual setup step used:

```text
RETAIL_DEMO_S3_INT
```

The repository actually uses:

```text
RETAIL_DEMO_S3_INTEGRATION
```

This caused:

```text
Integration 'RETAIL_DEMO_S3_INTEGRATION' does not exist or not authorized.
```

The correct fix was **not** to modify the repository.

The correct fix was to return to:

```text
sql/00_setup/01_storage_integrations.sql
```

and create the canonical repository-defined object.

### Rule

Before manually creating Snowflake objects, inspect the repository and use its names exactly.

---

## 58. Snowflake CLI did not expand `~`

This configuration failed:

```toml
token_file_path = "~/.snowflake/pat_bootstrap"
```

even though the file existed.

Snowflake CLI attempted to use the literal path instead of expanding the home directory.

The working configuration used:

```toml
token_file_path = "/Users/administrator/.snowflake/pat_bootstrap"
```

The same applies to:

```toml
token_file_path = "/Users/administrator/.snowflake/pat_retail_demo"
```

### Rule

Use absolute paths for Snowflake PAT files.

---

## 59. Imported Snowflake database grants

Trying individual grants against:

```text
SNOWFLAKE_SAMPLE_DATA
```

caused errors because it is an imported/shared database.

The correct grant is:

```sql
GRANT IMPORTED PRIVILEGES
ON DATABASE SNOWFLAKE_SAMPLE_DATA
TO ROLE RETAIL_DEMO_ENGINEER;
```

### Rule

Use imported privileges for the Snowflake sample database.

---

## 60. Restricted PAT cannot arbitrarily change roles

The administrative bootstrap PAT was restricted to `ACCOUNTADMIN`. During the first Openflow Phase 1
attempt, its role and grant statements succeeded, but the script stopped at:

```sql
USE ROLE OPENFLOW_ADMIN;
```

Snowflake returned `Current session is restricted. USE ROLE not allowed.` Role-restricted PAT
sessions also do not activate secondary roles, so granting `OPENFLOW_ADMIN` to the same user did not
make that role available within the administrative session.

The durable fix was to split the scripts by role and create a third CLI connection whose PAT is
restricted to `OPENFLOW_ADMIN`. The Openflow-owned scripts contain no executable:

```sql
USE ROLE ...
```

### Rule

Do not depend on role switching when using role-restricted PATs.

Use the correct connection for the correct role.

---

## 61. S3 bucket names cannot contain `/`

This is invalid as a bucket name:

```text
snowflake-retail/retail-demo
```

This is valid:

```text
Bucket:
snowflake-retail-demo-rommelg

Prefix:
retail-demo/
```

### Rule

The slash identifies an object prefix, not part of an S3 bucket name.

---

## 62. TLS-only access is not a bucket creation checkbox

The AWS bucket creation wizard did not contain an option labeled:

```text
deny non-TLS access
```

That is expected.

TLS enforcement is configured through a bucket policy using:

```text
aws:SecureTransport
```

### Rule

Use the bucket policy documented earlier in this guide.

---

## 63. Empty S3 stage does not mean failure

The command:

```sql
LIST @S3_CONNECTION_TEST;
```

returned:

```text
No data
```

This was successful because the prefix was empty.

The same applies to:

```sql
LIST @SEED.S3_LANDING_STAGE;
```

### Rule

Distinguish:

```text
No data
```

from an AWS authentication or authorization error.

---

## 64. Both storage integration and external volume need AWS trust

Initially it is easy to focus only on:

```text
RETAIL_DEMO_S3_INTEGRATION
```

However the repository also creates:

```text
RETAIL_DEMO_EXT_VOL
```

The external volume is needed for Snowflake-managed Iceberg.

Both Snowflake objects produce AWS trust information.

### Rule

Update `SnowflakeRetailDemoRole` so both objects can assume the IAM role.

---

## 65. Do not run Dynamic Tables yet

The raw tables now exist, but not all required source data has been ingested.

Initializing downstream Dynamic Tables too early can result in:

```text
empty derived datasets
incorrect readiness conclusions
unnecessary troubleshooting
```

### Rule

Follow the repository execution order.

Do not skip the cohort, generation, ingestion, and validation gates.

---

# Part U — Current verified state

At the completion of this prerequisite round, the environment has:

```text
Working Snowflake CLI authentication
Working ACCOUNTADMIN bootstrap connection
Working RETAIL_DEMO_ENGINEER connection
Working OPENFLOW_ADMIN connection
Working TPC-DS access
RETAIL_DEMO database
RETAIL_DEMO_WH warehouse
Cost resource monitor
Seven demo schemas
Secure S3 bucket
Scoped IAM permissions
AWS IAM role
Canonical Snowflake storage integration
Canonical Snowflake external volume
AWS trust relationship
Working S3 landing stage
Snowflake RAW tables
Python virtual environment
Repository development dependencies
Passing repository hygiene checks
Python 3.13.7
Working Docker Desktop
Active RETAIL_DEMO_OPENFLOW Gen 2 deployment
Openflow WIF secret and us-east-2 S3/STS egress integration
No Openflow runtime yet
Empty supplier, purchase-order, receipt, and merchant-plan targets
```

The only currently outstanding prerequisite phase is:

```text
Openflow Gen2 live implementation and ingestion verification
```

---

# Part V — Next step

The next phase is the AWS trust checkpoint:

```text
Create or reuse the Snowflake WIF OIDC provider and configure a prefix-scoped, read-only IAM role
```

The repository guide is:

```text
docs/06-openflow.md
```

Use the privately captured issuer and subject from `DESC SECRET`; do not commit them. Review the exact
AWS identity-provider, trust-policy, and S3 read-policy changes and obtain explicit approval before
applying them. Do not create the billable Openflow runtime until the AWS trust exchange is verified.
