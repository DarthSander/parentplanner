"""
Weather forecast service using Open-Meteo API.

Free, no API key required, GDPR-compliant (EU servers).
Docs: https://open-meteo.com/en/docs
"""
import logging
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

GEOCODING_API = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_API = "https://api.open-meteo.com/v1/forecast"

# WMO Weather interpretation codes → Dutch description
WMO_CODES = {
    0: "Heldere lucht",
    1: "Overwegend helder",
    2: "Gedeeltelijk bewolkt",
    3: "Bewolkt",
    45: "Mist",
    48: "IJsmist",
    51: "Lichte motregen",
    53: "Motregen",
    55: "Zware motregen",
    61: "Lichte regen",
    63: "Regen",
    65: "Zware regen",
    71: "Lichte sneeuw",
    73: "Sneeuw",
    75: "Zware sneeuw",
    77: "Sneeuwkorrels",
    80: "Lichte regenbuien",
    81: "Regenbuien",
    82: "Zware regenbuien",
    85: "Lichte sneeuwbuien",
    86: "Zware sneeuwbuien",
    95: "Onweer",
    96: "Onweer met hagel",
    99: "Zwaar onweer met hagel",
}


async def geocode_location(location: str) -> tuple[float, float] | None:
    """Convert location name to (latitude, longitude). Returns None if not found."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                GEOCODING_API,
                params={"name": location, "count": 1, "language": "nl", "format": "json"},
            )
            data = response.json()
            results = data.get("results", [])
            if results:
                return results[0]["latitude"], results[0]["longitude"]
    except Exception as e:
        logger.warning(f"Geocoding failed for '{location}': {e}")
    return None


def _clothing_advice(temp_min: float, temp_max: float, precip_prob: int, description: str) -> str:
    """Generate clothing advice in Dutch based on forecast."""
    advice = []

    if temp_max < 5:
        advice.append("dikke winterjas, handschoenen en muts")
    elif temp_max < 12:
        advice.append("warme jas en laagjes")
    elif temp_max < 18:
        advice.append("lichte jas of vest")
    else:
        advice.append("t-shirt, eventueel lichte jas voor de avond")

    if precip_prob >= 50:
        advice.append("regenjas en waterdicht schoeisel")
    elif precip_prob >= 25:
        advice.append("neem een regenjas mee voor de zekerheid")

    if "sneeuw" in description.lower():
        advice.append("laarzen")

    return ", ".join(advice) if advice else "normale kleding"


async def get_weather_forecast(location: str, date: datetime) -> dict | None:
    """
    Fetch a daily weather forecast for a location and date.

    Returns a dict with:
      - temp_min, temp_max (°C)
      - precipitation_prob (%)
      - description (Dutch text, e.g. "Regenbuien")
      - clothing_advice (Dutch, e.g. "warme jas, regenjas")
      - summary (one-line Dutch summary for AI prompt injection)

    Returns None if the location cannot be geocoded or the date is too far ahead (>16 days).
    """
    coords = await geocode_location(location)
    if not coords:
        return None

    lat, lon = coords
    date_str = date.strftime("%Y-%m-%d")

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(
                FORECAST_API,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode",
                    "timezone": "Europe/Amsterdam",
                    "start_date": date_str,
                    "end_date": date_str,
                    "forecast_days": 16,
                },
            )
            data = response.json()

        daily = data.get("daily", {})
        dates = daily.get("time", [])
        if not dates or dates[0] != date_str:
            return None

        temp_max = daily["temperature_2m_max"][0]
        temp_min = daily["temperature_2m_min"][0]
        precip_prob = daily["precipitation_probability_max"][0] or 0
        wmo_code = daily["weathercode"][0]
        description = WMO_CODES.get(wmo_code, "Wisselvallig")
        clothing = _clothing_advice(temp_min, temp_max, precip_prob, description)

        summary = (
            f"Weer op {date.strftime('%d %B')}: {description}, "
            f"{temp_min:.0f}–{temp_max:.0f}°C, "
            f"{precip_prob}% kans op neerslag. "
            f"Kleding: {clothing}."
        )

        return {
            "temp_min": temp_min,
            "temp_max": temp_max,
            "precipitation_prob": precip_prob,
            "description": description,
            "clothing_advice": clothing,
            "summary": summary,
        }
    except Exception as e:
        logger.warning(f"Weather fetch failed for {location} on {date_str}: {e}")
        return None
