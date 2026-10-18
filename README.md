<div align="center">

# 🍌 Banana

### FalkorDB-Powered Graph Memory & Context Brain for AI Coding Agents

**🏆 FalkorDB Hackathon Submission: Track 01 — Agents That Act on Connected Data**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Graph Engine](https://img.shields.io/badge/Graph_Engine-FalkorDB-red.svg?style=flat-square&logo=redis&logoColor=white)](https://falkordb.com)
[![Track 01](https://img.shields.io/badge/Hackathon_Track-01:_Agents_That_Act_on_Connected_Data-orange.svg?style=flat-square)](https://falkordb.com)
[![MCP Compatible](https://img.shields.io/badge/MCP-Claude_Code_|_Cursor_|_Windsurf-9cf.svg?style=flat-square&logo=anthropic&logoColor=white)](https://modelcontextprotocol.io)
[![Tests](https://img.shields.io/badge/pytest-39%20passed-brightgreen.svg?style=flat-square&logo=pytest&logoColor=white)](https://pytest.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

*Banana supercharges your existing coding agent (**Cursor**, **Claude Code**, **Windsurf**, or **VS Code**) with photographic cross-session memory, codebase AST dependency graphs, and deterministic policy guardrails powered by **FalkorDB**'s ultra-low latency graph engine.*

---

[How It Works](#-how-it-works-with-your-coding-agent) •
[FalkorDB Engine](#-powered-by-falkordb) •
[Live Deployment](#-live-serverless-deployment) •
[Graph Model & Cypher](#-graph-data-model--cypher-architecture) •
[Quickstart](#-quickstart-for-cursor--claude-code) •
[Capabilities](#-core-capabilities) •
[CLI Reference](#-cli-command-reference)

</div>

---

## ⚡ Why Your Coding Agent Needs Banana

AI coding assistants (Claude Code, Cursor, Copilot) write syntax quickly, but suffer from three fundamental limitations:
1. **Architectural Amnesia:** Every session starts from scratch. The agent forgets why decisions were made, reverts past refactors, or violates conventions (e.g. using deprecated `.dict()` instead of `.model_dump()`).
2. **Context Window Blindness:** Grepping or dumping 30+ files burns tokens and triggers attention loss without understanding how classes, methods, and modules actually connect.
3. **Missing Guardrails:** Coding agents frequently break Clean Architecture boundaries (e.g. importing low-level database drivers into UI views) or accidentally leak credentials.

### **The Banana Solution**
Banana connects your coding agent to **FalkorDB**'s high-performance graph engine:

```mermaid
flowchart LR
    subgraph CodingAgent ["💻 Your Coding Agent (Cursor / Claude Code / Windsurf / CLI)"]
        Agent["🤖 Coding Assistant\n(Uses its own built-in LLM subscription)"]
    end

    subgraph BananaBrain ["🍌 Banana Graph Engine (MCP / CLI)"]
        AST["AST Code Indexer\n(39 Files, 42 Classes, 83 Functions, 127 Imports)"]
        Knapsack["Graph Knapsack Assembler\n(Edmonds-Karp Max-Flow)"]
        Guardrails["Architecture & Security Guardrails\n(Clean Architecture & OWASP Credentials)"]
        Memory["Persistent Memory Manager\n(Decision Lineage with [:SUPERSEDES])"]
    end

    subgraph Falkor ["🧠 FalkorDB Graph Engine"]
        DemandGraph[("banana_demand\nRules, Invariants & Constraints")]
        CodeGraph[("banana_knowledge\nAST Dependency Graph & Memory Nodes")]
    end

    Agent <-->|1. 'Banana, give me optimal context for this symbol'| Knapsack
    Agent <-->|2. 'Banana, check if this change violates architecture/secrets'| Guardrails
    Agent <-->|3. 'Banana, record this architectural decision'| Memory
    
    AST --> CodeGraph
    Knapsack <--> DemandGraph & CodeGraph
    Guardrails <--> DemandGraph
    Memory <--> CodeGraph
```

---

## 🧠 Powered by FalkorDB

Banana relies on **FalkorDB** as its core graph engine:
- **Sub-Millisecond Traversal:** Leverages GraphBLAS sparse matrices to execute deep Cypher traversals in under 3ms.
- **Dual-Graph Architecture:**
  - `banana_demand`: Models task requirements, security constraints, and mandatory policies.
  - `banana_knowledge`: Stores codebase symbols (AST classes, functions, files), import graphs, and persistent memory nodes with `[:SUPERSEDES]` lineage.
- **Deployment Flexibility:**
  - **Local FalkorDB:** `docker run -d --name banana-falkordb -p 6379:6379 falkordb/falkordb:latest` (or `docker compose up -d`).
  - **FalkorDB Cloud:** Seamlessly connect via connection string in `.env`: `FALKORDB_URL=falkor://user:pass@host:port` (zero local Docker needed).

---

## 🌐 Live Serverless Deployment

Banana is deployed live on **AWS Lambda** in `ap-south-1` backed by **FalkorDB Cloud**:
- **Live Interactive Endpoint:** [https://ssrr3wg2ibyqkh6gph4ehlthay0ovdzp.lambda-url.ap-south-1.on.aws/](https://ssrr3wg2ibyqkh6gph4ehlthay0ovdzp.lambda-url.ap-south-1.on.aws/)
- **Live Latency:** **~2.5ms** read/write query latency against FalkorDB Cloud.
- **Interactive Web Tester:** Open the URL in any browser to execute live health checks, margin guardrails, and Cypher queries directly on AWS Lambda.

---

## 🗺️ Graph Data Model & Cypher Architecture

Banana implements a high-performance **dual-graph architecture** in FalkorDB:

```mermaid
graph TD
    subgraph DemandGraph ["banana_demand (Governance & Requirements)"]
        Task["(:Task {canonical_id, prompt})"]
        Policy["(:Policy {canonical_id, floor_pct: 0.25})"]
        Constraint["(:Constraint {max_tokens, boundary})"]
        
        Task -->|:REQUIRES| Policy
        Task -->|:CONSTRAINED_BY| Constraint
    end

    subgraph KnowledgeGraph ["banana_knowledge (Codebase AST & Memory)"]
        File["(:File {path, language})"]
        Class["(:Class {name, methods})"]
        Func["(:Function {name, signature})"]
        Mem["(:Memory {canonical_id, decision, provenance})"]
        OldMem["(:Memory {canonical_id, deprecated_decision})"]
        
        File -->|:DEFINES| Class
        File -->|:DEFINES| Func
        File -->|:IMPORTS| File
        Mem -->|:SUPERSEDES| OldMem
    end

    Policy -.->|:ENFORCES_ON| File
    Task -.->|:ASSEMBLES_FROM| KnowledgeGraph
```

### ⚡ Key Graph Algorithms & Cypher Queries

1. **Edmonds-Karp Max-Flow Knapsack (`MaxFlowScheduler`):**
   Treats prerequisite code symbols and policies as directed capacitated networks. Assembles the highest-utility context under strict token budgets (e.g. 1500 tokens) while mathematically guaranteeing **100% prerequisite preservation**.

2. **AST Dependency Linking (Cypher):**
   ```cypher
   MATCH (src:ContextNode {canonical_id: $src}), (tgt:ContextNode {canonical_id: $tgt})
   MERGE (src)-[r:IMPORTS]->(tgt)
   RETURN type(r)
   ```

3. **High-Signal Symbol Retrieval Under Knapsack Budget (Cypher):**
   ```cypher
   MATCH (n:ContextNode)
   WHERE (n.entity_type IN ['Class', 'Function', 'File'])
     AND (n.canonical_id CONTAINS $kw OR n.title CONTAINS $kw)
   RETURN n.canonical_id, n.title, n.content, n.entity_type, n.token_cost
   LIMIT 25
   ```

4. **Cross-Session Photographic Memory Lineage (Cypher):**
   ```cypher
   MATCH (m:ContextNode)
   WHERE m.entity_type = 'Memory' OR 'Memory' IN labels(m)
   OPTIONAL MATCH (m)-[:SUPERSEDES]->(old_m)
   RETURN m.canonical_id, m.title, m.content, old_m.canonical_id
   ORDER BY m.created_at DESC
   LIMIT 20
   ```

---

## 🚀 Quickstart for Cursor & Claude Code

### 1. Connect with Claude Code
```bash
claude mcp add banana -- uv run banana mcp
```

### 2. Connect with Cursor (`.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "banana": {
      "command": "uv",
      "args": ["run", "banana", "mcp"]
    }
  }
}
```

### 3. Verify Local Installation
```bash
uv run banana doctor
```

---

## 🌟 Core Capabilities

### 1. 🧠 Photographic Cross-Session Memory
- When your coding agent completes a refactor or architectural shift, it calls `banana_save_decision`:
  ```python
  banana_save_decision(
      title="Adopt Pydantic v2 schemas",
      finding="Always use .model_dump() instead of .dict() across models",
      supersedes_id="pydantic_v1_decision"
  )
  ```
- In tomorrow's session, the agent queries `banana_query_decisions` and automatically abides by all past architectural agreements.

### 2. ⚡ High-Signal Code Context Knapsack
- Instead of dumping entire files into context, the agent calls `banana_assemble_code_context(query="auth", token_budget=1500)`.
- Banana traverses the codebase AST graph and returns only the prerequisite class interfaces, function signatures, and docstrings under a strict token budget knapsack.

### 3. 🛑 Deterministic Architecture & Security Guardrails
- **Clean Architecture Layer Isolation:** Intercepts presentation layers (`views/app.py`, `ui/*`) directly importing low-level database engines.
- **OWASP Credential Leak Prevention:** Scans generated code for hardcoded AWS access keys (`AKIA...`), private keys, or unsafe `eval()`/`exec()` primitives.
- **Sub-Millisecond Speed:** All rule evaluations run deterministically in Python in **< 1ms without burning a single LLM token**.

### 4. 📁 Local AST Codebase Indexing
- Scans and maps your repository structure into graph nodes:
  - `(:File)-[:IMPORTS]->(:File)`
  - `(:File)-[:DEFINES]->(:Class)`
  - `(:Class)-[:DEFINES]->(:Function)`
- Run via terminal or let your coding agent index on demand via `banana_index_codebase()`.

---

## 💻 CLI Command Reference

| Command | Description |
| :--- | :--- |
| `uv run banana chat [directive]` | **Interactive Graph-Aware Coding Agent** dialogue in terminal (e.g. `"tell me about this codebase"`). |
| `uv run banana guardrails check --file <src> --import <mod>` | Test Clean Architecture layer isolation boundaries (e.g. UI importing DB). |
| `uv run banana guardrails check --code "<code>"` | Scan code snippet for hardcoded AWS keys, private keys, or dangerous primitives. |
| `uv run banana mcp [--url <url>]` | Launch Model Context Protocol (MCP) server for Cursor / Claude Code (local or remote Lambda). |
| `uv run banana index [path]` | Scan and index local codebase AST (classes, functions, imports) into the repository graph. |
| `uv run banana code-context "<query>"` | Assemble high-signal code context (signatures, interfaces) under a token knapsack. |
| `uv run banana decision list` | View all persistent cross-session architectural decisions in memory. |
| `uv run banana decision save --title ... --finding ...` | Record a new architectural decision or lesson learned with `[:SUPERSEDES]` lineage. |
| `uv run banana doctor` | Verify system health, tokenizers, LLM availability, and FalkorDB connectivity. |

---

## 🧪 Testing

Run the automated test suite:
```bash
uv run pytest
```
```
============================== 39 passed in 57.4s ==============================
```
Covers coding agent tools, codebase AST indexing, architecture and security guardrails validation, embedded SQLite fallback, Edmonds-Karp load shedding, and cross-session decision persistence.

---

## 📄 License

MIT © 2026 Banana Project Contributors.
