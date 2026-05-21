"""Phase 34 backfill: stamp every meal with diet_compatibility,
frequency, source.

Idempotent. Re-running against an already-backfilled file recomputes
diet_compatibility (in case the rules in src/data/schema.js change) but
leaves `frequency` and `source` untouched if they already exist —
Phase 36 will populate non-1 frequencies and source='corpus' on
discovered patterns and we don't want to clobber them.

DIET rules are duplicated here in Python from src/data/schema.js's DIETS.
The two must stay in sync; the JS file is the canonical reference. A
mismatch wouldn't break the app (the JS helper recomputes from DIETS at
runtime) but it WOULD make the precomputed array stale.
"""

import json
import pathlib
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
INGREDIENTS_PATH = ROOT / "src" / "data" / "ingredients.json"
MEALS_PATH       = ROOT / "src" / "data" / "meals.json"

NUTRIENT_FIELDS = [
    "calories", "carbs", "protein", "fiber",
    "fat", "sodium", "sugar", "saturated_fat",
]

# Mirror of src/data/schema.js DIETS. Keep in sync.
DIETS = {
    "keto": {
        "excludedCategories": [
            "Whole grains", "Refined grains", "Bread & rolls", "Pasta & noodles",
            "Baked snacks & pastries", "Legumes", "Soy products",
            "Starchy vegetables", "Sugar & sweeteners", "Candy & desserts",
            "Jams & preserves", "Juices", "Soft drinks",
            "Tropical fruits", "Temperate fruits", "Dried fruits",
            "Prepared mixes",
        ],
    },
    "paleo": {
        "excludedCategories": [
            "Whole grains", "Refined grains", "Bread & rolls", "Pasta & noodles",
            "Baked snacks & pastries", "Legumes", "Soy products",
            "Milk", "Yogurt", "Aged cheese", "Fresh cheese", "Processed cheese",
            "Frozen dairy", "Cream & butter",
            "Sugar & sweeteners", "Candy & desserts", "Jams & preserves",
            "Alcoholic beverages", "Soft drinks", "Prepared mixes",
            "Margarine & shortening",
        ],
    },
    "mediterranean": {
        "excludedCategories": [
            "Processed meat", "Processed cheese",
            "Candy & desserts", "Soft drinks",
            "Baked snacks & pastries", "Margarine & shortening",
            "Prepared mixes",
        ],
    },
    "whole30": {
        "excludedCategories": [
            "Whole grains", "Refined grains", "Bread & rolls", "Pasta & noodles",
            "Baked snacks & pastries", "Legumes", "Soy products",
            "Milk", "Yogurt", "Aged cheese", "Fresh cheese", "Processed cheese",
            "Frozen dairy", "Cream & butter",
            "Sugar & sweeteners", "Candy & desserts", "Jams & preserves",
            "Alcoholic beverages", "Soft drinks", "Juices",
            "Prepared mixes", "Processed meat",
        ],
    },
    "lowfodmap": {
        "excludedCategories": [
            "Legumes", "Soy products",
            "Milk", "Yogurt",
            "Sugar & sweeteners", "Jams & preserves",
            "Dried fruits",
        ],
    },
    "high_protein": {
        "nutrientMin": {"protein": 15},
    },
}
DIET_KEYS = list(DIETS.keys())


def category_aggregates(ingredients):
    """Return { category_name: { nutrient: mean_per_100g } }."""
    by_cat = defaultdict(list)
    for ing in ingredients:
        by_cat[ing["category"]].append(ing)
    out = {}
    for cat, members in by_cat.items():
        agg = {}
        for n in NUTRIENT_FIELDS:
            agg[n] = sum(m[n] for m in members) / len(members)
        out[cat] = agg
    return out


def meal_aggregate(meal, cat_aggs):
    """Equal-weighted mean of constituent categories' aggregates."""
    cats = [cat_aggs[c] for c in meal.get("ingredient_categories", []) if c in cat_aggs]
    if not cats:
        return None
    out = {}
    for n in NUTRIENT_FIELDS:
        out[n] = sum(c[n] for c in cats) / len(cats)
    return out


def diet_compatibility(meal, cat_aggs):
    cats = set(meal.get("ingredient_categories", []))
    meal_agg = meal_aggregate(meal, cat_aggs)
    compatible = []
    for key in DIET_KEYS:
        rule = DIETS[key]
        if "excludedCategories" in rule:
            if any(c in cats for c in rule["excludedCategories"]):
                continue
        if "nutrientMin" in rule:
            if not meal_agg:
                continue
            if not all(meal_agg.get(n, 0) >= v for n, v in rule["nutrientMin"].items()):
                continue
        if "nutrientMax" in rule:
            if not meal_agg:
                continue
            if not all(meal_agg.get(n, float("inf")) <= v for n, v in rule["nutrientMax"].items()):
                continue
        compatible.append(key)
    return compatible


def main():
    ingredients = json.loads(INGREDIENTS_PATH.read_text(encoding="utf-8"))
    meals = json.loads(MEALS_PATH.read_text(encoding="utf-8"))

    cat_aggs = category_aggregates(ingredients)

    counts = defaultdict(int)
    for meal in meals:
        meal["diet_compatibility"] = diet_compatibility(meal, cat_aggs)
        if "frequency" not in meal:
            meal["frequency"] = 1
        if "source" not in meal:
            meal["source"] = "curated"
        for k in meal["diet_compatibility"]:
            counts[k] += 1

    MEALS_PATH.write_text(
        json.dumps(meals, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Backfilled {len(meals)} meals.")
    print("Diet compatibility counts:")
    for k in DIET_KEYS:
        print(f"  {k:14s} {counts[k]:4d} / {len(meals)}")


if __name__ == "__main__":
    main()
