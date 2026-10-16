# Banana: Iteration 2 Planning — Multi-Session & Background Maintenance

## 1. Executive Overview

In **Iteration 1**, Banana established:
- FalkorDB Dual-Graph Foundation (`banana_demand` & `banana_knowledge`).
- Graph-Aware Context Assembly & Progressive Load Shedding under strict token budgets.
- Live Gemini model integration (`gemini-3.5-flash`) with structured graph tools.
- Persistent cross-session memory with `[:SUPERSEDES]` lineage.
- Scientific benchmarking proving 100% policy and dependency preservation.

In **Iteration 2**, we expand Banana from an atomic task-execution agent into a **stateful, multi-session agent platform with automated background graph maintenance**.

---

## 2. Pillar 1: Multi-Session & Conversation Turn Architecture

### 2.1 The Graph Data Model
Currently, memories persist across runs, but individual sessions and conversation turns are not modeled as queryable graph entities.

```
┌─────────────────────────────────────────────────────────────┐
│                      SESSION GRAPH                          │
│                                                             │
│  (:Session {session_id, title, created_at, turn_count})    │
│       │                                │                    │
│       ├──[:HAS_TURN]──► (:Turn)        └──[:PRODUCED]──►    │
│       │                  (role, content)           (:Memory)│
│       └──[:HAS_TURN]──► (:Turn)                             │
└─────────────────────────────────────────────────────────────┘
```

- **`Session` Node**:
  - `canonical_id`: `session_<timestamp>_<uuid>`
  - Properties: `title`, `created_at`, `updated_at`, `turn_count`, `active_task`
- **`Turn` Node**:
  - Properties: `role` (`user` / `model`), `content`, `token_cost`, `created_at`
  - Relationship: `(s:Session)-[:HAS_TURN]->(t:Turn)`
- **Session-to-Memory Lineage**:
  - Relationship: `(s:Session)-[:PRODUCED]->(m:Memory)`

### 2.2 CLI Surface Area
- `uv run banana chat`: Interactive terminal chat session with multi-turn memory.
- `uv run banana run "<prompt>" --session-id <id>`: Resume or append to an existing session.
- `uv run banana session list`: Rich table of all past sessions, turns, and produced decisions.
- `uv run banana session show <id>`: Inspect the complete conversation and graph audit trail of a session.

---

## 3. Pillar 2: Background Maintenance & Graph Cleanup

### 3.1 Memory Compaction & Pruning
As an agent runs across dozens of sessions, `Memory` nodes accumulate `[:SUPERSEDES]` chains:
`M_3 -[:SUPERSEDES]-> M_2 -[:SUPERSEDES]-> M_1`
- **Problem**: Querying long superseding chains introduces latency and bloat.
- **Solution**: A compaction job that flattens replacement lineages, archiving or pruning memories superseded beyond $K$ generations.

### 3.2 Graph Vacuuming
- Purge orphaned health checks or transient calculation nodes.
- Clean up disconnected intermediate nodes from interrupted runs.

### 3.3 Agent Autonomous Maintenance Tool
- `consolidate_memory`: An explicit tool given to the agent so it can autonomously retire obsolete hypotheses when new market evidence invalidates them.

### 3.4 Scheduled Background Runner
- A periodic daemon or cron schedule (`banana clean --daemon` or schedule job) that runs `prune_superseded_memories()` and `vacuum_orphans()` in the background every $N$ hours.

---

## 4. Deliverables Checklist for Iteration 2

- [ ] `src/banana/session.py`: `SessionManager` class with turn recording and session retrieval.
- [ ] `src/banana/cleanup.py`: `GraphMaintenance` class with memory pruning and orphan vacuuming.
- [ ] Agent tool: `consolidate_memory` added to `AgentTools`.
- [ ] Context Assembler update: includes recent session turns in context.
- [ ] CLI commands:
  - `banana session list`
  - `banana session show <id>`
  - `banana chat`
  - `banana clean [--dry-run]`
- [ ] Unit & Integration test suite for session resumption and compaction.
