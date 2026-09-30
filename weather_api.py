"""
Thin wrappers around two free, keyless HTTP APIs:

  * ipwho.is / ip-api.com  -> approximate location from the caller's IP
  * api.open-meteo.com     -> current + today's weather for a lat/lon

Both functions are synchronous (blocking) on purpose - they are always
called from a background QThread (see workers.py), never from the UI
thread.
"""
from __future__ import annotations

import requests

import config
import weather_codes


class WeatherApiError(Exception):
    """Raised when neither the primary nor fallback source could be reached."""


def geolocate_by_ip() -> dict:
    """Best-effort IP geolocation. Returns {'latitude', 'longitude', 'city'}.

    Falls back through two providers and finally to a static default so the
    widget always has *something* to show rather than failing outright.
    """
    try:
        resp = requests.get(config.IP_GEOLOCATION_URL, timeout=config.REQUEST_TIMEOUT_SECONDS)
        data = resp.json()
        if data.get("success", True) and data.get("latitude") is not None:
            return {
                "latitude": float(data["latitude"]),
                "longitude": float(data["longitude"]),
                "city": data.get("city") or config.FALLBACK_CITY_NAME,
            }
    except (requests.RequestException, ValueError, KeyError):
        pass

    try:
        resp = requests.get(config.IP_GEOLOCATION_FALLBACK_URL, timeout=config.REQUEST_TIMEOUT_SECONDS)
        data = resp.json()
        if data.get("status") == "success":
            return {
                "latitude": float(data["lat"]),
                "longitude": float(data["lon"]),
                "city": data.get("city") or config.FALLBACK_CITY_NAME,
            }
    except (requests.RequestException, ValueError, KeyError):
        pass

    return {
        "latitude": config.FALLBACK_LATITUDE,
        "longitude": config.FALLBACK_LONGITUDE,
        "city": config.FALLBACK_CITY_NAME,
    }


def geocode_city(name: str) -> dict | None:
    """Resolve a place name to coordinates via Open-Meteo's geocoding API.
    Returns None (never raises) if the name can't be resolved."""
    try:
        resp = requests.get(
            config.GEOCODING_URL,
            params={"name": name, "count": 1, "language": "en", "format": "json"},
            timeout=config.REQUEST_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        results = resp.json().get("results") or []
        if not results:
            return None
        top = results[0]
        return {
            "latitude": float(top["latitude"]),
            "longitude": float(top["longitude"]),
            "city": top.get("name") or name,
        }
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return None


def resolve_location() -> dict:
    """Location priority: explicit manual coordinates > geocoded manual city
    name > automatic IP-based detection. See config.py for the override
    fields - this exists because IP geolocation cannot be relied on outside
    major cities."""
    if config.MANUAL_LATITUDE is not None and config.MANUAL_LONGITUDE is not None:
        return {
            "latitude": config.MANUAL_LATITUDE,
            "longitude": config.MANUAL_LONGITUDE,
            "city": config.MANUAL_CITY_NAME or "Custom location",
        }
    if config.MANUAL_CITY_NAME:
        geocoded = geocode_city(config.MANUAL_CITY_NAME)
        if geocoded:
            return geocoded
    return geolocate_by_ip()


def fetch_weather(latitude: float, longitude: float, city: str) -> dict:
    """Fetch current conditions + today's high/low from Open-Meteo.

    Returns a flat dict the UI layer can consume directly. Raises
    WeatherApiError on total failure (caller decides how to degrade).
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join([
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "weather_code",
            "wind_speed_10m",
            "is_day",
        ]),
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
        ]),
        "temperature_unit": "fahrenheit" if config.UNITS == "fahrenheit" else "celsius",
        "wind_speed_unit": "kmh",
        "timezone": "auto",
        "forecast_days": 1,
    }

    try:
        resp = requests.get(config.FORECAST_URL, params=params, timeout=config.REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, ValueError) as exc:
        raise WeatherApiError(str(exc)) from exc

    try:
        current = payload["current"]
        daily = payload["daily"]
        is_day = bool(current.get("is_day", 1))
        look = weather_codes.describe(current["weather_code"], is_day)

        return {
            "city": city,
            "temperature": round(current["temperature_2m"]),
            "feels_like": round(current["apparent_temperature"]),
            "humidity": round(current["relative_humidity_2m"]),
            "wind_speed": round(current["wind_speed_10m"]),
            "high": round(daily["temperature_2m_max"][0]),
            "low": round(daily["temperature_2m_min"][0]),
            "is_day": is_day,
            "condition_label": look.label,
            "icon": look.icon,
            "palette_key": look.palette_key,
            "icon_color_key": look.icon_color_key,
            "units": "°F" if config.UNITS == "fahrenheit" else "°C",
        }
    except (KeyError, IndexError, TypeError) as exc:
        raise WeatherApiError(f"Unexpected response shape: {exc}") from exc
