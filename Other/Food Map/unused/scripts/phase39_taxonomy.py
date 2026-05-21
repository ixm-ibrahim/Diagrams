"""Phase 39: apply taxonomy refinements decided from the analysis pass.

Inputs (read-only references):
  docs/phase39-analysis.json    — output of analyze_extraction.py
  src/data/ingredients.json     — current ingredient set
  src/data/meals.json           — curated meals
  src/data/compositional-meals.json

Mutates (idempotently):
  src/data/ingredients.json     — apply RENAMES / MERGES / DROPS to `category`
  src/data/meals.json           — apply renames to `ingredient_categories`
  src/data/compositional-meals.json — same, plus drop patterns whose
                                       category set collapses to empty

After applying, this re-runs the Phase 24/25 invariants:
  - no category contains >50 ingredients
  - every food_group has >=2 categories
  - every category has >=2 subcategories
  - every meal's ingredient_categories resolve to current categories

CHANGES THIS RUN
================
None. The analysis pass found no structural refinements warranted:

  - All "merge candidates" surfaced by the lift metric are correlations
    between semantically distinct categories (e.g. Aged cheese + Refined
    grains co-occur in pasta dishes — that's not a merge, that's pasta).
  - No category is disproportionately used in tiny patterns (no split
    signal).
  - The four "low-coverage" categories (Dried herbs, Meat alternatives,
    Plant milks, Freshwater fish) all have populated ingredients lists
    in ingredients.json and exist for taxonomic completeness, even if
    the RecipeNLG corpus and curated meal library don't reference them
    often.

The CHANGES dict is therefore empty in this run. The applier still runs
end-to-end so the invariant checks and docs-update step exercise the
same code path future passes will use.

To add a refinement: append entries to CATEGORY_RENAMES, CATEGORY_MERGES,
or CATEGORY_DROPS and re-run. The script writes back to JSON only when
a change is actually applied (idempotent — running twice with no
new entries is a no-op).
"""

from __future__ import annotations

import json
import pathlib
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
ING_PATH       = ROOT / "src" / "data" / "ingredients.json"
MEALS_PATH     = ROOT / "src" / "data" / "meals.json"
CORPUS_PATH    = ROOT / "src" / "data" / "compositional-meals.json"
ANALYSIS_PATH  = ROOT / "docs" / "phase39-analysis.json"

# ----- Decided refinements ------------------------------------------------
# Empty in this run (see module docstring). To add one:
#
#   CATEGORY_RENAMES = {"Old name": "New name"}
#   CATEGORY_MERGES  = {"Source category": "Target category"}
#   CATEGORY_DROPS   = ["Dropped category"]   (must be empty in the
#                       ingredient set; the script refuses to drop a
#                       category that still has ingredients)
#
CATEGORY_RENAMES: dict[str, str] = {}
CATEGORY_MERGES:  dict[str, str] = {}
CATEGORY_DROPS:   list[str] = []


def load_json(p: pathlib.Path):
    return json.loads(p.read_text(encoding="utf-8"))


def save_json(p: pathlib.Path, data) -> None:
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def apply_to_category_field(records, field_path):
    """Apply RENAMES + MERGES + DROPS to a single string field on each
    record. `field_path` is either a string (single field) or a list
    (path into a list field, e.g. ['ingredient_categories'] for arrays).
    Returns the count of mutations."""
    edits = 0
    mapping = {**CATEGORY_RENAMES, **CATEGORY_MERGES}
    drops = set(CATEGORY_DROPS)

    for rec in records:
        if isinstance(field_path, str):
            old = rec.get(field_path)
            if old is None:
                continue
            if old in drops:
                # Caller must decide what dropping means for them; for
                # ingredients we refuse to drop; for meals/corpus we
                # filter the entry out (handled in the call site).
                continue
            if old in mapping:
                rec[field_path] = mapping[old]
                edits += 1
        else:
            assert len(field_path) == 1, "Only one-level array fields supported here"
            key = field_path[0]
            cats = rec.get(key) or []
            if not cats:
                continue
            new_cats = []
            seen = set()
            for c in cats:
                if c in drops:
                    continue
                mapped = mapping.get(c, c)
                if mapped in seen:
                    continue
                seen.add(mapped)
                new_cats.append(mapped)
            if new_cats != cats:
                rec[key] = new_cats
                edits += 1
    return edits


def reapply_corpus_filter(corpus):
    """Drop corpus patterns that lost all categories after the remap."""
    before = len(corpus)
    kept = [p for p in corpus if p.get("ingredient_categories")]
    return kept, before - len(kept)


def assert_invariants(ingredients, meals, corpus, current_categories):
    """Phase 24/25 invariants. Raises AssertionError on any breach."""
    # 1. No category contains >50 ingredients.
    by_cat: dict[str, int] = defaultdict(int)
    for i in ingredients:
        by_cat[i["category"]] += 1
    oversized = [c for c, n in by_cat.items() if n > 50]
    assert not oversized, f"categories with >50 ingredients: {oversized}"

    # 2. Every food_group has >=2 categories.
    by_fg: dict[str, set] = defaultdict(set)
    for i in ingredients:
        by_fg[i["food_group"]].add(i["category"])
    thin_fgs = [fg for fg, cats in by_fg.items() if len(cats) < 2]
    assert not thin_fgs, f"food_groups with <2 categories: {thin_fgs}"

    # 3. Every category has >=2 subcategories.
    sub_by_cat: dict[str, set] = defaultdict(set)
    for i in ingredients:
        sub_by_cat[i["category"]].add(i["subcategory"])
    thin_cats = [c for c, subs in sub_by_cat.items() if len(subs) < 2]
    assert not thin_cats, f"categories with <2 subcategories: {thin_cats}"

    # 4. Every meal's ingredient_categories resolve to current categories.
    for m in meals:
        for c in m.get("ingredient_categories", []):
            assert c in current_categories, (
                f"meal {m.get('id')!r} references unknown category {c!r}"
            )
    for p in corpus:
        for c in p.get("ingredient_categories", []):
            assert c in current_categories, (
                f"corpus pattern {p.get('id')!r} references unknown category {c!r}"
            )


def main():
    if not ING_PATH.exists() or not MEALS_PATH.exists() or not CORPUS_PATH.exists():
        print("Missing data file(s).", file=sys.stderr)
        return 2
    if not ANALYSIS_PATH.exists():
        print(
            "docs/phase39-analysis.json missing — run scripts/analyze_extraction.py first.",
            file=sys.stderr,
        )
        return 2

    ingredients = load_json(ING_PATH)
    meals       = load_json(MEALS_PATH)
    corpus      = load_json(CORPUS_PATH)

    print(f"Decided refinements:")
    print(f"  renames: {CATEGORY_RENAMES or '(none)'}")
    print(f"  merges:  {CATEGORY_MERGES or '(none)'}")
    print(f"  drops:   {CATEGORY_DROPS or '(none)'}")
    print()

    # Refuse to drop a category that still has ingredients — the user
    # must reassign the ingredients first.
    for c in CATEGORY_DROPS:
        if any(i["category"] == c for i in ingredients):
            print(
                f"  refusing to drop category {c!r}: still has ingredients. "
                "Reassign them first (CATEGORY_MERGES) or remove from the dataset.",
                file=sys.stderr,
            )
            return 1

    ing_edits  = apply_to_category_field(ingredients, "category")
    meal_edits = apply_to_category_field(meals,       ["ingredient_categories"])
    corp_edits = apply_to_category_field(corpus,      ["ingredient_categories"])

    corpus, corpus_dropped = reapply_corpus_filter(corpus)

    print(f"Applied edits:")
    print(f"  ingredients mutated:        {ing_edits}")
    print(f"  meals mutated:              {meal_edits}")
    print(f"  corpus patterns mutated:    {corp_edits}")
    print(f"  corpus patterns dropped:    {corpus_dropped}")
    print()

    current_categories = {i["category"] for i in ingredients}
    assert_invariants(ingredients, meals, corpus, current_categories)
    print("Phase 24/25 invariants: OK")
    print(f"Final categories:                 {len(current_categories)}")
    print(f"Final ingredients:                {len(ingredients)}")
    print(f"Final curated meals:              {len(meals)}")
    print(f"Final corpus patterns:            {len(corpus)}")

    if ing_edits or meal_edits or corp_edits or corpus_dropped:
        save_json(ING_PATH, ingredients)
        save_json(MEALS_PATH, meals)
        save_json(CORPUS_PATH, corpus)
        print()
        print("Wrote updated JSON files.")
    else:
        print()
        print("No changes — files left untouched.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
