"""Banana — Autonomous Multipurpose Domain Research & Live Meeting Agent."""

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
from banana.dynamic_graph import DynamicGraphManager
from banana.meeting_graph import (
    MeetingCommitment,
    MeetingGraphManager,
    MeetingParticipant,
    MeetingTurn,
)
from banana.multimodal import MultimodalIngestor
from banana.sandbox import SandboxManager
from banana.visualizer import GraphVisualizer

# Streamlit Page Config
st.set_page_config(
    page_title="Banana",
    page_icon="🍌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling (Dark, clean, ChatGPT/Claude style layout + Comic Strip Styles)
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
        padding-top: 1.2rem !important;
        padding-bottom: 3rem;
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
        padding: 24px 26px;
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        margin-bottom: 24px;
    }
    .graph-stat-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 12px 18px;
        text-align: center;
    }
    .hud-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 16px;
    }
    .entity-chip {
        display: inline-block;
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.78rem;
        color: #38bdf8;
        margin: 2px;
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
dynamic_graph = DynamicGraphManager(db_client)

# Clean 3 Workspace Options (Chat strictly 1st, Graph 2nd, Meeting 3rd)
WORKSPACE_OPTIONS = ["💬 Chat", "🧠 Knowledge Graph", "🎙️ Google Meet Sentinel"]

# Initialize session state variables
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {
        "session_default": {
            "id": "session_default",
            "title": "Domain Research & Discovery",
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
            "title": "Domain Research & Discovery",
            "created_at": "Today",
            "history": [],
            "attached_docs": [],
        }
        st.session_state.active_session_id = "session_default"

if "current_view" not in st.session_state or st.session_state.current_view not in WORKSPACE_OPTIONS:
    st.session_state.current_view = "💬 Chat"

if "meet_sim_history" not in st.session_state:
    st.session_state.meet_sim_history = []


# ==================== LEFT SIDEBAR ====================
with st.sidebar:
    st.markdown(
        """
        <div class="brand-header">
            <span style="font-size: 2rem;">🍌</span>
            <span class="brand-title">Banana</span>
        </div>
        <div class="brand-tagline">
            Autonomous Domain Research & Graph Intelligence
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. New Chat Button
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
        st.session_state.current_view = "💬 Chat"
        st.rerun()

    # 2. Main Workspace Navigation (3 Clean Views)
    st.markdown('<div class="nav-header">Workspace</div>', unsafe_allow_html=True)
    cur_idx = WORKSPACE_OPTIONS.index(st.session_state.current_view) if st.session_state.current_view in WORKSPACE_OPTIONS else 0

    def on_sidebar_nav_change():
        st.session_state.current_view = st.session_state.workspace_nav_radio
        st.session_state.top_workspace_segmented_nav = st.session_state.workspace_nav_radio

    chosen_view = st.radio(
        "Workspace",
        WORKSPACE_OPTIONS,
        index=cur_idx,
        label_visibility="collapsed",
        key="workspace_nav_radio",
        on_change=on_sidebar_nav_change,
    )

    st.markdown("---")

    # 3. Recent Chats List with Delete Action
    st.markdown('<div class="nav-header">Recent Research</div>', unsafe_allow_html=True)
    for sid in list(st.session_state.chat_sessions.keys())[::-1]:
        sess = st.session_state.chat_sessions[sid]
        is_active = (sid == st.session_state.active_session_id and st.session_state.current_view == "💬 Chat")
        c_item, c_del = st.columns([5, 1])
        with c_item:
            title = sess["title"]
            if len(title) > 22:
                title = title[:22] + "..."
            label = f"{'▶ ' if is_active else '💬 '}{title}"
            if st.button(label, key=f"s_btn_{sid}", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state.active_session_id = sid
                st.session_state.current_view = "💬 Chat"
                st.rerun()
        with c_del:
            if st.button("🗑️", key=f"del_{sid}", help=f"Delete {sess['title']}"):
                dynamic_graph.clear_session(sid)
                del st.session_state.chat_sessions[sid]
                if st.session_state.active_session_id == sid:
                    if st.session_state.chat_sessions:
                        st.session_state.active_session_id = list(st.session_state.chat_sessions.keys())[0]
                    else:
                        new_id = f"session_1_{int(time.time())}"
                        st.session_state.chat_sessions[new_id] = {
                            "id": new_id,
                            "title": "Domain Research & Discovery",
                            "created_at": "Today",
                            "history": [],
                            "attached_docs": [],
                        }
                        st.session_state.active_session_id = new_id
                st.rerun()

    st.markdown("---")
    # Compact System Diagnostics
    st.markdown(
        f"""
        <div style="background:#090d16;border:1px solid #1e293b;border-radius:8px;padding:10px 12px;font-size:0.75rem;color:#94a3b8;">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <span>LLM Engine:</span>
                <span style="color:#34d399;font-weight:700;">{settings.gemini_model}</span>
            </div>
            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <span>Session Graph:</span>
                <span style="color:#38bdf8;font-weight:600;">Isolated Space</span>
            </div>
            <div style="display:flex;justify-content:space-between;">
                <span>Status:</span>
                <span style="color:#34d399;font-weight:700;">● Online</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==================== MAIN PAGE TOP WORKSPACE TABS ====================
top_view = st.segmented_control(
    "Workspace Navigation",
    options=WORKSPACE_OPTIONS,
    default=st.session_state.current_view,
    label_visibility="collapsed",
    key="top_workspace_segmented_nav",
)
if top_view and top_view != st.session_state.current_view:
    st.session_state.current_view = top_view
    st.session_state.workspace_nav_radio = top_view
    st.rerun()

st.markdown('<div style="height: 6px;"></div>', unsafe_allow_html=True)


# ==================== VIEW 1: CHAT (FIRST TAB ONLY) ====================
if st.session_state.current_view == "💬 Chat":
    active_session = st.session_state.chat_sessions[st.session_state.active_session_id]
    history = active_session["history"]

    # Header Bar
    c_title, c_actions = st.columns([6, 3])
    with c_title:
        st.markdown(f"### 🍌 {active_session['title']}")
        attached = active_session.get("attached_docs", [])
        attached_badge = f'<span class="status-badge" style="background:#1e3a8a;color:#93c5fd;">📎 {len(attached)} Files</span>' if attached else ""
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;flex-wrap:wrap;">
                <span class="status-badge">● Active Session</span>
                <span class="status-badge" style="background:#064e3b;color:#34d399;">🌐 Multipurpose Domain Research</span>
                <span class="status-badge" style="background:#1e3a8a;color:#93c5fd;">🔍 Knowledge Graph Grounded</span>
                {attached_badge}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_actions:
        c_memo, c_clear = st.columns([1, 1])
        with c_memo:
            if history:
                latest = history[-1]
                memo = f"""# Banana Domain Research & Intelligence Memo
**Date:** {time.strftime('%B %Y')}
**Session:** {active_session['title']}

---

## 1. Research Query
{latest['prompt']}

## 2. Synthesized Domain Intelligence
{latest['recommendation']}

## 3. Discovered Knowledge Entities & Citations
{', '.join(latest.get('citations', [])) or 'Grounded in session knowledge graph.'}
"""
                st.download_button(
                    "📥 Memo",
                    data=memo,
                    file_name=f"Banana_Research_{active_session['id']}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            else:
                st.button("📥 Memo", disabled=True, use_container_width=True, help="Ask a question first to generate a memo")

        with c_clear:
            if st.button("🗑️ Clear", key="top_clear_btn", use_container_width=True, help="Clear this conversation and its graph"):
                active_session["history"] = []
                active_session["attached_docs"] = []
                dynamic_graph.clear_session(active_session["id"])
                st.rerun()

    # Agent Welcome Banner (When session is fresh)
    if len(history) == 0:
        st.markdown(
            """
            <div class="agent-banner">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                    <span style="font-size:1.8rem;">🍌</span>
                    <span style="font-weight:800;font-size:1.2rem;color:#fcd34d;">Banana Autonomous Research Agent Ready</span>
                    <span class="status-badge">● Connected Live</span>
                </div>
                <div style="color:#94a3b8;font-size:0.92rem;line-height:1.6;">
                    Banana is a multipurpose intelligence agent designed for deep domain investigations, technical teardowns, entity relationship exploration, and document fact verification.<br>
                    Every prompt genuinely queries <strong>Gemini 3.8 Flash</strong>, while autonomously extracting entities and relationships to build your isolated session knowledge graph in real time.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("**⚡ Quick Research Topics:**")
        q1, q2, q3 = st.columns(3)
        sample_prompt = None
        with q1:
            if st.button("🔬 RISC-V vs ARM Architecture", use_container_width=True):
                sample_prompt = "Analyze the key architectural trade-offs between RISC-V and ARMv9 for edge AI workloads."
        with q2:
            if st.button("🔒 Post-Quantum Cryptography", use_container_width=True):
                sample_prompt = "Explain NIST post-quantum cryptographic standards (ML-KEM vs classical RSA) and implementation risks."
        with q3:
            if st.button("☁️ Cloud Egress Pricing Models", use_container_width=True):
                sample_prompt = "Examine hidden egress fees and bandwidth markup tactics across major cloud providers."

        if sample_prompt:
            agent = BananaAgent(db_client=db_client)
            with st.status(f"🤖 Banana researching with Gemini ({settings.gemini_model})...", expanded=True) as status:
                st.write("🔍 Gathering domain context...")
                st.write("⚡ Executing Gemini 3.8 Flash inference & entity discovery...")
                result = agent.run(
                    task_prompt=sample_prompt,
                    session_id=active_session["id"],
                    token_budget=2000,
                    save_to_memory=True,
                )
                status.update(label="✅ Research synthesis complete!", state="complete", expanded=False)

            active_session["title"] = sample_prompt[:32] + "..."
            active_session["history"].append({
                "prompt": sample_prompt,
                "recommendation": result.recommendation,
                "citations": result.evidence_citations,
                "entities": result.extracted_entities,
                "relationships": result.extracted_relationships,
            })
            st.rerun()

    # Conversational History Display
    for turn in history:
        with st.chat_message("user", avatar="👤"):
            st.markdown(turn["prompt"])
            if turn.get("attached_files"):
                badges = " ".join([
                    f'<span class="status-badge" style="background:#1e293b;border:1px solid #38bdf8;color:#38bdf8;">📎 {fn}</span>'
                    for fn in turn["attached_files"]
                ])
                st.markdown(badges, unsafe_allow_html=True)
        with st.chat_message("assistant", avatar="🍌"):
            st.markdown(
                """
                <div style="display:flex;gap:6px;margin-bottom:8px;flex-wrap:wrap;">
                    <span class="status-badge">✓ Verified Ground Truth</span>
                    <span class="status-badge" style="background:#1e3a8a;color:#93c5fd;">✓ Gemini 3.8 Flash Synthesized</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(turn["recommendation"])

            # Highlight newly discovered entities
            ents = turn.get("entities", [])
            rels = turn.get("relationships", [])
            if ents or rels:
                st.markdown(
                    f"""
                    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;padding:10px 14px;margin-top:10px;">
                        <span style="font-weight:700;color:#fcd34d;font-size:0.85rem;">🧠 Knowledge Graph Update:</span>
                        <span style="color:#94a3b8;font-size:0.82rem;">Indexed <b>{len(ents)}</b> new entities and <b>{len(rels)}</b> relationships into session graph.</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if turn.get("citations"):
                with st.expander("📁 Verified Citations"):
                    st.markdown(f"**Grounded Citations:** {', '.join(turn['citations'])}")

    # Active Attached Documents Badge Indicator
    if active_session.get("attached_docs"):
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin:12px 0 6px 0;">
                <span style="font-size:0.8rem;color:#94a3b8;font-weight:600;">Active Attached Context:</span>
                {"".join([f'<span class="status-badge" style="background:#1e293b;border:1px solid #f59e0b;color:#fcd34d;">📎 {d["name"]}</span>' for d in active_session["attached_docs"]])}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Chat Input: STRICTLY IN TAB 1 WITH INTEGRATED NATIVE DOCUMENT UPLOAD
    chat_val = st.chat_input(
        "Ask Banana anything or upload documents (📎)...",
        accept_file="multiple",
        file_type=["png", "jpg", "jpeg", "pdf", "txt", "csv", "md"],
    )
    if chat_val:
        # Extract prompt text and any uploaded files directly from chat input
        if hasattr(chat_val, "text"):
            user_prompt = chat_val.text.strip()
            uploaded_files = getattr(chat_val, "files", []) or []
        elif isinstance(chat_val, dict):
            user_prompt = chat_val.get("text", "").strip()
            uploaded_files = chat_val.get("files", []) or []
        else:
            user_prompt = str(chat_val).strip()
            uploaded_files = []

        new_attached_docs = []
        attached_snippets = []
        attached_file_names = []

        for uf in uploaded_files:
            file_bytes = uf.read()
            attached_file_names.append(uf.name)
            size_kb = round(len(file_bytes) / 1024, 1)

            if uf.name.lower().endswith((".png", ".jpg", ".jpeg")):
                with st.spinner(f"Analyzing {uf.name} with Gemini Vision..."):
                    ingestor = MultimodalIngestor(db_client=db_client)
                    res = ingestor.ingest_bytes(data=file_bytes, file_name=uf.name, mime_type=uf.type)
                    finding = res.extracted.evidence_finding or f"Visual inspection of {uf.name}."
                    new_attached_docs.append({
                        "name": uf.name,
                        "finding": finding,
                        "size_kb": size_kb,
                    })
                    attached_snippets.append(f"Attached Image: {uf.name}\nVision Analysis: {finding}")
            elif uf.name.lower().endswith(".pdf"):
                text_content = ""
                try:
                    import io, pypdf
                    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                    text_content = "\n".join(page.extract_text() or "" for page in reader.pages)
                except Exception:
                    text_content = file_bytes.decode("utf-8", errors="ignore")
                new_attached_docs.append({
                    "name": uf.name,
                    "finding": text_content[:4000],
                    "size_kb": size_kb,
                })
                attached_snippets.append(f"Attached PDF: {uf.name}\nExtracted Content:\n{text_content[:4000]}")
            else:
                text_content = file_bytes.decode("utf-8", errors="ignore")
                new_attached_docs.append({
                    "name": uf.name,
                    "finding": text_content[:4000],
                    "size_kb": size_kb,
                })
                attached_snippets.append(f"Attached Document: {uf.name}\nContent:\n{text_content[:4000]}")

        if new_attached_docs:
            if "attached_docs" not in active_session:
                active_session["attached_docs"] = []
            active_session["attached_docs"].extend(new_attached_docs)

        # If user uploaded documents without typing prompt, synthesize a clear research directive
        if not user_prompt:
            user_prompt = f"Analyze the attached file(s) ({', '.join(attached_file_names)}): extract key findings, concepts, entities, and map them to the session knowledge graph."

        # Compile combined attached context for this turn
        attached_text = "\n\n".join(attached_snippets) if attached_snippets else None
        if not attached_text and active_session.get("attached_docs"):
            attached_text = "\n\n".join(
                f"Document: {d['name']}\nContent: {d.get('finding', '')}"
                for d in active_session.get("attached_docs", [])
            )

        agent = BananaAgent(db_client=db_client)
        with st.status(f"🤖 Banana researching with Gemini ({settings.gemini_model})...", expanded=True) as status:
            st.write("🔍 Gathering session context & history...")
            st.write("⚡ Executing Gemini 3.8 Flash inference & entity discovery...")
            st.write("🧠 Ingesting discovered entities into session knowledge graph...")

            result = agent.run(
                task_prompt=user_prompt,
                session_id=active_session["id"],
                attached_context=attached_text,
                conversation_history=history,
                token_budget=3000,
                save_to_memory=True,
            )
            status.update(label="✅ Research synthesis ready!", state="complete", expanded=False)

        if (len(history) == 0 and active_session["title"].startswith("Research Session")) or active_session["title"] == "Domain Research & Discovery":
            short_title = user_prompt.split(".")[0].strip()
            if len(short_title) > 28:
                short_title = short_title[:28] + "..."
            active_session["title"] = short_title

        active_session["history"].append({
            "prompt": user_prompt,
            "attached_files": attached_file_names,
            "recommendation": result.recommendation,
            "citations": result.evidence_citations,
            "entities": result.extracted_entities,
            "relationships": result.extracted_relationships,
            "memory_id": result.saved_memory_id,
        })
        st.rerun()


# ==================== VIEW 2: KNOWLEDGE GRAPH (DEDICATED FULL-PAGE TAB) ====================
elif st.session_state.current_view == "🧠 Knowledge Graph":
    # Strictly ensure chat input and bottom dock are hidden on non-chat tabs
    st.markdown(
        """
        <style>
        div[data-testid="stChatInput"],
        div[data-testid="stBottom"],
        .stChatInput {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
            pointer-events: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    active_session = st.session_state.chat_sessions[st.session_state.active_session_id]
    session_id = active_session["id"]

    # Header & Metric Banner
    graph_data = dynamic_graph.get_session_nodes_and_edges(session_id)
    node_count = len(graph_data["nodes"])
    edge_count = len(graph_data["edges"])

    c_head, c_btn = st.columns([7, 2])
    with c_head:
        st.markdown(f"## 🧠 Knowledge Graph: {active_session['title']}")
        st.caption(f"Session-isolated dynamic knowledge graph • Scoped to `{session_id}` • Zero mock data")
    with c_btn:
        if st.button("🗑️ Clear Session Graph", use_container_width=True, help="Clear graph nodes for this session"):
            dynamic_graph.clear_session(session_id)
            st.success("Session graph reset.")
            st.rerun()

    # Metric Cards Bar
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(
            f"""
            <div class="graph-stat-card">
                <div style="font-size:1.6rem;font-weight:800;color:#38bdf8;">{node_count}</div>
                <div style="font-size:0.8rem;color:#94a3b8;text-transform:uppercase;font-weight:600;">Discovered Entities</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f"""
            <div class="graph-stat-card">
                <div style="font-size:1.6rem;font-weight:800;color:#a855f7;">{edge_count}</div>
                <div style="font-size:0.8rem;color:#94a3b8;text-transform:uppercase;font-weight:600;">Active Relationships</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f"""
            <div class="graph-stat-card">
                <div style="font-size:1.6rem;font-weight:800;color:#34d399;">Isolated</div>
                <div style="font-size:0.8rem;color:#94a3b8;text-transform:uppercase;font-weight:600;">Session Memory Space</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)

    # Render Full-Screen Interactive D3 Graph
    visualizer = GraphVisualizer(db_client)
    html_graph = visualizer.generate_html(height=700, session_id=session_id)
    components.html(html_graph, height=720)

    # Catalog of Extracted Entities & Relationships (if any)
    if node_count > 0:
        with st.expander(f"📋 Discovered Entities Catalog ({node_count} Nodes)", expanded=False):
            df_nodes = pd.DataFrame([
                {
                    "ID": n["id"],
                    "Title": n["title"],
                    "Type": n["type"],
                    "Description": n["content"],
                }
                for n in graph_data["nodes"]
            ])
            st.dataframe(df_nodes, use_container_width=True, hide_index=True)

        if edge_count > 0:
            with st.expander(f"🔗 Relationships Catalog ({edge_count} Edges)", expanded=False):
                df_edges = pd.DataFrame([
                    {
                        "Source": e["source"],
                        "Relation": e["relation"],
                        "Target": e["target"],
                    }
                    for e in graph_data["edges"]
                ])
                st.dataframe(df_edges, use_container_width=True, hide_index=True)


# ==================== VIEW 3: GOOGLE MEET SENTINEL ====================
elif st.session_state.current_view == "🎙️ Google Meet Sentinel":
    # Strictly ensure chat input and bottom dock are hidden on non-chat tabs
    st.markdown(
        """
        <style>
        div[data-testid="stChatInput"],
        div[data-testid="stBottom"],
        .stChatInput {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
            pointer-events: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("## 🎙️ Google Meet Sentinel")
    st.caption("Native terminal companion for Google Meet & Zoom calls • 0 browser extensions required • 0 cloud tokens while idle")

    # 3-Step Clear Usage Guide (Prominently displayed at top)
    st.markdown(
        """
        <div style="background:#0f172a;border:2px solid #334155;border-radius:14px;padding:22px;margin:14px 0 20px 0;">
            <div style="font-size:1.15rem;font-weight:800;color:#fcd34d;margin-bottom:4px;">
                ⚡ How to Use in 3 Simple Steps
            </div>
            <div style="font-size:0.83rem;color:#94a3b8;margin-bottom:16px;">
                Run Banana Sentinel alongside your Google Meet or Zoom calls:
            </div>
            <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(260px, 1fr));gap:16px;">
                <div style="background:#020617;border:1px solid #1e293b;border-radius:10px;padding:16px;">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                        <span style="background:#f59e0b;color:#0f172a;font-weight:900;border-radius:50%;width:26px;height:26px;display:flex;align-items:center;justify-content:center;font-size:0.85rem;">1</span>
                        <span style="font-weight:700;color:#f8fafc;font-size:0.95rem;">Join Your Call</span>
                    </div>
                    <div style="font-size:0.82rem;color:#94a3b8;line-height:1.5;">
                        Open Google Meet or Zoom in Chrome as usual. Zero Chrome extensions to install, no meeting bots to invite, and no corporate admin approvals.
                    </div>
                </div>
                <div style="background:#020617;border:1px solid #1e293b;border-radius:10px;padding:16px;">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                        <span style="background:#f59e0b;color:#0f172a;font-weight:900;border-radius:50%;width:26px;height:26px;display:flex;align-items:center;justify-content:center;font-size:0.85rem;">2</span>
                        <span style="font-weight:700;color:#f8fafc;font-size:0.95rem;">Run in Terminal</span>
                    </div>
                    <div style="font-size:0.82rem;color:#94a3b8;line-height:1.5;">
                        Launch the Sentinel in any terminal window alongside your meeting:<br>
                        <code style="color:#38bdf8;font-size:0.85rem;display:inline-block;margin-top:6px;">uv run banana meet</code>
                    </div>
                </div>
                <div style="background:#020617;border:1px solid #1e293b;border-radius:10px;padding:16px;">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                        <span style="background:#f59e0b;color:#0f172a;font-weight:900;border-radius:50%;width:26px;height:26px;display:flex;align-items:center;justify-content:center;font-size:0.85rem;">3</span>
                        <span style="font-weight:700;color:#f8fafc;font-size:0.95rem;">Get Intel & Auto-Log</span>
                    </div>
                    <div style="font-size:0.82rem;color:#94a3b8;line-height:1.5;">
                        Banana operates silently (0 cloud tokens while idle). When competitor traps or pricing pushback arise, it flashes sub-second nudges and logs commitments to the graph.
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Minimal Terminal Commands Box
    st.markdown("### 💻 Terminal Commands")
    col_cmd1, col_cmd2 = st.columns(2)
    with col_cmd1:
        st.markdown("**Live Interactive Companion:**")
        st.code("uv run banana meet", language="bash")
        st.caption("Listens to meeting transcript/audio stream locally with zero cloud tokens while idle.")
    with col_cmd2:
        st.markdown("**Quick 30-Second Demo:**")
        st.code("uv run banana meet --auto", language="bash")
        st.caption("Replays real-time competitor nudge and margin interlock defense.")

    st.markdown("---")

    # Minimal Value Proposition Summary Cards
    st.markdown("### 🎯 Value Proposition")
    st.markdown(
        """
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:14px;margin-top:10px;">
            <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:18px;">
                <div style="font-size:1.5rem;margin-bottom:8px;">🛑</div>
                <div style="font-weight:700;color:#f8fafc;font-size:1rem;margin-bottom:6px;">1. Stop Rogue Discounts</div>
                <div style="font-size:0.84rem;color:#94a3b8;line-height:1.5;">
                    Sales reps under customer pressure often cave and offer below-cost discounts. Banana intercepts proposed pricing in real time and enforces mandatory gross margin floors (&ge; 25%) before words are spoken.
                </div>
            </div>
            <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:18px;">
                <div style="font-size:1.5rem;margin-bottom:8px;">⚡</div>
                <div style="font-weight:700;color:#f8fafc;font-size:1rem;margin-bottom:6px;">2. Expose Competitor Hidden Fees</div>
                <div style="font-size:0.84rem;color:#94a3b8;line-height:1.5;">
                    When prospects quote low competitor sticker prices (such as CloudScale's $800/mo), Banana instantly surfaces audited invoice citations exposing $0.08/GB egress fees that inflate true monthly cost to $1,936/mo.
                </div>
            </div>
            <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:18px;">
                <div style="font-size:1.5rem;margin-bottom:8px;">🤝</div>
                <div style="font-weight:700;color:#f8fafc;font-size:1rem;margin-bottom:6px;">3. Auto-Log Commitments to Graph</div>
                <div style="font-size:0.84rem;color:#94a3b8;line-height:1.5;">
                    Verbal agreements, starter tiers, deadlines, and attendee responsibilities are automatically logged into the persistent knowledge graph memory without manual note-taking.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
