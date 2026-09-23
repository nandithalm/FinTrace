"""Privacy masking and consent gate for mock bank facts.

Builder 3 calls `require_consent` before account-specific intents.
Mock service functions also call it so a missed check still returns no balances.
"""

from __future__ import annotations

import re
from typing import Optional

ACCOUNT_SPECIFIC_INTENTS = frozenset(
    {
        "balance_check",
        "transaction_history",
        "loan_eligibility",
        "why_balance_change",
        "spend_drilldown",
    }
)

PUBLIC_INTENTS = frozenset(
    {
        "interest_rate_query",
        "policy_rag",
        "human_handoff",
        "unsafe_refusal",
        "fallback",
        "small_talk",
        "unusual_spend",
        "affordability_what_if",
    }
)

CONSENT_MESSAGE = (
    "I cannot show account-specific information because data-access consent "
    "is disabled on this profile."
)


def error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def mask_account_number(raw: str) -> str:
    """Keep last 4 digits. Never return a full account number."""
    digits = re.sub(r"\D", "", raw or "")
    last4 = digits[-4:] if digits else "0000"
    return f"XXXXXX{last4}"


def mask_card_number(raw: str) -> str:
    digits = re.sub(r"\D", "", raw or "")
    last4 = digits[-4:] if digits else "0000"
    return f"XXXX-XXXX-XXXX-{last4}"


def mask_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) < 4:
        return "98XXXXXX21"
    return f"{digits[:2]}XXXXXX{digits[-2:]}"


def mask_email(raw: str) -> str:
    text = (raw or "").strip()
    local, sep, domain = text.partition("@")
    if not sep or not domain or not local:
        return "a***@mail.com"
    return f"{local[0]}***@{domain}"


def mask_customer_id(customer_id: str) -> str:
    """Optional UI mask. Internal services may keep CUST001."""
    match = re.fullmatch(r"CUST(\d+)", customer_id or "")
    if not match:
        return "CUST***"
    return f"CUST***{match.group(1)[-3:]}"


def require_consent(customer: Optional[dict], intent: Optional[str] = None) -> Optional[dict]:
    """Return an error payload when the call must be blocked, else None.

    Public intents (rates, policy, handoff) are allowed without consent.
    A missing intent is treated as account-specific.
    """
    if intent in PUBLIC_INTENTS:
        return None
    if customer is None:
        return error_body("MOCK_DATA_NOT_FOUND", "No simulated customer matches that id.")
    if not customer.get("consent_enabled"):
        return error_body("CONSENT_REQUIRED", CONSENT_MESSAGE)
    return None
