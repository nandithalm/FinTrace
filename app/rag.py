"""Policy RAG retrieve. Builder 3 routes policy_rag -> retrievePolicyChunks.

Similarity floor 0.35, k=3 (docs/03_ARCHITECTURE_DESIGN.md, docs/05_API_CONTRACT.md).
Rupees are never taken from chunks; only policy text is returned.
"""

from __future__ import annotations

from typing import Any

from app.paths import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL, RETRIEVE_K, SIMILARITY_FLOOR


def retrieve_policy(query: str, k: int = RETRIEVE_K) -> dict[str, Any]:
    """GET /api/mock/policy/search — chunks after the similarity floor."""
    text = (query or "").strip()
    empty = {"query": text, "chunks": [], "row_count": 0}
    if not text:
        return empty
    try:
        collection = _collection()
    except Exception:
        return empty
    try:
        result = collection.query(
            query_texts=[text],
            n_results=max(1, k),
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        return empty
    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    chunks = []
    for doc, meta, distance in zip(documents, metadatas, distances):
        score = _similarity(distance)
        if score < SIMILARITY_FLOOR:
            continue
        meta = meta or {}
        chunks.append(
            {
                "title": meta.get("title") or "",
                "source": meta.get("source") or "",
                "score": round(float(score), 4),
                "text": doc or "",
            }
        )
    return {"query": text, "chunks": chunks, "row_count": len(chunks)}


def retrievePolicyChunks(query: str, k: int = RETRIEVE_K) -> dict[str, Any]:
    """Alias matching the architecture diagram name for Builder 3."""
    return retrieve_policy(query, k=k)


def _similarity(distance: float) -> float:
    """Chroma cosine space stores distance = 1 - cosine similarity."""
    return 1.0 - float(distance)


def _collection():
    if not CHROMA_DIR.exists():
        raise FileNotFoundError("Chroma not built. Run python -m app.rag_ingest")
    import chromadb
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    return client.get_collection(name=COLLECTION_NAME, embedding_function=embedding_fn)
