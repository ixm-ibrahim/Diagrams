#!/usr/bin/env python3
"""Append a curated batch of low-carb / low-cal / high-protein meals to
meals.json. diet_compatibility is left empty here and (re)derived by
rederive_diet_compatibility.py afterward. Run once.

Preserves meals.json formatting (indent=2, ensure_ascii=False, trailing
newline). Validates that every listed ingredient_category is covered by an
example ingredient of that category, and that all ids resolve, before writing.
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

DATA = Path(__file__).resolve().parent.parent.parent / 'src' / 'data'
ings = json.load((DATA / 'ingredients.json').open(encoding='utf-8'))
cat_of = {i['id']: i['category'] for i in ings}

SKIP = {'Extracts & essences', 'Pastes & ferments', 'Pickled vegetables'}

FIELD_ORDER = ['id', 'name', 'ingredient_categories', 'example_ingredients', 'notes',
               'cuisine', 'diet_compatibility', 'frequency', 'source', 'tags', 'serving_grams']


def meal(id, name, cats, examples, notes, cuisine, tags, serving):
    return {
        'id': id, 'name': name, 'ingredient_categories': cats,
        'example_ingredients': examples, 'notes': notes, 'cuisine': cuisine,
        'diet_compatibility': [], 'frequency': 1, 'source': 'curated',
        'tags': tags, 'serving_grams': serving,
    }


NOODLE = 'Noodle & rice alternatives'
M = [
    meal('shirataki-chicken-ramen', 'Shirataki chicken ramen',
         [NOODLE, 'Poultry', 'Eggs', 'Prepared soups & broths', 'Other vegetables'],
         ['shirataki', 'chicken-breast', 'egg-whole', 'chicken-broth', 'scallion'],
         'Konjac shirataki noodles in a savory chicken broth with sliced poached chicken, a soft egg, and scallions — a full ramen bowl at a fraction of the carbs.',
         'Japanese', ['lunch', 'dinner'], 450),
    meal('shirataki-pad-thai', 'Shirataki pad thai',
         [NOODLE, 'Eggs', 'Shellfish', 'Other vegetables', 'Sauces'],
         ['tofu-shirataki', 'egg-whole', 'shrimp', 'scallion', 'fish-sauce'],
         'Tofu shirataki noodles tossed with shrimp, egg, and scallion in a tangy fish-sauce dressing — the pad thai experience without the rice-noodle carb load.',
         'Thai', ['lunch', 'dinner'], 380),
    meal('egg-drop-soup', 'Egg drop soup',
         ['Eggs', 'Prepared soups & broths', 'Other vegetables'],
         ['egg-whole', 'chicken-broth', 'scallion'],
         'Silky ribbons of egg swirled into hot chicken broth with scallion — a light, warming, near-zero-carb starter.',
         'Chinese', ['lunch'], 350),
    meal('tuna-lettuce-wraps', 'Tuna salad lettuce wraps',
         ['Oily fish', 'Leafy greens', 'Dressings & dips'],
         ['tuna', 'iceberg-lettuce', 'mayonnaise'],
         'Creamy tuna salad spooned into crunchy lettuce cups — high protein, almost no carbs, and quick to assemble.',
         'American', ['lunch'], 300),
    meal('greek-yogurt-protein-bowl', 'Greek yogurt protein bowl',
         ['Yogurt', 'Berries', 'Nuts'],
         ['greek-yogurt-nonfat', 'blueberry', 'almond'],
         'Thick nonfat Greek yogurt topped with a few berries and almonds — a high-volume, protein-forward breakfast that stays low in sugar.',
         'American', ['breakfast', 'snack'], 320),
    meal('cottage-cheese-berry-bowl', 'Cottage cheese & berries',
         ['Fresh cheese', 'Berries', 'Nuts'],
         ['cottage-cheese', 'strawberry', 'almond'],
         'Cottage cheese with fresh strawberries and a scatter of almonds — a filling, low-calorie snack with plenty of casein protein.',
         'American', ['breakfast', 'snack'], 280),
    meal('zoodle-shrimp-scampi', 'Zucchini noodle shrimp scampi',
         ['Other vegetables', 'Shellfish', 'Cream & butter', 'Fresh herbs'],
         ['zucchini', 'shrimp', 'butter', 'parsley'],
         'Spiralized zucchini "zoodles" with garlicky butter shrimp and parsley — all the comfort of scampi with the noodles swapped for vegetables.',
         'Italian', ['dinner'], 360),
    meal('zoodle-bolognese', 'Zucchini noodle bolognese',
         ['Other vegetables', 'Red meat', 'Peppers & nightshades', 'Aged cheese'],
         ['zucchini', 'ground-beef-90-10', 'tomato-sauce-canned', 'parmesan'],
         'A rich beef-and-tomato ragu over zucchini noodles, finished with parmesan — a hearty pasta night that skips the wheat.',
         'Italian', ['dinner'], 420),
    meal('cauliflower-fried-rice', 'Cauliflower fried rice',
         ['Cruciferous vegetables', 'Eggs', 'Poultry', 'Other vegetables', 'Sauces'],
         ['cauliflower', 'egg-whole', 'chicken-breast', 'scallion', 'soy-sauce'],
         'Riced cauliflower stir-fried with egg, chicken, and scallion in a splash of soy — the fried-rice format with a fraction of the carbs.',
         'Chinese', ['lunch', 'dinner'], 400),
    meal('egg-white-veggie-omelette', 'Egg-white veggie omelette',
         ['Eggs', 'Peppers & nightshades', 'Mushrooms', 'Aged cheese'],
         ['egg-white', 'bell-pepper-red', 'mushroom-white', 'cheddar'],
         'A fluffy egg-white omelette folded around peppers, mushrooms, and a little cheddar — lean protein to start the day.',
         'American', ['breakfast'], 300),
    meal('chicken-caesar-no-crouton', 'Chicken Caesar salad (no croutons)',
         ['Leafy greens', 'Poultry', 'Aged cheese', 'Dressings & dips'],
         ['romaine-lettuce', 'chicken-breast', 'parmesan', 'mayonnaise'],
         'Romaine tossed in a creamy parmesan Caesar dressing with grilled chicken, holding the croutons — crisp, savory, and protein-dense.',
         'American', ['lunch', 'dinner'], 350),
    meal('baked-salmon-asparagus', 'Baked salmon & asparagus',
         ['Oily fish', 'Other vegetables', 'Oils', 'Fresh herbs'],
         ['salmon', 'asparagus', 'olive-oil', 'dill'],
         'A fillet of omega-3-rich salmon roasted with asparagus, olive oil, and dill — a clean, satisfying low-carb plate.',
         'American', ['dinner'], 320),
    meal('steak-and-eggs', 'Steak & eggs',
         ['Red meat', 'Eggs', 'Cream & butter'],
         ['beef-sirloin', 'egg-whole', 'butter'],
         'Seared sirloin alongside butter-basted eggs — a classic high-protein, zero-carb breakfast that keeps you full for hours.',
         'American', ['breakfast'], 330),
    meal('bunless-bacon-cheeseburger', 'Bunless bacon cheeseburger',
         ['Red meat', 'Processed meat', 'Aged cheese', 'Leafy greens'],
         ['ground-beef-90-10', 'bacon', 'cheddar', 'iceberg-lettuce'],
         'A juicy beef patty with bacon and melted cheddar, wrapped in crisp lettuce instead of a bun — all the burger, none of the bread.',
         'American', ['lunch', 'dinner'], 320),
    meal('beef-broccoli-no-rice', 'Beef & broccoli (no rice)',
         ['Red meat', 'Cruciferous vegetables', 'Sauces', 'Oils'],
         ['beef-sirloin', 'broccoli', 'soy-sauce', 'sesame-oil'],
         'Tender sliced beef and broccoli in a glossy soy-sesame sauce, served as-is without rice — a takeout favorite made low-carb.',
         'Chinese', ['dinner'], 380),
    meal('buffalo-chicken-bites', 'Buffalo chicken bites',
         ['Poultry', 'Sauces', 'Cream & butter', 'Dressings & dips'],
         ['chicken-breast', 'sriracha', 'butter', 'mayonnaise'],
         'Bite-size chicken tossed in a buttery hot sauce with a cool creamy dip — a high-protein, low-carb take on wings.',
         'American', ['snack', 'dinner'], 300),
    meal('pork-rind-chicken-tenders', 'Pork-rind crusted chicken tenders',
         ['Poultry', 'Processed meat', 'Eggs'],
         ['chicken-breast', 'pork-rinds', 'egg-whole'],
         'Chicken tenders breaded in crushed pork rinds and baked crisp — the crunch of breaded tenders with zero breadcrumb carbs.',
         'American', ['lunch', 'dinner'], 300),
    meal('bell-pepper-beef-nachos', 'Bell pepper beef nachos',
         ['Peppers & nightshades', 'Red meat', 'Aged cheese', 'Dressings & dips'],
         ['bell-pepper-red', 'ground-beef-90-10', 'cheddar', 'guacamole'],
         'Bell-pepper "chips" loaded with seasoned beef, melted cheddar, and guacamole — nacho night without the tortilla chips.',
         'Mexican', ['snack', 'dinner'], 380),
    meal('shrimp-cauliflower-grits', 'Shrimp & cauliflower grits',
         ['Shellfish', 'Cruciferous vegetables', 'Aged cheese', 'Cream & butter'],
         ['shrimp', 'cauliflower', 'cheddar', 'butter'],
         'Sauteed shrimp over creamy cheesy cauliflower "grits" — a Southern comfort plate reimagined low-carb.',
         'American', ['dinner'], 360),
    meal('smoked-salmon-rollups', 'Smoked salmon & cream cheese roll-ups',
         ['Canned & cured fish', 'Fresh cheese', 'Fresh herbs'],
         ['smoked-salmon-lox', 'cream-cheese', 'dill'],
         'Smoked salmon rolled around herbed cream cheese — an elegant, near-zero-carb snack or light breakfast.',
         'American', ['breakfast', 'snack'], 180),
]

# --- validate before writing ---
existing = json.load((DATA / 'meals.json').open(encoding='utf-8'))
existing_ids = {m['id'] for m in existing}
errs = []
seen = set()
for m in M:
    if m['id'] in existing_ids or m['id'] in seen:
        errs.append(f"dup id {m['id']}")
    seen.add(m['id'])
    have = defaultdict(int)
    for eid in m['example_ingredients']:
        if eid not in cat_of:
            errs.append(f"{m['id']}: unknown ingredient {eid}")
        else:
            have[cat_of[eid]] += 1
    if len(set(m['example_ingredients'])) != len(m['example_ingredients']):
        errs.append(f"{m['id']}: duplicate example ids")
    for c in m['ingredient_categories']:
        if c in SKIP:
            continue
        if have.get(c, 0) == 0:
            errs.append(f"{m['id']}: category '{c}' has no covering example ingredient")

if errs:
    print('VALIDATION FAILED:')
    for e in errs:
        print('  ', e)
    sys.exit(1)

# field-order normalize
M = [{k: m[k] for k in FIELD_ORDER} for m in M]
existing.extend(M)
out = json.dumps(existing, indent=2, ensure_ascii=False)
(DATA / 'meals.json').open('w', encoding='utf-8').write(out + '\n')
print(f'OK: added {len(M)} meals; meals.json now {len(existing)} entries.')
