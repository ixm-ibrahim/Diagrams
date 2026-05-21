"""Phase 22: Vegetables + Pickled vegetables + Fruits expansion.

Adds ~65 entries:
  - Pickled vegetables  (~10) — Condiments & sauces food_group
  - Non-starchy vegetables (~12) — Vegetables food_group (chilies, tomatoes, mushrooms)
  - Starchy vegetables (~5)
  - Fruits (fresh) (~15) — Fruits food_group
  - Berries (~3)
  - Dried fruits (~5)
  - Mushrooms / aromatics (~5)
  - Apple / pear varieties (~10)

All plant [0,1,0].
"""
from __future__ import annotations

import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ING_PATH = ROOT / "src" / "data" / "ingredients.json"

PLANT = [0, 1, 0]


def E(id, name, cat, sub, fg, contains, kcal, c, p, fb, fat, na, sg, sf, notes,
      form=None, examples=None):
    entry = {
        "id": id, "name": name, "category": cat, "subcategory": sub,
        "food_group": fg, "contains": list(contains), "group_weights": PLANT,
        "examples": list(examples) if examples else [],
        "calories": kcal, "carbs": c, "protein": p, "fiber": fb,
        "fat": fat, "sodium": na, "sugar": sg, "saturated_fat": sf,
        "notes": notes,
    }
    if form:
        entry["form"] = form
    return entry


# ---------------------------------------------------------------------------
# Pickled vegetables (Condiments & sauces food_group)
# ---------------------------------------------------------------------------
PV = "Pickled vegetables"
CS = "Condiments & sauces"

PICKLED = [
    E("pickle-bread-and-butter", "Bread-and-butter pickle", PV, "Pickled cucumber & cabbage", CS, [],
      94, 22, 0.4, 0.9, 0.2, 562, 18, 0.05,
      "Sweet-and-vinegary cucumber slices.", form="pickled"),
    E("pickle-sweet-gherkin", "Sweet gherkin", PV, "Pickled cucumber & cabbage", CS, [],
      117, 28, 0.4, 0.8, 0.3, 627, 16, 0.05,
      "Small sweet pickled cucumber.", form="pickled"),
    E("cornichon", "Cornichon", PV, "Pickled cucumber & cabbage", CS, [],
      11, 2, 0.5, 1, 0.1, 800, 1, 0,
      "Tiny tart French gherkin.", form="pickled"),
    E("pickled-jalapeno", "Pickled jalapeño", PV, "Other pickled", CS, [],
      18, 3.7, 0.9, 1.6, 0.6, 1666, 2, 0.1,
      "Vinegar-brined sliced jalapeños.", form="pickled"),
    E("pepperoncini", "Pepperoncini (pickled)", PV, "Other pickled", CS, [],
      19, 4.5, 1, 1.6, 0.3, 1556, 2.6, 0.05,
      "Mild Italian/Greek pickled pepper.", form="pickled"),
    E("pickled-beet", "Pickled beet", PV, "Other pickled", CS, [],
      72, 17, 0.8, 1.5, 0.1, 240, 14, 0.02,
      "Sliced beets in vinegar-sugar brine.", form="pickled"),
    E("pickled-okra", "Pickled okra", PV, "Other pickled", CS, [],
      30, 7, 1.4, 2.1, 0.1, 660, 1.5, 0,
      "Dill-pickled okra; Southern US.", form="pickled"),
    E("kalamata-olive", "Kalamata olive", PV, "Other pickled", CS, [],
      239, 4.5, 1.8, 3.3, 25, 1556, 0, 3.4,
      "Greek brine-cured black olive.", form="pickled"),
    E("olive-castelvetrano", "Castelvetrano olive", PV, "Other pickled", CS, [],
      150, 2, 1, 3, 15, 730, 0, 2,
      "Mild buttery green Sicilian olive.", form="pickled"),
    E("pimento", "Pimento (jarred)", PV, "Pimentos", CS, [],
      23, 5.4, 1.1, 1.9, 0.3, 14, 3.7, 0.05,
      "Heart-shaped sweet red pepper; martini garnish.", form="pickled"),
]


# ---------------------------------------------------------------------------
# Non-starchy vegetables (chilies, tomatoes, mushrooms, etc.)
# ---------------------------------------------------------------------------
NSV = "Non-starchy vegetables"
VEG = "Vegetables"

NONSTARCHY = [
    E("anaheim-pepper", "Anaheim pepper", NSV, "Chili peppers", VEG, [],
      31, 7, 1.5, 1.7, 0.4, 1, 4.2, 0.05, "Mild long green New Mexico chile."),
    E("hatch-chile", "Hatch chile", NSV, "Chili peppers", VEG, [],
      37, 8, 1.3, 1.5, 0.3, 7, 4.7, 0.04, "Medium-heat New Mexico late-summer chile."),
    E("cubanelle", "Cubanelle pepper", NSV, "Chili peppers", VEG, [],
      31, 7.1, 1.0, 1.0, 0.3, 4, 4.6, 0.04, "Mild long Italian sweet pepper."),
    E("scotch-bonnet", "Scotch bonnet", NSV, "Chili peppers", VEG, [],
      40, 9, 2.0, 1.5, 0.4, 7, 5.3, 0.05, "Caribbean very-hot pepper; jerk seasoning."),
    E("thai-chili", "Thai chili (bird's eye)", NSV, "Chili peppers", VEG, [],
      40, 9, 2.0, 1.5, 0.4, 7, 5.3, 0.05, "Tiny very-hot chili; Southeast Asian cuisine."),
    E("shishito-pepper", "Shishito pepper", NSV, "Chili peppers", VEG, [],
      28, 6, 1.3, 1.5, 0.3, 4, 4.0, 0.05, "Mild Japanese pepper; blistered tapas."),
    E("padron-pepper", "Padrón pepper", NSV, "Chili peppers", VEG, [],
      28, 6, 1.3, 1.5, 0.3, 4, 4.0, 0.05, "Spanish small green pepper; mostly mild."),
    E("heirloom-tomato", "Heirloom tomato", NSV, "Tomatoes", VEG, [],
      19, 4.2, 0.9, 1.3, 0.2, 6, 2.8, 0.03, "Open-pollinated tomato variety."),
    E("beefsteak-tomato", "Beefsteak tomato", NSV, "Tomatoes", VEG, [],
      18, 3.9, 0.9, 1.2, 0.2, 5, 2.6, 0.03, "Large slicing tomato."),
    E("grape-tomato", "Grape tomato", NSV, "Tomatoes", VEG, [],
      19, 4.2, 0.9, 1.3, 0.2, 6, 2.8, 0.03, "Small oval salad tomato."),
    E("sun-dried-tomato", "Sun-dried tomato", NSV, "Tomato products", VEG, [],
      258, 56, 14, 12, 3, 2095, 38, 0.4,
      "Dehydrated tomatoes; concentrated sweetness.", form="dried"),
    E("king-trumpet-mushroom", "King trumpet mushroom", NSV, "Mushrooms", VEG, [],
      35, 6, 3.0, 2.5, 0.4, 18, 2, 0.05, "Eringi; meaty white-stemmed mushroom."),
    E("maitake-mushroom", "Maitake mushroom", NSV, "Mushrooms", VEG, [],
      31, 7, 1.9, 2.7, 0.2, 1, 2.1, 0.03, "Hen-of-the-woods; clustered Japanese mushroom."),
    E("lions-mane-mushroom", "Lion's mane mushroom", NSV, "Mushrooms", VEG, [],
      24, 4, 2.5, 2.0, 0.2, 4, 1, 0.03, "White shaggy edible mushroom; seafood-like texture."),
    E("nameko-mushroom", "Nameko mushroom", NSV, "Mushrooms", VEG, [],
      26, 4, 1.8, 2.0, 0.4, 5, 1, 0.05, "Small amber Japanese mushroom; gelatinous coating."),
]


# ---------------------------------------------------------------------------
# Starchy vegetables
# ---------------------------------------------------------------------------
SV = "Starchy vegetables"

STARCHY = [
    E("potato-purple", "Purple potato", SV, "Potatoes", VEG, [],
      77, 17, 2, 1.5, 0.1, 6, 0.8, 0.03, "Anthocyanin-rich blue-purple flesh."),
    E("potato-fingerling", "Fingerling potato", SV, "Potatoes", VEG, [],
      77, 17, 2, 1.7, 0.1, 6, 0.8, 0.03, "Small elongated waxy potato."),
    E("potato-new", "New potato (baby)", SV, "Potatoes", VEG, [],
      70, 16, 1.8, 1.6, 0.1, 5, 0.7, 0.03, "Small immature potato; thin skin."),
    E("delicata-squash", "Delicata squash", SV, "Winter squash", VEG, [],
      40, 9, 1.0, 2.0, 0.1, 2, 2.5, 0.02, "Sweet edible-skin winter squash."),
    E("malanga", "Malanga", SV, "Tubers", VEG, [],
      132, 31, 1.9, 4.1, 0.4, 21, 0.3, 0.08, "Tropical tuber; tannia / cocoyam relative."),
    E("tigernut", "Tigernut (chufa)", SV, "Tubers", VEG, ["tree_nut"],
      387, 49, 6, 19, 18, 12, 22, 3.3, "Sweet chickpea-sized tuber; horchata base."),
]


# ---------------------------------------------------------------------------
# Fruits (fresh + new)
# ---------------------------------------------------------------------------
FR = "Fruits"
FRU = "Fruits"

FRESH_FRUIT = [
    # Apple varieties
    E("apple-granny-smith", "Apple (Granny Smith)", FR, "Apple", FRU, [],
      58, 13.6, 0.4, 2.8, 0.2, 1, 10, 0.05, "Tart green apple; baking favorite."),
    E("apple-fuji", "Apple (Fuji)", FR, "Apple", FRU, [],
      63, 15.2, 0.4, 2.3, 0.2, 1, 11.4, 0.05, "Crisp very-sweet Japanese variety."),
    E("apple-gala", "Apple (Gala)", FR, "Apple", FRU, [],
      57, 13.7, 0.3, 2.4, 0.1, 1, 10.5, 0.04, "Sweet mild snacking apple."),
    E("apple-honeycrisp", "Apple (Honeycrisp)", FR, "Apple", FRU, [],
      57, 14, 0.3, 2.5, 0.2, 1, 10.5, 0.04, "Crunchy aromatic juicy apple."),
    E("apple-pink-lady", "Apple (Pink Lady)", FR, "Apple", FRU, [],
      59, 14.2, 0.3, 2.4, 0.2, 1, 11, 0.04, "Pink-red tart-sweet apple."),

    # Pear varieties
    E("pear-bartlett", "Pear (Bartlett)", FR, "Pear", FRU, [],
      57, 15, 0.4, 3.1, 0.1, 1, 9.8, 0.02, "Classic green-yellow juicy pear."),
    E("pear-bosc", "Pear (Bosc)", FR, "Pear", FRU, [],
      57, 15, 0.4, 3.1, 0.1, 1, 9.8, 0.02, "Russet-brown dense holds-shape pear."),
    E("pear-asian", "Asian pear", FR, "Pear", FRU, [],
      42, 11, 0.5, 3.6, 0.2, 0, 7.0, 0.01, "Round crisp apple-pear."),

    # Stone fruits
    E("pluot", "Pluot", FR, "Stone fruits", FRU, [],
      50, 12, 0.7, 1.4, 0.3, 0, 10, 0.02, "Plum + apricot hybrid; sweet stone fruit."),
    E("plum-damson", "Damson plum", FR, "Stone fruits", FRU, [],
      48, 11, 0.7, 1.4, 0.3, 0, 9.9, 0.02, "Small tart European plum; jam-making."),
    E("cherry-bing", "Cherry (Bing, sweet)", FR, "Stone fruit", FRU, [],
      63, 16, 1, 2.1, 0.2, 0, 12.8, 0.04, "Dark sweet cherry; standard supermarket."),
    E("cherry-sour", "Sour cherry", FR, "Stone fruit", FRU, [],
      50, 12, 1, 1.6, 0.3, 3, 8.5, 0.07, "Tart cherry; pies + preserves."),

    # Citrus
    E("meyer-lemon", "Meyer lemon", FR, "Citrus", FRU, [],
      30, 9.3, 0.7, 2.8, 0.3, 2, 2.5, 0.04, "Sweeter thin-skinned lemon-mandarin cross."),
    E("key-lime", "Key lime", FR, "Citrus", FRU, [],
      30, 10.5, 0.7, 2.8, 0.2, 2, 1.7, 0.02, "Small aromatic Mexican lime; key lime pie."),
    E("clementine", "Clementine", FR, "Citrus", FRU, [],
      47, 12, 0.9, 1.7, 0.2, 1, 9, 0.03, "Easy-peel small seedless mandarin."),
    E("satsuma", "Satsuma", FR, "Citrus", FRU, [],
      46, 12, 0.9, 1.8, 0.2, 1, 9.0, 0.03, "Cold-hardy seedless mandarin variety."),

    # Other / exotic
    E("quince", "Quince", FR, "Other fruits", FRU, [],
      57, 15, 0.4, 1.9, 0.1, 4, 8.7, 0.01, "Hard tart fall fruit; cooked into membrillo."),
    E("loquat", "Loquat", FR, "Other fruits", FRU, [],
      47, 12, 0.4, 1.7, 0.2, 1, 9.7, 0.04, "Sweet-tart yellow stone-bearing fruit."),
    E("tamarind", "Tamarind (pulp, raw)", FR, "Tropical", FRU, [],
      239, 63, 2.8, 5.1, 0.6, 28, 39, 0.27, "Tart brown pod pulp; sauces + drinks."),
    E("durian", "Durian", FR, "Tropical", FRU, [],
      147, 27, 1.5, 3.8, 5.3, 2, 0, 1.7, "Pungent Southeast Asian fruit; custardy flesh."),
    E("rose-apple", "Rose apple", FR, "Tropical", FRU, [],
      25, 5.7, 0.6, 1.1, 0.3, 0, 2.9, 0.06, "Crisp pear-textured tropical fruit."),
    E("salak", "Salak (snake fruit)", FR, "Tropical", FRU, [],
      82, 22, 0.4, 1.5, 0.4, 0, 14, 0.05, "Indonesian scaly tropical fruit."),
]


# ---------------------------------------------------------------------------
# Berries
# ---------------------------------------------------------------------------
BR = "Berries"

BERRIES = [
    E("boysenberry", "Boysenberry", BR, "Berries", FRU, [],
      50, 12, 1.4, 5.3, 0.3, 1, 7, 0.02, "Loganberry/raspberry/blackberry hybrid."),
    E("black-currant", "Black currant", BR, "Berries", FRU, [],
      63, 15, 1.4, 4.3, 0.4, 2, 8, 0.04, "Tart European berry; high vitamin C."),
    E("white-currant", "White currant", BR, "Berries", FRU, [],
      56, 14, 1.4, 4.3, 0.2, 1, 7.4, 0.02, "Albino redcurrant variant."),
    E("huckleberry", "Huckleberry", BR, "Berries", FRU, [],
      37, 8.7, 0.4, 4.8, 0.2, 0, 6, 0.02, "Wild Pacific-Northwest blueberry relative."),
    E("acai-berry", "Açaí berry", BR, "Berries", FRU, [],
      70, 4, 1, 3, 5, 7, 1, 1.4, "Antioxidant-rich Amazonian berry."),
]


# ---------------------------------------------------------------------------
# Dried fruits (additional)
# ---------------------------------------------------------------------------
DF = "Dried fruits"

DRIED = [
    E("raisin-golden", "Golden raisin", DF, "Raisin", FRU, [],
      302, 79, 3, 4, 0.5, 12, 59, 0.05,
      "Sulfur-treated lighter raisin (no Sulfite restriction in current schema).", form="dried"),
    E("dried-banana", "Banana chip / dried banana", DF, "Dried fruits", FRU, [],
      519, 58, 2.3, 7.7, 34, 6, 35, 29,
      "Crisp fried + dried banana chips.", form="dried"),
    E("dried-coconut", "Dried coconut (unsweetened)", DF, "Dried fruits", FRU, ["tree_nut"],
      660, 24, 6.9, 16, 64, 37, 7.4, 57,
      "Desiccated coconut flesh.", form="dried"),
    E("dried-strawberry", "Dried strawberry", DF, "Dried fruits", FRU, [],
      302, 71, 4.5, 11, 1.6, 11, 53, 0.1,
      "Freeze-dried sweet strawberries.", form="dried"),
    E("candied-citron", "Candied citron peel", DF, "Florals", FRU, [],
      323, 82, 0.2, 1.6, 0.05, 90, 73, 0.01,
      "Sweet preserved citron rind; fruitcake / panettone.", form="dried"),
]


# ---------------------------------------------------------------------------
# Melon additions
# ---------------------------------------------------------------------------
MELONS = [
    E("watermelon-yellow", "Yellow watermelon", FR, "Melon", FRU, [],
      30, 7.6, 0.6, 0.4, 0.2, 1, 6.2, 0.02, "Pale-fleshed sweeter watermelon variant."),
    E("galia-melon", "Galia melon", FR, "Melons", FRU, [],
      35, 9, 0.5, 0.5, 0.1, 16, 8, 0.02, "Green-fleshed netted melon; Israeli origin."),
    E("crenshaw-melon", "Crenshaw melon", FR, "Melons", FRU, [],
      36, 9, 0.7, 0.6, 0.1, 14, 8.2, 0.03, "Sweet salmon-fleshed casaba × cantaloupe hybrid."),
]


# ---------------------------------------------------------------------------
# Grape varieties
# ---------------------------------------------------------------------------
GRAPES = [
    E("grape-concord", "Concord grape", FR, "Grape", FRU, [],
      67, 17, 0.6, 0.9, 0.4, 2, 16, 0.13, "Slip-skin purple grape; juice / jelly."),
    E("grape-thompson", "Thompson seedless grape", FR, "Grape", FRU, [],
      69, 18, 0.7, 0.9, 0.2, 2, 16, 0.05, "Pale green table grape; California staple."),
]


ALL_NEW = PICKLED + NONSTARCHY + STARCHY + FRESH_FRUIT + BERRIES + DRIED + MELONS + GRAPES


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
