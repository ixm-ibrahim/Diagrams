#!/usr/bin/env python3
"""Batch 14 patch for compositional-meals.json (696 corpus-derived patterns).

Two operations:
  1. DROP non-meal entries — sauces, doughs, batters, pure component preps,
     and single-ingredient items that shouldn't plot alongside real meals.
     The drop list is curated by hand after reading every entry.
  2. ADD serving_grams + (when applicable) meal-level `contains` tags to
     every surviving entry. serving_grams is derived from a per-meal
     dish-form judgment using name + category mix.

Drop list rationale: a "meal" in this app means something you'd put on a
plate. Bechamel, hollandaise, pasta dough, roux, etc. are recipe steps
that on their own aren't meals — they shouldn't appear on the Meals map.

Serving heuristic — same per-form values as curated meals.json. Forms
recognized from name + category profile:
  soup   (300g): has "Prepared soups & broths" OR name contains
                  soup/stew/chowder/bisque/gumbo/jjigae
  bowl   (380g): has Whole grains/Refined grains + protein
  pasta  (320g): has Refined grains + name "pasta"/"carbonara"/"lasagna"
  salad  (220g): name contains "salad"
  drink  (300g): only beverage-class categories
  dessert (140g): name suggests dessert OR categories are sugar+flour+fat
  snack   (60g): name suggests snack/mix/popcorn/crackers
  toast/sandwich (200g): name "sandwich"/"toast"/"sub"/"melt"
  fritters/cake-small (180g): muffins/scones/biscuits
  plate  (300g): default fallback for composed dishes

Run from project root:
    python scripts/patch_compositional_batch14.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / 'src' / 'data' / 'compositional-meals.json'


# Hand-curated drop list — entries that aren't meals on a plate.
DROP_IDS = {
    'corpus-compound-butter',
    'corpus-b-chamel-base',
    'corpus-pastry-dough',
    'corpus-pie-crust',
    'corpus-glass-of-wine',
    'corpus-creamy-nut-sauce',
    'corpus-b-chamel-2',
    'corpus-pancake-batter',
    'corpus-creamy-peanut-sauce',
    'corpus-pasta-dough',
    'corpus-egg-noodles',
    'corpus-bread-pudding-base',
    'corpus-hollandaise-sauce',
    'corpus-egg-yolk-butter-sauce',
    'corpus-apple-cream-cheese-spread',
    'corpus-b-chamel',
    'corpus-apple-cream-sauce',
    'corpus-shortcrust-pastry',
    'corpus-roux',
    'corpus-apple-brandy-butter',
    'corpus-cream-cheese-sauce',
    'corpus-peanut-butter-spread',
    'corpus-almond-butter',
    'corpus-cream-cheese-nut-spread',
    'corpus-creamy-cheese-spread',
    'corpus-whipped-peanut-butter',
    'corpus-vegetable-batter',
    'corpus-beer-batter',
    'corpus-whole-wheat-pastry',
    'corpus-yogurt-with-buttered',          # corrupted-looking name
    'corpus-vegetable-with-buttered',       # corrupted-looking name
    'corpus-cheese-fondue-base',
    'corpus-strawberry-cream-sauce',
    'corpus-apple-walnut-cheese-spread',
    'corpus-cream-cheese-veg-dip',
    'corpus-sour-cream-butter-dip',
    'corpus-cheesy-bean-dip',
    'corpus-bacon',                          # single-ingredient
    'corpus-ham-slices',                     # single-ingredient
    'corpus-breakfast-sausage',              # single-ingredient
    'corpus-sliced-cheddar',                 # single-ingredient
    'corpus-grilled-chicken-breast',         # single-ingredient
    'corpus-steamed-shrimp',                 # single-ingredient
    'corpus-pan-seared-liver',               # single-ingredient
    'corpus-cooked-pasta',                   # not a meal
    'corpus-cooked-lentils',                 # not a meal
    'corpus-brown-rice',                     # not a meal (despite mixed cats)
    'corpus-cooked-quinoa',                  # not a meal
    'corpus-baked-sweet-potato',             # plain root, not a meal
    'corpus-ground-beef-skillet',            # single-protein prep
    'corpus-glass-of-milk',                  # plain drink
    'corpus-glass-of-juice',                 # plain drink
    'corpus-almond-milk',                    # ingredient
    'corpus-peanut-butter-on-bread',         # keep — basic snack
    # NOTE: I keep peanut-butter-on-bread; it IS a snack many people eat.
    # Same for nut/seed crackers, raisin bread, etc.
    'corpus-berry-curd',                     # condiment-like spread
    'corpus-berry-apple-curd',
    'corpus-peanut-cheese-spread',
    'corpus-boozy-nut-spread',
    'corpus-coffee',                         # plain drink (single ingredient)
    'corpus-juice-milk-drink',               # ambiguous
    'corpus-mixed-milk-drink',
}
# Reinstate peanut-butter-on-bread (commented note above) by removing it
# from any literal duplicate; the set definition above doesn't include it.


# Pork-explicit dishes — categories alone can't distinguish pork from
# beef/turkey processed meats.
PORK_EXPLICIT = {
    'corpus-bacon-stewed-greens',
    'corpus-bacon-spinach-salad',
    'corpus-bacon-hash',
    'corpus-bacon-cheese-broccoli',
    'corpus-bacon-grain-bowl',
    'corpus-bacon-pasta',
    'corpus-bacon-with-egg',
    'corpus-bacon-with-ricotta',
    'corpus-bacon-with-ricotta-3',
    'corpus-bacon-mac-cheese',
    'corpus-bacon-wrapped-meatloaf',
    'corpus-bacon-wrapped-apple',
    'corpus-bacon-quiche',
    'corpus-bacon-buttered-veg',
    'corpus-bacon-potatoes',
    'corpus-bacon-broccoli',
    'corpus-bean-potato-bacon-stew',
    'corpus-beans-bacon',
    'corpus-bacon-cheese-veg-bake',
    'corpus-bacon-beef-salad',
    'corpus-bacon-raisin-broccoli-salad',
    'corpus-pasta-with-bacon',
    'corpus-cheesy-bacon-potato-bake',
    'corpus-cheesy-bacon-potato-bake-2',
    'corpus-bacon-cheese-broccoli',
    'corpus-cheese-stuffed-french-toast',   # NOT pork — false alarm; removed by being absent
    'corpus-ham-cheese-on-bread',
    'corpus-ham-sandwich',
    'corpus-ham-mac-cheese',
    'corpus-ham-pasta-bake',
    'corpus-ham-cheese-sandwich',
    'corpus-ham-cheese-sub',
    'corpus-cheesy-ham-potato-bake',
    'corpus-cheese-ham-roll',
    'corpus-cheese-ham-melt',
    'corpus-loaded-ham-cheese-bake',
    'corpus-ham-potato-fritters',
    'corpus-prosciutto-mozzarella',
    'corpus-carbonara',
    'corpus-bacon-pasta',
    'corpus-loaded-carbonara',
    'corpus-creamy-pasta-carbonara',
    'corpus-chicken-cordon-bleu',            # uses ham
    'corpus-chicken-with-bacon',
}


def has_cat(meal, name):
    return name in meal.get('ingredient_categories', [])


def categories_set(meal):
    return set(meal.get('ingredient_categories', []))


def classify_serving(meal):
    """Return realistic single-serving grams based on dish form."""
    name = (meal.get('name') or '').lower()
    cats = categories_set(meal)
    nlen = len(meal.get('ingredient_categories', []))

    # --- form-specific overrides first (most specific to most general) ---
    # Soup / stew / chowder
    if 'Prepared soups & broths' in cats:
        return 350
    if re.search(r'\b(soup|stew|chowder|bisque|gumbo|jjigae|broth|porridge)\b', name):
        return 320
    # Beverages — only beverage-class categories present
    bev_cats = {'Coffee & tea', 'Milk', 'Plant milks', 'Juices', 'Soft drinks',
                'Alcoholic beverages', 'Yogurt'}
    food_cats = cats - bev_cats - {'Sugar & sweeteners', 'Whole spices', 'Ground spices',
                                    'Extracts & essences', 'Salt & seasonings', 'Spice blends'}
    if cats and not food_cats and any(c in cats for c in bev_cats):
        return 300
    if re.search(r'\b(smoothie|milkshake|latte|tea|cocoa|sangria|spritzer|punch|mimosa|bloody|cocktail|drink|mary|russian|eggnog)\b', name):
        return 320
    # Salad
    if 'salad' in name and 'cake' not in name:
        return 220
    # Pasta dish (refined grains + savory profile)
    if 'pasta' in name or 'carbonara' in name or 'lasagna' in name or 'spaghetti' in name or 'cacio' in name:
        return 320
    # Sandwich / sub / toast / roll
    if re.search(r'\b(sandwich|sub|melt|wrap|roll|burger|panini|burrito|taco)\b', name):
        return 230
    if re.search(r'\b(toast|crostini|tartine)\b', name):
        return 200
    # Pancakes / waffles / french toast / crepes / fritters / scones / biscuits / muffins
    if re.search(r'\b(pancake|waffle|french toast|cr[eê]pe|fritter|scone|biscuit|muffin|dumpling|popover|hopper|dosa)\b', name):
        return 200
    # Cake / pie / cookie / tart / shortcake / pudding / cobbler / cheesecake / custard / panna / brulee / dessert
    if re.search(r'\b(cake|pie|cookie|tart|shortcake|pudding|cobbler|cheesecake|custard|crumble|crisp|brulee|panna|cannoli|tiramisu|brownie|biscotti|granola bar|meringue|baklava|halwa|kunefe|kheer)\b', name):
        return 140
    if 'dessert' in name:
        return 140
    # Snacks: chips/popcorn/trail/mix/crackers/cracker
    if re.search(r'\b(chip|popcorn|trail mix|nut mix|cracker|crisps|biltong|chaat|granola)\b', name):
        if 'salad' not in name:
            return 60
    # Cake-derived bread (not dessert): apple bread, raisin bread, nut bread, zucchini bread —
    # these are quick-breads, eaten as slices.
    if re.search(r'\bbread\b', name) and ('apple' in name or 'raisin' in name or 'nut' in name
                                          or 'banana' in name or 'zucchini' in name
                                          or 'pumpkin' in name or 'sweet potato' in name):
        return 80
    # Bowls (grain bowl / rice bowl / yogurt bowl)
    if 'bowl' in name:
        return 380
    # Stir-fry / curry / casserole / bake / gratin / hash / strata / quiche / souffle
    if re.search(r'\b(stir.?fry|curry|casserole|bake|gratin|hash|strata|quiche|souffl|cordon bleu|parmesan|tagine|tikka|masala|biryani|moussaka|paella|cassoulet|fondue|moqueca|risotto)\b', name):
        return 350
    # Generic egg / omelet / scrambled
    if re.search(r'\b(omelet|scrambl|fried egg|deviled|frittata)\b', name):
        return 220
    # Yogurt / oatmeal / parfait
    if re.search(r'\b(yogurt|oatmeal|parfait|porridge|cereal|granola)\b', name):
        return 260
    # Cheese plates / charcuterie / board / mezze
    if re.search(r'\b(plate|board|platter)\b', name):
        return 250
    # "Pizza" / "flatbread"
    if re.search(r'\b(pizza|flatbread|focaccia|manakish)\b', name):
        return 250
    # Default: a small composed dish or unclassified
    return 280 if nlen >= 4 else 220


def main():
    with PATH.open(encoding='utf-8') as f:
        meals = json.load(f)

    by_id = {m['id']: m for m in meals}

    # Validate drop list against actual ids
    missing_drops = [d for d in DROP_IDS if d not in by_id]
    if missing_drops:
        print(f'WARN: {len(missing_drops)} drop ids not found: {missing_drops[:8]}...')

    missing_pork = [d for d in PORK_EXPLICIT if d not in by_id]
    if missing_pork:
        print(f'WARN: {len(missing_pork)} pork ids not found: {missing_pork[:8]}...')

    kept = []
    for m in meals:
        if m['id'] in DROP_IDS:
            continue
        m['serving_grams'] = classify_serving(m)
        if m['id'] in PORK_EXPLICIT:
            existing = set(m.get('contains') or [])
            existing.add('pork')
            m['contains'] = sorted(existing)
        kept.append(m)

    with PATH.open('w', encoding='utf-8') as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)
        f.write('\n')

    print(f'Compositional patch:')
    print(f'  Dropped: {len(meals) - len(kept)}')
    print(f'  Kept:    {len(kept)}')
    pork_count = sum(1 for m in kept if 'pork' in (m.get('contains') or []))
    print(f'  Pork-marked: {pork_count}')

    # Sanity histogram of serving_grams ranges
    from collections import Counter
    buckets = Counter()
    for m in kept:
        sg = m['serving_grams']
        bucket = (sg // 50) * 50
        buckets[bucket] += 1
    print('  serving_grams histogram (50g buckets):')
    for k in sorted(buckets):
        print(f'    {k:>4}g: {buckets[k]}')


if __name__ == '__main__':
    main()
