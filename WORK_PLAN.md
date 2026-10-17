# Implementation and Presentation Plan

## Research question

**Across Barcelona's 35 available 2020/21 La Liga matches featuring Lionel Messi, did the team create more and better scoring chances at home or away?**

The measures are shots per match, total expected goals (xG) per match, xG per shot, and actual goals. xG is a model estimate for a shot, not an observed goal or evidence that home status caused a result. The source includes 18 home and 17 away matches, so the comparison uses per-match averages.

## Source coverage and current data status

[StatsBomb's Messi Data Biography](https://blogarchive.statsbomb.com/articles/soccer/welcome-to-the-messi-data-biography/) covers La Liga matches Messi played. It does not represent every Barcelona fixture. Comparison with the [complete 2020/21 results](https://www.football-data.co.uk/mmz4281/2021/SP1.csv) identifies three omitted fixtures: Barcelona–Eibar (29 December 2020), Elche–Barcelona (24 January 2021), and Eibar–Barcelona (22 May 2021). Conclusions must be limited to the 35 included matches.

The source is pinned to Git commit `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`. The extraction script processed all 35 event files and produced:

| Measure | Verified value |
| --- | ---: |
| Matches | 35 (18 home, 17 away) |
| Events | 139,030 |
| Unique event IDs | 139,030 |
| Shots by both teams | 839 |
| Shots without xG | 0 |
| Batch 1 | 17 files, 66,380 events, 433 shots |
| Batch 2 | 18 files, 72,650 events, 406 shots |

The prepared event CSVs total about 9.8 MB. `data/generated/manifest.csv` records the source URL and SHA-256 hash for each match file. The script extracts nine stable fields from the nested source JSON. Fields such as shot freeze frames and pass geometry are outside the research question and are not included in the landing files.

## Work sequence and evidence

Each stage should produce code, a visible Databricks result, and a short explanation suitable for the live presentation.

| Stage | Implementation | Evidence and explanation |
| --- | --- | --- |
| Repository | Create a public GitHub repository and a Databricks Git folder. Develop on a branch. | Explain the pinned data source and why the JSON is reduced to a documented landing schema. |
| Configuration | Use the dedicated `barca_final_project` catalog with `bronze`, `silver`, `gold`, and `security` schemas and a landing volume. Place notebooks in `/Workspace/Users/<your-user>/final_project_module_4`. | Show the catalog structure and explain the role of volumes and schemas. |
| Incremental bronze | Upload only batch 1 and run Auto Loader. Upload batch 2 and rerun. Run once more without new files. | Show 66,380 then 139,030 rows, counts by batch, the source file path, and zero new rows on the third run. Explain `schemaLocation` and the checkpoint. |
| Clean silver | Cast fields, apply event-specific null rules, deduplicate on `event_id`, and join to matches on `match_id`. | Show row counts before and after, unique IDs, rejected records, and match coverage. Explain why xG is null for non-shot events. |
| Analytical gold | Produce one row per team and match, then compare Barcelona's home and away averages. Add enforced `NOT NULL` and `CHECK` rules. | Show the business answer and the literal error from an invalid insert executed outside the scheduled job. Define the gold table's grain. |
| Lakeflow Job | Configure bronze → silver → gold dependencies, a retry, a scheduled trigger, and a successful full run. | Show the task graph and successful run. |
| Governance | Grant a reader only required access, verify with `SHOW GRANTS`, apply a team-based row filter controlled by a principal-to-team mapping table, and tag the email column. | Change the mapping and show the visible rows change. Explain least privilege and why the mapping email is sensitive. |
| Git integration | Merge a pull request from the working branch into `main`. | Show the Git folder and merged pull request. A deployment bundle is recommended by the assignment but not required for its minimum. |
| Observability | Query a project-specific system table, identify the largest event table, apply liquid clustering, run `OPTIMIZE`, and inspect table detail or history. | Show a nonempty system-table result and clustering evidence. Do not claim a performance gain without measurement. |
| Rehearsal | Finish the public README, architecture diagram, run instructions, and screenshots. | Complete the walkthrough in about 15 minutes, leaving time for questions under the 20-minute limit. |

## Questions to rehearse

1. Why does `event_id` deduplicate events while `match_id` joins events to matches?
2. Why is a missing `shot_xg` valid for a pass but invalid for a shot?
3. What proves that Auto Loader did not reload batch 1?
4. What is the grain of the gold table, and how is xG per shot calculated?
5. How do the mapping table and row filter change a reader's result?
6. What proves that Databricks enforced each quality rule?
7. What does `DESCRIBE DETAIL` or `DESCRIBE HISTORY` show after `OPTIMIZE`?

## Presentation run of show

| Time | Topic |
| --- | --- |
| 0:00–1:30 | Question, source, 35-match coverage, and three omitted fixtures. |
| 1:30–2:30 | Architecture from source to volume, bronze, silver, and gold. |
| 2:30–5:00 | Two bronze batches, source paths, and idempotent rerun. |
| 5:00–7:00 | Silver types, null rules, deduplication, join, and metrics. |
| 7:00–9:00 | Gold answer, quality constraints, and rejected row. |
| 9:00–10:30 | Job dependencies, retry, trigger, and successful run. |
| 10:30–12:00 | Grants, column tag, and row-filter mapping change. |
| 12:00–13:00 | Git folder, branch, and merged pull request. |
| 13:00–14:30 | System table, clustering, and `OPTIMIZE`. |
| 14:30–15:00 | Conclusion and certification topic. |

## Target schedule

- **16 October:** Verify the source and extraction; configure Git and Databricks; complete the first bronze run.
- **17 October:** Complete silver and gold and validate their counts.
- **18 October:** Complete the job, governance, pull request, observability, README, and rehearsal.
- **19 or 21 October:** Present, according to the assigned slot.

The working Databricks environment and its visible notebook outputs are the assessed deliverable. The public README supports the live demonstration.
