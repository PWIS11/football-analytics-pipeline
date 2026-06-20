"""Extract + Load pipeline (the "EL" of ELT).

Run from the project root:

    python pipeline.py                 # pull live data, land raw_matches in DuckDB
    python pipeline.py --offline       # rebuild raw_matches from saved raw JSON

After this runs, transform the data with dbt:

    cd football_dbt
    dbt build --profiles-dir .         # staging -> marts + run all tests
    dbt docs generate --profiles-dir . # build the documentation site

The --offline flag rebuilds raw_matches from saved JSON without an API token or
network access, which is what the test suite and CI rely on.
"""

from __future__ import annotations

import argparse
import json
import logging

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
            except Exception as exc:  # noqa: BLE001 - log and continue, don't abort
                logger.warning("Skipping %s season %s: %s", competition, season, exc)
                continue
            raw_path = config.RAW_DIR / f"matches_{competition}_{season}.json"
            extract.save_raw(payload, raw_path)
            matches.extend(payload.get("matches", []))
    return matches


def main(offline: bool = False) -> None:
    load_dotenv()

    logger.info("Extracting matches (offline=%s)...", offline)
    matches = collect_raw_matches(offline)
    logger.info("Collected %s matches.", len(matches))

    logger.info("Flattening to raw table...")
    df = transform.flatten_matches(matches)

    logger.info("Loading raw_matches into DuckDB...")
    load.load_raw_matches(df, config.DUCKDB_PATH)

    logger.info("Done. Now run dbt to build the models:")
    logger.info("    cd football_dbt && dbt build --profiles-dir .")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Football EL pipeline")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Rebuild raw_matches from saved raw JSON instead of calling the API.",
    )
    args = parser.parse_args()
    main(offline=args.offline)