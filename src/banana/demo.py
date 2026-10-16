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
from banana.db import FalkorDBClient, get_db_client
from banana.inspector import GraphInspector
from banana.seeder import GraphSeeder


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
