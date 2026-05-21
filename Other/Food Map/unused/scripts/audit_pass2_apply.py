#!/usr/bin/env python3
"""Pass-2 audit fixes.

Three categories of change:
  A) Restore categories Pass 1 dropped that the meal definitionally
     requires (Burger lost bun, Wonton soup lost broth, etc.).
     Pass 1 used a 40% corpus threshold for curated meals; some
     defining categories fell just below that threshold and shouldn't
     have been removed.
  B) Add categories to untouched curated meals (n<20 corpus matches in
     Pass 1) where the dish definitionally requires them.
  C) Compositional meals where the first-pass strip removed all
     non-noise content, leaving entries semantically wrong
     (Compound butter stripped to plain butter; Béchamel base
     missing its flour).

The script also drops one nonsensical compositional entry
('Apple-walnut milk') and writes a report.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CURATED = ROOT / "src" / "data" / "meals.json"
COMPOSITIONAL = ROOT / "src" / "data" / "compositional-meals.json"
CORPUS_TITLED = ROOT / "src" / "data" / "corpus-titled-meals.json"
REPORT = ROOT / "docs" / "pass2-fixes-report.json"


# ---- A) Restore categories Pass 1 dropped ----
# For each, the comment shows the rationale.
RESTORE_CURATED: dict[str, dict] = {
    "Burger": {
        "add": ["Bread & rolls"],
        "why": "Bun is defining; corpus had 32% (below 40% threshold). A burger without a bun is just a patty.",
    },
    "Pesto pasta": {
        "add": ["Nuts"],
        "why": "Pine nuts are defining in pesto; corpus underweights them when recipes use jarred pesto (just 'pesto' as one NER token).",
    },
    "Wonton soup": {
        "add": ["Prepared soups & broths"],
        "why": "It is literally a soup. Corpus tags water+bouillon, not 'broth' subcategory, so this fell below threshold.",
    },
    "Caramel popcorn": {
        "add": ["Whole grains"],
        "why": "Popcorn IS the substrate; corpus had 38% (below 40%). Caramel popcorn without popcorn is just caramel.",
    },
    "Biscuits and gravy": {
        "add": ["Processed meat"],
        "why": "Sausage gravy is defining; corpus had 38% Processed meat + 38% Red meat (both below 40%, but combined evidence is clear).",
    },
    "Pierogi (potato-cheese)": {
        "add": ["Starchy vegetables", "Fresh cheese"],
        "why": "The name explicitly states the filling (potato-cheese). Removing these contradicts the dish identity.",
    },
    "Swedish meatballs": {
        "add": ["Cream & butter"],
        "why": "Served in cream gravy; corpus had 35% (below 40%). Jams & preserves (lingonberry) was below 10%, not restored.",
    },
}


# ---- B) Add categories to untouched curated meals (n<20 in Pass 1) ----
ADD_CURATED: dict[str, dict] = {
    "Pancakes & syrup": {
        "set": ["Flours", "Eggs", "Milk", "Sugar & sweeteners",
                "Cream & butter", "Baking ingredients", "Salt & seasonings"],
        "why": "Pancakes are batter-based, not bread. Mirror Crêpes Suzette pattern from Pass 1.",
    },
    "Peanut butter sandwich": {
        "set": ["Nut butters", "Bread & rolls", "Jams & preserves"],
        "why": "PB&J — Temperate fruits was a proxy for jelly/jam; replace with the correct Jams & preserves category.",
    },
    "Hummus plate": {
        "add": ["Nut butters", "Citrus"],
        "why": "Tahini (nut butter) and lemon juice are defining hummus ingredients.",
    },
    "Cheeseburger": {
        "add": ["Sauces", "Pickled vegetables"],
        "why": "Ketchup/mustard (Sauces) and pickles (Pickled vegetables) are core to a cheeseburger.",
    },
    "Yogurt parfait": {
        "add": ["Whole grains"],
        "why": "Granola is the carb component; without it, this is just yogurt + berries.",
    },
    "Cereal bowl": {
        "add": ["Sugar & sweeteners"],
        "why": "Most breakfast cereals carry added sugar.",
    },
    "Sashimi platter": {
        "add": ["Sauces"],
        "why": "Soy sauce + wasabi are the defining condiments.",
    },
    "Egg fried rice": {
        "add": ["Sauces"],
        "why": "Soy sauce is essential. Untouched in Pass 1 (n=19, just below 20). Corpus has Sauces at 58%.",
    },
    "Larb": {
        "add": ["Sauces"],
        "why": "Fish sauce is the defining ingredient of larb.",
    },
    "Tom yum goong": {
        "add": ["Sauces", "Fresh herbs"],
        "why": "Fish sauce and lemongrass/lime leaves are core. Pass 1 left this untouched (low corpus support).",
    },
    "Mole poblano with chicken": {
        "add": ["Candy & desserts"],
        "why": "Chocolate is the defining ingredient that distinguishes mole poblano.",
    },
    "Tofu stir-fry": {
        "add": ["Sauces"],
        "why": "Stir-fries are sauce-driven (soy/oyster/teriyaki).",
    },
}


# ---- C) Compositional fixes ----
COMP_FIXES: dict[str, dict] = {
    "Mulled apple wine": {
        "add": ["Whole spices", "Sugar & sweeteners", "Citrus"],
        "why": "Defining mulled-wine ingredients (cinnamon stick, cloves, sugar, orange). Pass 1's strip left it as just wine + fruit.",
    },
    "Béchamel base": {
        "add": ["Flours", "Salt & seasonings"],
        "why": "Béchamel = roux (butter + flour) + milk + salt. Pass 1 stripped sugar correctly but left it missing flour.",
    },
    "Compound butter": {
        "add": ["Fresh herbs", "Other vegetables"],
        "why": "Compound butter is butter blended with herbs/garlic/aromatics; the strip left it identical to plain butter.",
    },
    "Apple milkshake": {
        "add": ["Frozen dairy", "Sugar & sweeteners"],
        "why": "A milkshake requires ice cream; the strip left it as just milk + apple.",
    },
    "Bread pudding base": {
        "add": ["Eggs"],
        "why": "Bread pudding custard is bread + milk + eggs + sugar. Pass 1 had bread + milk + sugar; missing eggs.",
    },
}


# Compositional drops — meals that don't represent any real dish
COMP_DROPS: set[str] = {
    "Apple-walnut milk",
}


def load(path: Path) -> list:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data: list) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def apply_to_meal(m: dict, spec: dict) -> tuple[list, list]:
    before = list(m.get("ingredient_categories", []))
    if "set" in spec:
        m["ingredient_categories"] = list(spec["set"])
    else:
        cur = list(m["ingredient_categories"])
        for c in spec.get("add", []):
            if c not in cur:
                cur.append(c)
        m["ingredient_categories"] = cur
    return before, list(m["ingredient_categories"])


def main():
    report = {"curated_restore": [], "curated_add": [],
              "compositional": [], "drops": [], "missing": []}

    # ---- Curated ----
    meals = load(CURATED)
    by_name = {m["name"]: m for m in meals}

    for name, spec in RESTORE_CURATED.items():
        m = by_name.get(name)
        if not m:
            report["missing"].append({"file": "meals", "name": name})
            continue
        before, after = apply_to_meal(m, spec)
        if before != after:
            report["curated_restore"].append({
                "name": name, "before": before, "after": after,
                "why": spec["why"],
            })

    for name, spec in ADD_CURATED.items():
        m = by_name.get(name)
        if not m:
            report["missing"].append({"file": "meals", "name": name})
            continue
        before, after = apply_to_meal(m, spec)
        if before != after:
            report["curated_add"].append({
                "name": name, "before": before, "after": after,
                "why": spec["why"],
            })

    save(CURATED, meals)
    print(f"meals.json: {len(meals)} entries (restore={len(report['curated_restore'])}, add={len(report['curated_add'])})")

    # ---- Compositional ----
    comp = load(COMPOSITIONAL)
    comp_by_name = {m["name"]: m for m in comp}

    for name, spec in COMP_FIXES.items():
        m = comp_by_name.get(name)
        if not m:
            report["missing"].append({"file": "compositional", "name": name})
            continue
        before, after = apply_to_meal(m, spec)
        if before != after:
            report["compositional"].append({
                "name": name, "before": before, "after": after,
                "why": spec["why"],
            })

    n_before = len(comp)
    comp = [m for m in comp if m["name"] not in COMP_DROPS]
    for d in COMP_DROPS:
        if d in comp_by_name:
            report["drops"].append({"name": d, "cats": comp_by_name[d]["ingredient_categories"]})

    save(COMPOSITIONAL, comp)
    print(f"compositional-meals.json: {n_before} -> {len(comp)} entries ({len(report['compositional'])} fixed, {len(report['drops'])} dropped)")

    # ---- Report ----
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    print(f"\nWrote {REPORT.relative_to(ROOT)}")
    if report["missing"]:
        print(f"WARNING: {len(report['missing'])} entries not found:")
        for x in report["missing"]:
            print(f"  - {x['file']}: {x['name']!r}")


if __name__ == "__main__":
    main()
