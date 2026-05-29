/* Normalize raw per-100g nutrient values onto [0, 1] axis positions.
 *
 * Each axis carries two independent settings:
 *
 *   axes = [
 *     { nutrient: 'calories', direction: 'min', orientation: 'descending', constraint },
 *     { nutrient: 'carbs',    direction: 'min', orientation: 'descending', constraint },
 *     { nutrient: 'protein',  direction: 'max', orientation: 'ascending',  constraint },
 *   ]
 *
 * `direction` is the **semantic preference**: 'min' (low is best) or 'max'
 * (high is best). It does NOT affect ingredient positions. It governs where the
 * "★ Best" / "✗ Worst" corner sprites land — Best is at the cube corner
 * where each axis is at its preferred end.
 *
 * `orientation` is the **visual axis flip**: 'ascending' (value at min lands
 * at position 0, max at position 1) or 'descending' (inverted). It controls
 * tick label ordering and ingredient positions. Toggling orientation flips the
 * axis without changing the semantic.
 *
 * The two together determine where Best sits on each axis:
 *   direction='max' + orientation='ascending'  → best at position 1 (tip)
 *   direction='min' + orientation='descending' → best at position 1 (tip)
 *   direction='max' + orientation='descending' → best at position 0 (origin)
 *   direction='min' + orientation='ascending'  → best at position 0 (origin)
 *
 * Default state has the two settings coupled so that Best lands at (1,1,1)
 * — the cluster of "best ingredients" sits in the top-right-front corner. The
 * user can decouple by flipping orientation independently in the picker.
 *
 * `constraint` (optional) is the EFFECTIVE RANGE for that axis. Tick labels
 * read from it, and `normalizeFood` projects against it — so a tightened
 * constraint zooms the axis in. Out-of-range ingredients land outside the unit
 * cube but stay rendered.
 */

export const DEFAULT_AXES = Object.freeze([
  Object.freeze({ nutrient: 'calories', direction: 'min', orientation: 'descending' }),
  Object.freeze({ nutrient: 'carbs',    direction: 'min', orientation: 'descending' }),
  Object.freeze({ nutrient: 'protein',  direction: 'max', orientation: 'ascending'  }),
]);

/**
 * Inspect the dataset and return per-nutrient { min, max } envelopes for
 * every numeric field present on the first ingredient. min === max is bumped so
 * downstream division never produces NaN.
 */
export function computeRanges(ingredients) {
  if (!Array.isArray(ingredients) || ingredients.length === 0) {
    throw new Error('computeRanges: dataset must be a non-empty array');
  }

  const ranges = {};
  const numericFields = Object.keys(ingredients[0]).filter(
    k => typeof ingredients[0][k] === 'number' && Number.isFinite(ingredients[0][k]),
  );

  for (const field of numericFields) {
    let min = Infinity;
    let max = -Infinity;
    for (const ingredient of ingredients) {
      const v = ingredient[field];
      if (typeof v === 'number' && Number.isFinite(v)) {
        if (v < min) min = v;
        if (v > max) max = v;
      }
    }
    if (min === max) max = min + 1;
    ranges[field] = { min, max };
  }

  return ranges;
}

/**
 * Map a raw value onto [0, 1] for an axis with the given range and orientation.
 *   orientation='ascending'  → value at min lands at 0, max lands at 1 (direct).
 *   orientation='descending' → value at min lands at 1, max lands at 0 (inverted).
 */
export function projectAxis(value, range, orientation) {
  if (orientation === 'descending') {
    return (range.max - value) / (range.max - range.min);
  }
  return (value - range.min) / (range.max - range.min);
}

/**
 * Resolve the effective range for an axis: its constraint if set, otherwise
 * the dataset envelope for its nutrient. A degenerate (zero-width) constraint
 * is widened by 1 to avoid divide-by-zero downstream.
 */
export function effectiveRange(axis, ranges) {
  const base = ranges[axis.nutrient];
  if (!axis.constraint) return base;
  let { min, max } = axis.constraint;
  if (!(max > min)) max = min + 1;
  return { min, max };
}

/**
 * Project a ingredient onto the (x, y, z) axes given the axis config and dataset
 * ranges. Returns { id, x, y, z }. Each component may fall outside [0, 1]
 * if the ingredient's value is outside that axis's constraint.
 *
 * Phase 40 round 10: optional `scale` multiplies each nutrient value
 * before projection — used by the per-serving unit toggle so the dots
 * reposition to reflect serving-size values instead of per-100g. Pass
 * 1 (default) for the standard per-100g behavior.
 */
export function normalizeFood(ingredient, axes, ranges, scale = 1) {
  const [ax, ay, az] = axes;
  return {
    id: ingredient.id,
    x: projectAxis(ingredient[ax.nutrient] * scale, effectiveRange(ax, ranges), ax.orientation),
    y: projectAxis(ingredient[ay.nutrient] * scale, effectiveRange(ay, ranges), ay.orientation),
    z: projectAxis(ingredient[az.nutrient] * scale, effectiveRange(az, ranges), az.orientation),
  };
}

/**
 * Normalize an entire dataset in one pass. Returns { ranges, positions }
 * where ranges covers every numeric nutrient (not just the three on the
 * current axes) so the Phase 7 threshold UI can stay live as the axis
 * selection changes.
 *
 * Phase 40 round 10: optional `getScale(ingredient) => number` callback
 * is invoked per item to determine its display multiplier (e.g., per-
 * serving uses `servingGramsFor(ing)/100`). When omitted, scale=1 for
 * every item — original per-100g behavior.
 */
export function normalizeDataset(ingredients, axes = DEFAULT_AXES, getScale = null) {
  const ranges = computeRanges(ingredients);
  const positions = ingredients.map(f =>
    normalizeFood(f, axes, ranges, getScale ? (getScale(f) || 1) : 1)
  );
  return { ranges, positions };
}

/**
 * Map an arbitrary raw nutrient value back onto [0, 1] given the nutrient,
 * the axis's orientation, and the dataset ranges. Used by the Phase 7
 * threshold UI when sliders work in real units but the scene works in
 * normalized positions. Result is clamped to [0, 1].
 */
export function normalizeValue(value, nutrient, orientation, ranges) {
  const range = ranges[nutrient];
  if (!range) {
    throw new Error(`normalizeValue: unknown nutrient "${nutrient}"`);
  }
  return Math.min(1, Math.max(0, projectAxis(value, range, orientation)));
}
