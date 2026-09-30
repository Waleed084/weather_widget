"""
Optional live photo backgrounds via the Pexels API (https://pexels.com/api).

Entirely optional: if config.PEXELS_API_KEY is empty, fetch_background_for()
returns None immediately and the card falls back to its built-in procedural
gradient - the widget works with zero setup either way.

Downloaded photos are cached to disk by Pexels photo ID so the same photo
is never re-downloaded twice, and so a transient network failure just keeps
showing whatever was already cached rather than breaking anything.

Per Pexels' API guidelines, every photo we show must be credited to its
photographer - see WeatherCard.set_photo_credit(), which renders the small
clickable credit line on the card itself.
"""
from __future__ import annotations

import random
from pathlib import Path

import requests

import config

CACHE_DIR = Path(__file__).parent / "cache" / "backgrounds"
SEARCH_URL = "https://api.pexels.com/v1/search"


def _cache_path(photo_id: int) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{photo_id}.jpg"


def fetch_background_for(palette_key: str) -> dict | None:
    """Look up a fresh photo matching this condition/time-of-day and cache
    it locally. Returns None (never raises) on any failure - callers should
    just keep showing whatever background they already have."""
    if not config.PEXELS_API_KEY:
        return None

    query = config.PEXELS_SEARCH_TERMS.get(palette_key, "sky weather")
    try:
        resp = requests.get(
            SEARCH_URL,
            headers={"Authorization": config.PEXELS_API_KEY},
            params={
                "query": query,
                "orientation": "landscape",
                "per_page": 15,
                # Random page + random pick within it, so "rotate hourly"
                # actually surfaces different photos over time instead of
                # the same top search result every call.
                "page": random.randint(1, 3),
            },
            timeout=config.REQUEST_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        photos = resp.json().get("photos") or []
        if not photos:
            return None

        photo = random.choice(photos)
        cache_path = _cache_path(photo["id"])
        if not cache_path.exists():
            image_resp = requests.get(photo["src"]["large"], timeout=config.REQUEST_TIMEOUT_SECONDS)
            image_resp.raise_for_status()
            cache_path.write_bytes(image_resp.content)

        return {
            "path": str(cache_path),
            "photographer": photo.get("photographer") or "Unknown",
            "pexels_url": photo.get("url") or "https://www.pexels.com",
        }
    except (requests.RequestException, ValueError, KeyError, OSError):
        return None
