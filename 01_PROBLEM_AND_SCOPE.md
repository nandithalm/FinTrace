# Problem And Scope

TCS build loop move **01 — Decompose** (10 minutes, no code): users, jobs, data, screens.

## Problem statement (verbatim intent)

Banking customers wait too long for answers to balance, transaction history, loan eligibility, and interest-rate questions. Call centers and scripted FAQs cannot understand varied wording or context. The need is a scalable, AI-powered conversational agent that uses mock banking APIs, protects privacy, and responds in real time.

## One-sentence product

Build **FinTrace**: a Streamlit chatbot that understands English, Hindi, and Kannada banking questions, fetches simulated account data **or** retrieved policy chunks, and answers only with grounded facts — including *why* a balance moved and *which document* a FAQ came from.

## Who it helps

| User | Job to be done |
|---|---|
| Retail banking customer | Get a fast, private answer without waiting for an agent |
| Bank support / operations | Deflect repetitive balance, statement, rate, and eligibility queries |
| Hackathon judges | See a working, relevant, GenAI prototype aligned to the rubric |

## User jobs (in scope)

- Check savings or current **balance**
- View **transaction** history and spending
- Ask **why** this month’s balance is lower than last month
- Drill down (“only food”, “which merchant?”) without repeating context
- Ask **loan eligibility** (personal / home)
- Ask **interest rates** (savings, FD, personal loan, home loan)
- Ask **policy / FAQ** questions (UPI, NEFT/RTGS/IMPS, KYC, cards, account opening, loan documents, disputes)
- Be refused safely on PIN, OTP, transfer, or another customer’s data
- Hand off to a human when the query is a complaint or explicit request

## Data (decompose)

| Data | Form | Notes |
|---|---|---|
| Customer query logs | Text, intent-labeled | Mixed EN/HI/KN for validation |
| Product catalogue | JSON | Loan and deposit rates |
| Customer profiles | JSON | Consent flags, synthetic credit/income |
| Accounts + transactions | JSON | Masked numbers, categories, merchants |
| Policy knowledge base | Markdown + HF chunks | UPI, transfers, KYC, cards, loans, FD, disputes |
| Vector index | Chroma | Embeddings of curated + Hugging Face passages |
| Mock services | Python (HTTP-shaped) | Balance, transactions, eligibility, rates, insights, retrieve |

All data is **synthetic or anonymized**. See [04_DATA_AND_PRIVACY.md](04_DATA_AND_PRIVACY.md).

## Screens (decompose)

One **Streamlit** page only:

1. Prototype banner
2. Language toggle: English / हिन्दी / ಕನ್ನಡ
3. Chat transcript + composer (`st.chat_message` / `st.chat_input`)
4. Optional suggested chips (balance, why, rates, loan documents)
5. Sidebar **grounding trace** (API path **or** RAG retrieve)
6. Latency display
7. Stretch (hidden until ready): Analyze transactions

No static HTML, no CLI, no second app.

## Languages

| Code | UI chrome | Customer reply |
|---|---|---|
| `en` | Static i18n JSON | Gemini grounded wording, or English templates |
| `hi` | Static i18n JSON | Same, Hindi |
| `kn` | Static i18n JSON | Same, Kannada |

Language comes from the toggle **or** detected query script. Reply language must match the query when detection is confident.

## MVP goals (2 hours)

- Running Streamlit app
- At least the four problem-statement query types plus why-balance, drill-down, and **policy RAG**
- Mock APIs visible in the trace
- Masked account numbers
- Consent check
- Response time shown and under 15 seconds
- Labeled eval set of 20 queries targeting ≥80% acceptable answers
- One unsafe query refused
- One low-confidence fallback

## Out of scope for 2 hours

- Real core-banking or payment rails
- Real OTP / 2FA login
- Fund transfers, bill pay, card block execution
- Voice bot, mobile app, admin dashboard
- Fine-tuned or trained models
- Unusual-spend and what-if **unless** must-haves already work (stretch)

## Success criteria (demo)

The demo wins on relevance if judges see:

1. Natural-language balance, transactions, loan, and rates
2. A Hindi or Kannada turn that still calls a mock API
3. “Why is my balance lower?” with category deltas from data
4. A follow-up that keeps session context
5. “What documents do I need for a personal loan?” with RAG citations
6. A trace proving the reply is grounded (API **or** retrieved chunks)
7. A privacy refusal
8. Architecture explained in three slides

## Non-goals we will say out loud

This is not a production bank channel. It does not move money and does not access real customers.