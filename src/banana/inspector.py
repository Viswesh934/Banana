"""Graph inspection and diagnostics for FalkorDB dual graphs."""

from typing import Any, Dict, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from banana.db import FalkorDBClient, get_db_client


class GraphInspector:
    """Inspector for querying and visualizing graph topologies in FalkorDB."""

    def __init__(self, db_client: FalkorDBClient = None) -> None:
        self.db_client = db_client or get_db_client()

    def inspect_graph(self, graph_name: str) -> Dict[str, Any]:
        """Fetch summary statistics and sample nodes/edges from a graph."""
        graph = self.db_client.get_graph(graph_name)

        # 1. Total node and edge counts
        try:
            node_count_res = graph.query("MATCH (n) RETURN count(n) AS cnt")
            node_count = node_count_res.result_set[0][0] if node_count_res.result_set else 0
        except Exception:
            node_count = 0

        try:
            edge_count_res = graph.query("MATCH ()-[r]->() RETURN count(r) AS cnt")
            edge_count = edge_count_res.result_set[0][0] if edge_count_res.result_set else 0
        except Exception:
            edge_count = 0

        # 2. Node breakdown by entity_type
        type_breakdown: List[Dict[str, Any]] = []
        try:
            type_res = graph.query(
                "MATCH (n:ContextNode) RETURN n.entity_type AS type, count(n) AS cnt ORDER BY cnt DESC"
            )
            for row in type_res.result_set:
                type_breakdown.append({"type": row[0], "count": row[1]})
        except Exception:
            pass

        # 3. Partition salt distribution
        partition_stats: Dict[str, int] = {}
        try:
            part_res = graph.query(
                "MATCH (n:ContextNode) RETURN n.partition_salt AS salt, count(n) AS cnt ORDER BY salt"
            )
            for row in part_res.result_set:
                partition_stats[str(row[0])] = row[1]
        except Exception:
            pass

        # 4. Fetch all nodes for detailed display
        nodes: List[Dict[str, Any]] = []
        try:
            nodes_res = graph.query(
                "MATCH (n:ContextNode) "
                "RETURN n.canonical_id, n.entity_type, n.title, n.priority, n.token_cost, n.provenance, n.partition_salt "
                "ORDER BY n.priority ASC, n.canonical_id ASC"
            )
            for row in nodes_res.result_set:
                nodes.append({
                    "canonical_id": row[0],
                    "entity_type": row[1],
                    "title": row[2],
                    "priority": row[3],
                    "token_cost": row[4],
                    "provenance": row[5],
                    "partition_salt": row[6],
                })
        except Exception:
            pass

        # 5. Fetch all relationships
        relationships: List[Dict[str, Any]] = []
        try:
            rels_res = graph.query(
                "MATCH (a:ContextNode)-[r]->(b:ContextNode) "
                "RETURN a.canonical_id, type(r), b.canonical_id, b.entity_type "
                "ORDER BY type(r), a.canonical_id"
            )
            for row in rels_res.result_set:
                relationships.append({
                    "source": row[0],
                    "type": row[1],
                    "target": row[2],
                    "target_type": row[3],
                })
        except Exception:
            pass

        return {
            "graph_name": graph_name,
            "node_count": node_count,
            "edge_count": edge_count,
            "type_breakdown": type_breakdown,
            "partition_stats": partition_stats,
            "nodes": nodes,
            "relationships": relationships,
        }

    def render_cli(self, console: Console) -> None:
        """Render beautiful Rich visualization of both graphs in terminal."""
        settings = self.db_client.settings
        graphs = [
            ("Demand Graph (Task Requirements & Governance)", settings.demand_graph_name),
            ("Knowledge Graph (Company & Market Knowledge)", settings.knowledge_graph_name),
        ]

        for label, gname in graphs:
            stats = self.inspect_graph(gname)
            console.print(
                Panel.fit(
                    f"[bold yellow]📊 {label}[/bold yellow]\n"
                    f"[dim]FalkorDB Graph: [bold cyan]{gname}[/bold cyan] | "
                    f"Nodes: [green]{stats['node_count']}[/green] | "
                    f"Relationships: [green]{stats['edge_count']}[/green] | "
                    f"Partitions: {stats['partition_stats']}[/dim]",
                    border_style="cyan",
                )
            )

            # Node table
            node_table = Table(
                title=f"{gname} Entities",
                box=box.ROUNDED,
                header_style="bold magenta",
                show_lines=False,
            )
            node_table.add_column("Type", style="bold cyan", width=14)
            node_table.add_column("Canonical ID", style="green", width=26)
            node_table.add_column("Prio", style="bold yellow", width=6)
            node_table.add_column("Tokens", justify="right", width=8)
            node_table.add_column("Partition", style="blue", width=10)
            node_table.add_column("Title / Provenance", style="dim")

            for node in stats["nodes"]:
                prio_str = f"P{node['priority']}"
                prov = f" ({node['provenance']})" if node["provenance"] else ""
                node_table.add_row(
                    node["entity_type"],
                    node["canonical_id"],
                    prio_str,
                    str(node["token_cost"]),
                    node["partition_salt"],
                    f"{node['title']}{prov}",
                )
            console.print(node_table)

            # Relationship summary
            if stats["relationships"]:
                rel_table = Table(
                    title=f"{gname} Relationships",
                    box=box.SIMPLE,
                    header_style="bold yellow",
                    show_lines=False,
                )
                rel_table.add_column("Source ID", style="cyan", width=28)
                rel_table.add_column("Relationship", style="bold red", width=18)
                rel_table.add_column("Target ID", style="green", width=28)
                rel_table.add_column("Target Type", style="dim")

                for rel in stats["relationships"][:15]:
                    rel_table.add_row(
                        rel["source"],
                        f"--[{rel['type']}]-->",
                        rel["target"],
                        rel["target_type"],
                    )
                if len(stats["relationships"]) > 15:
                    rel_table.add_row("...", "...", "...", f"+{len(stats['relationships']) - 15} more edges")
                console.print(rel_table)

            console.print()
