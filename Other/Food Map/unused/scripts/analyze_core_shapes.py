#!/usr/bin/env python3
"""Strip out generic / noise categories and count the remaining unique
core shapes. Tells us the real size of the naming problem.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data" / "compositional-meals.json"

NOISE = {
    "Sugar & sweeteners",
    "Salt & seasonings",
    "Ground spices",
    "Oils",
    "Baking ingredients",
    "Extracts & essences",
    "Fresh herbs",
    "Sauces",
    "Margarine & shortening",
    "Prepared mixes",
}


def main() -> None:
    meals = json.loads(DATA.read_text(encoding="utf-8"))
    shapes: dict[frozenset[str], list[dict]] = defaultdict(list)
    for m in meals:
        core = frozenset(c for c in m.get("ingredient_categories", []) if c not in NOISE)
        shapes[core].append(m)

    by_total_freq = sorted(
        shapes.items(),
        key=lambda kv: -sum(m.get("frequency", 0) for m in kv[1]),
    )

    print(f"Total unique core shapes after stripping noise: {len(shapes)}")
    print(f"Total patterns: {sum(len(v) for v in shapes.values())}")
    n_empty = len(shapes[frozenset()]) if frozenset() in shapes else 0
    print(f"Patterns whose core shape is EMPTY (pure noise): {n_empty}")

    print("\nTop 80 core shapes by total frequency across their patterns:")
    for core, patterns in by_total_freq[:80]:
        total = sum(m.get("frequency", 0) for m in patterns)
        core_label = " + ".join(sorted(core)) if core else "(empty)"
        print(f"  total={total:6d}  variants={len(patterns):3d}  shape: {core_label}")

    sizes = Counter(len(c) for c in shapes)
    print("\nCore shape sizes:")
    for size, n in sorted(sizes.items()):
        print(f"  {size} categories: {n} unique shapes")


if __name__ == "__main__":
    main()
