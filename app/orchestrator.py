"""
Chat-turn contract shared by all builders.

Signature (do not change on merge):

    handle_turn(session_id, customer_id, message, ui_language) -> dict

Response keys the Streamlit UI requires:
    reply, intent, language, facts, entities,
    trace.latency_ms, trace.api_called, trace.grounded, trace.row_count

Builder 1: ships a local fixture so the UI runs without Gemini / mock bank / RAG.
Builder 3: replace `_fixture_handle_turn` internals (or set USE_FIXTURE = False
           and implement `real_handle_turn`) with the same return shape.
Builder 2 / 4: called from Builder 3, not from the UI.
"""

from __future__ import annotations

import time
from typing import Any

# Flip to False once Builder 3 lands a real orchestrator in this file.
USE_FIXTURE = True

SESSION: dict[str, dict[str, Any]] = {}


def handle_turn(
    session_id: str,
    customer_id: str,
    message: str,
    ui_language: str = "en",
) -> dict[str, Any]:
    if USE_FIXTURE:
        return _fixture_handle_turn(session_id, customer_id, message, ui_language)
    return real_handle_turn(session_id, customer_id, message, ui_language)


def real_handle_turn(
    session_id: str,
    customer_id: str,
    message: str,
    ui_language: str = "en",
) -> dict[str, Any]:
    """Builder 3 implements this. Must match the contract in docs/05_API_CONTRACT.md."""
    raise NotImplementedError("Builder 3: implement Gemini NLU + routing here")


def _base_trace(**extra: Any) -> dict[str, Any]:
    trace = {
        "nlu_source": "fallback",
        "api_called": "none",
        "row_count": 0,
        "privacy_masking": True,
        "grounded": False,
        "data_source": "mock",
        "latency_ms": 0,
        "session_follow_up": False,
    }
    trace.update(extra)
    return trace


def _ok(
    reply: str,
    intent: str,
    language: str,
    facts: dict[str, Any],
    entities: dict[str, Any],
    api: str,
    rows: int,
    follow_up: bool = False,
    latency_ms: int = 12,
) -> dict[str, Any]:
    return {
        "reply": reply,
        "intent": intent,
        "entities": entities,
        "language": language,
        "confidence": 0.85,
        "facts": facts,
        "trace": _base_trace(
            api_called=api,
            row_count=rows,
            grounded=True,
            latency_ms=latency_ms,
            session_follow_up=follow_up,
        ),
    }


def _fixture_handle_turn(
    session_id: str,
    customer_id: str,
    message: str,
    ui_language: str,
) -> dict[str, Any]:
    """Keyword fixtures using locked demo numbers from docs/02_MASTER_SPEC.md."""
    started = time.perf_counter()
    text = (message or "").strip()
    lang = ui_language if ui_language in {"en", "hi", "kn"} else "en"
    sess = SESSION.setdefault(
        session_id,
        {"last_intent": None, "last_entities": {}, "last_language": lang},
    )

    if not text:
        return {
            "reply": "Please type a banking question.",
            "intent": "fallback",
            "entities": {},
            "language": lang,
            "confidence": 0.0,
            "facts": {},
            "trace": _base_trace(api_called="none", latency_ms=1),
            "error": {"code": "EMPTY_MESSAGE", "message": "No query text"},
        }

    lower = text.lower()
    follow_up = False

    if customer_id == "CUST002" and any(
        k in lower for k in ("balance", "बैलेंस", "ಬ್ಯಾಲೆನ್ಸ್", "transaction", "spend")
    ):
        reply = {
            "en": "I cannot show account-specific information because data-access consent is disabled on this profile.",
            "hi": "इस प्रोफ़ाइल पर सहमति बंद है, इसलिए खाता जानकारी नहीं दिखा सकता।",
            "kn": "ಈ ಪ್ರೊಫೈಲ್‌ನಲ್ಲಿ ಸಮ್ಮತಿ ಇಲ್ಲದಿರುವುದರಿಂದ ಖಾತೆ ಮಾಹಿತಿಯನ್ನು ತೋರಿಸಲಾಗುವುದಿಲ್ಲ.",
        }[lang]
        return {
            "reply": reply,
            "intent": "fallback",
            "entities": {},
            "language": lang,
            "confidence": 1.0,
            "facts": {},
            "trace": _base_trace(
                api_called="consentGate",
                grounded=True,
                latency_ms=_ms(started),
            ),
            "error": {"code": "CONSENT_REQUIRED", "message": reply},
        }

    if any(k in lower for k in ("pin", "otp", "password", "transfer", "send money", "rahul")):
        reply = {
            "en": "I cannot display PINs, OTPs, or passwords, and I cannot transfer money in this prototype. Use official bank channels for those actions.",
            "hi": "मैं पिन, ओटीपी या पासवर्ड नहीं दिखा सकता, और इस प्रोटोटाइप में पैसे ट्रांसफर नहीं कर सकता।",
            "kn": "ನಾನು PIN, OTP ಅಥವಾ ಪಾಸ್‌ವರ್ಡ್ ತೋರಿಸುವುದಿಲ್ಲ ಮತ್ತು ಈ ಮೂಲಮಾದರಿಯಲ್ಲಿ ಹಣ ವರ್ಗಾಯಿಸುವುದಿಲ್ಲ.",
        }[lang]
        sess["last_intent"] = "unsafe_refusal"
        return {
            "reply": reply,
            "intent": "unsafe_refusal",
            "entities": {},
            "language": lang,
            "confidence": 1.0,
            "facts": {},
            "trace": _base_trace(
                api_called="safetyLayer",
                grounded=True,
                latency_ms=_ms(started),
            ),
        }

    if any(k in lower for k in ("agent", "human", "complaint", "escalate")):
        reply = {
            "en": "I can connect you to a human agent. This prototype only simulates handoff.",
            "hi": "मैं आपको मानव एजेंट से जोड़ सकता हूँ। यह प्रोटोटाइप केवल हैंडऑफ़ दिखाता है।",
            "kn": "ನಾನು ನಿಮ್ಮನ್ನು ಮಾನವ ಏಜೆಂಟ್‌ಗೆ ಸಂಪರ್ಕಿಸಬಹುದು. ಇದು ಸಿಮ್ಯುಲೇಟೆಡ್ ಹ್ಯಾಂಡ್‌ಆಫ್.",
        }[lang]
        return _ok(reply, "human_handoff", lang, {}, {}, "handoffTemplate", 0, latency_ms=_ms(started))

    fragment = lower in {"only food", "which merchant?", "which merchant", "savings", "last 5"} or "सिर्फ" in text
    if fragment and sess.get("last_intent") in {
        "transaction_history",
        "spend_drilldown",
        "why_balance_change",
    }:
        follow_up = True
        if "merchant" in lower:
            facts = {
                "period": "this_month",
                "category": "Food",
                "total": 4280,
                "by_merchant": [
                    {"merchant": "Swiggy", "total": 1840},
                    {"merchant": "Zomato", "total": 1120},
                    {"merchant": "Other", "total": 1320},
                ],
                "currency": "INR",
            }
            reply = {
                "en": "Swiggy ₹1,840, Zomato ₹1,120, and other food merchants ₹1,320.",
                "hi": "Swiggy ₹1,840, Zomato ₹1,120, अन्य फ़ूड ₹1,320।",
                "kn": "Swiggy ₹1,840, Zomato ₹1,120, ಇತರೆ ಆಹಾರ ₹1,320.",
            }[lang]
            sess["last_intent"] = "spend_drilldown"
            return _ok(
                reply,
                "spend_drilldown",
                lang,
                facts,
                {"category": "Food", "period": "this_month"},
                "getSpendBreakdown",
                3,
                follow_up=True,
                latency_ms=_ms(started),
            )
        facts = {
            "period": "this_month",
            "category": "Food",
            "total": 4280,
            "currency": "INR",
        }
        reply = {
            "en": "Food spending this month is ₹4,280.",
            "hi": "इस महीने फ़ूड खर्च ₹4,280 है।",
            "kn": "ಈ ತಿಂಗಳು ಆಹಾರ ಖರ್ಚು ₹4,280.",
        }[lang]
        sess["last_intent"] = "spend_drilldown"
        return _ok(
            reply,
            "spend_drilldown",
            lang,
            facts,
            {"category": "Food", "period": "this_month"},
            "getSpendBreakdown",
            3,
            follow_up=True,
            latency_ms=_ms(started),
        )

    if any(k in lower for k in ("document", "documents", "kyc", "neft", "imps", "rtgs", "dispute", "दस्तावेज", "ದಾಖಲೆ")):
        facts = {
            "topic": "loan_documents",
            "chunk_titles": ["Personal Loan Documents"],
            "chunks": [
                "For this prototype, a personal loan application typically requires: PAN, Aadhaar, last 3 months salary slips, last 6 months bank statements, and a passport-size photograph."
            ],
            "sources": ["data/kb/loan_documents.md"],
        }
        reply = {
            "en": "For a personal loan in this prototype policy pack you typically need: PAN, Aadhaar, last 3 months salary slips, last 6 months bank statements, and a passport-size photo. Final bank lists can differ. Sources: Personal Loan Documents.",
            "hi": "इस प्रोटोटाइप में पर्सनल लोन के लिए आमतौर पर PAN, आधार, 3 महीने के सैलरी स्लिप, 6 महीने के बैंक स्टेटमेंट और फोटो चाहिए। स्रोत: Personal Loan Documents.",
            "kn": "ಈ ಮೂಲಮಾದರಿಯಲ್ಲಿ ವೈಯಕ್ತಿಕ ಸಾಲಕ್ಕೆ ಸಾಮಾನ್ಯವಾಗಿ PAN, ಆಧಾರ್, 3 ತಿಂಗಳ ಸಂಬಳ ಸ್ಲಿಪ್, 6 ತಿಂಗಳ ಬ್ಯಾಂಕ್ ಸ್ಟೇಟ್‌ಮೆಂಟ್ ಮತ್ತು ಫೋಟೋ ಬೇಕು. ಮೂಲ: Personal Loan Documents.",
        }[lang]
        sess["last_intent"] = "policy_rag"
        return _ok(
            reply,
            "policy_rag",
            lang,
            facts,
            {"policy_topic": "loan_documents"},
            "retrievePolicyChunks",
            1,
            latency_ms=_ms(started),
        )

    if any(k in lower for k in ("why", "lower", "last month", "कम", "ಏಕೆ")):
        facts = {
            "this_month_spend": 18420,
            "last_month_spend": 12180,
            "spend_delta": 6240,
            "income_delta": 0,
            "drivers": [
                {"category": "Food", "delta": 2100},
                {"category": "Shopping", "delta": 1850},
            ],
            "currency": "INR",
        }
        reply = {
            "en": "Your spending increased by ₹6,240 compared with last month, mainly from Food (+₹2,100) and Shopping (+₹1,850). Income was unchanged. This uses simulated transactions.",
            "hi": "पिछले महीने की तुलना में खर्च ₹6,240 बढ़ा, मुख्यतः फ़ूड (+₹2,100) और शॉपिंग (+₹1,850)। आय वही रही। सिम्युलेटेड डेटा।",
            "kn": "ಕಳೆದ ತಿಂಗಳಿಗೆ ಹೋಲಿಸಿದರೆ ಖರ್ಚು ₹6,240 ಹೆಚ್ಚಾಗಿದೆ, ಮುಖ್ಯವಾಗಿ ಆಹಾರ (+₹2,100) ಮತ್ತು ಶಾಪಿಂಗ್ (+₹1,850). ಆದಾಯ ಬದಲಾಗಿಲ್ಲ.",
        }[lang]
        sess["last_intent"] = "why_balance_change"
        return _ok(
            reply,
            "why_balance_change",
            lang,
            facts,
            {"period": "last_month"},
            "getWhyBalance",
            12,
            latency_ms=_ms(started),
        )

    if any(k in lower for k in ("interest", "rate", "fd", "रेट", "ಬಡ್ಡಿ", "home loan")):
        facts = {
            "savings_account": "3.0% p.a.",
            "fixed_deposit": "6.8% p.a.",
            "personal_loan": "11.5% onwards",
            "home_loan": "8.4% onwards",
        }
        home = "home" in lower or "होम" in text or "ಹೋಮ್" in text
        reply = {
            "en": "Home loan rates currently start from 8.4% p.a. in this demo data."
            if home
            else "FD rates are 6.8% p.a. in this demo data. Home loans start from 8.4% p.a.",
            "hi": "इस डेमो डेटा में होम लोन की ब्याज दर 8.4% वार्षिक से शुरू होती है।",
            "kn": "ಈ ಡೆಮೊ ಡೇಟಾದಲ್ಲಿ ಹೋಮ್ ಲೋನ್ ಬಡ್ಡಿ ದರ 8.4% ವಾರ್ಷಿಕದಿಂದ ಪ್ರಾರಂಭವಾಗುತ್ತದೆ.",
        }[lang]
        sess["last_intent"] = "interest_rate_query"
        return _ok(
            reply,
            "interest_rate_query",
            lang,
            facts,
            {"loan_type": "home" if home else None},
            "getProductRates",
            4,
            latency_ms=_ms(started),
        )

    if any(k in lower for k in ("eligible", "eligibility", "emi")) or (
        "loan" in lower and "document" not in lower
    ):
        facts = {
            "eligible": True,
            "loan_type": "personal",
            "max_amount": 300000,
            "interest_rate": "11.5% onwards",
            "reason": "Simulated credit score and income meet the rule.",
            "disclaimer": "Not a real loan offer.",
        }
        reply = {
            "en": "Based on this simulated profile, you may be eligible for a personal loan up to ₹3,00,000 at 11.5% onwards. Final approval needs bank verification. This is not a real offer.",
            "hi": "इस सिम्युलेटेड प्रोफ़ाइल के अनुसार आप ₹3,00,000 तक पर्सनल लोन के पात्र हो सकते हैं (11.5% से)। यह वास्तविक ऑफ़र नहीं है।",
            "kn": "ಈ ಸಿಮ್ಯುಲೇಟೆಡ್ ಪ್ರೊಫೈಲ್ ಪ್ರಕಾರ ನೀವು ₹3,00,000 ವರೆಗೆ ವೈಯಕ್ತಿಕ ಸಾಲಕ್ಕೆ ಅರ್ಹರಾಗಿರಬಹುದು (11.5% ರಿಂದ). ಇದು ನಿಜವಾದ ಆಫರ್ ಅಲ್ಲ.",
        }[lang]
        sess["last_intent"] = "loan_eligibility"
        return _ok(
            reply,
            "loan_eligibility",
            lang,
            facts,
            {"loan_type": "personal"},
            "getLoanEligibility",
            1,
            latency_ms=_ms(started),
        )

    if any(k in lower for k in ("spend", "spending", "खर्च")):
        facts = {
            "period": "this_month",
            "total": 18420,
            "by_category": [
                {"category": "Food", "total": 4280},
                {"category": "Shopping", "total": 5350},
            ],
            "currency": "INR",
        }
        reply = {
            "en": "You spent ₹18,420 this month (simulated).",
            "hi": "इस महीने आपने ₹18,420 खर्च किए (सिम्युलेटेड)।",
            "kn": "ಈ ತಿಂಗಳು ನೀವು ₹18,420 ಖರ್ಚು ಮಾಡಿದ್ದೀರಿ (ಸಿಮ್ಯುಲೇಟೆಡ್).",
        }[lang]
        sess["last_intent"] = "spend_drilldown"
        return _ok(
            reply,
            "spend_drilldown",
            lang,
            facts,
            {"period": "this_month"},
            "getSpendBreakdown",
            2,
            follow_up=follow_up,
            latency_ms=_ms(started),
        )

    if any(k in lower for k in ("transaction", "लेनदेन", "ವಹಿವಾಟು")):
        facts = {
            "transactions": [
                {
                    "date": "2026-09-22",
                    "merchant": "Swiggy",
                    "category": "Food",
                    "amount": -1840,
                    "masked_counterparty": "Swiggy ****1022",
                }
            ],
            "row_count": 1,
        }
        reply = {
            "en": "Your latest simulated debit is Swiggy ₹1,840 on 22 Sep 2026 (account masked).",
            "hi": "नवीनतम सिम्युलेटेड डेबिट: Swiggy ₹1,840 (22 सितंबर 2026)।",
            "kn": "ಇತ್ತೀಚಿನ ಸಿಮ್ಯುಲೇಟೆಡ್ ಡೆಬಿಟ್: Swiggy ₹1,840 (22 ಸೆಪ್ಟೆಂಬರ್ 2026).",
        }[lang]
        sess["last_intent"] = "transaction_history"
        return _ok(
            reply,
            "transaction_history",
            lang,
            facts,
            {"transaction_limit": 5},
            "getTransactions",
            1,
            latency_ms=_ms(started),
        )

    if any(k in lower for k in ("balance", "बैलेंस", "ಬ್ಯಾಲೆನ್ಸ್")):
        account_type = "current" if "current" in lower else "savings"
        amount = 128900.00 if account_type == "current" else 48250.00
        last4 = "1190" if account_type == "current" else "4821"
        masked = f"XXXXXX{last4}"
        facts = {
            "account_type": account_type,
            "masked_account_number": masked,
            "available_balance": amount,
            "currency": "INR",
        }
        pretty = f"{amount:,.2f}"
        reply = {
            "en": f"Your {account_type} account ending in {last4} has an available balance of ₹{pretty}.",
            "hi": f"आपके {account_type} खाते (…{last4}) में उपलब्ध शेष ₹{pretty} है।",
            "kn": f"ನಿಮ್ಮ {account_type} ಖಾತೆ (…{last4}) ನಲ್ಲಿ ಲಭ್ಯ ಬ್ಯಾಲೆನ್ಸ್ ₹{pretty}.",
        }[lang]
        sess["last_intent"] = "balance_check"
        sess["last_entities"] = {"account_type": account_type}
        return _ok(
            reply,
            "balance_check",
            lang,
            facts,
            {"account_type": account_type},
            "getAccountBalance",
            1,
            latency_ms=_ms(started),
        )

    reply = {
        "en": "I could not confidently understand that. You can ask about balance, transactions, why your balance changed, loan eligibility, interest rates, or bank policy such as KYC and loan documents.",
        "hi": "मैं आपका प्रश्न पूरी तरह समझ नहीं पाया। आप बैलेंस, लेनदेन, लोन पात्रता, ब्याज दर या नीति पूछ सकते हैं।",
        "kn": "ನಾನು ವಿನಂತಿಯನ್ನು ಸ್ಪಷ್ಟವಾಗಿ ಅರ್ಥಮಾಡಿಕೊಳ್ಳಲಿಲ್ಲ. ಬ್ಯಾಲೆನ್ಸ್, ವಹಿವಾಟು, ಸಾಲ ಅರ್ಹತೆ, ಬಡ್ಡಿ ದರ ಅಥವಾ ನೀತಿ ಕೇಳಿ.",
    }[lang]
    return {
        "reply": reply,
        "intent": "fallback",
        "entities": {},
        "language": lang,
        "confidence": 0.30,
        "facts": {},
        "trace": _base_trace(api_called="none", latency_ms=_ms(started)),
    }


def _ms(started: float) -> int:
    return max(1, int((time.perf_counter() - started) * 1000))
