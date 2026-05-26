/* View-level vocabulary.
 *
 * `state.viewLevel` is one of three string values that drive what the
 * scene plots and how filters compose:
 *   'individual' — one dot per ingredient (the original visualization)
 *   'category'   — one dot per category aggregate (grouped by
 *                  food_group / category / subcategory per state.categoryGroupBy)
 *   'meal'       — one dot per curated meal (or user meal)
 *
 * The string values are load-bearing — they appear in localStorage
 * (persistence) and in DOM data-value attributes (view-controls.js).
 * Do not rename them.
 *
 * `isAggregateView` is the predicate that recurs across the filter
 * pipeline: many code paths split on "is this the individual dataset
 * or one of the aggregated datasets?". Named here so the concept
 * lives in one place.
 */

export const VIEW_LEVELS = Object.freeze({
  INDIVIDUAL: 'individual',
  CATEGORY:   'category',
  MEAL:       'meal',
});

export function isAggregateView(level) {
  return level === VIEW_LEVELS.CATEGORY || level === VIEW_LEVELS.MEAL;
}

export function isIndividualView(level) {
  return level === VIEW_LEVELS.INDIVIDUAL;
}
