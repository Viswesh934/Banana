"""Graph-Aware Context Assembler and Progressive Load Shedder.

Traverses FalkorDB Demand and Knowledge graphs, resolves dependencies,
ranks candidates by priority and utility, and executes progressive load shedding
under a strict token budget knapsack.
"""

import time
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from banana.db import FalkorDBClient, get_db_client
from banana.models import ContextItem, EntityType, PriorityClass
from banana.tokenizer import count_tokens, get_token_counter


class BudgetExceededError(Exception):
    """Raised when non-negotiable mandatory context cannot fit in the configured token budget."""
    pass


class AssemblyResult(BaseModel):
    """Detailed result of graph-aware context assembly operation."""
    task_id: str
    token_budget: int
    total_tokens: int
    system_tokens: int
    selected_items: List[ContextItem]
    excluded_items: List[ContextItem]
    item_tokens: Dict[str, int]
    inclusion_reasons: Dict[str, str]
    exclusion_reasons: Dict[str, str]
    preserved_dependencies: List[Tuple[str, str]]
    shedded_dependencies: List[Tuple[str, str]]
    latency_ms: float
    formatted_prompt: str


class ContextAssembler:
    """Orchestrates candidate retrieval, dependency expansion, and progressive load shedding."""

    def __init__(self, db_client: Optional[FalkorDBClient] = None) -> None:
        self.db_client = db_client or get_db_client()
        self.token_counter = get_token_counter()

    def fetch_demand_candidates(self, task_id: str = "task_pricing_strategy") -> Tuple[List[ContextItem], Dict[str, List[str]]]:
        """Traverse Demand Graph to find all requirements, policies, and tools required for the task."""
        graph = self.db_client.get_demand_graph()
        items: Dict[str, ContextItem] = {}
        dependencies: Dict[str, List[str]] = {}  # child_id -> [parent_id]

        # 1. Fetch task itself
        task_res = graph.query(
            "MATCH (t:Task {canonical_id: $task_id}) "
            "RETURN t.canonical_id, t.entity_type, t.title, t.content, t.provenance, t.priority, t.token_cost",
            {"task_id": task_id},
        )
        for row in task_res.result_set:
            item = ContextItem(
                canonical_id=row[0],
                entity_type=EntityType(row[1]),
                title=row[2],
                content=row[3],
                provenance=row[4],
                priority=PriorityClass(row[5]),
                token_cost=row[6] if row[6] is not None else 0,
            )
            items[item.canonical_id] = item

        # 2. Fetch connected requirements, policies, and tools
        demand_query = """
        MATCH (t:Task {canonical_id: $task_id})-[r]->(target:ContextNode)
        RETURN target.canonical_id, target.entity_type, target.title, target.content,
               target.provenance, target.priority, target.token_cost
        """
        connected_res = graph.query(demand_query, {"task_id": task_id})
        for row in connected_res.result_set:
            item = ContextItem(
                canonical_id=row[0],
                entity_type=EntityType(row[1]),
                title=row[2],
                content=row[3],
                provenance=row[4],
                priority=PriorityClass(row[5]),
                token_cost=row[6] if row[6] is not None else 0,
            )
            items[item.canonical_id] = item

        # 3. Fetch inter-requirement dependencies
        dep_query = """
        MATCH (a:ContextNode)-[:DEPENDS_ON]->(b:ContextNode)
        RETURN a.canonical_id, b.canonical_id
        """
        dep_res = graph.query(dep_query)
        for row in dep_res.result_set:
            child, parent = row[0], row[1]
            if child not in dependencies:
                dependencies[child] = []
            dependencies[child].append(parent)

        return list(items.values()), dependencies

    def fetch_knowledge_candidates(self) -> Tuple[List[ContextItem], Dict[str, List[str]]]:
        """Fetch candidates from Knowledge Graph and expand dependency edges."""
        graph = self.db_client.get_knowledge_graph()
        items: Dict[str, ContextItem] = {}
        dependencies: Dict[str, List[str]] = {}

        # Fetch all knowledge nodes
        query = """
        MATCH (n:ContextNode)
        RETURN n.canonical_id, n.entity_type, n.title, n.content,
               n.provenance, n.priority, n.token_cost
        """
        nodes_res = graph.query(query)
        for row in nodes_res.result_set:
            try:
                etype = EntityType(row[1]) if row[1] else EntityType.MEMORY
            except (ValueError, TypeError):
                etype = EntityType.MEMORY
            item = ContextItem(
                canonical_id=row[0],
                entity_type=etype,
                title=row[2] or row[0],
                content=row[3] or "",
                provenance=row[4],
                priority=PriorityClass(row[5]) if row[5] is not None else PriorityClass.EVIDENCE,
                token_cost=row[6] if row[6] is not None else 0,
            )
            items[item.canonical_id] = item

        # Fetch knowledge dependency / lineage edges
        # (Evidence)-[:EXTRACTED_FROM]->(Document)
        # (Evidence)-[:VALIDATES_FLOOR]->(Product)
        # (Evidence)-[:EVALUATES]->(Product)
        edge_query = """
        MATCH (a:ContextNode)-[r:EXTRACTED_FROM|VALIDATES_FLOOR|EVALUATES|APPLIES_TO|TARGETS]->(b:ContextNode)
        RETURN a.canonical_id, b.canonical_id
        """
        edge_res = graph.query(edge_query)
        for row in edge_res.result_set:
            child, parent = row[0], row[1]
            if child not in dependencies:
                dependencies[child] = []
            dependencies[child].append(parent)

        return list(items.values()), dependencies

    def assemble(
        self,
        task_id: str = "task_pricing_strategy",
        token_budget: int = 4000,
        reserved_output_tokens: int = 800,
    ) -> AssemblyResult:
        """Execute graph-aware context candidate gathering and progressive load shedding."""
        start_time = time.perf_counter()
        effective_budget = token_budget - reserved_output_tokens
        if effective_budget < 250:
            raise BudgetExceededError(
                f"Token budget {token_budget} is too small after reserving {reserved_output_tokens} output tokens."
            )

        # 1. Fetch demand & knowledge candidates
        demand_items, demand_deps = self.fetch_demand_candidates(task_id)
        knowledge_items, knowledge_deps = self.fetch_knowledge_candidates()

        all_items: Dict[str, ContextItem] = {it.canonical_id: it for it in demand_items + knowledge_items}
        all_deps: Dict[str, List[str]] = {**demand_deps}
        for k, v in knowledge_deps.items():
            if k in all_deps:
                all_deps[k].extend(v)
            else:
                all_deps[k] = list(v)

        inclusion_reasons: Dict[str, str] = {}
        exclusion_reasons: Dict[str, str] = {}
        item_tokens: Dict[str, int] = {it.canonical_id: it.token_cost for it in all_items.values()}

        # 2. Identify Mandatory Priority 0 Context Items
        p0_items = [it for it in all_items.values() if it.priority == PriorityClass.MANDATORY]
        p0_tokens = sum(it.token_cost for it in p0_items)

        if p0_tokens > effective_budget:
            raise BudgetExceededError(
                f"Mandatory priority 0 governance policies and instructions require {p0_tokens} tokens, "
                f"which exceeds the effective input budget of {effective_budget} tokens. "
                f"Increase token budget to at least {p0_tokens + reserved_output_tokens}."
            )

        # 3. Identify Priority 1 Tool Schemas
        p1_items = [it for it in all_items.values() if it.priority == PriorityClass.TOOL_SCHEMA]

        # 4. Partition remaining items by Priority
        p2_items = [it for it in all_items.values() if it.priority == PriorityClass.EVIDENCE]
        p3_items = [it for it in all_items.values() if it.priority == PriorityClass.MEMORY]
        p4_items = [it for it in all_items.values() if it.priority == PriorityClass.BACKGROUND]

        # Progressive Load Shedding Algorithm
        selected_ids: Set[str] = set()

        # Step A: Include all P0 mandatory items
        for it in p0_items:
            selected_ids.add(it.canonical_id)
            inclusion_reasons[it.canonical_id] = "Mandatory Governance & Task Constraint (Priority 0)"

        # Step B: Include all P1 tool schemas if they fit
        current_tokens = sum(all_items[cid].token_cost for cid in selected_ids)
        for it in p1_items:
            if current_tokens + it.token_cost <= effective_budget:
                selected_ids.add(it.canonical_id)
                current_tokens += it.token_cost
                inclusion_reasons[it.canonical_id] = "Required Tool Execution Schema (Priority 1)"
            else:
                exclusion_reasons[it.canonical_id] = "Tool schema excluded due to token budget"

        # Step C: Progressive evaluation of P2, P3, P4
        # We greedily include high-value evidence clusters (P2), then memories (P3), then background (P4).
        # A cluster includes the item AND its prerequisite parent in the dependency graph.
        tiers = [
            (PriorityClass.EVIDENCE, p2_items),
            (PriorityClass.MEMORY, p3_items),
            (PriorityClass.BACKGROUND, p4_items),
        ]

        preserved_deps: List[Tuple[str, str]] = []
        shedded_deps: List[Tuple[str, str]] = []

        for prio, tier_items in tiers:
            for item in tier_items:
                cid = item.canonical_id
                if cid in selected_ids:
                    continue

                # Compute dependency cluster cost: this item + any unselected prerequisites
                cluster_items = [item]
                prereqs = all_deps.get(cid, [])
                for pid in prereqs:
                    if pid in all_items and pid not in selected_ids:
                        cluster_items.append(all_items[pid])

                cluster_cost = sum(cit.token_cost for cit in cluster_items)

                if current_tokens + cluster_cost <= effective_budget:
                    # Include the entire dependency cluster
                    for cit in cluster_items:
                        selected_ids.add(cit.canonical_id)
                        current_tokens += cit.token_cost
                        if cit.canonical_id == cid:
                            inclusion_reasons[cid] = f"Retained with verified dependencies (Priority {int(prio)})"
                        else:
                            inclusion_reasons[cit.canonical_id] = (
                                f"Included as mandatory prerequisite dependency for {cid}"
                            )
                    # Record preserved dependency edges
                    for pid in prereqs:
                        if pid in selected_ids:
                            preserved_deps.append((cid, pid))
                else:
                    # Exclude and shed
                    exclusion_reasons[cid] = (
                        f"Progressive load shedding: cluster ({cluster_cost} tokens) exceeds remaining budget ({effective_budget - current_tokens})"
                    )
                    for pid in prereqs:
                        shedded_deps.append((cid, pid))

        # Fill exclusion reasons for any remaining unselected items
        for cid, item in all_items.items():
            if cid not in selected_ids and cid not in exclusion_reasons:
                exclusion_reasons[cid] = f"Shedded during budget optimization (Priority {int(item.priority)})"

        selected_items_list = [all_items[cid] for cid in selected_ids]
        # Sort selected by priority ascending (P0 first)
        selected_items_list.sort(key=lambda x: (int(x.priority), x.canonical_id))
        excluded_items_list = [all_items[cid] for cid in all_items if cid not in selected_ids]

        # Compile formatted context
        formatted_prompt = self._compile_context_prompt(selected_items_list)
        final_token_count = self.token_counter.count(formatted_prompt)

        duration_ms = (time.perf_counter() - start_time) * 1000

        return AssemblyResult(
            task_id=task_id,
            token_budget=token_budget,
            total_tokens=final_token_count,
            system_tokens=p0_tokens,
            selected_items=selected_items_list,
            excluded_items=excluded_items_list,
            item_tokens=item_tokens,
            inclusion_reasons=inclusion_reasons,
            exclusion_reasons=exclusion_reasons,
            preserved_dependencies=preserved_deps,
            shedded_dependencies=shedded_deps,
            latency_ms=round(duration_ms, 2),
            formatted_prompt=formatted_prompt,
        )

    def _compile_context_prompt(self, items: List[ContextItem]) -> str:
        """Compile selected context items into structured, grounded LLM prompt."""
        sections = {
            PriorityClass.MANDATORY: ("### MANDATORY GOVERNANCE POLICIES & CONSTRAINTS", []),
            PriorityClass.TOOL_SCHEMA: ("### AVAILABLE TOOL SCHEMAS", []),
            PriorityClass.EVIDENCE: ("### FACTUAL EVIDENCE & MARKET INTELLIGENCE", []),
            PriorityClass.MEMORY: ("### PERSISTENT CROSS-SESSION MEMORY", []),
            PriorityClass.BACKGROUND: ("### SUPPLEMENTAL BACKGROUND CONTEXT", []),
        }

        for it in items:
            prio = it.priority
            if prio in sections:
                entry = f"- **[{it.canonical_id}]** {it.title}\n  {it.content}"
                if it.provenance:
                    entry += f"\n  *Source*: {it.provenance}"
                sections[prio][1].append(entry)

        lines = ["# BANANA GRAPH-ASSEMBLED CONTEXT\n"]
        for prio in [
            PriorityClass.MANDATORY,
            PriorityClass.TOOL_SCHEMA,
            PriorityClass.EVIDENCE,
            PriorityClass.MEMORY,
            PriorityClass.BACKGROUND,
        ]:
            title, entries = sections[prio]
            if entries:
                lines.append(f"\n{title}\n")
                lines.extend(entries)

        return "\n".join(lines)
