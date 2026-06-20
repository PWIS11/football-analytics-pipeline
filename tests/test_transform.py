"""Tests for the flatten layer.

These run entirely on the committed sample JSON — no API token, no network —
so they are safe to run in CI on every push. Business-logic correctness (star
schema, standings) is tested separately by dbt's own data tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src import transform

SAMPLE = Path(__file__).resolve().parent / "fixtures" / "sample_matches.json"


@pytest.fixture(scope="module")
def raw() -> dict:
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def test_one_row_per_match(raw: dict) -> None:
    df = transform.flatten_matches(raw)
    assert len(df) == len(raw["matches"])
    assert df["match_id"].is_unique


def test_expected_columns_present(raw: dict) -> None:
    df = transform.flatten_matches(raw)
    for col in ("match_id", "competition_code", "season_id",
                "home_team_id", "away_team_id", "home_goals", "winner"):
        assert col in df.columns


def test_finished_match_scores(raw: dict) -> None:
    df = transform.flatten_matches(raw)
    row = df.loc[df["match_id"] == 500001].iloc[0]
    assert row["home_goals"] == 2
    assert row["away_goals"] == 0
    assert row["winner"] == "HOME_TEAM"


def test_scheduled_match_has_null_score(raw: dict) -> None:
    df = transform.flatten_matches(raw)
    row = df.loc[df["match_id"] == 500004].iloc[0]
    assert row["status"] == "SCHEDULED"
    assert pd.isna(row["home_goals"])
