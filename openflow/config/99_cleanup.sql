-- Final role cleanup. Run through the ACCOUNTADMIN connection only after
-- 98_cleanup_objects.sql succeeds through the OPENFLOW_ADMIN connection.

USE ROLE ACCOUNTADMIN;
DROP ROLE IF EXISTS OPENFLOW_RETAIL_DEMO_EXECUTE_AS_RL;
DROP ROLE IF EXISTS OPENFLOW_ADMIN;
