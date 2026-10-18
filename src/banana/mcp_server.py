"""Banana Model Context Protocol (MCP) Server.

Enables external AI coding CLIs (Claude Code, Cursor, Windsurf, Antigravity, Aider)
to inherit Banana's graph-aware context orchestration, sandboxed simulation,
and persistent cross-session memory in FalkorDB.
"""

import json
from typing import Optional
from mcp.server.mcpserver import MCPServer

from banana.assembler import ContextAssembler
from banana.db import FalkorDBClient, get_db_client
from banana.max_flow import MaxFlowScheduler
from banana.sandbox import SandboxManager
from banana.tools import AgentTools


def create_mcp_server(db_client: Optional[FalkorDBClient] = None) -> MCPServer:
    """Create and configure the Banana MCP server."""
    client = db_client or get_db_client()
    server = MCPServer("banana")

    @server.tool()
    def banana_orchestrate_context(prompt: str, token_budget: int = 1600) -> str:
        """Assemble optimal, dependency-preserved context under a strict token budget using Edmonds-Karp Max-Flow.

        Args:
            prompt: The coding task or strategic question.
            token_budget: Maximum tokens allowed for context (e.g. 1600).

        Returns:
            JSON string containing assembled context, preserved policies, shed items, and flow metrics.
        """
        assembler = ContextAssembler(client)
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
        flow_res = scheduler.schedule(
            all_items=all_items,
            dependencies=all_deps,
            token_budget=token_budget,
            reserved_output_tokens=max(200, token_budget // 5),
        )

        selected_items = [all_items[cid] for cid in flow_res.selected_canonical_ids if cid in all_items]
        context_text = "\n\n".join([f"[{it.entity_type.value.upper()}] {it.canonical_id} ({it.title}):\n{it.content}" for it in selected_items])

        return json.dumps({
            "prompt": prompt,
            "token_budget": token_budget,
            "tokens_used": flow_res.total_tokens_used,
            "total_flow_utility": flow_res.total_flow,
            "mandatory_policies_preserved": flow_res.mandatory_policies_preserved,
            "dependency_preservation_pct": flow_res.dependency_preservation_pct,
            "selected_canonical_ids": flow_res.selected_canonical_ids,
            "shed_canonical_ids": flow_res.shedded_canonical_ids,
            "assembled_context": context_text,
        }, indent=2)

    @server.tool()
    def banana_query_knowledge(query_or_cypher: str) -> str:
        """Query FalkorDB knowledge graph for companies, products, policies, or evidence.

        Args:
            query_or_cypher: A Cypher query or keyword search string (e.g., 'CloudScale', 'policy_minimum_margin').

        Returns:
            JSON string with matched graph entities and relationships.
        """
        kg = client.get_knowledge_graph()
        q_upper = query_or_cypher.strip().upper()
        if q_upper.startswith("MATCH") or q_upper.startswith("RETURN"):
            try:
                res = kg.query(query_or_cypher)
                return json.dumps({"result": res.result_set}, indent=2, default=str)
            except Exception as e:
                return json.dumps({"error": f"Cypher execution failed: {str(e)}"}, indent=2)

        # Keyword match across nodes
        cypher = """
        MATCH (n)
        WHERE (n.canonical_id IS NOT NULL AND n.canonical_id CONTAINS $kw)
           OR (n.title IS NOT NULL AND n.title CONTAINS $kw)
           OR (n.content IS NOT NULL AND n.content CONTAINS $kw)
           OR (n.name IS NOT NULL AND n.name CONTAINS $kw)
           OR (n.finding IS NOT NULL AND n.finding CONTAINS $kw)
        RETURN labels(n) AS labels, properties(n) AS props
        LIMIT 15
        """
        try:
            res = kg.query(cypher, {"kw": query_or_cypher})
            records = [{"labels": r[0], "properties": r[1]} for r in res.result_set]
            return json.dumps({"keyword": query_or_cypher, "matches": records}, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": f"Search failed: {str(e)}"}, indent=2)

    @server.tool()
    def banana_simulate_sandbox(cloudscale_discount_pct: float = 0.20, cogs_inflation_pct: float = 0.05) -> str:
        """Spin up an ephemeral FalkorDB micro-graph to simulate competitor price cuts against the 25% margin floor.

        Args:
            cloudscale_discount_pct: Competitor discount to test (e.g., 0.20 for 20%).
            cogs_inflation_pct: ApexCloud COGS cost inflation (e.g., 0.05 for 5%).

        Returns:
            JSON string with simulated financial margins, floor compliance, and synthesis.
        """
        sandbox = SandboxManager(db_client=client)
        sandbox.initialize_sandbox()
        sim_data = sandbox.simulate_pricing_scenario(
            cloudscale_discount_pct=cloudscale_discount_pct,
            cogs_inflation_pct=cogs_inflation_pct,
        )
        sandbox.discard_sandbox()
        return json.dumps(sim_data, indent=2)

    @server.tool()
    def banana_save_decision(title: str, finding: str, supersedes_id: str = "") -> str:
        """Record an architectural decision or strategic lesson learned into FalkorDB persistent memory.

        Args:
            title: Title of the decision or finding.
            finding: Grounded description and policy context.
            supersedes_id: Canonical ID of a prior decision this replaces (optional).

        Returns:
            JSON string with created Memory node ID and lineage status.
        """
        tools = AgentTools(client)
        sup_id = supersedes_id if supersedes_id.strip() else None
        res = tools.save_finding(title=title, finding=finding, supersedes_id=sup_id)
        return json.dumps(res, indent=2)

    @server.tool()
    def banana_query_decisions(keyword: str = "") -> str:
        """Query past architectural decisions and strategic lessons learned from persistent memory.

        Args:
            keyword: Optional search keyword to filter past decisions.

        Returns:
            JSON string containing past decision records with supersedes lineage.
        """
        tools = AgentTools(client)
        findings = tools.list_findings(limit=20)
        if keyword:
            kw = keyword.lower()
            findings = [f for f in findings if kw in f.get("title", "").lower() or kw in f.get("finding", "").lower()]
        return json.dumps({"count": len(findings), "decisions": findings}, indent=2)

    @server.tool()
    def banana_index_codebase(root_path: str = ".") -> str:
        """Scan and index the local codebase AST (classes, functions, imports) into the repository graph.

        Args:
            root_path: Root directory to scan (defaults to current working directory).

        Returns:
            JSON string with statistics of indexed files, classes, and dependencies.
        """
        from banana.code_graph import CodebaseIndexer
        indexer = CodebaseIndexer(db_client=client, root_dir=root_path)
        stats = indexer.index_repository()
        return json.dumps({"status": "complete", "root_path": root_path, "stats": stats}, indent=2)

    @server.tool()
    def banana_assemble_code_context(query: str, token_budget: int = 1500) -> str:
        """Assemble high-signal code context (signatures, interfaces, prerequisite symbols) under a strict token budget.

        Args:
            query: The coding task or feature symbol (e.g., 'auth', 'database', 'pricing').
            token_budget: Maximum tokens allowed for context (defaults to 1500).

        Returns:
            JSON string with assembled code snippets, symbols count, and token usage.
        """
        from banana.code_graph import CodebaseIndexer
        indexer = CodebaseIndexer(db_client=client)
        result = indexer.assemble_code_context(query=query, token_budget=token_budget)
        return json.dumps(result, indent=2)

    @server.tool()
    def banana_check_guardrails(action_name: str, parameters_json: str = "{}") -> str:
        """Verify proposed code edits or pricing actions against deterministic architectural invariants and policy floors.

        Args:
            action_name: The action being checked (e.g. 'propose_pricing', 'import_module').
            parameters_json: JSON string with parameters (e.g. '{"price": 700.0}' or '{"source_file": "app.py", "imported_module": "banana.db"}').

        Returns:
            JSON string with compliance status, list of violations, and recommended fixes.
        """
        from banana.guardrails import GuardrailsEngine
        try:
            params = json.loads(parameters_json)
        except Exception:
            params = {}
        engine = GuardrailsEngine(db_client=client)
        res = engine.check_generic_action(action_name, params)
        return json.dumps(res.model_dump(), indent=2)

    @server.tool()
    def banana_ingest_document(file_path: str) -> str:
        """Ingest an invoice, contract, or screenshot into FalkorDB knowledge graph memory.

        Args:
            file_path: Absolute or relative path to the image, PDF, or text file.

        Returns:
            JSON string with extracted structured evidence and created FalkorDB graph nodes.
        """
        from banana.multimodal import MultimodalIngestor
        ingestor = MultimodalIngestor(db_client=client)
        res = ingestor.ingest_file(file_path)
        return json.dumps(res.model_dump(), indent=2)

    return server


def create_remote_mcp_server(remote_url: str) -> MCPServer:
    """Create a lightweight proxy MCP server that routes tool calls to a remote AWS Lambda Function URL."""
    import urllib.request
    server = MCPServer("banana-remote")

    def _call_lambda(action: str, params: dict) -> str:
        req = urllib.request.Request(
            remote_url,
            data=json.dumps({"action": action, "params": params}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except Exception as exc:
            return json.dumps({"error": f"Remote Lambda request failed: {str(exc)}"})

    @server.tool()
    def banana_health_check() -> str:
        """Check live connection and latency to remote Banana Lambda and FalkorDB Cloud."""
        return _call_lambda("health", {})

    @server.tool()
    def banana_orchestrate_context(prompt: str, token_budget: int = 1600) -> str:
        """Assemble optimal, dependency-preserved context under a strict token budget using Edmonds-Karp Max-Flow."""
        return _call_lambda("orchestrate", {"prompt": prompt, "token_budget": token_budget})

    @server.tool()
    def banana_guardrails(action_name: str, parameters_json: str) -> str:
        """Validate proposed code or business decisions against deterministic margin and architecture guardrails."""
        try:
            params = json.loads(parameters_json)
        except Exception:
            params = {}
        return _call_lambda("guardrails", params)

    @server.tool()
    def banana_query_decisions(keyword: str = "") -> str:
        """Query past architectural decisions and strategic lessons learned from persistent memory."""
        return _call_lambda("query_decisions", {"keyword": keyword, "limit": 20})

    @server.tool()
    def banana_query_knowledge(query_or_cypher: str) -> str:
        """Query FalkorDB knowledge graph for companies, products, policies, or Cypher queries."""
        return _call_lambda("query", {"query": query_or_cypher})

    return server


def run_mcp_server(transport: str = "stdio", remote_url: Optional[str] = None) -> None:
    """Run the Banana MCP server on stdio or specified transport (local or remote proxy)."""
    if remote_url:
        server = create_remote_mcp_server(remote_url)
    else:
        server = create_mcp_server()
    server.run(transport=transport)
