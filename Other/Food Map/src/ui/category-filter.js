/* Phase 40 round 4: global Categories filter section.
 *
 * Tri-state per category. Applies in every view-level:
 *   Ingredients view — hides ingredients whose `category` isn't in `included`
 *                      (when included non-empty) or that match `excluded`.
 *   Categories view — same logic against the aggregate's category name.
 *   Meals view — meal must reference at least one included category and
 *                no excluded ones. With the global `ingredientFilterMatch`
 *                set to 'all', meal must reference EVERY included category.
 *
 * State: state.categoryFilter = { included: string[], excluded: string[] }
 * Empty arrays = no filter contribution.
 */

import { createRailSection } from './left-rail.js';
import { escapeHtml, escapeAttr } from '../util/dom.js';

export function mountCategoryFilter(host, { state, ingredients }) {
  if (!host) return;

  const { root: section, body } = createRailSection({
    title: 'Filter by category',
    initiallyCollapsed: true,
    tooltip: 'Include or exclude ingredients by their food category (e.g. Poultry, Whole grains). Affects every view.',
  });
  host.appendChild(section);

  const allCategories = Array.from(new Set(ingredients.map(i => i.category)))
    .filter(Boolean)
    .sort();

  body.classList.add('category-filter');
  body.innerHTML = `
    <div class="category-filter-controls">
      <input class="input category-filter-search" type="search"
             placeholder="Search categories…" aria-label="Search categories">
    </div>
    <div class="category-filter-bulk-row">
      <button class="btn-link category-filter-bulk" type="button"></button>
    </div>
    <div class="filter-modes-row">
      <div class="filter-mode-pair">
        <span class="filter-mode-label muted">Allow extras:</span>
        <div class="filter-scope-toggle seg-group" role="group"
             aria-label="ANY (extras allowed) vs ALL (only the included categories)"
             title="ANY — items can include other categories too. ALL — items must include ONLY these categories (no extras).">
          <button type="button" class="seg-btn seg-btn-sm" data-scope="any">ANY</button>
          <button type="button" class="seg-btn seg-btn-sm" data-scope="all">ALL</button>
        </div>
      </div>
      <div class="filter-mode-pair">
        <span class="filter-mode-label muted">Combine:</span>
        <div class="filter-match-toggle seg-group" role="group"
             aria-label="OR (at least one) vs AND (every one)"
             title="OR — at least one included category must be referenced. AND — every included category must be referenced.">
          <button type="button" class="seg-btn seg-btn-sm" data-match="any">OR</button>
          <button type="button" class="seg-btn seg-btn-sm" data-match="all">AND</button>
        </div>
      </div>
    </div>
    <p class="category-filter-summary muted" aria-live="polite"></p>
    <div class="category-filter-list meal-filter-options is-tri" role="list"></div>
  `;
  const searchEl   = body.querySelector('.category-filter-search');
  const bulkBtn    = body.querySelector('.category-filter-bulk');
  const matchGroup = body.querySelector('.filter-match-toggle');
  const scopeGroup = body.querySelector('.filter-scope-toggle');
  const modesRow   = body.querySelector('.filter-modes-row');
  const summary    = body.querySelector('.category-filter-summary');
  const listEl     = body.querySelector('.category-filter-list');

  /* Batch 4 (item 9): hide AND/OR + ANY/ALL toggles at Ingredients
   * and Categories views — each individual item / each category
   * aggregate has exactly one category, so the toggles collapse to a
   * single answer. Only Meals view actually composes multiple
   * categories per item, so that's where the toggles are meaningful. */
  function applyViewLevelVisibility() {
    const level = state.get('viewLevel') || 'individual';
    if (modesRow) modesRow.hidden = level !== 'meal';
  }
  state.subscribe(s => s.viewLevel, applyViewLevelVisibility);
  applyViewLevelVisibility();

  /* Phase 40 round 9: AND/OR (match) + ANY/ALL (scope) toggles. */
  function refreshToggles() {
    const matchCur = state.get('categoryFilterMatch') || 'any';
    matchGroup.querySelectorAll('[data-match]').forEach(btn => {
      btn.classList.toggle('is-active', btn.dataset.match === matchCur);
    });
    const scopeCur = state.get('categoryFilterScope') || 'any';
    scopeGroup.querySelectorAll('[data-scope]').forEach(btn => {
      btn.classList.toggle('is-active', btn.dataset.scope === scopeCur);
    });
  }
  matchGroup.addEventListener('click', (ev) => {
    const btn = ev.target.closest('[data-match]');
    if (!btn) return;
    state.set({ categoryFilterMatch: btn.dataset.match });
  });
  scopeGroup.addEventListener('click', (ev) => {
    const btn = ev.target.closest('[data-scope]');
    if (!btn) return;
    state.set({ categoryFilterScope: btn.dataset.scope });
  });
  state.subscribe(s => s.categoryFilterMatch, refreshToggles);
  state.subscribe(s => s.categoryFilterScope, refreshToggles);
  refreshToggles();

  function read() {
    const f = state.get('categoryFilter') || {};
    return {
      included: new Set(Array.isArray(f.included) ? f.included : []),
      excluded: new Set(Array.isArray(f.excluded) ? f.excluded : []),
    };
  }
  function write(included, excluded) {
    state.set({
      categoryFilter: { included: [...included], excluded: [...excluded] },
    });
  }

  function rowHtml(category, included, excluded) {
    const s = included.has(category) ? 'include'
            : excluded.has(category) ? 'exclude' : 'off';
    return `
      <div class="meal-filter-option meal-filter-option-tri"
           data-value="${escapeAttr(category)}" data-state="${s}" role="listitem">
        <span class="meal-filter-option-label">${escapeHtml(category)}</span>
        <span class="tri-state-controls" role="group" aria-label="${escapeAttr(category)} include or exclude">
          <button class="tri-state-btn" type="button" data-action="include"
                  aria-pressed="${s === 'include'}" title="Require — items must reference this category">+</button>
          <button class="tri-state-btn" type="button" data-action="exclude"
                  aria-pressed="${s === 'exclude'}" title="Disallow — hide items referencing this category">−</button>
        </span>
      </div>`;
  }

  function paint() {
    const { included, excluded } = read();
    const q = (searchEl.value || '').trim().toLowerCase();
    const shown = q ? allCategories.filter(c => c.toLowerCase().includes(q)) : allCategories;

    // Pin currently-selected categories to the top (matches the
    // Modify Meals pattern). Selection ignores the search filter so
    // it's always visible.
    const pinned = allCategories.filter(c => included.has(c) || excluded.has(c));
    const pinnedHtml = pinned.length
      ? `<div class="compose-meals-pinned" role="group" aria-label="Active selection">
           ${pinned.map(c => rowHtml(c, included, excluded)).join('')}
         </div>
         <div class="compose-meals-divider" aria-hidden="true">all categories</div>`
      : '';
    const fullHtml = shown.length
      ? shown.map(c => rowHtml(c, included, excluded)).join('')
      : '<p class="muted" style="padding: 8px 4px 4px;">No matches</p>';

    listEl.innerHTML = pinnedHtml + fullHtml;

    const incN = included.size;
    const excN = excluded.size;
    summary.textContent = (incN || excN)
      ? `${incN ? `${incN}+` : ''}${incN && excN ? ' / ' : ''}${excN ? `${excN}−` : ''}`
      : 'No category filter active.';

    // Phase 40 round 3 pattern: smart Check-all / Uncheck-all reads as
    // "include all" / "clear all" here. Majority included → "Clear all";
    // otherwise → "Include all".
    const majorityIncluded = incN * 2 >= allCategories.length;
    bulkBtn.textContent = majorityIncluded ? 'Clear all' : 'Include all';
    bulkBtn.dataset.action = majorityIncluded ? 'clear' : 'include-all';
  }

  listEl.addEventListener('click', (ev) => {
    const btn = ev.target.closest('.tri-state-btn');
    if (!btn) return;
    const row = btn.closest('.meal-filter-option-tri');
    if (!row) return;
    const value  = row.dataset.value;
    const action = btn.dataset.action;
    const current = row.dataset.state;
    const nextState = current === action ? 'off' : action;

    const { included, excluded } = read();
    included.delete(value);
    excluded.delete(value);
    if (nextState === 'include') included.add(value);
    if (nextState === 'exclude') excluded.add(value);
    write(included, excluded);
  });

  searchEl.addEventListener('input', paint);

  bulkBtn.addEventListener('click', () => {
    if (bulkBtn.dataset.action === 'clear') {
      write(new Set(), new Set());
    } else {
      write(new Set(allCategories), new Set());
    }
  });

  paint();
  state.subscribe(s => s.categoryFilter, paint);
}

