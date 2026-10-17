# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Incremental bronze ingestion
# MAGIC
# MAGIC Auto Loader ingests one prepared CSV per match from the Unity Catalog volume.
# MAGIC Each row retains its source path. Run this notebook after uploading batch 1,
# MAGIC again after uploading batch 2, and once more without new files.

# COMMAND ----------

from pyspark.sql import functions as F

CATALOG = "barca_final_project"
VOLUME = f"/Volumes/{CATALOG}/bronze/landing"
EVENTS_SOURCE = f"{VOLUME}/events"
MATCHES_SOURCE = f"{VOLUME}/matches/matches_2020_21.csv"
SCHEMA_LOCATION = f"{VOLUME}/_schemas/events"
CHECKPOINT_LOCATION = f"{VOLUME}/_checkpoints/events"
EVENTS_TABLE = f"{CATALOG}.bronze.events_raw"
MATCHES_TABLE = f"{CATALOG}.bronze.matches_raw"

# COMMAND ----------

# Keep raw CSV values as strings. Silver is responsible for type conversion and validation.
query = (
    spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "csv")
    .option("cloudFiles.schemaLocation", SCHEMA_LOCATION)
    .option("cloudFiles.inferColumnTypes", "false")
    .option("header", "true")
    .option("pathGlobFilter", "*.csv")
    .load(EVENTS_SOURCE)
    .withColumn("source_file", F.col("_metadata.file_path"))
    .withColumn("ingested_at", F.current_timestamp())
    .writeStream
    .option("checkpointLocation", CHECKPOINT_LOCATION)
    .trigger(availableNow=True)
    .toTable(EVENTS_TABLE)
)
query.awaitTermination()

# COMMAND ----------

# The match file is a small, versioned reference dataset. Overwriting it is idempotent.
(
    spark.read.option("header", "true").option("inferSchema", "false")
    .csv(MATCHES_SOURCE)
    .withColumn("source_file", F.lit(MATCHES_SOURCE))
    .write.mode("overwrite")
    .saveAsTable(MATCHES_TABLE)
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Incremental ingestion evidence
# MAGIC
# MAGIC Expected counts: batch 1 = 66,380 rows; batch 2 = 72,650 rows.
# MAGIC After both uploads, the total is 139,030. A rerun without new files
# MAGIC leaves these counts unchanged.

# COMMAND ----------

display(spark.sql(f"""
    SELECT regexp_extract(source_file, 'lote_[12]', 0) AS batch,
           count(*) AS event_rows,
           count(DISTINCT source_file) AS source_files,
           min(ingested_at) AS first_ingested_at
    FROM {EVENTS_TABLE}
    GROUP BY 1
    ORDER BY 1
"""))

# COMMAND ----------

display(spark.sql(f"""
    SELECT count(*) AS total_event_rows,
           count(DISTINCT event_id) AS unique_event_ids,
           count(DISTINCT match_id) AS covered_matches
    FROM {EVENTS_TABLE}
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC **Presentation point:** `schemaLocation` tracks the discovered CSV schema,
# MAGIC while the streaming checkpoint records processed files. Their separate paths
# MAGIC make the two responsibilities visible. The source path proves which batch
# MAGIC produced each bronze row.
