# Execution evidence

This document records results observed in the dedicated Databricks catalog `barca_final_project`. The project job is [barca_final_project_pipeline](https://dbc-cbc2bb58-ee6e.cloud.databricks.com/?o=7474647652788276#job/967461877121084), with dependent bronze, silver, and gold notebook tasks and one retry configured on bronze.

## Incremental ingestion

| Run | Input state | Bronze rows | Distinct event IDs | Source files |
| --- | --- | ---: | ---: | ---: |
| [First load](https://dbc-cbc2bb58-ee6e.cloud.databricks.com/?o=7474647652788276#job/967461877121084/run/160139310901670) | 17 batch 1 files | 66,380 | 66,380 | 17 |
| [Second load](https://dbc-cbc2bb58-ee6e.cloud.databricks.com/?o=7474647652788276#job/967461877121084/run/886099939724966) | 18 additional batch 2 files | 139,030 | 139,030 | 35 |
| [Full three-task run](https://dbc-cbc2bb58-ee6e.cloud.databricks.com/?o=7474647652788276#job/967461877121084/run/827648114393328) | No new files | 139,030 | 139,030 | 35 |

Batch 1 contributes 66,380 rows from 17 files. Batch 2 contributes 72,650 rows from 18 files. The unchanged count after another bronze run demonstrates that the Auto Loader checkpoint prevented reprocessing.

## Validation and analytical result

| Silver metric | Value |
| --- | ---: |
| Raw event rows | 139,030 |
| Invalid event rows | 0 |
| Duplicate event rows | 0 |
| Unmatched event rows | 0 |
| Clean event rows | 139,030 |
| Clean match rows | 35 |

The gold table contains 70 team-match rows and 839 shots across both teams. Barcelona's 18 home matches average 16.11 shots, 2.193 xG, 0.136 xG per shot, and 2.39 goals. Its 17 away matches average 14.88 shots, 1.914 xG, 0.129 xG per shot, and 2.24 goals.

Two invalid inserts were rejected by Delta:

```text
[DELTA_NOT_NULL_CONSTRAINT_VIOLATED] NOT NULL constraint violated for column: match_id.
[DELTA_VIOLATE_CONSTRAINT_WITH_VALUES] CHECK constraint valid_shot_count (shot_count >= 0) violated by row with values: shot_count : -1.
```

## Governance

`SHOW GRANTS ON TABLE barca_final_project.gold.match_team_summary_secured` returns `account users | SELECT` for that table. The related grants permit `USE CATALOG` and `USE SCHEMA` on `gold`; they do not grant reader access to bronze, silver, or `security.team_access`. The `principal_email` mapping column is tagged `classification = email`.

The protected table returned 35 Barcelona rows with the current user's mapping set to team `217`. Updating that mapping to Villarreal (`222`) returned two rows. Restoring `217` returned the 35 Barcelona rows again. Unmapped principals receive no rows from the row filter.

## System table and optimization

`system.lakeflow.job_run_timeline` returned project job ID `967461877121084` and the successful run ID `827648114393328`. The job has an active file arrival trigger on `/Volumes/barca_final_project/bronze/landing/events/`.

Before optimization, `DESCRIBE DETAIL` reported 4,083,491 bytes for `silver.events_clean` and 2,908,730 bytes for `bronze.events_raw`. Silver was therefore the largest project table. It now reports `clusteringColumns = ["match_id"]` after `ALTER TABLE ... CLUSTER BY (match_id)` and `OPTIMIZE ... FULL`. The optimization rewrote no files because the small table already occupied one file. This is configuration and maintenance evidence, not a measured performance improvement.
