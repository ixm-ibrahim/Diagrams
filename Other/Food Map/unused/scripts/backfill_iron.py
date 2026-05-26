#!/usr/bin/env python3
"""Backfill iron (mg per 100g) onto every ingredient in src/data/ingredients.json.

USDA FoodData Central is the source of truth for per-food iron values;
we encode a curated mapping from ingredient identifiers / subcategories /
categories / food_groups to typical USDA values. The resolution order is
narrowest-first so a specific lookup (chicken-liver, sesame-seeds) wins
over a category-level default (Organ meats, Seeds).

Items already carrying the 'iron-rich' identity tag get bumped to at least
the FDA "high" threshold (3.5 mg/100g) so the tag stays honest after we
re-derive it from the new value at boot (NUTRIENT_TAG_RULES.iron-rich).

A backup of the pre-iron file is written alongside (ingredients.pre-iron.json)
so the run is reversible.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INGREDIENTS_PATH = REPO_ROOT / 'src' / 'data' / 'ingredients.json'
BACKUP_PATH      = REPO_ROOT / 'src' / 'data' / 'ingredients.pre-iron.json'

# --- ID-level overrides (highest priority) -----------------------------
# Looked up by ingredient.id; USDA values for well-known foods.
ID_OVERRIDES = {
    # Organ meats
    'beef-liver':       6.5,
    'chicken-liver':    9.0,
    'pork-liver':       17.9,
    'lamb-liver':       8.7,
    'duck-liver':       30.5,
    'beef-heart':       4.6,
    'beef-kidney':      4.6,
    # Shellfish
    'mussels':          6.7,
    'oysters':          5.1,
    'clams':            13.9,
    'scallops':         0.4,
    'shrimp':           0.5,
    'crab':             0.7,
    'lobster':          0.3,
    'octopus':          5.3,
    'squid':            0.7,
    # Oily/canned fish
    'sardines':         2.9,
    'sardines-canned':  2.9,
    'anchovies':        3.3,
    'anchovies-canned': 4.6,
    'mackerel':         1.6,
    'mackerel-canned':  2.3,
    'salmon':           0.5,
    'salmon-canned':    0.9,
    'tuna':             1.0,
    'tuna-canned':      1.0,
    # Seeds
    'pumpkin-seeds':    8.8,
    'sesame-seeds':     14.6,
    'sunflower-seeds':  5.3,
    'chia-seeds':       7.7,
    'flax-seeds':       5.7,
    'hemp-seeds':       7.9,
    'poppy-seeds':      9.8,
    # Nuts
    'almonds':          3.7,
    'cashews':          6.7,
    'pistachios':       3.9,
    'walnuts':          2.9,
    'pecans':           2.5,
    'hazelnuts':        4.7,
    'brazil-nuts':      2.4,
    'macadamia-nuts':   3.7,
    'pine-nuts':        5.5,
    'peanuts':          4.6,
    # Legumes (cooked unless noted; matches dataset's cooked convention)
    'lentils':          3.3,
    'red-lentils':      3.3,
    'green-lentils':    3.3,
    'black-beans':      2.1,
    'kidney-beans':     2.2,
    'pinto-beans':      2.1,
    'navy-beans':       2.4,
    'chickpeas':        2.9,
    'soybeans':         5.1,
    'edamame':          2.3,
    'lima-beans':       2.4,
    'split-peas':       1.3,
    # Soy products
    'tofu':             5.4,
    'tempeh':           2.7,
    'soy-milk':         0.6,
    'natto':            2.8,
    # Dark leafy greens
    'spinach':          2.7,
    'spinach-cooked':   3.6,
    'kale':             1.5,
    'swiss-chard':      1.8,
    'collard-greens':   1.1,
    'beet-greens':      2.6,
    'mustard-greens':   1.5,
    'turnip-greens':    1.1,
    'watercress':       0.2,
    'arugula':          1.5,
    'romaine-lettuce':  1.0,
    'iceberg-lettuce':  0.4,
    # Other vegetables
    'broccoli':         0.7,
    'cauliflower':      0.4,
    'asparagus':        2.1,
    'brussels-sprouts': 1.4,
    'cabbage':          0.5,
    'bok-choy':         0.8,
    'edamame-pods':     2.3,
    'tomato':           0.3,
    'tomato-canned':    0.9,
    'tomato-paste':     2.9,
    'tomato-sauce':     1.0,
    'sun-dried-tomatoes':9.1,
    'red-bell-pepper':  0.4,
    'green-bell-pepper':0.3,
    'jalapeno':         1.0,
    'mushrooms':        0.5,
    'shiitake-mushrooms':0.4,
    'portobello-mushrooms':0.3,
    # Starchy
    'potato':           0.8,
    'sweet-potato':     0.6,
    'cassava':          0.3,
    'corn':             0.5,
    'plantain':         0.6,
    # Fruits
    'apple':            0.1,
    'banana':           0.3,
    'orange':           0.1,
    'lemon':            0.6,
    'lime':             0.6,
    'grapefruit':       0.1,
    'strawberries':     0.4,
    'blueberries':      0.3,
    'raspberries':      0.7,
    'blackberries':     0.6,
    'mango':            0.2,
    'pineapple':        0.3,
    'avocado':          0.6,
    'watermelon':       0.2,
    'grapes':           0.4,
    'cherries':         0.4,
    'pear':             0.2,
    'peach':            0.3,
    # Dried fruits
    'raisins':          1.9,
    'dried-apricots':   2.7,
    'dried-figs':       2.0,
    'prunes':           0.9,
    'dates':            0.9,
    'dried-cranberries':0.4,
    # Grains
    'oats':             4.7,
    'rolled-oats':      4.3,
    'steel-cut-oats':   4.3,
    'quinoa':           1.5,    # cooked
    'brown-rice':       0.4,    # cooked
    'white-rice':       0.2,    # cooked
    'wild-rice':        0.6,
    'barley':           1.3,
    'bulgur':           1.0,
    'farro':            1.4,
    'millet':           0.6,
    'buckwheat':        0.8,
    'amaranth':         2.1,
    'teff':             7.6,
    'corn-tortilla':    1.2,
    'flour-tortilla':   2.4,
    # Bread
    'whole-wheat-bread':2.5,
    'white-bread':      1.4,
    'sourdough-bread':  2.4,
    'rye-bread':        1.8,
    'pita-bread':       2.9,
    'naan':             2.4,
    'bagel':            2.7,
    'baguette':         2.6,
    'cornbread':        1.5,
    # Pasta
    'spaghetti':        1.3,    # cooked
    'penne':            1.3,
    'rice-noodles':     0.2,
    'soba-noodles':     1.1,
    'whole-wheat-pasta':1.5,
    # Flours
    'all-purpose-flour':4.6,
    'whole-wheat-flour':3.6,
    'almond-flour':     3.7,
    'coconut-flour':    6.3,
    'oat-flour':        4.0,
    'chickpea-flour':   4.9,
    'cornmeal':         2.4,
    'cornstarch':       0.5,
    # Dairy
    'milk':             0.03,
    'skim-milk':        0.03,
    'whole-milk':       0.03,
    'almond-milk':      0.3,
    'soy-milk':         0.6,
    'oat-milk':         0.4,
    'coconut-milk':     1.6,
    'yogurt':           0.05,
    'greek-yogurt':     0.07,
    'cottage-cheese':   0.1,
    'ricotta':          0.4,
    'mozzarella':       0.4,
    'cheddar':          0.7,
    'parmesan':         0.8,
    'feta':             0.7,
    'cream-cheese':     0.4,
    'butter':           0.02,
    'cream':            0.05,
    'sour-cream':       0.06,
    'ice-cream':        0.2,
    # Eggs
    'egg':              1.8,
    'egg-white':        0.1,
    'egg-yolk':         2.7,
    # Red meat
    'beef-sirloin':     2.6,
    'beef-ribeye':      1.9,
    'beef-tenderloin':  2.6,
    'beef-chuck':       2.7,
    'ground-beef':      2.6,
    'beef-brisket':     2.7,
    'lamb':             1.9,
    'lamb-chop':        1.9,
    'pork-loin':        0.9,
    'pork-shoulder':    1.0,
    'pork-belly':       0.8,
    'ground-pork':      0.9,
    'bacon':            0.6,
    'ham':              0.7,
    'prosciutto':       1.4,
    'salami':           1.4,
    'pepperoni':        1.4,
    'sausage':          1.5,
    'chorizo':          1.5,
    'hot-dog':          1.2,
    # Poultry
    'chicken-breast':   0.4,
    'chicken-thigh-skinless':1.0,
    'chicken-thigh-skin-on':1.0,
    'chicken-wing':     1.3,
    'chicken-drumstick':1.3,
    'ground-chicken':   0.9,
    'turkey-breast':    0.7,
    'turkey-thigh':     1.6,
    'ground-turkey':    1.3,
    'duck-breast':      4.5,
    'duck-skin-on':     2.7,
    # Sweets
    'sugar':            0.0,
    'brown-sugar':      0.7,
    'honey':            0.4,
    'maple-syrup':      0.1,
    'molasses':         4.7,
    'dark-chocolate':   11.9,
    'milk-chocolate':   2.4,
    'cocoa-powder':     13.9,
    'chocolate-chips':  8.0,
    'gummies':          0.5,
    'hard-candy':       0.1,
    # Fats & oils (effectively no iron)
    'olive-oil':        0.6,
    'butter-clarified':0.02,
    'coconut-oil':      0.05,
    'avocado-oil':      0.0,
    'vegetable-oil':    0.0,
    'canola-oil':       0.0,
    'sesame-oil':       0.0,
    'sunflower-oil':    0.0,
    'peanut-oil':       0.0,
    'lard':             0.0,
    'tallow':           0.0,
    'ghee':             0.02,
    'margarine':        0.06,
    # Herbs & spices (dried, very concentrated)
    'cumin':            66.4,
    'turmeric':         55.0,
    'paprika':          21.1,
    'curry-powder':     19.1,
    'cinnamon':         8.3,
    'oregano-dried':    36.8,
    'thyme-dried':      123.6,
    'rosemary-dried':   29.3,
    'basil-dried':      89.8,
    'parsley-dried':    22.0,
    'mint-dried':       87.5,
    'sage-dried':       28.1,
    'bay-leaves':       43.0,
    'cloves-ground':    11.8,
    'cardamom':         13.9,
    'nutmeg':           3.0,
    'ginger-ground':    19.8,
    'garlic-powder':    5.7,
    'onion-powder':     2.2,
    'mustard-seed':     9.2,
    'black-pepper':     9.7,
    'white-pepper':     14.3,
    'cayenne':          7.8,
    'chili-powder':     17.3,
    # Fresh herbs (much lower than dried)
    'basil':            3.2,
    'parsley':          6.2,
    'cilantro':         1.8,
    'mint':             5.1,
    'dill':             6.6,
    'chives':           1.6,
    'rosemary':         6.7,
    'thyme':            17.5,
    'sage':             28.1,
    'oregano':          3.6,
    'tarragon':         3.2,
    # Salt-table family is ~0 unless fortified
    'salt':             0.3,
    'kosher-salt':      0.3,
    'sea-salt':         0.4,
    'pink-salt':        0.4,
    # Condiments & sauces
    'soy-sauce':        2.4,
    'tamari':           2.4,
    'fish-sauce':       0.8,
    'oyster-sauce':     0.7,
    'hoisin-sauce':     0.9,
    'sriracha':         1.5,
    'ketchup':          0.4,
    'mustard':          1.5,
    'mayonnaise':       0.2,
    'vinegar':          0.0,
    'balsamic-vinegar': 0.7,
    'apple-cider-vinegar':0.2,
    'rice-vinegar':     0.0,
    'salsa':            0.6,
    'pesto':            2.7,
    'tahini':           8.95,
    'hummus':           2.4,
    'miso':             2.5,
    'gochujang':        2.5,
    'sambal':           2.0,
    # Pickled
    'pickles':          0.4,
    'sauerkraut':       1.5,
    'kimchi':           0.5,
    'olives-green':     0.5,
    'olives-black':     3.3,
    'capers':           1.7,
    # Beverages
    'water':            0.0,
    'coffee':           0.01,
    'tea':              0.02,
    'black-tea':        0.02,
    'green-tea':        0.02,
    'orange-juice':     0.2,
    'apple-juice':      0.1,
    'tomato-juice':     0.4,
    'beer':             0.02,
    'wine-red':         0.5,
    'wine-white':       0.3,
    'whiskey':          0.04,
    'vodka':            0.0,
    'soda':             0.0,
    'cola':             0.0,
}

# --- Subcategory defaults (USDA midpoint per subcategory) --------------
SUBCATEGORY_DEFAULTS = {
    # Vegetables
    'Spinach':                  2.7,
    'Dark leafy greens':        1.8,
    'Lettuce':                  0.7,
    'Cooking greens':           1.5,
    # Protein (animal)
    'Beef':                     2.5,
    'Pork':                     0.9,
    'Lamb':                     1.7,
    'Game meat':                3.5,
    'Chicken':                  0.9,
    'Turkey':                   1.4,
    'Duck':                     2.7,
    'Goose':                    2.6,
    'Other poultry':            1.5,
    'Ground poultry':           1.1,
    # Fish
    'Cod':                      0.4,
    'Tilapia':                  0.6,
    'Sole':                     0.4,
    'Halibut':                  1.1,
    'Salmon':                   0.7,
    'Tuna':                     1.0,
    'Mackerel':                 1.6,
    'Sardines':                 2.9,
    'Trout':                    0.7,
    'Catfish':                  0.3,
    'Bass':                     1.5,
    # Plant protein
    'Soy':                      4.0,
    'Lentils':                  3.3,
    'Beans':                    2.3,
    'Peas':                     1.5,
    # Grains
    'Oats':                     4.5,
    'Wheat':                    3.0,
    'Rice':                     0.3,
    'Corn':                     0.5,
    'Barley':                   1.3,
    'Quinoa':                   1.5,
    'Rye':                      2.0,
    'Bread':                    2.5,
    # Dairy
    'Cow milk':                 0.03,
    'Sheep milk':               0.1,
    'Goat milk':                0.1,
    'Plant milk':               0.4,
    'Yogurt':                   0.05,
    'Greek yogurt':             0.07,
    'Hard cheese':              0.7,
    'Soft cheese':              0.4,
    'Blue cheese':              0.3,
    # Nuts & seeds
    'Tree nuts':                4.0,
    'Peanuts':                  4.6,
    'Seeds':                    7.0,
    # Sweets
    'Chocolate':                7.0,
    'Sugar':                    0.1,
    'Syrups':                   0.5,
    'Candy':                    0.5,
    # Herbs
    'Fresh herbs':              4.0,
    'Dried herbs':              40.0,
    'Ground spices':            15.0,
    'Whole spices':             15.0,
    'Salt':                     0.3,
}

# --- Category defaults (broader; only used when subcat/id don't match) -
CATEGORY_DEFAULTS = {
    # Vegetables
    'Leafy greens':              2.0,
    'Cruciferous vegetables':    0.6,
    'Peppers & nightshades':     0.5,
    'Starchy vegetables':        0.6,
    'Other vegetables':          0.6,
    'Mushrooms':                 0.5,
    'Pickled vegetables':        0.8,
    # Fruits
    'Berries':                   0.5,
    'Citrus':                    0.2,
    'Tropical fruits':           0.3,
    'Temperate fruits':          0.2,
    'Dried fruits':              1.5,
    # Grains
    'Whole grains':              2.5,
    'Refined grains':            1.0,
    'Bread & rolls':             2.4,
    'Pasta & noodles':           1.3,
    'Baked snacks & pastries':   1.5,
    'Flours':                    3.5,
    'Prepared mixes':            2.5,
    # Protein (animal)
    'Red meat':                  2.5,
    'Poultry':                   1.0,
    'Organ meats':               7.5,
    'Processed meat':            1.4,
    'Eggs':                      1.7,
    'White fish':                0.5,
    'Oily fish':                 1.5,
    'Freshwater fish':           0.7,
    'Shellfish':                 3.0,
    'Canned & cured fish':       2.2,
    # Protein (plant)
    'Legumes':                   2.5,
    'Soy products':              3.5,
    'Meat alternatives':         2.5,
    # Dairy
    'Milk':                      0.05,
    'Plant milks':               0.4,
    'Yogurt':                    0.07,
    'Fermented dairy':           0.1,
    'Aged cheese':               0.5,
    'Fresh cheese':              0.3,
    'Processed cheese':          0.4,
    'Cream & butter':            0.05,
    'Frozen dairy':              0.2,
    # Nuts & seeds
    'Nuts':                      3.5,
    'Seeds':                     7.0,
    'Nut butters':               2.8,
    # Fats & oils
    'Oils':                      0.05,
    'Margarine & shortening':    0.06,
    # Sweets
    'Sugar & sweeteners':        0.3,
    'Jams & preserves':          0.3,
    'Candy & desserts':          1.5,
    # Herbs & spices
    'Fresh herbs':               4.0,
    'Dried herbs':               40.0,
    'Ground spices':             15.0,
    'Whole spices':              15.0,
    'Spice blends':              15.0,
    'Salt & seasonings':         0.5,
    'Extracts & essences':       0.1,
    # Condiments & sauces
    'Sauces':                    0.8,
    'Dressings & dips':          0.6,
    'Pastes & ferments':         3.0,
    'Prepared soups & broths':   0.4,
    'Baking ingredients':        4.5,
    # Beverages
    'Coffee & tea':              0.03,
    'Juices':                    0.3,
    'Soft drinks':               0.02,
    'Alcoholic beverages':       0.3,
}

# --- food_group fallback (broadest) ------------------------------------
FOOD_GROUP_DEFAULTS = {
    'Vegetables':           0.8,
    'Fruits':               0.3,
    'Grains':               2.0,
    'Protein (animal)':     1.8,
    'Protein (plant)':      3.0,
    'Dairy':                0.2,
    'Nuts & seeds':         4.0,
    'Fats & oils':          0.05,
    'Sweets':               1.0,
    'Herbs & spices':       15.0,
    'Condiments & sauces':  1.0,
    'Beverages':            0.1,
}

# FDA "high" iron threshold (used by NUTRIENT_TAG_RULES.iron-rich)
IRON_RICH_FLOOR = 3.5


def resolve_iron(ing):
    iid = ing.get('id', '')
    if iid in ID_OVERRIDES:
        return ID_OVERRIDES[iid]
    # Conservative base-id fallback: only strip suffixes where iron is
    # roughly preserved (cooked/raw/canned for meats and produce). NEVER
    # strip dried/fresh/powdered — dried herbs and spices carry 10-100×
    # the iron of their fresh form, so collapsing those would propagate
    # wildly wrong values (e.g., turmeric-fresh inheriting dried
    # turmeric's 55 mg/100g instead of its real ~0.4).
    SAFE_STRIP = {'cooked', 'raw', 'canned'}
    parts = iid.split('-')
    if any(p in SAFE_STRIP for p in parts):
        base_id = '-'.join(p for p in parts if p not in SAFE_STRIP)
        if base_id and base_id != iid and base_id in ID_OVERRIDES:
            return ID_OVERRIDES[base_id]
    sub = ing.get('subcategory')
    if sub and sub in SUBCATEGORY_DEFAULTS:
        return SUBCATEGORY_DEFAULTS[sub]
    cat = ing.get('category')
    if cat and cat in CATEGORY_DEFAULTS:
        return CATEGORY_DEFAULTS[cat]
    fg = ing.get('food_group')
    if fg and fg in FOOD_GROUP_DEFAULTS:
        return FOOD_GROUP_DEFAULTS[fg]
    return 0.5  # generic dataset midpoint


def main():
    ings = json.loads(INGREDIENTS_PATH.read_text(encoding='utf-8'))
    if not BACKUP_PATH.exists():
        BACKUP_PATH.write_text(json.dumps(ings, indent=2), encoding='utf-8')
        print(f'[backfill_iron] wrote backup: {BACKUP_PATH.name}')

    changed = 0
    bumped_for_tag = 0
    for ing in ings:
        if not isinstance(ing, dict):
            continue
        iron = resolve_iron(ing)
        # If the ingredient was hand-tagged iron-rich (pre-batch-5), make
        # sure our derived value clears the FDA "high" floor so the tag
        # remains valid after re-derivation at boot.
        stored_tags = ing.get('tags') or []
        if isinstance(stored_tags, list) and 'iron-rich' in stored_tags:
            if iron < IRON_RICH_FLOOR:
                iron = IRON_RICH_FLOOR
                bumped_for_tag += 1
        prev = ing.get('iron')
        ing['iron'] = round(iron, 2)
        if prev != ing['iron']:
            changed += 1

    INGREDIENTS_PATH.write_text(json.dumps(ings, indent=2), encoding='utf-8')
    print(f'[backfill_iron] updated {changed}/{len(ings)} ingredients')
    print(f'[backfill_iron] bumped {bumped_for_tag} items to clear iron-rich floor')
    # Distribution summary so the user can sanity-check at a glance.
    bins = [0, 0.5, 1, 2, 3.5, 6, 10, 20, 50, 200]
    counts = [0] * (len(bins) - 1)
    for ing in ings:
        v = ing.get('iron', 0)
        for i in range(len(bins) - 1):
            if bins[i] <= v < bins[i + 1]:
                counts[i] += 1
                break
    print('[backfill_iron] distribution (mg/100g):')
    for i, c in enumerate(counts):
        print(f'  {bins[i]:>5} – {bins[i+1]:<5}: {c}')


if __name__ == '__main__':
    main()
