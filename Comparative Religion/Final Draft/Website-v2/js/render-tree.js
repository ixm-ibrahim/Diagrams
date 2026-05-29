/* Convergent Tree archetype renderer.
 *
 * Data shape:
 * {
 *   archetype: "convergent-tree",
 *   eyebrow, title, subtitle,
 *   roots: [{ id, label }],
 *   tiers: [
 *     { n: 1, name: "Subject", cards: [{ id, title, internals?, more?: number }] },
 *     ...
 *   ]
 * }
 *
 * The `n` field (1..7) maps to CSS variables --tN, --tNn, --tNbg via inline style.
 */

import { renderNodeCard } from "./node-card.js";

export function renderTree(section, mount) {
  const frame = document.createElement("div");
  frame.className = "frame";
  frame.innerHTML = `
    <div class="frame-head">
      <div class="frame-eyebrow">${esc(section.eyebrow || "")}</div>
      <h2 class="frame-title">${esc(section.title)}</h2>
      ${section.subtitle ? `<div class="frame-subtitle">${esc(section.subtitle)}</div>` : ""}
    </div>
    <div class="collapse-controls">
      <span>Sections:</span>
      <button data-expand-all type="button">Expand all</button>
      <span class="sep">·</span>
      <button data-collapse-all type="button">Collapse all</button>
    </div>
    ${renderRoots(section.roots || [])}
    <div class="tree-lanes"></div>
  `;

  const lanesEl = frame.querySelector(".tree-lanes");
  (section.tiers || []).forEach((tier) => {
    lanesEl.appendChild(renderLane(section.id, tier));
  });

  mount.innerHTML = "";
  mount.appendChild(frame);
}

function renderRoots(roots) {
  if (!roots.length) return "";
  const cards = roots.map(r => `<div class="tree-root-card">${esc(r.label)}</div>`).join("");
  return `<div class="tree-roots">${cards}</div>`;
}

function renderLane(sectionId, tier) {
  const n = tier.n;
  const lane = document.createElement("div");
  lane.className = "tree-lane";
  lane.style.setProperty("--tier-bg", `var(--t${n}bg)`);
  lane.style.setProperty("--tier-color", `var(--t${n})`);
  lane.style.setProperty("--tier-numeral", `var(--t${n}n)`);

  const sectionKey = `${sectionId}-t${n}`;

  lane.innerHTML = `
    <div class="tree-lane-head" data-collapsible data-section-id="${esc(sectionKey)}">
      <div class="tree-lane-chip">
        <span class="tree-lane-name">${esc(tier.name || "")}</span>
        <span class="tree-lane-circle">${n}</span>
      </div>
      <div class="tree-lane-cards"></div>
      <span class="chevron" aria-hidden="true">▾</span>
    </div>
    <div class="section-body"></div>
  `;

  // Cards live in two places: surface (in lane-head, always visible on expand)
  // and a body container below for expanded node-cards.
  // For the v1: render compact card chips inline, and let click reveal node-card body.
  const cardsEl = lane.querySelector(".tree-lane-cards");
  const bodyEl = lane.querySelector(".section-body");

  (tier.cards || []).forEach((card) => {
    const chip = document.createElement("button");
    chip.className = "tree-card";
    chip.type = "button";
    chip.textContent = card.title;
    chip.dataset.cardId = card.id;
    chip.addEventListener("click", (e) => {
      e.stopPropagation();  // don't trigger the lane-head collapse
      toggleNodeCard(card, chip, bodyEl, n);
    });
    cardsEl.appendChild(chip);
  });

  if (tier.more) {
    const moreBtn = document.createElement("button");
    moreBtn.className = "tree-card-more";
    moreBtn.type = "button";
    moreBtn.textContent = `+${tier.more} more`;
    cardsEl.appendChild(moreBtn);
  }

  return lane;
}

function toggleNodeCard(card, chip, bodyEl, tierN) {
  const existing = bodyEl.querySelector(`[data-for="${card.id}"]`);
  if (existing) {
    existing.remove();
    chip.classList.remove("is-active");
    return;
  }
  // Remove other active node cards in this lane
  bodyEl.querySelectorAll(".node-card").forEach(el => el.remove());
  bodyEl.parentElement.querySelectorAll(".tree-card.is-active").forEach(el => el.classList.remove("is-active"));

  const node = renderNodeCard(card, tierN);
  node.dataset.for = card.id;
  bodyEl.appendChild(node);
  chip.classList.add("is-active");
}

function esc(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
