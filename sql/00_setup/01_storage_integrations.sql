-- Account-level bootstrap. Use one dedicated AWS IAM role limited to the two
-- tutorial prefixes. Snowflake generates identity values shown by DESCRIBE.
USE ROLE ACCOUNTADMIN;

CREATE STORAGE INTEGRATION IF NOT EXISTS RETAIL_DEMO_S3_INTEGRATION
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  STORAGE_AWS_ROLE_ARN = '<% aws_role_arn %>'
  ENABLED = TRUE
  STORAGE_ALLOWED_LOCATIONS = ('<% s3_landing_url %>');

CREATE EXTERNAL VOLUME IF NOT EXISTS RETAIL_DEMO_EXT_VOL
  STORAGE_LOCATIONS =
  (
    (
      NAME = 'retail-demo-s3'
      STORAGE_PROVIDER = 'S3'
      STORAGE_BASE_URL = '<% s3_iceberg_url %>'
      STORAGE_AWS_ROLE_ARN = '<% aws_role_arn %>'
      ENCRYPTION = (TYPE = 'AWS_SSE_S3')
    )
  )
  ALLOW_WRITES = TRUE
  COMMENT = 'Writable S3 storage for tutorial Iceberg tables';

GRANT USAGE ON INTEGRATION RETAIL_DEMO_S3_INTEGRATION TO ROLE RETAIL_DEMO_ENGINEER;
GRANT USAGE ON EXTERNAL VOLUME RETAIL_DEMO_EXT_VOL TO ROLE RETAIL_DEMO_ENGINEER;

DESCRIBE INTEGRATION RETAIL_DEMO_S3_INTEGRATION;
DESCRIBE EXTERNAL VOLUME RETAIL_DEMO_EXT_VOL;

-- Stop here. Add the returned Snowflake IAM principal and external ID values
-- to the AWS role trust policy before running 02_stage_objects.sql.
