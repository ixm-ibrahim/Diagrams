/* Comparison Matrix archetype renderer (also serves Evidence Cards via
 * `worldview.cellKind = "evidence"`, and Section 7 via topic clusters).
 *
 * Data shape:
 * {
 *   archetype: "comparison-matrix" | "comparison-matrix-clustered" | "evidence-cards",
 *   eyebrow, title, subtitle,
 *   worldviews: [
 *     { id, name, slot: 1..7 }  // slot maps to --tN palette
 *   ],
 *   criteria: [...]           // for non-clustered
 *   OR
 *   topics: [                 // for clustered (Section 7)
 *     { id, eyebrow, title, subtitle, criteria: [...], synthesis: "..." }
 *   ]
 *
 *   criterion: {
 *     id, header, tiesBackTo: { tier, name },
 *     cells: [
 *       { worldview: "...", verdict, text, source?, quote?, analysis?, internals? }
 *     ],
 *     synthesis: "..."
 *   }
 * }
 */

import { renderNodeCard } from "./node-card.js";

export function renderMatrix(section, mount) {
  const isClustered = section.archetype === "comparison-matrix-clustered";
  const isEvidence = section.archetype === "evidence-cards";

  const frame = document.createElement("div");
  frame.className = "frame";
  frame.innerHTML = `
    <div class="frame-head">
      <div class="frame-eyebrow">${esc(section.eyebrow || "")}</div>
      <h2 class="frame-title">${esc(section.title)}</h2>
      ${section.subtitle ? `<div class="frame-subtitle">${esc(section.subtitle)}</div>` : ""}
    </div>
    ${renderFilterBar(section.worldviews || [])}
    ${(isClustered || section.criteria) ? `
      <div class="collapse-controls">
        <span>Sections:</span>
        <button data-expand-all type="button">Expand all</button>
        <span class="sep">·</span>
        <button data-collapse-all type="button">Collapse all</button>
      </div>` : ""}
    <div class="matrix-body"></div>
  `;

  const body = frame.querySelector(".matrix-body");

  if (isClustered) {
    (section.topics || []).forEach((topic) => {
      body.appendChild(renderTopicCluster(section.id, section.worldviews, topic, isEvidence));
    });
  } else {
    const stack = document.createElement("div");
    stack.className = "criteria-stack";
    (section.criteria || []).forEach((criterion) => {
      stack.appendChild(renderCriterion(section.id, section.worldviews, criterion, isEvidence));
    });
    body.appendChild(stack);
  }

  mount.innerHTML = "";
  mount.appendChild(frame);

  wireFilters(frame);
  wireScrollSync(frame);
}

function renderFilterBar(worldviews) {
  if (!worldviews.length) return "";
  const pills = worldviews.map(w => `
    <button class="filter-pill" type="button" data-active="true" data-world-id="${esc(w.id)}"
            style="--w-color: var(--t${w.slot}); --w-numeral: var(--t${w.slot}n);">
      <span class="filter-pill-dot"></span>${esc(w.name)}
    </button>
  `).join("");
  return `
    <div class="filter-bar">
      <span class="filter-bar-label">Show</span>
      ${pills}
    </div>
  `;
}

function renderTopicCluster(sectionId, worldviews, topic, isEvidence) {
  const cluster = document.createElement("div");
  cluster.className = "topic-cluster";
  const topicKey = `${sectionId}-topic-${topic.id}`;

  cluster.innerHTML = `
    <div class="topic-eyebrow">${esc(topic.eyebrow || "")}</div>
    <h3 class="topic-header" data-collapsible data-section-id="${esc(topicKey)}">
      <span>${esc(topic.title)}</span>
      <span class="chevron" aria-hidden="true">▾</span>
    </h3>
    ${topic.subtitle ? `<div class="topic-subtitle">${esc(topic.subtitle)}</div>` : ""}
    <div class="section-body">
      <div class="criteria-stack"></div>
      ${topic.synthesis ? renderTopicSynth(topic) : ""}
    </div>
  `;

  const stack = cluster.querySelector(".criteria-stack");
  (topic.criteria || []).forEach((c) => {
    stack.appendChild(renderCriterion(sectionId, worldviews, c, isEvidence));
  });

  return cluster;
}

function renderCriterion(sectionId, worldviews, criterion, isEvidence) {
  const c = document.createElement("div");
  c.className = "criterion";
  const key = `${sectionId}-crit-${criterion.id}`;

  const tiesBack = criterion.tiesBackTo
    ? `<div class="tier-tag">↳ Ties back to Tier ${criterion.tiesBackTo.tier} · ${esc(criterion.tiesBackTo.name || "")}</div>`
    : "";

  c.innerHTML = `
    ${tiesBack}
    <div class="criterion-header" data-collapsible data-section-id="${esc(key)}">
      <span>${esc(criterion.header)}</span>
      <span class="chevron" aria-hidden="true">▾</span>
    </div>
    <div class="section-body">
      <div class="scroll-pane sync"><div class="cells-row"></div></div>
      ${criterion.synthesis ? renderSynth(criterion.synthesis) : ""}
    </div>
  `;

  const row = c.querySelector(".cells-row");
  (criterion.cells || []).forEach((cell) => {
    row.appendChild(renderCell(worldviews, cell, isEvidence));
  });

  return c;
}

function renderCell(worldviews, cell, isEvidence) {
  const wv = worldviews.find(w => w.id === cell.worldview);
  if (!wv) return document.createElement("div");

  const el = document.createElement("div");
  el.className = "matrix-cell" + (isEvidence ? " evidence-cell" : "");
  el.dataset.worldId = wv.id;
  el.style.setProperty("--w-color", `var(--t${wv.slot})`);
  el.style.setProperty("--w-numeral", `var(--t${wv.slot}n)`);
  el.style.setProperty("--w-bg", `var(--t${wv.slot}bg)`);

  if (isEvidence) {
    el.innerHTML = `
      <div class="evidence-source">${esc(cell.source || wv.name)}</div>
      <div class="evidence-quote">${esc(cell.quote || "")}</div>
      <div class="evidence-analysis">${esc(cell.analysis || cell.text || "")}</div>
    `;
  } else {
    el.innerHTML = `
      <div class="matrix-cell-head">
        <span class="matrix-cell-world">${esc(wv.name)}</span>
        <span class="matrix-cell-verdict">${esc(cell.verdict || "")}</span>
      </div>
      <div class="matrix-cell-text">${esc(cell.text || "")}</div>
    `;
  }

  // Optional click → open node-card if internals are provided
  if (cell.internals) {
    el.addEventListener("click", () => {
      // For v1: log; full inline expansion can be added when data model is fleshed out
      console.log("Cell clicked", cell.id);
    });
  }
  return el;
}

function renderSynth(text) {
  return `
    <div class="synth-card">
      <div class="synth-label">Synthesis</div>
      <div class="synth-text">${esc(text)}</div>
    </div>
  `;
}

function renderTopicSynth(topic) {
  return `
    <div class="topic-synth-card">
      <div class="topic-synth-label">Topic synthesis · ${esc(topic.title)}</div>
      <div class="topic-synth-text">${esc(topic.synthesis)}</div>
    </div>
  `;
}

function wireFilters(frame) {
  const pills = frame.querySelectorAll(".filter-pill");
  pills.forEach((pill) => {
    pill.addEventListener("click", () => {
      const wvId = pill.dataset.worldId;
      const isActive = pill.dataset.active === "true";
      pill.dataset.active = isActive ? "false" : "true";
      frame.querySelectorAll(`[data-world-id="${wvId}"].matrix-cell`).forEach(c => {
        c.classList.toggle("is-hidden", isActive);
      });
    });
  });
}

function wireScrollSync(frame) {
  const panes = frame.querySelectorAll(".scroll-pane.sync");
  let active = false;
  panes.forEach(pane => {
    pane.addEventListener("scroll", () => {
      if (active) return;
      active = true;
      panes.forEach(p => { if (p !== pane) p.scrollLeft = pane.scrollLeft; });
      requestAnimationFrame(() => { active = false; });
    });
  });
}

function esc(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
