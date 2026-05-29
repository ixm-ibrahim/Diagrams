/* Node card — expanded internal strips.
 * Shared by every archetype. Pass card data + tier number (1..7).
 *
 * Card data shape:
 * {
 *   id, title, tierName?,
 *   internals: {
 *     claim, soWhat,
 *     unlocks: [string],
 *     eliminates: [string],
 *     unknown: [string],
 *     objections: [{ text, type: "Premise"|"Rule"|"Conclusion"|"Def" }]
 *   },
 *   cost?: number  // count of downstream nodes if this is disagreed with
 * }
 */

export function renderNodeCard(card, tierN) {
  const el = document.createElement("div");
  el.className = "node-card";
  el.style.setProperty("--tier-color", `var(--t${tierN})`);
  el.style.setProperty("--tier-numeral", `var(--t${tierN}n)`);
  el.style.setProperty("--tier-bg", `var(--t${tierN}bg)`);

  const i = card.internals || {};
  const cost = card.cost ?? 0;

  el.innerHTML = `
    <div class="node-card-head">
      <span class="node-card-tier">
        <span class="node-card-tier-num">${tierN}</span> · ${esc(card.tierName || "")}
      </span>
      <h3 class="node-card-title">${esc(card.title)}</h3>
    </div>
    ${i.claim ? strip("Claim", `<div class="strip-text">${esc(i.claim)}</div>`) : ""}
    ${i.soWhat ? strip("So what", `<div class="strip-text">${esc(i.soWhat)}</div>`) : ""}
    ${bulletStrip("Unlocks", i.unlocks)}
    ${bulletStrip("Eliminates", i.eliminates)}
    ${bulletStrip("Unknown remainder", i.unknown)}
    ${objectionsStrip(i.objections)}
    <div class="node-card-footer">
      <button class="node-btn is-primary" type="button">Derivation →</button>
      <button class="node-btn is-agree" type="button" data-action="agree">✓ Agree</button>
      <button class="node-btn is-disagree" type="button" data-action="disagree">✗ Disagree</button>
      ${cost > 0 ? `<span class="cost-readout">Cost: ${cost} node${cost === 1 ? "" : "s"} downstream</span>` : ""}
    </div>
  `;

  // Simple agree/disagree toggle (state only — propagation comes later)
  el.querySelectorAll("[data-action]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const others = el.querySelectorAll("[data-action]");
      const wasActive = btn.classList.contains("is-active");
      others.forEach(b => b.classList.remove("is-active"));
      if (!wasActive) btn.classList.add("is-active");
    });
  });

  return el;
}

function strip(label, contentHtml) {
  return `<div class="strip"><div class="strip-label">${esc(label)}</div>${contentHtml}</div>`;
}

function bulletStrip(label, items) {
  if (!items || !items.length) return "";
  const lis = items.map(b => `<li>${esc(b)}</li>`).join("");
  return strip(label, `<ul class="strip-bullets">${lis}</ul>`);
}

function objectionsStrip(items) {
  if (!items || !items.length) return "";
  const rows = items.map(o => `
    <div class="objection">
      <span class="objection-arrow">→</span>
      <span class="objection-text">${esc(o.text)}</span>
      <span class="objection-type">${esc(o.type || "")}</span>
    </div>
  `).join("");
  return `<div class="strip"><div class="strip-label">Objections (${items.length})</div>${rows}</div>`;
}

function esc(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
