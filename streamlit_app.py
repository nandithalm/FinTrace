"""FinTrace Streamlit UI — Builder 1.

Green FinTrace brand (navy / teal / mint / cream).
Answer X-Ray panel follows the structured trace from the product mock
(intent → source → records → grounded), not a generic blue chatbot skin.

Talks only to app.orchestrator.handle_turn so Builder 3 can merge in place.
"""

from __future__ import annotations

import html
import json

import streamlit as st

from app.i18n import CHIP_QUERIES, t
from app.mock_bank import get_customer_profile
from app.orchestrator import handle_turn

NAVY = "#0B1F3A"
TEAL = "#0F766E"
MINT = "#DFF7F2"
CREAM = "#FAFAF0"
SLATE = "#475569"
GREEN = "#16A34A"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {{
  font-family: "Plus Jakarta Sans", "Segoe UI", sans-serif;
}}
.stApp {{
  background: linear-gradient(180deg, {CREAM} 0%, {MINT} 42%, #ffffff 100%);
}}
#MainMenu, footer {{ visibility: hidden; }}
[data-testid="stHeader"] {{
  background: transparent;
}}
[data-testid="collapsedControl"] {{
  visibility: visible !important;
  display: flex !important;
  color: {NAVY} !important;
}}

.ft-banner {{
  background: {NAVY};
  color: #F8FAFC;
  border-radius: 14px;
  padding: 10px 16px;
  font-size: 0.82rem;
  letter-spacing: 0.02em;
  text-align: center;
  margin-bottom: 12px;
}}
.ft-brand {{
  display: flex;
  align-items: center;
  gap: 12px;
}}
.ft-logo {{
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: {TEAL};
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.1rem;
  box-shadow: 0 8px 20px rgba(15, 118, 110, 0.28);
}}
.ft-name {{
  font-size: 1.45rem;
  font-weight: 700;
  color: {NAVY};
  line-height: 1.1;
}}
.ft-sub {{
  color: {SLATE};
  font-size: 0.85rem;
}}
.block-container {{
  max-width: 820px;
  padding-top: 1.25rem;
}}
[data-testid="stChatMessage"] {{
  background: transparent;
}}
.fact-card {{
  background: {MINT};
  border-radius: 14px;
  padding: 12px 14px;
  margin-top: 10px;
  color: {NAVY};
}}
.fact-amt {{
  font-size: 1.45rem;
  font-weight: 700;
  color: {TEAL};
}}
.xray {{
  background: white;
  border-radius: 18px;
  padding: 16px;
  border: 1px solid {MINT};
  box-shadow: 0 10px 28px rgba(11, 31, 58, 0.07);
}}
.xray h3 {{
  margin: 0 0 10px 0;
  color: {NAVY};
  font-size: 1.05rem;
}}
.step {{
  background: {CREAM};
  border-radius: 12px;
  padding: 10px 12px;
  margin-bottom: 8px;
  color: {NAVY};
  font-size: 0.86rem;
}}
.step strong {{ color: {TEAL}; }}
.ok {{ color: {GREEN}; font-weight: 700; }}
.warn {{ color: #B45309; font-weight: 700; }}
div.stButton > button {{
  background: {TEAL};
  color: white;
  border: 0;
  border-radius: 999px;
  font-weight: 600;
}}
div.stButton > button:hover {{
  background: {NAVY};
  color: white;
}}
.step code {{
  word-break: break-word;
  white-space: pre-wrap;
}}
.xray, .step {{
  overflow-wrap: anywhere;
  word-break: break-word;
}}
section[data-testid="stSidebar"] {{
  overflow-x: hidden;
}}
</style>
"""


def _init_state() -> None:
    st.session_state.setdefault("ui_language", "en")
    st.session_state.setdefault("customer_id", "CUST001")
    st.session_state.setdefault("session_id", "demo-session")
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("last_response", None)
    st.session_state.setdefault("pending_query", None)
    st.session_state.setdefault("started", False)


def _inr(value) -> str:
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _render_facts(facts: dict, intent: str) -> str:
    if not facts:
        return ""
    if intent == "balance_check" and "available_balance" in facts:
        last4 = str(facts.get("masked_account_number", "XXXXXX4821"))[-4:]
        acct = facts.get("account_type", "savings").title()
        return (
            f'<div class="fact-card"><div class="fact-amt">'
            f'{_inr(facts["available_balance"])}</div>'
            f"{acct} account ···· {last4}</div>"
        )
    if intent == "why_balance_change":
        drivers = facts.get("drivers") or []
        lines = " · ".join(
            f"{d.get('category')} +{_inr(d.get('delta'))}" for d in drivers
        )
        return (
            f'<div class="fact-card"><div class="fact-amt">'
            f'+{_inr(facts.get("spend_delta"))}</div>'
            f"Spend vs last month<br>{lines}</div>"
        )
    if intent == "spend_drilldown" and "total" in facts:
        extra = facts.get("category") or facts.get("period") or ""
        return (
            f'<div class="fact-card"><div class="fact-amt">'
            f'{_inr(facts["total"])}</div>{extra}</div>'
        )
    if intent == "policy_rag":
        titles = ", ".join(facts.get("chunk_titles") or [])
        return f'<div class="fact-card">Sources: {titles}</div>'
    if intent == "loan_eligibility":
        return (
            f'<div class="fact-card"><div class="fact-amt">'
            f'{_inr(facts.get("max_amount"))}</div>'
            f'{facts.get("interest_rate", "")} · {facts.get("disclaimer", "")}</div>'
        )
    return ""


def _send(message: str) -> None:
    lang = st.session_state.ui_language
    st.session_state.messages.append({"role": "user", "content": message})
    result = handle_turn(
        session_id=st.session_state.session_id,
        customer_id=st.session_state.customer_id,
        message=message,
        ui_language=lang,
    )
    st.session_state.last_response = result
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result.get("reply", ""),
            "intent": result.get("intent"),
            "facts": result.get("facts") or {},
            "trace": result.get("trace") or {},
        }
    )


def _xray(lang: str) -> None:
    st.markdown(f'<div class="xray"><h3>{t(lang, "xray_title")}</h3>', unsafe_allow_html=True)
    resp = st.session_state.last_response
    if not resp:
        st.caption(t(lang, "empty_trace"))
        st.markdown("</div>", unsafe_allow_html=True)
        return

    trace = resp.get("trace") or {}
    entities = resp.get("entities") or {}
    facts = resp.get("facts") or {}
    grounded = bool(trace.get("grounded"))
    latency = trace.get("latency_ms", "—")

    filled = {k: v for k, v in entities.items() if v not in (None, False, "", [])}
    entity_line = html.escape(json.dumps(filled, ensure_ascii=False)) if filled else "—"
    intent = html.escape(str(resp.get("intent") or ""))
    language = html.escape(str(resp.get("language") or ""))
    api = html.escape(str(trace.get("api_called") or "—"))
    nlu_src = html.escape(str(trace.get("nlu_source") or "—"))
    try:
        conf_pct = f"{int(round(float(resp.get('confidence') or 0) * 100))}%"
    except (TypeError, ValueError):
        conf_pct = "—"

    st.markdown(
        f'<div class="step"><strong>1. {t(lang, "intent")}</strong><br>'
        f'Intent: <code>{intent}</code> · Language: <code>{language}</code><br>'
        f'{t(lang, "confidence")}: <code>{conf_pct}</code><br>'
        f'Entities: <code>{entity_line}</code></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="step"><strong>2. {t(lang, "api")}</strong><br>'
        f'<code>{api}</code> · {t(lang, "nlu")}: '
        f'<code>{nlu_src}</code></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="step"><strong>3. {t(lang, "rows")}</strong><br>'
        f'{trace.get("row_count", 0)} · {t(lang, "follow_up")}: '
        f'{trace.get("session_follow_up")}</div>',
        unsafe_allow_html=True,
    )
    status = t(lang, "grounded") if grounded else t(lang, "not_grounded")
    klass = "ok" if grounded else "warn"
    st.markdown(
        f'<div class="step"><strong>4. {t(lang, "latency")}: {latency} ms</strong><br>'
        f'<span class="{klass}">{"✅ " if grounded else "⚠️ "}{status}</span></div>',
        unsafe_allow_html=True,
    )

    titles = facts.get("chunk_titles") or facts.get("sources")
    if titles:
        st.caption(f'{t(lang, "sources")}: {", ".join(map(str, titles))}')
    if facts:
        with st.expander(t(lang, "facts"), expanded=False):
            st.json(facts)
    st.markdown("</div>", unsafe_allow_html=True)


def _profile_strip(customer_id: str, lang: str) -> None:
    profile = get_customer_profile(customer_id)
    if not profile or profile.get("error"):
        return
    if profile.get("consent_blocked"):
        st.caption(f"{profile.get('name', customer_id)} · {t(lang, 'profile_consent_off')}")
        return
    parts = [
        profile.get("name"),
        profile.get("branch"),
        profile.get("masked_phone"),
        profile.get("masked_email"),
        f"IFSC {profile.get('ifsc')}" if profile.get("ifsc") else None,
        profile.get("nominee_first_name") and f"Nominee: {profile['nominee_first_name']}",
    ]
    line = " · ".join(p for p in parts if p)
    if line:
        st.caption(line)


def main() -> None:
    st.set_page_config(
        page_title="FinTrace",
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _init_state()
    st.markdown(CSS, unsafe_allow_html=True)

    lang = st.session_state.ui_language

    with st.sidebar:
        st.markdown(
            f'<div class="ft-brand"><div class="ft-logo">F</div>'
            f'<div><div class="ft-name">FinTrace</div>'
            f'<div class="ft-sub">{t(lang, "header_sub")}</div></div></div>',
            unsafe_allow_html=True,
        )
        st.selectbox(
            t(lang, "lang"),
            options=["en", "hi", "kn"],
            format_func=lambda c: {"en": "EN", "hi": "हिन्दी", "kn": "ಕನ್ನಡ"}[c],
            key="ui_language",
        )
        st.selectbox(
            t(lang, "customer"),
            options=["CUST001", "CUST002"],
            format_func=lambda c: "CUST001 · Aarav (consent on)"
            if c == "CUST001"
            else "CUST002 · Meera (consent off)",
            key="customer_id",
        )
        if st.button(
            t(lang, "analyze"),
            help=t(lang, "analyze_hint"),
            use_container_width=True,
        ):
            st.session_state.pending_query = "Analyze my transactions"
        st.divider()
        st.caption(t(lang, "sidebar_title"))
        _xray(st.session_state.ui_language)

    st.markdown(f'<div class="ft-banner">{t(lang, "banner")}</div>', unsafe_allow_html=True)
    _profile_strip(st.session_state.customer_id, lang)

    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.write(t(lang, "welcome_short"))

    for msg in st.session_state.messages:
        role = "user" if msg["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.write(msg["content"])
            if role == "assistant":
                card = _render_facts(msg.get("facts") or {}, msg.get("intent") or "")
                if card:
                    st.markdown(card, unsafe_allow_html=True)

    st.caption(t(lang, "chips_label"))
    chips = [
        "chip_balance",
        "chip_txns",
        "chip_loan",
        "chip_upi",
        "chip_why",
        "chip_rates",
    ]
    cols = st.columns(len(chips))
    for i, key in enumerate(chips):
        with cols[i]:
            if st.button(t(lang, key), key=f"chip_{key}", use_container_width=True):
                st.session_state.pending_query = CHIP_QUERIES[lang][key]

    typed = st.chat_input(t(lang, "placeholder"))
    query = st.session_state.pending_query or typed
    if query:
        st.session_state.pending_query = None
        _send(query)
        st.rerun()


main()
