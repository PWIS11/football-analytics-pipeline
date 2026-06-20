"""Transform layer: turn raw match JSON into a clean star schema.

The output is a small dimensional model that Power BI consumes directly:

    fact_matches  (one row per match)
        |
        +-- dim_teams        (home_team_id / away_team_id)
        +-- dim_competitions (competition_code)
        +-- dim_seasons      (season_id)

This separation of a fact table from its dimensions is the core idea an
analytics engineer is expected to demonstrate, so it is kept deliberately
explicit rather than collapsed into one wide table.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


def _matches(raw: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Accept either a full API payload or an already-unwrapped list of matches."""
    if isinstance(raw, dict):
        return raw.get("matches", [])
    return raw


def build_fact_matches(raw: dict[str, Any] | list[dict[str, Any]]) -> pd.DataFrame:
    """One row per match, with foreign keys to the dimension tables."""
    rows: list[dict[str, Any]] = []
    for match in _matches(raw):
        score = match.get("score", {}) or {}
        full_time = score.get("fullTime", {}) or {}
        half_time = score.get("halfTime", {}) or {}
        rows.append(
            {
                "match_id": match.get("id"),
                "utc_date": match.get("utcDate"),
                "matchday": match.get("matchday"),
                "status": match.get("status"),
                "stage": match.get("stage"),
                "competition_code": (match.get("competition") or {}).get("code"),
                "season_id": (match.get("season") or {}).get("id"),
                "home_team_id": (match.get("homeTeam") or {}).get("id"),
                "away_team_id": (match.get("awayTeam") or {}).get("id"),
                "home_goals": full_time.get("home"),
                "away_goals": full_time.get("away"),
                "ht_home_goals": half_time.get("home"),
                "ht_away_goals": half_time.get("away"),
                "winner": score.get("winner"),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["utc_date"] = pd.to_datetime(df["utc_date"], utc=True, errors="coerce")
    df["match_date"] = df["utc_date"].dt.date
    # Derived measures (meaningful only for finished matches).
    df["total_goals"] = df["home_goals"] + df["away_goals"]
    df["goal_difference"] = df["home_goals"] - df["away_goals"]
    return df


def build_dim_teams(raw: dict[str, Any] | list[dict[str, Any]]) -> pd.DataFrame:
    """Distinct teams appearing as either home or away side."""
    teams: dict[int, dict[str, Any]] = {}
    for match in _matches(raw):
        for side in ("homeTeam", "awayTeam"):
            team = match.get(side) or {}
            team_id = team.get("id")
            if team_id is not None and team_id not in teams:
                teams[team_id] = {
                    "team_id": team_id,
                    "name": team.get("name"),
                    "short_name": team.get("shortName"),
                    "tla": team.get("tla"),
                    "crest": team.get("crest"),
                }
    return pd.DataFrame(teams.values()).sort_values("team_id").reset_index(drop=True)


def build_dim_competitions(
    raw: dict[str, Any] | list[dict[str, Any]]
) -> pd.DataFrame:
    """Distinct competitions present in the payload."""
    comps: dict[str, dict[str, Any]] = {}
    for match in _matches(raw):
        comp = match.get("competition") or {}
        code = comp.get("code")
        if code and code not in comps:
            comps[code] = {
                "competition_code": code,
                "competition_id": comp.get("id"),
                "name": comp.get("name"),
                "type": comp.get("type"),
            }
    return pd.DataFrame(comps.values()).reset_index(drop=True)


def build_dim_seasons(raw: dict[str, Any] | list[dict[str, Any]]) -> pd.DataFrame:
    """Distinct seasons present in the payload."""
    seasons: dict[int, dict[str, Any]] = {}
    for match in _matches(raw):
        season = match.get("season") or {}
        season_id = season.get("id")
        if season_id is not None and season_id not in seasons:
            seasons[season_id] = {
                "season_id": season_id,
                "start_date": season.get("startDate"),
                "end_date": season.get("endDate"),
                "current_matchday": season.get("currentMatchday"),
            }
    return pd.DataFrame(seasons.values()).reset_index(drop=True)


def build_star_schema(
    raw: dict[str, Any] | list[dict[str, Any]]
) -> dict[str, pd.DataFrame]:
    """Build the full set of tables in one call."""
    return {
        "fact_matches": build_fact_matches(raw),
        "dim_teams": build_dim_teams(raw),
        "dim_competitions": build_dim_competitions(raw),
        "dim_seasons": build_dim_seasons(raw),
    }


def validate(tables: dict[str, pd.DataFrame]) -> list[str]:
    """Lightweight data-quality checks. Returns a list of problems (empty = OK).

    This is intentionally small for the MVP. In iteration 2 these checks move
    into dbt tests (unique, not_null, relationships).
    """
    problems: list[str] = []
    fact = tables["fact_matches"]

    if fact["match_id"].duplicated().any():
        problems.append("Duplicate match_id values in fact_matches.")

    finished = fact[fact["status"] == "FINISHED"]
    if (finished[["home_goals", "away_goals"]] < 0).any().any():
        problems.append("Negative goal counts found in finished matches.")
    if finished["home_goals"].isna().any() or finished["away_goals"].isna().any():
        problems.append("Missing scores in matches marked FINISHED.")

    team_ids = set(tables["dim_teams"]["team_id"])
    referenced = set(fact["home_team_id"]).union(fact["away_team_id"])
    missing = referenced - team_ids - {None}
    if missing:
        problems.append(f"Team ids referenced by matches but absent from dim_teams: {missing}")

    return problems
