# Data Dictionary and Transformation Rules

## Prepared event data

Each row represents one recorded event in a match. `prepare_data.py` extracts the fields below from public StatsBomb JSON files without generating new football events.

| Column | Source path | Silver type | Rule |
| --- | --- | --- | --- |
| `event_id` | `id` | STRING | Required business key; unique after deduplication. |
| `match_id` | `events/{match_id}.json` file name | BIGINT | Required join key to match metadata. |
| `event_index` | `index` | INT | Required sequence within a match. |
| `minute` | `minute` | INT | Required and nonnegative. |
| `team_id` | `team.id` | BIGINT | Required for team metrics; Barcelona is ID `217` in this source. |
| `player_id` | `player.id` | BIGINT | May be null for collective events such as Starting XI. |
| `event_type` | `type.name` | STRING | Required; `Shot` identifies shot events. |
| `shot_xg` | `shot.statsbomb_xg` | DOUBLE | Required for a shot, legitimately null for other event types; within [0, 1] when present. |
| `shot_outcome` | `shot.outcome.name` | STRING | Applicable to shots; null for other event types. |

## Match metadata

Each row represents one match from `matches/11/90.json`. The prepared table retains `match_id`, date, home and away team IDs and names, score, opponent, Barcelona home/away status, and Barcelona's result. The source contains 35 matches featuring Messi: 18 home and 17 away. Three other Barcelona league matches are outside this collection.

## Join and analytical grain

`events.match_id = matches.match_id` is a many-to-one relationship. If no labeled test input is added, the cleaned event table should contain 139,030 rows; Databricks must verify this after incremental ingestion.

The gold table has one row per **team per match**:

- `shot_count`: number of events where `event_type = 'Shot'`.
- `total_xg`: sum of xG across those shots.
- `xg_per_shot`: `total_xg / shot_count`, null when a team has no shots.
- `goals`: the actual score for that team, selected from the home or away score.

The primary comparison filters Barcelona's team ID and calculates home and away averages **per match**. The 839 extracted shots include both Barcelona and its opponents.

## Interpreting expected goals

xG is StatsBomb's estimated probability of a goal for an individual shot. An xG value of 0.20 represents an estimated 20% scoring probability for that chance. Summed xG reflects chance volume and quality together; xG per shot isolates average chance quality. These measures are distinct from observed goals and stadium attendance.
