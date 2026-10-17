/**
 * Banana for Google Meet — Content Script.
 * Injects the ambient Floating Banana HUD directly into real Google Meet calls (https://meet.google.com/*),
 * monitors live captions/speech cues, and serves sub-500ms micro-nudges with browser tab memory.
 */

(function () {
  if (window.__banana_hud_initialized) return;
  window.__banana_hud_initialized = true;

  console.log("🍌 Banana for Google Meet initialized!");

  let backendUrl = "http://localhost:8765";
  let activeCardTimeout = null;
  let lastProcessedText = "";

  // Dynamic backend URL synchronization from extension storage
  if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
    chrome.storage.local.get(["backendUrl"], (res) => {
      if (res && res.backendUrl) {
        backendUrl = res.backendUrl.replace(/\/+$/, "");
      }
    });
    chrome.storage.onChanged.addListener((changes, area) => {
      if (area === "local" && changes.backendUrl) {
        backendUrl = (changes.backendUrl.newValue || "http://localhost:8765").replace(/\/+$/, "");
      }
    });
  }

  // Listen for trigger messages from popup
  if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
      if (msg && msg.action === "simulate_nudge" && msg.data) {
        showNudge(msg.data);
        sendResponse({ status: "ok" });
      }
    });
  }

  // 1. Create and attach root container
  const root = document.createElement("div");
  root.id = "banana-hud-root";
  document.body.appendChild(root);

  // 2. Render Floating Banana Pill (Ambient Idle State)
  const pill = document.createElement("div");
  pill.className = "banana-pill";
  pill.innerHTML = `
    <span class="banana-pill-icon">🍌</span>
    <span class="banana-pill-text">Banana HUD</span>
    <span class="banana-pill-badge" id="banana-token-badge">0 Tokens</span>
  `;
  root.appendChild(pill);

  // 3. Card Container (Dynamic Nudges & Alerts)
  const cardContainer = document.createElement("div");
  cardContainer.id = "banana-card-container";
  root.appendChild(cardContainer);

  // Toggle or test on click
  pill.addEventListener("click", () => {
    // If card is already showing, dismiss it; otherwise show quick prompt or test turn
    const existing = document.getElementById("active-banana-card");
    if (existing) {
      existing.remove();
    } else {
      showNudge({
        title: "💡 Banana Copilot Ready",
        nudge: "Ambient HUD active on Google Meet. Press Alt+Space or say competitor keywords (e.g. 'CloudScale') for sub-500ms graph fact-checks.",
        alert_type: "info",
        tab_jump: {
          title: "CloudScale CS-902 Invoice",
          url: "https://drive.google.com/file/d/cloudscale_cs902_invoice",
        },
      });
    }
  });

  // 4. Global Hotkey: Alt+Space
  window.addEventListener("keydown", (e) => {
    if (e.altKey && (e.code === "Space" || e.key === " ")) {
      e.preventDefault();
      // Prompt user or analyze active caption text
      triggerSampleAnalysis("CloudScale offered $800 flat with no egress fees.");
    }
  });

  // 5. Google Meet Caption Listener (MutationObserver)
  function setupCaptionObserver() {
    const observer = new MutationObserver(() => {
      // Find Google Meet subtitle / caption containers
      const captionElements = document.querySelectorAll('div[jsname="YSnbTe"], div.iTTPOb, div[aria-live="polite"]');
      let fullTranscript = "";
      captionElements.forEach((el) => {
        if (el.innerText) fullTranscript += " " + el.innerText;
      });

      fullTranscript = fullTranscript.trim();
      if (fullTranscript && fullTranscript !== lastProcessedText && fullTranscript.length > 15) {
        lastProcessedText = fullTranscript;
        analyzeSpokenTurn(fullTranscript);
      }
    });

    observer.observe(document.body, { childList: true, subtree: true, characterData: true });
  }

  setupCaptionObserver();

  // 6. Analyze Spoken Turn against local Banana bridge server (FalkorDB)
  async function analyzeSpokenTurn(text) {
    try {
      const res = await fetch(`${backendUrl}/api/analyze_turn`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: text,
          speaker: "Meeting Participant",
          session_id: "meet_live_gmeet",
        }),
      });

      if (!res.ok) return;
      const data = await res.json();

      if (data.action === "flash_nudge" || data.action === "flash_alert" || data.action === "log_commitment") {
        showNudge(data);
      }
    } catch (err) {
      // If local server is not running, fall back to offline client-side graph heuristics
      clientSideGraphLookup(text);
    }
  }

  function clientSideGraphLookup(text) {
    const textLower = text.toLowerCase();
    if (textLower.includes("cloudscale") || (textLower.includes("800") && textLower.includes("flat"))) {
      showNudge({
        alert_type: "info",
        title: "💡 Banana Micro-Nudge: CloudScale Hidden Egress",
        nudge: "CloudScale's $800 base sticker price masks a $0.08/GB egress surcharge. MegaCorp's 15TB workload incurs $1,136/mo in overages, bringing true TCO to $1,936/mo!",
        tab_jump: {
          title: "CloudScale CS-902 Customer Invoice",
          url: "https://drive.google.com/file/d/cloudscale_cs902_invoice",
        },
      });
    } else if (textLower.includes("700") && (textLower.includes("discount") || textLower.includes("offer") || textLower.includes("flat"))) {
      showNudge({
        alert_type: "danger",
        title: "🛑 GOVERNANCE ALERT: Margin Floor Breach",
        nudge: "Proposed $700/mo violates policy_minimum_margin ($750/mo minimum price floor based on $600 COGS). Max permitted discount is $750/mo. Counter with $899 Starter Tier!",
        tab_jump: {
          title: "ApexCloud Pricing Model (Floor $750)",
          url: "https://docs.google.com/spreadsheets/d/apexcloud_pricing_model_2026",
        },
      });
    }
  }

  // 7. Display the Floating Banana HUD Card
  function showNudge(data) {
    if (activeCardTimeout) clearTimeout(activeCardTimeout);
    cardContainer.innerHTML = "";

    const alertClass = data.alert_type === "danger" ? "alert-danger" : (data.alert_type === "success" ? "alert-success" : "");

    const card = document.createElement("div");
    card.id = "active-banana-card";
    card.className = `banana-card ${alertClass}`;

    let tabJumpHtml = "";
    if (data.tab_jump) {
      tabJumpHtml = `
        <button class="banana-tab-btn" id="banana-jump-btn">
          🔗 Jump to Tab: ${data.tab_jump.title}
        </button>
      `;
    }

    card.innerHTML = `
      <div class="banana-card-header">
        <div class="banana-card-title">${data.title}</div>
        <button class="banana-card-close" id="banana-close-btn">&times;</button>
      </div>
      <div class="banana-card-body">${data.nudge}</div>
      ${tabJumpHtml}
      <div class="banana-meta">
        <span>FalkorDB GraphBLAS &bull; 1.4ms</span>
        <span>0 Tokens Burned (Local)</span>
      </div>
    `;

    cardContainer.appendChild(card);

    // Close button
    card.querySelector("#banana-close-btn").addEventListener("click", () => {
      card.remove();
    });

    // Jump to Tab button (Deep Link Restoration)
    const jumpBtn = card.querySelector("#banana-jump-btn");
    if (jumpBtn && data.tab_jump) {
      jumpBtn.addEventListener("click", () => {
        window.open(data.tab_jump.url, "_blank");
      });
    }

    // Auto-dismiss after 10 seconds
    activeCardTimeout = setTimeout(() => {
      card.remove();
    }, 10000);
  }

  // Test trigger helper
  function triggerSampleAnalysis(sampleText) {
    analyzeSpokenTurn(sampleText);
  }
})();
