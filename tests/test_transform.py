"""Tests for the transform layer.

These run entirely on the committed sample JSON — no API token, no network —
so they are safe to run in CI on every push.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src import transform

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "raw" / "matches_PL_2024.json"


@pytest.fixture(scope="module")
def raw() -> dict:
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def test_fact_has_one_row_per_match(raw: dict) -> None:
    fact = transform.build_fact_matches(raw)
    assert len(fact) == len(raw["matches"])
    assert fact["match_id"].is_unique


def test_derived_measures_for_finished_match(raw: dict) -> None:
    fact = transform.build_fact_matches(raw)
    row = fact.loc[fact["match_id"] == 500001].iloc[0]
    assert row["total_goals"] == 2
    assert row["goal_difference"] == 2
    assert row["winner"] == "HOME_TEAM"


def test_scheduled_match_has_null_score(raw: dict) -> None:
    fact = transform.build_fact_matches(raw)
    row = fact.loc[fact["match_id"] == 500004].iloc[0]
    assert row["status"] == "SCHEDULED"
    assert row["home_goals"] != row["home_goals"]  # NaN check


def test_dim_teams_are_unique(raw: dict) -> None:
    teams = transform.build_dim_teams(raw)
    # 4 distinct teams appear across the sample fixtures.
    assert len(teams) == 4
    assert teams["team_id"].is_unique


def test_star_schema_passes_validation(raw: dict) -> None:
    tables = transform.build_star_schema(raw)
    assert transform.validate(tables) == []
