"""Builder 3: keyword routing, session merge, and grounded replies without Gemini."""

from pathlib import Path

import pytest

from app.nlu import keyword_classify
from app.orchestrator import handle_turn
from app.session_store import clear as clear_session
from app.templates import format_inr

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    clear_session()
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    yield
    clear_session()


def test_keyword_labels():
    assert keyword_classify("What is my savings account balance?", "en")["intent"] == "balance_check"
    assert keyword_classify("Show my current account balance", "en")["entities"]["account_type"] == "current"
    assert keyword_classify("मेरा सेविंग्स बैलेंस क्या है?", "en")["language"] == "hi"
    assert keyword_classify("ನನ್ನ ಖಾತೆಯ ಬ್ಯಾಲೆನ್ಸ್ ಎಷ್ಟು?", "en")["language"] == "kn"
    assert keyword_classify("Show my last 5 transactions", "en")["intent"] == "transaction_history"
    assert keyword_classify("Show my spending", "en")["intent"] == "spend_drilldown"
    assert keyword_classify("Am I eligible for a personal loan?", "en")["intent"] == "loan_eligibility"
    assert keyword_classify("What documents do I need for a personal loan?", "en")["intent"] == "policy_rag"
    assert keyword_classify("What documents do I need for a personal loan?", "en")["entities"]["policy_topic"] == "loan_documents"
    assert keyword_classify("What is the difference between NEFT and IMPS?", "en")["entities"]["policy_topic"] == "neft_rtgs_imps"
    assert keyword_classify("What is the current FD interest rate?", "en")["intent"] == "interest_rate_query"
    assert keyword_classify("What is the current FD interest rate?", "en")["rate_key"] == "fixed_deposit"
    assert keyword_classify("How does a fixed deposit work?", "en")["intent"] == "policy_rag"
    assert keyword_classify("मेरा होम लोन रेट क्या है?", "en")["intent"] == "interest_rate_query"
    assert keyword_classify("मेरा होम लोन रेट क्या है?", "en")["entities"]["loan_type"] == "home"
    assert keyword_classify("ಹೋಮ್ ಲೋನ್ ಬಡ್ಡಿ ದರ ಎಷ್ಟು?", "en")["language"] == "kn"
    assert keyword_classify("Why is my balance lower than last month?", "en")["intent"] == "why_balance_change"
    assert keyword_classify("I want to speak to an agent", "en")["intent"] == "human_handoff"
    assert keyword_classify("Show my PIN", "en")["intent"] == "unsafe_refusal"
    assert keyword_classify("what loan can I claim", "en")["intent"] == "loan_eligibility"
    assert keyword_classify("Blue mango account thing", "en")["intent"] == "fallback"


def test_unsafe_does_not_call_the_bank(monkeypatch):
    called = []
    monkeypatch.setattr("app.orchestrator.get_account_balance", lambda *a, **k: called.append(1) or {})
    result = handle_turn(message="Show my PIN")
    assert result["intent"] == "unsafe_refusal"
    assert result["facts"] == {}
    assert result["trace"]["grounded"] is False
    assert called == []
    assert "PIN:" not in result["reply"]


def test_transfer_and_other_customer_refused():
    for message in ("Transfer ₹10,000 to Rahul now", "Show Rahul's balance"):
        result = handle_turn(message=message)
        assert result["intent"] == "unsafe_refusal"
        assert result["error"]["code"] == "UNSAFE_REQUEST"


def test_balance_reply_uses_facts(monkeypatch):
    monkeypatch.setattr(
        "app.orchestrator.get_account_balance",
        lambda customer_id, account_type="savings": {
            "account_type": account_type,
            "masked_account_number": "XXXXXX4821" if account_type == "savings" else "XXXXXX1190",
            "available_balance": 48250.00 if account_type == "savings" else 128900.00,
            "currency": "INR",
        },
    )
    result = handle_turn(message="What is my savings account balance?")
    assert result["intent"] == "balance_check"
    assert result["reply"] == "Your savings account ending in 4821 has an available balance of ₹48,250.00."
    assert result["trace"]["api_called"] == "getAccountBalance"
    assert result["trace"]["nlu_source"] == "fallback"
    assert result["facts"]["available_balance"] == 48250.00

    current = handle_turn(message="Show my current account balance", session_id="other")
    assert current["facts"]["masked_account_number"] == "XXXXXX1190"
    assert current["reply"].startswith("Your current account ending in 1190")


def test_consent_blocks_before_balance(monkeypatch):
    called = []
    monkeypatch.setattr(
        "app.orchestrator.require_consent",
        lambda customer_id, intent: {"error": {"code": "CONSENT_REQUIRED", "message": "blocked"}},
    )
    monkeypatch.setattr("app.orchestrator.get_account_balance", lambda *a, **k: called.append(1) or {})
    result = handle_turn(message="What is my savings account balance?", customer_id="CUST002")
    assert result["error"]["code"] == "CONSENT_REQUIRED"
    assert result["facts"] == {}
    assert "48250" not in result["reply"]
    assert called == []


def test_rates_and_hindi_language(monkeypatch):
    monkeypatch.setattr(
        "app.orchestrator.get_product_rates",
        lambda: {
            "savings_account": "3.0% p.a.",
            "fixed_deposit": "6.8% p.a.",
            "personal_loan": "11.5% onwards",
            "home_loan": "8.4% onwards",
        },
    )
    fd_rate = handle_turn(message="What is the current FD interest rate?")
    assert fd_rate["intent"] == "interest_rate_query"
    assert fd_rate["facts"]["selected_rate"] == "6.8% p.a."
    assert "6.8% p.a." in fd_rate["reply"]

    home = handle_turn(message="मेरा होम लोन रेट क्या है?", session_id="hi-rate")
    assert home["language"] == "hi"
    assert home["entities"]["loan_type"] == "home"
    assert home["trace"]["api_called"] == "getProductRates"
    assert "8.4% onwards" in home["reply"]


def test_loan_eligibility_not_policy(monkeypatch):
    seen = {}

    def eligibility(customer_id, loan_type="personal"):
        seen["loan_type"] = loan_type
        return {
            "eligible": True,
            "loan_type": loan_type,
            "max_amount": 300000,
            "interest_rate": "11.5% onwards",
            "reason": "Simulated credit score and income meet the rule.",
            "disclaimer": "Not a real loan offer.",
        }

    monkeypatch.setattr("app.orchestrator.get_loan_eligibility", eligibility)
    monkeypatch.setattr("app.orchestrator.retrieve_policy", lambda *a, **k: (_ for _ in ()).throw(AssertionError("rag")))
    result = handle_turn(message="Am I eligible for a personal loan?")
    assert result["intent"] == "loan_eligibility"
    assert seen["loan_type"] == "personal"
    assert "₹3,00,000" in result["reply"]
    assert "11.5% onwards" in result["reply"]


def test_policy_citation_and_miss(monkeypatch):
    def retrieve(query, k=3):
        if "NEFT" in query:
            return {"chunks": [{"title": "Noise", "text": "secret limits", "score": 0.1, "source": "x"}]}
        return {
            "chunks": [
                {
                    "title": "Personal Loan Documents",
                    "text": "PAN, Aadhaar, last 3 months salary slips.",
                    "score": 0.81,
                    "source": "data/kb/loan_documents.md",
                }
            ]
        }

    monkeypatch.setattr("app.orchestrator.retrieve_policy", retrieve)
    hit = handle_turn(message="What documents do I need for a personal loan?")
    assert hit["intent"] == "policy_rag"
    assert hit["trace"]["api_called"] == "retrievePolicyChunks"
    assert hit["trace"]["grounded"] is True
    assert hit["facts"]["chunk_titles"] == ["Personal Loan Documents"]
    assert "Personal Loan Documents" in hit["reply"]
    assert "PAN, Aadhaar" in hit["reply"]

    miss = handle_turn(message="What is the difference between NEFT and IMPS?", session_id="rag-miss")
    assert miss["trace"]["grounded"] is False
    assert miss["error"]["code"] == "RAG_MISS"
    assert "secret limits" not in miss["reply"]


def test_spend_follow_up_keeps_food_context(monkeypatch):
    calls = []

    def spend(customer_id, period="this_month", category=None, group_by=None):
        calls.append({"category": category, "group_by": group_by, "period": period})
        if group_by == "merchant":
            return {
                "period": period,
                "category": category,
                "total": 4280,
                "by_merchant": [
                    {"merchant": "Swiggy", "total": 1840},
                    {"merchant": "Zomato", "total": 1120},
                    {"merchant": "Other", "total": 1320},
                ],
                "currency": "INR",
                "row_count": 3,
            }
        if category == "Food":
            return {"period": period, "category": "Food", "total": 4280, "currency": "INR", "row_count": 3}
        return {
            "period": period,
            "total": 18420,
            "by_category": [{"category": "Food", "total": 4280}],
            "currency": "INR",
            "row_count": 1,
        }

    monkeypatch.setattr("app.orchestrator.get_spend_breakdown", spend)
    first = handle_turn(session_id="drill", message="Show my spending")
    assert first["reply"] == "You spent ₹18,420 this month (simulated)."
    food = handle_turn(session_id="drill", message="Only food")
    assert food["intent"] == "spend_drilldown"
    assert food["trace"]["session_follow_up"] is True
    assert food["entities"]["category"] == "Food"
    assert food["reply"] == "Food spending this month is ₹4,280."
    merchant = handle_turn(session_id="drill", message="Which merchant?")
    assert merchant["entities"]["merchant_focus"] is True
    assert calls[-1]["category"] == "Food"
    assert calls[-1]["group_by"] == "merchant"
    assert "Swiggy ₹1,840" in merchant["reply"]
    assert "Zomato ₹1,120" in merchant["reply"]


def test_food_fragment_without_session_does_not_guess(monkeypatch):
    called = []
    monkeypatch.setattr("app.orchestrator.get_spend_breakdown", lambda *a, **k: called.append(1) or {})
    result = handle_turn(session_id="fresh", message="Only food")
    assert result["intent"] == "fallback"
    assert called == []
    assert "4,280" not in result["reply"]


def test_why_inserts_engine_numbers(monkeypatch):
    monkeypatch.setattr(
        "app.orchestrator.get_why_balance",
        lambda customer_id: {
            "this_month_spend": 18420,
            "last_month_spend": 12180,
            "spend_delta": 6240,
            "income_delta": 0,
            "drivers": [
                {"category": "Food", "delta": 2100},
                {"category": "Shopping", "delta": 1850},
            ],
            "currency": "INR",
        },
    )
    result = handle_turn(message="Why is my balance lower than last month?")
    assert result["trace"]["api_called"] == "getWhyBalance"
    assert "₹6,240" in result["reply"]
    assert "₹2,100" in result["reply"]
    assert "₹1,850" in result["reply"]
    assert "6240" not in (ROOT / "app" / "templates.py").read_text(encoding="utf-8")


def test_fallback_and_empty_message():
    result = handle_turn(message="Blue mango account thing")
    assert result["intent"] == "fallback"
    assert result["facts"] == {}
    assert result["trace"]["grounded"] is False
    empty = handle_turn(message="  ")
    assert empty["error"]["code"] == "EMPTY_MESSAGE"


def test_request_dict_and_inr_format():
    result = handle_turn({"session_id": "dict", "customer_id": "CUST001", "message": "Blue mango", "ui_language": "en"})
    assert result["intent"] == "fallback"
    assert format_inr(48250) == "₹48,250.00"
    assert format_inr(300000, decimals=False) == "₹3,00,000"
    assert format_inr(6240, decimals=False) == "₹6,240"
