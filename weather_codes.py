"""
Maps Open-Meteo's WMO weather codes to a human label, a qtawesome icon
glyph, and a palette key (see styles.py) used to pick the card's gradient
and icon tint.

Reference: https://open-meteo.com/en/docs (WMO Weather interpretation codes)
"""
from collections import namedtuple

WeatherLook = namedtuple("WeatherLook", "label icon palette_key icon_color_key")

# code -> (label, icon-when-day, icon-when-night, palette family)
_TABLE = {
    0:  ("Clear sky",            "fa5s.sun",                 "fa5s.moon",              "clear"),
    1:  ("Mostly clear",         "fa5s.cloud-sun",           "fa5s.cloud-moon",        "clear"),
    2:  ("Partly cloudy",        "fa5s.cloud-sun",           "fa5s.cloud-moon",        "cloud"),
    3:  ("Overcast",             "fa5s.cloud",               "fa5s.cloud",             "cloud"),
    45: ("Fog",                  "fa5s.smog",                "fa5s.smog",              "fog"),
    48: ("Rime fog",             "fa5s.smog",                "fa5s.smog",              "fog"),
    51: ("Light drizzle",        "fa5s.cloud-rain",          "fa5s.cloud-rain",        "rain"),
    53: ("Drizzle",              "fa5s.cloud-rain",          "fa5s.cloud-rain",        "rain"),
    55: ("Dense drizzle",        "fa5s.cloud-rain",          "fa5s.cloud-rain",        "rain"),
    56: ("Freezing drizzle",     "fa5s.cloud-rain",          "fa5s.cloud-rain",        "rain"),
    57: ("Freezing drizzle",     "fa5s.cloud-rain",          "fa5s.cloud-rain",        "rain"),
    61: ("Light rain",           "fa5s.cloud-rain",          "fa5s.cloud-rain",        "rain"),
    63: ("Rain",                 "fa5s.cloud-showers-heavy", "fa5s.cloud-showers-heavy", "rain"),
    65: ("Heavy rain",           "fa5s.cloud-showers-heavy", "fa5s.cloud-showers-heavy", "rain"),
    66: ("Freezing rain",        "fa5s.cloud-showers-heavy", "fa5s.cloud-showers-heavy", "rain"),
    67: ("Heavy freezing rain",  "fa5s.cloud-showers-heavy", "fa5s.cloud-showers-heavy", "rain"),
    71: ("Light snow",           "fa5s.snowflake",           "fa5s.snowflake",         "snow"),
    73: ("Snow",                 "fa5s.snowflake",           "fa5s.snowflake",         "snow"),
    75: ("Heavy snow",           "fa5s.snowflake",           "fa5s.snowflake",         "snow"),
    77: ("Snow grains",          "fa5s.snowflake",           "fa5s.snowflake",         "snow"),
    80: ("Light showers",        "fa5s.cloud-rain",          "fa5s.cloud-rain",        "rain"),
    81: ("Showers",              "fa5s.cloud-showers-heavy", "fa5s.cloud-showers-heavy", "rain"),
    82: ("Violent showers",      "fa5s.cloud-showers-heavy", "fa5s.cloud-showers-heavy", "rain"),
    85: ("Snow showers",         "fa5s.snowflake",           "fa5s.snowflake",         "snow"),
    86: ("Heavy snow showers",   "fa5s.snowflake",           "fa5s.snowflake",         "snow"),
    95: ("Thunderstorm",         "fa5s.bolt",                "fa5s.bolt",              "storm"),
    96: ("Thunderstorm, hail",   "fa5s.bolt",                "fa5s.bolt",              "storm"),
    99: ("Severe thunderstorm",  "fa5s.bolt",                "fa5s.bolt",              "storm"),
}

_DEFAULT = ("Unknown", "fa5s.question", "fa5s.question", "cloud")


def describe(code: int, is_day: bool) -> WeatherLook:
    """Return the label/icon/palette for a WMO weathercode."""
    label, icon_day, icon_night, family = _TABLE.get(int(code), _DEFAULT)
    icon = icon_day if is_day else icon_night
    palette_key = f"{family}_{'day' if is_day else 'night'}"
    return WeatherLook(label=label, icon=icon, palette_key=palette_key, icon_color_key=family)
