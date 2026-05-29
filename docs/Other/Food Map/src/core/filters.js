/* Centralized filter logic.
 *
 * Phase 6: ingredient filter.
 *   shape: { excludedIds: string[] }
 *   A ingredient is "active" iff its id is NOT in excludedIds.
 *   Empty excludedIds = no filter applied = every ingredient is active.
 *
 * Phase 7 will add nutrient thresholds; composition will live here too —
 * a ingredient must pass every filter to be active.
 */

export function createEmptyFilter() {
  return { excludedIds: [] };
}

export function isExcluded(ingredientId, ingredientFilter) {
  if (!ingredientFilter || !Array.isArray(ingredientFilter.excludedIds)) return false;
  return ingredientFilter.excludedIds.includes(ingredientId);
}

/**
 * Return the set of active ingredient ids given the filter and the ingredient list.
 * O(n + m) where n=ingredients, m=excluded set size.
 */
export function computeActiveSet(ingredients, ingredientFilter) {
  const excluded = new Set(ingredientFilter?.excludedIds || []);
  const active = new Set();
  for (const f of ingredients) {
    if (!excluded.has(f.id)) active.add(f.id);
  }
  return active;
}

export function activeCount(ingredients, ingredientFilter) {
  const excluded = new Set(ingredientFilter?.excludedIds || []);
  let count = 0;
  for (const f of ingredients) if (!excluded.has(f.id)) count++;
  return count;
}

/**
 * Whether the filter is in its "no exclusions" baseline state. Useful so
 * scene reactions can skip the work entirely when nothing's filtered.
 */
export function isFilterEmpty(ingredientFilter) {
  return !ingredientFilter
      || !Array.isArray(ingredientFilter.excludedIds)
      || ingredientFilter.excludedIds.length === 0;
}

/**
 * Add the given ids to the excluded set (no-op for ids already excluded).
 * Returns a new filter object so subscribers see a fresh reference.
 */
export function excludeIds(ingredientFilter, ids) {
  const excluded = new Set(ingredientFilter?.excludedIds || []);
  for (const id of ids) excluded.add(id);
  return { ...(ingredientFilter || {}), excludedIds: [...excluded] };
}

/**
 * Remove the given ids from the excluded set (no-op for ids not present).
 */
export function includeIds(ingredientFilter, ids) {
  const removeSet = new Set(ids);
  const next = (ingredientFilter?.excludedIds || []).filter(id => !removeSet.has(id));
  return { ...(ingredientFilter || {}), excludedIds: next };
}

/* ---- Phase 26: tag filter --------------------------------------------------
 *
 * Tag filter shape: a string[] of selected tag names.
 *   Empty array (or undefined) = no filter applied.
 *   Non-empty = OR semantic: an ingredient is active iff it carries ANY
 *   of the selected tags in its `tags` field.
 *
 * Composition with other filters happens in main.js (intersected with the
 * ingredient-tree active set, dietary restrictions, and thresholds).
 */

export function isTagFilterEmpty(tagFilter) {
  return !Array.isArray(tagFilter) || tagFilter.length === 0;
}

export function tagActiveSet(ingredients, tagFilter, mode = 'any') {
  if (isTagFilterEmpty(tagFilter)) return null;
  const selected = new Set(tagFilter);
  const out = new Set();
  if (mode === 'all') {
    // Phase 40 round 6: ALL semantic — ingredient must carry every
    // selected tag.
    for (const ing of ingredients) {
      const tags = new Set(ing.tags || []);
      let ok = true;
      for (const t of selected) {
        if (!tags.has(t)) { ok = false; break; }
      }
      if (ok) out.add(ing.id);
    }
    return out;
  }
  for (const ing of ingredients) {
    const tags = ing.tags || [];
    for (const t of tags) {
      if (selected.has(t)) { out.add(ing.id); break; }
    }
  }
  return out;
}
