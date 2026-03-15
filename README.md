# 🌤️ Weather Assistant

A conversational AI assistant that answers free-text questions about **current weather**, **outdoor activities**, and **clothing recommendations** for any city in the world — powered by an open-source LLM, live weather data, and a vector knowledge base.

---

## Overview

The system accepts natural language queries like:

- *"What should I wear in Cairo tonight?"*
- *"Is London good for hiking this morning?"*
- *"Suggest outdoor activities for Tokyo this afternoon"*

It then runs a five-step pipeline to return a structured, context-aware response grounded in live weather data and a curated knowledge base.

---

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  Step 1 — LLM Function Calling  (Llama 3.3 / Groq) │
│  Extracts: location, units, time_of_day             │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  Step 2 — Weather API  (OpenWeatherMap)             │
│  Returns: live temperature, condition, wind, etc.   │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  Step 3 — Search Query Generation  (LLM)           │
│  Rewrites query + weather into semantic search str  │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  Step 4 — Vector Search  (FAISS + MiniLM)          │
│  Retrieves top-5 relevant KB chunks                 │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  Step 5 — Final Response  (LLM)                    │
│  Synthesizes weather + KB into structured answer    │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
            Streamlit UI Response
```

---

## Project Structure

```
weather_assistance/
│
├── app.py                        # Streamlit UI — entry point
├── orchestrator.py               # Pipeline coordinator
├── config.py                     # All constants and configuration
├── main.py                       # CLI entry point for testing
│
├── modules/                      # Core business logic
│   ├── __init__.py
│   ├── llm_client.py             # Groq / Llama LLM interactions
│   ├── pdf_processor.py          # Parses PDFs into chunk dicts
│   ├── vector_db.py              # FAISS index builder and searcher
│   └── weather_api.py            # OpenWeatherMap integration
│
├── utils/                        # Shared, domain-agnostic helpers
│   ├── __init__.py
│   ├── http_utils.py             # Retry logic for API calls
│   ├── llm_client_utils.py       # Tool / function definition for LLM
│   ├── logger.py                 # Centralised logging
│   ├── pdf_utils.py              # Low-level PDF text extraction
│   ├── text_utils.py             # String cleaning and parsing helpers
│   └── vector_utils.py           # KB context formatter for LLM prompt
│
├── data/
│   ├── pdf1_conditions.pdf       # 5 countries × 10 weather conditions
│   ├── pdf2_activity_clothing.pdf # 10 countries × 5 conditions
│   └── faiss_index/              # Auto-created on first run
│       ├── index.faiss
│       └── chunks.pkl
│
├── tests/
│   ├── test_llm_client.py
│   ├── test_pdf_processor.py
│   ├── test_vector_db.py
│   └── test_weather_api.py
│
├── .env                          # Your API keys (never commit this)
├── .env.example                  # Template — copy to .env
├── .gitignore
├── requirements.txt
├── install_requirements.cmd      # Windows installer script
└── README.md
```

---

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd weather_assistance
```

### 2. Install dependencies

**Windows:**
```bash
install_requirements.cmd
```

**macOS / Linux:**
```bash
pip install -r requirements.txt
```

### 3. Configure API keys

```bash
cp .env.example .env
```

Edit `.env` and add your keys:

```bash
GROQ_API_KEY=gsk_your-key-here
OPENWEATHER_API_KEY=your-owm-key-here
```

| Key | Where to get it |
|---|---|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) — free tier |
| `OPENWEATHER_API_KEY` | [openweathermap.org/api](https://openweathermap.org/api) — free tier |

### 4. Build the knowledge base index

Place your PDF files in the `data/` folder, then run the app — the FAISS index is built automatically on first launch and cached to `data/faiss_index/` for all subsequent runs.

### 5. Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Module Documentation

### `modules/llm_client.py`

Manages all interactions with the Groq API (Llama 3.3). Uses the OpenAI-compatible client pointed at Groq's endpoint.

| Method | Description |
|---|---|
| `extract_weather_params(query)` | Function calling — extracts location, units, time_of_day |
| `generate_search_query(query, weather, time)` | Rewrites query as semantic search string |
| `generate_final_response(query, weather, kb, time)` | Produces structured 3-section markdown answer |

**Function calling** is used in step 1. The LLM reads a tool definition (`WEATHER_TOOL` in `utils/llm_client_utils.py`) and returns structured arguments — `location`, `units`, `time_of_day` — which the orchestrator then passes to the real `get_weather()` function. The LLM never calls the API directly.

---

### `modules/weather_api.py`

Fetches live weather from OpenWeatherMap and returns a clean flat dict.

| Function | Description |
|---|---|
| `get_weather(location, units, api_key)` | Fetches and normalises weather data |
| `format_weather_summary(weather)` | Formats weather dict as a readable string for LLM prompts |

Returns `{"success": True, ...weather fields...}` on success, or `{"success": False, "error": "..."}` on failure. All HTTP errors are caught — 401, 404, timeouts, and connection errors each produce a specific user-friendly message.

---

### `modules/pdf_processor.py`

Parses two PDFs into structured chunk dicts and merges them.

| Function | Description |
|---|---|
| `load_and_chunk_pdfs(pdf1, pdf2)` | Main entry point — parses both, merges, returns chunks |
| `parse_pdf1(path)` | Extracts `{(condition, country): {narrative, temp_high, temp_low}}` |
| `parse_pdf2(path)` | Extracts `{(condition, country): {activities, clothing}}` |
| `merge_and_build_chunks(data1, data2)` | Merges on `(condition, country)` key, builds text blocks |

**PDF 1** — 5 countries × 10 conditions — narrative descriptions + temperature ranges.
**PDF 2** — 10 countries × 5 conditions — structured activity and clothing bullet lists.

Merging is done on normalized `(condition, country)` keys. Country variants like `"USA (California)"` are mapped to canonical names via `COUNTRY_NORMALIZATION` in `config.py`. Condition aliases like `"Sunny Weather"` → `"Clear/Sunny Weather"` are handled via `CONDITION_ALIASES`.

---

### `modules/vector_db.py`

FAISS-backed vector store using `all-MiniLM-L6-v2` embeddings (384 dimensions, runs locally).

| Method | Description |
|---|---|
| `build(chunks)` | Embeds all texts, builds `IndexFlatIP`, stores parallel chunk list |
| `search(query, top_k)` | Embeds query, returns top-k chunks with similarity scores |
| `save(directory)` | Persists `index.faiss` + `chunks.pkl` to disk |
| `VectorDB.load(directory)` | Loads saved index — fast path on subsequent runs |

Uses `IndexFlatIP` (exact inner-product search on L2-normalised vectors = cosine similarity). Sufficient for corpora under ~100k chunks with no approximate search error.

---

### `orchestrator.py`

Single entry point connecting all modules. The app only imports this.

```python
assistant = WeatherAssistant()
result    = assistant.answer("What should I wear in Cairo tonight?")
```

**Error handling strategy:**

| Step | Failure behaviour |
|---|---|
| Step 1 (LLM) | Hard stop — returns error immediately |
| Step 2 (Weather API) | Hard stop — returns weather error with location info |
| Step 3 (Search query) | Soft fail — falls back to raw user query |
| Step 4 (Vector search) | Soft fail — continues with empty KB context |
| Step 5 (LLM response) | Soft fail — returns weather summary + error note |

---

### `utils/`

| File | Contents |
|---|---|
| `logger.py` | `get_logger(__name__)` — consistent log format across all modules |
| `http_utils.py` | `get_with_retry()` — exponential backoff for API calls |
| `text_utils.py` | `clean_line`, `match_condition`, `match_country`, `extract_temp`, `normalize_condition`, `normalize_country`, `split_activities`, `split_clothing`, `map_country_code` |
| `pdf_utils.py` | `extract_text()`, `extract_pages()` — pdfplumber wrapper |
| `llm_client_utils.py` | `WEATHER_TOOL` — the function calling schema shown to the LLM |
| `vector_utils.py` | `format_retrieved_context()` — formats KB chunks for the LLM prompt |

---

## Configuration (`config.py`)

All constants in one place — nothing is hardcoded in modules.

```python
# Paths
PDF1_PATH   = "data/pdf1_conditions.pdf"
PDF2_PATH   = "data/pdf2_activity_clothing.pdf"
INDEX_DIR   = "data/faiss_index"

# LLM
GROQ_MODEL  = "llama-3.3-70b-versatile"
MAX_TOKENS  = 1024
DEFAULT_CITY = "Cairo, EG"

# Vector DB
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K_RESULTS   = 5

# Weather API
OWM_BASE_URL    = "https://api.openweathermap.org/data/2.5/weather"
REQUEST_TIMEOUT = 10
MAX_RETRIES     = 3

# Knowledge base mappings
CONDITION_ALIASES     = { "Sunny Weather": "Clear/Sunny Weather", ... }
COUNTRY_NORMALIZATION = { "USA (California)": "USA", ... }
COUNTRY_CODE_MAP      = { "EG": "Egypt", "GB": "United Kingdom", ... }
```

---

## Knowledge Base

The vector database is built from two PDFs:

**PDF 1** — `pdf1_conditions.pdf`
Covers 5 countries × 10 weather conditions. Each entry contains a narrative description and temperature range (high/low in °C).

Countries: Egypt, United Kingdom, USA, Japan, Australia

Conditions: Clear/Sunny, Partly Cloudy, Cloudy/Overcast, Light Rain/Drizzle, Heavy Rain/Stormy, Snowy, Windy, Foggy, Hot and Dry, Cold and Freezing

**PDF 2** — `pdf2_activity_clothing.pdf`
Covers 10 countries × 5 weather conditions. Each entry contains structured activity recommendations and clothing guidance.

Countries: Egypt, USA (California), Japan, Brazil, India, Canada, Australia, Russia (Sochi), United Kingdom, South Africa (Cape Town)

Conditions: Sunny, Rainy, Snowy, Windy, Cloudy

Each merged chunk contains the narrative, temperature range, activities, and clothing in a single text block — one chunk per `(condition, country)` pair.

---

## Running Tests

```bash
# From the project root
pytest tests/

# Individual module
pytest tests/test_pdf_processor.py -v
pytest tests/test_vector_db.py -v
pytest tests/test_weather_api.py -v
pytest tests/test_llm_client.py -v
```

Tests use `conftest.py` in the `tests/` folder to add the project root to `sys.path` automatically.

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `openai` | ≥ 1.30.0 | Groq API client (OpenAI-compatible) |
| `requests` | ≥ 2.31.0 | OpenWeatherMap HTTP calls |
| `faiss-cpu` | ≥ 1.8.0 | Vector similarity search |
| `sentence-transformers` | ≥ 2.7.0 | Local text embeddings (MiniLM) |
| `numpy` | ≥ 1.26.0 | FAISS dependency |
| `pdfplumber` | ≥ 0.11.0 | PDF text extraction |
| `pypdf` | ≥ 4.0.0 | PDF fallback extractor |
| `streamlit` | ≥ 1.35.0 | Web UI |
| `python-dotenv` | ≥ 1.0.0 | `.env` file loading |

> `sentence-transformers` downloads the `all-MiniLM-L6-v2` model (~90 MB) on first run. It is cached in `~/.cache/torch/sentence_transformers/` and reused on all subsequent runs.

---

## Design Decisions

**Groq + Llama 3.3** — Open-source, free tier, fast inference, OpenAI-compatible API. Switching to GPT-4 or Claude requires changing only two lines in `llm_client.py` and `config.py`.

**Function calling for location extraction** — More robust than regex or prompt parsing. The LLM reliably extracts location, units, and time of day from any phrasing in any language.

**Semantic chunking over word-count chunking** — One chunk per `(condition, country)` pair. This matches the retrieval granularity exactly — a query about Egypt in rainy weather retrieves exactly the Egypt/rainy chunk, not a fragmented subset.

**FAISS IndexFlatIP** — Exact cosine search (via L2-normalised inner product). No approximation error. Fast enough for 50–100 chunks; swap for `IndexIVFFlat` if scaling to 100k+.

**Two-stage LLM pipeline** — The search query rewriting step (step 3) meaningfully improves retrieval quality by enriching the user's original question with live weather context before embedding.

**Graceful degradation** — Steps 3, 4, and 5 all have fallbacks. A weather API failure returns a clear message. A vector search failure still produces an LLM response from general knowledge. The app never crashes silently.

---

## Limitations

- Weather data is current-conditions only — no forecasts.
- Knowledge base covers 5–10 countries. Queries for unlisted countries return general recommendations.
- `time_of_day` extraction (morning/afternoon/evening/night) is used to tailor suggestions but does not affect the weather API call, which always returns current conditions.
- Groq free tier has rate limits — heavy usage may require a paid plan.
