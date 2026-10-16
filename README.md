# Banana 🍌

**Graph-Aware Context Orchestration Agent powered by FalkorDB**

Banana connects task requirements with enterprise and market knowledge, preserves critical dependency subgraphs, manages persistent cross-session memory, and assembles high-signal context under strict token budgets using progressive load shedding.

---

## The Core Innovation

Standard LLM agents rely on flat top-$K$ vector search or brute-force context dumping:
- **Vector RAG Flaw**: Selects an evidence chunk or pricing table without its prerequisite definitions or security policies, causing hallucination or policy violations.
- **Context Bloat Flaw**: Dumping 100k+ tokens causes attention decay ("needle-in-a-haystack" loss) and high latency.

**Banana solves this by modeling context assembly as a graph-matching problem under a constrained token knapsack**:

```
       TASK / USER DIRECTIVE
               │
               ▼
   ┌───────────────────────┐
   │     DEMAND GRAPH      │ ◄── Task Requirements, Policies, Tool Schemas,
   │  (What the task needs)│     Prerequisite Entities, Expected Evidence
   └───────────┬───────────┘
               │ Cross-Graph Matching & Dependency Expansion
               ▼
   ┌───────────────────────┐
   │    KNOWLEDGE GRAPH    │ ◄── Companies, Products, Metrics, Evidence,
   │ (What the agent knows)│     Documents, Past Decisions, Persistent Memories
   └───────────┬───────────┘
               │
               ▼
   ┌────────────────────────────────────────────────────────┐
   │ GRAPH-AWARE CONTEXT ASSEMBLER & LOAD SHEDDER           │
   │ • Priority Classes (P0: Mandatory ──► P4: Background)  │
   │ • Subgraph Dependency Preservation (no orphaned chunks)│
   │ • Progressive Load Shedding under strict token budget  │
   │ • Deterministic Explainability (Audit Trail)           │
   └───────────┬────────────────────────────────────────────┘
               │
               ▼
     OPTIMAL CONTEXT PROMPT  ──►  GEMINI / LLM INFERENCE
               │
               ▼
   TOOL EXECUTION & PERSISTENT MEMORY UPDATE (FalkorDB)
```

---

## Quickstart

### 1. Prerequisites
- Python 3.12+
- Docker & Docker Compose
- [uv](https://astral.sh/uv)

### 2. Start FalkorDB
```bash
docker compose up -d
```

### 3. Verify Health & Environment
```bash
uv run banana doctor
```

### 4. Launch Interactive Streamlit Web Dashboard
```bash
uv run banana ui
# or: streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) to interact with:
- **Token Budget Slider**: Dynamically adjusts context size and triggers real-time load shedding.
- **Embedded D3.js Force-Directed Graph**: Visualizes dual-graph topology, glowing retained nodes vs dimmed shedded nodes.
- **Edmonds-Karp Max-Flow Diagnostics**: Inspects augmenting paths, bottleneck edges, and throughput.
- **Scenario Sandbox Simulator**: Tests pricing cuts and margin floors inside ephemeral FalkorDB scratchpad graphs.

### 5. Interactive Terminal Demo Walkthrough
```bash
uv run banana demo --budget 1600
```

### 6. Inspect FalkorDB Dual Graphs
```bash
uv run banana inspect-graph
```

### 7. Run Agent on Custom Tasks
```bash
uv run banana run "Analyze competitor pricing and recommend packaging strategy" --budget 4000
```

### 8. Run Head-to-Head Scientific Benchmark
```bash
uv run banana benchmark
```

---

## Measured Benchmark Results

Head-to-head comparison against **Baseline A (Naive Truncation)** and **Baseline B (Relevance-Only Top-K)** across identical tasks and budgets:

| Strategy | Budget | Assembled Tokens | Policy Preserved | Dependencies Preserved | Evidence Coverage | Assembly Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline A (Naive Truncation)** | 1,100 | 890 | 25.0% | 100.0% | 83.3% | ~4ms |
| **Baseline B (Relevance Top-K)** | 1,100 | 886 | 100.0% | 75.0% | 50.0% | ~0.2ms |
| **Banana (Graph-Aware Knapsack)** | **1,100** | **698** | **100.0%** | **100.0%** | **50.0%** | **~5ms** |
| Baseline A (Naive Truncation) | 1,600 | 1,285 | 87.5% | 100.0% | 100.0% | ~4ms |
| Baseline B (Relevance Top-K) | 1,600 | 1,298 | 100.0% | 75.0% | 83.3% | ~0.2ms |
| **Banana (Graph-Aware Knapsack)** | **1,600** | **1,030** | **100.0%** | **100.0%** | **83.3%** | **~5ms** |

### Key Findings:
- Under tight token constraints, **Baseline A** drops up to 75% of mandatory security & margin governance policies due to arbitrary tail truncation.
- **Baseline B** drops up to 25% of prerequisite dependency edges, including factual claims without their underlying source document or definitions.
- **Banana** guarantees **100% Policy Preservation** and **100% Subgraph Dependency Integrity** with sub-6ms traversal overhead.

---

## Running the Automated Test Suite

```bash
uv run pytest -v
```

---

## Documentation
- [Implementation Roadmap](docs/ROADMAP.md)
- [Architecture & Strategic Reasoning](docs/ARCHITECTURE_AND_REASONING.md)
- [Phase Execution Plan](docs/EXECUTION_PLAN.md)
