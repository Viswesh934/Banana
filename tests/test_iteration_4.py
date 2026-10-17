import pytest
from banana.db import FalkorDBClient
from banana.meeting_graph import (
    MeetingCommitment,
    MeetingGraphManager,
    MeetingParticipant,
    MeetingTurn,
)
from banana.seeder import GraphSeeder


@pytest.fixture(scope="module")
def seeded_db() -> FalkorDBClient:
    db = FalkorDBClient()
    seeder = GraphSeeder(db)
    seeder.seed_all(drop_existing=True)
    return db


def test_meeting_session_initialization(seeded_db: FalkorDBClient) -> None:
    mgr = MeetingGraphManager(db_client=seeded_db)
    session_id = "meet_test_01"
    participants = [
        MeetingParticipant(name="Alex Rivera", role="VP Sales", company="ApexCloud"),
        MeetingParticipant(name="Sarah Chen", role="Enterprise Lead", company="MegaCorp"),
        MeetingParticipant(name="You", role="Solutions Architect", company="ApexCloud"),
    ]

    sid = mgr.initialize_session(session_id, "Q3 Enterprise Pricing Sync", participants)
    assert sid == session_id

    # Verify nodes in FalkorDB Knowledge Graph
    kg = seeded_db.get_knowledge_graph()
    cypher = """
    MATCH (s:MeetingSession {canonical_id: $sid})-[:HAS_PARTICIPANT]->(spk:Speaker)
    RETURN count(spk)
    """
    res = kg.query(cypher, {"sid": session_id})
    assert res.result_set[0][0] == 3


def test_meeting_turn_and_tab_reference(seeded_db: FalkorDBClient) -> None:
    mgr = MeetingGraphManager(db_client=seeded_db)
    session_id = "meet_test_01"

    turn = MeetingTurn(
        speaker="Sarah Chen",
        text="CloudScale claims they offer $800/mo flat with no bandwidth fees.",
        timestamp_str="10:14 AM",
        referenced_tab_id="doc_cloudscale_teardown_2026",
        nudge_text="CloudScale $800 base masks $0.08/GB egress. Average 15TB workload actually costs $1,800/mo.",
    )
    res = mgr.record_turn(session_id, turn)
    assert res["status"] == "recorded"

    # Verify turn and tab reference in FalkorDB
    kg = seeded_db.get_knowledge_graph()
    cypher = """
    MATCH (s:MeetingSession {canonical_id: $sid})-[:HAS_TURN]->(t:MeetingTurn)-[:REFERENCED_TAB]->(d:Document)
    RETURN t.speaker, d.canonical_id
    """
    db_res = kg.query(cypher, {"sid": session_id})
    assert len(db_res.result_set) >= 1
    assert db_res.result_set[0][0] == "Sarah Chen"
    assert db_res.result_set[0][1] == "doc_cloudscale_teardown_2026"


def test_policy_breach_detection(seeded_db: FalkorDBClient) -> None:
    mgr = MeetingGraphManager(db_client=seeded_db)
    session_id = "meet_test_01"

    prop_id = mgr.record_policy_breach(
        session_id=session_id,
        speaker_name="Alex Rivera",
        proposed_price=700.0,
        policy_id="policy_minimum_margin",
        reason="Proposed $700 price violates mandatory 25% gross margin floor ($750 minimum).",
    )
    assert prop_id.startswith("prop_")

    # Verify proposal and violation edge to policy
    kg = seeded_db.get_knowledge_graph()
    cypher = """
    MATCH (spk:Speaker)-[:PROPOSED]->(p:Proposal {canonical_id: $pid})-[:VIOLATES]->(pol:Policy)
    RETURN spk.name, p.proposed_price, pol.canonical_id
    """
    res = kg.query(cypher, {"pid": prop_id})
    assert len(res.result_set) == 1
    assert res.result_set[0][0] == "Alex Rivera"
    assert res.result_set[0][1] == 700.0
    assert res.result_set[0][2] == "policy_minimum_margin"


def test_commitment_and_query_graph(seeded_db: FalkorDBClient) -> None:
    mgr = MeetingGraphManager(db_client=seeded_db)
    session_id = "meet_test_01"

    commitment = MeetingCommitment(
        commitment_id="com_alex_starter_tier",
        speaker_name="Alex Rivera",
        term="Offer transparent Enterprise Starter tier at $899/mo (33.3% gross margin)",
        deadline="Friday 5:00 PM",
        assignee="Alex Rivera",
        referenced_doc_id="doc_cloudscale_teardown_2026",
    )
    cid = mgr.record_commitment(session_id, commitment)
    assert cid == "com_alex_starter_tier"

    # Surgical queries on meeting graph
    ans_commit = mgr.query_meeting_graph(session_id, "What did Alex commit to?")
    assert "Alex Rivera" in ans_commit
    assert "$899/mo" in ans_commit
    assert "Friday 5:00 PM" in ans_commit

    ans_tab = mgr.query_meeting_graph(session_id, "What tabs were open or referenced?")
    assert "doc_cloudscale_teardown_2026" in ans_tab

    ans_policy = mgr.query_meeting_graph(session_id, "Were there any margin alerts or policy breaches?")
    assert "$700" in ans_policy
    assert "policy_minimum_margin" in ans_policy


def test_gmeet_bridge_api(seeded_db: FalkorDBClient) -> None:
    from starlette.testclient import TestClient
    from banana.server import app

    client = TestClient(app)

    # 1. Health check
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    data_health = res_health.json()
    assert data_health["status"] == "online"
    assert data_health["falkordb"]["status"] == "ok"

    # 2. Analyze Turn: Competitor mention -> flash nudge + tab jump
    res_nudge = client.post(
        "/api/analyze_turn",
        json={"text": "CloudScale offers $800 flat with no egress overages.", "speaker": "Sarah Chen"},
    )
    assert res_nudge.status_code == 200
    data_nudge = res_nudge.json()
    assert data_nudge["action"] == "flash_nudge"
    assert "0.08" in data_nudge["nudge"]
    assert "CloudScale CS-902" in data_nudge["tab_jump"]["title"]

    # 3. Analyze Turn: Policy margin breach -> flash alert
    res_alert = client.post(
        "/api/analyze_turn",
        json={"text": "Can we offer a discount to $700 flat to win?", "speaker": "Alex Rivera"},
    )
    assert res_alert.status_code == 200
    data_alert = res_alert.json()
    assert data_alert["action"] == "flash_alert"
    assert data_alert["policy_id"] == "policy_minimum_margin"

    # 4. Analyze Turn: Idle small-talk -> zero tokens burned
    res_idle = client.post(
        "/api/analyze_turn",
        json={"text": "Good morning everyone, can you see my screen?", "speaker": "Sarah Chen"},
    )
    assert res_idle.status_code == 200
    data_idle = res_idle.json()
    assert data_idle["action"] == "idle"
    assert data_idle["tokens_burned"] == 0

    # 5. Get active browser tabs
    res_tabs = client.get("/api/tabs")
    assert res_tabs.status_code == 200
    tabs = res_tabs.json()["tabs"]
    assert len(tabs) == 4
    assert any("CloudScale" in t["title"] for t in tabs)

