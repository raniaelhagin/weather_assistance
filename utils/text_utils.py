# text_utils.py
"""
Pure string utilities
"""

import re
from config import CONDITION_ALIASES, COUNTRY_NORMALIZATION, COUNTRY_CODE_MAP

def clean_line(line: str) -> str:
    """Normalise whitespace and strip leading bullet characters."""
    line = line.strip()
    line = re.sub(r"^[^a-zA-Z0-9]+", "", line)   # strip bullet
    line = re.sub(r"\s+", " ", line)            # collapse whitespace
    return line

def normalize_whitespace(text: str) -> str:
    """Collapse all whitespace sequences to single spaces."""
    return re.sub(r"\s+", " ", text).strip()

def match_condition(line: str, conditions: list) -> str | None:
    """Return the matching condition name if this line is a condition header."""
    stripped = re.sub(r"^\d+[.)]\s*", "", line).strip()
    for cond in conditions:
        # Flexible: handles "Clear/Sunny Weather", "CLEAR/SUNNY WEATHER", etc.
        if stripped.lower().startswith(cond.lower()):
            remaining = stripped[len(cond):].strip()
            if len(remaining) < 15:
                return cond
    return None

def match_country(line: str, countries: list) -> str | None:
    """Return matching country name. Handles 'Egypt' and 'Egypt:'."""
    clean = line.rstrip(":").strip()
    for country in countries:
        if clean.lower() == country.lower():
            return country
    return None

def extract_narrative(text: str) -> str:
    """Return text before the 'Temperature Range:' section."""
    split = re.split(r"temperature range", text, flags=re.IGNORECASE)
    if len(split) < 2:
        return ""
    
    return split[0].strip()

def extract_temp(text: str, which: str) -> str:
    """
    Extract temperature range string.
    which = "high" or "low"
    Looks for: "High: 32°C to 38°C" or "High: 32°C–38°C"
    """
    split = re.split(r"temperature range", text, flags=re.IGNORECASE)
    if len(split) < 2:
        return ""
    
    text = split[1].strip()
    stop = "low" if which == "high" else "high"
    pattern = rf"{which}\s*[:\-]\s*(.*?)(?=\s*{stop}\s*[:\-]|\Z)"
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else ""

def normalize_condition(condition: str) -> str:
    """
    Maps PDF2 condition names to their PDF1 canonical equivalents.
    If no mapping exists, returns the name unchanged.
    
    Args:
        condition (str): condition name from either PDF
        
    Returns:
        str: canonical condition name (PDF1 format)
    """
    return CONDITION_ALIASES.get(condition, condition)

def normalize_country(country: str) -> str:
    """
    Maps PDF2 country variants to their PDF1 canonical equivalents.
    Only maps entries where PDF1 has a matching general country.
    Entries with no PDF1 match are returned unchanged — partial chunks are fine.
    
    Args:
        country (str): country name from either PDF
        
    Returns:
        str: canonical country name
    """
    return COUNTRY_NORMALIZATION.get(country, country)

def split_activities(text: str) -> list[str]:
    """
    Splits a comma-separated activities string into individual items.
    
    Input:  "Sightseeing at historical sites, exploring outdoor markets, Nile cruises"
    Output: ["Sightseeing at historical sites", "exploring outdoor markets", "Nile cruises"]
    """
    items = re.split(r",(?![^(]*\))", text)
    return [item.strip().rstrip(".") for item in items if item.strip()]


def split_clothing(text: str) -> list[str]:
    """
    Splits a clothing recommendation string into individual sentences.
    
    Input:  "Lightweight clothing is recommended. Sunglasses are advisable. A light jacket helps."
    Output: ["Lightweight clothing is recommended", "Sunglasses are advisable", "A light jacket helps"]
    """
    items = re.split(r"(?<=[.!?])\s+", text.strip())
    return [item.strip().rstrip(".") for item in items if item.strip()]

def get_section_label(line: str) -> str | None:
    """
    Returns 'activities' or 'clothing' if the line is a section header.
    Returns None if it's a regular content line.
    """
    if re.match(r"^outdoor activities\s*:", line, re.IGNORECASE):
        return "activities"
    if re.match(r"^appropriate clothing\s*:", line, re.IGNORECASE):
        return "clothing"
    return None


def strip_section_label(line: str) -> str:
    """
    Removes the section label from the start of a line.
    Returns the content that follows the colon.

    Input:  "Outdoor Activities: Hiking in national parks..."
    Output: "Hiking in national parks..."

    Input:  "Hiking in national parks..."   (no label)
    Output: "Hiking in national parks..."   (unchanged)
    """
    cleaned = re.sub(r"^outdoor activities\s*:", "", line, flags=re.IGNORECASE)
    cleaned = re.sub(r"^appropriate clothing\s*:", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

def map_country_code(code: str) -> str:
    """
    Maps an ISO country code to its full name in our knowledge base.
    Returns the code unchanged if no mapping exists.

    Args:
        code: ISO 3166-1 alpha-2 country code e.g. "EG", "GB", "US"

    Returns:
        str: full country name e.g. "Egypt", "United Kingdom", "USA"
             or the original code if not in our database e.g. "DE" → "DE"

    Examples:
        map_country_code("EG")   → "Egypt"
        map_country_code("GB")   → "United Kingdom"
        map_country_code("DE")   → "DE"   (not in our KB, returned as-is)
    """
    return COUNTRY_CODE_MAP.get(code.upper(), code)