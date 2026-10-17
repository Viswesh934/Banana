/**
 * Banana for Google Meet - Extension Popup Script
 */

document.addEventListener("DOMContentLoaded", async () => {
  const statusBadge = document.getElementById("statusBadge");
  const statusText = document.getElementById("statusText");
  const serverUrlInput = document.getElementById("serverUrl");
  const saveBtn = document.getElementById("saveBtn");
  const testCloudScaleBtn = document.getElementById("testCloudScaleBtn");
  const testMarginBtn = document.getElementById("testMarginBtn");

  const DEFAULT_URL = "http://localhost:8765";

  // Load saved backend URL
  if (chrome.storage && chrome.storage.local) {
    chrome.storage.local.get(["backendUrl"], (res) => {
      if (res && res.backendUrl) {
        serverUrlInput.value = res.backendUrl;
      } else {
        serverUrlInput.value = DEFAULT_URL;
      }
      checkHealth(serverUrlInput.value);
    });
  } else {
    serverUrlInput.value = DEFAULT_URL;
    checkHealth(DEFAULT_URL);
  }

  // Health check helper
  async function checkHealth(url) {
    statusBadge.className = "status-badge";
    statusText.innerText = "Checking...";
    try {
      const cleanUrl = url.replace(/\/+$/, "");
      const start = performance.now();
      const res = await fetch(`${cleanUrl}/api/health`, { method: "GET" });
      const elapsed = Math.round(performance.now() - start);

      if (res.ok) {
        const data = await res.json();
        statusBadge.className = "status-badge online";
        statusText.innerText = `Online (${elapsed}ms)`;
      } else {
        statusBadge.className = "status-badge";
        statusText.innerText = `HTTP ${res.status}`;
      }
    } catch (err) {
      statusBadge.className = "status-badge";
      statusText.innerText = "Offline";
    }
  }

  // Save URL
  saveBtn.addEventListener("click", () => {
    let url = serverUrlInput.value.trim();
    if (!url) url = DEFAULT_URL;
    url = url.replace(/\/+$/, "");
    serverUrlInput.value = url;

    if (chrome.storage && chrome.storage.local) {
      chrome.storage.local.set({ backendUrl: url }, () => {
        checkHealth(url);
      });
    } else {
      checkHealth(url);
    }
  });

  // Helper to send message to active Google Meet tab
  function sendToActiveMeetTab(message) {
    if (!chrome.tabs) return;
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs && tabs[0] && tabs[0].id) {
        chrome.tabs.sendMessage(tabs[0].id, message, (response) => {
          if (chrome.runtime.lastError) {
            console.log("Could not send message to tab (is Google Meet open?):", chrome.runtime.lastError.message);
          }
        });
      }
    });
  }

  // Test CloudScale Nudge
  testCloudScaleBtn.addEventListener("click", () => {
    sendToActiveMeetTab({
      action: "simulate_nudge",
      data: {
        alert_type: "info",
        title: "💡 Banana Micro-Nudge: CloudScale Hidden Egress",
        nudge: "CloudScale's $800 base sticker price masks a $0.08/GB egress surcharge. MegaCorp's 15TB workload incurs $1,136/mo in overages, bringing true TCO to $1,936/mo!",
        tab_jump: {
          title: "CloudScale CS-902 Customer Invoice",
          url: "https://drive.google.com/file/d/cloudscale_cs902_invoice",
        },
      },
    });
  });

  // Test Margin Breach Alert
  testMarginBtn.addEventListener("click", () => {
    sendToActiveMeetTab({
      action: "simulate_nudge",
      data: {
        alert_type: "danger",
        title: "🛑 GOVERNANCE ALERT: Margin Floor Breach",
        nudge: "Proposed $700/mo violates policy_minimum_margin ($750/mo minimum price floor based on $600 COGS). Max permitted discount is $750/mo. Counter with $899 Starter Tier!",
        tab_jump: {
          title: "ApexCloud Pricing Model (Floor $750)",
          url: "https://docs.google.com/spreadsheets/d/apexcloud_pricing_model_2026",
        },
      },
    });
  });
});
