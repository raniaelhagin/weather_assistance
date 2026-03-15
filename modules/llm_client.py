# modules/llm_client.py
"""
LLM interactions using Groq (Llama 3.1) — open source, free tier.
Uses OpenAI-compatible client pointed at Groq's endpoint.

Three jobs:
1. extract_weather_params()  — function calling to extract location + time
2. generate_search_query()   — semantic search string for vector DB
3. generate_final_response() — final structured answer for the user
"""

import os
import json
from typing import Optional
from openai import OpenAI

from config import GROQ_MODEL, MAX_TOKENS, DEFAULT_CITY
from utils.logger import get_logger
from utils.llm_client_utils import WEATHER_TOOL

logger = get_logger(__name__)


# LLMClient 
class LLMClient:
    """
    Wraps the Groq API using the OpenAI-compatible client.
    Exposes three methods used by the orchestrator.
    """

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.getenv("GROQ_API_KEY", "")
        if not key:
            raise ValueError(
                "Groq API key not found. "
                "Set the GROQ_API_KEY environment variable. "
                "Get a free key at console.groq.com"
            )

        self._client = OpenAI(
            api_key=key,
            base_url="https://api.groq.com/openai/v1",
        )
        logger.info("LLMClient initialised — model: %s", GROQ_MODEL)
    
    # Extract location + time via function calling
    def extract_weather_params(self, user_query: str) -> dict:
        """
        Sends user query to Llama with the weather tool definition.
        Llama extracts location, units, and time_of_day as structured args.
        We return those args — the orchestrator uses them to call 
        get_weather().

        Args:
            user_query (str): raw user input

        Returns:
            {
                "tool_called":  True,
                "location":     "Cairo, EG",
                "units":        "metric",
                "time_of_day":  "night"
            }
            or if no tool was called:
            {
                "tool_called":  False,
                "raw_response": "Llama's direct text answer"
            }
        """
        logger.info("Extracting weather params from: '%s'", user_query[:60])

        response = self._client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a weather assistant. "
                        "When the user asks about weather, activities, or clothing, "
                        "you MUST call the get_current_weather tool. "
                        "Extract the location and time of day carefully from their message."
                    ),
                },
                {
                    "role": "user",
                    "content": user_query,
                },
            ],
            tools=[WEATHER_TOOL],
            tool_choice={
                "type": "function",
                "function": {"name": "get_current_weather"}   # force to use the tool
            },
        )

        message = response.choices[0].message

        # if tool is called by llm
        if message.tool_calls:
            tool_call = message.tool_calls[0]

            # Parse arguments
            args = json.loads(tool_call.function.arguments)

            location    = args.get("location",    DEFAULT_CITY)
            units       = args.get("units",       "metric")
            time_of_day = args.get("time_of_day", "unknown")

            logger.info(
                "Tool called: location='%s', units='%s', time='%s'",
                location, units, time_of_day,
            )
            return {
                "tool_called":  True,
                "location":     location,
                "units":        units,
                "time_of_day":  time_of_day,
            }

        # tool not called - get llm answer directly
        logger.info("No tool call - LLM responded directly")
        return {
            "tool_called":  False,
            "raw_response": message.content or "",
        }

    # Generate vector DB search query
    def generate_search_query(
        self,
        user_query:      str,
        weather_summary: str,
        time_of_day:     str = "unknown",
    ) -> str:
        """
        Rewrites user query + weather context into a short
        semantic search string optimised for vector similarity.

        Args:
            user_query:      original user question
            weather_summary: formatted string from format_weather_summary()
            time_of_day:     extracted in extract_weather_params

        Returns:
            str — search query for vector DB
        """
        logger.info("Generating search query...")

        prompt = (
            f"User question: {user_query}\n"
            f"Time of day: {time_of_day}\n"
            f"Current weather: {weather_summary}\n\n"
            "Rewrite the above as a short semantic search query (1-2 sentences) "
            "to retrieve the most relevant clothing and activity recommendations "
            "from a knowledge base.\n"
            "Include: weather condition, temperature range, time of day, user intent.\n"
            "Return ONLY the search query — no explanation, no preamble."
        )

        response = self._client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )

        query = response.choices[0].message.content.strip()
        logger.info("Search query: '%s'", query)
        return query

    # Generate final response
    def generate_final_response(
        self,
        user_query:      str,
        weather_summary: str,
        kb_context:      str,
        time_of_day:     str = "unknown",
    ) -> str:
        """
        Synthesizes weather data + KB chunks into a structured answer.

        Args:
            user_query:      original user question
            weather_summary: live weather as formatted string
            kb_context:      top-k KB chunks as formatted string
            time_of_day:     morning / afternoon / evening / night / unknown

        Returns:
            str - markdown response with 3 sections
        """
        logger.info("Generating final response...")

        # Add time context to the prompt when we know it
        time_context = (
            f"The user is asking about the {time_of_day} specifically. "
            "Tailor your activity and clothing suggestions to that time of day."
            if time_of_day != "unknown"
            else ""
        )

        response = self._client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful weather assistant. "
                        "Answer in a warm, practical, and concise tone. "
                        "Structure your response in exactly three sections:\n"
                        "1. **Weather Overview** - describe how the weather feels and what kind of day it is in natural, " "conversational language. Do NOT mention numbers, humidity, wind speed, pressure, or technical "
                        "metrics. Instead say things like 'it is a hot and " "sunny afternoon' or 'expect a chilly, overcast " "evening'. Only mention the temperature.\n"
                        "2. **Suggested Activities** - 3 to 5 outdoor activities suited to the weather.\n"
                        "3. **Clothing Recommendations** - practical outfit advice.\n\n"
                        "Base activities and clothing on the knowledge-base excerpts. "
                        "Use general knowledge only to fill gaps.\n"
                        f"{time_context}"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"User question: {user_query}\n\n"
                        f"--- Live Weather ---\n{weather_summary}\n\n"
                        f"--- Knowledge Base ---\n{kb_context}"
                    ),
                },
            ],
        )

        answer = response.choices[0].message.content.strip()
        logger.info("Final response generated (%d chars)", len(answer))
        return answer
