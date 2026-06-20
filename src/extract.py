"""Extraction layer: a thin, rate-limited client for the football-data.org API.

This module is responsible for *getting raw data out of the source* and nothing
else. It does not clean, reshape, or model the data — that is the job of the
transform layer. Keeping extraction isolated means the rest of the pipeline can
be tested against saved JSON without ever touching the network.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.football-data.org/v4"


class FootballDataClient:
    """Minimal client for the football-data.org v4 API.

    Handles authentication and free-tier rate limiting (~10 requests/minute).
    """

    def __init__(
        self,
        api_token: str | None = None,
        min_interval: float = 6.5,
    ) -> None:
        self.api_token = api_token or os.environ.get("FOOTBALL_DATA_TOKEN")
        if not self.api_token:
            raise ValueError(
                "Missing API token. Set FOOTBALL_DATA_TOKEN (see .env.example)."
            )
        self.session = requests.Session()
        self.session.headers.update({"X-Auth-Token": self.api_token})
        self.min_interval = min_interval
        self._last_call = 0.0

    def _throttle(self) -> None:
        """Sleep just enough to respect the free-tier rate limit."""
        elapsed = time.monotonic() - self._last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_call = time.monotonic()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._throttle()
        url = f"{BASE_URL}/{path.lstrip('/')}"
        logger.info("GET %s params=%s", url, params)
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_matches(
        self, competition_code: str, season: int | None = None
    ) -> dict[str, Any]:
        """Fetch all matches for a competition (optionally for one season)."""
        params = {"season": season} if season is not None else None
        return self._get(f"competitions/{competition_code}/matches", params=params)


def save_raw(payload: dict[str, Any], path: str | Path) -> Path:
    """Persist a raw API response to disk for reproducibility and testing."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Saved raw payload -> %s", path)
    return path
