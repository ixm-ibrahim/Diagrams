/* Universal collapsible-section behavior.
 *
 * Any element with [data-collapsible][data-section-id="..."] becomes a click
 * target that toggles the sibling .section-body. State persists in
 * localStorage keyed by section-id.
 *
 * Renderers should mark up headers like:
 *   <div class="lane-head" data-collapsible data-section-id="tier-3">
 *     <span class="lane-name">Corroboration</span>
 *     ...
 *     <span class="chevron" aria-hidden="true">▾</span>
 *   </div>
 *   <div class="section-body">...</div>
 */

const STORAGE_KEY = "collapsed-sections-v1";

function loadCollapsed() {
  try {
    return new Set(JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"));
  } catch {
    return new Set();
  }
}

function saveCollapsed(set) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify([...set]));
}

export function initCollapsible(root = document) {
  const collapsed = loadCollapsed();

  root.querySelectorAll("[data-collapsible][data-section-id]").forEach((head) => {
    const id = head.getAttribute("data-section-id");
    const body = head.nextElementSibling;
    if (!body || !body.classList.contains("section-body")) return;

    // Apply persisted state
    const isCollapsed = collapsed.has(id);
    head.setAttribute("data-collapsed", isCollapsed ? "true" : "false");
    body.setAttribute("data-collapsed", isCollapsed ? "true" : "false");

    head.addEventListener("click", () => {
      const nowCollapsed = head.getAttribute("data-collapsed") !== "true";
      head.setAttribute("data-collapsed", nowCollapsed ? "true" : "false");
      body.setAttribute("data-collapsed", nowCollapsed ? "true" : "false");
      const set = loadCollapsed();
      if (nowCollapsed) set.add(id); else set.delete(id);
      saveCollapsed(set);
    });
  });

  // Wire collapse-all / expand-all if present
  const allBtn = root.querySelector("[data-collapse-all]");
  const expandBtn = root.querySelector("[data-expand-all]");
  if (allBtn) {
    allBtn.addEventListener("click", () => setAll(root, true));
  }
  if (expandBtn) {
    expandBtn.addEventListener("click", () => setAll(root, false));
  }
}

function setAll(root, collapsedState) {
  const set = loadCollapsed();
  root.querySelectorAll("[data-collapsible][data-section-id]").forEach((head) => {
    const id = head.getAttribute("data-section-id");
    const body = head.nextElementSibling;
    if (!body) return;
    head.setAttribute("data-collapsed", collapsedState ? "true" : "false");
    body.setAttribute("data-collapsed", collapsedState ? "true" : "false");
    if (collapsedState) set.add(id); else set.delete(id);
  });
  saveCollapsed(set);
}
