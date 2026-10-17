# Databricks notebook source
# MAGIC %md
# MAGIC # 04 · Enforced gold quality rules
# MAGIC
# MAGIC Run either SQL cell individually after `03_gold`. Each insert is expected
# MAGIC to fail, leaving the analytical table unchanged. Capture the literal
# MAGIC Delta error as evidence that the rule is enforced.

# COMMAND ----------

# MAGIC %sql
# MAGIC INSERT INTO barca_final_project.gold.match_team_summary
# MAGIC (match_id, team_id, match_date, team_name, opponent_name, venue,
# MAGIC  goals, shot_count, total_xg, xg_per_shot)
# MAGIC VALUES
# MAGIC (NULL, 217, DATE '2020-09-27', 'Barcelona', 'Quality demonstration',
# MAGIC  'home', 0, 1, 0.1, 0.1);

# COMMAND ----------

# MAGIC %sql
# MAGIC INSERT INTO barca_final_project.gold.match_team_summary
# MAGIC (match_id, team_id, match_date, team_name, opponent_name, venue,
# MAGIC  goals, shot_count, total_xg, xg_per_shot)
# MAGIC VALUES
# MAGIC (-999, 217, DATE '2020-09-27', 'Barcelona', 'Quality demonstration',
# MAGIC  'home', 0, -1, 0.0, NULL);
