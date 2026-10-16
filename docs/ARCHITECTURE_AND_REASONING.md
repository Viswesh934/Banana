# Banana: Architecture, Core Concept, and Strategic Reasoning

## 1. Executive Summary

**Banana** is a graph-aware context orchestration agent powered by **FalkorDB**.

Instead of treating context as an unorganized bucket of text chunks or relying solely on flat vector embeddings, Banana treats context assembly as a **graph-matching problem under a constrained token budget (a knapsack problem with structural dependency constraints)**.

```
       TASK / USER PROMPT
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
   │  (What the agent knows│     Documents, Past Decisions, Persistent Memories
   └───────────┬───────────┘
               │
               ▼
   ┌────────────────────────────────────────────────────────┐
   │ GRAPH-AWARE CONTEXT ASSEMBLER & LOAD SHEDDER           │
   │ 1. Priority Classes (Mandatory -> Supporting)          │
   │ 2. Subgraph Dependency Preservation                    │
   │ 3. Progressive Load Shedding under Token Budget        │
   │ 4. Deterministic Explainability (Inclusion/Exclusion)  │
   └───────────┬────────────────────────────────────────────┘
               │
               ▼
     OPTIMAL CONTEXT PROMPT  ──►  GEMINI / LLM / DETERMINISTIC AGENT
               │
               ▼
   TOOL EXECUTION & PERSISTENT MEMORY UPDATE (FalkorDB)
```

---

## 2. Why Existing LLM Context Strategies Fail

| Paradigm | How it works | Critical Failure Mode |
| :--- | :--- | :--- |
| **Naive Truncation (Baseline A)** | Fill context window until token limit is hit; truncate the rest. | Arbitrarily severs critical context mid-document, drops policies, or discards crucial dependencies. |
| **Top-K Vector RAG (Baseline B)** | Embed chunks, calculate cosine similarity to query, select top $K$ chunks. | Suffers from semantic myopia: selects conclusion chunks without prerequisite definitions, drops context dependencies, mixes stale with fresh data. |
| **Massive Context Dump** | Feed 1M tokens into frontier models. | Expensive, high latency, degrades retrieval accuracy ("needle-in-a-haystack" degradation), prone to hallucination on contradictory facts. |
| **Banana (Graph-Aware Context Assembly)** | Explicit demand graph meets knowledge graph in FalkorDB; preserves dependency subgraphs; sheds optional context progressively. | Fits strict token budgets, guarantees mandatory policies and required schemas are never shed, and guarantees evidence is never isolated from its prerequisites. |

---

## 3. The Dual-Graph Paradigm in FalkorDB

Banana models the context problem with two explicit, queryable logical graphs in FalkorDB:

### 3.1 The Demand Graph (Task Needs)
Represents the structural requirements of the task:
- **`Task`**: The objective and constraints.
- **`Requirement`**: Specific facts or dimensions needed (e.g., "Competitor pricing tiers", "Margin thresholds", "SLA guarantees").
- **`Policy`**: Non-negotiable operational or security constraints (e.g., "Do not violate non-disclosure agreements", "Require source attribution").
- **`ToolSchema`**: Schemas of tools the agent may invoke to fulfill requirements.
- **`Dependency` edges**: `(ReqA)-[:DEPENDS_ON]->(ReqB)` (e.g., evaluating feature parity depends on product tier definitions).

### 3.2 The Knowledge Graph (Company & Market Knowledge)
Represents the persistent universe known to the enterprise:
- **`Company`**: Our company and competitor entities.
- **`Product`**: Offerings, feature sets, packaging.
- **`Document` / `Evidence`**: Sourced quotes, pricing sheets, whitepapers, earnings calls.
- **`Memory` / `Decision`**: Past executive decisions, prior agent findings, hypotheses, and feedback.
- **Relationships**: `(Product)-[:OFFERED_BY]->(Company)`, `(Decision)-[:SUPERSEDES]->(Decision)`, `(Evidence)-[:SUPPORTS]->(Finding)`, `(Finding)-[:DERIVED_FROM]->(Evidence)`.

---

## 4. Priority Classes and Progressive Load Shedding

Context items are categorized into explicit priority tiers:

1. **Priority 0 (Mandatory - System & Security)**:
   - System instructions, active security policies, output schema constraints.
   - *Rule*: Never shed. If $Tokens(P_0) > Budget$, fail immediately with `BudgetExceededError`.
2. **Priority 1 (Required Tool Schemas & Direct Dependencies)**:
   - Tools required to fulfill active task requirements and their mandatory schema definitions.
3. **Priority 2 (High-Value Grounding Evidence)**:
   - Directly matched evidence nodes in the Knowledge Graph with high confidence and verified provenance.
4. **Priority 3 (Supporting Memories & Historical Context)**:
   - Cross-session memories, past decisions, internal company context.
5. **Priority 4 (Optional Background Context)**:
   - General market summaries, peripheral entity relationships, extended documentation.

### Progressive Load Shedding Algorithm
When candidates exceed the token budget:
1. Preserve all Priority 0 and 1 items.
2. Group candidates into dependency clusters (e.g., Evidence $E_1$ and its prerequisite Document $D_1$).
3. Progressively shed lowest-priority clusters first (Priority 4 $\to$ Priority 3 $\to$ Priority 2).
4. If an entire cluster cannot fit, evaluate whether a summary or leaf node can be shed without breaking required root dependencies.
5. Return complete auditability: every token included or excluded has an explicit recorded reason.

---

## 5. Persistent Cross-Session Memory

A key requirement is that Banana is not a stateless chatbot.
- Findings and decisions from Session 1 are committed to FalkorDB as `Memory` and `Decision` nodes.
- When Session 2 runs (even hours or days later), the Demand Graph identifies that previous decisions exist for the target company/product.
- The context engine traverses `(m2:Memory)-[:SUPERSEDES]->(m1:Memory)` to identify when previous assumptions are outdated, preventing the agent from relying on stale data while preserving audit trails.

---

## 6. Flagship Demo: Competitor Intelligence & Pricing Strategy

The concrete showcase scenario:
- **Our Company**: *ApexCloud* (high-performance vector/graph infrastructure).
- **Competitors**: *CloudScale*, *HyperStore*, *DataVanguard*.
- **Task**: `"Analyze competitor pricing changes, evaluate feature gaps against our Enterprise tier, and recommend an adjusted pricing strategy adhering to our margin policy."`
- **Why this proves the architecture**:
  - Requires company knowledge (internal margin policies, cost structures).
  - Requires competitor intelligence (tiers, hidden fees, recent changes).
  - Requires cross-session memory (a previous finding on CloudScale's discount patterns).
  - Requires strict token management (fitting detailed pricing tables, policies, and schemas into 4,000 tokens).

---

## 7. Benchmarking and Verification Strategy

To scientifically validate Banana, we compare three strategies across identical tasks, candidates, and budgets:
1. **Baseline A (Naive Truncation)**
2. **Baseline B (Relevance-Only Top-K)**
3. **Banana (Graph-Aware Assembly)**

### Measured Metrics:
- **Dependency Preservation Rate**: % of selected evidence items whose prerequisite definitions were also preserved.
- **Budget Compliance**: % of runs strictly within token budget without overflow.
- **Evidence Signal-to-Noise Ratio**: Tokens of relevant evidence vs filler.
- **Task Success / Groundedness**: Model answer accuracy evaluated against ground truth.
- **Assembly Latency**: Graph traversal and knapsack resolution overhead.

---

## 8. CLI Surface Area

The terminal interface will provide:
```bash
uv run banana doctor         # Verifies FalkorDB, environment, model credentials
uv run banana inspect-graph  # Visualizes Demand & Knowledge graphs in rich terminal tables
uv run banana demo           # Full interactive walkthrough of competitor intelligence
uv run banana run "<prompt>" # Runs agent with customizable token budget
uv run banana benchmark      # Head-to-head comparison against Baseline A & B
```
