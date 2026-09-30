"""
Central configuration for the desktop weather widget.

Everything a user is likely to want to tweak lives here, so the rest of
the codebase never hard-codes a "magic" value.
"""

# ---------------------------------------------------------------------------
# Card geometry
# ---------------------------------------------------------------------------
CARD_WIDTH = 340
CARD_HEIGHT = 210
CORNER_RADIUS = 28
SHADOW_MARGIN = 36          # transparent margin around the card the drop shadow renders into

# ---------------------------------------------------------------------------
# Behaviour
# ---------------------------------------------------------------------------
UNITS = "celsius"                 # "celsius" or "fahrenheit"
REFRESH_INTERVAL_MS = 10 * 60_000  # 10 minutes
ALWAYS_ON_TOP = False              # True pins the widget above other windows
START_POSITION_MARGIN = 24         # px from the screen edge on first launch

# Where the widget remembers its screen position / cached data between runs.
ORG_NAME = "LocalWidgets"
APP_NAME = "DesktopWeatherWidget"

# ---------------------------------------------------------------------------
# Data sources (both free, no API key required)
# ---------------------------------------------------------------------------
IP_GEOLOCATION_URL = "https://ipwho.is/"
IP_GEOLOCATION_FALLBACK_URL = "http://ip-api.com/json/"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SECONDS = 8

# Fallback coordinates used only if IP geolocation fails outright and no
# cached location is available yet. (London — arbitrary, just needs to be
# somewhere valid so the widget never shows a hard crash on first run.)
FALLBACK_LATITUDE = 51.5074
FALLBACK_LONGITUDE = -0.1278
FALLBACK_CITY_NAME = "London"

# ---------------------------------------------------------------------------
# Manual location override
# ---------------------------------------------------------------------------
# IP geolocation is frequently wrong outside major cities - an ISP's IP
# block is often just registered to their regional hub city rather than
# your actual town, and no amount of retrying fixes that; it needs an
# explicit override.
#
# Priority: MANUAL_LATITUDE/LONGITUDE (if both set) > geocoding
# MANUAL_CITY_NAME (if set) > automatic IP-based detection.
#
# Set exact coordinates for the most reliable fix. To move somewhere new
# later, either update these two numbers, or clear them to None and just
# change MANUAL_CITY_NAME - it will be geocoded automatically on launch.
MANUAL_LATITUDE = 32.18833
MANUAL_LONGITUDE = 73.02861
MANUAL_CITY_NAME = "Phularwan, Pakistan"

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

# ---------------------------------------------------------------------------
# Background photos
# ---------------------------------------------------------------------------
# "local"  - use your own photos from backgrounds/<Category>/ (see README)
# "pexels" - fetch from the Pexels API (needs PEXELS_API_KEY below)
# "off"    - always use the built-in gradient, never a photo
BACKGROUND_SOURCE = "local"

BACKGROUND_ROTATE_INTERVAL_MS = 60 * 60_000  # rotate to a fresh photo hourly

# Folder names under backgrounds/ for each condition/time-of-day (used by
# BACKGROUND_SOURCE = "local"). You don't need to fill in every one - an
# empty or missing folder falls back to a related, more general category
# (see local_backgrounds.FALLBACK_CHAIN), and if nothing at all has been
# supplied yet the card just uses its gradient.
BACKGROUND_FOLDER_NAMES = {
    "clear_day":   "Clear Day",
    "clear_night": "Clear Night",
    "cloud_day":   "Cloudy Day",
    "cloud_night": "Cloudy Night",
    "rain_day":    "Rainy Day",
    "rain_night":  "Rainy Night",
    "snow_day":    "Snowy Day",
    "snow_night":  "Snowy Night",
    "storm_day":   "Stormy Day",
    "storm_night": "Stormy Night",
    "fog_day":     "Foggy Day",
    "fog_night":   "Foggy Night",
}

# ---------------------------------------------------------------------------
# Optional live photo backgrounds (Pexels API - https://pexels.com/api)
# Currently paused: set BACKGROUND_SOURCE = "pexels" above to use this
# instead of your own local photos.
# ---------------------------------------------------------------------------
PEXELS_API_KEY = ""

# One search query per palette key (see weather_codes.py) - tuned to pull
# back thematically-appropriate, landscape-oriented photography.
PEXELS_SEARCH_TERMS = {
    "clear_day":   "clear blue sky sunny",
    "clear_night": "clear starry night sky",
    "cloud_day":   "cloudy sky daytime",
    "cloud_night": "cloudy night sky moon",
    "rain_day":    "rain window daytime",
    "rain_night":  "rain city night lights",
    "snow_day":    "snow landscape daylight",
    "snow_night":  "snowy night winter",
    "storm_day":   "thunderstorm dark clouds",
    "storm_night": "lightning storm night sky",
    "fog_day":     "foggy morning landscape",
    "fog_night":   "fog night street lights",
}

# Open-Meteo's free tier is CC BY 4.0 - attribution is required, hence the
# small credit line drawn on the card itself. Do not remove it if you
# redistribute this widget.
ATTRIBUTION_TEXT = "Weather data by Open-Meteo.com"
