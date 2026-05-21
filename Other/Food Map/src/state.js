/* Observable global state.
 *
 * One shallow object. Views subscribe via a selector function and receive the
 * selected slice on change; they only re-render when their selected value
 * differs from last time (referentially or by ===). No framework, no proxy
 * magic — just a Map of subscribers and a setter that does shallow merge.
 *
 * Usage:
 *   import { state } from './state.js';
 *   state.subscribe(s => s.selectedIngredientId, id => render(id));
 *   state.set({ selectedIngredientId: 'egg-white' });
 *   const all = state.get();
 */

const _state = {
  // Theme — 'light' | 'dark' | 'auto' (auto = follow OS preference)
  theme: 'auto',

  // Data (Phase 2+)
  ingredients: [],
  normalized: null,

  // Axes — three { nutrient, direction, orientation, constraint } entries.
  // Set in main.js to DEFAULT_AXES once the dataset is loaded.
  //
  // Phase 40 round 13: live state.axes is the ACTIVE-unit copy. Two
  // stored mirrors hold each unit's adjustments independently:
  //   state.axes100g    — per-100g axis constraints (wider ranges)
  //   state.axesServing — per-serving axis constraints
  // A subscription in main.js keeps state.axes in sync with whichever
  // mirror matches state.nutrientUnit. All scene + UI consumers
  // continue to read state.axes (no refactor needed).
  axes: null,
  axes100g: null,
  axesServing: null,

  // Phase 40.6: fourth (Size) axis. When enabled, maps the chosen
  // nutrient to per-instance dot radius; clamped to the constraint
  // window. Off by default (uniform size).
  sizeAxis: { enabled: false, nutrient: null, constraint: null },

  // Per-nutrient settings cache so direction / orientation / constraint
  // persist across nutrient swaps. Populated in main.js boot from
  // NUTRIENT_DEFAULTS + dataset ranges. Updated whenever a nutrient is
  // swapped out of an axis — the leaving nutrient's settings are stashed
  // here, and the incoming nutrient's saved settings are restored.
  nutrientPrefs: null,

  // Phase 4.5: what the points represent and how the camera projects.
  viewLevel: 'individual',   // 'individual' | 'category' | 'meal'
  cameraMode: 'perspective', // 'perspective' | 'orthographic'

  // Tester feedback: in orthographic snap views, the axis aligned with
  // the camera direction is "edge-on" — its label fades out and its
  // row in the Axes panel greys out. Session-only — driven by the
  // animate loop from the camera angle.
  hiddenAxisIndex: null,   // null | 0 | 1 | 2

  // Phase 13.5 round 7: when viewLevel === 'category', which field
  // drives the aggregation — food_group (~11 groups), category (~40,
  // default), or subcategory (~80). Picked from the Categories
  // dropdown in the view-level toggle.
  categoryGroupBy: 'category',

  // Phase 13.5 round 3: hide axis labels (tick values, axis names,
  // Best/Worst markers) so they don't visually block dots underneath.
  axisLabelsVisible: true,

  // Phase 13.5 round 3: which color scheme drives the sphere colors and
  // the legend — 'rgb' (animal/plant/dairy additive RGB, the original
  // visualization) or 'food_group' (each food_group gets a fixed color,
  // multi-group meals/categories lerp between them).
  colorScheme: 'rgb',

  // Phase 13.75 refinement: per-scheme list of legend rows the user has
  // unchecked. Ingredients matching a hidden channel/group render at a
  // smaller scale + dimmed color so they're visibly filtered without
  // disappearing.
  legendHidden: { rgb: [], food_group: [] },

  // View (Phase 8)
  view: '3d', // '3d' | 'table'

  // Phase 8 table view.
  // tableColumns: id → visible bool. Composite is a derived column.
  // compositeWeights: nutrient → weight ∈ [0, 2]. Weight 0 = excluded
  // from the composite. Both persist to localStorage in main.js.
  // tableSort: { column, direction: 'asc'|'desc' } | null — session-only.
  tableColumns: null,
  compositeWeights: null,
  tableSort: null,

  // Selection (Phase 5)
  selectedIngredientId: null,
  hoveredIngredientId: null,

  // Phase 40 round 2: search-result preview. When the user hovers a row
  // in the 3D search dropdown, this id is set so the corresponding dot
  // pulses without committing the selection or opening the detail panel.
  // Session-only.
  previewIngredientId: null,

  // Filters (Phase 6/7)
  // Phase 6: `excludedIds` is the set of ingredient ids the user has unchecked
  // in the ingredient tree. Empty = no filter, every ingredient is active.
  ingredientFilter: { excludedIds: [] },

  /* Phase 40 round 11: two independent threshold sets that the
   * `nutrientUnit` toggle swaps between. The UI edits the active set;
   * the filter pipeline tests ingredient/aggregate values scaled to
   * that unit. Both sets are seeded at boot to the same per-100g
   * default constraints (defaultConstraintFor); the user can adjust
   * them independently. */
  thresholdsServing: null,

  // Phase 40 round 3: in aggregate views (Categories, Meals), the
  // ingredient filter can require ALL checked ingredients' categories
  // to be present in an aggregate, not just ANY. Default 'any' keeps
  // the existing behavior; the user toggles to 'all' for fridge-style
  // "I have these three ingredients, show me what I can make" queries.
  // Has no effect at the individual ingredient view-level.
  ingredientFilterMatch: 'any', // 'any' | 'all'

  // Phase 40 round 6: independent ANY/ALL setting for the Categories
  // filter — separate from ingredientFilterMatch so the two filters
  // can carry different combine modes (e.g. require ALL of categories
  // X, Y, Z while only requiring ANY of ingredients A, B, C).
  categoryFilterMatch: 'any', // 'any' | 'all'

  // Phase 40 round 6: ANY/ALL setting for the Tag filter. ANY (default)
  // is the historical OR semantic; ALL requires an item to carry every
  // selected tag. Only meaningful at the ingredient view-level — at
  // aggregate views, tags don't propagate cleanly, so the filter still
  // operates on member ingredients.
  tagFilterMatch: 'any', // 'any' | 'all'

  /* Phase 40 round 9: SCOPE toggle (independent from the inner AND/OR
   * match toggle). Controls whether non-selected attributes are
   * allowed on a matching item:
   *   'any' (default) — extras allowed; item passes as long as
   *                     selected items appear per match-mode logic
   *   'all'           — item's full attribute set must be a SUBSET of
   *                     the selection (no extras at all)
   *
   * Tester's reference case: X, Y selected on ingredient filter.
   *   ANY+AND = meal contains X AND Y, may also contain Z
   *   ANY+OR  = meal contains X OR Y,  may also contain Z
   *   ALL+AND = meal contains X AND Y, and NOTHING ELSE
   *   ALL+OR  = meal contains X or Y,  and NOTHING ELSE
   */
  ingredientFilterScope: 'any', // 'any' | 'all'
  categoryFilterScope:   'any', // 'any' | 'all'
  tagFilterScope:        'any', // 'any' | 'all'
  dietCuisineFilterScope:'any', // 'any' | 'all'
  thresholds: null,
  thresholdMode: 'filter', // 'filter' | 'score'

  // Tester feedback: profile presets (keto, low-carb, etc.) are pure
  // one-shot apply buttons — no active set, no tracking. Only the
  // combine mode persists, governing how each click stacks onto the
  // current thresholds ('narrowest' = tighten, 'widest' = loosen).
  nutrientProfileMode: 'narrowest', // 'narrowest' | 'widest'

  // Meals (Phase 9)
  // userMeals: array of { id, name, ingredients: [{ ingredientId, grams }] }
  // Persisted via localStorage in main.js.
  userMeals: [],

  // Phase 40 round 4: meal-specific filter slots removed. Categories,
  // food groups, and nutrient ranges are now global filters with their
  // own left-rail sections (state.categoryFilter, state.foodGroupFilter,
  // state.thresholds — now applied at the current view-level too).
  // The mealFilters slot is intentionally left in place but unused so
  // legacy localStorage shapes don't crash on hydration; persistence
  // migration zeroes it.
  mealFilters: {
    ingredientIds: [], ingredientIdsExcluded: [],
    categories: [],    categoriesExcluded: [],
    nutrients: {},
    foodGroupsExcluded: [],
  },

  // Phase 40 round 4: global Categories filter. Tri-state per category.
  //   included: meal/ingredient/category must reference at least one of
  //             these (with match-all on: must reference ALL).
  //   excluded: hide anything that references any of these.
  // Both empty = no filter.
  categoryFilter: { included: [], excluded: [] },

  // Phase 40 round 4: global Food groups filter (inverse-checkbox).
  // `excluded` holds the food_groups the user has unchecked. Hides
  // ingredients in those groups everywhere; aggregates (categories,
  // meals) whose entire content falls in excluded groups also disappear.
  foodGroupFilter: { excluded: [] },

  // Phase 40 round 7: Diet + Cuisine filter (meal-only). Empty arrays
  // = no constraint. Both apply only at the Meals view level.
  //   dietFilter.included: meal must be compatible with at least one
  //     selected diet (OR semantic against meal.diet_compatibility).
  //   cuisineFilter.included: meal's cuisine must be in the selected list.
  dietFilter: { included: [] },
  cuisineFilter: { included: [] },

  // Phase 40 round 8: AND/OR combine mode for the Diet + Cuisine
  // section as a whole. 'all' (default) = meal must satisfy BOTH the
  // diet check AND the cuisine check; 'any' = meal must satisfy at
  // least one. Only relevant when both sub-filters are populated.
  dietCuisineFilterMatch: 'all', // 'any' | 'all'

  // Phase 40 round 7: nutrient display unit.
  //   '100g'    — values shown per-100g (the underlying convention)
  //   'serving' — values shown per typical serving (food_group default)
  // Affects detail panel + table view (and any future surface that
  // prints nutrient numbers). The data itself is always per-100g; this
  // is a display multiplier only.
  nutrientUnit: '100g',

  // Phase 35: composition overlay. A global modifier applied on top of
  // every curated meal's `ingredient_categories`. `added` categories are
  // injected into every meal's category list (and so push each meal's
  // aggregate toward those categories' nutrient profile / color); `removed`
  // categories are stripped. A meal whose effective category list becomes
  // empty is hidden. Empty arrays = no overlay, meals plot as-is.
  mealComposition: { added: [], removed: [] },

  // Phase 37: in-flight remix of a single meal. Session-only (NOT in
  // PERSISTABLE_KEYS) — the draft is a transient workbench on top of a
  // specific meal, useful while the detail panel is open and gone the
  // moment the user navigates away. The `categories` slot holds the
  // working list; saving turns it into a userMeals entry, resetting
  // clears it. While the draft is active and matches the selected meal,
  // the scene plots that meal at the draft's centroid instead of the
  // original.
  mealDraft: null,

  // Phase 38: collapsed-to-pill state for the active-filters panel.
  // Default open; the user can collapse it to a "Filters (3)" pill via
  // the × button on the panel header.
  activeFiltersOpen: true,

  // Phase 40 round 5: true when the current filter composition leaves
  // zero items visible in the current view. Drives the persistent
  // warning in the active-filters panel (visible in both 3D and table
  // views). Session-only — recomputed every applyFilterToScene.
  filtersHideAll: false,

  // Phase 13.5: dietary restrictions. Each entry is a key from
  // DIETARY_RESTRICTIONS in core/restrictions.js. An ingredient is hidden
  // when ANY active restriction's `contains` set intersects with its
  // `contains` tags. Applies to the ingredient filter, table view, and
  // meal-builder (meals containing any hidden ingredient are also hidden).
  restrictions: [],

  // Phase 26: cross-category tag filter. Empty array = no filter. Non-empty
  // = OR semantic — an ingredient passes if it carries any of these tags
  // in its `tags` field. Composes with ingredientFilter + thresholds +
  // restrictions via intersection.
  tagFilter: [],

  // Per-rail "is this sub-section open" state for the meal builder.
  // Default collapsed (Phase 13.5 round 2) so the Meals section opens
  // compact and the user expands what they want to browse.
  mealsCuratedOpen: false,
  mealsUserOpen: false,

  // UI
  // Both rails default open on desktop. main.js boot overrides leftRailOpen
  // to false on mobile so the drawer doesn't occlude the canvas at first
  // paint. rightRailOpen only controls desktop's docked vs collapsed state;
  // on mobile the bottom sheet's visibility is driven by selectedIngredientId.
  leftRailOpen: true,
  rightRailOpen: true,
};

const _subs = new Set();

function _notify(prev) {
  for (const sub of _subs) {
    const next = sub.selector(_state);
    if (next !== sub.last) {
      sub.last = next;
      sub.callback(next, sub.selector(prev));
    }
  }
}

export const state = {
  get(key) {
    return key === undefined ? _state : _state[key];
  },

  set(patch) {
    const prev = { ..._state };
    Object.assign(_state, patch);
    _notify(prev);
  },

  subscribe(selector, callback) {
    const sub = { selector, callback, last: selector(_state) };
    _subs.add(sub);
    return () => _subs.delete(sub);
  },
};
