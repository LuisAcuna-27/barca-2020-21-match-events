"""Prepare public StatsBomb match events for incremental Databricks ingestion.

Usage: python prepare_data.py

The source is pinned to a specific Git commit. The script extracts nine fields
needed for the analysis and writes one CSV per match. File names identify two
ingestion batches. All match, event, shot, and xG values come from the source.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


SOURCE_COMMIT = "4b73468fc5b0f1950f9f66fada70ad3a4f9327cb"
BASE_URL = f"https://raw.githubusercontent.com/hudl/open-data/{SOURCE_COMMIT}/data"
MATCHES_URL = f"{BASE_URL}/matches/11/90.json"
BARCA_TEAM_ID = 217

EVENT_COLUMNS = (
    "event_id", "match_id", "event_index", "minute", "team_id",
    "player_id", "event_type", "shot_xg", "shot_outcome",
)
MATCH_COLUMNS = (
    "match_id", "match_date", "home_team_id", "home_team_name",
    "away_team_id", "away_team_name", "home_score", "away_score",
    "barca_home", "opponent_name", "barca_goals", "opponent_goals",
    "barca_result",
)
MANIFEST_COLUMNS = (
    "batch", "match_id", "match_date", "event_file", "event_rows",
    "shot_rows", "shots_without_xg", "source_url", "source_sha256",
    "retrieved_at_utc",
)


def fetch_json(url: str) -> tuple[object, bytes]:
    """Download a JSON document with bounded retries and return its raw bytes."""
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            request = Request(url, headers={"User-Agent": "barca-databricks-course-project/1.0"})
            with urlopen(request, timeout=60) as response:
                raw = response.read()
            return json.loads(raw), raw
        except Exception as error:
            last_error = error
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Could not download {url}: {last_error}")


def nested_name(value: object) -> str | None:
    return value.get("name") if isinstance(value, dict) else None


def nested_id(value: object) -> int | None:
    return value.get("id") if isinstance(value, dict) else None


def match_row(match: dict) -> dict:
    home = match["home_team"]
    away = match["away_team"]
    barca_home = home["home_team_id"] == BARCA_TEAM_ID
    barca_away = away["away_team_id"] == BARCA_TEAM_ID
    if not (barca_home or barca_away):
        raise ValueError(f"Match {match['match_id']} does not include Barcelona")

    barca_goals = match["home_score"] if barca_home else match["away_score"]
    opponent_goals = match["away_score"] if barca_home else match["home_score"]
    opponent_name = away["away_team_name"] if barca_home else home["home_team_name"]
    result = "W" if barca_goals > opponent_goals else "L" if barca_goals < opponent_goals else "D"
    return {
        "match_id": match["match_id"],
        "match_date": match["match_date"],
        "home_team_id": home["home_team_id"],
        "home_team_name": home["home_team_name"],
        "away_team_id": away["away_team_id"],
        "away_team_name": away["away_team_name"],
        "home_score": match["home_score"],
        "away_score": match["away_score"],
        "barca_home": barca_home,
        "opponent_name": opponent_name,
        "barca_goals": barca_goals,
        "opponent_goals": opponent_goals,
        "barca_result": result,
    }


def event_row(event: dict, match_id: int) -> dict:
    shot = event.get("shot") or {}
    return {
        "event_id": event.get("id"),
        "match_id": match_id,  # The source uses the match ID as the JSON file name.
        "event_index": event.get("index"),
        "minute": event.get("minute"),
        "team_id": nested_id(event.get("team")),
        "player_id": nested_id(event.get("player")),
        "event_type": nested_name(event.get("type")),
        "shot_xg": shot.get("statsbomb_xg"),
        "shot_outcome": nested_name(shot.get("outcome")),
    }


def write_csv(path: Path, columns: tuple[str, ...], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def prepare(output_dir: Path) -> dict:
    matches_data, matches_raw = fetch_json(MATCHES_URL)
    if not isinstance(matches_data, list):
        raise ValueError("The match document is not a JSON array")

    matches = sorted(matches_data, key=lambda m: (m["match_date"], m["match_id"]))
    if len(matches) != 35:
        raise ValueError(f"Expected 35 matches at the pinned commit; found {len(matches)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "matches_2020_21.csv", MATCH_COLUMNS, [match_row(m) for m in matches])

    seen_event_ids: set[str] = set()
    manifest: list[dict] = []
    total_events = 0
    total_shots = 0
    missing_shot_xg = 0
    for index, match in enumerate(matches):
        match_id = match["match_id"]
        batch = 1 if index < 17 else 2
        source_url = f"{BASE_URL}/events/{match_id}.json"
        events, raw = fetch_json(source_url)
        if not isinstance(events, list):
            raise ValueError(f"Events for match {match_id} are not a JSON array")

        rows = [event_row(event, match_id) for event in events]
        event_ids = [row["event_id"] for row in rows]
        if any(not event_id for event_id in event_ids):
            raise ValueError(f"Match {match_id} contains an event without an ID")
        if len(event_ids) != len(set(event_ids)) or seen_event_ids.intersection(event_ids):
            raise ValueError(f"Match {match_id} contains duplicate event IDs")
        seen_event_ids.update(event_ids)

        shots = [row for row in rows if row["event_type"] == "Shot"]
        missing_xg = sum(row["shot_xg"] is None for row in shots)
        filename = f"lote_{batch}_{match_id}.csv"
        write_csv(output_dir / "events" / filename, EVENT_COLUMNS, rows)
        manifest.append({
            "batch": batch,
            "match_id": match_id,
            "match_date": match["match_date"],
            "event_file": filename,
            "event_rows": len(rows),
            "shot_rows": len(shots),
            "shots_without_xg": missing_xg,
            "source_url": source_url,
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        })
        total_events += len(rows)
        total_shots += len(shots)
        missing_shot_xg += missing_xg
        print(f"{index + 1:02d}/35  batch {batch}  match {match_id}: {len(rows)} events, {len(shots)} shots")

    write_csv(output_dir / "manifest.csv", MANIFEST_COLUMNS, manifest)
    summary = {
        "source_commit": SOURCE_COMMIT,
        "matches_url": MATCHES_URL,
        "matches_sha256": hashlib.sha256(matches_raw).hexdigest(),
        "matches": len(matches),
        "batch_1_matches": 17,
        "batch_2_matches": 18,
        "events": total_events,
        "unique_event_ids": len(seen_event_ids),
        "shots": total_shots,
        "shots_without_xg": missing_shot_xg,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).parent / "data" / "generated",
        help="Output directory for the CSV files and source manifest",
    )
    args = parser.parse_args()
    print(json.dumps(prepare(args.output), indent=2, ensure_ascii=False))
