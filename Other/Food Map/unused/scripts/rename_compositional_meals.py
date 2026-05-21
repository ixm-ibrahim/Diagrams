#!/usr/bin/env python3
"""Audit + rebuild compositional-meals.json with human-recognizable dish names.

The original corpus-derived file uses machine names like "Pasta + cream"
that read as ingredient lists rather than dishes. This script:

  1. Strips "noise" categories (sugar, salt, spices, oils, baking ingredients,
     extracts, fresh herbs, sauces, margarine, prepared mixes) when keying
     a pattern to a dish, since they appear in almost every recipe and don't
     define the meal.
  2. Looks up the resulting "core shape" (a frozenset of meaningful categories)
     in SHAPE_TO_NAMES to produce 0, 1, or N recognizable dish names.
       - 0 names → DROP the pattern (e.g. "Sugar + Salt" — not a meal)
       - 1 name  → rename the existing pattern
       - N names → emit N pattern variants (each with the same category list
                   and a fraction of the original frequency), so users searching
                   for "Pancakes" or "Cake" can both land on the underlying
                   {flour+egg+butter+milk+sugar} shape.
  3. Falls back to a "best effort" composer for any shape not in the table
     (mostly long-tail single-variant patterns).

Outputs the rebuilt list to src/data/compositional-meals.json. A diff
report goes to docs/compositional-meals-audit.txt.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "data" / "compositional-meals.json"
OUT_DATA = SRC  # in-place rewrite
OUT_REPORT = ROOT / "docs" / "compositional-meals-audit.txt"

# Categories that appear in almost every pattern (salt, sugar, oil, spices,
# baking ingredients) — they don't identify the dish, only flavor it. Strip
# before looking up.
NOISE = frozenset({
    "Sugar & sweeteners",
    "Salt & seasonings",
    "Ground spices",
    "Oils",
    "Baking ingredients",
    "Extracts & essences",
    "Fresh herbs",
    "Sauces",
    "Margarine & shortening",
    "Prepared mixes",
})

# Marker for "drop this pattern, it has no recognizable meal name". Used as
# the sole value in SHAPE_TO_NAMES for empty-shape or junk-shape entries.
DROP: list[str] = []

# Frozen sets of meaningful categories (NOISE already stripped) → ordered
# list of dish names that pattern can plausibly be. When multiple names are
# listed, the pattern is split into that many variants in the output.
#
# Names are kept short and recognizable to a layperson; preparation is
# implied by the categories themselves.
SHAPE_TO_NAMES: dict[frozenset[str], list[str]] = {

    # ----- empty / noise-only -----
    frozenset(): DROP,

    # ----- single-category shapes -----
    frozenset({"Other vegetables"}): [
        "Roasted vegetables", "Sautéed vegetables", "Steamed vegetable medley",
    ],
    frozenset({"Temperate fruits"}): [
        "Sliced apples", "Fresh fruit plate", "Poached pears",
    ],
    frozenset({"Berries"}): [
        "Mixed berries", "Strawberry bowl",
    ],
    frozenset({"Starchy vegetables"}): [
        "Mashed potatoes", "Roasted potatoes", "Baked sweet potato",
    ],
    frozenset({"Cream & butter"}): [
        "Compound butter", "Brown butter sauce",
    ],
    frozenset({"Milk"}): [
        "Glass of milk", "Warm milk",
    ],
    frozenset({"Eggs"}): [
        "Scrambled eggs", "Fried eggs", "Omelet", "Hard-boiled eggs",
    ],
    frozenset({"Flours"}): DROP,  # plain flour isn't a meal
    frozenset({"Bread & rolls"}): [
        "Sliced bread", "Dinner rolls", "Toast",
    ],
    frozenset({"Aged cheese"}): [
        "Cheese plate", "Sliced cheddar",
    ],
    frozenset({"Fresh cheese"}): [
        "Ricotta plate", "Cottage cheese bowl", "Fresh mozzarella",
    ],
    frozenset({"Nuts"}): [
        "Mixed nuts", "Roasted nuts",
    ],
    frozenset({"Nut butters"}): [
        "Peanut butter spread", "Almond butter",
    ],
    frozenset({"Poultry"}): [
        "Roast chicken", "Grilled chicken breast", "Roast turkey",
    ],
    frozenset({"Red meat"}): [
        "Roast beef", "Grilled steak", "Ground beef skillet",
    ],
    frozenset({"Processed meat"}): [
        "Bacon", "Ham slices", "Breakfast sausage",
    ],
    frozenset({"Whole grains"}): [
        "Brown rice", "Oatmeal", "Cooked quinoa",
    ],
    frozenset({"Refined grains"}): [
        "White rice", "Buttered pasta",
    ],
    frozenset({"Legumes"}): [
        "Cooked lentils", "Black beans", "Chickpeas",
    ],
    frozenset({"Leafy greens"}): [
        "Sautéed greens", "Green salad",
    ],
    frozenset({"Shellfish"}): [
        "Steamed shrimp", "Boiled crab",
    ],
    frozenset({"Alcoholic beverages"}): [
        "Glass of wine", "Cocktail", "Beer",
    ],
    frozenset({"Coffee & tea"}): [
        "Coffee", "Hot tea",
    ],
    frozenset({"Juices"}): [
        "Glass of juice",
    ],
    frozenset({"Soft drinks"}): DROP,
    frozenset({"Dried fruits"}): [
        "Dried fruit mix", "Raisins",
    ],
    frozenset({"Organ meats"}): [
        "Pan-seared liver", "Chopped liver",
    ],
    frozenset({"Yogurt"}): [
        "Yogurt bowl",
    ],
    frozenset({"Fermented dairy"}): [
        "Yogurt bowl", "Kefir",
    ],
    frozenset({"Cruciferous vegetables"}): [
        "Roasted broccoli", "Sautéed cabbage",
    ],
    frozenset({"Plant milks"}): [
        "Almond milk glass",
    ],

    # ----- two-category shapes — most frequent first -----
    frozenset({"Berries", "Temperate fruits"}): [
        "Mixed fruit salad", "Berry & peach bowl",
    ],
    frozenset({"Other vegetables", "Temperate fruits"}): [
        "Waldorf-style salad", "Roasted veg with apple",
    ],
    frozenset({"Other vegetables", "Red meat"}): [
        "Beef stir-fry", "Beef & vegetables", "Pot roast with veg",
    ],
    frozenset({"Other vegetables", "Poultry"}): [
        "Chicken & vegetables", "Chicken stir-fry", "Sheet-pan chicken",
    ],
    frozenset({"Other vegetables", "Starchy vegetables"}): [
        "Roasted root medley", "Vegetable hash",
    ],
    frozenset({"Leafy greens", "Other vegetables"}): [
        "Tossed salad", "Garden salad", "Sautéed greens with veg",
    ],
    frozenset({"Cream & butter", "Milk"}): [
        "Béchamel base", "Cream sauce",
    ],
    frozenset({"Cream & butter", "Temperate fruits"}): [
        "Buttered apples", "Sautéed pears",
    ],
    frozenset({"Cream & butter", "Flours"}): [
        "Pie dough", "Shortcrust pastry", "Roux",
    ],
    frozenset({"Cream & butter", "Other vegetables"}): [
        "Buttered vegetables", "Sautéed veg in butter",
    ],
    frozenset({"Flours", "Milk"}): [
        "Pancake batter", "Crêpe batter", "Béchamel",
    ],
    frozenset({"Eggs", "Flours"}): [
        "Pasta dough", "Egg noodles", "Pancakes", "Crêpes",
    ],
    frozenset({"Eggs", "Flours", "Milk"}): [
        "Pancakes", "Crêpes", "Waffles", "Yorkshire pudding",
    ],
    frozenset({"Eggs", "Milk"}): [
        "French custard", "Scrambled eggs with milk", "Omelet",
    ],
    frozenset({"Eggs", "Temperate fruits"}): [
        "Apple-egg pancake", "Baked egg with fruit",
    ],
    frozenset({"Eggs", "Nuts"}): [
        "Nut meringue", "Almond macaroon",
    ],
    frozenset({"Cream & butter", "Eggs"}): [
        "Hollandaise sauce", "Egg yolk butter sauce",
    ],
    frozenset({"Cream & butter", "Starchy vegetables"}): [
        "Buttered mashed potatoes", "Pan-fried potatoes",
    ],
    frozenset({"Cream & butter", "Nuts"}): [
        "Buttered nuts", "Brown-butter praline",
    ],
    frozenset({"Cream & butter", "Fresh cheese"}): [
        "Creamy cheese spread", "Ricotta whipped with butter",
    ],
    frozenset({"Milk", "Temperate fruits"}): [
        "Fruit smoothie", "Apple milkshake",
    ],
    frozenset({"Milk", "Nuts"}): [
        "Nut horchata", "Almond milk",
    ],
    frozenset({"Berries", "Cream & butter"}): [
        "Berry butter", "Strawberry cream",
    ],
    frozenset({"Berries", "Milk"}): [
        "Berry smoothie", "Strawberry milk",
    ],
    frozenset({"Nuts", "Temperate fruits"}): [
        "Fruit & nut platter", "Trail mix with apples",
    ],
    frozenset({"Fresh cheese", "Temperate fruits"}): [
        "Ricotta with fruit", "Cottage cheese & peaches",
    ],
    frozenset({"Aged cheese", "Other vegetables"}): [
        "Cheesy roasted veg", "Cheese-topped vegetables",
    ],
    frozenset({"Aged cheese", "Processed meat"}): [
        "Cheese & charcuterie", "Ham & cheese plate",
    ],
    frozenset({"Other vegetables", "Processed meat"}): [
        "Bacon-stewed greens", "Ham & vegetables",
    ],
    frozenset({"Other vegetables", "Refined grains"}): [
        "Vegetable fried rice", "Pasta primavera",
    ],
    frozenset({"Eggs", "Fermented dairy", "Flours"}): [
        "Yogurt pancakes", "Sour cream loaf",
    ],
    frozenset({"Fermented dairy", "Flours"}): [
        "Yogurt flatbread", "Sour cream biscuit",
    ],
    frozenset({"Alcoholic beverages", "Temperate fruits"}): [
        "Sangria", "Mulled apple wine", "Fruit cocktail",
    ],
    frozenset({"Bread & rolls", "Cream & butter"}): [
        "Buttered bread", "Garlic bread",
    ],
    frozenset({"Bread & rolls", "Milk"}): [
        "Bread pudding base", "Milk-soaked bread",
    ],
    frozenset({"Bread & rolls", "Nuts"}): [
        "Nut bread", "Toasted nut crostini",
    ],
    frozenset({"Bread & rolls", "Temperate fruits"}): [
        "Apple bread", "Fruit toast",
    ],
    frozenset({"Bread & rolls", "Cream & butter", "Nuts"}): [
        "Buttered nut bread",
    ],
    frozenset({"Bread & rolls", "Cream & butter", "Milk", "Nuts"}): [
        "Nutty buttered milk bread",
    ],
    frozenset({"Coffee & tea", "Cream & butter"}): [
        "Coffee with cream", "Creamy latte",
    ],
    frozenset({"Coffee & tea", "Milk"}): [
        "Café au lait", "Milk tea",
    ],
    frozenset({"Coffee & tea", "Temperate fruits"}): [
        "Apple-spiced tea", "Fruit-infused tea",
    ],
    frozenset({"Coffee & tea", "Juices"}): [
        "Iced tea with juice",
    ],
    frozenset({"Coffee & tea", "Cream & butter", "Milk"}): [
        "Latte", "Café au lait",
    ],
    frozenset({"Cream & butter", "Refined grains"}): [
        "Buttered pasta", "Buttered rice",
    ],
    frozenset({"Cream & butter", "Whole grains"}): [
        "Buttered brown rice", "Butter-finished oatmeal",
    ],
    frozenset({"Cream & butter", "Poultry"}): [
        "Butter-roasted chicken", "Chicken in butter sauce",
    ],
    frozenset({"Cream & butter", "Legumes"}): [
        "Buttered beans", "Lentils in butter sauce",
    ],
    frozenset({"Cream & butter", "Nut butters"}): [
        "Whipped peanut butter", "Almond butter spread",
    ],
    frozenset({"Cream & butter", "Fermented dairy"}): [
        "Sour cream butter dip",
    ],
    frozenset({"Milk", "Nut butters"}): [
        "Peanut butter milkshake",
    ],
    frozenset({"Nut butters", "Whole grains"}): [
        "Peanut butter oatmeal", "Almond butter on brown rice",
    ],
    frozenset({"Nut butters", "Starchy vegetables"}): [
        "Peanut sweet potato",
    ],
    frozenset({"Eggs", "Nut butters"}): [
        "Peanut butter eggs",
    ],
    frozenset({"Bread & rolls", "Nut butters"}): [
        "Peanut butter sandwich",
    ],
    frozenset({"Legumes", "Other vegetables"}): [
        "Bean & vegetable stew", "Lentil salad",
    ],
    frozenset({"Legumes", "Whole grains"}): [
        "Rice & beans", "Lentil grain bowl",
    ],
    frozenset({"Legumes", "Starchy vegetables"}): [
        "Bean & potato stew",
    ],
    frozenset({"Legumes", "Refined grains"}): [
        "Bean burrito filling", "Rice & beans",
    ],
    frozenset({"Legumes", "Nut butters"}): [
        "Lentil-peanut stew",
    ],
    frozenset({"Legumes", "Milk"}): [
        "Dal makhani",
    ],
    frozenset({"Legumes", "Nuts"}): [
        "Bean & nut salad",
    ],
    frozenset({"Legumes", "Temperate fruits"}): [
        "Bean & apple salad",
    ],
    frozenset({"Aged cheese", "Refined grains"}): [
        "Mac & cheese", "Cacio e pepe",
    ],
    frozenset({"Aged cheese", "Red meat"}): [
        "Cheeseburger", "Steak with parmesan",
    ],
    frozenset({"Aged cheese", "Poultry"}): [
        "Chicken parmesan", "Chicken with cheese sauce",
    ],
    frozenset({"Aged cheese", "Fresh cheese"}): [
        "Three-cheese plate",
    ],
    frozenset({"Aged cheese", "Bread & rolls"}): [
        "Grilled cheese", "Cheese on toast",
    ],
    frozenset({"Aged cheese", "Cream & butter"}): [
        "Cheese fondue base",
    ],
    frozenset({"Aged cheese", "Organ meats"}): [
        "Liver & cheese pâté",
    ],
    frozenset({"Fresh cheese", "Other vegetables"}): [
        "Caprese with veg", "Ricotta-stuffed vegetables",
    ],
    frozenset({"Fresh cheese", "Milk"}): [
        "Paneer in milk", "Cheese in milk sauce",
    ],
    frozenset({"Fresh cheese", "Nuts"}): [
        "Cheese & nut plate",
    ],
    frozenset({"Fresh cheese", "Poultry"}): [
        "Chicken with feta", "Chicken & ricotta",
    ],
    frozenset({"Fresh cheese", "Processed meat"}): [
        "Prosciutto & mozzarella",
    ],
    frozenset({"Fresh cheese", "Red meat"}): [
        "Steak with blue cheese",
    ],
    frozenset({"Fresh cheese", "Refined grains"}): [
        "Cheese ravioli",
    ],
    frozenset({"Fresh cheese", "Nut butters"}): [
        "Ricotta peanut spread",
    ],
    frozenset({"Fresh cheese", "Shellfish"}): [
        "Shrimp & feta",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours"}): [
        "Pound cake", "Shortbread cookies", "Pastry dough", "Pie crust",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Milk"}): [
        "Cake", "Pancakes", "Crêpes", "Muffins", "Waffles",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Temperate fruits"}): [
        "Apple cake", "Apple pie", "Fruit cobbler", "Fruit crumble",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Nuts"}): [
        "Almond cookies", "Pecan shortbread", "Nut cake",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Milk", "Temperate fruits"}): [
        "Apple cake", "Fruit muffins", "Fruit cobbler",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Milk", "Nuts"}): [
        "Nut cake", "Pecan muffins",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Nuts", "Temperate fruits"}): [
        "Apple-pecan cake", "Walnut apple pie",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Milk", "Nuts", "Temperate fruits"}): [
        "Apple-walnut cake", "Fruit-and-nut muffins",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Whole grains"}): [
        "Whole-wheat cookies", "Oat cookies",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Fresh cheese"}): [
        "Cheesecake", "Ricotta cake",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Fermented dairy"}): [
        "Sour cream cake", "Yogurt cake",
    ],
    frozenset({"Cream & butter", "Eggs", "Fermented dairy", "Flours"}): [
        "Sour cream pound cake", "Yogurt loaf",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Starchy vegetables"}): [
        "Sweet potato cake", "Potato pancakes",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Milk", "Starchy vegetables"}): [
        "Sweet potato muffins",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Milk", "Nut butters"}): [
        "Peanut butter cake",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Nut butters"}): [
        "Peanut butter cookies",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Refined grains", "Temperate fruits"}): [
        "Apple pasta dessert",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Fresh cheese", "Nuts"}): [
        "Cheesecake with nut crust",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Fresh cheese", "Temperate fruits"}): [
        "Ricotta apple tart",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Fresh cheese", "Other vegetables"}): [
        "Cheese & veg quiche",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Fresh cheese", "Milk"}): [
        "Cheesecake (creamy)",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Fresh cheese", "Starchy vegetables"}): [
        "Potato-cheese gratin",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Legumes"}): [
        "Lentil-flour cake",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Legumes", "Nut butters"}): [
        "Peanut-lentil bake",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Nuts", "Whole grains"}): [
        "Whole-wheat nut cookies",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Nut butters", "Whole grains"}): [
        "Peanut butter oat cookies",
    ],
    frozenset({"Cream & butter", "Eggs", "Flours", "Milk", "Whole grains"}): [
        "Whole-wheat pancakes",
    ],
    frozenset({"Eggs", "Flours", "Temperate fruits"}): [
        "Apple pancakes", "Fruit clafoutis", "Apple dumplings",
    ],
    frozenset({"Eggs", "Flours", "Nuts"}): [
        "Almond cookies", "Pecan biscotti",
    ],
    frozenset({"Eggs", "Flours", "Nuts", "Temperate fruits"}): [
        "Apple-walnut muffin", "Pecan-pear bread",
    ],
    frozenset({"Eggs", "Flours", "Milk", "Temperate fruits"}): [
        "Apple pancakes",
    ],
    frozenset({"Eggs", "Flours", "Milk", "Nuts"}): [
        "Pecan pancakes",
    ],
    frozenset({"Eggs", "Flours", "Milk", "Nuts", "Temperate fruits"}): [
        "Walnut-apple pancakes",
    ],
    frozenset({"Eggs", "Flours", "Whole grains"}): [
        "Whole-wheat pancakes", "Oat cookies",
    ],
    frozenset({"Eggs", "Flours", "Starchy vegetables"}): [
        "Potato pancakes", "Sweet-potato fritter",
    ],
    frozenset({"Eggs", "Flours", "Other vegetables"}): [
        "Vegetable fritters", "Zucchini pancakes",
    ],
    frozenset({"Eggs", "Flours", "Other vegetables", "Temperate fruits"}): [
        "Apple-zucchini bread",
    ],
    frozenset({"Eggs", "Flours", "Nuts", "Other vegetables"}): [
        "Pecan-zucchini bread",
    ],
    frozenset({"Eggs", "Flours", "Nuts", "Starchy vegetables"}): [
        "Sweet potato nut bread",
    ],
    frozenset({"Eggs", "Flours", "Nuts", "Starchy vegetables", "Temperate fruits"}): [
        "Apple-walnut sweet-potato bread",
    ],
    frozenset({"Eggs", "Flours", "Nuts", "Whole grains"}): [
        "Oat-nut cookies",
    ],
    frozenset({"Eggs", "Flours", "Nut butters"}): [
        "Peanut butter cookies",
    ],
    frozenset({"Eggs", "Flours", "Fresh cheese"}): [
        "Cheese soufflé", "Ricotta-egg pancakes",
    ],
    frozenset({"Eggs", "Flours", "Seeds"}): [
        "Sesame crackers",
    ],
    frozenset({"Eggs", "Flours", "Legumes", "Temperate fruits"}): [
        "Lentil-apple cake",
    ],
    frozenset({"Eggs", "Flours", "Nuts", "Other vegetables", "Temperate fruits"}): [
        "Apple-zucchini-walnut bread",
    ],
    frozenset({"Eggs", "Flours", "Other vegetables", "Starchy vegetables"}): [
        "Veg & potato fritters",
    ],
    frozenset({"Eggs", "Flours", "Starchy vegetables", "Temperate fruits"}): [
        "Sweet-potato apple bread",
    ],
    frozenset({"Eggs", "Fermented dairy", "Flours", "Temperate fruits"}): [
        "Yogurt apple cake",
    ],
    frozenset({"Eggs", "Fermented dairy", "Flours", "Whole grains"}): [
        "Yogurt whole-wheat muffins",
    ],
    frozenset({"Eggs", "Fermented dairy", "Flours", "Nuts"}): [
        "Yogurt pecan muffins",
    ],
    frozenset({"Eggs", "Fermented dairy", "Flours", "Nuts", "Temperate fruits"}): [
        "Yogurt apple-walnut muffins",
    ],
    frozenset({"Cream & butter", "Eggs", "Fermented dairy", "Flours", "Nuts"}): [
        "Sour cream nut cake",
    ],
    frozenset({"Cream & butter", "Eggs", "Fermented dairy", "Flours", "Nuts", "Temperate fruits"}): [
        "Sour cream apple-walnut cake",
    ],
    frozenset({"Cream & butter", "Eggs", "Fermented dairy", "Flours", "Temperate fruits"}): [
        "Sour cream apple cake",
    ],
    frozenset({"Dried fruits", "Eggs", "Flours"}): [
        "Raisin scones", "Date cake",
    ],
    frozenset({"Dried fruits", "Eggs", "Flours", "Temperate fruits"}): [
        "Apple-raisin muffins",
    ],
    frozenset({"Dried fruits", "Eggs", "Flours", "Nuts"}): [
        "Date-walnut cake",
    ],
    frozenset({"Dried fruits", "Eggs", "Flours", "Milk"}): [
        "Raisin bread pudding",
    ],
    frozenset({"Dried fruits", "Eggs", "Flours", "Whole grains"}): [
        "Raisin oat cookies",
    ],
    frozenset({"Dried fruits", "Eggs", "Flours", "Nuts", "Starchy vegetables"}): [
        "Date-nut sweet potato bread",
    ],
    frozenset({"Dried fruits", "Eggs", "Flours", "Nuts", "Temperate fruits"}): [
        "Date-walnut apple cake",
    ],
    frozenset({"Dried fruits", "Eggs", "Flours", "Other vegetables"}): [
        "Carrot-raisin cake",
    ],
    frozenset({"Dried fruits", "Eggs", "Flours", "Other vegetables", "Temperate fruits"}): [
        "Carrot-raisin-apple cake",
    ],
    frozenset({"Dried fruits", "Eggs", "Flours", "Starchy vegetables"}): [
        "Sweet potato raisin bread",
    ],
    frozenset({"Dried fruits", "Eggs", "Flours", "Nuts", "Other vegetables"}): [
        "Carrot-walnut-raisin cake",
    ],
    frozenset({"Dried fruits", "Eggs", "Fermented dairy", "Flours"}): [
        "Yogurt raisin cake",
    ],
    frozenset({"Dried fruits", "Eggs", "Flours", "Nuts", "Starchy vegetables", "Temperate fruits"}): [
        "Date-walnut apple sweet-potato cake",
    ],
    frozenset({"Dried fruits", "Eggs", "Milk", "Whole grains"}): [
        "Raisin oatmeal",
    ],
    frozenset({"Dried fruits", "Eggs", "Flours", "Milk", "Whole grains"}): [
        "Raisin oat bread",
    ],
    frozenset({"Dried fruits", "Eggs", "Nuts", "Whole grains"}): [
        "Date-nut granola",
    ],
    frozenset({"Dried fruits", "Eggs", "Temperate fruits"}): [
        "Raisin apple compote",
    ],
    frozenset({"Cream & butter", "Dried fruits", "Eggs", "Flours"}): [
        "Raisin pound cake",
    ],
    frozenset({"Cream & butter", "Dried fruits", "Eggs", "Flours", "Nuts"}): [
        "Date-walnut butter cake",
    ],
    frozenset({"Cream & butter", "Dried fruits", "Eggs", "Flours", "Temperate fruits"}): [
        "Apple-raisin butter cake",
    ],
    frozenset({"Cream & butter", "Dried fruits", "Eggs", "Flours", "Milk"}): [
        "Raisin bread pudding",
    ],
    frozenset({"Cream & butter", "Dried fruits", "Eggs", "Flours", "Milk", "Nuts"}): [
        "Date-pecan bread pudding",
    ],
    frozenset({"Cream & butter", "Dried fruits", "Eggs", "Flours", "Nuts", "Temperate fruits"}): [
        "Apple-walnut-raisin cake",
    ],
    frozenset({"Cream & butter", "Dried fruits", "Eggs", "Flours", "Nuts", "Whole grains"}): [
        "Date-nut whole-wheat cake",
    ],
    frozenset({"Cream & butter", "Dried fruits", "Eggs", "Flours", "Whole grains"}): [
        "Whole-wheat raisin bread",
    ],
    frozenset({"Cream & butter", "Dried fruits", "Eggs", "Fermented dairy", "Flours"}): [
        "Sour cream raisin cake",
    ],
    frozenset({"Cream & butter", "Dried fruits", "Eggs", "Fermented dairy", "Flours", "Nuts", "Temperate fruits"}): [
        "Sour cream apple-walnut-raisin cake",
    ],
    frozenset({"Cream & butter", "Dried fruits", "Eggs", "Nuts", "Whole grains"}): [
        "Date-nut granola bars",
    ],

    # ----- Berry / cream / butter / sweet shapes -----
    frozenset({"Berries", "Cream & butter", "Temperate fruits"}): [
        "Strawberry-apple compote",
    ],
    frozenset({"Berries", "Cream & butter"}): [
        "Strawberries with cream",
    ],
    frozenset({"Berries", "Cream & butter", "Eggs", "Flours", "Milk"}): [
        "Berry pancakes",
    ],
    frozenset({"Berries", "Cream & butter", "Eggs", "Flours"}): [
        "Berry shortcake",
    ],
    frozenset({"Berries", "Cream & butter", "Eggs", "Flours", "Temperate fruits"}): [
        "Berry-apple cobbler",
    ],
    frozenset({"Berries", "Cream & butter", "Eggs", "Flours", "Nuts"}): [
        "Berry-pecan cake",
    ],
    frozenset({"Berries", "Cream & butter", "Eggs", "Flours", "Milk", "Temperate fruits"}): [
        "Berry apple muffins",
    ],
    frozenset({"Berries", "Cream & butter", "Eggs", "Flours", "Nuts", "Temperate fruits"}): [
        "Berry apple-walnut cake",
    ],
    frozenset({"Berries", "Cream & butter", "Fresh cheese", "Temperate fruits"}): [
        "Berry-ricotta dessert",
    ],
    frozenset({"Berries", "Cream & butter", "Fresh cheese", "Nuts", "Temperate fruits"}): [
        "Berry cheesecake with nuts",
    ],
    frozenset({"Berries", "Cream & butter", "Eggs"}): [
        "Berry curd",
    ],
    frozenset({"Berries", "Cream & butter", "Eggs", "Temperate fruits"}): [
        "Berry-apple curd",
    ],
    frozenset({"Berries", "Cream & butter", "Eggs", "Fermented dairy", "Flours"}): [
        "Yogurt berry cake",
    ],
    frozenset({"Berries", "Cream & butter", "Nuts", "Temperate fruits"}): [
        "Berry-nut apple crisp",
    ],
    frozenset({"Berries", "Cream & butter", "Flours"}): [
        "Berry scones",
    ],
    frozenset({"Berries", "Cream & butter", "Flours", "Milk"}): [
        "Berry biscuit shortcake",
    ],
    frozenset({"Berries", "Cream & butter", "Milk"}): [
        "Strawberry cream sauce",
    ],
    frozenset({"Berries", "Cream & butter", "Eggs", "Flours", "Milk", "Temperate fruits"}): [
        "Berry-apple muffins",
    ],

    # ----- Berries x other -----
    frozenset({"Berries", "Eggs"}): ["Berry meringue"],
    frozenset({"Berries", "Eggs", "Flours"}): ["Berry pancakes"],
    frozenset({"Berries", "Eggs", "Flours", "Milk"}): ["Berry crepes"],
    frozenset({"Berries", "Eggs", "Flours", "Temperate fruits"}): ["Berry apple pancakes"],
    frozenset({"Berries", "Eggs", "Flours", "Nuts"}): ["Berry-pecan muffins"],
    frozenset({"Berries", "Eggs", "Flours", "Nuts", "Temperate fruits"}): ["Berry-walnut apple bread"],
    frozenset({"Berries", "Fresh cheese"}): ["Berry & cheese plate"],
    frozenset({"Berries", "Fresh cheese", "Temperate fruits"}): ["Berry ricotta with fruit"],
    frozenset({"Berries", "Fresh cheese", "Nuts", "Temperate fruits"}): ["Berry-nut ricotta plate"],
    frozenset({"Berries", "Yogurt"}): ["Berry yogurt"],
    frozenset({"Berries", "Temperate fruits", "Yogurt"}): ["Berry-apple yogurt parfait"],
    frozenset({"Berries", "Milk", "Temperate fruits", "Yogurt"}): ["Berry yogurt smoothie"],
    frozenset({"Berries", "Milk", "Temperate fruits"}): ["Berry smoothie with fruit"],
    frozenset({"Berries", "Milk", "Nuts", "Temperate fruits"}): ["Berry-almond smoothie"],
    frozenset({"Berries", "Soft drinks", "Temperate fruits"}): ["Berry fruit punch"],
    frozenset({"Berries", "Juices", "Temperate fruits"}): ["Berry juice spritzer"],
    frozenset({"Alcoholic beverages", "Berries"}): ["Berry cocktail"],
    frozenset({"Alcoholic beverages", "Berries", "Temperate fruits"}): ["Berry sangria"],
    frozenset({"Berries", "Nuts"}): ["Berry-nut snack mix"],
    frozenset({"Berries", "Nuts", "Temperate fruits"}): ["Berry-nut fruit bowl"],
    frozenset({"Berries", "Bread & rolls"}): ["Strawberry toast"],
    frozenset({"Berries", "Bread & rolls", "Cream & butter"}): ["Berry buttered toast"],
    frozenset({"Berries", "Bread & rolls", "Cream & butter", "Eggs", "Fresh cheese"}): ["Berry French toast with cheese"],
    frozenset({"Berries", "Bread & rolls", "Cream & butter", "Fresh cheese", "Temperate fruits"}): ["Berry-fruit cheese toast"],
    frozenset({"Berries", "Bread & rolls", "Fresh cheese"}): ["Berry cheese toast"],
    frozenset({"Berries", "Bread & rolls", "Fresh cheese", "Temperate fruits"}): ["Berry fruit toast"],
    frozenset({"Berries", "Other vegetables"}): ["Berry & vegetable salad"],
    frozenset({"Berries", "Other vegetables", "Temperate fruits"}): ["Berry fruit-veg salad"],
    frozenset({"Berries", "Nuts", "Other vegetables", "Temperate fruits"}): ["Berry-nut fruit-veg salad"],
    frozenset({"Berries", "Dried fruits", "Temperate fruits"}): ["Berry & dried-fruit mix"],
    frozenset({"Berries", "Organ meats", "Temperate fruits"}): ["Liver with berry-fruit sauce"],

    # ----- Vegetable + animal protein shapes -----
    frozenset({"Other vegetables", "Red meat", "Starchy vegetables"}): [
        "Beef stew", "Pot roast with potatoes", "Shepherd's pie",
    ],
    frozenset({"Other vegetables", "Red meat", "Whole grains"}): [
        "Beef & brown rice", "Beef quinoa bowl",
    ],
    frozenset({"Other vegetables", "Red meat", "Refined grains"}): [
        "Beef stir-fry with rice", "Beef pasta",
    ],
    frozenset({"Other vegetables", "Red meat", "Temperate fruits"}): [
        "Beef with apples", "Pork & pear",
    ],
    frozenset({"Other vegetables", "Poultry", "Temperate fruits"}): [
        "Chicken with apples",
    ],
    frozenset({"Other vegetables", "Poultry", "Starchy vegetables"}): [
        "Chicken & potatoes",
    ],
    frozenset({"Other vegetables", "Poultry", "Whole grains"}): [
        "Chicken brown-rice bowl",
    ],
    frozenset({"Other vegetables", "Poultry", "Refined grains"}): [
        "Chicken fried rice", "Chicken pasta",
    ],
    frozenset({"Other vegetables", "Poultry", "Red meat"}): [
        "Mixed-meat stew",
    ],
    frozenset({"Other vegetables", "Poultry", "Red meat", "Starchy vegetables"}): [
        "Mixed meat & potato stew",
    ],
    frozenset({"Other vegetables", "Poultry", "Red meat", "Whole grains"}): [
        "Mixed-meat grain bowl",
    ],
    frozenset({"Other vegetables", "Processed meat", "Starchy vegetables"}): [
        "Bacon hash",
    ],
    frozenset({"Other vegetables", "Processed meat", "Refined grains"}): [
        "Ham fried rice",
    ],
    frozenset({"Other vegetables", "Processed meat", "Whole grains"}): [
        "Bacon brown-rice bowl",
    ],
    frozenset({"Other vegetables", "Processed meat", "Red meat"}): [
        "Bacon-wrapped meatloaf",
    ],
    frozenset({"Other vegetables", "Shellfish"}): [
        "Shrimp stir-fry",
    ],
    frozenset({"Other vegetables", "Shellfish", "Temperate fruits"}): [
        "Shrimp with apple slaw",
    ],
    frozenset({"Other vegetables", "Refined grains", "Shellfish"}): [
        "Shrimp fried rice",
    ],
    frozenset({"Alcoholic beverages", "Other vegetables", "Refined grains", "Shellfish"}): [
        "Drunken shrimp risotto",
    ],
    frozenset({"Cream & butter", "Other vegetables", "Shellfish"}): [
        "Shrimp scampi",
    ],
    frozenset({"Fresh cheese", "Other vegetables", "Shellfish"}): [
        "Shrimp with feta",
    ],
    frozenset({"Alcoholic beverages", "Other vegetables", "Shellfish"}): [
        "Wine-steamed shellfish",
    ],
    frozenset({"Other vegetables", "Spice blends"}): [
        "Spiced vegetable curry",
    ],
    frozenset({"Other vegetables", "Spice blends", "Temperate fruits"}): [
        "Spiced fruit-vegetable curry",
    ],
    frozenset({"Other vegetables", "Red meat", "Spice blends"}): [
        "Beef curry",
    ],
    frozenset({"Other vegetables", "Red meat", "Spice blends", "Starchy vegetables", "Legumes"}): [
        "Beef-lentil curry with potatoes",
    ],
    frozenset({"Other vegetables", "Refined grains", "Spice blends"}): [
        "Curry rice",
    ],

    # ----- Leafy greens + protein -----
    frozenset({"Leafy greens", "Other vegetables", "Temperate fruits"}): [
        "Fruity green salad",
    ],
    frozenset({"Leafy greens", "Temperate fruits"}): [
        "Apple-spinach salad",
    ],
    frozenset({"Leafy greens", "Other vegetables", "Starchy vegetables"}): [
        "Greens & potato salad",
    ],
    frozenset({"Leafy greens", "Other vegetables", "Red meat"}): [
        "Beef & greens salad",
    ],
    frozenset({"Leafy greens", "Other vegetables", "Red meat", "Whole grains"}): [
        "Beef grain bowl with greens",
    ],
    frozenset({"Leafy greens", "Other vegetables", "Red meat", "Starchy vegetables"}): [
        "Beef stew with greens",
    ],
    frozenset({"Leafy greens", "Other vegetables", "Processed meat"}): [
        "Bacon & spinach salad",
    ],
    frozenset({"Leafy greens", "Other vegetables", "Processed meat", "Red meat"}): [
        "Bacon-beef salad",
    ],
    frozenset({"Leafy greens", "Other vegetables", "Red meat", "Temperate fruits"}): [
        "Beef-apple salad",
    ],
    frozenset({"Leafy greens", "Other vegetables", "Refined grains"}): [
        "Pasta salad with greens",
    ],
    frozenset({"Leafy greens", "Other vegetables", "Seeds"}): [
        "Sunflower-seed salad",
    ],
    frozenset({"Leafy greens", "Legumes", "Other vegetables", "Processed meat", "Red meat"}): [
        "Lentil-meat salad with greens",
    ],
    frozenset({"Leafy greens", "Legumes", "Other vegetables", "Red meat"}): [
        "Beef-lentil green salad",
    ],
    frozenset({"Leafy greens", "Red meat"}): [
        "Steak salad",
    ],

    # ----- Bread & rolls combos -----
    frozenset({"Bread & rolls", "Cream & butter", "Eggs"}): ["French toast"],
    frozenset({"Bread & rolls", "Cream & butter", "Eggs", "Flours"}): ["French toast with batter"],
    frozenset({"Bread & rolls", "Cream & butter", "Eggs", "Flours", "Milk"}): ["French toast"],
    frozenset({"Bread & rolls", "Cream & butter", "Eggs", "Flours", "Nuts"}): ["Nutty French toast"],
    frozenset({"Bread & rolls", "Cream & butter", "Eggs", "Milk"}): ["Bread pudding"],
    frozenset({"Bread & rolls", "Cream & butter", "Eggs", "Milk", "Nuts"}): ["Nutty bread pudding"],
    frozenset({"Bread & rolls", "Cream & butter", "Eggs", "Milk", "Temperate fruits"}): ["Apple French toast"],
    frozenset({"Bread & rolls", "Cream & butter", "Eggs", "Nuts"}): ["Nutty stuffed bread"],
    frozenset({"Bread & rolls", "Cream & butter", "Eggs", "Temperate fruits"}): ["Apple French toast"],
    frozenset({"Bread & rolls", "Cream & butter", "Eggs", "Fresh cheese"}): ["Cheese-stuffed French toast"],
    frozenset({"Bread & rolls", "Cream & butter", "Eggs", "Fresh cheese", "Temperate fruits"}): ["Cheesy apple French toast"],
    frozenset({"Bread & rolls", "Cream & butter", "Eggs", "Nuts", "Temperate fruits"}): ["Apple-walnut French toast"],
    frozenset({"Bread & rolls", "Cream & butter", "Fresh cheese"}): ["Cheese-stuffed bread"],
    frozenset({"Bread & rolls", "Cream & butter", "Fresh cheese", "Temperate fruits"}): ["Cheese-apple toast"],
    frozenset({"Bread & rolls", "Cream & butter", "Flours", "Temperate fruits"}): ["Apple bread roll"],
    frozenset({"Bread & rolls", "Cream & butter", "Legumes"}): ["Bean-stuffed bread"],
    frozenset({"Bread & rolls", "Cream & butter", "Milk"}): ["Buttered bread with milk"],
    frozenset({"Bread & rolls", "Cream & butter", "Milk", "Temperate fruits"}): ["Apple cinnamon roll"],
    frozenset({"Bread & rolls", "Cream & butter", "Nut butters"}): ["Peanut butter sandwich"],
    frozenset({"Bread & rolls", "Cream & butter", "Nuts", "Temperate fruits"}): ["Nutty apple bread"],
    frozenset({"Bread & rolls", "Cream & butter", "Other vegetables"}): ["Veg-stuffed bread"],
    frozenset({"Bread & rolls", "Cream & butter", "Poultry"}): ["Chicken sandwich"],
    frozenset({"Bread & rolls", "Cream & butter", "Poultry", "Seeds"}): ["Seeded chicken sandwich"],
    frozenset({"Bread & rolls", "Cream & butter", "Other vegetables", "Poultry"}): ["Chicken sandwich with veg"],
    frozenset({"Bread & rolls", "Dried fruits", "Milk", "Nuts", "Temperate fruits"}): ["Fruit & nut bread"],
    frozenset({"Bread & rolls", "Eggs", "Flours", "Milk", "Temperate fruits"}): ["Apple bread pudding"],
    frozenset({"Bread & rolls", "Eggs", "Fresh cheese"}): ["Egg & cheese sandwich"],
    frozenset({"Bread & rolls", "Eggs", "Fresh cheese", "Temperate fruits"}): ["Egg-cheese-apple sandwich"],
    frozenset({"Bread & rolls", "Eggs", "Milk", "Nuts"}): ["French toast with nuts"],
    frozenset({"Bread & rolls", "Eggs", "Milk", "Starchy vegetables"}): ["Bread & potato strata"],
    frozenset({"Bread & rolls", "Eggs", "Milk", "Temperate fruits"}): ["Apple French toast"],
    frozenset({"Bread & rolls", "Eggs", "Nuts"}): ["Nutty egg toast"],
    frozenset({"Bread & rolls", "Eggs", "Nuts", "Temperate fruits"}): ["Apple-walnut egg toast"],
    frozenset({"Bread & rolls", "Eggs", "Other vegetables", "Red meat"}): ["Steak-egg sandwich"],
    frozenset({"Bread & rolls", "Eggs", "Temperate fruits"}): ["Apple egg toast"],
    frozenset({"Bread & rolls", "Fresh cheese"}): ["Cheese sandwich"],
    frozenset({"Bread & rolls", "Fresh cheese", "Milk"}): ["Cheese toast with milk"],
    frozenset({"Bread & rolls", "Fresh cheese", "Milk", "Nut butters"}): ["Peanut-cheese milk toast"],
    frozenset({"Bread & rolls", "Fresh cheese", "Milk", "Temperate fruits"}): ["Cheese-apple milk toast"],
    frozenset({"Bread & rolls", "Fresh cheese", "Nut butters"}): ["Peanut-cheese sandwich"],
    frozenset({"Bread & rolls", "Fresh cheese", "Other vegetables"}): ["Cheese-veg sandwich"],
    frozenset({"Bread & rolls", "Fresh cheese", "Processed meat"}): ["Ham & cheese sandwich"],
    frozenset({"Bread & rolls", "Fresh cheese", "Temperate fruits"}): ["Cheese-apple sandwich"],
    frozenset({"Bread & rolls", "Juices", "Milk"}): ["Toast with juice & milk"],
    frozenset({"Bread & rolls", "Milk", "Nuts"}): ["Nutty milk bread"],
    frozenset({"Bread & rolls", "Milk", "Nuts", "Temperate fruits"}): ["Apple-walnut milk bread"],
    frozenset({"Bread & rolls", "Milk", "Temperate fruits"}): ["Apple milk toast"],
    frozenset({"Bread & rolls", "Nuts", "Temperate fruits"}): ["Apple-nut bread"],
    frozenset({"Bread & rolls", "Nut butters"}): ["Peanut butter on bread"],
    frozenset({"Bread & rolls", "Other vegetables"}): ["Veg sandwich"],
    frozenset({"Bread & rolls", "Other vegetables", "Processed cheese"}): ["American-cheese veg sandwich"],
    frozenset({"Bread & rolls", "Other vegetables", "Processed cheese", "Red meat"}): ["Cheesesteak"],
    frozenset({"Bread & rolls", "Other vegetables", "Poultry"}): ["Chicken sandwich"],
    frozenset({"Bread & rolls", "Other vegetables", "Poultry", "Processed cheese"}): ["Chicken-cheese sandwich"],
    frozenset({"Bread & rolls", "Other vegetables", "Red meat"}): ["Beef sandwich"],
    frozenset({"Bread & rolls", "Poultry"}): ["Chicken sandwich"],
    frozenset({"Bread & rolls", "Processed meat"}): ["Ham sandwich"],
    frozenset({"Alcoholic beverages", "Bread & rolls"}): ["Beer & pretzels"],
    frozenset({"Alcoholic beverages", "Bread & rolls", "Nuts"}): ["Beer with nuts & bread"],

    # ----- Aged cheese combos -----
    frozenset({"Aged cheese", "Bread & rolls", "Cream & butter", "Other vegetables"}): ["Grilled cheese with veg"],
    frozenset({"Aged cheese", "Bread & rolls", "Cream & butter", "Flours", "Temperate fruits"}): ["Apple-cheese tart"],
    frozenset({"Aged cheese", "Bread & rolls", "Cream & butter", "Leafy greens", "Other vegetables", "Processed meat", "Seeds"}): ["Loaded green sandwich"],
    frozenset({"Aged cheese", "Bread & rolls", "Cream & butter", "Other vegetables", "Red meat"}): ["Beef-cheese sandwich"],
    frozenset({"Aged cheese", "Bread & rolls", "Cruciferous vegetables", "Eggs", "Other vegetables"}): ["Veggie cheese strata"],
    frozenset({"Aged cheese", "Bread & rolls", "Fresh cheese"}): ["Three-cheese toast"],
    frozenset({"Aged cheese", "Bread & rolls", "Flours", "Temperate fruits"}): ["Apple cheese bread"],
    frozenset({"Aged cheese", "Bread & rolls", "Leafy greens", "Other vegetables"}): ["Cheese-greens sandwich"],
    frozenset({"Aged cheese", "Bread & rolls", "Leafy greens", "Other vegetables", "Processed meat", "Seeds"}): ["Loaded sub sandwich"],
    frozenset({"Aged cheese", "Bread & rolls", "Leafy greens", "Other vegetables", "Red meat"}): ["Roast beef sub"],
    frozenset({"Aged cheese", "Bread & rolls", "Other vegetables"}): ["Cheese veg sandwich"],
    frozenset({"Aged cheese", "Bread & rolls", "Other vegetables", "Poultry"}): ["Chicken cheese sandwich"],
    frozenset({"Aged cheese", "Bread & rolls", "Other vegetables", "Red meat"}): ["Beef cheese sandwich"],
    frozenset({"Aged cheese", "Bread & rolls", "Other vegetables", "Processed meat"}): ["Ham & cheese sub"],
    frozenset({"Aged cheese", "Bread & rolls", "Processed meat"}): ["Ham & cheese on bread"],
    frozenset({"Aged cheese", "Cream & butter", "Flours"}): ["Cheese biscuits"],
    frozenset({"Aged cheese", "Cream & butter", "Flours", "Milk", "Refined grains"}): ["Mac & cheese baked"],
    frozenset({"Aged cheese", "Cream & butter", "Flours", "Milk", "Other vegetables", "Starchy vegetables"}): ["Cheesy veggie potato gratin"],
    frozenset({"Aged cheese", "Cream & butter", "Flours", "Other vegetables"}): ["Cheese-veg casserole"],
    frozenset({"Aged cheese", "Cream & butter", "Flours", "Milk", "Other vegetables", "Processed meat", "Starchy vegetables"}): ["Cheesy ham potato bake"],
    frozenset({"Aged cheese", "Cream & butter", "Fresh cheese", "Other vegetables"}): ["Two-cheese baked veg"],
    frozenset({"Aged cheese", "Cream & butter", "Milk", "Other vegetables", "Starchy vegetables"}): ["Cheesy mashed potatoes"],
    frozenset({"Aged cheese", "Cream & butter", "Other vegetables"}): ["Cheesy sautéed veg"],
    frozenset({"Aged cheese", "Cream & butter", "Other vegetables", "Poultry"}): ["Chicken with cheese sauce"],
    frozenset({"Aged cheese", "Cream & butter", "Other vegetables", "Poultry", "Refined grains"}): ["Chicken pasta bake"],
    frozenset({"Aged cheese", "Cream & butter", "Other vegetables", "Poultry", "Starchy vegetables"}): ["Cheesy chicken potato bake"],
    frozenset({"Aged cheese", "Cream & butter", "Other vegetables", "Poultry", "Whole grains"}): ["Chicken cheese grain bowl"],
    frozenset({"Aged cheese", "Cream & butter", "Other vegetables", "Processed meat", "Starchy vegetables"}): ["Cheesy bacon potatoes"],
    frozenset({"Aged cheese", "Cream & butter", "Other vegetables", "Refined grains"}): ["Cheesy pasta with veg"],
    frozenset({"Aged cheese", "Cream & butter", "Other vegetables", "Starchy vegetables"}): ["Cheesy potato bake"],
    frozenset({"Aged cheese", "Cream & butter", "Other vegetables", "Whole grains"}): ["Cheesy whole-grain bowl"],
    frozenset({"Aged cheese", "Cream & butter", "Refined grains"}): ["Cacio e pepe"],
    frozenset({"Aged cheese", "Cream & butter", "Starchy vegetables"}): ["Cheesy mashed potatoes"],
    frozenset({"Aged cheese", "Eggs", "Fresh cheese", "Other vegetables", "Red meat", "Refined grains"}): ["Beef lasagna"],
    frozenset({"Aged cheese", "Eggs", "Leafy greens", "Milk", "Other vegetables", "Processed meat", "Refined grains"}): ["Carbonara-style bake"],
    frozenset({"Aged cheese", "Eggs", "Leafy greens", "Milk", "Processed meat", "Refined grains"}): ["Carbonara"],
    frozenset({"Aged cheese", "Eggs", "Leafy greens", "Milk", "Red meat", "Refined grains"}): ["Beef pasta bake"],
    frozenset({"Aged cheese", "Eggs", "Milk", "Other vegetables", "Processed meat"}): ["Bacon quiche"],
    frozenset({"Aged cheese", "Eggs", "Milk", "Processed meat", "Refined grains"}): ["Bacon mac & cheese"],
    frozenset({"Aged cheese", "Eggs", "Other vegetables"}): ["Veggie omelet with cheese"],
    frozenset({"Aged cheese", "Cruciferous vegetables", "Eggs", "Other vegetables"}): ["Broccoli cheese omelet"],
    frozenset({"Aged cheese", "Cruciferous vegetables", "Leafy greens", "Other vegetables", "Processed meat"}): ["Loaded broccoli salad"],
    frozenset({"Aged cheese", "Cruciferous vegetables", "Other vegetables", "Processed meat"}): ["Bacon broccoli cheese"],
    frozenset({"Aged cheese", "Fresh cheese"}): ["Two-cheese plate"],
    frozenset({"Aged cheese", "Fresh cheese", "Nuts", "Other vegetables"}): ["Cheese-nut veg plate"],
    frozenset({"Aged cheese", "Fresh cheese", "Other vegetables"}): ["Two-cheese veg bake"],
    frozenset({"Aged cheese", "Fresh cheese", "Other vegetables", "Processed meat"}): ["Loaded ham cheese bake"],
    frozenset({"Aged cheese", "Fresh cheese", "Other vegetables", "Red meat"}): ["Beef cheese casserole"],
    frozenset({"Aged cheese", "Fresh cheese", "Other vegetables", "Red meat", "Refined grains"}): ["Beef pasta bake"],
    frozenset({"Aged cheese", "Fresh cheese", "Poultry"}): ["Chicken cheese roll"],
    frozenset({"Aged cheese", "Fresh cheese", "Red meat", "Refined grains"}): ["Beef lasagna"],
    frozenset({"Aged cheese", "Fresh cheese", "Refined grains"}): ["Cheese ravioli"],
    frozenset({"Aged cheese", "Leafy greens", "Legumes", "Other vegetables", "Processed meat"}): ["Loaded bean cheese salad"],
    frozenset({"Aged cheese", "Leafy greens", "Other vegetables"}): ["Cheese green salad"],
    frozenset({"Aged cheese", "Nuts", "Other vegetables"}): ["Cheese & nut salad"],
    frozenset({"Aged cheese", "Organ meats"}): ["Liver pâté with cheese"],
    frozenset({"Aged cheese", "Organ meats", "Other vegetables"}): ["Liver casserole with cheese"],
    frozenset({"Aged cheese", "Other vegetables", "Poultry"}): ["Chicken parmesan"],
    frozenset({"Aged cheese", "Other vegetables", "Poultry", "Refined grains"}): ["Chicken parm pasta"],
    frozenset({"Aged cheese", "Other vegetables", "Poultry", "Whole grains"}): ["Chicken cheese grain bowl"],
    frozenset({"Aged cheese", "Other vegetables", "Processed meat"}): ["Bacon-cheese veg bake"],
    frozenset({"Aged cheese", "Other vegetables", "Processed meat", "Refined grains"}): ["Ham mac & cheese"],
    frozenset({"Aged cheese", "Other vegetables", "Processed meat", "Starchy vegetables"}): ["Cheesy bacon potato bake"],
    frozenset({"Aged cheese", "Other vegetables", "Red meat"}): ["Beef cheese bowl"],
    frozenset({"Aged cheese", "Other vegetables", "Red meat", "Refined grains"}): ["Beef pasta bake"],
    frozenset({"Aged cheese", "Other vegetables", "Red meat", "Starchy vegetables"}): ["Beef potato cheese bake"],
    frozenset({"Aged cheese", "Other vegetables", "Red meat", "Whole grains"}): ["Beef cheese grain bowl"],
    frozenset({"Aged cheese", "Other vegetables", "Refined grains"}): ["Cheese pasta"],
    frozenset({"Aged cheese", "Other vegetables", "Refined grains", "Temperate fruits"}): ["Pasta with apple & cheese"],
    frozenset({"Aged cheese", "Other vegetables", "Starchy vegetables"}): ["Cheesy potato gratin"],
    frozenset({"Aged cheese", "Other vegetables", "Temperate fruits"}): ["Apple cheese salad"],
    frozenset({"Aged cheese", "Poultry", "Refined grains"}): ["Chicken cheese pasta"],
    frozenset({"Aged cheese", "Poultry"}): ["Cheesy chicken"],
    frozenset({"Aged cheese", "Red meat"}): ["Steak with parmesan"],
    frozenset({"Aged cheese", "Refined grains"}): ["Mac & cheese"],
    frozenset({"Alcoholic beverages", "Aged cheese", "Cream & butter", "Poultry"}): ["Coq au vin"],

    # ----- Beverage combos -----
    frozenset({"Alcoholic beverages", "Coffee & tea"}): ["Irish coffee"],
    frozenset({"Alcoholic beverages", "Coffee & tea", "Cream & butter"}): ["Boozy creamy coffee"],
    frozenset({"Alcoholic beverages", "Cream & butter"}): ["Buttered rum"],
    frozenset({"Alcoholic beverages", "Cream & butter", "Eggs"}): ["Eggnog"],
    frozenset({"Alcoholic beverages", "Cream & butter", "Eggs", "Milk"}): ["Brandy eggnog"],
    frozenset({"Alcoholic beverages", "Cream & butter", "Milk"}): ["Spiked hot cocoa"],
    frozenset({"Alcoholic beverages", "Cream & butter", "Nuts"}): ["Boozy nut spread"],
    frozenset({"Alcoholic beverages", "Cream & butter", "Other vegetables", "Poultry"}): ["Wine-braised chicken"],
    frozenset({"Alcoholic beverages", "Cream & butter", "Temperate fruits"}): ["Apple-brandy butter"],
    frozenset({"Alcoholic beverages", "Eggs", "Temperate fruits"}): ["Apple-bourbon custard"],
    frozenset({"Alcoholic beverages", "Flours"}): ["Beer batter"],
    frozenset({"Alcoholic beverages", "Flours", "Other vegetables", "Poultry"}): ["Beer-battered chicken"],
    frozenset({"Alcoholic beverages", "Flours", "Other vegetables", "Red meat", "Starchy vegetables"}): ["Beer-beef potato stew"],
    frozenset({"Alcoholic beverages", "Juices"}): ["Mimosa"],
    frozenset({"Alcoholic beverages", "Juices", "Temperate fruits"}): ["Apple mimosa"],
    frozenset({"Alcoholic beverages", "Milk"}): ["White Russian"],
    frozenset({"Alcoholic beverages", "Nuts", "Temperate fruits"}): ["Apple-nut sangria"],
    frozenset({"Alcoholic beverages", "Other vegetables"}): ["Bloody Mary"],
    frozenset({"Alcoholic beverages", "Other vegetables", "Poultry"}): ["Coq au vin"],
    frozenset({"Alcoholic beverages", "Other vegetables", "Red meat"}): ["Beef bourguignon"],
    frozenset({"Alcoholic beverages", "Other vegetables", "Red meat", "Starchy vegetables"}): ["Beef bourguignon with potatoes"],
    frozenset({"Alcoholic beverages", "Other vegetables", "Shellfish"}): ["White wine clams"],
    frozenset({"Alcoholic beverages", "Other vegetables", "Temperate fruits"}): ["Apple-wine veg salad"],
    frozenset({"Alcoholic beverages", "Soft drinks", "Temperate fruits"}): ["Spritzer with fruit"],
    frozenset({"Soft drinks", "Temperate fruits"}): ["Fruit punch"],
    frozenset({"Coffee & tea", "Cream & butter", "Eggs"}): ["Coffee custard"],
    frozenset({"Coffee & tea", "Cream & butter", "Eggs", "Flours"}): ["Coffee cake"],
    frozenset({"Coffee & tea", "Cream & butter", "Eggs", "Flours", "Milk"}): ["Tiramisu base"],
    frozenset({"Coffee & tea", "Cream & butter", "Eggs", "Flours", "Nuts"}): ["Coffee walnut cake"],
    frozenset({"Coffee & tea", "Eggs", "Flours", "Milk"}): ["Coffee cake with cream"],

    # ----- Egg combinations -----
    frozenset({"Eggs", "Fresh cheese"}): ["Cheese omelet"],
    frozenset({"Eggs", "Fresh cheese", "Milk"}): ["Cheesy scrambled eggs"],
    frozenset({"Eggs", "Fresh cheese", "Nuts"}): ["Cheesy nut omelet"],
    frozenset({"Eggs", "Fresh cheese", "Temperate fruits"}): ["Cheese & apple omelet"],
    frozenset({"Eggs", "Leafy greens"}): ["Spinach omelet"],
    frozenset({"Eggs", "Leafy greens", "Other vegetables"}): ["Veg & green omelet"],
    frozenset({"Eggs", "Leafy greens", "Other vegetables", "Red meat", "Refined grains"}): ["Beef pasta with greens & eggs"],
    frozenset({"Eggs", "Leafy greens", "Other vegetables", "Starchy vegetables"}): ["Egg-greens potato hash"],
    frozenset({"Eggs", "Milk", "Nuts"}): ["Nutty French toast filling"],
    frozenset({"Eggs", "Milk", "Other vegetables", "Red meat", "Refined grains"}): ["Beef carbonara"],
    frozenset({"Eggs", "Milk", "Refined grains"}): ["Carbonara"],
    frozenset({"Eggs", "Milk", "Starchy vegetables"}): ["Potato strata"],
    frozenset({"Eggs", "Milk", "Temperate fruits"}): ["Apple Dutch baby"],
    frozenset({"Eggs", "Nuts", "Temperate fruits"}): ["Apple-walnut egg salad"],
    frozenset({"Eggs", "Other vegetables"}): ["Veggie omelet"],
    frozenset({"Eggs", "Other vegetables", "Poultry"}): ["Chicken & egg veg dish"],
    frozenset({"Eggs", "Other vegetables", "Red meat"}): ["Steak & eggs"],
    frozenset({"Eggs", "Other vegetables", "Red meat", "Refined grains"}): ["Beef fried rice"],
    frozenset({"Eggs", "Other vegetables", "Red meat", "Whole grains"}): ["Beef & egg grain bowl"],
    frozenset({"Eggs", "Other vegetables", "Starchy vegetables"}): ["Veggie potato hash"],
    frozenset({"Eggs", "Refined grains", "Temperate fruits"}): ["Apple egg fried rice"],
    frozenset({"Eggs", "Fermented dairy", "Flours", "Nuts"}): ["Yogurt nut muffins"],
    frozenset({"Eggs", "Fermented dairy", "Flours", "Nuts", "Temperate fruits"}): ["Yogurt apple-nut muffins"],

    # ----- Cream & butter + Fresh cheese combos -----
    frozenset({"Cream & butter", "Eggs", "Fresh cheese"}): ["Cheesecake"],
    frozenset({"Cream & butter", "Eggs", "Fresh cheese", "Nuts"}): ["Nut-crust cheesecake"],
    frozenset({"Cream & butter", "Eggs", "Fresh cheese", "Temperate fruits"}): ["Apple cheesecake"],
    frozenset({"Cream & butter", "Eggs", "Fresh cheese", "Nuts", "Other vegetables"}): ["Cheese-veg quiche"],  # (rare)
    frozenset({"Cream & butter", "Fresh cheese", "Milk"}): ["Cream cheese sauce"],
    frozenset({"Cream & butter", "Fresh cheese", "Nuts"}): ["Cream cheese nut spread"],
    frozenset({"Cream & butter", "Fresh cheese", "Nuts", "Temperate fruits"}): ["Apple-walnut cheese spread"],
    frozenset({"Cream & butter", "Fresh cheese", "Other vegetables"}): ["Cream cheese veg dip"],
    frozenset({"Cream & butter", "Fresh cheese", "Other vegetables", "Red meat"}): ["Beef cheese roll"],
    frozenset({"Cream & butter", "Fresh cheese", "Other vegetables", "Starchy vegetables"}): ["Cheesy potato gratin"],
    frozenset({"Cream & butter", "Fresh cheese", "Milk", "Nuts", "Other vegetables", "Red meat"}): ["Loaded cheesy beef bake"],
    frozenset({"Cream & butter", "Fresh cheese", "Temperate fruits"}): ["Apple cream cheese spread"],
    frozenset({"Cream & butter", "Flours", "Fresh cheese"}): ["Cheese pastry"],
    frozenset({"Cream & butter", "Flours", "Fresh cheese", "Milk"}): ["Cheese béchamel pasta"],
    frozenset({"Cream & butter", "Flours", "Fresh cheese", "Milk", "Nuts"}): ["Cheesy nut pasta"],
    frozenset({"Cream & butter", "Flours", "Milk"}): ["Béchamel"],
    frozenset({"Cream & butter", "Flours", "Milk", "Other vegetables", "Starchy vegetables"}): ["Potato gratin"],
    frozenset({"Cream & butter", "Flours", "Milk", "Other vegetables"}): ["Creamy veg casserole"],
    frozenset({"Cream & butter", "Flours", "Milk", "Whole grains"}): ["Béchamel oat bake"],
    frozenset({"Cream & butter", "Flours", "Nuts"}): ["Nut shortbread"],
    frozenset({"Cream & butter", "Flours", "Nuts", "Temperate fruits"}): ["Apple-walnut shortcake"],
    frozenset({"Cream & butter", "Flours", "Other vegetables"}): ["Veg-stuffed pastry"],
    frozenset({"Cream & butter", "Flours", "Other vegetables", "Poultry"}): ["Chicken pot pie"],
    frozenset({"Cream & butter", "Flours", "Other vegetables", "Red meat"}): ["Beef pot pie"],
    frozenset({"Cream & butter", "Flours", "Starchy vegetables"}): ["Potato pastry"],
    frozenset({"Cream & butter", "Flours", "Temperate fruits"}): ["Apple turnover"],
    frozenset({"Cream & butter", "Flours", "Temperate fruits", "Whole grains"}): ["Whole-wheat apple crisp"],
    frozenset({"Cream & butter", "Flours", "Whole grains"}): ["Whole-wheat pastry"],

    # ----- Cream & butter + meat -----
    frozenset({"Cream & butter", "Other vegetables", "Poultry"}): ["Buttered chicken & veg"],
    frozenset({"Cream & butter", "Other vegetables", "Poultry", "Processed meat", "Red meat"}): ["Mixed meat butter braise"],
    frozenset({"Cream & butter", "Other vegetables", "Poultry", "Refined grains"}): ["Chicken pasta in butter"],
    frozenset({"Cream & butter", "Other vegetables", "Poultry", "Starchy vegetables"}): ["Butter chicken with potatoes"],
    frozenset({"Cream & butter", "Other vegetables", "Poultry", "Temperate fruits"}): ["Apple butter chicken"],
    frozenset({"Cream & butter", "Other vegetables", "Poultry", "Whole grains"}): ["Chicken grain bowl in butter"],
    frozenset({"Cream & butter", "Other vegetables", "Processed meat"}): ["Bacon-buttered veg"],
    frozenset({"Cream & butter", "Other vegetables", "Red meat"}): ["Beef in butter sauce"],
    frozenset({"Cream & butter", "Other vegetables", "Red meat", "Starchy vegetables"}): ["Beef potato butter braise"],
    frozenset({"Cream & butter", "Other vegetables", "Red meat", "Whole grains"}): ["Beef grain butter bowl"],
    frozenset({"Cream & butter", "Other vegetables", "Shellfish"}): ["Shrimp scampi"],
    frozenset({"Cream & butter", "Other vegetables", "Starchy vegetables"}): ["Buttered veg & potatoes"],
    frozenset({"Cream & butter", "Other vegetables", "Temperate fruits"}): ["Apple butter sauté"],
    frozenset({"Cream & butter", "Other vegetables", "Whole grains"}): ["Buttered grain bowl"],
    frozenset({"Cream & butter", "Other vegetables", "Refined grains"}): ["Buttered pasta with veg"],
    frozenset({"Cream & butter", "Other vegetables", "Processed cheese", "Starchy vegetables"}): ["Cheesy buttered potatoes"],
    frozenset({"Cream & butter", "Other vegetables", "Poultry", "Processed cheese", "Starchy vegetables"}): ["Chicken cheese potato bake"],
    frozenset({"Cream & butter", "Cruciferous vegetables", "Other vegetables", "Poultry", "Whole grains"}): ["Chicken broccoli grain bowl"],
    frozenset({"Cream & butter", "Cruciferous vegetables", "Other vegetables", "Whole grains"}): ["Broccoli whole-grain bake"],
    frozenset({"Cream & butter", "Leafy greens", "Other vegetables"}): ["Sautéed greens with butter"],
    frozenset({"Cream & butter", "Leafy greens", "Other vegetables", "Prepared soups & broths"}): ["Creamy greens soup"],
    frozenset({"Cream & butter", "Leafy greens", "Other vegetables", "Temperate fruits"}): ["Apple-spinach butter sauté"],
    frozenset({"Cream & butter", "Legumes", "Milk"}): ["Creamy lentil dal"],
    frozenset({"Cream & butter", "Legumes", "Whole grains"}): ["Lentil-grain butter bowl"],
    frozenset({"Cream & butter", "Milk", "Nuts"}): ["Creamy nut sauce"],
    frozenset({"Cream & butter", "Milk", "Nut butters"}): ["Creamy peanut sauce"],
    frozenset({"Cream & butter", "Milk", "Nut butters", "Whole grains"}): ["Peanut butter oatmeal"],
    frozenset({"Cream & butter", "Milk", "Nuts", "Temperate fruits"}): ["Creamy nut-apple dessert"],
    frozenset({"Cream & butter", "Milk", "Nuts", "Whole grains"}): ["Creamy oat nut porridge"],
    frozenset({"Cream & butter", "Milk", "Other vegetables", "Poultry", "Starchy vegetables"}): ["Creamy chicken potato bake"],
    frozenset({"Cream & butter", "Milk", "Starchy vegetables"}): ["Creamy mashed potatoes"],
    frozenset({"Cream & butter", "Milk", "Temperate fruits"}): ["Apple cream sauce"],
    frozenset({"Cream & butter", "Milk", "Whole grains"}): ["Creamy oatmeal"],
    frozenset({"Cream & butter", "Nut butters", "Whole grains"}): ["Peanut butter oat squares"],
    frozenset({"Cream & butter", "Nuts", "Starchy vegetables"}): ["Buttery nut potato bake"],
    frozenset({"Cream & butter", "Nuts", "Temperate fruits"}): ["Apple-walnut butter sauté"],
    frozenset({"Cream & butter", "Refined grains", "Temperate fruits"}): ["Apple pasta with butter"],
    frozenset({"Cream & butter", "Starchy vegetables", "Temperate fruits"}): ["Buttered sweet potato with apple"],
    frozenset({"Cream & butter", "Temperate fruits", "Whole grains"}): ["Apple buttered oatmeal"],

    # ----- Misc / smaller groupings -----
    frozenset({"Flours", "Fresh cheese"}): ["Cheese biscuit"],
    frozenset({"Flours", "Fresh cheese", "Milk"}): ["Cheese pancakes"],
    frozenset({"Flours", "Fresh cheese", "Milk", "Nuts"}): ["Nutty cheese pancakes"],
    frozenset({"Flours", "Fresh cheese", "Milk", "Nuts", "Temperate fruits"}): ["Apple-walnut cheese pancakes"],
    frozenset({"Flours", "Fresh cheese", "Milk", "Temperate fruits"}): ["Apple cheese pancakes"],
    frozenset({"Flours", "Other vegetables", "Poultry"}): ["Chicken fritters"],
    frozenset({"Flours", "Other vegetables", "Processed meat", "Starchy vegetables"}): ["Ham potato fritters"],
    frozenset({"Flours", "Other vegetables", "Red meat"}): ["Beef fritters"],
    frozenset({"Flours", "Other vegetables", "Red meat", "Starchy vegetables"}): ["Beef potato fritters"],
    frozenset({"Flours", "Other vegetables"}): ["Vegetable batter"],
    frozenset({"Flours", "Nuts"}): ["Nut shortbread"],
    frozenset({"Flours", "Milk", "Temperate fruits"}): ["Apple pancake batter"],
    frozenset({"Flours", "Poultry"}): ["Breaded chicken"],
    frozenset({"Flours", "Starchy vegetables"}): ["Potato bread"],
    frozenset({"Flours", "Temperate fruits"}): ["Apple flatbread"],
    frozenset({"Flours", "Temperate fruits", "Whole grains"}): ["Apple-oat flatbread"],
    frozenset({"Flours", "Whole grains"}): ["Whole-wheat bread"],

    frozenset({"Coffee & tea", "Cream & butter", "Eggs", "Flours", "Milk"}): ["Tiramisu"],

    frozenset({"Cruciferous vegetables", "Other vegetables"}): ["Broccoli-veg medley"],
    frozenset({"Cruciferous vegetables", "Other vegetables", "Poultry", "Whole grains"}): ["Chicken broccoli grain bowl"],
    frozenset({"Cruciferous vegetables", "Other vegetables", "Whole grains"}): ["Broccoli grain bowl"],
    frozenset({"Cruciferous vegetables", "Other vegetables", "Temperate fruits"}): ["Apple-broccoli slaw"],
    frozenset({"Cruciferous vegetables", "Other vegetables", "Processed meat"}): ["Bacon broccoli"],
    frozenset({"Cruciferous vegetables", "Dried fruits", "Other vegetables", "Processed meat"}): ["Bacon raisin broccoli salad"],
    frozenset({"Cruciferous vegetables", "Dried fruits", "Other vegetables", "Processed meat", "Seeds"}): ["Loaded broccoli salad"],

    frozenset({"Nuts", "Other vegetables", "Poultry", "Temperate fruits"}): ["Chicken apple-nut salad"],
    frozenset({"Nuts", "Other vegetables", "Temperate fruits"}): ["Apple-nut veg salad"],
    frozenset({"Nut butters", "Other vegetables", "Temperate fruits"}): ["Apple-peanut salad"],
    frozenset({"Nut butters", "Temperate fruits"}): ["Apple with peanut butter"],
    frozenset({"Legumes", "Nut butters", "Other vegetables", "Temperate fruits"}): ["African peanut stew"],
    frozenset({"Legumes", "Other vegetables", "Pickled vegetables"}): ["Pickled bean salad"],
    frozenset({"Legumes", "Other vegetables", "Pickled vegetables", "Starchy vegetables"}): ["Pickled bean & potato salad"],
    frozenset({"Legumes", "Other vegetables", "Processed meat"}): ["Beans & bacon"],
    frozenset({"Legumes", "Other vegetables", "Processed meat", "Red meat"}): ["Cassoulet"],
    frozenset({"Legumes", "Other vegetables", "Processed meat", "Starchy vegetables"}): ["Bean potato bacon stew"],
    frozenset({"Legumes", "Other vegetables", "Red meat"}): ["Beef & beans"],
    frozenset({"Legumes", "Other vegetables", "Red meat", "Spice blends", "Starchy vegetables"}): ["Beef-bean curry with potatoes"],
    frozenset({"Legumes", "Other vegetables", "Red meat", "Starchy vegetables"}): ["Beef bean stew"],
    frozenset({"Legumes", "Other vegetables", "Starchy vegetables"}): ["Bean potato stew"],
    frozenset({"Legumes", "Other vegetables", "Temperate fruits"}): ["Bean & apple salad"],

    frozenset({"Milk", "Other vegetables"}): ["Milk-stewed vegetables"],
    frozenset({"Milk", "Other vegetables", "Poultry"}): ["Creamed chicken & veg"],
    frozenset({"Milk", "Other vegetables", "Poultry", "Whole grains"}): ["Chicken milk grain bowl"],
    frozenset({"Milk", "Other vegetables", "Red meat", "Starchy vegetables"}): ["Beef potato milk stew"],
    frozenset({"Milk", "Plant milks"}): ["Mixed milk drink"],
    frozenset({"Milk", "Whole grains"}): ["Oatmeal with milk"],
    frozenset({"Milk", "Temperate fruits", "Yogurt"}): ["Apple yogurt smoothie"],
    frozenset({"Milk", "Yogurt"}): ["Milky yogurt drink"],
    frozenset({"Milk", "Nut butters", "Whole grains"}): ["Peanut milk oats"],
    frozenset({"Milk", "Nuts", "Temperate fruits"}): ["Apple-walnut milk"],
    frozenset({"Juices", "Temperate fruits"}): ["Apple juice with fruit"],
    frozenset({"Juices", "Milk"}): ["Juice-milk drink"],
    frozenset({"Plant milks", "Temperate fruits"}): ["Apple almond-milk drink"],

    frozenset({"Other vegetables", "Pickled vegetables"}): ["Pickle salad"],
    frozenset({"Other vegetables", "Poultry", "Processed cheese"}): ["Chicken cheese melt"],
    frozenset({"Other vegetables", "Poultry", "Processed cheese", "Refined grains"}): ["Chicken cheese pasta"],
    frozenset({"Other vegetables", "Poultry", "Processed cheese", "Starchy vegetables"}): ["Cheesy chicken potatoes"],
    frozenset({"Other vegetables", "Poultry", "Red meat"}): ["Mixed meat skillet"],
    frozenset({"Other vegetables", "Poultry", "Red meat", "Starchy vegetables"}): ["Mixed meat potato bake"],
    frozenset({"Other vegetables", "Poultry", "Red meat", "Whole grains"}): ["Mixed meat grain bowl"],
    frozenset({"Other vegetables", "Poultry", "Refined grains", "Temperate fruits"}): ["Chicken apple pasta"],
    frozenset({"Other vegetables", "Poultry", "Starchy vegetables", "Temperate fruits"}): ["Chicken apple potato bake"],
    frozenset({"Other vegetables", "Pickled vegetables", "Legumes", "Starchy vegetables"}): ["Pickled bean potato salad"],
    frozenset({"Other vegetables", "Prepared soups & broths", "Red meat"}): ["Beef soup"],
    frozenset({"Other vegetables", "Processed cheese"}): ["Cheesy veg melt"],
    frozenset({"Other vegetables", "Processed cheese", "Processed meat"}): ["Cheese & ham melt"],
    frozenset({"Other vegetables", "Processed cheese", "Processed meat", "Red meat"}): ["Loaded meat-cheese melt"],
    frozenset({"Other vegetables", "Processed cheese", "Red meat"}): ["Beef cheese melt"],
    frozenset({"Other vegetables", "Processed cheese", "Red meat", "Refined grains"}): ["Beef cheesy pasta"],
    frozenset({"Other vegetables", "Processed cheese", "Red meat", "Starchy vegetables"}): ["Beef cheesy potatoes"],
    frozenset({"Other vegetables", "Processed cheese", "Starchy vegetables"}): ["Cheesy potato veg bake"],
    frozenset({"Other vegetables", "Processed meat", "Refined grains"}): ["Bacon pasta"],
    frozenset({"Other vegetables", "Processed meat", "Whole grains"}): ["Bacon grain bowl"],
    frozenset({"Other vegetables", "Refined grains", "Temperate fruits"}): ["Apple pasta"],
    frozenset({"Other vegetables", "Red meat", "Seeds"}): ["Beef sesame stir-fry"],
    frozenset({"Other vegetables", "Red meat", "Starchy vegetables", "Whole grains"}): ["Beef grain potato bowl"],
    frozenset({"Other vegetables", "Refined grains", "Shellfish"}): ["Shrimp pasta"],
    frozenset({"Other vegetables", "Refined grains", "Spice blends"}): ["Curry pasta"],
    frozenset({"Other vegetables", "Seeds"}): ["Seeded vegetable salad"],
    frozenset({"Other vegetables", "Shellfish", "Temperate fruits"}): ["Shrimp-apple salad"],
    frozenset({"Other vegetables", "Spice blends", "Temperate fruits"}): ["Spiced apple veg"],
    frozenset({"Other vegetables", "Starchy vegetables", "Temperate fruits"}): ["Apple potato bake"],
    frozenset({"Other vegetables", "Temperate fruits", "Whole grains"}): ["Apple grain bowl"],
    frozenset({"Other vegetables", "Temperate fruits", "White fish"}): ["White fish with apple-veg"],
    frozenset({"Other vegetables", "Whole grains"}): ["Whole-grain veg bowl"],
    frozenset({"Other vegetables", "Yogurt"}): ["Yogurt-dressed veg"],
    frozenset({"Oily fish", "Other vegetables", "Temperate fruits"}): ["Salmon with apple-veg"],

    frozenset({"Processed cheese", "Processed meat"}): ["Cheese & ham roll"],
    frozenset({"Processed meat", "Refined grains"}): ["Pasta with bacon"],
    frozenset({"Processed meat", "Starchy vegetables"}): ["Bacon potatoes"],
    frozenset({"Processed meat", "Temperate fruits"}): ["Bacon-wrapped apple"],
    frozenset({"Poultry", "Refined grains"}): ["Chicken pasta"],
    frozenset({"Poultry", "Temperate fruits"}): ["Chicken with apples"],
    frozenset({"Poultry", "Whole grains"}): ["Chicken grain bowl"],
    frozenset({"Red meat", "Starchy vegetables"}): ["Steak & potatoes"],
    frozenset({"Red meat", "Temperate fruits"}): ["Beef with apples"],
    frozenset({"Refined grains"}): ["Cooked pasta", "Plain rice"],
    frozenset({"Starchy vegetables", "Temperate fruits"}): ["Apple sweet-potato bake"],
    frozenset({"Temperate fruits", "Whole grains"}): ["Apple oatmeal"],
    frozenset({"Temperate fruits", "Yogurt"}): ["Apple yogurt"],

    frozenset({"Fermented dairy", "Temperate fruits"}): ["Yogurt with apples"],
    frozenset({"Dried fruits", "Flours"}): ["Raisin bread"],
    frozenset({"Dried fruits", "Nuts"}): ["Date & nut snack"],
    frozenset({"Dried fruits", "Nuts", "Temperate fruits"}): ["Apple date nut mix"],
    frozenset({"Dried fruits", "Other vegetables", "Poultry"}): ["Chicken with raisin & veg"],
    frozenset({"Dried fruits", "Other vegetables", "Temperate fruits"}): ["Apple-raisin veg salad"],
    frozenset({"Dried fruits", "Temperate fruits"}): ["Apple & raisin compote"],

    # -- last odds & ends from the long tail
    frozenset({"Eggs", "Refined grains"}): ["Egg fried rice"],
    frozenset({"Eggs", "Other vegetables", "Refined grains"}): ["Veggie egg fried rice"],
    frozenset({"Eggs", "Other vegetables", "Red meat", "Refined grains"}): ["Beef egg fried rice"],
    frozenset({"Aged cheese", "Cream & butter", "Fresh cheese", "Other vegetables"}): ["Triple-cheese veg bake"],
    frozenset({"Aged cheese", "Cream & butter", "Other vegetables", "Poultry", "Refined grains"}): ["Chicken cheese pasta bake"],
    frozenset({"Aged cheese", "Cream & butter", "Other vegetables", "Poultry", "Whole grains"}): ["Chicken cheese grain bake"],
    frozenset({"Aged cheese", "Cream & butter", "Other vegetables", "Refined grains"}): ["Cheesy pasta bake"],
    frozenset({"Aged cheese", "Other vegetables", "Poultry", "Refined grains"}): ["Chicken parm pasta"],
    frozenset({"Aged cheese", "Other vegetables", "Poultry", "Whole grains"}): ["Chicken cheese grain bowl"],
    frozenset({"Aged cheese", "Other vegetables", "Red meat", "Refined grains"}): ["Beef cheese pasta"],
    frozenset({"Aged cheese", "Other vegetables", "Refined grains", "Temperate fruits"}): ["Apple cheese pasta"],
    frozenset({"Aged cheese", "Cream & butter", "Flours", "Milk", "Refined grains"}): ["Baked mac & cheese"],
    frozenset({"Aged cheese", "Cream & butter", "Fresh cheese", "Other vegetables", "Starchy vegetables"}): ["Loaded cheesy potato bake"],

    frozenset({"Eggs", "Fresh cheese", "Temperate fruits"}): ["Apple cheese omelet"],
    frozenset({"Eggs", "Fresh cheese", "Nuts"}): ["Nutty cheese eggs"],
    frozenset({"Eggs", "Other vegetables", "Poultry"}): ["Chicken & egg veg bowl"],

    # -- niche / individual long tail (covered by fallback if missed)
    frozenset({"Cream & butter", "Eggs", "Nuts", "Temperate fruits"}): ["Apple-walnut buttered eggs"],
    frozenset({"Cream & butter", "Eggs", "Milk", "Refined grains"}): ["Creamy pasta carbonara"],
    frozenset({"Cream & butter", "Eggs", "Milk", "Refined grains", "Temperate fruits"}): ["Apple-creamy pasta bake"],
    frozenset({"Cream & butter", "Eggs", "Milk", "Starchy vegetables"}): ["Potato custard"],
    frozenset({"Cream & butter", "Eggs", "Milk", "Temperate fruits"}): ["Apple custard"],
    frozenset({"Cream & butter", "Eggs", "Milk", "Nuts"}): ["Nutty custard"],
    frozenset({"Cream & butter", "Eggs", "Nuts"}): ["Nutty buttered eggs"],
    frozenset({"Cream & butter", "Eggs", "Starchy vegetables"}): ["Potato custard"],
    frozenset({"Cream & butter", "Eggs", "Refined grains", "Temperate fruits"}): ["Apple egg pasta"],
    frozenset({"Cream & butter", "Eggs", "Temperate fruits"}): ["Apple-egg butter dessert"],

    # -- shapes with `Coffee & tea` we don't already cover
    frozenset({"Coffee & tea", "Cream & butter", "Eggs", "Flours", "Nuts"}): ["Coffee walnut cake"],
    frozenset({"Coffee & tea", "Cream & butter", "Eggs", "Flours", "Milk"}): ["Coffee cream cake"],

    # -- generic-but-still-recognizable misc
    frozenset({"Flours", "Other vegetables", "Red meat", "Starchy vegetables"}): ["Beef potato pie"],
    frozenset({"Cream & butter", "Eggs", "Fermented dairy", "Flours", "Nuts"}): ["Sour cream nut muffins"],
    frozenset({"Cream & butter", "Eggs", "Fermented dairy", "Flours", "Nuts", "Temperate fruits"}): ["Sour cream apple-nut muffins"],
    frozenset({"Cream & butter", "Eggs", "Fermented dairy", "Flours", "Temperate fruits"}): ["Sour cream apple muffins"],
    frozenset({"Cream & butter", "Eggs", "Flours", "Milk", "Nuts", "Starchy vegetables"}): ["Nutty potato bread"],
    frozenset({"Cream & butter", "Eggs", "Flours", "Nut butters", "Whole grains"}): ["Peanut-oat butter cookies"],
    frozenset({"Cream & butter", "Eggs", "Nut butters", "Whole grains"}): ["Peanut butter oat cookies"],

    # -- alcohol + dairy long tail
    frozenset({"Alcoholic beverages", "Cream & butter", "Eggs", "Milk"}): ["Spiked custard"],

    # -- fresh cheese + organ + shellfish exotic
    frozenset({"Fresh cheese", "Nuts", "Oily fish", "Other vegetables", "Temperate fruits"}): ["Salmon fruit-cheese salad"],
    frozenset({"Fresh cheese", "Organ meats", "Other vegetables", "Shellfish"}): ["Seafood-liver casserole"],
    frozenset({"Fresh cheese", "Other vegetables", "Processed meat", "Red meat", "Refined grains"}): ["Meat lasagna"],
    frozenset({"Fresh cheese", "Other vegetables", "Processed meat", "Refined grains"}): ["Ham pasta bake"],
    frozenset({"Fresh cheese", "Other vegetables", "Red meat", "Refined grains"}): ["Beef pasta bake"],
    frozenset({"Fresh cheese", "Other vegetables", "Refined grains"}): ["Pasta with cheese & veg"],
    frozenset({"Fresh cheese", "Other vegetables", "Shellfish", "Temperate fruits"}): ["Shrimp apple cheese salad"],
    frozenset({"Fresh cheese", "Milk", "Nut butters"}): ["Creamy peanut cheese"],
    frozenset({"Fresh cheese", "Milk", "Nuts", "Temperate fruits"}): ["Apple-walnut cheese milk"],
    frozenset({"Fresh cheese", "Milk", "Temperate fruits"}): ["Apple cheese milk"],
    frozenset({"Fresh cheese", "Nut butters"}): ["Peanut cheese spread"],
    frozenset({"Fresh cheese", "Other vegetables", "Temperate fruits"}): ["Apple cheese veg salad"],
    frozenset({"Fresh cheese", "Red meat"}): ["Cheese-stuffed beef"],
    frozenset({"Fresh cheese", "Red meat", "Refined grains"}): ["Beef cheese pasta"],
    frozenset({"Fresh cheese", "Refined grains"}): ["Cheese pasta"],
    frozenset({"Fresh cheese", "Shellfish"}): ["Shrimp with feta"],
    frozenset({"Fresh cheese", "Legumes"}): ["Cheesy bean dip"],

    # -- a few "Aged cheese" longer combos
    frozenset({"Aged cheese", "Cruciferous vegetables", "Leafy greens", "Other vegetables", "Processed meat"}): ["Loaded broccoli salad"],
    frozenset({"Aged cheese", "Cruciferous vegetables", "Other vegetables", "Processed meat"}): ["Bacon-cheese broccoli"],
    frozenset({"Aged cheese", "Eggs", "Leafy greens", "Milk", "Other vegetables", "Processed meat", "Refined grains"}): ["Loaded carbonara"],
    frozenset({"Aged cheese", "Eggs", "Leafy greens", "Milk", "Red meat", "Refined grains"}): ["Beef pasta gratin"],
    frozenset({"Aged cheese", "Cream & butter", "Other vegetables", "Whole grains"}): ["Cheesy grain bowl"],
    frozenset({"Aged cheese", "Cream & butter", "Flours", "Milk", "Other vegetables", "Starchy vegetables"}): ["Cheesy potato gratin"],
    frozenset({"Aged cheese", "Cream & butter", "Flours"}): ["Cheese pastry"],
    frozenset({"Aged cheese", "Cream & butter", "Flours", "Other vegetables"}): ["Cheese-veg tart"],
    frozenset({"Aged cheese", "Cream & butter", "Refined grains"}): ["Cacio e pepe"],
    frozenset({"Aged cheese", "Cream & butter", "Other vegetables", "Processed meat", "Starchy vegetables"}): ["Cheesy bacon potato bake"],
    frozenset({"Aged cheese", "Cream & butter", "Other vegetables", "Starchy vegetables"}): ["Cheesy potato gratin"],
    frozenset({"Aged cheese", "Flours"}): ["Cheese crackers"],
    frozenset({"Aged cheese", "Fresh cheese", "Other vegetables", "Red meat"}): ["Beef cheese bake"],
    frozenset({"Aged cheese", "Fresh cheese", "Refined grains"}): ["Three-cheese pasta"],
    frozenset({"Aged cheese", "Fresh cheese", "Poultry"}): ["Chicken cordon bleu"],
    frozenset({"Aged cheese", "Fresh cheese", "Red meat", "Refined grains"}): ["Beef lasagna"],
    frozenset({"Aged cheese", "Other vegetables", "Refined grains"}): ["Cheesy pasta"],
    frozenset({"Aged cheese", "Other vegetables", "Refined grains", "Temperate fruits"}): ["Apple cheese pasta"],
    frozenset({"Aged cheese", "Other vegetables", "Red meat", "Refined grains"}): ["Beef cheese pasta"],
    frozenset({"Aged cheese", "Other vegetables", "Temperate fruits"}): ["Apple cheese salad"],

    # -- final less-common shapes
    frozenset({"Berries", "Bread & rolls"}): ["Berry toast"],
    frozenset({"Berries", "Bread & rolls", "Cream & butter"}): ["Berry buttered toast"],
    frozenset({"Berries", "Bread & rolls", "Cream & butter", "Eggs", "Fresh cheese"}): ["Berry-cheese French toast"],
    frozenset({"Berries", "Bread & rolls", "Cream & butter", "Fresh cheese", "Temperate fruits"}): ["Berry-apple cheese toast"],
    frozenset({"Berries", "Bread & rolls", "Fresh cheese"}): ["Berry cheese toast"],
    frozenset({"Berries", "Bread & rolls", "Fresh cheese", "Temperate fruits"}): ["Berry-apple cheese toast"],
}


# -------------------- composer for shapes not in the table --------------------

# Categories that should drive the primary noun of the dish name (a meal
# without a "protein" or "produce" anchor is hard to name). Listed roughly
# in order of how much they tell you about the dish.
PRIMARY_PRIORITY = [
    "Poultry", "Red meat", "Processed meat", "Shellfish", "White fish",
    "Oily fish", "Organ meats", "Eggs",
    "Aged cheese", "Fresh cheese", "Processed cheese",
    "Legumes", "Nut butters",
    "Berries", "Temperate fruits", "Tropical fruits", "Citrus fruits",
    "Dried fruits",
    "Starchy vegetables", "Cruciferous vegetables", "Leafy greens",
    "Other vegetables", "Pickled vegetables",
    "Whole grains", "Refined grains", "Bread & rolls",
    "Nuts", "Seeds",
    "Milk", "Plant milks", "Fermented dairy", "Yogurt", "Cream & butter",
    "Flours",
    "Alcoholic beverages", "Coffee & tea", "Juices", "Soft drinks",
    "Prepared soups & broths", "Spice blends",
]

# Short, human-friendly labels per category (for composing names from
# unrecognized shapes). Falls back to the category itself.
CATEGORY_NICKNAME = {
    "Other vegetables": "vegetable",
    "Starchy vegetables": "potato",
    "Leafy greens": "greens",
    "Cruciferous vegetables": "broccoli",
    "Pickled vegetables": "pickled veg",
    "Temperate fruits": "apple",
    "Tropical fruits": "tropical fruit",
    "Citrus fruits": "citrus",
    "Dried fruits": "raisin",
    "Berries": "berry",
    "Red meat": "beef",
    "Poultry": "chicken",
    "Processed meat": "bacon",
    "Organ meats": "liver",
    "Shellfish": "shrimp",
    "Oily fish": "salmon",
    "White fish": "white fish",
    "Aged cheese": "cheddar",
    "Fresh cheese": "ricotta",
    "Processed cheese": "American cheese",
    "Legumes": "bean",
    "Nuts": "walnut",
    "Nut butters": "peanut butter",
    "Seeds": "seed",
    "Whole grains": "oat",
    "Refined grains": "pasta",
    "Bread & rolls": "bread",
    "Eggs": "egg",
    "Milk": "milk",
    "Plant milks": "almond-milk",
    "Cream & butter": "buttered",
    "Fermented dairy": "yogurt",
    "Yogurt": "yogurt",
    "Flours": "flour-based",
    "Alcoholic beverages": "wine-braised",
    "Coffee & tea": "coffee",
    "Juices": "juice",
    "Soft drinks": "soda",
    "Spice blends": "curry",
    "Prepared soups & broths": "broth",
}


def compose_fallback_name(core: frozenset[str]) -> str | None:
    """Last-resort composer for shapes not in SHAPE_TO_NAMES.

    Picks the most distinctive 2 categories and stitches them into a short
    name. Returns None if the shape is empty or has nothing to anchor on.
    """
    if not core:
        return None

    ordered = [c for c in PRIMARY_PRIORITY if c in core]
    if not ordered:
        ordered = sorted(core)

    primary = ordered[0]
    secondary = ordered[1] if len(ordered) > 1 else None

    p = CATEGORY_NICKNAME.get(primary, primary.lower())
    if secondary is None:
        return f"{p.capitalize()} dish"

    s = CATEGORY_NICKNAME.get(secondary, secondary.lower())
    return f"{p.capitalize()} with {s}"


# -------------------- main --------------------


def slugify(text: str) -> str:
    """Produce an ID-safe slug from a name. Lowercase, alphanumerics + dashes."""
    s = text.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "meal"


def main() -> None:
    raw = json.loads(SRC.read_text(encoding="utf-8"))

    out: list[dict] = []
    dropped: list[dict] = []
    fallback_used: list[tuple[str, str]] = []
    used_ids: set[str] = set()

    for meal in raw:
        cats = list(meal.get("ingredient_categories", []))
        core = frozenset(c for c in cats if c not in NOISE)

        names = SHAPE_TO_NAMES.get(core)
        if names is None:
            fallback = compose_fallback_name(core)
            if fallback is None:
                dropped.append(meal)
                continue
            names = [fallback]
            fallback_used.append((" + ".join(sorted(core)) or "(empty)", fallback))
        elif names is DROP or not names:
            dropped.append(meal)
            continue

        freq_total = meal.get("frequency", 0)
        per_variant = max(1, freq_total // len(names))

        for i, name in enumerate(names):
            new_meal = dict(meal)
            base_slug = slugify(name)
            slug = base_slug
            suffix = 2
            while slug in used_ids:
                slug = f"{base_slug}-{suffix}"
                suffix += 1
            used_ids.add(slug)
            new_meal["id"] = f"corpus-{slug}"
            new_meal["name"] = name
            new_meal["notes"] = (
                f"Compositional pattern — derived from {freq_total:,} corpus recipes "
                f"matching this ingredient shape."
            )
            if len(names) > 1:
                new_meal["frequency"] = per_variant
            out.append(new_meal)

    out.sort(key=lambda m: -m.get("frequency", 0))

    OUT_DATA.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    report_lines: list[str] = []
    report_lines.append(f"# Compositional meals audit")
    report_lines.append(f"")
    report_lines.append(f"Input patterns: {len(raw)}")
    report_lines.append(f"Output patterns: {len(out)}")
    report_lines.append(f"Dropped patterns: {len(dropped)}")
    report_lines.append(f"Patterns with fallback (composed) names: {len(fallback_used)}")
    report_lines.append(f"")
    report_lines.append(f"## Dropped (no recognizable dish name)")
    for d in dropped[:200]:
        cats = " + ".join(d.get("ingredient_categories", []))
        report_lines.append(f"  freq={d.get('frequency', 0)}  {cats}")
    if len(dropped) > 200:
        report_lines.append(f"  ... and {len(dropped) - 200} more")
    report_lines.append(f"")
    report_lines.append(f"## Fallback-named (first 200)")
    seen: set[str] = set()
    for shape, nm in fallback_used:
        if shape in seen:
            continue
        seen.add(shape)
        report_lines.append(f"  {nm}  <-  {shape}")
        if len(seen) >= 200:
            break

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"Wrote {OUT_DATA.relative_to(ROOT)} ({len(out)} patterns; dropped {len(dropped)}; fallback {len(fallback_used)})")
    print(f"Wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
