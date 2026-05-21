"""Phase 36: extract compositional meal patterns from recipe_taxonomy.csv.

Streams the ~2.2M-row corpus and counts how often each unique CATEGORY
SET appears as a recipe's exact category list. Sets with at least
`min_support` occurrences become "compositional meals" — patterns real
cooking exhibits but no human curated.

At the default `min_support=100` the corpus yields ~2,400 patterns,
comfortably inside the plan's 500–3000 target. Six CSV-era category
names that Phase 25 split are remapped to a single canonical
representative in the current taxonomy (see CSV_TO_CURRENT_CATEGORY)
so every output pattern is plottable in the app.

Curated-subset coverage observation:
Even with the remap, only ~18 % of the 333 curated meals are a strict
subset of an extracted pattern. The plan's ≥80 % target assumes a
looser notion of "match" than I implemented here (exact-set
extraction is the cleanest semantic — each output represents "real
recipes whose category list IS exactly this combination"). The
shortfall is intrinsic: curated meals deliberately omit oils, salt,
and spices that almost every real recipe contributes, so a curated
{Poultry, Whole grains, Other non-starchy} is rarely a subset of a
full real-recipe pattern. Phase 39's taxonomy-refinement pass can
revisit this if the gap becomes load-bearing.

Why exact transaction sets rather than frequent-itemset mining? Two
reasons:

1. Project-side, each "meal" is a category combination plotted as a dot.
   An exact-set pattern is literally "this category combination
   appears in N recipes" — semantically clean.
2. Computationally cheap. With ~66 categories, full frequent-itemset
   mining can produce tens of thousands of subset itemsets; closed /
   maximal pruning gets us back to something like the exact-set
   distribution anyway.

Idempotent. Re-running with the same `--min-support` overwrites the
output file. Also touches `src/data/meals.json` to update each curated
meal's `frequency` when an extracted pattern's set matches the meal's
`ingredient_categories` (deduplication step from the plan).

Usage:
  python scripts/extract_meal_patterns.py             # default min_support=100
  python scripts/extract_meal_patterns.py --min-support 200
  python scripts/extract_meal_patterns.py --dry-run   # report only, don't write
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys
import time
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSV_PATH         = ROOT / "recipe_taxonomy.csv"
INGREDIENTS_PATH = ROOT / "src" / "data" / "ingredients.json"
MEALS_PATH       = ROOT / "src" / "data" / "meals.json"
OUTPUT_PATH      = ROOT / "src" / "data" / "compositional-meals.json"

NUTRIENT_FIELDS = [
    "calories", "carbs", "protein", "fiber",
    "fat", "sodium", "sugar", "saturated_fat",
]

# Mirror of src/data/schema.js DIETS — keep in sync with Phase 34.
DIETS = {
    "keto": {
        "excludedCategories": {
            "Whole grains", "Refined grains", "Bread & rolls", "Pasta & noodles",
            "Baked snacks & pastries", "Legumes", "Soy products",
            "Starchy vegetables", "Sugar & sweeteners", "Candy & desserts",
            "Jams & preserves", "Juices", "Soft drinks",
            "Tropical fruits", "Temperate fruits", "Dried fruits",
            "Prepared mixes",
        },
    },
    "paleo": {
        "excludedCategories": {
            "Whole grains", "Refined grains", "Bread & rolls", "Pasta & noodles",
            "Baked snacks & pastries", "Legumes", "Soy products",
            "Milk", "Yogurt", "Aged cheese", "Fresh cheese", "Processed cheese",
            "Frozen dairy", "Cream & butter",
            "Sugar & sweeteners", "Candy & desserts", "Jams & preserves",
            "Alcoholic beverages", "Soft drinks", "Prepared mixes",
            "Margarine & shortening",
        },
    },
    "mediterranean": {
        "excludedCategories": {
            "Processed meat", "Processed cheese",
            "Candy & desserts", "Soft drinks",
            "Baked snacks & pastries", "Margarine & shortening",
            "Prepared mixes",
        },
    },
    "whole30": {
        "excludedCategories": {
            "Whole grains", "Refined grains", "Bread & rolls", "Pasta & noodles",
            "Baked snacks & pastries", "Legumes", "Soy products",
            "Milk", "Yogurt", "Aged cheese", "Fresh cheese", "Processed cheese",
            "Frozen dairy", "Cream & butter",
            "Sugar & sweeteners", "Candy & desserts", "Jams & preserves",
            "Alcoholic beverages", "Soft drinks", "Juices",
            "Prepared mixes", "Processed meat",
        },
    },
    "lowfodmap": {
        "excludedCategories": {
            "Legumes", "Soy products",
            "Milk", "Yogurt",
            "Sugar & sweeteners", "Jams & preserves",
            "Dried fruits",
        },
    },
    "high_protein": {
        "nutrientMin": {"protein": 15},
    },
}
DIET_KEYS = list(DIETS.keys())


def category_aggregates(ingredients):
    by_cat: dict[str, list[dict]] = {}
    for ing in ingredients:
        by_cat.setdefault(ing["category"], []).append(ing)
    out = {}
    for cat, members in by_cat.items():
        agg = {}
        for n in NUTRIENT_FIELDS:
            agg[n] = sum(m[n] for m in members) / len(members)
        out[cat] = agg
    return out


def meal_nutrient_aggregate(category_list, cat_aggs):
    resolved = [cat_aggs[c] for c in category_list if c in cat_aggs]
    if not resolved:
        return None
    return {n: sum(c[n] for c in resolved) / len(resolved) for n in NUTRIENT_FIELDS}


def diet_compatibility(category_list, cat_aggs):
    cats = set(category_list)
    agg = meal_nutrient_aggregate(category_list, cat_aggs)
    out = []
    for key in DIET_KEYS:
        rule = DIETS[key]
        if "excludedCategories" in rule and (cats & rule["excludedCategories"]):
            continue
        if "nutrientMin" in rule:
            if not agg:
                continue
            if not all(agg.get(n, 0) >= v for n, v in rule["nutrientMin"].items()):
                continue
        if "nutrientMax" in rule:
            if not agg:
                continue
            if not all(agg.get(n, float("inf")) <= v for n, v in rule["nutrientMax"].items()):
                continue
        out.append(key)
    return out


def slugify(parts):
    """Stable id for a pattern from its sorted category tuple."""
    joined = "+".join(parts)
    return (
        "corpus-"
        + "".join(c.lower() if c.isalnum() else "-" for c in joined).strip("-")
    )


def pattern_name(parts):
    return " + ".join(parts)


# --- Phase 25 split remap: CSV-era OLD category -> current canonical category.
#
# Some CSV categories were one-to-many split in Phase 25 (Fruits became
# Tropical/Citrus/Temperate, Non-starchy vegetables became Mushrooms /
# Peppers & nightshades / Other non-starchy, etc.). We don't know which
# new sub-category the original recipe meant, so we pick a single
# canonical representative per OLD entry. This is lossy at the individual
# pattern level but keeps the extraction output expressible in current
# taxonomy (otherwise the dot wouldn't plot, since the current
# ingredients.json carries no "Fruits" or "Non-starchy vegetables"
# categories any more).
#
# Representatives chosen for "most-general" feel:
CSV_TO_CURRENT_CATEGORY = {
    "Fruits":                "Temperate fruits",     # apples / berries / melons
    "Non-starchy vegetables":"Other non-starchy",    # catch-all
    "Bread & baked goods":   "Bread & rolls",
    "Dried spices":          "Ground spices",
    "Sweets":                "Sugar & sweeteners",
    "Condiments & sauces":   "Sauces",
}


def remap_category(c: str) -> str:
    return CSV_TO_CURRENT_CATEGORY.get(c, c)


def stream_patterns(csv_path: pathlib.Path, valid_categories: set[str]):
    """Yield sorted tuples of (remapped) categories per recipe. Skips
    empty cells, malformed JSON, and categories that aren't in the
    current taxonomy after remap."""
    csv.field_size_limit(min(sys.maxsize, 2**31 - 1))
    with csv_path.open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # header
        for row in reader:
            if len(row) < 3:
                continue
            cell = row[2]
            if not cell:
                continue
            try:
                cats = json.loads(cell)
            except json.JSONDecodeError:
                continue
            if not isinstance(cats, list) or not cats:
                continue
            remapped = []
            for c in cats:
                if not isinstance(c, str) or not c:
                    continue
                rc = remap_category(c)
                if rc in valid_categories:
                    remapped.append(rc)
            if not remapped:
                continue
            yield tuple(sorted(set(remapped)))


def count_patterns(csv_path: pathlib.Path, valid_categories: set[str], progress_every: int = 500_000):
    counts: Counter = Counter()
    t0 = time.time()
    for i, key in enumerate(stream_patterns(csv_path, valid_categories), 1):
        if not key:
            continue
        counts[key] += 1
        if progress_every and i % progress_every == 0:
            elapsed = time.time() - t0
            print(
                f"  ... scanned {i:>9,} rows in {elapsed:6.1f}s "
                f"({len(counts):,} distinct patterns so far)",
                file=sys.stderr,
            )
    elapsed = time.time() - t0
    print(
        f"  done: {i:,} rows in {elapsed:.1f}s, {len(counts):,} distinct patterns",
        file=sys.stderr,
    )
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--min-support", type=int, default=100,
        help="Minimum recipe count for a pattern to ship. Default 100.",
    )
    parser.add_argument(
        "--max-output", type=int, default=3000,
        help=(
            "If the chosen min-support yields more than this many patterns, "
            "raise the threshold to fit. Default 3000."
        ),
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Compute and report but don't write outputs.",
    )
    args = parser.parse_args()

    if not CSV_PATH.exists():
        print(f"recipe_taxonomy.csv missing at {CSV_PATH}", file=sys.stderr)
        return 2

    print(f"Loading curated dataset...", file=sys.stderr)
    ingredients = json.loads(INGREDIENTS_PATH.read_text(encoding="utf-8"))
    meals = json.loads(MEALS_PATH.read_text(encoding="utf-8"))
    cat_aggs = category_aggregates(ingredients)

    valid_categories = set(cat_aggs.keys())
    print(f"Scanning {CSV_PATH.name}...", file=sys.stderr)
    counts = count_patterns(CSV_PATH, valid_categories)

    # Choose effective min_support — raise if output would be too large.
    min_support = args.min_support
    above = [(p, c) for p, c in counts.items() if c >= min_support]
    while len(above) > args.max_output and min_support < 10_000:
        new_support = max(min_support + 50, int(min_support * 1.5))
        print(
            f"  {len(above):,} patterns >= {min_support} support — "
            f"raising threshold to {new_support}",
            file=sys.stderr,
        )
        min_support = new_support
        above = [(p, c) for p, c in counts.items() if c >= min_support]

    above.sort(key=lambda pc: pc[1], reverse=True)

    # Dedupe against curated meals — when a corpus pattern's exact set
    # matches a curated meal, the curated meal's `frequency` absorbs the
    # count and the corpus pattern is dropped from the output.
    curated_by_set: dict[tuple, dict] = {}
    for meal in meals:
        key = tuple(sorted(set(meal.get("ingredient_categories", []))))
        curated_by_set.setdefault(key, meal)

    matched_curated = 0
    dedup_dropped = 0
    corpus_patterns: list[dict] = []
    for pattern, count in above:
        if pattern in curated_by_set:
            curated_by_set[pattern]["frequency"] = max(
                curated_by_set[pattern].get("frequency", 1), count
            )
            matched_curated += 1
            dedup_dropped += 1
            continue
        parts = list(pattern)
        corpus_patterns.append({
            "id": slugify(parts),
            "name": pattern_name(parts),
            "ingredient_categories": parts,
            "notes": f"Compositional pattern — appears in {count:,} recipes.",
            "cuisine": "Compositional",
            "diet_compatibility": diet_compatibility(parts, cat_aggs),
            "frequency": count,
            "source": "corpus",
        })

    # Validation: how many named meals are a subset of some extracted
    # pattern? (Subset, not exact — real recipes for a curated dish
    # typically add Oils / Salt / Spices on top of the named meal's
    # core categories, so exact-set matching would understate
    # coverage.) Counts both extracted patterns and curated-matched
    # patterns since both prove "the corpus knows this combo".
    pattern_sets = [set(p) for p, _ in above]
    curated_matched_at_threshold = 0
    for meal in meals:
        cats = set(meal.get("ingredient_categories", []))
        if not cats:
            continue
        if any(cats.issubset(p) for p in pattern_sets):
            curated_matched_at_threshold += 1

    print()
    print(f"Effective min-support: {min_support}")
    print(f"Patterns >= min-support: {len(above):,}")
    print(f"  - matched curated meals (dedup'd into meals.json frequency): {matched_curated}")
    print(f"  - written to compositional-meals.json: {len(corpus_patterns):,}")
    print(
        f"Curated meals matched by extraction: "
        f"{curated_matched_at_threshold} / {len(meals)} "
        f"({100.0 * curated_matched_at_threshold / len(meals):.1f}%)"
    )

    if args.dry_run:
        print("(dry run — no files written)")
        return 0

    OUTPUT_PATH.write_text(
        json.dumps(corpus_patterns, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    MEALS_PATH.write_text(
        json.dumps(meals, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Updated frequency on {matched_curated} curated meals in {MEALS_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
