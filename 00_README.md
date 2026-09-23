# FinTrace — Spec Pack

FinTrace is a 2-hour hackathon prototype: an AI-powered banking customer query assistant for **TCS Technology Day**.

It understands **English, Hindi, and Kannada**, calls **mock banking APIs**, retrieves **banking FAQ and policy** from a small vector store, and answers only with numbers and policy text that exist in simulated data. It then explains *why* a number moved, and traces a policy answer back to retrieved chunks.

This folder is the only planning source of truth. Spec-driven order: problem → spec → architecture → data → API → AI → eval → build → demo → Q&A.

**Prototype · simulated data · not a real bank.**

## Product promise

FinTrace lets a customer ask common banking questions in natural language, fetches safe mock account data **or** retrieved policy passages, and returns a context-aware, privacy-masked answer with a visible grounding trace.

## Locked decisions

| Decision | Value |
|---|---|
| Product name | **FinTrace** |
| Coding window | 2 hours |
| GenAI | Gemini Flash (`google-genai`) |
| Languages | English (`en`), Hindi (`hi`), Kannada (`kn`) |
| Team | 4 builders + 1 presenter |
| UI | **Streamlit** chat + sidebar trace (`streamlit_app.py`) |
| Services | Python modules (`app/`); FastAPI mock routes optional if time remains |
| Data | Local synthetic JSON (`data/`) + policy KB (`data/kb/`) |
| RAG corpus | Curated policy markdown **plus** Hugging Face `sidddd625/adaption-banking-and-digital-payments` |
| Vector store | Chroma (local persist) + `sentence-transformers` MiniLM embeddings |
| Source of truth for rupees | Deterministic Python engine + mock APIs, never the LLM |
| Source of truth for policy | Retrieved KB chunks only, never the LLM’s memory |

## Official rubric (source of truth)

| Criterion | Max | How FinTrace scores |
|---|---:|---|
| Relevance | 30 | Chat for balance, transactions, loan eligibility, rates, **and** policy FAQs |
| Use of AI / GenAI / ML | 20 | Gemini NLU + NER + grounded reply; **FAQ/policy RAG**; deterministic insights; trace |
| Teamwork and presentation | 20 | 4 parallel tracks, 3-slide deck, 90-second multilingual demo |
| Innovation and creativity | 15 | EN/HI/KN, “why this number”, drill-down, RAG citations, anti-hallucination panel |
| Feasibility and scalability | 15 | Mock APIs isomorphic to CBS; Chroma → enterprise vector DB; Gemini swappable |
| **Total** | **100** | |

Success from the problem statement: **≥80% query resolution** on the labeled set, **sub-15-second** response (target **&lt;2s** local path, RAG typically 2–6s).

## Documentation files

| File | Purpose |
|---|---|
| [01_PROBLEM_AND_SCOPE.md](01_PROBLEM_AND_SCOPE.md) | Decompose: users, jobs, data, screens, in/out of scope |
| [02_MASTER_SPEC.md](02_MASTER_SPEC.md) | Product spec: intents, session, i18n, dialogues, RAG |
| [03_ARCHITECTURE_DESIGN.md](03_ARCHITECTURE_DESIGN.md) | Grounded pipeline, RAG, fallback, scale-up map |
| [04_DATA_AND_PRIVACY.md](04_DATA_AND_PRIVACY.md) | Synthetic ledger, policy KB, HF ingest, labeled queries |
| [05_API_CONTRACT.md](05_API_CONTRACT.md) | Chat turn, mock GETs, insight + retrieve endpoints |
| [06_AI_DESIGN.md](06_AI_DESIGN.md) | Two Gemini calls, RAG prompt, JSON schemas, no-math rule |
| [07_EVALUATION_PLAN.md](07_EVALUATION_PLAN.md) | Rubric tests, 80% / 15s / privacy / RAG citation |
| [08_BUILD_PLAN_2_HOURS.md](08_BUILD_PLAN_2_HOURS.md) | TCS six moves + 4-builder swimlanes |
| [09_DEMO_SCRIPT.md](09_DEMO_SCRIPT.md) | 90-second live demo + 3 slides |
| [10_JUDGE_QA.md](10_JUDGE_QA.md) | Expected questions and locked answers |

## Team

| Role | Work |
|---|---|
| Builder 1 — UI | Streamlit chat, EN/HI/KN toggle, trace sidebar, latency, prototype banner |
| Builder 2 — Mock bank | JSON data, mock service functions, masking, consent, health |
| Builder 3 — Brain | `handle_turn`, Gemini NLU + grounded reply, session, keyword fallback, route to RAG |
| Builder 4 — RAG + insights | Policy KB, HF ingest, Chroma, why-balance, eval queries |
| Member 5 — Presenter | 3 slides, rehearsal, backup demo video, Q&A, timekeeper |

## MVP (must demo)

- Streamlit chat with language toggle and latency
- Intents: `balance_check`, `transaction_history`, `loan_eligibility`, `interest_rate_query`, `why_balance_change`, `spend_drilldown`, **`policy_rag`**, `human_handoff`, `unsafe_refusal`, `fallback`
- **Banking FAQ + Policy RAG** (must have): UPI, NEFT/RTGS/IMPS, KYC, debit/credit cards, account opening, loan documents, loan policies, FD/savings info, transaction dispute
- Session memory so “only food” does not need the user to repeat context
- Privacy masking + consent gate
- Grounding trace: AI Understanding → API **or** vector retrieve → N rows/chunks → grounded
- Banner: *Prototype · simulated data · not a real bank*

## Stretch (only after minute-80 freeze check)

- Unusual spend: “Analyze my transactions”
- What-if: “Can I afford ₹20,000?”
- FastAPI HTTP wrappers around the same mock functions

## Out of scope

Real bank APIs, OTP login, payments, voice, mobile app, model fine-tuning, admin dashboards, ingesting the full 2,631-row HF set at demo time.

## Proposed repo layout (for the build hour)

```text
data/                 synthetic JSON + labeled eval queries
data/kb/              curated policy markdown (must-have topics)
data/kb/hf_chunks.json  cached subset from Hugging Face
data/chroma/          local vector persist
app/                  orchestrator, mock bank, insights, rag, privacy
streamlit_app.py      Streamlit UI
tests/                pytest against the labeled query set
.env                  GEMINI_API_KEY (never commit)
```

## Run commands (target after build)

```text
python -m venv .venv
.venv\Scripts\activate
pip install streamlit google-genai chromadb sentence-transformers datasets pytest python-dotenv
copy .env.example .env
python -m app.rag_ingest
streamlit run streamlit_app.py
```

## Personal touch

The **anti-hallucination trace** plus **policy RAG with citations** plus **“why this number”** plus **EN/HI/KN**. Judges see that rupees come from APIs and policy sentences come from retrieved chunks, not from the model’s memory.
