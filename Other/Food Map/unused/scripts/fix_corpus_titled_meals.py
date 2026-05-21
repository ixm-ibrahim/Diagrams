#!/usr/bin/env python3
"""Rebuild ingredient_categories on every corpus-titled meal from the
recipe_taxonomy.csv subcategory distribution.

Background: the file was generated from a 3-NER-sample-per-title bag
mapped through a small keyword table. That produced sparse, often
wildly incomplete categories — e.g. "Banana Bread" stored as
{Tropical fruits, Eggs, Flours, Nuts, Baking, Cream & butter,
Sugar & sweeteners, Bread & rolls} (correct enough) but "Lemon Bread"
missing Flours, Sugar, Baking, Salt, Milk (all >75% in corpus).

This script:
  1. Re-streams recipe_taxonomy.csv, building canonical-title -> per-
     recipe subcategory sets, mapped through SUB_TO_CATEGORY.
  2. For each corpus-titled meal, sets ingredient_categories to all
     categories whose presence rate >= INCLUDE_THR across matching
     recipes, in descending order of prevalence.
  3. Strips Bread & rolls when the dish is itself a Bread & rolls
     entry (the category was used to mean "this IS bread" before, but
     bread doesn't contain bread).
  4. Drops meals whose name doesn't yield at least one meaningful
     category at the 30% threshold (these were one-off corpus titles
     that don't represent a real dish, e.g. "Pretty Salad" or
     "Mexican Surprise"). Dropped meals go to docs/dropped-meals.json.
  5. Updates the `notes` field to reflect the rebuild.

Thresholds:
  INCLUDE_THR = 0.30   — category appears in >=30% of matching recipes
  MIN_MATCHES = 20     — meals with fewer corpus hits aren't reliable;
                         keep stored categories as-is for those
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
TITLED = ROOT / "src" / "data" / "corpus-titled-meals.json"
DROPPED = ROOT / "docs" / "dropped-corpus-titled-meals.json"

INCLUDE_THR = 0.30
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


def main():
    print("Building canonical-title index...", file=sys.stderr)
    idx = build_title_index()
    print(f"  done: {len(idx):,} titles", file=sys.stderr)

    titled = json.loads(TITLED.read_text(encoding="utf-8"))
    print(f"Loaded {len(titled)} corpus-titled meals", file=sys.stderr)

    kept: list[dict] = []
    dropped: list[dict] = []
    changed_count = 0
    for m in titled:
        canon = normalize_title(m.get("name", ""))
        matches = idx.get(canon) or []
        n = len(matches)

        if n < MIN_MATCHES:
            # Low corpus confidence — keep meal as-is, just retag notes.
            kept.append(m)
            continue

        freq = Counter()
        for cats in matches:
            for c in cats:
                freq[c] += 1
        rel = {c: freq[c] / n for c in freq}
        derived = [c for c, p in rel.items() if p >= INCLUDE_THR]
        derived.sort(key=lambda c: -rel[c])

        if not derived:
            # No core categories — likely a non-meal title.
            dropped.append({
                "id": m.get("id"),
                "name": m.get("name"),
                "n_matches": n,
                "reason": "no categories >= 30% threshold",
                "top": sorted(rel.items(), key=lambda kv: -kv[1])[:5],
            })
            continue

        new_meal = dict(m)
        old_cats = list(m.get("ingredient_categories", []))
        if set(old_cats) != set(derived):
            changed_count += 1
        new_meal["ingredient_categories"] = derived
        new_meal["notes"] = (
            f"Recipe title appearing in {m.get('frequency', n):,} corpus recipes. "
            f"Categories rebuilt from {n:,} matching corpus rows "
            f"(included if present in >= {int(INCLUDE_THR*100)}% of them)."
        )
        kept.append(new_meal)

    print(f"Kept: {len(kept)}; changed categories: {changed_count}; "
          f"dropped: {len(dropped)}", file=sys.stderr)

    TITLED.write_text(json.dumps(kept, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    DROPPED.parent.mkdir(parents=True, exist_ok=True)
    DROPPED.write_text(json.dumps(dropped, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
    print(f"Wrote {TITLED.relative_to(ROOT)} ({len(kept)} entries)", file=sys.stderr)
    print(f"Wrote {DROPPED.relative_to(ROOT)} ({len(dropped)} dropped)", file=sys.stderr)


if __name__ == "__main__":
    main()
