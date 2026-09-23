# AI Design — FinTrace

## Role of GenAI

Gemini Flash is used for:

1. **NLU:** intent, entities, language, follow-up flag
2. **Wording:** a short customer sentence **from `facts_json` or retrieved chunks only**

Gemini is **not** used for:

- Arithmetic (deltas, totals, eligibility math)
- Inventing transactions, rates, balances, or policy clauses
- Executing banking actions

That split is the AI/GenAI story: NLU + NER + generation + **RAG**, with a deterministic ledger engine and a vector store underneath.

## Two calls per turn (happy path)

| Call | Model | Output |
|---|---|---|
| NLU | Gemini Flash, JSON mime | `intent`, `entities`, `language`, `follow_up`, `confidence` |
| Wording | Gemini Flash, text | `reply` in `language` |

If either call fails, use keyword NLU and canned templates. Trace `nlu_source` is `gemini` or `fallback`.

## NLU JSON schema

```json
{
  "intent": "balance_check",
  "language": "en",
  "follow_up": false,
  "confidence": 0.92,
  "entities": {
    "account_type": "savings",
    "loan_type": null,
    "policy_topic": null,
    "category": null,
    "merchant_focus": false,
    "period": null,
    "transaction_limit": null,
    "amount": null
  }
}
```

Allowed `intent` values: `balance_check`, `transaction_history`, `loan_eligibility`, `interest_rate_query`, `why_balance_change`, `spend_drilldown`, `policy_rag`, `human_handoff`, `unsafe_refusal`, `fallback`.

`language`: `en` | `hi` | `kn`.

`follow_up`: true when the message is a fragment that needs session entities.

## NLU prompt (lock this shape)

```text
You extract banking intent from a customer message.
Return JSON only. Do not answer the customer.

Allowed intents:
balance_check, transaction_history, loan_eligibility, interest_rate_query,
why_balance_change, spend_drilldown, policy_rag, human_handoff, unsafe_refusal, fallback

Entities to fill when present:
account_type: savings | current
loan_type: personal | home
policy_topic: upi | neft_rtgs_imps | kyc | cards | account_opening | loan_documents | loan_policies | fd_savings | transaction_dispute
category: Food | Shopping | Bills | Travel | Income | Other
period: this_month | last_month
transaction_limit: integer
amount: number in INR
merchant_focus: true if they ask which merchant / where

Language: en, hi, or kn (script and wording).
follow_up: true if the message only makes sense with prior context
  (examples: "only food", "which merchant", "savings", "last 5").

Prior session JSON:
{{session}}

User message:
{{message}}
```

## Wording prompt (lock this shape)

```text
You are FinTrace, a prototype banking assistant.
Use only facts_json and retrieved_chunks. Never invent or recalculate amounts, rates, dates, or policy clauses.
If a number is not in facts_json, or a policy sentence is not in retrieved_chunks, say you do not have enough information
and offer to check simulated transactions or search bank policy.
Reply in language={{language}}. Keep it to 1-3 short sentences.
List retrieved chunk titles as Sources when intent is policy_rag.
Mention that data is simulated only if facts_json.contains_disclaimer is true
or this is the first turn.
Never reveal PIN, OTP, full account numbers, or another customer.

User query:
{{message}}

Intent:
{{intent}}

facts_json:
{{facts}}

retrieved_chunks:
{{chunks}}
```

## RAG retrieve (must have)

After NLU returns `policy_rag` (or keyword FAQ):

1. Embed the user query (MiniLM).
2. Query Chroma `k=3`.
3. Drop chunks with score &lt; 0.35.
4. Put remaining `title`, `text`, `source` into `retrieved_chunks`.
5. Wording model may paraphrase **only** that text.
6. Trace: `api_called=retrievePolicyChunks`, `row_count=len(chunks)`, `grounded=true` if at least one chunk kept.

Keyword route to `policy_rag` if the message contains: `document`, `documents`, `KYC`, `UPI`, `NEFT`, `RTGS`, `IMPS`, `dispute`, `account opening`, `fixed deposit`, `debit card`, `credit card`, `दस्तावेज`, `ದಾಖಲೆ`.

Do not send the full Chroma collection into Gemini.

## No-math rule

`why_balance_change` facts already contain `spend_delta` and `drivers[]`. The wording model may **name** those fields. It may not add 2100 + 1850 itself. Unit tests should assert `6240`, `2100`, and `1850` appear from the engine, not from a hand-written LLM string in backend code.

## Keyword fallback (must ship)

```text
unsafe: pin, otp, password, transfer, send money, another customer, rahul's
handoff: agent, human, complaint, escalate
policy: document, kyc, upi, neft, rtgs, imps, dispute, fd, debit card, credit card, दस्तावेज
why: why, lower, last month, कम, ಏಕೆ
rate: interest, rate, fd, होम लोन रेट, ಬಡ್ಡಿ
loan: eligible, eligibility, emi, loan
spend/txn: spend, spending, transaction, merchant, food, shopping, लेनदेन
balance: balance, बैलेंस, ಬ್ಯಾಲೆನ್ಸ್
```

Priority: unsafe → handoff → policy → why → rate → loan → spend → balance → fallback.

If the query is eligibility (`am I eligible`) keep `loan_eligibility`, not `policy_rag`. If it is document/policy, keep `policy_rag`.

Fragments: if message matches `only food|which merchant|सिर्फ फूड` and session last_intent in `{spend_drilldown, transaction_history, why_balance_change}`, force `spend_drilldown` with `follow_up=true`.

## Confidence

| Condition | Score |
|---|---|
| Gemini JSON valid + required entity present | 0.90 |
| Gemini JSON valid, entity defaulted | 0.80 |
| Keyword strong match | 0.75 |
| Keyword weak / fragment without session | 0.55 |
| Unclear | 0.30 → `fallback` |

Route to `fallback` when confidence &lt; 0.50.

## Canned templates (fallback wording)

Keep five templates × three languages:

1. Balance — insert masked last-4 and amount from facts
2. Rates — insert `home_loan` / `fixed_deposit` string from facts
3. Unsafe refusal
4. Fallback clarification listing allowed topics including policy FAQ
5. RAG miss — offer to rephrase the policy question

Hindi and Kannada strings can be short and formal. Builder 3 owns English; Builder 4 can paste HI/KN from this spec if needed:

- Fallback EN: `I could not confidently understand that. You can ask about balance, transactions, why your balance changed, loan eligibility, interest rates, or bank policy such as KYC and loan documents.`
- Fallback HI: `मैं आपका प्रश्न पूरी तरह समझ नहीं पाया। आप बैलेंस, लेनदेन, लोन पात्रता, या ब्याज दर पूछ सकते हैं।`
- Fallback KN: `ನಾನು ವಿನಂತಿಯನ್ನು ಸ್ಪಷ್ಟವಾಗಿ ಅರ್ಥಮಾಡಿಕೊಳ್ಳಲಿಲ್ಲ. ಬ್ಯಾಲೆನ್ಸ್, ವಹಿವಾಟು, ಸಾಲ ಅರ್ಹತೆ ಅಥವಾ ಬಡ್ಡಿ ದರ ಕೇಳಿ.`

## Trace (personal touch)

Always populate:

```json
{
  "nlu_source": "gemini",
  "api_called": "getWhyBalance",
  "row_count": 12,
  "privacy_masking": true,
  "grounded": true,
  "data_source": "mock",
  "latency_ms": 610,
  "session_follow_up": false
}
```

UI copy:

```text
🤖 AI Understanding    Intent: Transaction Analysis
↓
🏦 Transaction API
↓
N transactions retrieved
↓
✅ Response grounded in banking data
```

If `grounded` is false: show the insufficient-facts sentence, not a guessed chart.

## Safety

Refuse before NLU if regex hits PIN/OTP/password/transfer. Still set intent `unsafe_refusal` so the trace is honest.

Do not send raw account ledgers into the wording prompt beyond the already-masked `facts_json`.
