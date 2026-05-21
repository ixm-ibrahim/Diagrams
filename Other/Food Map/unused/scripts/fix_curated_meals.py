#!/usr/bin/env python3
"""Audit-driven fixes for src/data/meals.json.

What this script does:
  1. Merges the two "Berry smoothie" duplicates into one entry whose
     categories track the corpus distribution.
  2. For every curated meal with >= 20 matching corpus recipes,
     replaces ingredient_categories with the corpus-derived set
     (categories present in >= 40% of matches), in prevalence order.
     The 40% bar (higher than the 30% used for the corpus-titled
     rebuild) is meant to preserve the curated dataset's "core dish
     concept" intent while still adding genuinely-defining categories
     the curator missed.
  3. Hand-fix dessert items where the curator used "Bread & rolls"
     for items that are actually cakes / sweets (corpus disagrees in
     each case, and putting a cake in the bread bucket distorts both
     the visualization color and the nutrition aggregation).
  4. Hand-fix Greek salad: Aged cheese -> Fresh cheese (feta is a
     fresh, brined cheese; the corpus and the project's own
     ingredients.json agree).

Skip rule:
  - Meals with < 20 corpus matches keep their stored categories. The
    corpus distribution is too noisy at that sample size to override
    a domain-curator's choice.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from audit_subcategory_map import SUB_TO_CATEGORY

TAXONOMY = ROOT / "recipe_taxonomy.csv"
MEALS = ROOT / "src" / "data" / "meals.json"
REPORT = ROOT / "docs" / "curated-fixes-report.json"

INCLUDE_THR = 0.40
MIN_MATCHES = 20

POSSESSIVE_PREFIXES = re.compile(
    r"^\s*("
    r"aunt|uncle|grandma|grandpa|granny|nana|mom|mama|mother|"
    r"dad|papa|father|"
    r"mrs|mr|ms|miss|"
    r"my|our|"
    r"best|easy|quick|simple|amazing|delicious|favorite|favourite|perfect|"
    r"super|ultimate|classic|original|traditional|homemade|home-made|home|"
    r"world|world's|grandmother's|grandma's|grandpa's|grandfather's|"
    r"mom's|mama's|mother's|dad's|papa's|father's|"
    r"the|a|an|"
    r"low-fat|low fat|low-carb|low carb|low-sodium|low sodium|"
    r"healthy|crockpot|crock-pot|crock pot|slow-cooker|slow cooker|"
    r"instant pot|microwave|easy peasy"
    r")\b[\s'.,!]+",
    re.IGNORECASE,
)
LEADING_POSSESSIVE = re.compile(r"^\s*[A-Z][a-zA-Z\-]+(\s+[A-Z][a-zA-Z\-]+)?'s\s+", re.UNICODE)
TRAILING_PAREN = re.compile(r"\s*[\(\[][^)\]]*[\)\]]\s*$")
TRAILING_DASH = re.compile(r"\s*[-:|]\s+.{1,40}$")
WHITESPACE = re.compile(r"\s+")


def normalize_title(raw: str) -> str:
    s = (raw or "").strip().strip("\"'")
    for _ in range(6):
        new = LEADING_POSSESSIVE.sub("", s)
        new = POSSESSIVE_PREFIXES.sub("", new)
        if new == s:
            break
        s = new
    s = TRAILING_PAREN.sub("", s)
    s = TRAILING_DASH.sub("", s)
    s = WHITESPACE.sub(" ", s).strip(" \t.,!\"'-")
    return s.title()


def build_title_index():
    csv.field_size_limit(min(sys.maxsize, 2**31 - 1))
    idx: dict[str, list[set]] = defaultdict(list)
    with TAXONOMY.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        for i, row in enumerate(reader, 1):
            if len(row) < 4:
                continue
            title = row[1]
            sub_cell = row[3]
            if not title or not sub_cell:
                continue
            canon = normalize_title(title)
            if not canon:
                continue
            try:
                subs = json.loads(sub_cell)
            except json.JSONDecodeError:
                continue
            if not isinstance(subs, list) or not subs:
                continue
            cats = set()
            for s in subs:
                c = SUB_TO_CATEGORY.get(s)
                if c:
                    cats.add(c)
            if cats:
                idx[canon].append(cats)
            if i % 500_000 == 0:
                print(f"  ... {i:,} rows, {len(idx):,} titles", file=sys.stderr)
    return idx


def corpus_derived(canon, idx):
    matches = idx.get(canon) or []
    n = len(matches)
    if n < MIN_MATCHES:
        return None, n
    freq = Counter()
    for cats in matches:
        for c in cats:
            freq[c] += 1
    rel = [(c, freq[c] / n) for c in freq]
    rel.sort(key=lambda kv: -kv[1])
    derived = [c for c, p in rel if p >= INCLUDE_THR]
    return derived, n


def main():
    print("Building canonical-title index...", file=sys.stderr)
    idx = build_title_index()
    print(f"  done: {len(idx):,} titles", file=sys.stderr)

    meals = json.loads(MEALS.read_text(encoding="utf-8"))
    print(f"Loaded {len(meals)} curated meals", file=sys.stderr)

    # ---- (1) Merge the Berry smoothie duplicate ----
    bs = [m for m in meals if m["name"].lower() == "berry smoothie"]
    if len(bs) > 1:
        keep = bs[0]
        keep["id"] = "berry-smoothie"
        # Both variants represent the same dish; let the corpus rebuild
        # set categories. Notes capture both descriptions.
        keep["notes"] = "Blended berries with yogurt and/or milk; honey optional."
        meals = [m for m in meals if m["name"].lower() != "berry smoothie"]
        meals.insert(13, keep)  # roughly the original first position
        print("Merged Berry smoothie duplicate", file=sys.stderr)

    # ---- (2) Rebuild via corpus where confidence is enough ----
    report: list[dict] = []
    changed = 0
    for m in meals:
        canon = normalize_title(m["name"])
        derived, n = corpus_derived(canon, idx)
        if derived is None:
            continue
        before = list(m.get("ingredient_categories", []))
        if set(before) != set(derived):
            m["ingredient_categories"] = derived
            changed += 1
            report.append({
                "name": m["name"],
                "n_matches": n,
                "before": before,
                "after": derived,
            })

    # ---- (3) Hand-fix dessert/cake misclassifications ----
    # The corpus puts these in "Baked snacks & pastries" (cake) territory,
    # not "Bread & rolls". Keep the dessert flavor; replace Bread with the
    # right shelf.
    HAND_FIXES = {
        "Carrot cake with cream cheese frosting": [
            "Flours", "Sugar & sweeteners", "Eggs", "Baking ingredients",
            "Starchy vegetables", "Ground spices", "Oils",
            "Extracts & essences", "Fresh cheese", "Cream & butter",
            "Salt & seasonings", "Nuts", "Tropical fruits",
        ],
        "Red velvet cake": [
            "Flours", "Sugar & sweeteners", "Eggs", "Baking ingredients",
            "Milk", "Extracts & essences", "Candy & desserts",
            "Cream & butter", "Fresh cheese", "Dressings & dips",
            "Salt & seasonings", "Margarine & shortening",
        ],
        "Tres leches cake": [
            "Flours", "Sugar & sweeteners", "Eggs", "Baking ingredients",
            "Milk", "Cream & butter", "Extracts & essences",
            "Salt & seasonings",
        ],
        # Crepes Suzette: thin pancakes flambéed in orange-butter sauce.
        # Not bread.
        "Crêpes Suzette": [
            "Flours", "Eggs", "Milk", "Sugar & sweeteners", "Citrus",
            "Cream & butter", "Alcoholic beverages",
        ],
        # Greek salad: feta is Fresh cheese, not Aged cheese.
        "Greek salad": [
            "Other vegetables", "Peppers & nightshades", "Pickled vegetables",
            "Fresh cheese", "Oils", "Fresh herbs", "Dressings & dips",
            "Salt & seasonings",
        ],
        # Mochi ice cream: mochi (sweet rice cake) wrapped around ice
        # cream. The "Refined grains" tag is correct for the rice flour,
        # but the dish is plotted way too rice-heavy without the sweet
        # tags. Adding Flours (mochiko) + Sugar.
        "Mochi ice cream": [
            "Flours", "Frozen dairy", "Sugar & sweeteners",
            "Starches", "Extracts & essences",
        ],
    }
    for m in meals:
        if m["name"] in HAND_FIXES:
            before = list(m.get("ingredient_categories", []))
            new = [c for c in HAND_FIXES[m["name"]] if c]
            # Drop any categories not in our taxonomy (defensive)
            from audit_subcategory_map import SUB_TO_CATEGORY as _smap
            VALID = set(v for v in _smap.values() if v)
            VALID |= {
                "Whole grains", "Refined grains", "Bread & rolls",
                "Baked snacks & pastries", "Flours", "Prepared mixes",
                "Cream & butter", "Aged cheese", "Fresh cheese",
                "Processed cheese", "Milk", "Plant milks", "Yogurt",
                "Fermented dairy", "Frozen dairy",
                "Margarine & shortening", "Oils",
                "Sugar & sweeteners", "Candy & desserts", "Jams & preserves",
                "Fresh herbs", "Dried herbs", "Ground spices", "Whole spices",
                "Spice blends", "Salt & seasonings", "Extracts & essences",
                "Sauces", "Dressings & dips", "Pastes & ferments",
                "Prepared soups & broths", "Baking ingredients",
                "Coffee & tea", "Juices", "Soft drinks", "Alcoholic beverages",
                "Leafy greens", "Cruciferous vegetables", "Peppers & nightshades",
                "Starchy vegetables", "Other vegetables", "Mushrooms",
                "Pickled vegetables", "Berries", "Citrus", "Tropical fruits",
                "Temperate fruits", "Dried fruits",
                "Red meat", "Poultry", "Organ meats", "Processed meat",
                "Eggs", "White fish", "Oily fish", "Freshwater fish",
                "Shellfish", "Canned & cured fish",
                "Legumes", "Soy products", "Meat alternatives",
                "Nuts", "Seeds", "Nut butters",
            }
            new = [c for c in new if c in VALID]
            if set(before) != set(new):
                m["ingredient_categories"] = new
                changed += 1
                report.append({
                    "name": m["name"],
                    "n_matches": None,
                    "before": before,
                    "after": new,
                    "kind": "hand-fix",
                })

    print(f"Changed {changed} meals; writing...", file=sys.stderr)
    MEALS.write_text(json.dumps(meals, indent=2, ensure_ascii=False) + "\n",
                     encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    print(f"Wrote {MEALS.relative_to(ROOT)} ({len(meals)} entries)", file=sys.stderr)
    print(f"Wrote {REPORT.relative_to(ROOT)} ({len(report)} changes)", file=sys.stderr)


if __name__ == "__main__":
    main()
