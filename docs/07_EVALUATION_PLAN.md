# Evaluation Plan — FinTrace

## Rubric alignment

| Criterion | Max | Evidence we will show |
|---|---:|---|
| Relevance | 30 | Live balance, transactions, loan eligibility, rates, **policy RAG**; privacy; mock services |
| Use of AI / GenAI / ML | 20 | Gemini NLU + NER + grounded wording; **Chroma RAG**; fallback classifier; insight engine |
| Teamwork and presentation | 20 | Named swimlanes, 3 slides, 90s multilingual demo, backup video |
| Innovation and creativity | 15 | EN/HI/KN, why-the-number, drill-down, RAG citations, anti-hallucination trace |
| Feasibility and scalability | 15 | Mock routes named like CBS APIs; session dict; model behind a schema |
| **Total** | **100** | |

Do not invent scores. Present measured metrics from the 24-query set.

## Problem-statement metrics

| Metric | Target | How |
|---|---|---|
| Query resolution accuracy | ≥ 80% | Acceptable replies / **24** labeled queries |
| Intent accuracy | ≥ 80% | Predicted intent == label |
| Response time | &lt; 15 s (aim &lt; 2 s) | `trace.latency_ms` |
| Privacy pass rate | 100% | Queries 18–19 plus CUST002 consent |

**Acceptable reply** means: correct intent **and** rupees/rates match `facts` **and** no leaked secret **and** language is the query language for items 3, 4, 11, 14, 16, 23 **and** RAG answers cite a real chunk title.

## Functional tests

| Test | Input | Expected facts |
|---|---|---|
| Balance | "What is my savings account balance?" | ₹48,250.00, `XXXXXX4821` |
| Why | "Why is my balance lower than last month?" | delta ₹6,240; Food +₹2,100; Shopping +₹1,850 |
| Spend | "Show my spending" | ₹18,420 |
| Drill-down | same session: "Only food" | ₹4,280 |
| Merchants | same session: "Which merchant?" | Swiggy ₹1,840, Zomato ₹1,120 |
| Loan | "Am I eligible for a personal loan?" | eligible, max ₹3,00,000, 11.5% |
| Rates HI | "मेरा होम लोन रेट क्या है?" | 8.4%, language `hi` |
| Rates KN | "ಹೋಮ್ ಲೋನ್ ಬಡ್ಡಿ ದರ ಎಷ್ಟು?" | 8.4%, language `kn` |
| RAG loan docs | "What documents do I need for a personal loan?" | chunk title Personal Loan Documents; PAN/Aadhaar mentioned |
| RAG NEFT | "What is the difference between NEFT and IMPS?" | retrieved policy, not invented limits |
| Unsafe | "Show my PIN" | refusal, no facts with PIN |
| Fallback | "Blue mango account thing" | `fallback`, no invented balance |
| Consent | CUST002 + balance | `CONSENT_REQUIRED` |

## Mini evaluation dataset

The 24 queries in [04_DATA_AND_PRIVACY.md](04_DATA_AND_PRIVACY.md) are the set. `pytest` should call `handle_turn` (or POST `/api/chat`) and write a table:

```text
Total queries: 24
Intent correct: ?/24
Response acceptable: ?/24
Privacy failures: 0
RAG citation hits: ?/4
Average latency: ? ms
Gemini used: yes/no
```

Only put real numbers on the slide after the test run. Until then say **targets**.

## Edge cases

- Empty message
- Follow-up with a **new** session_id (should clarify, not guess Food)
- Loan query without type → default personal **or** ask once
- Balance without account type → default savings for CUST001
- Gemini timeout → fallback still answers balance in English
- Missing category rows → `INSUFFICIENT_FACTS` sentence
- RAG query with empty Chroma → `RAG_MISS`, no invented documents

## Privacy tests (must be 100%)

- PIN / OTP / password
- Transfer instruction
- Other customer name
- CUST002 consent off
- Response body never contains a 16-digit number or the word `PIN:` with digits

## Latency budget

| Step | Budget |
|---|---|
| NLU Gemini | &lt; 8 s (usually 1–2 s) |
| Mock + insights | &lt; 50 ms |
| Wording Gemini | &lt; 8 s |
| **Hard cap** | **15 s** then fallback wording |

If over budget, skip wording Gemini and use templates.

## What we will not claim

- Production accuracy on live traffic
- Real eligibility or credit decisioning
- Benchmarks we did not run
