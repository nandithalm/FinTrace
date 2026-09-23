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

_SMALL_TALK_GREETING = {
    "en": (
        "Hi! I'm FinTrace — a simulated banking assistant. I can help with balance, "
        "recent transactions, spending, why your balance changed, loan eligibility, "
        "interest rates, and policy topics like UPI, KYC, and loan documents."
    ),
    "hi": (
        "नमस्ते! मैं FinTrace हूँ (सिम्युलेटेड डेटा)। बैलेंस, लेनदेन, खर्च, लोन पात्रता, "
        "ब्याज दर और UPI/KYC जैसी नीति में मदद कर सकता हूँ।"
    ),
    "kn": (
        "ನಮಸ್ಕಾರ! ನಾನು FinTrace (ಸಿಮ್ಯುಲೇಟೆಡ್). ಬ್ಯಾಲೆನ್ಸ್, ವಹಿವಾಟು, ಖರ್ಚು, ಸಾಲ ಅರ್ಹತೆ, "
        "ಬಡ್ಡಿ ದರ ಮತ್ತು UPI/KYC ನೀತಿ ಕುರಿತು ಸಹಾಯ ಮಾಡಬಹುದು."
    ),
}

_SMALL_TALK_HELP = {
    "en": (
        "You can ask in everyday words — for example: “What is my balance?”, "
        "“Show recent transactions”, “Why did my money go down?”, “Am I eligible for a home loan?”, "
        "“FD rate”, or “How does UPI work?”. All answers use simulated data."
    ),
    "hi": "आप सामान्य भाषा में पूछ सकते हैं: बैलेंस, हाल के लेनदेन, खर्च, लोन, ब्याज दर, या UPI/KYC।",
    "kn": "ಸಾಮಾನ್ಯ ಪದಗಳಲ್ಲಿ ಕೇಳಿ: ಬ್ಯಾಲೆನ್ಸ್, ವಹಿವಾಟು, ಖರ್ಚು, ಸಾಲ, ಬಡ್ಡಿ ದರ, ಅಥವಾ UPI/KYC.",
}

_SMALL_TALK_THANKS = {
    "en": "You're welcome! Ask anytime about your simulated accounts or bank policy.",
    "hi": "आपका स्वागत है! सिम्युलेटेड खाते या बैंक नीति के बारे में पूछें।",
    "kn": "ಸ್ವಾಗತ! ಸಿಮ್ಯುಲೇಟೆಡ್ ಖಾತೆ ಅಥವಾ ಬ್ಯಾಂಕ್ ನೀತಿ ಕುರಿತು ಕೇಳಿ.",
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


def small_talk(language: str, message: str = "") -> str:
    text = (message or "").strip()
    lang = _lang(language)
    if re.fullmatch(r"(thanks?|thank you|thx|धन्यवाद|शुक्रिया|ಧನ್ಯವಾದ)[\s!.,?]*", text, re.I):
        return _SMALL_TALK_THANKS[lang]
    if re.search(r"\bhelp\b|what can you do|how can you help|मदद|ಹೇಗೆ ಸಹಾಯ", text, re.I):
        return _SMALL_TALK_HELP[lang]
    return _SMALL_TALK_GREETING[lang]


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
        bits = []
        for item in merchants:
            name = item.get("merchant")
            if name == "Other" and category == "Food":
                name = "other food merchants"
            bits.append(f"{name} {format_inr(item.get('total') or 0, decimals=False)}")
        listing = ", ".join(bits[:-1]) + ", and " + bits[-1] if len(bits) > 1 else (bits[0] if bits else "")
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


def unusual(language: str, facts: dict) -> str:
    flags = facts.get("flags") or []
    if not flags:
        return insufficient(language)
    bits = [
        f"{item.get('category')} (+{format_inr(item.get('delta') or 0, decimals=False)})"
        for item in flags[:2]
    ]
    detail = " and ".join(bits)
    spend = format_inr(facts.get("this_month_spend") or 0, decimals=False)
    lang = _lang(language)
    if lang == "hi":
        return f"इस महीने खर्च {spend} है। असामान्य वृद्धि: {detail}। यह सिम्युलेटेड लेनदेन है।"
    if lang == "kn":
        return f"ಈ ತಿಂಗಳ ಖರ್ಚು {spend}. ಅಸಾಮಾನ್ಯ ಏರಿಕೆ: {detail}. ಇದು ಅನುಕರಣೆ ವಹಿವಾಟು."
    return (
        f"This month's simulated spend is {spend}. Unusual increases versus last month: {detail}."
    )


def afford(language: str, facts: dict) -> str:
    if "projected_remaining" not in facts:
        return insufficient(language)
    purchase = format_inr(facts.get("amount") or 0, decimals=False)
    remaining = format_inr(facts.get("remaining_after_purchase") or 0, decimals=False)
    commitments = format_inr(facts.get("commitments") or 0, decimals=False)
    projected = format_inr(facts.get("projected_remaining") or 0, decimals=False)
    lang = _lang(language)
    if lang == "hi":
        return (
            f"{purchase} खर्चने के बाद शेष {remaining}। आने वाली प्रतिबद्धताएँ {commitments}। "
            f"अनुमानित शेष {projected}। सिम्युलेटेड।"
        )
    if lang == "kn":
        return (
            f"{purchase} ಖರ್ಚಿನ ನಂತರ ಉಳಿಕೆ {remaining}. ಬಾಧ್ಯತೆಗಳು {commitments}. "
            f"ಅಂದಾಜು ಉಳಿಕೆ {projected}. ಅನುಕರಣೆ."
        )
    return (
        f"After a {purchase} purchase, {remaining} would remain. Upcoming commitments are {commitments}. "
        f"Projected remaining is {projected}. This uses simulated data."
    )


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
    if intent == "small_talk":
        return small_talk(language, message)
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
    if intent == "unusual_spend":
        return unusual(language, facts or {})
    if intent == "affordability_what_if":
        return afford(language, facts or {})
    if intent == "policy_rag":
        return policy(language, facts or {})
    if not (message or "").strip():
        return empty(language)
    return fallback(language)
