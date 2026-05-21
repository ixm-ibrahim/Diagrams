"""Optionally apply the high-confidence subset of audit_meal_sanity findings.

This is a *proposal* pass — by default it runs in dry-run mode and prints
what it WOULD change. Pass --apply to write the fixes back to the meal
JSON files.

Scope (only the unambiguous "name-implies-missing-category" cases):
  - "X soup" / "chowder" / "bisque"  → add  Prepared soups & broths
  - "pizza" / "fruit pizza"          → add  Bread & rolls
  - "spaghetti" / "lasagna" / "ramen" / "soba" / "udon" / "macaroni" /
    "penne" / "linguine" / "fettuccine"
                                     → add  Refined grains
  - "wine" / "beer" / "cocktail" / "martini" / "mojito" / "margarita" /
    "sangria"
                                     → add  Alcoholic beverages

Skips any meal where the category is already present. Does NOT touch
meals whose categories list is empty (those need human review).

Run:
  python scripts/audit_apply_name_implied_fixes.py            # dry run
  python scripts/audit_apply_name_implied_fixes.py --apply    # write
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = {
    "curated":       ROOT / "src" / "data" / "meals.json",
    "compositional": ROOT / "src" / "data" / "compositional-meals.json",
    "corpus-titled": ROOT / "src" / "data" / "corpus-titled-meals.json",
}

# (pattern, category to ensure present)
# Notes on false-positive exclusions:
#   - "spaghetti sauce" / "lasagna casserole" — these are sauces /
#     casseroles, not the noodle itself; the regex requires the dish
#     name to NOT be qualified by "sauce", "casserole" before grain
#     is added.
#   - "fruit cocktail" — canned mixed fruit, not a drink; excluded
#     from the alcohol pattern.
RULES = [
    (re.compile(r"\bsoup\b|\bchowder\b|\bbisque\b", re.I), "Prepared soups & broths"),
    (re.compile(r"\bpizza(?! casserole)\b", re.I),         "Bread & rolls"),
    (re.compile(r"^(?:spaghetti|macaroni|penne|linguine|fettuccine|ramen|soba|udon|lasagna)\b(?! sauce| casserole| pie)|\b(?:spaghetti|macaroni|penne|linguine|fettuccine|ramen|soba|udon|lasagna) (?:noodles|dish|bowl|salad|with)", re.I), "Refined grains"),
    (re.compile(r"\b(?:red|white|rose|sparkling) wine\b|\bbeer\b|\bmartini\b|\bmojito\b|\bmargarita\b|\bsangria\b", re.I), "Alcoholic beverages"),
]


def main(apply: bool):
    fixes = []
    for label, path in FILES.items():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        changed = False
        for meal in data:
            name = meal.get("name", "")
            cats = meal.get("ingredient_categories") or []
            if not cats:
                continue
            added_here = []
            for pat, cat in RULES:
                if pat.search(name) and cat not in cats:
                    cats.append(cat)
                    added_here.append(cat)
            if added_here:
                meal["ingredient_categories"] = cats
                fixes.append({"file": label, "id": meal.get("id"), "name": name, "added": added_here})
                changed = True
        if apply and changed:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")
            print(f"  wrote {path.relative_to(ROOT)}")

    print(f"{'APPLIED' if apply else 'DRY RUN'} — {len(fixes)} meals would change")
    for fx in fixes[:25]:
        print(f"  [{fx['file']:14s}] {fx['name']:42s} + {fx['added']}")
    if len(fixes) > 25:
        print(f"  ... and {len(fixes) - 25} more")

    out = ROOT / "docs" / "audit-name-implied-fixes.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"applied": apply, "fixes": fixes}, f, indent=2)
    print(f"Report: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main(apply=("--apply" in sys.argv))
