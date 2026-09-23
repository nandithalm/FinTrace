"""Mock banking services. Rupees come from local JSON, never from an LLM.

Trace names Builder 3 should put in `trace.api_called`:
  getAccountBalance, getTransactions, getLoanEligibility, getProductRates
"""

from __future__ import annotations

import json
import os
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Optional

from app.mock_privacy import (
    error_body,
    mask_account_number,
    mask_email,
    mask_phone,
    require_consent,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

THIS_MONTH_START = date(2026, 9, 1)
THIS_MONTH_END = date(2026, 9, 23)
LAST_MONTH_START = date(2026, 8, 1)
LAST_MONTH_END = date(2026, 8, 31)

PERIODS = {
    "this_month": (THIS_MONTH_START, THIS_MONTH_END),
    "last_month": (LAST_MONTH_START, LAST_MONTH_END),
}


def _load(name: str):
    path = DATA / name
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def _customers() -> tuple:
    return tuple(_load("customers.json"))


@lru_cache(maxsize=1)
def _accounts() -> tuple:
    return tuple(_load("accounts.json"))


@lru_cache(maxsize=1)
def _transactions() -> tuple:
    return tuple(_load("transactions.json"))


@lru_cache(maxsize=1)
def _products() -> dict:
    return _load("products.json")


def get_customer(customer_id: str) -> Optional[dict]:
    for row in _customers():
        if row["customer_id"] == customer_id:
            return row
    return None


def get_customer_profile(customer_id: str) -> dict:
    """Masked profile fields for the UI strip. No full account numbers."""
    customer = get_customer(customer_id)
    if customer is None:
        return error_body("MOCK_DATA_NOT_FOUND", "No simulated customer matches that id.")
    if not customer.get("consent_enabled"):
        return {
            "name": customer.get("name"),
            "consent_enabled": False,
            "consent_blocked": True,
        }
    return {
        "name": customer.get("name"),
        "branch": customer.get("branch"),
        "masked_phone": mask_phone(customer.get("phone", "")),
        "masked_email": mask_email(customer.get("email", "")),
        "ifsc": customer.get("ifsc"),
        "nominee_first_name": customer.get("nominee_first_name"),
        "account_open_date": customer.get("account_open_date"),
        "consent_enabled": True,
        "consent_blocked": False,
    }


def health() -> dict:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return {"status": "ok", "product": "FinTrace", "gemini": bool(key)}


def get_account_balance(customer_id: str, account_type: str = "savings") -> dict:
    """GET /api/mock/accounts/{customer_id}/balance?account_type=savings"""
    customer = get_customer(customer_id)
    blocked = require_consent(customer, "balance_check")
    if blocked:
        return blocked

    wanted = (account_type or "savings").strip().lower()
    for account in _accounts():
        if account["customer_id"] != customer_id:
            continue
        if account["account_type"].lower() != wanted:
            continue
        return {
            "account_type": account["account_type"],
            "masked_account_number": mask_account_number(account["account_number"]),
            "available_balance": float(account["available_balance"]),
            "currency": account["currency"],
        }
    return error_body("MOCK_DATA_NOT_FOUND", f"No simulated {wanted} account for this customer.")


def get_transactions(
    customer_id: str,
    limit: Optional[int] = 5,
    category: Optional[str] = None,
    period: Optional[str] = None,
) -> dict:
    """GET /api/mock/accounts/{customer_id}/transactions

    limit=None returns every matching row (for the insight engine).
    """
    customer = get_customer(customer_id)
    blocked = require_consent(customer, "transaction_history")
    if blocked:
        return blocked

    window = PERIODS.get((period or "").strip())
    if period and window is None:
        return error_body("MOCK_DATA_NOT_FOUND", "Period must be this_month or last_month.")

    wanted_category = (category or "").strip().lower()
    rows = []
    for txn in _transactions():
        if txn["customer_id"] != customer_id:
            continue
        txn_date = date.fromisoformat(txn["date"])
        if window and not (window[0] <= txn_date <= window[1]):
            continue
        if wanted_category and txn["category"].lower() != wanted_category:
            continue
        rows.append(txn)

    rows.sort(key=lambda row: row["date"], reverse=True)
    if limit is not None:
        rows = rows[: max(int(limit), 0)]

    public = [
        {
            "date": row["date"],
            "merchant": row["merchant"],
            "category": row["category"],
            "amount": row["amount"],
            "masked_counterparty": row["masked_counterparty"],
        }
        for row in rows
    ]
    return {"transactions": public, "row_count": len(public)}


def get_loan_eligibility(customer_id: str, loan_type: str = "personal") -> dict:
    """GET /api/mock/loans/eligibility?customer_id=&loan_type="""
    customer = get_customer(customer_id)
    blocked = require_consent(customer, "loan_eligibility")
    if blocked:
        return blocked

    wanted = (loan_type or "personal").strip().lower()
    rule = next(
        (item for item in _products()["loan_rules"] if item["loan_type"] == wanted),
        None,
    )
    if rule is None:
        return error_body("MOCK_DATA_NOT_FOUND", f"No simulated rule for loan type '{wanted}'.")

    score = int(customer["credit_score"])
    income = int(customer["monthly_income"])
    eligible = score >= int(rule["min_credit_score"]) and income >= int(rule["min_income"])
    if eligible:
        reason = "Simulated credit score and income meet the rule."
    else:
        reason = "Simulated credit score or income does not meet the rule."

    return {
        "eligible": eligible,
        "loan_type": wanted,
        "max_amount": int(rule["max_amount"]) if eligible else 0,
        "interest_rate": rule["interest_rate"],
        "reason": reason,
        "disclaimer": "Not a real loan offer.",
    }


def get_product_rates() -> dict:
    """GET /api/mock/products/rates — public, no consent."""
    return dict(_products()["rates"])


getAccountBalance = get_account_balance
getTransactions = get_transactions
getLoanEligibility = get_loan_eligibility
getProductRates = get_product_rates
