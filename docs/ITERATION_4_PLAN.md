# Banana: Iteration 4 Plan — Floating Banana Desktop Demo & Meeting Graph

## 1. Executive Vision

In **Iteration 4**, Banana evolves into an ambient desktop companion demo that bridges high-powered AI coding tools (Claude Code, Cursor, Antigravity) to non-technical business operators. 

Instead of generating flat text summaries that cause hallucination and context loss, Banana **constructs a live Meeting Knowledge Graph in FalkorDB** during calls, surfaces real-time micro-nudges via a **Floating Banana HUD**, remembers exact browser tabs, and enables surgical post-call conversational debriefs.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BANANA FLOATING DESKTOP COMPANION                        │
│                                                                             │
│  [Asleep / Zero-Token Pill]  ──►  [Trigger: Safe Word / Hotkey Alt+Space]   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      IN-MEETING AMBIENT NUDGES & TAB MEMORY                 │
│  • 15-Word Micro-Nudges (Competitor claims, pricing floor whispers)        │
│  • Instant Tab Memory: "🔗 Jump to Tab 4: CloudScale CS-902 Invoice"       │
│  • Ephemeral 30s local ring buffer: ZERO cloud tokens burned while idle    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Call Concludes
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 FALKORDB MEETING GRAPH CONSTRUCTION (NO FLAT SUMMARIES)      │
│  • (:Speaker)-[:COMMITTED_TO]->(:Commitment {deadline, terms})             │
│  • (:Speaker)-[:PROPOSED]->(:Proposal)-[:VIOLATES]->(:Policy)              │
│  • (:Topic)-[:REFERENCED_TAB]->(:Document {url, exact_tab_id})             │
│  • (:Decision)-[:SUPERSEDES]->(:OldDecision)                               │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    POST-MEETING GRAPH-POWERED DIALOGUE                      │
│  • "What did Alex commit to?" -> Traverses graph directly (100% accuracy)   │
│  • "What tab was Sarah viewing?" -> Returns exact document deep-link        │
│  • Retention Policy: 24h raw transcript decay; permanent graph promotion   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. The FalkorDB Meeting Graph Schema

Rather than storing a wall of text, the meeting is ingested as an interconnected knowledge subgraph:

### Node Types
- `(:MeetingSession {session_id, title, date, retention_ttl})`
- `(:Speaker {name, role})`
- `(:Topic {name, category})`
- `(:Proposal {price, terms, margin_pct})`
- `(:Commitment {term, deadline, status, assignee})`
- `(:Decision {title, rationale, timestamp})`
- `(:Document {title, url, exact_tab_id, mime_type})`

### Relationship Types
- `(:MeetingSession)-[:INCLUDES]->(:Topic)`
- `(:Speaker)-[:PROPOSED]->(:Proposal)`
- `(:Proposal)-[:VIOLATES]->(:Policy)` (flags margin breaches during call)
- `(:Speaker)-[:COMMITTED_TO]->(:Commitment)`
- `(:Commitment)-[:GROUNDED_IN]->(:Document)`
- `(:Topic)-[:REFERENCED_TAB]->(:Document)`
- `(:Decision)-[:SUPERSEDES]->(:Decision)`

---

## 3. Demo Implementation Components (For Tomorrow)

### Pillar 1: Floating Banana Meeting HUD (Streamlit Desktop Window)
- Floating widget pinned to the corner with smooth CSS styling.
- **Visual States:**
  - *Ambient Idle Pill:* Pulsing golden banana, zero tokens consumed.
  - *Flash Nudge Card:* Pops up for 8 seconds when competitor keywords or hotkey `Alt+Space` is triggered.
  - *Tab Memory Button:* Direct link to restore referenced documents.

### Pillar 2: Interactive Meeting Simulator
- Pre-scripted audio/transcript scenarios (e.g., Executive Pricing War call with competitor mentions).
- Trigger simulator: simulate spoken safe words (*"Banana, check this"*) or hotkey presses.
- Live token burn counter: proves zero tokens burned during idle chatter.

### Pillar 3: Graph Construction Pipeline (`src/banana/meeting_graph.py`)
- Ingests meeting transcript turns $\to$ Gemini 3.5 Flash extracts entities $\to$ writes the Meeting Subgraph into FalkorDB in $<20\text{ms}$.
- Live render in the D3.js **Visual Brain** tab showing speakers, commitments, and documents.

### Pillar 4: Post-Meeting Graph Dialogue
- Interactive chat tab allowing non-technical users to converse directly with the meeting graph.
- Demonstrates exact attribution ("Alex promised X by Friday") and tab retrieval with zero hallucinations.
- Retention TTL control slider (e.g., 24h transcript decay vs permanent graph promotion).

---

## 4. Tomorrow's Execution Checklist

- [ ] Implement `src/banana/meeting_graph.py` (FalkorDB Meeting Subgraph schema & Cypher builder).
- [ ] Add "🎙️ Ambient Meeting HUD & Simulator" tab in `app.py`:
  - Floating banana glassmorphism widget with trigger simulation.
  - Interactive transcript player with competitor fee mentions.
  - Instant "Jump to Exact Tab" action card.
- [ ] Connect Post-Meeting Conversational Chat to query the meeting graph.
- [ ] Add unit tests in `tests/test_iteration_4.py`.
- [ ] Prepare an executive demo walkthrough recording / script.
