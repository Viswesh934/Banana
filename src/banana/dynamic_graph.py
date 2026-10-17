"""Dynamic Session-Based Knowledge Graph Manager for Banana.

Extracts, stores, and manages session-isolated entities and relationships
dynamically generated from user conversations, documents, and research queries.
"""

import json
import re
from typing import Any, Dict, List, Optional, Set
from banana.db import FalkorDBClient, get_db_client
from banana.models import PriorityClass


class DynamicGraphManager:
    """Manages dynamic, user-driven session knowledge graphs in FalkorDB."""

    def __init__(self, db_client: Optional[FalkorDBClient] = None) -> None:
        self.db_client = db_client or get_db_client()

    def add_entity(
        self,
        session_id: str,
        canonical_id: str,
        entity_type: str,
        title: str,
        content: str = "",
        priority: int = PriorityClass.EVIDENCE,
        token_cost: int = 50,
    ) -> Dict[str, Any]:
        """Add or update an entity node scoped to a session in the knowledge graph."""
        k_graph = self.db_client.get_knowledge_graph()
        # Clean canonical_id
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", canonical_id.strip()).lower()
        if not safe_id:
            safe_id = f"entity_{abs(hash(title)) % 100000}"

        query = (
            "MERGE (n:ContextNode {canonical_id: $canonical_id}) "
            "SET n.title = $title, "
            "    n.content = $content, "
            "    n.entity_type = $entity_type, "
            "    n.session_id = $session_id, "
            "    n.priority = $priority, "
            "    n.token_cost = $token_cost "
            "RETURN n.canonical_id AS id"
        )
        params = {
            "canonical_id": safe_id,
            "title": title[:100],
            "content": content,
            "entity_type": entity_type.capitalize() if entity_type else "Concept",
            "session_id": session_id,
            "priority": int(priority),
            "token_cost": token_cost,
        }
        k_graph.query(query, params)
        return {"id": safe_id, "title": title, "type": entity_type, "session_id": session_id}

    def add_relationship(
        self,
        session_id: str,
        source_id: str,
        target_id: str,
        rel_type: str = "RELATES_TO",
    ) -> bool:
        """Add a directed edge between two entities within a session."""
        k_graph = self.db_client.get_knowledge_graph()
        safe_src = re.sub(r"[^a-zA-Z0-9_-]", "_", source_id.strip()).lower()
        safe_tgt = re.sub(r"[^a-zA-Z0-9_-]", "_", target_id.strip()).lower()
        safe_rel = re.sub(r"[^a-zA-Z0-9_]", "_", rel_type.strip().upper()) or "RELATES_TO"

        query = (
            f"MATCH (a:ContextNode {{canonical_id: $src_id}}), (b:ContextNode {{canonical_id: $tgt_id}}) "
            f"MERGE (a)-[r:{safe_rel} {{session_id: $session_id}}]->(b) "
            "RETURN type(r)"
        )
        res = k_graph.query(query, {"src_id": safe_src, "tgt_id": safe_tgt, "session_id": session_id})
        return len(res.result_set) > 0

    def ingest_extracted_graph(
        self,
        session_id: str,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        """Bulk ingest extracted entities and relationships for a session."""
        created_nodes = 0
        created_edges = 0

        id_map: Dict[str, str] = {}
        for ent in entities:
            raw_id = ent.get("id") or ent.get("title") or "entity"
            title = ent.get("title") or ent.get("name") or raw_id
            etype = ent.get("type") or "Concept"
            desc = ent.get("description") or ent.get("content") or ""
            res = self.add_entity(
                session_id=session_id,
                canonical_id=raw_id,
                entity_type=etype,
                title=title,
                content=desc,
            )
            id_map[raw_id] = res["id"]
            id_map[title.lower()] = res["id"]
            created_nodes += 1

        for rel in relationships:
            src = rel.get("source") or rel.get("from") or ""
            tgt = rel.get("target") or rel.get("to") or ""
            rtype = rel.get("relation") or rel.get("type") or "RELATES_TO"

            src_id = id_map.get(src, re.sub(r"[^a-zA-Z0-9_-]", "_", src.strip()).lower())
            tgt_id = id_map.get(tgt, re.sub(r"[^a-zA-Z0-9_-]", "_", tgt.strip()).lower())

            if src_id and tgt_id and src_id != tgt_id:
                if self.add_relationship(session_id, src_id, tgt_id, rtype):
                    created_edges += 1

        return {"nodes_created": created_nodes, "edges_created": created_edges}

    def get_session_nodes_and_edges(self, session_id: str) -> Dict[str, Any]:
        """Retrieve all nodes and edges belonging to a given session."""
        k_graph = self.db_client.get_knowledge_graph()

        nodes_res = k_graph.query(
            "MATCH (n:ContextNode {session_id: $sid}) "
            "RETURN n.canonical_id, n.entity_type, n.title, n.content, n.priority, n.token_cost",
            {"sid": session_id},
        )
        nodes: List[Dict[str, Any]] = []
        node_ids: Set[str] = set()
        for r in nodes_res.result_set:
            cid = r[0]
            node_ids.add(cid)
            nodes.append({
                "id": cid,
                "type": r[1] or "Concept",
                "title": r[2] or cid,
                "content": r[3] or "",
                "priority": r[4] or PriorityClass.EVIDENCE,
                "token_cost": r[5] or 0,
            })

        edges_res = k_graph.query(
            "MATCH (a:ContextNode {session_id: $sid})-[r]->(b:ContextNode {session_id: $sid}) "
            "RETURN a.canonical_id, type(r), b.canonical_id",
            {"sid": session_id},
        )
        edges: List[Dict[str, Any]] = []
        for r in edges_res.result_set:
            edges.append({
                "source": r[0],
                "relation": r[1],
                "target": r[2],
            })

        return {"nodes": nodes, "edges": edges, "session_id": session_id}

    def get_session_context_summary(self, session_id: str) -> str:
        """Format the session's dynamic knowledge graph into a concise text prompt context."""
        graph_data = self.get_session_nodes_and_edges(session_id)
        nodes = graph_data["nodes"]
        edges = graph_data["edges"]

        if not nodes:
            return ""

        lines = ["### Session Knowledge Graph Context:"]
        lines.append(f"Discovered Entities ({len(nodes)}):")
        for n in nodes[:20]:
            lines.append(f"- [{n['type']}] **{n['title']}** (ID: {n['id']}): {n['content']}")

        if edges:
            lines.append(f"\nDiscovered Relationships ({len(edges)}):")
            for e in edges[:25]:
                lines.append(f"- ({e['source']}) --[{e['relation']}]--> ({e['target']})")

        return "\n".join(lines)

    def clear_session(self, session_id: str) -> int:
        """Remove all nodes and relationships belonging to a specific session."""
        k_graph = self.db_client.get_knowledge_graph()
        res = k_graph.query(
            "MATCH (n:ContextNode {session_id: $sid}) DETACH DELETE n",
            {"sid": session_id},
        )
        return getattr(res, "nodes_deleted", 0)

    def clear_all_dynamic_graphs(self) -> None:
        """Remove all session-isolated nodes across all sessions."""
        k_graph = self.db_client.get_knowledge_graph()
        k_graph.query("MATCH (n:ContextNode) WHERE exists(n.session_id) DETACH DELETE n")
