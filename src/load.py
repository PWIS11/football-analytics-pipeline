"""Load layer: land the flat raw table into DuckDB for dbt to transform.

This is the "L" in ELT. We write a single `raw_matches` table into the DuckDB
file; the dbt project then reads it as a source and builds staging + marts.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def load_raw_matches(df: pd.DataFrame, db_path: str | Path) -> Path:
    """Write the flat match table into DuckDB as `raw_matches` (full refresh)."""
    import duckdb

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    try:
        con.register("_staging", df)
        con.execute("CREATE OR REPLACE TABLE raw_matches AS SELECT * FROM _staging")
        con.unregister("_staging")
        n = con.execute("SELECT count(*) FROM raw_matches").fetchone()[0]
        logger.info("Loaded %s rows into raw_matches", n)
    finally:
        con.close()
    return db_path
