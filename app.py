# app.py
"""
Streamlit UI for the Weather Assistant.
Professional editorial theme — navy, amber accent, IBM Plex Sans.

Run with:
    streamlit run app.py
"""

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Weather Assistant",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

/* ── Variables ── */
:root {
    --navy-900:  #0a0f1e;
    --navy-800:  #111827;
    --navy-700:  #1a2540;
    --navy-600:  #243052;
    --navy-400:  #3d4f73;
    --navy-200:  #8896b3;
    --navy-100:  #c5cedd;
    --navy-050:  #eef1f6;
    --amber:     #f59e0b;
    --amber-dim: #fbbf24;
    --green:     #10b981;
    --red:       #ef4444;
    --white:     #ffffff;
    --border:    rgba(255,255,255,0.07);
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: var(--navy-900) !important;
    color: var(--navy-050) !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--navy-800) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] * { color: var(--navy-100) !important; }
section[data-testid="stSidebar"] .stTextInput input {
    background: var(--navy-700) !important;
    border: 1px solid var(--navy-400) !important;
    color: var(--white) !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.78rem !important;
}
section[data-testid="stSidebar"] .stButton button {
    background: var(--navy-700) !important;
    border: 1px solid var(--navy-400) !important;
    color: var(--navy-100) !important;
    border-radius: 6px !important;
    font-size: 0.78rem !important;
    text-align: left !important;
    transition: all 0.15s !important;
}
section[data-testid="stSidebar"] .stButton button:hover {
    border-color: var(--amber) !important;
    color: var(--amber) !important;
    background: var(--navy-600) !important;
}

/* ── Page title ── */
.page-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.8rem;
    color: var(--white);
    letter-spacing: -0.02em;
    margin-bottom: 2px;
}
.page-subtitle {
    font-size: 0.82rem;
    color: var(--navy-200);
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* ── Divider ── */
.styled-divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 18px 0;
}

/* ── Sidebar title ── */
section[data-testid="stSidebar"] h3 {
    font-family: 'DM Serif Display', serif !important;
    font-size: 1.4rem !important;    /* ← explicit size */
    color: var(--white) !important;
}

/* ── User bubble ── */
.user-bubble-wrap { text-align: right; margin: 12px 0; }
.user-bubble {
    display: inline-block;
    background: var(--navy-600);
    border: 1px solid var(--navy-400);
    border-radius: 12px 12px 2px 12px;
    padding: 10px 16px;
    font-size: 0.9rem;
    color: var(--navy-050);
    max-width: 75%;
    text-align: left;
}

/* ── Assistant bubble ── */
.assistant-bubble {
    background: var(--navy-800);
    border: 1px solid var(--border);
    border-left: 3px solid var(--amber);
    border-radius: 0 10px 10px 10px;
    padding: 16px 20px;
    font-size: 0.92rem;
    color: var(--navy-050);
    line-height: 1.75;
    margin: 12px 0 8px 0;
}
.assistant-bubble h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 1.05rem !important;   /* ← cap h1 inside bubble */
    color: var(--white);
}
.assistant-bubble h2 {
    font-family: 'DM Serif Display', serif;
    font-size: 1rem !important;      /* ← cap h2 inside bubble */
    color: var(--white);
}
.assistant-bubble h3 {
    font-family: 'DM Serif Display', serif;
    font-size: 0.95rem !important;   /* ← cap h3 inside bubble */
    color: var(--white);
    margin-top: 14px;
    margin-bottom: 4px;
}
.assistant-bubble strong { color: var(--amber-dim); }

/* ── Weather card ── */
.weather-card {
    background: var(--navy-700);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px 24px;
    margin: 8px 0 4px 0;
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 24px;
    align-items: start;
}
.weather-temp {
    font-family: 'DM Serif Display', serif;
    font-size: 3.2rem;
    color: var(--amber);
    line-height: 1;
}
.weather-location {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--navy-200);
    margin-bottom: 4px;
}
.weather-condition {
    font-size: 1rem;
    color: var(--navy-050);
    text-transform: capitalize;
    margin-top: 4px;
}
.weather-feels {
    font-size: 0.78rem;
    color: var(--navy-200);
    margin-top: 2px;
}
.weather-metrics {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
}
.metric-chip {
    background: var(--navy-600);
    border: 1px solid var(--navy-400);
    border-radius: 4px;
    padding: 3px 10px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: var(--navy-100);
}
.metric-chip span { color: var(--navy-200); font-size: 0.68rem; margin-right: 4px; }

/* ── Pipeline panel ── */
.pipeline-panel {
    background: var(--navy-800);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 18px;
    margin: 4px 0 16px 0;
}
.pipeline-header {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--navy-400);
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
}
.pipeline-row {
    display: grid;
    grid-template-columns: 120px 1fr;
    gap: 8px;
    align-items: baseline;
    margin-bottom: 8px;
}
.pipeline-key {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--navy-400);
}
.pipeline-val {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: var(--navy-100);
    background: var(--navy-700);
    border-radius: 4px;
    padding: 3px 8px;
    word-break: break-word;
}

/* ── KB chunks ── */
.kb-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 8px;
    margin-top: 10px;
}
.kb-chunk {
    background: var(--navy-700);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 10px 12px;
}
.kb-chunk-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}
.kb-chunk-label {
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--amber-dim);
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.kb-score {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    background: var(--navy-600);
    border-radius: 3px;
    padding: 1px 6px;
    color: var(--green);
}
.kb-chunk-text {
    font-size: 0.75rem;
    color: var(--navy-200);
    line-height: 1.5;
}

/* ── Input area ── */
.stTextInput input {
    background: var(--navy-800) !important;
    border: 1px solid var(--navy-400) !important;
    border-radius: 8px !important;
    color: var(--white) !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.92rem !important;
    padding: 12px 16px !important;
    transition: border-color 0.2s !important;
}
.stTextInput input:focus {
    border-color: var(--amber) !important;
    box-shadow: 0 0 0 2px rgba(245,158,11,0.15) !important;
}

/* ── Primary button ── */
.stButton button[kind="primary"] {
    background: var(--amber) !important;
    color: var(--navy-900) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.02em !important;
    padding: 10px 24px !important;
    transition: opacity 0.15s !important;
}
.stButton button[kind="primary"]:hover { opacity: 0.88 !important; }

/* ── Status box ── */
.stStatus { background: var(--navy-800) !important; border-color: var(--border) !important; }

/* ── Alerts ── */
.stAlert { border-radius: 8px !important; }

/* ── Error ── */
.stAlert[data-baseweb="notification"] {
    background: rgba(239,68,68,0.1) !important;
    border-color: var(--red) !important;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 80px 20px;
    color: var(--navy-400);
}
.empty-icon { font-size: 2.8rem; margin-bottom: 12px; }
.empty-title { font-family: 'DM Serif Display', serif; font-size: 1.3rem; color: var(--navy-200); }
.empty-sub { font-size: 0.82rem; margin-top: 6px; color: var(--navy-400); }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--navy-600); border-radius: 3px; }

/* ── Hide Streamlit chrome ── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Weather icon map ──────────────────────────────────────────────────────────
CONDITION_ICONS = {
    "clear": "☀️", "sun": "☀️", "cloud": "☁️",
    "rain": "🌧️", "drizzle": "🌦️", "thunder": "⛈️",
    "storm": "⛈️", "snow": "❄️", "mist": "🌫️",
    "fog": "🌫️",  "haze": "🌁",  "wind": "💨",
}

def get_weather_icon(condition: str) -> str:
    c = condition.lower()
    for key, icon in CONDITION_ICONS.items():
        if key in c:
            return icon
    return "🌤️"

def wind_direction(degrees) -> str:
    if degrees is None:
        return ""
    dirs = ["N","NE","E","SE","S","SW","W","NW"]
    return dirs[round(degrees / 45) % 8]


# ── Session state ─────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []


# ── Cached assistant ──────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_assistant(groq_key: str, owm_key: str):
    from orchestrator import WeatherAssistant
    return WeatherAssistant(groq_api_key=groq_key, owm_api_key=owm_key)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🌤️ Weather Assistant")
    st.caption("Llama 3.3 · OpenWeatherMap · FAISS")
    st.divider()

    st.markdown("**Configuration**")
    groq_key = st.text_input(
        "Groq API Key", type="password",
        value=os.getenv("GROQ_API_KEY", ""),
        placeholder="gsk_...",
    )
    owm_key = st.text_input(
        "OpenWeatherMap Key", type="password",
        value=os.getenv("OPENWEATHER_API_KEY", ""),
        placeholder="your key",
    )

    st.divider()
    st.markdown("**Examples**")
    examples = [
        "What to wear in Cairo tonight?",
        "Activities in London this morning?",
        "Is Tokyo good for hiking today?",
        "Weather in New York right now?",
        "Suggest activities for Sydney afternoon",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True, key=f"ex_{ex[:12]}"):
            st.session_state["prefill"] = ex

    st.divider()
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.history = []
        st.rerun()


# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    "<div class='page-title'>Weather Intelligence</div>"
    "<div class='page-subtitle'>Live conditions · Activity suggestions · Outfit guidance</div>",
    unsafe_allow_html=True,
)
st.markdown("<hr class='styled-divider'>", unsafe_allow_html=True)


# ── Render weather card ───────────────────────────────────────────────────────
def render_weather_card(weather: dict) -> None:
    if not weather.get("success"):
        return

    icon      = get_weather_icon(weather.get("condition", ""))
    unit_sym  = "°C" if weather.get("unit") == "Celsius" else "°F"
    wind_dir  = wind_direction(weather.get("wind_deg"))
    location  = f"{weather.get('location','')}, {weather.get('country_code','')}"

    metrics = [
        ("HUM",  f"{weather.get('humidity')}%"),
        ("WIND", f"{weather.get('wind_speed')} {weather.get('wind_unit','m/s')} {wind_dir}"),
        ("CLOUD",f"{weather.get('cloud_coverage')}%"),
        ("HIGH", f"{weather.get('temp_max')}{unit_sym}"),
        ("LOW",  f"{weather.get('temp_min')}{unit_sym}"),
    ]
    if weather.get("rain_1h_mm"):
        metrics.append(("RAIN", f"{weather['rain_1h_mm']} mm/h"))
    if weather.get("snow_1h_mm"):
        metrics.append(("SNOW", f"{weather['snow_1h_mm']} mm/h"))

    chips = "".join(
        f"<div class='metric-chip'><span>{k}</span>{v}</div>"
        for k, v in metrics
    )

    st.markdown(f"""
    <div class='weather-card'>
        <div>
            <div class='weather-temp'>{icon} {weather.get('temperature')}{unit_sym}</div>
            <div class='weather-feels'>Feels like {weather.get('feels_like')}{unit_sym}</div>
        </div>
        <div>
            <div class='weather-location'>{location}</div>
            <div class='weather-condition'>{weather.get('description','').capitalize()}</div>
            <div class='weather-metrics'>{chips}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Render pipeline panel ─────────────────────────────────────────────────────
def render_pipeline(result: dict) -> None:
    rows = [
        ("Location",    result.get("location",    "—")),
        ("Time of day", result.get("time_of_day", "—")),
        ("Units",       result.get("units",        "—")),
        ("Search query",result.get("search_query", "—")),
    ]

    rows_html = "".join(
        f"<div class='pipeline-row'>"
        f"<div class='pipeline-key'>{k}</div>"
        f"<div class='pipeline-val'>{v}</div>"
        f"</div>"
        for k, v in rows
    )

    kb_results = result.get("kb_results", [])
    chunks_html = ""
    if kb_results:
        cards = ""
        for chunk in kb_results:
            cards += (
                f"<div class='kb-chunk'>"
                f"<div class='kb-chunk-header'>"
                f"<span class='kb-chunk-label'>"
                f"{chunk.get('condition','?')} · {chunk.get('country','?')}</span>"
                f"<span class='kb-score'>{chunk.get('score',0):.3f}</span>"
                f"</div>"
                f"<div class='kb-chunk-text'>{chunk.get('text','')[:160]}…</div>"
                f"</div>"
            )
        chunks_html = (
            f"<div class='pipeline-row'>"
            f"<div class='pipeline-key'>KB chunks</div>"
            f"<div style='grid-column:2'>"
            f"<div class='kb-grid'>{cards}</div>"
            f"</div></div>"
        )

    st.markdown(f"""
    <div class='pipeline-panel'>
        <div class='pipeline-header'>Pipeline trace</div>
        {rows_html}
        {chunks_html}
    </div>
    """, unsafe_allow_html=True)


# ── Chat history ──────────────────────────────────────────────────────────────
for entry in st.session_state.history:
    if entry["role"] == "user":
        st.markdown(
            f"<div class='user-bubble-wrap'>"
            f"<span class='user-bubble'>{entry['content']}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown("<div class='assistant-bubble'>", unsafe_allow_html=True)
        st.markdown(entry["content"])
        st.markdown("</div>", unsafe_allow_html=True)
        meta = entry.get("meta", {})
        if meta.get("weather", {}).get("success"):
            render_weather_card(meta["weather"])
        if meta:
            render_pipeline(meta)
        st.markdown("<hr class='styled-divider'>", unsafe_allow_html=True)


# ── Input ─────────────────────────────────────────────────────────────────────
prefill = st.session_state.pop("prefill", "")
query   = st.text_input(
    "Your query",
    value=prefill,
    placeholder="Ask about weather, activities, or what to wear in any city...",
    label_visibility="collapsed",
    key="query_input",
)

col_btn, col_hint = st.columns([1, 5])
with col_btn:
    submit = st.button("Ask →", type="primary", use_container_width=True)
with col_hint:
    st.caption("Mention a city for live weather data.")


# ── Submit handler ────────────────────────────────────────────────────────────
if submit and query.strip():
    if not groq_key:
        st.error("Groq API key required. Add it in the sidebar.")
        st.stop()
    if not owm_key:
        st.error("OpenWeatherMap key required. Add it in the sidebar.")
        st.stop()

    st.session_state.history.append({"role": "user", "content": query.strip()})

    with st.status("Running pipeline...", expanded=True) as status:
        st.write("① Extracting location and time of day...")
        try:
            assistant = get_assistant(groq_key, owm_key)
        except Exception as e:
            st.error(f"Initialisation failed: {e}")
            st.stop()

        st.write("② Fetching live weather data...")
        st.write("③ Searching knowledge base...")
        st.write("④ Generating response...")
        result = assistant.answer(query.strip())
        status.update(label="Complete", state="complete", expanded=False)

    if result.get("error") and not result.get("final_response"):
        st.error(result["error"])
        st.stop()

    st.session_state.history.append({
        "role":    "assistant",
        "content": result.get("final_response", ""),
        "meta":    result,
    })
    st.rerun()


# ── Empty state ───────────────────────────────────────────────────────────────
if not st.session_state.history:
    st.markdown("""
    <div class='empty-state'>
        <div class='empty-icon'>🌍</div>
        <div class='empty-title'>Ask anything about the weather</div>
        <div class='empty-sub'>
            Live conditions · Outdoor activities · Clothing recommendations
        </div>
    </div>
    """, unsafe_allow_html=True)