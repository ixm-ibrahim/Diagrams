"""Phase 32: NLG-corpus coverage report.

For each recipe in recipe_taxonomy.csv, count how many of its `categories`
entries map to a category in the current ingredients.json (either directly,
or via the Phase 25 split remap). Report:
  - Total category-occurrences across the corpus
  - Mapped / unmapped counts
  - Coverage percent (target: >=95%)
  - Top-N most-frequent unmapped category names (gaps)

Also re-prints the Phase 24/25 dataset metadata for the README / CLAUDE.md
update.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "recipe_taxonomy.csv"
ING_PATH = ROOT / "src" / "data" / "ingredients.json"
MEALS_PATH = ROOT / "src" / "data" / "meals.json"


# Phase 25 split: OLD CSV-era category -> set of NEW current categories
# that absorbed it. If a CSV cell holds OLD, we count it as covered iff
# at least one NEW exists in the current dataset.
OLD_TO_NEW = {
    "Condiments & sauces": {"Sauces", "Pastes & ferments", "Dressings & dips"},
    "Fruits":               {"Tropical fruits", "Citrus", "Temperate fruits"},
    "Bread & baked goods":  {"Bread & rolls", "Baked snacks & pastries"},
    "Dried spices":         {"Whole spices", "Ground spices", "Dried herbs"},
    "Sweets":               {"Sugar & sweeteners", "Candy & desserts"},
    "Non-starchy vegetables": {"Mushrooms", "Peppers & nightshades", "Other non-starchy"},
}


def load_current_categories() -> set[str]:
    with ING_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return {ing["category"] for ing in data}


def main() -> int:
    current = load_current_categories()

    total_occurrences = 0
    mapped = 0
    unmapped_counts: Counter[str] = Counter()
    empty_recipes = 0
    total_recipes = 0

    with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_recipes += 1
            try:
                cats = json.loads(row["categories"])
            except Exception:
                continue
            if not cats:
                empty_recipes += 1
                continue
            for c in cats:
                total_occurrences += 1
                if c in current:
                    mapped += 1
                elif c in OLD_TO_NEW and OLD_TO_NEW[c] & current:
                    mapped += 1
                else:
                    unmapped_counts[c] += 1

    pct = (mapped / total_occurrences * 100) if total_occurrences else 0.0
    unmapped = total_occurrences - mapped

    print("=" * 72)
    print(" RecipeNLG COVERAGE REPORT")
    print("=" * 72)
    print(f"Recipes scanned:               {total_recipes:,}")
    print(f"Recipes with empty categories: {empty_recipes:,}")
    print(f"Total category-occurrences:    {total_occurrences:,}")
    print(f"Mapped to current dataset:     {mapped:,}  ({pct:.2f}%)")
    print(f"Unmapped:                      {unmapped:,}  ({100-pct:.2f}%)")
    print(f"Target:                        >=95% mapped  =>  "
          f"{'PASS' if pct >= 95 else 'FAIL'}")
    print()

    if unmapped_counts:
        print(f"--- Top 20 unmapped category names ---")
        for name, n in unmapped_counts.most_common(20):
            print(f"  {n:8d}  {name}")
    print()

    # Dataset metadata
    with ING_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    with MEALS_PATH.open("r", encoding="utf-8") as f:
        meals = json.load(f)

    fg_counts = Counter(ing["food_group"] for ing in data)
    cat_counts: dict[tuple, int] = defaultdict(int)
    sub_counts: dict[tuple, int] = defaultdict(int)
    for ing in data:
        cat_counts[(ing["food_group"], ing["category"])] += 1
        sub_counts[(ing["food_group"], ing["category"], ing["subcategory"])] += 1

    print("--- Dataset metadata ---")
    print(f"Ingredients:    {len(data):,}")
    print(f"Meals:          {len(meals):,}")
    print(f"Food groups:    {len(fg_counts)}")
    print(f"Categories:     {len(cat_counts)}")
    print(f"Subcategories:  {len(sub_counts)}")
    print()
    over = [(k, c) for k, c in cat_counts.items() if c > 50]
    if over:
        print(f"WARN: {len(over)} category(s) exceed 50 entries:")
        for k, c in over: print(f"  {k}: {c}")
    else:
        print("All categories have <=50 entries.")

    return 0 if pct >= 95 else 1


if __name__ == "__main__":
    sys.exit(main())
