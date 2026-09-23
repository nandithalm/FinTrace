"""Labeled 24-query eval (docs/07_EVALUATION_PLAN.md).

Always checks Builder 4 engines (insights + RAG retrieve).
If app.orchestrator.handle_turn exists (Builders 1/3), also scores the chat set.

Usage:
  python tests/eval_run.py
  pytest tests/test_insights.py tests/test_eval.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.insights import getSpendBreakdown, getWhyBalance
from app.paths import EVAL_QUERIES_PATH
from app.rag import retrieve_policy

LANGUAGE_IDS = {3, 4, 11, 14, 16, 23}
RAG_IDS = {21, 22, 23, 24}
PRIVACY_IDS = {18, 19}
SESSION_IDS = {6, 7, 8}


def load_eval_queries() -> list[dict]:
    return json.loads(EVAL_QUERIES_PATH.read_text(encoding="utf-8"))


def try_handle_turn():
    try:
        from app.orchestrator import handle_turn

        return handle_turn
    except Exception:
        return None


def _leaks_secret(text: str) -> bool:
    blob = text or ""
    if re.search(r"\b\d{16}\b", blob):
        return True
    if re.search(r"PIN:\s*\d", blob, re.I):
        return True
    return False


def score_chat(handle_turn) -> dict:
    rows = load_eval_queries()
    session_id = "eval-session-spend"
    intent_ok = 0
    acceptable = 0
    privacy_failures = 0
    rag_hits = 0
    latencies = []
    gemini = False
    details = []

    for row in rows:
        sid = session_id if row["id"] in SESSION_IDS else f"eval-{row['id']}"
        turn = handle_turn(sid, "CUST001", row["query"], row["lang"])
        predicted = turn.get("intent")
        intent_match = predicted == row["intent"]
        if intent_match:
            intent_ok += 1
        trace = turn.get("trace") or {}
        latencies.append(int(trace.get("latency_ms") or 0))
        if trace.get("nlu_source") == "gemini":
            gemini = True
        reply = str(turn.get("reply") or "")
        facts = turn.get("facts") or {}
        leak = _leaks_secret(json.dumps(turn, ensure_ascii=False))
        if row["id"] in PRIVACY_IDS:
            if leak or "PIN:" in reply:
                privacy_failures += 1
        lang_ok = True
        if row["id"] in LANGUAGE_IDS:
            lang_ok = turn.get("language") == row["lang"]
        rag_ok = True
        if row["id"] == 21:
            titles = facts.get("chunk_titles") or []
            rag_ok = "Personal Loan Documents" in titles
            if rag_ok:
                rag_hits += 1
        elif row["id"] in RAG_IDS:
            rag_ok = bool(facts.get("chunk_titles") or facts.get("chunks"))
            if rag_ok:
                rag_hits += 1
        ok = intent_match and lang_ok and rag_ok and not leak
        if row["id"] == 1:
            ok = ok and facts.get("available_balance") in (48250, 48250.0, 48250.00)
        if row["id"] == 10:
            ok = ok and facts.get("spend_delta") in (6240, 6240.0)
        if row["id"] == 6:
            ok = ok and facts.get("total") in (18420, 18420.0)
        if row["id"] == 7:
            ok = ok and facts.get("total") in (4280, 4280.0)
        if ok:
            acceptable += 1
        details.append(
            {
                "id": row["id"],
                "intent_ok": intent_match,
                "acceptable": ok,
                "predicted": predicted,
            }
        )

    avg = int(sum(latencies) / len(latencies)) if latencies else 0
    return {
        "total": len(rows),
        "intent_correct": intent_ok,
        "acceptable": acceptable,
        "privacy_failures": privacy_failures,
        "rag_citation_hits": rag_hits,
        "average_latency_ms": avg,
        "gemini_used": gemini,
        "details": details,
    }


def score_engines() -> dict:
    why = getWhyBalance("CUST001")
    spend = getSpendBreakdown("CUST001", period="this_month")
    food = getSpendBreakdown(
        "CUST001", period="this_month", category="Food", group_by="merchant"
    )
    loan = retrieve_policy("What documents do I need for a personal loan?")
    titles = [c.get("title") for c in loan.get("chunks") or []]
    return {
        "this_month_spend": why.get("this_month_spend"),
        "spend_delta": why.get("spend_delta"),
        "food_delta": next(
            (d["delta"] for d in why.get("drivers") or [] if d["category"] == "Food"),
            None,
        ),
        "shopping_delta": next(
            (d["delta"] for d in why.get("drivers") or [] if d["category"] == "Shopping"),
            None,
        ),
        "spend_total": spend.get("total"),
        "food_total": food.get("total"),
        "swiggy": next(
            (m["total"] for m in food.get("by_merchant") or [] if m["merchant"] == "Swiggy"),
            None,
        ),
        "zomato": next(
            (m["total"] for m in food.get("by_merchant") or [] if m["merchant"] == "Zomato"),
            None,
        ),
        "loan_doc_hit": "Personal Loan Documents" in titles,
        "loan_row_count": loan.get("row_count"),
    }


def print_report(chat: dict | None, engines: dict) -> None:
    print("Builder 4 engine (no LLM math)")
    print(f"  this_month_spend: {engines['this_month_spend']} (target 18420)")
    print(f"  spend_delta:      {engines['spend_delta']} (target 6240)")
    print(f"  Food delta:       {engines['food_delta']} (target 2100)")
    print(f"  Shopping delta:   {engines['shopping_delta']} (target 1850)")
    print(f"  Food merchants:   Swiggy {engines['swiggy']} / Zomato {engines['zomato']}")
    print(
        f"  RAG loan docs:    hit={engines['loan_doc_hit']} rows={engines['loan_row_count']}"
        " (run python -m app.rag_ingest if rows=0)"
    )
    print()
    if not chat:
        print("handle_turn not on this branch yet - chat 24-query table skipped.")
        print("After Builder 3 merges, re-run: python tests/eval_run.py")
        return
    print(f"Total queries: {chat['total']}")
    print(f"Intent correct: {chat['intent_correct']}/{chat['total']}")
    print(f"Response acceptable: {chat['acceptable']}/{chat['total']}")
    print(f"Privacy failures: {chat['privacy_failures']}")
    print(f"RAG citation hits: {chat['rag_citation_hits']}/4")
    print(f"Average latency: {chat['average_latency_ms']} ms")
    print(f"Gemini used: {'yes' if chat['gemini_used'] else 'no'}")


def run_eval() -> dict:
    engines = score_engines()
    handle_turn = try_handle_turn()
    chat = score_chat(handle_turn) if handle_turn else None
    print_report(chat, engines)
    return {"engines": engines, "chat": chat}


if __name__ == "__main__":
    run_eval()
