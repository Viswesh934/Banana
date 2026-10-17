"""Tests for Banana's Autonomous Coding Agent & Zero-Deploy Brain.

Verifies:
1. Embedded local graph engine (zero-Docker fallback).
2. Codebase AST indexing and symbol graph traversal.
3. Code context assembly under strict token budget knapsack.
4. Deterministic policy and architecture guardrails.
5. Coding MCP server tool execution.
"""

import asyncio
import json
import pytest
from pathlib import Path

from banana.code_graph import CodebaseIndexer
from banana.embedded_graph import EmbeddedGraphClient
from banana.guardrails import GuardrailsEngine
from banana.mcp_server import create_mcp_server


def test_embedded_graph_client(tmp_path: Path) -> None:
    """Verify embedded SQLite graph operates without Docker or external servers."""
    client = EmbeddedGraphClient(db_dir=str(tmp_path))
    health = client.check_connection()
    assert health["status"] == "ok"
    assert health["backend"] == "embedded_sqlite"

    # Test create node & edge
    g = client.get_knowledge_graph()
    res = g.query("CREATE (n:ContextNode {id: 'test_sym', title: 'Test Symbol', entity_type: 'Function'})")
    assert len(res.result_set) > 0

    g.query("MERGE (a)-[:DEPENDS_ON]->(b)", {"src_id": "test_sym", "tgt_id": "other_sym"})
    deps = g.query("MATCH (a)-[:DEPENDS_ON]->(b) RETURN a, b")
    assert len(deps.result_set) > 0


def test_codebase_indexer() -> None:
    """Verify local Python AST parser extracts classes, functions, and imports."""
    indexer = CodebaseIndexer(root_dir="src/banana")
    stats = indexer.index_repository(max_files=10)
    assert stats["files_indexed"] > 0
    assert stats["functions_indexed"] > 0

    # Test context assembly under 1500 tokens
    res = indexer.assemble_code_context(query="client", token_budget=1500)
    assert res["tokens_used"] <= 1500
    assert "assembled_context" in res
    assert res["query"] == "client"


def test_guardrails_engine() -> None:
    """Verify deterministic policy and architecture guardrails."""
    engine = GuardrailsEngine()

    # 1. Margin Floor Breach ($700 proposed vs $750 floor based on $600 COGS)
    res_margin_fail = engine.check_pricing_proposal(proposed_price=700.0, cogs=600.0, margin_floor_pct=0.25)
    assert res_margin_fail.compliant is False
    assert len(res_margin_fail.violations) > 0
    assert res_margin_fail.violations[0].rule_id == "policy_minimum_margin"

    # 2. Margin Floor Pass ($899 proposed > $750 floor)
    res_margin_pass = engine.check_pricing_proposal(proposed_price=899.0, cogs=600.0, margin_floor_pct=0.25)
    assert res_margin_pass.compliant is True
    assert len(res_margin_pass.violations) == 0

    # 3. Architecture Layer Boundary: UI importing database directly
    res_arch_fail = engine.check_code_architecture("src/ui/app.py", "database.connection")
    assert res_arch_fail.compliant is False
    assert res_arch_fail.violations[0].rule_id == "arch_layer_violation_db_in_ui"


def test_coding_mcp_tools() -> None:
    """Verify coding agent MCP tools execute properly via create_mcp_server."""
    server = create_mcp_server()

    async def run_mcp_tests():
        # Check tool list
        tools = await server.list_tools()
        names = [t.name for t in tools]
        assert "banana_assemble_code_context" in names
        assert "banana_index_codebase" in names
        assert "banana_check_guardrails" in names
        assert "banana_query_decisions" in names

        # Execute guardrails tool
        res_guard = await server.call_tool(
            "banana_check_guardrails",
            {"action_name": "propose_pricing", "parameters_json": '{"price": 700.0, "cogs": 600.0}'},
        )
        assert res_guard.is_error is False
        parsed_guard = json.loads(res_guard.content[0].text)
        assert parsed_guard["compliant"] is False

        # Execute decision save & query
        await server.call_tool(
            "banana_save_decision",
            {"title": "Adopt Pydantic v2", "finding": "Never use .dict(); use .model_dump()"},
        )
        res_query = await server.call_tool("banana_query_decisions", {"keyword": "Pydantic"})
        parsed_query = json.loads(res_query.content[0].text)
        assert parsed_query["count"] >= 1

    asyncio.run(run_mcp_tests())
