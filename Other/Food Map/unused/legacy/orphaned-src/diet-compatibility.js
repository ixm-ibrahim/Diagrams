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

/* Batch 14: gram-weighted plate mean — matches the math in
 * aggregateMeals (src/core/aggregations.js) where each category
 * contributes one serving by its `serving_grams`. The earlier
 * equal-weighted mean diverged: a Soup + Cream meal under the plate
 * model is mostly soup (245g) lightly enriched with cream (14g), but
 * under equal-weighted averaging the cream's high-fat numbers counted
 * 50%. high_protein judgments now see the same numbers the meal is
 * plotted at. Returns null if no category resolves. */
function aggregateMealNutrients(categories, aggByName) {
  const resolved = categories.map(c => aggByName.get(c)).filter(Boolean);
  if (resolved.length === 0) return null;
  let totalGrams = 0;
  for (const c of resolved) totalGrams += (c.serving_grams || 100);
  if (!(totalGrams > 0)) totalGrams = resolved.length * 100;
  const out = {};
  for (const field of NUTRIENT_FIELDS) {
    let totalNutrient = 0;
    for (const c of resolved) {
      const sg = c.serving_grams || 100;
      totalNutrient += (c[field] || 0) * (sg / 100);
    }
    out[field] = totalNutrient / totalGrams * 100;
  }
  return out;
}
