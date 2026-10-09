-- Phase 2: run only after the AWS OIDC provider and read-only IAM role trust
-- have been configured from the WIF issuer and subject returned by
-- 01_gen2_objects.sql. Run through the role-restricted OPENFLOW_ADMIN
-- connection; do not add USE ROLE. Creating this runtime starts billable S1
-- compute.

USE DATABASE RETAIL_DEMO_OPENFLOW_CONTROL;
USE SCHEMA RUNTIME;

CREATE OPENFLOW RUNTIME IF NOT EXISTS RETAIL_DEMO_RUNTIME
  IN DEPLOYMENT RETAIL_DEMO_OPENFLOW
  NODE_TYPE = SMALL
  NODE_TYPE_TIER = 'S1'
  MIN_NODES = 1
  MAX_NODES = 1
  EXECUTE_AS_ROLE = OPENFLOW_RETAIL_DEMO_EXECUTE_AS_RL
  EXTERNAL_ACCESS_INTEGRATIONS = (RETAIL_DEMO_OPENFLOW_S3_EAI)
  DISPLAY_NAME = 'Retail demo runtime'
  COMMENT = 'Single-node disposable runtime for four staged operational feeds';

SELECT SYSTEM$WAIT_FOR_OPENFLOW_RUNTIME_STATUS(
  900,
  'ACTIVE',
  'RETAIL_DEMO_OPENFLOW_CONTROL.RUNTIME.RETAIL_DEMO_RUNTIME'
);

DESC OPENFLOW RUNTIME RETAIL_DEMO_RUNTIME;
