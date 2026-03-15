# llm_client_utils.py
"""
LLM client helpers
"""

from config import DEFAULT_CITY

# Tool definition 
WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": (
            "Fetches live weather data for a location. "
            "Call this for any question about weather, activities, or clothing. "
            "All answers depend on live weather - never answer from memory alone."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": (
                        "City with country code e.g. 'Cairo, EG', 'London, GB'. "
                        f"Default to '{DEFAULT_CITY}' if not mentioned."
                    ),
                },
                "units": {
                    "type": "string",
                    "enum": ["metric", "imperial"],
                    "description": (
                        "'metric' for Celsius (default). "
                        "'imperial' for Fahrenheit - only if user explicitly asks "
                    ),
                },
                "time_of_day": {
                    "type": "string",
                    "enum": ["morning", "afternoon", "evening", "night", "unknown"],
                    "description": (
                        "Time of day from the query. "
                        "'tonight': 'night', 'this morning': 'morning'. "
                        "Default 'unknown'."
                    ),
                },
            },
            "required": ["location"],
        },
    },
}


