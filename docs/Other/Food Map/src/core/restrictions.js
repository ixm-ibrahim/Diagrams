/* Phase 13.5: dietary restriction definitions.
 *
 * Each restriction maps to a set of `contains` tags. An ingredient is
 * hidden if ANY active restriction's tag set intersects with the
 * ingredient's `contains` array. Restrictions compose by union — picking
 * Vegan + Gluten-free hides everything either one would hide.
 *
 * Group structure is for UI rendering only (dietary patterns vs allergies
 * vs religious). The filter logic doesn't care which group a restriction
 * is in.
 */

/* Phase 14: `caffeine` tag added to the vocabulary alongside the
 * "Caffeine-free" restriction. Carried by coffee, tea, cola, energy drinks,
 * and cocoa-derived products. */
export const CONTAINS_TAGS = [
  'meat', 'fish', 'shellfish', 'pork', 'dairy', 'eggs', 'gluten',
  'tree_nut', 'peanut', 'soy', 'sesame', 'alcohol', 'honey',
  'animal_byproduct', 'caffeine',
];

export const DIETARY_RESTRICTIONS = [
  // Lifestyle / pattern
  { key: 'vegetarian',   label: 'Vegetarian',       group: 'Diet',     excludes: ['meat', 'fish', 'shellfish', 'animal_byproduct'] },
  { key: 'vegan',        label: 'Vegan',            group: 'Diet',     excludes: ['meat', 'fish', 'shellfish', 'animal_byproduct', 'dairy', 'eggs', 'honey'] },
  { key: 'pescatarian',  label: 'Pescatarian',      group: 'Diet',     excludes: ['meat', 'animal_byproduct'] },
  // Religious
  { key: 'halal',        label: 'Halal',            group: 'Religious', excludes: ['pork', 'alcohol'] },
  { key: 'kosher',       label: 'Kosher',           group: 'Religious', excludes: ['pork', 'shellfish'] },
  // Allergies / intolerances
  { key: 'gluten_free',  label: 'Gluten-free',      group: 'Allergy',  excludes: ['gluten'] },
  { key: 'dairy_free',   label: 'Dairy-free',       group: 'Allergy',  excludes: ['dairy'] },
  { key: 'tree_nut_free',label: 'Tree-nut allergy', group: 'Allergy',  excludes: ['tree_nut'] },
  { key: 'peanut_free',  label: 'Peanut allergy',   group: 'Allergy',  excludes: ['peanut'] },
  { key: 'egg_free',     label: 'Egg allergy',      group: 'Allergy',  excludes: ['eggs'] },
  { key: 'soy_free',     label: 'Soy allergy',      group: 'Allergy',  excludes: ['soy'] },
  { key: 'shellfish_free', label: 'Shellfish allergy', group: 'Allergy', excludes: ['shellfish'] },
  { key: 'fish_free',    label: 'Fish allergy',     group: 'Allergy',  excludes: ['fish'] },
  { key: 'sesame_free',  label: 'Sesame allergy',   group: 'Allergy',  excludes: ['sesame'] },
  // Sensitivities
  { key: 'caffeine_free',label: 'Caffeine-free',    group: 'Sensitivity', excludes: ['caffeine'] },
];

const BY_KEY = new Map(DIETARY_RESTRICTIONS.map(r => [r.key, r]));

/* Given the list of active restriction keys, return the union of tags
 * that should hide an ingredient. */
export function excludedTagsFor(activeKeys) {
  const out = new Set();
  for (const key of activeKeys || []) {
    const r = BY_KEY.get(key);
    if (!r) continue;
    for (const t of r.excludes) out.add(t);
  }
  return out;
}

/* Predicate: would the active restrictions hide this ingredient? */
export function isRestricted(ingredient, excludedTags) {
  if (!excludedTags || excludedTags.size === 0) return false;
  const contains = ingredient.contains || [];
  for (const t of contains) if (excludedTags.has(t)) return true;
  return false;
}

/* Given the active restriction keys and the ingredient list, return the
 * set of ingredient ids that pass (i.e., are NOT restricted). Returns null
 * when there are no active restrictions, signaling "no filter". */
export function passingIngredientIds(ingredients, activeKeys) {
  const tags = excludedTagsFor(activeKeys);
  if (tags.size === 0) return null;
  const out = new Set();
  for (const ing of ingredients) {
    if (!isRestricted(ing, tags)) out.add(ing.id);
  }
  return out;
}

/* Group restrictions by their `group` field for grouped UI rendering. */
export function groupedRestrictions() {
  const groups = new Map();
  for (const r of DIETARY_RESTRICTIONS) {
    if (!groups.has(r.group)) groups.set(r.group, []);
    groups.get(r.group).push(r);
  }
  return [...groups.entries()].map(([group, items]) => ({ group, items }));
}
