"""Phase 24: final ingredient sweep.

Adds ~35 entries to round out food_groups the earlier phases didn't cover:
  - Nuts & seeds extras (~8)
  - Protein (animal) extras (~20)
  - Protein (plant) extras (~7)
"""
from __future__ import annotations

import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ING_PATH = ROOT / "src" / "data" / "ingredients.json"

PLANT = [0, 1, 0]
ANIMAL = [1, 0, 0]


def E(id, name, cat, sub, fg, contains, gw, kcal, c, p, fb, fat, na, sg, sf,
      notes, form=None, examples=None):
    entry = {
        "id": id, "name": name, "category": cat, "subcategory": sub,
        "food_group": fg, "contains": list(contains), "group_weights": list(gw),
        "examples": list(examples) if examples else [],
        "calories": kcal, "carbs": c, "protein": p, "fiber": fb,
        "fat": fat, "sodium": na, "sugar": sg, "saturated_fat": sf,
        "notes": notes,
    }
    if form:
        entry["form"] = form
    return entry


# ---------------------------------------------------------------------------
# Nuts & seeds extras
# ---------------------------------------------------------------------------
NS = "Nuts & seeds"

NUTS_SEEDS = [
    E("almond-paste", "Almond paste", "Nut butters", "Almond butter", NS,
      ["tree_nut"], PLANT,
      458, 47, 8.4, 4.5, 27, 8, 41, 2.5, "Sweetened ground almonds; baking.", form="paste"),
    E("pistachio-paste", "Pistachio paste", "Nut butters", "Nut butters", NS,
      ["tree_nut"], PLANT,
      550, 30, 14, 8, 45, 5, 25, 6, "Ground pistachio with sugar; ice cream / pastry.",
      form="paste"),
    E("gianduja", "Gianduja (chocolate-hazelnut paste)", "Nut butters", "Nut butters", NS,
      ["tree_nut", "dairy", "soy", "caffeine"], PLANT,
      539, 58, 6.3, 3.4, 30, 32, 56, 11,
      "Italian confection: hazelnut + cocoa + sugar.", form="paste"),
    E("hazelnut-paste", "Hazelnut paste (pure)", "Nut butters", "Nut butters", NS,
      ["tree_nut"], PLANT,
      628, 17, 15, 9.7, 60, 0, 4.3, 4.5, "Unsweetened ground hazelnut.", form="paste"),
    E("chestnut-puree-sweetened", "Chestnut purée (sweetened)", "Nuts", "Chestnut", NS,
      [], PLANT,
      270, 65, 1.5, 4, 0.5, 5, 45, 0.1, "Mont Blanc / Marrons glacés base.", form="paste"),
    E("sacha-inchi-seeds", "Sacha inchi seeds", "Seeds", "Seeds", NS, [], PLANT,
      566, 26, 27, 8, 49, 7, 0.5, 6, "Peruvian Amazonian seed; high omega-3."),
    E("marcona-almond", "Marcona almond", "Nuts", "Almond", NS, ["tree_nut"], PLANT,
      630, 21, 21, 10, 56, 100, 4, 4.5, "Round flat Spanish almond; fried-salted snack."),
    E("pepitas-shelled", "Pepitas (shelled pumpkin seed)", "Seeds", "Pumpkin seed", NS,
      [], PLANT,
      559, 11, 30, 6, 49, 7, 1.4, 8.7, "Shelled roasted pumpkin seed; Mexican."),
]


# ---------------------------------------------------------------------------
# Protein (animal) extras
# ---------------------------------------------------------------------------
PA = "Protein (animal)"

ANIMAL_PROTEIN = [
    # --- Red meat additions ---
    E("pulled-pork", "Pulled pork (cooked)", "Red meat", "Pork", PA,
      ["meat", "pork"], ANIMAL,
      232, 1, 27, 0, 13, 380, 0.5, 4.5, "Slow-cooked shredded pork shoulder."),
    E("oxtail", "Oxtail", "Red meat", "Beef", PA, ["meat"], ANIMAL,
      262, 0, 30, 0, 16, 47, 0, 6.5, "Bone-in beef tail; rich in collagen. Braised."),
    E("beef-cheek", "Beef cheek", "Red meat", "Beef", PA, ["meat"], ANIMAL,
      266, 0, 31, 0, 15, 60, 0, 5.5, "Connective-tissue-rich braising cut."),
    E("wagyu-beef", "Wagyu beef (ribeye)", "Red meat", "Beef", PA, ["meat"], ANIMAL,
      444, 0, 18, 0, 41, 65, 0, 17, "Heavily marbled Japanese beef; very high fat."),
    E("lamb-breast", "Lamb breast", "Red meat", "Lamb", PA, ["meat"], ANIMAL,
      342, 0, 21, 0, 28, 70, 0, 13, "Fatty cut; slow-roasted, riblets."),

    # --- Organ meats ---
    E("brain-calf", "Brain (calf)", "Organ meats", "Other", PA, ["meat"], ANIMAL,
      150, 1, 11, 0, 11, 130, 0, 2.5, "Soft offal; French/Italian / Pakistani maghaz."),

    # --- Shellfish ---
    E("soft-shell-crab", "Soft-shell crab", "Shellfish", "Crab", PA, ["shellfish"], ANIMAL,
      91, 0, 18, 0, 1.5, 410, 0, 0.2, "Recently-molted blue crab; whole edible."),
    E("snow-crab", "Snow crab", "Shellfish", "Crab", PA, ["shellfish"], ANIMAL,
      90, 0, 19, 0, 1.2, 540, 0, 0.2, "Cold-water Alaskan crab; sweet meat."),
    E("dungeness-crab", "Dungeness crab", "Shellfish", "Crab", PA, ["shellfish"], ANIMAL,
      86, 0.7, 18, 0, 1.0, 295, 0, 0.1, "Pacific Northwest crab."),
    E("king-crab", "King crab", "Shellfish", "Crab", PA, ["shellfish"], ANIMAL,
      97, 0, 19, 0, 1.5, 1072, 0, 0.1, "Large red Alaskan crab; sweet rich legs."),
    E("prawn", "Prawn (large)", "Shellfish", "Shrimp", PA, ["shellfish"], ANIMAL,
      99, 0.2, 24, 0, 0.3, 111, 0, 0.06,
      "Cooked; near-identical to shrimp but larger."),
    E("conch", "Conch", "Shellfish", "Mollusks", PA, ["shellfish"], ANIMAL,
      130, 1.7, 26, 0, 1.2, 153, 0, 0.2, "Tough Caribbean sea snail; ceviche / fritters."),

    # --- Roe ---
    E("ikura", "Ikura (salmon roe)", "Canned & cured fish", "Roe", PA,
      ["fish"], ANIMAL,
      144, 1.5, 22, 0, 6, 1500, 0, 1.4,
      "Salmon eggs cured in salt + soy."),
    E("tobiko", "Tobiko (flying-fish roe)", "Canned & cured fish", "Roe", PA,
      ["fish"], ANIMAL,
      143, 1.5, 28, 0, 3, 1500, 0, 0.7, "Tiny crunchy sushi roe."),
    E("masago", "Masago (capelin roe)", "Canned & cured fish", "Roe", PA,
      ["fish"], ANIMAL,
      130, 2.5, 22, 0, 4, 1100, 0, 1, "Tobiko substitute; smaller, less crunchy."),
    E("mentaiko", "Mentaiko (pollock roe)", "Canned & cured fish", "Roe", PA,
      ["fish"], ANIMAL,
      135, 0.5, 21, 0, 5, 4000, 0, 1.2,
      "Spicy Korean-Japanese marinated pollock roe."),

    # --- More fish ---
    E("marlin", "Marlin", "Oily fish", "Oily fish", PA, ["fish", "meat"], ANIMAL,
      155, 0, 25, 0, 6, 73, 0, 1.5, "Cooked. Firm tuna-like flesh."),
    E("whitefish-lake", "Lake whitefish", "Freshwater fish", "Freshwater fish", PA,
      ["fish", "meat"], ANIMAL,
      172, 0, 24, 0, 7.5, 71, 0, 1.2, "Cooked. Mild Great Lakes fish."),
    E("tilefish", "Tilefish", "White fish", "Saltwater white fish", PA,
      ["fish", "meat"], ANIMAL,
      147, 0, 25, 0, 4.7, 65, 0, 0.9, "Cooked. Sweet-flavored sustainable choice."),

    # --- Processed meat extras ---
    E("smoked-turkey-deli", "Smoked turkey (deli)", "Processed meat", "Deli", PA,
      ["meat"], ANIMAL,
      99, 1.5, 18, 0, 2, 1000, 1, 0.6, "Wood-smoked sliced deli turkey."),
    E("boudin", "Boudin (Cajun sausage)", "Processed meat", "Fresh sausage", PA,
      ["meat", "pork"], ANIMAL,
      210, 18, 9, 0.5, 12, 670, 0.5, 4, "Pork + rice + spices in casing."),
]


# ---------------------------------------------------------------------------
# Protein (plant) extras
# ---------------------------------------------------------------------------
PP = "Protein (plant)"

PLANT_PROTEIN = [
    E("beyond-meat-burger", "Beyond Meat-style plant burger", "Legumes", "Plant protein", PP,
      ["soy"], PLANT,
      252, 7, 18, 2, 18, 380, 0, 6,
      "Pea-protein-based meat substitute; raw uncooked.", form="frozen"),
    E("impossible-burger", "Impossible-style plant burger", "Legumes", "Plant protein", PP,
      ["soy", "gluten"], PLANT,
      240, 9, 19, 3, 14, 370, 0, 8,
      "Soy + heme plant burger; uncooked.", form="frozen"),
    E("aburaage", "Aburaage (fried tofu)", "Legumes", "Soy", PP, ["soy"], PLANT,
      377, 2.5, 22, 1.4, 31, 9, 0, 4.5,
      "Deep-fried tofu pouch; inari sushi."),
    E("smoked-tofu", "Smoked tofu", "Legumes", "Soy", PP, ["soy"], PLANT,
      188, 4, 18, 1.5, 11, 350, 1, 1.5, "Pre-smoked firm tofu; sandwich-ready."),
    E("lupini-bean", "Lupini bean", "Legumes", "Beans", PP, [], PLANT,
      119, 9.9, 16, 2.8, 2.9, 7, 1, 0.3, "Brined Mediterranean legume; antipasto snack."),
    E("anko-red-bean-paste", "Anko (red bean paste)", "Legumes", "Beans", PP, [], PLANT,
      244, 53, 5, 4, 0.3, 75, 41, 0.05,
      "Sweetened adzuki paste; Japanese dessert filling.", form="paste"),
    E("white-bean-paste", "White bean paste (shiroan)", "Legumes", "Beans", PP, [], PLANT,
      240, 50, 5, 3.5, 0.3, 60, 38, 0.05,
      "Sweet white-bean paste; Japanese wagashi.", form="paste"),
]


ALL_NEW = NUTS_SEEDS + ANIMAL_PROTEIN + PLANT_PROTEIN


def main() -> None:
    with ING_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    by_id = {ing["id"]: ing for ing in data}

    appended = skipped = 0
    for entry in ALL_NEW:
        if entry["id"] in by_id:
            print(f"  ! skipped — {entry['id']} already exists", file=sys.stderr)
            skipped += 1
            continue
        gw = entry["group_weights"]
        assert len(gw) == 3 and sum(gw) == 1 and gw.count(1) == 1 and gw.count(0) == 2
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
