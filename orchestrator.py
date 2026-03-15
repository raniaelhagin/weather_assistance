# orchestrator.py
"""
Connects all modules into a single pipeline.
The app only interacts with this file - nothing else.

Pipeline:
    1. LLM extracts location + time  (function calling)
    2. Weather API fetches live data
    3. LLM generates search query
    4. Vector DB retrieves KB chunks
    5. LLM generates final response
"""

import os
from pathlib import Path
from dotenv  import load_dotenv

from modules.llm_client  import LLMClient
from modules.weather_api import get_weather, format_weather_summary
from modules.vector_db   import VectorDB
from utils.vector_utils  import format_retrieved_context
from utils.logger        import get_logger
from config              import (
    PDF1_PATH, PDF2_PATH,
    INDEX_DIR,
    TOP_K_RESULTS,
)

load_dotenv()
logger = get_logger(__name__)


class WeatherAssistant:
    """
    Single entry point for the entire pipeline.
    
    Usage:
        assistant = WeatherAssistant()
        result    = assistant.answer("What should I wear in Cairo tonight?")
    """

    def __init__(
        self,
        groq_api_key:  str | None = None,
        owm_api_key:   str | None = None,
    ):
        # API keys
        self._owm_key = owm_api_key or os.getenv("OPENWEATHER_API_KEY", "")
        self._groq_key = groq_api_key or os.getenv("GROQ_API_KEY", "")

        # Initialise LLM client
        self._llm = LLMClient(api_key=self._groq_key)

        # Initialise vector DB
        self._vdb   = self._load_vector_db()
        self._ready = self._vdb is not None

    # Vector DB loader
    def _load_vector_db(self) -> VectorDB | None:
        """
        Loads the saved FAISS index from disk.
        If not found, attempts to build from PDFs.
        Returns None if both fail.
        """
        index_path = Path(INDEX_DIR) / "index.faiss"

        # Fast path: load from disk
        if index_path.exists():
            try:
                db = VectorDB.load(INDEX_DIR)
                logger.info("VectorDB loaded — %d chunks", db.size)
                return db
            except Exception as e:
                logger.warning("Failed to load VectorDB: %s — rebuilding...", e)

        # build from PDFs
        if Path(PDF1_PATH).exists() and Path(PDF2_PATH).exists():
            try:
                from modules.pdf_processor import load_and_chunk_pdfs
                logger.info("Building VectorDB from PDFs...")
                chunks = load_and_chunk_pdfs(PDF1_PATH, PDF2_PATH)
                db     = VectorDB()
                db.build(chunks)
                db.save(INDEX_DIR)
                logger.info("VectorDB built and saved — %d chunks", db.size)
                return db
            except Exception as e:
                logger.error("Failed to build VectorDB: %s", e)
                return None

        logger.error(
            "No VectorDB found and no PDFs available. "
            "Place PDFs in '%s'", INDEX_DIR
        )
        return None

    # Main pipeline
    def answer(self, user_query: str) -> dict:
        """
        Runs the full pipeline from user query to final response.

        Args:
            user_query (str): free-text user input

        Returns:
            {
                "final_response":  str,      # markdown answer for the user
                "location":        str,
                "units":           str,
                "time_of_day":     str,
                "weather":         dict,     # full weather data
                "weather_summary": str,
                "search_query":    str,
                "kb_results":      list,     # top-k chunks with scores
                "error":           str|None
            }
        """
        # Initialise result dict
        result = {
            "final_response":  "",
            "location":        "",
            "units":           "metric",
            "time_of_day":     "unknown",
            "weather":         {},
            "weather_summary": "",
            "search_query":    "",
            "kb_results":      [],
            "error":           None,
        }

        # Step 1: Extract location + time via function calling
        logger.info("Step 1 — extracting weather params...")
        try:
            params = self._llm.extract_weather_params(user_query)
        except Exception as e:
            result["error"]          = f"LLM error: {e}"
            result["final_response"] = f"Could not process your query: {e}"
            return result

        # LLM answered directly without calling the tool
        if not params.get("tool_called"):
            result["final_response"] = params.get("raw_response", "")
            return result

        result["location"]    = params["location"]
        result["units"]       = params.get("units", "metric")
        result["time_of_day"] = params.get("time_of_day", "unknown")

        # Step 2: Fetch live weather
        logger.info("Step 2 — fetching weather for '%s'...", result["location"])
        weather = get_weather(
            location = result["location"],
            units    = result["units"],
            api_key  = self._owm_key,
        )
        result["weather"] = weather

        # Hard stop — can't continue without weather data
        if not weather.get("success"):
            error_msg = weather.get("error", "Weather API error")
            result["error"] = error_msg
            result["final_response"] = (
                f"Could not retrieve weather for **{result['location']}**.\n\n"
                f"{error_msg}\n\n"
                "Please check the location name and try again."
            )
            return result

        weather_summary = format_weather_summary(weather)
        result["weather_summary"] = weather_summary

        # Step 3: Generate semantic search query
        logger.info("Step 3 — generating search query...")
        try:
            search_query = self._llm.generate_search_query(
                user_query      = user_query,
                weather_summary = weather_summary,
                time_of_day     = result["time_of_day"],
            )
            result["search_query"] = search_query
        except Exception as e:
            # Graceful fallback — use user query directly
            logger.warning("Search query generation failed: %s — using user query", e)
            search_query           = user_query
            result["search_query"] = search_query

        # Step 4: Vector DB search
        logger.info("Step 4 — searching knowledge base...")
        kb_results = []
        if self._ready:
            try:
                kb_results = self._vdb.search(search_query, top_k=TOP_K_RESULTS)
                result["kb_results"] = kb_results
            except Exception as e:
                logger.warning("Vector search failed: %s — continuing without KB", e)

        kb_context = format_retrieved_context(kb_results)

        # Step 5: Generate final response
        logger.info("Step 5 — generating final response...")
        try:
            final_response = self._llm.generate_final_response(
                user_query      = user_query,
                weather_summary = weather_summary,
                kb_context      = kb_context,
                time_of_day     = result["time_of_day"],
            )
            result["final_response"] = final_response
        except Exception as e:
            logger.error("Final response generation failed: %s", e)
            result["error"]          = f"Response generation failed: {e}"
            result["final_response"] = (
                f"**Weather Summary**\n{weather_summary}\n\n"
                f"_Could not generate full recommendations: {e}_"
            )

        logger.info("Pipeline complete.")
        return result