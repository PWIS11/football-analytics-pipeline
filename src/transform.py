"""Light flattening layer (EL, not ELT).

In iteration 1 this module built the full star schema in pandas. In iteration 2
that responsibility moves to dbt: Python now only flattens the nested API JSON
into a single, lightly-typed `raw_matches` table. All modelling, cleaning, and
business logic lives in the dbt project under ``football_dbt/``.

Keeping Python's job to "extract + load raw" and pushing transformation into
SQL is the ELT pattern that modern analytics-engineering stacks are built on.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


def _matches(raw: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Accept either a full API payload or an already-unwrapped list of matches."""
    if isinstance(raw, dict):
        return raw.get("matches", [])
    return raw


def flatten_matches(raw: dict[str, Any] | list[dict[str, Any]]) -> pd.DataFrame:
    """Flatten nested match JSON into one flat row per match.

    No derived measures, no dimension splitting — that is dbt's job. This stays
    deliberately close to the source so the warehouse holds an honest copy of
    what the API returned.
    """
    rows: list[dict[str, Any]] = []
    for match in _matches(raw):
        score = match.get("score", {}) or {}
        full_time = score.get("fullTime", {}) or {}
        half_time = score.get("halfTime", {}) or {}
        competition = match.get("competition") or {}
        season = match.get("season") or {}
        home = match.get("homeTeam") or {}
        away = match.get("awayTeam") or {}
        rows.append(
            {
                "match_id": match.get("id"),
                "utc_date": match.get("utcDate"),
                "matchday": match.get("matchday"),
                "status": match.get("status"),
                "stage": match.get("stage"),
                "competition_id": competition.get("id"),
                "competition_code": competition.get("code"),
                "competition_name": competition.get("name"),
                "season_id": season.get("id"),
                "season_start_date": season.get("startDate"),
                "season_end_date": season.get("endDate"),
                "home_team_id": home.get("id"),
                "home_team_name": home.get("name"),
                "home_team_short_name": home.get("shortName"),
                "home_team_tla": home.get("tla"),
                "home_team_crest": home.get("crest"),
                "away_team_id": away.get("id"),
                "away_team_name": away.get("name"),
                "away_team_short_name": away.get("shortName"),
                "away_team_tla": away.get("tla"),
                "away_team_crest": away.get("crest"),
                "home_goals": full_time.get("home"),
                "away_goals": full_time.get("away"),
                "ht_home_goals": half_time.get("home"),
                "ht_away_goals": half_time.get("away"),
                "winner": score.get("winner"),
            }
        )
    return pd.DataFrame(rows)
