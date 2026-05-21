"""Spot-check the audit subcategory map.

For each subcategory, walk the corpus and collect:
  - count of recipes containing that subcategory
  - sample recipe titles that include it
  - which item-names (from the corpus's ingredient lists) most often
    appear under that subcategory header.

The goal is to catch mappings that look wrong on inspection — e.g.
"Pickled" potentially covering things that aren't pickled vegetables
(maraschino cherries), or "Olives" being treated as pickled veg when
they may belong in their own category.

Reads recipe_taxonomy.csv directly. CSV columns:
  0 = id
  1 = title
  2 = categories (json list)
  3 = subcategories (json list)
  4 = ingredients (json list, raw NER tokens)
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAXONOMY = ROOT / "recipe_taxonomy.csv"

TARGET_SUBS = {
    "Pickled",
    "Olives",
    "Pickled cucumber & cabbage",
    "Fermented vegetables",
    "Other pickled",
    "Capers",
    "Squash",
    "Carrot",
    "Avocado",
    "Eggplant",
    "Cider",
    "Liqueurs",
    "Florals",
    "Other fruits",
    "Sea vegetables",
    "Tropical starches",
    "Cassava products",
    "Plant protein",
    "Wheat protein",
    "Cured fish",
    "Roe",
}


def main():
    csv.field_size_limit(min(sys.maxsize, 2**31 - 1))
    titles_per_sub: dict[str, list[str]] = defaultdict(list)
    ingredient_per_sub: dict[str, Counter] = defaultdict(Counter)
    count_per_sub: Counter = Counter()

    with TAXONOMY.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        for i, row in enumerate(reader, 1):
            if len(row) < 5:
                continue
            title = row[1]
            sub_cell = row[3]
            ner_cell = row[4]
            if not sub_cell:
                continue
            try:
                subs = json.loads(sub_cell)
                ners = json.loads(ner_cell) if ner_cell else []
            except json.JSONDecodeError:
                continue
            if not isinstance(subs, list):
                continue
            hits = [s for s in subs if s in TARGET_SUBS]
            for s in hits:
                count_per_sub[s] += 1
                if len(titles_per_sub[s]) < 30:
                    titles_per_sub[s].append(title)
                for n in ners:
                    if isinstance(n, str):
                        ingredient_per_sub[s][n.lower()] += 1
            if i % 500_000 == 0:
                print(f"  ... {i:,} rows", file=sys.stderr)

    out = ROOT / "docs" / "pass2-subcheck.json"
    payload = {}
    for s in TARGET_SUBS:
        payload[s] = {
            "n_recipes": count_per_sub[s],
            "sample_titles": titles_per_sub[s][:20],
            "top_ingredients": ingredient_per_sub[s].most_common(30),
        }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
