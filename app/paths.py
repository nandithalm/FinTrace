"""Repo-root paths. Shared by ingest, RAG retrieve, and the insight engine."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
KB_DIR = DATA_DIR / "kb"
CHROMA_DIR = DATA_DIR / "chroma"
TRANSACTIONS_PATH = DATA_DIR / "transactions.json"
EVAL_QUERIES_PATH = DATA_DIR / "eval_queries.json"
HF_CACHE_PATH = KB_DIR / "hf_chunks.json"

COLLECTION_NAME = "fintrace_policy"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
SIMILARITY_FLOOR = 0.35
RETRIEVE_K = 3
HF_ROW_CAP = 150
HF_DATASET = "sidddd625/adaption-banking-and-digital-payments"
