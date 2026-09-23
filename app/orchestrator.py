"""One chat turn. Streamlit calls handle_turn; rupees come from mock or insight functions.

Builder 4 is expected to expose:
  app.insights.get_why_balance(customer_id)
  app.insights.get_spend_breakdown(customer_id, period=, category=, group_by=)
  app.rag.retrieve_policy(query, k=3)
Those imports are optional until that branch is merged.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Optional

from app import nlu, session_store, templates
from app.env import gemini_api_key, gemini_enabled, gemini_model
from app.safety import is_unsafe

_GEMINI_WORD_OK = True

ACCOUNT_INTENTS = frozenset(
    {
        "balance_check",
        "transaction_history",
        "loan_eligibility",
        "why_balance_change",
        "spend_drilldown",
    }
)

WORDING_PROMPT = """You are FinTrace, a prototype banking assistant.
Use only facts_json and retrieved_chunks. Never invent or recalculate amounts, rates, dates, or policy clauses.
If a number is not in facts_json, or a policy sentence is not in retrieved_chunks, say you do not have enough information
and offer to check simulated transactions or search bank policy.
Reply in language={language}. Keep it to 1-3 short sentences.
List retrieved chunk titles as Sources when intent is policy_rag.
Mention that data is simulated only if facts_json.contains_disclaimer is true
or this is the first turn.
Never reveal PIN, OTP, full account numbers, or another customer.

User query:
{message}

Intent:
{intent}

facts_json:
{facts}

retrieved_chunks:
{chunks}
"""


def _error(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def get_account_balance(customer_id: str, account_type: str = "savings") -> dict:
    try:
        from app.mock_bank import get_account_balance as impl
    except ImportError:
        return _error("MOCK_DATA_NOT_FOUND", "Mock bank is not available until the builder 2 branch is merged.")
    return impl(customer_id, account_type=account_type)


def get_transactions(customer_id: str, limit: Optional[int] = 5, category: Optional[str] = None, period: Optional[str] = None) -> dict:
    try:
        from app.mock_bank import get_transactions as impl
    except ImportError:
        return _error("MOCK_DATA_NOT_FOUND", "Mock bank is not available until the builder 2 branch is merged.")
    return impl(customer_id, limit=limit, category=category, period=period)


def get_loan_eligibility(customer_id: str, loan_type: str = "personal") -> dict:
    try:
        from app.mock_bank import get_loan_eligibility as impl
    except ImportError:
        return _error("MOCK_DATA_NOT_FOUND", "Mock bank is not available until the builder 2 branch is merged.")
    return impl(customer_id, loan_type=loan_type)


def get_product_rates() -> dict:
    try:
        from app.mock_bank import get_product_rates as impl
    except ImportError:
        return _error("MOCK_DATA_NOT_FOUND", "Mock bank is not available until the builder 2 branch is merged.")
    return impl()


def get_why_balance(customer_id: str) -> dict:
    try:
        import app.insights as insights
    except ImportError:
        return _error("INSUFFICIENT_FACTS", "Insight engine is not available until the builder 4 branch is merged.")
    fn = getattr(insights, "get_why_balance", None) or getattr(insights, "getWhyBalance", None)
    if fn is None:
        return _error("INSUFFICIENT_FACTS", "get_why_balance is not defined.")
    return fn(customer_id)


def get_spend_breakdown(
    customer_id: str,
    period: str = "this_month",
    category: Optional[str] = None,
    group_by: Optional[str] = None,
) -> dict:
    try:
        import app.insights as insights
    except ImportError:
        return _error("INSUFFICIENT_FACTS", "Insight engine is not available until the builder 4 branch is merged.")
    fn = getattr(insights, "get_spend_breakdown", None) or getattr(insights, "getSpendBreakdown", None)
    if fn is None:
        return _error("INSUFFICIENT_FACTS", "get_spend_breakdown is not defined.")
    return fn(customer_id, period=period, category=category, group_by=group_by)


def retrieve_policy(query: str, k: int = 3) -> dict:
    module = None
    for name in ("app.rag", "app.rag_retrieve"):
        try:
            module = __import__(name, fromlist=["retrieve_policy"])
            break
        except ImportError:
            continue
    if module is None or not hasattr(module, "retrieve_policy"):
        return {
            "query": query,
            "chunks": [],
            "row_count": 0,
            **_error("RAG_MISS", "Policy index is not built. Run python -m app.rag_ingest."),
        }
    return module.retrieve_policy(query, k=k)


def require_consent(customer_id: str, intent: str) -> Optional[dict]:
    try:
        from app.mock_bank import get_customer
        from app.mock_privacy import require_consent as impl
    except ImportError:
        return None
    return impl(get_customer(customer_id), intent)


def _rate_key(message: str, entities: dict) -> Optional[str]:
    if entities.get("loan_type") == "home" or re_search(r"home|होम|ಹೋಮ್", message):
        return "home_loan"
    if re_search(r"\bfd\b|fixed deposit|फिक्स्ड", message):
        return "fixed_deposit"
    if entities.get("loan_type") == "personal" or re_search(r"\bpersonal\b", message):
        return "personal_loan"
    if re_search(r"saving|सेविंग", message):
        return "savings_account"
    return None


def re_search(pattern: str, message: str) -> bool:
    import re

    return bool(re.search(pattern, message or "", re.I))


def _keep_chunks(payload: dict) -> list:
    kept = []
    for chunk in payload.get("chunks") or []:
        score = chunk.get("score")
        if score is not None and float(score) < 0.35:
            continue
        kept.append(chunk)
    return kept


def _route(intent: str, customer_id: str, message: str, entities: dict) -> tuple[dict, str, int, str]:
    """Return facts, api_called, row_count, data_source."""
    if intent == "balance_check":
        account_type = entities.get("account_type") or "savings"
        payload = get_account_balance(customer_id, account_type=account_type)
        return payload, "getAccountBalance", 1, "mock"

    if intent == "transaction_history":
        payload = get_transactions(
            customer_id,
            limit=entities.get("transaction_limit") or 5,
            category=entities.get("category"),
            period=entities.get("period"),
        )
        count = payload.get("row_count", len(payload.get("transactions") or []))
        facts = {
            "transactions": payload.get("transactions") or [],
            "row_count": count,
            "currency": "INR",
        }
        if "error" in payload:
            facts = payload
        return facts, "getTransactions", count if "error" not in payload else 0, "mock"

    if intent == "loan_eligibility":
        payload = get_loan_eligibility(customer_id, loan_type=entities.get("loan_type") or "personal")
        return payload, "getLoanEligibility", 1, "mock"

    if intent == "interest_rate_query":
        payload = get_product_rates()
        if "error" in payload:
            return payload, "getProductRates", 0, "mock"
        key = _rate_key(message, entities)
        facts = dict(payload)
        if key and key in payload:
            facts["selected_product"] = key
            facts["selected_rate"] = payload[key]
        return facts, "getProductRates", 1, "mock"

    if intent == "why_balance_change":
        payload = get_why_balance(customer_id)
        count = len(payload.get("drivers") or []) if "error" not in payload else 0
        return payload, "getWhyBalance", count, "mock"

    if intent == "spend_drilldown":
        group_by = "merchant" if entities.get("merchant_focus") else None
        payload = get_spend_breakdown(
            customer_id,
            period=entities.get("period") or "this_month",
            category=entities.get("category"),
            group_by=group_by,
        )
        if "error" in payload:
            return payload, "getSpendBreakdown", 0, "mock"
        count = payload.get("row_count")
        if count is None:
            count = len(payload.get("by_merchant") or payload.get("by_category") or [])
        return payload, "getSpendBreakdown", int(count), "mock"

    if intent == "policy_rag":
        payload = retrieve_policy(message, k=3)
        chunks = _keep_chunks(payload)
        if not chunks:
            return _error("RAG_MISS", "No policy chunk was above the similarity floor."), "retrievePolicyChunks", 0, "kb"
        facts = {
            "topic": entities.get("policy_topic") or "policy",
            "chunk_titles": [chunk.get("title") for chunk in chunks if chunk.get("title")],
            "chunks": [chunk.get("text") or "" for chunk in chunks],
            "sources": [chunk.get("source") for chunk in chunks if chunk.get("source")],
        }
        return facts, "retrievePolicyChunks", len(chunks), "kb"

    return {}, "", 0, "mock"


def _word(message: str, intent: str, language: str, facts: dict, first_turn: bool, started: float) -> str:
    if intent in {"unsafe_refusal", "human_handoff", "fallback"}:
        return templates.render(intent, language, facts, message)
    if "error" in (facts or {}):
        code = facts["error"]["code"]
        if code == "CONSENT_REQUIRED":
            return templates.consent(language)
        if code == "RAG_MISS":
            return templates.rag_miss(language)
        return templates.insufficient(language)

    elapsed = time.perf_counter() - started
    global _GEMINI_WORD_OK
    if _GEMINI_WORD_OK and gemini_enabled() and elapsed < 6:
        try:
            from google import genai
            from google.genai import types

            prompt_facts = dict(facts or {})
            prompt_facts["contains_disclaimer"] = first_turn
            chunks = prompt_facts.get("chunks") if intent == "policy_rag" else []
            prompt = WORDING_PROMPT.format(
                language=language,
                message=message,
                intent=intent,
                facts=prompt_facts,
                chunks=chunks or [],
            )

            def _call() -> str:
                client = genai.Client(api_key=gemini_api_key())
                response = client.models.generate_content(
                    model=gemini_model(),
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.2),
                )
                return (getattr(response, "text", "") or "").strip()

            with ThreadPoolExecutor(max_workers=1) as pool:
                text = pool.submit(_call).result(timeout=4)
            if text:
                return text
        except (Exception, FuturesTimeout):
            _GEMINI_WORD_OK = False
    return templates.render(intent, language, facts or {}, message)


def _response(
    *,
    reply: str,
    intent: str,
    entities: dict,
    language: str,
    confidence: float,
    facts: dict,
    nlu_source: str,
    api_called: str,
    row_count: int,
    grounded: bool,
    data_source: str,
    session_follow_up: bool,
    started: float,
    error: Optional[dict] = None,
) -> dict:
    public_facts = {}
    if facts and "error" not in facts:
        public_facts = {key: value for key, value in facts.items() if key != "contains_disclaimer"}
    body = {
        "reply": reply,
        "intent": intent,
        "entities": entities or {},
        "language": language,
        "confidence": confidence,
        "facts": public_facts,
        "trace": {
            "nlu_source": nlu_source,
            "api_called": api_called,
            "row_count": row_count,
            "privacy_masking": True,
            "grounded": grounded,
            "data_source": data_source,
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "session_follow_up": session_follow_up,
        },
    }
    if error:
        body["error"] = error
    return body


def handle_turn(
    session_id: str | dict = "demo-session",
    customer_id: str = "CUST001",
    message: str = "",
    ui_language: str = "en",
) -> dict:
    """Chat contract from docs/05_API_CONTRACT.md. A request dict is also accepted."""
    if isinstance(session_id, dict):
        payload = session_id
        session_id = payload.get("session_id") or "demo-session"
        customer_id = payload.get("customer_id") or customer_id
        message = payload.get("message") or ""
        ui_language = payload.get("ui_language") or ui_language

    started = time.perf_counter()
    message = (message or "").strip()
    if ui_language not in {"en", "hi", "kn"}:
        ui_language = "en"
    prior = session_store.get(session_id)
    first_turn = prior is None

    if not message:
        return _response(
            reply=templates.empty(ui_language),
            intent="fallback",
            entities={},
            language=ui_language,
            confidence=0.3,
            facts={},
            nlu_source="fallback",
            api_called="",
            row_count=0,
            grounded=False,
            data_source="mock",
            session_follow_up=False,
            started=started,
            error={"code": "EMPTY_MESSAGE", "message": "No query text"},
        )

    if is_unsafe(message):
        language = nlu.detect_language(message, ui_language)
        session_store.clear(session_id)
        return _response(
            reply=templates.unsafe(language),
            intent="unsafe_refusal",
            entities={},
            language=language,
            confidence=0.99,
            facts={},
            nlu_source="fallback",
            api_called="",
            row_count=0,
            grounded=False,
            data_source="mock",
            session_follow_up=False,
            started=started,
            error={"code": "UNSAFE_REQUEST", "message": "Forbidden action"},
        )

    parsed = nlu.understand(message, prior, ui_language)
    intent = parsed["intent"]
    entities = parsed["entities"]
    language = parsed["language"]
    confidence = float(parsed["confidence"])
    follow_up = bool(parsed["follow_up"])

    if intent in ACCOUNT_INTENTS:
        blocked = require_consent(customer_id, intent)
        if blocked:
            return _response(
                reply=templates.consent(language),
                intent=intent,
                entities=entities,
                language=language,
                confidence=confidence,
                facts={},
                nlu_source=parsed["nlu_source"],
                api_called="",
                row_count=0,
                grounded=False,
                data_source="mock",
                session_follow_up=follow_up,
                started=started,
                error=blocked["error"],
            )

    facts, api_called, row_count, data_source = _route(intent, customer_id, message, entities)
    error = facts.get("error") if isinstance(facts, dict) else None
    grounded = bool(facts) and error is None and intent not in {"fallback", "human_handoff", "unsafe_refusal"}
    if intent == "policy_rag":
        grounded = error is None and row_count > 0
    if intent in {"fallback", "human_handoff"}:
        grounded = False
        facts = {}
        api_called = ""
        row_count = 0

    reply = _word(message, intent, language, facts if error or facts else {}, first_turn, started)

    if intent == "unsafe_refusal":
        session_store.clear(session_id)
    else:
        session_store.save(
            session_id,
            {
                "customer_id": customer_id,
                "last_intent": intent,
                "last_entities": entities,
                "last_language": language,
                "last_facts": facts if error is None else {},
            },
        )

    return _response(
        reply=reply,
        intent=intent,
        entities=entities,
        language=language,
        confidence=confidence,
        facts=facts if error is None else {},
        nlu_source=parsed["nlu_source"],
        api_called=api_called if error is None or intent == "policy_rag" else api_called,
        row_count=0 if error else row_count,
        grounded=grounded,
        data_source=data_source,
        session_follow_up=follow_up,
        started=started,
        error=error,
    )
