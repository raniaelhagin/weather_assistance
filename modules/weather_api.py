# modules/weather_api.py
"""
Fetches current weather from OpenWeatherMap and returns a clean,
flat dictionary. Also provides a formatted summary string for LLM prompts.
"""

import os
from typing import Optional

from config      import OWM_BASE_URL, REQUEST_TIMEOUT, MAX_RETRIES
from utils.http_utils import get_with_retry
from utils.logger     import get_logger
from utils.text_utils import map_country_code

import requests

logger = get_logger(__name__)

# Maps units param to readable label
UNIT_LABELS = {
    "metric":   ("Celsius",    "°C", "m/s"),
    "imperial": ("Fahrenheit", "°F", "mph"),
    "standard": ("Kelvin",     "K",  "m/s"),
}


# Public API 
def get_weather(
    location:  str,
    units:     str = "metric",
    api_key:   Optional[str] = None,
) -> dict:
    """
    Fetch current weather for a location from OpenWeatherMap.

    Args:
        location (str): city name e.g. "Cairo", "London, GB", "Tokyo, JP"
        units (str): "metric" (°C), "imperial" (°F), or "standard" (K)
        api_key (str | None): OWM key — falls back to OPENWEATHER_API_KEY env variable

    Returns:
        dict with "success": True and weather fields,
        or "success": False and "error" message
    """
    key = api_key or os.getenv("OPENWEATHER_API_KEY", "")
    if not key:
        return _error("OpenWeatherMap API key not configured. "
                      "Set the OPENWEATHER_API_KEY environment variable.")

    params = {
        "q":     location,
        "appid": key,
        "units": units,
    }

    try:
        response = get_with_retry(
            url=OWM_BASE_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
            max_retries=MAX_RETRIES,
        )
        return _parse(response.json(), units)

    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            if e.response.status_code == 401:
                return _error("Invalid OpenWeatherMap API key.")
            if e.response.status_code == 404:
                return _error(f"Location '{location}' not found. "
                              "Try adding a country code e.g. 'Cairo, EG'.")
        return _error(f"HTTP error: {e}")

    except requests.exceptions.ConnectionError:
        return _error("Network error: could not reach OpenWeatherMap. "
                      "Check your internet connection.")

    except requests.exceptions.Timeout:
        return _error("Request timed out. OpenWeatherMap did not respond.")

    except requests.exceptions.RequestException as e:
        return _error(f"Unexpected error: {e}")


def format_weather_summary(weather: dict) -> str:
    """
    Converts a weather dict into a readable paragraph for LLM prompts.

    Args:
        weather (dict): dict returned by get_weather()

    Returns:
        str — single paragraph summary, or error message if call failed
    """
    if not weather.get("success"):
        return f"Weather data unavailable: {weather.get('error', 'unknown error')}"

    _, unit_sym, speed_unit = UNIT_LABELS.get(
        weather.get("units_param", "metric"), UNIT_LABELS["metric"]
    )

    location = weather["location"]
    if weather.get("country"):
        location += f", {weather['country']}"

    parts = [
        f"Current weather in {location}:",
        f"Temperature {weather['temperature']}{unit_sym}"
        f" (feels like {weather['feels_like']}{unit_sym},"
        f" min {weather['temp_min']}{unit_sym},"
        f" max {weather['temp_max']}{unit_sym}).",
        f"Condition: {weather['description']}.",
        f"Humidity: {weather['humidity']}%.",
        f"Wind: {weather['wind_speed']} {speed_unit}.",
        f"Cloud cover: {weather['cloud_coverage']}%.",
    ]

    if weather.get("rain_1h_mm"):
        parts.append(f"Rain last hour: {weather['rain_1h_mm']} mm.")
    if weather.get("snow_1h_mm"):
        parts.append(f"Snow last hour: {weather['snow_1h_mm']} mm.")

    return " ".join(parts)


# Private helpers 
def _parse(data: dict, units: str) -> dict:
    """
    Transforms raw OWM JSON into a clean flat dict.
    Uses .get() with defaults everywhere — OWM omits keys
    when values are zero or unavailable.
    
    Args:
        data (dict): the json response from get_weather
        units (str): units value
        
    Returns:
        dict: a flatten dictionary that contains the cleaned data from the response
    """
    weather_info = data.get("weather", [{}])[0]
    main         = data.get("main",    {})
    wind         = data.get("wind",    {})
    sys          = data.get("sys",     {})
    clouds       = data.get("clouds",  {})
    rain         = data.get("rain",    {})
    snow         = data.get("snow",    {})

    unit_label, unit_sym, speed_unit = UNIT_LABELS.get(units, UNIT_LABELS["metric"])

    result = {
        "success":       True,
        "units_param":   units,
        # Location
        "location":      data.get("name", "Unknown"),
        "country":       map_country_code(sys.get("country", "")),
        # Temperature
        "temperature":   main.get("temp"),
        "feels_like":    main.get("feels_like"),
        "temp_min":      main.get("temp_min"),
        "temp_max":      main.get("temp_max"),
        "unit":          unit_label,
        "unit_symbol":   unit_sym,
        # Atmosphere
        "humidity":      main.get("humidity"),      # %
        "pressure":      main.get("pressure"),      # hPa
        # Condition
        "condition":     weather_info.get("main", ""),  
        "description":   weather_info.get("description", ""),
        # Wind
        "wind_speed":    wind.get("speed"),
        "wind_deg":      wind.get("deg"),
        "wind_unit":     speed_unit,
        # Extras
        "cloud_coverage": clouds.get("all",  0),    # %
        "rain_1h_mm":     rain.get("1h",     0),
        "snow_1h_mm":     snow.get("1h",     0),
        "visibility_m":   data.get("visibility"),   # metres
    }

    logger.info(
        "Weather fetched: %s, %s — %s %.1f%s",
        result["location"], result["country"],
        result["description"], result["temperature"], unit_sym,
    )
    return result


def _error(message: str) -> dict:
    """
    Returns a standardised failure dict.

    Args:
        message (str): error message
        
    Returns:
        dict: contains status and error message    
    """
    logger.warning("Weather API error: %s", message)
    return {"success": False, "error": message}