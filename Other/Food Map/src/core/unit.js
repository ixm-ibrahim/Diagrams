/* Per-100g ↔ per-serving unit helpers.
 *
 * The dataset is authored per-100g. The header unit toggle
 * (state.nutrientUnit = '100g' | 'serving') flips every nutrient-bearing
 * surface into per-serving values via a single per-item scale factor:
 *
 *   scale = servingGramsFor(item) / 100   when unit === 'serving'
 *   scale = 1                              when unit === '100g'
 *
 * This module is the single source of truth. Scene (points, meals),
 * detail panel, table view, picking tooltip, filter pipeline, and the
 * active-filters chip rail all import from here so adding a new
 * surface (or changing the formula) is a one-place edit. Centralizing
 * also kills five copies of `(item) => unit === 'serving' ? sg/100 : 1`
 * that drifted across modules during Phase 40 rounds 7-13.
 */

import { servingGramsFor } from '../data/schema.js';

/** Per-item scale factor for the given unit. */
export function scaleForItem(item, unit) {
  if (unit !== 'serving') return 1;
  const sg = servingGramsFor(item);
  return Number.isFinite(sg) && sg > 0 ? (sg / 100) : 1;
}

/** Returns a function (item) => scale, capturing the unit so callers can
 *  pass it to threshold / normalize / score helpers without rechecking
 *  state on every item. */
export function makeScaleGetter(unit) {
  if (unit !== 'serving') return () => 1;
  return (item) => {
    const sg = servingGramsFor(item);
    return Number.isFinite(sg) && sg > 0 ? (sg / 100) : 1;
  };
}

/** Normalize whatever the caller has into 'serving' | '100g'. */
export function normalizeUnit(unit) {
  return unit === 'serving' ? 'serving' : '100g';
}
