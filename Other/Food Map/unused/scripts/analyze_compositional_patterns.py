#!/usr/bin/env python3
"""Dump the shape of compositional-meals.json so we can plan the rename audit.

Prints:
- total pattern count
- frequency distribution buckets
- distinct ingredient_categories tuples grouped by category-set shape
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data" / "compositional-meals.json"


def main() -> None:
    meals = json.loads(DATA.read_text(encoding="utf-8"))
    print(f"Total compositional patterns: {len(meals)}")

    freqs = [m.get("frequency", 0) for m in meals]
    buckets = [
        ("freq >= 1000", lambda f: f >= 1000),
        ("freq 500-999", lambda f: 500 <= f < 1000),
        ("freq 200-499", lambda f: 200 <= f < 500),
        ("freq 100-199", lambda f: 100 <= f < 200),
        ("freq 50-99",   lambda f: 50  <= f < 100),
        ("freq 20-49",   lambda f: 20  <= f < 50),
        ("freq 10-19",   lambda f: 10  <= f < 20),
        ("freq 5-9",     lambda f: 5   <= f < 10),
        ("freq 1-4",     lambda f: 1   <= f < 5),
        ("freq 0",       lambda f: f == 0),
    ]
    print("\nFrequency distribution:")
    for label, pred in buckets:
        n = sum(1 for f in freqs if pred(f))
        print(f"  {label:14s}  {n:5d}")

    cat_counter: Counter[str] = Counter()
    size_counter: Counter[int] = Counter()
    for m in meals:
        cats = m.get("ingredient_categories", [])
        size_counter[len(cats)] += 1
        for c in cats:
            cat_counter[c] += 1

    print("\nCategory-set sizes (how many categories per pattern):")
    for size, n in sorted(size_counter.items()):
        print(f"  {size} categories: {n} patterns")

    print("\nMost common categories (across all patterns):")
    for cat, n in cat_counter.most_common(30):
        print(f"  {n:5d}  {cat}")

    print("\nTop 30 patterns by frequency:")
    top = sorted(meals, key=lambda m: -m.get("frequency", 0))[:30]
    for m in top:
        cats = " + ".join(m.get("ingredient_categories", []))
        print(f"  freq={m.get('frequency', 0):5d}  {cats}")


if __name__ == "__main__":
    main()
