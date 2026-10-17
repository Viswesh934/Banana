/**
 * Banana for Google Meet — Instant Console Injector.
 * 
 * How to use:
 * 1. Open any real Google Meet call (https://meet.google.com/...)
 * 2. Press F12 (or Cmd+Option+I on Mac) to open DevTools, click "Console".
 * 3. Paste this script and press Enter.
 * 
 * The Floating Banana will appear in the bottom-right corner of your real Google Meet!
 */

(function () {
  if (document.getElementById("banana-hud-root")) {
    console.log("🍌 Banana HUD is already injected!");
    return;
  }

  // 1. Inject Styles
  const style = document.createElement("style");
  style.id = "banana-hud-styles";
  style.textContent = `
    #banana-hud-root {
      position: fixed;
      bottom: 85px;
      right: 24px;
      z-index: 9999999;
      font-family: 'Google Sans', Roboto, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    .banana-pill {
      display: flex;
      align-items: center;
      gap: 8px;
      background: rgba(30, 41, 59, 0.95);
      border: 2px solid #f59e0b;
      border-radius: 9999px;
      padding: 8px 16px;
      color: #f8fafc;
      cursor: pointer;
      box-shadow: 0 10px 25px -5px rgba(245, 158, 11, 0.35);
      transition: all 0.25s ease;
      user-select: none;
    }
    .banana-pill:hover {
      transform: translateY(-2px) scale(1.03);
      border-color: #fbbf24;
    }
    .banana-pill-icon {
      font-size: 1.3rem;
    }
    .banana-pill-text {
      font-size: 0.82rem;
      font-weight: 700;
      color: #fcd34d;
    }
    .banana-pill-badge {
      background: #064e3b;
      color: #34d399;
      font-size: 0.7rem;
      font-weight: 600;
      padding: 2px 7px;
      border-radius: 9999px;
    }
    .banana-card {
      width: 380px;
      background: rgba(15, 23, 42, 0.97);
      border: 2px solid #f59e0b;
      border-radius: 14px;
      padding: 16px 18px;
      color: #f8fafc;
      box-shadow: 0 20px 35px -10px rgba(0, 0, 0, 0.8);
      margin-top: 10px;
    }
    .banana-card.alert-danger {
      border-color: #ef4444;
    }
    .banana-card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      padding-bottom: 8px;
      margin-bottom: 10px;
    }
    .banana-card-title {
      font-size: 0.92rem;
      font-weight: 700;
    }
    .banana-card-body {
      font-size: 0.88rem;
      line-height: 1.45;
      color: #cbd5e1;
      margin-bottom: 12px;
    }
    .banana-tab-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f59e0b;
      color: #0f172a;
      font-weight: 700;
      font-size: 0.82rem;
      padding: 8px 14px;
      border-radius: 8px;
      border: none;
      cursor: pointer;
      width: 100%;
    }
    .banana-tab-btn:hover {
      background: #fbbf24;
    }
    .banana-meta {
      font-size: 0.72rem;
      color: #64748b;
      margin-top: 8px;
      display: flex;
      justify-content: space-between;
    }
  `;
  document.head.appendChild(style);

  // 2. Inject DOM
  const root = document.createElement("div");
  root.id = "banana-hud-root";

  const pill = document.createElement("div");
  pill.className = "banana-pill";
  pill.innerHTML = `
    <span class="banana-pill-icon">🍌</span>
    <span class="banana-pill-text">Banana HUD</span>
    <span class="banana-pill-badge">0 Tokens</span>
  `;
  root.appendChild(pill);

  const cardContainer = document.createElement("div");
  cardContainer.id = "banana-card-container";
  root.appendChild(cardContainer);

  document.body.appendChild(root);

  function showCard(title, text, isDanger, tabTitle) {
    cardContainer.innerHTML = `
      <div class="banana-card ${isDanger ? 'alert-danger' : ''}">
        <div class="banana-card-header">
          <div class="banana-card-title">${title}</div>
          <button style="background:none;border:none;color:#94a3b8;cursor:pointer;font-size:1.1rem;" onclick="this.closest('.banana-card').remove()">&times;</button>
        </div>
        <div class="banana-card-body">${text}</div>
        <button class="banana-tab-btn" onclick="alert('🔗 Opened Tab: ${tabTitle}')">🔗 Jump to Tab: ${tabTitle}</button>
        <div class="banana-meta">
          <span>FalkorDB GraphBLAS • 1.4ms</span>
          <span>0 Tokens (Local)</span>
        </div>
      </div>
    `;
  }

  pill.addEventListener("click", () => {
    showCard(
      "💡 Banana Micro-Nudge: CloudScale Hidden Egress",
      "CloudScale $800 sticker price masks a $0.08/GB egress fee. MegaCorp's 15TB workload incurs $1,136/mo in overages, bringing true TCO to $1,936/mo!",
      false,
      "CloudScale CS-902 Customer Invoice"
    );
  });

  // Global Hotkey: Alt+Space
  window.addEventListener("keydown", (e) => {
    if (e.altKey && (e.code === "Space" || e.key === " ")) {
      e.preventDefault();
      showCard(
        "🛑 GOVERNANCE ALERT: Margin Floor Breach",
        "Proposed $700/mo violates policy_minimum_margin ($750/mo minimum price floor based on $600 COGS). Max permitted discount is $750/mo. Counter with $899 Starter Tier!",
        true,
        "ApexCloud Pricing Model (Floor $750)"
      );
    }
  });

  console.log("✅ Banana Floating HUD successfully injected into real Google Meet! Click the pill or press Alt+Space.");
})();
