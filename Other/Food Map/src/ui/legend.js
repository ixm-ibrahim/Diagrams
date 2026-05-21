/* Corner legend.
 *
 * Phase 4 (original): additive RGB Animal/Plant/Dairy guide.
 * Phase 7: Score-mode gradient (green→red) overlays when Score mode is on.
 * Phase 13.5 rounds 3–5: secondary blends, food_group scheme toggle,
 *   hue-ordered list, fixed-shape body.
 * Phase 13.75: each row is a checkbox — unchecking filters ingredients
 *   in that channel/group out of the active set. Filtered ingredients
 *   render distinctly (smaller + dimmer) so they stay locatable but
 *   are obviously deprioritized.
 */

import { FOOD_GROUPS_BY_HUE, FOOD_GROUP_COLORS } from '../data/schema.js';

const RGB_PRIMARIES = [
  { key: 'animal', label: 'Animal', css: 'rgb(255, 0, 0)' },
  { key: 'plant',  label: 'Plant',  css: 'rgb(0, 200, 0)' },
  { key: 'dairy',  label: 'Dairy',  css: 'rgb(40, 80, 255)' },
];

const RGB_COMBINATIONS = [
  { label: 'Animal + plant', css: 'rgb(230, 200, 0)' },
  { label: 'Plant + dairy',  css: 'rgb(0, 200, 220)' },
  { label: 'Animal + dairy', css: 'rgb(200, 0, 220)' },
  { label: 'All three (near-white)', css: null, swatchClass: 'legend-swatch-tri' },
];

export function mountLegend(root, { state } = {}) {
  if (!root) return;
  root.removeAttribute('hidden');

  function open()    { state && state.set({ legendOpen: true });  }
  function close()   { state && state.set({ legendOpen: false }); }
  function isOpen()  { return state ? state.get('legendOpen') !== false : true; }
  function scheme()  { return state ? (state.get('colorScheme') || 'rgb') : 'rgb'; }
  function mode()    { return state ? (state.get('thresholdMode') || 'filter') : 'filter'; }
  function setScheme(s) { state && state.set({ colorScheme: s }); }

  function hiddenSet() {
    const lh = state ? (state.get('legendHidden') || {}) : {};
    const arr = lh[scheme()] || [];
    return new Set(arr);
  }
  function toggleHidden(key) {
    if (!state) return;
    const lh = { ...(state.get('legendHidden') || {}) };
    const sch = scheme();
    const arr = Array.isArray(lh[sch]) ? [...lh[sch]] : [];
    const idx = arr.indexOf(key);
    if (idx >= 0) arr.splice(idx, 1);
    else arr.push(key);
    lh[sch] = arr;
    state.set({ legendHidden: lh });
  }
  /* Phase 40 round 3: smart Check-all / Uncheck-all. Flips its label
   * based on majority — "Uncheck all" when >=half are checked,
   * "Check all" otherwise. Acts on whichever scheme is active. */
  function setAllHidden(keys, hide) {
    if (!state) return;
    const lh = { ...(state.get('legendHidden') || {}) };
    const sch = scheme();
    lh[sch] = hide ? keys.slice() : [];
    state.set({ legendHidden: lh });
  }

  function render() {
    if (!isOpen()) { renderCollapsed(root, open); return; }
    if (mode() === 'score') { renderScore(root, close); return; }
    if (scheme() === 'food_group') {
      renderFoodGroups(root, close, setScheme, hiddenSet(), toggleHidden, setAllHidden);
    } else {
      renderRgb(root, close, setScheme, hiddenSet(), toggleHidden, setAllHidden);
    }
  }

  render();
  if (state) {
    state.subscribe(s => s.thresholdMode, render);
    state.subscribe(s => s.colorScheme,   render);
    state.subscribe(s => s.legendOpen,    render);
    state.subscribe(s => s.legendHidden,  render);
  }

  // Phase 13.75 round 6: publish the legend's actual rendered width as
  // a CSS variable on :root. The axis-controls panel reads it to park
  // flush against the legend's left edge — when the legend collapses
  // from its 220px expanded form down to a small "Legend" pill, the
  // axis-controls panel slides over to match instead of leaving a gap.
  const ro = new ResizeObserver(() => {
    document.documentElement.style.setProperty(
      '--legend-width',
      `${Math.round(root.offsetWidth)}px`
    );
  });
  ro.observe(root);
}

function schemeToggleHtml(current) {
  return `
    <div class="legend-scheme seg-group" role="group" aria-label="Color scheme">
      <button type="button" class="seg-btn ${current === 'rgb' ? 'is-active' : ''}"
              data-scheme="rgb" title="Color by animal / plant / dairy mix">A/P/D</button>
      <button type="button" class="seg-btn ${current === 'food_group' ? 'is-active' : ''}"
              data-scheme="food_group" title="Color by food_group">Food group</button>
    </div>
  `;
}

function wireSchemeToggle(root, setScheme) {
  root.querySelectorAll('.legend-scheme [data-scheme]').forEach(btn => {
    btn.addEventListener('click', () => setScheme(btn.dataset.scheme));
  });
}

function checkboxItemHtml(key, label, swatchHtml, hidden) {
  return `
    <li class="legend-item${hidden ? ' is-hidden' : ''}">
      <label class="legend-check">
        <input type="checkbox" data-legend-key="${escapeAttr(key)}" ${hidden ? '' : 'checked'}>
        ${swatchHtml}
        <span class="legend-item-label">${escapeHtml(label)}</span>
      </label>
    </li>
  `;
}

function wireCheckboxes(root, toggle) {
  root.querySelectorAll('input[data-legend-key]').forEach(cb => {
    cb.addEventListener('change', () => toggle(cb.dataset.legendKey));
  });
}

function bulkToggleHtml(checkedCount, totalCount) {
  // Majority-checked → offer "Uncheck all"; otherwise → "Check all".
  const majorityChecked = checkedCount * 2 >= totalCount;
  const action = majorityChecked ? 'uncheck' : 'check';
  const label  = majorityChecked ? 'Uncheck all' : 'Check all';
  return `<button class="legend-bulk-toggle btn-link" type="button"
                  data-bulk-action="${action}">${label}</button>`;
}

function renderRgb(root, onClose, setScheme, hidden, toggleHidden, setAllHidden) {
  root.classList.remove('legend-collapsed');
  const swatch = (css, cls) =>
    `<span class="legend-swatch${cls ? ' ' + cls : ''}" style="${css ? `background: ${css};` : ''}"></span>`;
  const allKeys = RGB_PRIMARIES.map(p => p.key);
  const checkedCount = allKeys.filter(k => !hidden.has(k)).length;
  const primaryRows = RGB_PRIMARIES.map(p =>
    checkboxItemHtml(p.key, p.label, swatch(p.css), hidden.has(p.key))).join('');
  // Combinations are illustrative only — no checkbox semantics (they're
  // derived from the primaries). Render as plain rows.
  const comboRows = RGB_COMBINATIONS.map(c => `
    <li class="legend-item legend-item-static">
      <span class="legend-check-spacer" aria-hidden="true"></span>
      ${swatch(c.css, c.swatchClass)}
      <span class="legend-item-label">${escapeHtml(c.label)}</span>
    </li>`).join('');
  root.innerHTML = `
    <div class="legend-header">
      <strong class="legend-title">Color guide</strong>
      <button class="legend-close" type="button" aria-label="Hide color guide">×</button>
    </div>
    ${schemeToggleHtml('rgb')}
    <div class="legend-body">
      <div class="legend-section-row">
        <p class="legend-section-title muted">Individual</p>
        ${bulkToggleHtml(checkedCount, allKeys.length)}
      </div>
      <ul class="legend-list">${primaryRows}</ul>
      <p class="legend-section-title muted">Combinations</p>
      <ul class="legend-list">${comboRows}</ul>
    </div>
    <p class="legend-note muted">Uncheck a row to hide that group from view.</p>
  `;
  root.querySelector('.legend-close').addEventListener('click', onClose);
  wireSchemeToggle(root, setScheme);
  wireCheckboxes(root, toggleHidden);
  wireBulkToggle(root, allKeys, setAllHidden);
}

function renderFoodGroups(root, onClose, setScheme, hidden, toggleHidden, setAllHidden) {
  root.classList.remove('legend-collapsed');
  const swatch = (rgb) => {
    const css = `rgb(${Math.round(rgb[0]*255)}, ${Math.round(rgb[1]*255)}, ${Math.round(rgb[2]*255)})`;
    return `<span class="legend-swatch" style="background: ${css};"></span>`;
  };
  const allKeys = FOOD_GROUPS_BY_HUE.slice();
  const checkedCount = allKeys.filter(k => !hidden.has(k)).length;
  const items = FOOD_GROUPS_BY_HUE.map(g =>
    checkboxItemHtml(g, g, swatch(FOOD_GROUP_COLORS[g] || [0.5, 0.5, 0.5]), hidden.has(g))).join('');
  root.innerHTML = `
    <div class="legend-header">
      <strong class="legend-title">Color guide</strong>
      <button class="legend-close" type="button" aria-label="Hide color guide">×</button>
    </div>
    ${schemeToggleHtml('food_group')}
    <div class="legend-body">
      <div class="legend-section-row">
        <span class="muted legend-section-title">Food groups</span>
        ${bulkToggleHtml(checkedCount, allKeys.length)}
      </div>
      <ul class="legend-list">${items}</ul>
    </div>
    <p class="legend-note muted">Uncheck a row to hide that group from view.</p>
  `;
  root.querySelector('.legend-close').addEventListener('click', onClose);
  wireSchemeToggle(root, setScheme);
  wireCheckboxes(root, toggleHidden);
  wireBulkToggle(root, allKeys, setAllHidden);
}

function wireBulkToggle(root, allKeys, setAllHidden) {
  const btn = root.querySelector('.legend-bulk-toggle');
  if (!btn) return;
  btn.addEventListener('click', () => {
    const hide = btn.dataset.bulkAction === 'uncheck';
    setAllHidden(allKeys, hide);
  });
}

function renderScore(root, onClose) {
  root.classList.remove('legend-collapsed');
  root.innerHTML = `
    <div class="legend-header">
      <strong class="legend-title">Distance from targets</strong>
      <button class="legend-close" type="button" aria-label="Hide color guide">×</button>
    </div>
    <div class="legend-gradient" aria-hidden="true"></div>
    <div class="legend-gradient-labels">
      <span>Close</span>
      <span class="muted">Far</span>
    </div>
    <p class="legend-note muted">Score = RMS distance from each nutrient's target.</p>
  `;
  root.querySelector('.legend-close').addEventListener('click', onClose);
}

function renderCollapsed(root, onExpand) {
  root.classList.add('legend-collapsed');
  root.innerHTML = `<button class="legend-expand" type="button">Legend</button>`;
  root.querySelector('.legend-expand').addEventListener('click', onExpand);
}

function escapeHtml(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
function escapeAttr(s) { return escapeHtml(s); }
