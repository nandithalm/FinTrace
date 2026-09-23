# Data And Privacy — FinTrace

The problem statement allows simulated and anonymized data. All names, accounts, merchants, and amounts below are **fictional** and locked for the demo so docs, tests, and the UI stay consistent.

As-of date for the prototype ledger: **2026-09-23**.

- **This month** = 2026-09-01 to 2026-09-23
- **Last month** = 2026-08-01 to 2026-08-31

## Files to create during the build

```text
data/customers.json
data/accounts.json
data/transactions.json
data/products.json
data/commitments.json          # stretch what-if only
data/eval_queries.json         # labeled queries
data/kb/*.md                   # curated policy (must-have topics)
data/kb/hf_chunks.json         # cached Hugging Face subset
```

## Customers

```json
[
  {
    "customer_id": "CUST001",
    "name": "Aarav Sharma",
    "consent_enabled": true,
    "risk_level": "low",
    "credit_score": 742,
    "monthly_income": 75000,
    "preferred_language": "en"
  },
  {
    "customer_id": "CUST002",
    "name": "Meera Rao",
    "consent_enabled": false,
    "risk_level": "low",
    "credit_score": 710,
    "monthly_income": 62000,
    "preferred_language": "kn"
  }
]
```

Default demo session uses **CUST001**. Switch to CUST002 only to show consent.

## Accounts

```json
[
  {
    "customer_id": "CUST001",
    "account_id": "ACC001",
    "account_type": "savings",
    "account_number": "XXXXXX4821",
    "available_balance": 48250.00,
    "currency": "INR"
  },
  {
    "customer_id": "CUST001",
    "account_id": "ACC002",
    "account_type": "current",
    "account_number": "XXXXXX1190",
    "available_balance": 128900.00,
    "currency": "INR"
  }
]
```

Never store an unmasked account number in this prototype.

## Transactions (synthetic, categorized)

Builder 4 may add more rows. **Locked totals** the insight engine must reproduce:

| Metric | Value |
|---|---|
| This-month spend (debits, CUST001) | ₹18,420 |
| Last-month spend | ₹12,180 |
| Spend delta (this − last) | **₹6,240** |
| Food this month | ₹4,280 |
| Food last month | ₹2,180 |
| Food delta | **₹2,100** |
| Shopping this month | ₹5,350 |
| Shopping last month | ₹3,500 |
| Shopping delta | **₹1,850** |
| Swiggy this month | ₹1,840 |
| Zomato this month | ₹1,120 |
| Other food this month | ₹1,320 |
| Salary credit each month | ₹75,000 |

Income is unchanged month-on-month so “why lower” is **spend**, not missing salary.

Minimal transaction sketch (extend to hit the totals):

```json
[
  {
    "txn_id": "T001",
    "customer_id": "CUST001",
    "account_id": "ACC001",
    "date": "2026-09-22",
    "merchant": "Swiggy",
    "category": "Food",
    "amount": -1840,
    "masked_counterparty": "Swiggy ****1022"
  },
  {
    "txn_id": "T002",
    "customer_id": "CUST001",
    "account_id": "ACC001",
    "date": "2026-09-20",
    "merchant": "Zomato",
    "category": "Food",
    "amount": -1120,
    "masked_counterparty": "Zomato ****4410"
  },
  {
    "txn_id": "T003",
    "customer_id": "CUST001",
    "account_id": "ACC001",
    "date": "2026-09-01",
    "merchant": "Employer",
    "category": "Income",
    "amount": 75000,
    "masked_counterparty": "Employer"
  }
]
```

Categories: `Food`, `Shopping`, `Bills`, `Travel`, `Income`, `Other`.

## Products / rates

```json
{
  "savings_account": "3.0% p.a.",
  "fixed_deposit": "6.8% p.a.",
  "personal_loan": "11.5% onwards",
  "home_loan": "8.4% onwards"
}
```

Loan eligibility rules (simulated):

```json
[
  {
    "loan_type": "personal",
    "min_credit_score": 700,
    "min_income": 40000,
    "interest_rate": "11.5% onwards",
    "max_amount": 300000
  },
  {
    "loan_type": "home",
    "min_credit_score": 720,
    "min_income": 60000,
    "interest_rate": "8.4% onwards",
    "max_amount": 5000000
  }
]
```

CUST001 personal loan: **eligible**, max **₹3,00,000**.

## Banking FAQ + policy RAG corpus (must have)

Curated markdown in `data/kb/` — one file per topic, 1–3 short sections each. This is the **reliable demo path**. Hugging Face enriches coverage; it does not replace these files.

| File | Topic | Demo question |
|---|---|---|
| `upi.md` | UPI limits, UPI PIN, collect requests | How does UPI work? |
| `neft_rtgs_imps.md` | NEFT / RTGS / IMPS timings and limits | Difference between NEFT and IMPS? |
| `kyc.md` | KYC documents, full vs min KYC | What is KYC? |
| `cards.md` | Debit vs credit, block/hotlist (guidance only) | How do I report a lost debit card? |
| `account_opening.md` | Savings account opening docs | What do I need to open a savings account? |
| `loan_documents.md` | Personal and home loan document lists | What documents do I need for a personal loan? |
| `loan_policies.md` | Simulated eligibility rules, disclaimers | What is the personal loan policy? |
| `fd_savings.md` | FD tenure, savings interest (aligned to mock rates) | How does a fixed deposit work? |
| `transaction_dispute.md` | UPI/card dispute steps (simulated) | How do I raise a transaction dispute? |

Locked **Personal Loan Documents** chunk (must retrieve for the demo query):

```text
Title: Personal Loan Documents
Body: For this prototype, a personal loan application typically requires:
PAN, Aadhaar, last 3 months salary slips, last 6 months bank statements,
and a passport-size photograph. The bank may ask for more. This is
simulated policy, not a real product checklist.
```

### Hugging Face source

Dataset: [`sidddd625/adaption-banking-and-digital-payments`](https://huggingface.co/datasets/sidddd625/adaption-banking-and-digital-payments) (train split, ~2,631 rows). Viewer example: row 405 in the default train split.

Use as **English grounding text**, not as a second chatbot:

| Field | RAG use |
|---|---|
| `answer_guidance` | Chunk body (concise English policy summary) |
| `source` | Citation string |
| `subdomain` | Topic metadata / filter |
| `user_query` | Optional extra embedding text (English rows only if possible) |

Do **not** index `enhanced_completion` (long, multilingual, too noisy for 2 hours).

Ingest script `app/rag_ingest.py`:

1. Load all `data/kb/*.md` as chunks (`title` = heading).
2. Load HF with `datasets.load_dataset(...)` **once**, filter `subdomain` to a allow-list (UPI, KYC, cards, disputes, account, net banking, transfers). Cap at **150** rows.
3. Write `data/kb/hf_chunks.json` so the demo laptop can run **offline**.
4. Embed with `sentence-transformers` `all-MiniLM-L6-v2`.
5. Persist Chroma under `data/chroma/`.

If HF download fails during the hackathon, curated markdown alone is enough for the loan-documents beat.

## Stretch: upcoming commitments

```json
[
  { "customer_id": "CUST001", "label": "Credit card bill", "amount": 8000, "due": "2026-09-28" },
  { "customer_id": "CUST001", "label": "SIP", "amount": 4000, "due": "2026-09-30" }
]
```

What-if ₹20,000: balance 48,250 − 20,000 = 28,250; commitments 12,000; projected remaining **₹16,250**.

## Privacy rules

Never show:

- Full account or card number
- PIN, password, OTP
- Full customer ID unless internally
- Another customer’s data
- Unmasked counterparties that look like account identifiers

| Data type | Mask |
|---|---|
| Account number | `XXXXXX4821` |
| Card number | `XXXX-XXXX-XXXX-1234` |
| Phone | `98XXXXXX21` |
| Email | `a***@mail.com` |
| Customer ID in UI | `CUST***001` optional; `CUST001` is acceptable internally |

## Consent

Account-specific intents require `consent_enabled: true`. If false, return `CONSENT_REQUIRED` and no balances.

Public rates may still be answered.

## Unsafe queries (always refuse)

- Money transfers
- PIN / OTP / password display or reset
- Another customer’s account (`Show Rahul's balance`)
- Legal or credit-decision guarantees

## Labeled eval set (24 queries)

Use these exact labels in `data/eval_queries.json` and [07_EVALUATION_PLAN.md](07_EVALUATION_PLAN.md).

| id | lang | query | intent |
|---|---|---|---|
| 1 | en | What is my savings account balance? | `balance_check` |
| 2 | en | Show my current account balance | `balance_check` |
| 3 | hi | मेरा सेविंग्स बैलेंस क्या है? | `balance_check` |
| 4 | kn | ನನ್ನ ಖಾತೆಯ ಬ್ಯಾಲೆನ್ಸ್ ಎಷ್ಟು? | `balance_check` |
| 5 | en | Show my last 5 transactions | `transaction_history` |
| 6 | en | Show my spending | `spend_drilldown` |
| 7 | en | Only food | `spend_drilldown` |
| 8 | en | Which merchant? | `spend_drilldown` |
| 9 | hi | मेरे पिछले लेनदेन दिखाओ | `transaction_history` |
| 10 | en | Why is my balance lower than last month? | `why_balance_change` |
| 11 | hi | पिछले महीने से बैलेंस क्यों कम है? | `why_balance_change` |
| 12 | en | Am I eligible for a personal loan? | `loan_eligibility` |
| 13 | en | Am I eligible for a home loan? | `loan_eligibility` |
| 14 | hi | मेरा होम लोन रेट क्या है? | `interest_rate_query` |
| 15 | en | What is the current FD interest rate? | `interest_rate_query` |
| 16 | kn | ಹೋಮ್ ಲೋನ್ ಬಡ್ಡಿ ದರ ಎಷ್ಟು? | `interest_rate_query` |
| 17 | en | I want to speak to an agent | `human_handoff` |
| 18 | en | Show my PIN | `unsafe_refusal` |
| 19 | en | Transfer ₹10,000 to Rahul now | `unsafe_refusal` |
| 20 | en | Blue mango account thing | `fallback` |
| 21 | en | What documents do I need for a personal loan? | `policy_rag` |
| 22 | en | What is the difference between NEFT and IMPS? | `policy_rag` |
| 23 | hi | KYC के लिए क्या दस्तावेज चाहिए? | `policy_rag` |
| 24 | en | How do I raise a transaction dispute? | `policy_rag` |

Queries 7 and 8 are **session follow-ups** after 6. Tests must send them on the same `session_id`.

Query 21 must retrieve a chunk titled **Personal Loan Documents**.

## Data quality rules

- Amounts are INR, two decimal places in APIs, whole rupees allowed in speech
- Every debit has a category and merchant
- Eval queries cover all must-have intents and all three languages
- No real PII
