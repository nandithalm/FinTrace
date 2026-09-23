# FinTrace — Eraser.io Diagrams

Copy each code block below and paste it into [eraser.io](https://eraser.io) → **New Diagram** → select the appropriate diagram type.

---

## 1. System Architecture Diagram (Cloud Architecture)

> **Paste into**: Eraser.io → New Diagram → **Cloud Architecture**

```
// FinTrace — System Architecture
// Paste this into eraser.io Cloud Architecture diagram

User [icon: user, color: blue]

Streamlit UI [icon: monitor, color: green] {
  Chat Interface [icon: message-circle, color: teal]
  Language Toggle [icon: globe, color: teal]
  Answer X-Ray Panel [icon: search, color: teal]
  Quick Action Chips [icon: grid, color: teal]
}

Orchestrator Layer [icon: cpu, color: orange] {
  handle_turn [icon: play-circle, color: orange]
  Safety Gate [icon: shield, color: red]
  Consent Gate [icon: lock, color: red]
  Intent Router [icon: git-branch, color: orange]
  Grounded Reply [icon: message-square, color: orange]
}

NLU Engine [icon: brain, color: purple] {
  Gemini NLU [icon: zap, color: purple]
  Keyword Fallback [icon: type, color: purple]
  Fragment Resolver [icon: link, color: purple]
}

Mock Banking Services [icon: database, color: blue] {
  getAccountBalance [icon: dollar-sign, color: blue]
  getTransactions [icon: list, color: blue]
  getLoanEligibility [icon: check-circle, color: blue]
  getProductRates [icon: trending-up, color: blue]
}

Insight Engine [icon: bar-chart-2, color: cyan] {
  getWhyBalance [icon: help-circle, color: cyan]
  getSpendBreakdown [icon: pie-chart, color: cyan]
}

Policy RAG [icon: book-open, color: green] {
  RAG Retrieve [icon: search, color: green]
  Chroma Vector DB [icon: database, color: green]
  Sentence Transformer [icon: cpu, color: green]
}

Privacy Layer [icon: shield, color: red] {
  Account Masking [icon: eye-off, color: red]
  Consent Check [icon: check-square, color: red]
}

Session Store [icon: hard-drive, color: gray] {
  In-Memory Dict [icon: server, color: gray]
}

External Services [icon: cloud, color: indigo] {
  Google Gemini API [icon: cloud, color: indigo]
  Hugging Face Datasets [icon: cloud, color: indigo]
}

Data Layer [icon: folder, color: yellow] {
  customers.json [icon: file-text, color: yellow]
  accounts.json [icon: file-text, color: yellow]
  transactions.json [icon: file-text, color: yellow]
  products.json [icon: file-text, color: yellow]
  KB Markdown [icon: file-text, color: yellow]
}

// Connections
User > Streamlit UI: Query (EN/HI/KN)
Streamlit UI > handle_turn: handle_turn()
handle_turn > Safety Gate: Check unsafe patterns
Safety Gate > Consent Gate: If safe
Consent Gate > NLU Engine: If consent OK
NLU Engine > Gemini NLU: Try Gemini first
Gemini NLU > Google Gemini API: JSON prompt
NLU Engine > Keyword Fallback: Fallback if no API key
NLU Engine > Fragment Resolver: Follow-up resolution
NLU Engine > Intent Router: Structured JSON
Intent Router > Mock Banking Services: Account intents
Intent Router > Insight Engine: Why/Spend intents
Intent Router > Policy RAG: Policy questions
Mock Banking Services > Privacy Layer: Mask before return
Mock Banking Services > Data Layer: Read JSON
Insight Engine > Data Layer: Read transactions.json
Policy RAG > Chroma Vector DB: Vector search
Chroma Vector DB > Sentence Transformer: Embeddings
RAG Retrieve > Chroma Vector DB: query_texts
Intent Router > Grounded Reply: facts_json + chunks
Grounded Reply > Google Gemini API: Wording prompt
Grounded Reply > Streamlit UI: reply + trace
handle_turn > Session Store: Save/load context
Streamlit UI > User: Answer + X-Ray panel
```

---

## 2. Request Flow — Sequence Diagram

> **Paste into**: Eraser.io → New Diagram → **Sequence Diagram**

```
// FinTrace — Request Flow Sequence Diagram

title FinTrace Request Flow

User [icon: user, color: blue]
StreamlitUI [icon: monitor, color: green, label: "Streamlit UI"]
Orchestrator [icon: cpu, color: orange, label: "handle_turn"]
Safety [icon: shield, color: red, label: "Safety Gate"]
Consent [icon: lock, color: red, label: "Consent Gate"]
NLU [icon: brain, color: purple, label: "NLU Engine"]
GeminiAPI [icon: cloud, color: indigo, label: "Gemini API"]
Router [icon: git-branch, color: orange, label: "Intent Router"]
MockBank [icon: database, color: blue, label: "Mock Bank"]
Insights [icon: bar-chart-2, color: cyan, label: "Insights"]
RAG [icon: book-open, color: green, label: "Policy RAG"]
Chroma [icon: database, color: green, label: "ChromaDB"]
Reply [icon: message-square, color: orange, label: "Grounded Reply"]
Session [icon: hard-drive, color: gray, label: "Session Store"]

// Main flow
User > StreamlitUI: Query in EN, HI, or KN
StreamlitUI > Orchestrator: handle_turn(session_id, customer_id, message, ui_language)

// Safety check
Orchestrator > Safety: is_unsafe(message)
Safety > Orchestrator: safe / unsafe_refusal

// Consent check
Orchestrator > Consent: require_consent(customer_id, intent)
Consent > Orchestrator: allowed / CONSENT_REQUIRED

// NLU
Orchestrator > Session: get(session_id) — load prior context
Session > Orchestrator: prior session or None
Orchestrator > NLU: understand(message, session, ui_language)
NLU > GeminiAPI: NLU prompt → JSON (intent, entities, language, follow_up)
GeminiAPI > NLU: Structured JSON response
NLU > Orchestrator: {intent, entities, language, confidence, follow_up, nlu_source}

// Routing
Orchestrator > Router: _route(intent, customer_id, message, entities)

activate Router

// Branch: Account intents
Router > MockBank: getAccountBalance / getTransactions / getLoanEligibility
MockBank > Router: facts_json + row_count

// Branch: Insight intents
Router > Insights: getWhyBalance / getSpendBreakdown
Insights > Router: facts_json + drivers

// Branch: Policy RAG
Router > RAG: retrieve_policy(message, k=3)
RAG > Chroma: query(query_texts, n_results=3)
Chroma > RAG: documents + metadatas + distances
RAG > Router: chunks above similarity floor 0.35

deactivate Router

Router > Orchestrator: facts, api_called, row_count, data_source

// Grounded reply
Orchestrator > Reply: _word(message, intent, language, facts)
Reply > GeminiAPI: Wording prompt with facts_json + chunks
GeminiAPI > Reply: Natural language reply (1-3 sentences)
Reply > Orchestrator: reply text

// Fallback path
Reply > Orchestrator: template reply (if no API key / timeout)

// Save session
Orchestrator > Session: save(session_id, {customer_id, last_intent, last_entities, ...})

// Return
Orchestrator > StreamlitUI: {reply, intent, entities, language, confidence, facts, trace}
StreamlitUI > User: Chat bubble + Fact Card + Answer X-Ray panel
```

---

## 3. Component / Module Diagram (Entity Relationship)

> **Paste into**: Eraser.io → New Diagram → **Entity Relationship Diagram**

```
// FinTrace — Module Dependency Diagram

streamlit_app [icon: monitor, color: green] {
  main()
  _send()
  _xray()
  _render_facts()
  _init_state()
}

orchestrator [icon: cpu, color: orange] {
  handle_turn()
  _route()
  _word()
  _response()
  require_consent()
  get_account_balance()
  get_transactions()
  get_loan_eligibility()
  get_product_rates()
  get_why_balance()
  get_spend_breakdown()
  retrieve_policy()
}

nlu [icon: brain, color: purple] {
  understand()
  keyword_classify()
  _gemini_nlu()
  detect_language()
  apply_fragment()
  _apply_defaults()
  _merge_entities()
}

mock_bank [icon: database, color: blue] {
  get_account_balance()
  get_transactions()
  get_loan_eligibility()
  get_product_rates()
  get_customer()
  health()
}

mock_privacy [icon: shield, color: red] {
  require_consent()
  mask_account_number()
  mask_card_number()
  mask_phone()
  mask_email()
  error_body()
}

insights [icon: bar-chart-2, color: cyan] {
  getWhyBalance()
  getSpendBreakdown()
  _customer_rows()
  _spend()
  _income()
  _category_spend()
  _merchant_rollups()
}

rag [icon: book-open, color: green] {
  retrieve_policy()
  _collection()
  _similarity()
}

rag_ingest [icon: download, color: green] {
  main()
  load_curated_chunks()
  load_hf_chunks()
  persist_chroma()
  parse_markdown_chunks()
}

safety [icon: alert-triangle, color: red] {
  is_unsafe()
}

session_store [icon: hard-drive, color: gray] {
  get()
  save()
  clear()
}

templates [icon: file-text, color: teal] {
  render()
  consent()
  unsafe()
  empty()
  rag_miss()
  insufficient()
}

i18n [icon: globe, color: teal] {
  t()
  CHIP_QUERIES
}

paths [icon: folder, color: yellow] {
  CHROMA_DIR
  KB_DIR
  TRANSACTIONS_PATH
  COLLECTION_NAME
  EMBEDDING_MODEL
}

// Dependencies
streamlit_app > orchestrator: "handle_turn()"
streamlit_app > i18n: "t(), CHIP_QUERIES"
orchestrator > nlu: "understand(), detect_language()"
orchestrator > safety: "is_unsafe()"
orchestrator > session_store: "get(), save(), clear()"
orchestrator > templates: "render(), consent(), unsafe(), ..."
orchestrator > mock_bank: "get_account_balance(), get_transactions(), ..."
orchestrator > insights: "get_why_balance(), get_spend_breakdown()"
orchestrator > rag: "retrieve_policy()"
orchestrator > mock_privacy: "require_consent()"
mock_bank > mock_privacy: "require_consent(), mask_account_number()"
insights > paths: "TRANSACTIONS_PATH"
rag > paths: "CHROMA_DIR, COLLECTION_NAME, ..."
rag_ingest > paths: "KB_DIR, HF_CACHE_PATH, ..."
nlu > safety: "is_unsafe()"
```

---

## 4. Intent Routing Flowchart

> **Paste into**: Eraser.io → New Diagram → **Flowchart / Diagram as Code**

```
// FinTrace — Intent Routing Flowchart

User Query [shape: oval, icon: message-circle, color: blue]
Safety Check [shape: diamond, icon: shield, color: red, label: "Unsafe?\nPIN/OTP/transfer"]
Unsafe Refusal [shape: oval, icon: x-circle, color: red]
Consent Check [shape: diamond, icon: lock, color: red, label: "Consent\nenabled?"]
Consent Required [shape: oval, icon: alert-triangle, color: orange]
NLU [shape: rectangle, icon: brain, color: purple, label: "NLU Engine\n(Gemini or Keyword)"]
Intent [shape: diamond, icon: git-branch, color: orange, label: "Intent?"]

balance_check [shape: rectangle, icon: dollar-sign, color: blue, label: "getAccountBalance\nmock_bank.py"]
transaction_history [shape: rectangle, icon: list, color: blue, label: "getTransactions\nmock_bank.py"]
loan_eligibility [shape: rectangle, icon: check-circle, color: blue, label: "getLoanEligibility\nmock_bank.py"]
interest_rate [shape: rectangle, icon: trending-up, color: blue, label: "getProductRates\nmock_bank.py"]
why_balance [shape: rectangle, icon: help-circle, color: cyan, label: "getWhyBalance\ninsights.py"]
spend_drilldown [shape: rectangle, icon: pie-chart, color: cyan, label: "getSpendBreakdown\ninsights.py"]
policy_rag [shape: rectangle, icon: book-open, color: green, label: "retrievePolicyChunks\nrag.py → ChromaDB"]
human_handoff [shape: rectangle, icon: phone, color: gray, label: "Handoff Template"]
fallback [shape: rectangle, icon: help-circle, color: gray, label: "Clarifying Fallback"]

Privacy Masking [shape: rectangle, icon: eye-off, color: red, label: "Privacy Masking\nmask account numbers"]
Grounded Reply [shape: rectangle, icon: message-square, color: orange, label: "Grounded Reply\nGemini wording or templates"]
Response [shape: oval, icon: check, color: green, label: "Response + Trace\n→ UI"]

// Flow
User Query > Safety Check
Safety Check > Unsafe Refusal: Yes
Safety Check > Consent Check: No
Consent Check > Consent Required: Account intent + consent off
Consent Check > NLU: OK
NLU > Intent

Intent > balance_check: balance_check
Intent > transaction_history: transaction_history
Intent > loan_eligibility: loan_eligibility
Intent > interest_rate: interest_rate_query
Intent > why_balance [label: why_balance_change]
Intent > spend_drilldown: spend_drilldown
Intent > policy_rag: policy_rag
Intent > human_handoff: human_handoff
Intent > fallback: fallback / low confidence

balance_check > Privacy Masking
transaction_history > Privacy Masking
loan_eligibility > Privacy Masking
interest_rate > Privacy Masking
why_balance > Privacy Masking
spend_drilldown > Privacy Masking
policy_rag > Grounded Reply
human_handoff > Grounded Reply
fallback > Grounded Reply
Privacy Masking > Grounded Reply

Grounded Reply > Response
```

---

## 5. Data Flow Diagram

> **Paste into**: Eraser.io → New Diagram → **Flowchart / Diagram as Code**

```
// FinTrace — Data Flow

JSON Files [shape: cylinder, icon: database, color: yellow, label: "Local JSON\ncustomers / accounts\ntransactions / products"]
KB Markdown [shape: cylinder, icon: file-text, color: green, label: "data/kb/*.md\nPolicy Documents"]
HF Cache [shape: cylinder, icon: cloud, color: indigo, label: "HF Cached Subset\nhf_chunks.json"]

RAG Ingest [shape: rectangle, icon: download, color: green, label: "rag_ingest.py\nParse + Embed"]
Chroma DB [shape: cylinder, icon: database, color: green, label: "data/chroma/\nVector Index\n(cosine, k=3, floor=0.35)"]
MiniLM [shape: rectangle, icon: cpu, color: purple, label: "all-MiniLM-L6-v2\nSentence Transformer"]

Mock Bank [shape: rectangle, icon: server, color: blue, label: "mock_bank.py\nJSON Lookups"]
Insight Engine [shape: rectangle, icon: bar-chart-2, color: cyan, label: "insights.py\nDeterministic Math"]
RAG Retrieve [shape: rectangle, icon: search, color: green, label: "rag.py\nSimilarity Search"]

Orchestrator [shape: rectangle, icon: cpu, color: orange, label: "orchestrator.py\nhandle_turn()"]
Session Memory [shape: cylinder, icon: hard-drive, color: gray, label: "In-Memory Dict\nsession_store.py"]

Gemini [shape: rectangle, icon: cloud, color: indigo, label: "Google Gemini\n2.5 Flash"]

Streamlit [shape: rectangle, icon: monitor, color: green, label: "streamlit_app.py\nChat UI"]
User [shape: oval, icon: user, color: blue]

// Ingest path
KB Markdown > RAG Ingest
HF Cache > RAG Ingest
RAG Ingest > MiniLM: Encode chunks
MiniLM > Chroma DB: Store embeddings

// Runtime path
User > Streamlit: Query
Streamlit > Orchestrator: handle_turn()
Orchestrator > Session Memory: Load/save context
Orchestrator > Gemini: NLU prompt → intent JSON
Orchestrator > Mock Bank: Account/loan/rate queries
Orchestrator > Insight Engine: Why-balance / spend
Orchestrator > RAG Retrieve: Policy questions
Mock Bank > JSON Files: Read
Insight Engine > JSON Files: Read transactions
RAG Retrieve > Chroma DB: Vector search
RAG Retrieve > MiniLM: Embed query
Orchestrator > Gemini: Wording prompt → reply
Orchestrator > Streamlit: reply + facts + trace
Streamlit > User: Chat + X-Ray
```

---

## 6. Tech Stack Diagram

> **Paste into**: Eraser.io → New Diagram → **Cloud Architecture**

```
// FinTrace — Tech Stack

Frontend [icon: layout, color: green] {
  Streamlit [icon: monitor, color: green]
  Plus Jakarta Sans [icon: type, color: green]
  Custom CSS [icon: code, color: green]
}

Backend [icon: server, color: orange] {
  Python 3.10+ [icon: code, color: orange]
  Orchestrator [icon: cpu, color: orange]
  NLU Engine [icon: brain, color: purple]
  Safety Module [icon: shield, color: red]
  i18n Module [icon: globe, color: teal]
}

AI and ML [icon: zap, color: indigo] {
  Google Gemini 2.5 Flash [icon: cloud, color: indigo]
  Sentence Transformers [icon: cpu, color: purple]
  all-MiniLM-L6-v2 [icon: box, color: purple]
}

Data Storage [icon: database, color: blue] {
  Local JSON Files [icon: file-text, color: yellow]
  ChromaDB [icon: database, color: green]
  In-Memory Session [icon: hard-drive, color: gray]
}

External Data [icon: cloud, color: cyan] {
  Hugging Face Datasets [icon: cloud, color: cyan]
  Curated KB Markdown [icon: file-text, color: green]
}

Languages [icon: globe, color: teal] {
  English [icon: type, color: teal]
  Hindi [icon: type, color: teal]
  Kannada [icon: type, color: teal]
}

Frontend > Backend
Backend > AI and ML
Backend > Data Storage
AI and ML > Data Storage
External Data > Data Storage: RAG Ingest
```

---

## 7. Grounding Contract Flowchart

> **Paste into**: Eraser.io → New Diagram → **Flowchart / Diagram as Code**

```
// FinTrace — Anti-Hallucination Grounding Contract

Query [shape: oval, icon: message-circle, color: blue, label: "User Query"]

NLU Parse [shape: rectangle, icon: brain, color: purple, label: "Step 1: NLU\nGemini returns JSON only:\nintent, entities, language,\nfollow_up, confidence"]

Backend Call [shape: rectangle, icon: server, color: blue, label: "Step 2: Backend\nMock function = ONLY place\nrupees are calculated.\nNo LLM math ever."]

Grounded Wording [shape: rectangle, icon: message-square, color: orange, label: "Step 3: Gemini Wording\nSees facts_json + query.\nMust NOT add, invent, or\nround any amounts."]

Facts Check [shape: diamond, icon: help-circle, color: red, label: "Facts empty\nor RAG below\nfloor?"]

Refuse [shape: oval, icon: x-circle, color: red, label: "Grounded Refusal\nDo not guess.\nOffer alternatives."]

Trace Panel [shape: rectangle, icon: search, color: green, label: "Step 4: UI Trace\nAI Understanding →\nAPI called → N records →\nResponse grounded ✅"]

Response [shape: oval, icon: check, color: green, label: "Grounded Response\n+ Fact Card\n+ X-Ray Panel"]

Query > NLU Parse
NLU Parse > Backend Call
Backend Call > Facts Check
Facts Check > Refuse: Yes — empty
Facts Check > Grounded Wording: No — has facts
Grounded Wording > Trace Panel
Trace Panel > Response
```

---

## How to Use

1. Go to [eraser.io](https://app.eraser.io)
2. Click **New** → **Diagram**
3. Choose the diagram type noted above each block
4. Paste the code block contents (without the triple backticks)
5. The diagram renders instantly

> [!TIP]
> Diagrams 1, 2, and 6 work best as **Cloud Architecture** or **Sequence Diagram**. Diagrams 4, 5, and 7 work best as **Diagram as Code** (flowchart). Diagram 3 works best as **Entity Relationship**.
