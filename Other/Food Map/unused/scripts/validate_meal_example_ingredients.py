#!/usr/bin/env python3
"""Validate the `example_ingredients` field on every meal (Batch 2).

Hard checks (exit 1 on any failure):
  - every meal has a non-empty example_ingredients list of strings
  - every id resolves to a real ingredient in ingredients.json
  - every meal category (except the incidental flavoring categories that are
    intentionally not default-filled) is represented by >=1 example ingredient
    whose own category matches it
  - no duplicate ids within a meal

Soft report (never fails):
  - "hero" ingredients: example ingredients whose category is NOT one of the
    meal's ingredient_categories. These are deliberate — a headline ingredient
    named in the dish title (e.g. banana in "Banana bread", which the project
    files under Temperate fruits while the meal tags Tropical). Reported so a
    reviewer can eyeball them, but allowed.

Run: python scripts/validate_meal_example_ingredients.py
"""
from __future__ import annotations

import io
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data"
MEAL_FILES = ["meals.json", "compositional-meals.json", "corpus-titled-meals.json"]

# Mirror of gen_meal_example_ingredients.py: categories not default-filled, so
# a meal may legitimately list them without an example ingredient.
SKIP_DEFAULT_CATEGORIES = {
    "Extracts & essences", "Pastes & ferments", "Pickled vegetables",
}


def load(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    ingredients = load(DATA / "ingredients.json")
    cat_of = {ing["id"]: ing["category"] for ing in ingredients}
    by_id = {ing["id"]: ing for ing in ingredients}

    errors = []
    hero_count = 0
    meal_count = 0
    ex_total = 0
    hero_samples = []

    for fn in MEAL_FILES:
        meals = load(DATA / fn)
        for m in meals:
            meal_count += 1
            mid = m.get("id", "?")
            ex = m.get("example_ingredients")
            cats = set(m.get("ingredient_categories") or [])

            if not isinstance(ex, list) or len(ex) == 0:
                errors.append(f"[{fn}] {mid}: missing/empty example_ingredients")
                continue
            if len(ex) != len(set(ex)):
                dupes = [i for i, c in Counter(ex).items() if c > 1]
                errors.append(f"[{fn}] {mid}: duplicate ids {dupes}")

            ex_total += len(ex)
            covered = set()
            for iid in ex:
                if not isinstance(iid, str) or iid not in by_id:
                    errors.append(f"[{fn}] {mid}: unknown ingredient id {iid!r}")
                    continue
                c = cat_of[iid]
                covered.add(c)
                if c not in cats:
                    hero_count += 1
                    if len(hero_samples) < 25:
                        hero_samples.append(f"[{fn}] {m.get('name')}: "
                                            f"{by_id[iid]['name']} ({c} not in meal cats)")

            # Coverage: every non-skip meal category should have a representative.
            for c in cats:
                if c in SKIP_DEFAULT_CATEGORIES:
                    continue
                if c not in covered:
                    errors.append(f"[{fn}] {mid}: category {c!r} has no example ingredient")

    print("=" * 72)
    print(" MEAL example_ingredients VALIDATION")
    print("=" * 72)
    print(f"Meals checked:        {meal_count}")
    print(f"Example ids total:    {ex_total}  (avg {ex_total / max(1, meal_count):.2f}/meal)")
    print(f"Hero ids (out-of-cat):{hero_count}")
    print(f"Hard errors:          {len(errors)}")
    print()
    if hero_samples:
        print("--- Hero samples (allowed; headline ingredient outside meal cats) ---")
        for s in hero_samples:
            print(f"  {s}")
        print()
    if errors:
        print("ERRORS:")
        for e in errors[:60]:
            print(f"  {e}")
        if len(errors) > 60:
            print(f"  ... and {len(errors) - 60} more")
        print("\n FAILED")
        return 1
    print(" PASSED — all example_ingredients resolve and every core category is covered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
