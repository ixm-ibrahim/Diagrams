"""Phase 27 tooling: validate meal patterns against recipe_taxonomy.csv.

For each meal pattern (a list of project category names), stream the
2.2M-recipe CSV and count how many recipes contain ALL of the pattern's
categories. Use a NEW->OLD category remap because Phase 25 split several
categories that the CSV still names with the pre-split convention.

Usage:
  # Validate a single pattern from the CLI:
  python scripts/validate_meal_pattern.py "Poultry" "Whole grains" "Mushrooms"

  # Or validate every meal in meals.json (default):
  python scripts/validate_meal_pattern.py --all

Output: per-pattern recipe count + 3 sample titles. Streams the CSV; never
loads it into memory.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "recipe_taxonomy.csv"
MEALS_PATH = ROOT / "src" / "data" / "meals.json"

# Phase 25 split categories from a pre-split CSV-era taxonomy. To validate a
# new-category meal pattern against the CSV, we ask: "what CSV-era category
# names should we look for instead?" Each new -> old mapping is many-to-one
# (the old category) or many-to-many for the Bread/Spices/Sweets/Veg splits.
NEW_TO_OLD_CATEGORIES = {
    # Condiments & sauces (split)
    "Sauces": {"Condiments & sauces"},
    "Pastes & ferments": {"Condiments & sauces"},
    "Dressings & dips": {"Condiments & sauces"},
    # Fruits (split)
    "Tropical fruits": {"Fruits"},
    "Citrus": {"Fruits"},
    "Temperate fruits": {"Fruits"},
    # Bread & baked goods (split)
    "Bread & rolls": {"Bread & baked goods"},
    "Baked snacks & pastries": {"Bread & baked goods"},
    # Dried spices (split)
    "Whole spices": {"Dried spices"},
    "Ground spices": {"Dried spices"},
    "Dried herbs": {"Dried spices"},
    # Sweets (split)
    "Sugar & sweeteners": {"Sweets"},
    "Candy & desserts": {"Sweets"},
    # Non-starchy vegetables (split)
    "Mushrooms": {"Non-starchy vegetables"},
    "Peppers & nightshades": {"Non-starchy vegetables"},
    "Other non-starchy": {"Non-starchy vegetables"},
    # Protein (plant) / Legumes split — tofu/tempeh/etc. were Legumes in CSV.
    "Soy products": {"Legumes"},
    "Meat alternatives": {"Legumes"},
}


def remap_to_old(cat_name: str) -> set[str]:
    """Return set of CSV-era category names this new-category should match."""
    if cat_name in NEW_TO_OLD_CATEGORIES:
        return NEW_TO_OLD_CATEGORIES[cat_name]
    return {cat_name}  # not remapped — name didn't change


def count_pattern_matches(pattern: list[str], cap: int = 200000):
    """Stream the CSV and count recipes whose categories include ALL of the
    pattern's (remapped) categories. cap stops the scan early — for huge
    matches we don't need to count every one."""
    # Build the set-of-sets each pattern token wants to match.
    requirement_sets = [remap_to_old(p) for p in pattern]
    matches = 0
    samples: list[str] = []
    with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                cats = set(json.loads(row["categories"]))
            except Exception:
                continue
            ok = all(any(opt in cats for opt in req) for req in requirement_sets)
            if ok:
                matches += 1
                if len(samples) < 3:
                    samples.append(row["title"])
                if matches >= cap:
                    break
    return matches, samples


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pattern", nargs="*",
                    help="Meal category names to AND-match")
    ap.add_argument("--all", action="store_true",
                    help="Validate every meal in meals.json")
    args = ap.parse_args()

    if args.all:
        with MEALS_PATH.open("r", encoding="utf-8") as f:
            meals = json.load(f)
        # Single pass through the CSV — for each meal we keep a running
        # match count + 3 sample titles.
        requirements = [
            (m, [remap_to_old(c) for c in (m.get("ingredient_categories") or [])])
            for m in meals
        ]
        counts = {m["id"]: 0 for m in meals}
        samples: dict[str, list[str]] = {m["id"]: [] for m in meals}
        with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    cats = set(json.loads(row["categories"]))
                except Exception:
                    continue
                title = row["title"]
                for m, reqs in requirements:
                    if all(any(opt in cats for opt in req) for req in reqs):
                        counts[m["id"]] += 1
                        if len(samples[m["id"]]) < 3:
                            samples[m["id"]].append(title)
        low_match = []
        for m in meals:
            n = counts[m["id"]]
            sym = "OK " if n >= 10 else "LOW"
            pat = m.get("ingredient_categories") or []
            print(f"  [{sym}] {n:6d}  {m['id']:35s} {pat}")
            if n < 10:
                low_match.append((m["id"], n))
        print()
        print(f"Total meals: {len(meals)}, low-match (<10): {len(low_match)}")
        return 0

    if not args.pattern:
        print("Usage: validate_meal_pattern.py <cat> [<cat>...] | --all",
              file=sys.stderr)
        return 1
    n, samples = count_pattern_matches(args.pattern)
    print(f"Pattern: {args.pattern}")
    print(f"Recipe matches: {n}")
    print(f"Sample titles:")
    for s in samples:
        print(f"  - {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
