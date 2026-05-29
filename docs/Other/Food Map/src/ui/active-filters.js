/* Phase 38: active filters chip rail.
 *
 * Corner-anchored panel that summarizes every filter currently shaping
 * the view. Each active filter renders as a removable chip with an
 * inline × that clears it. "Clear all" wipes everything at once.
 *
 * Sources of filter state covered:
 *   - state.restrictions[]                  → "Vegan", "Caffeine-free", …
 *   - state.thresholds (when != defaults)   → "Cal ≤ 500 kcal", "Protein ≥ 20g"
 *   - state.mealComposition.added/removed   → "+ Olive oil", "− Whole grains"
 *   - state.tagFilter[]                     → "high-protein", "fermented"
 *   - state.ingredientFilter.excludedIds    → "ingredients: 132/1362"
 *   - state.mealDraft                       → "draft: <meal name>"
 *
 * Phase 40.9: the panel is ALWAYS mounted (no auto-hide when chips
 * are empty). The × button on the header toggles between "expanded
 * panel" and a "Filters" pill in the same corner. When expanded with
 * zero chips, the body shows a "No active filters right now" message
 * so the user can always see where the panel lives. Clicking "Clear
 * all" stays expanded.
 *
 * Phase 40.11: per-nutrient threshold chips now diff against the
 * user-default map (boot-initial defaultConstraint values) rather than
 * the dataset envelope. An untouched config has no threshold chips —
 * 1000 kcal isn't shown as "≤ 1000 kcal" just because the dataset
 * max is 902.
 */

import { NUTRIENT_FIELDS, NUTRIENT_META } from '../data/schema.js';
import { DIETARY_RESTRICTIONS } from '../core/restrictions.js';
import { isNutrientThresholdAtDefault } from '../core/scoring.js';
import { escapeHtml, escapeAttr } from '../util/dom.js';

const RESTRICTION_BY_KEY = new Map(DIETARY_RESTRICTIONS.map(r => [r.key, r]));

export function mountActiveFilters(root, {
  state,
  ingredients,
  ranges,
  getRawMeal = () => null,
  // Phase 40.11: map of { nutrient: { min, max } } representing the
  // BOOT-INITIAL defaults (defaultConstraintFor across all nutrients).
  // Chips diff against this map so "untouched" thresholds don't show.
  // Falls back to ranges when not provided (preserves old behavior).
  defaultThresholdsMap = null,
  // Per-serving counterpart: used when nutrientUnit === 'serving' so
  // per-serving threshold chips diff against per-serving defaults
  // (which can differ from per-100g — e.g., calories max 2000 vs 1000).
  // Without this, an untouched per-serving slot generated phantom chips
  // because the per-serving defaults didn't match the per-100g defaults
  // used here.
  defaultThresholdsMapServing = null,
}) {
  if (!root) return;

  // Always make the panel visible — no more auto-hide.
  root.removeAttribute('hidden');

  function activeDefaultsMap() {
    const unit = state.get('nutrientUnit') || '100g';
    return unit === 'serving'
      ? (defaultThresholdsMapServing || defaultThresholdsMap)
      : defaultThresholdsMap;
  }
  function effectiveDefault(nutrient) {
    const map = activeDefaultsMap();
    if (map && map[nutrient]) return map[nutrient];
    return ranges && ranges[nutrient];
  }

  function buildChips() {
    const chips = [];

    /* Tester feedback: Score mode is a top-of-mind setting that's
     * easy to forget once switched on. Show it as a chip whose × flips
     * the mode back to 'filter'. Sits at the top so it's the first
     * thing the user sees in this rail. */
    const mode = state.get('thresholdMode') || 'filter';
    if (mode === 'score') {
      chips.push({
        kind: 'threshold-mode',
        value: 'score',
        label: 'Mode: Score',
        clear: () => state.set({ thresholdMode: 'filter' }),
      });
    }

    // Restrictions
    const restrictions = state.get('restrictions') || [];
    for (const key of restrictions) {
      const def = RESTRICTION_BY_KEY.get(key);
      chips.push({
        kind: 'restriction',
        value: key,
        label: def ? def.label : key,
        clear: () => state.set({
          restrictions: (state.get('restrictions') || []).filter(r => r !== key),
        }),
      });
    }

    // Tag filter (Phase 26)
    const tagFilter = state.get('tagFilter') || [];
    for (const tag of tagFilter) {
      chips.push({
        kind: 'tag',
        value: tag,
        label: tag,
        clear: () => state.set({
          tagFilter: (state.get('tagFilter') || []).filter(t => t !== tag),
        }),
      });
    }

    // Thresholds: any nutrient whose window differs from the user-default.
    // Phase 40 round 11: reads the ACTIVE threshold set (per-100g or
    // per-serving based on nutrientUnit). The clear() handler writes
    // back to the same slot so toggling the unit doesn't accidentally
    // reset the wrong set.
    const unit       = state.get('nutrientUnit') || '100g';
    const slotKey    = unit === 'serving' ? 'thresholdsServing' : 'thresholds';
    const unitSuffix = unit === 'serving' ? ' /serv' : '';
    const thresholds = state.get(slotKey);
    if (thresholds) {
      for (const n of NUTRIENT_FIELDS) {
        const t = thresholds[n];
        if (!t) continue;
        const d = effectiveDefault(n);
        if (!d) continue;
        if (isNutrientThresholdAtDefault(t, d)) continue;
        const minMoved = Math.abs(t.min - d.min) > 1e-6;
        const maxMoved = Math.abs(t.max - d.max) > 1e-6;
        const meta = NUTRIENT_META[n];
        let label;
        if (minMoved && maxMoved) {
          label = `${meta.label}: ${meta.format(t.min)}–${meta.format(t.max)}${unitSuffix}`;
        } else if (maxMoved) {
          label = `${meta.label} ≤ ${meta.format(t.max)}${unitSuffix}`;
        } else {
          label = `${meta.label} ≥ ${meta.format(t.min)}${unitSuffix}`;
        }
        chips.push({
          kind: 'threshold',
          value: n,
          label,
          clear: () => {
            const next = { ...(state.get(slotKey) || {}) };
            next[n] = { min: d.min, max: d.max };
            state.set({ [slotKey]: next });
          },
        });
      }
    }

    // Composition overlay (Phase 35): one chip per added or removed category.
    const composition = state.get('mealComposition') || { added: [], removed: [] };
    const added   = Array.isArray(composition.added)   ? composition.added   : [];
    const removed = Array.isArray(composition.removed) ? composition.removed : [];
    for (const cat of added) {
      chips.push({
        kind: 'composition-add',
        value: cat,
        label: `+ ${cat}`,
        clear: () => {
          const c = state.get('mealComposition') || { added: [], removed: [] };
          state.set({
            mealComposition: {
              added:   (c.added   || []).filter(x => x !== cat),
              removed: (c.removed || []).slice(),
            },
          });
        },
      });
    }
    for (const cat of removed) {
      chips.push({
        kind: 'composition-remove',
        value: cat,
        label: `− ${cat}`,
        clear: () => {
          const c = state.get('mealComposition') || { added: [], removed: [] };
          state.set({
            mealComposition: {
              added:   (c.added   || []).slice(),
              removed: (c.removed || []).filter(x => x !== cat),
            },
          });
        },
      });
    }

    // Meal filter slots (Phase 33). Each non-empty slot turns into a
    // chip with its slot's count; clicking the × wipes that slot entirely.
    /* Phase 40 round 4: global Categories filter chips (was meal-only). */
    const cf = state.get('categoryFilter') || {};
    const cfIncluded = Array.isArray(cf.included) ? cf.included : [];
    const cfExcluded = Array.isArray(cf.excluded) ? cf.excluded : [];
    if (cfIncluded.length > 0) {
      chips.push({
        kind: 'category-included',
        value: 'included',
        label: `category in (${cfIncluded.length})`,
        clear: () => {
          const cur = state.get('categoryFilter') || {};
          state.set({ categoryFilter: { ...cur, included: [] } });
        },
      });
    }
    if (cfExcluded.length > 0) {
      chips.push({
        kind: 'category-excluded',
        value: 'excluded',
        label: `category not (${cfExcluded.length})`,
        clear: () => {
          const cur = state.get('categoryFilter') || {};
          state.set({ categoryFilter: { ...cur, excluded: [] } });
        },
      });
    }

    /* Phase 40 round 4 / Batch 4: tri-state food-group filter chips
     * (included + excluded), mirroring the category-filter pattern. */
    const gf = state.get('foodGroupFilter') || {};
    const gfIncluded = Array.isArray(gf.included) ? gf.included : [];
    const gfExcluded = Array.isArray(gf.excluded) ? gf.excluded : [];
    if (gfIncluded.length > 0) {
      chips.push({
        kind: 'food-group-included',
        value: 'included',
        label: `food group in (${gfIncluded.length})`,
        clear: () => {
          const cur = state.get('foodGroupFilter') || {};
          state.set({ foodGroupFilter: { ...cur, included: [] } });
        },
      });
    }
    if (gfExcluded.length > 0) {
      chips.push({
        kind: 'food-group-excluded',
        value: 'excluded',
        label: `food group not (${gfExcluded.length})`,
        clear: () => {
          const cur = state.get('foodGroupFilter') || {};
          state.set({ foodGroupFilter: { ...cur, excluded: [] } });
        },
      });
    }

    /* Phase 40 round 7: Diet + Cuisine chips (meal-only). */
    const df = state.get('dietFilter') || {};
    const dfInc = Array.isArray(df.included) ? df.included : [];
    if (dfInc.length > 0) {
      chips.push({
        kind: 'diet-included',
        value: 'diet',
        label: `diet: ${dfInc.length}`,
        clear: () => state.set({ dietFilter: { included: [] } }),
      });
    }
    const cuf = state.get('cuisineFilter') || {};
    const cufInc = Array.isArray(cuf.included) ? cuf.included : [];
    if (cufInc.length > 0) {
      chips.push({
        kind: 'cuisine-included',
        value: 'cuisine',
        label: `cuisine: ${cufInc.length}`,
        clear: () => state.set({ cuisineFilter: { included: [] } }),
      });
    }

    /* Phase 40 round 4: legend (color guide) unchecks. */
    const lh = state.get('legendHidden') || {};
    const scheme = state.get('colorScheme') || 'rgb';
    const lhArr = Array.isArray(lh[scheme]) ? lh[scheme] : [];
    if (lhArr.length > 0) {
      chips.push({
        kind: 'legend-hidden',
        value: scheme,
        label: `color guide hidden (${lhArr.length})`,
        clear: () => {
          const next = { ...lh };
          next[scheme] = [];
          state.set({ legendHidden: next });
        },
      });
    }

    // Ingredient tree (Phase 6): chip surfaces "ingredients: X / Y"
    // when anything is excluded.
    const filter = state.get('ingredientFilter') || { excludedIds: [] };
    const excludedIds = Array.isArray(filter.excludedIds) ? filter.excludedIds : [];
    if (excludedIds.length > 0 && Array.isArray(ingredients)) {
      const total = ingredients.length;
      const visible = Math.max(0, total - excludedIds.length);
      chips.push({
        kind: 'ingredient-filter',
        value: 'tree',
        label: `ingredients: ${visible}/${total}`,
        clear: () => state.set({ ingredientFilter: { excludedIds: [] } }),
      });
    }

    // Active meal draft (Phase 37). Label uses the source meal name.
    const draft = state.get('mealDraft');
    if (draft && draft.mealId) {
      const raw = getRawMeal && getRawMeal(draft.mealId);
      const mealName = raw && raw.name ? raw.name : draft.mealId;
      chips.push({
        kind: 'draft',
        value: draft.mealId,
        label: `draft: ${mealName}`,
        clear: () => state.set({ mealDraft: null }),
      });
    }

    return chips;
  }

  function clearAll() {
    // Build a single state.set patch so listeners only fire once.
    // Phase 40.11: reset thresholds to USER defaults (defaultThresholdsMap)
    // when available, not the dataset envelope.
    const resetThresholds = {};
    const resetThresholdsServing = {};
    for (const n of NUTRIENT_FIELDS) {
      const d100   = (defaultThresholdsMap && defaultThresholdsMap[n])
        || (ranges && ranges[n]);
      const dServ  = (defaultThresholdsMapServing && defaultThresholdsMapServing[n])
        || d100;
      if (d100)  resetThresholds[n]        = { min: d100.min,  max: d100.max  };
      if (dServ) resetThresholdsServing[n] = { min: dServ.min, max: dServ.max };
    }
    const patch = {
      thresholdMode: 'filter',
      restrictions: [],
      tagFilter: [],
      ingredientFilter: { excludedIds: [] },
      ingredientFilterMatch: 'any',
      categoryFilterMatch: 'any',  // Phase 40 round 6
      tagFilterMatch: 'any',       // Phase 40 round 6
      dietCuisineFilterMatch: 'all', // Phase 40 round 8 (default = both must match)
      // Phase 40 round 9: reset scope toggles too.
      ingredientFilterScope: 'any',
      categoryFilterScope:   'any',
      tagFilterScope:        'any',
      dietCuisineFilterScope:'any',
      mealComposition: { added: [], removed: [] },
      mealDraft: null,
      thresholds: resetThresholds,
      thresholdsServing: resetThresholdsServing, // each slot at its own unit defaults
      // Phase 40 round 4: clear the new global filters too.
      categoryFilter: { included: [], excluded: [] },
      foodGroupFilter: { included: [], excluded: [] },
      // Batch 4: reset the new food-group toggle slots too.
      foodGroupFilterMatch: 'any',
      foodGroupFilterScope: 'any',
      // Phase 40 round 7
      dietFilter: { included: [] },
      cuisineFilter: { included: [] },
      // Reset the legacy slot so any stale data is dropped.
      mealFilters: {
        ingredientIds: [], ingredientIdsExcluded: [],
        categories: [],    categoriesExcluded: [],
        nutrients: {},
        foodGroupsExcluded: [],
      },
      // Also reset color-guide unchecks so the user starts fresh.
      legendHidden: { rgb: [], food_group: [] },
    };
    state.set(patch);
  }

  /* The chip list is rebuilt cheaply, but the resulting innerHTML +
   * listener wiring is expensive. The 17 SLICES below subscribe broadly
   * (e.g. nutrientUnit, colorScheme) — many mutations don't change the
   * chip set at all. Fingerprint the inputs that affect rendering and
   * skip the DOM rebuild when nothing changed. */
  let _lastRenderFingerprint = null;
  function render() {
    const chips = buildChips();
    /* Phase 40 round 5: persistent "filters hide everything" warning
     * — both collapsed pill and expanded body get a red treatment so
     * the user always sees that filters are eating the dataset.
     *
     * Phase 40 round 6: when filtersHideAll is on, the section is
     * force-expanded; the × collapse button is disabled. Users can't
     * stash the warning into the corner pill while the dataset is
     * empty. */
    const hideAll = state.get('filtersHideAll') === true;
    const open = hideAll ? true : (state.get('activeFiltersOpen') !== false);

    const fingerprint = `${open ? 1 : 0}|${hideAll ? 1 : 0}|` +
      chips.map(c => `${c.kind}:${c.value}:${c.label}`).join('\x1f');
    if (fingerprint === _lastRenderFingerprint) return;
    _lastRenderFingerprint = fingerprint;

    if (!open) {
      root.classList.add('is-collapsed');
      root.classList.toggle('has-warning', hideAll);
      const label = `Filters${chips.length > 0 ? ` (${chips.length})` : ''}`;
      root.innerHTML = `
        <button class="active-filters-expand" type="button"
                title="Show active filters">
          <span aria-hidden="true">▴</span>
          <span>${label}</span>
        </button>
      `;
      root.querySelector('.active-filters-expand').addEventListener('click', () => {
        state.set({ activeFiltersOpen: true });
      });
      return;
    }

    root.classList.remove('is-collapsed');
    root.classList.toggle('has-warning', hideAll);

    const warningHtml = hideAll
      ? `<p class="active-filters-warning" role="status">
           ⚠ Your filters hide every item in this view.
         </p>`
      : '';
    const bodyHtml = chips.length === 0
      ? `<p class="active-filters-empty muted">No active filters right now.</p>`
      : `<ul class="active-filters-list">${
          chips.map(c => `
            <li class="active-filter-chip"
                data-kind="${escapeAttr(c.kind)}"
                data-value="${escapeAttr(c.value)}">
              <span class="active-filter-chip-label">${escapeHtml(c.label)}</span>
              <button class="active-filter-chip-x" type="button"
                      aria-label="Clear ${escapeAttr(c.label)}">×</button>
            </li>
          `).join('')
        }</ul>`;

    /* Phase 40 round 6: while filtersHideAll is true, the × is
     * disabled — the panel must stay visible so the user remembers
     * filters are responsible for the empty view. */
    const collapseDisabled = hideAll ? 'disabled' : '';
    const collapseTitle    = hideAll
      ? 'Cannot collapse while filters hide every item — clear or relax a filter first'
      : 'Collapse';
    root.innerHTML = `
      <header class="active-filters-header">
        <strong class="active-filters-title">
          Active filters
          ${chips.length > 0
            ? `<span class="muted">(${chips.length})</span>`
            : ''}
        </strong>
        <button class="active-filters-collapse" type="button"
                aria-label="${collapseTitle}" title="${collapseTitle}"
                ${collapseDisabled}>▾</button>
      </header>
      ${warningHtml}
      ${bodyHtml}
      <button class="active-filters-clear btn-link" type="button"
              ${chips.length === 0 ? 'disabled' : ''}>Clear all</button>
    `;

    const collapseBtn = root.querySelector('.active-filters-collapse');
    if (collapseBtn && !hideAll) {
      collapseBtn.addEventListener('click', () => {
        state.set({ activeFiltersOpen: false });
      });
    }
    root.querySelector('.active-filters-clear').addEventListener('click', clearAll);

    // Per-chip × dispatches to the chip's own clear() closure.
    const list = root.querySelector('.active-filters-list');
    if (list) {
      list.addEventListener('click', (ev) => {
        const x = ev.target.closest('.active-filter-chip-x');
        if (!x) return;
        const li = x.closest('.active-filter-chip');
        if (!li) return;
        const kind = li.dataset.kind;
        const value = li.dataset.value;
        const chip = chips.find(c => c.kind === kind && String(c.value) === String(value));
        if (chip) chip.clear();
      });
    }
  }

  render();
  // Subscribe to every state slice the chips read so the rail stays
  // in sync. Restrictions / tags / thresholds / composition / etc. all
  // trigger a re-render. The render itself is cheap (O(chips)).
  const SLICES = [
    s => s.thresholdMode,     // Score-mode chip shows / hides on this
    s => s.restrictions,
    s => s.tagFilter,
    s => s.thresholds,
    s => s.thresholdsServing, // Phase 40 round 11
    s => s.nutrientUnit,      // Phase 40 round 11 — flips which set drives chips
    s => s.mealComposition,
    s => s.mealFilters,
    s => s.ingredientFilter,
    s => s.mealDraft,
    s => s.activeFiltersOpen,
    // Phase 40 round 4: new global filter slots.
    s => s.categoryFilter,
    s => s.foodGroupFilter,
    s => s.legendHidden,
    s => s.colorScheme,
    // Phase 40 round 5: persistent "filters hide everything" warning.
    s => s.filtersHideAll,
    // Phase 40 round 7: diet + cuisine.
    s => s.dietFilter,
    s => s.cuisineFilter,
  ];
  for (const sel of SLICES) state.subscribe(sel, render);
}

