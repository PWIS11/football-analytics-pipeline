"""Load layer: persist the star schema as Parquet and (optionally) DuckDB.

Two output formats, two purposes:

* Parquet  — committed to the repo (small) and read directly by Power BI,
             even from a raw GitHub URL. Fully reproducible, zero hosting cost.
* DuckDB   — a single-file analytical database you can query with SQL, and the
             target dbt will build into in iteration 2.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def write_parquet(tables: dict[str, pd.DataFrame], out_dir: str | Path) -> list[Path]:
    """Write each table to <out_dir>/<table>.parquet."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, df in tables.items():
        path = out_dir / f"{name}.parquet"
        df.to_parquet(path, index=False)
        logger.info("Wrote %s rows -> %s", len(df), path)
        written.append(path)
    return written


def build_duckdb(tables: dict[str, pd.DataFrame], db_path: str | Path) -> Path:
    """Create (or replace) a DuckDB database containing every table."""
    import duckdb

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    try:
        for name, df in tables.items():
            con.register("_staging", df)
            con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM _staging")
            con.unregister("_staging")
            logger.info("Loaded table %s into DuckDB", name)
    finally:
        con.close()
    return db_path
