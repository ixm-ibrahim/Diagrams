#!/usr/bin/env python3
"""Round-2 audit: re-derive every meal's ingredient_categories from the
recipe_taxonomy.csv SUBCATEGORY column (not the coarse `categories`
column the earlier extract used).

Why subcategory and not categories? The CSV's `categories` value
"Fruits" is a lumped bucket — apple, banana, mango, blueberry all map
to it. The project remaps "Fruits" -> "Temperate fruits" which is wrong
for banana / mango / pineapple. Subcategory preserves "Apple" /
"Banana" / "Strawberry" / etc., so the rebuilt classification actually
tracks what the recipe contains.

Inputs:
  recipe_taxonomy.csv          (2.23M corpus rows, pre-tagged)
  src/data/meals.json
  src/data/compositional-meals.json
  src/data/corpus-titled-meals.json
  scripts/audit_subcategory_map.py   (SUB_TO_CATEGORY)

Output:
  docs/meal-audit-v2.json — per meal: stored, corpus-derived,
                            n_matches, top categories with %, diff.
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
COMP = ROOT / "src" / "data" / "compositional-meals.json"
TITLED = ROOT / "src" / "data" / "corpus-titled-meals.json"
OUT = ROOT / "docs" / "meal-audit-v2.json"

# Same canonicalizer as extract_corpus_titles.py so title strings agree.
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


def categories_for_subcats(subs):
    """A subcategory list from one recipe -> a set of current categories."""
    out = set()
    for s in subs:
        cat = SUB_TO_CATEGORY.get(s)
        if cat:
            out.add(cat)
    return out


def build_title_index():
    """canonical title -> list of (category-set) per matching recipe.

    Streaming, holds every per-recipe set in memory only for titles
    referenced by our meal list (filtered later). For simplicity we
    keep them all — ~2.2M sets of <10 strings each ≈ 200MB which is
    fine on this machine.
    """
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
            cats = categories_for_subcats(subs)
            if cats:
                idx[canon].append(cats)
            if i % 500_000 == 0:
                print(f"  ... {i:,} rows, {len(idx):,} titles", file=sys.stderr)
    return idx


def audit(meals, file_tag, idx, core_thr=0.30, drop_thr=0.05):
    out = []
    for m in meals:
        name = m.get("name", "")
        stored = list(m.get("ingredient_categories", []))
        canon = normalize_title(name)
        matches = idx.get(canon) or []
        n = len(matches)
        freq = Counter()
        for cats in matches:
            for c in cats:
                freq[c] += 1
        rel = {c: freq[c] / n for c in freq} if n else {}
        core = sorted([c for c, p in rel.items() if p >= core_thr], key=lambda c: -rel[c])
        fluff = sorted([c for c in stored if rel.get(c, 0) < drop_thr],
                       key=lambda c: rel.get(c, 0))
        missing = [c for c in core if c not in stored]
        top = sorted(rel.items(), key=lambda kv: -kv[1])[:20]
        entry = {
            "id": m.get("id"),
            "name": name,
            "file": file_tag,
            "canonical_title": canon,
            "stored": stored,
            "n_matches": n,
            "top": [{"cat": c, "pct": round(p * 100, 1)} for c, p in top],
            "fluff": [{"cat": c, "pct": round(rel.get(c, 0) * 100, 1)} for c in fluff],
            "missing": [{"cat": c, "pct": round(rel.get(c, 0) * 100, 1)} for c in missing],
            "frequency": m.get("frequency"),
            "source": m.get("source"),
        }
        out.append(entry)
    return out


def main():
    print("Building canonical-title index from recipe_taxonomy.csv subcategories...",
          file=sys.stderr)
    idx = build_title_index()
    print(f"  done: {len(idx):,} canonical titles", file=sys.stderr)

    meals = json.loads(MEALS.read_text(encoding="utf-8"))
    comp = json.loads(COMP.read_text(encoding="utf-8"))
    titled = json.loads(TITLED.read_text(encoding="utf-8"))

    print(f"Auditing curated ({len(meals)}) / compositional ({len(comp)}) / "
          f"corpus-titled ({len(titled)})...", file=sys.stderr)
    a = audit(meals, "curated", idx)
    b = audit(comp, "compositional", idx)
    c = audit(titled, "corpus-titled", idx)

    all_entries = a + b + c
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(all_entries, indent=2, ensure_ascii=False),
                   encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(all_entries)} entries)", file=sys.stderr)


if __name__ == "__main__":
    main()
