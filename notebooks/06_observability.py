# Databricks notebook source
# MAGIC %md
# MAGIC # 06 · Job history and table layout
# MAGIC
# MAGIC The project job has ID `967461877121084`. The Lakeflow system table
# MAGIC provides project-specific run evidence. `DESCRIBE DETAIL` measured the
# MAGIC bronze event table at 2,908,730 bytes and the silver event table at
# MAGIC 4,083,491 bytes before optimization, making silver the larger table.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT job_id, run_id, period_start_time, result_state, trigger_type
# MAGIC FROM system.lakeflow.job_run_timeline
# MAGIC WHERE job_id = 967461877121084
# MAGIC ORDER BY period_start_time DESC
# MAGIC LIMIT 10;

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE DETAIL barca_final_project.bronze.events_raw;

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE DETAIL barca_final_project.silver.events_clean;

# COMMAND ----------

# MAGIC %sql
# MAGIC ALTER TABLE barca_final_project.silver.events_clean CLUSTER BY (match_id);

# COMMAND ----------

# MAGIC %sql
# MAGIC OPTIMIZE barca_final_project.silver.events_clean FULL;

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE DETAIL barca_final_project.silver.events_clean;

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE HISTORY barca_final_project.silver.events_clean;

# COMMAND ----------

# MAGIC %md
# MAGIC **Presentation point:** The `clusteringColumns` field should contain
# MAGIC `match_id`. The source is only a few megabytes, so an `OPTIMIZE` run may
# MAGIC rewrite zero files. Do not claim a speed gain without a measured query
# MAGIC comparison. The value here is a documented layout choice and a visible
# MAGIC maintenance operation on the largest project table.
