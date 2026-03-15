# utils/pdf_utils.py
"""
Low-level PDF text extraction.
"""

from pathlib import Path
from utils.logger import get_logger
import pdfplumber
import re

logger = get_logger(__name__)

def extract_text(pdf_path: str) -> str:
    """
    Extract raw text from a PDF. Tries pdfplumber first, falls back to pypdf.
    Returns a single string with pages joined by newlines.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    with pdfplumber.open(str(path)) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
        text = "\n".join(pages)

    if not text.strip():
        raise ValueError(f"Could not extract any text from: {pdf_path}")

    logger.info("Extracted %d characters from %s", len(text), path.name)
    return text


def extract_pages(pdf_path: str) -> list[tuple[int, str]]:
    """
    Same as extract_text but returns [(page_number, text), ...].
    Useful for debugging — you can see which page a chunk came from.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    with pdfplumber.open(str(path)) as pdf:
        return [(i + 1, page.extract_text() or "")
                for i, page in enumerate(pdf.pages)]
        
