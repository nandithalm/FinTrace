"""Builder 2 contract checks. Does not own the 24-query eval set."""

from app.mock_bank import (
    get_account_balance,
    get_loan_eligibility,
    get_product_rates,
    get_transactions,
)
from app.mock_privacy import mask_account_number, mask_card_number, mask_email, mask_phone


def _spend(period: str, category: str | None = None) -> int:
    payload = get_transactions("CUST001", limit=None, category=category, period=period)
    return sum(-row["amount"] for row in payload["transactions"] if row["amount"] < 0)


def test_savings_balance_is_locked():
    payload = get_account_balance("CUST001", "savings")
    assert payload["masked_account_number"] == "XXXXXX4821"
    assert payload["available_balance"] == 48250.00
    assert payload["currency"] == "INR"


def test_current_balance():
    payload = get_account_balance("CUST001", "current")
    assert payload["masked_account_number"] == "XXXXXX1190"
    assert payload["available_balance"] == 128900.00


def test_consent_blocks_cust002_without_facts():
    payload = get_account_balance("CUST002", "savings")
    assert payload["error"]["code"] == "CONSENT_REQUIRED"
    assert "available_balance" not in payload


def test_unknown_customer():
    payload = get_account_balance("CUST999")
    assert payload["error"]["code"] == "MOCK_DATA_NOT_FOUND"


def test_rates_are_public():
    rates = get_product_rates()
    assert rates["savings_account"] == "3.0% p.a."
    assert rates["fixed_deposit"] == "6.8% p.a."
    assert rates["personal_loan"] == "11.5% onwards"
    assert rates["home_loan"] == "8.4% onwards"


def test_personal_loan_eligibility():
    payload = get_loan_eligibility("CUST001", "personal")
    assert payload["eligible"] is True
    assert payload["max_amount"] == 300000
    assert payload["interest_rate"] == "11.5% onwards"
    assert payload["disclaimer"] == "Not a real loan offer."


def test_locked_spend_totals():
    assert _spend("this_month") == 18420
    assert _spend("last_month") == 12180
    assert _spend("this_month") - _spend("last_month") == 6240
    assert _spend("this_month", "Food") == 4280
    assert _spend("last_month", "Food") == 2180
    assert _spend("this_month", "Shopping") == 5350
    assert _spend("last_month", "Shopping") == 3500


def test_food_merchants_this_month():
    payload = get_transactions("CUST001", limit=None, category="Food", period="this_month")
    by_merchant = {}
    for row in payload["transactions"]:
        by_merchant[row["merchant"]] = by_merchant.get(row["merchant"], 0) - row["amount"]
    assert by_merchant["Swiggy"] == 1840
    assert by_merchant["Zomato"] == 1120
    assert by_merchant["Other"] == 1320


def test_salary_credit_each_month():
    for period in ("this_month", "last_month"):
        payload = get_transactions("CUST001", limit=None, category="Income", period=period)
        assert payload["row_count"] == 1
        assert payload["transactions"][0]["amount"] == 75000


def test_transaction_limit_and_masking():
    payload = get_transactions("CUST001", limit=5)
    assert payload["row_count"] == 5
    assert payload["transactions"][0]["date"] == "2026-09-22"
    assert "****" in payload["transactions"][0]["masked_counterparty"] or payload["transactions"][0][
        "masked_counterparty"
    ] == "Employer"


def test_mask_helpers():
    assert mask_account_number("12345678904821") == "XXXXXX4821"
    assert mask_card_number("4111111111111234") == "XXXX-XXXX-XXXX-1234"
    assert mask_phone("9876543221") == "98XXXXXX21"
    assert mask_email("aarav@mail.com") == "a***@mail.com"
