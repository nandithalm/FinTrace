"""Deterministic insight engine. Gemini must not compute these rupees.

Builder 3 routes:
  why_balance_change  -> getWhyBalance
  spend_drilldown     -> getSpendBreakdown

Ledger as-of 2026-09-23 (docs/04_DATA_AND_PRIVACY.md).
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, datetime
from typing import Any

from app.paths import TRANSACTIONS_PATH

THIS_MONTH = (date(2026, 9, 1), date(2026, 9, 23))
LAST_MONTH = (date(2026, 8, 1), date(2026, 8, 31))
PERIODS = {"this_month": THIS_MONTH, "last_month": LAST_MONTH}
FOOD_FEATURED = ("Swiggy", "Zomato")
SPEND_CATEGORIES = ("Food", "Shopping", "Bills", "Travel", "Other")


def _inr(value: float) -> int | float:
    rounded = round(float(value), 2)
    return int(rounded) if rounded == int(rounded) else rounded


def _parse_date(raw: str) -> date:
    return datetime.strptime(raw[:10], "%Y-%m-%d").date()


def _load_transactions() -> list[dict[str, Any]]:
    if not TRANSACTIONS_PATH.exists():
        return []
    return json.loads(TRANSACTIONS_PATH.read_text(encoding="utf-8"))


def _in_period(txn: dict[str, Any], bounds: tuple[date, date]) -> bool:
    day = _parse_date(str(txn["date"]))
    return bounds[0] <= day <= bounds[1]


def _customer_rows(customer_id: str) -> list[dict[str, Any]]:
    return [row for row in _load_transactions() if row.get("customer_id") == customer_id]


def _spend(rows: list[dict[str, Any]]) -> float:
    total = 0.0
    for row in rows:
        amount = float(row.get("amount") or 0)
        if amount < 0 and row.get("category") != "Income":
            total += -amount
    return total


def _income(rows: list[dict[str, Any]]) -> float:
    total = 0.0
    for row in rows:
        amount = float(row.get("amount") or 0)
        if amount > 0 and row.get("category") == "Income":
            total += amount
    return total


def _category_spend(rows: list[dict[str, Any]], category: str) -> float:
    total = 0.0
    for row in rows:
        if row.get("category") != category:
            continue
        amount = float(row.get("amount") or 0)
        if amount < 0:
            total += -amount
    return total


def getWhyBalance(customer_id: str) -> dict[str, Any]:
    """GET /api/mock/insights/why-balance — locked keys from docs/05_API_CONTRACT.md."""
    rows = _customer_rows(customer_id)
    this_rows = [r for r in rows if _in_period(r, THIS_MONTH)]
    last_rows = [r for r in rows if _in_period(r, LAST_MONTH)]
    this_spend = _spend(this_rows)
    last_spend = _spend(last_rows)
    drivers = []
    for category in SPEND_CATEGORIES:
        delta = _category_spend(this_rows, category) - _category_spend(last_rows, category)
        if delta:
            drivers.append({"category": category, "delta": _inr(delta)})
    drivers.sort(key=lambda item: abs(float(item["delta"])), reverse=True)
    return {
        "this_month_spend": _inr(this_spend),
        "last_month_spend": _inr(last_spend),
        "spend_delta": _inr(this_spend - last_spend),
        "income_delta": _inr(_income(this_rows) - _income(last_rows)),
        "drivers": drivers[:2],
        "currency": "INR",
    }


def getSpendBreakdown(
    customer_id: str,
    period: str = "this_month",
    category: str | None = None,
    group_by: str | None = None,
) -> dict[str, Any]:
    """GET /api/mock/insights/spend — locked keys from docs/05_API_CONTRACT.md."""
    bounds = PERIODS.get(period or "this_month", THIS_MONTH)
    period_key = period if period in PERIODS else "this_month"
    rows = [r for r in _customer_rows(customer_id) if _in_period(r, bounds)]
    category = (category or "").strip() or None
    group_by = (group_by or "").strip() or None

    if category:
        rows = [r for r in rows if r.get("category") == category]
        payload: dict[str, Any] = {
            "period": period_key,
            "category": category,
            "total": _inr(_spend(rows)),
            "currency": "INR",
            "row_count": 0,
        }
        if group_by == "merchant":
            by_merchant = _merchant_rollups(rows, food_other=(category == "Food"))
            payload["by_merchant"] = by_merchant
            payload["row_count"] = len(by_merchant)
        else:
            payload["row_count"] = len(rows)
        return payload

    by_category = [
        {"category": name, "total": _inr(_category_spend(rows, name))}
        for name in SPEND_CATEGORIES
        if _category_spend(rows, name)
    ]
    return {
        "period": period_key,
        "total": _inr(_spend(rows)),
        "by_category": by_category,
        "currency": "INR",
        "row_count": len(by_category),
    }


def _merchant_rollups(rows: list[dict[str, Any]], food_other: bool) -> list[dict[str, Any]]:
    buckets: dict[str, float] = defaultdict(float)
    for row in rows:
        amount = float(row.get("amount") or 0)
        if amount >= 0:
            continue
        merchant = str(row.get("merchant") or "Other")
        if food_other and merchant not in FOOD_FEATURED:
            merchant = "Other"
        buckets[merchant] += -amount
    ordered: list[dict[str, Any]] = []
    if food_other:
        for name in FOOD_FEATURED:
            if name in buckets:
                ordered.append({"merchant": name, "total": _inr(buckets.pop(name))})
        if "Other" in buckets:
            ordered.append({"merchant": "Other", "total": _inr(buckets.pop("Other"))})
        return ordered
    return [
        {"merchant": name, "total": _inr(total)}
        for name, total in sorted(buckets.items(), key=lambda item: item[1], reverse=True)
    ]
