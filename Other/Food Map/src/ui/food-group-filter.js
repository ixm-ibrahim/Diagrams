/* Phase 40 round 4 / Batch 4 rework: global Food groups filter section.
 *
 * Tri-state per food group (include +, exclude −, off), mirroring the
 * categories filter. Plus AND/OR (match) and ANY/ALL (scope) toggles
 * that compose the same way as the other section-level filters:
 *
 *   match=any (OR)  — aggregate references at least one included group
 *   match=all (AND) — aggregate references EVERY included group
 *   scope=any       — aggregate may also reference groups not in the
 *                     selection (extras allowed)
 *   scope=all       — aggregate's food_groups must be a SUBSET of the
 *                     selection (no extras)
 *
 * At Ingredients and Categories view the toggles collapse (each item
 * has exactly one food_group, so AND vs OR and ANY vs ALL produce the
 * same answer) — the toggle row hides for those views. The filter
 * itself still applies via included / excluded.
 *
 * State:
 *   state.foodGroupFilter      = { included: string[], excluded: string[] }
 *   state.foodGroupFilterMatch = 'any' | 'all'
 *   state.foodGroupFilterScope = 'any' | 'all'
 */

import { createRailSection } from './left-rail.js';
import { FOOD_GROUPS } from '../data/schema.js';
import { escapeHtml, escapeAttr } from '../util/dom.js';

export function mountFoodGroupFilter(host, { state }) {
  if (!host) return;

  const { root: section, body } = createRailSection({
    title: 'Filter by food group',
    initiallyCollapsed: true,
    tooltip: 'Include or exclude food groups (e.g. Vegetables, Dairy). Affects every view; at Meals view, the AND/OR and ANY/ALL toggles let you compose how a meal\'s constituent groups satisfy your selection.',
  });
  host.appendChild(section);

  const allGroups = [...FOOD_GROUPS].sort((a, b) => a.localeCompare(b));

  body.classList.add('food-group-filter');
  body.innerHTML = `
    <p class="food-group-filter-help muted">
      Click <strong>+</strong> to require a group, <strong>−</strong> to hide it.
      At Meals view, use AND/OR + ANY/ALL to compose what counts as a match.
    </p>
    <div class="food-group-filter-bulk-row">
      <button class="btn-link food-group-filter-bulk" type="button"></button>
      <span class="food-group-filter-summary muted" aria-live="polite"></span>
    </div>
    <div class="filter-modes-row">
      <div class="filter-mode-pair">
        <span class="filter-mode-label muted">Allow extras:</span>
        <div class="filter-scope-toggle seg-group" role="group"
             aria-label="ANY (extras allowed) vs ALL (only the included groups)"
             title="ANY — meals can include other food groups too. ALL — meal must contain ONLY the selected groups.">
          <button type="button" class="seg-btn seg-btn-sm" data-scope="any">ANY</button>
          <button type="button" class="seg-btn seg-btn-sm" data-scope="all">ALL</button>
        </div>
      </div>
      <div class="filter-mode-pair">
        <span class="filter-mode-label muted">Combine:</span>
        <div class="filter-match-toggle seg-group" role="group"
             aria-label="OR (at least one) vs AND (every one)"
             title="OR — meal contains at least one included group. AND — meal contains every included group.">
          <button type="button" class="seg-btn seg-btn-sm" data-match="any">OR</button>
          <button type="button" class="seg-btn seg-btn-sm" data-match="all">AND</button>
        </div>
      </div>
    </div>
    <div class="food-group-filter-list meal-filter-options is-tri" role="list">
      ${allGroups.map(g => rowHtml(g, new Set(), new Set())).join('')}
    </div>
  `;
  const bulkBtn    = body.querySelector('.food-group-filter-bulk');
  const summary    = body.querySelector('.food-group-filter-summary');
  const matchGroup = body.querySelector('.filter-match-toggle');
  const scopeGroup = body.querySelector('.filter-scope-toggle');
  const modesRow   = body.querySelector('.filter-modes-row');
  const listEl     = body.querySelector('.food-group-filter-list');

  function read() {
    const f = state.get('foodGroupFilter') || {};
    return {
      included: new Set(Array.isArray(f.included) ? f.included : []),
      excluded: new Set(Array.isArray(f.excluded) ? f.excluded : []),
    };
  }
  function write(included, excluded) {
    state.set({
      foodGroupFilter: { included: [...included], excluded: [...excluded] },
    });
  }

  function rowHtml(group, included, excluded) {
    const s = included.has(group) ? 'include'
            : excluded.has(group) ? 'exclude' : 'off';
    return `
      <div class="meal-filter-option meal-filter-option-tri"
           data-value="${escapeAttr(group)}" data-state="${s}" role="listitem">
        <span class="meal-filter-option-label">${escapeHtml(group)}</span>
        <span class="tri-state-controls" role="group"
              aria-label="${escapeAttr(group)} include or exclude">
          <button class="tri-state-btn" type="button" data-action="include"
                  aria-pressed="${s === 'include'}"
                  title="Require — items must reference this food group">+</button>
          <button class="tri-state-btn" type="button" data-action="exclude"
                  aria-pressed="${s === 'exclude'}"
                  title="Disallow — hide items in this food group">−</button>
        </span>
      </div>`;
  }

  function paint() {
    const { included, excluded } = read();
    listEl.innerHTML = allGroups.map(g => rowHtml(g, included, excluded)).join('');
    const incN = included.size;
    const excN = excluded.size;
    summary.textContent = (incN || excN)
      ? `${incN ? `${incN}+` : ''}${incN && excN ? ' / ' : ''}${excN ? `${excN}−` : ''}`
      : 'No food-group filter active.';
    /* Smart bulk-toggle. Mirrors the categories filter: majority included
     * → "Clear all"; otherwise → "Include all". Excludes don't enter the
     * majority calculation — the bulk button only operates on includes. */
    const majorityIncluded = incN * 2 >= allGroups.length;
    bulkBtn.textContent = majorityIncluded ? 'Clear all' : 'Include all';
    bulkBtn.dataset.action = majorityIncluded ? 'clear' : 'include-all';
  }

  /* match / scope toggle wiring. Both default to 'any'. */
  function refreshToggles() {
    const matchCur = state.get('foodGroupFilterMatch') || 'any';
    matchGroup.querySelectorAll('[data-match]').forEach(btn => {
      btn.classList.toggle('is-active', btn.dataset.match === matchCur);
    });
    const scopeCur = state.get('foodGroupFilterScope') || 'any';
    scopeGroup.querySelectorAll('[data-scope]').forEach(btn => {
      btn.classList.toggle('is-active', btn.dataset.scope === scopeCur);
    });
  }
  matchGroup.addEventListener('click', (ev) => {
    const btn = ev.target.closest('[data-match]');
    if (!btn) return;
    state.set({ foodGroupFilterMatch: btn.dataset.match });
  });
  scopeGroup.addEventListener('click', (ev) => {
    const btn = ev.target.closest('[data-scope]');
    if (!btn) return;
    state.set({ foodGroupFilterScope: btn.dataset.scope });
  });
  state.subscribe(s => s.foodGroupFilterMatch, refreshToggles);
  state.subscribe(s => s.foodGroupFilterScope, refreshToggles);

  /* View-level toggle visibility. AND/OR + ANY/ALL only have meaning when
   * an aggregate can carry MULTIPLE food groups — at Ingredients view
   * each ingredient has exactly one food_group, and at Categories view
   * each aggregate is a single category (typically one food_group). Only
   * the Meals view-level genuinely composes multiple groups per item, so
   * the toggle row hides everywhere else.
   *
   * The filter itself (include/exclude) still applies at every view —
   * only the combine semantic collapses. */
  function applyViewLevelVisibility() {
    const level = state.get('viewLevel') || 'individual';
    const hideToggles = level !== 'meal';
    modesRow.hidden = hideToggles;
  }
  state.subscribe(s => s.viewLevel, applyViewLevelVisibility);

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

  bulkBtn.addEventListener('click', () => {
    if (bulkBtn.dataset.action === 'clear') {
      write(new Set(), new Set());
    } else {
      write(new Set(allGroups), new Set());
    }
  });

  paint();
  refreshToggles();
  applyViewLevelVisibility();
  state.subscribe(s => s.foodGroupFilter, paint);
}
