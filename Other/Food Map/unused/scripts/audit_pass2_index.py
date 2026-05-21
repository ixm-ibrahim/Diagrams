"""Build a canonical-title -> list[set[category]] index from
recipe_taxonomy.csv using the existing audit_subcategory_map.

Used by audit_pass2_review.py for second-pass spot-checks. The first
pass already wrote the actual rebuild scripts; this one is read-only.
"""
from __future__ import annotations

import csv
import json
import pickle
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from audit_subcategory_map import SUB_TO_CATEGORY

TAXONOMY = ROOT / "recipe_taxonomy.csv"
CACHE = ROOT / "docs" / "_pass2_index.pkl"


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


def build():
    csv.field_size_limit(min(sys.maxsize, 2**31 - 1))
    idx: dict[str, list[frozenset]] = defaultdict(list)
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
                idx[canon].append(frozenset(cats))
            if i % 500_000 == 0:
                print(f"  ... {i:,} rows, {len(idx):,} titles", file=sys.stderr)
    return idx


def load_index():
    if CACHE.exists():
        with CACHE.open("rb") as f:
            return pickle.load(f)
    print("Building canonical-title index (no cache)...", file=sys.stderr)
    idx = build()
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    with CACHE.open("wb") as f:
        pickle.dump(dict(idx), f)
    print(f"Cached {len(idx):,} titles to {CACHE.relative_to(ROOT)}", file=sys.stderr)
    return idx


if __name__ == "__main__":
    idx = load_index()
    print(f"Index has {len(idx):,} canonical titles")
