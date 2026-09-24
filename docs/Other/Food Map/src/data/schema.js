/* Ingredient dataset schema and validation.
 *
 * Each ingredient entry is a flat object with:
 *   id              string, unique within the dataset (slug-like, kebab-case)
 *   name            string, human-readable
 *   category        string, mid-level grouping (e.g. "Leafy greens", "Whole grains")
 *   subcategory     string, finer label within the category
 *   food_group      string, one of FOOD_GROUPS — used as the top level of the
 *                   ingredient filter tree (food-science classification, not the
 *                   3-channel [animal, plant, dairy] used for visualization)
 *   group_weights   [animal, plant, dairy] — three numbers in [0, 1] summing to 1.
 *                   Drives the additive RGB color blending for meal centroids.
 *                   Per the single-group rule, every ingredient has one channel
 *                   = 1 and the others = 0.
 *   contains        array of strings — dietary-restriction tags (see
 *                   src/core/restrictions.js for the vocabulary).
 *   form            (optional) one of FORMS — physical state of the ingredient.
 *                   Lets fresh / canned / dried / frozen variants coexist
 *                   without exploding the category tree. Omit when ambiguous
 *                   or when the entry stands for the canonical raw form.
 *   examples        array of strings — short common preparations / dish names
 *   calories        number, kcal per 100g
 *   carbs           number, g per 100g (total carbohydrate)
 *   protein         number, g per 100g
 *   fiber           number, g per 100g
 *   fat             number, g per 100g (total fat)
 *   sodium          number, mg per 100g
 *   sugar           number, g per 100g (total sugars)
 *   saturated_fat   number, g per 100g
 *   notes           string, free-text context (1–2 sentences)
 *
 * Validators continue past the first error so a single run surfaces every
 * problem in the dataset.
 */

export const FOOD_GROUPS = [
  'Vegetables',
  'Fruits',
  'Grains',
  'Protein (animal)',
  'Protein (plant)',
  'Dairy',
  'Nuts & seeds',
  'Fats & oils',
  'Sweets',
  'Herbs & spices',
  'Condiments & sauces',
  'Beverages',
];

/* Phase 14: 12 food_groups (Beverages added). 11 hues spaced 360/11 ≈ 32.7°
 * on the HSL wheel at S=100%, L=50% so the additive A/P/D primaries and the
 * food_group palette read at the same brightness. Dairy keeps its warm
 * off-white "no hue" slot. Beverages slots between Vegetables and Herbs &
 * spices (teal/aqua — liquid-ish, sitting between produce-green and herb-
 * cyan). Stored as `[r, g, b]` floats in [0, 1].
 */
export const FOOD_GROUP_COLORS = {
  'Fruits':              [1.0,  0.0,  0.0 ], // hue 0°      — pure red
  'Protein (animal)':    [1.0,  0.55, 0.0 ], // hue 32.7°   — orange (cooked meat)
  'Grains':              [0.9,  1.0,  0.0 ], // hue 65.4°   — yellow (wheat)
  'Protein (plant)':     [0.35, 1.0,  0.0 ], // hue 98.2°   — chartreuse
  'Vegetables':          [0.0,  1.0,  0.2 ], // hue 130.9°  — leaf green
  'Beverages':           [0.0,  1.0,  0.75], // hue 163.6°  — teal/aqua
  'Herbs & spices':      [0.0,  0.75, 1.0 ], // hue 196.4°  — cyan-azure
  'Fats & oils':         [0.0,  0.2,  1.0 ], // hue 229.1°  — azure
  'Sweets':              [0.35, 0.0,  1.0 ], // hue 261.8°  — blue-violet
  'Nuts & seeds':        [0.9,  0.0,  1.0 ], // hue 294.5°  — purple
  'Condiments & sauces': [1.0,  0.0,  0.55], // hue 327.3°  — magenta
  'Dairy':               [1.0,  0.98, 0.3 ], // creamy yellow — high G with low B so the hue reads as lemon yellow, distinct from the (1.0, 0.55, 0) orange used for Protein (animal). Low enough B that Lambert lighting (max 1.25×) doesn't clip the yellow tone to plain white.
};

/* Phase 14: 12 food_groups in legend-display order. Dairy (cream, no hue)
 * leads, then the 11-hue rainbow at 32.7° spacing. The data-shape order is
 * in FOOD_GROUPS; this is only for legend rendering. */
/* Display labels for the 3-channel `group_weights` vector. Distinct from
 * FOOD_GROUPS (the 12 food-science groups) — this is the additive RGB
 * visualization scheme: Animal=R, Plant=G, Dairy=B. */
export const GROUP_WEIGHT_LABELS = ['Animal', 'Plant', 'Dairy'];

export const FOOD_GROUPS_BY_HUE = [
  'Dairy',                // cream (no hue)
  'Fruits',               // 0°
  'Protein (animal)',     // 32.7°
  'Grains',               // 65.4°
  'Protein (plant)',      // 98.2°
  'Vegetables',           // 130.9°
  'Beverages',            // 163.6°
  'Herbs & spices',       // 196.4°
  'Fats & oils',          // 229.1°
  'Sweets',               // 261.8°
  'Nuts & seeds',         // 294.5°
  'Condiments & sauces',  // 327.3°
];

/* Phase 14: optional `form` field on ingredients. Lets the same canonical
 * ingredient appear in multiple physical states (canned tomato vs. fresh
 * tomato) without doubling the category tree. Omit `form` when the entry
 * stands for the canonical raw form of the ingredient. */
export const FORMS = [
  'fresh',
  'canned',
  'frozen',
  'dried',
  'cured',
  'cooked',
  'powdered',
  'paste',
  'pickled',
];

/* Phase 26: optional cross-category `tags` array on ingredients. Each entry
 * may carry any number of tags from this vocabulary; the filter UI composes
 * them with OR semantic (any selected tag matches = ingredient is active).
 * Tags are orthogonal to food_group / category / subcategory — they describe
 * usage / nutrient profile / preparation / culinary role rather than
 * taxonomy.
 *
 * Auto-computed tags (from per-100g nutrient values):
 *   high-protein   protein supplies >= 40% of calories (and >= 5g/100g)
 *                  OR protein >= 20g/100g (whichever is met first)
 *   high-fiber     fiber    >= 6   g/100g
 *   low-cal        calories <  100 kcal/100g
 *   high-sodium    sodium   >= 600 mg/100g
 *
 * Hand-assigned tags (food identity / role):
 *   breakfast        items typically eaten at the morning meal
 *   lunch            items / meals typically eaten at midday (curated meals only — Batch 5b)
 *   dinner           items / meals typically eaten in the evening (curated meals only — Batch 5b)
 *   snack            items typically eaten between meals (chips, nuts, jerky, etc.)
 *   dessert          items typically eaten as a sweet course
 *   condiment        flavor add-ons (sauces, mustards, vinegars, etc.)
 *   garnish          finishing-style additions (fresh herbs, microgreens, zest)
 *   fermented        yogurt / kefir / kimchi / miso / sauerkraut / sourdough / etc.
 *   cured            bacon / ham / prosciutto / salami / cured fish
 *   smoked           items processed with smoke
 *   omega3-rich      salmon / mackerel / sardines / chia / flax / hemp / walnut
 *   iron-rich        liver / heart / kidney / red meat / dark leafy greens / lentils
 *                    (NOTE: now derived from iron value ≥ 3.5 mg/100g; see NUTRIENT_TAG_RULES)
 *
 * lunch/dinner tags are unusual in that they only apply to whole meals
 * (curated meals.json), not individual ingredients — most foods aren't
 * intrinsically "lunch" or "dinner", but a meal-as-composed is.
 * scripts/tag_meals_by_mealtime.py is the source of those tags.
 */
export const TAGS = [
  'high-protein', 'high-fiber', 'low-cal', 'high-sodium',
  'breakfast', 'lunch', 'dinner', 'snack', 'dessert', 'condiment', 'garnish',
  'fermented', 'cured', 'smoked',
  'omega3-rich', 'iron-rich',
];

/* Phase 40 round 7: predicates that re-derive the four nutrient-based
 * tags from an ingredient's actual values. Stored tags drift over time
 * (a tester correctly noticed "high-fiber" items with 0.9g fiber); we
 * recompute these at boot so the filter is always honest. Identity
 * tags (breakfast/snack/etc.) stay as curated since they're qualitative.
 *
 * Batch 5: iron-rich was a hand-curated tag; now that iron is a
 * first-class nutrient field, derive iron-rich from the actual value.
 * Threshold: ≥ 3.5 mg/100g (FDA "high" cutoff for iron, equivalent to
 * ≥ 20% DV per RACC for a typical serving size). */
export const NUTRIENT_TAG_RULES = {
  'high-protein': (ing) => {
    const cals = +ing.calories || 0;
    const prot = +ing.protein  || 0;
    if (prot >= 20) return true;
    const protCals = prot * 4;
    return cals > 0 && (protCals / cals) >= 0.4 && prot >= 5;
  },
  'high-fiber':   (ing) => (+ing.fiber   || 0) >= 6,
  'low-cal':      (ing) => (+ing.calories || 0) < 100,
  'high-sodium':  (ing) => (+ing.sodium  || 0) >= 600,
  'iron-rich':    (ing) => (+ing.iron    || 0) >= 3.5,
};

export const NUTRIENT_TAG_KEYS = Object.keys(NUTRIENT_TAG_RULES);

/* Returns the ingredient's effective tag list: identity tags (as curated)
 * plus recomputed nutrient tags. Stored nutrient tags are discarded so
 * stale data can't outvote the actual numbers. */
export function effectiveTags(ingredient) {
  if (!ingredient) return [];
  const stored = Array.isArray(ingredient.tags) ? ingredient.tags : [];
  const nutSet = new Set(NUTRIENT_TAG_KEYS);
  const out = stored.filter(t => !nutSet.has(t));
  for (const t of NUTRIENT_TAG_KEYS) {
    if (NUTRIENT_TAG_RULES[t](ingredient)) out.push(t);
  }
  return out;
}

/* Phase 40 round 7 / round 12: per-category serving sizes (in grams)
 * based on the USDA Reference Amount Customarily Consumed (RACC,
 * 21 CFR 101.12) where available — these are the FDA-defined "typical
 * serving" amounts used on Nutrition Facts panels.
 *
 * Categories override the broader food_group default. The override
 * map is consulted first; food_group fall-back picks up anything that
 * doesn't have a category-level entry. Meals get a fixed 350g plate.
 *
 * Why a per-category map instead of food_group alone: Dairy spans
 * milk (240g) and butter (14g); Beverages span tea/coffee (240g),
 * soda (360g), wine (150g), and spirits (45g); Grains span dry oats
 * (40g) and cooked pasta (140g). One number per food_group can't
 * represent all of those honestly. */
export const SERVING_GRAMS_BY_CATEGORY = {
  // --- Vegetables ---
  'Leafy greens':              30,   // 1 cup raw
  'Cruciferous vegetables':    85,
  'Peppers & nightshades':     85,
  'Starchy vegetables':       125,   // medium potato, ear of corn
  'Other vegetables':          85,
  'Mushrooms':                 70,
  'Pickled vegetables':        30,
  // --- Fruits ---
  'Berries':                  140,
  'Citrus':                   130,
  'Tropical fruits':          140,
  'Temperate fruits':         140,
  'Dried fruits':              40,
  // --- Grains (DRY measure for staples; cooked-form items in their own group) ---
  'Whole grains':              45,   // 1/4 cup dry rice/oats
  'Refined grains':            45,
  'Bread & rolls':             55,   // 1-2 slices
  'Baked snacks & pastries':   40,
  'Flours':                    30,
  'Prepared mixes':            55,
  'Noodle & rice alternatives':115,  // hydrated shirataki / konjac / kelp portion
  // --- Protein (animal), all cooked weights ---
  'Red meat':                  85,   // 3 oz
  'Poultry':                   85,
  'Organ meats':               85,
  'Processed meat':            55,
  'Eggs':                      50,   // 1 large
  'White fish':                85,
  'Oily fish':                 85,
  'Freshwater fish':           85,
  'Shellfish':                 85,
  'Canned & cured fish':       55,
  // --- Protein (plant) ---
  'Legumes':                  130,   // 1/2 cup cooked
  'Soy products':              85,   // tofu / tempeh
  'Meat alternatives':         85,
  // --- Dairy ---
  'Milk':                     240,   // 1 cup (8 fl oz)
  'Plant milks':              240,
  'Yogurt':                   170,   // 6 oz container
  'Fermented dairy':          170,
  'Aged cheese':               28,   // 1 oz
  'Fresh cheese':              55,
  'Processed cheese':          28,
  'Cream & butter':            14,   // 1 tbsp
  'Frozen dairy':              85,   // 1/2 cup ice cream
  // --- Nuts & seeds ---
  'Nuts':                      28,   // 1 oz
  'Seeds':                     28,
  'Nut butters':               32,   // 2 tbsp
  // --- Fats & oils ---
  'Oils':                      14,   // 1 tbsp
  'Margarine & shortening':    14,
  // --- Sweets ---
  'Sugar & sweeteners':         4,   // 1 tsp added sugar
  'Jams & preserves':          20,   // 1 tbsp
  'Candy & desserts':          40,
  // --- Herbs & spices ---
  'Fresh herbs':                3,   // garnish-size
  'Dried herbs':                0.5, // pinch
  'Ground spices':              1,
  'Whole spices':               1,
  'Spice blends':               1,
  'Salt & seasonings':          1,
  'Extracts & essences':        2,
  // --- Condiments & sauces ---
  'Sauces':                    30,   // 2 tbsp
  'Dressings & dips':          30,
  'Pastes & ferments':         15,   // 1 tbsp
  'Prepared soups & broths':  245,   // 1 cup
  'Baking ingredients':        12,
  // --- Beverages ---
  'Coffee & tea':             240,   // 1 cup
  'Juices':                   240,
  'Soft drinks':              355,   // 12 fl oz can
  'Alcoholic beverages':      150,   // 5 fl oz wine baseline
};

/* food_group fall-back, used when a category-level entry isn't set
 * (or when the item is an aggregate whose category is unknown). */
export const SERVING_GRAMS_BY_FOOD_GROUP = {
  'Vegetables':           85,
  'Fruits':              140,
  'Grains':               55,
  'Protein (animal)':     85,
  'Protein (plant)':     100,
  'Dairy':                85,
  'Nuts & seeds':         28,
  'Fats & oils':          14,
  'Sweets':               30,
  'Herbs & spices':        1,
  'Condiments & sauces':  30,
  'Beverages':           240,
};

export const SERVING_GRAMS_MEAL    = 350;   // typical mixed plate
export const SERVING_GRAMS_DEFAULT = 100;

/* Pick a sensible serving size for any ingredient / category / meal
 * aggregate. Resolution order:
 *   1. Item has its own `serving_grams` (set per-ingredient by
 *      scripts/backfill_serving_grams.py from USDA SR / FDA RACC)
 *      → use that. THIS is the most accurate path and covers every
 *      ingredient after the backfill ran.
 *   2. Meal aggregate  → 350g fixed plate
 *   3. Category lookup → SERVING_GRAMS_BY_CATEGORY (for aggregates
 *      whose `.name` equals a category)
 *   4. Dominant food_group (for category/meal aggregates that have
 *      `food_group_weights`) → SERVING_GRAMS_BY_FOOD_GROUP
 *   5. Own food_group field → SERVING_GRAMS_BY_FOOD_GROUP
 *   6. Fallback 100g
 *
 * In practice every raw ingredient now hits step 1; aggregates
 * (Category / Meal view) flow through step 2 / 3. */
export function servingGramsFor(item) {
  if (!item) return SERVING_GRAMS_DEFAULT;
  if (typeof item.serving_grams === 'number' && Number.isFinite(item.serving_grams)) {
    return item.serving_grams;
  }
  if (item.category === 'Meal') {
    // Single-category compositional patterns (e.g. the corpus "Red meat"
    // pattern with examples=['Red meat']) read more honestly at the
    // category's serving than the 350g mixed-plate baseline.
    if (Array.isArray(item.examples) && item.examples.length === 1
        && SERVING_GRAMS_BY_CATEGORY[item.examples[0]] != null) {
      return SERVING_GRAMS_BY_CATEGORY[item.examples[0]];
    }
    return SERVING_GRAMS_MEAL;
  }
  if (item.category && SERVING_GRAMS_BY_CATEGORY[item.category] != null) {
    return SERVING_GRAMS_BY_CATEGORY[item.category];
  }
  // Category-level aggregates use the aggregate's own name as the category.
  if (item.name && SERVING_GRAMS_BY_CATEGORY[item.name] != null) {
    return SERVING_GRAMS_BY_CATEGORY[item.name];
  }
  // Fall back to dominant food_group for aggregates, then own food_group.
  if (item.food_group_weights) {
    let bestGrp = null, bestW = -Infinity;
    for (const [grp, w] of Object.entries(item.food_group_weights)) {
      if (w > bestW) { bestW = w; bestGrp = grp; }
    }
    if (bestGrp && SERVING_GRAMS_BY_FOOD_GROUP[bestGrp] != null) {
      return SERVING_GRAMS_BY_FOOD_GROUP[bestGrp];
    }
  }
  if (item.food_group && SERVING_GRAMS_BY_FOOD_GROUP[item.food_group] != null) {
    return SERVING_GRAMS_BY_FOOD_GROUP[item.food_group];
  }
  return SERVING_GRAMS_DEFAULT;
}

/* Phase 34: diet definitions.
 *
 * Each diet maps to:
 *   excludedCategories:    a meal is incompatible if its ingredient_categories
 *                          intersects this list.
 *   nutrientMin / nutrientMax: per-100g aggregate-nutrient thresholds the
 *                          meal must satisfy to be compatible.
 *
 * `computeDietCompatibility(meal, categoryAggregates)` in
 * core/diet-compatibility.js runs each meal through these rules and
 * returns the array of compatible diet keys. The same rules drive the
 * Phase 34 backfill script so meals.json carries a precomputed
 * `diet_compatibility` array.
 *
 * The category lists are deliberately broad — diets are family of rules,
 * not strict definitions. A meal that passes here is "compatible enough to
 * surface in a diet-filter"; the user can drill in for nuance.
 */
export const DIETS = {
  keto: {
    key: 'keto',
    label: 'Keto',
    excludedCategories: [
      'Whole grains', 'Refined grains', 'Bread & rolls', 'Pasta & noodles',
      'Baked snacks & pastries', 'Legumes', 'Soy products',
      'Starchy vegetables', 'Sugar & sweeteners', 'Candy & desserts',
      'Jams & preserves', 'Juices', 'Soft drinks',
      'Tropical fruits', 'Temperate fruits', 'Dried fruits',
      'Prepared mixes',
    ],
    // Batch 14: nutrient floor catches berry-heavy parfaits and other
    // category-permissive items that exceed real keto carb budgets.
    // 15 g carbs / 100g of plate ≈ ≤45g per typical 300g serving.
    nutrientMax: { carbs: 15, sugar: 8 },
  },
  paleo: {
    key: 'paleo',
    label: 'Paleo',
    excludedCategories: [
      'Whole grains', 'Refined grains', 'Bread & rolls', 'Pasta & noodles',
      'Baked snacks & pastries', 'Legumes', 'Soy products',
      'Milk', 'Yogurt', 'Aged cheese', 'Fresh cheese', 'Processed cheese',
      'Fermented dairy', 'Frozen dairy', 'Cream & butter',
      'Sugar & sweeteners', 'Candy & desserts', 'Jams & preserves',
      'Alcoholic beverages', 'Soft drinks', 'Prepared mixes',
      'Margarine & shortening',
      'Processed meat',
      'Noodle & rice alternatives',  // konjac/processed; not paleo
    ],
  },
  mediterranean: {
    key: 'mediterranean',
    label: 'Mediterranean',
    excludedCategories: [
      'Processed meat', 'Processed cheese',
      'Candy & desserts', 'Soft drinks',
      'Baked snacks & pastries', 'Margarine & shortening',
      'Prepared mixes',
    ],
  },
  whole30: {
    key: 'whole30',
    label: 'Whole30',
    excludedCategories: [
      'Whole grains', 'Refined grains', 'Bread & rolls', 'Pasta & noodles',
      'Baked snacks & pastries', 'Legumes', 'Soy products',
      'Milk', 'Yogurt', 'Aged cheese', 'Fresh cheese', 'Processed cheese',
      'Fermented dairy', 'Frozen dairy', 'Cream & butter',
      'Sugar & sweeteners', 'Candy & desserts', 'Jams & preserves',
      'Alcoholic beverages', 'Soft drinks', 'Juices',
      'Prepared mixes', 'Processed meat',
      'Noodle & rice alternatives',  // konjac/processed; not whole30
    ],
  },
  lowfodmap: {
    key: 'lowfodmap',
    label: 'Low FODMAP',
    excludedCategories: [
      'Legumes', 'Soy products',
      'Milk', 'Yogurt',
      'Sugar & sweeteners', 'Jams & preserves',
      'Dried fruits',
    ],
  },
  high_protein: {
    key: 'high_protein',
    label: 'High protein',
    // ≥15 g protein per 100g of meal-aggregate. Aggregates are equal-
    // weighted means of constituent category averages, so this lands the
    // bar at "meal centered on at least one substantive protein source".
    nutrientMin: { protein: 15 },
  },
};

export const DIET_KEYS = Object.keys(DIETS);

export const NUTRIENT_FIELDS = [
  'calories', 'carbs', 'protein', 'fiber', 'fat', 'sodium', 'sugar', 'saturated_fat',
  // Batch 5: iron added as a first-class nutrient field. Stored in mg per
  // 100g; surfaces everywhere the other nutrients do (axis picker, table,
  // detail panel, thresholds, score weights). Backfilled from USDA-aligned
  // category defaults via scripts/backfill_iron.py.
  'iron',
];

/* Per-nutrient display metadata: label for UI, unit, and a tick/cell formatter.
 * Anywhere a nutrient appears in the UI (axis tick labels, axis-picker, table
 * columns, detail panel) should pull from here so the wording stays uniform.
 */
function formatGrams(value) {
  if (value < 0.05) return '0g';
  if (value < 10 && Math.round(value) !== value) return `${value.toFixed(1)}g`;
  return `${Math.round(value)}g`;
}

/* All nutrient values in ingredients.json are per-100g of the ingredient itself, so the
 * meaningful unit for UI display is "X per 100g". `unit` stays compact for
 * dense tick labels in the 3D scene; `unitLong` is for menus and range
 * inputs where space is available and the per-100g context matters.
 */
/* Iron formatter: under 1mg shows one decimal, above shows whole mg.
 * Reads cleanly across the wide range we hit (milk 0.03mg → dark
 * chocolate 12mg → dried herbs 60mg+). */
function formatIron(v) {
  if (v == null || !Number.isFinite(v)) return '0 mg';
  if (v < 0.05) return '0 mg';
  if (v < 1)    return `${v.toFixed(2)} mg`;
  if (v < 10)   return `${v.toFixed(1)} mg`;
  return `${Math.round(v)} mg`;
}

export const NUTRIENT_META = {
  calories:      { label: 'Calories', unit: 'kcal', unitLong: 'kcal per 100g', format: v => `${Math.round(v)} kcal` },
  carbs:         { label: 'Carbs',    unit: 'g',    unitLong: 'g per 100g',    format: formatGrams },
  protein:       { label: 'Protein',  unit: 'g',    unitLong: 'g per 100g',    format: formatGrams },
  fiber:         { label: 'Fiber',    unit: 'g',    unitLong: 'g per 100g',    format: formatGrams },
  fat:           { label: 'Fat',      unit: 'g',    unitLong: 'g per 100g',    format: formatGrams },
  sodium:        { label: 'Sodium',   unit: 'mg',   unitLong: 'mg per 100g',   format: v => `${Math.round(v)} mg` },
  sugar:         { label: 'Sugar',    unit: 'g',    unitLong: 'g per 100g',    format: formatGrams },
  saturated_fat: { label: 'Sat. fat', unit: 'g',    unitLong: 'g per 100g',    format: formatGrams },
  iron:          { label: 'Iron',     unit: 'mg',   unitLong: 'mg per 100g',   format: formatIron },
};

/* Per-nutrient defaults for direction (semantic preference) and orientation
 * (visual axis flip). Used to seed the per-nutrient prefs cache at boot.
 * "Best" is generally low for energy-dense / sodium-heavy / refined-sugar
 * nutrients, high for protein and fiber.
 */
export const NUTRIENT_DEFAULTS = {
  calories:      { direction: 'min', orientation: 'descending' },
  carbs:         { direction: 'min', orientation: 'descending' },
  protein:       { direction: 'max', orientation: 'ascending'  },
  fiber:         { direction: 'max', orientation: 'ascending'  },
  fat:           { direction: 'min', orientation: 'descending' },
  sodium:        { direction: 'min', orientation: 'descending' },
  sugar:         { direction: 'min', orientation: 'descending' },
  saturated_fat: { direction: 'min', orientation: 'descending' },
  // Iron is a beneficial micronutrient — more is better up to the dietary
  // limit (45 mg/day UL for adults), which no realistic food approaches.
  iron:          { direction: 'max', orientation: 'ascending'  },
};

const REQUIRED_FIELDS = [
  'id', 'name', 'category', 'subcategory', 'food_group',
  'contains', 'group_weights', 'examples',
  ...NUTRIENT_FIELDS,
  'notes',
];

const GROUP_WEIGHT_TOLERANCE = 1e-3;

function isFiniteNumber(v) {
  return typeof v === 'number' && Number.isFinite(v);
}

/**
 * Validate a single ingredient object.
 * Returns { ok: boolean, errors: Array<{ field, message }> }.
 */
export function validateIngredient(ingredient) {
  const errors = [];
  const push = (field, message) => errors.push({ field, message });

  if (ingredient == null || typeof ingredient !== 'object') {
    return { ok: false, errors: [{ field: '<root>', message: 'ingredient is not an object' }] };
  }

  for (const field of REQUIRED_FIELDS) {
    if (!(field in ingredient)) push(field, 'missing required field');
  }

  if ('id' in ingredient && (typeof ingredient.id !== 'string' || ingredient.id.length === 0)) {
    push('id', 'must be a non-empty string');
  }
  for (const field of ['name', 'category', 'subcategory', 'food_group', 'notes']) {
    if (field in ingredient && typeof ingredient[field] !== 'string') {
      push(field, 'must be a string');
    }
  }
  if ('food_group' in ingredient && typeof ingredient.food_group === 'string'
      && !FOOD_GROUPS.includes(ingredient.food_group)) {
    push('food_group', `must be one of FOOD_GROUPS (got ${JSON.stringify(ingredient.food_group)})`);
  }

  if ('examples' in ingredient) {
    if (!Array.isArray(ingredient.examples)) {
      push('examples', 'must be an array of strings');
    } else if (!ingredient.examples.every(e => typeof e === 'string' && e.length > 0)) {
      push('examples', 'must contain only non-empty strings');
    }
  }

  if ('contains' in ingredient) {
    if (!Array.isArray(ingredient.contains)) {
      push('contains', 'must be an array of strings');
    } else if (!ingredient.contains.every(t => typeof t === 'string')) {
      push('contains', 'must contain only strings');
    }
  }

  if ('group_weights' in ingredient) {
    const gw = ingredient.group_weights;
    if (!Array.isArray(gw) || gw.length !== 3) {
      push('group_weights', 'must be a 3-element array [animal, plant, dairy]');
    } else if (!gw.every(isFiniteNumber)) {
      push('group_weights', 'must contain only finite numbers');
    } else if (gw.some(w => w < 0 || w > 1)) {
      push('group_weights', 'each weight must be in [0, 1]');
    } else {
      const sum = gw[0] + gw[1] + gw[2];
      if (Math.abs(sum - 1) > GROUP_WEIGHT_TOLERANCE) {
        push('group_weights', `must sum to 1.0 (got ${sum.toFixed(4)})`);
      }
    }
  }

  for (const field of NUTRIENT_FIELDS) {
    if (!(field in ingredient)) continue;
    const v = ingredient[field];
    if (!isFiniteNumber(v)) {
      push(field, 'must be a finite number');
    } else if (v < 0) {
      push(field, 'must be >= 0');
    }
  }

  if ('form' in ingredient && ingredient.form !== undefined && ingredient.form !== null) {
    if (typeof ingredient.form !== 'string') {
      push('form', 'must be a string when present');
    } else if (!FORMS.includes(ingredient.form)) {
      push('form', `must be one of FORMS (got ${JSON.stringify(ingredient.form)})`);
    }
  }

  if ('tags' in ingredient && ingredient.tags !== undefined && ingredient.tags !== null) {
    if (!Array.isArray(ingredient.tags)) {
      push('tags', 'must be an array of strings when present');
    } else {
      for (const t of ingredient.tags) {
        if (typeof t !== 'string') {
          push('tags', 'each tag must be a string');
        } else if (!TAGS.includes(t)) {
          push('tags', `unknown tag ${JSON.stringify(t)}`);
        }
      }
    }
  }

  return { ok: errors.length === 0, errors };
}

/**
 * Validate the whole dataset.
 * Returns { ok, errors, count } where errors[] entries carry { index, id?, field, message }.
 * Also checks that ids are unique.
 */
export function validateDataset(ingredients) {
  if (!Array.isArray(ingredients)) {
    return { ok: false, errors: [{ index: -1, field: '<root>', message: 'dataset is not an array' }], count: 0 };
  }

  const errors = [];
  const seenIds = new Map(); // id → first index

  ingredients.forEach((ingredient, index) => {
    const result = validateIngredient(ingredient);
    for (const err of result.errors) {
      errors.push({ index, id: ingredient && ingredient.id, ...err });
    }
    if (ingredient && typeof ingredient.id === 'string') {
      if (seenIds.has(ingredient.id)) {
        errors.push({
          index,
          id: ingredient.id,
          field: 'id',
          message: `duplicate id (first seen at index ${seenIds.get(ingredient.id)})`,
        });
      } else {
        seenIds.set(ingredient.id, index);
      }
    }
  });

  return { ok: errors.length === 0, errors, count: ingredients.length };
}
