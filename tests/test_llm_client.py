import sys
import os
from dotenv import load_dotenv

# Add the project root to Python's search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.llm_client import LLMClient
from modules.weather_api import get_weather, format_weather_summary

load_dotenv()
weather_apikey = os.getenv("OPENWEATHER_API_KEY", "")
groq_apikey = os.environ.get("GROQ_API_KEY")

llmClient = LLMClient(groq_apikey)

user_query = "What should I wear in Australia tommorrow morining?"
weather_params = llmClient.extract_weather_params(user_query)

print(f"Extracted location details in the query: {user_query} is: {weather_params}")

if weather_params["tool_called"]:
    location = weather_params["location"]
    units = weather_params["units"]
    time_of_day = weather_params["time_of_day"]
    
    weather_data = get_weather(location, units, weather_apikey)
    weather_summary = format_weather_summary(weather_data)
    
    search_query = llmClient.generate_search_query(user_query, weather_summary, time_of_day)
    
    print(f"Generated search query: {search_query}")

