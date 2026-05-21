/* Phase 13.5: dietary restrictions section.
 *
 * Sits at the top of the left rail above "Filter by ingredient". Each
 * restriction is a checkbox grouped by Diet / Religious / Allergy. State
 * lives in state.restrictions as an array of restriction keys.
 *
 * Active restrictions hide ingredients with matching `contains` tags
 * everywhere they appear: the ingredient filter (composed with
 * excludedIds), the table view, and the meal builder (meals containing
 * any hidden ingredient are also hidden).
 */

import { createRailSection } from './left-rail.js';
import { DIETARY_RESTRICTIONS, groupedRestrictions } from '../core/restrictions.js';

export function mountRestrictions(host, { state }) {
  if (!host) return;

  const { root: section, body } = createRailSection({
    title: 'Dietary restrictions',
    initiallyCollapsed: true,
    tooltip: 'Hide ingredients that contain specific items (gluten, dairy, nuts, caffeine, etc.). Meals containing a restricted ingredient are also hidden.',
  });
  host.appendChild(section);

  body.classList.add('restrictions');

  const groups = groupedRestrictions();
  body.innerHTML = `
    <p class="restrictions-help muted">
      Hide ingredients (and meals containing them) that don't fit your needs.
    </p>
    ${groups.map(({ group, items }) => `
      <div class="restrictions-group">
        <h4 class="restrictions-group-title">${escapeHtml(group)}</h4>
        <ul class="restrictions-list">
          ${items.map(r => `
            <li class="restriction-item">
              <label class="restriction-check">
                <input type="checkbox" data-key="${escapeAttr(r.key)}">
                <span>${escapeHtml(r.label)}</span>
              </label>
            </li>
          `).join('')}
        </ul>
      </div>
    `).join('')}
    <div class="restrictions-bulk-row">
      <button class="btn-link restrictions-bulk" type="button"></button>
      <span class="restrictions-summary muted" aria-live="polite"></span>
    </div>
  `;

  const bulkBtn = body.querySelector('.restrictions-bulk');
  const summary = body.querySelector('.restrictions-summary');
  const allKeys = DIETARY_RESTRICTIONS.map(r => r.key);

  function refreshChecks() {
    const active = new Set(state.get('restrictions') || []);
    body.querySelectorAll('input[type="checkbox"][data-key]').forEach(cb => {
      cb.checked = active.has(cb.dataset.key);
    });
    summary.textContent = active.size === 0
      ? 'No restrictions active.'
      : `${active.size} active: ${[...active]
          .map(k => (DIETARY_RESTRICTIONS.find(r => r.key === k) || {}).label || k)
          .join(', ')}.`;
    // Phase 40 round 3: smart bulk-toggle. Most users will start at 0
    // active and only ever uncheck their currently-active rows, so the
    // "Check all" side of this toggle is rarely useful — but the user
    // explicitly asked for the same pattern across every filter, so
    // here it is.
    const majorityChecked = active.size * 2 >= allKeys.length;
    bulkBtn.textContent = majorityChecked ? 'Uncheck all' : 'Check all';
    bulkBtn.dataset.action = majorityChecked ? 'uncheck' : 'check';
  }

  body.addEventListener('change', (ev) => {
    const cb = ev.target;
    if (!(cb instanceof HTMLInputElement) || !cb.dataset.key) return;
    const key = cb.dataset.key;
    const next = new Set(state.get('restrictions') || []);
    if (cb.checked) next.add(key); else next.delete(key);
    state.set({ restrictions: [...next] });
  });

  bulkBtn.addEventListener('click', () => {
    const action = bulkBtn.dataset.action;
    state.set({ restrictions: action === 'check' ? allKeys.slice() : [] });
  });

  refreshChecks();
  state.subscribe(s => s.restrictions, refreshChecks);
}

function escapeHtml(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
function escapeAttr(s) { return escapeHtml(s); }
