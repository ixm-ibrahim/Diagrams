#!/usr/bin/env python3
"""Audit helper for the manual example_ingredients review (tester follow-up).

Two outputs, no mutation:
  1. scripts/_audit_examples_catindex.txt
       category -> every ingredient id (name) in it. Grep this when picking a
       legitimate replacement for a wrong example.
  2. scripts/_audit_examples_review_<file>.txt
       per-meal review for one meal file: name, notes, and each example
       ingredient as "Category: name (id)" so the reviewer can see at a glance
       whether the pick actually fits the dish.

Usage:
  python scripts/audit_examples_dump.py catindex
  python scripts/audit_examples_dump.py review meals.json [start] [end]
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data"


def load(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def cat_index():
    ings = load(DATA / "ingredients.json")
    by_cat = defaultdict(list)
    for ing in ings:
        by_cat[ing["category"]].append((ing["id"], ing["name"]))
    out = []
    for cat in sorted(by_cat):
        out.append(f"### {cat}  ({len(by_cat[cat])})")
        for iid, name in sorted(by_cat[cat], key=lambda x: x[1]):
            out.append(f"    {iid:32s} {name}")
        out.append("")
    p = ROOT / "scripts" / "_audit_examples_catindex.txt"
    p.write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote {p}  ({len(by_cat)} categories)")


def review(fn: str, start: int, end: int):
    ings = {i["id"]: i for i in load(DATA / "ingredients.json")}
    meals = load(DATA / fn)
    end = min(end, len(meals))
    out = []
    for idx in range(start, end):
        m = meals[idx]
        cats = m.get("ingredient_categories", []) or []
        ex = m.get("example_ingredients", []) or []
        notes = (m.get("notes") or "").replace("\r", " ").replace("\n", " ")
        out.append(f"[{idx}] {m.get('id')}  |  {m.get('name')}")
        if notes:
            out.append(f"     notes: {notes}")
        out.append(f"     cats : {', '.join(cats)}")
        for iid in ex:
            ing = ings.get(iid)
            if ing:
                flag = "" if ing["category"] in cats else "  <hero/out-of-cat>"
                out.append(f"       - {ing['category']:24s} {ing['name']}  ({iid}){flag}")
            else:
                out.append(f"       - ??? unknown id ({iid})")
        out.append("")
    safe = fn.replace(".json", "")
    p = ROOT / "scripts" / f"_audit_examples_review_{safe}.txt"
    p.write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote {p}  (meals {start}..{end-1} of {len(meals)})")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "catindex":
        cat_index()
    elif len(sys.argv) >= 3 and sys.argv[1] == "review":
        fn = sys.argv[2]
        start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        end = int(sys.argv[4]) if len(sys.argv) > 4 else 10 ** 9
        review(fn, start, end)
    else:
        print(__doc__)
        sys.exit(1)
