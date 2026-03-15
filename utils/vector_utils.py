# utils/vector_utils.py

def format_retrieved_context(results: list, max_chunks: int = 5) -> str:
    """
    Formats vector search results into a clean string for the LLM prompt.

    Args:
        results (list): list of chunk dicts from VectorDB.search()
        max_chunks (int): maximum number of chunks to include

    Returns:
        str: numbered context block ready for the LLM
    """
    if not results:
        return "No relevant knowledge-base entries found."

    lines = ["Relevant knowledge-base excerpts:"]
    for i, chunk in enumerate(results[:max_chunks], start=1):
        lines.append(
            f"\n[{i}] Country: {chunk.get('country', '?')} | "
            f"Condition: {chunk.get('condition', '?')} | "
            f"Score: {chunk.get('score', 0):.3f}\n"
            f"{chunk['text']}"
        )
    return "\n".join(lines)