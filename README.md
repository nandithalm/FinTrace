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

## Run (after build)

```text
python -m venv .venv
.venv\Scripts\activate
pip install streamlit google-genai chromadb sentence-transformers datasets pytest python-dotenv
copy .env.example .env
python -m app.rag_ingest
streamlit run streamlit_app.py
```

## Builder 4 (this branch)

```text
pip install -r requirements.txt
python -m app.rag_ingest
pytest tests/test_insights.py tests/test_rag.py tests/test_eval.py
python tests/eval_run.py
```

Builder 3 should import `getWhyBalance`, `getSpendBreakdown` from `app.insights` and `retrieve_policy` / `retrievePolicyChunks` from `app.rag`. Do not change those JSON keys.
