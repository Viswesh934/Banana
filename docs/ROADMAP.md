# Banana — Implementation Roadmap

## Project Overview

**Banana is a graph-aware context orchestration agent.**

It uses FalkorDB to connect task requirements with available knowledge, preserve important dependencies, manage persistent memory, and assemble context under a strict token budget.

The flagship demo is a competitor intelligence and pricing strategy agent. The architecture should also support persistent agent memory and company-wide knowledge retrieval.

### Core objectives

1. Demonstrate graph-driven decisions and actions.
2. Demonstrate persistent memory across sessions.
3. Demonstrate retrieval across connected company knowledge.
4. Implement graph-aware context assembly and progressive load shedding.
5. Run everything through a terminal interface.

The three hackathon tracks should be supported by one coherent agent, not three separate implementations.

---

## Phase 1 — Environment and Project Foundation

### Goal

Create a reproducible development environment and verify that Banana can communicate with FalkorDB.

### Tasks

- Initialize a Python 3.12+ project using `uv`.
- Configure the project as an installable package named `banana`.
- Add Typer and Rich for the CLI.
- Add the official FalkorDB Python client.
- Add Pydantic for data validation.
- Add a tokenizer dependency.
- Add the Gemini SDK for later integration.
- Configure pytest.
- Create `.env.example` and `.gitignore`.
- Configure FalkorDB using Docker Compose or an external instance.
- Implement configuration validation and useful startup errors.
- Add a `doctor` command that checks connectivity and configuration.
- Verify that the application can write and read a test node in FalkorDB.

### Deliverables

- Working Python environment.
- FalkorDB connectivity.
- Basic package structure.
- Passing smoke tests.
- `uv run banana doctor`.

### Completion criteria

A fresh environment can start Banana and verify its database connection without manual source-code modifications.

Do not implement the full graph algorithm or load-shedding logic in this phase.

---

## Phase 2 — Graph Foundation and Data Model

### Goal

Represent task requirements and available knowledge as two connected logical graph structures.

### Tasks

Define the core entities:

- `Task`
- `Company`
- `Product`
- `Competitor`
- `Document`
- `Memory`
- `Tool`
- `Policy`
- `Evidence`

Every context item should have a stable canonical ID, type, content reference, provenance, priority, and estimated token cost.

Create two logical graphs:

**Demand graph**

Represents what a task needs: required facts, capabilities, tools, policies, and dependencies.

**Knowledge graph**

Represents what Banana knows: companies, products, documents, prior decisions, evidence, and their relationships.

Use FalkorDB to store and traverse actual relationships. Keep the graph names configurable.

Implement a deterministic seed dataset for the competitor-intelligence demo.

### Salting and partitioning

- Establish the intended meaning of the `+1`, `+2` scheme.
- Separate canonical identity from salted storage keys.
- Implement deterministic bucket assignment only if appropriate for the intended scheme.
- Ensure cross-graph matching remains correct regardless of bucket assignment.

Do not implement distributed sharding prematurely. The initial version only needs to demonstrate the partitioning concept correctly.

### Deliverables

- FalkorDB graph initialization.
- Data models and relationships.
- Seed-data loader.
- Graph inspection command.
- Tests for identity, relationships, and repeatable seeding.

### Completion criteria

Banana can load the demo dataset and retrieve graph relationships relevant to a task.

---

## Phase 3 — Context Assembly and Load Shedding

### Goal

Build the core differentiating technology: select the most useful context that fits the model's token budget without losing critical dependencies.

### Tasks

Implement a context candidate pipeline:

1. Parse the task into requirements.
2. Traverse the demand graph to identify required information.
3. Query the knowledge graph for matching candidates.
4. Expand required dependencies.
5. Remove or consolidate redundant candidates where safe.
6. Rank candidates by relevance, utility, freshness, and token cost.
7. Apply progressive load shedding when the budget is exceeded.
8. Compile the final context.
9. Validate the final token count before invoking the model.

Implement explicit priority classes:

- Mandatory instructions and security policies.
- Required tool schemas and dependencies.
- High-value task evidence.
- Supporting memories and documents.
- Optional background context.

Mandatory items must not be silently discarded. If mandatory context exceeds the budget, return an explicit error or request a larger budget.

Account for system instructions, tool schemas, and output-token reservations. Use the target model's tokenizer where available.

### Required output

Every assembly operation should return:

- Selected context items.
- Excluded context items.
- Token count per item.
- Total assembled token count.
- Reasons for inclusion or exclusion.
- Preserved dependencies.
- Items that could not fit.
- Assembly latency.

### Deliverables

A deterministic context engine that works without an LLM.

### Completion criteria

The assembled context respects the configured budget whenever a feasible solution exists, and required dependencies are preserved.

---

## Phase 4 — Agent and Tool Execution

### Goal

Connect the context engine to a functioning terminal agent.

### Tasks

- Integrate the configured Gemini model.
- Implement an agent runner that sends all model requests through the context assembler.
- Implement structured tool definitions.
- Add a small number of useful tools:
  - Search the seeded knowledge graph.
  - Retrieve source documents or evidence.
  - Compare competitor products and pricing.
  - Save findings and decisions to persistent memory.
- Validate tool inputs and outputs.
- Handle API errors, missing credentials, and unavailable services.
- Prevent untrusted retrieved content from overriding system instructions.
- Save useful findings with provenance and timestamps.

Keep the initial agent loop simple. Avoid building a general-purpose multi-agent framework.

### Deliverables

- Working terminal agent.
- Model integration.
- Graph-backed tool execution.
- Persistent memory updates.

### Completion criteria

A user can submit a business question, watch Banana retrieve relevant context, execute tools, and receive a grounded answer.

---

## Phase 5 — Persistent Memory and Company Knowledge

### Goal

Demonstrate the second and third hackathon tracks through the same graph and context engine.

### Persistent memory

- Store previous findings, decisions, and unresolved questions.
- Retrieve relevant information in later sessions.
- Track provenance and timestamps.
- Prefer newer evidence when appropriate.
- Identify conflicting or superseded information rather than silently merging it.

### Company knowledge

- Represent company products, strategies, customers, documents, and decisions.
- Connect internal context to competitor intelligence.
- Allow the agent to answer questions that require multiple connected sources.
- Preserve important dependencies during context assembly.

Use a small, deterministic synthetic company dataset for the demo. Do not depend on external enterprise integrations.

### Deliverables

- Cross-session memory.
- Connected company knowledge.
- Multi-hop graph retrieval.
- Demonstration of prior findings influencing a new task.

### Completion criteria

A decision saved in one session can meaningfully influence a related task in a later session.

---

## Phase 6 — Benchmarking and Evaluation

### Goal

Demonstrate that graph-aware context assembly offers a measurable benefit over simpler alternatives.

### Implement three selection strategies

1. **Baseline A — Naive truncation:** truncate or remove context without understanding dependencies.
2. **Baseline B — Relevance-only selection:** rank context items independently and select by score and token cost.
3. **Banana — Graph-aware assembly:** use graph relationships, dependency preservation, and progressive load shedding.

Run all three against the same seeded tasks, context candidates, and token budgets.

### Measure

- Task success and answer correctness.
- Final input-token count.
- Budget violations.
- Required dependency preservation.
- Evidence coverage.
- Assembly latency.
- Number of graph traversals.
- Model calls and token consumption.

Keep the evaluation dataset and scoring rules identical across strategies. Record actual results; do not hardcode performance claims.

### Deliverables

- Reproducible benchmark command.
- Summary table in the terminal.
- Example of a task where graph-aware selection retains necessary context that an independent ranking or naive truncation misses.

### Completion criteria

The demo shows exactly where graph-aware assembly helps, where it adds overhead, and what its limitations are.

---

## Phase 7 — Demo Polish and Submission

### Goal

Create a polished, reliable terminal demonstration.

### Required CLI

```bash
uv run banana doctor

uv run banana demo

uv run banana run "Analyze competitor pricing" --budget 4000

uv run banana inspect-graph

uv run banana benchmark
```

### Demo scenario

Ask Banana to compare three competitors, identify pricing and feature gaps, and recommend a pricing strategy using prior research and internal company objectives.

The terminal should display:

1. The incoming task.
2. The demand graph's requirements.
3. Relevant knowledge graph relationships.
4. Context candidates and token costs.
5. Load-shedding decisions.
6. The final assembled token budget.
7. Tool calls and evidence used.
8. The final recommendation.
9. A benchmark comparison against the baselines.

Provide a deterministic demo mode so the presentation remains useful even if the model API is unavailable.

### Final deliverables

- Reproducible setup instructions.
- Working CLI.
- FalkorDB integration.
- Dual-graph context engine.
- Persistent memory.
- Load-shedding implementation.
- Benchmark results.
- Clear limitations and architecture documentation.

---

## Implementation Rules

- Keep the terminal as the primary interface.
- Use FalkorDB for actual graph operations, not merely storage or visualization.
- Keep the context algorithm testable independently of the model provider.
- Avoid unnecessary infrastructure and dependencies.
- Implement in small, runnable increments.
- Use synthetic data for repeatable demonstrations.
- Never claim benchmark improvements without measured evidence.
- Ask for clarification only when an unresolved decision materially changes the design.
- At each phase, leave the repository runnable and document what works.

## Priority Order

If time becomes limited, prioritize:

1. Environment and FalkorDB connectivity.
2. Two working graphs and seeded data.
3. Context selection and load shedding.
4. One live model-backed agent workflow.
5. A convincing competitor-intelligence demo.
6. Persistent memory and company knowledge.
7. Benchmarking and polish.

The primary success criterion is a working agent whose graph-aware context assembly makes a visible, measurable difference.

---

## Iteration Progress & Future Roadmap

- **Iteration 1 (Complete — Commit `e58fb45`):** Dual-graph Cypher foundation, greedy knapsack context assembler, Gemini 3.5 Flash integration, persistent cross-session memory with `[:SUPERSEDES]`, and scientific benchmark suite.
- **Iteration 2 (Complete — Commit `2618e36`):** Edmonds-Karp Maximum Flow context scheduler, ephemeral FalkorDB "thinking" sandboxes, D3.js force-directed Visual Brain, executive Streamlit web dashboard (`app.py`), and FalkorDB Cloud support.
- **Iteration 3 (Complete — Commit `bca5943`):** Model Context Protocol (MCP) server for Claude Code, Cursor, Windsurf, and Antigravity; Multimodal Vision ingestion pipeline (`src/banana/multimodal.py`); multi-turn conversational memory; and 1-click board briefing memo export. (27/27 tests passing).
- **Iteration 4 (Planned — Next Session):** **"Floating Banana" Desktop Demo & Meeting Graph Architecture**:
  - Live FalkorDB Meeting Subgraph construction (`:Speaker`, `:Topic`, `:Commitment`, `:Proposal`, `:ReferencedTab`).
  - Zero-token idle floating HUD with hotkey (`Alt+Space`) and safe-word triggers.
  - Exact tab memory and 1-click deep-link restore.
  - Post-meeting graph-powered conversational dialogue with retention TTL.
