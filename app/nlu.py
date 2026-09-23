"""Intent detection: Gemini JSON when a key is present, otherwise keyword fallback."""

from __future__ import annotations

import json
import os
import re
from typing import Optional

ALLOWED_INTENTS = {
    "balance_check",
    "transaction_history",
    "loan_eligibility",
    "interest_rate_query",
    "why_balance_change",
    "spend_drilldown",
    "policy_rag",
    "human_handoff",
    "unsafe_refusal",
    "fallback",
}

_SPEND_CONTEXT = {"spend_drilldown", "transaction_history", "why_balance_change"}

_NLU_PROMPT = """You extract banking intent from a customer message.
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
{session}

User message:
{message}
"""


def empty_entities() -> dict:
    return {
        "account_type": None,
        "loan_type": None,
        "policy_topic": None,
        "category": None,
        "merchant_focus": False,
        "period": None,
        "transaction_limit": None,
        "amount": None,
    }


def detect_language(message: str, ui_language: str) -> str:
    if re.search(r"[\u0C80-\u0CFF]", message or ""):
        return "kn"
    if re.search(r"[\u0900-\u097F]", message or ""):
        return "hi"
    if ui_language in {"en", "hi", "kn"}:
        return ui_language
    return "en"


def _pack(intent: str, confidence: float, entities: dict, language: str, follow_up: bool, source: str) -> dict:
    return {
        "intent": intent if intent in ALLOWED_INTENTS else "fallback",
        "language": language,
        "follow_up": follow_up,
        "confidence": confidence,
        "entities": entities,
        "nlu_source": source,
        "rate_key": None,
    }


def _merge_entities(base: Optional[dict], update: Optional[dict]) -> dict:
    merged = empty_entities()
    merged.update({k: v for k, v in (base or {}).items() if k in merged})
    for key, value in (update or {}).items():
        if key not in merged or value is None:
            continue
        if key == "merchant_focus" and value is False and merged.get("merchant_focus"):
            continue
        if value is False and key != "merchant_focus":
            continue
        merged[key] = value
    return merged


def _fragment(message: str) -> Optional[dict]:
    text = (message or "").strip()
    if re.search(r"only food|just food|सिर्फ फूड|सिर्फ भोजन|केवल भोजन", text, re.I):
        return {"kind": "food", "entities": {"category": "Food", "merchant_focus": False}}
    if re.search(r"which merchant|what merchant|किस व्यापारी", text, re.I):
        return {"kind": "merchant", "entities": {"merchant_focus": True}}
    if re.fullmatch(r"savings|सेविंग्स", text, re.I):
        return {"kind": "account_only", "entities": {"account_type": "savings"}}
    if re.fullmatch(r"current", text, re.I):
        return {"kind": "account_only", "entities": {"account_type": "current"}}
    match = re.fullmatch(r"last\s+(\d+)", text, re.I)
    if match:
        return {"kind": "last_n", "entities": {"transaction_limit": int(match.group(1))}}
    return None


def apply_fragment(nlu: dict, message: str, session: Optional[dict]) -> dict:
    frag = _fragment(message)
    if not frag:
        return nlu
    last_intent = (session or {}).get("last_intent")
    entities = _merge_entities((session or {}).get("last_entities"), frag["entities"])
    if last_intent in _SPEND_CONTEXT and frag["kind"] in {"food", "merchant", "last_n", "account_only"}:
        nlu["intent"] = "spend_drilldown"
        nlu["follow_up"] = True
        nlu["confidence"] = max(float(nlu.get("confidence") or 0), 0.75)
        nlu["entities"] = entities
        return nlu
    if frag["kind"] == "account_only" and last_intent == "balance_check":
        nlu["intent"] = "balance_check"
        nlu["follow_up"] = True
        nlu["confidence"] = max(float(nlu.get("confidence") or 0), 0.75)
        nlu["entities"] = entities
        return nlu
    nlu["intent"] = "fallback"
    nlu["confidence"] = 0.30
    nlu["follow_up"] = False
    nlu["entities"] = empty_entities()
    return nlu


def _loan_type(text: str) -> Optional[str]:
    if re.search(r"home|होम|ಹೋಮ್", text, re.I):
        return "home"
    if re.search(r"personal|पर्सनल", text, re.I):
        return "personal"
    return None


def _account_type(text: str) -> Optional[str]:
    if re.search(r"\bcurrent\b|करंट", text, re.I):
        return "current"
    if re.search(r"saving|सेविंग|ಉಳಿತಾಯ", text, re.I):
        return "savings"
    return None


def _category(text: str) -> Optional[str]:
    for name in ("Food", "Shopping", "Bills", "Travel", "Income", "Other"):
        if re.search(rf"\b{name}\b", text, re.I):
            return name
    return None


def _period(text: str) -> Optional[str]:
    if re.search(r"last month|पिछले महीने|ಕಳೆದ ತಿಂಗಳ", text, re.I):
        return "last_month"
    if re.search(r"this month|इस महीने|ಈ ತಿಂಗಳ", text, re.I):
        return "this_month"
    return None


def _limit(text: str) -> Optional[int]:
    match = re.search(r"\blast\s+(\d+)\b|\b(\d+)\s+transactions?\b", text, re.I)
    if not match:
        return None
    return int(match.group(1) or match.group(2))


def _policy_topic(text: str) -> str:
    if re.search(r"\bkyc\b", text, re.I):
        return "kyc"
    if re.search(r"document|दस्तावेज|ದಾಖಲೆ", text, re.I) and re.search(r"loan|लोन|ಸಾಲ", text, re.I):
        return "loan_documents"
    if re.search(r"document|दस्तावेज|ದಾಖಲೆ", text, re.I):
        return "loan_documents"
    if re.search(r"\bupi\b", text, re.I):
        return "upi"
    if re.search(r"\b(neft|rtgs|imps)\b", text, re.I):
        return "neft_rtgs_imps"
    if re.search(r"dispute", text, re.I):
        return "transaction_dispute"
    if re.search(r"debit card|credit card", text, re.I):
        return "cards"
    if re.search(r"account opening", text, re.I):
        return "account_opening"
    if re.search(r"fixed deposit|\bfd\b", text, re.I):
        return "fd_savings"
    if re.search(r"\bpolicy\b", text, re.I):
        return "loan_policies"
    return "loan_policies"


def _rate_key(text: str) -> str:
    if re.search(r"home|होम|ಹೋಮ್", text, re.I):
        return "home_loan"
    if re.search(r"fixed deposit|\bfd\b", text, re.I):
        return "fixed_deposit"
    if re.search(r"personal|पर्सनल", text, re.I):
        return "personal_loan"
    if re.search(r"saving|सेविंग", text, re.I):
        return "savings_account"
    return "savings_account"


def _is_rate(text: str) -> bool:
    return bool(re.search(r"\brates?\b|\binterest\b|ब्याज|रेट|ಬಡ್ಡಿ|ದರ", text, re.I))


def _is_strong_policy(text: str) -> bool:
    return bool(
        re.search(
            r"document|documents|दस्तावेज|ದಾಖಲೆ|\bkyc\b|\bupi\b|\bneft\b|\brtgs\b|\bimps\b"
            r"|dispute|debit card|credit card|account opening|\bpolicy\b",
            text,
            re.I,
        )
    )


def keyword_classify(message: str, ui_language: str) -> dict:
    """Priority: unsafe, handoff, policy, rate (FD rate stays a rate), why, loan, spend, txn, balance."""
    text = message or ""
    language = detect_language(text, ui_language)
    entities = empty_entities()

    from app.safety import is_unsafe

    if is_unsafe(text):
        return _pack("unsafe_refusal", 0.95, entities, language, False, "fallback")
    if re.search(r"\bagent\b|\bhuman\b|complaint|escalate|एजेंट", text, re.I):
        return _pack("human_handoff", 0.75, entities, language, False, "fallback")
    if _is_strong_policy(text):
        entities["policy_topic"] = _policy_topic(text)
        return _pack("policy_rag", 0.75, entities, language, False, "fallback")
    if _is_rate(text):
        key = _rate_key(text)
        if key == "home_loan":
            entities["loan_type"] = "home"
        elif key == "personal_loan":
            entities["loan_type"] = "personal"
        packed = _pack("interest_rate_query", 0.75, entities, language, False, "fallback")
        packed["rate_key"] = key
        return packed
    if re.search(r"fixed deposit|\bfd\b", text, re.I):
        entities["policy_topic"] = "fd_savings"
        return _pack("policy_rag", 0.75, entities, language, False, "fallback")
    if re.search(r"\bwhy\b|lower|last month|कम|क्यों|ಏಕೆ|ಕಳೆದ ತಿಂಗಳ", text, re.I):
        entities["period"] = _period(text) or "this_month"
        return _pack("why_balance_change", 0.75, entities, language, False, "fallback")
    if re.search(r"eligible|eligibility|\bemi\b|पात्र|ಅರ್ಹ", text, re.I):
        entities["loan_type"] = _loan_type(text)
        return _pack("loan_eligibility", 0.75, entities, language, False, "fallback")
    if re.search(r"\bspend(?:ing)?\b|\bspent\b|shopping|लेनदेन खर्च", text, re.I):
        entities["category"] = _category(text)
        entities["period"] = _period(text)
        entities["merchant_focus"] = bool(re.search(r"which merchant", text, re.I))
        return _pack("spend_drilldown", 0.75, entities, language, False, "fallback")
    if re.search(r"transaction|लेनदेन|ವಹಿವಾಟು", text, re.I):
        entities["transaction_limit"] = _limit(text)
        entities["category"] = _category(text)
        entities["period"] = _period(text)
        return _pack("transaction_history", 0.75, entities, language, False, "fallback")
    if re.search(r"\bbalance\b|बैलेंस|ಬ್ಯಾಲೆನ್ಸ್", text, re.I):
        entities["account_type"] = _account_type(text)
        return _pack("balance_check", 0.75, entities, language, False, "fallback")
    return _pack("fallback", 0.30, entities, language, False, "fallback")


def _session_prompt(session: Optional[dict]) -> str:
    if not session:
        return "{}"
    public = {
        "last_intent": session.get("last_intent"),
        "last_entities": session.get("last_entities"),
        "last_language": session.get("last_language"),
    }
    return json.dumps(public, ensure_ascii=False)


def _gemini_nlu(message: str, session: Optional[dict], ui_language: str) -> Optional[dict]:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        return None
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        return None
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return None
    prompt = _NLU_PROMPT.format(session=_session_prompt(session), message=message)
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0, response_mime_type="application/json"),
        )
        raw = (response.text or "").strip()
    except Exception:
        return None
    return _parse_nlu_json(raw, message, ui_language)


def _parse_nlu_json(raw: str, message: str, ui_language: str) -> Optional[dict]:
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.I | re.M).strip()
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    if isinstance(payload, list):
        payload = payload[0] if payload else None
    if not isinstance(payload, dict):
        return None
    intent = payload.get("intent")
    if intent not in ALLOWED_INTENTS:
        return None
    entities = empty_entities()
    incoming = payload.get("entities") or {}
    if not isinstance(incoming, dict):
        incoming = {}
    entities = _merge_entities(entities, incoming)
    language = payload.get("language")
    if language not in {"en", "hi", "kn"}:
        language = detect_language(message, ui_language)
    try:
        confidence = float(payload.get("confidence"))
    except (TypeError, ValueError):
        confidence = 0.90 if any(entities.values()) else 0.80
    confidence = min(max(confidence, 0.0), 1.0)
    packed = _pack(intent, confidence, entities, language, bool(payload.get("follow_up")), "gemini")
    if intent == "interest_rate_query":
        packed["rate_key"] = _rate_key(message)
        if packed["rate_key"] == "home_loan":
            packed["entities"]["loan_type"] = packed["entities"].get("loan_type") or "home"
        elif packed["rate_key"] == "personal_loan":
            packed["entities"]["loan_type"] = packed["entities"].get("loan_type") or "personal"
    return packed


def _apply_defaults(nlu: dict) -> dict:
    intent = nlu["intent"]
    entities = nlu["entities"]
    if intent == "balance_check":
        entities["loan_type"] = None
        entities["policy_topic"] = None
        entities["account_type"] = entities.get("account_type") or "savings"
    elif intent == "loan_eligibility":
        entities["loan_type"] = entities.get("loan_type") or "personal"
    elif intent == "spend_drilldown":
        entities["period"] = entities.get("period") or "this_month"
    elif intent == "transaction_history" and not entities.get("transaction_limit"):
        entities["transaction_limit"] = 5
    elif intent == "why_balance_change":
        entities["period"] = entities.get("period") or "this_month"
    if float(nlu.get("confidence") or 0) < 0.50:
        nlu["intent"] = "fallback"
    return nlu


def understand(message: str, session: Optional[dict], ui_language: str) -> dict:
    parsed = _gemini_nlu(message, session, ui_language)
    if parsed is None:
        parsed = keyword_classify(message, ui_language)
    if parsed.get("follow_up") and session and parsed["intent"] not in {"fallback", "unsafe_refusal"}:
        parsed["entities"] = _merge_entities(session.get("last_entities"), parsed["entities"])
    parsed = apply_fragment(parsed, message, session)
    if parsed.get("follow_up") and session and parsed["intent"] in _SPEND_CONTEXT | {"balance_check", "transaction_history"}:
        parsed["entities"] = _merge_entities(session.get("last_entities"), parsed["entities"])
    return _apply_defaults(parsed)
