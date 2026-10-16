"""Deterministic seed dataset and graph loader for Banana.

Populates the Demand Graph and Knowledge Graph in FalkorDB with:
- ApexCloud vs Competitors (CloudScale, HyperStore, DataVanguard)
- Mandatory business and margin policies
- Verified evidence with source provenance
- Sourced documents and pricing breakdowns
- Cross-session persistent memories and prior strategic decisions
- Tool definitions and dependency chains
"""

from typing import Any, Dict, List, Tuple
from banana.db import FalkorDBClient, get_db_client
from banana.models import ContextItem, EntityType, PriorityClass, calculate_partition_salt


def get_seed_demand_items() -> Tuple[List[ContextItem], List[Tuple[str, str, str]]]:
    """Return demand graph items and relationship tuples (source_id, rel_type, target_id)."""
    items: List[ContextItem] = [
        # Root Task
        ContextItem(
            canonical_id="task_pricing_strategy",
            entity_type=EntityType.TASK,
            title="Strategic Competitor Pricing & Packaging Evaluation",
            content=(
                "Evaluate recent competitor pricing adjustments across CloudScale, HyperStore, and DataVanguard. "
                "Detect feature, SLA, and egress fee gaps against ApexCloud Enterprise ($1,200/mo). "
                "Recommend an adjusted pricing and packaging strategy adhering to our 25% minimum gross margin policy."
            ),
            priority=PriorityClass.MANDATORY,
            provenance="Executive Strategy Board Directive 2026-Q3",
        ),
        # Requirements
        ContextItem(
            canonical_id="req_competitor_tiers",
            entity_type=EntityType.REQUIREMENT,
            title="Competitor Base Tiers & Pricing Models",
            content="Extract advertised base tiers, commitment terms, and published pricing for all target competitors.",
            priority=PriorityClass.MANDATORY,
            provenance="Task Decomposition Engine",
        ),
        ContextItem(
            canonical_id="req_egress_hidden_fees",
            entity_type=EntityType.REQUIREMENT,
            title="Egress Markups & Hidden Fee Analysis",
            content="Identify hidden network egress fees, surcharge thresholds, and overage billing that increase effective cost.",
            priority=PriorityClass.EVIDENCE,
            provenance="Task Decomposition Engine",
        ),
        ContextItem(
            canonical_id="req_feature_parity",
            entity_type=EntityType.REQUIREMENT,
            title="Enterprise Feature & SLA Parity",
            content="Map architectural capabilities including dedicated instances, high availability SLA, and compliance certifications.",
            priority=PriorityClass.EVIDENCE,
            provenance="Task Decomposition Engine",
        ),
        ContextItem(
            canonical_id="req_margin_compliance",
            entity_type=EntityType.REQUIREMENT,
            title="Gross Margin & Financial Viability Check",
            content="Verify proposed pricing structures maintain at least a 25% gross margin above cloud infrastructure COGS.",
            priority=PriorityClass.MANDATORY,
            provenance="Task Decomposition Engine",
        ),
        ContextItem(
            canonical_id="req_past_decisions",
            entity_type=EntityType.REQUIREMENT,
            title="Prior Strategic Decisions & Feedback",
            content="Retrieve historical executive decisions and prior win/loss findings regarding competitor discounting behavior.",
            priority=PriorityClass.MEMORY,
            provenance="Task Decomposition Engine",
        ),
        # Mandatory Policies
        ContextItem(
            canonical_id="policy_minimum_margin",
            entity_type=EntityType.POLICY,
            title="Policy: Minimum Gross Margin Floor (25%)",
            content=(
                "MANDATORY GOVERNANCE: All enterprise SaaS pricing proposals must maintain a minimum 25% gross margin "
                "over our verified infrastructure cost basis ($600/month COGS floor). "
                "Absolute minimum permitted price is $750/month. No discounts below $750/month are permitted without CFO approval."
            ),
            priority=PriorityClass.MANDATORY,
            provenance="ApexCloud Finance Governance Policy Doc POL-2026-08",
        ),
        ContextItem(
            canonical_id="policy_source_attribution",
            entity_type=EntityType.POLICY,
            title="Policy: Mandatory Source Evidence Attribution",
            content=(
                "MANDATORY GOVERNANCE: Every competitive claim, pricing metric, and feature comparison must cite "
                "a verified Evidence node canonical ID and audited provenance. Unreferenced claims are rejected."
            ),
            priority=PriorityClass.MANDATORY,
            provenance="ApexCloud Corporate Audit Standard CAS-04",
        ),
        ContextItem(
            canonical_id="policy_anti_predatory",
            entity_type=EntityType.POLICY,
            title="Policy: Sustainable Non-Predatory Pricing",
            content=(
                "MANDATORY GOVERNANCE: ApexCloud will not engage in loss-leader or predatory below-cost pricing. "
                "Value proposition must emphasize total cost of ownership (TCO) and transparent egress."
            ),
            priority=PriorityClass.MANDATORY,
            provenance="ApexCloud Executive Committee Memo 2026-B",
        ),
        # Tools
        ContextItem(
            canonical_id="tool_search_kg",
            entity_type=EntityType.TOOL,
            title="Tool: search_knowledge_graph",
            content="Tool schema to execute Cypher queries against companies, products, documents, and evidence in FalkorDB.",
            priority=PriorityClass.TOOL_SCHEMA,
            provenance="Banana Tool Registry",
        ),
        ContextItem(
            canonical_id="tool_retrieve_evidence",
            entity_type=EntityType.TOOL,
            title="Tool: retrieve_evidence",
            content="Tool schema to retrieve full audited evidence details, invoice extracts, and document provenance.",
            priority=PriorityClass.TOOL_SCHEMA,
            provenance="Banana Tool Registry",
        ),
        ContextItem(
            canonical_id="tool_compare_pricing",
            entity_type=EntityType.TOOL,
            title="Tool: compare_competitors",
            content="Tool schema to compute effective monthly pricing matrices factoring in base fees, egress, and SLAs.",
            priority=PriorityClass.TOOL_SCHEMA,
            provenance="Banana Tool Registry",
        ),
        ContextItem(
            canonical_id="tool_save_finding",
            entity_type=EntityType.TOOL,
            title="Tool: save_finding",
            content="Tool schema to write persistent memory nodes, superseding relationships, and strategic findings into FalkorDB.",
            priority=PriorityClass.TOOL_SCHEMA,
            provenance="Banana Tool Registry",
        ),
    ]

    relationships: List[Tuple[str, str, str]] = [
        # Task -> Requirements
        ("task_pricing_strategy", "REQUIRES", "req_competitor_tiers"),
        ("task_pricing_strategy", "REQUIRES", "req_egress_hidden_fees"),
        ("task_pricing_strategy", "REQUIRES", "req_feature_parity"),
        ("task_pricing_strategy", "REQUIRES", "req_margin_compliance"),
        ("task_pricing_strategy", "REQUIRES", "req_past_decisions"),
        # Task -> Policies
        ("task_pricing_strategy", "GOVERNED_BY", "policy_minimum_margin"),
        ("task_pricing_strategy", "GOVERNED_BY", "policy_source_attribution"),
        ("task_pricing_strategy", "GOVERNED_BY", "policy_anti_predatory"),
        # Task -> Tools
        ("task_pricing_strategy", "USES_TOOL", "tool_search_kg"),
        ("task_pricing_strategy", "USES_TOOL", "tool_retrieve_evidence"),
        ("task_pricing_strategy", "USES_TOOL", "tool_compare_pricing"),
        ("task_pricing_strategy", "USES_TOOL", "tool_save_finding"),
        # Inter-requirement dependencies
        ("req_margin_compliance", "DEPENDS_ON", "policy_minimum_margin"),
        ("req_egress_hidden_fees", "DEPENDS_ON", "req_competitor_tiers"),
        ("req_feature_parity", "DEPENDS_ON", "req_competitor_tiers"),
    ]

    return items, relationships


def get_seed_knowledge_items() -> Tuple[List[ContextItem], List[Tuple[str, str, str]]]:
    """Return knowledge graph items and relationship tuples (source_id, rel_type, target_id)."""
    items: List[ContextItem] = [
        # Companies
        ContextItem(
            canonical_id="comp_apexcloud",
            entity_type=EntityType.COMPANY,
            title="ApexCloud Technologies (Internal)",
            content="ApexCloud is our internal company providing enterprise graph intelligence and vector database infrastructure with high uptime and zero egress markup.",
            priority=PriorityClass.BACKGROUND,
            provenance="ApexCloud Corporate Factsheet 2026",
        ),
        ContextItem(
            canonical_id="comp_cloudscale",
            entity_type=EntityType.COMPETITOR,
            title="CloudScale Systems",
            content="Direct competitor known for aggressive sticker-price discounting, but high downstream bandwidth and egress overage fees.",
            priority=PriorityClass.EVIDENCE,
            provenance="Market Intelligence Briefing Q2 2026",
        ),
        ContextItem(
            canonical_id="comp_hyperstore",
            entity_type=EntityType.COMPETITOR,
            title="HyperStore Networks",
            content="Traditional enterprise infrastructure vendor offering predictable bundled storage tiers with strict SLA penalties.",
            priority=PriorityClass.EVIDENCE,
            provenance="Market Intelligence Briefing Q2 2026",
        ),
        ContextItem(
            canonical_id="comp_datavanguard",
            entity_type=EntityType.COMPETITOR,
            title="DataVanguard AI",
            content="Emerging competitor using pure consumption-based compute unit pricing, leading to unpredictable monthly customer bills.",
            priority=PriorityClass.EVIDENCE,
            provenance="Market Intelligence Briefing Q2 2026",
        ),
        # Products
        ContextItem(
            canonical_id="prod_apex_enterprise",
            entity_type=EntityType.PRODUCT,
            title="ApexCloud Enterprise Tier",
            content=(
                "ApexCloud Enterprise Plan: $1,200/month. Dedicated single-tenant clusters, sub-millisecond GraphBLAS vector engine, "
                "99.99% uptime SLA with full financial guarantee, 24/7 dedicated engineering support, 0% egress markup (at-cost bandwidth)."
            ),
            priority=PriorityClass.EVIDENCE,
            provenance="ApexCloud Product Catalog v4.1",
        ),
        ContextItem(
            canonical_id="prod_cloudscale_standard",
            entity_type=EntityType.PRODUCT,
            title="CloudScale Enterprise Standard",
            content=(
                "CloudScale advertised pricing: $800/month base. Shared multitenant cluster, 99.9% uptime SLA. "
                "Crucial fine print: $0.08 per GB egress overage fee applies to all cross-region and outbound traffic."
            ),
            priority=PriorityClass.EVIDENCE,
            provenance="CloudScale Public Pricing Page (Captured July 2026)",
        ),
        ContextItem(
            canonical_id="prod_hyperstore_scale",
            entity_type=EntityType.PRODUCT,
            title="HyperStore Scale Tier",
            content=(
                "HyperStore Scale: $1,500/month flat. Bundles 5TB data transfer, $0.05/GB thereafter. "
                "99.99% SLA but SLA breach refunds capped at 10% of monthly subscription."
            ),
            priority=PriorityClass.EVIDENCE,
            provenance="HyperStore Enterprise Agreement Schedule A",
        ),
        ContextItem(
            canonical_id="prod_datavanguard_flex",
            entity_type=EntityType.PRODUCT,
            title="DataVanguard Flex Compute",
            content=(
                "DataVanguard Flex: $0.15 per Compute Unit (CU) hour. No base monthly fee. "
                "Typical enterprise workloads consume 7,000 to 11,000 CU/month ($1,050 to $1,650/month effective). High monthly volatility."
            ),
            priority=PriorityClass.EVIDENCE,
            provenance="DataVanguard Developer Billing Guide",
        ),
        # Documents
        ContextItem(
            canonical_id="doc_cloudscale_teardown_2026",
            entity_type=EntityType.DOCUMENT,
            title="CloudScale Customer Billing Audit 2026",
            content="Forensic audit of 12 enterprise customers migrating from CloudScale to ApexCloud, detailing effective versus advertised expenditure.",
            priority=PriorityClass.BACKGROUND,
            provenance="ApexCloud Solutions Architecture Field Study CS-2026-11",
        ),
        ContextItem(
            canonical_id="doc_apex_cogs_breakdown",
            entity_type=EntityType.DOCUMENT,
            title="ApexCloud COGS & Unit Economics Analysis",
            content="Cost accounting breakdown of infrastructure compute, memory, storage, and datacenter transit costs per enterprise tenant.",
            priority=PriorityClass.MANDATORY,
            provenance="ApexCloud Finance Controller Audit 2026-Q2",
        ),
        ContextItem(
            canonical_id="doc_churn_survey_datavanguard",
            entity_type=EntityType.DOCUMENT,
            title="DataVanguard Enterprise Win/Loss Survey",
            content="Interviews with 25 engineering leaders evaluating DataVanguard vs ApexCloud regarding billing transparency.",
            priority=PriorityClass.BACKGROUND,
            provenance="B2B Tech Insights Quarterly Review",
        ),
        # Evidence (High-value groundings)
        ContextItem(
            canonical_id="ev_cloudscale_hidden_egress",
            entity_type=EntityType.EVIDENCE,
            title="Audited CloudScale Effective Monthly Bill: $1,600 - $2,000",
            content=(
                "CRITICAL EVIDENCE: Audit of customer migration logs demonstrates that while CloudScale advertises $800/mo, "
                "average enterprise data transfer (10TB - 15TB egress at $0.08/GB) adds $800 to $1,200/mo in surprise charges, "
                "raising the true total monthly cost to $1,600 - $2,000/mo. "
                "CloudScale's low sticker price is effectively negated by egress fees."
            ),
            priority=PriorityClass.EVIDENCE,
            provenance="Migration Audit Log #MIG-8843 (Audited July 2026)",
        ),
        ContextItem(
            canonical_id="ev_apex_cost_floor",
            entity_type=EntityType.EVIDENCE,
            title="Audited ApexCloud Cost Floor: $600 COGS -> $750 Minimum Price",
            content=(
                "CRITICAL EVIDENCE: Dedicated hardware allocation and datacenter transit for one Enterprise tenant costs $600/mo. "
                "A 25% gross margin requirement sets the non-negotiable pricing floor at $750/mo ($600 / (1 - 0.25) = $800 standard, "
                "or $600 * 1.25 = $750 cost-plus minimum). Pricing below $750 creates direct operating losses."
            ),
            priority=PriorityClass.MANDATORY,
            provenance="Financial Controller Certified Report #FIN-2026-04",
        ),
        ContextItem(
            canonical_id="ev_datavanguard_churn_unpredictability",
            entity_type=EntityType.EVIDENCE,
            title="42% DataVanguard Customer Dissatisfaction Due to Unpredictable Invoicing",
            content=(
                "CRITICAL EVIDENCE: 42% of surveyed DataVanguard enterprise customers reported billing disputes due to unexpected "
                "compute spikes during batch ETL runs. Customers express strong preference for predictable fixed-tier pricing."
            ),
            priority=PriorityClass.EVIDENCE,
            provenance="Survey Report #SRV-901, ApexCloud Product Marketing",
        ),
        ContextItem(
            canonical_id="ev_hyperstore_sla_limitation",
            entity_type=EntityType.EVIDENCE,
            title="HyperStore SLA Clause Restricts Refunds to 10% Max",
            content=(
                "CRITICAL EVIDENCE: HyperStore Master Services Agreement Section 8.2 explicitly caps downtime refunds at 10% of monthly fee, "
                "whereas ApexCloud offers 100% credit for SLA violations below 99.9%."
            ),
            priority=PriorityClass.EVIDENCE,
            provenance="HyperStore MSA Review, Legal Counsel Memo LG-2026-3",
        ),
        # Persistent Memories / Prior Strategic Decisions
        ContextItem(
            canonical_id="mem_q2_decision_apex",
            entity_type=EntityType.MEMORY,
            title="Prior Decision: Maintain $1,200/mo Enterprise Tier in Q2",
            content=(
                "HISTORICAL PERSISTENT MEMORY: In Q2 2026, CEO and Strategy Committee resolved to maintain the $1,200/mo price point "
                "rather than discounting down to CloudScale's $800 sticker price. "
                "Rationale: Highlight ApexCloud's zero-egress advantage and high reliability SLA."
            ),
            priority=PriorityClass.MEMORY,
            provenance="Executive Strategy Board Meeting Minutes 2026-05-14",
        ),
        ContextItem(
            canonical_id="mem_q2_finding_discounting",
            entity_type=EntityType.MEMORY,
            title="Prior Intelligence Finding: CloudScale Secret 15-20% Discounts",
            content=(
                "HISTORICAL PERSISTENT MEMORY: Win-loss debriefs revealed CloudScale enterprise reps routinely offer an undocumented "
                "15% to 20% discount ($640 to $680/mo) when enterprise prospects demand a multi-year commitment."
            ),
            priority=PriorityClass.MEMORY,
            provenance="Competitive Intelligence Field Dispatch #CI-2026-44",
        ),
    ]

    relationships: List[Tuple[str, str, str]] = [
        # Product -> Company
        ("prod_apex_enterprise", "OFFERED_BY", "comp_apexcloud"),
        ("prod_cloudscale_standard", "OFFERED_BY", "comp_cloudscale"),
        ("prod_hyperstore_scale", "OFFERED_BY", "comp_hyperstore"),
        ("prod_datavanguard_flex", "OFFERED_BY", "comp_datavanguard"),
        # Evidence -> Document
        ("ev_cloudscale_hidden_egress", "EXTRACTED_FROM", "doc_cloudscale_teardown_2026"),
        ("ev_apex_cost_floor", "EXTRACTED_FROM", "doc_apex_cogs_breakdown"),
        ("ev_datavanguard_churn_unpredictability", "EXTRACTED_FROM", "doc_churn_survey_datavanguard"),
        # Evidence -> Product
        ("ev_cloudscale_hidden_egress", "EVALUATES", "prod_cloudscale_standard"),
        ("ev_apex_cost_floor", "VALIDATES_FLOOR", "prod_apex_enterprise"),
        ("ev_datavanguard_churn_unpredictability", "EVALUATES", "prod_datavanguard_flex"),
        ("ev_hyperstore_sla_limitation", "EVALUATES", "prod_hyperstore_scale"),
        # Memory -> Product / Company
        ("mem_q2_decision_apex", "APPLIES_TO", "prod_apex_enterprise"),
        ("mem_q2_finding_discounting", "TARGETS", "comp_cloudscale"),
    ]

    return items, relationships


class GraphSeeder:
    """Manages deterministic seeding of Demand and Knowledge graphs in FalkorDB."""

    def __init__(self, db_client: FalkorDBClient = None) -> None:
        self.db_client = db_client or get_db_client()

    def seed_graph(
        self,
        graph_name: str,
        items: List[ContextItem],
        relationships: List[Tuple[str, str, str]],
        drop_existing: bool = True,
    ) -> Dict[str, Any]:
        """Seed a single graph deterministically."""
        graph = self.db_client.get_graph(graph_name)

        if drop_existing:
            try:
                graph.delete()
            except Exception:
                pass  # Graph might not exist yet
            graph = self.db_client.get_graph(graph_name)

        # 1. Create index on canonical_id
        try:
            graph.query("CREATE INDEX FOR (n:ContextNode) ON (n.canonical_id)")
        except Exception:
            pass

        # 2. Insert items idempotently
        nodes_created = 0
        for item in items:
            bucket_num = int(item.partition_salt.replace("+", "")) if "+" in item.partition_salt else 1
            query = (
                f"MERGE (n:{item.entity_type.value}:ContextNode {{canonical_id: $canonical_id}}) "
                "SET n.title = $title, "
                "    n.content = $content, "
                "    n.provenance = $provenance, "
                "    n.priority = $priority, "
                "    n.token_cost = $token_cost, "
                "    n.partition_salt = $partition_salt, "
                "    n.bucket_id = $bucket_id, "
                "    n.entity_type = $entity_type"
            )
            params = {
                "canonical_id": item.canonical_id,
                "title": item.title,
                "content": item.content,
                "provenance": item.provenance or "",
                "priority": int(item.priority),
                "token_cost": item.token_cost,
                "partition_salt": item.partition_salt,
                "bucket_id": bucket_num,
                "entity_type": item.entity_type.value,
            }
            graph.query(query, params)
            nodes_created += 1

        # 3. Create relationships
        edges_created = 0
        for src_id, rel_type, tgt_id in relationships:
            rel_query = (
                f"MATCH (a:ContextNode {{canonical_id: $src_id}}), (b:ContextNode {{canonical_id: $tgt_id}}) "
                f"MERGE (a)-[r:{rel_type}]->(b)"
            )
            graph.query(rel_query, {"src_id": src_id, "tgt_id": tgt_id})
            edges_created += 1

        return {
            "graph_name": graph_name,
            "nodes_created": nodes_created,
            "edges_created": edges_created,
        }

    def seed_all(self, drop_existing: bool = True) -> Dict[str, Any]:
        """Seed both Demand and Knowledge graphs."""
        demand_items, demand_rels = get_seed_demand_items()
        demand_res = self.seed_graph(
            self.db_client.settings.demand_graph_name,
            demand_items,
            demand_rels,
            drop_existing=drop_existing,
        )

        knowledge_items, knowledge_rels = get_seed_knowledge_items()
        knowledge_res = self.seed_graph(
            self.db_client.settings.knowledge_graph_name,
            knowledge_items,
            knowledge_rels,
            drop_existing=drop_existing,
        )

        return {
            "demand": demand_res,
            "knowledge": knowledge_res,
            "total_nodes": demand_res["nodes_created"] + knowledge_res["nodes_created"],
            "total_edges": demand_res["edges_created"] + knowledge_res["edges_created"],
        }
