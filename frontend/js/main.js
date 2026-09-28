/*
 * main.js
 * -------
 * Shared across every page: the API base URL, the mobile nav toggle,
 * and a couple of small utility functions used elsewhere.
 */

// Use the same origin in production; keep the separate local frontend server workflow.
const isLocalFrontendServer = window.location.protocol === "file:"
  || (["localhost", "127.0.0.1"].includes(window.location.hostname)
    && window.location.port !== "8000");
const API_BASE = isLocalFrontendServer ? "http://127.0.0.1:8000/api" : "/api";

function initNav() {
  const toggle = document.querySelector(".nav-toggle");
  const links = document.querySelector(".nav-links");
  if (!toggle || !links) return;

  toggle.addEventListener("click", () => {
    const isOpen = links.classList.toggle("open");
    toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
  });

  links.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      links.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
    });
  });
}

function formatPercent(value, decimals = 1) {
  return `${(value * 100).toFixed(decimals)}%`;
}

function formatPoints(value, decimals = 1) {
  return `${(value * 100).toFixed(decimals)} pts`;
}

// Animate a number counting up — used for the fairness score and stats.
function animateCount(el, target, duration = 900, suffix = "") {
  if (!el) return;
  const start = 0;
  const startTime = performance.now();

  function tick(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(start + (target - start) * eased);
    el.textContent = current + suffix;
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    let detail = "Something went wrong while talking to the FairLens server.";
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch (e) {
      /* ignore parse errors */
    }
    throw new Error(detail);
  }
  return response;
}

document.addEventListener("DOMContentLoaded", initNav);
