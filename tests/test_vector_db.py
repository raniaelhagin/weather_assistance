import sys
import os

# Add the project root to Python's search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    
from modules.pdf_processor import load_and_chuck_pdfs
from modules.vector_db import VectorDB
from config import PDF1_PATH, PDF2_PATH, INDEX_DIR

# Build once
chunks = load_and_chuck_pdfs(PDF1_PATH, PDF2_PATH)
db = VectorDB()
db.build(chunks)
db.save(INDEX_DIR)

print("Index size:", db.size)

# Search
results = db.search("rainy weather clothing UK", top_k=3)
for r in results:
    print(r["condition"], r["country"], r["score"])

# Load on next run (fast)
db = VectorDB.load(INDEX_DIR)