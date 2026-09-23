"""Build the local Chroma index from curated KB markdown plus optional HF cache.

Run: python -m app.rag_ingest

If Hugging Face download fails, curated markdown alone is enough for the
loan-documents demo beat (docs/04_DATA_AND_PRIVACY.md).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.paths import (
    CHROMA_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    HF_CACHE_PATH,
    HF_DATASET,
    HF_ROW_CAP,
    KB_DIR,
)

HF_ALLOW_NEEDLES = (
    "upi",
    "kyc",
    "card",
    "dispute",
    "account",
    "net banking",
    "netbanking",
    "transfer",
    "neft",
    "imps",
    "rtgs",
    "payment",
    "loan",
    "fd",
    "deposit",
)


def parse_markdown_chunks(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8")
    title = path.stem.replace("_", " ").title()
    body_lines: list[str] = []
    chunks: list[dict] = []
    source = f"data/kb/{path.name}"

    def flush() -> None:
        text = "\n".join(body_lines).strip()
        if not text:
            return
        chunks.append({"title": title, "source": source, "text": text})

    for line in raw.splitlines():
        if line.startswith("# "):
            flush()
            title = line[2:].strip()
            body_lines = []
        elif line.startswith("## "):
            flush()
            title = line[3:].strip()
            body_lines = []
        else:
            body_lines.append(line)
    flush()
    return chunks


def load_curated_chunks() -> list[dict]:
    chunks: list[dict] = []
    for path in sorted(KB_DIR.glob("*.md")):
        chunks.extend(parse_markdown_chunks(path))
    return chunks


def load_hf_chunks(refresh: bool = False) -> list[dict]:
    if HF_CACHE_PATH.exists() and not refresh:
        try:
            cached = json.loads(HF_CACHE_PATH.read_text(encoding="utf-8"))
            if isinstance(cached, list):
                return cached
        except json.JSONDecodeError:
            pass
    rows = _download_hf_subset()
    HF_CACHE_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return rows


def _allowed_subdomain(value: str) -> bool:
    lower = (value or "").lower()
    return any(needle in lower for needle in HF_ALLOW_NEEDLES)


def _download_hf_subset() -> list[dict]:
    try:
        from datasets import load_dataset
    except ImportError:
        print("datasets not installed; skipping Hugging Face subset", file=sys.stderr)
        return []
    try:
        ds = load_dataset(HF_DATASET, split="train")
    except Exception as exc:
        print(f"Hugging Face download failed ({exc}); curated KB only", file=sys.stderr)
        return []
    kept: list[dict] = []
    for row in ds:
        subdomain = str(row.get("subdomain") or "")
        if not _allowed_subdomain(subdomain):
            continue
        text = str(row.get("answer_guidance") or "").strip()
        if not text:
            continue
        source = str(row.get("source") or f"huggingface:{HF_DATASET}")
        title = subdomain.strip() or "Banking FAQ"
        query = str(row.get("user_query") or "").strip()
        body = text if not query else f"{query}\n{text}"
        kept.append(
            {
                "title": title,
                "source": source,
                "text": body,
                "subdomain": subdomain,
            }
        )
        if len(kept) >= HF_ROW_CAP:
            break
    return kept


def persist_chroma(chunks: list[dict]) -> int:
    import chromadb
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )
    ids = []
    documents = []
    metadatas = []
    for index, chunk in enumerate(chunks):
        text = (chunk.get("text") or "").strip()
        if not text:
            continue
        ids.append(f"chunk-{index}")
        documents.append(text)
        metadatas.append(
            {
                "title": chunk.get("title") or "",
                "source": chunk.get("source") or "",
            }
        )
    if not ids:
        raise SystemExit("No chunks to index. Add data/kb/*.md")
    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    return len(ids)


def main(argv: list[str] | None = None) -> int:
    refresh_hf = "--refresh-hf" in (argv or sys.argv[1:])
    curated = load_curated_chunks()
    hf_rows = load_hf_chunks(refresh=refresh_hf)
    combined = curated + hf_rows
    count = persist_chroma(combined)
    print(f"Indexed {count} chunks ({len(curated)} curated, {len(hf_rows)} HF cache) -> {CHROMA_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
