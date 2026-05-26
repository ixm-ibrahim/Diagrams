/* Left-rail container + collapse logic.
 *
 * The rail itself is just chrome: a corner collapse arrow (‹) that hides
 * it, an inline expand handle (›) that brings it back on desktop, a
 * stack of collapsible sections, and a mobile backdrop. Section content
 * (ingredient filter Phase 6, nutrient thresholds Phase 7, meal builder
 * Phase 9) lives in `<section class="rail-section">` blocks created by
 * `createRailSection({ title })` so every section gets the same
 * header-with-chevron pattern.
 *
 * State coupling:
 *   leftRailOpen=true  → rail expanded (drawer slid in on mobile;
 *                        docked column on desktop).
 *   leftRailOpen=false → rail collapsed (drawer off-screen on mobile;
 *                        thin handle column on desktop).
 *   The grid sees this via `data-left-open` on `.app-main`, which the
 *   layout CSS uses to size the columns.
 */

export function mountLeftRail(root, { state }) {
  if (!root) return null;

  root.classList.add('left-rail');
  root.removeAttribute('hidden');
  // Phase 13.5 round 4: "Food Map" title moves from .app-header-left
  // into the rail's own chrome row. On desktop this lets the rail extend
  // top-to-bottom (header no longer covers it). On mobile the rail is a
  // drawer; when closed the chrome is off-screen with the rail, and the
  // .app-header-left .app-title still shows.
  /* Batch 8: sticky "Collapse all" button sits as the first child of
   * .rail-sections so it pins to the top of the rail's scroll viewport
   * once the chrome scrolls out of view. Background is transparent by
   * default and surfaces on hover/focus — keeps the rail visually quiet
   * but always available. The button calls collapseAll() exposed on
   * this rail handle below. */
  root.innerHTML = `
    <header class="rail-chrome">
      <h1 class="app-title-rail">Food Map</h1>
      <button class="rail-collapse" type="button"
              aria-label="Hide filters" title="Hide filters">
        <span aria-hidden="true">←</span>
      </button>
    </header>
    <div class="rail-sections">
      <button class="rail-collapse-all" type="button"
              aria-label="Collapse all sections" title="Collapse all sections">
        <span class="rail-collapse-all-icon" aria-hidden="true">⌃</span>
        <span class="rail-collapse-all-label">Collapse all</span>
      </button>
    </div>
    <button class="rail-expand" type="button"
            aria-label="Show filters" title="Show filters">
      <span aria-hidden="true">→</span>
    </button>
    <div class="rail-resize" data-rail="left" role="separator"
         aria-orientation="vertical" aria-label="Resize filters panel"></div>
    <div class="rail-backdrop" aria-hidden="true"></div>
  `;

  const expandBtn      = root.querySelector('.rail-expand');
  const collapseBtn    = root.querySelector('.rail-collapse');
  const backdrop       = root.querySelector('.rail-backdrop');
  const sections       = root.querySelector('.rail-sections');
  const collapseAllBtn = root.querySelector('.rail-collapse-all');

  /* Batch 8: collapse every section currently open. Sections are the
   * single source of truth for their own collapsed state via
   * data-collapsed — write it, then sync the chevron and aria so the
   * UI matches without each section needing its own subscription. */
  function collapseAll() {
    const openSections = sections.querySelectorAll(
      '.rail-section[data-collapsed="false"]'
    );
    for (const section of openSections) {
      section.dataset.collapsed = 'true';
      const toggle  = section.querySelector('.rail-section-toggle');
      const chevron = section.querySelector('.rail-section-chevron');
      if (toggle)  toggle.setAttribute('aria-expanded', 'false');
      if (chevron) chevron.textContent = '▸';
    }
  }
  collapseAllBtn.addEventListener('click', collapseAll);

  /* Batch 10: nothing to collapse means nothing to offer. Section
   * collapsed-state lives only on each section's data-collapsed
   * attribute (no central state slice), so we watch the subtree with
   * a MutationObserver — fires on toggle clicks AND on collapseAll
   * itself, which is what flips us back to hidden. */
  /* Batch 10 + 14 fix: observe `data-collapsed` AND `hidden` on
   * sections so view-level visibility changes (diet-cuisine section
   * hiding outside meals view) also flow into the collapse-all
   * visibility. The button itself sits inside the observed subtree —
   * setting its own `hidden` attribute would re-trigger the observer
   * and infinite-loop the page (this hung boot). Guard the write so
   * we only mutate when the value actually needs to flip. */
  function syncCollapseAllVisibility() {
    const anyOpen = !!sections.querySelector(
      '.rail-section[data-collapsed="false"]:not([hidden])'
    );
    const shouldHide = !anyOpen;
    if (collapseAllBtn.hidden !== shouldHide) {
      collapseAllBtn.hidden = shouldHide;
    }
  }
  const collapseObserver = new MutationObserver(syncCollapseAllVisibility);
  collapseObserver.observe(sections, {
    subtree: true,
    attributes: true,
    attributeFilter: ['data-collapsed', 'hidden'],
    childList: true,
  });
  syncCollapseAllVisibility();

  function setOpen(open) {
    state.set({ leftRailOpen: open });
  }

  expandBtn.addEventListener('click',   () => setOpen(true));
  collapseBtn.addEventListener('click', () => setOpen(false));
  backdrop.addEventListener('click',    () => setOpen(false));

  const appMain = document.querySelector('.app-main');
  function applyOpen(open) {
    root.classList.toggle('is-open', open);
    root.classList.toggle('is-collapsed', !open);
    if (appMain) appMain.setAttribute('data-left-open', open ? 'true' : 'false');
    syncRailToggleVisibility(open);
  }
  applyOpen(state.get('leftRailOpen'));
  state.subscribe(s => s.leftRailOpen, applyOpen);

  // Esc dismisses the mobile drawer (overlay over canvas). On desktop
  // the same key would just collapse the rail — opting out so Esc on
  // desktop stays available for the detail panel.
  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape' && state.get('leftRailOpen')
        && matchMedia('(max-width: 768px)').matches) {
      setOpen(false);
    }
  });

  return {
    getContentEl: () => sections,
    addSection: (section) => sections.appendChild(section),
    collapseAll,
  };
}

/**
 * Build a collapsible section for the left rail.
 *
 * Returns `{ root, body }`:
 *   - `root` is the `<section>` element to append into the rail.
 *   - `body` is where you mount your section's content; toggling the
 *     header collapses/expands it via `data-collapsed`.
 *
 * The chevron rotates between ▾ (expanded) and ▸ (collapsed) — matches
 * the ingredient-filter disclosure style.
 */
export function createRailSection({ title, initiallyCollapsed = true, tooltip = '', id = '' } = {}) {
  const root = document.createElement('section');
  root.className = 'rail-section';
  if (id) root.id = id;
  root.dataset.collapsed = initiallyCollapsed ? 'true' : 'false';

  root.innerHTML = `
    <button class="rail-section-toggle" type="button" aria-expanded="${!initiallyCollapsed}">
      <span class="rail-section-chevron" aria-hidden="true">${initiallyCollapsed ? '▸' : '▾'}</span>
      <span class="rail-section-title"></span>
    </button>
    <div class="rail-section-body"></div>
  `;

  const titleEl   = root.querySelector('.rail-section-title');
  const chevronEl = root.querySelector('.rail-section-chevron');
  const toggleEl  = root.querySelector('.rail-section-toggle');
  const bodyEl    = root.querySelector('.rail-section-body');

  titleEl.textContent = title || '';
  /* Tester feedback: the visible "?" glyph on every section header was
   * redundant — hovering the header row already surfaces the same
   * tooltip via the title attribute. Removing the glyph cleans up the
   * rail without losing the help text. */
  if (tooltip) {
    toggleEl.title = tooltip;
  }

  toggleEl.addEventListener('click', () => {
    const collapsed = root.dataset.collapsed === 'true';
    const next = !collapsed;
    root.dataset.collapsed = String(next);
    toggleEl.setAttribute('aria-expanded', String(!next));
    chevronEl.textContent = next ? '▸' : '▾';
  });

  return { root, body: bodyEl };
}

/* The header toggle is the single collapse/expand affordance for the
 * left rail on every viewport. Icon flips with state:
 *   open  → ← (clicking will collapse)
 *   closed → → (clicking will expand)
 */
function syncRailToggleVisibility(railOpen) {
  const railToggle = document.getElementById('rail-toggle');
  if (!railToggle) return;
  const icon = railToggle.querySelector('.rail-toggle-icon') || railToggle;
  icon.textContent = railOpen ? '←' : '→';
  railToggle.setAttribute('aria-label', railOpen ? 'Hide filters' : 'Show filters');
  railToggle.title = railOpen ? 'Hide filters' : 'Show filters';
}
