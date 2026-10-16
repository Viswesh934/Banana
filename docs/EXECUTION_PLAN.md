# Banana: Detailed Phase-by-Phase Execution Plan

This execution plan maps out each phase, concrete files, test gates, and deliverables.

---

## Phase 1 — Environment and Project Foundation

### Objectives
- Initialize project with `uv`.
- Set up `pyproject.toml` with dependencies: `typer`, `rich`, `falkordb`, `pydantic`, `pydantic-settings`, `tiktoken`, `google-genai`, `pytest`, `pytest-asyncio`.
- Set up `docker-compose.yml` for FalkorDB (`falkordb/falkordb:latest` on port 6379).
- Create package structure under `src/banana/`.
- Implement `banana doctor` command verifying FalkorDB connectivity (read/write ping node), environment variables, and Gemini configuration.
- Write smoke tests for CLI, config, and FalkorDB connection.

### Verification Gate
- `uv run banana doctor` succeeds.
- `uv run pytest tests/test_smoke.py` passes.

---

## Phase 2 — Graph Foundation and Data Model

### Objectives
- Define Pydantic models for core entities: `Task`, `Company`, `Product`, `Competitor`, `Document`, `Memory`, `Tool`, `Policy`, `Evidence`.
- Create FalkorDB graph client wrapper supporting dual graphs (`banana_demand` and `banana_knowledge`).
- Implement canonical ID, salting/partitioning (`+1`, `+2` bucket scheme) separating logical identity from graph keys.
- Build deterministic seed dataset for Competitor Intelligence & Pricing Strategy (ApexCloud vs CloudScale, HyperStore, DataVanguard).
- Implement `banana inspect-graph` CLI command with Rich tree/table displays.
- Write unit tests for schema, seed data idempotency, and graph query integrity.

### Verification Gate
- `uv run banana inspect-graph` outputs demand and knowledge graph statistics.
- Seeding is 100% deterministic and repeatable.

---

## Phase 3 — Context Assembly and Load Shedding

### Objectives
- Implement Context Candidate Pipeline:
  1. Task requirement decomposition.
  2. Demand graph traversal for prerequisites and policies.
  3. Knowledge graph traversal for matching candidate nodes.
  4. Dependency subgraph expansion (e.g., Parent Document $\to$ Evidence).
  5. Priority ranking (Priority 0: Mandatory, 1: Tool Schemas, 2: Evidence, 3: Memories, 4: Background).
  6. Progressive Load Shedder: knapsack solver that preserves dependency subgraphs, never drops Priority 0/1, sheds lowest-priority clusters first.
- Support precise token counting with tokenizer (fallback to character/word estimation if offline).
- Assemble structured context payload with complete audit trails (included items, excluded items, reasons, preserved dependencies).
- Unit tests verifying load shedding at various strict budgets (e.g. 1000, 2000, 4000 tokens) without LLM.

### Verification Gate
- Context engine tests pass under constrained budgets.
- All required dependencies are preserved; mandatory policies are never shed.

---

## Phase 4 — Agent and Tool Execution

### Objectives
- Implement Agent Runner connecting Context Assembler with LLM.
- Implement Gemini client via `google-genai` with fallback to deterministic mock agent for offline/demo reliability.
- Implement structured graph-backed tools:
  - `search_knowledge_graph(query, entity_type)`
  - `retrieve_evidence(evidence_id)`
  - `compare_competitors(company_ids, feature_keys)`
  - `save_finding(title, finding, confidence, tags)`
- Implement the agent loop: Task $\to$ Context Assembly $\to$ Model Thought & Tool Execution $\to$ Observation $\to$ Grounded Answer.
- CLI command `banana run "<prompt>" --budget 4000`.

### Verification Gate
- User can run `banana run "Compare CloudScale and ApexCloud pricing"` and receive a verified, grounded response with tool execution traces.

---

## Phase 5 — Persistent Memory and Company Knowledge

### Objectives
- Implement persistent memory lifecycle in FalkorDB:
  - Nodes: `Memory`, `Decision`, `Finding`.
  - Edges: `SUPERSEDES`, `DERIVED_FROM`, `CONTRADICTS`.
- Cross-session retrieval: detect previously recorded decisions and update them when new evidence surfaces.
- Multi-hop company knowledge retrieval (connecting internal cost margins with external market prices).
- Multi-session integration test: Session 1 records a strategic finding; Session 2 queries pricing and incorporates Session 1 finding.

### Verification Gate
- Multi-session test passes verifying cross-session graph memory retention and conflict detection.

---

## Phase 6 — Benchmarking and Evaluation

### Objectives
- Implement Baseline A (Naive Truncation: fills raw context up to token limit, slicing tail).
- Implement Baseline B (Relevance-Only: ranks items independently by vector/relevance score, ignoring graph dependencies).
- Implement Banana Strategy (Graph-aware dependency preservation + progressive load shedding).
- Create a benchmark suite running all three against identical tasks and token constraints.
- Measure:
  - Dependency preservation rate (%)
  - Budget compliance rate (%)
  - Evidence coverage (%)
  - Latency (ms)
- CLI command `banana benchmark` with formatted Rich comparison table.

### Verification Gate
- `uv run banana benchmark` executes and demonstrates measurable graph-aware dependency preservation advantages over Baselines A and B.

---

## Phase 7 — Demo Polish and Submission

### Objectives
- Implement `banana demo` command: step-by-step interactive walkthrough with Rich animations, diagrams, and explanations.
- Polish terminal outputs with banners, color coding, and clean tables.
- Write end-to-end documentation: `README.md`, setup instructions, architecture diagram, benchmark analysis.
- Validate complete CLI suite:
  - `banana doctor`
  - `banana inspect-graph`
  - `banana run "..."`
  - `banana demo`
  - `banana benchmark`
