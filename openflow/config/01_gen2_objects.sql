-- Phase 1: create the gen 2 control objects and AWS workload-identity trust
-- anchor. Run through a connection whose PAT is restricted to OPENFLOW_ADMIN.
-- Do not add USE ROLE: Snowflake prohibits role switching in a role-restricted
-- PAT session. This script deliberately does not create a runtime: the AWS OIDC
-- trust policy must be configured from DESC SECRET output first, and an active
-- runtime consumes credits.
--
-- Required Snowflake CLI definitions:
--   aws_region: region containing the tutorial S3 bucket, for example us-east-2.

CREATE DATABASE IF NOT EXISTS RETAIL_DEMO_OPENFLOW_CONTROL;
CREATE SCHEMA IF NOT EXISTS RETAIL_DEMO_OPENFLOW_CONTROL.RUNTIME;
GRANT CREATE OPENFLOW RUNTIME ON SCHEMA RETAIL_DEMO_OPENFLOW_CONTROL.RUNTIME
  TO ROLE OPENFLOW_ADMIN;
GRANT CREATE OPENFLOW CONNECTOR ON SCHEMA RETAIL_DEMO_OPENFLOW_CONTROL.RUNTIME
  TO ROLE OPENFLOW_ADMIN;

CREATE SECRET IF NOT EXISTS
  RETAIL_DEMO_OPENFLOW_CONTROL.RUNTIME.RETAIL_DEMO_AWS_WIF
  TYPE = WORKLOAD_IDENTITY_FEDERATION
  COMMENT = 'OIDC trust anchor for Openflow read-only access to tutorial S3 files';

CREATE NETWORK RULE IF NOT EXISTS
  RETAIL_DEMO_OPENFLOW_CONTROL.RUNTIME.RETAIL_DEMO_OPENFLOW_S3_NETWORK_RULE
  MODE = EGRESS
  TYPE = HOST_PORT
  VALUE_LIST = (
    'sts.<% aws_region %>.amazonaws.com:443',
    's3.<% aws_region %>.amazonaws.com:443',
    's3.amazonaws.com:443',
    '*.s3.<% aws_region %>.amazonaws.com:443',
    '*.s3.amazonaws.com:443'
  )
  COMMENT = 'Exact AWS STS and S3 egress required by the tutorial Openflow runtime';

CREATE EXTERNAL ACCESS INTEGRATION IF NOT EXISTS RETAIL_DEMO_OPENFLOW_S3_EAI
  ALLOWED_NETWORK_RULES = (
    RETAIL_DEMO_OPENFLOW_CONTROL.RUNTIME.RETAIL_DEMO_OPENFLOW_S3_NETWORK_RULE
  )
  ENABLED = TRUE
  COMMENT = 'Egress only; AWS authentication is provided separately through WIF';

GRANT USAGE ON DATABASE RETAIL_DEMO_OPENFLOW_CONTROL
  TO ROLE OPENFLOW_RETAIL_DEMO_EXECUTE_AS_RL;
GRANT USAGE ON SCHEMA RETAIL_DEMO_OPENFLOW_CONTROL.RUNTIME
  TO ROLE OPENFLOW_RETAIL_DEMO_EXECUTE_AS_RL;
GRANT USAGE ON SECRET
  RETAIL_DEMO_OPENFLOW_CONTROL.RUNTIME.RETAIL_DEMO_AWS_WIF
  TO ROLE OPENFLOW_RETAIL_DEMO_EXECUTE_AS_RL;
GRANT USAGE ON INTEGRATION RETAIL_DEMO_OPENFLOW_S3_EAI
  TO ROLE OPENFLOW_RETAIL_DEMO_EXECUTE_AS_RL;

CREATE OPENFLOW DEPLOYMENT IF NOT EXISTS RETAIL_DEMO_OPENFLOW
  DEPLOYMENT_TYPE = SNOWFLAKE
  DISPLAY_NAME = 'Retail demo gen 2 deployment'
  COMMENT = 'Disposable Openflow deployment for the merchant tutorial';

SELECT SYSTEM$WAIT_FOR_OPENFLOW_DEPLOYMENT_STATUS(
  900,
  'ACTIVE',
  'RETAIL_DEMO_OPENFLOW'
);

-- Record only the issuer and subject in the operator's private deployment
-- notes. They are identifiers, not credentials. Do not commit account values.
DESC SECRET RETAIL_DEMO_OPENFLOW_CONTROL.RUNTIME.RETAIL_DEMO_AWS_WIF;
DESC OPENFLOW DEPLOYMENT RETAIL_DEMO_OPENFLOW;
