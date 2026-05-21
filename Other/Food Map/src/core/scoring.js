/* Phase 7 thresholds: per-nutrient {min, max} ranges, mode selection,
 * and the scoring used by Score mode's per-ingredient color gradient.
 *
 * Shape of `thresholds`:
 *   { calories: { min, max }, carbs: { min, max }, ... }
 * Where min/max are in real per-100g units. Missing nutrients mean
 * "no constraint for this nutrient" — same as a wide-open slider.
 *
 * A ingredient passes the threshold filter iff every constrained nutrient
 * lies within [min, max].
 *
 * Score mode treats the midpoint of each [min, max] as the target.
 * Per-ingredient distance is the RMS of per-nutrient distances normalized by
 * dataset width, so calorie scale doesn't dominate gram scale. The map
 * is then renormalized to [0, 1] across the current ingredients so the worst
 * ingredient sits at 1 and the best at 0.
 */

import { NUTRIENT_FIELDS } from '../data/schema.js';

/* Phase 40 round 11: optional `scale` multiplies ingredient values
 * before comparing — used by the per-serving unit toggle so the
 * threshold filter tests "calories per serving" not "calories per
 * 100g". scale=1 (default) preserves original per-100g behavior. */
export function isWithinThresholds(ingredient, thresholds, scale = 1) {
  if (!thresholds) return true;
  for (const nutrient of NUTRIENT_FIELDS) {
    const t = thresholds[nutrient];
    if (!t) continue;
    const v = (ingredient[nutrient] || 0) * scale;
    if (typeof t.min === 'number' && v < t.min) return false;
    if (typeof t.max === 'number' && v > t.max) return false;
  }
  return true;
}

/* `getScale(ingredient) => number` lets the caller per-item the scale
 * (each ingredient has its own serving size). Defaults to 1 for all. */
export function thresholdActiveSet(ingredients, thresholds, getScale = null) {
  const active = new Set();
  if (!thresholds) {
    for (const f of ingredients) active.add(f.id);
    return active;
  }
  for (const f of ingredients) {
    const scale = getScale ? (getScale(f) || 1) : 1;
    if (isWithinThresholds(f, thresholds, scale)) active.add(f.id);
  }
  return active;
}

/**
 * RMS distance from per-nutrient targets, normalized by dataset width
 * so the slider sliders for protein (g) and calories (kcal) contribute
 * comparably. Returns a non-negative number — small means "close to all
 * targets", larger means "further out".
 */
export function distanceFromTargets(ingredient, thresholds, ranges, scale = 1) {
  let sumSq = 0;
  let count = 0;
  for (const nutrient of NUTRIENT_FIELDS) {
    const t = thresholds && thresholds[nutrient];
    if (!t) continue;
    const target = (t.min + t.max) / 2;
    const datasetWidth = Math.max(1e-6, ranges[nutrient].max - ranges[nutrient].min);
    const v = (ingredient[nutrient] || 0) * scale;
    const d = (v - target) / datasetWidth;
    sumSq += d * d;
    count++;
  }
  return count > 0 ? Math.sqrt(sumSq / count) : 0;
}

/**
 * Map every ingredient to a [0, 1] score where 0 = closest-to-targets among
 * the current dataset, 1 = furthest. Per-ingredient coloring in points.js
 * then maps these scores to the green→red gradient.
 */
export function computeScores(ingredients, thresholds, ranges, getScale = null) {
  const distances = ingredients.map(f =>
    distanceFromTargets(f, thresholds, ranges, getScale ? (getScale(f) || 1) : 1)
  );
  let minD = Infinity, maxD = -Infinity;
  for (const d of distances) { if (d < minD) minD = d; if (d > maxD) maxD = d; }
  const spread = Math.max(1e-6, maxD - minD);
  const scores = new Map();
  for (let i = 0; i < ingredients.length; i++) {
    scores.set(ingredients[i].id, (distances[i] - minD) / spread);
  }
  return scores;
}

/** Default thresholds = dataset envelope for every nutrient (no filter). */
export function defaultThresholds(ranges) {
  const t = {};
  for (const nutrient of NUTRIENT_FIELDS) {
    t[nutrient] = { min: ranges[nutrient].min, max: ranges[nutrient].max };
  }
  return t;
}

/** True iff the thresholds match the dataset envelope on every nutrient. */
export function isThresholdsBaseline(thresholds, ranges) {
  if (!thresholds) return true;
  for (const nutrient of NUTRIENT_FIELDS) {
    const t = thresholds[nutrient];
    if (!t) continue;
    const r = ranges[nutrient];
    if (Math.abs(t.min - r.min) > 1e-6) return false;
    if (Math.abs(t.max - r.max) > 1e-6) return false;
  }
  return true;
}

/* Phase 40.11: True iff the thresholds match the boot-initial defaults
 * (defaultsMap shape: { nutrient: { min, max } }). Active-filters uses
 * this so an untouched config doesn't generate "Calories ≤ 1000" chips
 * just because the user-default 1000 differs from the dataset max 902. */
export function isThresholdsAtDefaults(thresholds, defaultsMap) {
  if (!thresholds || !defaultsMap) return true;
  for (const nutrient of NUTRIENT_FIELDS) {
    const t = thresholds[nutrient];
    const d = defaultsMap[nutrient];
    if (!t || !d) continue;
    if (Math.abs(t.min - d.min) > 1e-6) return false;
    if (Math.abs(t.max - d.max) > 1e-6) return false;
  }
  return true;
}

/* Phase 40.11: per-nutrient "is this threshold at its default" check.
 * Used by active-filters to decide whether a per-nutrient chip should
 * appear. */
export function isNutrientThresholdAtDefault(t, d) {
  if (!t || !d) return true;
  return Math.abs(t.min - d.min) < 1e-6 && Math.abs(t.max - d.max) < 1e-6;
}
