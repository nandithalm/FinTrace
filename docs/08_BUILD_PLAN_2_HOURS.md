# Two-Hour Build Plan — FinTrace

TCS build loop: **01 Decompose → 02 Specs → 03 Tasks → 04 Code → 05 Add your touch → 06 Test**. Specs are this pack. Do not reopen naming or stack debates during the window.

**No new features after minute 100.** Presenter kills stretch at minute 80 if must-haves are not on screen.

## Strategy

Smallest winning vertical slice first: **English savings balance + Streamlit trace**. Then **policy RAG** (loan documents). Then why-balance, drill-down, Hindi/Kannada rates, privacy. Stretch last.

Stack: **Streamlit** UI + Python `app/` services. Gemini Flash. Chroma + MiniLM. JSON in `data/`. Curated KB in `data/kb/`. Cached Hugging Face subset.

## Roles (minute zero)

| Person | Track | Owns |
|---|---|---|
| Builder 1 | UI | `streamlit_app.py`, chat, sidebar trace, i18n, banner |
| Builder 2 | Mock bank | `data/*.json` (except eval/kb), `app/mock_*.py`, masking, consent |
| Builder 3 | Brain | `app/orchestrator.py`, Gemini, session, safety, templates, route `policy_rag` |
| Builder 4 | RAG + insights | `data/kb/*.md`, `app/rag_ingest.py`, Chroma, why-balance, eval |
| Member 5 | Presenter | 3 slides, [09_DEMO_SCRIPT.md](09_DEMO_SCRIPT.md), backup recording, Q&A, timer |

Builders agree the `handle_turn` JSON from [05_API_CONTRACT.md](05_API_CONTRACT.md) at minute 10.

## Timeline

| Time | Move | What happens |
|---|---|---|
| 0–10 | 01 Decompose | Whole team: walk [01](01_PROBLEM_AND_SCOPE.md). Confirm CUST001 numbers and RAG loan-docs chunk. |
| 10–15 | 03 Tasks | Each builder repeats their first commit out loud. |
| 10–50 | 04 Code (parallel) | B1 Streamlit shell with fake trace. B2 balance + rates + transactions. B3 `handle_turn` stub + fallback. B4 write 9 kb markdown files, ingest Chroma, why-engine totals. |
| 50–80 | Integrate | English balance end-to-end, then **What documents for a personal loan?** with citations. Then why + spend. |
| 80–100 | 05 Touch | EN/HI/KN, Hindi rates, drill-down, RAG titles in sidebar. Stretch only if this is green. |
| 100–110 | 06 Test | 24-query checklist. Privacy. Fix only blockers. |
| 110–120 | Freeze | Rehearse 90s demo. Presenter drives. No feature commits. |

## Must-have task checklist

Builder 1

- [ ] `streamlit run streamlit_app.py`
- [ ] Prototype banner
- [ ] Language toggle `en` / `hi` / `kn`
- [ ] `st.chat_input` + history in `st.session_state`
- [ ] Call `handle_turn` with `session_id`, `customer_id`, `ui_language`
- [ ] Sidebar: intent → API **or** retrieve → row_count → grounded
- [ ] Show `latency_ms` and `facts` / chunk titles
- [ ] Analyze button present but disabled until stretch

Builder 2

- [ ] `customers`, `accounts`, `transactions`, `products` JSON
- [ ] Masked account `XXXXXX4821`, balance `48250.00`
- [ ] Mock functions: balance, transactions, eligibility, rates
- [ ] Consent gate helper

Builder 3

- [ ] Safety regex before NLU
- [ ] Gemini NLU JSON parse including `policy_rag`
- [ ] Keyword fallback (policy keywords included)
- [ ] Session merge for follow-ups
- [ ] Wording call with facts **or** chunks only
- [ ] Templates × 3 languages including RAG-miss
- [ ] Trace fields as specified

Builder 4

- [ ] Nine `data/kb/*.md` files including **Personal Loan Documents**
- [ ] Optional HF cache `hf_chunks.json` (cap 150); curated KB works offline
- [ ] `python -m app.rag_ingest` builds Chroma
- [ ] Transactions that sum to locked totals (18420, 6240, 4280, 1840, 1120)
- [ ] `getWhyBalance` / `getSpendBreakdown`
- [ ] `eval_queries.json` (24 rows)
- [ ] pytest or `python tests/eval_run.py`

Presenter

- [ ] Slide 1 problem, slide 2 demo+architecture (include RAG), slide 3 touch+limits
- [ ] Backup video including the loan-documents RAG beat
- [ ] Call time at 50 / 80 / 100 / 110

## Nice-to-have (after 80, only if must-haves work)

- Unusual spend heuristic + enabled Analyze button
- What-if affordability ₹20,000 → projected ₹16,250
- FastAPI wrappers
- CUST002 toggle for consent
- Live HF download if cache missing

## Explicitly do not build

- Real login / OTP
- Real bank HTTP
- Payments
- React/Next/static HTML (Streamlit is the UI)
- Fine-tuning on the Hugging Face set
- Indexing all 2,631 HF rows at demo time
- Extra product names

## Integration contract (minute 50)

UI sends the chat request JSON from [05](05_API_CONTRACT.md). UI requires: `reply`, `intent`, `facts`, `trace.latency_ms`, `trace.api_called`, `trace.grounded`, `trace.row_count`, `language`.

If B3 is late, B1 uses a fixture dict. If Gemini is late, B3 ships fallback. If HF is late, B4 ships curated markdown only.

## Final 3-slide deck

1. **The problem** — wait times; static FAQs; FinTrace one-liner; EN/HI/KN
2. **What we built** — Streamlit demo; Gemini NLU + mock services + **policy RAG** + Python insights
3. **Our touch** — trace a question to APIs **or** KB chunks; why-the-number; CBS swap next
