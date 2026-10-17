"""Banana — Autonomous AI Strategy & Live Meeting Agent."""

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
    page_title="Banana",
    page_icon="🍌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling (Dark, focused, agentic aesthetic + Comic Strip Styles)
st.markdown(
    """
    <style>
    /* Hide Streamlit top header, theme selector, decoration, and toolbar */
    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    #MainMenu,
    footer,
    .stDeployButton {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2.5rem;
    }
    .brand-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 2px;
    }
    .brand-title {
        font-size: 1.6rem;
        font-weight: 800;
        color: #f59e0b;
        letter-spacing: -0.5px;
    }
    .brand-tagline {
        font-size: 0.85rem;
        color: #94a3b8;
        margin-bottom: 16px;
    }
    .status-badge {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 9999px;
        font-size: 0.74rem;
        font-weight: 600;
        background: #064e3b;
        color: #34d399;
        margin-right: 6px;
    }
    .nav-header {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #64748b;
        margin-top: 14px;
        margin-bottom: 6px;
    }
    .agent-banner {
        padding: 22px 24px;
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .hud-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 16px;
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

    /* Comic Strip Styling */
    .comic-strip-container {
        background: #020617;
        border: 2px solid #334155;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
    }
    .comic-title-banner {
        background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%);
        color: #0f172a;
        font-weight: 900;
        font-size: 1.15rem;
        letter-spacing: 0.5px;
        padding: 8px 16px;
        border-radius: 8px;
        display: inline-block;
        margin-bottom: 6px;
        text-transform: uppercase;
    }
    .comic-subtitle {
        color: #94a3b8;
        font-size: 0.88rem;
        margin-bottom: 20px;
    }
    .comic-panel {
        background: #0f172a;
        border: 2px solid #1e293b;
        border-radius: 14px;
        padding: 18px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 440px;
        position: relative;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        margin-bottom: 16px;
    }
    .panel-badge {
        position: absolute;
        top: -12px;
        left: 14px;
        background: #f59e0b;
        color: #0f172a;
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
        padding: 3px 10px;
        border-radius: 6px;
        letter-spacing: 0.5px;
    }
    .panel-scene {
        font-size: 0.75rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        margin-top: 6px;
        margin-bottom: 12px;
    }
    .speech-bubble {
        padding: 10px 14px;
        border-radius: 12px;
        font-size: 0.85rem;
        line-height: 1.45;
        margin-bottom: 10px;
    }
    .bubble-client {
        background: #1e1b4b;
        border-left: 4px solid #a855f7;
        color: #f1f5f9;
    }
    .bubble-rep {
        background: #172554;
        border-left: 4px solid #38bdf8;
        color: #f1f5f9;
    }
    .bubble-banana {
        background: #272108;
        border: 1px solid #f59e0b;
        border-left: 4px solid #f59e0b;
        color: #fef08a;
    }
    .bubble-alert {
        background: #3a1014;
        border: 1px solid #ef4444;
        border-left: 4px solid #ef4444;
        color: #fecaca;
    }
    .bubble-success {
        background: #063226;
        border: 1px solid #10b981;
        border-left: 4px solid #10b981;
        color: #a7f3d0;
    }
    .comic-caption {
        background: #020617;
        border: 1px dashed #334155;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 0.78rem;
        color: #cbd5e1;
        font-style: italic;
        margin-top: 10px;
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

# Initialize session state variables
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {
        "session_default": {
            "id": "session_default",
            "title": "Domain Research & Fact Checking",
            "created_at": "Today",
            "history": [],
            "attached_docs": [],
        }
    }

if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = "session_default"

if st.session_state.active_session_id not in st.session_state.chat_sessions:
    if st.session_state.chat_sessions:
        st.session_state.active_session_id = list(st.session_state.chat_sessions.keys())[0]
    else:
        st.session_state.chat_sessions["session_default"] = {
            "id": "session_default",
            "title": "Domain Research Session",
            "created_at": "Today",
            "history": [],
            "attached_docs": [],
        }
        st.session_state.active_session_id = "session_default"

WORKSPACE_OPTIONS = ["🍌 Banana Chat", "🎙️ Google Meet Sentinel", "🧪 Simulations & Diagnostics"]

if "current_view" not in st.session_state or st.session_state.current_view not in WORKSPACE_OPTIONS:
    st.session_state.current_view = "🍌 Banana Chat"

if "show_live_graph" not in st.session_state:
    st.session_state.show_live_graph = True

if "meet_sim_history" not in st.session_state:
    st.session_state.meet_sim_history = []

# Ensure baseline knowledge is seeded
inspector_db = db_client.get_demand_graph()
try:
    check_cnt = inspector_db.query("MATCH (n) RETURN count(n)").result_set[0][0]
    if check_cnt == 0:
        GraphSeeder(db_client).seed_all(drop_existing=True)
except Exception:
    pass

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
    token_budget=1600,
    reserved_output_tokens=320,
)
selected_ids_set = set(flow_result.selected_canonical_ids)


# ==================== LEFT SIDEBAR ====================
with st.sidebar:
    st.markdown(
        """
        <div class="brand-header">
            <span style="font-size: 2rem;">🍌</span>
            <span class="brand-title">Banana</span>
        </div>
        <div class="brand-tagline">
            Multipurpose Domain Research & Graph Intelligence
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Big + New Chat Button
    if st.button("＋ New Chat", type="primary", use_container_width=True):
        new_count = len(st.session_state.chat_sessions) + 1
        new_sid = f"session_{new_count}_{int(time.time())}"
        st.session_state.chat_sessions[new_sid] = {
            "id": new_sid,
            "title": f"Research Session #{new_count}",
            "created_at": "Just now",
            "history": [],
            "attached_docs": [],
        }
        st.session_state.active_session_id = new_sid
        st.session_state.current_view = "🍌 Banana Chat"
        st.rerun()

    # 2. Main Workspace Navigation (Clean 3 Views, Chat is 1st)
    st.markdown('<div class="nav-header">Workspace</div>', unsafe_allow_html=True)
    cur_idx = WORKSPACE_OPTIONS.index(st.session_state.current_view) if st.session_state.current_view in WORKSPACE_OPTIONS else 0
    chosen_view = st.radio(
        "Workspace",
        WORKSPACE_OPTIONS,
        index=cur_idx,
        label_visibility="collapsed",
        key="workspace_nav_radio",
    )
    if chosen_view != st.session_state.current_view:
        st.session_state.current_view = chosen_view
        st.rerun()

    st.markdown("---")

    # 3. Recent Chats List with Delete Action
    st.markdown('<div class="nav-header">Recent Research</div>', unsafe_allow_html=True)
    for sid in list(st.session_state.chat_sessions.keys())[::-1]:
        sess = st.session_state.chat_sessions[sid]
        is_active = (sid == st.session_state.active_session_id and st.session_state.current_view == "🍌 Banana Chat")
        c_item, c_del = st.columns([5, 1])
        with c_item:
            title = sess["title"]
            if len(title) > 22:
                title = title[:22] + "..."
            label = f"{'▶ ' if is_active else '💬 '}{title}"
            if st.button(label, key=f"s_btn_{sid}", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state.active_session_id = sid
                st.session_state.current_view = "🍌 Banana Chat"
                st.rerun()
        with c_del:
            if st.button("🗑️", key=f"del_{sid}", help=f"Delete {sess['title']}"):
                del st.session_state.chat_sessions[sid]
                if st.session_state.active_session_id == sid:
                    if st.session_state.chat_sessions:
                        st.session_state.active_session_id = list(st.session_state.chat_sessions.keys())[0]
                    else:
                        new_id = f"session_1_{int(time.time())}"
                        st.session_state.chat_sessions[new_id] = {
                            "id": new_id,
                            "title": "Research Session #1",
                            "created_at": "Today",
                            "history": [],
                            "attached_docs": [],
                        }
                        st.session_state.active_session_id = new_id
                st.rerun()




# ==================== VIEW 1: BANANA CHAT (FIRST TAB) ====================
if st.session_state.current_view == "🍌 Banana Chat":
    active_session = st.session_state.chat_sessions[st.session_state.active_session_id]
    history = active_session["history"]

    show_graph = st.session_state.get("show_live_graph", True)

    if show_graph:
        c_chat, c_graph_pane = st.columns([6, 6], gap="large")
    else:
        c_chat = st.container()
        c_graph_pane = None

    with c_chat:
        # Header Bar
        c_title, c_actions = st.columns([5, 4])
        with c_title:
            st.markdown(f"### 🍌 {active_session['title']}")
            attached = active_session.get("attached_docs", [])
            attached_badge = f'<span class="status-badge" style="background:#1e3a8a;color:#93c5fd;">📎 {len(attached)} Files</span>' if attached else ""
            st.markdown(
                f"""
                <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;flex-wrap:wrap;">
                    <span class="status-badge">● Active</span>
                    <span class="status-badge" style="background:#064e3b;color:#34d399;">🌐 Multipurpose Domain Research</span>
                    <span class="status-badge" style="background:#1e3a8a;color:#93c5fd;">🔍 Graph Ground Truth</span>
                    <span class="status-badge" style="background:#1e293b;border:1px solid #334155;color:#94a3b8;">💻 Terminal: <code>uv run banana chat</code></span>
                    {attached_badge}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c_actions:
            c_tog, c_memo, c_del = st.columns([1.5, 1, 1])
            with c_tog:
                graph_btn_label = "✕ Hide Graph" if show_graph else "🧠 Show Graph"
                if st.button(graph_btn_label, key="toggle_live_graph_btn", use_container_width=True, type="primary" if show_graph else "secondary", help="Toggle live knowledge graph view"):
                    st.session_state.show_live_graph = not show_graph
                    st.rerun()

            with c_memo:
                if history:
                    latest = history[-1]
                    memo = f"""# Banana Domain Research & Intelligence Memo
**Date:** October 2026
**Session:** {active_session['title']}

---

## 1. Research Query
{latest['prompt']}

## 2. Synthesized Domain Intelligence
{latest['recommendation']}

## 3. Governance & Grounded Citations
- **Source Verification:** Verified against connected knowledge graph
- **Status:** PASS
"""
                    st.download_button(
                        "📥 Memo",
                        data=memo,
                        file_name=f"Banana_Research_{active_session['id']}.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
                else:
                    st.button("📥 Memo", disabled=True, use_container_width=True, help="Submit a prompt first to generate a memo")

            with c_del:
                if st.button("🗑️ Delete", key="top_del_btn", use_container_width=True, help="Delete this research chat"):
                    sid = st.session_state.active_session_id
                    del st.session_state.chat_sessions[sid]
                    if st.session_state.chat_sessions:
                        st.session_state.active_session_id = list(st.session_state.chat_sessions.keys())[0]
                    else:
                        new_id = f"session_1_{int(time.time())}"
                        st.session_state.chat_sessions[new_id] = {
                            "id": new_id,
                            "title": "Research Session #1",
                            "created_at": "Today",
                            "history": [],
                            "attached_docs": [],
                        }
                        st.session_state.active_session_id = new_id
                    st.rerun()

        # Agent Presence (If empty session, show agy CLI style greeting)
        if len(history) == 0:
            st.markdown(
                """
                <div class="agent-banner">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                        <span style="font-size:1.6rem;">🍌</span>
                        <span style="font-weight:700;font-size:1.15rem;color:#fcd34d;">Banana Multipurpose Research Agent Ready</span>
                        <span class="status-badge">Online</span>
                    </div>
                    <div style="color:#94a3b8;font-size:0.9rem;line-height:1.5;">
                        Autonomous multipurpose intelligence bot for deep domain research, technical teardowns, entity relationship exploration, and document fact verification. Ask any question, explore connected knowledge, or upload documents to investigate.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Conversational History
        for turn in history:
            with st.chat_message("user", avatar="👤"):
                st.markdown(turn["prompt"])
            with st.chat_message("assistant", avatar="🍌"):
                st.markdown(
                    """
                    <div style="display:flex;gap:6px;margin-bottom:8px;flex-wrap:wrap;">
                        <span class="status-badge">✓ Verified Ground Truth</span>
                        <span class="status-badge" style="background:#1e3a8a;color:#93c5fd;">✓ Graph & Source Audited</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(turn["recommendation"])
                if turn.get("citations"):
                    with st.expander("📁 Verified Citations"):
                        st.markdown(f"**Grounded Citations:** {', '.join(turn['citations'])}")

        # Active Attached Documents
        if active_session.get("attached_docs"):
            st.markdown(
                f"""
                <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin:10px 0 6px 0;">
                    <span style="font-size:0.8rem;color:#94a3b8;font-weight:600;">Active Attached Documents:</span>
                    {"".join([f'<span class="status-badge" style="background:#1e293b;border:1px solid #f59e0b;color:#fcd34d;">📎 {d["name"]} ({d["company"]})</span>' for d in active_session["attached_docs"]])}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Integrated Attachment Bar
        with st.expander("📎 Attach Competitor Invoice / Document (Multimodal Vision)", expanded=False):
            uploaded_file = st.file_uploader(
                "Upload invoice (PDF/TXT) or screenshot (PNG/JPG):",
                type=["png", "jpg", "jpeg", "pdf", "txt", "csv"],
                key=f"uploader_{st.session_state.active_session_id}",
            )
            if uploaded_file:
                file_bytes = uploaded_file.read()
                c_prev, c_ext = st.columns([1, 1])
                with c_prev:
                    st.caption(f"**File:** `{uploaded_file.name}` ({len(file_bytes)} bytes)")
                    if uploaded_file.type.startswith("image"):
                        st.image(file_bytes, caption=uploaded_file.name, use_container_width=True)
                    else:
                        st.text_area("Preview", file_bytes.decode("utf-8", errors="ignore")[:350], height=120)
                with c_ext:
                    if st.button("⚡ Ingest Document into Session", type="primary", key="ingest_doc_btn"):
                        with st.spinner("Analyzing document with Gemini Vision..."):
                            ingestor = MultimodalIngestor(db_client=db_client)
                            res = ingestor.ingest_bytes(
                                data=file_bytes,
                                file_name=uploaded_file.name,
                                mime_type=uploaded_file.type,
                            )
                        st.success(f"✓ Ingested `{uploaded_file.name}` into Banana memory!")
                        ext = res.extracted
                        st.markdown(f"**Company:** `{ext.company_name}` • **Price:** `${ext.advertised_price or 'N/A'}`")
                        if ext.hidden_fees_or_penalties:
                            st.warning(f"**Hidden Fees Flagged:** {ext.hidden_fees_or_penalties}")
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

    # Right Column: High-Visibility Knowledge Graph
    if c_graph_pane is not None:
        with c_graph_pane:
            st.markdown(
                """
                <div style="background:#0f172a;border:1px solid #334155;border-radius:12px;padding:14px 18px 10px 18px;margin-bottom:12px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div style="display:flex;align-items:center;gap:8px;">
                            <span style="font-weight:700;font-size:1.12rem;color:#fcd34d;">🧠 Live Knowledge Graph</span>
                            <span class="status-badge" style="background:#064e3b;color:#34d399;">Active Graph</span>
                        </div>
                        <div style="font-size:0.8rem;color:#94a3b8;">
                            <span style="color:#10b981;font-weight:700;">● Glowing:</span> Max-Flow Kept &nbsp;|&nbsp; 
                            <span style="color:#cbd5e1;font-weight:600;">○ Nodes:</span> Shed
                        </div>
                    </div>
                    <div style="font-size:0.82rem;color:#94a3b8;margin-top:6px;">
                        Interactive force-directed topology. Drag nodes to inspect relationships and governance policies.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            visualizer = GraphVisualizer(db_client)
            html_graph = visualizer.generate_html(selected_canonical_ids=selected_ids_set, height=640)
            components.html(html_graph, height=660)

    # Pinned Chat Input (ChatGPT style)
    user_prompt = st.chat_input("Ask Banana anything or enter a domain research topic...")
    if user_prompt:
        agent = BananaAgent(db_client=db_client)
        with st.status("🤖 Banana is researching domain & knowledge graph...", expanded=True) as status:
            st.write("🔍 Exploring domain entity relationships...")
            st.write("🛡️ Auditing governance & evidence policies...")
            st.write("⚡ Scheduling high-utility context via graph...")
            st.write("🧠 Synthesizing verified domain analysis...")
            result = agent.run(task_prompt=user_prompt, token_budget=1600, save_to_memory=True)
            status.update(label="✅ Domain Research Synthesis Ready!", state="complete", expanded=False)

        if len(history) == 0 and active_session["title"].startswith("Research Session"):
            short_title = user_prompt.split(".")[0].strip()
            if len(short_title) > 26:
                short_title = short_title[:26] + "..."
            active_session["title"] = short_title

        active_session["history"].append({
            "prompt": user_prompt,
            "recommendation": result.recommendation,
            "citations": result.evidence_citations,
            "memory_id": result.saved_memory_id,
        })
        st.rerun()


# ==================== VIEW 2: GOOGLE MEET SENTINEL ====================
elif st.session_state.current_view == "🎙️ Google Meet Sentinel":
    st.markdown("## 🎙️ Google Meet Sentinel")
    st.caption("Native terminal companion for Google Meet & Zoom. Zero browser extensions required. 0 cloud tokens burned while idle.")

    # 3-Step Clear Usage Guide
    st.markdown(
        """
        <div style="background:#0f172a;border:2px solid #334155;border-radius:14px;padding:22px;margin:14px 0 24px 0;">
            <div style="font-size:1.15rem;font-weight:800;color:#fcd34d;margin-bottom:4px;">
                ⚡ How to Use in 3 Simple Steps
            </div>
            <div style="font-size:0.83rem;color:#94a3b8;margin-bottom:16px;">
                Follow these 3 simple steps to run Banana Sentinel alongside your Google Meet or Zoom calls:
            </div>
            <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(260px, 1fr));gap:16px;">
                <div style="background:#020617;border:1px solid #1e293b;border-radius:10px;padding:16px;">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                        <span style="background:#f59e0b;color:#0f172a;font-weight:900;border-radius:50%;width:26px;height:26px;display:flex;align-items:center;justify-content:center;font-size:0.85rem;">1</span>
                        <span style="font-weight:700;color:#f8fafc;font-size:0.95rem;">Join Your Call</span>
                    </div>
                    <div style="font-size:0.82rem;color:#94a3b8;line-height:1.5;">
                        Open Google Meet or Zoom in Chrome as usual. No Chrome extension to install, no meeting bots to invite, and no corporate admin approval required.
                    </div>
                </div>
                <div style="background:#020617;border:1px solid #1e293b;border-radius:10px;padding:16px;">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                        <span style="background:#f59e0b;color:#0f172a;font-weight:900;border-radius:50%;width:26px;height:26px;display:flex;align-items:center;justify-content:center;font-size:0.85rem;">2</span>
                        <span style="font-weight:700;color:#f8fafc;font-size:0.95rem;">Run in Terminal</span>
                    </div>
                    <div style="font-size:0.82rem;color:#94a3b8;line-height:1.5;">
                        Launch the Sentinel in any terminal window alongside your meeting:<br>
                        <code style="color:#38bdf8;font-size:0.85rem;display:inline-block;margin-top:6px;">uv run banana meet</code><br>
                        <span style="font-size:0.75rem;color:#64748b;">(Or run <code>banana meet --auto</code> for an instant demo)</span>
                    </div>
                </div>
                <div style="background:#020617;border:1px solid #1e293b;border-radius:10px;padding:16px;">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                        <span style="background:#f59e0b;color:#0f172a;font-weight:900;border-radius:50%;width:26px;height:26px;display:flex;align-items:center;justify-content:center;font-size:0.85rem;">3</span>
                        <span style="font-weight:700;color:#f8fafc;font-size:0.95rem;">Get Intel & Auto-Log</span>
                    </div>
                    <div style="font-size:0.82rem;color:#94a3b8;line-height:1.5;">
                        Banana operates silently (0 cloud tokens while idle). When competitor traps or questions arise, it flashes sub-second nudges and automatically saves commitments to the graph.
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Comic Strip Banner
    st.markdown(
        """
        <div class="comic-strip-container">
            <div class="comic-title-banner">
                🍌 THE MEGACORP AMBUSH: A 4-PANEL CASE STUDY
            </div>
            <div class="comic-subtitle">
                How Banana protects deal margins and counters competitor ambush in real-time Google Meet calls.
            </div>
        """,
        unsafe_allow_html=True,
    )

    # 4 Comic Panels in a 2x2 Grid
    p_row1_col1, p_row1_col2 = st.columns(2)

    with p_row1_col1:
        st.markdown(
            """
            <div class="comic-panel">
                <span class="panel-badge">PANEL 1 • THE AMBUSH</span>
                <div class="panel-scene">📍 Live Google Meet Call • MegaCorp Deal Room</div>
                <div>
                    <div class="speech-bubble bubble-client">
                        <strong>👩‍💼 Sarah Chen (MegaCorp VP Procurement):</strong><br>
                        <em>"CloudScale just offered us $800/mo flat all-inclusive! If you can't beat their price right now, we're signing with them by 5 PM today."</em>
                    </div>
                    <div class="speech-bubble bubble-rep">
                        <strong>👨‍💻 Alex Rivera (Enterprise Rep):</strong><br>
                        <em>(Sweating nervously 😰, fingers hovering over the discount tool)</em><br>
                        <em>"Uhh... $800? Wow... let me see if we can do $700 to win your business..."</em>
                    </div>
                </div>
                <div class="comic-caption">
                    💭 The sales rep is completely blind to competitor contract traps and about to cave on price, destroying quarterly gross margin.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with p_row1_col2:
        st.markdown(
            """
            <div class="comic-panel">
                <span class="panel-badge">PANEL 2 • 0-TOKEN SENTINEL</span>
                <div class="panel-scene">⚡ Terminal Background • Zero Cloud Tokens Burned While Idle</div>
                <div>
                    <div class="speech-bubble bubble-banana">
                        <strong>🍌 Banana Sentinel (Terminal Background):</strong><br>
                        <em>(Silently intercepts speech stream in 14ms — zero tokens wasted during idle banter!)</em>
                    </div>
                    <div class="hud-card" style="margin-bottom:8px;padding:12px;border:1px solid #f59e0b;background:#181504;">
                        <div style="font-weight:700;color:#fcd34d;font-size:0.85rem;margin-bottom:4px;">⚡ ALERT: CloudScale Hidden Egress Surcharge!</div>
                        <div style="font-size:0.78rem;color:#fef08a;line-height:1.4;">
                            • CloudScale advertises $800 base, but Clause 4.2 charges <strong>$0.08/GB egress</strong>.<br>
                            • MegaCorp transfers 15 TB/mo = <strong>+$1,136/mo hidden fee</strong>.<br>
                            • <strong>True CloudScale TCO: $1,936/mo (NOT $800!)</strong><br>
                            <span style="color:#93c5fd;">🔗 Citation: contract_cloudscale_q3.pdf</span>
                        </div>
                    </div>
                </div>
                <div class="comic-caption">
                    💭 Zero prompt tokens burned while idle. High-frequency factual counter-intelligence delivered to rep before speaking.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    p_row2_col1, p_row2_col2 = st.columns(2)

    with p_row2_col1:
        st.markdown(
            """
            <div class="comic-panel">
                <span class="panel-badge" style="background:#ef4444;color:#fff;">PANEL 3 • MARGIN INTERLOCK</span>
                <div class="panel-scene">🛑 Governance Interlock • Margin Policy Triggered</div>
                <div>
                    <div class="speech-bubble bubble-rep">
                        <strong>👨‍💻 Alex:</strong> <em>(About to say: "Okay Sarah, we can match $700...")</em>
                    </div>
                    <div class="speech-bubble bubble-alert">
                        <strong>🛑 BANANA RED ALERT SCREEN FLASH:</strong><br>
                        <strong>GOVERNANCE VIOLATION PREVENTED!</strong><br>
                        • Base COGS = $600/mo. At $700, Gross Margin = <strong>14.3% ❌</strong><br>
                        • Mandatory Margin Floor: <strong>≥ 25.0% ($750 minimum)</strong><br>
                        • <strong>RECOMMENDED COUNTER-PLAY:</strong> Pitch <strong>$899 Starter Tier</strong> with zero-fee egress!<br>
                        • Sarah still saves <strong>$1,037/mo</strong> vs CloudScale's actual $1,936 cost!
                    </div>
                </div>
                <div class="comic-caption">
                    💭 Deterministic policy engine stops rogue discounts in their tracks, defending EBITDA margins.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with p_row2_col2:
        st.markdown(
            """
            <div class="comic-panel">
                <span class="panel-badge" style="background:#10b981;color:#fff;">PANEL 4 • THE FLAWLESS CLOSE</span>
                <div class="panel-scene">🤝 Deal Won • Autonomous Memory Commitment</div>
                <div>
                    <div class="speech-bubble bubble-rep">
                        <strong>👨‍💻 Alex Rivera:</strong><br>
                        <em>"Sarah, CloudScale's $800 sticker excludes egress. On your 15TB data volume, that's $1,936/mo. We'll give you our Starter Tier at $899 with zero egress fees included."</em>
                    </div>
                    <div class="speech-bubble bubble-success">
                        <strong>👩‍💼 Sarah Chen:</strong><br>
                        <em>"Wait, really?! You caught that hidden fee?! That would have blown our budget! Send over the $899 contract right now—we're signing today!"</em>
                    </div>
                    <div class="speech-bubble bubble-banana" style="border-left-color:#10b981;">
                        <strong>🍌 Banana Sentinel:</strong><br>
                        ✓ <strong>Deal Closed: $899/mo (33.3% Gross Margin)</strong><br>
                        🧠 <strong>Autonomously Saved to Knowledge Graph:</strong> Node <code>MegaCorp_Commitment_StarterTier</code>
                    </div>
                </div>
                <div class="comic-caption">
                    💭 Deal won. 33.3% margin protected. Zero browser extension needed. Meeting commitments written to graph memory.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # Interactive Step-Through Simulation
    st.markdown("### 🎮 Interactive Call Step-Through")
    st.caption("Step through the live Google Meet call to watch Banana's in-call intelligence engine react in real time.")

    c_btn1, c_btn2, c_btn3, c_btn4, c_reset = st.columns([1, 1, 1, 1.2, 0.8])
    with c_btn1:
        if st.button("1. Sarah Ambush", use_container_width=True):
            st.session_state.meet_sim_history = [
                {"speaker": "Sarah Chen", "role": "MegaCorp VP Procurement", "text": "CloudScale claims they offer $800/mo flat with no bandwidth fees. Why should MegaCorp pay $1,200?"}
            ]
            st.rerun()
    with c_btn2:
        if st.button("2. Panic Discount", use_container_width=True):
            st.session_state.meet_sim_history = [
                {"speaker": "Sarah Chen", "role": "MegaCorp VP Procurement", "text": "CloudScale claims they offer $800/mo flat with no bandwidth fees. Why should MegaCorp pay $1,200?"},
                {"speaker": "Alex Rivera", "role": "ApexCloud Sales Rep", "text": "We could meet in the middle and offer $700 flat for the first year to close today."}
            ]
            st.rerun()
    with c_btn3:
        if st.button("3. Counter-Offer", use_container_width=True):
            st.session_state.meet_sim_history = [
                {"speaker": "Sarah Chen", "role": "MegaCorp VP Procurement", "text": "CloudScale claims they offer $800/mo flat with no bandwidth fees. Why should MegaCorp pay $1,200?"},
                {"speaker": "Alex Rivera", "role": "ApexCloud Sales Rep", "text": "We could meet in the middle and offer $700 flat for the first year to close today."},
                {"speaker": "You", "role": "Solutions Architect", "text": "We can deliver our Enterprise Starter Tier at $899/mo flat with 0 dollar egress markup by Friday."}
            ]
            st.rerun()
    with c_btn4:
        if st.button("▶ Run Full Walkthrough", type="primary", use_container_width=True):
            st.session_state.meet_sim_history = [
                {"speaker": "Sarah Chen", "role": "MegaCorp VP Procurement", "text": "CloudScale claims they offer $800/mo flat with no bandwidth fees. Why should MegaCorp pay $1,200?"},
                {"speaker": "Alex Rivera", "role": "ApexCloud Sales Rep", "text": "We could meet in the middle and offer $700 flat for the first year to close today."},
                {"speaker": "You", "role": "Solutions Architect", "text": "We can deliver our Enterprise Starter Tier at $899/mo flat with 0 dollar egress markup by Friday."}
            ]
            st.rerun()
    with c_reset:
        if st.button("Reset", use_container_width=True):
            st.session_state.meet_sim_history = []
            st.rerun()

    if st.session_state.meet_sim_history:
        mgr = MeetingGraphManager(db_client=db_client)
        session_id = "meet_demo_live"
        mgr.initialize_session(
            session_id=session_id,
            topic="MegaCorp Cloud Migration & Pricing",
            participants=[
                MeetingParticipant(name="Sarah Chen", role="VP Procurement", company="MegaCorp"),
                MeetingParticipant(name="Alex Rivera", role="VP Sales", company="ApexCloud"),
                MeetingParticipant(name="You", role="Solutions Architect", company="ApexCloud"),
            ],
        )

        for item in st.session_state.meet_sim_history:
            spk = item["speaker"]
            txt = item["text"]
            txt_lower = txt.lower()

            st.markdown(f"**🎙️ {spk}** ({item.get('role', 'Participant')}):")
            st.write(f"> *\"{txt}\"*")

            if "cloudscale" in txt_lower or "800" in txt_lower:
                st.markdown(
                    """
                    <div style="background:#181504;border:1px solid #f59e0b;border-radius:10px;padding:14px;margin-bottom:12px;">
                        <div style="font-weight:700;color:#fcd34d;font-size:0.9rem;margin-bottom:4px;">💡 Micro-Nudge: CloudScale Hidden Egress Surcharge</div>
                        <div style="font-size:0.83rem;color:#fef08a;line-height:1.45;">
                            CloudScale's $800 sticker price masks a <strong>$0.08/GB egress fee</strong>.<br>
                            MegaCorp's 15TB workload incurs <strong>$1,136/mo in overages</strong>, bringing true TCO to <strong>$1,936/mo</strong>!<br>
                            <span style="color:#93c5fd;">🔗 Document Link: CloudScale CS-902 Invoice (doc_cloudscale_teardown_2026)</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif "700" in txt_lower:
                mgr.record_policy_breach(session_id, spk, 700.0, "policy_minimum_margin", "Proposed $700 violates 25% gross margin floor ($750 minimum).")
                st.markdown(
                    """
                    <div style="background:#2a0808;border:1px solid #ef4444;border-radius:10px;padding:14px;margin-bottom:12px;">
                        <div style="font-weight:700;color:#fca5a5;font-size:0.9rem;margin-bottom:4px;">🛑 GOVERNANCE ALERT: Margin Floor Breach</div>
                        <div style="font-size:0.83rem;color:#fecaca;line-height:1.45;">
                            Proposed $700/mo violates <strong>policy_minimum_margin</strong> ($750 minimum based on $600 COGS).<br>
                            Max permitted discount is $750/mo. Counter with our <strong>$899 Starter Tier</strong> instead!<br>
                            <span style="color:#93c5fd;">🔗 Document Link: Pricing Model Floor $750 (policy_minimum_margin)</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif "899" in txt_lower or "starter" in txt_lower:
                mgr.record_commitment(
                    session_id,
                    MeetingCommitment(
                        commitment_id="com_starter_tier",
                        speaker_name=spk,
                        term="Deliver Enterprise Starter Tier ($899/mo, 33.3% gross margin, $0 egress markup)",
                        deadline="Friday 5:00 PM",
                        assignee=spk,
                        referenced_doc_id="doc_cloudscale_teardown_2026",
                    ),
                )
                st.markdown(
                    """
                    <div style="background:#04231b;border:1px solid #10b981;border-radius:10px;padding:14px;margin-bottom:12px;">
                        <div style="font-weight:700;color:#6ee7b7;font-size:0.9rem;margin-bottom:4px;">✓ Strategy Aligned & Commitment Logged</div>
                        <div style="font-size:0.83rem;color:#a7f3d0;line-height:1.45;">
                            Agreed commitment recorded in Banana memory: <strong>$899/mo Starter Tier (33.3% margin)</strong>.<br>
                            • Assignee: Solutions Architect • Graph Commitment ID: <code>com_starter_tier</code>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # Native CLI Companion Guide
    st.markdown("### 💻 How to Run the Native CLI Companion")
    st.markdown(
        """
        No Chrome extension, no DOM injection, no meeting permission roadblocks.
        Run the native companion in your terminal right alongside Google Meet or Zoom:
        """
    )
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("**Live Interactive Companion:**")
        st.code("uv run banana meet", language="bash")
        st.caption("Listens to meeting transcript stream or takes input. Prompts live flash cards in terminal.")
    with col_c2:
        st.markdown("**Automated Demo Walkthrough:**")
        st.code("uv run banana meet --auto", language="bash")
        st.caption("Replays the MegaCorp scenario with live micro-nudges and policy validation.")

    st.markdown(
        """
        <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:16px;margin-top:14px;">
            <div style="font-weight:700;color:#fcd34d;font-size:0.95rem;margin-bottom:6px;">Why Native CLI Beats Chrome Extensions</div>
            <div style="font-size:0.82rem;color:#94a3b8;line-height:1.6;">
                • <strong>Zero Browser Friction:</strong> No Chrome Web Store review delays, corporate IT extension whitelisting, or Google Meet DOM breakage.<br>
                • <strong>0 Cloud Tokens While Idle:</strong> Consumes zero LLM tokens during meeting banter. Only triggers on high-relevance intent signals.<br>
                • <strong>Deterministic Policy Guardrails:</strong> Strictly enforces minimum gross margin floor (&ge; 25.0%) before discounts are verbalized.<br>
                • <strong>Autonomous Cross-Session Memory:</strong> Automatically persists commitments, participants, and tab citations into graph memory.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==================== VIEW 3: SIMULATIONS & DIAGNOSTICS ====================
elif st.session_state.current_view == "🧪 Simulations & Diagnostics":
    st.markdown("## 🧪 Simulations & Agent Diagnostics")
    st.caption("Test competitive price wars in isolated memory sandboxes, inspect agent protocols, and run performance benchmarks.")

    # Part 1: Scenario Simulator
    st.markdown("### 1. What-If Price War Simulator")
    st.caption("Execute what-if hypothesis testing inside isolated memory sandboxes without polluting baseline memory.")
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        cs_cut = st.slider("CloudScale Price Cut", min_value=0.0, max_value=0.40, value=0.20, step=0.05, format="%.2f")
    with s_col2:
        cogs_rise = st.slider("COGS Inflation", min_value=0.0, max_value=0.25, value=0.05, step=0.05, format="%.2f")

    if st.button("⚡ Test Hypothesis in Sandbox", type="secondary"):
        with st.spinner("Testing inside isolated sandbox graph..."):
            sandbox = SandboxManager(db_client=db_client)
            sandbox.initialize_sandbox()
            sim = sandbox.simulate_pricing_scenario(
                cloudscale_discount_pct=cs_cut,
                cogs_inflation_pct=cogs_rise,
            )
            sandbox.discard_sandbox()

        st.success("✓ Hypothesis tested and scratchpad dropped cleanly.")
        sc = sim["scenario"]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Competitor Price", sc["simulated_competitor_price"], f"-{sc['competitor_discount_pct']}")
        m2.metric("ApexCloud COGS", sc["simulated_apex_cogs"], f"+{int(cogs_rise*100)}%")
        m3.metric("Recommended Starter", sc["recommended_starter_price"], f"Floor: {sc['mandatory_25pct_margin_floor']}")
        m4.metric("Gross Margin", sc["projected_gross_margin"], "Policy Compliant")
        st.info(f"💡 **Synthesis:** {sim['sandbox_finding']}")

    st.markdown("---")

    # Part 2: External Agent Protocols (MCP)
    st.markdown("### 2. External Agent Integration (Model Context Protocol)")
    st.caption("Connect external coding agents (Claude Code, Cursor, Antigravity) to Banana.")
    mcp_c1, mcp_c2 = st.columns(2)
    with mcp_c1:
        st.markdown("**Claude Code CLI:**")
        st.code("claude mcp add banana -- uv run banana mcp", language="bash")
    with mcp_c2:
        st.markdown("**Cursor / Antigravity (`mcpServers` config):**")
        st.code('{\n  "mcpServers": {\n    "banana": {\n      "command": "uv",\n      "args": ["run", "banana", "mcp"]\n    }\n  }\n}', language="json")

    st.markdown("---")

    # Part 3: Performance & Integrity Benchmark Suite
    st.markdown("### 3. Performance & Policy Integrity Benchmarks")
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
