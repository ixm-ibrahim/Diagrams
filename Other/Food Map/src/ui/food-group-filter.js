/* Phase 40 round 4: global Food groups filter section.
 *
 * Inverse checkbox semantics — every food_group is checked by default,
 * unchecking adds it to state.foodGroupFilter.excluded. Applies in
 * every view:
 *   Ingredients view — hide ingredients in excluded food_groups.
 *   Categories view — hide aggregates whose dominant food_group is
 *                     excluded (or whose membership lies entirely in
 *                     excluded groups).
 *   Meals view — hide meals whose every constituent ingredient sits in
 *                an excluded food_group.
 *
 * State: state.foodGroupFilter = { excluded: string[] }
 */

import { createRailSection } from './left-rail.js';
import { FOOD_GROUPS } from '../data/schema.js';

export function mountFoodGroupFilter(host, { state }) {
  if (!host) return;

  const { root: section, body } = createRailSection({
    title: 'Filter by food group',
    initiallyCollapsed: true,
    tooltip: 'Hide entire food groups (e.g. Meat, Dairy). Uncheck a group to remove all its ingredients and any meals built from them.',
  });
  host.appendChild(section);

  const allGroups = [...FOOD_GROUPS].sort((a, b) => a.localeCompare(b));

  body.classList.add('food-group-filter');
  body.innerHTML = `
    <p class="food-group-filter-help muted">
      Uncheck a food group to hide everything in it across all views.
    </p>
    <div class="food-group-filter-bulk-row">
      <button class="btn-link food-group-filter-bulk" type="button"></button>
      <span class="food-group-filter-summary muted" aria-live="polite"></span>
    </div>
    <ul class="food-group-filter-list">
      ${allGroups.map(g => `
        <li class="food-group-filter-item">
          <label class="food-group-check">
            <input type="checkbox" data-group="${escapeAttr(g)}">
            <span>${escapeHtml(g)}</span>
          </label>
        </li>
      `).join('')}
    </ul>
  `;
  const bulkBtn = body.querySelector('.food-group-filter-bulk');
  const summary = body.querySelector('.food-group-filter-summary');

  function refresh() {
    const excluded = new Set((state.get('foodGroupFilter') || {}).excluded || []);
    body.querySelectorAll('input[type="checkbox"][data-group]').forEach(cb => {
      cb.checked = !excluded.has(cb.dataset.group); // inverse — checked = allowed
    });
    summary.textContent = excluded.size === 0
      ? 'All groups allowed.'
      : `${excluded.size} group${excluded.size === 1 ? '' : 's'} hidden.`;
    // Smart bulk-toggle. Majority allowed → "Uncheck all"; otherwise → "Check all".
    const allowedCount = allGroups.length - excluded.size;
    const majorityAllowed = allowedCount * 2 >= allGroups.length;
    bulkBtn.textContent = majorityAllowed ? 'Uncheck all' : 'Check all';
    bulkBtn.dataset.action = majorityAllowed ? 'uncheck' : 'check';
  }

  body.addEventListener('change', (ev) => {
    const cb = ev.target;
    if (!(cb instanceof HTMLInputElement) || !cb.dataset.group) return;
    const grp = cb.dataset.group;
    const cur = new Set((state.get('foodGroupFilter') || {}).excluded || []);
    if (cb.checked) cur.delete(grp); else cur.add(grp);
    state.set({ foodGroupFilter: { excluded: [...cur] } });
  });

  bulkBtn.addEventListener('click', () => {
    const action = bulkBtn.dataset.action;
    state.set({
      foodGroupFilter: { excluded: action === 'uncheck' ? allGroups.slice() : [] },
    });
  });

  refresh();
  state.subscribe(s => s.foodGroupFilter, refresh);
}

function escapeHtml(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
function escapeAttr(s) { return escapeHtml(s); }
