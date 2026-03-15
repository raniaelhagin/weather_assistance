#utils/config.py
"""
All constants should be here, to avoid using hardcoded values
"""

from pathlib import Path

# -------------------------------- Paths --------------------------------
BASE_DIR       = Path(__file__).parent
DATA_DIR       = BASE_DIR / "data"
PDF1_PATH      = DATA_DIR / "pdf1_conditions.pdf"
PDF2_PATH      = DATA_DIR / "pdf2_activity_clothing.pdf"
INDEX_DIR      = DATA_DIR / "faiss_index"

# ---------------------------- Knowledge Base ----------------------------
PDF1_CONDITIONS = [
    "Clear/Sunny Weather",
    "Partly Cloudy Weather",
    "Cloudy/Overcast Weather",
    "Light Rain/Drizzle",
    "Heavy Rain/Stormy/Thunderstorms",
    "Snowy Conditions",
    "Windy Conditions",
    "Foggy Conditions",
    "Hot and Dry Conditions",
    "Cold and Freezing Conditions",
]
PDF1_COUNTRIES = ["Egypt", "United Kingdom", "USA", "Japan", "Australia"]

PDF2_CONDITIONS = [
    "Sunny Weather",
    "Rainy Weather",
    "Snowy Weather",
    "Windy Weather",
    "Cloudy Weather",
]
PDF2_COUNTRIES = [
    "Egypt", "USA (California)", "Japan", "Brazil", 
    "India", "Canada", "Australia", "Russia (Sochi)", 
    "United Kingdom", "South Africa (Cape Town)",
]

# Maps PDF2 condition names to PDF1 condition names (canonical)
CONDITION_ALIASES = {
    "Sunny Weather" : "Clear/Sunny Weather",
    "Rainy Weather" : "Light Rain/Drizzle",
    "Snowy Weather" : "Snowy Conditions",
    "Windy Weather" : "Windy Conditions",
    "Cloudy Weather": "Cloudy/Overcast Weather",
}

# Maps PDF2 country names to PDF1 county names
COUNTRY_NORMALIZATION = {
    "USA (California)": "USA"
}

# ---------------------------- Vector DB ----------------------------
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K_RESULTS   = 5
CHUNK_OVERLAP   = 80    # words

# ---------------------------- LLM ----------------------------
CLAUDE_MODEL    = "claude-sonnet-4-20250514"
MAX_TOKENS      = 1024
DEFAULT_UNITS   = "metric"
DEFAULT_CITY    = "Cairo, EG"

# ---------------------------- Weather API ----------------------------
OWM_BASE_URL    = "https://api.openweathermap.org/data/2.5/weather"
REQUEST_TIMEOUT = 10     # seconds
MAX_RETRIES     = 3

COUNTRY_CODE_MAP = {
    # Countries in our knowledge base — exact names must match
    "EG": "Egypt",
    "GB": "United Kingdom",
    "US": "USA",
    "JP": "Japan",
    "AU": "Australia",
    "BR": "Brazil",
    "IN": "India",
    "CA": "Canada",
    "RU": "Russia (Sochi)",
    "ZA": "South Africa (Cape Town)",
}

# ---------------------------- LLM API ----------------------------
GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS   = 1024
DEFAULT_CITY = "Cairo, EG"