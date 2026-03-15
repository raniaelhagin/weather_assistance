# PDF Processor

import re
from pathlib import Path
from config import PDF1_PATH, PDF2_PATH, PDF1_CONDITIONS, PDF1_COUNTRIES, PDF2_CONDITIONS, PDF2_COUNTRIES, CONDITION_ALIASES, COUNTRY_NORMALIZATION
from utils.pdf_utils  import extract_text
from utils.text_utils import *

def load_and_chuck_pdfs(pdf1_path: str, pdf2_path: str) -> list[dict]:
    """Main entry point, parses two pdfs, merge them on one 
    (condition, country) pairs, and return a list of chunck dicts

    Args:
        pdf1_path (str): the full path of the first pdf
        pdf2_path (str): the full path of the second pdf

    Returns:
        list[dict]: a list of chuncks per each (condition, country) pair
    """
    pdf1_data = parse_pdf1(pdf1_path)
    pdf2_data = parse_pdf2(pdf2_path)
    
    return merge_and_build_chuncks(pdf1_data, pdf2_data)


def save_collection(
    result: dict, 
    condition: str | None, 
    country: str | None, 
    content_lines: list[str],
    is_pdf1: bool
) -> None:
    """Writes a completed PDF1 block into result.
       Called whenever a new condition or country header is detected,
       and once more after the loop ends.
       Does nothing if any required piece is missing.

    Args:
        result (dict): dictionary of condition and country that contains country data
        condition (str | None): condition description
        country (str | None): country name
        content_lines (list[str]): block of lines
        is_pdf1 (bool): checks if pdf1 or 2 to return the appropriate result

    Returns:
        None
    """
    if not (condition and country and content_lines):
        return
    
    block = " ".join(content_lines)
    if is_pdf1:
        result[(condition, country)] = {
            "narrative": extract_narrative(block),
            "temp_high": extract_temp(block, "high"),
            "temp_low":  extract_temp(block, "low"),
        }
    else:
        activities, clothing = extract_activities_and_clothing(block)
        result[normalize_condition(condition), normalize_country(country)] = {
            "activities": activities,
            "clothing": clothing
        }
        

def extract_activities_and_clothing(block: str) -> tuple[list[str], list[str]]:
    """
    Given a raw text block for one country, extracts activities and clothing
    by finding the boundaries between the two sections.

    Args:
        block (str): raw text for one (condition, country) pair

    Returns:
        tuple: (activities_list, clothing_list)
    """
    # find boundaries
    activities_match = re.search(r"outdoor activities\s*:", block, re.IGNORECASE)
    clothing_match   = re.search(r"appropriate clothing\s*:", block, re.IGNORECASE)

    activities_text = ""
    clothing_text   = ""

    if activities_match and clothing_match:
        # Both sections found — extract between them
        activities_start = activities_match.end()
        clothing_start   = clothing_match.end()

        activities_text  = block[activities_start:clothing_match.start()].strip()
        clothing_text    = block[clothing_start:].strip()

    elif activities_match and not clothing_match:
        # Only activities found
        activities_text  = block[activities_match.end():].strip()

    elif clothing_match and not activities_match:
        # Only clothing found
        clothing_text    = block[clothing_match.end():].strip()

    return activities_text, clothing_text


def parse_pdf1(pdf_path: str) -> dict:
    """Parse PDF1 to return (condition, country) pair that its value contains
    narrative, temp_high and temp_low 
    
    Args:
        pdf_path (str): pdf path
        
    Returns:
        dict: (condition, country) pair
            {
            ("Clear/Sunny Weather", "Egypt"): {
                "narrative": "In Egypt, clear and sunny...",
                "temp_high": "32°C to 38°C",
                "temp_low":  "18°C to 24°C",
            },
            ...
            }
    """
    text = extract_text(pdf_path)
    lines = [clean_line(l) for l in text.splitlines()]
    
    current_condition = None
    current_country   = None
    content_lines     = []
    result = {}

    for line in lines:
        # new condition header found
        matched_condition = match_condition(line, PDF1_CONDITIONS)
        if matched_condition:
            # Save collection
            save_collection(result, current_condition, 
                                 current_country, content_lines, True)
            current_condition = matched_condition
            current_country   = None
            content_lines     = []
            continue
        
        # new country header found
        matched_country = match_country(line, PDF1_COUNTRIES)
        if matched_country:
            # Save collection
            save_collection(result, current_condition, 
                                 current_country, content_lines, True)
            current_country = matched_country
            content_lines = []
            continue
        
        if current_condition and current_country:
            content_lines.append(line)
            
    save_collection(result, current_condition, 
                         current_country, content_lines, True)
    return result        
            

def parse_pdf2(pdf_path: str) -> dict:
    """Parse PDF2 to return (condition, country) pair that its value contains
    activities and clothing

    Args:
        pdf_path (str): pdf path

    Returns:
        dict: (condition, country) pair
            {
            ("Sunny Weather", "Egypt"): {
                "activities": ["Sightseeing...", "Desert safaris..."],
                "clothing":   ["Lightweight clothing...", "Sunscreen..."],
            },
            ...
            }
    """
    text = extract_text(pdf_path)
    lines = [clean_line(l) for l in text.splitlines()]
    
    current_condition = None
    current_country   = None
    content_line      = []
    result            = {}

    for line in lines:
        # new condition header found
        matched_condition = match_condition(line, PDF2_CONDITIONS)
        if matched_condition:
            # Save collection
            save_collection(result, current_condition, 
                                 current_country, content_line, False)
            current_condition = matched_condition
            current_country   = None
            content_line      = []
            continue
        
        matched_country = match_country(line, PDF2_COUNTRIES)
        if matched_country:
            # Save collection
            save_collection(result, current_condition, 
                                 current_country, content_line, False)
            current_country = matched_country
            content_line    = []
            continue
        
        if current_condition and current_country:
            content_line.append(line)
            
    save_collection(result, current_condition, 
                         current_country, content_line, False)
    return result
   

def build_chunk_text(condition: str, country: str, d1: dict, d2: dict) -> str:
    """Assemble a single coherent text block for embedding.

    Args:
        condition (str): weather condition
        country (str): country
        d1 (dict): dict of the value extracted from pdf1 for (condition, country) pair
        d2 (dict): dict of the value extracted from pdf2 for (condition, country) pair
    Returns:
        str: chunk text block
    """
    parts = [f"Condition: {condition}", f"Country: {country}"]

    if d1.get("narrative"):
        parts.append(d1["narrative"])

    if d1.get("temp_high") or d1.get("temp_low"):
        parts.append(
            f"Temperature range — High: {d1.get('temp_high','')},"
            f" Low: {d1.get('temp_low','')}."
        )

    if d2.get("activities"):
        parts.append("Recommended activities: " + d2["activities"] + ".")

    if d2.get("clothing"):
        parts.append("Clothing recommendations: " + d2["clothing"] + ".")

    return "\n".join(parts)


def merge_and_build_chuncks(data1: dict, data2:dict) -> list[dict]:
    """Merge both dicts on normalized (condition, country) keys.
       Builds one rich text chunk per pair.

    Args:
        data1 (dict): parsed fata from pdf1
        data2 (dict): parsed data from pdf2

    Returns:
        list[dict]: list of text chuncks
    """
    
    # Collect all unique (condition, country) pairs from both
    all_keys = set(data1.keys()) | set(data2.keys())
    
    chunks = []
    for (condition, country) in sorted(all_keys):
        d1 = data1.get((condition, country), {})
        d2 = data2.get((condition, country), {})

        chunk_text = build_chunk_text(condition, country, d1, d2)

        chunks.append({
            "text"     : chunk_text,
            "condition": condition,
            "country"  : country,
            "temp_high": d1.get("temp_high", ""),
            "temp_low" : d1.get("temp_low", ""),
            "source"   : "knowledge_base",
        })

    return chunks