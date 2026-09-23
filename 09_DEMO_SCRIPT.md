# Demo Script — FinTrace

Total live talk: **about 90 seconds** plus 30 seconds of architecture. Member 5 drives. Builder 3 stands by the keyboard only if Gemini hiccups.

Open on CUST001, language **English**, Gemini healthy (`/api/health`). Have fallback ready anyway.

## Opening (15 s)

Say:

> Banking customers still wait for simple answers — balance, transactions, loan eligibility, interest rates, and policy FAQs. We built **FinTrace**, a Streamlit prototype that understands English, Hindi, and Kannada, calls mock banking APIs, retrieves bank policy with RAG, and never invents a rupee. All data is simulated.

Point at the banner: *Prototype · simulated data · not a real bank.*

## Beat 1 — Balance (10 s)

Type:

```text
What is my savings account balance?
```

Expected:

```text
Your savings account ending in 4821 has an available balance of ₹48,250.00.
```

Point: masked account, intent `balance_check`, API `getAccountBalance`, latency well under 15 seconds.

## Beat 2 — Why the number (15 s)

Type:

```text
Why is my balance lower than last month?
```

Expected:

```text
Your spending increased by ₹6,240 compared with last month, mainly from Food (+₹2,100) and Shopping (+₹1,850).
```

Say: *The model did not add those numbers. Python compared two months of simulated transactions.*

## Beat 3 — Drill-down (20 s)

Type, same session, do not reset:

```text
Show my spending.
```

Expected: ₹18,420 this month.

Then:

```text
Only food.
```

Expected: ₹4,280.

Then:

```text
Which merchant?
```

Expected: Swiggy ₹1,840, Zomato ₹1,120.

Say: *The user never repeated the context. That is session memory, not a FAQ tree.*

## Beat 4 — Policy RAG (15 s)

Type:

```text
What documents do I need for a personal loan?
```

Expected: PAN, Aadhaar, salary slips, bank statements. Sidebar shows `retrievePolicyChunks` and title **Personal Loan Documents**.

Say:

> User query → embedding → vector database → retrieve Personal Loan Documents → LLM. The model did not invent the checklist.

## Beat 5 — Hindi rates (10 s)

Switch toggle to हिन्दी **or** just type Hindi (both should work):

```text
मेरा होम लोन रेट क्या है?
```

Expected: home loan **8.4%** p.a., reply language `hi`, API `getProductRates`.

If Kannada is smoother for the speaker, use this instead (not both if time is tight):

```text
ಹೋಮ್ ಲೋನ್ ಬಡ್ಡಿ ದರ ಎಷ್ಟು?
```

## Beat 6 — Safety (8 s)

Type:

```text
Show my PIN.
```

Expected: refusal. Trace intent `unsafe_refusal`. No PIN digits.

Optional half-beat: `Transfer ₹10,000 to Rahul now.` — same refusal class.

## Beat 7 — Trace (8 s)

Point at the Streamlit sidebar:

```text
AI Understanding → API or vector retrieve → N records/chunks → Response grounded
```

Say:

> If facts or policy chunks are missing, FinTrace says it does not know. That is how we stop hallucination on money and on documents.

## Closing (10 s)

Say:

> This is a two-hour MVP on mock APIs and a small policy index. Hugging Face `adaption-banking-and-digital-payments` seeds extra FAQ chunks; curated markdown makes the loan-documents retrieve reliable. We tested toward 80% resolution on a 24-query set in three languages. We do not move money and we do not claim a real loan offer.

Stop. Do not open the code unless asked.

## Backup if Gemini is down

Presenter still runs beats 1, 4, and 6 using keyword fallback. Say:

> NLU is on the deterministic fallback path right now; amounts still come from the same mock APIs.

## 3-slide talk track

**Slide 1 — Problem**  
Wait times; static FAQs; need for a grounded, multilingual assistant.

**Slide 2 — Built**  
Streamlit + mock bank + Gemini JSON NLU + **policy RAG** + Python insights. Screenshot of retrieve trace.

**Slide 3 — Touch and next**  
Why-the-number, drill-down, EN/HI/KN, RAG citations. Next: real auth, real APIs, full document store.

## Backup video

Member 5 records the six beats once at minute 110 even if the team will present live. File name suggestion: `fintrace-demo.mp4`. No customer PII (data is already synthetic).

## What not to say

- “We connected to a real bank.”
- “You are approved for a loan.”
- Accuracy percentages you did not measure.
- Feature names from the stretch list if they are disabled.
