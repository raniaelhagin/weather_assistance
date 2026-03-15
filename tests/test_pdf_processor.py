import sys
import os

# Add the project root to Python's search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.pdf_processor import parse_pdf1, parse_pdf2, merge_and_build_chuncks, load_and_chuck_pdfs
from config import PDF1_PATH, PDF2_PATH


result1 = parse_pdf1(PDF1_PATH)
result2 = parse_pdf2(PDF2_PATH)

print(f"length of parsed data from PDF1: {len(result1)}")
print(f"\nKeys of parsed PDF1 data: {result1.keys()}")
print(f"\nFoggy conditions in Egypt and temperature range: {result1[('Foggy Conditions', 'Egypt')]}")
print("-"*100)

print(f"length of parsed data from PDF2: {len(result2)}")
print(f"\nKeys of parsed PDF2 data: {result2.keys()}")
print(f"\nSnowy Conditions in Canada activities and clothing recommendations: {result2[('Snowy Conditions', 'Canada')]}")
print("-"*100)

print(f"Length of data after merging both documents: {len(merge_and_build_chuncks(result1, result2))}")
print("-"*100)

load_and_chuck_pdfs(PDF1_PATH, PDF2_PATH)