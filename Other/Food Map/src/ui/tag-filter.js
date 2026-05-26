/* Phase 26: tag filter section.
 *
 * Multi-select chips, one per TAGS vocabulary entry. Selecting one or more
 * tags narrows the active set to ingredients carrying ANY of those tags
 * (OR semantic). Composes with ingredient-tree filter, dietary restrictions,
 * and nutrient thresholds via main.js's applyFilterToScene.
 *
 * State key: state.tagFilter = string[]  (empty = no filter)
 */

import { createRailSection } from './left-rail.js';
import { TAGS } from '../data/schema.js';
import { escapeHtml, escapeAttr } from '../util/dom.js';

// Display labels for the vocabulary tags. Falls back to the slug itself.
const TAG_LABELS = {
  'high-protein': 'High protein',
  'high-fiber':   'High fiber',
  'low-cal':      'Low calorie',
  'high-sodium':  'High sodium',
  'breakfast':    'Breakfast',
  'lunch':        'Lunch',
  'dinner':       'Dinner',
  'snack':        'Snack',
  'dessert':      'Dessert',
  'condiment':    'Condiment',
  'garnish':      'Garnish',
  'fermented':    'Fermented',
  'cured':        'Cured',
  'smoked':       'Smoked',
  'omega3-rich':  'Omega-3 rich',
  'iron-rich':    'Iron rich',
};

export function mountTagFilter(host, { state }) {
  if (!host) return;

  const { root: section, body } = createRailSection({
    title: 'Filter by tag',
    initiallyCollapsed: true,
    tooltip: 'Match cross-category labels like high-protein, high-fiber, breakfast, snack. Use ANY/ALL to require any or every selected tag.',
  });
  host.appendChild(section);
  body.classList.add('tag-filter');

  body.innerHTML = `
    <p class="tag-filter-help muted">
      Select one or more tags. With <strong>OR</strong>, an ingredient
      passes if it carries at least one selected tag. With
      <strong>AND</strong>, it must carry every selected tag.
    </p>
    <div class="tag-filter-bulk-row">
      <button class="btn-link tag-filter-bulk" type="button"></button>
    </div>
    <div class="filter-modes-row">
      <div class="filter-mode-pair">
        <span class="filter-mode-label muted">Allow extras:</span>
        <div class="filter-scope-toggle seg-group" role="group"
             aria-label="ANY (other tags allowed) vs ALL (only these tags)"
             title="ANY — items can carry other tags too. ALL — items must carry ONLY the selected tags (no extras).">
          <button type="button" class="seg-btn seg-btn-sm" data-scope="any">ANY</button>
          <button type="button" class="seg-btn seg-btn-sm" data-scope="all">ALL</button>
        </div>
      </div>
      <div class="filter-mode-pair">
        <span class="filter-mode-label muted">Combine:</span>
        <div class="filter-match-toggle seg-group" role="group"
             aria-label="OR (at least one) vs AND (every one)"
             title="OR — at least one selected tag must be present. AND — every selected tag must be present.">
          <button type="button" class="seg-btn seg-btn-sm" data-match="any">OR</button>
          <button type="button" class="seg-btn seg-btn-sm" data-match="all">AND</button>
        </div>
      </div>
    </div>
    <p class="tag-filter-summary muted" aria-live="polite"></p>
    <ul class="tag-filter-list">
      ${TAGS.map(t => `
        <li class="tag-filter-item">
          <label class="tag-chip">
            <input type="checkbox" data-tag="${escapeAttr(t)}">
            <span>${escapeHtml(TAG_LABELS[t] || t)}</span>
          </label>
        </li>
      `).join('')}
    </ul>
  `;

  const summary    = body.querySelector('.tag-filter-summary');
  const bulkBtn    = body.querySelector('.tag-filter-bulk');
  const matchGroup = body.querySelector('.filter-match-toggle');
  const scopeGroup = body.querySelector('.filter-scope-toggle');

  /* Phase 40 round 9: AND/OR (match) + ANY/ALL (scope) toggles. */
  function refreshToggles() {
    const matchCur = state.get('tagFilterMatch') || 'any';
    matchGroup.querySelectorAll('[data-match]').forEach(btn => {
      btn.classList.toggle('is-active', btn.dataset.match === matchCur);
    });
    const scopeCur = state.get('tagFilterScope') || 'any';
    scopeGroup.querySelectorAll('[data-scope]').forEach(btn => {
      btn.classList.toggle('is-active', btn.dataset.scope === scopeCur);
    });
  }
  matchGroup.addEventListener('click', (ev) => {
    const btn = ev.target.closest('[data-match]');
    if (!btn) return;
    state.set({ tagFilterMatch: btn.dataset.match });
  });
  scopeGroup.addEventListener('click', (ev) => {
    const btn = ev.target.closest('[data-scope]');
    if (!btn) return;
    state.set({ tagFilterScope: btn.dataset.scope });
  });
  state.subscribe(s => s.tagFilterMatch, refreshToggles);
  state.subscribe(s => s.tagFilterScope, refreshToggles);
  refreshToggles();

  function refresh() {
    const active = new Set(state.get('tagFilter') || []);
    body.querySelectorAll('input[type="checkbox"][data-tag]').forEach(cb => {
      cb.checked = active.has(cb.dataset.tag);
    });
    summary.textContent = active.size === 0
      ? 'No tag filter active.'
      : `${active.size} tag${active.size === 1 ? '' : 's'} active.`;
    // Phase 40 round 3: bulk-toggle label flips with majority state.
    const majorityChecked = active.size * 2 >= TAGS.length;
    bulkBtn.textContent = majorityChecked ? 'Uncheck all' : 'Check all';
    bulkBtn.dataset.action = majorityChecked ? 'uncheck' : 'check';
  }

  body.addEventListener('change', (ev) => {
    const cb = ev.target;
    if (!(cb instanceof HTMLInputElement) || !cb.dataset.tag) return;
    const t = cb.dataset.tag;
    const next = new Set(state.get('tagFilter') || []);
    if (cb.checked) next.add(t); else next.delete(t);
    state.set({ tagFilter: [...next] });
  });

  bulkBtn.addEventListener('click', () => {
    const action = bulkBtn.dataset.action;
    state.set({ tagFilter: action === 'check' ? TAGS.slice() : [] });
  });

  refresh();
  state.subscribe(s => s.tagFilter, refresh);
}

