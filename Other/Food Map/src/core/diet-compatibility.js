/* Phase 34: diet compatibility.
 *
 * Each meal in `meals.json` carries a precomputed `diet_compatibility`
 * array (Phase 34 backfill script). At runtime, components that need to
 * recompute compatibility on the fly — e.g. the per-meal remix in Phase
 * 37 or filtering an unsaved user meal — call computeDietCompatibility().
 *
 * Rules live in DIETS (src/data/schema.js):
 *   - excludedCategories: any overlap with the meal's ingredient_categories
 *     disqualifies the meal.
 *   - nutrientMin / nutrientMax: per-100g aggregate-nutrient thresholds
 *     the meal's aggregate must satisfy.
 *
 * For nutrient checks the caller passes in `categoryAggregates` (the
 * output of aggregateByCategory), so we can compute the meal's effective
 * per-100g aggregate as the equal-weighted mean of its constituent
 * categories' nutrient values — same shape aggregateMeals() produces but
 * without needing the meal to already be aggregated.
 */

import { DIETS, NUTRIENT_FIELDS } from '../data/schema.js';

/**
 * Compute the array of diet keys (from DIETS) that this meal is compatible
 * with.
 *
 * @param meal              { ingredient_categories: string[] } (or full meal record)
 * @param categoryAggregates result of aggregateByCategory(ingredients) — required
 *                          when any diet has a nutrient rule.
 * @returns string[] sorted in DIETS-declaration order
 */
export function computeDietCompatibility(meal, categoryAggregates) {
  const categories = Array.isArray(meal && meal.ingredient_categories)
    ? meal.ingredient_categories : [];
  const categorySet = new Set(categories);

  const aggByName = new Map();
  if (Array.isArray(categoryAggregates)) {
    for (const c of categoryAggregates) aggByName.set(c.name, c);
  }
  const mealAgg = aggregateMealNutrients(categories, aggByName);

  const result = [];
  for (const key of Object.keys(DIETS)) {
    const def = DIETS[key];
    if (def.excludedCategories) {
      let hit = false;
      for (const cat of def.excludedCategories) {
        if (categorySet.has(cat)) { hit = true; break; }
      }
      if (hit) continue;
    }
    if (def.nutrientMin) {
      let ok = true;
      for (const [n, min] of Object.entries(def.nutrientMin)) {
        if (!(mealAgg && Number.isFinite(mealAgg[n]) && mealAgg[n] >= min)) { ok = false; break; }
      }
      if (!ok) continue;
    }
    if (def.nutrientMax) {
      let ok = true;
      for (const [n, max] of Object.entries(def.nutrientMax)) {
        if (!(mealAgg && Number.isFinite(mealAgg[n]) && mealAgg[n] <= max)) { ok = false; break; }
      }
      if (!ok) continue;
    }
    result.push(key);
  }
  return result;
}

/* Equal-weighted mean of category aggregates' per-100g values — matches
 * aggregateMeals' nutrient pipeline so the rules see the same numbers the
 * meal sphere is plotted at. Returns null if no category resolves. */
function aggregateMealNutrients(categories, aggByName) {
  const resolved = categories.map(c => aggByName.get(c)).filter(Boolean);
  if (resolved.length === 0) return null;
  const out = {};
  for (const field of NUTRIENT_FIELDS) {
    let sum = 0;
    for (const c of resolved) sum += (c[field] || 0);
    out[field] = sum / resolved.length;
  }
  return out;
}
