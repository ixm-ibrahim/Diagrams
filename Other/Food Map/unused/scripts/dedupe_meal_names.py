#!/usr/bin/env python3
"""Collapse duplicate dish names in compositional-meals.json — but only
the *true* duplicates.

Two flavors of duplicate exist in the post-rename file:

  (a) Same dish, different noise — the same recognizable dish (e.g.
      "Roasted vegetables") appears N times because the original recipe
      patterns differed only in noise categories (Sugar+Salt+Oil etc.).
      After noise stripping they reduce to a single core shape — these
      are true duplicates. Keep one, drop the rest.

  (b) Same name, genuinely different shapes — the rename mapping
      intentionally lists the same dish name under several different
      core shapes (e.g. "Pancakes" comes from {Eggs+Flours},
      {Eggs+Flours+Milk}, and {Cream+Eggs+Flours+Milk} — those produce
      crepe-like, classic, and rich pancakes respectively, which ARE
      different dishes). For these we keep one entry per core shape,
      but disambiguate the name with a short modifier so each entry's
      name is unique.

Curated meals (meals.json) always win on a name clash: if a curated
entry already uses a name, the compositional version is dropped
entirely so only the hand-curated dot remains.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPOSITIONAL = ROOT / "src" / "data" / "compositional-meals.json"
CURATED = ROOT / "src" / "data" / "meals.json"
REPORT = ROOT / "docs" / "compositional-meals-dedup.txt"

# Same noise set the rename script uses — must stay in sync.
NOISE = frozenset({
    "Sugar & sweeteners", "Salt & seasonings", "Ground spices", "Oils",
    "Baking ingredients", "Extracts & essences", "Fresh herbs", "Sauces",
    "Margarine & shortening", "Prepared mixes",
})

# Short adjective fragments per category, for disambiguating names that
# span multiple core shapes. Keys are categories; values land directly in
# a parenthetical like "Pancakes (with milk)" or "Pancakes (buttery)".
CATEGORY_MODIFIER = {
    "Milk": "with milk",
    "Cream & butter": "buttery",
    "Eggs": "egg-based",
    "Flours": "flour-based",
    "Other vegetables": "with vegetables",
    "Starchy vegetables": "with potato",
    "Cruciferous vegetables": "with broccoli",
    "Leafy greens": "with greens",
    "Pickled vegetables": "pickled",
    "Temperate fruits": "with apple",
    "Berries": "with berries",
    "Citrus fruits": "with citrus",
    "Tropical fruits": "with tropical fruit",
    "Dried fruits": "with raisins",
    "Bread & rolls": "on bread",
    "Refined grains": "with pasta",
    "Whole grains": "with whole grain",
    "Aged cheese": "with cheddar",
    "Fresh cheese": "with ricotta",
    "Processed cheese": "with American cheese",
    "Poultry": "with chicken",
    "Red meat": "with beef",
    "Processed meat": "with bacon",
    "Organ meats": "with liver",
    "Shellfish": "with shrimp",
    "Oily fish": "with salmon",
    "White fish": "with white fish",
    "Legumes": "with beans",
    "Nuts": "with nuts",
    "Nut butters": "with peanut butter",
    "Seeds": "with seeds",
    "Fermented dairy": "with yogurt",
    "Yogurt": "with yogurt",
    "Plant milks": "with plant milk",
    "Alcoholic beverages": "boozy",
    "Coffee & tea": "with coffee",
    "Juices": "with juice",
    "Soft drinks": "with soda",
    "Spice blends": "curried",
    "Prepared soups & broths": "in broth",
}


def core_of(meal: dict) -> frozenset[str]:
    return frozenset(c for c in meal["ingredient_categories"] if c not in NOISE)


def disambiguate(base: str, extras: frozenset[str]) -> str:
    if not extras:
        return base
    mods = [CATEGORY_MODIFIER.get(c, c.lower()) for c in sorted(extras)]
    return f"{base} ({', '.join(mods)})"


def main() -> None:
    composit = json.loads(COMPOSITIONAL.read_text(encoding="utf-8"))
    curated = json.loads(CURATED.read_text(encoding="utf-8"))
    curated_names = {m["name"] for m in curated}

    # First pass: group by (name, core_shape) and keep one per pair.
    by_pair: dict[tuple[str, frozenset[str]], dict] = {}
    for m in composit:
        core = core_of(m)
        key = (m["name"], core)
        prev = by_pair.get(key)
        if prev is None or m.get("frequency", 0) > prev.get("frequency", 0):
            by_pair[key] = m

    # Re-group by name to find which names span multiple core shapes.
    by_name: dict[str, list[tuple[frozenset[str], dict]]] = defaultdict(list)
    for (name, core), meal in by_pair.items():
        by_name[name].append((core, meal))

    kept: list[dict] = []
    renamed_log: list[tuple[str, str, list[str]]] = []  # (orig, new, extras)
    dropped_to_curated: list[str] = []

    for name, pairs in by_name.items():
        if name in curated_names:
            dropped_to_curated.extend([name] * len(pairs))
            continue

        if len(pairs) == 1:
            kept.append(pairs[0][1])
            continue

        # Multiple core shapes share this name. Use the smallest shape as
        # the canonical owner of the unmodified name; disambiguate the rest
        # with a parenthetical of the extra categories.
        pairs_sorted = sorted(pairs, key=lambda cp: (len(cp[0]), -cp[1].get("frequency", 0)))
        canonical_core = pairs_sorted[0][0]
        for core, meal in pairs_sorted:
            extras = core - canonical_core
            new_name = disambiguate(name, extras)
            meal = dict(meal)  # shallow copy so we don't mutate the original
            if new_name != meal["name"]:
                renamed_log.append((meal["name"], new_name, sorted(extras)))
            meal["name"] = new_name
            kept.append(meal)

    # After disambiguation a new name could still clash with curated or
    # collide with another disambiguated entry — defensively dedupe by
    # the final name.
    final_by_name: dict[str, dict] = {}
    name_collisions = 0
    for m in kept:
        prev = final_by_name.get(m["name"])
        if m["name"] in curated_names:
            dropped_to_curated.append(m["name"])
            continue
        if prev is None or m.get("frequency", 0) > prev.get("frequency", 0):
            if prev is not None:
                name_collisions += 1
            final_by_name[m["name"]] = m

    final = sorted(final_by_name.values(), key=lambda m: -m.get("frequency", 0))

    COMPOSITIONAL.write_text(
        json.dumps(final, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    lines = []
    lines.append("# Compositional meals dedup (shape-aware)")
    lines.append("")
    lines.append(f"Input:                      {len(composit)} entries")
    lines.append(f"Output:                     {len(final)} entries")
    lines.append(f"True (same-shape) dupes collapsed: {len(composit) - len(by_pair)}")
    lines.append(f"Cross-shape name clashes disambiguated: {len(renamed_log)}")
    lines.append(f"Post-disambiguation final-name collisions resolved: {name_collisions}")
    lines.append(f"Names dropped to curated:   {len(dropped_to_curated)}")
    lines.append("")
    lines.append("## Renamed entries (cross-shape disambiguation)")
    seen = set()
    for orig, new, extras in renamed_log:
        if (orig, new) in seen:
            continue
        seen.add((orig, new))
        lines.append(f"  '{orig}' -> '{new}'  (extras: {extras})")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Input:  {len(composit)}")
    print(f"Output: {len(final)}")
    print(f"Same-shape dupes collapsed: {len(composit) - len(by_pair)}")
    print(f"Cross-shape disambiguations: {len(renamed_log)}")
    print(f"Curated wins:                {len(set(dropped_to_curated))}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
