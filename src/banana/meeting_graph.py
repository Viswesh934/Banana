"""Banana Meeting Knowledge Graph Engine.

Constructs and queries structured meeting subgraphs in FalkorDB during and after calls:
- Tracks speakers, claims, proposals, commitments, and referenced browser tabs.
- Flags policy breaches during live conversation.
- Eliminates flat-summary hallucination by modeling human commitments and causal decision chains.
"""

import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from banana.db import FalkorDBClient, get_db_client


class MeetingParticipant(BaseModel):
    name: str
    role: str
    company: str = "ApexCloud"


class MeetingCommitment(BaseModel):
    commitment_id: str
    speaker_name: str
    term: str
    deadline: str
    assignee: str
    status: str = "agreed"
    referenced_doc_id: Optional[str] = None


class MeetingTurn(BaseModel):
    speaker: str
    text: str
    timestamp_str: str = "now"
    referenced_tab_id: Optional[str] = None
    policy_breach: Optional[str] = None
    nudge_text: Optional[str] = None


class MeetingSessionSummary(BaseModel):
    session_id: str
    title: str
    participant_count: int
    commitments_count: int
    policy_alerts_count: int
    referenced_tabs_count: int


class MeetingGraphManager:
    """Manages creation, ingestion, and surgical querying of FalkorDB Meeting Subgraphs."""

    def __init__(self, db_client: Optional[FalkorDBClient] = None) -> None:
        self.db_client = db_client or get_db_client()

    def initialize_session(
        self,
        session_id: str,
        title: str,
        participants: List[MeetingParticipant],
        raw_ttl_hours: int = 24,
    ) -> str:
        """Create a new MeetingSession and Speaker nodes in FalkorDB."""
        kg = self.db_client.get_knowledge_graph()

        # Create session node
        cypher = """
        MERGE (s:MeetingSession:ContextNode {canonical_id: $session_id})
        SET s.title = $title,
            s.entity_type = 'MeetingSession',
            s.priority = 2,
            s.token_cost = 40,
            s.created_at = timestamp(),
            s.raw_ttl_hours = $ttl,
            s.status = 'active'
        RETURN s.canonical_id
        """
        kg.query(cypher, {"session_id": session_id, "title": title, "ttl": raw_ttl_hours})

        # Create participant speaker nodes and connect to session
        for p in participants:
            spk_cypher = """
            MERGE (spk:Speaker:ContextNode {canonical_id: $spk_id})
            SET spk.name = $name,
                spk.role = $role,
                spk.company = $company,
                spk.title = $name + ' (' + $role + ')',
                spk.entity_type = 'Speaker',
                spk.priority = 2,
                spk.token_cost = 25
            WITH spk
            MATCH (s:MeetingSession {canonical_id: $session_id})
            MERGE (s)-[:HAS_PARTICIPANT]->(spk)
            """
            spk_id = f"spk_{p.name.lower().replace(' ', '_')}"
            kg.query(spk_cypher, {
                "spk_id": spk_id,
                "name": p.name,
                "role": p.role,
                "company": p.company,
                "session_id": session_id,
            })

        return session_id

    def record_turn(
        self,
        session_id: str,
        turn: MeetingTurn,
    ) -> Dict[str, Any]:
        """Ingest a live spoken turn, linking speaker, topics, and tab references."""
        kg = self.db_client.get_knowledge_graph()
        spk_id = f"spk_{turn.speaker.lower().replace(' ', '_')}"
        turn_id = f"turn_{uuid.uuid4().hex[:6]}"

        cypher = """
        MATCH (s:MeetingSession {canonical_id: $session_id})
        MATCH (spk:Speaker {canonical_id: $spk_id})
        CREATE (t:MeetingTurn:ContextNode {
            canonical_id: $turn_id,
            title: $speaker + ': ' + substring($text, 0, 35) + '...',
            entity_type: 'MeetingTurn',
            priority: 3,
            token_cost: 20,
            speaker: $speaker,
            text: $text,
            timestamp_str: $ts,
            nudge: $nudge,
            created_at: timestamp()
        })
        MERGE (s)-[:HAS_TURN]->(t)
        MERGE (spk)-[:SPOKE]->(t)
        """
        params = {
            "session_id": session_id,
            "spk_id": spk_id,
            "turn_id": turn_id,
            "speaker": turn.speaker,
            "text": turn.text,
            "ts": turn.timestamp_str,
            "nudge": turn.nudge_text or "",
        }
        kg.query(cypher, params)

        # If a browser tab was referenced, link the turn to the Document node
        if turn.referenced_tab_id:
            tab_cypher = """
            MATCH (t:MeetingTurn {canonical_id: $turn_id})
            MATCH (d:Document {canonical_id: $doc_id})
            MERGE (t)-[:REFERENCED_TAB]->(d)
            """
            kg.query(tab_cypher, {"turn_id": turn_id, "doc_id": turn.referenced_tab_id})

        return {"turn_id": turn_id, "status": "recorded"}

    def record_policy_breach(
        self,
        session_id: str,
        speaker_name: str,
        proposed_price: float,
        policy_id: str = "policy_minimum_margin",
        reason: str = "Proposed price violates mandatory 25% gross margin floor ($750/mo minimum).",
    ) -> str:
        """Record an in-meeting proposal that violated company governance."""
        kg = self.db_client.get_knowledge_graph()
        prop_id = f"prop_{uuid.uuid4().hex[:6]}"
        spk_id = f"spk_{speaker_name.lower().replace(' ', '_')}"

        cypher = """
        MATCH (s:MeetingSession {canonical_id: $session_id})
        MATCH (spk:Speaker {canonical_id: $spk_id})
        CREATE (p:Proposal:ContextNode {
            canonical_id: $prop_id,
            title: 'Proposal: $' + toString($price) + '/mo',
            entity_type: 'Proposal',
            priority: 0,
            token_cost: 30,
            proposed_price: $price,
            reason: $reason,
            status: 'flagged_policy_breach',
            created_at: timestamp()
        })
        MERGE (spk)-[:PROPOSED]->(p)
        MERGE (s)-[:CONTAINS_ALERT]->(p)
        WITH p
        MERGE (pol:Policy {canonical_id: $policy_id})
        MERGE (p)-[:VIOLATES]->(pol)
        RETURN p.canonical_id
        """
        res = kg.query(cypher, {
            "session_id": session_id,
            "spk_id": spk_id,
            "prop_id": prop_id,
            "price": proposed_price,
            "reason": reason,
            "policy_id": policy_id,
        })
        return prop_id

    def record_commitment(
        self,
        session_id: str,
        commitment: MeetingCommitment,
    ) -> str:
        """Record an explicit human commitment or agreed term with deadline and assignee."""
        kg = self.db_client.get_knowledge_graph()
        spk_id = f"spk_{commitment.speaker_name.lower().replace(' ', '_')}"

        cypher = """
        MATCH (s:MeetingSession {canonical_id: $session_id})
        MATCH (spk:Speaker {canonical_id: $spk_id})
        MERGE (c:Commitment:ContextNode {canonical_id: $cid})
        SET c.term = $term,
            c.title = 'Commitment: ' + $term,
            c.entity_type = 'Commitment',
            c.priority = 1,
            c.token_cost = 35,
            c.deadline = $deadline,
            c.assignee = $assignee,
            c.status = $status,
            c.created_at = timestamp()
        MERGE (s)-[:HAS_COMMITMENT]->(c)
        MERGE (spk)-[:COMMITTED_TO]->(c)
        RETURN c.canonical_id
        """
        kg.query(cypher, {
            "session_id": session_id,
            "spk_id": spk_id,
            "cid": commitment.commitment_id,
            "term": commitment.term,
            "deadline": commitment.deadline,
            "assignee": commitment.assignee,
            "status": commitment.status,
        })

        if commitment.referenced_doc_id:
            doc_cypher = """
            MATCH (c:Commitment {canonical_id: $cid})
            MATCH (d:Document {canonical_id: $doc_id})
            MERGE (c)-[:GROUNDED_IN]->(d)
            """
            kg.query(doc_cypher, {"cid": commitment.commitment_id, "doc_id": commitment.referenced_doc_id})

        return commitment.commitment_id

    def get_session_summary(self, session_id: str) -> MeetingSessionSummary:
        """Fetch statistics for a meeting session directly from FalkorDB."""
        kg = self.db_client.get_knowledge_graph()
        cypher = """
        MATCH (s:MeetingSession {canonical_id: $session_id})
        OPTIONAL MATCH (s)-[:HAS_PARTICIPANT]->(spk:Speaker)
        OPTIONAL MATCH (s)-[:HAS_COMMITMENT]->(com:Commitment)
        OPTIONAL MATCH (s)-[:CONTAINS_ALERT]->(prop:Proposal)
        OPTIONAL MATCH (s)-[:HAS_TURN]->(t:MeetingTurn)-[:REFERENCED_TAB]->(d:Document)
        RETURN s.title,
               count(DISTINCT spk),
               count(DISTINCT com),
               count(DISTINCT prop),
               count(DISTINCT d)
        """
        res = kg.query(cypher, {"session_id": session_id})
        if not res.result_set:
            return MeetingSessionSummary(
                session_id=session_id,
                title="Unknown Session",
                participant_count=0,
                commitments_count=0,
                policy_alerts_count=0,
                referenced_tabs_count=0,
            )

        row = res.result_set[0]
        return MeetingSessionSummary(
            session_id=session_id,
            title=row[0] or "Executive Meeting",
            participant_count=row[1] or 0,
            commitments_count=row[2] or 0,
            policy_alerts_count=row[3] or 0,
            referenced_tabs_count=row[4] or 0,
        )

    def query_meeting_graph(self, session_id: str, question: str) -> str:
        """Surgically answer questions about the meeting by traversing FalkorDB graph relationships."""
        q_lower = question.lower()
        kg = self.db_client.get_knowledge_graph()

        # Case 1: Who committed to what? / Commitments
        if "commit" in q_lower or "promise" in q_lower or "action" in q_lower or "alex" in q_lower:
            cypher = """
            MATCH (s:MeetingSession {canonical_id: $session_id})-[:HAS_COMMITMENT]->(c:Commitment)
            MATCH (spk:Speaker)-[:COMMITTED_TO]->(c)
            OPTIONAL MATCH (c)-[:GROUNDED_IN]->(d:Document)
            RETURN spk.name, c.term, c.deadline, c.assignee, d.name
            """
            res = kg.query(cypher, {"session_id": session_id})
            if res.result_set:
                lines = ["### Verified Meeting Commitments (FalkorDB Graph Traversal):"]
                for r in res.result_set:
                    doc_cite = f" (Referenced Document: `{r[4]}`)" if r[4] else ""
                    lines.append(f"- **Speaker:** {r[0]} | **Commitment:** {r[1]} | **Deadline:** {r[2]} | **Assignee:** {r[3]}{doc_cite}")
                return "\n".join(lines)

        # Case 2: What tabs / documents were referenced?
        if "tab" in q_lower or "doc" in q_lower or "invoice" in q_lower or "open" in q_lower:
            cypher = """
            MATCH (s:MeetingSession {canonical_id: $session_id})-[:HAS_TURN]->(t:MeetingTurn)-[:REFERENCED_TAB]->(d:Document)
            RETURN DISTINCT d.canonical_id, d.name, t.speaker, t.text
            """
            res = kg.query(cypher, {"session_id": session_id})
            if res.result_set:
                lines = ["### Referenced Browser Tabs & Documents:"]
                for r in res.result_set:
                    lines.append(f"- 📄 **Document:** `{r[1]}` (ID: `{r[0]}`) — referenced when **{r[2]}** said: *\"{r[3]}\"*")
                return "\n".join(lines)

        # Case 3: Policy breaches / Alerts
        if "policy" in q_lower or "alert" in q_lower or "margin" in q_lower or "breach" in q_lower or "price" in q_lower:
            cypher = """
            MATCH (s:MeetingSession {canonical_id: $session_id})-[:CONTAINS_ALERT]->(p:Proposal)-[:VIOLATES]->(pol:Policy)
            MATCH (spk:Speaker)-[:PROPOSED]->(p)
            RETURN spk.name, p.proposed_price, p.reason, pol.canonical_id
            """
            res = kg.query(cypher, {"session_id": session_id})
            if res.result_set:
                lines = ["### In-Meeting Governance Alerts:"]
                for r in res.result_set:
                    lines.append(f"- ⚠️ **Speaker:** {r[0]} proposed **${r[1]}/mo** — **Alert:** {r[2]} (Violates `{r[3]}`)")
                return "\n".join(lines)

        # Default: General session overview
        summary = self.get_session_summary(session_id)
        return (
            f"**Session Overview for '{summary.title}'**:\n"
            f"- **Participants:** {summary.participant_count}\n"
            f"- **Agreed Commitments:** {summary.commitments_count}\n"
            f"- **Governance Alerts Flagged:** {summary.policy_alerts_count}\n"
            f"- **Referenced Tabs/Documents:** {summary.referenced_tabs_count}\n\n"
            f"*Try asking: 'What did Alex commit to?', 'Which tabs were referenced?', or 'Did we violate any margin policies?'*"
        )
