"""Phase 21: Fats, oils, margarine, shortening.

Adds ~24 Fats & oils entries: margarine variants, animal fats (bacon/goose/
suet), and additional culinary oils. Plant oils [0,1,0]; animal-derived fats
[1,0,0] with `meat` tag (and `pork` for bacon-derived).
"""
from __future__ import annotations

import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ING_PATH = ROOT / "src" / "data" / "ingredients.json"

FG = "Fats & oils"


def F(id, name, cat, sub, contains, gw, kcal, c, p, fb, fat, na, sg, sf, notes,
      form=None, examples=None):
    entry = {
        "id": id, "name": name, "category": cat, "subcategory": sub,
        "food_group": FG, "contains": list(contains), "group_weights": list(gw),
        "examples": list(examples) if examples else [],
        "calories": kcal, "carbs": c, "protein": p, "fiber": fb,
        "fat": fat, "sodium": na, "sugar": sg, "saturated_fat": sf,
        "notes": notes,
    }
    if form:
        entry["form"] = form
    return entry


PLANT = [0, 1, 0]
ANIMAL = [1, 0, 0]


MS = "Margarine & shortening"
OILS = "Oils"
CB = "Cream & butter"

NEW = [
    # --- Margarine & shortening ---
    F("margarine-tub", "Margarine (tub)", MS, "Margarine", [], PLANT,
      534, 0.7, 0.2, 0, 60, 700, 0, 11, "Softer tub margarine, lower fat than stick."),
    F("margarine-light", "Margarine (light)", MS, "Margarine", [], PLANT,
      359, 0.4, 0.4, 0, 40, 689, 0, 7, "Reduced-fat spread; more water."),
    F("margarine-with-butter", "Margarine + butter blend", MS, "Margarine",
      ["dairy"], PLANT,
      655, 0.5, 0.5, 0, 73, 660, 0, 17, "I-can't-believe-it's-not-butter-style blend."),
    F("bacon-fat", "Bacon fat (rendered)", MS, "Animal fats",
      ["meat", "pork"], ANIMAL,
      897, 0, 0, 0, 100, 75, 0, 39, "Rendered bacon drippings; flavorful cooking fat."),
    F("goose-fat", "Goose fat", MS, "Animal fats", ["meat"], ANIMAL,
      900, 0, 0, 0, 100, 0, 0, 28, "Rendered goose fat; potato-roasting prize."),
    F("beef-suet", "Beef suet", MS, "Animal fats", ["meat"], ANIMAL,
      854, 0, 1.5, 0, 94, 18, 0, 52, "Hard raw beef kidney fat; for pastry / mincemeat."),

    # --- Oils ---
    F("soybean-oil", "Soybean oil", OILS, "Vegetable oils", ["soy"], PLANT,
      884, 0, 0, 0, 100, 0, 0, 15.7, "Common neutral cooking oil; high in PUFA."),
    F("rice-bran-oil", "Rice bran oil", OILS, "Vegetable oils", [], PLANT,
      884, 0, 0, 0, 100, 0, 0, 20, "High smoke point; common in Asian cooking."),
    F("flaxseed-oil", "Flaxseed oil", OILS, "Vegetable oils", [], PLANT,
      884, 0, 0, 0, 100, 0, 0, 9, "Cold-pressed; high omega-3. Don't heat."),
    F("hazelnut-oil", "Hazelnut oil", OILS, "Vegetable oils", ["tree_nut"], PLANT,
      884, 0, 0, 0, 100, 0, 0, 7.4, "Nutty finishing oil; dressings + drizzles."),
    F("macadamia-oil", "Macadamia oil", OILS, "Vegetable oils", ["tree_nut"], PLANT,
      884, 0, 0, 0, 100, 0, 0, 15.4, "Buttery monounsaturated nut oil."),
    F("hempseed-oil", "Hempseed oil", OILS, "Vegetable oils", [], PLANT,
      884, 0, 0, 0, 100, 0, 0, 8.6, "Green, grassy; balanced omega-3/6."),
    F("mct-oil", "MCT oil", OILS, "Vegetable oils", [], PLANT,
      823, 0, 0, 0, 100, 0, 0, 100,
      "Medium-chain triglycerides; coconut/palm derived. Mostly C8/C10."),
    F("almond-oil", "Almond oil", OILS, "Vegetable oils", ["tree_nut"], PLANT,
      884, 0, 0, 0, 100, 0, 0, 8.2, "Mild nutty oil; sweet baking + dressings."),
    F("pistachio-oil", "Pistachio oil", OILS, "Vegetable oils", ["tree_nut"], PLANT,
      884, 0, 0, 0, 100, 0, 0, 12.7, "Bright-green finishing oil."),
    F("cottonseed-oil", "Cottonseed oil", OILS, "Vegetable oils", [], PLANT,
      884, 0, 0, 0, 100, 0, 0, 25.9, "Industrial frying oil; mid-PUFA."),
    F("wheat-germ-oil", "Wheat germ oil", OILS, "Vegetable oils", ["gluten"], PLANT,
      884, 0, 0, 0, 100, 0, 0, 18.8, "Vitamin-E-rich finishing oil."),
    F("vegetable-oil-blend", "Vegetable oil (generic blend)", OILS, "Vegetable oils", ["soy"], PLANT,
      884, 0, 0, 0, 100, 0, 0, 15, "Soy/canola/sunflower blend; supermarket neutral oil."),
    F("garlic-infused-oil", "Garlic-infused oil", OILS, "Infused oils", [], PLANT,
      884, 0, 0, 0, 100, 0, 0, 14, "Garlic-flavored olive or neutral oil."),
    F("basil-infused-oil", "Basil-infused oil", OILS, "Infused oils", [], PLANT,
      884, 0, 0, 0, 100, 0, 0, 14, "Herb-infused olive oil; finishing."),
    F("rosemary-infused-oil", "Rosemary-infused oil", OILS, "Infused oils", [], PLANT,
      884, 0, 0, 0, 100, 0, 0, 14, "Rosemary in olive oil; roast meat finish."),
    F("lemon-infused-oil", "Lemon-infused oil", OILS, "Infused oils", [], PLANT,
      884, 0, 0, 0, 100, 0, 0, 14, "Citrus-flavored olive oil; fish + salads."),
    F("chia-seed-oil", "Chia seed oil", OILS, "Vegetable oils", [], PLANT,
      884, 0, 0, 0, 100, 0, 0, 10, "Very high omega-3; supplemental use."),
]


def main() -> None:
    with ING_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    by_id = {ing["id"]: ing for ing in data}

    appended = skipped = 0
    for entry in NEW:
        if entry["id"] in by_id:
            print(f"  ! skipped — {entry['id']} already exists", file=sys.stderr)
            skipped += 1
            continue
        gw = entry["group_weights"]
        assert len(gw) == 3 and sum(gw) == 1 and gw.count(1) == 1 and gw.count(0) == 2, \
            f"{entry['id']} violates single-group rule"
        assert entry["food_group"] == "Fats & oils"
        data.append(entry)
        appended += 1

    print(f"\nSummary: {appended} appended, {skipped} skipped.")
    write_compact(data, ING_PATH)
    print(f"Wrote {len(data)} entries.")


def write_compact(data, path: Path) -> None:
    lines = ["["]
    for i, ing in enumerate(data):
        sep = "," if i < len(data) - 1 else ""
        lines.append("  " + json.dumps(ing, ensure_ascii=False, separators=(", ", ": ")) + sep)
    lines.append("]")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
