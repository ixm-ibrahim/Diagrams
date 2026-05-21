#!/usr/bin/env python3
"""Backfill `serving_grams` onto every ingredient in src/data/ingredients.json.

Two-tier lookup:
  1. SERVING_BY_ID — item-specific values curated from USDA FoodData Central
     Standard Reference (SR Legacy) and FDA RACC (21 CFR 101.12). Covers
     common, easily-verified items.
  2. SERVING_BY_CATEGORY — USDA RACC averages, used as fallback for the
     long tail of items not in the per-ID lookup.

This is a one-shot script. After running, ingredients.json has a
`serving_grams` field on every entry; schema.js prefers that value over
the category fallback when `servingGramsFor()` runs at scene time.

The lookup is conservative: when an exact item isn't in the per-ID
map, the category default applies — accurate-on-average but not
item-specific. The user can hand-edit `serving_grams` in
ingredients.json for any item where they want a different value.
"""
import json
import re
import sys
from pathlib import Path

# --- USDA RACC averages by category. Numbers in grams. ---
# Source: FDA 21 CFR 101.12 Table 2 (Reference Amounts Customarily
# Consumed). Where the regulation gives a volume (mL), it's converted
# 1:1 (water density assumption — close enough for thin liquids).
SERVING_BY_CATEGORY = {
    # Vegetables
    'Leafy greens':              30,
    'Cruciferous vegetables':    85,
    'Peppers & nightshades':     85,
    'Starchy vegetables':       125,
    'Other vegetables':          85,
    'Mushrooms':                 70,
    'Pickled vegetables':        30,
    # Fruits
    'Berries':                  140,
    'Citrus':                   130,
    'Tropical fruits':          140,
    'Temperate fruits':         140,
    'Dried fruits':              40,
    # Grains (dry baseline for staples)
    'Whole grains':              45,
    'Refined grains':            45,
    'Bread & rolls':             55,
    'Baked snacks & pastries':   40,
    'Flours':                    30,
    'Prepared mixes':            55,
    # Protein (animal), cooked weights
    'Red meat':                  85,
    'Poultry':                   85,
    'Organ meats':               85,
    'Processed meat':            55,
    'Eggs':                      50,
    'White fish':                85,
    'Oily fish':                 85,
    'Freshwater fish':           85,
    'Shellfish':                 85,
    'Canned & cured fish':       55,
    # Protein (plant)
    'Legumes':                  130,
    'Soy products':              85,
    'Meat alternatives':         85,
    # Dairy
    'Milk':                     240,
    'Plant milks':              240,
    'Yogurt':                   170,
    'Fermented dairy':          170,
    'Aged cheese':               28,
    'Fresh cheese':              55,
    'Processed cheese':          28,
    'Cream & butter':            14,
    'Frozen dairy':              85,
    # Nuts & seeds
    'Nuts':                      28,
    'Seeds':                     28,
    'Nut butters':               32,
    # Fats & oils
    'Oils':                      14,
    'Margarine & shortening':    14,
    # Sweets
    'Sugar & sweeteners':         4,
    'Jams & preserves':          20,
    'Candy & desserts':          40,
    # Herbs & spices
    'Fresh herbs':                3,
    'Dried herbs':                0.5,
    'Ground spices':              1,
    'Whole spices':               1,
    'Spice blends':               1,
    'Salt & seasonings':          1,
    'Extracts & essences':        2,
    # Condiments & sauces
    'Sauces':                    30,
    'Dressings & dips':          30,
    'Pastes & ferments':         15,
    'Prepared soups & broths':  245,
    'Baking ingredients':        12,
    # Beverages
    'Coffee & tea':             240,
    'Juices':                   240,
    'Soft drinks':              360,
    'Alcoholic beverages':      150,
}

# --- Per-ingredient overrides. Values are grams of a typical serving. ---
# Sources:
#   - USDA FoodData Central, SR Legacy database (sr/Foundation Foods)
#   - FDA 21 CFR 101.12 Reference Amounts Customarily Consumed
# Numbers are USDA SR's "1 medium" or "1 cup" weights where applicable,
# falling back to RACC category amounts for items without a per-piece
# convention.
SERVING_BY_ID = {
    # === Eggs ===
    'egg-whole':            50,   # 1 large egg
    'egg-white':            33,   # white of 1 large
    'egg-yolk':             17,   # yolk of 1 large

    # === Poultry (cooked weights, USDA SR) ===
    'chicken-breast':           85,
    'chicken-thigh-skinless':   85,
    'chicken-thigh-skin-on':    85,
    'chicken-drumstick':        44,   # 1 drumstick, skinless cooked
    'chicken-wing':             21,   # 1 wing cooked, no skin
    'chicken-whole-roasted':    85,
    'chicken-liver':            85,
    'turkey-breast':            85,
    'turkey-thigh':             85,
    'ground-chicken':           85,
    'ground-turkey':            85,
    'duck-breast':              85,

    # === Red meat (3 oz cooked baseline) ===
    'beef-sirloin':         85,
    'beef-ribeye':          85,
    'beef-tenderloin':      85,
    'beef-brisket':         85,
    'beef-chuck-roast':     85,
    'beef-short-ribs':      85,
    'beef-flank-steak':     85,
    'beef-skirt-steak':     85,
    'beef-shank':           85,
    'ground-beef-90-10':    85,
    'ground-beef-80-20':    85,
    'pork-loin':            85,
    'pork-chop':            85,
    'pork-shoulder':        85,
    'pork-belly':           85,
    'pork-ribs-spare':      85,
    'pork-tenderloin':      85,
    'ground-pork':          85,
    'lamb-chop':            85,
    'ground-lamb':          85,
    'veal-cutlet':          85,

    # === Processed meat ===
    'bacon':              16,   # 2 slices cooked
    'ham':                28,   # 1 slice
    'sausage':            45,
    'pepperoni':          14,   # ~7 slices
    'salami':             28,
    'hot-dog':            45,
    'deli-turkey':        56,   # 2 slices
    'beef-jerky':         28,
    'prosciutto':         15,   # 1-2 slices

    # === Fish & seafood (cooked) ===
    'cod':         85,
    'tilapia':     85,
    'halibut':     85,
    'sole':        85,
    'haddock':     85,
    'pollock':     85,
    'salmon':      85,
    'tuna':        85,
    'mackerel':    85,
    'sardines':    50,   # 1 small can drained
    'anchovies':   16,   # 2 fillets
    'trout':       85,
    'shrimp':      85,   # ~4-5 large cooked
    'lobster':     85,
    'crab':        85,
    'scallops':    85,
    'mussels':     85,
    'oysters':     85,   # 6 medium

    # === Vegetables (USDA SR weights) ===
    'spinach':              30,   # 1 cup raw
    'kale':                 67,   # 1 cup chopped
    'romaine-lettuce':      47,
    'arugula':              20,
    'swiss-chard':          36,
    'collard-greens':       36,
    'cabbage-green':        89,   # 1 cup chopped
    'cabbage-red':          89,
    'broccoli':             91,
    'cauliflower':         100,
    'brussels-sprouts':     88,
    # Whole-cucumber (301g) and whole-eggplant (458g) numbers were
    # encoding the produce-item weight, not a serving. RACC pegs a
    # cucumber serving at ~1/2 cup (52g) and an eggplant serving at
    # ~1 cup cubed (82g) — what people actually plate.
    'cucumber':             52,   # 1/2 cup sliced
    'zucchini':            196,   # 1 medium
    'tomato':              123,   # 1 medium
    'bell-pepper-red':     119,   # 1 medium
    'bell-pepper-green':   119,
    'mushroom-white':       70,   # 1 cup sliced
    'mushroom-portobello':  84,
    'asparagus':           134,   # 1 cup chopped
    'green-beans':         100,   # 1 cup
    'eggplant':             82,   # 1 cup cubed
    'celery':               40,   # 1 stalk
    'onion':               110,   # 1 medium
    'garlic':                3,   # 1 clove
    'potato-russet':       213,   # 1 medium
    'sweet-potato':        130,   # 1 medium
    'corn':                 90,   # 1 cup kernels
    'carrot':               61,   # 1 medium
    'beet':                 82,
    'butternut-squash':    205,   # 1 cup cubed
    'pumpkin':             116,   # 1 cup cubed
    # Tomato-derived items overruled the Peppers & nightshades default (85g),
    # which doesn't match how these are used in practice.
    'tomato-paste':         33,   # 2 tbsp — used as a flavor add, not a vegetable serving
    'sun-dried-tomato':      7,   # ~1 tbsp / a small handful of pieces

    # === Fruits (USDA SR) ===
    'apple':           182,   # 1 medium (3" diameter)
    'banana':          118,
    'orange':          131,
    'grape':           151,   # 1 cup
    'mango':           165,   # 1 cup pieces
    'pineapple':       165,   # 1 cup chunks
    'watermelon':      152,   # 1 cup diced
    'cantaloupe':      160,   # 1 cup diced
    'peach':           147,
    'pear':            178,
    'plum':             66,
    'cherry':          154,   # 1 cup with pits
    'kiwi':             69,
    'avocado':         200,   # 1 medium
    'lemon':            84,
    'lime':             67,
    'strawberry':      152,   # 1 cup
    'blueberry':       148,
    'raspberry':       123,
    'blackberry':      144,
    'cranberry':       100,   # 1 cup fresh
    'grapefruit':      246,
    'apricot':          35,
    'nectarine':       140,
    'pomegranate-seeds': 87,

    # === Dried fruit ===
    'raisin':           43,   # 1/4 cup
    'date-medjool':     24,   # 1 medjool
    'dried-apricot':    40,   # ~5 halves
    'dried-cranberry':  40,
    'prune':            24,   # 1 prune

    # === Legumes (cooked, 1/2 cup) ===
    'lentils-green':  99,    # 1/2 cup cooked
    'lentils-red':    99,
    'black-beans':    86,    # 1/2 cup cooked
    'chickpea':       82,    # 1/2 cup cooked
    'kidney-bean':    88,
    'white-bean':     88,
    'pinto-bean':     86,
    'soybeans':       86,
    'edamame':        78,    # 1/2 cup shelled
    'peanut':         28,    # 1 oz; (peanut is botanically a legume)
    'tofu-firm':      85,
    'tempeh':         84,    # 1/2 cup
    # Bean-derived items that landed in Legumes but don't get used at
    # the 130g cooked-bean serving.
    'chickpea-flour-besan': 30,   # 1/4 cup, like other flours
    'anko-red-bean-paste':  30,   # ~2 tbsp; mochi/wagashi filling
    'white-bean-paste':     30,   # 2 tbsp; shiroan

    # === Grains (cooked for cooked-form items, dry for dry staples) ===
    'brown-rice':       195,   # 1 cup cooked
    'wild-rice':        164,
    'quinoa':           185,
    'oats-rolled':       40,   # 1/2 cup dry
    'barley':           157,   # 1 cup cooked pearl
    'buckwheat':        168,
    'whole-wheat-bread': 28,   # 1 slice
    'whole-wheat-pasta': 56,   # 2 oz dry
    'bulgur':           182,   # 1 cup cooked
    'farro':            194,
    'white-rice':       158,
    'white-bread':       25,
    'white-pasta':       56,
    'white-tortilla':    30,   # 1 small flour tortilla
    'saltine-crackers':  15,   # 5 crackers

    # === Nuts & seeds (1 oz baseline) ===
    'almond':         28,
    'walnut':         28,
    'cashew':         28,
    'pistachio':      28,
    'pecan':          28,
    'hazelnut':       28,
    'peanut-butter':  32,   # 2 tbsp
    'almond-butter':  32,
    'tahini':         30,   # 2 tbsp
    'chia-seed':      28,   # ~2 tbsp
    'flax-seed':       7,   # 1 tbsp
    'pumpkin-seed':   28,
    'sunflower-seed': 28,
    'sesame-seed':     9,   # 1 tbsp

    # === Oils & fats ===
    'olive-oil':     14,
    'coconut-oil':   14,
    'avocado-oil':   14,
    'canola-oil':    14,
    'sesame-oil':    14,
    'butter':        14,
    'ghee':          14,
    'heavy-cream':   30,   # 2 tbsp
    'sour-cream':    30,

    # === Dairy ===
    'whole-milk':            240,
    'milk-2-percent':        240,
    'milk-1-percent':        240,
    'skim-milk':             240,
    'yogurt-whole':          170,
    'greek-yogurt-whole':    170,
    'greek-yogurt-nonfat':   170,
    'cottage-cheese':        113,   # 1/2 cup
    'ricotta':                62,   # 1/4 cup
    'cream-cheese':           28,
    'fresh-mozzarella':       28,
    'cheddar':                28,
    'parmesan':                5,   # 1 tbsp grated
    'swiss':                  28,
    'brie':                   28,
    'blue-cheese':            28,
    'feta':                   28,
    'mozzarella-low-moisture':28,
    'ice-cream-vanilla':      66,   # 1/2 cup (was 85 in older RACC; current FDA is 66g for ice cream)

    # === Sugars & sweets ===
    'white-sugar':     4,    # 1 tsp
    'honey':          21,    # 1 tbsp
    'maple-syrup':    20,
    'dark-chocolate': 40,
    'milk-chocolate': 40,

    # === Beverages ===
    # (Many beverage IDs will fall into their categories; we cover
    #  staples here.)
}


def main():
    root = Path(__file__).resolve().parent.parent
    src = root / 'src' / 'data' / 'ingredients.json'
    if not src.exists():
        sys.exit(f"ingredients.json not found at {src}")

    text = src.read_text(encoding='utf-8')
    data = json.loads(text)

    changed = 0
    per_id_hits = 0
    per_category_hits = 0
    fallback_hits = 0
    missing_category = set()

    for ing in data:
        ing_id = ing.get('id')
        category = ing.get('category')
        if ing_id in SERVING_BY_ID:
            grams = SERVING_BY_ID[ing_id]
            per_id_hits += 1
        elif category in SERVING_BY_CATEGORY:
            grams = SERVING_BY_CATEGORY[category]
            per_category_hits += 1
        else:
            grams = 100  # untyped fallback
            fallback_hits += 1
            if category:
                missing_category.add(category)
        if ing.get('serving_grams') != grams:
            ing['serving_grams'] = grams
            changed += 1
        else:
            # Already at this value — still update field order if needed,
            # but no need to count as a change.
            ing['serving_grams'] = grams

    # Write back with the same single-line-per-ingredient style the
    # source file uses. The file is "[\n  {ingredient}, \n  {ingredient}, ...\n]"
    # so we emit each ingredient on one JSON line with stable key order.
    lines = ['[']
    for i, ing in enumerate(data):
        suffix = ',' if i < len(data) - 1 else ''
        lines.append('  ' + json.dumps(ing, ensure_ascii=False) + suffix)
    lines.append(']')
    src.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    print(f"Updated {src}")
    print(f"  per-id hits:       {per_id_hits}")
    print(f"  per-category hits: {per_category_hits}")
    print(f"  untyped fallback:  {fallback_hits}")
    print(f"  rows changed:      {changed} / {len(data)}")
    if missing_category:
        print(f"  categories without RACC entry: {sorted(missing_category)}")


if __name__ == '__main__':
    main()
