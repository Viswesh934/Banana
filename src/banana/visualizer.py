"""Interactive D3.js Force-Directed Graph Visualizer for Banana Dual Graphs.

Generates a standalone, interactive HTML/D3.js visualization showing Demand and
Knowledge graph topologies, with real-time visual distinction between nodes
retained by Max-Flow scheduling (glowing) vs shedded nodes (dimmed).
"""

import json
from typing import Any, Dict, List, Optional, Set
from banana.db import FalkorDBClient, get_db_client
from banana.models import PriorityClass


class GraphVisualizer:
    """Generates self-contained interactive D3.js force-directed graph HTML."""

    def __init__(self, db_client: Optional[FalkorDBClient] = None) -> None:
        self.db_client = db_client or get_db_client()

    def get_graph_data(
        self,
        selected_canonical_ids: Optional[Set[str]] = None,
    ) -> Dict[str, Any]:
        """Extract all nodes and relationships from Demand and Knowledge graphs."""
        settings = self.db_client.settings
        d_graph = self.db_client.get_demand_graph()
        k_graph = self.db_client.get_knowledge_graph()

        nodes: Dict[str, Dict[str, Any]] = {}
        links: List[Dict[str, Any]] = []

        # Color palette by entity type
        type_colors = {
            "Policy": "#f59e0b",       # Gold
            "Task": "#ef4444",         # Red
            "Requirement": "#6366f1",  # Indigo
            "Tool": "#8b5cf6",         # Purple
            "Evidence": "#10b981",     # Emerald
            "Product": "#3b82f6",      # Blue
            "Company": "#ec4899",      # Pink
            "Competitor": "#f97316",   # Orange
            "Document": "#06b6d4",     # Cyan
            "Memory": "#14b8a6",       # Teal
            "Speaker": "#38bdf8",      # Sky Blue
            "Commitment": "#eab308",   # Amber
            "Proposal": "#f43f5e",     # Coral
            "MeetingSession": "#a855f7",# Purple
            "MeetingTurn": "#64748b",  # Slate
        }

        # 1. Fetch nodes from Demand Graph
        d_nodes_res = d_graph.query(
            "MATCH (n:ContextNode) RETURN n.canonical_id, n.entity_type, n.title, n.priority, n.token_cost, n.provenance"
        )
        for r in d_nodes_res.result_set:
            cid = r[0]
            is_selected = True if selected_canonical_ids is None else (cid in selected_canonical_ids)
            nodes[cid] = {
                "id": cid,
                "label": r[2],
                "type": r[1],
                "priority": r[3],
                "tokens": r[4] or 0,
                "provenance": r[5] or "",
                "color": type_colors.get(r[1], "#94a3b8"),
                "selected": is_selected,
                "graph": "Demand Graph",
            }

        # 2. Fetch edges from Demand Graph
        d_edge_res = d_graph.query(
            "MATCH (a:ContextNode)-[r]->(b:ContextNode) RETURN a.canonical_id, type(r), b.canonical_id"
        )
        for r in d_edge_res.result_set:
            links.append({"source": r[0], "target": r[2], "type": r[1], "graph": "Demand"})

        # 3. Fetch nodes from Knowledge Graph
        k_nodes_res = k_graph.query(
            "MATCH (n:ContextNode) RETURN n.canonical_id, n.entity_type, n.title, n.priority, n.token_cost, n.provenance"
        )
        for r in k_nodes_res.result_set:
            cid = r[0]
            is_selected = True if selected_canonical_ids is None else (cid in selected_canonical_ids)
            nodes[cid] = {
                "id": cid,
                "label": r[2],
                "type": r[1],
                "priority": r[3],
                "tokens": r[4] or 0,
                "provenance": r[5] or "",
                "color": type_colors.get(r[1], "#94a3b8"),
                "selected": is_selected,
                "graph": "Knowledge Graph",
            }

        # 4. Fetch edges from Knowledge Graph
        k_edge_res = k_graph.query(
            "MATCH (a:ContextNode)-[r]->(b:ContextNode) RETURN a.canonical_id, type(r), b.canonical_id"
        )
        for r in k_edge_res.result_set:
            links.append({"source": r[0], "target": r[2], "type": r[1], "graph": "Knowledge"})

        return {
            "nodes": list(nodes.values()),
            "links": links,
        }

    def generate_html(
        self,
        selected_canonical_ids: Optional[Set[str]] = None,
        height: int = 650,
    ) -> str:
        """Generate interactive self-contained HTML page using D3.js v7."""
        data = self.get_graph_data(selected_canonical_ids)
        json_data = json.dumps(data)

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Banana Dual Graph Visualizer</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
  body {{
    margin: 0;
    padding: 0;
    background-color: #0b0f19;
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    overflow: hidden;
  }}
  #graph-container {{
    width: 100%;
    height: {height}px;
    position: relative;
  }}
  .link {{
    stroke: #334155;
    stroke-opacity: 0.6;
    stroke-width: 1.5px;
  }}
  .link-label {{
    font-size: 8px;
    fill: #64748b;
    pointer-events: none;
  }}
  .node {{
    cursor: pointer;
    transition: all 0.3s ease;
  }}
  .node-dimmed {{
    opacity: 0.25 !important;
    filter: grayscale(80%);
  }}
  .node-selected {{
    filter: drop-shadow(0 0 8px rgba(16, 185, 129, 0.8));
  }}
  .node-policy {{
    filter: drop-shadow(0 0 10px rgba(245, 158, 11, 0.9));
  }}
  .node-label {{
    font-size: 10px;
    font-weight: 600;
    fill: #f8fafc;
    pointer-events: none;
    text-shadow: 0 1px 3px rgba(0,0,0,0.9);
  }}
  #tooltip {{
    position: absolute;
    display: none;
    background: rgba(15, 23, 42, 0.95);
    border: 1px solid #3b82f6;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 12px;
    line-height: 1.4;
    color: #f8fafc;
    box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    pointer-events: none;
    z-index: 100;
    max-width: 320px;
  }}
  #legend {{
    position: absolute;
    bottom: 12px;
    left: 14px;
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 11px;
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    z-index: 50;
  }}
  .legend-item {{
    display: flex;
    align-items: center;
    gap: 5px;
  }}
  .legend-dot {{
    width: 9px;
    height: 9px;
    border-radius: 50%;
  }}
</style>
</head>
<body>
<div id="graph-container">
  <div id="tooltip"></div>
  <div id="legend">
    <div class="legend-item"><span class="legend-dot" style="background:#f59e0b"></span>Policy (P0)</div>
    <div class="legend-item"><span class="legend-dot" style="background:#8b5cf6"></span>Tool (P1)</div>
    <div class="legend-item"><span class="legend-dot" style="background:#10b981"></span>Evidence (P2)</div>
    <div class="legend-item"><span class="legend-dot" style="background:#3b82f6"></span>Product</div>
    <div class="legend-item"><span class="legend-dot" style="background:#ec4899"></span>Company</div>
    <div class="legend-item"><span class="legend-dot" style="background:#06b6d4"></span>Document</div>
    <div class="legend-item" style="margin-left: 10px; border-left: 1px solid #334155; padding-left: 10px;">
      <span style="color:#10b981">● Glowing:</span> Max-Flow Selected
    </div>
    <div class="legend-item">
      <span style="color:#64748b">○ Dimmed:</span> Load-Shedded
    </div>
  </div>
</div>

<script>
const graphData = {json_data};
const width = window.innerWidth || 800;
const height = {height};

const svg = d3.select("#graph-container")
  .append("svg")
  .attr("width", "100%")
  .attr("height", height)
  .call(d3.zoom().scaleExtent([0.3, 3]).on("zoom", (event) => {{
    g.attr("transform", event.transform);
  }}));

const g = svg.append("g");

// Arrow markers for directed edges
svg.append("defs").selectAll("marker")
  .data(["end"])
  .enter().append("marker")
  .attr("id", "arrow")
  .attr("viewBox", "0 -5 10 10")
  .attr("refX", 18)
  .attr("refY", 0)
  .attr("markerWidth", 5)
  .attr("markerHeight", 5)
  .attr("orient", "auto")
  .append("path")
  .attr("d", "M0,-5L10,0L0,5")
  .attr("fill", "#475569");

const simulation = d3.forceSimulation(graphData.nodes)
  .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(90))
  .force("charge", d3.forceManyBody().strength(-240))
  .force("center", d3.forceCenter(width / 2, height / 2))
  .force("collision", d3.forceCollide().radius(26));

const link = g.append("g")
  .selectAll("line")
  .data(graphData.links)
  .enter().append("line")
  .attr("class", "link")
  .attr("marker-end", "url(#arrow)");

const linkText = g.append("g")
  .selectAll("text")
  .data(graphData.links)
  .enter().append("text")
  .attr("class", "link-label")
  .text(d => d.type);

const node = g.append("g")
  .selectAll(".node")
  .data(graphData.nodes)
  .enter().append("g")
  .attr("class", d => {{
    let cls = "node";
    if (!d.selected) cls += " node-dimmed";
    else if (d.type === "Policy") cls += " node-policy";
    else cls += " node-selected";
    return cls;
  }})
  .call(d3.drag()
    .on("start", dragstarted)
    .on("drag", dragged)
    .on("end", dragended));

node.append("circle")
  .attr("r", d => d.type === "Policy" ? 14 : (d.type === "Task" ? 16 : 11))
  .attr("fill", d => d.color)
  .attr("stroke", d => d.selected ? "#ffffff" : "#475569")
  .attr("stroke-width", d => d.selected ? 2 : 1);

node.append("text")
  .attr("class", "node-label")
  .attr("x", 14)
  .attr("y", 4)
  .text(d => d.id.length > 20 ? d.id.substring(0, 18) + '...' : d.id);

// Tooltip logic
const tooltip = d3.select("#tooltip");
node.on("mouseover", (event, d) => {{
  tooltip.style("display", "block")
    .html(`
      <strong style="color:${{d.color}}">${{d.type}}</strong>: <b>${{d.id}}</b><br/>
      <b>${{d.label}}</b><br/>
      <div style="font-size:11px; margin-top:4px; color:#94a3b8;">
        • Graph: ${{d.graph}}<br/>
        • Tokens: <b>${{d.tokens}}</b> | Priority: P${{d.priority}}<br/>
        • Status: <b style="color:${{d.selected ? '#10b981' : '#ef4444'}}">${{d.selected ? 'KEPT BY MAX-FLOW' : 'LOAD-SHEDDED'}}</b><br/>
        ${{d.provenance ? '• Source: ' + d.provenance : ''}}
      </div>
    `);
}})
.on("mousemove", (event) => {{
  tooltip.style("left", (event.pageX + 14) + "px")
         .style("top", (event.pageY - 28) + "px");
}})
.on("mouseout", () => {{
  tooltip.style("display", "none");
}});

simulation.on("tick", () => {{
  link
    .attr("x1", d => d.source.x)
    .attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x)
    .attr("y2", d => d.target.y);

  linkText
    .attr("x", d => (d.source.x + d.target.x) / 2)
    .attr("y", d => (d.source.y + d.target.y) / 2);

  node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
}});

function dragstarted(event, d) {{
  if (!event.active) simulation.alphaTarget(0.3).restart();
  d.fx = d.x;
  d.fy = d.y;
}}

function dragged(event, d) {{
  d.fx = event.x;
  d.fy = event.y;
}}

function dragended(event, d) {{
  if (!event.active) simulation.alphaTarget(0);
  d.fx = null;
  d.fy = null;
}}
</script>
</body>
</html>
"""
        return html_template
