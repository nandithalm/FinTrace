# Judge Questions And Answers — FinTrace

Short answers. Do not improvise new product claims.

## Q1. What did you build?

FinTrace, a Streamlit prototype for banking queries. Customers ask in English, Hindi, or Kannada. We detect intent and entities, call mock banking APIs **or** retrieve policy chunks (RAG), mask sensitive fields, and return a grounded answer with a visible trace.

## Q2. What problem does it solve?

It reduces wait time for the high-volume questions in the problem statement: balance, transactions, loan eligibility, and interest rates — plus policy FAQs (loan documents, KYC, UPI, NEFT/IMPS) and an explanation of *why* a balance moved.

## Q3. How did you use AI / GenAI / ML?

Gemini Flash does NLU (intent, entities, language, follow-up) and reply wording. A Python insight engine does all arithmetic. **Policy questions go through RAG:** embed → Chroma → retrieve titled chunks → LLM. Corpus is curated bank-policy markdown plus a cached subset of Hugging Face `sidddd625/adaption-banking-and-digital-payments` (`answer_guidance` + `source`). If Gemini is unavailable, a keyword fallback keeps the same contract.

## Q4. Is it connected to a real bank?

No. The problem statement allows mock APIs and synthetic data. Routes are named so a core-banking adapter could replace JSON later.

## Q5. How do you protect privacy?

Account numbers are stored and shown masked (`XXXXXX4821`). We refuse PIN, OTP, password, transfers, and other-customer access. Account-specific answers require `consent_enabled`. The UI is labeled as simulated data.

## Q6. How is this different from a FAQ bot?

FAQs cannot use the customer’s ledger or keep drill-down context. FinTrace calls balance, transaction, rate, and insight APIs, remembers “only food”, **retrieves policy instead of memorizing it**, and shows which API or chunk grounded the answer.

## Q7. What is your personal touch?

Four things judges can see: (1) anti-hallucination trace, (2) policy RAG with citations, (3) “why is my balance lower?” from month-over-month spend, (4) English / Hindi / Kannada.

## Q8. What are the limitations?

Two-hour MVP. Mock data, no real authentication, no payments, no production NLU evaluation. Loan output is a simulated rule, not an offer. RAG uses a **small** index (curated KB + ≤150 HF rows), not the full 2,631-row dataset at demo time. Unusual-spend and what-if are stretch and may be off.

## Q9. How would you scale it?

Replace mock GETs with authenticated CBS/statement APIs, keep Chroma until a bank document store exists, move session off Streamlit `session_state` to Redis, keep the same `facts_json` / chunk contract in front of any LLM, add audit logging, and route `human_handoff` to the contact center.

## Q10. How did you test it?

A 24-query labeled set spanning EN/HI/KN, including follow-ups, four policy-RAG items, unsafe prompts, and fallback. Targets: ≥80% acceptable answers, 100% privacy pass, under 15 seconds (typically under 2 seconds on mock data; RAG a few seconds more). Cite the table from the run, not this sentence.

## Q11. What is the expected response time?

Problem statement: sub-15 seconds. Prototype path is local JSON, optional Chroma retrieve, plus two Gemini calls, usually well under that. If wording exceeds the budget, we fall back to templates.

## Q12. Can it handle diverse customer queries?

Yes for the locked intents, including Hindi and Kannada wording and short follow-ups. Out-of-scope actions are refused. Unknown text gets a clarifying fallback, not a guessed balance.

## Q13. Does it make financial decisions?

No. Eligibility is a transparent rule on simulated credit score and income, with an explicit disclaimer. We do not disburse or commit the bank.

## Q14. Why mock services?

Safety, feasibility in two hours, and alignment with the problem statement. Mock services let us show the full grounded path without real PII.

## Q15. Why Gemini and not only rules?

Rules cannot cover Hindi/Kannada paraphrase in two hours. Gemini covers NLU and fluent wording; rules remain the safety net so the demo cannot go dark.

## Q16. How do you stop hallucination?

Numbers are calculated in Python and passed as `facts`. Policy sentences come from retrieved chunks. The wording prompt forbids new amounts and new clauses. The UI displays `facts` or chunk titles and a `grounded` flag. Empty facts produce “I don’t have enough information…”.

## Q17. Why these languages?

The team must serve regional-language customers, not English-only FAQs. English, Hindi, and Kannada cover the demo without exploding i18n scope.

## Q18. What would you build next?

Real auth, real APIs, stronger evaluation dashboard, human handoff, then stretch insights (unusual spend, affordability) on production-quality synthetic data.

## Q19. How did the team split work?

UI (Streamlit), mock bank, chat/NLU orchestration, RAG + insights/eval, plus a dedicated presenter. Specs were written before code (this pack). See [08_BUILD_PLAN_2_HOURS.md](08_BUILD_PLAN_2_HOURS.md).

## Q20. Did you train a model?

No. Fine-tuning is out of scope. We do **not** train on the Hugging Face set. We use it as a retrieval corpus (`answer_guidance` field) plus hosted Gemini with JSON schemas and a deterministic engine.
