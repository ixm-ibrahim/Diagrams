#!/usr/bin/env python3
"""Write every unique core shape with its variants + frequencies to a
text file we can audit by hand and use to build the rename mapping.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data" / "compositional-meals.json"
OUT = ROOT / "docs" / "core-shapes.txt"

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

    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append(f"# Compositional meal core shapes ({len(shapes)} unique, {len(meals)} total patterns)")
    lines.append("# Noise categories stripped before grouping: " + ", ".join(sorted(NOISE)))
    lines.append("")
    for core, patterns in by_total_freq:
        total = sum(m.get("frequency", 0) for m in patterns)
        core_label = " + ".join(sorted(core)) if core else "(EMPTY — pure noise)"
        lines.append(f"## total={total} variants={len(patterns)}")
        lines.append(f"   core: {core_label}")
        lines.append("")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
