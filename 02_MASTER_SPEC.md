# Master Specification — FinTrace

## Product name

**FinTrace** (trace a question back to transactions **or** policy). Locked. Do not rebrand during the build.

Tagline for slides: *Traces a question back to the underlying facts.*

## Product summary

FinTrace is a lightweight banking customer query assistant with a Streamlit UI. A customer types in English, Hindi, or Kannada. The system classifies intent and entities with Gemini, then either fetches mock banking data, runs deterministic insights in Python, **or** retrieves policy passages from a vector store, and generates a short reply that may only use those facts.

It demonstrates:

- Natural language understanding and entity recognition
- Mock banking API integration
- **Banking FAQ + policy RAG** (Hugging Face + curated KB)
- Privacy masking and consent
- Conversational context (drill-down)
- “Why this number” explanations
- Anti-hallucination / grounding trace
- Sub-15-second responses

## Non-negotiable demo requirements

1. User enters a query in the chat UI.
2. Trace shows detected intent, entities, language, API, row count.
3. Answer uses mock data; rupees match the API `facts` payload.
4. Account numbers are masked (`XXXXXX4821`).
5. Latency is displayed and under 15 seconds.
6. At least one Hindi **or** Kannada successful turn.
7. At least one graceful fallback and one unsafe refusal.
8. Banner states the data is simulated.
9. At least one **policy RAG** turn with visible chunk titles (e.g. Personal Loan Documents).

## Screen layout

```text
+------------------------------------------------------------------+
| FinTrace (Streamlit)         Prototype · simulated data          |
| EN | हिन्दी | ಕನ್ನड                                    380 ms   |
+----------------------------------------+-------------------------+
| Chat                                   | Sidebar: AI Understanding|
| User: What documents for a personal    | Intent: policy_rag      |
|      loan?                             | Topic: loan_documents   |
| Bot: PAN, Aadhaar, salary slips...     | ↓                       |
|      Sources: Personal Loan Documents  | 📚 retrievePolicyChunks |
|                                        | 3 chunks retrieved      |
|                                        | ↓                       |
| [ Ask about your account...        ]   | ✅ Grounded in KB       |
+----------------------------------------+-------------------------+
```

UI chrome uses Streamlit widgets and a small i18n dict in `app/i18n.py`. Do not hard-code English in button labels.

## Supported intents

| Intent | Example | Data source |
|---|---|---|
| `balance_check` | "What is my savings account balance?" | `GET .../balance` |
| `transaction_history` | "Show my last 5 transactions" | `GET .../transactions` |
| `loan_eligibility` | "Am I eligible for a personal loan?" | `GET .../loans/eligibility` |
| `interest_rate_query` | "मेरा होम लोन रेट क्या है?" | `GET .../products/rates` |
| `why_balance_change` | "Why is my balance lower than last month?" | `GET .../insights/why-balance` |
| `spend_drilldown` | "Only food" / "Which merchant?" | `GET .../insights/spend` + session |
| `policy_rag` | "What documents do I need for a personal loan?" | `retrievePolicyChunks` |
| `human_handoff` | "I want to speak to an agent" | No money API |
| `unsafe_refusal` | "Show my PIN" / "Transfer ₹10,000" | Safety layer |
| `fallback` | Unclear query | No money API |

Stretch intents (do not implement before must-haves): `unusual_spend`, `affordability_what_if`.

## Session rules (conversational drill-down)

Store per `session_id`:

```text
last_intent
last_entities        # account_type, category, period, loan_type, limit
last_language
last_facts           # last API facts blob
```

Merge rules:

- If the new message is a fragment (`only food`, `which merchant`, `savings`, `last 5`) and `last_intent` is `transaction_history`, `spend_drilldown`, or `why_balance_change`, treat as `spend_drilldown` and union entities.
- Do not carry loan entities into a balance question.
- Reset session on `unsafe_refusal` after responding.
- Default customer for the demo: `CUST001` (consent on). Optional switch to `CUST002` (consent off) for a 10-second safety beat.

## Response principles

- Concise, polite, no invented rupees
- Always mention simulated/demo data once per session (banner covers most of this)
- Ask a clarifying question when account type or loan type is missing **and** cannot be defaulted
- Default account type to `savings` for CUST001 when unspecified
- Escalate unsafe actions; never execute them
- Reply in the query language when known

## Example dialogues (locked numbers)

Locked demo customer: **Aarav Sharma / CUST001**. Savings **XXXXXX4821**, available **₹48,250.00**.

### 1. Balance

User: `What is my savings account balance?`

Assistant: `Your savings account ending in 4821 has an available balance of ₹48,250.00.`

Trace: intent `balance_check`, entity `account_type=savings`, API `getAccountBalance`, rows `1`, grounded `true`, language `en`.

### 2. Why this number

User: `Why is my balance lower than last month?`

Assistant: `Your spending increased by ₹6,240 compared with last month, mainly from Food (+₹2,100) and Shopping (+₹1,850). Income was unchanged. This uses simulated transactions.`

Trace: intent `why_balance_change`, API `getWhyBalance`, facts include `spend_delta=6240`.

### 3. Drill-down

User: `Show my spending.`

Assistant: `You spent ₹18,420 this month (simulated).`

User: `Only food.`

Assistant: `Food spending this month is ₹4,280.`

User: `Which merchant?`

Assistant: `Swiggy ₹1,840, Zomato ₹1,120, and other food merchants ₹1,320.`

The last two turns must **not** require the user to repeat “spending” or “this month”.

### 4. Hindi rates

User: `मेरा होम लोन रेट क्या है?`

Assistant (hi): `इस डेमो डेटा में होम लोन की ब्याज दर 8.4% वार्षिक से शुरू होती है।`

Trace: intent `interest_rate_query`, entity `loan_type=home`, API `getProductRates`, language `hi`.

### 5. Loan eligibility

User: `Am I eligible for a personal loan?`

Assistant: `Based on this simulated profile, you may be eligible for a personal loan up to ₹3,00,000 at 11.5% onwards. Final approval needs bank verification. This is not a real offer.`

### 6. Policy RAG (must-have demo)

User: `What documents do I need for a personal loan?`

Assistant: `For a personal loan in this prototype policy pack you typically need: PAN, Aadhaar, last 3 months salary slips, last 6 months bank statements, and a passport-size photo. Final bank lists can differ. Sources: Personal Loan Documents.`

Trace: intent `policy_rag`, API `retrievePolicyChunks`, top chunk title `Personal Loan Documents`, `row_count` ≥ 1, `grounded` true.

### 7. Unsafe

User: `Show my PIN.` / `Transfer ₹10,000 to Rahul now.`

Assistant: `I cannot display PINs, OTPs, or passwords, and I cannot transfer money in this prototype. Use official bank channels for those actions.`

### 8. Missing facts (anti-hallucination)

If the insight API returns no rows **or** RAG similarity is below threshold:

Assistant: `I don't have enough information to answer that. Would you like me to check your simulated transactions or search bank policy?`

### 9. Consent off (CUST002)

Assistant: `I cannot show account-specific information because data-access consent is disabled on this profile.`

## i18n rules

| Surface | Implementation |
|---|---|
| Buttons, placeholders, trace labels | Streamlit i18n dict |
| Banking facts | Mock service JSON (language-agnostic numbers) |
| Policy answers | Retrieved chunk text, worded by Gemini |
| Customer-facing sentences | Gemini wording call **or** canned templates (balance, rates, refuse, fallback, RAG-miss) in EN/HI/KN |

Do not ship a full translation memory. Four templates are enough if Gemini is down.

## Important caveat

This is a prototype using mock data. It must never claim to access real customer data or perform real banking transactions.
