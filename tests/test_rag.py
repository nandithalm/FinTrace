"""RAG retrieve tests. Ingest must run first for the citation hit."""

import pytest

from app.paths import KB_DIR
from app.rag import retrieve_policy
from app.rag_ingest import load_curated_chunks, parse_markdown_chunks


def test_curated_kb_has_nine_markdown_files():
    files = sorted(p.name for p in KB_DIR.glob("*.md"))
    assert files == [
        "account_opening.md",
        "cards.md",
        "fd_savings.md",
        "kyc.md",
        "loan_documents.md",
        "loan_policies.md",
        "neft_rtgs_imps.md",
        "transaction_dispute.md",
        "upi.md",
    ]


def test_personal_loan_documents_chunk_title():
    path = KB_DIR / "loan_documents.md"
    chunks = parse_markdown_chunks(path)
    titles = [c["title"] for c in chunks]
    assert "Personal Loan Documents" in titles
    loan = next(c for c in chunks if c["title"] == "Personal Loan Documents")
    assert "PAN" in loan["text"] and "Aadhaar" in loan["text"]
    assert loan["source"] == "data/kb/loan_documents.md"


def test_curated_chunk_count_nonzero():
    assert len(load_curated_chunks()) >= 9


def test_retrieve_loan_documents_when_chroma_built():
    result = retrieve_policy("What documents do I need for a personal loan?")
    if result["row_count"] == 0:
        pytest.skip("Chroma not built — run python -m app.rag_ingest")
    titles = [c["title"] for c in result["chunks"]]
    assert "Personal Loan Documents" in titles
    assert any("PAN" in (c.get("text") or "") for c in result["chunks"])
