"""Comprehensive dataset validator + coverage reporter.

Mirrors src/data/schema.js's validateIngredient + validateDataset, plus extra
checks called out by the Phase 24 plan:
  - no duplicate ids
  - every food_group is in FOOD_GROUPS
  - every category has >=2 ingredients (warn on singletons)
  - every group_weights sums to 1.0 and has exactly one channel = 1
  - every nutrient is finite and >= 0
  - every `form` value is in FORMS
  - every `contains` tag is in CONTAINS_TAGS vocabulary
  - reports: per-food_group counts, largest categories, 3D octant distribution

Exit code: 0 if all checks pass; 1 otherwise.

Run: python scripts/validate_full_dataset.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ING_PATH = ROOT / "src" / "data" / "ingredients.json"

# Mirror of src/data/schema.js exports.
FOOD_GROUPS = [
    "Vegetables", "Fruits", "Grains", "Protein (animal)", "Protein (plant)",
    "Dairy", "Nuts & seeds", "Fats & oils", "Sweets", "Herbs & spices",
    "Condiments & sauces", "Beverages",
]

FORMS = {
    "fresh", "canned", "frozen", "dried", "cured", "cooked",
    "powdered", "paste", "pickled",
}

# Mirror of src/core/restrictions.js CONTAINS_TAGS.
CONTAINS_TAGS = {
    "meat", "fish", "shellfish", "pork", "dairy", "eggs", "gluten",
    "tree_nut", "peanut", "soy", "sesame", "alcohol", "honey",
    "animal_byproduct", "caffeine",
}

NUTRIENTS = [
    "calories", "carbs", "protein", "fiber", "fat",
    "sodium", "sugar", "saturated_fat",
]

REQUIRED = ["id", "name", "category", "subcategory", "food_group",
            "contains", "group_weights", "examples", *NUTRIENTS, "notes"]

GROUP_WEIGHT_TOLERANCE = 1e-3


def is_finite_number(v):
    return isinstance(v, (int, float)) and v == v and abs(v) < float("inf")


def validate_one(i, ing):
    errors = []
    if not isinstance(ing, dict):
        return [(i, "?", "<root>", "ingredient is not an object")]
    iid = ing.get("id", "?")

    for f in REQUIRED:
        if f not in ing:
            errors.append((i, iid, f, "missing required field"))

    for f in ("id", "name", "category", "subcategory", "food_group", "notes"):
        if f in ing and not isinstance(ing[f], str):
            errors.append((i, iid, f, "must be a string"))

    if "food_group" in ing and isinstance(ing["food_group"], str) \
            and ing["food_group"] not in FOOD_GROUPS:
        errors.append((i, iid, "food_group", f"not in FOOD_GROUPS: {ing['food_group']!r}"))

    if "examples" in ing:
        if not isinstance(ing["examples"], list):
            errors.append((i, iid, "examples", "must be a list"))

    if "contains" in ing:
        if not isinstance(ing["contains"], list):
            errors.append((i, iid, "contains", "must be a list"))
        else:
            for t in ing["contains"]:
                if not isinstance(t, str):
                    errors.append((i, iid, "contains", "must contain only strings"))
                elif t not in CONTAINS_TAGS:
                    errors.append((i, iid, "contains", f"unknown tag {t!r}"))

    if "group_weights" in ing:
        gw = ing["group_weights"]
        if not (isinstance(gw, list) and len(gw) == 3
                and all(is_finite_number(x) for x in gw)):
            errors.append((i, iid, "group_weights", "must be a 3-num finite array"))
        else:
            s = gw[0] + gw[1] + gw[2]
            if abs(s - 1.0) > GROUP_WEIGHT_TOLERANCE:
                errors.append((i, iid, "group_weights", f"sum={s:.4f} (must be 1.0)"))
            # Single-group rule
            ones = sum(1 for x in gw if x == 1)
            zeros = sum(1 for x in gw if x == 0)
            if ones != 1 or zeros != 2:
                errors.append((i, iid, "group_weights",
                              f"violates single-group rule: {gw}"))

    for nf in NUTRIENTS:
        if nf not in ing:
            continue
        v = ing[nf]
        if not is_finite_number(v):
            errors.append((i, iid, nf, "must be finite number"))
        elif v < 0:
            errors.append((i, iid, nf, f"must be >= 0 (got {v})"))

    if "form" in ing and ing["form"] is not None:
        if not isinstance(ing["form"], str):
            errors.append((i, iid, "form", "must be a string"))
        elif ing["form"] not in FORMS:
            errors.append((i, iid, "form", f"not in FORMS: {ing['form']!r}"))

    return errors


def main() -> int:
    with ING_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print("ERROR: dataset is not an array", file=sys.stderr)
        return 1

    all_errors = []
    seen_ids: dict[str, int] = {}

    for i, ing in enumerate(data):
        for err in validate_one(i, ing):
            all_errors.append(err)
        if isinstance(ing, dict) and isinstance(ing.get("id"), str):
            iid = ing["id"]
            if iid in seen_ids:
                all_errors.append((i, iid, "id",
                                   f"duplicate of index {seen_ids[iid]}"))
            else:
                seen_ids[iid] = i

    # --- Coverage analysis ---
    fg_counts = Counter(ing.get("food_group") for ing in data)
    cat_counts: dict[tuple, list] = defaultdict(list)
    sub_counts: dict[tuple, list] = defaultdict(list)
    for ing in data:
        cat_counts[(ing.get("food_group"), ing.get("category"))].append(ing["id"])
        sub_counts[(ing.get("food_group"), ing.get("category"),
                    ing.get("subcategory"))].append(ing["id"])

    singletons_cat = {k: ids for k, ids in cat_counts.items() if len(ids) < 2}
    oversized_cat = {k: ids for k, ids in cat_counts.items() if len(ids) > 50}
    fg_without_two_cats = []
    for fg in FOOD_GROUPS:
        cats_in_fg = {c for (fg2, c) in cat_counts if fg2 == fg}
        if len(cats_in_fg) < 2:
            fg_without_two_cats.append((fg, len(cats_in_fg)))

    # 3D octant distribution: split each food's normalized position by axis median
    cals = [ing["calories"] for ing in data if isinstance(ing.get("calories"), (int, float))]
    carbs = [ing["carbs"] for ing in data if isinstance(ing.get("carbs"), (int, float))]
    prots = [ing["protein"] for ing in data if isinstance(ing.get("protein"), (int, float))]
    med_cal = sorted(cals)[len(cals) // 2]
    med_carb = sorted(carbs)[len(carbs) // 2]
    med_prot = sorted(prots)[len(prots) // 2]
    octants = Counter()
    for ing in data:
        c = (1 if ing["calories"] > med_cal else 0,
             1 if ing["carbs"] > med_carb else 0,
             1 if ing["protein"] > med_prot else 0)
        octants[c] += 1

    # --- Print report ---
    print("=" * 72)
    print(" DATASET VALIDATION REPORT")
    print("=" * 72)
    print(f"Total ingredients: {len(data)}")
    print(f"Schema errors:     {len(all_errors)}")
    print()

    if all_errors:
        print("ERRORS:")
        for idx, iid, field, msg in all_errors[:50]:
            print(f"  [{idx}] {iid}.{field}: {msg}")
        if len(all_errors) > 50:
            print(f"  ... and {len(all_errors) - 50} more.")
        print()

    print("--- Per food_group ---")
    for fg in FOOD_GROUPS:
        print(f"  {fg:24s} {fg_counts.get(fg, 0)}")
    print()

    print(f"--- Category sizes ---")
    print(f"  Distinct categories:       {len(cat_counts)}")
    print(f"  Distinct subcategories:    {len(sub_counts)}")
    print(f"  Categories with 1 entry:   {len(singletons_cat)}")
    if singletons_cat:
        for k, ids in sorted(singletons_cat.items()):
            print(f"    {k}: {ids}")
    print(f"  Categories with >50 entries (Phase 25 split candidates): {len(oversized_cat)}")
    if oversized_cat:
        for k, ids in sorted(oversized_cat.items()):
            print(f"    {k[0]} / {k[1]}: {len(ids)} entries")
    print()

    print("--- food_groups with <2 categories ---")
    if fg_without_two_cats:
        for fg, n in fg_without_two_cats:
            print(f"  WARN: {fg} has only {n} category")
    else:
        print("  (all food_groups have >=2 categories)")
    print()

    print("--- 3D octant distribution (calories/carbs/protein medians) ---")
    for k in sorted(octants.keys()):
        marker = " <-- empty" if octants[k] == 0 else ""
        print(f"  {k}: {octants[k]}{marker}")
    print()

    print("--- Contains-tag usage ---")
    tag_counts = Counter()
    for ing in data:
        for t in ing.get("contains", []) or []:
            tag_counts[t] += 1
    for t in sorted(CONTAINS_TAGS):
        print(f"  {t:20s} {tag_counts.get(t, 0)}")
    unknown_tags = set(tag_counts) - CONTAINS_TAGS
    if unknown_tags:
        print(f"  UNKNOWN TAGS PRESENT: {unknown_tags}")
    print()

    print("--- Form usage ---")
    form_counts = Counter(ing.get("form") for ing in data if ing.get("form"))
    for f, c in sorted(form_counts.items()):
        print(f"  {f:12s} {c}")
    print(f"  (entries without form: {sum(1 for ing in data if not ing.get('form'))})")
    print()

    print("=" * 72)
    if all_errors:
        print(" FAILED — schema errors present")
        return 1
    print(" PASSED — no schema errors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
