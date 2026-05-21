/* Aggregate the ingredient dataset into category-level pseudo-ingredients.
 *
 * Each category becomes a single record with the same shape as a real ingredient
 * (so it flows through normalize.js / points.js unchanged):
 *   - per-100g nutrient values = mean of members
 *   - group_weights = mean of members' weights
 *   - examples = names of all members (capped for display)
 *   - notes = "Average of N items"
 *
 * Useful when the 179-point cloud reads as too busy — toggling to Categories
 * gives ~25 spheres centered at each category's nutrient profile.
 */

import {
  NUTRIENT_FIELDS, FOOD_GROUPS,
  SERVING_GRAMS_BY_CATEGORY, SERVING_GRAMS_BY_FOOD_GROUP,
  SERVING_GRAMS_DEFAULT,
} from '../data/schema.js';

/* Per-serving math (Phase 40 follow-up).
 *
 * Earlier rounds treated every meal aggregate as a flat 350g plate
 * whose per-100g nutrients were the EQUAL-WEIGHTED mean of constituent
 * category averages. That overstated per-serving values by 2-4× for
 * any meal with a dense category (Oils at 884 kcal/100g × 350g flat
 * gave fish-and-chips 1290 kcal/serving — the realistic plate is ~357).
 *
 * The honest model is: a meal IS the sum of one typical serving of
 * each constituent category. Total plate grams = Σ category serving
 * grams; total plate nutrient n = Σ (cat[n] × cat.serving / 100); the
 * meal's per-100g is just the gram-weighted mean of category densities
 * (i.e., total nutrient / total grams × 100). This makes both the
 * per-100g and per-serving readings correspond to something real, and
 * keeps the meal aggregate's plotted position consistent with its
 * displayed numbers regardless of unit toggle.
 */
function categoryServingGrams(category, fallback = SERVING_GRAMS_DEFAULT) {
  if (category && SERVING_GRAMS_BY_CATEGORY[category] != null) {
    return SERVING_GRAMS_BY_CATEGORY[category];
  }
  return fallback;
}

/* Phase 13.5 round 3: compute a food_group weight vector for an
 * ingredient — one-hot for an individual, mean-of-constituents for an
 * aggregate (set explicitly by the aggregator). Used by the food_group
 * color scheme in scene/points.js. */
function emptyFoodGroupWeights() {
  const w = {};
  for (const g of FOOD_GROUPS) w[g] = 0;
  return w;
}
function foodGroupWeightsFor(ingredient) {
  if (ingredient.food_group_weights) return ingredient.food_group_weights;
  const w = emptyFoodGroupWeights();
  if (ingredient.food_group && (ingredient.food_group in w)) w[ingredient.food_group] = 1;
  return w;
}
function averageFoodGroupWeights(items, weight = () => 1) {
  const out = emptyFoodGroupWeights();
  let total = 0;
  for (const item of items) {
    const w = weight(item);
    if (!(w > 0)) continue;
    const fgw = foodGroupWeightsFor(item);
    for (const g of FOOD_GROUPS) out[g] += w * fgw[g];
    total += w;
  }
  if (total > 0) for (const g of FOOD_GROUPS) out[g] /= total;
  return out;
}

function slugify(s) {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

/* Phase 13.5 round 7: aggregate by an arbitrary identity field. The
 * Categories dropdown in the view-level toggle lets the user pick
 * `food_group` (~11 groups), `category` (~40, default), or
 * `subcategory` (~80). The output rows always set `category` to the
 * grouped value so downstream lookups (e.g., meal-builder's
 * foodGroupsByCategory map) still work. */
export function aggregateByCategory(ingredients, groupBy = 'category') {
  const validGroupBy = ['food_group', 'category', 'subcategory'].includes(groupBy)
    ? groupBy : 'category';
  const groups = new Map();
  for (const f of ingredients) {
    const key = f[validGroupBy];
    if (key == null || key === '') continue;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(f);
  }

  const result = [];
  for (const [category, members] of groups) {
    const n = members.length;
    const agg = {
      id: `cat-${slugify(category)}`,
      name: category,
      category,
      subcategory: category,
      examples: members.map(f => f.name).slice(0, 8),
      group_weights: [0, 0, 0],
      notes: `Mean across ${n} ${n === 1 ? 'entry' : 'entries'} in this ${validGroupBy.replace('_', ' ')}.`,
    };

    for (const field of NUTRIENT_FIELDS) {
      let sum = 0;
      for (const f of members) sum += f[field];
      agg[field] = sum / n;
    }

    for (const f of members) {
      agg.group_weights[0] += f.group_weights[0];
      agg.group_weights[1] += f.group_weights[1];
      agg.group_weights[2] += f.group_weights[2];
    }
    agg.group_weights = agg.group_weights.map(w => w / n);
    agg.food_group_weights = averageFoodGroupWeights(members);
    // Phase 13.5 round 5: pick the dominant food_group so the table's
    // food_group column renders something meaningful for category rows.
    agg.food_group = dominantFoodGroup(agg.food_group_weights, members);

    /* Stamp serving_grams onto every aggregate so servingGramsFor()
     * resolves via the item's own field (step 1 of its resolution
     * order) instead of falling back through the category /
     * food_group maps. For `category` grouping the lookup uses the
     * category name; for `food_group` grouping it uses the
     * food_group fallback map; subcategory groupings (no
     * subcategory-level RACC) inherit the category mean of their
     * members' serving sizes. */
    if (validGroupBy === 'category') {
      agg.serving_grams = categoryServingGrams(category);
    } else if (validGroupBy === 'food_group') {
      agg.serving_grams = SERVING_GRAMS_BY_FOOD_GROUP[category] ?? SERVING_GRAMS_DEFAULT;
    } else {
      // Subcategory: average the members' own serving_grams when present.
      let sgSum = 0, sgCount = 0;
      for (const f of members) {
        if (Number.isFinite(f.serving_grams)) { sgSum += f.serving_grams; sgCount++; }
      }
      agg.serving_grams = sgCount > 0 ? sgSum / sgCount : SERVING_GRAMS_DEFAULT;
    }

    result.push(agg);
  }
  return result;
}

/* Phase 13.5 round 5: highest-weight food_group from a weights map. If
 * weights are uniform (e.g., a single-channel ingredient), fall back to
 * the first member's food_group so the result is deterministic. */
function dominantFoodGroup(weights, members) {
  if (!weights) return members?.[0]?.food_group || null;
  let best = null;
  let bestW = -Infinity;
  for (const g of FOOD_GROUPS) {
    const w = weights[g];
    if (typeof w === 'number' && w > bestW) { bestW = w; best = g; }
  }
  return best || members?.[0]?.food_group || null;
}

/**
 * Aggregate a list of curated meal patterns into ingredient-shaped records, ready
 * to plot. Each meal record:
 *   { id, name, ingredient_categories: [string], notes }
 *
 * The aggregate is the equal-weighted mean of its constituent categories
 * (which are themselves means of their member ingredients). Color blending shows
 * up here because the constituent categories can be in different ingredient
 * groups (animal vs. plant vs. dairy), so the meal's group_weights end up
 * as a real RGB mix rather than a pure channel.
 *
 * Phase 9 user meals (specific ingredients × grams) flow through
 * `aggregateUserMeal` instead; `aggregateAllMeals` merges both so the
 * "Meals" view-level plots curated + user meals side-by-side.
 *
 * Phase 35: optional `composition` overlay reshapes every meal's effective
 * category list before aggregation:
 *   effectiveCategories = (meal.ingredient_categories ∪ composition.added)
 *                         \ composition.removed
 * A meal that loses all its categories after removal is dropped (no dot).
 * Empty composition leaves positions unchanged.
 */
export function aggregateMeals(ingredients, meals, composition) {
  const byCategory = new Map();
  for (const cat of aggregateByCategory(ingredients)) {
    byCategory.set(cat.name, cat);
  }

  const added   = (composition && Array.isArray(composition.added))   ? composition.added   : [];
  const removed = (composition && Array.isArray(composition.removed)) ? new Set(composition.removed) : new Set();
  const addedFiltered = added.filter(name => byCategory.has(name));

  const result = [];
  for (const meal of meals) {
    const baseCategories = meal.ingredient_categories || [];
    const effectiveNames = effectiveCategoryList(baseCategories, addedFiltered, removed);
    const cats = effectiveNames
      .map(name => byCategory.get(name))
      .filter(Boolean);
    if (cats.length === 0) continue;

    const n = cats.length;
    /* Plate model: each category contributes one typical serving.
     * Total grams = Σ servings; this is the meal aggregate's own
     * serving_grams. Nutrients per-100g = Σ(cat[n] × cat.serving) / Σ
     * cat.serving × 100 — the gram-weighted mean, so dense categories
     * (Oils 884 kcal/100g at 14g) no longer dominate light ones
     * (Leafy greens 25 kcal/100g at 30g) the way an equal-weighted
     * mean would. group_weights / food_group_weights stay gram-
     * weighted for the same reason. */
    let totalGrams = 0;
    for (const c of cats) totalGrams += (c.serving_grams || SERVING_GRAMS_DEFAULT);
    if (!(totalGrams > 0)) totalGrams = n * SERVING_GRAMS_DEFAULT;

    const agg = {
      id: meal.id,
      name: meal.name,
      category: 'Meal',
      subcategory: meal.name,
      examples: effectiveNames,
      notes: meal.notes || `Combination of ${effectiveNames.join(', ')}.`,
      group_weights: [0, 0, 0],
      isCurated: meal.source !== 'corpus',
      // Phase 36: propagate source so the scene can render corpus
      // patterns smaller / dimmer. Defaults to 'curated' when missing.
      source: meal.source || 'curated',
      frequency: typeof meal.frequency === 'number' ? meal.frequency : 1,
      diet_compatibility: Array.isArray(meal.diet_compatibility) ? meal.diet_compatibility : [],
      cuisine: meal.cuisine || null,
      serving_grams: totalGrams,
    };

    for (const field of NUTRIENT_FIELDS) {
      let totalNutrient = 0;
      for (const c of cats) {
        const sg = c.serving_grams || SERVING_GRAMS_DEFAULT;
        totalNutrient += (c[field] || 0) * (sg / 100);
      }
      agg[field] = totalNutrient / totalGrams * 100;
    }
    for (const c of cats) {
      const sg = c.serving_grams || SERVING_GRAMS_DEFAULT;
      agg.group_weights[0] += sg * c.group_weights[0];
      agg.group_weights[1] += sg * c.group_weights[1];
      agg.group_weights[2] += sg * c.group_weights[2];
    }
    agg.group_weights = agg.group_weights.map(w => w / totalGrams);
    agg.food_group_weights = averageFoodGroupWeights(
      cats,
      c => (c.serving_grams || SERVING_GRAMS_DEFAULT),
    );

    result.push(agg);
  }
  return result;
}

/* Compose a meal's effective category list given the user's overlay.
 * Preserves the original ordering and dedupes added categories that
 * already appeared on the meal. */
function effectiveCategoryList(baseCategories, added, removed) {
  const seen = new Set();
  const out = [];
  for (const c of baseCategories) {
    if (removed.has(c)) continue;
    if (seen.has(c)) continue;
    seen.add(c);
    out.push(c);
  }
  for (const c of added) {
    if (removed.has(c)) continue;
    if (seen.has(c)) continue;
    seen.add(c);
    out.push(c);
  }
  return out;
}

/**
 * Aggregate a user-built meal — { id, name, ingredients: [{ ingredientId, grams }] }
 * — into the same ingredient-shaped record curated meals use. Nutrient values
 * are the gram-weighted mean of the constituent ingredients' per-100g values,
 * which is the meal's true per-100g profile: scaling the meal up or down
 * by total grams doesn't change the projected position.
 *
 * Group weights are gram-weighted in the same way. Missing ingredients (whose
 * id no longer exists in the dataset) are silently skipped — the meal
 * still plots based on whatever ingredients can be resolved.
 *
 * Returns `null` for meals with no resolvable ingredients (zero total
 * grams), so callers can skip them in the meal-level dataset.
 */
export function aggregateUserMeal(userMeal, ingredients) {
  if (!userMeal) return null;

  // Phase 37: category-shaped user meal (the "save remix" output).
  // Same aggregation pipeline curated meals use, but tagged isUserMade
  // so the meal-builder card list can edit / delete it. We don't go
  // through aggregateMeals here because that function takes the WHOLE
  // meals list and reads its own categories map; for a single user
  // meal it's lighter to do the equal-weighted mean inline.
  if (Array.isArray(userMeal.ingredient_categories) && userMeal.ingredient_categories.length > 0) {
    const byCategory = new Map();
    for (const cat of aggregateByCategory(ingredients)) byCategory.set(cat.name, cat);
    const cats = userMeal.ingredient_categories
      .map(name => byCategory.get(name))
      .filter(Boolean);
    if (cats.length === 0) return null;
    /* Plate model — see aggregateMeals for the rationale. */
    let totalGrams = 0;
    for (const c of cats) totalGrams += (c.serving_grams || SERVING_GRAMS_DEFAULT);
    if (!(totalGrams > 0)) totalGrams = cats.length * SERVING_GRAMS_DEFAULT;
    const agg = {
      id: userMeal.id,
      name: userMeal.name || 'Untitled meal',
      category: 'Meal',
      subcategory: userMeal.name || 'Untitled meal',
      examples: userMeal.ingredient_categories.slice(),
      notes: userMeal.notes
        || `Your remix · ${userMeal.ingredient_categories.join(', ')}.`,
      tags: Array.isArray(userMeal.tags) ? userMeal.tags.slice() : [],
      group_weights: [0, 0, 0],
      isUserMade: true,
      source: 'user',
      kind: 'category',
      serving_grams: totalGrams,
    };
    for (const field of NUTRIENT_FIELDS) {
      let totalNutrient = 0;
      for (const c of cats) {
        const sg = c.serving_grams || SERVING_GRAMS_DEFAULT;
        totalNutrient += (c[field] || 0) * (sg / 100);
      }
      agg[field] = totalNutrient / totalGrams * 100;
    }
    for (const c of cats) {
      const sg = c.serving_grams || SERVING_GRAMS_DEFAULT;
      agg.group_weights[0] += sg * c.group_weights[0];
      agg.group_weights[1] += sg * c.group_weights[1];
      agg.group_weights[2] += sg * c.group_weights[2];
    }
    agg.group_weights = agg.group_weights.map(w => w / totalGrams);
    agg.food_group_weights = averageFoodGroupWeights(
      cats,
      c => (c.serving_grams || SERVING_GRAMS_DEFAULT),
    );
    return agg;
  }

  if (!Array.isArray(userMeal.ingredients)) return null;
  const ingredientById = new Map(ingredients.map(f => [f.id, f]));

  let totalGrams = 0;
  for (const ing of userMeal.ingredients) {
    if (ingredientById.has(ing.ingredientId) && ing.grams > 0) totalGrams += ing.grams;
  }
  if (totalGrams <= 0) return null;

  const exampleNames = userMeal.ingredients
    .map(i => ingredientById.get(i.ingredientId)?.name)
    .filter(Boolean);

  const ingredientCount = exampleNames.length;
  const agg = {
    id: userMeal.id,
    name: userMeal.name || 'Untitled meal',
    category: 'Meal',
    subcategory: userMeal.name || 'Untitled meal',
    examples: exampleNames,
    notes: userMeal.notes
      || `Your meal · ${totalGrams}g across ${ingredientCount} ingredient${ingredientCount === 1 ? '' : 's'}.`,
    tags: Array.isArray(userMeal.tags) ? userMeal.tags.slice() : [],
    group_weights: [0, 0, 0],
    isUserMade: true,
    source: 'user',
    kind: 'ingredient',
    /* The user already picked the exact grams — so the meal's serving
     * IS its total grams. Skips the 350g fallback for plotted /
     * displayed per-serving values. */
    serving_grams: totalGrams,
  };

  for (const field of NUTRIENT_FIELDS) {
    let sum = 0;
    for (const ing of userMeal.ingredients) {
      const f = ingredientById.get(ing.ingredientId);
      if (!f || !(ing.grams > 0)) continue;
      sum += ing.grams * f[field];
    }
    agg[field] = sum / totalGrams;
  }
  for (const ing of userMeal.ingredients) {
    const f = ingredientById.get(ing.ingredientId);
    if (!f || !(ing.grams > 0)) continue;
    agg.group_weights[0] += ing.grams * f.group_weights[0];
    agg.group_weights[1] += ing.grams * f.group_weights[1];
    agg.group_weights[2] += ing.grams * f.group_weights[2];
  }
  agg.group_weights = agg.group_weights.map(w => w / totalGrams);
  agg.food_group_weights = averageFoodGroupWeights(
    userMeal.ingredients
      .map(ing => ({ ...ingredientById.get(ing.ingredientId), _g: ing.grams }))
      .filter(f => f && f.food_group && f._g > 0),
    f => f._g,
  );

  return agg;
}

/**
 * Curated + user meals merged into one ingredient-shaped dataset. Curated meals
 * come first so the Meals view shows the stable library before user
 * compositions. Useful both for the Meals view-level (rendered as
 * spheres) and for any downstream code that needs "every meal".
 */
export function aggregateAllMeals(ingredients, curatedMeals, userMeals, composition) {
  const curated = aggregateMeals(ingredients, curatedMeals || [], composition);
  // Phase 35 composition only applies to curated meals (whose
  // identity is a category list). User meals are gram-weighted ingredient
  // mixtures — adding a "category" to one would be ambiguous. Leave them
  // unchanged.
  const user = (userMeals || [])
    .map(m => aggregateUserMeal(m, ingredients))
    .filter(Boolean);
  return [...curated, ...user];
}
