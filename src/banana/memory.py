"""Persistent cross-session memory management and company knowledge retrieval in FalkorDB."""

from typing import Any, Dict, List, Optional
from banana.db import FalkorDBClient, get_db_client


class MemoryManager:
    """Manages persistent cross-session memory, superseding relationships, and multi-hop knowledge retrieval."""

    def __init__(self, db_client: Optional[FalkorDBClient] = None) -> None:
        self.db_client = db_client or get_db_client()

    def get_active_memories(self) -> List[Dict[str, Any]]:
        """Retrieve all active memories that have NOT been superseded by newer decisions."""
        graph = self.db_client.get_knowledge_graph()
        cypher = """
        MATCH (m:Memory)
        WHERE NOT (m)<-[:SUPERSEDES]-()
        RETURN m.canonical_id, m.title, m.content, m.provenance, m.created_at
        ORDER BY m.created_at DESC
        """
        res = graph.query(cypher)
        memories = []
        for row in res.result_set:
            memories.append({
                "canonical_id": row[0],
                "title": row[1],
                "content": row[2],
                "provenance": row[3],
                "created_at": row[4],
                "status": "active",
            })
        return memories

    def get_superseded_history(self) -> List[Dict[str, Any]]:
        """Retrieve historical decisions that were superseded, along with their replacement."""
        graph = self.db_client.get_knowledge_graph()
        cypher = """
        MATCH (newer:Memory)-[:SUPERSEDES]->(older:Memory)
        RETURN newer.canonical_id, newer.title, older.canonical_id, older.title, newer.created_at
        ORDER BY newer.created_at DESC
        """
        res = graph.query(cypher)
        history = []
        for row in res.result_set:
            history.append({
                "newer_decision_id": row[0],
                "newer_title": row[1],
                "superseded_decision_id": row[2],
                "superseded_title": row[3],
                "replaced_at": row[4],
            })
        return history

    def multi_hop_company_context(self, company_id: str = "comp_apexcloud") -> Dict[str, Any]:
        """Perform multi-hop retrieval connecting internal company products, policies, and evidence."""
        k_graph = self.db_client.get_knowledge_graph()
        d_graph = self.db_client.get_demand_graph()

        # Multi-hop in Knowledge Graph: Company -> Product -> Evidence -> Document
        cypher = """
        MATCH (c:Company {canonical_id: $cid})<-[:OFFERED_BY]-(p:Product)
        OPTIONAL MATCH (p)<-[:VALIDATES_FLOOR|SUPPORTS|EVALUATES]-(e:Evidence)
        OPTIONAL MATCH (e)-[:EXTRACTED_FROM]->(d:Document)
        RETURN c.title, p.canonical_id, p.title, e.canonical_id, e.title, d.canonical_id, d.title
        """
        k_res = k_graph.query(cypher, {"cid": company_id})
        knowledge_chain = []
        for row in k_res.result_set:
            knowledge_chain.append({
                "company": row[0],
                "product_id": row[1],
                "product": row[2],
                "evidence_id": row[3],
                "evidence": row[4],
                "source_doc_id": row[5],
                "source_doc": row[6],
            })

        # Connected Policies in Demand Graph
        p_res = d_graph.query("MATCH (p:Policy) RETURN p.canonical_id, p.title, p.content")
        policies = [{"id": r[0], "title": r[1], "content": r[2]} for r in p_res.result_set]

        # Active cross-session memories
        active_mems = self.get_active_memories()

        return {
            "company_id": company_id,
            "connected_knowledge_chains": knowledge_chain,
            "governing_policies": policies,
            "active_cross_session_memories": active_mems,
        }
