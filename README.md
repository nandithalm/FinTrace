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
streamlit_app.py      Streamlit UI
```

## Specs

Read [docs/00_README.md](docs/00_README.md), then `01` → `10`.

## On main now

| Track | Status |
|---|---|
| Builder 1 — Streamlit chat, i18n, trace sidebar | merged |
| Builder 2 — mock JSON, masking, consent | merged |
| Builder 3 — `handle_turn`, NLU, safety, templates | merged |
| Builder 4 — policy KB, Chroma, why-balance, eval | merged |

The UI calls `app.orchestrator.handle_turn` using the contract in [docs/05_API_CONTRACT.md](docs/05_API_CONTRACT.md). Builder 3 routes why-balance and spend to `app.insights` and policy questions to `app.rag`.

## Run

```text
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install google-genai
copy .env.example .env
python -m app.rag_ingest
streamlit run streamlit_app.py
```

Without `python -m app.rag_ingest`, `policy_rag` returns a grounded miss instead of inventing documents.

```text
pytest
python tests/eval_run.py
```
