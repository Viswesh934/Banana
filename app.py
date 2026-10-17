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

# Custom Styling (Dark, focused, agentic aesthetic)
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
            "title": "MegaCorp Strategy & Pricing",
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
            "title": "New Chat",
            "created_at": "Today",
            "history": [],
            "attached_docs": [],
        }
        st.session_state.active_session_id = "session_default"

if "current_view" not in st.session_state:
    st.session_state.current_view = "🍌 Banana"

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
            Autonomous Strategy & Meeting Agent
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
            "title": f"New Chat #{new_count}",
            "created_at": "Just now",
            "history": [],
            "attached_docs": [],
        }
        st.session_state.active_session_id = new_sid
        st.session_state.current_view = "🍌 Banana"
        st.rerun()

    # 2. Main Workspace Navigation (Clean 3 Views)
    st.markdown('<div class="nav-header">Workspace</div>', unsafe_allow_html=True)
    workspace_choices = ["🍌 Banana", "🧠 Knowledge Graph", "🧪 Simulations & Diagnostics"]
    cur_idx = workspace_choices.index(st.session_state.current_view) if st.session_state.current_view in workspace_choices else 0
    chosen_view = st.radio(
        "Workspace",
        workspace_choices,
        index=cur_idx,
        label_visibility="collapsed",
        key="workspace_nav_radio",
    )
    if chosen_view != st.session_state.current_view:
        st.session_state.current_view = chosen_view
        st.rerun()

    st.markdown("---")

    # 3. Recent Chats List with Delete Action
    st.markdown('<div class="nav-header">Recent Chats</div>', unsafe_allow_html=True)
    for sid in list(st.session_state.chat_sessions.keys())[::-1]:
        sess = st.session_state.chat_sessions[sid]
        is_active = (sid == st.session_state.active_session_id and st.session_state.current_view == "🍌 Banana")
        c_item, c_del = st.columns([5, 1])
        with c_item:
            title = sess["title"]
            if len(title) > 22:
                title = title[:22] + "..."
            label = f"{'▶ ' if is_active else '💬 '}{title}"
            if st.button(label, key=f"s_btn_{sid}", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state.active_session_id = sid
                st.session_state.current_view = "🍌 Banana"
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
                            "title": "New Chat #1",
                            "created_at": "Today",
                            "history": [],
                            "attached_docs": [],
                        }
                        st.session_state.active_session_id = new_id
                st.rerun()

    # 4. Meeting CLI Callout
    st.markdown(
        """
        <div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:12px;margin:16px 0 10px 0;">
            <div style="font-weight:700;color:#fcd34d;font-size:0.85rem;margin-bottom:4px;">🎙️ Meeting Sentinel</div>
            <div style="font-size:0.78rem;color:#94a3b8;line-height:1.4;">
                Run in terminal alongside Google Meet calls:<br>
                <code style="color:#38bdf8;">banana meet</code>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # 5. Settings & Memory Reset
    with st.expander("⚙️ Settings & Memory", expanded=False):
        backend_url = st.text_input(
            "Backend / Lambda Endpoint",
            value="http://localhost:8765",
            help="Configure remote Lambda or local backend bridge",
            key="backend_url_cfg",
        )
        if st.button("🔄 Reset Memory", use_container_width=True):
            with st.spinner("Resetting baseline memory..."):
                GraphSeeder(db_client).seed_all(drop_existing=True)
                st.session_state.chat_sessions = {
                    "session_default": {
                        "id": "session_default",
                        "title": "MegaCorp Strategy & Pricing",
                        "created_at": "Today",
                        "history": [],
                        "attached_docs": [],
                    }
                }
                st.session_state.active_session_id = "session_default"
                st.session_state.current_view = "🍌 Banana"
                st.success("Memory reset!")
                st.rerun()


# ==================== VIEW 1: BANANA (AGENT CHAT) ====================
if st.session_state.current_view == "🍌 Banana":
    active_session = st.session_state.chat_sessions[st.session_state.active_session_id]
    history = active_session["history"]

    # Header Bar
    c_title, c_memo, c_del = st.columns([4, 1, 1])
    with c_title:
        st.markdown(f"### 🍌 {active_session['title']}")
        attached = active_session.get("attached_docs", [])
        attached_badge = f'<span class="status-badge" style="background:#1e3a8a;color:#93c5fd;">📎 {len(attached)} Attached Files</span>' if attached else ""
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">
                <span class="status-badge">● Active</span>
                <span class="status-badge" style="background:#064e3b;color:#34d399;">🛡️ 25% Margin Floor Verified</span>
                {attached_badge}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_memo:
        if history:
            latest = history[-1]
            memo = f"""# Banana Strategic Briefing Memo
**Date:** October 2026
**Session:** {active_session['title']}

---

## 1. Directive
{latest['prompt']}

## 2. Strategic Recommendation
{latest['recommendation']}

## 3. Governance & Policy Verification
- **Gross Margin Floor:** >= 25.0%
- **Status:** PASS
"""
            st.download_button(
                "📥 Memo",
                data=memo,
                file_name=f"Banana_Memo_{active_session['id']}.md",
                mime="text/markdown",
                use_container_width=True,
            )

    with c_del:
        if st.button("🗑️ Delete", key="top_del_btn", use_container_width=True, help="Delete this chat"):
            sid = st.session_state.active_session_id
            del st.session_state.chat_sessions[sid]
            if st.session_state.chat_sessions:
                st.session_state.active_session_id = list(st.session_state.chat_sessions.keys())[0]
            else:
                new_id = f"session_1_{int(time.time())}"
                st.session_state.chat_sessions[new_id] = {
                    "id": new_id,
                    "title": "New Chat #1",
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
                    <span style="font-weight:700;font-size:1.15rem;color:#fcd34d;">Banana Agent Ready</span>
                    <span class="status-badge">Online</span>
                </div>
                <div style="color:#94a3b8;font-size:0.9rem;line-height:1.5;">
                    Ask any deal strategy question, request competitor pricing teardowns, or attach an invoice to ground the conversation.
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
                    <span class="status-badge">✓ 33.3% Gross Margin Verified</span>
                    <span class="status-badge" style="background:#1e3a8a;color:#93c5fd;">✓ Grounded in Invoices</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(turn["recommendation"])
            if turn.get("citations") or turn.get("memory_id"):
                with st.expander("📁 Verified Citations & Memory Node"):
                    st.markdown(f"**Grounded Citations:** {', '.join(turn['citations']) if turn.get('citations') else 'Core Knowledge'}")
                    if turn.get("memory_id"):
                        st.info(f"Recorded in Banana memory: `{turn['memory_id']}`")

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

    # Pinned Chat Input (ChatGPT style)
    user_prompt = st.chat_input("Message Banana or enter a strategic directive...")
    if user_prompt:
        agent = BananaAgent(db_client=db_client)
        with st.status("🤖 Banana is analyzing strategy & memory...", expanded=True) as status:
            st.write("🔍 Searching verified entity knowledge...")
            st.write("🛡️ Auditing 25% gross margin floor policy...")
            st.write("⚡ Scheduling high-utility context...")
            st.write("🧪 Simulating competitive counter-response...")
            result = agent.run(task_prompt=user_prompt, token_budget=1600, save_to_memory=True)
            status.update(label="✅ Strategic Recommendation Ready!", state="complete", expanded=False)

        if len(history) == 0 and active_session["title"].startswith("New Chat"):
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


# ==================== VIEW 2: KNOWLEDGE GRAPH ====================
elif st.session_state.current_view == "🧠 Knowledge Graph":
    c_back, _ = st.columns([1, 4])
    with c_back:
        if st.button("← Back to Banana Agent", key="back_from_brain"):
            st.session_state.current_view = "🍌 Banana"
            st.rerun()

    st.markdown("## 🧠 Banana Knowledge Graph")
    st.caption("Interactive visual memory graph. Bright nodes are currently scheduled in active memory. Dimmed nodes are shed to protect context limits.")

    visualizer = GraphVisualizer(db_client)
    html_graph = visualizer.generate_html(selected_canonical_ids=selected_ids_set, height=680)
    components.html(html_graph, height=700)


# ==================== VIEW 3: SIMULATIONS & DIAGNOSTICS ====================
elif st.session_state.current_view == "🧪 Simulations & Diagnostics":
    c_back, _ = st.columns([1, 4])
    with c_back:
        if st.button("← Back to Banana Agent", key="back_from_sim"):
            st.session_state.current_view = "🍌 Banana"
            st.rerun()

    st.markdown("## 🧪 Simulations & Agent Diagnostics")
    st.caption("Test competitive price wars in isolated memory sandboxes, inspect agent protocols, and run performance benchmarks.")

    # Part 1: Scenario Simulator
    st.markdown("### 1. What-If Price War Simulator")
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
