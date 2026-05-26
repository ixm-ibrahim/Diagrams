/* Phase 13.5 round 2: explain why an ingredient is currently inactive.
 *
 * Returns an array of short reason strings describing every filter the
 * ingredient is failing right now. An empty array means the ingredient
 * passes all active filters (= rendered in its true color, not grey).
 *
 * Reasons checked, in user-facing priority order:
 *   1. Ingredient filter        (excludedIds checkbox)
 *   2. Dietary restrictions     (per-restriction label + matched tags)
 *   3. Nutrient thresholds      (per-nutrient out-of-range)
 *
 * Note: threshold reasons fire when threshold acts as a filter. Both
 * `filter` mode and `score` mode hide out-of-range items now, so
 * either mode produces threshold reasons.
 */

import { NUTRIENT_FIELDS, NUTRIENT_META } from '../data/schema.js';
import { DIETARY_RESTRICTIONS } from './restrictions.js';

export function inactiveReasons(ingredient, {
  ingredientFilter,
  thresholds,
  thresholdMode = 'filter',
  restrictions = [],
  ranges = null,
  // Phase 40 round 11: optional scale (per-serving toggle). When set,
  // ingredient values are multiplied by this factor before the
  // threshold comparison so the "outside range" message matches what
  // the user sees in the table / detail panel.
  nutrientScale = 1,
  nutrientUnit = '100g',
  // Batch 14: per-unit default-thresholds map. When supplied, nutrients
  // whose threshold equals the default are SKIPPED in the reasons list
  // — they aren't contributing to the filter (the filter pipeline
  // ignores at-default slots), so reporting "Fat above max 100g" for
  // a slot the user never touched is misleading.
  nutrientDefaults = null,
} = {}) {
  if (!ingredient) return [];
  const reasons = [];

  // 1. Manual checkbox exclusion in the ingredient filter tree.
  if (ingredientFilter && Array.isArray(ingredientFilter.excludedIds)
      && ingredientFilter.excludedIds.includes(ingredient.id)) {
    reasons.push('Hidden by the ingredient filter');
  }

  // 2. Dietary restrictions — list each restriction that matched and the
  //    `contains` tag(s) that triggered it.
  if (Array.isArray(restrictions) && restrictions.length > 0) {
    const contains = new Set(ingredient.contains || []);
    const triggered = [];
    for (const key of restrictions) {
      const r = DIETARY_RESTRICTIONS.find(d => d.key === key);
      if (!r) continue;
      const matched = r.excludes.filter(t => contains.has(t));
      if (matched.length > 0) {
        triggered.push(`${r.label} (contains ${matched.join(', ')})`);
      }
    }
    if (triggered.length > 0) {
      reasons.push(`Restricted by: ${triggered.join('; ')}`);
    }
  }

  // 3. Nutrient thresholds — both filter and score modes hide
  // out-of-range items, so either mode produces these reasons.
  if ((thresholdMode === 'filter' || thresholdMode === 'score') && thresholds) {
    const outside = [];
    const unitNote = nutrientUnit === 'serving' ? ' / serv' : '';
    for (const n of NUTRIENT_FIELDS) {
      const t = thresholds[n];
      if (!t) continue;
      // Batch 14: skip nutrients still at their default (slider bar
      // edge). Those aren't filtering; reporting them as "out of range"
      // confuses the user when they only moved a different nutrient.
      const d = nutrientDefaults && nutrientDefaults[n];
      if (d
          && Math.abs(t.min - d.min) < 1e-6
          && Math.abs(t.max - d.max) < 1e-6) {
        continue;
      }
      const rawV = ingredient[n];
      if (typeof rawV !== 'number') continue;
      const v = rawV * nutrientScale;
      if (v < t.min - 1e-9) {
        outside.push(`${NUTRIENT_META[n].label} ${fmt(v, n)}${unitNote} below min ${fmt(t.min, n)}`);
      } else if (v > t.max + 1e-9) {
        outside.push(`${NUTRIENT_META[n].label} ${fmt(v, n)}${unitNote} above max ${fmt(t.max, n)}`);
      }
    }
    if (outside.length > 0) {
      reasons.push(`Outside threshold range: ${outside.join('; ')}`);
    }
  }

  return reasons;
}

function fmt(v, nutrient) {
  if (v == null || !Number.isFinite(v)) return '—';
  const meta = NUTRIENT_META[nutrient];
  return meta ? meta.format(v) : String(v);
}
