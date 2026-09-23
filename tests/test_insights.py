"""Locked insight totals must come from the ledger engine, not a handwritten LLM string."""

from app.insights import getSpendBreakdown, getWhyBalance


def test_eval_file_has_24_labeled_queries():
    from tests.eval_run import load_eval_queries

    rows = load_eval_queries()
    assert len(rows) == 24
    assert rows[20]["intent"] == "policy_rag"
    assert rows[20]["query"] == "What documents do I need for a personal loan?"


def test_why_balance_locked_totals():
    facts = getWhyBalance("CUST001")
    assert facts["this_month_spend"] == 18420
    assert facts["last_month_spend"] == 12180
    assert facts["spend_delta"] == 6240
    assert facts["income_delta"] == 0
    assert facts["currency"] == "INR"
    by_cat = {row["category"]: row["delta"] for row in facts["drivers"]}
    assert by_cat["Food"] == 2100
    assert by_cat["Shopping"] == 1850


def test_spend_this_month_and_food_merchants():
    all_cats = getSpendBreakdown("CUST001", period="this_month")
    assert all_cats["total"] == 18420
    food = getSpendBreakdown(
        "CUST001", period="this_month", category="Food", group_by="merchant"
    )
    assert food["total"] == 4280
    by_merchant = {row["merchant"]: row["total"] for row in food["by_merchant"]}
    assert by_merchant["Swiggy"] == 1840
    assert by_merchant["Zomato"] == 1120
    assert by_merchant["Other"] == 1320
    assert food["row_count"] == 3
