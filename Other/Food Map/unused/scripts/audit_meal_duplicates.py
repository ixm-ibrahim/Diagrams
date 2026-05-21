#!/usr/bin/env python3
"""Find duplicate meal names — i.e. the same dish name appearing on
multiple entries in compositional-meals.json (and meals.json).

Two causes today:
  1) Cross-shape collapse — distinct ingredient_categories sets reduce
     to the same "core shape" after stripping noise categories. The
     rename script then assigns them the same name list.
  2) Cross-shape semantic overlap — different shapes' name lists
     coincidentally share a label ("Beef stir-fry" used for two shapes).

Outputs:
  - Count of duplicate name groups
  - For each duplicated name, the count + total frequency + a sample
    of the distinct ingredient_categories sets it spans.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

COMPOSITIONAL = ROOT / "src" / "data" / "compositional-meals.json"
CURATED = ROOT / "src" / "data" / "meals.json"


def main() -> None:
    composit = json.loads(COMPOSITIONAL.read_text(encoding="utf-8"))
    curated = json.loads(CURATED.read_text(encoding="utf-8"))

    print(f"Compositional entries: {len(composit)}")
    print(f"Curated entries:       {len(curated)}")
    print()

    # Group by name within compositional
    by_name: dict[str, list[dict]] = defaultdict(list)
    for m in composit:
        by_name[m["name"]].append(m)

    dups = {n: ms for n, ms in by_name.items() if len(ms) > 1}
    print(f"Compositional names with duplicates: {len(dups)}")
    print(f"Total duplicate entries (count - 1 per name): "
          f"{sum(len(ms) - 1 for ms in dups.values())}")
    print()

    # Show top 40 worst offenders
    print("Top 40 most-duplicated names:")
    for name, ms in sorted(dups.items(), key=lambda kv: -len(kv[1]))[:40]:
        total_freq = sum(m.get("frequency", 0) for m in ms)
        distinct_shapes = {tuple(sorted(m["ingredient_categories"])) for m in ms}
        print(f"  {len(ms):3d}x  total_freq={total_freq:6d}  shapes={len(distinct_shapes)}  '{name}'")

    print()

    # Also check curated vs compositional name clashes
    curated_names = {m["name"] for m in curated}
    composit_names = set(by_name)
    clash = curated_names & composit_names
    print(f"Curated names also appearing in compositional: {len(clash)}")
    if clash:
        for n in sorted(clash)[:30]:
            print(f"  '{n}'")


if __name__ == "__main__":
    main()
