# Banana: Iteration 2 Plan — Streamlit UI, Max-Flow Scheduling, FalkorDB Cloud & Sandboxing

## 1. Executive Summary & Architectural Vision

In **Iteration 2**, Banana evolves into an interactive, visually stunning AI agent platform deployed via **Streamlit** and powered by **FalkorDB Cloud**, featuring:

1. **Algorithmic Core**: **Ford-Fulkerson & Edmonds-Karp (Maximum Flow)** network algorithms for dependency-constrained context scheduling.
2. **Interactive UI**: **Streamlit Web Dashboard** featuring a dynamic token budget slider, live execution traces, and an embedded **Interactive HTML Force-Directed Graph Visualizer**.
3. **FalkorDB Cloud Readiness**: Built-in support for cloud-hosted FalkorDB instances with SSL/TLS and authentication.
4. **Ephemeral Sandboxing**: Lightweight micro-graphs (`banana_scratch_<session_id>`) for speculative reasoning, pricing scenario simulations, and policy verification before permanent memory commits.
5. **Hybrid Search & Knowledge Retrieval**: Combining full-text matching with Cypher multi-hop graph expansion.

---

## 2. Deep Dive: Ford-Fulkerson & Edmonds-Karp (Max-Flow) Context Scheduling

### The Mathematical Problem
Standard LLM context selection is usually treated as a flat 0/1 Knapsack, which fails to account for structural bottlenecks:
- An evidence chunk $E$ requires parent document $D$.
- Policy $P$ must govern both $E$ and $D$.
- Token capacity is a bottleneck constraint at the sink.

### The Network Flow Formulation:
```
           ┌──────────────┐     capacity = utility(R1)      ┌──────────────────┐
           │ Requirement 1├────────────────────────────────►│ Evidence 1 (E1)  │──┐
      ┌───►│              │                                 └────────┬─────────┘  │
      │    └──────────────┘                                          │            │
      │                                             Prerequisite Dep │ (Tokens)   │
┌─────┴──┐                                                           ▼            │
│ Source │                                                  ┌──────────────────┐  │ capacity = Token Budget
│  (S)   │                                                  │  Document 1 (D1) │──┼────────────────────────►┌──────┐
└─────┬──┘                                                  └──────────────────┘  │                         │ Sink │
      │    ┌──────────────┐     capacity = utility(R2)      ┌──────────────────┐  │                         │ (T)  │
      └───►│ Requirement 2├────────────────────────────────►│ Policy Floor (P1)│──┘                         └──────┘
           │ (Mandatory)  │                                 └──────────────────┘
           └──────────────┘
```

1. **Source ($S$) to Requirements**: Edges carry capacities equal to requirement priority and utility weights. Mandatory policies receive infinite/max capacity.
2. **Requirements to Candidate Clusters**: Edges route demand flow to candidate evidence and tools.
3. **Dependency Edges**: If node $A$ depends on node $B$, flow through $A$ is bounded by the capacity of prerequisite $B$.
4. **Candidates to Sink ($T$)**: The capacity of each candidate edge is its token cost. The total flow into $T$ is bounded by the **Configured Token Budget**.
5. **Edmonds-Karp Algorithm**: Uses BFS to find shortest augmenting paths in $O(V \cdot E^2)$ time, maximizing context signal throughput while strictly respecting budget bottlenecks and preserving dependency chains.

---

## 3. UI: Streamlit Dashboard + Interactive HTML Graph

Instead of terminal-only output, Iteration 2 delivers a modern web application in `streamlit`:

- **Token Budget Slider**: Interactive slider (e.g. 500 to 8,000 tokens). Adjusting the slider instantly re-runs the Max-Flow scheduler and updates the graph in real-time.
- **Embedded Interactive HTML Graph (D3.js / Pyvis)**:
  - Visual force-directed dual graph.
  - Nodes selected by Max-Flow glow in **green**; shedded nodes are dimmed in **gray**; mandatory policies glow in **gold**.
  - Clicking on any node displays its title, canonical ID, priority, and source document provenance.
- **Execution Log & Agent Thought Trace**:
  - Live sandbox simulation results.
  - FalkorDB tool calls and audited pricing matrices.
  - Final grounded recommendation with verified evidence citations.

---

## 4. FalkorDB Cloud Support

Iteration 2 adds seamless configuration for **FalkorDB Cloud**:
- Environment variables:
  - `FALKORDB_URL`: Cloud connection URI (e.g., `falkor://user:password@cloud-instance.falkordb.cloud:6379`).
  - `FALKORDB_SSL`: Boolean flag for secure TLS connections.
- Automatic fallback: Connects to local Docker Compose if cloud credentials are not provided.

---

## 5. Ephemeral Sandboxing ("Thinking Graphs")

Before committing permanent changes to company knowledge:
1. Agent initializes an ephemeral graph: `db.select_graph(f"banana_scratch_{session_id}")`.
2. Clones relevant candidate subgraphs.
3. Simulates hypothetical market scenarios (e.g., *"What if CloudScale cuts prices by another 10%? What happens to ApexCloud's 25% gross margin floor?"*).
4. Runs Cypher queries inside the sandbox to verify policy compliance.
5. Emits the verified recommendation and drops the scratchpad graph (`scratch_graph.delete()`).

---

## 6. What We Are Ditching (Clean Scope)
- ❌ Ditching terminal-only ASCII art (Streamlit + Interactive HTML graph replaces it).
- ❌ Ditching distributed multi-agent framework bloat (keeps single coherent graph agent).
- ❌ Ditching heavy local vector databases (uses native FalkorDB search).

---

## 7. Iteration 2 Engineering Roadmap & Phases

- **Phase 8 — FalkorDB Cloud & Ephemeral Sandboxing**:
  - Support cloud connection URI and SSL/TLS.
  - Implement `SandboxManager` for micro-graphs.
- **Phase 9 — Ford-Fulkerson & Edmonds-Karp Scheduler**:
  - Build `MaxFlowScheduler` computing optimal context selection using augmenting paths.
  - Verify dependency preservation against edge capacities.
- **Phase 10 — Interactive HTML Graph Visualizer**:
  - Implement D3.js / Pyvis interactive graph generator (`banana_graph.html`).
  - Highlight selected vs shedded subgraphs.
- **Phase 11 — Streamlit Web Application**:
  - Build `app.py` for Streamlit.
  - Live budget slider, scenario simulator, and agent execution dashboard.
