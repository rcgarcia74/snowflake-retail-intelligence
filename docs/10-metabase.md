# 10 — Build the Metabase dashboard

Start the local service:

```bash
docker compose --env-file .env -f metabase/docker-compose.yml up -d
docker compose --env-file .env -f metabase/docker-compose.yml ps
```

Before the first start, add independently generated `MB_ENCRYPTION_SECRET_KEY` and
`MB_SESSION_SECRET_KEY` values to the ignored repository-root `.env`, set the file to mode `600`, and
do not print or commit either value. Compose refuses to start without both keys. Require the container
to report `healthy` and `curl http://localhost:3000/api/health` to return `{"status":"ok"}` before
opening the setup screen.

If this local application database was initialized before the encryption key was configured, stop
here and follow the one-time [existing-database encryption procedure](../metabase/README.md#if-metabase-was-started-before-the-encryption-key-was-configured).
Do not delete the database: the procedure backs it up, releases any stale migration lock, encrypts
it offline, and verifies the restarted service.

Open `http://localhost:3000`. Connect Snowflake with a dedicated `TYPE=SERVICE` user authenticated
by an RSA key pair. Keep the private PKCS #8 PEM file outside the repository with mode `600`; register
only its public key in Snowflake. Grant the user only `RETAIL_DEMO_METABASE`, set that as its default
role, set `DEFAULT_SECONDARY_ROLES = ()`, and use `RETAIL_DEMO_WH` as its default warehouse. Do not
use the engineering user or role. The bootstrap command in
[02 — Snowflake setup](02-snowflake-setup.md#1-bootstrap-the-workspace) creates this user and
registers the public key; Metabase receives the matching private key.

Use these Metabase connection values:

| Field | Value |
| --- | --- |
| Account or hostname | Snowflake account identifier, such as `<organization>-<account>` |
| Username | Dedicated Metabase service user |
| Password | Blank |
| RSA private key | Local PKCS #8 PEM private-key file |
| Warehouse | `RETAIL_DEMO_WH` |
| Database | `RETAIL_DEMO` |
| Schemas | Only `SERVING` |
| Role | `RETAIL_DEMO_METABASE` |

Do not append `.snowflakecomputing.com` to the account identifier in this Metabase field. The
Snowflake JDBC driver adds that suffix; including it produces a duplicated hostname and TLS
certificate mismatch. Saving the connection resumes the warehouse briefly for its connection test
and initial metadata sync. Verify that Metabase discovers exactly these four views:

```text
SERVING.MERCHANT_SCORECARD
SERVING.MERCHANT_PROBLEMS
SERVING.ROOT_CAUSE_EVIDENCE
SERVING.CATEGORY_SALES_TO_PLAN_TREND
```

After the sync, `SHOW WAREHOUSES LIKE 'RETAIL_DEMO_WH'` must return `SUSPENDED` after the 60-second
idle interval and `AUTO_RESUME = FALSE`. Resume the warehouse explicitly only for an active tutorial
step. Choosing `RETAIL_DEMO_METABASE` in Metabase selects the connection role but does not remove
privileges inherited from other roles, which is why the dedicated user must have no broader role
grants.

Build one dashboard with:

- scorecards for at-risk item/store count, lost sales, and positive margin at risk;
- a category sales-shortfall trend;
- a ranked problem table with days of supply, fill rate, signed margin impact, and margin at risk;
- a drill-through evidence table showing store, item, supplier, baseline demand, on-hand, on-order,
  and exposure;
- category, store, item, and supplier filters.

Use model metadata only for friendly labels, descriptions, formatting, and relationships. Do not
recreate thresholds, supplier classification, or exposure math in Metabase.

Build the margin scorecard from `SUM(MARGIN_AT_RISK)` and label it `Margin at Risk`. Keep
`ESTIMATED_MARGIN_IMPACT` available in evidence views and tables; negative values are valid signed
economics, not a dashboard error.

## Create the six saved questions

Create each scorecard as a native SQL question against the Snowflake connection and save it with the
name shown. Configure all `category`, `store`, `item`, and `supplier` variables below as optional,
multi-value **Field Filters** using the mappings in the next section. Run each query with every
filter empty before saving.

### At-Risk Item-Store Count

```sql
SELECT COUNT(*) AS "At-Risk Item-Store Count"
FROM RETAIL_DEMO.SERVING.ROOT_CAUSE_EVIDENCE
WHERE 1 = 1
[[AND {{category}}]]
[[AND {{store}}]]
[[AND {{item}}]]
[[AND {{supplier}}]];
```

Save as `At-Risk Item-Store Count`; the empty-filter result must be `24`.

### Estimated Lost Sales

```sql
SELECT ROUND(SUM(ESTIMATED_LOST_SALES), 2) AS "Estimated Lost Sales"
FROM RETAIL_DEMO.SERVING.ROOT_CAUSE_EVIDENCE
WHERE 1 = 1
[[AND {{category}}]]
[[AND {{store}}]]
[[AND {{item}}]]
[[AND {{supplier}}]];
```

Save as `Estimated Lost Sales`, format it as USD with two decimal places, and require the
empty-filter result `USD 25,658.28`.

### Margin at Risk

```sql
SELECT ROUND(SUM(MARGIN_AT_RISK), 2) AS "Margin at Risk"
FROM RETAIL_DEMO.SERVING.ROOT_CAUSE_EVIDENCE
WHERE 1 = 1
[[AND {{category}}]]
[[AND {{store}}]]
[[AND {{item}}]]
[[AND {{supplier}}]];
```

Save as `Margin at Risk`, format it as USD with two decimal places, and require the empty-filter
result `USD 3,631.55`.

If the signed `ESTIMATED_MARGIN_IMPACT` is summed instead, this fixture returns `-USD 8,318.60`.
That is valid evidence but is not the positive-only executive risk KPI. A different result from any
saved question is a stop condition: run the readiness assertion and inspect the Dynamic Table refresh
history before building the remaining dashboard cards.

## Build the category trend

Create a native SQL question named `Category Sales Shortfall Trend`. The distinct store map adds the
readable store identifier used by the other cards without changing the seven-date aggregation:

```sql
WITH STORE_MAP AS (
  SELECT DISTINCT STORE_SK, STORE_ID
  FROM RETAIL_DEMO.SERVING.ROOT_CAUSE_EVIDENCE
)
SELECT
  T.BUSINESS_DATE AS "Business Date",
  T.CATEGORY AS "Category",
  ROUND(SUM(T.SALES_SHORTFALL), 2) AS "Sales Shortfall"
FROM RETAIL_DEMO.SERVING.CATEGORY_SALES_TO_PLAN_TREND AS T
LEFT JOIN STORE_MAP AS SM
  ON T.STORE_SK = SM.STORE_SK
WHERE 1 = 1
[[AND {{category}}]]
[[AND {{store}}]]
GROUP BY T.BUSINESS_DATE, T.CATEGORY
ORDER BY T.BUSINESS_DATE, T.CATEGORY;
```

Configure `category` as a Field Filter mapped to
`CATEGORY_SALES_TO_PLAN_TREND.CATEGORY`, with table and field alias `T.CATEGORY`. Configure `store`
as a Field Filter mapped to `ROOT_CAUSE_EVIDENCE.STORE_ID`, with alias `SM.STORE_ID`. Run the
question with both filters empty before saving; it must still return seven rows.

Choose a line visualization. Use `Business Date` for the horizontal axis, `Sales Shortfall` for the
vertical axis, and `Category` for the series. Format `Sales Shortfall` as USD with two decimal places.
The deterministic fixture should return seven locked business dates, one category series, and no
negative shortfall. A `NULL` shortfall indicates missing merchant-plan data and is a stop condition;
do not coerce it to zero in Metabase.

## Build the two detail tables

Create `Ranked Merchant Problems` with this complete SQL:

```sql
SELECT
  IMPACT_RANK AS "Impact Rank",
  BUSINESS_DATE AS "Business Date",
  CATEGORY AS "Category",
  STORE_ID AS "Store ID",
  ITEM_ID AS "Item ID",
  SUPPLIER_ID AS "Supplier ID",
  ROOT_CAUSE AS "Root Cause",
  ROUND(DAYS_OF_SUPPLY, 2) AS "Days of Supply",
  ROUND(FILL_RATE, 4) AS "Fill Rate",
  ROUND(ESTIMATED_LOST_SALES, 2) AS "Estimated Lost Sales",
  ROUND(ESTIMATED_MARGIN_IMPACT, 2) AS "Estimated Margin Impact",
  ROUND(MARGIN_AT_RISK, 2) AS "Margin at Risk"
FROM RETAIL_DEMO.SERVING.ROOT_CAUSE_EVIDENCE
WHERE 1 = 1
[[AND {{category}}]]
[[AND {{store}}]]
[[AND {{item}}]]
[[AND {{supplier}}]]
ORDER BY IMPACT_RANK;
```

Create `Root Cause Evidence` with this complete SQL:

```sql
SELECT
  IMPACT_RANK AS "Impact Rank",
  BUSINESS_DATE AS "Business Date",
  CATEGORY AS "Category",
  STORE_ID AS "Store ID",
  STORE_NAME AS "Store Name",
  ITEM_ID AS "Item ID",
  ITEM_DESC AS "Item Description",
  SUPPLIER_ID AS "Supplier ID",
  SUPPLIER_NAME AS "Supplier Name",
  ROOT_CAUSE AS "Root Cause",
  ROUND(AVG_DAILY_UNITS, 2) AS "Average Daily Units",
  ON_HAND_QTY AS "On Hand Quantity",
  ON_ORDER_QTY AS "On Order Quantity",
  ROUND(DAYS_OF_SUPPLY, 2) AS "Days of Supply",
  ROUND(FILL_RATE, 4) AS "Fill Rate",
  ROUND(ESTIMATED_LOST_SALES, 2) AS "Estimated Lost Sales",
  ROUND(ESTIMATED_MARGIN_IMPACT, 2) AS "Estimated Margin Impact",
  ROUND(MARGIN_AT_RISK, 2) AS "Margin at Risk"
FROM RETAIL_DEMO.SERVING.ROOT_CAUSE_EVIDENCE
WHERE 1 = 1
[[AND {{category}}]]
[[AND {{store}}]]
[[AND {{item}}]]
[[AND {{supplier}}]]
ORDER BY IMPACT_RANK;
```

Format fill rate as a percentage only if the Metabase format preserves the underlying decimal.
Format the three monetary columns as USD with two decimal places.

## Add reusable SQL field filters

The five query definitions above already contain these optional clauses:

```sql
WHERE 1 = 1
[[AND {{category}}]]
[[AND {{store}}]]
[[AND {{item}}]]
[[AND {{supplier}}]]
```

All five questions must read from `RETAIL_DEMO.SERVING.ROOT_CAUSE_EVIDENCE`. Configure each
variable as a Field Filter, not as a basic Text variable:

| Variable | Field mapping |
| --- | --- |
| `category` | `ROOT_CAUSE_EVIDENCE.CATEGORY` |
| `store` | `ROOT_CAUSE_EVIDENCE.STORE_ID` |
| `item` | `ROOT_CAUSE_EVIDENCE.ITEM_ID` |
| `supplier` | `ROOT_CAUSE_EVIDENCE.SUPPLIER_ID` |

Keep each variable optional and allow multiple values. Field Filter syntax supplies the complete
predicate, so use `[[AND {{store}}]]`; do not write `STORE_ID = {{store}}`.

After each question is edited, run it with every filter empty and choose **Replace original
question** when saving. Do not choose **Save as new question**, which creates duplicate dashboard
cards. Verify:

| Saved question | Empty-filter verification |
| --- | --- |
| `At-Risk Item-Store Count` | one row with `24` |
| `Estimated Lost Sales` | one row with `25,658.28` |
| `Margin at Risk` | one row with `3,631.55` |
| `Ranked Merchant Problems` | `24` rows ordered by `IMPACT_RANK` |
| `Root Cause Evidence` | `24` rows ordered by `IMPACT_RANK` |

For `Ranked Merchant Problems`, select readable `STORE_ID` and `ITEM_ID` from
`ROOT_CAUSE_EVIDENCE` rather than the internal `STORE_SK` and `ITEM_SK` values. Keep the evidence
question's existing friendly columns and number formatting.

## Connect the dashboard filters

Edit the dashboard and add four **Text or Category** filters named `Category`, `Store`, `Item`, and
`Supplier`. Use the `Is` operator, dropdown widgets, multiple values, and no required/default value.
Connect them as follows:

| Dashboard card | Category | Store | Item | Supplier |
| --- | --- | --- | --- | --- |
| At-Risk Item-Store Count | yes | yes | yes | yes |
| Estimated Lost Sales | yes | yes | yes | yes |
| Margin at Risk | yes | yes | yes | yes |
| Category Sales Shortfall Trend | yes | yes | no | no |
| Ranked Merchant Problems | yes | yes | yes | yes |
| Root Cause Evidence | yes | yes | yes | yes |

Save the dashboard, then verify the filter wiring against the deterministic fixture:

1. With no filters, the at-risk KPI is `24` and both detail tables contain `24` rows.
2. Select Store `AAAAAAAABLBAAAAA`. The at-risk KPI and both detail tables must change to `3`; the
   trend must still contain seven business dates.
3. Clear Store and select Item `AAAAAAAAIMIKCAAA`. The at-risk KPI and both detail tables must
   change to `8`.
4. Clear Item, select Supplier `SUP-001`, and confirm the dashboard returns without an error. This
   fixture has one supplier, so the counts remain `24`.
5. Clear every filter and confirm the original `24` / `24` / `24` state is restored.

Verify the Metabase user cannot query `RAW`, `ANALYTICS`, `CONFIG`, or `LAKEHOUSE`. Then continue to
the [demo scenario](11-demo-scenario.md).

After evidence capture, stop the container with
`docker compose --env-file .env -f metabase/docker-compose.yml stop`, suspend `RETAIL_DEMO_WH`, and confirm the
Dynamic Tables remain suspended. The file-backed Metabase application database is for this
disposable local tutorial only, not production use.
