"""Final sanity audit pass over all meal files.

Catches low-hanging issues that earlier auto-extraction passes might
have missed:

  - meals with <2 categories (too sparse to characterise the dish)
  - duplicate categories within one meal
  - categories that don't exist in the ingredient dataset
  - duplicate meal NAMES (case-insensitive) within a file
  - duplicate meal NAMES across files
  - meals whose name strongly implies a category that's missing
    (uses a small keyword → category map)

Writes a single JSON report to docs/meal-sanity-audit.json and prints
a summary. Read-only — does NOT modify any data file.

Run: python scripts/audit_meal_sanity.py
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ING_PATH = ROOT / "src" / "data" / "ingredients.json"
FILES = {
    "curated":       ROOT / "src" / "data" / "meals.json",
    "compositional": ROOT / "src" / "data" / "compositional-meals.json",
    "corpus-titled": ROOT / "src" / "data" / "corpus-titled-meals.json",
}
OUT = ROOT / "docs" / "meal-sanity-audit.json"

# Name-keyword → category mapping. Each tuple = (regex pattern,
# category that should be present if the pattern matches). Conservative;
# only flag when the name unambiguously implies a defining ingredient.
NAME_HINTS = [
    # Carb/grain dishes — "pasta", "spaghetti", "ramen", etc. — must
    # have a grain category.
    (r"\bspaghetti\b|\bmacaroni\b|\bpenne\b|\blinguine\b|\bfettuccine\b|\bramen\b|\bsoba\b|\budon\b|\blasagna\b",
     "Refined grains"),
    # Pizza must have a bread/dough category.
    (r"\bpizza\b",                                                  "Bread & rolls"),
    # Soups (singular form, not part of "soup-er" or "soup kitchen").
    (r"^soup\b|\bsoup$|\bsoup\b(?! kitchen| stock| green)|\bchowder\b|\bbisque\b",
     "Prepared soups & broths"),
    # Egg dishes.
    (r"\bomelet(te)?\b|\bfrittata\b|\bquiche\b|\bshakshuka\b",      "Eggs"),
    # Chicken-named dishes need poultry.
    (r"^chicken\b|\bchicken (?:soup|salad|pot pie|tikka|curry|wings|noodle)\b", "Poultry"),
    # Beef-named dishes.
    (r"^beef\b|\bsteak\b(?!s? sauce)|\bbeef bourguignon\b|\bbrisket\b", "Red meat"),
    # Coffee/tea drinks.
    (r"\bespresso\b|\blatte\b|\bcappuccino\b|\bmacchiato\b|^coffee\b",
     "Coffee & tea"),
    # Wine/beer/cocktail must have alcohol.
    (r"\b(red|white|rose|sparkling) wine\b|\bbeer\b|\bcocktail\b|\bmartini\b|\bmojito\b|\bmargarita\b|\bsangria\b",
     "Alcoholic beverages"),
    # Granola / oatmeal.
    (r"\bgranola\b|\boatmeal\b",                                    "Whole grains"),
    # Popcorn.
    (r"\bpopcorn\b",                                                "Whole grains"),
    # Hummus.
    (r"\bhummus\b",                                                 "Legumes"),
    # Tofu.
    (r"\btofu\b|\btempeh\b",                                        "Soy products"),
    # Jam/jelly preserves.
    (r"\bjelly sandwich\b|\bjam toast\b|\bpreserves on\b",          "Jams & preserves"),
    # Sushi/sashimi — fish.
    (r"^sushi\b|\bsashimi\b|\bnigiri\b",                            None),  # rice + fish; ambiguous primary
    # Risotto / pilaf / biryani — rice base.
    (r"\brisotto\b|\bpilaf\b|\bbiryani\b|\bjambalaya\b",            "Refined grains"),
]

# Compile.
NAME_HINTS_C = [(re.compile(p, re.I), c) for (p, c) in NAME_HINTS if c]


def load_categories():
    with open(ING_PATH, encoding="utf-8") as f:
        ings = json.load(f)
    return sorted({i["category"] for i in ings})


def audit():
    valid_cats = set(load_categories())

    by_file = {}
    all_names = defaultdict(list)   # lowercased name -> [(file, id)]
    issues = defaultdict(list)
    counts = {"total": 0, "files": {}}

    for label, path in FILES.items():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        by_file[label] = data
        counts["files"][label] = len(data)
        counts["total"] += len(data)
        local_names = Counter()
        for meal in data:
            mid   = meal.get("id", "?")
            name  = meal.get("name", "?")
            cats  = meal.get("ingredient_categories") or []
            lc    = name.strip().lower()
            local_names[lc] += 1
            all_names[lc].append((label, mid))

            if not isinstance(cats, list) or len(cats) == 0:
                issues["empty_categories"].append({"file": label, "id": mid, "name": name})
                continue
            if len(cats) < 2:
                issues["too_few_categories"].append({"file": label, "id": mid, "name": name, "categories": cats})
            seen = set()
            dups = []
            for c in cats:
                if c in seen:
                    dups.append(c)
                seen.add(c)
            if dups:
                issues["duplicate_categories"].append({"file": label, "id": mid, "name": name, "duplicates": dups})
            bad = [c for c in cats if c not in valid_cats]
            if bad:
                issues["unknown_categories"].append({"file": label, "id": mid, "name": name, "unknown": bad})

            # Name-hint mismatches.
            missing_hints = []
            for pat, hint_cat in NAME_HINTS_C:
                if pat.search(name) and hint_cat not in cats:
                    missing_hints.append(hint_cat)
            if missing_hints:
                issues["name_implies_missing_category"].append({
                    "file": label, "id": mid, "name": name,
                    "missing_implied": sorted(set(missing_hints)),
                    "stored": cats,
                })

        # In-file duplicate names.
        for lc, ct in local_names.items():
            if ct > 1:
                issues["duplicate_name_within_file"].append({"file": label, "name": lc, "count": ct})

    # Cross-file duplicate names.
    for lc, occurs in all_names.items():
        files = {o[0] for o in occurs}
        if len(files) > 1:
            issues["duplicate_name_across_files"].append({"name": lc, "occurrences": occurs})

    summary = {
        "counts": counts,
        "issue_counts": {k: len(v) for k, v in issues.items()},
        "issues": issues,
    }
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Audit complete — {OUT.relative_to(ROOT)}")
    print(f"Total meals: {counts['total']} ({', '.join(f'{k}={v}' for k,v in counts['files'].items())})")
    print()
    print("Issue counts:")
    for k, n in summary["issue_counts"].items():
        print(f"  {k:42s}  {n}")


if __name__ == "__main__":
    audit()
