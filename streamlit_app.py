"""FinTrace Streamlit UI — Premium AI Banking Assistant.

Clean, high-contrast fintech design (Navy / Emerald Teal / Mint / Slate).
Dual-column cockpit:
  - Left: Interactive chat with styled bubbles, quick action chips, customer profile
  - Right: Live Answer X-Ray inspection panel (Intent -> API -> Records -> Grounding)
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
TEAL_HOVER = "#115E59"
MINT = "#E6F7F4"
MINT_BORDER = "#99F6E4"
SLATE = "#334155"
MUTED = "#64748B"
GREEN = "#16A34A"
AMBER = "#D97706"
CARD_BG = "#FFFFFF"
PAGE_BG = "#F8FAFC"
BORDER = "#E2E8F0"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {{
  font-family: "Plus Jakarta Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}}

.stApp {{
  background-color: {PAGE_BG} !important;
  color: {NAVY} !important;
}}

#MainMenu, footer {{ visibility: hidden; }}
[data-testid="stHeader"] {{
  background: transparent;
}}

/* Force main content container to be wide and centered */
.block-container {{
  max-width: 1380px !important;
  padding-top: 1rem !important;
  padding-bottom: 2rem !important;
  padding-left: 2rem !important;
  padding-right: 2rem !important;
  margin: 0 auto !important;
}}

/* Sidebar styling */
section[data-testid="stSidebar"] {{
  background-color: {NAVY} !important;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
}}
section[data-testid="stSidebar"] * {{
  color: #F8FAFC !important;
}}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stButton button {{
  color: #F8FAFC !important;
}}
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
  background-color: #1E293B !important;
  border-color: #334155 !important;
  color: #F8FAFC !important;
}}
section[data-testid="stSidebar"] div[data-baseweb="select"] * {{
  color: #F8FAFC !important;
}}
section[data-testid="stSidebar"] div.stButton > button {{
  background: linear-gradient(135deg, {TEAL} 0%, #14B8A6 100%) !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
  padding: 0.5rem 1rem !important;
  box-shadow: 0 4px 12px rgba(15, 118, 110, 0.3) !important;
}}
section[data-testid="stSidebar"] div.stButton > button:hover {{
  background: linear-gradient(135deg, {TEAL_HOVER} 0%, {TEAL} 100%) !important;
}}

/* Brand elements */
.ft-sidebar-brand {{
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0.5rem 0 1.25rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 1.25rem;
}}
.ft-logo {{
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #14B8A6 0%, {TEAL} 100%);
  color: #FFFFFF !important;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 1.35rem;
  box-shadow: 0 6px 16px rgba(20, 184, 166, 0.35);
}}
.ft-sidebar-name {{
  font-size: 1.4rem;
  font-weight: 800;
  color: #FFFFFF !important;
  letter-spacing: -0.02em;
  line-height: 1.1;
}}
.ft-sidebar-sub {{
  color: #94A3B8 !important;
  font-size: 0.8rem;
  font-weight: 500;
}}

/* Top banner */
.ft-banner {{
  background: linear-gradient(90deg, {NAVY} 0%, #1E293B 100%);
  color: #F8FAFC !important;
  border-radius: 12px;
  padding: 8px 16px;
  font-size: 0.82rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  text-align: center;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 2px 8px rgba(11, 31, 58, 0.08);
}}
.ft-banner-badge {{
  background: #334155;
  color: #38BDF8 !important;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  text-transform: uppercase;
}}

/* Profile Strip */
.ft-profile-bar {{
  background: {CARD_BG};
  border: 1px solid {BORDER};
  border-radius: 12px;
  padding: 10px 16px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
}}
.ft-profile-info {{
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}}
.ft-profile-name {{
  font-weight: 700;
  color: {NAVY} !important;
  font-size: 0.95rem;
}}
.ft-profile-item {{
  color: {MUTED} !important;
  font-size: 0.82rem;
  display: flex;
  align-items: center;
  gap: 4px;
}}
.ft-profile-tag-ok {{
  background: #DCFCE7;
  color: #15803D !important;
  font-weight: 700;
  font-size: 0.75rem;
  padding: 3px 10px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}}
.ft-profile-tag-warn {{
  background: #FEF3C7;
  color: #B45309 !important;
  font-weight: 700;
  font-size: 0.75rem;
  padding: 3px 10px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}}

/* Chat Bubbles */
.chat-stream {{
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}}
.user-msg {{
  background: linear-gradient(135deg, {TEAL} 0%, #115E59 100%);
  color: #FFFFFF !important;
  padding: 12px 18px;
  border-radius: 18px 18px 4px 18px;
  margin-left: auto;
  max-width: 82%;
  font-size: 0.94rem;
  line-height: 1.45;
  box-shadow: 0 4px 12px rgba(15, 118, 110, 0.18);
  word-break: break-word;
}}
.bot-msg {{
  background: {CARD_BG};
  color: {NAVY} !important;
  padding: 14px 20px;
  border-radius: 18px 18px 18px 4px;
  margin-right: auto;
  max-width: 90%;
  font-size: 0.94rem;
  line-height: 1.5;
  border: 1px solid {BORDER};
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
  word-break: break-word;
}}
.bot-msg * {{
  color: {NAVY} !important;
}}

/* Fact Cards */
.fact-card {{
  background: linear-gradient(135deg, {MINT} 0%, #F0FDFA 100%);
  border: 1px solid {MINT_BORDER};
  border-radius: 12px;
  padding: 12px 16px;
  margin-top: 10px;
  color: {NAVY} !important;
}}
.fact-amt {{
  font-size: 1.5rem;
  font-weight: 800;
  color: {TEAL} !important;
  letter-spacing: -0.02em;
}}

/* Quick Action Suggestion Chips */
.chips-section {{
  margin-top: 14px;
  margin-bottom: 18px;
}}
.chips-title {{
  font-size: 0.85rem;
  font-weight: 700;
  color: {SLATE} !important;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}}
div.stButton > button {{
  background: #FFFFFF !important;
  color: {TEAL} !important;
  border: 1.5px solid #99F6E4 !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
  font-size: 0.84rem !important;
  padding: 0.5rem 0.75rem !important;
  transition: all 0.15s ease-in-out !important;
  box-shadow: 0 1px 3px rgba(15, 118, 110, 0.06) !important;
}}
div.stButton > button:hover {{
  background: {TEAL} !important;
  color: #FFFFFF !important;
  border-color: {TEAL} !important;
  box-shadow: 0 4px 10px rgba(15, 118, 110, 0.2) !important;
  transform: translateY(-1px);
}}

/* Answer X-Ray Card */
.xray-card {{
  background: {CARD_BG};
  border: 1px solid {BORDER};
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.06);
  position: sticky;
  top: 1rem;
}}
.xray-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid {BORDER};
}}
.xray-title {{
  font-size: 1.15rem;
  font-weight: 800;
  color: {NAVY} !important;
  display: flex;
  align-items: center;
  gap: 8px;
}}
.xray-sub {{
  color: {MUTED} !important;
  font-size: 0.78rem;
  font-weight: 500;
}}
.xray-step {{
  background: #F8FAFC;
  border: 1px solid {BORDER};
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 10px;
  color: {NAVY} !important;
  font-size: 0.85rem;
}}
.xray-step strong {{
  color: {TEAL} !important;
  font-weight: 700;
  display: block;
  margin-bottom: 4px;
}}
.xray-step code {{
  background: #EDF2F7;
  color: {NAVY} !important;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.82rem;
  word-break: break-all;
}}
.badge-grounded {{
  background: #DCFCE7;
  color: #15803D !important;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  display: inline-block;
  font-size: 0.8rem;
}}
.badge-warning {{
  background: #FEF3C7;
  color: #B45309 !important;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  display: inline-block;
  font-size: 0.8rem;
}}

/* Chat input styling */
[data-testid="stChatInput"] {{
  padding-bottom: 1rem;
}}
[data-testid="stChatInput"] textarea {{
  border: 1.5px solid {BORDER} !important;
  border-radius: 14px !important;
  background-color: #FFFFFF !important;
  color: {NAVY} !important;
  font-size: 0.95rem !important;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05) !important;
}}
[data-testid="stChatInput"] textarea:focus {{
  border-color: {TEAL} !important;
  box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.15) !important;
}}
[data-testid="stChatInput"] button {{
  color: {TEAL} !important;
}}

/* Fix text contrast in light and dark modes */
.stMarkdown p, .stMarkdown span, .stCaption {{
  color: {NAVY} !important;
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
            f'<div class="fact-card">'
            f'<div class="fact-amt">{_inr(facts["available_balance"])}</div>'
            f'<div style="font-weight: 600; margin-top: 4px;">{acct} Account ···· {last4} · {facts.get("currency", "INR")}</div>'
            f'</div>'
        )
    if intent == "why_balance_change":
        drivers = facts.get("drivers") or []
        lines = " &nbsp;·&nbsp; ".join(
            f"<strong>{d.get('category')}</strong> +{_inr(d.get('delta'))}" for d in drivers
        )
        delta = facts.get("spend_delta", 0)
        return (
            f'<div class="fact-card">'
            f'<div class="fact-amt">+{_inr(delta)}</div>'
            f'<div style="font-weight: 600; margin-top: 2px;">Higher spend vs last month</div>'
            f'<div style="margin-top: 6px; font-size: 0.88rem;">{lines}</div>'
            f'</div>'
        )
    if intent == "spend_drilldown" and "total" in facts:
        category = facts.get("category") or "Total"
        period = facts.get("period", "").replace("_", " ").title()
        extra_parts = []
        if category:
            extra_parts.append(f"Category: <strong>{category}</strong>")
        if period:
            extra_parts.append(f"Period: <strong>{period}</strong>")
        subtext = " · ".join(extra_parts)
        return (
            f'<div class="fact-card">'
            f'<div class="fact-amt">{_inr(facts["total"])}</div>'
            f'<div style="margin-top: 4px; font-size: 0.88rem;">{subtext}</div>'
            f'</div>'
        )
    if intent == "policy_rag":
        titles = ", ".join(facts.get("chunk_titles") or [])
        return (
            f'<div class="fact-card">'
            f'<div style="font-weight: 700; color: {TEAL};">Verified Bank Policy Sources</div>'
            f'<div style="margin-top: 4px; font-size: 0.85rem;">{titles}</div>'
            f'</div>'
        )
    if intent == "loan_eligibility":
        return (
            f'<div class="fact-card">'
            f'<div class="fact-amt">{_inr(facts.get("max_amount", 0))}</div>'
            f'<div style="font-weight: 600; margin-top: 4px;">{facts.get("interest_rate", "")} &nbsp;·&nbsp; {facts.get("reason", "")}</div>'
            f'<div style="margin-top: 4px; font-size: 0.78rem; color: {MUTED};">{facts.get("disclaimer", "")}</div>'
            f'</div>'
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


def _render_profile_bar(customer_id: str, lang: str) -> None:
    profile = get_customer_profile(customer_id)
    if not profile or profile.get("error"):
        return

    name = profile.get("name", customer_id)
    consent_on = profile.get("consent_enabled", False)

    if consent_on:
        status_badge = '<span class="ft-profile-tag-ok">● Consent Active</span>'
        details = (
            f'<span class="ft-profile-item">📍 {profile.get("branch", "Main Branch")}</span>'
            f'<span class="ft-profile-item">📱 {profile.get("masked_phone", "")}</span>'
            f'<span class="ft-profile-item">✉️ {profile.get("masked_email", "")}</span>'
            f'<span class="ft-profile-item">🏦 IFSC: {profile.get("ifsc", "")}</span>'
        )
    else:
        status_badge = '<span class="ft-profile-tag-warn">● Consent Revoked</span>'
        details = f'<span class="ft-profile-item">{t(lang, "profile_consent_off")}</span>'

    st.markdown(
        f'<div class="ft-profile-bar">'
        f'  <div class="ft-profile-info">'
        f'    <span class="ft-profile-name">👤 {name}</span>'
        f'    {details}'
        f'  </div>'
        f'  <div>{status_badge}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _render_xray(lang: str) -> None:
    resp = st.session_state.last_response

    st.markdown(
        f'<div class="xray-card">'
        f'  <div class="xray-header">'
        f'    <div>'
        f'      <div class="xray-title">🔍 {t(lang, "xray_title")}</div>'
        f'      <div class="xray-sub">{t(lang, "sidebar_title")}</div>'
        f'    </div>'
        f'  </div>',
        unsafe_allow_html=True,
    )

    if not resp:
        st.markdown(
            f'<div style="text-align: center; padding: 2.5rem 1rem; color: {MUTED};">'
            f'  <div style="font-size: 2rem; margin-bottom: 8px;">🛡️</div>'
            f'  <div style="font-weight: 600; font-size: 0.95rem; margin-bottom: 4px;">Anti-Hallucination Monitor</div>'
            f'  <div style="font-size: 0.82rem; line-height: 1.4;">{t(lang, "empty_trace")}</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        return

    trace = resp.get("trace") or {}
    entities = resp.get("entities") or {}
    facts = resp.get("facts") or {}
    grounded = bool(trace.get("grounded"))
    latency = trace.get("latency_ms", "—")

    filled_entities = {k: v for k, v in entities.items() if v not in (None, False, "", [])}
    entities_str = html.escape(json.dumps(filled_entities, ensure_ascii=False)) if filled_entities else "None"
    intent = html.escape(str(resp.get("intent") or "—"))
    language = html.escape(str(resp.get("language") or "en")).upper()
    api = html.escape(str(trace.get("api_called") or "None"))
    nlu_src = html.escape(str(trace.get("nlu_source") or "—"))
    data_src = html.escape(str(trace.get("data_source") or "mock"))

    try:
        conf_pct = f"{int(round(float(resp.get('confidence') or 0) * 100))}%"
    except (TypeError, ValueError):
        conf_pct = "—"

    # Step 1
    st.markdown(
        f'<div class="xray-step">'
        f'  <strong>1. {t(lang, "intent")}</strong>'
        f'  Intent: <code>{intent}</code> &nbsp;·&nbsp; Lang: <code>{language}</code><br>'
        f'  {t(lang, "confidence")}: <code>{conf_pct}</code> &nbsp;·&nbsp; {t(lang, "nlu")}: <code>{nlu_src}</code><br>'
        f'  Entities: <code>{entities_str}</code>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Step 2
    st.markdown(
        f'<div class="xray-step">'
        f'  <strong>2. {t(lang, "api")}</strong>'
        f'  Function: <code>{api}</code><br>'
        f'  Data Store: <code>{data_src}</code> &nbsp;·&nbsp; Privacy Masking: <code>Active</code>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Step 3
    st.markdown(
        f'<div class="xray-step">'
        f'  <strong>3. {t(lang, "rows")}</strong>'
        f'  Count: <strong>{trace.get("row_count", 0)}</strong> &nbsp;·&nbsp; '
        f'  {t(lang, "follow_up")}: <code>{trace.get("session_follow_up")}</code>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Step 4
    status_label = t(lang, "grounded") if grounded else t(lang, "not_grounded")
    badge_html = (
        f'<span class="badge-grounded">✅ {status_label}</span>'
        if grounded
        else f'<span class="badge-warning">⚠️ {status_label}</span>'
    )

    st.markdown(
        f'<div class="xray-step">'
        f'  <strong>4. Verification & Speed</strong>'
        f'  {badge_html} &nbsp;·&nbsp; {t(lang, "latency")}: <code>{latency} ms</code>'
        f'</div>',
        unsafe_allow_html=True,
    )

    titles = facts.get("chunk_titles") or facts.get("sources")
    if titles:
        st.markdown(
            f'<div style="font-size: 0.8rem; color: {MUTED}; margin: 8px 0;">'
            f'  <strong>Sources:</strong> {", ".join(map(str, titles))}'
            f'</div>',
            unsafe_allow_html=True,
        )

    if facts:
        with st.expander(f"📦 {t(lang, 'facts')} (JSON)", expanded=False):
            st.json(facts)

    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(
        page_title="FinTrace — AI Banking Assistant",
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _init_state()
    st.markdown(CSS, unsafe_allow_html=True)

    lang = st.session_state.ui_language

    # Sidebar controls
    with st.sidebar:
        st.markdown(
            f'<div class="ft-sidebar-brand">'
            f'  <div class="ft-logo">F</div>'
            f'  <div>'
            f'    <div class="ft-sidebar-name">FinTrace</div>'
            f'    <div class="ft-sidebar-sub">{t(lang, "header_sub")}</div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.selectbox(
            t(lang, "lang"),
            options=["en", "hi", "kn"],
            format_func=lambda c: {"en": "🇬🇧 English", "hi": "🇮🇳 हिन्दी", "kn": "🇮🇳 ಕನ್ನಡ"}[c],
            key="ui_language",
        )

        st.selectbox(
            t(lang, "customer"),
            options=["CUST001", "CUST002"],
            format_func=lambda c: "CUST001 · Aarav Sharma (Consent On)"
            if c == "CUST001"
            else "CUST002 · Meera Nair (Consent Off)",
            key="customer_id",
        )

        if st.button(
            t(lang, "analyze"),
            help=t(lang, "analyze_hint"),
            use_container_width=True,
        ):
            st.session_state.pending_query = "Analyze my transactions"

        st.divider()

        if st.button("🔄 Reset Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.last_response = None
            st.session_state.pending_query = None
            st.rerun()

    # Top Banner
    st.markdown(
        f'<div class="ft-banner">'
        f'  <span class="ft-banner-badge">Demo</span>'
        f'  <span>{t(lang, "banner")}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Customer Profile Bar
    _render_profile_bar(st.session_state.customer_id, lang)

    # Balanced 2-Column Cockpit Layout
    col_chat, col_xray = st.columns([1.28, 0.72], gap="large")

    with col_chat:
        # Chat Messages
        st.markdown('<div class="chat-stream">', unsafe_allow_html=True)
        if not st.session_state.messages:
            st.markdown(
                f'<div class="bot-msg">'
                f'  <strong>{t(lang, "welcome")}</strong><br><br>'
                f'  {t(lang, "welcome_body")}<br><br>'
                f'  <em>{t(lang, "welcome_ask")}</em>'
                f'</div>',
                unsafe_allow_html=True,
            )

        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="user-msg">{html.escape(msg["content"])}</div>',
                    unsafe_allow_html=True,
                )
            else:
                card = _render_facts(msg.get("facts") or {}, msg.get("intent") or "")
                content = html.escape(msg.get("content", ""))
                st.markdown(
                    f'<div class="bot-msg">'
                    f'  {content}'
                    f'  {card}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

        # Quick Action Suggestion Chips in a clean 3x2 grid
        st.markdown(f'<div class="chips-title">💡 {t(lang, "chips_label")}</div>', unsafe_allow_html=True)
        chips = [
            "chip_balance",
            "chip_txns",
            "chip_loan",
            "chip_upi",
            "chip_why",
            "chip_rates",
        ]
        row1 = st.columns(3)
        row2 = st.columns(3)
        for i, key in enumerate(chips[:3]):
            with row1[i]:
                if st.button(t(lang, key), key=f"chip_{key}", use_container_width=True):
                    st.session_state.pending_query = CHIP_QUERIES[lang][key]

        for i, key in enumerate(chips[3:]):
            with row2[i]:
                if st.button(t(lang, key), key=f"chip_{key}", use_container_width=True):
                    st.session_state.pending_query = CHIP_QUERIES[lang][key]

        # Chat Input
        typed = st.chat_input(t(lang, "placeholder"))
        query = st.session_state.pending_query or typed
        if query:
            st.session_state.pending_query = None
            _send(query)
            st.rerun()

    with col_xray:
        _render_xray(lang)


if __name__ == "__main__":
    main()
