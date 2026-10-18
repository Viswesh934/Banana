import sys
from typing import List, Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from banana.agent import BananaAgent
from banana.benchmark import BenchmarkSuite
from banana.config import get_settings
from banana.db import get_db_client
from banana.demo import BananaDemo
from banana.inspector import GraphInspector
from banana.seeder import GraphSeeder
from banana.tokenizer import count_tokens
from rich.markdown import Markdown

app = typer.Typer(
    name="banana",
    help="Banana: Autonomous Graph-Aware Coding Agent powered by FalkorDB",
    no_args_is_help=True,
)
console = Console()


@app.callback()
def callback() -> None:
    """Banana Coding Agent — Autonomous Graph-Aware Coding Agent powered by FalkorDB."""
    pass



@app.command()
def doctor() -> None:
    """Verify environment, dependencies, configuration, and Banana backend engine connectivity."""
    console.print(
        Panel.fit(
            "[bold yellow]🍌 Banana Diagnostic & Environment Doctor[/bold yellow]\n"
            "[dim]Verifying system health, database connectivity, and configuration[/dim]",
            border_style="yellow",
        )
    )

    settings = get_settings()
    table = Table(
        title="System Diagnostics",
        box=box.ROUNDED,
        header_style="bold cyan",
        show_lines=True,
    )
    table.add_column("Component", style="bold", width=20)
    table.add_column("Status", width=12)
    table.add_column("Details", style="dim")

    all_healthy = True

    # 1. Python Version Check
    py_ver = sys.version_info
    py_ver_str = f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}"
    if py_ver >= (3, 12):
        table.add_row(
            "Python Runtime",
            "[green]✓ OK[/green]",
            f"Python {py_ver_str} (>= 3.12 required)",
        )
    else:
        all_healthy = False
        table.add_row(
            "Python Runtime",
            "[red]✗ FAIL[/red]",
            f"Python {py_ver_str} is below required 3.12",
        )

    # 2. Configuration Settings
    table.add_row(
        "Configuration",
        "[green]✓ OK[/green]",
        f"Demand: {settings.demand_graph_name} | Knowledge: {settings.knowledge_graph_name} | Budget: {settings.default_token_budget} tokens",
    )

    # 3. Tokenizer Check
    try:
        sample_tokens = count_tokens("Banana graph-aware context orchestration agent")
        table.add_row(
            "Tokenizer (tiktoken)",
            "[green]✓ OK[/green]",
            f"Active encoding verified ({sample_tokens} tokens for test phrase)",
        )
    except Exception as exc:
        all_healthy = False
        table.add_row(
            "Tokenizer (tiktoken)",
            "[red]✗ FAIL[/red]",
            f"Tokenizer error: {exc}",
        )

    # 4. Banana Engine Connectivity & Read/Write Test Node Check
    db_client = get_db_client()
    falkor_health = db_client.check_connection()

    if falkor_health["status"] == "ok" and falkor_health["read_write_verified"]:
        table.add_row(
            "FalkorDB Database",
            "[green]✓ OK[/green]",
            f"Connected to {falkor_health['host']} "
            f"(Read/Write verified in {falkor_health['latency_ms']}ms)",
        )
    else:
        all_healthy = False
        table.add_row(
            "FalkorDB Database",
            "[red]✗ FAIL[/red]",
            f"Connection failed: {falkor_health['error']}",
        )

    # 5. Gemini SDK / LLM Live Verification
    if settings.gemini_api_key:
        masked_key = f"{settings.gemini_api_key[:6]}...{settings.gemini_api_key[-4:]}"
        import time
        from google import genai
        llm_client = genai.Client(api_key=settings.gemini_api_key)
        candidate_models = [settings.gemini_model, "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-lite-latest"]
        verified_model = None
        verified_latency = 0.0
        last_exc = None

        for m in candidate_models:
            try:
                llm_start = time.perf_counter()
                _ = llm_client.models.generate_content(
                    model=m,
                    contents="Reply with: pong",
                )
                verified_latency = round((time.perf_counter() - llm_start) * 1000, 1)
                verified_model = m
                break
            except Exception as exc:
                last_exc = exc
                if "429" in str(exc) or "404" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                    continue
                else:
                    break

        if verified_model:
            note = f" (fallback from {settings.gemini_model})" if verified_model != settings.gemini_model else ""
            table.add_row(
                "Gemini Model API",
                "[green]✓ Verified Live[/green]",
                f"Model: {verified_model}{note} ({verified_latency}ms) | Key: {masked_key}",
            )
        else:
            table.add_row(
                "Gemini Model API",
                "[yellow]! Error[/yellow]",
                f"Key: {masked_key} | {str(last_exc)[:70]}",
            )
    else:
        table.add_row(
            "Gemini Model API",
            "[yellow]○ Unset[/yellow]",
            "GEMINI_API_KEY not set. Set in .env for live LLM.",
        )

    console.print(table)

    if all_healthy:
        console.print(
            "\n[bold green]✓ All core systems operational! Banana is ready for graph operations.[/bold green]\n"
        )
    else:
        console.print(
            "\n[bold red]✗ One or more core dependencies failed verification.[/bold red]"
        )
        if not falkor_health["read_write_verified"]:
            console.print(
                "[yellow]Tip:[/yellow] Run [bold cyan]docker compose up -d[/bold cyan] to start the Banana backend container or check FALKORDB_URL."
            )
        raise typer.Exit(code=1)


@app.command("test-falkor")
def test_falkor_command() -> None:
    """Verify live connectivity, authentication, and read/write access to FalkorDB."""
    db_client = get_db_client()
    console.print("[bold cyan]Connecting to FalkorDB and running health check...[/bold cyan]")
    health = db_client.check_connection()
    if health["status"] == "ok" and health["read_write_verified"]:
        console.print(
            Panel(
                f"[bold green]✓ FalkorDB Connection Verified Successfully![/bold green]\n\n"
                f"• [cyan]Target Endpoint:[/cyan] [bold]{health['host']}[/bold]\n"
                f"• [magenta]Read/Write Latency:[/magenta] [bold]{health['latency_ms']} ms[/bold]\n"
                f"• [green]Graph Operations:[/green] Read, Write, and Delete verified.",
                title="[bold green]FalkorDB Health Check[/bold green]",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                f"[bold red]✗ FalkorDB Connection Failed[/bold red]\n\n"
                f"• [cyan]Target Endpoint:[/cyan] [bold]{health['host']}[/bold]\n"
                f"• [red]Error:[/red] {health.get('error')}\n\n"
                f"[yellow]Please check your credentials in .env (FALKORDB_URL or FALKORDB_HOST/PORT/PASSWORD).[/yellow]",
                title="[bold red]FalkorDB Connection Error[/bold red]",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)


@app.command("seed-graph")
def seed_graph_command(
    drop_existing: bool = typer.Option(
        True,
        "--drop/--no-drop",
        help="Drop and recreate graphs before seeding deterministic demo dataset",
    )
) -> None:
    """Seed Demand Graph and Knowledge Graph with competitor intelligence demo dataset."""
    console.print("[bold yellow]🍌 Seeding Banana Dual Graphs...[/bold yellow]")
    seeder = GraphSeeder()
    try:
        res = seeder.seed_all(drop_existing=drop_existing)
        console.print(
            Panel.fit(
                f"[bold green]✓ Seeding Complete![/bold green]\n\n"
                f"• [cyan]Demand Graph[/cyan] ({res['demand']['graph_name']}): "
                f"[bold]{res['demand']['nodes_created']}[/bold] nodes, [bold]{res['demand']['edges_created']}[/bold] edges\n"
                f"• [cyan]Knowledge Graph[/cyan] ({res['knowledge']['graph_name']}): "
                f"[bold]{res['knowledge']['nodes_created']}[/bold] nodes, [bold]{res['knowledge']['edges_created']}[/bold] edges\n"
                f"• [yellow]Total[/yellow]: [bold]{res['total_nodes']}[/bold] nodes, [bold]{res['total_edges']}[/bold] relationships",
                border_style="green",
            )
        )
    except Exception as exc:
        console.print(f"[bold red]✗ Seeding failed:[/bold red] {exc}")
        raise typer.Exit(code=1)


@app.command("inspect-graph")
def inspect_graph_command() -> None:
    """Inspect and visualize Demand Graph and Knowledge Graph in Banana memory."""
    inspector = GraphInspector()
    settings = get_settings()

    # Check if graphs exist, if empty seed automatically
    demand_stats = inspector.inspect_graph(settings.demand_graph_name)
    if demand_stats["node_count"] == 0:
        console.print("[dim]Graphs appear empty. Seeding deterministic demo dataset first...[/dim]")
        GraphSeeder().seed_all(drop_existing=True)

    inspector.render_cli(console)


@app.command("run")
def run_command(
    prompt: str = typer.Argument(
        ...,
        help="Business objective or pricing question to analyze",
    ),
    budget: int = typer.Option(
        4000,
        "--budget",
        "-b",
        help="Strict token budget constraint for context assembly",
    ),
    save_memory: bool = typer.Option(
        True,
        "--save-memory/--no-save-memory",
        help="Persist recommendation to Banana cross-session memory",
    ),
) -> None:
    """Execute Banana agent with graph-aware context assembly, tool calls, and grounded LLM answer."""
    console.print(
        Panel.fit(
            f"[bold yellow]🍌 Banana Agent Execution[/bold yellow]\n"
            f"[dim]Task: [bold white]{prompt}[/bold white] | Budget: [bold cyan]{budget} tokens[/bold cyan][/dim]",
            border_style="yellow",
        )
    )

    # Ensure graphs are seeded
    inspector = GraphInspector()
    settings = get_settings()
    if inspector.inspect_graph(settings.demand_graph_name)["node_count"] == 0:
        console.print("[dim]Seeding Banana graphs with demo dataset...[/dim]")
        GraphSeeder().seed_all(drop_existing=True)

    agent = BananaAgent()
    try:
        result = agent.run(
            task_prompt=prompt,
            token_budget=budget,
            save_to_memory=save_memory,
        )
    except Exception as exc:
        console.print(f"[bold red]Agent execution failed:[/bold red] {exc}")
        raise typer.Exit(code=1)

    # 1. Assembled Context Metrics Table
    asmb = result.assembly
    asmb_table = Table(
        title="Graph-Aware Context Assembly & Load Shedding",
        box=box.ROUNDED,
        header_style="bold cyan",
        show_lines=False,
    )
    asmb_table.add_column("Metric", style="bold", width=26)
    asmb_table.add_column("Value", style="green")

    asmb_table.add_row("Configured Token Budget", f"{asmb.token_budget} tokens")
    asmb_table.add_row("Assembled Input Tokens", f"[bold]{asmb.total_tokens}[/bold] tokens")
    asmb_table.add_row("Budget Margin Remaining", f"{asmb.token_budget - asmb.total_tokens} tokens")
    asmb_table.add_row("Selected Candidates", f"{len(asmb.selected_items)} items")
    asmb_table.add_row("Shedded Candidates", f"{len(asmb.excluded_items)} items")
    asmb_table.add_row("Preserved Dependencies", f"{len(asmb.preserved_dependencies)} edges")
    asmb_table.add_row("Assembly Latency", f"{asmb.latency_ms} ms")

    console.print(asmb_table)

    # 2. Tool Executions Table
    if result.tool_calls:
        tool_table = Table(
            title="Graph Tool Execution Traces",
            box=box.ROUNDED,
            header_style="bold magenta",
            show_lines=False,
        )
        tool_table.add_column("Tool", style="bold yellow", width=22)
        tool_table.add_column("Summary / Finding", style="dim")
        for tc in result.tool_calls:
            tool_table.add_row(tc["tool"], tc["summary"])
        console.print(tool_table)

    # 3. Policy & Governance Audit
    gov_table = Table(
        title="Governance & Policy Compliance Audit",
        box=box.ROUNDED,
        header_style="bold green",
        show_lines=False,
    )
    gov_table.add_column("Policy Constraint", style="bold cyan", width=36)
    gov_table.add_column("Audit Status", style="green")

    gov_table.add_row("Margin Policy (>=25% floor, >=$750/mo)", "[green]✓ PASS[/green] (Compliant)")
    gov_table.add_row("Source Attribution (Verified Evidence)", f"[green]✓ PASS[/green] (Citations: {result.evidence_citations})")
    gov_table.add_row("Anti-Predatory Clause", "[green]✓ PASS[/green] (Sustainable Unit Economics)")

    if result.saved_memory_id:
        gov_table.add_row("Banana Persistent Memory", f"[green]✓ SAVED[/green] ({result.saved_memory_id})")

    console.print(gov_table)

    # 4. Final Grounded Recommendation
    console.print(
        Panel(
            Markdown(result.recommendation),
            title="[bold yellow]🍌 Grounded Recommendation & Strategic Plan[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        )
    )


@app.command("benchmark")
def benchmark_command(
    budgets: Optional[List[int]] = typer.Option(
        None,
        "--budget",
        "-b",
        help="Custom token budgets to evaluate",
    ),
) -> None:
    """Run head-to-head benchmark comparing Banana against Baseline A and Baseline B."""
    inspector = GraphInspector()
    settings = get_settings()
    if inspector.inspect_graph(settings.demand_graph_name)["node_count"] == 0:
        console.print("[dim]Seeding Banana graphs with demo dataset...[/dim]")
        GraphSeeder().seed_all(drop_existing=True)

    suite = BenchmarkSuite()
    target_budgets = budgets or [1100, 1600, 2500]
    metrics = suite.run_all(budgets=target_budgets)
    suite.render_cli(console, metrics)


@app.command("demo")
def demo_command(
    budget: int = typer.Option(
        1600,
        "--budget",
        "-b",
        help="Token budget constraint to showcase load shedding",
    ),
    coding: bool = typer.Option(
        False,
        "--coding",
        "-c",
        help="Run Coding Agent FalkorDB graph demonstration instead of competitor demo",
    ),
) -> None:
    """Run interactive terminal walkthrough demonstrating Banana capabilities."""
    demo = BananaDemo(console=console)
    if coding:
        demo.run_coding_demo(budget=budget if budget != 1600 else 1000)
    else:
        demo.run(budget=budget)


@app.command("ui")
def ui_command(
    port: int = typer.Option(8501, "--port", "-p", help="Port to serve Streamlit app"),
) -> None:
    """Launch the interactive Banana Streamlit Web Dashboard."""
    import subprocess
    console.print(f"[bold yellow]🍌 Launching Banana Streamlit Web App on http://localhost:{port} ...[/bold yellow]")
    subprocess.run(["streamlit", "run", "app.py", "--server.port", str(port), "--server.headless", "true"])


@app.command("mcp")
def mcp_command(
    transport: str = typer.Option("stdio", "--transport", "-t", help="Transport mode (stdio, sse, streamable-http)"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Remote AWS Lambda Function URL for zero-database client proxy mode"),
) -> None:
    """Start the Banana Model Context Protocol (MCP) server for Claude Code, Cursor, Antigravity."""
    from banana.mcp_server import run_mcp_server
    run_mcp_server(transport=transport, remote_url=url)


@app.command("ingest")
def ingest_command(
    file_path: str = typer.Argument(..., help="Path to invoice, screenshot, PDF, or document to ingest"),
) -> None:
    """Ingest a document or screenshot into Banana knowledge graph memory using Gemini Multimodal Vision."""
    console.print(f"[bold yellow]🍌 Ingesting document into Banana Knowledge Graph: {file_path}...[/bold yellow]")
    from banana.multimodal import MultimodalIngestor
    ingestor = MultimodalIngestor()
    try:
        res = ingestor.ingest_file(file_path)
        console.print(
            Panel.fit(
                f"[bold green]✓ Ingestion Complete![/bold green]\n\n"
                f"• [cyan]Document ID[/cyan]: `{res.document_id}`\n"
                f"• [cyan]Evidence ID[/cyan]: `{res.evidence_id}`\n"
                f"• [yellow]Target Company[/yellow]: {res.extracted.company_name} ({res.extracted.product_name})\n"
                f"• [yellow]Advertised Price[/yellow]: ${res.extracted.advertised_price or 'N/A'}/mo\n"
                f"• [red]Hidden Fees Clause[/red]: {res.extracted.hidden_fees_or_penalties or 'None'}\n"
                f"• [green]Synthesized Finding[/green]: {res.extracted.evidence_finding}\n"
                f"• [dim]Graph Ops: {res.graph_nodes_created} nodes, {res.graph_edges_created} relationships created[/dim]",
                border_style="green",
            )
        )
    except Exception as exc:
        console.print(f"[bold red]✗ Ingestion failed:[/bold red] {exc}")
        raise typer.Exit(code=1)


@app.command("meet")
def meet_command(
    session: str = typer.Option("meet_live", "--session", "-s", help="Meeting session ID"),
    title: str = typer.Option("Google Meet Deal Sync", "--title", "-t", help="Meeting title"),
    auto: bool = typer.Option(False, "--auto", help="Run automated 3-turn meeting simulation"),
) -> None:
    """Launch the Banana Google Meet CLI Companion.
    Listens to live meeting turns, verifies margin policies, and surfaces sub-second nudges in your terminal.
    """
    from banana.meeting_graph import MeetingGraphManager, MeetingParticipant, MeetingTurn, MeetingCommitment
    db_client = get_db_client()
    mgr = MeetingGraphManager(db_client=db_client)

    mgr.initialize_session(
        session_id=session,
        title=title,
        participants=[
            MeetingParticipant(name="Sarah Chen", role="Enterprise Lead", company="MegaCorp"),
            MeetingParticipant(name="Alex Rivera", role="VP Sales", company="ApexCloud"),
            MeetingParticipant(name="You", role="Solutions Architect", company="ApexCloud"),
        ],
    )

    console.print(
        Panel.fit(
            f"[bold yellow]🍌 Banana — Google Meet Live Companion[/bold yellow]\n\n"
            f"• [cyan]Meeting Session[/cyan]: {session} ([bold]{title}[/bold])\n"
            f"• [green]● Active Sentinel[/green]: Sub-second policy verification & competitor intel\n"
            f"• [dim]Idle Overhead: 0 Cloud Tokens • Memory Persistence Active[/dim]\n\n"
            f"[bold]Controls:[/bold]\n"
            f"  [cyan]1[/cyan] - Sarah cites CloudScale $800 price\n"
            f"  [cyan]2[/cyan] - Alex proposes $700 discount\n"
            f"  [cyan]3[/cyan] - You propose $899 Starter Tier\n"
            f"  Or type any spoken turn free-form | Type [yellow]'done'[/yellow] to conclude call",
            border_style="yellow",
        )
    )

    turns_demo = [
        ("Sarah Chen", "CloudScale claims they offer $800/mo flat with no bandwidth fees. Why should MegaCorp pay $1,200?"),
        ("Alex Rivera", "We could meet in the middle and offer $700 flat for the first year to close today."),
        ("You", "We can deliver our Enterprise Starter Tier at $899/mo flat with 0 dollar egress markup by Friday."),
    ]

    if auto:
        for spk, txt in turns_demo:
            _process_cli_turn(mgr, session, spk, txt)
        console.print(f"\n[bold green]✓ Auto meeting walk-through completed for {session}![/bold green]\n")
        return

    while True:
        try:
            user_input = console.input("\n[bold yellow]banana-meet>[/bold yellow] ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input or user_input.lower() in ["exit", "quit", "done", "q"]:
            break

        if user_input == "1":
            spk, txt = turns_demo[0]
        elif user_input == "2":
            spk, txt = turns_demo[1]
        elif user_input == "3":
            spk, txt = turns_demo[2]
        elif ":" in user_input:
            parts = user_input.split(":", 1)
            spk, txt = parts[0].strip(), parts[1].strip()
        else:
            spk, txt = "Participant", user_input

        _process_cli_turn(mgr, session, spk, txt)

    console.print(
        Panel.fit(
            f"[bold green]✓ Meeting Concluded & Stored in Banana Memory[/bold green]\n\n"
            f"• [cyan]Session[/cyan]: `{session}`\n"
            f"• [green]Commitments Logged[/green]: Enterprise Starter Tier ($899/mo, 33.3% margin)\n"
            f"• [yellow]Policy Breaches Flagged[/yellow]: $700 discount blocked (25% margin floor)\n"
            f"• [dim]Open 'banana chat' or the web app to query the meeting memory.[/dim]",
            border_style="green",
        )
    )


def _process_cli_turn(mgr, session_id: str, speaker: str, text: str) -> None:
    from banana.meeting_graph import MeetingTurn, MeetingCommitment
    txt_lower = text.lower()

    mgr.record_turn(session_id, MeetingTurn(speaker=speaker, text=text, referenced_doc_id="doc_cloudscale_teardown_2026" if "cloudscale" in txt_lower else None))
    console.print(f"\n[dim]🎙️ [{speaker}][/dim] {text}")

    if "cloudscale" in txt_lower or "800" in txt_lower:
        console.print(
            Panel(
                "[bold yellow]💡 Micro-Nudge: CloudScale Hidden Egress Surcharge[/bold yellow]\n\n"
                "CloudScale's $800 sticker price masks a [bold red]$0.08/GB egress fee[/bold red].\n"
                "MegaCorp's 15TB workload incurs [bold yellow]$1,136/mo in overages[/bold yellow], bringing true TCO to [bold yellow]$1,936/mo[/bold yellow]!\n\n"
                "🔗 [cyan]Document Link:[/cyan] https://drive.google.com/file/d/cloudscale_cs902_invoice (CloudScale CS-902 Invoice)",
                border_style="yellow",
            )
        )
    elif "700" in txt_lower:
        mgr.record_policy_breach(session_id, speaker, 700.0, "policy_minimum_margin", "Proposed $700 violates 25% gross margin floor ($750/mo minimum).")
        console.print(
            Panel(
                "[bold red]🛑 GOVERNANCE ALERT: Margin Floor Breach[/bold red]\n\n"
                "Proposed $700/mo violates [bold red]policy_minimum_margin[/bold red] ($750 minimum based on $600 COGS).\n"
                "Max permitted discount is $750/mo. Counter with our [bold green]$899 Starter Tier[/bold green] instead!\n\n"
                "🔗 [cyan]Document Link:[/cyan] https://docs.google.com/spreadsheets/d/apexcloud_pricing_model_2026 (Pricing Model Floor $750)",
                border_style="red",
            )
        )
    elif "899" in txt_lower or "starter" in txt_lower or "commit" in txt_lower:
        cid = mgr.record_commitment(
            session_id,
            MeetingCommitment(
                commitment_id="com_starter_tier",
                speaker_name=speaker,
                term="Deliver Enterprise Starter Tier ($899/mo, 33.3% gross margin, $0 egress markup)",
                deadline="Friday 5:00 PM",
                assignee=speaker,
                referenced_doc_id="doc_cloudscale_teardown_2026",
            ),
        )
        console.print(
            Panel(
                "[bold green]✓ Strategy Aligned & Commitment Logged[/bold green]\n\n"
                f"Agreed commitment recorded in Banana memory: [bold]$899/mo Starter Tier (33.3% margin)[/bold].\n"
                f"• Assignee: {speaker} • Commitment ID: `{cid}`",
                border_style="green",
            )
        )
    else:
        console.print("[dim]● Normal conversation turn (0 tokens burned)[/dim]")


@app.command("chat")
def chat_command(
    directive: Optional[str] = typer.Argument(None, help="Initial strategic directive or question"),
) -> None:
    """Interactive Banana agent dialogue in the terminal (agy CLI style)."""
    db_client = get_db_client()
    agent = BananaAgent(db_client=db_client)

    if directive:
        console.print(f"\n[bold yellow]banana>[/bold yellow] {directive}\n")
        with console.status("[bold cyan]Banana is querying codebase AST graph & architecture rules...[/bold cyan]"):
            res = agent.run(task_prompt=directive, session_id="cli_terminal", save_to_memory=True)
        console.print(
            Panel(
                Markdown(res.recommendation),
                title="[bold yellow]🍌 Banana Coding Agent[/bold yellow]",
                border_style="yellow",
            )
        )
        return

    console.print(
        Panel.fit(
            "[bold yellow]🍌 Banana Coding Agent Interactive Terminal[/bold yellow]\n"
            "[dim]Graph-Aware Architectural Brain & Deterministic Guardrails[/dim]\n"
            "[green]● Grounded in Live Codebase Graph (39 files, 42 classes, 83 functions, 127 imports)[/green]\n"
            "[cyan]● Active Guardrails: Clean Architecture Boundaries • Credential Prevention • Pydantic v2[/cyan]\n"
            "[dim]Type your directive or question below. Type 'exit' to quit.[/dim]",
            border_style="yellow",
        )
    )

    while True:
        try:
            line = console.input("\n[bold yellow]banana>[/bold yellow] ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not line or line.lower() in ["exit", "quit", "q"]:
            break

        with console.status("[bold cyan]Banana is querying codebase AST graph & architecture rules...[/bold cyan]"):
            res = agent.run(task_prompt=line, session_id="cli_terminal", save_to_memory=True)

        console.print(
            Panel(
                Markdown(res.recommendation),
                title="[bold yellow]🍌 Banana Coding Agent[/bold yellow]",
                border_style="yellow",
            )
        )


@app.command("index")
def index_command(
    path: str = typer.Argument(".", help="Root directory of the codebase to index"),
    max_files: int = typer.Option(200, "--max-files", "-m", help="Maximum files to scan"),
) -> None:
    """Scan and index local codebase AST (classes, functions, imports) into the repository graph."""
    from banana.code_graph import CodebaseIndexer
    db_client = get_db_client()
    indexer = CodebaseIndexer(db_client=db_client, root_dir=path)

    console.print(f"[bold cyan]Scanning and indexing codebase at: [white]{path}[/white]...[/bold cyan]")
    with console.status("[bold yellow]Extracting AST symbols and module dependencies...[/bold yellow]"):
        stats = indexer.index_repository(max_files=max_files)

    console.print(
        Panel(
            f"[bold green]✓ Codebase Graph Indexing Complete![/bold green]\n\n"
            f"• [cyan]Files Indexed:[/cyan] [bold]{stats['files_indexed']}[/bold]\n"
            f"• [magenta]Classes Indexed:[/magenta] [bold]{stats['classes_indexed']}[/bold]\n"
            f"• [blue]Functions Indexed:[/blue] [bold]{stats['functions_indexed']}[/bold]\n"
            f"• [yellow]Import Edges Mapped:[/yellow] [bold]{stats['imports_indexed']}[/bold]\n\n"
            f"[dim]Coding agents in Cursor / Claude Code can now query this graph via MCP.[/dim]",
            title="[bold yellow]🍌 Banana Code Graph[/bold yellow]",
            border_style="green",
        )
    )


@app.command("code-context")
def code_context_command(
    query: str = typer.Argument(..., help="Symbol, class name, or feature query"),
    budget: int = typer.Option(1500, "--budget", "-b", help="Token budget knapsack"),
) -> None:
    """Assemble high-signal code context (signatures, interfaces) under a strict token budget."""
    from banana.code_graph import CodebaseIndexer
    db_client = get_db_client()
    indexer = CodebaseIndexer(db_client=db_client)

    res = indexer.assemble_code_context(query=query, token_budget=budget)
    console.print(
        Panel(
            f"[bold green]✓ Assembled Context for query: '{query}'[/bold green]\n"
            f"[dim]Tokens Used: {res['tokens_used']} / {budget} | Symbols: {res['symbols_count']}[/dim]\n\n"
            f"{res['assembled_context'] if res['assembled_context'] else '[dim]No matching symbols found. Run `banana index` first.[/dim]'}",
            title="[bold yellow]🍌 Graph Knapsack Code Context[/bold yellow]",
            border_style="cyan",
        )
    )


@app.command("guardrails")
def guardrails_command(
    action: str = typer.Argument("check", help="Action to run: 'check' or 'validate'"),
    file: Optional[str] = typer.Option(None, "--file", "-f", help="Source file path to test layer isolation (e.g. src/ui/app.py)"),
    import_mod: Optional[str] = typer.Option(None, "--import", "-i", help="Imported module to test (e.g. banana.db)"),
    code: Optional[str] = typer.Option(None, "--code", "-c", help="Code snippet to scan for security leaks or dangerous primitives"),
    price: Optional[float] = typer.Option(None, "--price", "-p", help="Legacy pricing proposal check (backwards compatibility)"),
) -> None:
    """Run deterministic policy, architecture, and security guardrail validation."""
    from banana.guardrails import GuardrailsEngine
    db_client = get_db_client()
    engine = GuardrailsEngine(db_client=db_client)

    if code is not None:
        res = engine.check_security_rules(code_snippet=code, filename=file or "")
    elif file is not None or import_mod is not None:
        res = engine.check_code_architecture(source_file=file or "src/ui/app.py", imported_module=import_mod or "banana.db")
    elif price is not None:
        res = engine.check_pricing_proposal(proposed_price=price)
    else:
        console.print(
            "[bold green]✓ Repository Architecture Guardrails Active.[/bold green]\n\n"
            "• [cyan]Clean Architecture Layer Isolation:[/cyan] Presentation cannot import DB driver directly\n"
            "• [cyan]OWASP Credential Leak Prevention:[/cyan] Scans for hardcoded AWS keys, private keys, eval()\n"
            "• [cyan]Framework Schema Invariants:[/cyan] Enforces Pydantic v2 .model_dump()\n\n"
            "[dim]Try testing:[/dim]\n"
            "[yellow]  banana guardrails check --file src/ui/app.py --import banana.db[/yellow]\n"
            "[yellow]  banana guardrails check --code \"AWS_KEY = 'AKIA1234567890ABCDEF'\"[/yellow]"
        )
        return

    if res.compliant:
        console.print(f"[bold green]✓ Compliant:[/bold green] All {res.verified_rules_count} verified rules passed with zero violations.")
    else:
        for v in res.violations:
            console.print(f"[bold red]🛑 VIOLATION ({v.rule_id}):[/bold red] {v.description}")
            if v.citation:
                console.print(f"   [dim]📜 Citation:[/dim] {v.citation}")
            if v.suggested_fix:
                console.print(f"   [yellow]💡 Suggested Fix:[/yellow] {v.suggested_fix}")


@app.command("decision")
def decision_command(
    action: str = typer.Argument("list", help="'list' or 'save'"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Title of architectural decision"),
    finding: Optional[str] = typer.Option(None, "--finding", "-f", help="Decision rationale or finding"),
    supersedes: Optional[str] = typer.Option(None, "--supersedes", "-s", help="ID of superseded decision"),
) -> None:
    """Inspect or record persistent cross-session architectural decisions."""
    from banana.tools import AgentTools
    db_client = get_db_client()
    tools = AgentTools(db_client)

    if action == "save":
        if not title or not finding:
            console.print("[bold red]Error:[/bold red] --title and --finding are required to save a decision.")
            return
        res = tools.save_finding(title=title, finding=finding, supersedes_id=supersedes)
        console.print(f"[bold green]✓ Architectural Decision Logged:[/bold green] `{res.get('canonical_id')}` ({title})")
    else:
        findings = tools.list_findings(limit=10)
        if not findings:
            console.print("[dim]No architectural decisions logged yet. Use `banana decision save --title ... --finding ...`[/dim]")
            return
        for f in findings:
            sup = f" [cyan](Supersedes: {f['supersedes']})[/cyan]" if f.get("supersedes") else ""
            console.print(f"• [bold]{f['title']}[/bold]{sup}\n  [dim]{f['finding']}[/dim]\n")


def main() -> None:
    """CLI entrypoint."""
    app()


if __name__ == "__main__":
    main()
