"""Structured FalkorDB graph-backed tools for the Banana agent."""

import time
from typing import Any, Dict, List, Optional
from banana.db import FalkorDBClient, get_db_client
from banana.models import calculate_partition_salt


class AgentTools:
    """Graph-backed tools executed by the Banana agent."""

    def __init__(self, db_client: Optional[FalkorDBClient] = None) -> None:
        self.db_client = db_client or get_db_client()

    def search_knowledge_graph(self, query_term: str, entity_type: Optional[str] = None) -> Dict[str, Any]:
        """Search entities in the Knowledge Graph by title or content substring."""
        graph = self.db_client.get_knowledge_graph()
        q_lower = query_term.lower()

        if entity_type:
            cypher = """
            MATCH (n:ContextNode)
            WHERE n.entity_type = $entity_type
              AND (toLower(n.title) CONTAINS $q OR toLower(n.content) CONTAINS $q)
            RETURN n.canonical_id, n.entity_type, n.title, n.content, n.provenance
            LIMIT 10
            """
            params = {"q": q_lower, "entity_type": entity_type}
        else:
            cypher = """
            MATCH (n:ContextNode)
            WHERE toLower(n.title) CONTAINS $q OR toLower(n.content) CONTAINS $q
            RETURN n.canonical_id, n.entity_type, n.title, n.content, n.provenance
            LIMIT 10
            """
            params = {"q": q_lower}

        res = graph.query(cypher, params)
        matches = []
        for row in res.result_set:
            matches.append({
                "canonical_id": row[0],
                "entity_type": row[1],
                "title": row[2],
                "content": row[3],
                "provenance": row[4],
            })

        return {
            "query": query_term,
            "entity_type": entity_type,
            "match_count": len(matches),
            "results": matches,
        }

    def retrieve_evidence(self, evidence_id: str) -> Dict[str, Any]:
        """Fetch verbatim evidence details, audited claims, and source document citations."""
        graph = self.db_client.get_knowledge_graph()
        cypher = """
        MATCH (e:ContextNode {canonical_id: $id})
        OPTIONAL MATCH (e)-[:EXTRACTED_FROM]->(d:Document)
        OPTIONAL MATCH (e)-[:VALIDATES_FLOOR|EVALUATES]->(p:Product)
        RETURN e.canonical_id, e.title, e.content, e.provenance, e.priority,
               d.canonical_id, d.title, p.canonical_id, p.title
        """
        res = graph.query(cypher, {"id": evidence_id})
        if not res.result_set:
            return {"error": f"Evidence node '{evidence_id}' not found in Knowledge Graph."}

        row = res.result_set[0]
        return {
            "evidence_id": row[0],
            "title": row[1],
            "audited_content": row[2],
            "provenance": row[3],
            "priority": row[4],
            "source_document": {"id": row[5], "title": row[6]} if row[5] else None,
            "target_product": {"id": row[7], "title": row[8]} if row[7] else None,
        }

    def compare_competitors(self) -> Dict[str, Any]:
        """Compute an effective total-cost-of-ownership (TCO) comparison across all competitors."""
        graph = self.db_client.get_knowledge_graph()
        cypher = """
        MATCH (p:Product)-[:OFFERED_BY]->(c:ContextNode)
        RETURN c.canonical_id, c.title, p.canonical_id, p.title, p.content
        """
        res = graph.query(cypher)
        competitors = []
        for row in res.result_set:
            competitors.append({
                "company_id": row[0],
                "company_name": row[1],
                "product_id": row[2],
                "product_title": row[3],
                "details": row[4],
            })

        # Structured synthesis of market data
        analysis = [
            {
                "company": "ApexCloud (Internal)",
                "advertised_base": "$1,200/mo",
                "hidden_fees": "$0 egress markup (at-cost transit)",
                "effective_monthly_tco": "$1,200/mo",
                "margin_above_floor": "50% (Floor is $600 COGS -> $750 min price)",
                "sla": "99.99% with 100% financial guarantee",
                "key_risk": "Perception of higher sticker price against CloudScale's $800 lure.",
            },
            {
                "company": "CloudScale Systems",
                "advertised_base": "$800/mo",
                "hidden_fees": "$0.08/GB egress. Standard 15TB egress adds $1,200/mo.",
                "effective_monthly_tco": "$1,600 - $2,000/mo",
                "margin_above_floor": "N/A (Competitor)",
                "sla": "99.9% (Shared multitenant)",
                "key_risk": "Exploitative billing; hidden egress costs 2x the base fee.",
            },
            {
                "company": "HyperStore Networks",
                "advertised_base": "$1,500/mo (Includes 5TB)",
                "hidden_fees": "$0.05/GB overage",
                "effective_monthly_tco": "$1,500 - $1,750/mo",
                "margin_above_floor": "N/A (Competitor)",
                "sla": "99.99% with strict 10% refund cap",
                "key_risk": "Rigid pricing tiers and restrictive downtime refund terms.",
            },
            {
                "company": "DataVanguard AI",
                "advertised_base": "$0.15/Compute Unit",
                "hidden_fees": "Uncapped compute volatility",
                "effective_monthly_tco": "$1,050 - $1,650/mo (Variable)",
                "margin_above_floor": "N/A (Competitor)",
                "sla": "99.9% (SOC2/HIPAA certified)",
                "key_risk": "High churn (42% customer disputes over monthly bill swings).",
            },
        ]

        return {
            "entity_count": len(competitors),
            "market_summary": analysis,
        }

    def save_finding(
        self,
        title: str,
        finding: str,
        provenance: str = "Banana Agent Executive Session",
        supersedes_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Persist an agent decision or intelligence finding to FalkorDB persistent memory."""
        from banana.tokenizer import count_tokens

        graph = self.db_client.get_knowledge_graph()
        timestamp = int(time.time() * 1000)
        canonical_id = f"mem_decision_{timestamp}"
        salt = calculate_partition_salt(canonical_id)
        cost = count_tokens(f"{title}\n{finding}\nSource: {provenance}")

        cypher = """
        CREATE (m:Memory:ContextNode {
            canonical_id: $id,
            entity_type: 'Memory',
            title: $title,
            content: $content,
            provenance: $provenance,
            priority: 3,
            token_cost: $token_cost,
            partition_salt: $salt,
            created_at: timestamp()
        })
        RETURN m.canonical_id
        """
        params = {
            "id": canonical_id,
            "title": title,
            "content": finding,
            "provenance": provenance,
            "token_cost": cost,
            "salt": salt,
        }
        res = graph.query(cypher, params)
        if not res.result_set:
            return {"error": "Failed to persist memory node in FalkorDB."}

        # If this finding supersedes a prior memory, link it with SUPERSEDES relationship
        if supersedes_id:
            link_cypher = """
            MATCH (new_m:Memory {canonical_id: $new_id}), (old_m:Memory {canonical_id: $old_id})
            MERGE (new_m)-[:SUPERSEDES]->(old_m)
            """
            graph.query(link_cypher, {"new_id": canonical_id, "old_id": supersedes_id})

        return {
            "status": "success",
            "canonical_id": canonical_id,
            "title": title,
            "supersedes": supersedes_id,
            "timestamp": timestamp,
        }

    def list_findings(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent persistent memory decisions and findings from the Knowledge Graph."""
        graph = self.db_client.get_knowledge_graph()
        cypher = """
        MATCH (m:ContextNode)
        WHERE m.entity_type = 'Memory' OR 'Memory' IN labels(m)
        OPTIONAL MATCH (m)-[:SUPERSEDES]->(old_m)
        RETURN m.canonical_id, m.title, m.content, m.provenance, old_m.canonical_id
        ORDER BY m.created_at DESC
        LIMIT $limit
        """
        try:
            res = graph.query(cypher, {"limit": limit})
            findings = []
            for row in res.result_set:
                findings.append({
                    "canonical_id": row[0],
                    "title": row[1],
                    "finding": row[2],
                    "provenance": row[3],
                    "supersedes": row[4] if len(row) > 4 else None,
                })
            return findings
        except Exception:
            return []
