"""Canned replies. Amounts are inserted from facts; this file stores no demo rupees."""

from __future__ import annotations

import re

_FALLBACK = {
    "en": (
        "I could not confidently understand that. You can ask about balance, "
        "transactions, why your balance changed, loan eligibility, interest rates, "
        "or bank policy such as KYC and loan documents."
    ),
    "hi": "मैं आपका प्रश्न पूरी तरह समझ नहीं पाया। आप बैलेंस, लेनदेन, लोन पात्रता, या ब्याज दर पूछ सकते हैं।",
    "kn": "ನಾನು ವಿನಂತಿಯನ್ನು ಸ್ಪಷ್ಟವಾಗಿ ಅರ್ಥಮಾಡಿಕೊಳ್ಳಲಿಲ್ಲ. ಬ್ಯಾಲೆನ್ಸ್, ವಹಿವಾಟು, ಸಾಲ ಅರ್ಹತೆ ಅಥವಾ ಬಡ್ಡಿ ದರ ಕೇಳಿ.",
}

_UNSAFE = {
    "en": (
        "I cannot display PINs, OTPs, or passwords, and I cannot transfer money "
        "in this prototype. Use official bank channels for those actions."
    ),
    "hi": "मैं पिन, ओटीपी या पासवर्ड नहीं दिखा सकता और इस प्रोटोटाइप में पैसे ट्रांसफर नहीं कर सकता।",
    "kn": "ನಾನು PIN, OTP ಅಥವಾ ಪಾಸ್‌ವರ್ಡ್ ತೋರಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ, ಮತ್ತು ಈ ಮಾದರಿಯಲ್ಲಿ ಹಣ ವರ್ಗಾಯಿಸಲು ಆಗುವುದಿಲ್ಲ.",
}

_RAG_MISS = {
    "en": (
        "I could not find a matching policy passage. Please rephrase your question "
        "about KYC, UPI, NEFT, loan documents, or card services."
    ),
    "hi": "मुझे इस प्रश्न से मेल खाता नीति अंश नहीं मिला। कृपया KYC, UPI या लोन दस्तावेज़ के बारे में फिर पूछें।",
    "kn": "ಈ ಪ್ರಶ್ನೆಗೆ ಹೊಂದುವ ನೀತಿ ಭಾಗ ಸಿಗಲಿಲ್ಲ. KYC, UPI ಅಥವಾ ಸಾಲ ದಾಖಲೆಗಳ ಬಗ್ಗೆ ಮತ್ತೆ ಕೇಳಿ.",
}

_CONSENT = {
    "en": (
        "I cannot show account-specific information because data-access consent "
        "is disabled on this profile."
    ),
    "hi": "इस प्रोफ़ाइल पर डेटा एक्सेस की सहमति बंद है, इसलिए मैं खाते की जानकारी नहीं दिखा सकता।",
    "kn": "ಈ ಪ್ರೊಫೈಲ್‌ನಲ್ಲಿ ಡೇಟಾ ಒಪ್ಪಿಗೆ ನಿಷ್ಕ್ರಿಯವಾಗಿದೆ, ಆದ್ದರಿಂದ ಖಾತೆ ಮಾಹಿತಿಯನ್ನು ತೋರಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ.",
}

_HANDOFF = {
    "en": "I can flag this for a bank agent. This prototype cannot transfer money or change account settings.",
    "hi": "मैं इसे बैंक एजेंट के लिए दर्ज कर सकता हूँ। यह प्रोटोटाइप पैसे ट्रांसफर नहीं कर सकता।",
    "kn": "ಇದನ್ನು ಬ್ಯಾಂಕ್ ಏಜೆಂಟ್‌ಗೆ ಗುರುತಿಸಬಹುದು. ಈ ಮಾದರಿ ಹಣ ವರ್ಗಾವಣೆ ಮಾಡುವುದಿಲ್ಲ.",
}

_INSUFFICIENT = {
    "en": (
        "I don't have enough information to answer that. Would you like me to "
        "check your simulated transactions or search bank policy?"
    ),
    "hi": "इसका उत्तर देने के लिए मेरे पास पर्याप्त जानकारी नहीं है। क्या मैं सिम्युलेटेड लेनदेन या बैंक नीति देखूँ?",
    "kn": "ಇದಕ್ಕೆ ಉತ್ತರಿಸಲು ಸಾಕಷ್ಟು ಮಾಹಿತಿ ಇಲ್ಲ. ಸಿಮ್ಯುಲೇಟೆಡ್ ವಹಿವಾಟು ಅಥವಾ ಬ್ಯಾಂಕ್ ನೀತಿ ನೋಡಲೇ?",
}

_EMPTY = {
    "en": "Please type a banking question.",
    "hi": "कृपया एक बैंकिंग प्रश्न लिखें।",
    "kn": "ದಯವಿಟ್ಟು ಬ್ಯಾಂಕಿಂಗ್ ಪ್ರಶ್ನೆಯನ್ನು ಬರೆಯಿರಿ.",
}


def format_inr(amount, decimals: bool = True) -> str:
    value = float(amount)
    sign = "-" if value < 0 else ""
    value = abs(value)
    frac = None
    if decimals:
        whole, frac = f"{value:.2f}".split(".")
    else:
        whole = str(int(round(value)))
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = [tail]
        while head:
            groups.append(head[-2:])
            head = head[:-2]
        whole = ",".join(reversed(groups))
    if frac is None:
        return f"{sign}₹{whole}"
    return f"{sign}₹{whole}.{frac}"


def last4(masked: str) -> str:
    digits = re.sub(r"\D", "", masked or "")
    return digits[-4:] if digits else "----"


def _lang(language: str) -> str:
    return language if language in {"en", "hi", "kn"} else "en"


def _period_phrase(period: str, language: str) -> str:
    if period == "last_month":
        return {"en": "last month", "hi": "पिछले महीने", "kn": "ಕಳೆದ ತಿಂಗಳು"}[_lang(language)]
    return {"en": "this month", "hi": "इस महीने", "kn": "ಈ ತಿಂಗಳು"}[_lang(language)]


def fallback(language: str) -> str:
    return _FALLBACK[_lang(language)]


def unsafe(language: str) -> str:
    return _UNSAFE[_lang(language)]


def rag_miss(language: str) -> str:
    return _RAG_MISS[_lang(language)]


def consent(language: str) -> str:
    return _CONSENT[_lang(language)]


def handoff(language: str) -> str:
    return _HANDOFF[_lang(language)]


def insufficient(language: str) -> str:
    return _INSUFFICIENT[_lang(language)]


def empty(language: str) -> str:
    return _EMPTY[_lang(language)]


def balance(language: str, facts: dict) -> str:
    account = facts.get("account_type") or "savings"
    tail = last4(facts.get("masked_account_number") or "")
    amount = format_inr(facts.get("available_balance") or 0, decimals=True)
    lang = _lang(language)
    if lang == "hi":
        return f"आपके {account} खाते के अंतिम अंक {tail} हैं और उपलब्ध बैलेंस {amount} है।"
    if lang == "kn":
        return f"ನಿಮ್ಮ {account} ಖಾತೆಯ ಕೊನೆಯ ಅಂಕೆ {tail}. ಲಭ್ಯ ಬಾಕಿ {amount}."
    return f"Your {account} account ending in {tail} has an available balance of {amount}."


def rates(language: str, facts: dict) -> str:
    rate = facts.get("selected_rate") or ""
    product = facts.get("selected_product") or "rate"
    lang = _lang(language)
    labels = {
        "en": {
            "home_loan": "home loan",
            "personal_loan": "personal loan",
            "fixed_deposit": "fixed deposit",
            "savings_account": "savings account",
        },
        "hi": {
            "home_loan": "होम लोन",
            "personal_loan": "पर्सनल लोन",
            "fixed_deposit": "फिक्स्ड डिपॉजिट",
            "savings_account": "सेविंग्स खाता",
        },
        "kn": {
            "home_loan": "ಹೋಮ್ ಲೋನ್",
            "personal_loan": "ಪರ್ಸನಲ್ ಲೋನ್",
            "fixed_deposit": "ಫಿಕ್ಸೆಡ್ ಡೆಪಾಸಿಟ್",
            "savings_account": "ಉಳಿತಾಯ ಖಾತೆ",
        },
    }
    name = labels[lang].get(product, product)
    if not rate:
        return insufficient(language)
    if lang == "hi":
        return f"इस डेमो डेटा में {name} की ब्याज दर {rate} है।"
    if lang == "kn":
        return f"ಈ ಡೆಮೊ ಡೇಟಾದಲ್ಲಿ {name} ಬಡ್ಡಿ ದರ {rate}."
    return f"In this demo data the {name} interest rate is {rate}."


def loan(language: str, facts: dict) -> str:
    lang = _lang(language)
    kind = facts.get("loan_type") or "personal"
    rate = facts.get("interest_rate") or ""
    disclaimer = facts.get("disclaimer") or "Not a real loan offer."
    if not facts.get("eligible"):
        reason = facts.get("reason") or ""
        if lang == "hi":
            return f"इस सिम्युलेटेड प्रोफ़ाइल पर {kind} लोन की पात्रता नहीं बनती। {reason} {disclaimer}"
        if lang == "kn":
            return f"ಈ ಸಿಮ್ಯುಲೇಟೆಡ್ ಪ್ರೊಫೈಲ್ {kind} ಸಾಲಕ್ಕೆ ಅರ್ಹವಾಗಿಲ್ಲ. {reason} {disclaimer}"
        return f"Based on this simulated profile, you do not meet the {kind} loan rule. {reason} {disclaimer}"
    amount = format_inr(facts.get("max_amount") or 0, decimals=False)
    if lang == "hi":
        return f"इस सिम्युलेटेड प्रोफ़ाइल पर आप {amount} तक के {kind} लोन के लिए पात्र हो सकते हैं, दर {rate}। {disclaimer}"
    if lang == "kn":
        return f"ಈ ಸಿಮ್ಯುಲೇಟೆಡ್ ಪ್ರೊಫೈಲ್‌ನಲ್ಲಿ ನೀವು {amount} ವರೆಗಿನ {kind} ಸಾಲಕ್ಕೆ ಅರ್ಹರಾಗಬಹುದು, ದರ {rate}. {disclaimer}"
    return (
        f"Based on this simulated profile, you may be eligible for a {kind} loan "
        f"up to {amount} at {rate}. Final approval needs bank verification. {disclaimer}"
    )


def transactions(language: str, facts: dict) -> str:
    rows = facts.get("transactions") or []
    if not rows:
        return insufficient(language)
    bits = [
        f"{row.get('date')} {row.get('merchant')} {format_inr(row.get('amount') or 0, decimals=False)}"
        for row in rows[:5]
    ]
    joined = "; ".join(bits)
    lang = _lang(language)
    if lang == "hi":
        return f"आपके हाल के सिम्युलेटेड लेनदेन: {joined}।"
    if lang == "kn":
        return f"ನಿಮ್ಮ ಇತ್ತೀಚಿನ ಸಿಮ್ಯುಲೇಟೆಡ್ ವಹಿವಾಟುಗಳು: {joined}."
    return f"Here are your latest simulated transactions: {joined}."


def why_balance(language: str, facts: dict) -> str:
    if "spend_delta" not in facts:
        return insufficient(language)
    delta = float(facts.get("spend_delta") or 0)
    amount = format_inr(abs(delta), decimals=False)
    drivers = facts.get("drivers") or []
    pieces = [
        f"{item.get('category')} (+{format_inr(item.get('delta') or 0, decimals=False)})"
        for item in drivers[:2]
    ]
    driver_text = " and ".join(pieces)
    income = facts.get("income_delta", 0)
    lang = _lang(language)
    if lang == "en":
        change = "increased" if delta > 0 else "decreased" if delta < 0 else "was unchanged"
        income_text = "Income was unchanged." if income == 0 else f"Income change was {format_inr(income, decimals=False)}."
        mainly = f", mainly from {driver_text}" if driver_text else ""
        return (
            f"Your spending {change} by {amount} compared with last month{mainly}. "
            f"{income_text} This uses simulated transactions."
        )
    if lang == "hi":
        return f"पिछले महीने की तुलना में खर्च {amount} बदला है। {driver_text}. यह सिम्युलेटेड लेनदेन पर आधारित है।"
    return f"ಕಳೆದ ತಿಂಗಳಿಗಿಂತ ಖರ್ಚು {amount} ಬದಲಾಗಿದೆ. {driver_text}. ಇದು ಸಿಮ್ಯುಲೇಟೆಡ್ ವಹಿವಾಟು."


def spend(language: str, facts: dict) -> str:
    if "total" not in facts:
        return insufficient(language)
    total = format_inr(facts.get("total") or 0, decimals=False)
    period = _period_phrase(facts.get("period") or "this_month", language)
    category = facts.get("category")
    merchants = facts.get("by_merchant") or []
    lang = _lang(language)
    if merchants:
        bits = [
            f"{item.get('merchant')} {format_inr(item.get('total') or 0, decimals=False)}"
            for item in merchants
        ]
        listing = ", ".join(bits)
        if lang == "hi":
            return f"{period} के {category or 'खर्च'} व्यापारी: {listing}।"
        if lang == "kn":
            return f"{period} {category or 'ಖರ್ಚು'} ವ್ಯಾಪಾರಿಗಳು: {listing}."
        return f"{listing}."
    if category:
        if lang == "hi":
            return f"{period} {category} खर्च {total} है।"
        if lang == "kn":
            return f"{period} {category} ಖರ್ಚು {total}."
        return f"{category} spending {period} is {total}."
    if lang == "hi":
        return f"आपने {period} {total} खर्च किए (सिम्युलेटेड)।"
    if lang == "kn":
        return f"ನೀವು {period} {total} ಖರ್ಚು ಮಾಡಿದ್ದೀರಿ (ಸಿಮ್ಯುಲೇಟೆಡ್)."
    return f"You spent {total} {period} (simulated)."


def policy(language: str, facts: dict) -> str:
    titles = facts.get("chunk_titles") or []
    chunks = facts.get("chunks") or []
    if not titles and not chunks:
        return rag_miss(language)
    body = chunks[0] if chunks else ""
    source = ", ".join(titles)
    lang = _lang(language)
    if lang == "hi":
        return f"{body} स्रोत: {source}."
    if lang == "kn":
        return f"{body} ಮೂಲ: {source}."
    return f"{body} Sources: {source}."


def render(intent: str, language: str, facts: dict, message: str = "") -> str:
    if intent == "unsafe_refusal":
        return unsafe(language)
    if intent == "human_handoff":
        return handoff(language)
    if intent == "balance_check" and "available_balance" in (facts or {}):
        return balance(language, facts)
    if intent == "interest_rate_query":
        return rates(language, facts or {})
    if intent == "loan_eligibility" and facts:
        return loan(language, facts)
    if intent == "transaction_history":
        return transactions(language, facts or {})
    if intent == "why_balance_change":
        return why_balance(language, facts or {})
    if intent == "spend_drilldown":
        return spend(language, facts or {})
    if intent == "policy_rag":
        return policy(language, facts or {})
    if not (message or "").strip():
        return empty(language)
    return fallback(language)
