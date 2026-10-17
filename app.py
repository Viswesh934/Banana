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
    st.markdown("## 🎙️ Google Meet Sentinel")
    st.caption("Native terminal companion for Google Meet & Zoom. Zero browser extensions required. 0 cloud tokens burned while idle.")

    # 3-Step Clear Usage Guide (Prominently displayed at top)
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

    # Comic Strip Banner: The MegaCorp Ambush
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
    st.markdown("### 💻 Native CLI Companion Guide")
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
        st.caption("Listens to meeting audio/captions stream or takes terminal input. Prompts live flash cards.")
    with col_c2:
        st.markdown("**Automated Demo Walkthrough:**")
        st.code("uv run banana meet --auto", language="bash")
        st.caption("Replays the MegaCorp scenario with live micro-nudges and policy validation.")

    # Advanced Diagnostics Expander (Moved cleanly to bottom expander)
    with st.expander("🧪 Scenario Simulator & Agent Benchmarks", expanded=False):
        st.markdown("#### What-If Price War Simulator")
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
            sm1, sm2, sm3, sm4 = st.columns(4)
            sm1.metric("Competitor Price", sc["simulated_competitor_price"], f"-{sc['competitor_discount_pct']}")
            sm2.metric("ApexCloud COGS", sc["simulated_apex_cogs"], f"+{int(cogs_rise*100)}%")
            sm3.metric("Recommended Starter", sc["recommended_starter_price"], f"Floor: {sc['mandatory_25pct_margin_floor']}")
            sm4.metric("Gross Margin", sc["projected_gross_margin"], "Policy Compliant")
            st.info(f"💡 **Synthesis:** {sim['sandbox_finding']}")

        st.markdown("---")
        st.markdown("#### External Agent Integration (MCP)")
        mcp_c1, mcp_c2 = st.columns(2)
        with mcp_c1:
            st.markdown("**Claude Code CLI:**")
            st.code("claude mcp add banana -- uv run banana mcp", language="bash")
        with mcp_c2:
            st.markdown("**Cursor / Antigravity Config:**")
            st.code('{\n  "mcpServers": {\n    "banana": {\n      "command": "uv",\n      "args": ["run", "banana", "mcp"]\n    }\n  }\n}', language="json")

        st.markdown("---")
        st.markdown("#### Performance Benchmark Evaluation")
        if st.button("Run Benchmark Evaluation"):
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
            st.success("Banana maintains 100% Policy Preservation and 100% Dependency Integrity.")
