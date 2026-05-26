/* Phase 40 round 7: Diet + Cuisine filter section (meal-only).
 *
 * Distinct from the left-rail "Dietary restrictions" section (which
 * covers lifestyle restrictions like vegan / gluten-free at the
 * INGREDIENT level): this section filters MEALS by their compatible
 * diet patterns (keto / paleo / mediterranean / etc.) and by cuisine.
 *
 * Only meaningful in Meals view-level — at Ingredients / Categories
 * view, the filter has no effect (the dataset doesn't carry per-item
 * diet / cuisine).
 *
 * State:
 *   state.dietFilter.included    — string[] of DIET keys (keto/paleo/etc).
 *                                  Meal passes iff its diet_compatibility
 *                                  intersects this list (OR).
 *   state.cuisineFilter.included — string[] of exact cuisine labels.
 *                                  Meal passes iff its cuisine is in this list.
 */

import { createRailSection } from './left-rail.js';
import { DIETS } from '../data/schema.js';
import { escapeHtml, escapeAttr } from '../util/dom.js';

export function mountDietCuisineFilter(host, { state, meals = [] }) {
  if (!host) return;

  const { root: section, body } = createRailSection({
    title: 'Filter by diet & cuisine',
    initiallyCollapsed: true,
    tooltip: 'Restrict meals to specific diets (keto, mediterranean, etc.) or cuisines. Only applies in the Meals view.',
  });
  host.appendChild(section);

  const dietOptions = Object.values(DIETS).map(d => ({ value: d.key, label: d.label }));
  const cuisineSet = new Set();
  for (const m of meals) {
    if (m && typeof m.cuisine === 'string' && m.cuisine.trim()) {
      cuisineSet.add(m.cuisine.trim());
    }
  }
  const allCuisines = [...cuisineSet].sort((a, b) => a.localeCompare(b));

  body.classList.add('diet-cuisine-filter');
  body.innerHTML = `
    <p class="diet-cuisine-help muted">
      Affects the Meals view only. Diets and cuisines are treated as
      one flat selection — AND/OR + ANY/ALL apply to every selected
      item regardless of which list it came from.
    </p>
    <div class="filter-modes-row">
      <div class="filter-mode-pair">
        <span class="filter-mode-label muted">Allow extras:</span>
        <div class="filter-scope-toggle seg-group" role="group"
             aria-label="ANY (extras allowed) vs ALL (only the selected)"
             title="ANY — meal's diet_compatibility / cuisine can include items outside your selection. ALL — every diet / cuisine the meal carries must be in your selection (no extras).">
          <button type="button" class="seg-btn seg-btn-sm" data-scope="any">ANY</button>
          <button type="button" class="seg-btn seg-btn-sm" data-scope="all">ALL</button>
        </div>
      </div>
      <div class="filter-mode-pair">
        <span class="filter-mode-label muted">Combine:</span>
        <div class="filter-match-toggle seg-group" role="group"
             aria-label="OR (at least one selected item present) vs AND (every selected item present)"
             title="OR — meal carries at least one selected diet or cuisine. AND — meal carries every selected diet and the selected cuisine.">
          <button type="button" class="seg-btn seg-btn-sm" data-match="any">OR</button>
          <button type="button" class="seg-btn seg-btn-sm" data-match="all">AND</button>
        </div>
      </div>
    </div>

    <div class="diet-cuisine-block" data-block="diet">
      <header class="diet-cuisine-block-head">
        <strong class="diet-cuisine-block-title">Diet</strong>
        <button class="btn-link diet-cuisine-bulk" type="button" data-block="diet"></button>
      </header>
      <ul class="diet-cuisine-list">
        ${dietOptions.map(o => `
          <li class="diet-cuisine-item">
            <label class="diet-cuisine-check">
              <input type="checkbox" data-kind="diet" data-value="${escapeAttr(o.value)}">
              <span>${escapeHtml(o.label)}</span>
            </label>
          </li>
        `).join('')}
      </ul>
    </div>

    <div class="diet-cuisine-block" data-block="cuisine">
      <header class="diet-cuisine-block-head">
        <strong class="diet-cuisine-block-title">Cuisine</strong>
        <button class="btn-link diet-cuisine-bulk" type="button" data-block="cuisine"></button>
      </header>
      <input class="input diet-cuisine-search" type="search"
             placeholder="Search cuisines…" aria-label="Search cuisines">
      <ul class="diet-cuisine-list diet-cuisine-list-cuisine">
        ${allCuisines.map(c => `
          <li class="diet-cuisine-item" data-cuisine="${escapeAttr(c)}">
            <label class="diet-cuisine-check">
              <input type="checkbox" data-kind="cuisine" data-value="${escapeAttr(c)}">
              <span>${escapeHtml(c)}</span>
            </label>
          </li>
        `).join('')}
      </ul>
    </div>
  `;

  const searchEl = body.querySelector('.diet-cuisine-search');
  const cuisineListEl = body.querySelector('.diet-cuisine-list-cuisine');
  const matchGroup = body.querySelector('.filter-match-toggle');
  const scopeGroup = body.querySelector('.filter-scope-toggle');
  const modesRow   = body.querySelector('.filter-modes-row');

  /* Batch 14 follow-up: hide the ENTIRE section outside meals view.
   * Ingredients carry no diet/cuisine fields (0/1362 in the dataset),
   * and the categories view aggregates from ingredients, so neither
   * view can meaningfully apply this filter. Showing an empty,
   * inactive section just adds rail clutter and confuses users.
   * (The earlier Batch 4 behavior only hid the AND/OR row.) */
  function applyViewLevelVisibility() {
    const level = state.get('viewLevel') || 'individual';
    section.hidden = level !== 'meal';
  }
  state.subscribe(s => s.viewLevel, applyViewLevelVisibility);
  applyViewLevelVisibility();

  function refreshToggles() {
    const matchCur = state.get('dietCuisineFilterMatch') || 'all';
    matchGroup.querySelectorAll('[data-match]').forEach(btn => {
      btn.classList.toggle('is-active', btn.dataset.match === matchCur);
    });
    const scopeCur = state.get('dietCuisineFilterScope') || 'any';
    scopeGroup.querySelectorAll('[data-scope]').forEach(btn => {
      btn.classList.toggle('is-active', btn.dataset.scope === scopeCur);
    });
  }
  matchGroup.addEventListener('click', (ev) => {
    const btn = ev.target.closest('[data-match]');
    if (!btn) return;
    state.set({ dietCuisineFilterMatch: btn.dataset.match });
  });
  scopeGroup.addEventListener('click', (ev) => {
    const btn = ev.target.closest('[data-scope]');
    if (!btn) return;
    state.set({ dietCuisineFilterScope: btn.dataset.scope });
  });
  state.subscribe(s => s.dietCuisineFilterMatch, refreshToggles);
  state.subscribe(s => s.dietCuisineFilterScope, refreshToggles);
  refreshToggles();

  function refresh() {
    const dietIncluded    = new Set((state.get('dietFilter')    || {}).included || []);
    const cuisineIncluded = new Set((state.get('cuisineFilter') || {}).included || []);
    body.querySelectorAll('input[type="checkbox"][data-kind]').forEach(cb => {
      const set = cb.dataset.kind === 'diet' ? dietIncluded : cuisineIncluded;
      cb.checked = set.has(cb.dataset.value);
    });
    // Bulk-toggle labels per block.
    body.querySelectorAll('.diet-cuisine-bulk').forEach(btn => {
      const block = btn.dataset.block;
      const total = block === 'diet' ? dietOptions.length : allCuisines.length;
      const checked = block === 'diet' ? dietIncluded.size : cuisineIncluded.size;
      const majority = checked * 2 >= total;
      btn.textContent = majority ? 'Uncheck all' : 'Check all';
      btn.dataset.action = majority ? 'uncheck' : 'check';
    });
  }

  body.addEventListener('change', (ev) => {
    const cb = ev.target;
    if (!(cb instanceof HTMLInputElement) || !cb.dataset.kind) return;
    const kind = cb.dataset.kind;
    const value = cb.dataset.value;
    const slotKey = kind === 'diet' ? 'dietFilter' : 'cuisineFilter';
    const cur = new Set(((state.get(slotKey) || {}).included) || []);
    if (cb.checked) cur.add(value); else cur.delete(value);
    state.set({ [slotKey]: { included: [...cur] } });
  });

  body.addEventListener('click', (ev) => {
    const btn = ev.target.closest('.diet-cuisine-bulk');
    if (!btn) return;
    const block = btn.dataset.block;
    const action = btn.dataset.action;
    if (block === 'diet') {
      state.set({
        dietFilter: { included: action === 'check' ? dietOptions.map(o => o.value) : [] },
      });
    } else {
      state.set({
        cuisineFilter: { included: action === 'check' ? allCuisines.slice() : [] },
      });
    }
  });

  searchEl.addEventListener('input', () => {
    const q = searchEl.value.trim().toLowerCase();
    cuisineListEl.querySelectorAll('.diet-cuisine-item[data-cuisine]').forEach(li => {
      const c = li.dataset.cuisine || '';
      li.hidden = q ? !c.toLowerCase().includes(q) : false;
    });
  });

  refresh();
  state.subscribe(s => s.dietFilter,    refresh);
  state.subscribe(s => s.cuisineFilter, refresh);
}

