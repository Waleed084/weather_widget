"""
Your own background photos, organized by weather category.

Drop images into backgrounds/<Category>/ - the folder names are in
config.BACKGROUND_FOLDER_NAMES (e.g. "backgrounds/Clear Day/",
"backgrounds/Rainy Night/"). Every folder already exists in the project
with a short note inside explaining what goes there.

You don't have to fill in all twelve. If a specific category's folder is
empty (or missing), FALLBACK_CHAIN below tries progressively more general
categories instead - e.g. an empty "Stormy Night" falls back to whatever
is in "Rainy Night", then "Cloudy Night", then "Clear Night". If nothing
has been supplied anywhere yet, the caller just keeps the gradient.
"""
from __future__ import annotations

import random
from pathlib import Path

import config

BACKGROUNDS_ROOT = Path(__file__).parent / "backgrounds"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

FALLBACK_CHAIN = {
    "storm_day":   ["rain_day", "cloud_day", "clear_day"],
    "storm_night": ["rain_night", "cloud_night", "clear_night"],
    "rain_day":    ["cloud_day", "clear_day"],
    "rain_night":  ["cloud_night", "clear_night"],
    "snow_day":    ["cloud_day", "clear_day"],
    "snow_night":  ["cloud_night", "clear_night"],
    "fog_day":     ["cloud_day", "clear_day"],
    "fog_night":   ["cloud_night", "clear_night"],
    "cloud_day":   ["clear_day"],
    "cloud_night": ["clear_night"],
    "clear_day":   [],
    "clear_night": [],
}


def _folder_for(palette_key: str) -> Path:
    name = config.BACKGROUND_FOLDER_NAMES.get(palette_key, palette_key)
    return BACKGROUNDS_ROOT / name


def _images_in(palette_key: str) -> list[Path]:
    folder = _folder_for(palette_key)
    if not folder.is_dir():
        return []
    return sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )


def pick_local_background(palette_key: str, avoid: Path | None = None) -> Path | None:
    """Return a random photo for this condition, walking the fallback chain
    to a more general category if the specific one is empty. `avoid` (the
    previously-shown path) is skipped when there's another option, so
    hourly rotation doesn't just re-show the same single photo.

    Returns None if nothing has been supplied in this category or any of
    its fallbacks yet - callers should treat that as "keep the gradient",
    not as an error.
    """
    for key in [palette_key, *FALLBACK_CHAIN.get(palette_key, [])]:
        images = _images_in(key)
        if not images:
            continue
        if avoid is not None and len(images) > 1:
            images = [p for p in images if p != avoid] or images
        return random.choice(images)
    return None
