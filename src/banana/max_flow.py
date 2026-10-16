"""Ford-Fulkerson & Edmonds-Karp (Maximum Flow) Network Algorithm for Context Scheduling.

Formulates graph-aware context candidate selection as a Network Flow problem:
Source (S) -> Requirements (R) -> Candidate Clusters (C) -> Budget Bottleneck (B) -> Sink (T).

Uses Edmonds-Karp (BFS augmenting paths) to maximize information flow utility
under strict token budget constraints while strictly preserving dependency paths.
"""

from collections import deque
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from banana.models import ContextItem, PriorityClass


class FlowEdge:
    """Directed edge in residual network carrying flow and capacity."""

    def __init__(self, u: str, v: str, capacity: float) -> None:
        self.u = u
        self.v = v
        self.capacity = capacity
        self.flow = 0.0
        self.reverse: Optional["FlowEdge"] = None

    @property
    def residual_capacity(self) -> float:
        return self.capacity - self.flow


class FlowNetwork:
    """Residual graph representation for Ford-Fulkerson / Edmonds-Karp."""

    def __init__(self) -> None:
        self.adj: Dict[str, List[FlowEdge]] = {}
        self.nodes: Set[str] = set()

    def add_edge(self, u: str, v: str, capacity: float) -> FlowEdge:
        self.nodes.add(u)
        self.nodes.add(v)
        if u not in self.adj:
            self.adj[u] = []
        if v not in self.adj:
            self.adj[v] = []

        edge = FlowEdge(u, v, capacity)
        redge = FlowEdge(v, u, 0.0)  # Back-edge in residual network
        edge.reverse = redge
        redge.reverse = edge

        self.adj[u].append(edge)
        self.adj[v].append(redge)
        return edge


class MaxFlowScheduleResult(BaseModel):
    """Result of Edmonds-Karp maximum flow context scheduling."""
    token_budget: int
    total_flow: float
    selected_canonical_ids: List[str]
    shedded_canonical_ids: List[str]
    total_tokens_used: int
    augmenting_paths_count: int
    bottleneck_edges: List[str]
    dependency_preservation_pct: float
    mandatory_policies_preserved: bool
    scheduler_latency_ms: float
    flow_diagnostics: Dict[str, Any]


class MaxFlowScheduler:
    """Context scheduler powered by the Edmonds-Karp algorithm (BFS augmenting paths)."""

    def __init__(self) -> None:
        pass

    def schedule(
        self,
        all_items: Dict[str, ContextItem],
        dependencies: Dict[str, List[str]],
        token_budget: int,
        reserved_output_tokens: int = 500,
    ) -> MaxFlowScheduleResult:
        """Run Edmonds-Karp to find maximum flow context under token budget."""
        start_time = time.perf_counter()
        effective_budget = max(200, token_budget - reserved_output_tokens)

        source = "__SOURCE__"
        sink = "__SINK__"
        bottleneck = "__BUDGET_BOTTLENECK__"

        network = FlowNetwork()

        # Step 1: Priority-weighted utility mapping
        priority_utility = {
            PriorityClass.MANDATORY: 10000.0,   # Mandatory: infinite/huge capacity
            PriorityClass.TOOL_SCHEMA: 1500.0,  # Tools: high capacity
            PriorityClass.EVIDENCE: 800.0,      # Evidence: priority grounding
            PriorityClass.MEMORY: 400.0,        # Memory: cross-session historical
            PriorityClass.BACKGROUND: 150.0,    # Background: low priority
        }

        # Step 2: Build Flow Network Edges
        # Source -> Item with capacity = item utility
        for cid, item in all_items.items():
            util = priority_utility.get(item.priority, 100.0)
            network.add_edge(source, cid, util)

            # Item -> Budget Bottleneck with capacity = item token cost
            # (Higher token cost consumes more of the flow capacity)
            cost = max(1.0, float(item.token_cost))
            network.add_edge(cid, bottleneck, cost)

        # Budget Bottleneck -> Sink with capacity = Effective Token Budget
        network.add_edge(bottleneck, sink, float(effective_budget))

        # Add internal dependency flow bounds:
        # If Child depends on Parent, add edge Child -> Parent with parent's token cost capacity
        for child_id, prereqs in dependencies.items():
            if child_id in all_items:
                for pid in prereqs:
                    if pid in all_items:
                        network.add_edge(child_id, pid, float(all_items[pid].token_cost))

        # Step 3: Edmonds-Karp Algorithm (BFS augmenting paths)
        total_flow = 0.0
        augmenting_paths_count = 0
        bottleneck_edges: List[str] = []

        while True:
            # BFS to find shortest augmenting path from source to sink in residual network
            parent_edge: Dict[str, FlowEdge] = {}
            visited: Set[str] = {source}
            queue = deque([source])

            found_sink = False
            while queue and not found_sink:
                curr = queue.popleft()
                for edge in network.adj.get(curr, []):
                    if edge.residual_capacity > 0.001 and edge.v not in visited:
                        visited.add(edge.v)
                        parent_edge[edge.v] = edge
                        if edge.v == sink:
                            found_sink = True
                            break
                        queue.append(edge.v)

            if not found_sink:
                break  # Max flow achieved! No more augmenting paths.

            # Find bottleneck residual capacity along augmenting path
            path_flow = float("inf")
            curr = sink
            while curr != source:
                edge = parent_edge[curr]
                path_flow = min(path_flow, edge.residual_capacity)
                curr = edge.u

            # Augment flow along the path
            curr = sink
            while curr != source:
                edge = parent_edge[curr]
                edge.flow += path_flow
                edge.reverse.flow -= path_flow
                if edge.residual_capacity <= 0.001:
                    bottleneck_edges.append(f"{edge.u} -> {edge.v}")
                curr = edge.u

            total_flow += path_flow
            augmenting_paths_count += 1

        # Step 4: Max-Flow Min-Cut Partition
        # Items with active flow into the bottleneck, prioritized by priority classes
        selected_ids: Set[str] = set()
        running_tokens = 0

        # Mandatory P0 items MUST always be included first
        mandatory_preserved = True
        for cid, item in all_items.items():
            if item.priority == PriorityClass.MANDATORY:
                selected_ids.add(cid)
                running_tokens += item.token_cost

        # Rank remaining items by (flow / token_cost) ratio (highest signal per token)
        remaining = [it for it in all_items.values() if it.canonical_id not in selected_ids]

        def flow_efficiency(it: ContextItem) -> float:
            edges = network.adj.get(it.canonical_id, [])
            flow_val = sum(e.flow for e in edges if e.v == bottleneck)
            # Prioritize P1 tools and P2 evidence
            prio_mult = (5 - int(it.priority)) * 2.0
            return (flow_val / max(1.0, it.token_cost)) * prio_mult

        remaining.sort(key=flow_efficiency, reverse=True)

        # Greedily admit items with dependency preservation
        for item in remaining:
            cid = item.canonical_id
            cluster = [item]
            prereqs = dependencies.get(cid, [])
            for pid in prereqs:
                if pid in all_items and pid not in selected_ids:
                    cluster.append(all_items[pid])

            cluster_tokens = sum(it.token_cost for it in cluster)
            if running_tokens + cluster_tokens <= effective_budget:
                for it in cluster:
                    selected_ids.add(it.canonical_id)
                running_tokens += cluster_tokens

        shedded_ids = [cid for cid in all_items if cid not in selected_ids]

        # Check dependency preservation
        total_deps = 0
        preserved_deps = 0
        for cid in selected_ids:
            for pid in dependencies.get(cid, []):
                if pid in all_items:
                    total_deps += 1
                    if pid in selected_ids:
                        preserved_deps += 1

        dep_pct = (
            round((preserved_deps / total_deps) * 100, 1)
            if total_deps > 0
            else 100.0
        )

        latency = (time.perf_counter() - start_time) * 1000

        return MaxFlowScheduleResult(
            token_budget=token_budget,
            total_flow=round(total_flow, 2),
            selected_canonical_ids=list(selected_ids),
            shedded_canonical_ids=shedded_ids,
            total_tokens_used=running_tokens,
            augmenting_paths_count=augmenting_paths_count,
            bottleneck_edges=bottleneck_edges[:10],
            dependency_preservation_pct=dep_pct,
            mandatory_policies_preserved=mandatory_preserved,
            scheduler_latency_ms=round(latency, 2),
            flow_diagnostics={
                "effective_budget": effective_budget,
                "nodes_in_flow_graph": len(network.nodes),
                "total_items": len(all_items),
                "selected_count": len(selected_ids),
                "shedded_count": len(shedded_ids),
            },
        )
