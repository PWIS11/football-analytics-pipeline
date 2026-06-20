"""Central configuration for the football analytics pipeline.

Keeping configuration in one place makes the pipeline reproducible: anyone
cloning the repo can see exactly which competitions and seasons are pulled
and where the outputs land, without reading the pipeline code.
"""

from __future__ import annotations

from pathlib import Path

# --- Paths -------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DUCKDB_PATH = PROCESSED_DIR / "football.duckdb"

# --- API ---------------------------------------------------------------------
# Free tier of football-data.org allows ~10 requests/minute.
# 6.5s between calls keeps us comfortably under that ceiling.
API_MIN_INTERVAL_SECONDS = 6.5

# Competitions to ingest. Codes come from football-data.org (free tier covers
# the 12 listed below). Start with one league for a fast MVP, then add more.
#   PL  = Premier League        PD  = La Liga
#   BL1 = Bundesliga            SA  = Serie A
#   FL1 = Ligue 1               DED = Eredivisie
#   PPL = Primeira Liga         ELC = Championship
#   CL  = UEFA Champions League BSA = Brazil Serie A
COMPETITIONS: list[str] = ["PL", "PD", "BL1", "SA", "FL1"]

# Seasons to pull, given as the starting year (e.g. 2024 = 2024/25 season).
# Historical depth available depends on your football-data.org plan. On the
# free tier, older seasons typically return 403 (history requires a paid add-
# on) — the pipeline skips and logs any season/competition combo that fails
# rather than aborting the whole run, so partial data is still usable.
SEASONS: list[int] = [2023, 2024]
