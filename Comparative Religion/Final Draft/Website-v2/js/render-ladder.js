/* Rainbow Ladder archetype renderer.
 *
 * Data shape:
 * {
 *   archetype: "rainbow-ladder",
 *   eyebrow, title, subtitle,
 *   tiers: [
 *     { n: 1..7, title, internals? },
 *     ...
 *   ]
 * }
 *
 * Renders apex-on-top (tier N at top, tier 1 at bottom).
 * Row widths taper 56% (apex) → 96% (base).
 */

import { renderNodeCard } from "./node-card.js";

const TAPER = {
  1: { px: 520, pct: 96 },
  2: { px: 460, pct: 88 },
  3: { px: 400, pct: 80 },
  4: { px: 340, pct: 72 },
  5: { px: 280, pct: 64 },
  6: { px: 220, pct: 56 },
  7: { px: 220, pct: 56 }
};

export function renderLadder(section, mount) {
  const frame = document.createElement("div");
  frame.className = "frame";
  frame.innerHTML = `
    <div class="frame-head">
      <div class="frame-eyebrow">${esc(section.eyebrow || "")}</div>
      <h2 class="frame-title">${esc(section.title)}</h2>
      ${section.subtitle ? `<div class="frame-subtitle">${esc(section.subtitle)}</div>` : ""}
    </div>
    <div class="ladder-stack"></div>
  `;

  const stack = frame.querySelector(".ladder-stack");

  // Apex-on-top: render highest tier first
  const tiers = [...(section.tiers || [])].sort((a, b) => b.n - a.n);

  tiers.forEach((tier) => {
    const n = tier.n;
    const taper = TAPER[n] || TAPER[6];

    const row = document.createElement("div");
    row.className = "ladder-row";
    row.style.width = `min(${taper.px}px, ${taper.pct}%)`;
    row.style.setProperty("--tier-color", `var(--t${n})`);
    row.style.setProperty("--tier-numeral", `var(--t${n}n)`);
    row.style.setProperty("--tier-bg", `var(--t${n}bg)`);
    row.dataset.cardId = tier.id || `tier-${n}`;

    row.innerHTML = `
      <span class="ladder-circle">${n}</span>
      <span class="ladder-text">${esc(tier.title)}</span>
      <span class="ladder-dot"></span>
    `;

    const body = document.createElement("div");
    body.className = "ladder-row-body";

    row.addEventListener("click", () => {
      const existing = body.querySelector(".node-card");
      if (existing) {
        existing.remove();
        row.classList.remove("is-active");
        return;
      }
      // Remove other active expansions
      stack.querySelectorAll(".ladder-row.is-active").forEach(r => r.classList.remove("is-active"));
      stack.querySelectorAll(".ladder-row-body .node-card").forEach(c => c.remove());

      const card = renderNodeCard({ ...tier, tierName: tier.name || "" }, n);
      body.appendChild(card);
      row.classList.add("is-active");
    });

    stack.appendChild(row);
    stack.appendChild(body);
  });

  mount.innerHTML = "";
  mount.appendChild(frame);
}

function esc(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
