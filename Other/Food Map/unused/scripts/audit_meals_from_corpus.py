#!/usr/bin/env python3
"""Audit every meal in meals.json / compositional-meals.json / corpus-titled-meals.json
against ground truth derived directly from the RecipeNLG corpus.

For each meal name, we:
  1. Normalize the title using the same rules extract_corpus_titles.py uses.
  2. Find all recipes in recipe_taxonomy.csv with a matching canonical title.
  3. Tally how often each category appears across those recipes.
  4. Compare the stored ingredient_categories to the corpus distribution.

Output: docs/meal-audit-report.json — one entry per meal with:
  { id, name, file, stored, n_matches, freq, top, fluff, missing }

Definitions:
  - "core"    : categories present in >= 50% of matching recipes
  - "fluff"   : stored categories present in <  10% of matching recipes
  - "missing" : core categories not stored

No project-side classifications are consulted; the corpus is the only source.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAXONOMY = ROOT / "recipe_taxonomy.csv"
MEALS = ROOT / "src" / "data" / "meals.json"
COMP = ROOT / "src" / "data" / "compositional-meals.json"
TITLED = ROOT / "src" / "data" / "corpus-titled-meals.json"
OUT = ROOT / "docs" / "meal-audit-report.json"

# Title normalization mirrors extract_corpus_titles.py so canonical
# title strings are comparable end-to-end.
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

CSV_TO_CURRENT_CATEGORY = {
    "Fruits":                "Temperate fruits",
    "Non-starchy vegetables":"Other vegetables",
    "Bread & baked goods":   "Bread & rolls",
    "Dried spices":          "Ground spices",
    "Sweets":                "Sugar & sweeteners",
    "Condiments & sauces":   "Sauces",
}


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


def remap_categories(cats):
    out = []
    seen = set()
    for c in cats:
        if not isinstance(c, str):
            continue
        rc = CSV_TO_CURRENT_CATEGORY.get(c, c)
        if rc not in seen:
            seen.add(rc)
            out.append(rc)
    return out


def build_title_index():
    """canonical title -> list of category-set lists (one per matching recipe)."""
    csv.field_size_limit(min(sys.maxsize, 2**31 - 1))
    idx: dict[str, list[list[str]]] = defaultdict(list)
    with TAXONOMY.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        for i, row in enumerate(reader, 1):
            if len(row) < 3:
                continue
            title = row[1]
            cell = row[2]
            if not title or not cell:
                continue
            canon = normalize_title(title)
            if not canon:
                continue
            try:
                cats = json.loads(cell)
            except json.JSONDecodeError:
                continue
            if not isinstance(cats, list) or not cats:
                continue
            idx[canon].append(remap_categories(cats))
            if i % 250_000 == 0:
                print(f"  ... {i:,} rows scanned, {len(idx):,} distinct canonical titles", file=sys.stderr)
    return idx


def audit(meals, file_tag, idx, core_thr=0.5, fluff_thr=0.10):
    out = []
    for m in meals:
        name = m.get("name", "")
        stored = list(m.get("ingredient_categories", []))
        canon = normalize_title(name)
        matches = idx.get(canon) or []
        n = len(matches)
        freq = Counter()
        for cats in matches:
            for c in set(cats):
                freq[c] += 1
        rel = {c: freq[c] / n for c in freq} if n else {}
        core = sorted([c for c, p in rel.items() if p >= core_thr], key=lambda c: -rel[c])
        fluff = sorted([c for c in stored if rel.get(c, 0) < fluff_thr], key=lambda c: rel.get(c, 0))
        missing = [c for c in core if c not in stored]
        top = sorted(rel.items(), key=lambda kv: -kv[1])[:15]
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
    print("Building canonical-title index from recipe_taxonomy.csv...", file=sys.stderr)
    idx = build_title_index()
    print(f"  done: {len(idx):,} canonical titles", file=sys.stderr)

    meals = json.loads(MEALS.read_text(encoding="utf-8"))
    comp  = json.loads(COMP.read_text(encoding="utf-8"))
    titled= json.loads(TITLED.read_text(encoding="utf-8"))

    print(f"Auditing {len(meals)} curated meals...", file=sys.stderr)
    a = audit(meals, "curated", idx)
    print(f"Auditing {len(comp)} compositional meals...", file=sys.stderr)
    b = audit(comp, "compositional", idx)
    print(f"Auditing {len(titled)} corpus-titled meals...", file=sys.stderr)
    c = audit(titled, "corpus-titled", idx)

    all_entries = a + b + c
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(all_entries, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(all_entries)} entries)", file=sys.stderr)


if __name__ == "__main__":
    main()
