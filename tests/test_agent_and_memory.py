import pytest
from banana.agent import BananaAgent
from banana.db import FalkorDBClient
from banana.memory import MemoryManager
from banana.seeder import GraphSeeder
from banana.tools import AgentTools


@pytest.fixture(scope="module")
def seeded_db() -> FalkorDBClient:
    db = FalkorDBClient()
    seeder = GraphSeeder(db)
    seeder.seed_all(drop_existing=True)
    return db


def test_tools_execution(seeded_db: FalkorDBClient) -> None:
    tools = AgentTools(seeded_db)

    # 1. Search Knowledge Graph
    search_res = tools.search_knowledge_graph("CloudScale")
    assert search_res["match_count"] > 0
    assert any("comp_cloudscale" in m["canonical_id"] for m in search_res["results"])

    # 2. Retrieve Evidence
    ev_res = tools.retrieve_evidence("ev_cloudscale_hidden_egress")
    assert "error" not in ev_res
    assert ev_res["evidence_id"] == "ev_cloudscale_hidden_egress"
    assert ev_res["source_document"]["id"] == "doc_cloudscale_teardown_2026"

    # 3. Compare Competitors
    comp_res = tools.compare_competitors()
    assert comp_res["entity_count"] >= 4
    assert len(comp_res["market_summary"]) >= 4

    # 4. Save Finding
    mem_res = tools.save_finding(
        title="Test Strategic Insight",
        finding="Test content for memory persistence",
        supersedes_id="mem_q2_decision_apex",
    )
    assert mem_res["status"] == "success"
    assert mem_res["canonical_id"].startswith("mem_decision_")


def test_agent_run_grounded(seeded_db: FalkorDBClient) -> None:
    agent = BananaAgent(db_client=seeded_db)
    result = agent.run(
        task_prompt="Evaluate competitor pricing and recommend packaging strategy.",
        token_budget=4000,
        save_to_memory=True,
    )
    assert result.assembly.total_tokens <= 4000
    assert result.margin_verified is True
    assert len(result.evidence_citations) > 0
    assert result.saved_memory_id is not None
    assert "ApexCloud" in result.recommendation


def test_cross_session_memory_and_superseding(seeded_db: FalkorDBClient) -> None:
    mem_mgr = MemoryManager(seeded_db)

    # In previous test, we saved a decision superseding mem_q2_decision_apex
    history = mem_mgr.get_superseded_history()
    assert len(history) >= 1
    assert any(h["superseded_decision_id"] == "mem_q2_decision_apex" for h in history)

    # Verify active memories exclude the superseded one
    active_mems = mem_mgr.get_active_memories()
    active_ids = [m["canonical_id"] for m in active_mems]
    assert "mem_q2_decision_apex" not in active_ids


def test_multi_hop_company_context(seeded_db: FalkorDBClient) -> None:
    mem_mgr = MemoryManager(seeded_db)
    ctx = mem_mgr.multi_hop_company_context("comp_apexcloud")

    assert ctx["company_id"] == "comp_apexcloud"
    assert len(ctx["connected_knowledge_chains"]) > 0
    chain = ctx["connected_knowledge_chains"][0]
    assert chain["product_id"] == "prod_apex_enterprise"
    assert chain["evidence_id"] == "ev_apex_cost_floor"
    assert chain["source_doc_id"] == "doc_apex_cogs_breakdown"
    assert len(ctx["governing_policies"]) >= 3
