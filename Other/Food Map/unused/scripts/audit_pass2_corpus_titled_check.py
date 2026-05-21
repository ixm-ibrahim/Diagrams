"""For corpus-titled meals, surface entries where the name and categories
look incongruent. Specifically:
  - Cake / cookie / pie / bread / muffin items that lack expected
    sweet-baking categories (Flours, Sugar & sweeteners)
  - Drink / juice / cocktail items that have major non-beverage tags
  - Meat-named dishes with no protein category
  - Dishes whose name suggests one cuisine but tags look wrong

For each flag, report the name, current categories, and the corpus
distribution so we can decide if a manual override is warranted.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from audit_pass2_index import load_index, normalize_title

MEALS = ROOT / "src" / "data" / "corpus-titled-meals.json"
OUT = ROOT / "docs" / "pass2-corpus-titled-flags.json"


SWEET_BAKED_TOKENS = ("cake", "cookie", "pie", "bread", "muffin",
                     "biscuit", "scone", "brownie", "cupcake", "tart",
                     "shortbread", "macaroon", "cobbler", "crisp",
                     "crumble", "loaf", "torte", "trifle")
DRINK_TOKENS = ("juice", "cocktail", "punch", "smoothie", "milkshake",
                "tea ", "tea,", "coffee ", "latte", "mocha",
                "soda", "fizz", "spritzer", "frappe", "shake", "lemonade",
                "limeade", "agua ", "drink", "cooler")
MEAT_TOKENS = ("chicken", "beef", "pork", "lamb", "turkey", "duck",
               "veal", "venison", "bacon", "sausage", "ham",
               "salmon", "tuna", "shrimp", "crab", "lobster")
PROTEIN_CATS = {"Poultry", "Red meat", "Processed meat", "Oily fish",
                "White fish", "Freshwater fish", "Shellfish",
                "Canned & cured fish", "Eggs", "Organ meats",
                "Legumes", "Soy products", "Meat alternatives", "Nuts"}
SWEET_BAKE_CATS = {"Flours", "Sugar & sweeteners", "Baking ingredients",
                  "Bread & rolls", "Baked snacks & pastries",
                  "Prepared mixes"}


def main():
    meals = json.loads(MEALS.read_text(encoding="utf-8"))
    idx = load_index()
    flags = []
    for m in meals:
        name = m["name"]
        nlow = name.lower()
        cats = set(m.get("ingredient_categories", []))
        kind = None

        if any(t in nlow for t in SWEET_BAKED_TOKENS):
            if not (cats & SWEET_BAKE_CATS) and "Cream & butter" not in cats:
                kind = "baked_without_baking_cats"

        if any(t in nlow for t in DRINK_TOKENS):
            heavy_food = cats & {"Red meat", "Poultry", "Eggs", "Oily fish",
                                  "White fish", "Shellfish", "Refined grains",
                                  "Whole grains", "Legumes", "Bread & rolls"}
            if heavy_food and "Juices" not in cats:
                kind = "drink_with_heavy_food_tags"

        if any(t in nlow for t in MEAT_TOKENS) and not (cats & PROTEIN_CATS):
            kind = "meat_named_no_protein"

        if kind:
            canon = normalize_title(name)
            matches = idx.get(canon) or []
            n = len(matches)
            freq = Counter()
            for s in matches:
                for c in s:
                    freq[c] += 1
            top = [(c, round(freq[c]/max(n,1), 3)) for c in freq]
            top.sort(key=lambda kv: -kv[1])
            flags.append({
                "name": name,
                "kind": kind,
                "current": sorted(cats),
                "corpus_n": n,
                "corpus_top": top[:15],
                "frequency": m.get("frequency"),
            })
    OUT.write_text(json.dumps(flags, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(flags)} flagged entries")
    by_kind = Counter(f["kind"] for f in flags)
    for k, v in by_kind.most_common():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
