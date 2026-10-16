# Banana: Iteration 3 Plan — MCP Server for Coding CLIs & Multimodal Ingestion

## 1. Executive Summary

In **Iteration 3**, Banana expands beyond a standalone application to become an **extensible graph orchestration layer** that other AI coding agents (Claude Code, Cursor, Windsurf, Antigravity, Aider) can inherit, alongside a **multimodal document and image ingestion pipeline**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FAMOUS CODING CLIs & AGENT ECOSYSTEM                     │
│       Claude Code  •  Cursor  •  Windsurf  •  Antigravity  •  Aider        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                      Model Context Protocol (MCP) / CLI SDK
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BANANA MCP SERVER & ORCHESTRATION LAYER                  │
│  • banana_orchestrate_context: Max-Flow context assembly under token budget │
│  • banana_query_knowledge: Multi-hop graph retrieval & dependency expansion │
│  • banana_simulate_sandbox: Ephemeral scenario testing                      │
│  • banana_persist_memory: Cross-session memory with SUPERSEDES lineage      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   MULTIMODAL DOCUMENT & IMAGE INGESTION                     │
│  • Upload: Invoices (PDF/CSV), Pricing Screenshots (PNG/JPG), Teardowns     │
│  • Vision Extraction: Gemini 3.5 Flash Multimodal Schema Parser              │
│  • FalkorDB Ingestion: Automatic (Document)->(Evidence)->(Product) creation  │
│  • Visual Brain: Uploaded assets instantly appear in the D3.js graph         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Pillar 1: Model Context Protocol (MCP) Server for Famous Coding CLIs

### 2.1 The Concept
Modern coding tools like **Claude Code**, **Cursor**, **Windsurf**, and **Google Antigravity** support the **Model Context Protocol (MCP)**. 

By adding an MCP server interface (`banana mcp`), developers can install Banana as a tool provider into their coding environment:
```bash
# In Claude Code / Cursor / Antigravity config:
claude mcp add banana -- uv run banana mcp
```

### 2.2 Tools Inherited by External Coding CLIs
1. **`orchestrate_context(prompt: str, token_budget: int)`**:
   - Takes the developer's coding task and token budget.
   - Runs Edmonds-Karp Max-Flow to assemble optimal, dependency-preserved context.
   - Returns high-signal context without token bloat.
2. **`query_graph_memory(query: str, entity_type: str = None)`**:
   - Allows coding agents to search persistent enterprise and architectural knowledge across sessions.
3. **`save_agent_decision(title: str, content: str, supersedes_id: str = None)`**:
   - Allows external agents to record architectural decisions and lessons learned directly into FalkorDB.
4. **`simulate_sandbox(scenario: dict)`**:
   - Spins up ephemeral FalkorDB micro-graphs to test code or architectural refactors before applying them.

---

## 3. Pillar 2: Multimodal Ingestion (Documents & Images)

### 3.1 Supported Ingestion Types
- **PDF Documents**: Sourced competitor contracts, SLAs, Whitepapers, COGS audits.
- **Images (PNG/JPEG)**: Screenshots of competitor pricing tables, discount emails, invoice screenshots.
- **Data (CSV/JSON)**: Raw pricing matrices and feature sheets.

### 3.2 Ingestion & Multimodal Graph Extraction Pipeline
1. **User Uploads Asset** via Streamlit UI (`st.file_uploader`) or CLI (`banana ingest <path>`).
2. **Gemini 3.5 Flash Multimodal Extraction**:
   - Analyzes the image or document text/tables.
   - Emits structured JSON schema:
     ```json
     {
       "company": "CloudScale",
       "product": "Enterprise Cloud",
       "advertised_price": 800.0,
       "egress_fee_per_gb": 0.08,
       "sla_pct": 99.9,
       "evidence_quotes": [
         "Section 4.1: $0.08 per GB egress overage fee applies to all outbound traffic."
       ]
     }
     ```
3. **FalkorDB Graph Insertion**:
   - Creates `(:Document)` node with file path and hash.
   - Creates `(:Evidence)` nodes with verbatim quotes.
   - Creates/Updates `(:Product)` and `(:Company)` relationships.
4. **Immediate Graph Feedback**:
   - The interactive D3.js Visual Brain instantly adds the new node with glowing edges connecting it to the enterprise knowledge base!

---

## 4. Pillar 3: Exportable Artifacts & Board Strategy Briefs

- **1-Click Executive PDF / Markdown Export**:
  - Compiles the final recommendation, competitor comparison tables, policy compliance audits, and evidence citations into a formatted executive briefing memo.

---

## 5. Iteration 3 Implementation Checklist

- [ ] Add `fastmcp` or `mcp` dependency for standard Model Context Protocol server.
- [ ] Implement `src/banana/mcp_server.py`: exposes tools for Claude Code, Cursor, Antigravity.
- [ ] Implement `src/banana/multimodal.py`: Gemini Vision parser for invoices, screenshots, PDFs.
- [ ] Update Streamlit UI (`app.py`):
  - Add "📁 Upload Invoices & Screenshots" drag-and-drop tab.
  - Show uploaded images and their extracted graph entities in real-time.
- [ ] Add CLI commands:
  - `banana mcp`: Starts the MCP server on stdio.
  - `banana ingest <path>`: Ingests documents or screenshots from the command line.
