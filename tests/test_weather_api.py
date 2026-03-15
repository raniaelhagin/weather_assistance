import sys
import os
from dotenv import load_dotenv

# Add the project root to Python's search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.weather_api import get_weather, format_weather_summary

load_dotenv()
key = os.getenv("OPENWEATHER_API_KEY", "")

weather_response = get_weather("New York", api_key=key)

print(format_weather_summary(weather_response))