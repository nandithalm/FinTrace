# Service Contract — FinTrace

Streamlit calls Python functions with these shapes. HTTP paths are the **same contracts** if FastAPI is added later.

Base prefix if HTTP: `/api`

All mock payloads are simulated. JSON field names are stable; do not rename during the build.

## 1. Chat turn

```text
handle_turn(...)  |  optional POST /api/chat
```

### Request

```json
{
  "session_id": "demo-session",
  "customer_id": "CUST001",
  "message": "What is my savings account balance?",
  "ui_language": "en"
}
```

`ui_language` is the toggle (`en` | `hi` | `kn`). Reply `language` may follow the query if NLU detects Hindi or Kannada script.

### Response

```json
{
  "reply": "Your savings account ending in 4821 has an available balance of ₹48,250.00.",
  "intent": "balance_check",
  "entities": {
    "account_type": "savings"
  },
  "language": "en",
  "confidence": 0.92,
  "facts": {
    "account_type": "savings",
    "masked_account_number": "XXXXXX4821",
    "available_balance": 48250.00,
    "currency": "INR"
  },
  "trace": {
    "nlu_source": "gemini",
    "api_called": "getAccountBalance",
    "row_count": 1,
    "privacy_masking": true,
    "grounded": true,
    "data_source": "mock",
    "latency_ms": 420,
    "session_follow_up": false
  }
}
```

`facts` is what the UI may render as numbers. `reply` is wording only.

### Follow-up example

Request: `{ "session_id": "demo-session", "customer_id": "CUST001", "message": "Only food", "ui_language": "en" }`

```json
{
  "reply": "Food spending this month is ₹4,280.",
  "intent": "spend_drilldown",
  "entities": { "category": "Food", "period": "this_month" },
  "language": "en",
  "facts": {
    "period": "this_month",
    "category": "Food",
    "total": 4280,
    "currency": "INR"
  },
  "trace": {
    "nlu_source": "gemini",
    "api_called": "getSpendBreakdown",
    "row_count": 3,
    "grounded": true,
    "session_follow_up": true,
    "latency_ms": 390
  }
}
```

## 2. Health

```text
GET /api/health
```

```json
{ "status": "ok", "product": "FinTrace", "gemini": true }
```

`gemini` is false when the key is missing (fallback mode).

## 3. Mock balance

```text
GET /api/mock/accounts/{customer_id}/balance?account_type=savings
```

```json
{
  "account_type": "savings",
  "masked_account_number": "XXXXXX4821",
  "available_balance": 48250.00,
  "currency": "INR"
}
```

## 4. Mock transactions

```text
GET /api/mock/accounts/{customer_id}/transactions?limit=5&category=&period=
```

```json
{
  "transactions": [
    {
      "date": "2026-09-22",
      "merchant": "Swiggy",
      "category": "Food",
      "amount": -1840,
      "masked_counterparty": "Swiggy ****1022"
    }
  ],
  "row_count": 1
}
```

## 5. Mock loan eligibility

```text
GET /api/mock/loans/eligibility?customer_id=CUST001&loan_type=personal
```

```json
{
  "eligible": true,
  "loan_type": "personal",
  "max_amount": 300000,
  "interest_rate": "11.5% onwards",
  "reason": "Simulated credit score and income meet the rule.",
  "disclaimer": "Not a real loan offer."
}
```

## 6. Mock product rates

```text
GET /api/mock/products/rates
```

```json
{
  "savings_account": "3.0% p.a.",
  "fixed_deposit": "6.8% p.a.",
  "personal_loan": "11.5% onwards",
  "home_loan": "8.4% onwards"
}
```

## 7. Why-balance insight

```text
GET /api/mock/insights/why-balance?customer_id=CUST001
```

```json
{
  "this_month_spend": 18420,
  "last_month_spend": 12180,
  "spend_delta": 6240,
  "income_delta": 0,
  "drivers": [
    { "category": "Food", "delta": 2100 },
    { "category": "Shopping", "delta": 1850 }
  ],
  "currency": "INR"
}
```

Python compares two month buckets. Gemini does not compute `spend_delta`.

## 8. Spend breakdown

```text
GET /api/mock/insights/spend?customer_id=CUST001&period=this_month&category=Food&group_by=merchant
```

Without category:

```json
{
  "period": "this_month",
  "total": 18420,
  "by_category": [
    { "category": "Food", "total": 4280 },
    { "category": "Shopping", "total": 5350 }
  ],
  "currency": "INR",
  "row_count": 2
}
```

With `category=Food` and `group_by=merchant`:

```json
{
  "period": "this_month",
  "category": "Food",
  "total": 4280,
  "by_merchant": [
    { "merchant": "Swiggy", "total": 1840 },
    { "merchant": "Zomato", "total": 1120 },
    { "merchant": "Other", "total": 1320 }
  ],
  "currency": "INR",
  "row_count": 3
}
```

## Stretch (do not build first)

```text
GET /api/mock/insights/unusual?customer_id=CUST001
GET /api/mock/insights/afford?customer_id=CUST001&amount=20000
```

Affordability locked result if implemented: remaining after purchase ₹28,250; commitments ₹12,000; projected ₹16,250.

## 9. Policy retrieve (RAG)

```text
retrieve_policy(query, k=3)  |  optional GET /api/mock/policy/search?q=...
```

```json
{
  "query": "What documents do I need for a personal loan?",
  "chunks": [
    {
      "title": "Personal Loan Documents",
      "source": "data/kb/loan_documents.md",
      "score": 0.81,
      "text": "For this prototype, a personal loan application typically requires: PAN, Aadhaar, last 3 months salary slips, last 6 months bank statements, and a passport-size photograph."
    }
  ],
  "row_count": 1
}
```

Chat `facts` for `policy_rag`:

```json
{
  "topic": "loan_documents",
  "chunk_titles": ["Personal Loan Documents"],
  "chunks": ["...masked/truncated text..."],
  "sources": ["data/kb/loan_documents.md"]
}
```

`trace.api_called` = `retrievePolicyChunks`. `trace.row_count` = number of chunks kept after the similarity floor.

## Error body

```json
{
  "error": {
    "code": "UNSUPPORTED_QUERY",
    "message": "I could not confidently understand this banking request."
  }
}
```

Prefer still returning a bot line with `intent=fallback` so Streamlit always shows a reply. Use 4xx only if HTTP wrappers are added and the customer is missing.

## Error codes

| Code | Meaning |
|---|---|
| `EMPTY_MESSAGE` | No query text |
| `UNSUPPORTED_QUERY` | Intent not detected |
| `CONSENT_REQUIRED` | Account data blocked |
| `UNSAFE_REQUEST` | Forbidden action |
| `MOCK_DATA_NOT_FOUND` | Missing demo data |
| `INSUFFICIENT_FACTS` | Grounded refusal |
| `RAG_MISS` | No chunk above similarity floor |

## CORS / process

Streamlit and `app/` run in one Python process. No CORS needed for the MVP. Optional FastAPI should allow `http://localhost:8501`.
