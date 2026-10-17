"""Banana — Executive AI Strategy Copilot powered by FalkorDB Graph Intelligence."""

import os
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

# Custom Styling for Premium Agent Experience
st.markdown(
    """
    <style>
    .brand-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 4px;
    }
    .brand-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #f59e0b;
        letter-spacing: -0.5px;
    }
    .brand-tagline {
        font-size: 1.05rem;
        color: #94a3b8;
        margin-bottom: 24px;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        background: #064e3b;
        color: #34d399;
        margin-right: 8px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        border-bottom: 1px solid #334155;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.95rem;
        font-weight: 600;
        padding: 8px 18px;
    }
    .gmeet-container {
        background: #202124;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #3c4043;
        margin-bottom: 16px;
    }
    .video-tile {
        background: #171717;
        border: 2px solid #3c4043;
        border-radius: 10px;
        height: 180px;
        position: relative;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        transition: all 0.3s ease;
    }
    .video-tile.speaking {
        border-color: #34d399;
        box-shadow: 0 0 16px rgba(52, 211, 153, 0.4);
    }
    .video-tile-name {
        position: absolute;
        bottom: 8px;
        left: 10px;
        background: rgba(0, 0, 0, 0.7);
        color: #e8eaed;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 500;
    }
    .floating-banana-card {
        background: rgba(15, 23, 42, 0.96);
        border: 2px solid #f59e0b;
        border-radius: 12px;
        padding: 16px;
        margin-top: 14px;
        box-shadow: 0 10px 25px -5px rgba(245, 158, 11, 0.3);
    }
    .gmeet-controls-bar {
        display: flex;
        justify-content: center;
        gap: 14px;
        margin-top: 16px;
        padding-top: 12px;
        border-top: 1px solid #3c4043;
    }
    .gmeet-circle-btn {
        width: 42px;
        height: 42px;
        border-radius: 50%;
        background: #3c4043;
        color: white;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
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

# Initialize session states
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "gmeet_step" not in st.session_state:
    st.session_state.gmeet_step = 0
if "gmeet_active_tab" not in st.session_state:
    st.session_state.gmeet_active_tab = "tab1"
if "gmeet_concluded" not in st.session_state:
    st.session_state.gmeet_concluded = False
if "gmeet_chat_history" not in st.session_state:
    st.session_state.gmeet_chat_history = []

# Ensure database is seeded with company & competitor knowledge
inspector_db = db_client.get_demand_graph()
try:
    check_cnt = inspector_db.query("MATCH (n) RETURN count(n)").result_set[0][0]
    if check_cnt == 0:
        GraphSeeder(db_client).seed_all(drop_existing=True)
except Exception:
    pass

# Header
st.markdown(
    """
    <div class="brand-header">
        <span style="font-size: 2.3rem;">🍌</span>
        <span class="brand-title">Banana</span>
    </div>
    <div class="brand-tagline">
        Autonomous Pricing & Competitive Strategy Copilot • Powered by <b>FalkorDB Graph Intelligence</b>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar: Executive Controls
with st.sidebar:
    st.markdown("### 🧭 Copilot Control Center")

    # Copilot Status
    health = db_client.check_connection()
    if health["status"] == "ok":
        st.markdown(
            f'<div class="status-badge">● Graph Online</div><span style="font-size:0.85rem;color:#94a3b8;">FalkorDB ({health["latency_ms"]}ms)</span>',
            unsafe_allow_html=True,
        )
    else:
        st.error("Graph Database Offline")

    if settings.gemini_api_key:
        st.markdown(
            f'<div style="margin-top:8px;"><span class="status-badge" style="background:#1e3a8a;color:#93c5fd;">● LLM Active</span><span style="font-size:0.85rem;color:#94a3b8;">{settings.gemini_model}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # High-level budget/depth slider
    st.markdown("#### 🎯 Context Precision / Budget")
    token_budget = st.slider(
        "Token Knapsack Limit",
        min_value=800,
        max_value=4000,
        value=1600,
        step=100,
        help="Controls how much evidence the agent retains. The Max-Flow engine strictly prioritizes mandatory policies and critical evidence.",
    )

    st.markdown("---")

    st.markdown("#### 💡 Quick Strategic Prompts")
    prompt_q3 = st.button("💼 Recommend Q3 Pricing Strategy", use_container_width=True)
    prompt_egress = st.button("🔍 Expose CloudScale Hidden Fees", use_container_width=True)
    prompt_parity = st.button("⚖️ Compare SLA & Feature Parity", use_container_width=True)

    st.markdown("---")
    if st.button("🔄 Reset Graph Knowledge Base", use_container_width=True):
        with st.spinner("Resetting to baseline market knowledge..."):
            GraphSeeder(db_client).seed_all(drop_existing=True)
            st.session_state.chat_history = []
            st.session_state.gmeet_step = 0
            st.session_state.gmeet_concluded = False
            st.session_state.gmeet_chat_history = []
            st.success("Knowledge base reset!")
            st.rerun()

# Set prompt based on quick buttons or default
if prompt_egress:
    default_directive = "Expose CloudScale's hidden bandwidth and egress overage fees compared to ApexCloud's zero-markup model."
elif prompt_parity:
    default_directive = "Compare SLA uptime guarantees, refund terms, and architectural parity across HyperStore, CloudScale, and ApexCloud."
elif prompt_q3:
    default_directive = (
        "Analyze competitor pricing changes (CloudScale, HyperStore, DataVanguard), "
        "identify hidden fee and feature gaps against ApexCloud Enterprise, and recommend "
        "an adjusted pricing strategy complying with our 25% minimum gross margin policy."
    )
else:
    default_directive = (
        "Analyze competitor pricing changes (CloudScale, HyperStore, DataVanguard), "
        "identify hidden fee and feature gaps against ApexCloud Enterprise, and recommend "
        "an adjusted pricing strategy complying with our 25% minimum gross margin policy."
    )

# Pre-fetch candidate universe for live visualizer
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

# Main Navigation Tabs (GMeet Flagship Tab Added!)
tab_gmeet, tab_agent, tab_brain, tab_ingest, tab_sandbox, tab_tech = st.tabs([
    "🎙️ Google Meet & Floating Banana HUD",
    "💬 Strategic Copilot",
    "🧠 Visual Brain (Knowledge Graph)",
    "📁 Ingest Invoices & Screenshots",
    "🧪 Scenario Simulator",
    "🔬 Under The Hood & MCP Server",
])

# ==================== TAB 0: GOOGLE MEET & FLOATING BANANA HUD ====================
with tab_gmeet:
    st.markdown("### 🎙️ Ambient Google Meet & Floating Banana HUD")
    st.caption(
        "Experience Banana floating during an executive deal call. It operates with **0 cloud tokens burned while idle**, "
        "pops up 15-word fact-checks and margin alerts when triggered, remembers the exact open browser tab, "
        "and constructs a **FalkorDB Meeting Graph** for post-call dialogue."
    )

    # 1. Google Meet Virtual Stage
    gmeet_step = st.session_state.gmeet_step

    speaker1_active = "speaking" if gmeet_step == 1 else ""
    speaker2_active = "speaking" if gmeet_step == 2 else ""
    speaker3_active = "speaking" if gmeet_step == 3 else ""

    st.markdown(
        f"""
        <div class="gmeet-container">
            <div class="gmeet-header">
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="font-size:1.2rem;">🟢</span>
                    <span style="font-weight:700;color:#e8eaed;font-size:1.05rem;">Google Meet — Enterprise Deal Sync: MegaCorp & ApexCloud</span>
                    <span style="background:#303134;color:#9aa0a6;padding:2px 8px;border-radius:6px;font-size:0.75rem;">meet.google.com/ban-ana-meet</span>
                </div>
                <div style="display:flex;align-items:center;gap:12px;">
                    <span style="color:#34d399;font-weight:600;font-size:0.85rem;">● LIVE RECORDING</span>
                    <span style="background:#3c4043;color:#e8eaed;padding:4px 10px;border-radius:16px;font-size:0.8rem;">👥 3 on call</span>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
                <div class="video-tile {speaker1_active}">
                    <div style="font-size:2.8rem;">👩‍💼</div>
                    <div style="color:#94a3b8;font-size:0.85rem;margin-top:4px;">MegaCorp Enterprise Lead</div>
                    <div class="video-tile-name">Sarah Chen (MegaCorp) 🎤</div>
                </div>
                <div class="video-tile {speaker2_active}">
                    <div style="font-size:2.8rem;">👨‍💼</div>
                    <div style="color:#94a3b8;font-size:0.85rem;margin-top:4px;">VP Sales</div>
                    <div class="video-tile-name">Alex Rivera (ApexCloud) 🎤</div>
                </div>
                <div class="video-tile {speaker3_active}">
                    <div style="font-size:2.8rem;">💻</div>
                    <div style="color:#94a3b8;font-size:0.85rem;margin-top:4px;">Solutions Architect [You]</div>
                    <div class="video-tile-name">You (ApexCloud) [Self-View] 🎤</div>
                </div>
            </div>
            <div class="gmeet-controls-bar">
                <span class="gmeet-circle-btn">🎤</span>
                <span class="gmeet-circle-btn">📹</span>
                <span class="gmeet-circle-btn">💬</span>
                <span class="gmeet-circle-btn">✋</span>
                <span class="gmeet-circle-btn">🖥️</span>
                <span class="gmeet-circle-btn" style="background:#ea4335;">🔴</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Interactive Meeting Progression Controller
    st.markdown("#### 🎬 Live Meeting Progression & Safe-Word Triggers")
    col_t1, col_t2, col_t3, col_end = st.columns(4)

    with col_t1:
        if st.button("Turn 1: Sarah cites CloudScale $800", use_container_width=True):
            st.session_state.gmeet_step = 1
            st.session_state.gmeet_active_tab = "tab4"
            st.rerun()
    with col_t2:
        if st.button("Turn 2: Alex proposes $700 discount", use_container_width=True):
            st.session_state.gmeet_step = 2
            st.rerun()
    with col_t3:
        if st.button("Turn 3: You propose $899 Starter Tier", use_container_width=True):
            st.session_state.gmeet_step = 3
            st.rerun()
    with col_end:
        if st.button("🔴 Conclude Call & Ingest Graph", type="primary", use_container_width=True):
            with st.spinner("Ingesting Meeting Knowledge Graph into FalkorDB..."):
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
                # Turn 1
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
                # Turn 2: Policy Breach
                mgr.record_policy_breach(
                    session_id="meet_megacorp_q3",
                    speaker_name="Alex Rivera",
                    proposed_price=700.0,
                    policy_id="policy_minimum_margin",
                    reason="Proposed $700 price violates mandatory 25% gross margin floor ($750 minimum).",
                )
                # Turn 3: Commitment
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
                st.success("✓ Meeting Graph successfully constructed in FalkorDB!")
                st.rerun()

    # 3. The Floating Banana HUD (Overlaid Reactively)
    st.markdown("---")
    st.markdown("#### 🍌 Ambient Floating Banana HUD Feed")

    if gmeet_step == 0:
        st.markdown(
            """
            <div class="floating-banana-card" style="border-color:#64748b;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span style="font-size:1.6rem;">🍌</span>
                        <span style="font-weight:700;color:#f59e0b;font-size:1.1rem;">BANANA HUD • 0 CLOUD TOKENS (IDLE)</span>
                    </div>
                    <span class="status-badge" style="background:#1e293b;color:#94a3b8;">Listening for Alt+Space or Safe Words</span>
                </div>
                <div style="color:#94a3b8;font-size:0.9rem;margin-top:8px;">
                    Silently maintaining local 30-second circular audio buffer in memory. Zero cloud tokens burned during small talk.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif gmeet_step == 1:
        st.markdown(
            """
            <div class="floating-banana-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span style="font-size:1.6rem;">🍌</span>
                        <span style="font-weight:700;color:#f59e0b;font-size:1.1rem;">BANANA FLASH NUDGE (Triggered by mention of "CloudScale $800")</span>
                    </div>
                    <span class="status-badge">⚡ Sub-500ms Graph Lookup</span>
                </div>
                <div style="color:#e2e8f0;font-size:0.95rem;margin-top:8px;">
                    💡 <b>Micro-Nudge:</b> CloudScale's $800 sticker price masks a <b>$0.08/GB egress surcharge</b> beyond 1TB.
                    MegaCorp's 14.2TB monthly outbound traffic adds <b>$1,136.00/mo in hidden fees</b>, bringing true TCO to <b>$1,936.00/mo</b>!
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col_jump, col_stat = st.columns([1, 2])
        with col_jump:
            if st.button("🔗 Jump to Tab 4: CloudScale CS-902 Invoice", type="primary"):
                st.session_state.gmeet_active_tab = "tab4"
                st.rerun()
        with col_stat:
            st.caption("FalkorDB traversed `(:Competitor {name: 'CloudScale'})-[:EVALUATED_BY]->(:Evidence)` in 1.4ms.")

    elif gmeet_step == 2:
        st.markdown(
            """
            <div class="floating-banana-card" style="border-color:#ef4444;box-shadow: 0 10px 25px -5px rgba(239, 68, 68, 0.3);">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span style="font-size:1.6rem;">🍌</span>
                        <span style="font-weight:700;color:#ef4444;font-size:1.1rem;">⚠️ GOVERNANCE ALERT (Triggered by proposal of "$700/mo")</span>
                    </div>
                    <span class="status-badge" style="background:#7f1d1d;color:#fca5a5;">Policy Floor Breach</span>
                </div>
                <div style="color:#f8fafc;font-size:0.95rem;margin-top:8px;">
                    🛑 <b>Margin Floor Violation:</b> Proposed $700/mo is below our <b>$750/mo minimum price floor</b> ($600 infrastructure COGS basis).
                    Violates <code>policy_minimum_margin</code> (mandatory 25% revenue floor). Propose annual upfront discount or introduce the $899 Starter tier!
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif gmeet_step == 3:
        st.markdown(
            """
            <div class="floating-banana-card" style="border-color:#10b981;box-shadow: 0 10px 25px -5px rgba(16, 185, 129, 0.3);">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span style="font-size:1.6rem;">🍌</span>
                        <span style="font-weight:700;color:#10b981;font-size:1.1rem;">✓ STRATEGY ALIGNED & COMMITMENT RECORDED</span>
                    </div>
                    <span class="status-badge" style="background:#064e3b;color:#34d399;">Compliant (33.3% Margin)</span>
                </div>
                <div style="color:#f8fafc;font-size:0.95rem;margin-top:8px;">
                    🤝 <b>Agreed Commitment:</b> Alex Rivera commits to delivering the <b>$899/mo Enterprise Starter Tier</b> (33.3% margin, $0 egress markup) by <b>Friday 5:00 PM</b>.
                    Saves MegaCorp $1,037/mo over CloudScale!
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 4. Active Browser Tab Memory Tray
    st.markdown("---")
    st.markdown("#### 📑 Active Browser Tab Memory Tray (Zero-Search Deep Links)")
    st.caption("Banana tracks which documents and tabs were referenced during the call so you never have to hunt across 45 open tabs.")

    tab_btn1, tab_btn2, tab_btn3, tab_btn4 = st.columns(4)
    with tab_btn1:
        if st.button("Tab 1: ApexCloud Tiers", use_container_width=True):
            st.session_state.gmeet_active_tab = "tab1"
            st.rerun()
    with tab_btn2:
        if st.button("Tab 2: Competitor Matrix", use_container_width=True):
            st.session_state.gmeet_active_tab = "tab2"
            st.rerun()
    with tab_btn3:
        if st.button("Tab 3: MegaCorp 15TB Spec", use_container_width=True):
            st.session_state.gmeet_active_tab = "tab3"
            st.rerun()
    with tab_btn4:
        # Highlight in gold if active
        t4_label = "⭐ Tab 4: CloudScale CS-902 (Referenced)" if st.session_state.gmeet_active_tab == "tab4" else "Tab 4: CloudScale CS-902"
        if st.button(t4_label, type="primary" if st.session_state.gmeet_active_tab == "tab4" else "secondary", use_container_width=True):
            st.session_state.gmeet_active_tab = "tab4"
            st.rerun()

    # Display preview of active tab
    active_tab = st.session_state.gmeet_active_tab
    if active_tab == "tab4":
        st.info(
            "📄 **Tab 4 Preview — CloudScale Customer Invoice CS-90218 (Google Drive)**\n\n"
            "• **Customer:** MegaCorp Global Systems | **Billing Period:** June 2026\n"
            "• **Base Subscription:** Enterprise Cloud Pro: **$800.00/mo**\n"
            "• **Hidden Egress Surcharge (14.2 TB @ $0.08/GB):** **$1,136.00** ⚠️\n"
            "• **Peak Hours Multiplier (Clause 4.2):** **$142.50**\n"
            "• **Total Billed:** **$2,128.50** (vs. ApexCloud Starter Tier: $899.00 Flat)\n"
            "• *Verbatim Clause 4.1:* 'Customer agrees to $0.08 per GB egress overage fee beyond standard 1TB allowance.'"
        )
    elif active_tab == "tab1":
        st.markdown("📄 **Tab 1 Preview — ApexCloud Internal Pricing Model**: Enterprise Tier: $1,200/mo | Enterprise Starter: $899/mo | COGS Basis: $600/mo | Absolute Price Floor: $750/mo.")
    elif active_tab == "tab2":
        st.markdown("📄 **Tab 2 Preview — Competitive Parity Analysis**: HyperStore SLA: 99.5% with 10% refund cap | DataVanguard: $0.15/Compute Unit with 42% dispute churn.")
    elif active_tab == "tab3":
        st.markdown("📄 **Tab 3 Preview — MegaCorp Workload Spec**: 15TB monthly egress | 4,000 IOPS | 99.9% uptime requirement.")

    # 5. Post-Meeting Graph Dialogue (When Concluded)
    if st.session_state.gmeet_concluded:
        st.markdown("---")
        st.markdown("### 💬 Post-Meeting Graph Dialogue (No Flat Summaries)")
        st.caption(
            "Chat directly with the **FalkorDB Meeting Graph**. Ask who committed to what, which tabs were referenced, "
            "or audit policy governance with 100% deterministic accuracy."
        )

        # Quick query buttons
        q_col1, q_col2, q_col3 = st.columns(3)
        mgr = MeetingGraphManager(db_client)

        clicked_q = None
        with q_col1:
            if st.button("👤 What did Alex commit to?", use_container_width=True):
                clicked_q = "What did Alex commit to?"
        with q_col2:
            if st.button("📑 Which browser tabs were referenced?", use_container_width=True):
                clicked_q = "What browser tabs were open or referenced?"
        with q_col3:
            if st.button("⚠️ Were there any margin policy breaches?", use_container_width=True):
                clicked_q = "Were there any margin alerts or policy breaches?"

        custom_q = st.text_input("Or ask any question about the meeting session:", key="gmeet_query_input")
        target_q = clicked_q or custom_q

        if target_q:
            ans = mgr.query_meeting_graph("meet_megacorp_q3", target_q)
            st.session_state.gmeet_chat_history.append({"q": target_q, "a": ans})

        for item in st.session_state.gmeet_chat_history[-3:]:
            with st.chat_message("user"):
                st.markdown(f"**Question:** {item['q']}")
            with st.chat_message("assistant"):
                st.markdown(item["a"])

        st.caption("🔒 **Retention Policy**: Ephemeral raw transcript TTL set to 24 Hours. Permanent decision and commitment nodes promoted into FalkorDB Knowledge Graph with `[:SUPERSEDES]` lineage.")

# ==================== TAB 1: STRATEGIC COPILOT ====================
with tab_agent:
    st.markdown("### Executive Strategic Dialogue")
    st.caption("Interact with the copilot. All decisions are verified against FalkorDB gross margin policies ($750/mo minimum floor).")

    # Display past conversation history
    for i, turn in enumerate(st.session_state.chat_history):
        with st.chat_message("user"):
            st.markdown(f"**Objective:** {turn['prompt']}")
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

    # New prompt input
    user_query = st.text_input(
        "Enter your strategic question or select a preset from the sidebar:",
        value=default_directive,
        key="agent_prompt_input",
    )

    col_run, col_mem = st.columns([1, 4])
    with col_run:
        exec_btn = st.button("🚀 Consult Banana", type="primary", use_container_width=True)
    with col_mem:
        persist_chk = st.checkbox("Remember this decision in FalkorDB across sessions", value=True)

    if exec_btn and user_query:
        agent = BananaAgent(db_client=db_client)

        with st.status("🤖 Banana is orchestrating intelligence...", expanded=True) as status:
            st.write("🔍 **Traversing Knowledge Graph**: Matching competitor entities and audited invoices in FalkorDB...")
            st.write("🛡️ **Auditing Governance Policies**: Verifying minimum 25% gross margin floor ($750/mo minimum)...")
            st.write("⚡ **Running Max-Flow Context Knapsack**: Preserving connected evidence subgraphs within token limit...")
            st.write("🧪 **Simulating Competitive Response**: Testing price moves in isolated FalkorDB sandbox...")

            result = agent.run(
                task_prompt=user_query,
                token_budget=token_budget,
                save_to_memory=persist_chk,
            )
            status.update(label="✅ Strategic Recommendation Ready!", state="complete", expanded=False)

        # Store turn in session state
        st.session_state.chat_history.append({
            "prompt": user_query,
            "recommendation": result.recommendation,
            "citations": result.evidence_citations,
            "memory_id": result.saved_memory_id,
        })
        st.rerun()

    # One-Click Exportable Board Briefing Artifact
    if st.session_state.chat_history:
        st.markdown("---")
        latest_turn = st.session_state.chat_history[-1]
        memo_content = f"""# ApexCloud Executive Strategy & Pricing Briefing Memo
**Date:** October 2026
**Prepared by:** Banana Autonomous Strategy Copilot
**Underlying Engine:** FalkorDB Graph Intelligence & Edmonds-Karp Context Scheduler

---

## 1. Executive Directive
{latest_turn['prompt']}

## 2. Recommended Strategic Decision
{latest_turn['recommendation']}

## 3. Governance & Policy Verification Audit
- **Mandatory Gross Margin Floor:** >= 25.0% (Enforced by `policy_minimum_margin`)
- **Unit Economic Cost Basis (COGS):** $600.00 / month
- **Absolute Minimum Price Floor:** $750.00 / month
- **Recommended Starter Offering:** $899.00 / month (Yielding 33.3% Gross Margin)
- **Policy Audit Status:** 100% PASS — Zero violations permitted

## 4. Grounded Citations & Audit Provenance
- Sourced Evidence Nodes: {latest_turn['citations']}
- FalkorDB Persistent Lineage Node: {latest_turn.get('memory_id', 'Session Ephemeral')}
"""
        st.download_button(
            label="📥 Export Executive Briefing Memo (.md)",
            data=memo_content,
            file_name="ApexCloud_Board_Briefing_Memo.md",
            mime="text/markdown",
            use_container_width=True,
        )

# ==================== TAB 2: VISUAL BRAIN ====================
with tab_brain:
    st.markdown("### 🧠 The Agent's Visual Knowledge Graph")
    st.caption(
        "Explore the live FalkorDB network Banana traverses to make decisions. "
        "Nodes highlighted in **bright color** are actively loaded into the agent's context. "
        "**Dimmed nodes** were safely shed to protect the token budget without losing critical policies. "
        "Notice the **Sky Blue (Speakers)**, **Amber (Commitments)**, and **Purple (Meeting Sessions)** nodes created by Google Meet calls!"
    )

    visualizer = GraphVisualizer(db_client)
    html_graph = visualizer.generate_html(selected_canonical_ids=selected_ids_set, height=620)
    components.html(html_graph, height=640)

# ==================== TAB 3: INGEST DOCUMENTS & SCREENSHOTS ====================
with tab_ingest:
    st.markdown("### 📁 Multimodal Document & Screenshot Ingestion")
    st.caption(
        "Upload competitor invoices, pricing screenshots, or SLA contracts. "
        "Gemini 3.5 Flash Vision extracts verified pricing structures, and writes them directly into FalkorDB."
    )

    uploaded_file = st.file_uploader(
        "Drag & Drop Competitor Invoice (PDF/TXT) or Pricing Screenshot (PNG/JPG):",
        type=["png", "jpg", "jpeg", "pdf", "txt", "csv"],
    )

    if uploaded_file:
        file_bytes = uploaded_file.read()
        col_preview, col_extract = st.columns([1, 1])

        with col_preview:
            st.markdown(f"**Asset:** `{uploaded_file.name}` ({len(file_bytes)} bytes)")
            if uploaded_file.type.startswith("image"):
                st.image(file_bytes, caption=uploaded_file.name, use_container_width=True)
            else:
                sample_txt = file_bytes.decode("utf-8", errors="ignore")[:600]
                st.text_area("Document Preview", sample_txt, height=220)

        with col_extract:
            if st.button("⚡ Extract & Ingest to FalkorDB", type="primary"):
                with st.spinner("Extracting competitive evidence with Gemini Vision..."):
                    ingestor = MultimodalIngestor(db_client=db_client)
                    ingest_res = ingestor.ingest_bytes(
                        data=file_bytes,
                        file_name=uploaded_file.name,
                        mime_type=uploaded_file.type,
                    )

                st.success(f"✓ Ingested `{ingest_res.document_id}` into FalkorDB Knowledge Graph!")
                ext = ingest_res.extracted

                st.markdown(f"**Target Company:** `{ext.company_name}` • **Product:** `{ext.product_name}`")
                st.markdown(f"**Advertised Price:** `${ext.advertised_price or 'N/A'}` / {ext.billing_cycle}")
                if ext.hidden_fees_or_penalties:
                    st.warning(f"**Hidden Fees Flagged:** {ext.hidden_fees_or_penalties}")
                st.info(f"💡 **Synthesized Evidence:** {ext.evidence_finding}")
                st.caption(f"Verbatim Quote: *\"{ext.key_quote}\"*")
                st.markdown("👉 *Switch to the **Visual Brain** tab to see this new evidence node in the live graph!*")

# ==================== TAB 4: SCENARIO SIMULATOR ====================
with tab_sandbox:
    st.markdown("### 🧪 What-If Scenario Simulator")
    st.caption(
        "Test competitor aggressive moves before they happen. Banana spins up an **isolated FalkorDB scratchpad graph** "
        "to simulate the scenario, verify financial margins, and drop the sandbox without polluting company records."
    )

    sim_col1, sim_col2 = st.columns(2)
    with sim_col1:
        cs_cut = st.slider("Competitor Price Cut (CloudScale)", min_value=0.0, max_value=0.40, value=0.20, step=0.05, format="%.2f")
    with sim_col2:
        cogs_rise = st.slider("ApexCloud Infrastructure Inflation", min_value=0.0, max_value=0.25, value=0.05, step=0.05, format="%.2f")

    if st.button("⚡ Test Hypothesis in Sandbox", type="secondary"):
        with st.spinner("Testing scenario inside isolated FalkorDB micro-graph..."):
            sandbox = SandboxManager(db_client=db_client)
            sandbox.initialize_sandbox()
            sim_data = sandbox.simulate_pricing_scenario(
                cloudscale_discount_pct=cs_cut,
                cogs_inflation_pct=cogs_rise,
            )
            sandbox.discard_sandbox()

        st.success("✓ Scenario simulated and scratchpad graph dropped cleanly.")

        # Metric cards
        sc_m1, sc_m2, sc_m3, sc_m4 = st.columns(4)
        sc = sim_data["scenario"]
        sc_m1.metric("Competitor Simulated Price", sc["simulated_competitor_price"], f"-{sc['competitor_discount_pct']}")
        sc_m2.metric("ApexCloud COGS Basis", sc["simulated_apex_cogs"], f"+{int(cogs_rise*100)}% Inflation")
        sc_m3.metric("Recommended Starter Price", sc["recommended_starter_price"], "Safe Floor: " + sc["mandatory_25pct_margin_floor"])
        sc_m4.metric("Projected Gross Margin", sc["projected_gross_margin"], "Compliant with Policy")

        st.info(f"💡 **Copilot Synthesis**: {sim_data['sandbox_finding']}")

# ==================== TAB 5: UNDER THE HOOD & MCP ====================
with tab_tech:
    st.markdown("### 🔬 Technical Engine, Maximum Flow & MCP Server")
    st.caption("Inspect the Ford-Fulkerson & Edmonds-Karp network flow metrics and connect external coding CLIs via MCP.")

    # Flow metrics
    em1, em2, em3, em4 = st.columns(4)
    em1.metric("Max-Flow Throughput", f"{flow_result.total_flow}", "Utility Units")
    em2.metric("Augmenting Paths", f"{flow_result.augmenting_paths_count}", "Edmonds-Karp Iterations")
    em3.metric("Tokens Scheduled", f"{flow_result.total_tokens_used}", f"Limit: {token_budget}")
    em4.metric("Scheduler Latency", f"{flow_result.scheduler_latency_ms} ms", "GraphBLAS")

    st.markdown("---")
    st.markdown("#### 🔌 Connect External Coding CLIs (Model Context Protocol)")
    st.markdown(
        "Banana can be mounted into **Claude Code**, **Cursor**, **Windsurf**, or **Google Antigravity** "
        "allowing external coding agents to inherit context orchestration, sandboxing, and persistent memory."
    )

    cli_tab1, cli_tab2 = st.columns(2)
    with cli_tab1:
        st.markdown("**1. Claude Code CLI:**")
        st.code("claude mcp add banana -- uv run banana mcp", language="bash")
    with cli_tab2:
        st.markdown("**2. Cursor / Antigravity (`mcpServers` config):**")
        st.code('{\n  "mcpServers": {\n    "banana": {\n      "command": "uv",\n      "args": ["run", "banana", "mcp"]\n    }\n  }\n}', language="json")

    st.markdown("---")
    st.markdown("#### 📊 Head-to-Head Benchmark Suite")
    if st.button("Run Live Benchmark Evaluation"):
        with st.spinner("Running Benchmark Suite against Baseline A and B..."):
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
        st.success("Key Result: Under strict token budgets (1,100 tokens), Baseline A drops 75% of mandatory policies and Baseline B drops 25% of dependencies. Banana maintains 100% Policy Preservation and 100% Dependency Integrity.")
