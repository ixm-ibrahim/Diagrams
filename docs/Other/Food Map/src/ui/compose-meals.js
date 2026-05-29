/* Phase 35: composition overlay — "Modify meals" filter body.
 *
 * Adds or removes categories from every curated meal's effective
 * ingredient_categories. Each row gets a tri-state +/− control (matches
 * Phase 33's pattern from meal-builder.js):
 *   + → category injected into every meal       (state.mealComposition.added)
 *   − → category stripped from every meal       (state.mealComposition.removed)
 *
 * Aggregations re-run on state.mealComposition change, so meal dots in
 * the Meals view-level reposition immediately. Empty arrays = no overlay.
 *
 * Phase 40 round 4: re-promoted to a standalone left-rail section
 * (mountComposeMealsSection wraps the existing body renderer in a
 * createRailSection). The bare-body mountComposeMeals export is also
 * preserved for any future host that wants the body alone.
 */

import { createRailSection } from './left-rail.js';
import { escapeHtml, escapeAttr } from '../util/dom.js';

export function mountComposeMealsSection(host, { state, ingredients }) {
  if (!host) return () => {};
  const { root: section, body } = createRailSection({
    title: 'Modify all meals',
    initiallyCollapsed: true,
    id: 'section-modify-meals', // tutorial slide 12 targets this
    tooltip: 'Inject or strip a category across every meal at once. + adds it to every meal; − removes it. Affects both the 3D view and the table.',
  });
  host.appendChild(section);
  return mountComposeMeals(body, { state, ingredients });
}

export function mountComposeMeals(host, { state, ingredients }) {
  if (!host) return () => {};

  host.classList.add('compose-meals');
  host.innerHTML = `
    <p class="compose-meals-blurb muted">
      Add or remove a category across every meal. Dots reposition live.
    </p>
    <div class="compose-meals-head">
      <input class="compose-meals-search input" type="search"
             placeholder="Search categories…" aria-label="Search categories">
      <button class="compose-meals-reset" type="button">Reset</button>
    </div>
    <div class="compose-meals-summary muted"></div>
    <div class="compose-meals-list meal-filter-options is-tri" role="list"></div>
  `;

  const searchEl  = host.querySelector('.compose-meals-search');
  const resetEl   = host.querySelector('.compose-meals-reset');
  const summaryEl = host.querySelector('.compose-meals-summary');
  const listEl    = host.querySelector('.compose-meals-list');

  const allCategories = Array.from(new Set(ingredients.map(i => i.category))).sort();

  function readComposition() {
    const c = state.get('mealComposition') || {};
    return {
      added:   new Set(Array.isArray(c.added)   ? c.added   : []),
      removed: new Set(Array.isArray(c.removed) ? c.removed : []),
    };
  }

  function writeComposition(added, removed) {
    state.set({
      mealComposition: { added: [...added], removed: [...removed] },
    });
  }

  function rowHtml(category, added, removed, pinned = false) {
    const s = added.has(category) ? 'include'
            : removed.has(category) ? 'exclude'
            : 'off';
    return `
      <div class="meal-filter-option meal-filter-option-tri${pinned ? ' is-pinned' : ''}"
           data-value="${escapeAttr(category)}" data-state="${s}" role="listitem">
        <span class="meal-filter-option-label">${escapeHtml(category)}</span>
        <span class="tri-state-controls" role="group" aria-label="${escapeAttr(category)} include or exclude">
          <button class="tri-state-btn" type="button" data-action="include"
                  aria-pressed="${s === 'include'}" title="Inject this category into every meal">+</button>
          <button class="tri-state-btn" type="button" data-action="exclude"
                  aria-pressed="${s === 'exclude'}" title="Strip this category from every meal">−</button>
        </span>
      </div>`;
  }

  function paint() {
    const { added, removed } = readComposition();
    const q = (searchEl.value || '').trim().toLowerCase();
    const shown = q ? allCategories.filter(c => c.toLowerCase().includes(q)) : allCategories;

    // Phase 40 round 2: COPY (not move) every currently-selected category
    // to a pinned section at the top, so the user always sees their
    // active overlay without scrolling. Pinned ignores the search filter
    // on purpose — hiding selections behind a search would defeat the
    // "always visible" goal. The same category appears in both groups;
    // the click handler operates by value so toggling either copy works.
    const pinned = allCategories.filter(c => added.has(c) || removed.has(c));
    const pinnedHtml = pinned.length
      ? `<div class="compose-meals-pinned" role="group" aria-label="Active overlay">
           ${pinned.map(c => rowHtml(c, added, removed, true)).join('')}
         </div>
         <div class="compose-meals-divider" aria-hidden="true">all categories</div>`
      : '';
    const fullHtml = shown.length
      ? shown.map(c => rowHtml(c, added, removed)).join('')
      : '<p class="muted" style="padding: 8px 4px 4px;">No matches</p>';

    listEl.innerHTML = pinnedHtml + fullHtml;

    const summary = [];
    if (added.size > 0)   summary.push(`+${added.size}`);
    if (removed.size > 0) summary.push(`−${removed.size}`);
    summaryEl.textContent = summary.length ? `Overlay: ${summary.join(' / ')}` : '';
  }
  paint();

  listEl.addEventListener('click', (ev) => {
    const btn = ev.target.closest('.tri-state-btn');
    if (!btn) return;
    const row = btn.closest('.meal-filter-option-tri');
    if (!row) return;
    const value  = row.dataset.value;
    const action = btn.dataset.action;
    const current = row.dataset.state;
    const nextState = current === action ? 'off' : action;

    const { added, removed } = readComposition();
    added.delete(value);
    removed.delete(value);
    if (nextState === 'include') added.add(value);
    if (nextState === 'exclude') removed.add(value);
    writeComposition(added, removed);
    // Paint will refresh from state via the subscribe below; the optimistic
    // dataset update keeps the button feedback instant in the same frame.
    row.dataset.state = nextState;
    row.querySelector('.tri-state-btn[data-action="include"]').setAttribute('aria-pressed', String(nextState === 'include'));
    row.querySelector('.tri-state-btn[data-action="exclude"]').setAttribute('aria-pressed', String(nextState === 'exclude'));
  });

  searchEl.addEventListener('input', paint);

  resetEl.addEventListener('click', () => {
    writeComposition(new Set(), new Set());
  });

  const unsubscribe = state.subscribe(s => s.mealComposition, paint);
  return unsubscribe;
}

