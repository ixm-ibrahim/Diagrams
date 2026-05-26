#!/usr/bin/env python3
"""Batch 14 patch for corpus-titled-meals.json (2,659 corpus dishes).

Operations:
  1. DROP entries that are condiments / sauces / dressings / dough / frosting
     etc. by name pattern, with manual rescues for false-positive matches
     (e.g. "Spaghetti With Meat Sauce" — a real meal — survives).
  2. ADD serving_grams via the same dish-form classifier as the
     compositional file.
  3. ADD `contains: ['pork']` for dishes whose names imply mandatory pork
     (bacon/ham/sausage/prosciutto/pancetta/chorizo by name + context).

Run from project root:
    python scripts/patch_corpus_titled_batch14.py
"""

import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'


# A dish that ENDS with one of these words is a condiment/sauce/component.
TAIL_PAT = re.compile(
    r'\b(sauce|dressing|relish|chutney|aioli|ketchup|jam|jelly|preserve|'
    r'syrup|spread|paste|frosting|icing|gravy|marinade|brine|dough|batter|'
    r'seasoning|stuffing|filling|crust|fondant|glaze|tapenade|pickling|'
    r'rub|brittle)\s*$',
    re.IGNORECASE,
)

# If any of these words appear ANYWHERE in the name, the dish is a real
# meal even though the tail matches. ("Spaghetti With Meat Sauce" stays.)
MEAL_OK = re.compile(
    r'\b(chicken|beef|pork|lamb|turkey|fish|shrimp|salmon|tuna|crab|lobster|'
    r'oyster|clam|mussel|squid|octopus|bean|lentil|tofu|chickpea|tempeh|seitan|'
    r'veggie|vegetable|veg|cake|cookie|pie|bread|muffin|tart|pancake|roll|'
    r'biscuit|scone|brownie|cupcake|salad|soup|stew|chili|curry|casserole|'
    r'bake|gratin|hash|pizza|pasta|risotto|burger|sandwich|wrap|sub|melt|'
    r'burrito|taco|fajita|enchilada|quesadilla|tamale|empanada|dumpling|'
    r'ravioli|noodle|rice|grain|bowl|fritter|crepe|frittata|omelet|quiche|'
    r'spaghetti|meatball|steak|chop|wing|leg|breast|drumstick|loaf|patty|'
    r'cutlet|kebab|skewer|nugget|tender|jerky|nachos|po.boy|gnocchi|'
    r'lasagna|cannelloni|manicotti|paella|jambalaya|stir.?fry|'
    r'shawarma|gyro|kabob|stroganoff|wellington|cordon|parmigiana|tagine|'
    r'sausage stuffing|spaghetti.+meat|meat sauce.+(spaghetti|pasta|noodle))\b',
    re.IGNORECASE,
)

# Bare single-word condiments — drop unconditionally
BARE_DROP = {
    'salsa', 'hummus', 'dressing', 'mayonnaise', 'mayo', 'pesto',
    'stuffing', 'frosting', 'icing', 'gravy', 'syrup', 'marinade',
    'ketchup', 'aioli', 'relish', 'tapenade', 'sauce', 'jam', 'jelly',
    'chutney', 'filling', 'dough', 'batter', 'brine', 'glaze',
    'seasoning', 'garnish', 'spread', 'butter', 'play dough', 'rub',
    'crust',
}

# Forced manual drops (names where the heuristic was too lenient)
EXTRA_DROPS_NAMES = {
    'play dough', 'pizza dough', 'pizza crust', 'pie crust',
    'flaky pie crust', 'foolproof pie crust', 'fried pie crust',
    'never fail pie crust', 'basic pizza dough', 'tart shell',
    'phyllo dough', 'cookie dough', 'bread dough',
    'apple butter', 'pumpkin butter', 'peach butter', 'pear butter',
    'butter (compound)', 'compound butter', 'cinnamon sugar',
    'taco seasoning', 'taco rub', 'spice rub', 'rub',
    'royal icing', 'fondant', 'meringue',  # standalone meringue is a component
    'simple syrup', 'caramel', 'praline',
    'whipped cream', 'whipped butter', 'whipped topping',
    'butter brittle', 'peanut brittle',  # candy components
    'bolognese sauce',  # without pasta it's a sauce
    'meat sauce',
    'pesto sauce',
    'tomato gravy',
    'hot sauce', 'bbq sauce',
}

# Manual rescues — items that match the TAIL pattern but should NOT drop
RESCUE_NAMES = {
    'chicken and dressing',          # Southern stuffing-with-chicken
    'chicken and dressing casserole',
    'cornbread dressing',            # Southern thanksgiving side — meal-ish
    'sausage stuffing',              # thanksgiving side
    'cornbread stuffing',
    'oyster stuffing',
    'apple stuffing',
    'mushroom stuffing',
    'bread stuffing',
    'rice stuffing',
    'spaghetti with meat sauce',
    'steak and gravy',
    'chicken and gravy',
    'biscuits and gravy',
}


def name_norm(s):
    return (s or '').strip().lower()


def has_cat(meal, name):
    return name in meal.get('ingredient_categories', [])


def categories_set(meal):
    return set(meal.get('ingredient_categories', []))


def classify_serving(meal):
    """Same form-based classifier as compositional patch."""
    name = (meal.get('name') or '').lower()
    cats = categories_set(meal)
    nlen = len(meal.get('ingredient_categories', []))

    if 'Prepared soups & broths' in cats:
        return 350
    if re.search(r'\b(soup|stew|chowder|bisque|gumbo|jjigae|broth|porridge|chili)\b', name):
        return 320
    bev_cats = {'Coffee & tea', 'Milk', 'Plant milks', 'Juices', 'Soft drinks',
                'Alcoholic beverages', 'Yogurt'}
    food_cats = cats - bev_cats - {
        'Sugar & sweeteners', 'Whole spices', 'Ground spices',
        'Extracts & essences', 'Salt & seasonings', 'Spice blends',
    }
    if cats and not food_cats and any(c in cats for c in bev_cats):
        return 300
    if re.search(r'\b(smoothie|milkshake|latte|tea$|cocoa|sangria|spritzer|punch|mimosa|bloody|cocktail|drink|toddy|eggnog|chai|lemonade|lassi|horchata|frapp)\b', name):
        return 320
    if 'salad' in name and 'cake' not in name and 'salad dressing' not in name:
        return 230
    if re.search(r'\b(pasta|carbonara|lasagna|spaghetti|cacio|fettuccine|linguine|penne|rigatoni|gnocchi|ravioli|tortellini|cannelloni|manicotti|ziti|orzo|noodle|alfredo|primavera|stroganoff)\b', name):
        return 320
    if re.search(r'\b(sandwich|sub|melt|wrap|roll up|burger|panini|burrito|taco|fajita|enchilada|quesadilla|hoagie|po.boy|gyro|shawarma)\b', name):
        return 240
    if re.search(r'\b(toast|crostini|tartine|bruschetta)\b', name):
        return 200
    if re.search(r'\b(pancake|waffle|french toast|cr[eê]pe|fritter|scone|biscuit|muffin|popover|hopper|dosa|hotcake|johnny.?cake)\b', name):
        return 180
    if re.search(r'\b(cake|pie|cookie|tart|shortcake|pudding|cobbler|cheesecake|custard|crumble|crisp|brulee|panna|cannoli|tiramisu|brownie|biscotti|baklava|halwa|kunefe|kheer|trifle|profiterole|eclair|macaron|gulab|barfi)\b', name):
        return 140
    if 'dessert' in name or 'parfait' in name:
        return 160
    if re.search(r'\b(chip|popcorn|trail mix|nut mix|cracker|crisps|jerky|biltong|granola bar|snack mix|cheese ball|pretzel|popcorn balls)\b', name) and 'salad' not in name:
        return 60
    if re.search(r'\bbread\b', name) and any(w in name for w in ['apple','raisin','nut','banana','zucchini','pumpkin','sweet potato','date','cranberry','poppy','blueberry','strawberry','lemon','orange','cornbread','spice']):
        return 90
    if 'bowl' in name:
        return 380
    if re.search(r'\b(stir.?fry|curry|casserole|bake|gratin|hash|strata|quiche|souffl|cordon bleu|parmesan|parmigiana|tagine|tikka|masala|biryani|moussaka|paella|cassoulet|fondue|risotto|jambalaya|gumbo|stroganoff|wellington)\b', name):
        return 360
    if re.search(r'\b(omelet|scrambl|fried egg|deviled|frittata|huevos|shakshuka)\b', name):
        return 230
    if re.search(r'\b(yogurt|oatmeal|porridge|cereal|granola|muesli)\b', name) and 'cake' not in name and 'cookie' not in name:
        return 260
    if re.search(r'\b(plate|board|platter|charcuterie|mezze)\b', name):
        return 250
    if re.search(r'\b(pizza|flatbread|focaccia|manakish|calzone|stromboli)\b', name):
        return 260
    if re.search(r'\b(roast|grilled|baked|fried|seared|braised) (chicken|beef|pork|lamb|turkey|fish|salmon|duck|veg|chops|steak|whole|leg|breast|thigh|wing|cutlet)\b', name):
        return 330
    if re.search(r'\b(meatball|meatloaf|patty|cutlet|nugget|tender|wing|drumstick|chops|skewer|kebab|kabob)\b', name):
        return 280
    if re.search(r'\bdumpling|spring roll|samosa|empanada|wonton|tamale|ravioli\b', name):
        return 230
    return 320 if nlen >= 6 else 260


def main():
    with PATH.open(encoding='utf-8') as f:
        meals = json.load(f)

    # Build drop set
    drops = set()
    for m in meals:
        n = m.get('name', '')
        nl = name_norm(n)
        # Bare condiment names
        if nl in BARE_DROP:
            drops.add(m['id']); continue
        if nl in EXTRA_DROPS_NAMES:
            drops.add(m['id']); continue
        # Tail-pattern with no main-meal rescue
        if TAIL_PAT.search(n):
            if nl in RESCUE_NAMES:
                continue
            if MEAL_OK.search(n):
                continue
            drops.add(m['id'])

    # Pork-mandatory detection.
    # We mark `contains: ['pork']` if name explicitly names a pork-derived
    # ingredient. False positives are minimal because the meal IS the
    # pork (Bacon Quiche, Ham & Cheese, Pork Chops...).
    PORK_NAME = re.compile(
        r'\b(bacon|ham|prosciutto|pancetta|guanciale|chorizo|salami|'
        r'pepperoni|capicola|mortadella|bratwurst|kielbasa|'
        r'pork(?!\s*and\s*beans)|carnitas|al pastor|jamon|'
        r'lardon|nduja|spam|breakfast sausage|italian sausage|andouille)\b',
        re.IGNORECASE,
    )
    pork_marked = 0

    kept = []
    for m in meals:
        if m['id'] in drops:
            continue
        m['serving_grams'] = classify_serving(m)
        name = m.get('name', '')
        if PORK_NAME.search(name):
            existing = set(m.get('contains') or [])
            existing.add('pork')
            m['contains'] = sorted(existing)
            pork_marked += 1
        kept.append(m)

    with PATH.open('w', encoding='utf-8') as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)
        f.write('\n')

    print(f'Corpus-titled patch:')
    print(f'  Original: {len(meals)}')
    print(f'  Dropped:  {len(drops)}')
    print(f'  Kept:     {len(kept)}')
    print(f'  Pork-marked: {pork_marked}')
    print()
    buckets = Counter()
    for m in kept:
        buckets[(m['serving_grams'] // 50) * 50] += 1
    print('serving_grams histogram (50g buckets):')
    for k in sorted(buckets):
        print(f'  {k:>4}g: {buckets[k]}')


if __name__ == '__main__':
    main()
