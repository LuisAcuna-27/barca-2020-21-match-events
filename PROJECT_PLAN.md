# Final project: Barça 2020/21 match events

## Research question

**Question:** In the 2020/21 La Liga matches in which Messi played and that are available in StatsBomb Open Data, did Barça generate more and better scoring chances at home or away?

The project uses a dedicated Databricks workspace folder at `/Workspace/Users/<your-user>/final_project_module_4` and a dedicated Unity Catalog catalog, `barca_final_project`.

## Why this dataset fits the course

[StatsBomb Open Data](https://github.com/hudl/open-data) publishes competitions, matches, and event JSON files with stable IDs. This La Liga subset belongs to its [Messi Data Biography](https://blogarchive.statsbomb.com/articles/soccer/welcome-to-the-messi-data-biography/), which covers matches Messi played. At pinned source commit `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`, its La Liga 2020/21 file (`competition_id=11`, `season_id=90`) contains **35 Barcelona matches**. We extracted **139,030 events**, including **839 shots** by both teams, and verified that all 139,030 event IDs are unique and every shot has an xG value. Barça played 38 league matches; the source omits three without Messi, so we must not describe this as the full season.

Comparing the 35 StatsBomb dates with the [full 2020/21 results CSV](https://www.football-data.co.uk/mmz4281/2021/SP1.csv) identifies the absent fixtures: **Barcelona–Eibar (29 Dec 2020), Elche–Barcelona (24 Jan 2021), and Eibar–Barcelona (22 May 2021)**. This is a source-coverage limitation, not a failed download or a cleaning error. It may affect the home/away comparison, so conclusions apply only to the 35 included matches.

Source paths:

- [Competition catalog](https://github.com/hudl/open-data/blob/master/data/competitions.json)
- [La Liga 2020/21 match metadata](https://github.com/hudl/open-data/blob/master/data/matches/11/90.json)
- Event files: `data/events/{match_id}.json` in the same repository
- [Dataset documentation and attribution terms](https://github.com/hudl/open-data#readme)

Pin a source Git commit for reproducibility. The README and presentation will credit StatsBomb and include its logo as its repository terms request. The final public repository will contain transformation code, a small sample or manifest, and source links; large raw event files can be fetched by the setup script.

## Data model and ingestion

Download the 35 match-event JSON files using the published `match_id` values. A local preparation script flattens **only nine leaf fields** into one CSV per match: `event_id`, `match_id`, `event_index`, `minute`, `team_id`, `player_id`, `event_type`, `shot_xg`, and `shot_outcome`. It ignores nested arrays such as `freeze_frame`, coordinates, and pass details because the question does not use them. `shot_xg` and `shot_outcome` are correctly null for non-shot events; `player_id` may be null for events such as Starting XI. A second small CSV contains match metadata, scores, home/away team IDs, opponent, and date. All analytical values remain sourced from StatsBomb; flattening changes their shape only. The script records each source URL and pinned source commit in a manifest.

Split the per-match event files into **batch 1 (17 matches, 66,380 events)** and **batch 2 (18 matches, 72,650 events)**. Give files a visible `lote_1_` or `lote_2_` prefix so counts by `_metadata.file_path` prove which batch arrived. Place batch 1 in the Unity Catalog volume, run Auto Loader, then add batch 2 and rerun. Keep the file path in bronze and separate `schemaLocation` and checkpoint paths. A third run without new files should add zero rows. The match metadata file loads to a second bronze table.

Silver casts IDs and numeric fields, treats event-specific nulls explicitly (including `shot_xg` null for non-shots), deduplicates by `event_id`, and joins events to matches by the published `match_id`. Its metrics show raw/clean row counts, duplicate and invalid counts, number of matched events, and coverage of the 35 available matches. An optional labeled test-input file can demonstrate a duplicate or invalid row without altering the canonical source files.

Gold produces one row per match and team with shot count, summed shot xG, xG per shot, actual goals, date, opponent, home/away status, and result. The business answer focuses on Barça, but the table retains both teams so governance can filter team access. Compare **per-match averages** because the available home and away match counts may differ. This is a descriptive comparison; xG is StatsBomb's model output and is not a causal explanation for results.

## Mapping to the final-project rubric

| Requirement | Demonstration |
| --- | --- |
| V1 Bronze | Auto Loader CSV ingestion from a volume, schema location, source-file path, two batch counts, idempotent rerun. |
| V2 Silver | Typed event fields, event-specific null rules, `event_id` deduplication, event-to-match join, before/after metrics. |
| C1 Gold and quality | Match-team summary with `match_id NOT NULL` and `shot_count >= 0` enforced by Delta; a separate manual invalid insert captures the literal error. |
| C2 Orchestration | Lakeflow Job with dependent bronze → silver → gold tasks, a retry on at least one task, a scheduled trigger, and one successful complete run. |
| C3 Governance | Layered catalog schemas, least-privilege reader grants with `SHOW GRANTS`, a `principal_email` → `team_id` mapping controlling a gold row filter, and a sensitive-data tag on `principal_email`. Change a mapping row and show the filtered result change. The mapping is a demonstration of access control on public sports data. |
| C4 CI/CD | Databricks Git folder, branch, merged pull request, public README. A bundle is optional because the brief recommends it but does not require it. |
| C5 Observability and optimization | A nonempty project-specific system-table query; compare event-table sizes after loading, apply liquid clustering to the **largest table** by `match_id` or `team_id`, run `OPTIMIZE`, and capture `DESCRIBE DETAIL` or `DESCRIBE HISTORY` evidence. |

## Presentation and trade-offs

Show the two batches, the match/event join, one Barça shot/xG result, the rejected row, the job graph and successful run, governance, merged PR, and observability evidence within 20 minutes. The public README needs the problem, sources, architecture diagram, selected components, design decisions, run order, and screenshots; notebook-cell outputs are the live evidence. Explain that the dataset is a historical subset of Barça matches, not current-season or ticket data.

**Advantages over attendance:** Fully downloadable source files, around 100,000 or more real event rows, natural published join key, and a meaningful large table for clustering. No manual collection of 19 web pages.

**Costs:** Nested event JSON needs a small flattening script; event-specific nulls require careful explanation; xG must be described accurately. Governance is an access-control demonstration because the source is public.

## Expected preparation time

Allow approximately **2–4 hours** for source download, flattening, schema design, and a local reconciliation of counts. Databricks notebooks, job, governance, Git, and presentation evidence are additional work. This estimate should be revisited after a first full extraction.
