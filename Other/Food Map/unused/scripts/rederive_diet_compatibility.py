#!/usr/bin/env python3
"""Re-derive `diet_compatibility` for every meal in the three meal files
using the (tightened) DIETS rules from src/data/schema.js.

Mirrors the JS code path:
  - excludedCategories: any overlap with the meal's ingredient_categories
    disqualifies the meal.
  - nutrientMin / nutrientMax: per-100g plate-aggregate thresholds the
    meal must satisfy. Plate-aggregate = gram-weighted mean of category
    densities (Σ cat[n] × cat.serving / Σ cat.serving × 100). Matches
    aggregateMeals() in src/core/aggregations.js — the same numbers the
    sphere is plotted at.

Run from project root:
    python scripts/rederive_diet_compatibility.py
"""

import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'src' / 'data'

# Mirror src/data/schema.js DIETS — keep in sync if schema.js changes.
DIETS = {
    'keto': {
        'excludedCategories': [
            'Whole grains', 'Refined grains', 'Bread & rolls', 'Pasta & noodles',
            'Baked snacks & pastries', 'Legumes', 'Soy products',
            'Starchy vegetables', 'Sugar & sweeteners', 'Candy & desserts',
            'Jams & preserves', 'Juices', 'Soft drinks',
            'Tropical fruits', 'Temperate fruits', 'Dried fruits',
            'Prepared mixes',
        ],
        'nutrientMax': {'carbs': 15, 'sugar': 8},
    },
    'paleo': {
        'excludedCategories': [
            'Whole grains', 'Refined grains', 'Bread & rolls', 'Pasta & noodles',
            'Baked snacks & pastries', 'Legumes', 'Soy products',
            'Milk', 'Yogurt', 'Aged cheese', 'Fresh cheese', 'Processed cheese',
            'Fermented dairy', 'Frozen dairy', 'Cream & butter',
            'Sugar & sweeteners', 'Candy & desserts', 'Jams & preserves',
            'Alcoholic beverages', 'Soft drinks', 'Prepared mixes',
            'Margarine & shortening',
            'Processed meat',
            'Noodle & rice alternatives',
        ],
    },
    'mediterranean': {
        'excludedCategories': [
            'Processed meat', 'Processed cheese',
            'Candy & desserts', 'Soft drinks',
            'Baked snacks & pastries', 'Margarine & shortening',
            'Prepared mixes',
        ],
    },
    'whole30': {
        'excludedCategories': [
            'Whole grains', 'Refined grains', 'Bread & rolls', 'Pasta & noodles',
            'Baked snacks & pastries', 'Legumes', 'Soy products',
            'Milk', 'Yogurt', 'Aged cheese', 'Fresh cheese', 'Processed cheese',
            'Fermented dairy', 'Frozen dairy', 'Cream & butter',
            'Sugar & sweeteners', 'Candy & desserts', 'Jams & preserves',
            'Alcoholic beverages', 'Soft drinks', 'Juices',
            'Prepared mixes', 'Processed meat',
            'Noodle & rice alternatives',
        ],
    },
    'lowfodmap': {
        'excludedCategories': [
            'Legumes', 'Soy products',
            'Milk', 'Yogurt',
            'Sugar & sweeteners', 'Jams & preserves',
            'Dried fruits',
        ],
    },
    'high_protein': {
        'nutrientMin': {'protein': 15},
    },
}
DIET_KEYS = list(DIETS.keys())

NUTRIENT_FIELDS = [
    'calories', 'carbs', 'protein', 'fiber', 'fat', 'sodium', 'sugar',
    'saturated_fat', 'iron',
]

# Mirror SERVING_GRAMS_BY_CATEGORY (subset used by aggregateByCategory).
# Pulled from src/data/schema.js. We need realistic serving grams per
# category so the plate-aggregate math agrees with the JS code.

SERVING_GRAMS_DEFAULT = 100


def load_ingredients():
    with (DATA / 'ingredients.json').open(encoding='utf-8') as f:
        return json.load(f)


def load_schema_servings():
    """Parse SERVING_GRAMS_BY_CATEGORY from schema.js as JSON-like text.
    Lightweight reader — the constant uses object-literal syntax we can
    coerce by extracting the braces and turning JS into JSON.
    """
    import re
    schema_text = (ROOT / 'src' / 'data' / 'schema.js').read_text(encoding='utf-8')
    # Extract the block `SERVING_GRAMS_BY_CATEGORY = { ... };`
    m = re.search(r'SERVING_GRAMS_BY_CATEGORY\s*=\s*(\{.*?\})\s*;', schema_text, re.DOTALL)
    if not m:
        return {}
    block = m.group(1)
    # Strip line/block comments
    block = re.sub(r'/\*.*?\*/', '', block, flags=re.DOTALL)
    block = re.sub(r'//[^\n]*', '', block)
    # Convert JS to JSON: 'key': value → "key": value
    block = re.sub(r"'([^']+)'", r'"\1"', block)
    # Trailing commas
    block = re.sub(r',(\s*[}\]])', r'\1', block)
    try:
        return json.loads(block)
    except Exception as e:
        print(f'WARN: failed to parse SERVING_GRAMS_BY_CATEGORY ({e}). Falling back to {{}}')
        return {}


def aggregate_categories(ingredients):
    """Equivalent to aggregateByCategory(ingredients, 'category') in JS:
    one record per category with per-100g nutrients = mean of members.
    """
    by_cat = defaultdict(list)
    for ing in ingredients:
        c = ing.get('category')
        if c:
            by_cat[c].append(ing)

    out = {}
    for cat, members in by_cat.items():
        agg = {'name': cat}
        n = len(members)
        for field in NUTRIENT_FIELDS:
            vals = [m.get(field) or 0 for m in members]
            agg[field] = sum(vals) / n if n else 0
        out[cat] = agg
    return out


def plate_mean_nutrients(meal_categories, cat_aggs, cat_servings):
    """Gram-weighted plate-aggregate nutrient profile for a category-shape
    meal. Categories are resolved via cat_aggs (Map by name); each
    contributes one serving (cat_servings[name] grams)."""
    cats = [cat_aggs[c] for c in meal_categories if c in cat_aggs]
    if not cats:
        return None
    plate_grams = sum(cat_servings.get(c['name'], SERVING_GRAMS_DEFAULT) for c in cats)
    if plate_grams <= 0:
        plate_grams = len(cats) * SERVING_GRAMS_DEFAULT
    out = {}
    for field in NUTRIENT_FIELDS:
        total = 0.0
        for c in cats:
            sg = cat_servings.get(c['name'], SERVING_GRAMS_DEFAULT)
            total += (c.get(field) or 0) * (sg / 100.0)
        out[field] = total / plate_grams * 100.0
    return out


def compatible_diets(meal_categories, plate_agg):
    """Return list of diet keys this meal passes, in DIETS-declaration order."""
    cat_set = set(meal_categories)
    result = []
    for key in DIET_KEYS:
        spec = DIETS[key]
        # excludedCategories
        excluded = spec.get('excludedCategories')
        if excluded:
            if cat_set & set(excluded):
                continue
        # nutrientMin
        nmin = spec.get('nutrientMin')
        if nmin:
            if plate_agg is None:
                continue
            ok = True
            for n, v in nmin.items():
                if not (plate_agg.get(n) is not None and plate_agg[n] >= v):
                    ok = False
                    break
            if not ok:
                continue
        # nutrientMax
        nmax = spec.get('nutrientMax')
        if nmax:
            if plate_agg is None:
                continue
            ok = True
            for n, v in nmax.items():
                if not (plate_agg.get(n) is not None and plate_agg[n] <= v):
                    ok = False
                    break
            if not ok:
                continue
        result.append(key)
    return result


def patch_file(path, cat_aggs, cat_servings, report):
    with path.open(encoding='utf-8') as f:
        meals = json.load(f)
    changed = 0
    for m in meals:
        cats = m.get('ingredient_categories') or []
        plate = plate_mean_nutrients(cats, cat_aggs, cat_servings)
        new_compat = compatible_diets(cats, plate)
        if new_compat != (m.get('diet_compatibility') or []):
            changed += 1
        m['diet_compatibility'] = new_compat
    with path.open('w', encoding='utf-8') as f:
        json.dump(meals, f, ensure_ascii=False, indent=2)
        f.write('\n')
    report[path.name] = (len(meals), changed)
    # Tally
    counts = defaultdict(int)
    for m in meals:
        for d in m.get('diet_compatibility', []):
            counts[d] += 1
    return counts


def main():
    ingredients = load_ingredients()
    cat_servings = load_schema_servings()
    print(f'Loaded {len(ingredients)} ingredients, {len(cat_servings)} category servings.')

    cat_aggs = aggregate_categories(ingredients)
    print(f'Built {len(cat_aggs)} category aggregates.')

    report = {}
    print()
    print('Re-deriving diet_compatibility...')
    for fname in ['meals.json', 'compositional-meals.json', 'corpus-titled-meals.json']:
        path = DATA / fname
        counts = patch_file(path, cat_aggs, cat_servings, report)
        total, changed = report[fname]
        print(f'\n{fname}: {total} meals, {changed} changed compat array')
        for d in DIET_KEYS:
            print(f'   {d:>15s}: {counts.get(d, 0):>5d} meals')


if __name__ == '__main__':
    main()
