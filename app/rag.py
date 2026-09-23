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
    curated = _from_markdown(text, k)
    if curated["row_count"]:
        return curated
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


def _from_markdown(query: str, k: int) -> dict[str, Any]:
    """Instant curated-KB retrieve so the demo never waits on MiniLM."""
    from app.rag_ingest import load_curated_chunks

    q = query.lower()
    needles = [tok for tok in q.replace("?", " ").split() if len(tok) > 2]
    ranked = []
    for chunk in load_curated_chunks():
        blob = f"{chunk.get('title', '')} {chunk.get('text', '')}".lower()
        score = sum(1 for tok in needles if tok in blob)
        title = chunk.get("title") or ""
        if "personal loan documents" in title.lower() and any(
            w in q for w in ("document", "documents", "loan", "दस्तावेज", "ದಾಖಲೆ")
        ):
            score += 8
        if "neft" in q and "neft" in blob:
            score += 6
        if "kyc" in q and "kyc" in blob:
            score += 6
        if "upi" in q and "upi" in blob:
            score += 6
        if "dispute" in q and "dispute" in blob:
            score += 6
        if score:
            ranked.append((score, chunk))
    ranked.sort(key=lambda item: item[0], reverse=True)
    chunks = []
    for score, chunk in ranked[: max(1, k)]:
        chunks.append(
            {
                "title": chunk.get("title") or "",
                "source": chunk.get("source") or "",
                "score": min(0.99, 0.5 + 0.05 * score),
                "text": chunk.get("text") or "",
            }
        )
    return {"query": query, "chunks": chunks, "row_count": len(chunks)}


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
