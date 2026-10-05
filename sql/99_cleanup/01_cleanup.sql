-- Destructive by design. This targets only the fixed tutorial database,
-- warehouse, monitor, integration, external volume, and roles.
USE ROLE ACCOUNTADMIN;

DROP DATABASE IF EXISTS RETAIL_DEMO;
DROP WAREHOUSE IF EXISTS RETAIL_DEMO_WH;
DROP RESOURCE MONITOR IF EXISTS RETAIL_DEMO_MONITOR;
DROP STORAGE INTEGRATION IF EXISTS RETAIL_DEMO_S3_INTEGRATION;
DROP EXTERNAL VOLUME IF EXISTS RETAIL_DEMO_EXT_VOL;
DROP ROLE IF EXISTS RETAIL_DEMO_STREAMER;
DROP ROLE IF EXISTS RETAIL_DEMO_METABASE;
DROP ROLE IF EXISTS RETAIL_DEMO_ENGINEER;

-- Openflow deployments/runtimes are intentionally excluded. Stop and remove
-- only the named resources recorded during setup by following docs/13-cleanup.md.
-- S3 deletion is also a separate, explicit AWS step.
