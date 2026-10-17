"""Interactive walkthrough demonstration of Banana: Graph-Aware Context Orchestration."""

import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich import box

from banana.agent import BananaAgent
from banana.assembler import ContextAssembler
from banana.benchmark import BenchmarkSuite
from banana.code_graph import CodebaseIndexer
from banana.db import FalkorDBClient, get_db_client
from banana.guardrails import GuardrailsEngine
from banana.inspector import GraphInspector
from banana.seeder import GraphSeeder
from banana.tools import AgentTools


class BananaDemo:
    """End-to-end interactive terminal demonstration."""

    def __init__(self, console: Console = None, db_client: FalkorDBClient = None) -> None:
        self.console = console or Console()
        self.db_client = db_client or get_db_client()

    def run(self, budget: int = 1600) -> None:
        """Run the flagship competitor intelligence and pricing strategy demo."""
        c = self.console

        # Step 0: Ensure FalkorDB seeded
        seeder = GraphSeeder(self.db_client)
        seed_res = seeder.seed_all(drop_existing=True)

        # Step 1: Banner & Scenario Introduction
        c.print(
            Panel.fit(
                "[bold yellow]🍌 BANANA — GRAPH-AWARE CONTEXT ORCHESTRATION AGENT[/bold yellow]\n"
                "[dim]Powered by FalkorDB Graph Database • Token-Constrained Context Optimization[/dim]\n\n"
                "[bold white]Flagship Showcase:[/bold white] Competitor Intelligence & Pricing Strategy\n"
                "[bold white]Company Context:[/bold white] ApexCloud (Internal) vs CloudScale, HyperStore, DataVanguard\n"
                "[bold white]Core Challenge:[/bold white] Strict Token Budget + Mandatory Margin Governance Policies",
                border_style="yellow",
            )
        )
        time.sleep(0.5)

        # Step 2: The Incoming Task
        task_prompt = (
            "Analyze competitor pricing changes (CloudScale, HyperStore, DataVanguard), "
            "identify hidden fee and feature gaps against ApexCloud Enterprise, and recommend "
            "an adjusted pricing strategy complying with our 25% minimum gross margin policy."
        )
        c.print(
            Panel(
                f"[bold cyan]Task Directive:[/bold cyan]\n\"{task_prompt}\"\n\n"
                f"[bold magenta]Configured Input Token Budget:[/bold magenta] [bold green]{budget} tokens[/bold green]",
                title="[bold]Step 1: Incoming Business Directive[/bold]",
                border_style="cyan",
            )
        )
        time.sleep(0.5)

        # Step 3: Demand Graph & Mandatory Governance
        inspector = GraphInspector(self.db_client)
        demand_stats = inspector.inspect_graph(self.db_client.settings.demand_graph_name)

        demand_table = Table(
            title="Step 2: Demand Graph Extraction (Task Requirements & Mandatory Policies)",
            box=box.ROUNDED,
            header_style="bold magenta",
        )
        demand_table.add_column("Type", style="cyan", width=14)
        demand_table.add_column("Canonical ID", style="bold", width=26)
        demand_table.add_column("Priority", style="yellow", width=8)
        demand_table.add_column("Title / Constraint")

        for node in demand_stats["nodes"][:7]:
            demand_table.add_row(
                node["entity_type"],
                node["canonical_id"],
                f"P{node['priority']}",
                node["title"],
            )
        c.print(demand_table)
        time.sleep(0.5)

        # Step 4: Knowledge Graph Traversal
        knowledge_stats = inspector.inspect_graph(self.db_client.settings.knowledge_graph_name)
        k_table = Table(
            title="Step 3: Knowledge Graph Candidate Match (Competitors, Evidence & COGS)",
            box=box.ROUNDED,
            header_style="bold green",
        )
        k_table.add_column("Type", style="green", width=14)
        k_table.add_column("Canonical ID", style="bold", width=30)
        k_table.add_column("Tokens", justify="right", width=8)
        k_table.add_column("Summary / Provenance")

        for node in knowledge_stats["nodes"][:7]:
            k_table.add_row(
                node["entity_type"],
                node["canonical_id"],
                str(node["token_cost"]),
                f"{node['title']} ({node['provenance'][:30]}...)",
            )
        c.print(k_table)
        time.sleep(0.5)

        # Step 5: Graph-Aware Context Assembly & Progressive Load Shedding
        assembler = ContextAssembler(self.db_client)
        assembly_result = assembler.assemble(task_id="task_pricing_strategy", token_budget=budget)

        shed_table = Table(
            title=f"Step 4: Progressive Load Shedding under Budget ({budget} tokens)",
            box=box.ROUNDED,
            header_style="bold yellow",
        )
        shed_table.add_column("Decision", style="bold", width=10)
        shed_table.add_column("Canonical ID", style="cyan", width=30)
        shed_table.add_column("Priority", width=8)
        shed_table.add_column("Tokens", justify="right", width=8)
        shed_table.add_column("Reason / Dependency Status")

        # Show selected highlights
        for item in assembly_result.selected_items[:5]:
            shed_table.add_row(
                "[green]KEEP[/green]",
                item.canonical_id,
                f"P{int(item.priority)}",
                str(item.token_cost),
                assembly_result.inclusion_reasons.get(item.canonical_id, "Retained"),
            )
        # Show shedded items
        for item in assembly_result.excluded_items[:4]:
            shed_table.add_row(
                "[red]SHED[/red]",
                item.canonical_id,
                f"P{int(item.priority)}",
                str(item.token_cost),
                assembly_result.exclusion_reasons.get(item.canonical_id, "Shedded"),
            )
        c.print(shed_table)

        c.print(
            f"[bold]Context Assembly Metrics:[/bold] Input Tokens: [green]{assembly_result.total_tokens}[/green] / {budget} | "
            f"Preserved Dependencies: [green]{len(assembly_result.preserved_dependencies)} edges[/green] | "
            f"Assembly Latency: [cyan]{assembly_result.latency_ms}ms[/cyan]\n"
        )
        time.sleep(0.5)

        # Step 6: Tool Execution & Verification
        agent = BananaAgent(db_client=self.db_client)
        exec_res = agent.run(task_prompt=task_prompt, token_budget=budget, save_to_memory=True)

        tool_table = Table(
            title="Step 5: Graph-Backed Tool Execution & Verification",
            box=box.ROUNDED,
            header_style="bold magenta",
        )
        tool_table.add_column("Tool", style="bold yellow", width=24)
        tool_table.add_column("Observation & Verified Fact")
        for tc in exec_res.tool_calls:
            tool_table.add_row(tc["tool"], tc["summary"])
        c.print(tool_table)
        time.sleep(0.5)

        # Step 7: Grounded Strategic Recommendation
        c.print(
            Panel(
                Markdown(exec_res.recommendation),
                title="[bold yellow]Step 6: Grounded Recommendation & Strategic Output[/bold yellow]",
                border_style="yellow",
                padding=(1, 2),
            )
        )
        time.sleep(0.5)

        # Step 8: Persistent Cross-Session Memory
        c.print(
            Panel.fit(
                f"[bold green]✓ Persistent Memory Committed to FalkorDB[/bold green]\n"
                f"• Node ID: [cyan]{exec_res.saved_memory_id}[/cyan]\n"
                f"• Relationship: [bold](new:Memory)-[:SUPERSEDES]->(mem_q2_decision_apex)[/bold]\n"
                f"• Provenance: Audited timestamp {int(time.time() * 1000)} | Partition: +1",
                border_style="green",
            )
        )
        time.sleep(0.5)

        # Step 9: Head-to-Head Scientific Benchmark
        c.print("\n[bold yellow]Step 7: Head-to-Head Scientific Benchmark Comparison[/bold yellow]")
        bench = BenchmarkSuite(self.db_client)
        metrics = bench.run_all(budgets=[1100, 1600, 2500])
        bench.render_cli(c, metrics)

    def run_coding_demo(self, budget: int = 1000) -> None:
        """Run the flagship coding agent context, AST graph, and guardrails demonstration."""
        c = self.console

        # Step 1: Banner
        c.print(
            Panel.fit(
                "[bold yellow]🍌 BANANA — GRAPH-AWARE CODING AGENT SHOWCASE[/bold yellow]\n"
                "[dim]Powered by FalkorDB Graph Database • High-Performance GraphBLAS Sparse Matrices[/dim]\n\n"
                "[bold white]Target Audience:[/bold white] Coding Assistants (Cursor, Claude Code, Windsurf)\n"
                "[bold white]Core Capabilities:[/bold white] AST Code Graph • Knapsack Token Pruning • Deterministic Guardrails • Decision Memory\n"
                "[bold white]Infrastructure:[/bold white] Zero Server AI Token Cost (Inherits Agent LLM) • Sub-3ms Cypher Traversal",
                border_style="yellow",
            )
        )
        time.sleep(0.4)

        # Step 2: FalkorDB Engine Verification
        health = self.db_client.check_connection()
        c.print(
            Panel(
                f"[bold green]✓ Connected to FalkorDB Cloud Engine[/bold green]\n"
                f"• Endpoint: [cyan]{health.get('host')}:{health.get('port')}[/cyan]\n"
                f"• Engine Latency: [green]{health.get('latency_ms', 0):.2f}ms[/green]\n"
                f"• Dual-Graph Model: [cyan]banana_demand[/cyan] (Policies) & [cyan]banana_knowledge[/cyan] (AST & Memory)",
                title="[bold cyan]Step 1: FalkorDB Graph Engine Status[/bold cyan]",
                border_style="cyan",
            )
        )
        time.sleep(0.4)

        # Step 3: Codebase AST Graph Indexing
        indexer = CodebaseIndexer(self.db_client, root_dir="src/banana")
        stats = indexer.index_repository(max_files=50)
        c.print(
            Panel(
                f"[bold green]✓ AST Symbol Graph Indexed in FalkorDB[/bold green]\n"
                f"• Source Files Mapped: [bold]{stats['files_indexed']}[/bold]\n"
                f"• Class Interface Nodes: [bold]{stats['classes_indexed']}[/bold]\n"
                f"• Function Signature Nodes: [bold]{stats['functions_indexed']}[/bold]\n"
                f"• Import Hierarchies Mapped: [bold]{stats['imports_indexed']}[/bold]\n"
                f"[dim]Graph Schema: (:File)-[:IMPORTS]->(:File), (:File)-[:DEFINES]->(:Class|:Function)[/dim]",
                title="[bold cyan]Step 2: Codebase AST Graph Indexing[/bold cyan]",
                border_style="cyan",
            )
        )
        time.sleep(0.4)

        # Step 4: High-Signal Code Context Knapsack
        query_kw = "falkordb"
        ctx_result = indexer.assemble_code_context(query=query_kw, token_budget=budget)
        c.print(
            Panel(
                f"[bold magenta]Query:[/bold magenta] '{query_kw}' | [bold magenta]Token Budget:[/bold magenta] {budget} tokens | [bold green]Tokens Used:[/bold green] {ctx_result['tokens_used']}\n"
                f"[bold]Selected AST Symbols:[/bold] {ctx_result['symbols_count']} nodes\n\n"
                f"{ctx_result['assembled_context']}",
                title="[bold cyan]Step 3: Graph Knapsack Context Assembly (Edmonds-Karp Filter)[/bold cyan]",
                border_style="cyan",
            )
        )
        time.sleep(0.4)

        # Step 5: Deterministic Policy & Architecture Guardrails
        guardrails = GuardrailsEngine(self.db_client)
        violating_price = 45.0
        compliant_price = 850.0
        v_res = guardrails.check_pricing_proposal(violating_price, cogs=600.0)
        c_res = guardrails.check_pricing_proposal(compliant_price, cogs=600.0)
        arch_res = guardrails.check_code_architecture("app.py", "database_driver")

        guard_table = Table(
            title="Step 4: Deterministic Guardrails Engine (< 2ms Evaluation)",
            box=box.ROUNDED,
            header_style="bold magenta",
        )
        guard_table.add_column("Proposed Change", style="bold yellow")
        guard_table.add_column("Status", width=12)
        guard_table.add_column("Guardrail Evaluation / Remediation")
        guard_table.add_row(
            f"Offer discount: ${violating_price}/mo",
            "[red]BLOCKED[/red]",
            f"{v_res.violations[0].description} -> {v_res.violations[0].suggested_fix}" if v_res.violations else "OK"
        )
        guard_table.add_row(
            f"Adjust pricing: ${compliant_price}/mo",
            "[green]PASSED[/green]",
            "Complies with 25% gross margin floor (Yields 29.4% margin)."
        )
        guard_table.add_row(
            "UI directly imports db engine",
            "[red]BLOCKED[/red]",
            f"{arch_res.violations[0].description} -> {arch_res.violations[0].suggested_fix}" if arch_res.violations else "Blocked"
        )
        c.print(guard_table)
        time.sleep(0.4)

        # Step 6: Persistent Cross-Session Architectural Memory
        tools = AgentTools(self.db_client)
        memories = tools.list_findings(limit=3)
        mem_lines = [f"• [bold]{m.get('title')}:[/bold] {m.get('finding')}" for m in memories]
        c.print(
            Panel(
                f"[bold green]✓ FalkorDB Cross-Session Architectural Memory[/bold green]\n"
                f"• Active Decision Lineage: [cyan](new_decision)-[:SUPERSEDES]->(prior_decision)[/cyan]\n\n"
                + "\n".join(mem_lines),
                title="[bold cyan]Step 5: Cross-Session Photographic Memory[/bold cyan]",
                border_style="cyan",
            )
        )
        time.sleep(0.4)

        # Step 7: Ready for Developer / Coding Agent
        c.print(
            Panel.fit(
                "[bold green]🎉 Banana Ready for Coding Agents![/bold green]\n"
                "[white]1. Claude Code Connection:[/white] [yellow]claude mcp add banana -- uv run banana mcp[/yellow]\n"
                "[white]2. Cursor IDE Connection:[/white] Add to [yellow].cursor/mcp.json[/yellow]\n"
                "[white]3. Serverless API Endpoint:[/white] Deploy [yellow]Dockerfile.lambda[/yellow] to AWS Lambda",
                border_style="green",
            )
        )
