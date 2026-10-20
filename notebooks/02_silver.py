# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Validated match events
# MAGIC
# MAGIC Convert raw strings to documented types, reject records that violate
# MAGIC field-specific rules, deduplicate by `event_id`, and join events to their
# MAGIC match metadata through `match_id`.

# COMMAND ----------

from pyspark.sql import Window, functions as F

CATALOG = "barca_final_project"
RAW_EVENTS = f"{CATALOG}.bronze.events_raw"
RAW_MATCHES = f"{CATALOG}.bronze.matches_raw"
CLEAN_EVENTS = f"{CATALOG}.silver.events_clean"
CLEAN_MATCHES = f"{CATALOG}.silver.matches_clean"
QUALITY_METRICS = f"{CATALOG}.silver.quality_metrics"

# COMMAND ----------

# The match file has one row per game. The source identifiers make this join
# many events to one match, so repeated match_id values in events are expected.
matches = (
    spark.table(RAW_MATCHES)
    .select(
        F.col("match_id").cast("long").alias("match_id"),
        F.to_date("match_date").alias("match_date"),
        F.col("home_team_id").cast("long").alias("home_team_id"),
        F.col("home_team_name"),
        F.col("away_team_id").cast("long").alias("away_team_id"),
        F.col("away_team_name"),
        F.col("home_score").cast("int").alias("home_score"),
        F.col("away_score").cast("int").alias("away_score"),
        F.col("barca_home").cast("boolean").alias("barca_home"),
        F.col("opponent_name"),
        F.col("barca_result"),
    )
    .filter(
        F.col("match_id").isNotNull()
        & F.col("match_date").isNotNull()
        & F.col("home_team_id").isNotNull()
        & F.col("away_team_id").isNotNull()
        & F.col("home_score").isNotNull()
        & F.col("away_score").isNotNull()
    )
    .dropDuplicates(["match_id"])
)
matches.write.mode("overwrite").saveAsTable(CLEAN_MATCHES)

# COMMAND ----------

events = (
    spark.table(RAW_EVENTS)
    .select(
        F.trim("event_id").alias("event_id"),
        F.col("match_id").cast("long").alias("match_id"),
        F.col("event_index").cast("int").alias("event_index"),
        F.col("minute").cast("int").alias("minute"),
        F.col("team_id").cast("long").alias("team_id"),
        F.col("player_id").cast("long").alias("player_id"),
        F.trim("event_type").alias("event_type"),
        F.col("shot_xg").cast("double").alias("shot_xg"),
        F.col("shot_outcome"),
        F.col("source_file"),
        F.col("ingested_at"),
    )
)

validity = (
    F.col("event_id").isNotNull()
    & (F.length("event_id") > 0)
    & F.col("match_id").isNotNull()
    & F.col("event_index").isNotNull()
    & F.col("minute").isNotNull()
    & (F.col("minute") >= 0)
    & F.col("team_id").isNotNull()
    & F.col("event_type").isNotNull()
    & (F.length("event_type") > 0)
    & (
        (F.col("event_type") != "Shot")
        | (
            F.col("shot_xg").isNotNull()
            & F.col("shot_xg").between(0.0, 1.0)
        )
    )
)

valid_events = events.filter(validity)
invalid_count = events.filter(~validity).count()

# Retain a deterministic copy if the same business key appears more than once.
dedup_window = Window.partitionBy("event_id").orderBy(
    F.col("ingested_at").desc(), F.col("source_file").asc()
)
deduplicated = (
    valid_events.withColumn("row_number", F.row_number().over(dedup_window))
    .filter(F.col("row_number") == 1)
    .drop("row_number")
)

joined = deduplicated.join(F.broadcast(matches), "match_id", "inner")
if spark.catalog.tableExists(CLEAN_EVENTS):
    joined.createOrReplaceTempView("clean_events_new")
    spark.sql(f"INSERT OVERWRITE TABLE {CLEAN_EVENTS} SELECT * FROM clean_events_new")
else:
    joined.write.mode("overwrite").saveAsTable(CLEAN_EVENTS)

# COMMAND ----------

raw_count = spark.table(RAW_EVENTS).count()
valid_count = valid_events.count()
unique_count = deduplicated.count()
joined_count = spark.table(CLEAN_EVENTS).count()

metric_rows = [
    ("raw_event_rows", raw_count),
    ("invalid_event_rows", invalid_count),
    ("valid_event_rows", valid_count),
    ("duplicate_event_rows", valid_count - unique_count),
    ("unmatched_event_rows", unique_count - joined_count),
    ("clean_event_rows", joined_count),
    ("clean_match_rows", spark.table(CLEAN_MATCHES).count()),
]
spark.createDataFrame(metric_rows, ["metric", "value"]).write.mode("overwrite").saveAsTable(
    QUALITY_METRICS
)
display(spark.table(QUALITY_METRICS).orderBy("metric"))

# COMMAND ----------

# MAGIC %md
# MAGIC **Business keys and nulls:** `event_id` is the event deduplication key.
# MAGIC Repeated `match_id` values are expected and provide the many-to-one link
# MAGIC to match metadata. A null `shot_xg` is valid for a non-shot event.
