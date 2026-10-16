# Banana: Enterprise Multimodal Adapters Architecture
## Live Browser Meetings • Google Workspace (Drive & Sheets) • Connected Edge Devices

---

## 1. System Vision

Banana evolves from a passive query agent into an **ambient, real-time enterprise copilot** powered by **FalkorDB Graph Intelligence**. 

Instead of waiting for manual prompts, Banana listens to live executive meetings, reads connected Google Workspace sheets and documents, and ingests live edge-device visual captures to make **governed, graph-backed decisions on the fly**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       AMBIENT ENTERPRISE ADAPTER LAYER                      │
│                                                                             │
│  ┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────┐  │
│  │ BROWSER MEETING       │ │ GOOGLE WORKSPACE      │ │ CONNECTED DEVICES │  │
│  │ LISTENER ADAPTER      │ │ ADAPTER (DRIVE/SHEETS)│ │ (CAMERA / EDGE)   │  │
│  │ (Google Meet / Audio) │ │ (Live Pricing Sync)   │ │ (Whiteboards/Flyer│  │
│  └───────────┬───────────┘ └───────────┬───────────┘ └─────────┬─────────┘  │
└──────────────┼─────────────────────────┼───────────────────────┼────────────┘
               │ Live Audio Stream       │ Two-way Sync          │ Edge Visual
               ▼                         ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              MULTIMODAL INGESTION & EXTRACTION PIPELINE                     │
│               Gemini 3.5 Flash Multimodal Vision & Audio API                │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Real-time Cypher Graph Updates
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 FALKORDB REAL-TIME ENTERPRISE KNOWLEDGE GRAPH               │
│  • Live Meeting Turns: (:MeetingTurn)-[:DECIDED]->(:Memory)                 │
│  • Live Spreadsheet Models: (:SheetCell)-[:BOUND_BY]->(:Policy)             │
│  • Real-Time Policy Alerting: Flags margin breaches during live conversation │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│               ON-THE-FLY STRATEGIC DECISIONS & WORKSPACE ACTIONS            │
│  • Instant in-meeting nudges: "Warning: $700 price violates 25% margin"     │
│  • Automated Google Sheet formula & price adjustments                       │
│  • Cross-session persistent memories linked to meeting recordings           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Adapter 1: Browser Meeting Listener & Live Strategic Nudge

### 2.1 How It Works
- A browser extension or WebRTC audio adapter captures conference audio (e.g. Google Meet, Zoom web).
- Streams audio chunks to **Gemini 3.5 Flash Audio**.
- **Real-time Graph Extraction**:
  - Detects competitive mentions: *"CloudScale sales reps are offering 20% discounts off-book."*
  - Automatically creates an `(:Evidence {source: 'Executive Strategy Call', confidence: 0.95})` node in FalkorDB.
- **In-Meeting Live Policy Nudge**:
  - If a team member suggests: *"Can we discount ApexCloud Enterprise to $700/mo to close this deal?"*
  - Banana traverses `(policy:Policy {canonical_id: 'policy_minimum_margin'})`, detects that $700 is below the $750 floor (violating the 25% margin rule), and emits an instant on-screen alert:
    > ⚠️ **Margin Violation Alert**: Proposed $700/mo price is below our $750/mo minimum floor ($600 COGS basis). Max permitted discount without CFO override is $750/mo (yielding 20% cost-plus / 25% revenue margin).

---

## 3. Adapter 2: Google Workspace Integration (Drive & Sheets)

### 3.1 Google Sheets (Two-Way Live Pricing Engine)
- **Live Sync**: Banana monitors financial sheets (e.g., `ApexCloud_Pricing_Model_2026.xlsx` or Google Sheet).
- **On-The-Fly Decision Making**:
  - When an account executive requests a custom deal in Google Sheets, Banana validates the parameters against FalkorDB policy graphs.
  - If approved, Banana automatically calculates the optimal bundle and updates the Google Sheet cells with verified figures and audit notes.

### 3.2 Google Drive (Ambient Contract & Teardown Ingestion)
- Connects via Google Drive API webhook.
- Whenever a new PDF, proposal, or competitor teardown is dropped into a monitored Drive folder:
  - Banana automatically ingests the document.
  - Extracts pricing tables, SLAs, and hidden fees using Gemini Vision.
  - Inserts new `(:Document)` and `(:Evidence)` nodes into FalkorDB, updating the visual graph in real-time.

---

## 4. Adapter 3: Connected Devices & Edge Optical Capture

### 4.1 Whiteboard & On-Site Intelligence Capture
- Field sales reps or executives at conferences snap photos of:
  - Competitor booth pricing boards.
  - Event flyers and promotional discount tiers.
  - Physical enterprise agreements and invoices.
- Sent via mobile / edge camera to Banana:
  - Gemini Vision performs OCR and table structure reconstruction.
  - Links the photographic evidence to the competitor entity in FalkorDB with geolocation and timestamp provenance.

---

## 5. Technical Implementation Roadmap

1. **Browser Audio Adapter**:
   - Web Audio API / MediaStream capture in Streamlit or Chrome Extension.
   - Streaming websocket endpoint connecting audio to Gemini Audio $\to$ FalkorDB Cypher ingestion.
2. **Google Workspace Client**:
   - `google-api-python-client` with OAuth2 service account for Google Drive & Google Sheets API.
   - Two-way pricing sync tool: `read_pricing_sheet()` and `write_approved_deal()`.
3. **Multimodal Ingestion Tab in UI**:
   - Drag & drop live audio files (WAV/MP3), camera snapshots, and Drive folder sync status.
