"""End-to-end pipeline: extract -> transform -> load.

Run from the project root:

    python pipeline.py                 # uses config.py defaults
    python pipeline.py --offline       # rebuild outputs from saved raw JSON

The --offline flag lets you (and CI) rebuild the whole star schema without an
API token or network access, which is what the test suite relies on.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from dotenv import load_dotenv

import config
from src import extract, load, transform

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pipeline")


def collect_raw_matches(offline: bool) -> list[dict]:
    """Return a flat list of match objects from the API or from saved JSON."""
    matches: list[dict] = []

    if offline:
        for raw_file in sorted(config.RAW_DIR.glob("matches_*.json")):
            payload = json.loads(raw_file.read_text(encoding="utf-8"))
            matches.extend(payload.get("matches", []))
            logger.info("Loaded %s (offline)", raw_file.name)
        return matches

    client = extract.FootballDataClient(min_interval=config.API_MIN_INTERVAL_SECONDS)
    for competition in config.COMPETITIONS:
        for season in config.SEASONS:
            try:
                payload = client.get_matches(competition, season=season)
            except Exception as exc:  # noqa: BLE001 - log and continue, don't abort the run
                logger.warning(
                    "Skipping %s season %s: %s", competition, season, exc
                )
                continue
            raw_path = config.RAW_DIR / f"matches_{competition}_{season}.json"
            extract.save_raw(payload, raw_path)
            matches.extend(payload.get("matches", []))
    return matches


def main(offline: bool = False, with_duckdb: bool = True) -> None:
    load_dotenv()

    logger.info("Extracting matches (offline=%s)...", offline)
    matches = collect_raw_matches(offline)
    logger.info("Collected %s matches.", len(matches))

    logger.info("Building star schema...")
    tables = transform.build_star_schema(matches)

    problems = transform.validate(tables)
    if problems:
        for problem in problems:
            logger.warning("DATA QUALITY: %s", problem)
    else:
        logger.info("Data quality checks passed.")

    logger.info("Writing Parquet outputs...")
    load.write_parquet(tables, config.PROCESSED_DIR)

    if with_duckdb:
        logger.info("Building DuckDB database...")
        load.build_duckdb(tables, config.DUCKDB_PATH)

    logger.info("Done. Outputs in %s", config.PROCESSED_DIR)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Football analytics pipeline")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Rebuild from saved raw JSON instead of calling the API.",
    )
    parser.add_argument(
        "--no-duckdb",
        action="store_true",
        help="Skip building the DuckDB database (Parquet only).",
    )
    args = parser.parse_args()
    main(offline=args.offline, with_duckdb=not args.no_duckdb)
