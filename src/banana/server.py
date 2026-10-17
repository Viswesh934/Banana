"""Banana Local Meeting Bridge Server.

Exposes a lightweight, CORS-enabled HTTP API on localhost:8765 so that the
Floating Banana Chrome Extension or browser injector running on https://meet.google.com
can communicate with FalkorDB in sub-millisecond graph lookups.
"""

import json
from typing import Any, Dict
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
import uvicorn

from banana.db import FalkorDBClient, get_db_client
from banana.meeting_graph import MeetingGraphManager, MeetingTurn, MeetingCommitment, MeetingParticipant


db_client = get_db_client()
meeting_mgr = MeetingGraphManager(db_client)


async def health(request: Request) -> JSONResponse:
    """Check system health and FalkorDB connectivity."""
    db_status = db_client.check_connection()
    return JSONResponse({
        "status": "online",
        "app": "Banana Google Meet Bridge",
        "falkordb": db_status,
    })


async def analyze_turn(request: Request) -> JSONResponse:
    """Analyze real-time spoken text from Google Meet captions or audio buffer.

    Performs sub-500ms graph lookup in FalkorDB and returns instant micro-nudges,
    governance margin alerts, and exact browser tab deep-links.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    text = body.get("text", "").strip()
    speaker = body.get("speaker", "Speaker")
    session_id = body.get("session_id", "meet_live_gmeet")

    text_lower = text.lower()

    # Rule 1: Competitor Pricing & Hidden Fee Detection (CloudScale)
    if "cloudscale" in text_lower or ("800" in text_lower and "flat" in text_lower):
        # Fetch verified evidence from FalkorDB Knowledge Graph
        kg = db_client.get_knowledge_graph()
        cypher = """
        MATCH (c:Company {name: 'CloudScale'})-[:OFFERED_BY]-(p:Product)-[:EVALUATES]-(e:Evidence)
        RETURN e.canonical_id, e.finding, e.quote, e.hidden_fees
        LIMIT 1
        """
        evidence_res = kg.query(cypher)
        finding = (
            "CloudScale's $800 base sticker price masks a $0.08/GB egress surcharge. "
            "A 15TB workload incurs $1,136/mo in overages, bringing true TCO to $1,936/mo!"
        )
        if evidence_res.result_set:
            finding = evidence_res.result_set[0][1] or finding

        return JSONResponse({
            "action": "flash_nudge",
            "alert_type": "info",
            "title": "💡 Banana Micro-Nudge: CloudScale Hidden Egress",
            "nudge": finding,
            "speaker_flagged": speaker,
            "tab_jump": {
                "title": "CloudScale CS-902 Customer Invoice",
                "tab_id": "doc_cloudscale_teardown_2026",
                "url": "https://drive.google.com/file/d/cloudscale_cs902_invoice",
                "quote": "Clause 4.1: Customer agrees to $0.08 per GB egress overage fee beyond 1TB allowance.",
            },
        })

    # Rule 2: Policy Governance Margin Floor Alert ($700/mo breach)
    if "700" in text_lower and ("discount" in text_lower or "offer" in text_lower or "give" in text_lower or "flat" in text_lower):
        # Record breach in FalkorDB
        meeting_mgr.record_policy_breach(
            session_id=session_id,
            speaker_name=speaker,
            proposed_price=700.0,
            policy_id="policy_minimum_margin",
            reason="Proposed $700 price violates mandatory 25% gross margin floor ($750/mo minimum).",
        )
        return JSONResponse({
            "action": "flash_alert",
            "alert_type": "danger",
            "title": "🛑 GOVERNANCE ALERT: Margin Floor Breach",
            "nudge": (
                "Proposed $700/mo violates policy_minimum_margin ($750/mo minimum price floor based on $600 COGS). "
                "Max permitted discount without CFO approval is $750/mo. Counter with our $899 Starter Tier instead!"
            ),
            "speaker_flagged": speaker,
            "policy_id": "policy_minimum_margin",
            "tab_jump": {
                "title": "ApexCloud Pricing Model & Unit Economics",
                "tab_id": "doc_apexcloud_cogs_breakdown",
                "url": "https://docs.google.com/spreadsheets/d/apexcloud_pricing_model_2026",
                "quote": "Rule: Minimum 25% gross margin required on all enterprise SaaS subscriptions.",
            },
        })

    # Rule 3: Counter-Offer & Commitment Alignment ($899 Starter Tier / SLA Promises)
    if (
        ("899" in text_lower and ("starter" in text_lower or "tier" in text_lower))
        or (("commit" in text_lower or "promise" in text_lower or "will send" in text_lower or "agree" in text_lower)
            and ("sla" in text_lower or "pricing" in text_lower or "proposal" in text_lower or "friday" in text_lower or "today" in text_lower or "5 pm" in text_lower))
    ):
        cid = meeting_mgr.record_commitment(
            session_id=session_id,
            commitment=MeetingCommitment(
                commitment_id="com_alex_starter_tier",
                speaker_name=speaker,
                term="Deliver Enterprise Starter Tier ($899/mo, 33.3% gross margin, $0 egress markup)",
                deadline="Friday 5:00 PM",
                assignee=speaker,
                referenced_doc_id="doc_cloudscale_teardown_2026",
            ),
        )
        return JSONResponse({
            "action": "log_commitment",
            "alert_type": "success",
            "title": "✓ Strategy Aligned & Commitment Logged",
            "nudge": f"Agreed commitment recorded into FalkorDB Knowledge Graph: $899/mo Starter Tier (33.3% margin). Assignee: {speaker}.",
            "commitment_id": cid,
        })

    # Default: Idle small-talk / normal discussion -> 0 Tokens burned
    return JSONResponse({
        "action": "idle",
        "alert_type": "none",
        "nudge": None,
        "tokens_burned": 0,
    })


async def get_tabs(request: Request) -> JSONResponse:
    """Return referenced browser tabs available for deep-linking."""
    tabs = [
        {
            "tab_id": "tab1",
            "title": "ApexCloud Pricing Model 2026",
            "url": "https://docs.google.com/spreadsheets/d/apexcloud_pricing_model_2026",
            "preview": "Base COGS: $600/mo | Absolute Price Floor: $750/mo | Enterprise Starter: $899/mo (33.3% Margin)",
        },
        {
            "tab_id": "tab2",
            "title": "Competitor Architectural Matrix",
            "url": "https://docs.google.com/spreadsheets/d/competitor_matrix_2026",
            "preview": "HyperStore: 99.5% SLA, 10% refund cap | DataVanguard: $0.15/Compute Unit, 42% dispute churn",
        },
        {
            "tab_id": "tab3",
            "title": "MegaCorp Workload Spec (15TB Egress)",
            "url": "https://docs.google.com/document/d/megacorp_architecture_brief",
            "preview": "Outbound Egress: 15TB/mo | Database IOPS: 4,000 | HA Requirement: 99.9%",
        },
        {
            "tab_id": "tab4",
            "title": "CloudScale CS-902 Customer Invoice",
            "url": "https://drive.google.com/file/d/cloudscale_cs902_invoice",
            "preview": "Base Tier: $800.00/mo | Egress Surcharge (14.2TB @ $0.08/GB): $1,136.00 | Total Billed: $2,128.50",
            "referenced": True,
        },
    ]
    return JSONResponse({"tabs": tabs})


routes = [
    Route("/api/health", health, methods=["GET"]),
    Route("/api/analyze_turn", analyze_turn, methods=["POST"]),
    Route("/api/tabs", get_tabs, methods=["GET"]),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = Starlette(routes=routes, middleware=middleware)


def run_server(port: int = 8765) -> None:
    """Launch the Banana Google Meet bridge server on specified port."""
    print(f"🍌 Banana Google Meet Bridge running on http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    run_server()
