/* Default axis-constraint windows per nutrient and per unit.
 *
 * Phase 13.5 round 5 set the per-100g envelopes so quartile tick labels
 * read as round numbers and the dataset max stays inside the cube.
 * Phase 40 round 13 added the per-serving envelopes: multi-category
 * meals scale by ~3.5× from 100g→serving, so the per-100g envelopes
 * would push them off the cube; the serving values are picked to
 * comfortably hold typical meals without crowding ingredients.
 *
 * `defaultConstraintFor(nutrient, ranges)` returns the per-100g window
 * widened by the dataset's own min/max where the preset is narrower.
 * `defaultConstraintForServing(nutrient, ranges)` does NOT widen by
 * dataset min/max — the per-100g envelope is unit-incompatible with
 * per-serving values (a tester reported this bug). The fallback only
 * fires when a nutrient has no preset configured.
 */

export const AXIS_CONSTRAINT_DEFAULTS = {
  calories:      { min: 0, max: 1000  }, // dataset max 902
  carbs:         { min: 0, max: 100   }, // dataset max 100
  protein:       { min: 0, max: 110   }, // ingredients max 86; meals can reach ~107 (cheeseburger soup)
  fiber:         { min: 0, max: 100   }, // dataset max 78
  fat:           { min: 0, max: 100   }, // dataset max 100
  sodium:        { min: 0, max: 40000 }, // dataset max 38758 (salt-table after Phase 15)
  sugar:         { min: 0, max: 100   }, // dataset max 100
  saturated_fat: { min: 0, max: 100   }, // dataset max 82.5
  // Batch 5: iron range covers ordinary foods (0–10 mg) plus high
  // outliers — dried herbs/spices reach 50-90 mg/100g and cocoa solids
  // ~12 mg. 100 keeps the cube readable while still containing those.
  iron:          { min: 0, max: 100   },
};

export const AXIS_CONSTRAINT_DEFAULTS_SERVING = {
  calories:      { min: 0, max: 2000  },
  carbs:         { min: 0, max: 200   },
  protein:       { min: 0, max: 110   }, // ingredients max 86; meals can reach ~107 (cheeseburger soup)
  fiber:         { min: 0, max: 50    },
  fat:           { min: 0, max: 100   },
  sodium:        { min: 0, max: 5000  },
  sugar:         { min: 0, max: 100   },
  saturated_fat: { min: 0, max: 50    },
  // Per-serving iron: typical servings deliver < 5 mg; outlier meals
  // (liver, fortified cereal, dark chocolate) can push 10-15 mg per
  // serving. 25 mg covers comfortably.
  iron:          { min: 0, max: 25    },
};

export function defaultConstraintFor(nutrient, ranges) {
  const fallback = { min: ranges[nutrient].min, max: ranges[nutrient].max };
  const preset = AXIS_CONSTRAINT_DEFAULTS[nutrient];
  if (!preset) return fallback;
  return {
    min: Math.min(preset.min, fallback.min),
    max: Math.max(preset.max, fallback.max),
  };
}

export function defaultConstraintForServing(nutrient, ranges) {
  const preset = AXIS_CONSTRAINT_DEFAULTS_SERVING[nutrient];
  if (preset) return { min: preset.min, max: preset.max };
  const r = ranges[nutrient];
  return r ? { min: r.min, max: r.max } : { min: 0, max: 1 };
}
