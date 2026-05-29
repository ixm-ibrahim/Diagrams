/* Entry point.
 * Loads data.json, picks the section to render, dispatches to the
 * archetype renderer, then initializes universal behaviors.
 */

import { initTheme } from "./theme.js";
import { initCollapsible } from "./collapsible.js";
import { renderTree } from "./render-tree.js";
import { renderLadder } from "./render-ladder.js";
import { renderMatrix } from "./render-matrix.js";

const RENDERERS = {
  "convergent-tree": renderTree,
  "rainbow-ladder": renderLadder,
  "comparison-matrix": renderMatrix,
  "comparison-matrix-clustered": renderMatrix,
  "evidence-cards": renderMatrix,
};

initTheme();

(async function bootstrap() {
  const mount = document.getElementById("content");
  try {
    const data = await fetch("./data.json").then(r => r.json());

    // For v1: render the first section in data.sections (later: route by hash)
    const section = chooseSection(data);
    if (!section) {
      mount.innerHTML = `<p>No section to render.</p>`;
      return;
    }

    document.getElementById("page-title").textContent = `${section.eyebrow || ""} — ${section.title}`;
    document.getElementById("breadcrumb-current").textContent = section.title;

    const renderer = RENDERERS[section.archetype];
    if (!renderer) {
      mount.innerHTML = `<p>Archetype "<code>${section.archetype}</code>" not implemented yet.</p>`;
      return;
    }

    renderSectionPicker(data, section);
    renderer(section, mount);
    initCollapsible(mount);
  } catch (err) {
    console.error(err);
    mount.innerHTML = `<p>Failed to load data: ${err.message}</p>`;
  }
})();

function chooseSection(data) {
  const hash = location.hash.replace(/^#/, "");
  if (hash) {
    const match = (data.sections || []).find(s => s.id === hash);
    if (match) return match;
  }
  return (data.sections || [])[0];
}

function renderSectionPicker(data, current) {
  const picker = document.getElementById("section-picker");
  if (!picker) return;
  picker.innerHTML = (data.sections || []).map(s => {
    const isCurrent = s.id === current.id;
    return `<a href="#${s.id}"${isCurrent ? ' aria-current="page"' : ""}>${escapeHtml(s.eyebrow || s.id)}</a>`;
  }).join("");
}

function escapeHtml(s) {
  return String(s).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

// Re-render when hash changes
window.addEventListener("hashchange", () => {
  location.reload();
});
