# modules/vector_db.py

import pickle
from pathlib import Path
from typing import List, Dict
import faiss
import numpy as np

from utils.logger import get_logger

logger = get_logger(__name__)


class VectorDB:
    """
    FAISS-backed vector store for weather knowledge base chunks.

    Workflow:
        db = VectorDB()
        db.build(chunks)    # embed + index
        results = db.search("query", top_k=5)
        db.save("data/faiss_index")
        db = VectorDB.load("data/faiss_index")
    """

    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    def __init__(self):
        self._model  = None   
        self._index  = None   # faiss index
        self._chunks = []     # parallel list of chunk dicts

    # Build FAISS index
    def build(self, chunks: List[Dict]) -> None:
        """
        Embeds all chunk texts and builds the FAISS index.

        Args:
            chunks (List[Dict]): list of dicts from pdf_processor, each must have a 'text' key
        """
        if not chunks:
            raise ValueError("Cannot build VectorDB from empty chunk list.")

        model      = self._get_model()
        texts      = [chunk["text"] for chunk in chunks]

        logger.info(f"Embedding {len(texts)} chunks...")
        embeddings = model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,   # unit length: inner product = cosine similarity
        ).astype("float32")

        # Build IndexFlatIP — exact inner product search (cosine for normalised vectors)
        dim          = embeddings.shape[1]   # 384 for MiniLM
        self._index  = faiss.IndexFlatIP(dim)
        self._index.add(embeddings)
        self._chunks = chunks

        logger.info("VectorDB built: %d vectors, dim=%d", self._index.ntotal, dim)

    # Search for a query in top_k similar chunks
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Returns the top_k most relevant chunks for the query.

        Args:
            query (str):  natural language search string
            top_k (int):  number of results to return

        Returns:
            list of chunk dicts sorted by descending similarity score,
            each chunk gets an extra 'score' key added
        """
        if self._index is None:
            raise RuntimeError("VectorDB is not built yet. Call build() or load() first.")

        model = self._get_model()
        query_vec = model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

        # Clamp top_k to available chunks
        k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(query_vec, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:          # FAISS uses -1 for empty slots
                continue
            chunk = self._chunks[idx].copy()
            chunk["score"] = float(score)
            results.append(chunk)

        logger.info("Search returned %d results for query: '%s'", len(results), query[:60])
        return results

    # Save FAISS index and chunk list
    def save(self, directory: str) -> None:
        """
        Saves the FAISS index and chunk list to disk.

        Args:
            directory (str): folder to save into (created if it doesn't exist)
        """
        
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self._index, str(path / "index.faiss"))

        with open(path / "chunks.pkl", "wb") as f:
            pickle.dump(self._chunks, f)

        logger.info("VectorDB saved to %s (%d chunks)", directory, len(self._chunks))

    @classmethod
    def load(cls, directory: str) -> "VectorDB":
        """
        Loads a previously saved VectorDB from disk.

        Args:
            directory (str): folder containing index.faiss and chunks.pkl

        Returns:
            a ready-to-search VectorDB instance
        """

        path = Path(directory)
        index_path  = path / "index.faiss"
        chunks_path = path / "chunks.pkl"

        if not index_path.exists() or not chunks_path.exists():
            raise FileNotFoundError(
                f"No saved VectorDB found in '{directory}'. "
                "Run build() and save() first."
            )

        db         = cls()
        db._index  = faiss.read_index(str(index_path))

        with open(chunks_path, "rb") as f:
            db._chunks = pickle.load(f)

        logger.info("VectorDB loaded from %s (%d chunks)", directory, len(db._chunks))
        return db

    # Properties
    @property
    def size(self) -> int:
        """Number of indexed chunks."""
        return len(self._chunks)

    @property
    def is_built(self) -> bool:
        """True if the index has been built or loaded."""
        return self._index is not None and self._index.ntotal > 0

    # internal method to get model
    def _get_model(self):
        """Lazy-loads the embedding model on first call."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model: %s", self.EMBEDDING_MODEL)
            self._model = SentenceTransformer(self.EMBEDDING_MODEL)
        return self._model