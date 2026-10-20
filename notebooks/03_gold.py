# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · Match and team scoring chances
# MAGIC
# MAGIC One row represents one team in one match. The table includes both teams
# MAGIC so a row filter can later govern which team a reader can see.

# COMMAND ----------

from pyspark.sql import functions as F

CATALOG = "barca_final_project"
EVENTS = f"{CATALOG}.silver.events_clean"
MATCHES = f"{CATALOG}.silver.matches_clean"
GOLD = f"{CATALOG}.gold.match_team_summary"
BARCELONA_ID = 217

# COMMAND ----------

# Delta enforces the required key and nonnegative analytical values.
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {GOLD} (
        match_id BIGINT NOT NULL,
        team_id BIGINT NOT NULL,
        match_date DATE NOT NULL,
        team_name STRING NOT NULL,
        opponent_name STRING NOT NULL,
        venue STRING NOT NULL,
        goals INT NOT NULL,
        shot_count BIGINT NOT NULL,
        total_xg DOUBLE NOT NULL,
        xg_per_shot DOUBLE
    ) USING DELTA
""")

# Databricks adds named CHECK rules to an existing Delta table.
table_properties = {
    row.key: row.value for row in spark.sql(f"SHOW TBLPROPERTIES {GOLD}").collect()
}
for constraint_name, expression in (
    ("valid_shot_count", "shot_count >= 0"),
    ("valid_total_xg", "total_xg >= 0"),
):
    if f"delta.constraints.{constraint_name}" not in table_properties:
        spark.sql(f"ALTER TABLE {GOLD} ADD CONSTRAINT {constraint_name} CHECK ({expression})")

# COMMAND ----------

matches = spark.table(MATCHES)
home = matches.select(
    "match_id",
    "match_date",
    F.col("home_team_id").alias("team_id"),
    F.col("home_team_name").alias("team_name"),
    F.col("away_team_name").alias("opponent_name"),
    F.lit("home").alias("venue"),
    F.col("home_score").alias("goals"),
)
away = matches.select(
    "match_id",
    "match_date",
    F.col("away_team_id").alias("team_id"),
    F.col("away_team_name").alias("team_name"),
    F.col("home_team_name").alias("opponent_name"),
    F.lit("away").alias("venue"),
    F.col("away_score").alias("goals"),
)
match_teams = home.unionByName(away)

shots = (
    spark.table(EVENTS)
    .filter(F.col("event_type") == "Shot")
    .groupBy("match_id", "team_id")
    .agg(
        F.count("*").alias("shot_count"),
        F.sum("shot_xg").alias("total_xg"),
    )
)

summary = (
    match_teams.join(shots, ["match_id", "team_id"], "left")
    .fillna({"shot_count": 0, "total_xg": 0.0})
    .withColumn(
        "xg_per_shot",
        F.when(F.col("shot_count") > 0, F.col("total_xg") / F.col("shot_count"))
        .otherwise(F.lit(None).cast("double")),
    )
)
summary.createOrReplaceTempView("match_team_summary_new")
spark.sql(f"""
    INSERT OVERWRITE TABLE {GOLD}
    SELECT match_id, team_id, match_date, team_name, opponent_name, venue,
           goals, shot_count, total_xg, xg_per_shot
    FROM match_team_summary_new
""")

# COMMAND ----------

display(spark.sql(f"""
    SELECT venue,
           count(*) AS matches,
           round(avg(shot_count), 2) AS shots_per_match,
           round(avg(total_xg), 3) AS xg_per_match,
           round(sum(total_xg) / nullif(sum(shot_count), 0), 3) AS xg_per_shot,
           round(avg(goals), 2) AS goals_per_match
    FROM {GOLD}
    WHERE team_id = {BARCELONA_ID}
    GROUP BY venue
    ORDER BY venue
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC **Interpreting results:** Total xG per match reflects both chance volume
# MAGIC and chance quality. xG per shot describes average chance quality. These
# MAGIC are descriptive measures for the 35 included matches, not evidence that
# MAGIC playing at home caused a difference.
