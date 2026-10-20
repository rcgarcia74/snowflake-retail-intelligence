-- One-time setup for the isolated CoCo incident lab.
-- This script creates only RETAIL_DEMO_COCO_LAB. It never changes RETAIL_DEMO.
-- Stop if the lab already exists; use 98_cleanup_sandbox.sql only after explicit approval.

USE ROLE ACCOUNTADMIN;

CREATE DATABASE RETAIL_DEMO_COCO_LAB
  COMMENT = 'Isolated business-date contract incident lab for the retail tutorial';

GRANT OWNERSHIP ON DATABASE RETAIL_DEMO_COCO_LAB
  TO ROLE RETAIL_DEMO_ENGINEER
  COPY CURRENT GRANTS;
