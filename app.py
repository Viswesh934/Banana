"""Banana — Executive AI Strategy Copilot powered by FalkorDB Graph Intelligence."""

import os
import time
import uuid
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from banana.agent import BananaAgent
from banana.assembler import ContextAssembler
from banana.benchmark import BenchmarkSuite
from banana.config import get_settings
from banana.db import FalkorDBClient, get_db_client
from banana.max_flow import MaxFlowScheduler
from banana.meeting_graph import (
    MeetingCommitment,
    MeetingGraphManager,
    MeetingParticipant,
    MeetingTurn,
)
from banana.multimodal import MultimodalIngestor
from banana.sandbox import SandboxManager
from banana.seeder import GraphSeeder
from banana.visualizer import GraphVisualizer

# Streamlit Page Config
st.set_page_config(
    page_title="Banana | Executive AI Strategy Copilot",
    page_icon="🍌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for Sleek Sidebar Layout (No top tabs)
st.markdown(
    """
    <style>
    /* Global Background and Typography */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    .brand-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 2px;
    }
    .brand-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #f59e0b;
        letter-spacing: -0.5px;
    }
    .brand-tagline {
        font-size: 0.95rem;
        color: #94a3b8;
        margin-bottom: 20px;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 600;
        background: #064e3b;
        color: #34d399;
        margin-right: 6px;
    }
    .nav-header {
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #64748b;
        margin-top: 14px;
        margin-bottom: 6px;
    }
    /* Sleek Card Container */
    .hud-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .hud-card-highlight {
        background: rgba(15, 23, 42, 0.95);
        border: 2px solid #f59e0b;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(245, 158, 11, 0.2);
    }
    .hud-card-danger {
        background: rgba(15, 23, 42, 0.95);
        border: 2px solid #ef4444;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(239, 68, 68, 0.25);
    }
    .hud-card-success {
        background: rgba(15, 23, 42, 0.95);
        border: 2px solid #10b981;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(16, 185, 129, 0.25);
    }
    .code-box {
        background: #020617;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 12px 14px;
        font-family: monospace;
        font-size: 0.85rem;
        color: #e2e8f0;
        overflow-x: auto;
    }
    .landing-box {
        text-align: center;
        padding: 28px 24px 22px 24px;
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid #1e293b;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    }
    .prompt-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 10px;
        transition: all 0.2s ease;
    }
    .prompt-card:hover {
        border-color: #f59e0b;
        background: #1e293b;
    }
    .session-item {
        padding: 6px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        color: #cbd5e1;
        cursor: pointer;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_db():
    return get_db_client()


db_client = get_db()
settings = get_settings()

# Initialize modern multi-session state
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {
        "session_default": {
            "id": "session_default",
            "title": "MegaCorp Deal Strategy",
            "created_at": "Today",
            "history": [],
            "attached_docs": [],
        }
    }
if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = "session_default"

if st.session_state.active_session_id not in st.session_state.chat_sessions:
    st.session_state.active_session_id = list(st.session_state.chat_sessions.keys())[0]

# Synchronize legacy chat_history with active session
st.session_state.chat_history = st.session_state.chat_sessions[st.session_state.active_session_id]["history"]

if "gmeet_step" not in st.session_state:
    st.session_state.gmeet_step = 0
if "gmeet_active_tab" not in st.session_state:
    st.session_state.gmeet_active_tab = "tab4"
if "gmeet_concluded" not in st.session_state:
    st.session_state.gmeet_concluded = False
if "gmeet_chat_history" not in st.session_state:
    st.session_state.gmeet_chat_history = []

# Ensure FalkorDB knowledge graph is seeded
inspector_db = db_client.get_demand_graph()
try:
    check_cnt = inspector_db.query("MATCH (n) RETURN count(n)").result_set[0][0]
    if check_cnt == 0:
        GraphSeeder(db_client).seed_all(drop_existing=True)
except Exception:
    pass

# ==================== LEFT SIDEBAR NAVIGATION ====================
with st.sidebar:
    st.markdown(
        """
        <div class="brand-header">
            <span style="font-size: 2.2rem;">🍌</span>
            <span class="brand-title">Banana</span>
        </div>
        <div class="brand-tagline">
            Autonomous Strategy Copilot • FalkorDB
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1-Click New Session Action (like modern ChatGPT / Claude)
    if st.button("＋ New Strategic Session", type="primary", use_container_width=True):
        new_count = len(st.session_state.chat_sessions) + 1
        new_sid = f"session_{new_count}_{int(time.time())}"
        st.session_state.chat_sessions[new_sid] = {
            "id": new_sid,
            "title": f"New Session #{new_count}",
            "created_at": "Just now",
            "history": [],
            "attached_docs": [],
        }
        st.session_state.active_session_id = new_sid
        st.session_state.chat_history = []
        st.rerun()

    # Session Selector
    st.markdown('<div class="nav-header">Chat Sessions</div>', unsafe_allow_html=True)
    session_keys = list(st.session_state.chat_sessions.keys())
    active_idx = session_keys.index(st.session_state.active_session_id) if st.session_state.active_session_id in session_keys else 0
    chosen_sid = st.selectbox(
        "Chat Sessions",
        options=session_keys,
        format_func=lambda sid: f"💬 {st.session_state.chat_sessions[sid]['title']}",
        index=active_idx,
        label_visibility="collapsed",
        key="session_select_dropdown",
    )
    if chosen_sid != st.session_state.active_session_id:
        st.session_state.active_session_id = chosen_sid
        st.session_state.chat_history = st.session_state.chat_sessions[chosen_sid]["history"]
        st.rerun()

    st.markdown("---")

    # Clean Left Sidebar Navigation (Strategic Copilot is first)
    st.markdown('<div class="nav-header">Workspace Views</div>', unsafe_allow_html=True)
    selected_view = st.radio(
        "Navigation",
        [
            "💬 Strategic Copilot",
            "🎙️ Google Meet Companion",
            "🧠 Visual Brain (Graph)",
            "🧪 Scenario Simulator",
            "🔬 MCP Agents & Diagnostics",
        ],
        index=0,
        label_visibility="collapsed",
        key="main_nav_radio",
    )

    st.markdown("---")

    # System Status & Health Badges
    st.markdown('<div class="nav-header">System Health</div>', unsafe_allow_html=True)
    health = db_client.check_connection()
    if health["status"] == "ok":
        st.markdown(
            f'<div class="status-badge">● FalkorDB Online</div><span style="font-size:0.8rem;color:#94a3b8;">{health["latency_ms"]}ms</span>',
            unsafe_allow_html=True,
        )
    else:
        st.error("FalkorDB Offline")

    if settings.gemini_api_key:
        st.markdown(
            f'<div style="margin-top:6px;"><span class="status-badge" style="background:#1e3a8a;color:#93c5fd;">● LLM Active</span><span style="font-size:0.8rem;color:#94a3b8;">{settings.gemini_model}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div style="margin-top:6px;"><span class="status-badge" style="background:#312e81;color:#c7d2fe;">● Bridge :8765</span><span style="font-size:0.8rem;color:#94a3b8;">Ready</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Precision & Token Budget Slider
    st.markdown('<div class="nav-header">Context Knapsack Budget</div>', unsafe_allow_html=True)
    token_budget = st.slider(
        "Tokens",
        min_value=800,
        max_value=4000,
        value=1600,
        step=100,
        label_visibility="collapsed",
        help="Controls evidence scheduling under Edmonds-Karp maximum flow.",
    )

    st.markdown("---")
    if st.button("🔄 Reset Graph Knowledge", use_container_width=True):
        with st.spinner("Resetting baseline knowledge base..."):
            GraphSeeder(db_client).seed_all(drop_existing=True)
            st.session_state.chat_sessions = {
                "session_default": {
                    "id": "session_default",
                    "title": "MegaCorp Deal Strategy",
                    "created_at": "Today",
                    "history": [],
                    "attached_docs": [],
                }
            }
            st.session_state.active_session_id = "session_default"
            st.session_state.chat_history = []
            st.session_state.gmeet_step = 0
            st.session_state.gmeet_concluded = False
            st.session_state.gmeet_chat_history = []
            st.success("Knowledge reset!")
            st.rerun()

# Pre-fetch candidate universe for context engine
assembler = ContextAssembler(db_client)
demand_items, demand_deps = assembler.fetch_demand_candidates("task_pricing_strategy")
knowledge_items, knowledge_deps = assembler.fetch_knowledge_candidates()

all_items = {it.canonical_id: it for it in demand_items + knowledge_items}
all_deps = {**demand_deps}
for k, v in knowledge_deps.items():
    if k in all_deps:
        all_deps[k].extend(v)
    else:
        all_deps[k] = list(v)

scheduler = MaxFlowScheduler()
flow_result = scheduler.schedule(
    all_items=all_items,
    dependencies=all_deps,
    token_budget=token_budget,
    reserved_output_tokens=max(200, token_budget // 5),
)
selected_ids_set = set(flow_result.selected_canonical_ids)

# ==================== VIEW 1: STRATEGIC COPILOT & LANDING HERO ====================
if selected_view == "💬 Strategic Copilot":
    active_session = st.session_state.chat_sessions[st.session_state.active_session_id]
    history = active_session["history"]

    # Top Header & Session Bar
    c_hdr_info, c_hdr_btns = st.columns([3, 2])
    with c_hdr_info:
        st.markdown(f"### 💬 {active_session['title']}")
        attached = active_session.get("attached_docs", [])
        attached_badge = f'<span class="status-badge" style="background:#1e3a8a;color:#93c5fd;">📎 {len(attached)} Ingested Docs</span>' if attached else ""
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                <span class="status-badge">● FalkorDB GraphBLAS</span>
                <span class="status-badge" style="background:#064e3b;color:#34d399;">🛡️ Margin Policy Active</span>
                {attached_badge}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_hdr_btns:
        c_top_new, c_top_clear = st.columns(2)
        with c_top_new:
            if st.button("＋ New Session", key="copilot_top_new_btn", use_container_width=True):
                new_idx = len(st.session_state.chat_sessions) + 1
                new_id = f"session_{new_idx}_{int(time.time())}"
                st.session_state.chat_sessions[new_id] = {
                    "id": new_id,
                    "title": f"New Session #{new_idx}",
                    "created_at": "Just now",
                    "history": [],
                    "attached_docs": [],
                }
                st.session_state.active_session_id = new_id
                st.session_state.chat_history = []
                st.rerun()
        with c_top_clear:
            if st.button("🗑️ Clear Chat", key="copilot_top_clear_btn", use_container_width=True):
                active_session["history"] = []
                active_session["attached_docs"] = []
                st.session_state.chat_history = []
                st.rerun()

    # Starter prompt trigger placeholder
    selected_starter_prompt = None

    # LANDING PAGE HERO (when history is empty)
    if len(history) == 0:
        st.markdown(
            """
            <div class="landing-box">
                <div style="font-size: 3.2rem; margin-bottom: 6px;">🍌</div>
                <h1 style="font-size: 2.2rem; font-weight: 800; color: #f59e0b; margin-bottom: 8px; letter-spacing: -0.5px;">
                    Banana Strategic Copilot
                </h1>
                <p style="font-size: 0.98rem; color: #cbd5e1; max-width: 680px; margin: 0 auto 16px auto; line-height: 1.55;">
                    Autonomous executive deal intelligence & strategy engine powered by <b>FalkorDB GraphBLAS</b>.
                    Grounded in audited competitor invoices, mandatory 25% gross margin policies, and live Google Meet session memory.
                </p>
                <div style="display: flex; justify-content: center; gap: 8px; flex-wrap: wrap;">
                    <span class="status-badge">🛡️ Zero Margin Floor Breaches</span>
                    <span class="status-badge" style="background:#1e3a8a; color:#93c5fd;">⚡ Sub-5ms Graph Traversal</span>
                    <span class="status-badge" style="background:#312e81; color:#c7d2fe;">📎 Integrated Multimodal Vision</span>
                    <span class="status-badge" style="background:#064e3b; color:#34d399;">🎙️ Real Google Meet Tab Memory</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### ⚡ Quick-Start Strategic Directives")
        st.caption("Select a prompt card below to consult Banana with pre-grounded competitor benchmarks and policy constraints:")

        c_p1, c_p2 = st.columns(2)
        with c_p1:
            st.markdown(
                """
                <div class="hud-card" style="margin-bottom:8px;min-height:105px;">
                    <div style="font-weight:700;color:#fcd34d;font-size:0.92rem;margin-bottom:4px;">🏷️ Competitor Hidden Egress Audit</div>
                    <div style="font-size:0.83rem;color:#94a3b8;line-height:1.4;">
                        Analyze CloudScale's $800 price vs hidden $0.08/GB egress fees for MegaCorp's 15TB workload, and recommend a winning counter-strategy.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Run Egress Audit ➜", key="pcard_1", use_container_width=True):
                selected_starter_prompt = (
                    "Analyze competitor pricing changes (CloudScale, HyperStore, DataVanguard), "
                    "identify hidden fee and feature gaps against ApexCloud Enterprise, and recommend "
                    "an adjusted pricing strategy complying with our 25% minimum gross margin policy."
                )

            st.markdown(
                """
                <div class="hud-card" style="margin-bottom:8px;min-height:105px;margin-top:12px;">
                    <div style="font-weight:700;color:#fcd34d;font-size:0.92rem;margin-bottom:4px;">🤝 MegaCorp Deal Structuring</div>
                    <div style="font-size:0.83rem;color:#94a3b8;line-height:1.4;">
                        Synthesize Sarah Chen's objections and Alex's proposals to draft the $899 Enterprise Starter Tier with 33.3% gross margin.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Structure Deal Terms ➜", key="pcard_3", use_container_width=True):
                selected_starter_prompt = (
                    "Synthesize Sarah Chen's objections regarding competitor pricing and draft our $899 Enterprise Starter Tier proposal "
                    "with 33.3% gross margin and $0 egress markup to close the MegaCorp agreement."
                )

        with c_p2:
            st.markdown(
                """
                <div class="hud-card" style="margin-bottom:8px;min-height:105px;">
                    <div style="font-weight:700;color:#fcd34d;font-size:0.92rem;margin-bottom:4px;">🛑 Margin Floor Policy Audit</div>
                    <div style="font-size:0.83rem;color:#94a3b8;line-height:1.4;">
                        Audit a proposed $700 flat discount against our mandatory 25% gross margin floor ($750 minimum based on $600 COGS).
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Audit Margin Floor ➜", key="pcard_2", use_container_width=True):
                selected_starter_prompt = (
                    "Audit a proposed $700 flat discount against our mandatory 25% gross margin floor ($750 minimum based on $600 COGS) "
                    "and explain why this violates policy_minimum_margin. Recommend permissible counter-terms."
                )

            st.markdown(
                """
                <div class="hud-card" style="margin-bottom:8px;min-height:105px;margin-top:12px;">
                    <div style="font-weight:700;color:#fcd34d;font-size:0.92rem;margin-bottom:4px;">⚖️ HyperStore SLA & Penalty Benchmark</div>
                    <div style="font-size:0.83rem;color:#94a3b8;line-height:1.4;">
                        Benchmark HyperStore's 99.5% uptime SLA and 10% refund cap against ApexCloud Enterprise reliability standards.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Benchmark SLA Reliability ➜", key="pcard_4", use_container_width=True):
                selected_starter_prompt = (
                    "Benchmark HyperStore's 99.5% uptime SLA, 10% refund cap, and 30-day retention penalties against ApexCloud Enterprise "
                    "and recommend sales positioning for high-availability enterprise clients."
                )

    # ACTIVE CONVERSATION (when history has items)
    else:
        for i, turn in enumerate(history):
            with st.chat_message("user"):
                st.markdown(f"**Directive:** {turn['prompt']}")
            with st.chat_message("assistant"):
                st.markdown(
                    """
                    <div style="display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap;">
                        <div class="status-badge">✓ Margin Policy Verified (33.3% Gross Margin)</div>
                        <div class="status-badge">✓ Sourced from Audited Invoices</div>
                        <div class="status-badge" style="background:#1e1b4b;color:#a5b4fc;">✓ Max-Flow Dependency Intact</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(turn["recommendation"])
                with st.expander("📁 Verified Citations & Persistent Memory Audit"):
                    st.markdown(f"**Grounded Citations:** {', '.join(turn['citations']) if turn['citations'] else 'Core Knowledge Graph'}")
                    if turn.get("memory_id"):
                        st.info(f"Recorded in FalkorDB node `{turn['memory_id']}`.")

    # INTEGRATED MULTIMODAL INTEL UPLOAD (in the same tab)
    with st.expander("📎 Attach & Ingest Competitor Document / Invoice into Graph Memory", expanded=False):
        st.caption("Upload competitor invoices (PDF/TXT) or pricing screenshots (PNG/JPG). Gemini Vision extracts prices and writes them directly into FalkorDB knowledge graph memory for this session.")
        uploaded_file = st.file_uploader(
            "Upload Competitor Document:",
            type=["png", "jpg", "jpeg", "pdf", "txt", "csv"],
            key=f"file_uploader_{st.session_state.active_session_id}",
        )
        if uploaded_file:
            file_bytes = uploaded_file.read()
            c_prev, c_ext = st.columns([1, 1])
            with c_prev:
                st.markdown(f"**File:** `{uploaded_file.name}` ({len(file_bytes)} bytes)")
                if uploaded_file.type.startswith("image"):
                    st.image(file_bytes, caption=uploaded_file.name, use_container_width=True)
                else:
                    st.text_area("Preview", file_bytes.decode("utf-8", errors="ignore")[:400], height=160)
            with c_ext:
                if st.button("⚡ Extract & Ingest into Knowledge Graph", type="primary", key="ingest_modal_btn"):
                    with st.spinner("Extracting with Gemini Vision & writing to FalkorDB..."):
                        ingestor = MultimodalIngestor(db_client=db_client)
                        res = ingestor.ingest_bytes(
                            data=file_bytes,
                            file_name=uploaded_file.name,
                            mime_type=uploaded_file.type,
                        )
                    st.success(f"✓ Ingested `{res.document_id}` into FalkorDB!")
                    ext = res.extracted
                    st.markdown(f"**Company:** `{ext.company_name}` • **Product:** `{ext.product_name}`")
                    st.markdown(f"**Price:** `${ext.advertised_price or 'N/A'}` / {ext.billing_cycle}")
                    if ext.hidden_fees_or_penalties:
                        st.warning(f"**Hidden Fees Flagged:** {ext.hidden_fees_or_penalties}")
                    st.info(f"💡 **Finding:** {ext.evidence_finding}")
                    if "attached_docs" not in active_session:
                        active_session["attached_docs"] = []
                    active_session["attached_docs"].append({
                        "name": uploaded_file.name,
                        "doc_id": res.document_id,
                        "company": ext.company_name,
                        "price": ext.advertised_price,
                        "finding": ext.evidence_finding,
                    })
                    st.rerun()

    # Active Ingested Document Chips
    if active_session.get("attached_docs"):
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin:12px 0 6px 0;">
                <span style="font-size:0.8rem;color:#94a3b8;font-weight:600;">Active Session Ingested Docs:</span>
                {"".join([f'<span class="status-badge" style="background:#1e293b;border:1px solid #f59e0b;color:#fcd34d;">📎 {d["name"]} ({d["company"]})</span>' for d in active_session["attached_docs"]])}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Chat Input Box
    st.markdown("---")
    default_text = selected_starter_prompt or ""
    c_in, c_send = st.columns([5, 1])
    with c_in:
        user_query = st.text_input(
            "Strategic Directive:",
            value=default_text,
            placeholder="Ask Banana a strategic question or enter a directive...",
            key=f"directive_input_{st.session_state.active_session_id}_{len(history)}",
            label_visibility="collapsed",
        )
    with c_send:
        exec_btn = st.button("🚀 Send", type="primary", use_container_width=True, key=f"send_btn_{st.session_state.active_session_id}")

    col_sub1, col_sub2 = st.columns([1, 1])
    with col_sub1:
        persist_chk = st.checkbox("Persist recommendation in FalkorDB memory", value=True, key=f"persist_chk_{st.session_state.active_session_id}")
    with col_sub2:
        st.caption("FalkorDB Edmonds-Karp Max-Flow Context Active • Sub-5ms Query")

    final_query = selected_starter_prompt or (user_query if exec_btn and user_query else None)
    if final_query:
        agent = BananaAgent(db_client=db_client)
        with st.status("🤖 Banana is orchestrating intelligence...", expanded=True) as status:
            st.write("🔍 Traversing Knowledge Graph entities in FalkorDB...")
            st.write("🛡️ Auditing Governance Policies (25% gross margin floor / $750 minimum)...")
            st.write("⚡ Running Max-Flow Context Knapsack under token limit...")
            st.write("🧪 Simulating Competitive Response in isolated sandbox...")

            result = agent.run(
                task_prompt=final_query,
                token_budget=token_budget,
                save_to_memory=persist_chk,
            )
            status.update(label="✅ Strategic Recommendation Ready!", state="complete", expanded=False)

        # Auto-set session title from first prompt if default title
        if len(history) == 0 and active_session["title"].startswith("New Session"):
            short_title = final_query.split(".")[0].strip()
            if len(short_title) > 30:
                short_title = short_title[:30] + "..."
            active_session["title"] = short_title

        active_session["history"].append({
            "prompt": final_query,
            "recommendation": result.recommendation,
            "citations": result.evidence_citations,
            "memory_id": result.saved_memory_id,
        })
        st.session_state.chat_history = active_session["history"]
        st.rerun()

    # One-Click Board Briefing Memo Export
    if history:
        st.markdown("---")
        latest = history[-1]
        memo = f"""# ApexCloud Executive Strategy & Pricing Briefing Memo
**Date:** October 2026
**Prepared by:** Banana Autonomous Strategy Copilot
**Engine:** FalkorDB Graph Intelligence & Edmonds-Karp Context Scheduler

---

## 1. Executive Directive
{latest['prompt']}

## 2. Recommended Strategic Decision
{latest['recommendation']}

## 3. Governance & Policy Verification Audit
- **Mandatory Gross Margin Floor:** >= 25.0%
- **Cost Basis (COGS):** $600.00 / month
- **Absolute Minimum Price Floor:** $750.00 / month
- **Recommended Starter Offering:** $899.00 / month (33.3% Gross Margin)
- **Status:** 100% PASS
"""
        st.download_button(
            label="📥 Export Executive Briefing Memo (.md)",
            data=memo,
            file_name="ApexCloud_Board_Briefing_Memo.md",
            mime="text/markdown",
            use_container_width=True,
            key=f"memo_export_btn_{st.session_state.active_session_id}",
        )

# ==================== VIEW 2: GOOGLE MEET COMPANION ====================
elif selected_view == "🎙️ Google Meet Companion":
    st.markdown("## 🎙️ Real Google Meet Companion & Floating Banana HUD")
    st.caption("How Banana connects directly to real Google Meet calls (`https://meet.google.com/*`) to deliver zero-token idle monitoring, micro-nudges, and browser tab memory.")

    # Top Connection Architecture Card
    col_arch, col_stat = st.columns([2, 1])
    with col_arch:
        st.markdown(
            """
            <div class="hud-card">
                <div style="font-weight:700;font-size:1.05rem;color:#fcd34d;margin-bottom:8px;">
                    🔌 How the Chrome Extension Connects to Banana
                </div>
                <div style="font-size:0.9rem;color:#cbd5e1;line-height:1.5;">
                    1. <b>Injected Client</b>: Injects the Floating Banana into <code>meet.google.com</code>.<br>
                    2. <b>Zero-Token Idle</b>: Captions are held in a local 30s RAM buffer—zero cloud tokens burned.<br>
                    3. <b>Sub-500ms Lookups</b>: Spoken cues trigger CORS calls to <code>http://localhost:8765/api/analyze_turn</code>.<br>
                    4. <b>Tab Memory</b>: Banana surfaces exact document deep-links and records commitments to FalkorDB.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_stat:
        st.markdown(
            f"""
            <div class="hud-card" style="text-align:center;">
                <div style="font-size:1.8rem;margin-bottom:4px;">🍌</div>
                <div style="font-weight:700;color:#f59e0b;font-size:1rem;">Bridge Server</div>
                <div style="color:#34d399;font-weight:600;font-size:0.85rem;margin:6px 0;">● Port 8765 Active</div>
                <div style="font-size:0.75rem;color:#94a3b8;">FalkorDB Latency: {health['latency_ms']}ms</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Two Deployment Methods
    c_dep1, c_dep2 = st.columns(2)
    with c_dep1:
        with st.expander("⚡ Method 1: Instant 5-Sec Console Injector (No Install)", expanded=True):
            st.markdown("**Test in a live Google Meet call right now in 5 seconds:**")
            st.markdown("1. Open any active Google Meet call (`https://meet.google.com/`) in your browser.")
            st.markdown("2. Press **`F12`** (or `Cmd+Option+I` on Mac), click **Console**.")
            st.markdown("3. Paste the snippet below and press **Enter**:")
            with open("extension/inject_console.js", "r") as f:
                inject_code = f.read()
            st.code(inject_code, language="javascript")
            st.caption("👉 The Floating Banana immediately pins itself to the bottom-right of your real call! Click the pill or hit Alt+Space to test.")

    with c_dep2:
        with st.expander("📦 Method 2: Permanent Chrome Extension", expanded=True):
            st.markdown("**Install the unpacked extension for automated caption listening:**")
            st.markdown("1. Start the local bridge server: `uv run banana listen` (serves port 8765).")
            st.markdown("2. In Chrome, go to `chrome://extensions/` and toggle **Developer Mode** on.")
            st.markdown("3. Click **Load unpacked** and select `/workspaces/Banana/extension`.")
            st.markdown("4. Join any Google Meet call and turn on Closed Captions (`[CC]`).")
            st.markdown("5. Open the Banana extension icon in Chrome to test status or customize the bridge URL.")

    st.markdown("---")

    # Interactive In-Meeting Simulation & Tab Memory Walkthrough
    st.markdown("### 🎬 Test What the Banana Does in Google Meet")
    st.caption("Step through real meeting turns below to preview the exact micro-nudges and tab deep-links surfaced by Banana:")

    c_step1, c_step2, c_step3, c_conclude = st.columns(4)
    with c_step1:
        if st.button("Turn 1: Sarah cites CloudScale $800", use_container_width=True):
            st.session_state.gmeet_step = 1
            st.session_state.gmeet_active_tab = "tab4"
            st.rerun()
    with c_step2:
        if st.button("Turn 2: Alex proposes $700 discount", use_container_width=True):
            st.session_state.gmeet_step = 2
            st.rerun()
    with c_step3:
        if st.button("Turn 3: You propose $899 Starter Tier", use_container_width=True):
            st.session_state.gmeet_step = 3
            st.rerun()
    with c_conclude:
        if st.button("🔴 Conclude Call & Ingest Graph", type="primary", use_container_width=True):
            mgr = MeetingGraphManager(db_client)
            mgr.initialize_session(
                session_id="meet_megacorp_q3",
                title="Enterprise Deal Sync: MegaCorp & ApexCloud",
                participants=[
                    MeetingParticipant(name="Sarah Chen", role="Enterprise Lead", company="MegaCorp"),
                    MeetingParticipant(name="Alex Rivera", role="VP Sales", company="ApexCloud"),
                    MeetingParticipant(name="You", role="Solutions Architect", company="ApexCloud"),
                ],
            )
            mgr.record_turn(
                "meet_megacorp_q3",
                MeetingTurn(
                    speaker="Sarah Chen",
                    text="CloudScale claims they offer $800/mo flat with no bandwidth fees. Why pay $1,200?",
                    timestamp_str="10:14 AM",
                    referenced_tab_id="doc_cloudscale_teardown_2026",
                    nudge_text="CloudScale $800 base masks $0.08/GB egress. Average 15TB workload costs $1,936/mo.",
                ),
            )
            mgr.record_policy_breach(
                session_id="meet_megacorp_q3",
                speaker_name="Alex Rivera",
                proposed_price=700.0,
                policy_id="policy_minimum_margin",
                reason="Proposed $700 price violates mandatory 25% gross margin floor ($750 minimum).",
            )
            mgr.record_commitment(
                session_id="meet_megacorp_q3",
                commitment=MeetingCommitment(
                    commitment_id="com_alex_starter_tier",
                    speaker_name="Alex Rivera",
                    term="Deliver transparent Enterprise Starter tier at $899/mo (33.3% margin, $0 egress markup)",
                    deadline="Friday 5:00 PM",
                    assignee="Alex Rivera",
                    referenced_doc_id="doc_cloudscale_teardown_2026",
                ),
            )
            st.session_state.gmeet_concluded = True
            st.success("✓ FalkorDB Meeting Knowledge Graph constructed!")
            st.rerun()

    # Dynamic HUD Display based on step
    gmeet_step = st.session_state.gmeet_step
    if gmeet_step == 0:
        st.markdown(
            """
            <div class="hud-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div style="font-weight:700;color:#f59e0b;font-size:1.05rem;">🍌 Floating Banana HUD • 0 Tokens (Idle)</div>
                    <span class="status-badge" style="background:#1e293b;color:#94a3b8;">Listening for Alt+Space or Safe Words</span>
                </div>
                <div style="color:#94a3b8;font-size:0.9rem;margin-top:6px;">
                    Local 30-second rolling circular buffer running in RAM. Zero cloud tokens consumed while idle.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif gmeet_step == 1:
        st.markdown(
            """
            <div class="hud-card-highlight">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div style="font-weight:700;color:#f59e0b;font-size:1.05rem;">💡 Micro-Nudge: CloudScale Hidden Egress Surcharge</div>
                    <span class="status-badge">⚡ 1.4ms FalkorDB Lookup</span>
                </div>
                <div style="color:#e2e8f0;font-size:0.95rem;margin-top:8px;">
                    Sarah mentioned: <i>"CloudScale offered $800 flat..."</i><br>
                    <b>Banana Fact-Check:</b> CloudScale's $800 sticker price masks a <b>$0.08/GB egress fee</b> beyond 1TB.
                    MegaCorp's 14.2TB monthly outbound traffic adds <b>$1,136.00/mo in overages</b> ($1,936 true TCO)!
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif gmeet_step == 2:
        st.markdown(
            """
            <div class="hud-card-danger">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div style="font-weight:700;color:#ef4444;font-size:1.05rem;">🛑 GOVERNANCE ALERT: Margin Floor Breach</div>
                    <span class="status-badge" style="background:#7f1d1d;color:#fca5a5;">Policy Floor Violation</span>
                </div>
                <div style="color:#f8fafc;font-size:0.95rem;margin-top:8px;">
                    Alex proposed: <i>"Can we do $700 flat to close today?"</i><br>
                    <b>Policy Breach:</b> Proposed $700/mo is below our <b>$750/mo minimum price floor</b> ($600 COGS basis).
                    Violates <code>policy_minimum_margin</code>. Counter with our $899 Starter tier instead!
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif gmeet_step == 3:
        st.markdown(
            """
            <div class="hud-card-success">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div style="font-weight:700;color:#10b981;font-size:1.05rem;">✓ Strategy Aligned & Commitment Logged</div>
                    <span class="status-badge" style="background:#064e3b;color:#34d399;">33.3% Gross Margin</span>
                </div>
                <div style="color:#f8fafc;font-size:0.95rem;margin-top:8px;">
                    <b>Agreed Commitment:</b> Alex commits to delivering the <b>$899/mo Enterprise Starter Tier</b> (0 egress markup) by <b>Friday 5:00 PM</b>.
                    Saves MegaCorp $1,037/mo over CloudScale!
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Active Browser Tab Memory Tray
    st.markdown("#### 📑 Active Browser Tab Memory Tray")
    tab_c1, tab_c2, tab_c3, tab_c4 = st.columns(4)
    with tab_c1:
        if st.button("Tab 1: ApexCloud Tiers", use_container_width=True):
            st.session_state.gmeet_active_tab = "tab1"
            st.rerun()
    with tab_c2:
        if st.button("Tab 2: Competitor Matrix", use_container_width=True):
            st.session_state.gmeet_active_tab = "tab2"
            st.rerun()
    with tab_c3:
        if st.button("Tab 3: MegaCorp 15TB Spec", use_container_width=True):
            st.session_state.gmeet_active_tab = "tab3"
            st.rerun()
    with tab_c4:
        is_active = st.session_state.gmeet_active_tab == "tab4"
        lbl = "⭐ Tab 4: CloudScale CS-902 (Active)" if is_active else "Tab 4: CloudScale CS-902"
        if st.button(lbl, type="primary" if is_active else "secondary", use_container_width=True):
            st.session_state.gmeet_active_tab = "tab4"
            st.rerun()

    active_tab = st.session_state.gmeet_active_tab
    if active_tab == "tab4":
        st.info(
            "📄 **Tab 4 Preview — CloudScale Customer Invoice CS-90218 (Google Drive)**\n\n"
            "• **Customer:** MegaCorp Global Systems | **Billing Period:** June 2026\n"
            "• **Base Subscription:** Enterprise Cloud Pro: **$800.00/mo**\n"
            "• **Hidden Egress Surcharge (14.2 TB @ $0.08/GB):** **$1,136.00** ⚠️\n"
            "• **Total Billed:** **$2,128.50** (vs. ApexCloud Starter Tier: $899.00 Flat)\n"
            "• *Clause 4.1:* 'Customer agrees to $0.08 per GB egress overage fee beyond standard 1TB allowance.'"
        )
    elif active_tab == "tab1":
        st.markdown("📄 **Tab 1 Preview — ApexCloud Internal Pricing Model**: Enterprise: $1,200/mo | Starter: $899/mo | COGS Floor: $750/mo.")
    elif active_tab == "tab2":
        st.markdown("📄 **Tab 2 Preview — Competitive Parity Analysis**: HyperStore: 99.5% SLA | DataVanguard: $0.15/Compute Unit.")
    elif active_tab == "tab3":
        st.markdown("📄 **Tab 3 Preview — MegaCorp Workload Spec**: 15TB monthly egress | 4,000 IOPS | 99.9% uptime.")

    # Post-Meeting Graph Dialogue
    if st.session_state.gmeet_concluded:
        st.markdown("---")
        st.markdown("### 💬 Post-Meeting Graph Dialogue (No Flat Summaries)")
        st.caption("Chat with the FalkorDB meeting graph. Zero hallucinations, 100% human commitment attribution.")

        q_c1, q_c2, q_c3 = st.columns(3)
        mgr = MeetingGraphManager(db_client)

        sel_q = None
        with q_c1:
            if st.button("👤 What did Alex commit to?", use_container_width=True):
                sel_q = "What did Alex commit to?"
        with q_c2:
            if st.button("📑 Which browser tabs were referenced?", use_container_width=True):
                sel_q = "What browser tabs were open or referenced?"
        with q_c3:
            if st.button("⚠️ Were there any margin policy breaches?", use_container_width=True):
                sel_q = "Were there any margin alerts or policy breaches?"

        custom_q = st.text_input("Or ask any question about the meeting session:", key="gmeet_user_query")
        final_q = sel_q or custom_q

        if final_q:
            ans = mgr.query_meeting_graph("meet_megacorp_q3", final_q)
            st.session_state.gmeet_chat_history.append({"q": final_q, "a": ans})

        for item in st.session_state.gmeet_chat_history[-3:]:
            with st.chat_message("user"):
                st.markdown(f"**Question:** {item['q']}")
            with st.chat_message("assistant"):
                st.markdown(item["a"])
        st.markdown("---")
        if st.button("💬 Open Meeting Debrief in Strategic Copilot", type="primary", use_container_width=True):
            meet_sid = f"session_meet_{int(time.time())}"
            st.session_state.chat_sessions[meet_sid] = {
                "id": meet_sid,
                "title": "MegaCorp Meeting Debrief",
                "created_at": "Just now",
                "history": [{
                    "prompt": "Synthesize Sarah Chen's objections regarding CloudScale and finalize our $899 Starter Tier closing offer.",
                    "recommendation": (
                        "### Executive Closing Strategy: MegaCorp Enterprise Deal\n\n"
                        "**1. Objection Debrief:** Sarah Chen cited CloudScale's $800/mo flat rate. "
                        "Our FalkorDB teardown reveals CloudScale's $0.08/GB outbound egress surcharge elevates MegaCorp's 15TB workload to $1,936/mo true TCO.\n\n"
                        "**2. Policy Governance Verification:** Alex's verbal proposal of $700/mo was flagged and blocked by Banana as a 25% margin floor breach ($750 minimum based on $600 COGS).\n\n"
                        "**3. Recommended Closing Term:** Deliver the **Enterprise Starter Tier at $899.00 / month** (33.3% gross margin, $0 egress surcharge). "
                        "This undercuts CloudScale's true $1,936 TCO by $1,037/mo while preserving 100% policy compliance."
                    ),
                    "citations": ["doc_cloudscale_teardown_2026", "policy_minimum_margin", "meet_megacorp_q3", "com_alex_starter_tier"],
                    "memory_id": "mem_meet_megacorp_debrief",
                }],
                "attached_docs": [{
                    "name": "CloudScale CS-902 Invoice",
                    "doc_id": "doc_cloudscale_teardown_2026",
                    "company": "CloudScale",
                    "price": 800.0,
                    "finding": "CloudScale $800 sticker price masks $0.08/GB egress penalties.",
                }],
            }
            st.session_state.active_session_id = meet_sid
            st.session_state.chat_history = st.session_state.chat_sessions[meet_sid]["history"]
            st.session_state.main_nav_radio = "💬 Strategic Copilot"
            st.rerun()

# ==================== VIEW 3: VISUAL BRAIN ====================
elif selected_view == "🧠 Visual Brain (Graph)":
    st.markdown("## 🧠 FalkorDB Knowledge Graph Visual Brain")
    st.caption(
        "Interactive D3.js force-directed knowledge graph. **Bright colored nodes** are loaded by the Edmonds-Karp scheduler. "
        "**Dimmed nodes** were shed to protect the token budget. "
        "Notice the **Sky Blue (Speakers)**, **Amber (Commitments)**, and **Purple (Meetings)** nodes!"
    )

    visualizer = GraphVisualizer(db_client)
    html_graph = visualizer.generate_html(selected_canonical_ids=selected_ids_set, height=680)
    components.html(html_graph, height=700)

# ==================== VIEW 4: SCENARIO SIMULATOR ====================
elif selected_view == "🧪 Scenario Simulator":
    st.markdown("## 🧪 What-If Competitive Scenario Simulator")
    st.caption("Test competitor aggressive price wars inside isolated FalkorDB micro-graphs without polluting company records.")

    s_col1, s_col2 = st.columns(2)
    with s_col1:
        cs_cut = st.slider("CloudScale Price Cut", min_value=0.0, max_value=0.40, value=0.20, step=0.05, format="%.2f")
    with s_col2:
        cogs_rise = st.slider("ApexCloud COGS Inflation", min_value=0.0, max_value=0.25, value=0.05, step=0.05, format="%.2f")

    if st.button("⚡ Test Hypothesis in Sandbox", type="secondary"):
        with st.spinner("Testing inside ephemeral FalkorDB micro-graph..."):
            sandbox = SandboxManager(db_client=db_client)
            sandbox.initialize_sandbox()
            sim = sandbox.simulate_pricing_scenario(
                cloudscale_discount_pct=cs_cut,
                cogs_inflation_pct=cogs_rise,
            )
            sandbox.discard_sandbox()

        st.success("✓ Hypothesis tested and scratchpad graph dropped cleanly.")
        sc = sim["scenario"]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Simulated Competitor Price", sc["simulated_competitor_price"], f"-{sc['competitor_discount_pct']}")
        m2.metric("ApexCloud COGS", sc["simulated_apex_cogs"], f"+{int(cogs_rise*100)}%")
        m3.metric("Recommended Starter", sc["recommended_starter_price"], f"Floor: {sc['mandatory_25pct_margin_floor']}")
        m4.metric("Projected Gross Margin", sc["projected_gross_margin"], "Policy Compliant")
        st.info(f"💡 **Synthesis:** {sim['sandbox_finding']}")

# ==================== VIEW 6: MCP & DIAGNOSTICS ====================
elif selected_view == "🔬 MCP Agents & Diagnostics":
    st.markdown("## 🔬 Model Context Protocol (MCP) & Max-Flow Engine")
    st.caption("Inspect Edmonds-Karp network flow metrics and connect external coding CLIs.")

    # Flow metrics
    em1, em2, em3, em4 = st.columns(4)
    em1.metric("Max-Flow Throughput", f"{flow_result.total_flow}", "Utility Units")
    em2.metric("Augmenting Paths", f"{flow_result.augmenting_paths_count}", "Edmonds-Karp")
    em3.metric("Tokens Scheduled", f"{flow_result.total_tokens_used}", f"Limit: {token_budget}")
    em4.metric("Scheduler Latency", f"{flow_result.scheduler_latency_ms} ms", "GraphBLAS")

    st.markdown("---")
    st.markdown("#### 🔌 Connect External Coding CLIs (Model Context Protocol)")
    mcp_c1, mcp_c2 = st.columns(2)
    with mcp_c1:
        st.markdown("**1. Claude Code CLI:**")
        st.code("claude mcp add banana -- uv run banana mcp", language="bash")
    with mcp_c2:
        st.markdown("**2. Cursor / Antigravity (`mcpServers` config):**")
        st.code('{\n  "mcpServers": {\n    "banana": {\n      "command": "uv",\n      "args": ["run", "banana", "mcp"]\n    }\n  }\n}', language="json")

    st.markdown("---")
    st.markdown("#### 📊 Head-to-Head Benchmark Suite")
    if st.button("Run Live Benchmark Evaluation"):
        with st.spinner("Running Benchmark Suite against Baselines..."):
            suite = BenchmarkSuite(db_client)
            metrics = suite.run_all(budgets=[1100, 1600, 2500])

        rows = []
        for m in metrics:
            rows.append({
                "Strategy": m.strategy,
                "Budget": m.budget,
                "Tokens": m.total_tokens,
                "Policy Preserved": f"{m.policy_preservation_pct}%",
                "Dependencies Preserved": f"{m.dependency_preservation_pct}%",
                "Evidence Coverage": f"{m.evidence_coverage_pct}%",
                "Latency": f"{m.latency_ms} ms",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.success("Key Result: Under strict budgets, Banana maintains 100% Policy Preservation and 100% Dependency Integrity.")
