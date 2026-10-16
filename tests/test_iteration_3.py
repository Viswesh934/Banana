import asyncio
import json
import pytest
from banana.db import FalkorDBClient
from banana.mcp_server import create_mcp_server
from banana.multimodal import MultimodalIngestor
from banana.seeder import GraphSeeder


@pytest.fixture(scope="module")
def seeded_db() -> FalkorDBClient:
    db = FalkorDBClient()
    seeder = GraphSeeder(db)
    seeder.seed_all(drop_existing=True)
    return db


def test_mcp_server_registration(seeded_db: FalkorDBClient) -> None:
    server = create_mcp_server(seeded_db)
    assert server.name == "banana"

    async def check_tools():
        tools = await server.list_tools()
        tool_names = [t.name for t in tools]
        assert "banana_orchestrate_context" in tool_names
        assert "banana_query_knowledge" in tool_names
        assert "banana_simulate_sandbox" in tool_names
        assert "banana_save_decision" in tool_names
        assert "banana_ingest_document" in tool_names

    asyncio.run(check_tools())


def test_mcp_tool_execution(seeded_db: FalkorDBClient) -> None:
    server = create_mcp_server(seeded_db)

    async def execute_tools():
        # 1. Test sandbox simulation tool
        res_sandbox = await server.call_tool(
            "banana_simulate_sandbox",
            {"cloudscale_discount_pct": 0.20, "cogs_inflation_pct": 0.05},
        )
        assert res_sandbox.is_error is False
        parsed_sandbox = json.loads(res_sandbox.content[0].text)
        assert parsed_sandbox["scenario"]["policy_compliant"] is True
        assert "recommended_starter_price" in parsed_sandbox["scenario"]

        # 2. Test context orchestration tool
        res_orch = await server.call_tool(
            "banana_orchestrate_context",
            {"prompt": "Analyze pricing under $750 floor", "token_budget": 1600},
        )
        assert res_orch.is_error is False
        parsed_orch = json.loads(res_orch.content[0].text)
        assert parsed_orch["mandatory_policies_preserved"] is True
        assert parsed_orch["tokens_used"] <= 1600
        assert len(parsed_orch["selected_canonical_ids"]) > 0

        # 3. Test knowledge query tool
        res_query = await server.call_tool(
            "banana_query_knowledge",
            {"query_or_cypher": "CloudScale"},
        )
        assert res_query.is_error is False
        parsed_query = json.loads(res_query.content[0].text)
        assert len(parsed_query["matches"]) > 0

        # 4. Test decision memory tool
        res_mem = await server.call_tool(
            "banana_save_decision",
            {
                "title": "Architectural refactor: MCP Stdio adapter",
                "finding": "Standardized on MCP 2.x MCPServer interface for Claude Code and Cursor.",
            },
        )
        assert res_mem.is_error is False
        parsed_mem = json.loads(res_mem.content[0].text)
        assert parsed_mem["status"] == "success"
        assert parsed_mem["canonical_id"].startswith("mem_decision_")

    asyncio.run(execute_tools())


def test_multimodal_ingestion(seeded_db: FalkorDBClient) -> None:
    ingestor = MultimodalIngestor(db_client=seeded_db)

    # Ingest test fixture invoice
    fixture_path = "tests/fixtures/cloudscale_customer_invoice.txt"
    res = ingestor.ingest_file(fixture_path)

    assert res.document_id.startswith("doc_cloudscale_customer_invoice_")
    assert res.evidence_id.startswith("ev_cloudscale_customer_invoice_")
    assert res.extracted.company_name == "CloudScale"
    assert res.extracted.advertised_price == 800.0
    assert "0.08" in (res.extracted.hidden_fees_or_penalties or "")

    # Query FalkorDB to verify graph nodes and relationships
    kg = seeded_db.get_knowledge_graph()
    cypher = """
    MATCH (doc:Document {canonical_id: $doc_id})-[:PROVIDES_EVIDENCE]->(ev:Evidence {canonical_id: $ev_id})
    MATCH (ev)-[:EVALUATES]->(p:Product)-[:OFFERED_BY]->(c:Company)
    RETURN doc.name, ev.advertised_price, c.name, p.name
    """
    db_res = kg.query(cypher, {"doc_id": res.document_id, "ev_id": res.evidence_id})
    assert len(db_res.result_set) == 1
    assert db_res.result_set[0][0] == "cloudscale_customer_invoice.txt"
    assert db_res.result_set[0][1] == 800.0
    assert db_res.result_set[0][2] == "CloudScale"
