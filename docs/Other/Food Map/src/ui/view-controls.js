/* Header-mounted view controls — split into two halves so the layout
 * can place them on opposite sides of the canvas/table area.
 *
 *   mountViewLevel   — Ingredients | Categories | Meals (applies in 3D AND table)
 *   mount3DControls  — Perspective | Orthographic + X | Y | Z | ⟲ (3D only)
 *
 * Both subscribe to their respective state slices and stay in sync. The
 * snap buttons fire `onSnap('x'|'y'|'z'|'free')` so the caller can move
 * the camera; nothing about scene/camera lives in this module.
 */

const LEVEL_OPTIONS = [
  { value: 'individual', label: 'Ingredients' },
  { value: 'category',   label: 'Categories' },
  { value: 'meal',       label: 'Meals' },
];

// Phase 13.5 round 7: when viewLevel === 'category', the user picks
// WHICH identity field drives the grouping via this dropdown.
const CATEGORY_GROUP_OPTIONS = [
  { value: 'food_group',  label: 'By food group' },
  { value: 'category',    label: 'By category' },
  { value: 'subcategory', label: 'By subcategory' },
];

const CAMERA_OPTIONS = [
  { value: 'perspective',  label: 'Perspective' },
  { value: 'orthographic', label: 'Orthographic' },
];

const SNAP_OPTIONS = [
  { value: 'x',    label: 'X' },
  { value: 'y',    label: 'Y' },
  { value: 'z',    label: 'Z' },
  { value: 'free', label: '⟲', title: 'Default isometric view' },
];

export function mountViewLevel(root, { state }) {
  if (!root) return;
  // Phase 13.5 round 7: the "Categories" button is a dropdown — click
  // opens a popover with food_group / category / subcategory options.
  // Clicking an option sets viewLevel='category' and categoryGroupBy.
  // Ingredients and Meals are still flat seg-buttons.
  root.innerHTML = `
    <div class="seg-group" role="group" aria-label="Display level">
      <button type="button" class="seg-btn" data-group="viewLevel" data-value="individual">Ingredients</button>
      <div class="seg-btn-dropdown" data-group="viewLevel" data-value="category">
        <button type="button" class="seg-btn seg-btn-category" aria-haspopup="menu" aria-expanded="false">
          <span class="seg-btn-label">Categories</span>
          <span class="seg-btn-chev" aria-hidden="true">▾</span>
        </button>
        <div class="seg-dropdown" role="menu" hidden>
          ${CATEGORY_GROUP_OPTIONS.map(o => `
            <button type="button" class="seg-dropdown-item" role="menuitem" data-group-by="${o.value}">
              ${o.label}
            </button>`).join('')}
        </div>
      </div>
      <button type="button" class="seg-btn" data-group="viewLevel" data-value="meal">Meals</button>
    </div>
  `;

  const dropdown    = root.querySelector('.seg-btn-dropdown');
  const dropdownBtn = root.querySelector('.seg-btn-category');
  const menu        = root.querySelector('.seg-dropdown');
  const labelEl     = root.querySelector('.seg-btn-label');

  function openMenu() {
    // Position the fixed menu just below the Categories button. Done at
    // open-time because window resize / camera changes don't trigger a
    // re-layout for fixed elements.
    const rect = dropdownBtn.getBoundingClientRect();
    menu.style.left = `${Math.round(rect.left)}px`;
    menu.style.top  = `${Math.round(rect.bottom + 4)}px`;
    menu.hidden = false;
    dropdownBtn.setAttribute('aria-expanded', 'true');
  }
  function closeMenu() {
    menu.hidden = true;
    dropdownBtn.setAttribute('aria-expanded', 'false');
  }

  function categoryLabel() {
    const groupBy = state.get('categoryGroupBy') || 'category';
    const opt = CATEGORY_GROUP_OPTIONS.find(o => o.value === groupBy);
    // Strip the "By " prefix for the button itself; only the menu uses
    // the full "By X" phrasing.
    return opt ? opt.label.replace(/^By\s+/i, '').replace(/^./, c => c.toUpperCase()) : 'Categories';
  }

  function syncActive() {
    const viewLevel = state.get('viewLevel');
    root.querySelectorAll('[data-group="viewLevel"]').forEach(el => {
      el.classList.toggle('is-active', el.dataset.value === viewLevel);
    });
    if (labelEl) {
      labelEl.textContent = viewLevel === 'category' ? categoryLabel() : 'Categories';
    }
    const groupBy = state.get('categoryGroupBy') || 'category';
    menu.querySelectorAll('.seg-dropdown-item').forEach(item => {
      item.classList.toggle('is-active', item.dataset.groupBy === groupBy);
    });
  }

  // Flat buttons (Ingredients, Meals) just set viewLevel.
  root.addEventListener('click', (ev) => {
    const flatBtn = ev.target.closest('.seg-btn[data-group="viewLevel"]:not(.seg-btn-category)');
    if (flatBtn) {
      const value = flatBtn.dataset.value;
      if (value && state.get('viewLevel') !== value) state.set({ viewLevel: value });
      closeMenu();
      return;
    }
    // Categories button toggles the dropdown.
    if (ev.target.closest('.seg-btn-category')) {
      if (menu.hidden) openMenu(); else closeMenu();
      return;
    }
    // Picking a menu item commits both viewLevel and categoryGroupBy.
    const item = ev.target.closest('.seg-dropdown-item');
    if (item) {
      const groupBy = item.dataset.groupBy;
      state.set({ viewLevel: 'category', categoryGroupBy: groupBy });
      closeMenu();
      return;
    }
  });

  // Dismiss on outside click / Escape / viewport resize (the fixed
  // coords go stale once the button moves). Phase 40: pointerdown
  // (capture) so an in-menu re-render doesn't detach ev.target before
  // the containment check.
  document.addEventListener('pointerdown', (ev) => {
    if (!dropdown.contains(ev.target) && !menu.contains(ev.target)) closeMenu();
  }, true);
  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape') closeMenu();
  });
  window.addEventListener('resize', closeMenu);

  state.subscribe(s => s.viewLevel,         syncActive);
  state.subscribe(s => s.categoryGroupBy,   syncActive);
  syncActive();
}

export function mount3DControls(root, { state, onSnap }) {
  if (!root) return;
  root.innerHTML = `
    <div class="seg-group" role="group" aria-label="Camera projection">
      ${CAMERA_OPTIONS.map(o =>
        `<button type="button" class="seg-btn" data-group="cameraMode" data-value="${o.value}">${o.label}</button>`).join('')}
    </div>
    <div class="seg-group seg-group-snap" role="group" aria-label="Snap camera to axis">
      ${SNAP_OPTIONS.map(o =>
        `<button type="button" class="seg-btn seg-btn-snap" data-action="snap" data-value="${o.value}"${o.title ? ` title="${o.title}"` : ''}>${o.label}</button>`).join('')}
    </div>
    <button type="button" class="seg-btn axis-labels-toggle" data-action="toggle-axis-labels"
            aria-pressed="true" title="Hide axis labels (so they don't block dots)">
      <span aria-hidden="true">Aa</span>
    </button>
  `;
  // Phase 13.75 refinement: the capture-thresholds button moved into
  // the new axis-controls panel (where it has a proper text label and
  // sits beside the per-axis pan/zoom controls).

  function syncActive() {
    const cameraMode = state.get('cameraMode');
    root.querySelectorAll('.seg-btn[data-group="cameraMode"]').forEach(btn => {
      btn.classList.toggle('is-active', btn.dataset.value === cameraMode);
    });
    const labelsBtn = root.querySelector('.axis-labels-toggle');
    if (labelsBtn) {
      const visible = state.get('axisLabelsVisible') !== false;
      labelsBtn.classList.toggle('is-active', visible);
      labelsBtn.setAttribute('aria-pressed', String(visible));
      labelsBtn.title = visible
        ? 'Hide axis labels (so they don’t block dots)'
        : 'Show axis labels';
    }
  }

  root.addEventListener('click', (ev) => {
    const btn = ev.target.closest('.seg-btn, .axis-labels-toggle');
    if (!btn) return;
    if (btn.dataset.action === 'snap') {
      onSnap?.(btn.dataset.value);
      return;
    }
    if (btn.dataset.action === 'toggle-axis-labels') {
      state.set({ axisLabelsVisible: !(state.get('axisLabelsVisible') !== false) });
      return;
    }
    const value = btn.dataset.value;
    if (value && state.get('cameraMode') !== value) state.set({ cameraMode: value });
  });

  state.subscribe(s => s.cameraMode,        syncActive);
  state.subscribe(s => s.axisLabelsVisible, syncActive);
  syncActive();
}
