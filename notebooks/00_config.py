# Databricks notebook source
# MAGIC %md
# MAGIC # 00 · Workspace configuration
# MAGIC
# MAGIC This project uses a dedicated Unity Catalog catalog. Create the catalog
# MAGIC once in Catalog Explorer with Default Storage, then run these cells to
# MAGIC create its schemas and landing volume.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE SCHEMA IF NOT EXISTS barca_final_project.bronze;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE SCHEMA IF NOT EXISTS barca_final_project.silver;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE SCHEMA IF NOT EXISTS barca_final_project.gold;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE SCHEMA IF NOT EXISTS barca_final_project.security;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE VOLUME IF NOT EXISTS barca_final_project.bronze.landing;

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW SCHEMAS IN barca_final_project;

# COMMAND ----------

# MAGIC %md
# MAGIC **Presentation point:** Schemas separate raw ingestion, validated events,
# MAGIC analytical results, and access-control objects. A managed volume stores the
# MAGIC landing files and Auto Loader metadata in Unity Catalog.
