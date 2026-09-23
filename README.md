# FinTrace

Prototype banking customer query assistant (TCS Technology Day).

**Prototype · simulated data · not a real bank.**

## Repo

```text
docs/                 spec pack (start here)
app/                  orchestrator, mock bank, RAG, insights
data/                 synthetic JSON
data/kb/              policy markdown + HF cache
data/chroma/          local vector index (generated)
tests/                labeled-query eval
streamlit_app.py      Streamlit UI (to be built)
```

## Specs

Read [docs/00_README.md](docs/00_README.md), then `01` → `10`.

## Branches

| Branch | Owner |
|---|---|
| `builder-one` | Builder 1 — Streamlit UI + `handle_turn` contract |
| (your branch) | Builder 2 / 3 / 4 — mock bank, NLU, RAG |

Merge into `main` when each track is ready. UI already calls `app.orchestrator.handle_turn` with the contract in `docs/05_API_CONTRACT.md`. Builder 3 replaces the fixture by setting `USE_FIXTURE = False` and implementing `real_handle_turn`.

## Run (Builder 1 UI)

```text
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Full stack (after other builders land): also install `google-genai chromadb sentence-transformers datasets pytest`, copy `.env.example` to `.env`, run `python -m app.rag_ingest`.
