/* Entry point.
 *
 * Phase 1: scaffolded; logged ready.
 * Phase 2: dataset + ranges.
 * Phase 3: Three.js scene + axes + arcball controls.
 * Phase 3.5: configurable axes (nutrient + direction + constraint).
 * Phase 4: ingredient points (InstancedMesh, RGB-blended group colors, fade-in).
 * Phase 4.5: view options — Ingredients/Categories toggle, Perspective/Orthographic
 *            camera, snap-to-axis buttons; axes now emanate from the Best corner.
 * Phase 5: hover scale + tooltip, click → selectedIngredientId, right-rail / bottom-sheet
 *          detail panel.
 * Phase 6: left-rail ingredient filter (3-level checkbox tree). Inactive ingredients
 *          are blended toward gray in the scene to keep spatial context.
 * Phase 7: nutrient threshold section (Filter / Highlight / Score modes), per-
 *          ingredient gradient coloring in Score mode, URL-hash sync.
 * Phase 8: 3D ↔ table view toggle; sortable table with sortable columns,
 *          column picker + composite-score weights (localStorage), row
 *          click → detail panel, shared filter composition with the 3D view.
 */

const LS_TABLE_COLUMNS = 'foodMap.tableColumns';
const LS_TABLE_WEIGHTS = 'foodMap.compositeWeights';
const LS_USER_MEALS    = 'foodMap.userMeals';

import * as THREE from 'three';

import { state } from './state.js';
import { computeRanges, DEFAULT_AXES } from './core/normalize.js';
import {
  NUTRIENT_FIELDS, NUTRIENT_DEFAULTS, effectiveTags,
  NUTRIENT_TAG_RULES, NUTRIENT_TAG_KEYS, TAGS,
} from './data/schema.js';
import { makeScaleGetter } from './core/unit.js';
import { aggregateByCategory, aggregateAllMeals, aggregateUserMeal, aggregateIngredientDraft } from './core/aggregations.js';
import { createScene, readCssColor } from './scene/setup.js';
import { attachControls } from './scene/controls.js';
import { buildAxes, disposeAxes } from './scene/axes.js';
import { buildPoints } from './scene/points.js';
import { buildMeals } from './scene/meals.js';
import { attachPicking } from './scene/picking.js';
import { attachAxisDrag } from './scene/axis-drag.js';
import { mountAxisPicker } from './ui/axis-picker.js';
import { mountAxisControls } from './ui/axis-controls.js';
import { mountLegend } from './ui/legend.js';
import { mountViewLevel, mount3DControls } from './ui/view-controls.js';
import { mountDetailPanel } from './ui/detail-panel.js';
import { mountLeftRail } from './ui/left-rail.js';
import { mountIngredientFilter } from './ui/ingredient-filter.js';
import { mountNutrientThresholds } from './ui/nutrient-thresholds.js';
import { mountMealBuilder, isMealFiltersEmpty } from './ui/meal-builder.js';
import { mountCategoryFilter } from './ui/category-filter.js';
import { mountFoodGroupFilter } from './ui/food-group-filter.js';
import { mountDietCuisineFilter } from './ui/diet-cuisine-filter.js';
import { mountComposeMealsSection } from './ui/compose-meals.js';
import { mountActiveFilters } from './ui/active-filters.js';
import { mountSearch } from './ui/search.js';
import { mountUnitToggle } from './ui/unit-toggle.js';
import { attachPickMenu } from './ui/pick-menu.js';
import { mountViewToggle } from './ui/view-toggle.js';
import { mountTableView } from './ui/table-view.js';
import { mountThemeToggle } from './ui/theme-toggle.js';
import { mountShortcuts } from './ui/shortcuts.js';
import { attachRailResize } from './ui/rail-resize.js';
import { mountConfigMenu } from './ui/config-menu.js';
import { mountTutorial } from './ui/tutorial.js';
import { computeActiveSet, isFilterEmpty, isTagFilterEmpty, tagActiveSet } from './core/filters.js';
import {
  thresholdActiveSet, computeScores, defaultThresholds, isThresholdsBaseline,
  isThresholdsAtDefaults,
} from './core/scoring.js';
import { hydratePatch, attachAutoSave } from './core/persistence.js';
import { passingIngredientIds, excludedTagsFor } from './core/restrictions.js';
import { mountRestrictions } from './ui/restrictions.js';
import { mountTagFilter } from './ui/tag-filter.js';
import { isAggregateView, isIndividualView } from './core/view-levels.js';
import { loadJson, loadJsonSafe, loadArraySafe } from './util/load.js';
import { showBootError, hideBootOverlay, wireBootResetButton } from './boot-error.js';
import {
  defaultConstraintFor, defaultConstraintForServing,
  AXIS_CONSTRAINT_DEFAULTS, AXIS_CONSTRAINT_DEFAULTS_SERVING,
} from './core/nutrient-defaults.js';

const SNAP_POSITIONS = {
  x:    new THREE.Vector3(3.5, 0.5, 0.5),
  y:    new THREE.Vector3(0.5, 3.5, 0.5),
  z:    new THREE.Vector3(0.5, 0.5, 3.5),
  free: new THREE.Vector3(2.4, 1.9, 2.4),
};

function buildFloorGrid(scene) {
  // Slightly larger than the unit cube + a small y-offset so the grid
  // sits clearly below the ingredient spheres.
  const grid = new THREE.GridHelper(2, 10);
  grid.position.set(0.5, -0.04, 0.5);
  scene.add(grid);

  function refreshColor() {
    const color = readCssColor('--color-axis-tick', '#888');
    const apply = (m) => {
      m.color.copy(color);
      m.transparent = true;
      m.opacity = 0.22;
      m.needsUpdate = true;
    };
    if (Array.isArray(grid.material)) grid.material.forEach(apply);
    else apply(grid.material);
  }
  refreshColor();

  return { grid, refreshColor };
}

async function boot() {
  window.__foodMapState = state;

  /* Phase 40 round 5: `let` declared at the top of boot() so the
   * updateEmptyFilterOverlay function (defined later but invoked by
   * the very first applyFilterToScene during boot) can read it
   * without hitting the TDZ. Mutated by the OK button handler and by
   * updateEmptyFilterOverlay itself. */
  let emptyOverlayAcknowledged = false;

  /* Phase 40 round 7: rawMealById Map declared up here for the same
   * reason — getRawMealForFilter / mealDietCuisineHidden run during
   * the first applyFilterToScene before the original later
   * initialization site would have executed. Assigned in the data
   * load block once meals.json is available. */
  let rawMealById = new Map();

  const title = document.querySelector('.app-title');
  if (title) title.textContent = 'Food Map';

  state.subscribe(s => s.theme, theme => {
    // eslint-disable-next-line no-console
    console.log(`[ingredient-map] theme → ${theme}`);
  });

  const container = document.getElementById('canvas-container');
  if (!container) {
    console.error('[ingredient-map] #canvas-container not found');
    return;
  }

  let ingredients;
  let meals;
  let compositionalMeals = [];
  let corpusTitledMeals = [];
  let ranges;
  try {
    [ingredients, meals, compositionalMeals, corpusTitledMeals] = await Promise.all([
      loadJson('src/data/ingredients.json'),
      loadJson('src/data/meals.json'),
      // Phase 36: compositional (corpus-derived) meal patterns. If the
      // file is missing (e.g., dev environment without the corpus), fall
      // back to an empty list so the rest of the app still boots.
      loadJson('src/data/compositional-meals.json').catch(() => []),
      // Corpus-titled meals: recognizable dish names lifted from the
      // RecipeNLG corpus that aren't already represented in the curated
      // or compositional sets. Each has an inferred ingredient_categories
      // list and a frequency reflecting how many corpus recipes it covers.
      loadJson('src/data/corpus-titled-meals.json').catch(() => []),
    ]);
    /* Phase 40 round 7: recompute the four nutrient-derived tags from
     * each ingredient's actual per-100g values. Curated identity tags
     * (breakfast, snack, etc.) survive unchanged. Tester reported a
     * "high-fiber" check still surfacing 0.9 g/100g items — the stored
     * tags had drifted from the documented thresholds, and the only
     * honest fix is to re-derive at runtime so the data file never
     * outvotes the numbers. */
    for (const ing of ingredients) {
      ing.tags = effectiveTags(ing);
    }
    /* Boot-time indexes: ingredients grouped by category and food_group.
     * The category/food-group filter helpers were scanning all 1,362
     * ingredients per call; with these maps they iterate only the
     * categories (~66) or food groups (12) that actually matter. The
     * dataset is immutable at runtime so these maps never need rebuilding. */
    const ingredientsByCategory = new Map();
    const ingredientsByFoodGroup = new Map();
    for (const ing of ingredients) {
      if (ing.category) {
        let list = ingredientsByCategory.get(ing.category);
        if (!list) { list = []; ingredientsByCategory.set(ing.category, list); }
        list.push(ing);
      }
      if (ing.food_group) {
        let list = ingredientsByFoodGroup.get(ing.food_group);
        if (!list) { list = []; ingredientsByFoodGroup.set(ing.food_group, list); }
        list.push(ing);
      }
    }
    /* Phase 40 round 7: raw-meal lookup built early so the Diet +
     * Cuisine filter can resolve meal aggregates back to their source
     * entries during the very first applyFilterToScene that runs
     * during boot. Re-populated for user meals dynamically via the
     * helper below the Map definition. */
    rawMealById = new Map();
    for (const m of meals)              rawMealById.set(m.id, m);
    for (const m of compositionalMeals) rawMealById.set(m.id, m);
    for (const m of corpusTitledMeals)  rawMealById.set(m.id, m);
    ranges = computeRanges(ingredients);
    // Axis constraint defaults are module-scope (see top of file). The
    // per-call helper passes in `ranges` so we can fall back to the
    // dataset envelope for any nutrient without an explicit preset.
    const defaultConstraint = (nutrient) => defaultConstraintFor(nutrient, ranges);
    // Seed the per-nutrient prefs cache so every nutrient (not just the 3
    // on the initial axes) has saved settings the picker can restore.
    const nutrientPrefs = {};
    for (const nutrient of NUTRIENT_FIELDS) {
      const defaults = NUTRIENT_DEFAULTS[nutrient];
      nutrientPrefs[nutrient] = {
        direction: defaults.direction,
        orientation: defaults.orientation,
        constraint: defaultConstraint(nutrient),
      };
    }
    const initialAxes = DEFAULT_AXES.map(a => ({
      ...a,
      constraint: defaultConstraint(a.nutrient),
    }));
    /* Phase 40 round 13: per-serving axis-constraint defaults stored
     * in their own slot. State.axes mirrors the slot matching the
     * current nutrientUnit; a subscription below keeps them in sync. */
    const initialAxesServing = DEFAULT_AXES.map(a => ({
      ...a,
      constraint: defaultConstraintForServing(a.nutrient, ranges),
    }));
    // Restore table preferences from localStorage if present; fall back to
    // defaults (all columns visible, all composite weights = 1).
    // Phase 13.5 round 3: removed the "group" (animal/plant/dairy) column
    // — the colored dot next to the Name cell already conveys it, and the
    // legend (now visible in table view too) is the canonical key.
    // Subcategory stays off by default; food_group is on.
    const defaultTableColumns = Object.fromEntries([
      ['food_group',  true],
      ['category',    true],
      ['subcategory', false],
      ...NUTRIENT_FIELDS.map(n => [n, true]),
      ['composite',   true],
    ]);
    const defaultCompositeWeights = Object.fromEntries(
      NUTRIENT_FIELDS.map(n => [n, 1])
    );
    const tableColumns     = loadJsonSafe(LS_TABLE_COLUMNS, defaultTableColumns);
    const compositeWeights = loadJsonSafe(LS_TABLE_WEIGHTS, defaultCompositeWeights);
    const userMeals        = loadArraySafe(LS_USER_MEALS, []);

    const defaultConstraintServing = (nutrient) => defaultConstraintForServing(nutrient, ranges);
    /* Batch 14 fix: the slider bar size per unit IS the threshold default.
     *
     * Earlier the slider bar was unit-agnostic (max of envelope + 100g
     * default + serving default) but the initial threshold value was the
     * per-unit preset — narrower than the bar. The handle started at the
     * bar's midpoint in many nutrients (calories+carbs in 100g, fiber/
     * sodium/saturated_fat/iron in serving), which violated the user's
     * mental model that "the default IS at the slider edges". Now the
     * slider resizes per unit, and the handle is always at the bar's
     * edges on boot.
     *
     * defaultThresholdsMap / defaultThresholdsMapServing back this:
     * isThresholdsAtDefaults uses them, so the filter is dormant when
     * the user hasn't moved any handle off its bar edge.
     *
     * `var` declaration so the function is hoisted out of the try block
     * — mountNutrientThresholds (post-try) closes over it. A plain
     * `function` declaration would be block-scoped in strict mode and
     * unreachable from the outer code. */
    var sliderBaselineFor = function (nutrient, unit) {
      if (unit === 'serving') {
        const b = defaultConstraintForServing(nutrient, ranges);
        return { min: b.min, max: b.max };
      }
      const r = ranges[nutrient];
      const a = defaultConstraintFor(nutrient, ranges);
      return { min: Math.min(r.min, a.min), max: Math.max(r.max, a.max) };
    };
    const initialThresholds = {};
    const initialThresholdsServing = {};
    var defaultThresholdsMap = {};
    var defaultThresholdsMapServing = {};
    for (const nutrient of NUTRIENT_FIELDS) {
      const b100g = sliderBaselineFor(nutrient, '100g');
      const bServ = sliderBaselineFor(nutrient, 'serving');
      initialThresholds[nutrient]         = { ...b100g };
      initialThresholdsServing[nutrient]  = { ...bServ };
      defaultThresholdsMap[nutrient]      = { ...b100g };
      defaultThresholdsMapServing[nutrient] = { ...bServ };
    }
    state.set({
      ingredients,
      normalized: { ranges },
      nutrientPrefs,
      axes: initialAxes,
      axes100g: initialAxes,
      axesServing: initialAxesServing,
      thresholds: initialThresholds,
      thresholdsServing: initialThresholdsServing,
      tableColumns,
      compositeWeights,
      userMeals,
    });

    // Phase 12: hydrate persisted state on top of the just-seeded
    // defaults. Anything the user saved last session overrides; new
    // fields (added in future versions) fall back to defaults.
    const persistedPatch = hydratePatch();
    if (Object.keys(persistedPatch).length > 0) {
      /* Tester feedback: thresholds must survive a refresh as the user
       * set them. The earlier "expand to envelope" safety net silently
       * widened any narrowed window back to the default — a user who
       * dragged carbs to [0, 30] would reload and find [0, 100] again.
       * We now backfill any missing nutrient from defaults, but never
       * widen a persisted range. The empty-filter overlay already
       * handles the case where a stale narrow range hides everything. */
      for (const slotKey of ['thresholds', 'thresholdsServing']) {
        if (!persistedPatch[slotKey]) continue;
        const next = { ...persistedPatch[slotKey] };
        const def = slotKey === 'thresholdsServing'
          ? defaultConstraintServing : defaultConstraint;
        for (const nutrient of NUTRIENT_FIELDS) {
          if (!next[nutrient]) next[nutrient] = def(nutrient);
        }
        persistedPatch[slotKey] = next;
      }
      /* Tester feedback: axis ranges (and nutrientPrefs) must persist
       * verbatim, same as thresholds. The earlier safety net widened
       * every persisted constraint to the default envelope on hydration,
       * undoing any narrowing the user had applied (e.g. zooming
       * calories to 0–300 reverted to 0–1000 on reload). We now only
       * backfill missing constraints; existing windows ride through
       * untouched. */
      function backfillConstraint(c, nutrient, defFn) {
        if (c && Number.isFinite(c.min) && Number.isFinite(c.max)) return c;
        return defFn(nutrient);
      }
      const fill100g    = (c, n) => backfillConstraint(c, n, defaultConstraint);
      const fillServing = (c, n) => backfillConstraint(c, n, defaultConstraintServing);
      if (Array.isArray(persistedPatch.axes)) {
        persistedPatch.axes = persistedPatch.axes.map(a => a
          ? { ...a, constraint: fill100g(a.constraint, a.nutrient) }
          : a);
      }
      if (Array.isArray(persistedPatch.axes100g)) {
        persistedPatch.axes100g = persistedPatch.axes100g.map(a => a
          ? { ...a, constraint: fill100g(a.constraint, a.nutrient) }
          : a);
      }
      if (Array.isArray(persistedPatch.axesServing)) {
        persistedPatch.axesServing = persistedPatch.axesServing.map(a => a
          ? { ...a, constraint: fillServing(a.constraint, a.nutrient) }
          : a);
      }
      if (persistedPatch.nutrientPrefs && typeof persistedPatch.nutrientPrefs === 'object') {
        const np = { ...persistedPatch.nutrientPrefs };
        for (const nutrient of NUTRIENT_FIELDS) {
          if (!np[nutrient]) continue;
          np[nutrient] = {
            ...np[nutrient],
            constraint: fill100g(np[nutrient].constraint, nutrient),
          };
        }
        persistedPatch.nutrientPrefs = np;
      }
      state.set(persistedPatch);
    }
    // eslint-disable-next-line no-console
    console.log(`[ingredient-map] loaded ${ingredients.length} ingredients and ${meals.length} meal patterns`);
  } catch (err) {
    // Re-throw so the outer boot overlay surfaces this to the user.
    throw new Error(`Dataset load failed: ${err.message || err}`, { cause: err });
  }

  const scn = createScene(container);
  const controls = attachControls(scn.getActiveCamera(), scn.renderer.domElement);

  let axesHandle = buildAxes(scn.scene, state.get('axes'), ranges);

  // Phase 13.5 round 3: axis labels (tick values, axis names, Best/Worst
  // markers) can be toggled off so they don't obscure dots underneath.
  // Keep the labelsGroup.visible in sync with state on every rebuild.
  function applyAxisLabelsVisibility() {
    if (axesHandle && axesHandle.labelsGroup) {
      axesHandle.labelsGroup.visible = state.get('axisLabelsVisible') !== false;
    }
  }
  applyAxisLabelsVisibility();
  state.subscribe(s => s.axisLabelsVisible, applyAxisLabelsVisibility);

  // Phase 11: subtle floor grid for spatial reference. Sits just below
  // the unit cube on the XZ plane; theme-driven color via readCssColor
  // so it flips with dark/light mode like everything else in the scene.
  const floorGrid = buildFloorGrid(scn.scene);
  state.subscribe(s => s.theme, () => floorGrid.refreshColor());

  // category → Set(food_groups) — mirrors the map built in meal-builder.js
  // so the Meals view's scene filter can resolve curated meals' categories
  // to food_groups when applying the food_group exclusion filter.
  const foodGroupsByCategory = new Map();
  for (const ing of ingredients) {
    let set = foodGroupsByCategory.get(ing.category);
    if (!set) { set = new Set(); foodGroupsByCategory.set(ing.category, set); }
    set.add(ing.food_group);
  }

  function activeDataset() {
    const level = state.get('viewLevel');
    if (level === 'category') return aggregateByCategory(ingredients, state.get('categoryGroupBy'));
    if (level === 'meal') {
      // Phase 35: pass the composition overlay through to aggregateAllMeals
      // so each curated meal's plotted position reflects the user's added
      // / removed categories. Empty composition leaves positions unchanged.
      const composition = state.get('mealComposition') || { added: [], removed: [] };
      // Phase 36 (revised in Phase 40): plot named (curated + user) meals
      // alongside corpus-derived compositional patterns. The dedicated
      // source toggle was removed; both source kinds always render and
      // the user disambiguates via the existing visual treatment
      // (curated dots full-size, corpus dots smaller + dimmed).
      let mealsForAgg = [...meals, ...compositionalMeals, ...corpusTitledMeals];
      let userMealsForAgg = state.get('userMeals') || [];

      // Phase 37: when the user is actively remixing a meal, splice in
      // a draft version with the edited category list. The draft's id
      // matches the original so the selection stays anchored as the dot
      // shifts. Applies to curated/corpus meals AND category-shaped user
      // meals; ingredient-shaped user meals (whose identity is a gram
      // mixture) are not draftable here.
      const draft = state.get('mealDraft');
      if (draft && draft.mealId && Array.isArray(draft.categories)) {
        mealsForAgg = mealsForAgg.map(m => m.id === draft.mealId
          ? { ...m, ingredient_categories: draft.categories.slice() }
          : m);
        userMealsForAgg = userMealsForAgg.map(m => {
          if (m.id !== draft.mealId) return m;
          if (Array.isArray(m.ingredient_categories)) {
            return { ...m, ingredient_categories: draft.categories.slice() };
          }
          return m;
        });
      }

      const all = aggregateAllMeals(
        ingredients,
        mealsForAgg,
        userMealsForAgg,
        composition,
      );
      /* Batch 4 ingredient-level remix: when the draft carries an explicit
       * ingredient id list, recompute just that meal's dot from those specific
       * ingredients (gram-weighted) instead of its category means. Done after
       * aggregation since the meal aggregates by category by default. */
      if (draft && draft.mealId && Array.isArray(draft.ingredients)) {
        for (let i = 0; i < all.length; i++) {
          if (all[i].id === draft.mealId) {
            all[i] = aggregateIngredientDraft(all[i], ingredients, draft.ingredients);
            break;
          }
        }
      }
      const f = state.get('mealFilters');
      const restrictions = state.get('restrictions') || [];
      if (isMealFiltersEmpty(f) && restrictions.length === 0) return all;
      return filterMealsByMealFilters(all, ingredients, mealsForAgg, userMealsForAgg, f, restrictions);
    }
    return ingredients;
  }

  function filterMealsByMealFilters(aggregates, ingredients, curatedMeals, userMeals, filters, restrictions = []) {
    const ingredientById = new Map(ingredients.map(ingredient => [ingredient.id, ingredient]));
    // category -> [ingredient]; the category-shape restriction check below needs
    // to know whether a referenced category is ENTIRELY restricted (no in-category
    // substitution would make the meal acceptable).
    const ingredientsByCategory = new Map();
    for (const ing of ingredients) {
      if (!ing.category) continue;
      let list = ingredientsByCategory.get(ing.category);
      if (!list) { list = []; ingredientsByCategory.set(ing.category, list); }
      list.push(ing);
    }
    const curatedById = new Map(curatedMeals.map(m => [m.id, m]));
    const userById = new Map(userMeals.map(m => [m.id, m]));
    const ingredientIds         = filters.ingredientIds         || [];
    const ingredientIdsExcluded = filters.ingredientIdsExcluded || [];
    const categories            = filters.categories            || [];
    const categoriesExcluded    = filters.categoriesExcluded    || [];
    // Phase 40.2: nutrients is now a { nutrient: { min, max } } map.
    const nutrientsRaw = filters.nutrients;
    const nutrients = (nutrientsRaw && typeof nutrientsRaw === 'object' && !Array.isArray(nutrientsRaw))
      ? nutrientsRaw : {};
    const nutrientKeys = Object.keys(nutrients);
    const foodGroupsExcluded    = filters.foodGroupsExcluded    || [];
    const restrictedAllowed     = passingIngredientIds(ingredients, restrictions);

    const excludedSet = foodGroupsExcluded.length > 0 ? new Set(foodGroupsExcluded) : null;

    // Phase 37: category-shape user meals (saved remixes) carry an
    // ingredient_categories array and must be filtered against the
    // curated path, not the ingredient-grams path.
    const isCategoryRaw = raw => Array.isArray(raw.ingredient_categories) && raw.ingredient_categories.length > 0;

    return aggregates.filter(agg => {
      const src = agg.isUserMade ? 'user' : 'curated';
      const raw = src === 'user' ? userById.get(agg.id) : curatedById.get(agg.id);
      if (!raw) return true;
      const useCategoryShape = src === 'curated' || isCategoryRaw(raw);

      if (ingredientIds.length > 0) {
        let matches = false;
        if (!useCategoryShape) {
          matches = (raw.ingredients || []).some(ing => ingredientIds.includes(ing.ingredientId));
        } else {
          const cats = new Set(raw.ingredient_categories || []);
          matches = ingredientIds.some(fid => {
            const f = ingredientById.get(fid);
            return f && cats.has(f.category);
          });
        }
        if (!matches) return false;
      }
      // Phase 33: ingredient-level EXCLUDE.
      if (ingredientIdsExcluded.length > 0) {
        if (!useCategoryShape) {
          const has = (raw.ingredients || []).some(ing => ingredientIdsExcluded.includes(ing.ingredientId));
          if (has) return false;
        } else {
          const cats = new Set(raw.ingredient_categories || []);
          const has = ingredientIdsExcluded.some(fid => {
            const f = ingredientById.get(fid);
            return f && cats.has(f.category);
          });
          if (has) return false;
        }
      }
      if (categories.length > 0) {
        let matches = false;
        if (!useCategoryShape) {
          matches = (raw.ingredients || []).some(ing => {
            const f = ingredientById.get(ing.ingredientId);
            return f && categories.includes(f.category);
          });
        } else {
          matches = (raw.ingredient_categories || []).some(c => categories.includes(c));
        }
        if (!matches) return false;
      }
      // Phase 33: category-level EXCLUDE.
      if (categoriesExcluded.length > 0) {
        if (!useCategoryShape) {
          const has = (raw.ingredients || []).some(ing => {
            const f = ingredientById.get(ing.ingredientId);
            return f && categoriesExcluded.includes(f.category);
          });
          if (has) return false;
        } else {
          const has = (raw.ingredient_categories || []).some(c => categoriesExcluded.includes(c));
          if (has) return false;
        }
      }
      if (nutrientKeys.length > 0) {
        let allInRange = true;
        for (const n of nutrientKeys) {
          const entry = nutrients[n];
          if (!entry || typeof entry !== 'object') continue;
          const v = agg[n];
          if (!Number.isFinite(v)) continue;
          if (Number.isFinite(entry.min) && v < entry.min) { allInRange = false; break; }
          if (Number.isFinite(entry.max) && v > entry.max) { allInRange = false; break; }
        }
        if (!allInRange) return false;
      }
      if (excludedSet) {
        if (!useCategoryShape) {
          const hit = (raw.ingredients || []).some(ing => {
            const f = ingredientById.get(ing.ingredientId);
            return f && excludedSet.has(f.food_group);
          });
          if (hit) return false;
        } else {
          const hit = (raw.ingredient_categories || []).some(cat => {
            const groups = foodGroupsByCategory.get(cat);
            if (!groups) return false;
            for (const g of groups) if (excludedSet.has(g)) return true;
            return false;
          });
          if (hit) return false;
        }
      }
      if (restrictedAllowed) {
        /* Batch 14: meal-level `contains` tags trump the category check.
         * 'Sweet-and-sour pork' / 'Pasta carbonara' / 'Bangers and mash'
         * etc. carry `contains: ["pork"]` because the category 'Red meat'
         * (or 'Processed meat') alone can't distinguish pork from beef
         * options. If ANY active restriction excludes any of the meal's
         * own contains tags, hide. */
        const mealContains = Array.isArray(raw.contains) ? raw.contains : [];
        if (mealContains.length > 0) {
          const excludedTags = excludedTagsFor(restrictions);
          for (const t of mealContains) {
            if (excludedTags.has(t)) return false;
          }
        }
        if (!useCategoryShape) {
          /* Ingredient-shape: every named ingredient must pass. */
          const hit = (raw.ingredients || []).some(ing => {
            const f = ingredientById.get(ing.ingredientId);
            return f && !restrictedAllowed.has(f.id);
          });
          if (hit) return false;
        } else {
          /* Batch 13: category-shape meals are slot-templates — a
           * referenced category like 'Red meat' is a slot the meal
           * fills with SOME ingredient from that category, not a
           * commitment to every member. The previous logic ("any
           * restricted ingredient in any referenced category → hide")
           * hid 49% of meals under halal: Burger, Steak dinner, Cobb
           * salad, etc. all share 'Red meat' with pork variants and
           * got incorrectly excluded even though they can clearly be
           * made with beef.
           *
           * New rule: a meal is incompatible only if some referenced
           * category is ENTIRELY restricted — no in-category
           * substitution would make it acceptable. 'Alcoholic
           * beverages' (33/33 restricted under halal) still hides the
           * meal. 'Red meat' (9/39) does not.
           *
           * Strict restrictions (vegetarian, vegan, etc.) still hide
           * meat-bearing meals correctly because every member of
           * 'Red meat' / 'White meat' / 'Seafood' carries the 'meat'
           * or 'fish' tag — the entire category is restricted. */
          for (const cat of raw.ingredient_categories || []) {
            const list = ingredientsByCategory.get(cat);
            if (!list || list.length === 0) continue;
            const anyAllowed = list.some(f => restrictedAllowed.has(f.id));
            if (!anyAllowed) return false;
          }
        }
      }
      return true;
    });
  }

  // Cache so pointermove (which calls getIngredients on every mouse pixel) doesn't
  // recompute the aggregation each tick.
  let currentDataset = activeDataset();
  let firstPointsBuild = true;
  let pointsHandle = buildPoints(scn.scene, currentDataset, state.get('axes'), ranges,
    { animate: firstPointsBuild });
  firstPointsBuild = false;

  // Phase 13.5 round 3: persisted color scheme applies immediately and
  // on every rebuild.
  function applyColorScheme() {
    if (pointsHandle && pointsHandle.setColorScheme) {
      pointsHandle.setColorScheme(state.get('colorScheme') || 'rgb');
    }
  }
  applyColorScheme();
  state.subscribe(s => s.colorScheme, applyColorScheme);

  // Phase 13.75: legend checkboxes filter ingredients by color
  // category. An ingredient's dominant channel (A/P/D scheme) or
  // dominant food_group (food_group scheme) is matched against the
  // current hidden list; matches render dimmer + smaller via
  // pointsHandle.setColorFilteredSet.
  function computeColorFilteredSet() {
    const scheme = state.get('colorScheme') || 'rgb';
    const lh = state.get('legendHidden') || {};
    const hidden = Array.isArray(lh[scheme]) ? lh[scheme] : [];
    if (hidden.length === 0) return null;
    const hiddenSet = new Set(hidden);
    const out = new Set();
    const dataset = currentDataset || [];
    for (const ing of dataset) {
      if (scheme === 'rgb') {
        const gw = ing.group_weights || [0, 0, 0];
        let idx = 0, max = -Infinity;
        for (let i = 0; i < 3; i++) if (gw[i] > max) { max = gw[i]; idx = i; }
        if (hiddenSet.has(['animal', 'plant', 'dairy'][idx])) out.add(ing.id);
      } else {
        let dom = ing.food_group;
        if (ing.food_group_weights) {
          let max = -Infinity;
          for (const [g, w] of Object.entries(ing.food_group_weights)) {
            if (w > max) { max = w; dom = g; }
          }
        }
        if (dom && hiddenSet.has(dom)) out.add(ing.id);
      }
    }
    return out;
  }
  /* Phase 40 round 3: legend unchecks used to drive a separate
   * "color-filtered" set on the InstancedMesh (smaller + dimmed). They
   * now fold into the universal hiddenSet via applyFilterToScene, so
   * this just clears the legacy slot and lets applyFilterToScene do the
   * real work whenever legendHidden / colorScheme changes. */
  function applyColorFilter() {
    if (pointsHandle && pointsHandle.setColorFilteredSet) {
      pointsHandle.setColorFilteredSet(null);
    }
    applyFilterToScene();
  }
  applyColorFilter();
  state.subscribe(s => s.legendHidden, applyColorFilter);
  state.subscribe(s => s.colorScheme,  applyColorFilter);

  // Phase 9 user-meal rings + connector lines. Always referenced against
  // the ingredient-level positions (not the current viewLevel's aggregates),
  // so visibility is gated to the individual viewLevel below.
  const mealsHandle = buildMeals(scn.scene, ingredients, state.get('axes'), ranges);
  function refreshMeals() {
    mealsHandle.update(state.get('userMeals') || []);
    mealsHandle.setVisible(isIndividualView(state.get('viewLevel')));
  }
  refreshMeals();

  // --- State subscriptions ---

  state.subscribe(s => s.axes, (axes) => {
    disposeAxes(axesHandle.group);
    axesHandle = buildAxes(scn.scene, axes, ranges);
    applyAxisLabelsVisibility();
    pointsHandle.setAxes(axes);
    mealsHandle.setAxes(axes);
    refreshMeals();
  });

  state.subscribe(s => s.viewLevel, () => {
    pointsHandle.dispose();
    currentDataset = activeDataset();
    pointsHandle = buildPoints(scn.scene, currentDataset, state.get('axes'), ranges,
      { animate: false });
    applyColorScheme();
    applyColorFilter();
    applyFilterToScene();
    reapplyPointHandleState();
    refreshMeals();
    // Selection's id was meaningful only in the previous dataset.
    if (state.get('selectedIngredientId') !== null) state.set({ selectedIngredientId: null });
  });

  // Phase 13.5 round 7: switching the Categories grouping (food_group /
  // category / subcategory) rebuilds the dataset just like a viewLevel
  // change, but only while we're actually in category view.
  state.subscribe(s => s.categoryGroupBy, () => {
    if (state.get('viewLevel') !== 'category') return;
    pointsHandle.dispose();
    currentDataset = activeDataset();
    pointsHandle = buildPoints(scn.scene, currentDataset, state.get('axes'), ranges,
      { animate: false });
    applyColorScheme();
    applyColorFilter();
    applyFilterToScene();
    reapplyPointHandleState();
    if (state.get('selectedIngredientId') !== null) state.set({ selectedIngredientId: null });
  });

  function rebuildMealsPointsIfActive() {
    if (state.get('viewLevel') !== 'meal') return;
    pointsHandle.dispose();
    currentDataset = activeDataset();
    pointsHandle = buildPoints(scn.scene, currentDataset, state.get('axes'), ranges,
      { animate: false });
    applyColorScheme();
    applyColorFilter();
    applyFilterToScene();
    reapplyPointHandleState();
  }

  /* Phase 40.3 + 40.6: helper that re-pushes the slices the new
   * pointsHandle doesn't carry across a dispose/rebuild (selection
   * pulse target + size-axis config). Called from every rebuild
   * subscriber so the pulsing dot doesn't vanish on view-level swap. */
  function reapplyPointHandleState() {
    if (!pointsHandle) return;
    if (pointsHandle.setSelectedId) {
      pointsHandle.setSelectedId(state.get('selectedIngredientId'));
    }
    if (pointsHandle.setPreviewId) {
      pointsHandle.setPreviewId(state.get('previewIngredientId'));
    }
    if (pointsHandle.setSizeAxis) {
      pointsHandle.setSizeAxis(state.get('sizeAxis'));
    }
    /* Phase 40 round 10: nutrient unit drives positions — reapply
     * after every rebuild so the per-serving setting survives a
     * view-level swap. */
    if (pointsHandle.setNutrientUnit) {
      pointsHandle.setNutrientUnit(state.get('nutrientUnit') || '100g');
    }
  }

  state.subscribe(s => s.userMeals, () => {
    refreshMeals();
    rebuildMealsPointsIfActive();
    try { localStorage.setItem(LS_USER_MEALS, JSON.stringify(state.get('userMeals'))); }
    catch { /* localStorage full or unavailable — meals stay in memory */ }
  });

  state.subscribe(s => s.mealFilters, () => {
    rebuildMealsPointsIfActive();
  });
  state.subscribe(s => s.restrictions, () => {
    rebuildMealsPointsIfActive();
  });
  // Phase 35: composition overlay reshapes every curated meal's effective
  // category list, which moves dots in the Meals view.
  state.subscribe(s => s.mealComposition, () => {
    rebuildMealsPointsIfActive();
  });
  // Phase 37: per-meal remix draft. Each draft mutation rebuilds the
  // meals points so the selected dot moves to the new centroid.
  state.subscribe(s => s.mealDraft, () => {
    rebuildMealsPointsIfActive();
  });
  // Phase 37: clear the draft when the user navigates away from the
  // selected meal — the draft only makes sense while the panel is open
  // on that meal. Switching selection to a different meal also clears.
  state.subscribe(s => s.selectedIngredientId, (id) => {
    const draft = state.get('mealDraft');
    if (draft && draft.mealId !== id) state.set({ mealDraft: null });
  });

  // --- Filter / threshold → scene reaction ---
  //
  // Ingredient filter (Phase 6) + nutrient thresholds (Phase 7) compose
  // into the active/score state the scene shows:
  //   mode=filter → activeSet = ingredientActive ∩ thresholdInRange
  //   mode=score  → activeSet = ingredientActive;
  //                 scoreMap = per-item gradient (color override)
  //
  // For category/meal views, the ingredient-level masks are translated to the
  // aggregate dataset's ids — an aggregate is active iff any of its
  // member ingredients is active.

  function translateSetToCurrent(ingredientIdSet) {
    if (!ingredientIdSet) return null;
    const level = state.get('viewLevel');
    if (isIndividualView(level)) return ingredientIdSet;
    // Phase 13.5 round 9: category view aggregates by the user-selected
    // field (food_group / category / subcategory). To translate an
    // ingredient-id set into the aggregate-id set, look up each
    // ingredient by the SAME field that built the aggregate's name —
    // otherwise every aggregate fails the lookup and renders inactive
    // (greyed), which is what made Subcategory view look washed out.
    const groupBy = level === 'category'
      ? (state.get('categoryGroupBy') || 'category')
      : 'category';
    const activeGroupKeys = new Set();
    for (const f of ingredients) {
      if (!ingredientIdSet.has(f.id)) continue;
      const key = f[groupBy];
      if (key) activeGroupKeys.add(key);
    }
    const out = new Set();
    if (level === 'category') {
      for (const cat of currentDataset) {
        if (activeGroupKeys.has(cat.name)) out.add(cat.id);
      }
    } else if (level === 'meal') {
      // Meals reference categories (by ingredient.category), so build a
      // separate category lookup here.
      const byCategory = new Set();
      for (const f of ingredients) {
        if (ingredientIdSet.has(f.id) && f.category) byCategory.add(f.category);
      }
      for (const meal of currentDataset) {
        const cats = meal.examples || [];
        if (cats.some(c => byCategory.has(c))) out.add(meal.id);
      }
    }
    return out;
  }

  /* Shared first-pass of the filter pipeline: reads all filter inputs
   * and builds the six ingredient-id "passing" sets that both the 3D
   * scene (applyFilterToScene) and the table view (tableHiddenSet) need.
   * Previously these two functions independently rebuilt all six sets
   * on every filter change — same work, twice. Centralizing here cuts
   * the per-mutation cost in half and ensures the two surfaces never
   * drift in their filter semantics.
   *
   * Phase 40 round 8 note: at aggregate views, tagActive is null — the
   * aggregate-direct tag pass below handles tags honestly using the
   * aggregate's own per-100g values rather than lifting "any member
   * carries the tag".
   *
   * Phase 40 round 11 note: thresholds are read from whichever set
   * matches the active nutrientUnit, and ingredient values are scaled
   * accordingly via getNutrientScale. */
  function computeAllFilterSets() {
    const level             = state.get('viewLevel');
    const isAggregate       = isAggregateView(level);
    const filter            = state.get('ingredientFilter');
    const thresholds        = activeThresholds();
    const restrictions      = state.get('restrictions') || [];
    const tagFilter         = state.get('tagFilter');
    const categoryFilter    = state.get('categoryFilter');
    const foodGroupFilter   = state.get('foodGroupFilter');
    const getNutrientScale  = nutrientScaleGetter();

    const ingredientActive = isFilterEmpty(filter) ? null : computeActiveSet(ingredients, filter);
    /* Batch 14: only enforce nutrient thresholds that the user has
     * actually moved off the bar edge. Some items legitimately exceed
     * the per-unit baseline (e.g. nut butters at ~50 g fat / serving
     * blow past the serving-fat default 100 g when one drag activates
     * the global threshold filter). Filtering only on the user's
     * actually-moved nutrients matches their mental model: "I dragged
     * calories, so calories should narrow — fat shouldn't kick in." */
    const effectiveThresholds = activeThresholdSlots(thresholds);
    const thresholdActive  = !effectiveThresholds
      ? null : thresholdActiveSet(ingredients, effectiveThresholds, getNutrientScale);
    const restrictionActive = passingIngredientIds(ingredients, restrictions);
    const tagActive = (isTagFilterEmpty(tagFilter) || isAggregate)
      ? null : tagActiveSet(ingredients, tagFilter, state.get('tagFilterMatch') || 'any');
    const categoryActive  = categoryFilterPassingIngredients(categoryFilter);
    const foodGroupActive = foodGroupFilterPassingIngredients(foodGroupFilter);

    return {
      level, isAggregate,
      filter, thresholds, restrictions, tagFilter, categoryFilter, foodGroupFilter,
      getNutrientScale,
      ingredientActive, thresholdActive, restrictionActive,
      tagActive, categoryActive, foodGroupActive,
    };
  }

  function applyFilterToScene() {
    const mode = state.get('thresholdMode') || 'filter';
    const {
      level, ingredientActive, thresholdActive, restrictionActive,
      tagActive, categoryActive, foodGroupActive,
      thresholds, getNutrientScale,
    } = computeAllFilterSets();

    /* Phase 40 round 3: per tester feedback, ALL filters now HIDE
     * non-matching dots rather than greying them. Build a single
     * "hiddenIngredientIds" set that's the union of every filter's
     * non-matching items, then translate it to the current view level
     * and feed it to pointsHandle.setHiddenSet. */
    /* Tester feedback: Score mode used to keep every dot visible
     * (only the gradient changed). The user wants the threshold
     * range to act as a filter AND drive the gradient — items
     * outside the range disappear, items inside get a green→red
     * tint reflecting their distance from the midpoint. So we
     * always include thresholdActive in the passing-set
     * combination, regardless of mode. */
    /* Batch 3: at meal view the ingredient filter is handled separately by
     * ingredientMealHidden (matches each meal's specific example_ingredients,
     * not its categories), so it's dropped from the category-based combine /
     * translateHiddenToCurrent path here. Category + individual views keep the
     * member-based behavior. */
    const ingredientActiveForCombine = level === 'meal' ? null : ingredientActive;
    const passingActiveCombined = combinePassingSets([
      ingredientActiveForCombine,
      restrictionActive,
      tagActive,
      categoryActive,
      foodGroupActive,
      thresholdActive,
    ]);
    const hiddenIngredientIds = passingActiveCombined
      ? new Set(ingredients.filter(f => !passingActiveCombined.has(f.id)).map(f => f.id))
      : null;

    /* Color-guide unchecks contribute to the hidden set. Tester
     * feedback: at Categories / Meals view the legend filter looked
     * dead because computeColorFilteredSet returns ids from the
     * CURRENT dataset (aggregate ids at aggregate views), but the
     * code path used to merge those into hiddenIngredientIds and run
     * the result through translateHiddenToCurrent — which expects
     * INGREDIENT ids and produced an empty set. We now fold
     * colorFilteredIds in AFTER translation so the ids stay in the
     * right space and the filter actually fires. */
    const colorFilteredIds = computeColorFilteredSet();

    // activeSet is now null — there's no greying treatment anymore.
    pointsHandle.setActiveSet(null);

    /* Phase 40 round 3: match-all override for aggregate views. When
     * ingredientFilterMatch === 'all' and viewLevel is meal/category,
     * an aggregate is required to contain EVERY checked ingredient's
     * category — not just ANY. This produces an extra set of
     * aggregate ids to hide on top of the universal translation. */
    let hiddenInCurrent = translateHiddenToCurrent(hiddenIngredientIds);
    /* Color-guide unchecks: fold AFTER translation so the ids are in
     * the current dataset's namespace (aggregate ids at aggregate
     * views, ingredient ids at individual view). */
    if (colorFilteredIds && colorFilteredIds.size > 0) {
      if (!hiddenInCurrent) hiddenInCurrent = new Set();
      for (const id of colorFilteredIds) hiddenInCurrent.add(id);
    }
    const matchAllHidden = computeMatchAllHidden(ingredientActive);
    if (matchAllHidden && matchAllHidden.size > 0) {
      if (!hiddenInCurrent) hiddenInCurrent = new Set();
      for (const id of matchAllHidden) hiddenInCurrent.add(id);
    }
    /* Batch 3: meal-level ingredient filter via specific example_ingredients. */
    const ingMealHidden = ingredientMealHidden(level);
    if (ingMealHidden && ingMealHidden.size > 0) {
      if (!hiddenInCurrent) hiddenInCurrent = new Set();
      for (const id of ingMealHidden) hiddenInCurrent.add(id);
    }
    /* Phase 40 round 4: same idea for categoryFilter — when match-all
     * is on, EVERY included category must appear in the aggregate. */
    const categoryMatchAllHidden = computeCategoryMatchAllHidden(state.get('categoryFilter'));
    if (categoryMatchAllHidden && categoryMatchAllHidden.size > 0) {
      if (!hiddenInCurrent) hiddenInCurrent = new Set();
      for (const id of categoryMatchAllHidden) hiddenInCurrent.add(id);
    }
    /* Aggregate-level threshold filtering. Same as the ingredient-
     * level threshold filter above: applies in BOTH filter and score
     * modes so the threshold range honestly hides out-of-range items
     * everywhere. */
    {
      const aggThresholdHidden = aggregateLevelThresholdHidden(thresholds, level);
      if (aggThresholdHidden && aggThresholdHidden.size > 0) {
        if (!hiddenInCurrent) hiddenInCurrent = new Set();
        for (const id of aggThresholdHidden) hiddenInCurrent.add(id);
      }
    }
    /* Phase 40 round 7: Diet + Cuisine — meal-only. */
    const dietCuisineHidden = mealDietCuisineHidden(level);
    if (dietCuisineHidden && dietCuisineHidden.size > 0) {
      if (!hiddenInCurrent) hiddenInCurrent = new Set();
      for (const id of dietCuisineHidden) hiddenInCurrent.add(id);
    }
    /* Phase 40 round 8: tag filter at aggregate views uses the
     * aggregate's own values for nutrient tags. */
    const aggTagHidden = aggregateLevelTagHidden(level);
    if (aggTagHidden && aggTagHidden.size > 0) {
      if (!hiddenInCurrent) hiddenInCurrent = new Set();
      for (const id of aggTagHidden) hiddenInCurrent.add(id);
    }
    /* Batch 4: aggregate-level food-group filter (stricter exclude +
     * AND/OR match) layered on top of the soft ingredient-level path. */
    const fgAggHidden = aggregateFoodGroupHidden(level);
    if (fgAggHidden && fgAggHidden.size > 0) {
      if (!hiddenInCurrent) hiddenInCurrent = new Set();
      for (const id of fgAggHidden) hiddenInCurrent.add(id);
    }
    /* Phase 40 round 9: SCOPE='all' hides — extras-not-allowed mode
     * per filter section. Composes with the inner AND/OR match logic. */
    for (const scopeFn of [
      ingredientScopeHidden, categoryScopeHidden, tagScopeHidden,
      dietCuisineScopeHidden, foodGroupScopeHidden,
    ]) {
      const h = scopeFn(level);
      if (h && h.size > 0) {
        if (!hiddenInCurrent) hiddenInCurrent = new Set();
        for (const id of h) hiddenInCurrent.add(id);
      }
    }

    /* Tester feedback: Score mode renormalizes the green→red gradient.
     * Previously this used the full currentDataset as the basis, so when
     * a filter hid the worst items (low protein, high sodium, etc.) the
     * surviving dots collapsed into the green end of the gradient — no
     * red visible in 3D even though the table view (which renormalizes
     * over its visible rows) showed red. The fix: pass a predicate so
     * computeScores only uses items the user can actually see when
     * computing min/max. Score is computed after hiddenInCurrent is
     * finalized for this reason. */
    let scoreMap = null;
    if (mode === 'score') {
      const visiblePredicate = (hiddenInCurrent && hiddenInCurrent.size > 0)
        ? (item) => !hiddenInCurrent.has(item.id)
        : null;
      scoreMap = computeScores(currentDataset, thresholds, ranges, getNutrientScale, visiblePredicate);
    }
    pointsHandle.setScoreMap(scoreMap);

    pointsHandle.setHiddenSet(hiddenInCurrent);

    // Phase 11 / 40 round 5: empty-filter detection. The overlay below
    // appears once on the transition from "some visible" → "none visible"
    // and is dismissed by the user via OK. The persistent warning lives
    // on the active-filters panel so the user can't forget that filters
    // are eating their dataset.
    const total = (currentDataset || []).length;
    const visibleCount = hiddenInCurrent
      ? Math.max(0, total - hiddenInCurrent.size)
      : total;
    const isEmpty = visibleCount === 0 && total > 0;
    updateEmptyFilterOverlay(isEmpty);
    if (isEmpty !== state.get('filtersHideAll')) {
      state.set({ filtersHideAll: isEmpty });
    }
  }

  /* Phase 40 round 5: the overlay is now a one-shot dialog the user
   * dismisses with OK. We track whether they've already acknowledged
   * the current empty state — once acknowledged, it stays dismissed
   * until the visible count climbs back up and falls again.
   *
   * The `emptyOverlayAcknowledged` `let` lives near the top of boot()
   * to avoid a TDZ trap: applyColorFilter() runs applyFilterToScene
   * during boot, which calls updateEmptyFilterOverlay before this point
   * would have executed if the let were declared here. */
  function updateEmptyFilterOverlay(isEmpty) {
    const overlay = document.getElementById('empty-filter');
    if (!overlay) return;
    if (!isEmpty) {
      // Visible items came back — reset the ack so the next descent to
      // zero will surface a fresh dialog.
      emptyOverlayAcknowledged = false;
      overlay.hidden = true;
      return;
    }
    overlay.hidden = emptyOverlayAcknowledged;
  }

  /* Phase 40 round 3: build the set of aggregate ids that fail the
   * match-all check (i.e. aggregates missing one or more of the
   * required categories derived from currently-checked ingredients).
   * Returns null when match-all is off or the current view doesn't
   * use the override (individual view). */
  /* Phase 40 round 4: match-all for the explicit Categories filter.
   * When match-all is on and the user includes multiple categories,
   * an aggregate must reference EVERY included one.
   *
   * Phase 40 round 6: now uses its OWN categoryFilterMatch state slot
   * so the user can set category-filter AND independently of
   * ingredient-filter AND. */
  function computeCategoryMatchAllHidden(cf) {
    if (!cf) return null;
    const match = state.get('categoryFilterMatch') || 'any';
    if (match !== 'all') return null;
    const included = Array.isArray(cf.included) ? cf.included : [];
    if (included.length === 0) return null;
    const level = state.get('viewLevel');
    if (isIndividualView(level)) return null;
    const reqSet = new Set(included);
    const toHide = new Set();
    if (level === 'category') {
      // A single category aggregate can carry only one category — so
      // if the user requires multiple, none satisfy.
      if (reqSet.size > 1) {
        for (const agg of currentDataset) toHide.add(agg.id);
      }
    } else if (level === 'meal') {
      for (const meal of currentDataset) {
        const mealCats = new Set(meal.examples || []);
        let ok = true;
        for (const req of reqSet) {
          if (!mealCats.has(req)) { ok = false; break; }
        }
        if (!ok) toHide.add(meal.id);
      }
    }
    return toHide;
  }

  function computeMatchAllHidden(ingredientActive) {
    const match = state.get('ingredientFilterMatch') || 'any';
    if (match !== 'all' || !ingredientActive) return null;
    const level = state.get('viewLevel');
    if (isIndividualView(level)) return null;

    const requiredCats = new Set();
    for (const f of ingredients) {
      if (ingredientActive.has(f.id) && f.category) requiredCats.add(f.category);
    }
    if (requiredCats.size === 0) return null;

    const toHide = new Set();
    if (level === 'category') {
      // Each category aggregate carries one category name. With
      // requiredCats > 1, no single aggregate can satisfy match-all,
      // so all of them hide. With requiredCats == 1, only aggregates
      // whose name matches that one stay visible.
      const required = requiredCats.size === 1 ? [...requiredCats][0] : null;
      for (const agg of currentDataset) {
        if (required == null || agg.name !== required) toHide.add(agg.id);
      }
    }
    // Batch 3: meal view's match-all is handled by ingredientMealHidden using
    // each meal's specific example_ingredients, not its categories.
    return toHide;
  }

  /* Tester-feedback Batch 3: the meal-level ingredient filter, keyed off each
   * meal's specific `example_ingredients` (the actual ingredients it uses)
   * rather than its categories — so "show meals that use bagels" returns only
   * meals that actually list a bagel, not every refined-grain meal. The
   * existing toggles carry over, with "selected" = the checked (non-excluded)
   * ingredients:
   *   match OR  — meal must contain at least one selected ingredient
   *   match AND — meal must contain every selected ingredient
   *   scope ALL — meal must contain ONLY selected ingredients (no extras),
   *               which is the "what can I make with just what I have" case
   * Meals with an empty example_ingredients list (e.g. a category-shape user
   * remix) are never constrained here. Category + individual views keep their
   * existing member/category-based semantics elsewhere. */
  function ingredientMealHidden(level) {
    if (level !== 'meal') return null;
    const filter = state.get('ingredientFilter');
    if (isFilterEmpty(filter)) return null;
    const selected = computeActiveSet(ingredients, filter);
    const match = state.get('ingredientFilterMatch') || 'any';
    const scope = state.get('ingredientFilterScope') || 'any';
    const out = new Set();
    for (const meal of (currentDataset || [])) {
      const E = meal.example_ingredients;
      if (!Array.isArray(E) || E.length === 0) continue;
      let pass;
      if (match === 'all') {
        // Every selected ingredient must be present. Impossible the moment the
        // selection outnumbers the meal's short ingredient list — bail early.
        if (selected.size > E.length) {
          pass = false;
        } else {
          pass = true;
          for (const s of selected) { if (!E.includes(s)) { pass = false; break; } }
        }
      } else {
        pass = false;
        for (const id of E) { if (selected.has(id)) { pass = true; break; } }
      }
      if (pass && scope === 'all') {
        for (const id of E) { if (!selected.has(id)) { pass = false; break; } }
      }
      if (!pass) out.add(meal.id);
    }
    return out.size > 0 ? out : null;
  }

  /* Intersect every non-null "passing" set into one. Returns null when
   * every input is null (= no filter is active). */
  function combinePassingSets(sets) {
    const real = sets.filter(Boolean);
    if (real.length === 0) return null;
    return real.reduce((acc, s) => acc ? intersectSets(acc, s) : s, null);
  }

  /* Phase 40 round 4: global Categories filter → set of passing
   * ingredient ids. An ingredient passes iff its category is in
   * `included` (or included is empty) AND not in `excluded`. Empty
   * filter → null = no constraint. */
  function categoryFilterPassingIngredients(cf) {
    if (!cf) return null;
    const included = Array.isArray(cf.included) ? cf.included : [];
    const excluded = Array.isArray(cf.excluded) ? cf.excluded : [];
    if (included.length === 0 && excluded.length === 0) return null;
    const excSet = new Set(excluded);
    const out = new Set();
    if (included.length > 0) {
      // Iterate only the included categories' ingredient lists.
      for (const cat of included) {
        if (excSet.has(cat)) continue;
        const list = ingredientsByCategory.get(cat);
        if (!list) continue;
        for (const f of list) out.add(f.id);
      }
    } else {
      // Include everything except the excluded categories.
      for (const [cat, list] of ingredientsByCategory) {
        if (excSet.has(cat)) continue;
        for (const f of list) out.add(f.id);
      }
    }
    return out;
  }

  /* Phase 40 round 4 / Batch 4: global Food groups filter is now tri-
   * state (included + excluded), matching the categories filter.
   * Returns the set of ingredient ids that pass the include AND exclude
   * checks. Empty filter → null = no constraint.
   *
   * The aggregate-level AND/OR + ANY/ALL semantics live in
   * aggregateFoodGroupHidden / foodGroupScopeHidden below — this
   * function only enforces the ingredient-level membership check, which
   * the shared translateHiddenToCurrent then lifts to aggregates with
   * the historical "every member hidden" semantic. The new aggregate-
   * level functions add the stricter hides on top. */
  function foodGroupFilterPassingIngredients(gf) {
    if (!gf) return null;
    const inc = Array.isArray(gf.included) ? gf.included : [];
    const exc = Array.isArray(gf.excluded) ? gf.excluded : [];
    if (inc.length === 0 && exc.length === 0) return null;
    const incSet = new Set(inc);
    const excSet = new Set(exc);
    const out = new Set();
    for (const [group, list] of ingredientsByFoodGroup) {
      if (excSet.has(group)) continue;
      if (incSet.size > 0 && !incSet.has(group)) continue;
      for (const f of list) out.add(f.id);
    }
    return out;
  }

  /* Batch 4: aggregate-level food-group filter for Meals and Categories
   * views. Tester feedback wanted the filter to compose like the diet+
   * cuisine and category filters — AND/OR for "which selected groups
   * must be present" and ANY/ALL for "extras allowed vs subset only".
   *
   * Excluded is stricter here than the soft translateHiddenToCurrent
   * path: if a meal references ANY excluded food_group it's hidden.
   * That matches user intuition ("I don't want Dairy in any of my
   * meals") even if the meal also contains permitted groups. */
  function aggregateFoodGroupHidden(level) {
    if (isIndividualView(level)) return null;
    const gf = state.get('foodGroupFilter') || {};
    const inc = Array.isArray(gf.included) ? gf.included : [];
    const exc = Array.isArray(gf.excluded) ? gf.excluded : [];
    if (inc.length === 0 && exc.length === 0) return null;
    const incArr = inc;
    const incSet = new Set(inc);
    const excSet = new Set(exc);
    const match = state.get('foodGroupFilterMatch') || 'any';

    function aggGroups(agg) {
      if (level === 'meal') {
        const cats = agg.examples || [];
        const groups = new Set();
        for (const cat of cats) {
          const cg = foodGroupsByCategory.get(cat);
          if (cg) for (const g of cg) groups.add(g);
        }
        return groups;
      }
      // category view: aggregate-name → food_groups (typically one).
      const cg = foodGroupsByCategory.get(agg.name);
      return cg || new Set();
    }

    const out = new Set();
    for (const agg of (currentDataset || [])) {
      const groups = aggGroups(agg);
      // Excluded: ANY excluded group in the aggregate → hide.
      if (excSet.size > 0) {
        let hit = false;
        for (const g of groups) if (excSet.has(g)) { hit = true; break; }
        if (hit) { out.add(agg.id); continue; }
      }
      // Included: AND requires every selected group present; OR (default)
      // requires at least one.
      if (incSet.size > 0) {
        let pass;
        if (match === 'all') {
          pass = incArr.every(g => groups.has(g));
        } else {
          pass = incArr.some(g => groups.has(g));
        }
        if (!pass) out.add(agg.id);
      }
    }
    return out.size > 0 ? out : null;
  }

  /* Batch 4: scope='all' (subset) constraint for the food-group filter.
   * An aggregate passes only when every food_group it references is in
   * the included set. Composes with the inner match (AND/OR) logic via
   * union of hide sets. */
  function foodGroupScopeHidden(level) {
    if (isIndividualView(level)) return null;
    if ((state.get('foodGroupFilterScope') || 'any') !== 'all') return null;
    const gf = state.get('foodGroupFilter') || {};
    const inc = Array.isArray(gf.included) ? gf.included : [];
    if (inc.length === 0) return null;
    const incSet = new Set(inc);

    function aggGroups(agg) {
      if (level === 'meal') {
        const cats = agg.examples || [];
        const groups = new Set();
        for (const cat of cats) {
          const cg = foodGroupsByCategory.get(cat);
          if (cg) for (const g of cg) groups.add(g);
        }
        return groups;
      }
      const cg = foodGroupsByCategory.get(agg.name);
      return cg || new Set();
    }

    const out = new Set();
    for (const agg of (currentDataset || [])) {
      const groups = aggGroups(agg);
      let pass = true;
      for (const g of groups) {
        if (!incSet.has(g)) { pass = false; break; }
      }
      if (!pass) out.add(agg.id);
    }
    return out.size > 0 ? out : null;
  }

  /* Phase 40 round 9: SCOPE = 'all' helpers. An item passes the scope
   * constraint when its full attribute set is a SUBSET of the user's
   * selection. Used in concert with the existing match (AND/OR) logic
   * to give the user four distinct semantics per filter.
   *
   * Returns a set of item ids to HIDE because they carry attributes
   * outside the selection. Returns null when the constraint doesn't
   * apply (scope='any', filter empty, or wrong view level). */

  function ingredientScopeHidden(level) {
    if ((state.get('ingredientFilterScope') || 'any') !== 'all') return null;
    if (isIndividualView(level)) return null; // each ingredient is itself
    // Batch 3: meal scope='all' (no extras) is handled inside
    // ingredientMealHidden against example_ingredients; this category-based
    // path now only applies to the Categories view.
    if (level === 'meal') return null;
    const filter = state.get('ingredientFilter');
    if (isFilterEmpty(filter)) return null;
    const excluded = new Set(filter.excludedIds || []);
    const selectedCats = new Set();
    for (const f of ingredients) {
      if (!excluded.has(f.id) && f.category) selectedCats.add(f.category);
    }
    if (selectedCats.size === 0) return null;
    return aggregateCategorySubsetHidden(level, selectedCats);
  }

  function categoryScopeHidden(level) {
    if ((state.get('categoryFilterScope') || 'any') !== 'all') return null;
    const cf = state.get('categoryFilter') || {};
    const included = Array.isArray(cf.included) ? cf.included : [];
    if (included.length === 0) return null;
    return aggregateCategorySubsetHidden(level, new Set(included));
  }

  /* Generic helper: hide aggregates whose category set is NOT a subset
   * of `allowed`. At meal view we check meal.examples; at categories
   * view we check the aggregate's own name (one-category set). */
  function aggregateCategorySubsetHidden(level, allowed) {
    const out = new Set();
    if (level === 'meal') {
      for (const meal of (currentDataset || [])) {
        const mealCats = meal.examples || [];
        for (const c of mealCats) {
          if (!allowed.has(c)) { out.add(meal.id); break; }
        }
      }
    } else if (level === 'category') {
      for (const agg of (currentDataset || [])) {
        if (!allowed.has(agg.name)) out.add(agg.id);
      }
    }
    return out.size > 0 ? out : null;
  }

  function tagScopeHidden(level) {
    if ((state.get('tagFilterScope') || 'any') !== 'all') return null;
    const tagF = state.get('tagFilter') || [];
    if (!Array.isArray(tagF) || tagF.length === 0) return null;
    const allowed = new Set(tagF);
    const out = new Set();
    if (isIndividualView(level)) {
      for (const ing of ingredients) {
        const itags = ing.tags || [];
        let ok = itags.length > 0;
        for (const t of itags) {
          if (!allowed.has(t)) { ok = false; break; }
        }
        if (!ok) out.add(ing.id);
      }
    } else {
      // Aggregate view — use effective aggregate tags.
      const identityTagSet = new Set(TAGS.filter(t => !NUTRIENT_TAG_KEYS.includes(t)));
      for (const agg of (currentDataset || [])) {
        const atags = effectiveAggregateTags(agg, level, identityTagSet);
        let ok = atags.length > 0;
        for (const t of atags) {
          if (!allowed.has(t)) { ok = false; break; }
        }
        if (!ok) out.add(agg.id);
      }
    }
    return out.size > 0 ? out : null;
  }

  /* Batch 4 (revised flat-selection semantics): the user said the
   * AND/OR shouldn't care about diet vs cuisine — selected items
   * across both sub-filters form one flat set. ANY/ALL (scope) still
   * applies per-sub-set when that sub-set is non-empty (selecting only
   * a diet shouldn't suddenly forbid all cuisines). Concretely:
   *
   *   ALL/AND — meal contains EVERY selected attribute AND has no
   *             extras within sub-sets the user has restricted.
   *   ALL/OR  — meal contains AT LEAST ONE selected attribute AND has
   *             no extras within restricted sub-sets.
   *   ANY/AND — meal contains every selected attribute; extras allowed.
   *   ANY/OR  — meal contains at least one selected attribute; extras
   *             allowed.
   *
   * The "no extras" subset constraint lives in dietCuisineScopeHidden
   * (this function) and the AND/OR match lives in mealDietCuisineHidden
   * — they layer via union of hide sets, same pattern as every other
   * filter pair in this file. */
  function dietCuisineScopeHidden(level) {
    if (level !== 'meal') return null;
    if ((state.get('dietCuisineFilterScope') || 'any') !== 'all') return null;
    const dietInc    = ((state.get('dietFilter')    || {}).included) || [];
    const cuisineInc = ((state.get('cuisineFilter') || {}).included) || [];
    if (dietInc.length === 0 && cuisineInc.length === 0) return null;
    const allowedDiets    = new Set(dietInc);
    const allowedCuisines = new Set(cuisineInc);
    const out = new Set();
    for (const meal of (currentDataset || [])) {
      const raw = getRawMealForFilter(meal.id);
      if (!raw) continue;
      let bad = false;
      // Diets sub-set: when the user has restricted diets, the meal's
      // diet_compatibility must be a subset of the allowed list.
      if (dietInc.length > 0) {
        const dc = Array.isArray(raw.diet_compatibility) ? raw.diet_compatibility : [];
        for (const d of dc) {
          if (!allowedDiets.has(d)) { bad = true; break; }
        }
      }
      // Cuisine sub-set: a meal has one cuisine. When the user has
      // restricted cuisines, the meal's cuisine must be in the list.
      // Empty meal.cuisine passes (treated as "no cuisine claim").
      if (!bad && cuisineInc.length > 0) {
        const c = raw.cuisine || '';
        if (c && !allowedCuisines.has(c)) bad = true;
      }
      if (bad) out.add(meal.id);
    }
    return out.size > 0 ? out : null;
  }

  /* Phase 40 round 8: aggregate-level tag filter. At Categories or
   * Meals view, computes each aggregate's effective tag set (nutrient
   * tags from the aggregate's own values, identity tags lifted from
   * any member ingredient) and hides aggregates failing the
   * AND/OR semantic. Only fires when at least one tag is selected
   * AND we're not in the individual view. */
  function aggregateLevelTagHidden(level) {
    if (isIndividualView(level)) return null;
    const tagFilter = state.get('tagFilter');
    if (!Array.isArray(tagFilter) || tagFilter.length === 0) return null;
    const matchMode = state.get('tagFilterMatch') || 'any';

    const identityTagSet = new Set(TAGS.filter(t => !NUTRIENT_TAG_KEYS.includes(t)));

    const out = new Set();
    for (const agg of (currentDataset || [])) {
      const aggTags = effectiveAggregateTags(agg, level, identityTagSet);
      const aggTagSet = new Set(aggTags);
      let pass;
      if (matchMode === 'all') {
        pass = tagFilter.every(t => aggTagSet.has(t));
      } else {
        pass = tagFilter.some(t => aggTagSet.has(t));
      }
      if (!pass) out.add(agg.id);
    }
    return out;
  }

  /* Build the effective tag set for an aggregate. Nutrient tags come
   * from the aggregate's per-100g values via NUTRIENT_TAG_RULES (so
   * "high-fiber" on a Meals aggregate means meal.fiber ≥ 6, not "one
   * ingredient is high-fiber"). Identity tags come from any member
   * ingredient — they don't have a numeric definition so the lift is
   * the honest answer.
   *
   * Batch 5b: meals also carry direct identity tags on the meal itself
   * (lunch/dinner/breakfast — meal-as-composed tags that don't fall out
   * of any one ingredient). Those merge in alongside the lifted member
   * tags so "Filter by tag → lunch" surfaces the curated lunch meals. */
  function effectiveAggregateTags(agg, level, identityTagSet) {
    const tags = [];
    for (const t of NUTRIENT_TAG_KEYS) {
      if (NUTRIENT_TAG_RULES[t](agg)) tags.push(t);
    }
    const memberTags = new Set();
    // Meal-direct identity tags (Batch 5b). Drop nutrient tags here — those
    // are recomputed from agg's own values above and we don't want stored
    // values to outvote the numeric definitions.
    if (Array.isArray(agg.tags)) {
      for (const t of agg.tags) {
        if (identityTagSet.has(t)) memberTags.add(t);
      }
    }
    if (level === 'category') {
      // category aggregates are derived by aggregating ingredients
      // whose `category` (or categoryGroupBy field) equals agg.name.
      const groupBy = state.get('categoryGroupBy') || 'category';
      for (const ing of ingredients) {
        if (ing[groupBy] !== agg.name) continue;
        for (const t of (ing.tags || [])) {
          if (identityTagSet.has(t)) memberTags.add(t);
        }
      }
    } else if (level === 'meal') {
      // meal aggregates reference categories via .examples; any
      // ingredient in any of those categories contributes.
      const cats = new Set(agg.examples || []);
      if (cats.size === 0) return tags;
      for (const ing of ingredients) {
        if (!cats.has(ing.category)) continue;
        for (const t of (ing.tags || [])) {
          if (identityTagSet.has(t)) memberTags.add(t);
        }
      }
    }
    for (const t of memberTags) tags.push(t);
    return tags;
  }

  /* Batch 4 (revised): meal-only Diet + Cuisine match. Treats selected
   * diets ∪ cuisines as a single flat selection — the AND/OR toggle
   * controls how many of those flat selections the meal must satisfy:
   *   match='all' (AND) — every selected item present in the meal's
   *                       attributes (diet_compatibility ∪ {cuisine})
   *   match='any' (OR)  — at least one selected item present
   *
   * A meal carries multiple diets but only one cuisine, so AND with
   * multiple selected cuisines is unsatisfiable (correctly returning
   * "no meals"). The user's example (one diet + one cuisine selected)
   * works naturally — AND means meal has both, OR means at least one.
   *
   * The ANY/ALL (scope) constraint that says "no extras" lives in
   * dietCuisineScopeHidden — see the comment block there for the
   * full ANY+AND / ALL+OR / etc. truth table. */
  function mealDietCuisineHidden(level) {
    if (level !== 'meal') return null;
    const dietInc    = ((state.get('dietFilter')    || {}).included) || [];
    const cuisineInc = ((state.get('cuisineFilter') || {}).included) || [];
    if (dietInc.length === 0 && cuisineInc.length === 0) return null;
    const dietSet    = new Set(dietInc);
    const cuisineSet = new Set(cuisineInc);
    const match = state.get('dietCuisineFilterMatch') || 'all';

    const out = new Set();
    for (const meal of (currentDataset || [])) {
      const raw = getRawMealForFilter(meal.id);
      if (!raw) continue;
      const mealDiets = Array.isArray(raw.diet_compatibility) ? raw.diet_compatibility : [];
      const mealCuisine = raw.cuisine || '';
      const mealDietSet = new Set(mealDiets);

      // Flat AND/OR over the union of selected diets and cuisines.
      // A selected diet matches if it's in mealDiets; a selected cuisine
      // matches if it equals mealCuisine.
      let pass;
      if (match === 'all') {
        const allDietsMatch    = dietInc.every(d => mealDietSet.has(d));
        const allCuisinesMatch = cuisineInc.every(c => c === mealCuisine);
        pass = allDietsMatch && allCuisinesMatch;
      } else {
        const anyDiet    = dietInc.some(d => mealDietSet.has(d));
        const anyCuisine = cuisineInc.some(c => c === mealCuisine);
        pass = anyDiet || anyCuisine;
      }
      if (!pass) out.add(meal.id);
    }
    return out;
  }

  /* Helper: look up the raw meal record (curated / corpus / user) by id.
   * Defined inline so we don't have to thread the lookup map through
   * every consumer; the rawMealById Map is built once after data load. */
  function getRawMealForFilter(id) {
    const userMeal = (state.get('userMeals') || []).find(m => m.id === id);
    if (userMeal) return userMeal;
    return rawMealById.get(id) || null;
  }

  /* Phase 40 round 4 + round 11: aggregate-level threshold check.
   * Tests aggregate's own per-100g values, scaled by the aggregate's
   * serving size when nutrientUnit === 'serving'.
   *
   * Batch 14: only enforce nutrients the user has moved off the bar
   * edge (activeThresholdSlots strips defaults). Same logic as the
   * ingredient pipeline. */
  function aggregateLevelThresholdHidden(thresholds, level) {
    if (!thresholds) return null;
    if (isIndividualView(level)) return null;
    const effective = activeThresholdSlots(thresholds);
    if (!effective) return null;
    const getScale = nutrientScaleGetter();
    const out = new Set();
    for (const agg of (currentDataset || [])) {
      const scale = getScale(agg) || 1;
      for (const n of NUTRIENT_FIELDS) {
        const t = effective[n];
        if (!t) continue;
        const v = (agg[n] || 0) * scale;
        if (!Number.isFinite(v)) continue;
        if (v < t.min - 1e-9 || v > t.max + 1e-9) { out.add(agg.id); break; }
      }
    }
    return out;
  }

  /* Bug-fix: "at-defaults" check used wherever the threshold filter
   * would otherwise treat user-default values as an active filter.
   * Returns true when the supplied thresholds match either the dataset
   * envelope (legacy baseline) OR the user-default map for the current
   * unit. The user-default check is what stops the per-serving sodium
   * default (0-5000 mg) from hiding 28 high-sodium meals after a
   * "reset to defaults". */
  function thresholdsActAsFilter(thresholds) {
    if (!thresholds) return false;
    if (isThresholdsBaseline(thresholds, ranges)) return false;
    const unit = state.get('nutrientUnit') || '100g';
    const defaults = unit === 'serving' ? defaultThresholdsMapServing : defaultThresholdsMap;
    if (isThresholdsAtDefaults(thresholds, defaults)) return false;
    return true;
  }

  /* Batch 14: return a thresholds-shaped map containing ONLY nutrients
   * the user has moved off the bar edge. At-default nutrients are
   * dropped, so isWithinThresholds short-circuits past them — moving
   * a single handle no longer kicks every other nutrient's default
   * range into the filter. Returns null when no nutrient is off-default
   * (caller uses that to skip filtering entirely). */
  function activeThresholdSlots(thresholds) {
    if (!thresholds) return null;
    const unit = state.get('nutrientUnit') || '100g';
    const defaults = unit === 'serving' ? defaultThresholdsMapServing : defaultThresholdsMap;
    const out = {};
    let any = false;
    for (const nutrient of NUTRIENT_FIELDS) {
      const t = thresholds[nutrient];
      const d = defaults && defaults[nutrient];
      if (!t) continue;
      if (d && Math.abs(t.min - d.min) < 1e-6 && Math.abs(t.max - d.max) < 1e-6) {
        continue; // at default for this nutrient — no filter contribution
      }
      out[nutrient] = t;
      any = true;
    }
    return any ? out : null;
  }

  /* Phase 40 round 11: return the active threshold set based on the
   * current nutrient-unit toggle. Falls back to the per-100g set if
   * the per-serving slot hasn't been initialized yet. */
  function activeThresholds() {
    const unit = state.get('nutrientUnit') || '100g';
    if (unit === 'serving') {
      return state.get('thresholdsServing') || state.get('thresholds');
    }
    return state.get('thresholds');
  }

  /* Returns a function (item) => scale. In per-serving mode this is
   * servingGramsFor(item)/100 (per-item). In per-100g mode it's always
   * 1. Thin wrapper around the central core/unit helper so the threshold
   * filter, aggregate-level threshold filter, and scene scaling all
   * read from the same source. */
  function nutrientScaleGetter() {
    return makeScaleGetter(state.get('nutrientUnit') || '100g');
  }

  /* Phase 40.1: lift an ingredient-id "hidden" set to the current
   * dataset. At meal/category levels we hide an aggregate iff EVERY
   * member ingredient is restricted — partial overlap (e.g. a meal
   * with one pork category, three permitted) should still render. */
  function translateHiddenToCurrent(hiddenIngredientIds) {
    if (!hiddenIngredientIds || hiddenIngredientIds.size === 0) return null;
    const level = state.get('viewLevel');
    if (isIndividualView(level)) return hiddenIngredientIds;
    const out = new Set();
    if (level === 'category') {
      const groupBy = state.get('categoryGroupBy') || 'category';
      // Group ingredients by the grouping field, then mark a group
      // hidden iff all of its members are hidden.
      const byGroup = new Map();
      for (const f of ingredients) {
        const key = f[groupBy];
        if (!key) continue;
        let arr = byGroup.get(key);
        if (!arr) { arr = []; byGroup.set(key, arr); }
        arr.push(f);
      }
      for (const agg of currentDataset) {
        const members = byGroup.get(agg.name);
        if (!members || members.length === 0) continue;
        const allHidden = members.every(f => hiddenIngredientIds.has(f.id));
        if (allHidden) out.add(agg.id);
      }
    } else if (level === 'meal') {
      // category → has any non-hidden ingredient
      const categoryHasAllowed = new Map();
      for (const f of ingredients) {
        const has = !hiddenIngredientIds.has(f.id);
        const cur = categoryHasAllowed.get(f.category);
        if (cur === undefined) categoryHasAllowed.set(f.category, has);
        else if (has) categoryHasAllowed.set(f.category, true);
      }
      for (const meal of currentDataset) {
        const cats = meal.examples || [];
        if (cats.length === 0) continue;
        const allFullyHidden = cats.every(c => categoryHasAllowed.get(c) === false);
        if (allFullyHidden) out.add(meal.id);
      }
    }
    return out;
  }

  function intersectSets(a, b) {
    const out = new Set();
    const [small, large] = a.size <= b.size ? [a, b] : [b, a];
    for (const id of small) if (large.has(id)) out.add(id);
    return out;
  }

  /* Coalesce filter-pipeline re-runs. 19 separate state slices below
   * each subscribe to "re-run the pipeline when this slice changes".
   * A single state.set({ keyA: x, keyB: y }) fires both subscribers
   * synchronously inside one notify pass — each would otherwise call
   * applyFilterToScene end-to-end. Routing the subscribers through a
   * microtask-scheduled wrapper collapses any number of mutations in
   * one tick to a single pipeline pass. The direct synchronous calls
   * inside scene-rebuild handlers (viewLevel, categoryGroupBy, etc.)
   * stay direct — they need to populate a freshly-built pointsHandle
   * without a microtask gap that would render an unfiltered frame. */
  let _applyFilterPending = false;
  function scheduleApplyFilterToScene() {
    if (_applyFilterPending) return;
    _applyFilterPending = true;
    queueMicrotask(() => {
      _applyFilterPending = false;
      applyFilterToScene();
    });
  }
  state.subscribe(s => s.ingredientFilter,      scheduleApplyFilterToScene);
  state.subscribe(s => s.ingredientFilterMatch, scheduleApplyFilterToScene); // Phase 40 round 3
  state.subscribe(s => s.thresholds,            scheduleApplyFilterToScene);
  state.subscribe(s => s.thresholdsServing,     scheduleApplyFilterToScene); // Phase 40 round 11
  state.subscribe(s => s.nutrientUnit,          scheduleApplyFilterToScene); // Phase 40 round 11 — unit drives which set is active + scale
  state.subscribe(s => s.thresholdMode,         scheduleApplyFilterToScene);
  state.subscribe(s => s.restrictions,          scheduleApplyFilterToScene);
  state.subscribe(s => s.tagFilter,             scheduleApplyFilterToScene);  // Phase 26
  state.subscribe(s => s.tagFilterMatch,        scheduleApplyFilterToScene);  // Phase 40 round 6
  state.subscribe(s => s.categoryFilter,        scheduleApplyFilterToScene);  // Phase 40 round 4
  state.subscribe(s => s.categoryFilterMatch,   scheduleApplyFilterToScene);  // Phase 40 round 6
  state.subscribe(s => s.foodGroupFilter,       scheduleApplyFilterToScene);  // Phase 40 round 4
  state.subscribe(s => s.foodGroupFilterMatch,  scheduleApplyFilterToScene);  // Batch 4
  state.subscribe(s => s.foodGroupFilterScope,  scheduleApplyFilterToScene);  // Batch 4
  state.subscribe(s => s.dietFilter,            scheduleApplyFilterToScene);  // Phase 40 round 7
  state.subscribe(s => s.cuisineFilter,         scheduleApplyFilterToScene);  // Phase 40 round 7
  state.subscribe(s => s.dietCuisineFilterMatch,scheduleApplyFilterToScene);  // Phase 40 round 8
  state.subscribe(s => s.ingredientFilterScope, scheduleApplyFilterToScene);  // Phase 40 round 9
  state.subscribe(s => s.categoryFilterScope,   scheduleApplyFilterToScene);  // Phase 40 round 9
  state.subscribe(s => s.tagFilterScope,        scheduleApplyFilterToScene);  // Phase 40 round 9
  state.subscribe(s => s.dietCuisineFilterScope,scheduleApplyFilterToScene);  // Phase 40 round 9

  // --- Phase 8 table view: shared active-set, view-switch, localStorage ---

  function tableActiveSet() {
    // The table mirrors the 3D scene's hide-not-grey policy. Returning
    // null here means "no active-set filter"; everything goes through
    // tableHiddenSet() below.
    return null;
  }

  /* Phase 40 round 4: hidden ids that the table view must filter OUT
   * entirely. Mirrors applyFilterToScene's combinedHidden logic so the
   * table stays consistent with the 3D view (every filter hides; no
   * greying anywhere). */
  function tableHiddenSet() {
    const {
      level, ingredientActive, thresholdActive, restrictionActive,
      tagActive, categoryActive, foodGroupActive,
      thresholds, categoryFilter,
    } = computeAllFilterSets();

    // Batch 3: meal-level ingredient filter handled by ingredientMealHidden
    // (specific example_ingredients), so drop it from the category-based path.
    const ingredientActiveForCombine = level === 'meal' ? null : ingredientActive;
    const passing = combinePassingSets([
      ingredientActiveForCombine, thresholdActive, restrictionActive,
      tagActive, categoryActive, foodGroupActive,
    ]);

    const hidden = passing
      ? new Set(ingredients.filter(f => !passing.has(f.id)).map(f => f.id))
      : null;

    let inCurrent = translateHiddenToCurrent(hidden);

    /* Color-guide unchecks (legendHidden): fold AFTER translation so
     * aggregate-view ids stay in the right namespace. See the matching
     * fix in applyFilterToScene above for the bug this was hiding. */
    const colorFilteredIds = computeColorFilteredSet();
    if (colorFilteredIds && colorFilteredIds.size > 0) {
      if (!inCurrent) inCurrent = new Set();
      for (const id of colorFilteredIds) inCurrent.add(id);
    }

    // Match-all extra hides (ingredient and category) — aggregate-only.
    const matchAllHidden = computeMatchAllHidden(ingredientActive);
    if (matchAllHidden && matchAllHidden.size > 0) {
      if (!inCurrent) inCurrent = new Set();
      for (const id of matchAllHidden) inCurrent.add(id);
    }
    // Batch 3: meal-level ingredient filter via specific example_ingredients.
    const ingMealHidden = ingredientMealHidden(level);
    if (ingMealHidden && ingMealHidden.size > 0) {
      if (!inCurrent) inCurrent = new Set();
      for (const id of ingMealHidden) inCurrent.add(id);
    }
    const categoryMatchAllHidden = computeCategoryMatchAllHidden(categoryFilter);
    if (categoryMatchAllHidden && categoryMatchAllHidden.size > 0) {
      if (!inCurrent) inCurrent = new Set();
      for (const id of categoryMatchAllHidden) inCurrent.add(id);
    }
    // Aggregate-level threshold filter.
    const aggThresholdHidden = aggregateLevelThresholdHidden(thresholds, level);
    if (aggThresholdHidden && aggThresholdHidden.size > 0) {
      if (!inCurrent) inCurrent = new Set();
      for (const id of aggThresholdHidden) inCurrent.add(id);
    }
    // Phase 40 round 7: diet + cuisine (meal-only).
    const dietCuisineHidden = mealDietCuisineHidden(level);
    if (dietCuisineHidden && dietCuisineHidden.size > 0) {
      if (!inCurrent) inCurrent = new Set();
      for (const id of dietCuisineHidden) inCurrent.add(id);
    }
    // Phase 40 round 8: tag filter aggregate-direct test.
    const aggTagHidden = aggregateLevelTagHidden(level);
    if (aggTagHidden && aggTagHidden.size > 0) {
      if (!inCurrent) inCurrent = new Set();
      for (const id of aggTagHidden) inCurrent.add(id);
    }
    // Batch 4: aggregate-level food-group filter (mirrors the scene path).
    const fgAggHidden = aggregateFoodGroupHidden(level);
    if (fgAggHidden && fgAggHidden.size > 0) {
      if (!inCurrent) inCurrent = new Set();
      for (const id of fgAggHidden) inCurrent.add(id);
    }
    // Phase 40 round 9 / Batch 4: scope='all' hides — extras-not-allowed.
    for (const scopeFn of [
      ingredientScopeHidden, categoryScopeHidden, tagScopeHidden,
      dietCuisineScopeHidden, foodGroupScopeHidden,
    ]) {
      const h = scopeFn(level);
      if (h && h.size > 0) {
        if (!inCurrent) inCurrent = new Set();
        for (const id of h) inCurrent.add(id);
      }
    }
    return inCurrent;
  }

  function applyViewToggle(view, prevView) {
    const canvasEl   = document.getElementById('canvas-container');
    const tableEl    = document.getElementById('table-container');
    const camera3D   = document.getElementById('view-3d-controls');
    const axisCtrls  = document.getElementById('axis-controls');
    const is3D = view !== 'table';
    if (canvasEl)  canvasEl.hidden  = !is3D;
    if (tableEl)   tableEl.hidden   =  is3D;
    // Phase 13.75 refinement: axis controls panel is 3D-only (no axes
    // in the table view to pan/zoom).
    if (axisCtrls) axisCtrls.hidden = !is3D;
    // Camera/snap controls apply only to the 3D view. Level
    // (Ingredients/Categories/Meals) and 3D↔Table toggle stay visible
    // in both views. The corner legend stays visible in both, so it
    // can guide table-row color dots as well as 3D spheres.
    if (camera3D)  camera3D.hidden  = !is3D;
    // Phase 13.5 round 3: replay the fade-in whenever the 3D view
    // becomes visible after being hidden, so re-entering the scene from
    // the table view re-creates the pop-in animation.
    if (is3D && prevView === 'table' && pointsHandle && pointsHandle.replayFadeIn) {
      pointsHandle.replayFadeIn();
    }
  }
  let lastView = state.get('view');
  applyViewToggle(lastView);
  state.subscribe(s => s.view, (view) => {
    applyViewToggle(view, lastView);
    lastView = view;
  });

  state.subscribe(s => s.tableColumns, (cols) => {
    try { localStorage.setItem(LS_TABLE_COLUMNS, JSON.stringify(cols)); } catch {}
  });
  state.subscribe(s => s.compositeWeights, (w) => {
    try { localStorage.setItem(LS_TABLE_WEIGHTS, JSON.stringify(w)); } catch {}
  });

  // --- Phase 7 URL hash sync (thresholds + mode) ---
  //
  // The hash carries a JSON blob of `{ m: mode, t: { nutrient: [min, max] } }`
  // — compact enough to share via link. Reads run before any user input so a
  // pasted URL lands on the right configuration. Writes are debounced so
  // dragging a slider doesn't spam the browser history.

  function applyHashFromUrl() {
    try {
      const raw = window.location.hash.replace(/^#/, '');
      if (!raw) return;
      const decoded = JSON.parse(decodeURIComponent(raw));
      if (!decoded || typeof decoded !== 'object') return;
      const patch = {};
      if (decoded.m && ['filter', 'score'].includes(decoded.m)) {
        patch.thresholdMode = decoded.m;
      }
      if (decoded.t && typeof decoded.t === 'object') {
        const next = { ...defaultThresholds(ranges) };
        for (const nutrient of NUTRIENT_FIELDS) {
          const entry = decoded.t[nutrient];
          if (Array.isArray(entry) && entry.length === 2) {
            const lo = Number(entry[0]);
            const hi = Number(entry[1]);
            if (Number.isFinite(lo) && Number.isFinite(hi) && lo <= hi) {
              // Phase 13.5 round 5: expand hash-loaded ranges to the
              // axis-defaults envelope so stale URLs can't clamp
              // ingredients out via narrow ranges.
              const d = defaultConstraintFor(nutrient, ranges);
              next[nutrient] = { min: Math.min(lo, d.min), max: Math.max(hi, d.max) };
            }
          }
        }
        patch.thresholds = next;
      }
      if (Object.keys(patch).length) state.set(patch);
    } catch {
      // Bad hash → ignore; never block boot on URL parsing.
    }
  }

  let writeHashTimer = null;
  function scheduleWriteHash() {
    if (writeHashTimer) clearTimeout(writeHashTimer);
    writeHashTimer = setTimeout(writeHashToUrl, 200);
  }
  function writeHashToUrl() {
    const mode = state.get('thresholdMode');
    const thresholds = state.get('thresholds');
    const baseline = isThresholdsBaseline(thresholds, ranges);
    const isDefault = (mode === 'filter' || !mode) && baseline;
    if (isDefault) {
      // Drop the hash entirely so the URL stays clean when nothing's set.
      history.replaceState(null, '', window.location.pathname + window.location.search);
      return;
    }
    const t = {};
    for (const nutrient of NUTRIENT_FIELDS) {
      const e = thresholds && thresholds[nutrient];
      if (!e) continue;
      const r = ranges[nutrient];
      if (Math.abs(e.min - r.min) < 1e-6 && Math.abs(e.max - r.max) < 1e-6) continue;
      t[nutrient] = [e.min, e.max];
    }
    const payload = { m: mode, t };
    const hash = '#' + encodeURIComponent(JSON.stringify(payload));
    history.replaceState(null, '', window.location.pathname + window.location.search + hash);
  }
  state.subscribe(s => s.thresholds,    scheduleWriteHash);
  state.subscribe(s => s.thresholdMode, scheduleWriteHash);
  applyHashFromUrl();

  /* Tester feedback: thresholds must persist verbatim across reloads.
   * The earlier safety net here unconditionally widened narrow ranges
   * to the default envelope, undoing every user-narrowed slider. We
   * now only backfill nutrients that are missing entirely (e.g. a new
   * nutrient added in a later version of the app); existing windows
   * are left exactly as the user set them. */
  (function backfillMissingThresholdNutrients() {
    for (const slotKey of ['thresholds', 'thresholdsServing']) {
      const t = state.get(slotKey);
      if (!t) continue;
      const next = { ...t };
      let changed = false;
      const defFor = slotKey === 'thresholdsServing'
        ? (n) => defaultConstraintForServing(n, ranges)
        : (n) => defaultConstraintFor(n, ranges);
      for (const n of NUTRIENT_FIELDS) {
        if (!next[n]) { next[n] = defFor(n); changed = true; }
      }
      if (changed) state.set({ [slotKey]: next });
    }
  })();

  function applyCameraMode(mode) {
    const next = scn.setCameraMode(mode);
    controls.object = next;
    controls.update();
  }
  state.subscribe(s => s.cameraMode, applyCameraMode);
  /* Tester feedback: cameraMode is in PERSISTABLE_KEYS, but the
   * persistedPatch state.set above ran BEFORE this subscription was
   * wired — the hydrated value never reached scn.setCameraMode and
   * the scene kept the default 'perspective' camera. Apply the
   * current value once here so reloading in orthographic actually
   * lands in orthographic. */
  applyCameraMode(state.get('cameraMode') || 'perspective');

  // --- Snap-to-axis (no state — fires camera moves directly) ---

  function snapToAxis(axis) {
    const target = SNAP_POSITIONS[axis];
    if (!target) return;
    const cam = scn.getActiveCamera();
    cam.position.copy(target);
    cam.up.set(0, 1, 0);
    cam.lookAt(scn.target);
    controls.update();
  }

  // --- UI ---

  mountViewToggle(document.getElementById('view-toggle'), { state });

  mountViewLevel(document.getElementById('view-level'), { state });

  mount3DControls(document.getElementById('view-3d-controls'), {
    state,
    onSnap: snapToAxis,
  });

  mountTableView(document.getElementById('table-container'), {
    state,
    getCurrentIngredients: () => currentDataset,
    getActiveSet: () => translateSetToCurrent(tableActiveSet()),
    getHiddenSet: () => tableHiddenSet(),
    ranges,
  });

  /* Unit-aware axis default. Reset buttons (axis picker popover, Axes
   * panel row, size axis) all need to land on the unit-appropriate
   * default — per-serving mode should reset calories to 0–2000, not the
   * per-100g 0–1000. Single closure shared across all three mounts. */
  const getAxisDefaultForUnit = (nutrient) =>
    (state.get('nutrientUnit') || '100g') === 'serving'
      ? defaultConstraintForServing(nutrient, ranges)
      : defaultConstraintFor(nutrient, ranges);

  const axisPicker = mountAxisPicker({
    getCamera: () => scn.getActiveCamera(),
    renderer: scn.renderer,
    controls,
    state,
    getAxisNameSprites: () => axesHandle.axisNameSprites,
    getAxisDefault: getAxisDefaultForUnit,
  });

  // Phase 13.75 refinement: manual axis controls panel (pan / zoom /
  // capture as threshold). Stacks above the legend. Clicking the axis
  // name row opens the same picker as clicking the 3D axis-name sprite.
  mountAxisControls(document.getElementById('axis-controls'), {
    state,
    openAxisPicker: (axisIndex, anchorEl) => {
      if (axisPicker && axisPicker.openForAxis) axisPicker.openForAxis(axisIndex, anchorEl);
    },
    getAxisDefault: getAxisDefaultForUnit,
    // Size axis is unit-agnostic — its values aren't scaled by the
    // per-serving toggle — so its reset always uses per-100g defaults.
    getSizeAxisDefault: (nutrient) => defaultConstraintFor(nutrient, ranges),
    /* Tester feedback: after applying filters that cluster every dot
     * into a small region, the user wants a one-click "zoom the axes
     * to fit what I'm actually looking at." We reuse the same hidden
     * set the table view computes, walk the visible items, and snap
     * each axis to that envelope with 5% padding. Per-serving scales
     * each item's nutrient by its own serving size, matching the
     * scene's projection. */
    onFitToVisible: () => fitAxesToVisible(),
  });

  function fitAxesToVisible() {
    const dataset = currentDataset || [];
    if (dataset.length === 0) return;
    const hidden = tableHiddenSet();
    const visible = hidden ? dataset.filter(d => !hidden.has(d.id)) : dataset;
    if (visible.length === 0) return;
    const axes = state.get('axes') || [];
    const getScale = nutrientScaleGetter();
    const nextAxes = axes.map(axis => {
      if (!axis || !axis.nutrient) return axis;
      let lo = Infinity, hi = -Infinity;
      for (const item of visible) {
        const scale = getScale(item) || 1;
        const v = (item[axis.nutrient] || 0) * scale;
        if (!Number.isFinite(v)) continue;
        if (v < lo) lo = v;
        if (v > hi) hi = v;
      }
      if (!Number.isFinite(lo) || !Number.isFinite(hi)) return axis;
      if (hi === lo) { hi = lo + 1; }
      const pad = Math.max(1e-9, (hi - lo) * 0.05);
      return { ...axis, constraint: { min: Math.max(0, lo - pad), max: hi + pad } };
    });
    state.set({ axes: nextAxes });
  }

  // Phase 40.5: ray-disambiguation menu. Sits at body level; opens on
  // multi-hit clicks routed from picking.js.
  const pickMenu = attachPickMenu({ state });

  attachPicking({
    renderer: scn.renderer,
    getCamera: () => scn.getActiveCamera(),
    getPoints: () => pointsHandle,
    getIngredients: () => currentDataset,
    getAxisNameSprites: () => axesHandle.axisNameSprites,
    state,
    ranges,
    onMultiHit: (candidates, anchor) => pickMenu.open(candidates, anchor),
    /* Batch 14: per-unit defaults so the hover tooltip's threshold
     * reasons skip at-default nutrients, matching the filter pipeline. */
    getThresholdDefaults: (unit) =>
      unit === 'serving' ? defaultThresholdsMapServing : defaultThresholdsMap,
  });

  // Phase 13.75: drag an axis line to pan its min/max window. The
  // capture-phase handler in axis-drag.js pre-empts the OrbitControls
  // pointerdown listener on an axis hit and disables `controls.enabled`
  // for the duration of the drag, so the camera doesn't orbit at the
  // same time. The axes group ref tracks rebuilds (theme/axes change).
  attachAxisDrag({
    renderer: scn.renderer,
    getCamera: () => scn.getActiveCamera(),
    controls,
    getAxesGroup: () => axesHandle.group,
    state,
  });

  // Phase 37: detail-panel's Remix needs to know the full category
  // vocabulary (for the "Add category" autocomplete) and to resolve a
  // selected meal aggregate back to its raw source entry (so it can
  // read the ORIGINAL category list — the aggregate's `examples` would
  // reflect any active draft).
  const allCategoriesSorted = Array.from(new Set(ingredients.map(i => i.category))).sort();
  // rawMealById is initialized at the top of boot() (Phase 40 round 7);
  // here we just expose the lookup helper for the detail panel.
  function getRawMeal(id) {
    // userMeals can change at runtime — look those up dynamically.
    const userHit = (state.get('userMeals') || []).find(m => m.id === id);
    if (userHit) return userHit;
    return rawMealById.get(id) || null;
  }

  mountDetailPanel(document.getElementById('rail-right'), {
    state,
    getCurrentIngredients: () => currentDataset,
    ranges,
    getAllCategories: () => allCategoriesSorted,
    // Batch 4: the ingredient-level Remix needs the raw ingredient list for
    // its add-ingredient autocomplete and id→name chip labels.
    getAllIngredients: () => ingredients,
    getRawMeal,
    /* Tester feedback: when the selected item is filtered out, the
     * detail panel should say so with a banner. The hidden-id set is
     * already computed for the table view; reuse it so the banner
     * fires whenever the same set hides the selected item. */
    getHiddenSet: () => tableHiddenSet(),
    /* Batch 14: per-unit defaults so inactiveReasons can skip nutrients
     * still at the bar's edge. Without this, the banner reports
     * "Fat above max 100g" for items that exceed the default-bar even
     * when the user only touched a different nutrient. */
    getThresholdDefaults: (unit) =>
      unit === 'serving' ? defaultThresholdsMapServing : defaultThresholdsMap,
  });

  // Boot the left rail open on desktop, closed (drawer) on mobile so the
  // first paint on a phone doesn't cover the canvas with a filter panel.
  if (matchMedia('(max-width: 768px)').matches) {
    state.set({ leftRailOpen: false });
  }

  const leftRail = mountLeftRail(document.getElementById('rail-left'), { state });
  /* Left-rail order. Tester feedback (batch 10) elevated Dietary
   * restrictions to the top — it's the most identity-anchored filter
   * (allergies / lifestyle), so framing the rest of the rail with it
   * already locked in matches how users actually shop the panel.
   *
   *   GROUP 1 — "What can you eat?" (identity-anchored)
   *     1. Dietary restrictions       (ingredient-level: what you AVOID)
   *
   *   GROUP 2 — "Numeric lens" (the dial users adjust most)
   *     2. Nutrient thresholds        (numeric range sliders)
   *
   *   GROUP 3 — "What kind of food?" (preferences)
   *     3. Filter by diet & cuisine   (meal-level: what you PREFER)
   *
   *   GROUP 4 — "Drill into content" (taxonomy + attributes)
   *     4. Filter by food group       (broadest taxonomy)
   *     5. Filter by category
   *     6. Filter by ingredient       (narrowest taxonomy)
   *     7. Filter by tag              (cross-cutting attribute)
   *
   *   GROUP 5 — "Work with meals" (meal-only operations)
   *     8. Modify all meals           (global composition overlay)
   *     9. Your meals                 (user-meal editor)
   */
  mountRestrictions(leftRail.getContentEl(), { state });
  mountNutrientThresholds(leftRail.getContentEl(), {
    state, ranges,
    /* Batch 14 fix: per-unit slider baseline IS the default. Match this
     * to initialThresholds / defaultThresholdsMap above so the per-row
     * ↻ fallback target (when Batch 12's slider-bounds path can't be
     * reached) stays consistent. */
    getDefaultThreshold: (nutrient) =>
      sliderBaselineFor(nutrient, state.get('nutrientUnit') || '100g'),
    /* Slider bounds = per-unit baseline (matches the default position
     * of the threshold handles) PLUS expansion to fit user meals that
     * exceed the baseline. The expansion uses the current unit's
     * gram-scaled value so a user meal contributing 60 g fiber/serving
     * pushes the per-serving slider up but the per-100g slider stays
     * sized to the per-100g envelope. */
    getSliderBounds: (nutrient) => {
      const unit = state.get('nutrientUnit') || '100g';
      const base = sliderBaselineFor(nutrient, unit);
      let maxFromUserMeals = -Infinity;
      const userMeals = state.get('userMeals') || [];
      for (const meal of userMeals) {
        const agg = aggregateUserMeal(meal, ingredients);
        if (!agg) continue;
        const v100g = +agg[nutrient];
        if (!Number.isFinite(v100g)) continue;
        const sg = +agg.serving_grams || 100;
        const val = unit === 'serving' ? v100g * (sg / 100) : v100g;
        if (val > maxFromUserMeals) maxFromUserMeals = val;
      }
      let max = base.max;
      if (maxFromUserMeals > base.max) {
        // 5% headroom, rounded up to a tidy number so the track-fill math
        // doesn't produce odd partial-pixel positions.
        const padded = maxFromUserMeals * 1.05;
        const step = padded > 500 ? 50 : padded > 100 ? 10 : 1;
        max = Math.ceil(padded / step) * step;
      }
      return { min: base.min, max };
    },
  });
  mountDietCuisineFilter(leftRail.getContentEl(), {
    state,
    meals: [...meals, ...compositionalMeals, ...corpusTitledMeals],
  });
  mountFoodGroupFilter(leftRail.getContentEl(), { state });
  mountCategoryFilter(leftRail.getContentEl(), { state, ingredients });
  mountIngredientFilter(leftRail.getContentEl(), { state, ingredients });
  mountTagFilter(leftRail.getContentEl(), { state });
  mountComposeMealsSection(leftRail.getContentEl(), { state, ingredients });
  mountMealBuilder(leftRail.getContentEl(), { state, ingredients });

  const railToggle = document.getElementById('rail-toggle');
  if (railToggle) {
    railToggle.addEventListener('click', () => {
      state.set({ leftRailOpen: !state.get('leftRailOpen') });
    });
  }

  mountLegend(document.getElementById('legend'), { state });

  // Phase 38 + 40.{9,11}: active-filters chip rail. Always visible; chips
  // diff against the user-default thresholds map (not the dataset envelope)
  // so an untouched config has no chips. Per-unit maps so per-serving
  // chips diff against the per-serving defaults, not the per-100g ones.
  // (Maps are defined earlier in boot() so the filter code can also use
  // them — see the threshold init block above.)
  mountActiveFilters(document.getElementById('active-filters'), {
    state,
    ingredients,
    ranges,
    getRawMeal,
    defaultThresholdsMap,
    defaultThresholdsMapServing,
  });

  // Phase 40.4: 3D search dropdown. Mounted in the header center,
  // shares the same hidden-set logic the scene uses so restricted
  // items don't show up in results.
  const searchSlot = document.getElementById('search-slot');
  if (searchSlot) {
    // Batch 3: id -> name lookup so the search box can match a meal by the
    // specific ingredients it uses (typing "bagel" surfaces bagel meals).
    const ingredientNameById = new Map(ingredients.map(f => [f.id, f.name]));
    mountSearch(searchSlot, {
      state,
      getCurrentIngredients: () => currentDataset,
      getIngredientName: (id) => ingredientNameById.get(id) || '',
      /* Batch 7: return the FULL hidden-id set once per open() call so
       * search.js can do O(1) `.has()` lookups in the per-item loop.
       * The previous `isHidden(id)` shape re-ran the entire filter
       * pipeline per item (N × heavy ≈ a visible hang per keystroke).
       *
       * Semantics preserved from the old code: search only hides items
       * blocked by DIETARY RESTRICTIONS (Phase 40.1's hidden set). Other
       * filters (thresholds, food groups, categories, etc.) DON'T hide
       * search rows — the user expects to be able to search the whole
       * dataset, with restricted (allergen / ethical) items excluded. */
      getHiddenIds: () => {
        const restrictions = state.get('restrictions') || [];
        if (restrictions.length === 0) return null;
        if (isIndividualView(state.get('viewLevel'))) {
          const allowed = passingIngredientIds(ingredients, restrictions);
          if (!allowed) return null;
          const hidden = new Set();
          for (const f of ingredients) {
            if (!allowed.has(f.id)) hidden.add(f.id);
          }
          return hidden;
        }
        return tableHiddenSet();
      },
    });
  }

  /* Phase 40 round 8: global per-100g / per-serving toggle in the
   * header so it's visible in both 3D and table views. Replaces the
   * detail-panel and table-toolbar duplicates that earlier rounds
   * introduced — single source of truth via state.nutrientUnit. */
  mountUnitToggle(document.getElementById('unit-toggle-slot'), { state });

  // Phase 40.3: selection halo. The scene's setSelectedId drives the
  // pulse + tint; we just relay state changes.
  function applySelectionToPoints() {
    if (pointsHandle && pointsHandle.setSelectedId) {
      pointsHandle.setSelectedId(state.get('selectedIngredientId'));
    }
  }
  applySelectionToPoints();
  state.subscribe(s => s.selectedIngredientId, applySelectionToPoints);

  // Phase 40 round 2: preview pulse (search-result hover). Same wiring
  // pattern as selection; the scene paints both simultaneously when set.
  function applyPreviewToPoints() {
    if (pointsHandle && pointsHandle.setPreviewId) {
      pointsHandle.setPreviewId(state.get('previewIngredientId'));
    }
  }
  applyPreviewToPoints();
  state.subscribe(s => s.previewIngredientId, applyPreviewToPoints);

  // Phase 40.6: Size axis → per-instance dot radius.
  function applySizeAxisToPoints() {
    if (pointsHandle && pointsHandle.setSizeAxis) {
      pointsHandle.setSizeAxis(state.get('sizeAxis'));
    }
  }
  applySizeAxisToPoints();
  state.subscribe(s => s.sizeAxis, applySizeAxisToPoints);

  /* Phase 40 round 10: per-100g ↔ per-serving toggle drives dot
   * positions in 3D. Both the InstancedMesh and the user-meal rings
   * use the same scale factor (servingGramsFor(ing)/100 in serving
   * mode), so they stay co-located. */
  function applyNutrientUnitToScene() {
    const unit = state.get('nutrientUnit') || '100g';
    if (pointsHandle && pointsHandle.setNutrientUnit) {
      pointsHandle.setNutrientUnit(unit);
    }
    if (mealsHandle && mealsHandle.setNutrientUnit) {
      mealsHandle.setNutrientUnit(unit);
      // Force a redraw of the centroid rings with the new per-ingredient
      // positions.
      refreshMeals();
    }
  }
  applyNutrientUnitToScene();
  state.subscribe(s => s.nutrientUnit, applyNutrientUnitToScene);

  /* Phase 40 round 13: per-unit axis defaults. Mirror state.axes ↔
   * state.axes<currentUnit>. When user adjusts axes (picker / drag /
   * pan / zoom / capture button), the mirror writes the change back
   * to whichever stored slot matches the current unit. When the user
   * toggles the unit, the swap pulls the OTHER unit's stored axes
   * into state.axes. The two stored slots persist independently. */
  let axesMirrorUnit = state.get('nutrientUnit') || '100g';
  state.subscribe(s => s.axes, (axes) => {
    if (!axes) return;
    const slotKey = axesMirrorUnit === 'serving' ? 'axesServing' : 'axes100g';
    if (state.get(slotKey) !== axes) {
      state.set({ [slotKey]: axes });
    }
  });
  state.subscribe(s => s.nutrientUnit, (unit) => {
    axesMirrorUnit = unit || '100g';
    const incoming = axesMirrorUnit === 'serving'
      ? state.get('axesServing')
      : state.get('axes100g');
    if (incoming && incoming !== state.get('axes')) {
      state.set({ axes: incoming });
    }
  });

  // Phase 11: theme toggle drives <html data-theme>; the scene re-reads
  // CSS-driven colors below, and the axes get rebuilt so their tick /
  // label colors flip in lockstep.
  mountThemeToggle(document.getElementById('theme-toggle-slot'), { state });

  state.subscribe(s => s.theme, () => {
    scn.scene.background = readCssColor('--color-bg', '#0e1014');
    disposeAxes(axesHandle.group);
    axesHandle = buildAxes(scn.scene, state.get('axes'), ranges);
    applyAxisLabelsVisibility();
    // Pulse glow's blending mode + halo color depend on theme — additive
    // disappears against a white background, so we switch to normal
    // blending and dial the white-mix down in light mode.
    if (pointsHandle && pointsHandle.refreshTheme) pointsHandle.refreshTheme();
  });

  mountShortcuts({
    state,
    onSnap: snapToAxis,
  });

  // Phase 11 polish: rails are drag-resizable on desktop (non-persistent).
  attachRailResize();
  // Phase 13.5 round 4: the .rail-fade gradient (round 2) was tied to the
  // header overlapping the rail. With the rail now extending top-to-bottom
  // and the header offset to start at left: var(--left-rail-w), there's
  // no overlap to fade through — chrome row provides the visual boundary.

  // Phase 12: config menu + auto-save. attachAutoSave subscribes to every
  // persistable state slice and debounces the write — after this call,
  // any state change is durable on the next reload.
  mountConfigMenu(document.getElementById('config-menu-slot'), { state });
  attachAutoSave(state);

  // First-run guided tour. Auto-fires once for new users; relaunchable
  // from the ⋯ menu via a custom event the tutorial listens for.
  // Batch 9: scene refs let the tutorial anchor callouts to 3D
  // elements (axis-name sprites) by re-projecting world coords each
  // frame. Getters not direct handles so swapping the scene rebuild
  // (axesHandle reassigned during axis changes) stays correct.
  mountTutorial({
    state,
    getCamera: () => scn.getActiveCamera(),
    getCanvas: () => scn.renderer.domElement,
    getAxisNameSprites: () => axesHandle && axesHandle.axisNameSprites,
    // Tutorial polish round 3: the guided flows need to start from a clean
    // scene so each demo is intuitive (no leftover filters/score-mode/hidden
    // groups from a previous slide), and the held-ingredient flow needs every
    // ingredient id to start the filter from an empty selection.
    getAllIngredientIds: () => ingredients.map(f => f.id),
    resetScene: () => {
      state.set({
        ingredientFilter: { excludedIds: [] },
        thresholds: defaultThresholds(ranges),
        thresholdsServing: { ...defaultThresholdsMapServing },
        thresholdMode: 'filter',
        legendHidden: { rgb: [], food_group: [] },
        tagFilter: [],
        // Clear selection + draft so a use-case flow's "click a meal" /
        // remix steps start from a known-empty baseline.
        selectedIngredientId: null,
        mealDraft: null,
      });
    },
  });

  /* Phase 40 round 5: OK dismisses the dialog WITHOUT touching any
   * filters. The persistent warning on the active-filters panel keeps
   * the user oriented while the dataset stays empty. */
  const emptyOkBtn = document.querySelector('#empty-filter .empty-filter-ok');
  if (emptyOkBtn) {
    emptyOkBtn.addEventListener('click', () => {
      emptyOverlayAcknowledged = true;
      const overlay = document.getElementById('empty-filter');
      if (overlay) overlay.hidden = true;
    });
  }

  window.__foodMap = {
    scene: scn.scene, controls,
    get camera() { return scn.getActiveCamera(); },
    get axes() { return axesHandle; },
    points: () => pointsHandle,
    snapToAxis,
  };

  /* Tester feedback: in orthographic mode, snapping the camera to
   * an X/Y/Z view collapses the corresponding axis to a single
   * point on screen — its name label sits right at the origin and
   * reads as noise. Fade the label's opacity by the dot product of
   * the view direction with each axis. Tight thresholds so the
   * label disappears only when the axis is genuinely edge-on, and
   * comes back smoothly with the slightest rotation. */
  const FADE_EDGE_LOW  = Math.cos(5 * Math.PI / 180);  // ~5° off-axis → start fading
  const FADE_EDGE_HIGH = Math.cos(1 * Math.PI / 180);  // ~1° off-axis → fully faded
  const AXIS_DIRS_WORLD = [
    new THREE.Vector3(1, 0, 0),
    new THREE.Vector3(0, 1, 0),
    new THREE.Vector3(0, 0, 1),
  ];
  const _viewDir = new THREE.Vector3();
  function setAxisGroupOpacity(axisIndex, opacity) {
    /* Tester feedback: once an axis fades fully out, it shouldn't be
     * pickable in 3D and its row in the Axes panel should grey out.
     * Visibility flips at opacity < 0.005; picking.js already filters
     * by Object3D.visible, so non-pickable comes for free. */
    const visible = opacity > 0.005;
    const nameSprite = axesHandle.axisNameSprites[axisIndex];
    if (nameSprite) {
      nameSprite.material.opacity = opacity;
      nameSprite.visible = visible;
    }
    const ticks = axesHandle.tickLabelSprites && axesHandle.tickLabelSprites[axisIndex];
    if (ticks) for (const s of ticks) {
      s.material.opacity = opacity;
      s.visible = visible;
    }
  }

  let _lastHiddenAxisIndex = null;
  function publishHiddenAxisIndex(idx) {
    if (idx === _lastHiddenAxisIndex) return;
    _lastHiddenAxisIndex = idx;
    state.set({ hiddenAxisIndex: idx });
  }

  /* Per-frame cache: in perspective mode the opacity is always 1, and
   * in orthographic mode the dot products only change when the camera
   * moves. Skip the per-sprite material writes when neither input has
   * changed since the last frame. */
  let _lastAxisLabelMode = null;
  const _lastAxisLabelCamPos = new THREE.Vector3();
  const _lastAxisLabelCamQuat = new THREE.Quaternion();
  function updateAxisLabelOpacity() {
    const sprites = axesHandle && axesHandle.axisNameSprites;
    if (!sprites || sprites.length !== 3) return;
    /* Perspective views always carry some depth cue — the label
     * isn't visually trapped at the origin the way orthographic
     * snap views trap it — so the fade only fires in orthographic. */
    const orthoMode = state.get('cameraMode') === 'orthographic';
    if (!orthoMode) {
      if (_lastAxisLabelMode === 'perspective') return; // unchanged since last frame
      for (let i = 0; i < 3; i++) setAxisGroupOpacity(i, 1);
      publishHiddenAxisIndex(null);
      _lastAxisLabelMode = 'perspective';
      return;
    }
    const cam = scn.getActiveCamera();
    if (_lastAxisLabelMode === 'orthographic'
        && _lastAxisLabelCamPos.equals(cam.position)
        && _lastAxisLabelCamQuat.equals(cam.quaternion)) {
      return; // camera hasn't moved since last computation
    }
    _lastAxisLabelCamPos.copy(cam.position);
    _lastAxisLabelCamQuat.copy(cam.quaternion);
    _lastAxisLabelMode = 'orthographic';

    _viewDir.copy(scn.target).sub(cam.position).normalize();
    let hidden = null;
    for (let i = 0; i < 3; i++) {
      const d = Math.abs(_viewDir.dot(AXIS_DIRS_WORLD[i]));
      let opacity;
      if (d <= FADE_EDGE_LOW) {
        opacity = 1;
      } else if (d >= FADE_EDGE_HIGH) {
        opacity = 0;
      } else {
        const t = (d - FADE_EDGE_LOW) / (FADE_EDGE_HIGH - FADE_EDGE_LOW);
        const smooth = t * t * (3 - 2 * t); // smoothstep for the fade curve
        opacity = 1 - smooth;
      }
      setAxisGroupOpacity(i, opacity);
      if (opacity <= 0.005) hidden = i;
    }
    publishHiddenAxisIndex(hidden);
  }

  function animate(now) {
    requestAnimationFrame(animate);
    controls.update();
    pointsHandle.update(now);
    updateAxisLabelOpacity();
    scn.renderer.render(scn.scene, scn.getActiveCamera());
  }
  requestAnimationFrame(animate);

  // eslint-disable-next-line no-console
  console.log('[ingredient-map] ready');
}

// --- Boot orchestration with a visible loading/error overlay ---
//
// The overlay (#boot-overlay) starts visible and is removed on successful
// boot. Any error inside boot(), or any later unhandled rejection / global
// error, surfaces in the overlay with a stack trace and a "clear settings
// and reload" affordance so a stale localStorage shape doesn't soft-brick
// the app.

async function runBoot() {
  wireBootResetButton();
  try {
    await boot();
    hideBootOverlay();
  } catch (err) {
    console.error('[ingredient-map] boot failed', err);
    showBootError(err);
  }
}

// Catch errors that happen *after* boot — async tasks, render-loop crashes.
window.addEventListener('error', (ev) => {
  showBootError(ev.error || new Error(ev.message || 'unknown error'));
});
window.addEventListener('unhandledrejection', (ev) => {
  showBootError(ev.reason || new Error('unhandled promise rejection'));
});

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', runBoot, { once: true });
} else {
  runBoot();
}
