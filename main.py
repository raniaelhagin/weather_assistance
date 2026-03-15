# main.py
from orchestrator import WeatherAssistant

assistant = WeatherAssistant()
result    = assistant.answer("What should I wear in Cairo tonight?")

print("Location:   ", result["location"])
print("Time:       ", result["time_of_day"])
print("Weather:    ", result["weather_summary"])
print("Search Q:   ", result["search_query"])
print("KB chunks:  ", len(result["kb_results"]))
print("\nFinal Response:\n", result["final_response"])

if result["error"]:
    print("\nError:", result["error"])