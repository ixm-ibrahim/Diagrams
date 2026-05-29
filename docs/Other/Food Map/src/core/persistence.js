/* Phase 12: persistence and sharing.
 *
 * The user's configuration (axes, view level, theme, filters,
 * thresholds, meals, table preferences, etc.) lives in a single
 * versioned blob at LS_KEY. Per-slice writes from earlier phases
 * still happen but their values are also captured here, so any change
 * triggers a debounced unified save.
 *
 * Migration: if the user has values under the legacy per-slice LS keys
 * but no unified blob yet, we read them once and seed the unified blob.
 * Subsequent writes go to the unified key.
 *
 * Export = JSON.stringify of the snapshot, suitable for clipboard or
 * download. Import = JSON.parse + state.set, with a schema-version
 * check so we don't merge incompatible blobs.
 *
 * The hash-based URL sync from Phase 7 stays — it's a complementary
 * sharing affordance (the URL only carries thresholds + mode for
 * "share a quick lens" use cases).
 */

const LS_KEY = 'foodMap.state.v1';
const SCHEMA_VERSION = 1;

const LEGACY_KEYS = {
  'foodMap.tableColumns':     'tableColumns',
  'foodMap.compositeWeights': 'compositeWeights',
  'foodMap.userMeals':        'userMeals',
  'foodMap.theme':            'theme',
};

/* The list of state slices that round-trip. Selection (hovered /
 * selected ingredient) and the dataset itself are intentionally NOT here —
 * those are derived or per-session. */
export const PERSISTABLE_KEYS = [
  'theme',
  'axes',
  'axes100g',           // Phase 40 round 13
  'axesServing',        // Phase 40 round 13
  'nutrientPrefs',
  'viewLevel',
  'cameraMode',
  'view',
  'ingredientFilter',
  'thresholds',
  'thresholdsServing',  // Phase 40 round 11
  'thresholdMode',
  'tableColumns',
  'compositeWeights',
  'userMeals',
  'mealFilters',
  'mealsCuratedOpen',
  'mealsUserOpen',
  'leftRailOpen',
  'rightRailOpen',
  'restrictions',       // Phase 13.5
  'axisLabelsVisible',  // Phase 13.5 round 3
  'colorScheme',        // Phase 13.5 round 3
  'legendOpen',         // Phase 13.5 round 3
  'categoryGroupBy',    // Phase 13.5 round 7
  'legendHidden',       // Phase 13.75
  'axisControlsOpen',   // Phase 13.75 round 5
  'tagFilter',          // Phase 26
  'mealComposition',    // Phase 35
  'activeFiltersOpen',  // Phase 38
  'sizeAxis',           // Phase 40.6
  'ingredientFilterMatch', // Phase 40 round 3
  'categoryFilter',     // Phase 40 round 4
  'foodGroupFilter',    // Phase 40 round 4
  'categoryFilterMatch',// Phase 40 round 6
  'tagFilterMatch',     // Phase 40 round 6
  'dietFilter',         // Phase 40 round 7
  'cuisineFilter',      // Phase 40 round 7
  'nutrientUnit',       // Phase 40 round 7
  'dietCuisineFilterMatch', // Phase 40 round 8
  'ingredientFilterScope',  // Phase 40 round 9
  'categoryFilterScope',    // Phase 40 round 9
  'tagFilterScope',         // Phase 40 round 9
  'dietCuisineFilterScope', // Phase 40 round 9
  'foodGroupFilterMatch',   // Batch 4
  'foodGroupFilterScope',   // Batch 4
  'zoomAnchor',             // axis-controls Zoom button anchor: 'left' | 'center' | 'right'
  'nutrientProfileMode',    // tester feedback: 'narrowest' | 'widest' combine rule for profile-apply buttons
  'remixMode',              // tester-feedback Batch 4: 'category' | 'ingredient' remix toggle
];

export function snapshotPersistable(state) {
  const snap = { version: SCHEMA_VERSION };
  for (const key of PERSISTABLE_KEYS) {
    const v = state.get(key);
    if (v !== undefined) snap[key] = v;
  }
  return snap;
}

export function loadPersisted() {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return null;
    if (parsed.version !== SCHEMA_VERSION) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function savePersisted(state) {
  try {
    const snap = snapshotPersistable(state);
    localStorage.setItem(LS_KEY, JSON.stringify(snap));
  } catch {
    /* private mode or quota exceeded — keep state in memory and move on */
  }
}

let debounceTimer = null;
export function debouncedSave(state, ms = 300) {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => savePersisted(state), ms);
}

/* Read the legacy per-slice keys (Phases 6/8/9/11 wrote to these
 * individually). Returns a patch object that can be merged into state.
 * Only called when no unified blob exists yet — the unified blob is
 * the source of truth from then on. */
export function loadLegacyPatch() {
  const patch = {};
  for (const [lsKey, stateKey] of Object.entries(LEGACY_KEYS)) {
    try {
      const raw = localStorage.getItem(lsKey);
      if (!raw) continue;
      patch[stateKey] = JSON.parse(raw);
    } catch { /* skip a bad legacy entry */ }
  }
  return patch;
}

/* Migrate any pre-rename shape inside a hydrated value.
 *
 * Phase 14 renamed food → ingredient across the codebase, including the
 * `mealFilters.foodIds` slot which became `ingredientIds`. Users who saved
 * config before the rename will get back the old shape on next load; this
 * normalizes it so downstream code can trust the new field names. */
function migrateHydrated(key, value) {
  /* Tester feedback: Highlight threshold mode was removed. Any
   * persisted blob that still has 'highlight' falls back to 'filter'
   * so the user lands on a working mode. */
  if (key === 'thresholdMode') {
    if (value === 'filter' || value === 'score') return value;
    return 'filter';
  }
  if (key === 'mealFilters' && value && typeof value === 'object') {
    const next = { ...value };
    if (!Array.isArray(next.ingredientIds)) {
      next.ingredientIds = Array.isArray(next.foodIds) ? next.foodIds : [];
    }
    delete next.foodIds;
    if (!Array.isArray(next.categories)) next.categories = [];
    // Phase 40.2: nutrients changed from string[] ("checked = ≥ median")
    // to a per-nutrient { min, max } map. Old-shape saves coerce to an
    // empty map — the user can re-pick with the new UI which is clearer
    // anyway than carrying the median semantics across.
    if (Array.isArray(next.nutrients) || next.nutrients == null
        || typeof next.nutrients !== 'object') {
      next.nutrients = {};
    }
    // Phase 33: Option-A bidirectional filters. Default new exclusion
    // slots to empty for any save that predates them.
    if (!Array.isArray(next.ingredientIdsExcluded)) next.ingredientIdsExcluded = [];
    if (!Array.isArray(next.categoriesExcluded))    next.categoriesExcluded    = [];
    if (!Array.isArray(next.foodGroupsExcluded))    next.foodGroupsExcluded    = [];
    // Phase 40 round 3: Restrictions and Ingredients dropdowns inside
    // the Meals section were removed — left-rail "Dietary restrictions"
    // and "Filter by ingredient" cover those needs. Clear any persisted
    // values that no longer have a UI control.
    next.ingredientIds = [];
    next.ingredientIdsExcluded = [];
    return next;
  }
  if (key === 'categoryFilter' && value && typeof value === 'object') {
    return {
      included: Array.isArray(value.included) ? value.included : [],
      excluded: Array.isArray(value.excluded) ? value.excluded : [],
    };
  }
  if (key === 'foodGroupFilter' && value && typeof value === 'object') {
    /* Batch 4: filter shape grew from `{excluded}` to `{included,
     * excluded}` (matches categoryFilter). Read both fields when
     * present, default missing to empty so older saves still load. */
    return {
      included: Array.isArray(value.included) ? value.included : [],
      excluded: Array.isArray(value.excluded) ? value.excluded : [],
    };
  }
  if ((key === 'dietFilter' || key === 'cuisineFilter') && value && typeof value === 'object') {
    return {
      included: Array.isArray(value.included) ? value.included : [],
    };
  }
  if (key === 'sizeAxis' && value && typeof value === 'object') {
    return {
      enabled: !!value.enabled,
      nutrient: typeof value.nutrient === 'string' ? value.nutrient : null,
      constraint: (value.constraint && typeof value.constraint === 'object'
                   && Number.isFinite(value.constraint.min)
                   && Number.isFinite(value.constraint.max))
        ? { min: value.constraint.min, max: value.constraint.max }
        : null,
    };
  }
  if (key === 'mealComposition' && value && typeof value === 'object') {
    return {
      added:   Array.isArray(value.added)   ? value.added   : [],
      removed: Array.isArray(value.removed) ? value.removed : [],
    };
  }
  if (key === 'userMeals' && Array.isArray(value)) {
    return value.map(meal => {
      if (!meal || typeof meal !== 'object') return meal;
      const ingredients = Array.isArray(meal.ingredients)
        ? meal.ingredients.map(ing => {
            if (!ing || typeof ing !== 'object') return ing;
            // foodId → ingredientId (Phase 14 rename)
            if (ing.ingredientId == null && ing.foodId != null) {
              const { foodId, ...rest } = ing;
              return { ingredientId: foodId, ...rest };
            }
            return ing;
          })
        : [];
      return { ...meal, ingredients };
    });
  }
  return value;
}

/* Return a state patch derived from persisted (or legacy) storage.
 * Caller applies it via state.set after computing data-dependent
 * defaults so the patch overrides those defaults. */
export function hydratePatch() {
  const unified = loadPersisted();
  if (unified) {
    const patch = {};
    for (const key of PERSISTABLE_KEYS) {
      if (key in unified) patch[key] = migrateHydrated(key, unified[key]);
    }
    /* Phase 40 round 13: backfill state.axes100g from state.axes when
     * the persisted state predates the two-slot model (only `axes`
     * existed). Otherwise switching to per-serving and back would
     * overwrite the user's per-100g axis customizations with the
     * boot defaults. */
    if (patch.axes && !patch.axes100g) {
      patch.axes100g = patch.axes;
    }
    /* Phase 40 round 4: lift any old mealFilters.{categories,
     * categoriesExcluded, foodGroupsExcluded} into the new global
     * filter slots so users carrying state from previous rounds don't
     * lose their picks. Only fires when the new slot is empty. */
    const old = unified.mealFilters;
    if (old && typeof old === 'object') {
      const oldCatsInc = Array.isArray(old.categories) ? old.categories : [];
      const oldCatsExc = Array.isArray(old.categoriesExcluded) ? old.categoriesExcluded : [];
      const oldGroupsExc = Array.isArray(old.foodGroupsExcluded) ? old.foodGroupsExcluded : [];
      const liftedCategory = (oldCatsInc.length || oldCatsExc.length) ? {
        included: oldCatsInc,
        excluded: oldCatsExc,
      } : null;
      const liftedGroups = oldGroupsExc.length ? { excluded: oldGroupsExc } : null;
      if (liftedCategory && (!patch.categoryFilter
          || (Array.isArray(patch.categoryFilter.included) && patch.categoryFilter.included.length === 0
              && Array.isArray(patch.categoryFilter.excluded) && patch.categoryFilter.excluded.length === 0))) {
        patch.categoryFilter = liftedCategory;
      }
      if (liftedGroups && (!patch.foodGroupFilter
          || (Array.isArray(patch.foodGroupFilter.excluded) && patch.foodGroupFilter.excluded.length === 0))) {
        patch.foodGroupFilter = liftedGroups;
      }
    }
    return patch;
  }
  const legacy = loadLegacyPatch();
  const migrated = {};
  for (const [k, v] of Object.entries(legacy)) {
    migrated[k] = migrateHydrated(k, v);
  }
  return migrated;
}

export function exportJson(state) {
  return JSON.stringify(snapshotPersistable(state), null, 2);
}

/* Apply an imported JSON blob to the state. Throws on parse error or
 * schema mismatch so the caller can surface the failure in UI. Returns
 * the list of keys that were applied. */
export function importJson(state, jsonText) {
  let parsed;
  try {
    parsed = JSON.parse(jsonText);
  } catch (err) {
    throw new Error(`Invalid JSON: ${err.message}`);
  }
  if (!parsed || typeof parsed !== 'object') {
    throw new Error('Expected a JSON object at top level.');
  }
  if (parsed.version !== SCHEMA_VERSION) {
    throw new Error(`Schema version ${parsed.version ?? 'missing'} doesn't match expected ${SCHEMA_VERSION}.`);
  }
  const patch = {};
  for (const key of PERSISTABLE_KEYS) {
    if (key in parsed) patch[key] = migrateHydrated(key, parsed[key]);
  }
  state.set(patch);
  return Object.keys(patch);
}

export function clearPersisted() {
  try { localStorage.removeItem(LS_KEY); } catch { /* ignore */ }
}

export function attachAutoSave(state) {
  for (const key of PERSISTABLE_KEYS) {
    state.subscribe(s => s[key], () => debouncedSave(state));
  }
}
