# Databricks notebook source
# MAGIC %md
# MAGIC # 05 · Catalog access and team-level visibility
# MAGIC
# MAGIC The analytical table retains enforced Delta quality constraints. A
# MAGIC separate gold snapshot supports a row filter, because Databricks does
# MAGIC not allow a row filter on a table that has CHECK constraints. Access to
# MAGIC the snapshot is restricted to a table-level SELECT grant and a mapping
# MAGIC lookup for the invoking principal.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS barca_final_project.security.team_access (
# MAGIC   principal_email STRING NOT NULL,
# MAGIC   team_id BIGINT NOT NULL
# MAGIC ) USING DELTA;

# COMMAND ----------

# MAGIC %sql
# MAGIC MERGE INTO barca_final_project.security.team_access AS target
# MAGIC USING (SELECT current_user() AS principal_email, CAST(217 AS BIGINT) AS team_id) AS source
# MAGIC ON target.principal_email = source.principal_email
# MAGIC WHEN MATCHED THEN UPDATE SET team_id = source.team_id
# MAGIC WHEN NOT MATCHED THEN INSERT (principal_email, team_id)
# MAGIC VALUES (source.principal_email, source.team_id);

# COMMAND ----------

# MAGIC %sql
# MAGIC ALTER TABLE barca_final_project.security.team_access
# MAGIC ALTER COLUMN principal_email SET TAGS ('classification' = 'email');

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS barca_final_project.gold.match_team_summary_secured
# MAGIC AS SELECT * FROM barca_final_project.gold.match_team_summary;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE FUNCTION IF NOT EXISTS barca_final_project.security.can_read_team(team_value BIGINT)
# MAGIC RETURNS BOOLEAN
# MAGIC RETURN EXISTS (
# MAGIC   SELECT 1 FROM barca_final_project.security.team_access AS access
# MAGIC   WHERE access.principal_email = current_user()
# MAGIC     AND access.team_id = team_value
# MAGIC );

# COMMAND ----------

# MAGIC %sql
# MAGIC ALTER TABLE barca_final_project.gold.match_team_summary_secured
# MAGIC SET ROW FILTER barca_final_project.security.can_read_team ON (team_id);

# COMMAND ----------

# MAGIC %sql
# MAGIC GRANT USE CATALOG ON CATALOG barca_final_project TO `account users`;

# COMMAND ----------

# MAGIC %sql
# MAGIC GRANT USE SCHEMA ON SCHEMA barca_final_project.gold TO `account users`;

# COMMAND ----------

# MAGIC %sql
# MAGIC GRANT SELECT ON TABLE barca_final_project.gold.match_team_summary_secured
# MAGIC TO `account users`;

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW GRANTS ON TABLE barca_final_project.gold.match_team_summary_secured;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT count(*) AS visible_rows, min(team_id) AS team_id
# MAGIC FROM barca_final_project.gold.match_team_summary_secured;

# COMMAND ----------

# MAGIC %md
# MAGIC The mapping table initially selects Barcelona (`team_id = 217`), which
# MAGIC yields 35 rows. To demonstrate dynamic access, run the next two cells:
# MAGIC the first changes the mapping to Villarreal (`team_id = 222`), whose two
# MAGIC rows become visible; the second restores the Barcelona mapping. The
# MAGIC reader grant does not include bronze, silver, or the mapping table.

# COMMAND ----------

# MAGIC %sql
# MAGIC UPDATE barca_final_project.security.team_access
# MAGIC SET team_id = 222 WHERE principal_email = current_user();

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT count(*) AS visible_rows, min(team_id) AS team_id
# MAGIC FROM barca_final_project.gold.match_team_summary_secured;

# COMMAND ----------

# MAGIC %sql
# MAGIC UPDATE barca_final_project.security.team_access
# MAGIC SET team_id = 217 WHERE principal_email = current_user();

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT count(*) AS visible_rows, min(team_id) AS team_id
# MAGIC FROM barca_final_project.gold.match_team_summary_secured;
