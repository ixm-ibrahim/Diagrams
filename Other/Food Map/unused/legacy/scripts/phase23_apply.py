"""Phase 23: Spices, condiments, seasonings, sauces expansion.

Adds ~65 entries:
  - Salt & seasonings (~5)
  - Spice blends (~10)
  - Dried spices (~10)
  - Fresh herbs (~5)
  - Condiments & sauces (~35) — dressings, mustards, vinegars, sauces, spreads

All plant [0,1,0].
"""
from __future__ import annotations

import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ING_PATH = ROOT / "src" / "data" / "ingredients.json"

PLANT = [0, 1, 0]
HS = "Herbs & spices"
CS = "Condiments & sauces"


def E(id, name, cat, sub, fg, contains, kcal, c, p, fb, fat, na, sg, sf, notes,
      form=None, gw=None, examples=None):
    entry = {
        "id": id, "name": name, "category": cat, "subcategory": sub,
        "food_group": fg, "contains": list(contains),
        "group_weights": list(gw) if gw else PLANT,
        "examples": list(examples) if examples else [],
        "calories": kcal, "carbs": c, "protein": p, "fiber": fb,
        "fat": fat, "sodium": na, "sugar": sg, "saturated_fat": sf,
        "notes": notes,
    }
    if form:
        entry["form"] = form
    return entry


# ---------------------------------------------------------------------------
# Salt & seasonings (Herbs & spices food_group)
# ---------------------------------------------------------------------------
SALT_SEASONINGS = [
    E("garlic-salt", "Garlic salt", "Salt & seasonings", "Seasoned salts", HS, [],
      10, 2.4, 0.3, 0.2, 0.05, 32550, 0.05, 0,
      "Table salt + garlic powder; staple seasoning.", form="powdered"),
    E("celery-salt", "Celery salt", "Salt & seasonings", "Seasoned salts", HS, [],
      36, 7.5, 1.4, 1.7, 0.5, 35000, 0.5, 0.2,
      "Table salt + ground celery seed; Bloody Mary classic.", form="powdered"),
    E("onion-salt", "Onion salt", "Salt & seasonings", "Seasoned salts", HS, [],
      35, 8, 1, 0.5, 0.1, 32500, 1.5, 0,
      "Table salt + dehydrated onion powder.", form="powdered"),
    E("msg", "MSG (monosodium glutamate)", "Salt & seasonings", "Salt", HS, [],
      0, 0, 0, 0, 0, 12230, 0, 0,
      "Pure umami enhancer. Sodium ~12% of NaCl by mass.", form="powdered"),
    E("pickling-salt", "Pickling salt", "Salt & seasonings", "Salt", HS, [],
      0, 0, 0, 0, 0, 38758, 0, 0,
      "Pure NaCl, no anti-caking agents (which cloud brine)."),
    E("smoked-salt", "Smoked salt", "Salt & seasonings", "Salt", HS, [],
      0, 0, 0, 0, 0, 38000, 0, 0,
      "Cold-smoked sea salt; finishing seasoning."),
]


# ---------------------------------------------------------------------------
# Spice blends (Herbs & spices food_group)
# ---------------------------------------------------------------------------
BLENDS = [
    E("creole-seasoning", "Creole seasoning", "Spice blends", "American blends", HS, [],
      262, 49, 9, 16, 4.5, 9000, 5, 0.6, "Tony Chachere-style; spicier than Cajun.", form="powdered"),
    E("lemon-pepper", "Lemon-pepper seasoning", "Spice blends", "American blends", HS, [],
      300, 64, 12, 18, 5, 17500, 7, 1, "Dried citrus zest + cracked pepper + salt.", form="powdered"),
    E("bbq-rub", "BBQ rub", "Spice blends", "American blends", HS, [],
      305, 60, 7, 9, 5, 5400, 35, 0.5, "Sweet-and-savory dry rub (paprika + brown sugar + salt + spice).", form="powdered"),
    E("poultry-seasoning", "Poultry seasoning", "Spice blends", "American blends", HS, [],
      306, 60, 9, 21, 8.5, 39, 0.4, 2.2, "Sage-thyme-marjoram-rosemary blend.", form="powdered"),
    E("fines-herbes", "Fines herbes", "Spice blends", "European blends", HS, [],
      270, 60, 21, 26, 6, 95, 1, 1.5, "French chervil-chives-parsley-tarragon blend.", form="dried"),
    E("montreal-steak", "Montreal steak seasoning", "Spice blends", "American blends", HS, [],
      150, 30, 5, 10, 4, 16000, 1, 0.5, "Coarse salt + pepper + garlic + coriander + dill.", form="powdered"),
    E("tajin", "Tajín (chili-lime seasoning)", "Spice blends", "Mexican blends", HS, [],
      211, 53, 8, 14, 1.5, 13000, 4.5, 0.3, "Mild chili + lime + sea salt; Mexican.", form="powdered"),
    E("blackening-seasoning", "Blackening seasoning", "Spice blends", "American blends", HS, [],
      268, 50, 11, 21, 9, 12000, 4, 1.5, "Cajun-style high-heat sear blend.", form="powdered"),
    E("ranch-seasoning", "Ranch seasoning", "Spice blends", "American blends", HS, ["dairy"],
      275, 50, 5, 4, 6, 9000, 5, 4, "Buttermilk + dill + onion powder blend.", form="powdered"),
    E("fajita-seasoning", "Fajita seasoning", "Spice blends", "Mexican blends", HS, [],
      265, 52, 8, 11, 5, 13000, 6, 1, "Cumin + chili + paprika + salt blend.", form="powdered"),
]


# ---------------------------------------------------------------------------
# Dried spices (Herbs & spices food_group)
# ---------------------------------------------------------------------------
DRIED = [
    E("chipotle-powder", "Chipotle powder", "Dried spices", "Chili powders", HS, [],
      315, 56, 12, 28, 7, 91, 8, 1.7, "Ground smoked-dried jalapeño.", form="powdered"),
    E("gochugaru", "Gochugaru (Korean chili flake)", "Dried spices", "Chili powders", HS, [],
      300, 51, 12, 31, 7, 30, 24, 1, "Sun-dried Korean chili pepper; medium heat.", form="powdered"),
    E("espelette", "Piment d'Espelette", "Dried spices", "Chili powders", HS, [],
      330, 55, 15, 28, 12, 30, 10, 2, "AOP-protected French Basque chili powder.", form="powdered"),
    E("garlic-powder", "Garlic powder", "Dried spices", "Ground spices", HS, [],
      331, 73, 17, 9, 0.7, 60, 2.4, 0.1, "Dehydrated ground garlic.", form="powdered"),
    E("grains-of-paradise", "Grains of paradise", "Dried spices", "Seed spices", HS, [],
      290, 60, 11, 25, 6, 25, 0.5, 1.5, "West African pepper relative; black-cardamom adjacent.", form="dried"),
    E("long-pepper", "Long pepper", "Dried spices", "Peppers", HS, [],
      255, 65, 12, 25, 3, 44, 0.6, 1.2, "Sweet-floral cousin of black pepper.", form="dried"),
    E("fenugreek-seed", "Fenugreek seed", "Dried spices", "Seed spices", HS, [],
      323, 58, 23, 25, 6.4, 67, 0, 1.5, "Bitter golden Indian seed; curry powder ingredient."),
    E("kasoori-methi", "Kasoori methi (dried fenugreek leaves)", "Dried spices", "Dried herbs", HS, [],
      323, 58, 23, 25, 6.4, 67, 0, 1.5, "Crushed dried fenugreek leaves; Indian curry finishing.", form="dried"),
    E("amchur", "Amchur (mango powder)", "Dried spices", "Ground spices", HS, [],
      315, 73, 4, 7, 1, 30, 53, 0, "Ground sun-dried green mango; Indian souring agent.", form="powdered"),
    E("epazote", "Epazote (dried)", "Dried spices", "Dried herbs", HS, [],
      270, 50, 6, 15, 6, 50, 0.5, 0.5, "Pungent Mexican herb; bean-cooking partner.", form="dried"),
]


# ---------------------------------------------------------------------------
# Fresh herbs (Herbs & spices food_group)
# ---------------------------------------------------------------------------
FRESH_HERBS = [
    E("chervil", "Chervil (fresh)", "Fresh herbs", "Soft herbs", HS, [],
      32, 7, 3, 4, 0.5, 76, 0.2, 0.1, "Delicate anise-parsley flavor; fines herbes."),
    E("lovage", "Lovage", "Fresh herbs", "Soft herbs", HS, [],
      40, 7, 4, 5, 0.5, 100, 0.5, 0.1, "Celery-like perennial herb."),
    E("lemon-balm", "Lemon balm", "Fresh herbs", "Soft herbs", HS, [],
      27, 5, 2, 3, 0.5, 20, 1, 0.1, "Mint-family lemon-scented herb; tisanes."),
    E("salad-burnet", "Salad burnet", "Fresh herbs", "Soft herbs", HS, [],
      28, 5, 2, 3, 0.4, 15, 0.5, 0.1, "Cucumber-flavored small leafy herb."),
    E("summer-savory", "Summer savory", "Fresh herbs", "Hard herbs", HS, [],
      272, 69, 7, 45, 6, 24, 2, 3, "Pepper-thyme cousin; bean dishes.", form="dried"),
]


# ---------------------------------------------------------------------------
# Condiments & sauces (Condiments & sauces food_group)
# ---------------------------------------------------------------------------
CSAU = "Condiments & sauces"

CONDIMENTS = [
    # Asian sauces
    E("plum-sauce", "Plum sauce", CSAU, "Asian sauces", CS, [],
      184, 45, 0.5, 1, 0.4, 522, 39, 0.05, "Sweet-tart Chinese duck sauce."),
    E("sweet-chili-sauce", "Sweet chili sauce", CSAU, "Asian sauces", CS, [],
      225, 53, 1, 0.7, 0.4, 1320, 50, 0.05, "Thai sweet-and-spicy dipping sauce."),
    E("teriyaki-sauce", "Teriyaki sauce", CSAU, "Asian sauces", CS, ["soy", "gluten"],
      89, 16, 5.9, 0.1, 0, 3833, 13, 0, "Sweet soy glaze; chicken / beef marinade."),
    E("eel-sauce", "Eel sauce (unagi)", CSAU, "Asian sauces", CS, ["soy", "gluten"],
      163, 38, 2, 0, 0, 2000, 30, 0, "Thick sweet soy reduction; sushi glaze."),

    # Tomato-based / Mixed condiments
    E("tartar-sauce", "Tartar sauce", CSAU, "Emulsions", CS, ["eggs"],
      330, 13, 0.7, 0.5, 30, 588, 4, 4.6, "Mayo + relish + capers + lemon; for fried fish."),
    E("remoulade", "Remoulade", CSAU, "Emulsions", CS, ["eggs"],
      380, 9, 0.7, 0.3, 38, 580, 4, 5.5, "Mayo-based French/Cajun cold sauce."),
    E("romesco", "Romesco sauce", CSAU, "Herb sauces", CS, ["tree_nut"],
      264, 12, 4, 2.5, 22, 470, 6, 3,
      "Spanish red-pepper-and-nut purée; almond/hazelnut."),
    E("muhammara", "Muhammara", CSAU, "Herb sauces", CS, ["tree_nut"],
      245, 17, 3.5, 2.5, 18, 450, 9, 2.5,
      "Levantine roasted-pepper + walnut + pomegranate dip."),
    E("zhug", "Zhug (Yemenite green sauce)", CSAU, "Herb sauces", CS, [],
      105, 8, 3, 5, 7, 450, 1, 1,
      "Spicy cilantro-jalapeño-cumin paste."),
    E("salsa-verde-mexican", "Salsa verde (Mexican)", CSAU, "Tomato condiments", CS, [],
      37, 8, 1.4, 1.5, 0.3, 750, 4.5, 0.05, "Tomatillo + chili + lime green sauce."),
    E("pico-de-gallo", "Pico de gallo", CSAU, "Tomato condiments", CS, [],
      32, 7, 1.5, 1.5, 0.2, 376, 4, 0.03, "Fresh diced tomato + onion + cilantro + lime."),
    E("salsa-criolla", "Salsa criolla", CSAU, "Latin American pastes", CS, [],
      45, 9, 1.2, 1.5, 0.3, 400, 4, 0.04, "Peruvian/Argentine red-onion + lime relish."),
    E("demi-glace", "Demi-glace", CSAU, "Mixed condiments", CS, ["meat"],
      54, 5, 8, 0, 0.4, 700, 2, 0.1,
      "Reduced veal stock + espagnole; haute French.", gw=[1, 0, 0]),
    E("cranberry-sauce-canned", "Cranberry sauce (canned)", CSAU, "Mixed condiments", CS, [],
      154, 39, 0.3, 0.9, 0.2, 35, 36, 0.02, "Jellied or whole-berry sweetened cranberries.",
      form="canned"),
    E("applesauce-unsweetened", "Applesauce (unsweetened)", CSAU, "Mixed condiments", CS, [],
      42, 11, 0.2, 1.2, 0.1, 2, 9.4, 0.02, "Cooked apple purée; sugar-free.", form="canned"),
    E("gravy-brown", "Brown gravy", CSAU, "Mixed condiments", CS, ["gluten", "meat"],
      45, 6, 1.5, 0.4, 1.7, 510, 0.5, 0.7, "Pan-drippings + flour + stock; roast accompaniment.",
      gw=[1, 0, 0]),
    E("steak-sauce-heinz57", "Heinz 57 steak sauce", CSAU, "Mixed condiments", CS, [],
      111, 27, 0.8, 0.7, 0.3, 1450, 22, 0.05, "Tomato-based sweet-tangy steak sauce."),

    # Salad dressings
    E("french-dressing", "French dressing", CSAU, "Salad dressings", CS, [],
      414, 22, 0.7, 0, 36, 859, 21, 5, "Sweet-tart orange-red American dressing."),
    E("balsamic-vinaigrette", "Balsamic vinaigrette", CSAU, "Salad dressings", CS, [],
      280, 11, 0.5, 0, 27, 580, 9, 4, "Balsamic + olive oil + Dijon emulsion."),
    E("greek-dressing", "Greek dressing", CSAU, "Salad dressings", CS, [],
      378, 5, 0.5, 0, 40, 800, 3, 6, "Olive oil + lemon + oregano vinaigrette."),
    E("russian-dressing", "Russian dressing", CSAU, "Salad dressings", CS, ["eggs"],
      370, 13, 0.6, 0.3, 35, 933, 11, 5, "Mayo + ketchup + horseradish; Reuben sandwich."),
    E("poppy-seed-dressing", "Poppy seed dressing", CSAU, "Salad dressings", CS, [],
      400, 28, 0.8, 0.5, 32, 740, 25, 5, "Sweet creamy dressing with poppy seeds."),
    E("vinaigrette-house", "House vinaigrette", CSAU, "Salad dressings", CS, [],
      340, 4, 0.2, 0, 36, 600, 2, 5, "Generic mustard-shallot olive oil vinaigrette."),

    # Mustards
    E("mustard-whole-grain", "Whole grain mustard", CSAU, "Mustards", CS, [],
      141, 5, 6, 4.4, 8, 1300, 1, 0.5, "Coarse-ground mustard seeds in vinegar."),
    E("mustard-english", "English mustard", CSAU, "Mustards", CS, [],
      117, 5, 7, 3, 7, 1250, 1, 0.5, "Hot Coleman's-style yellow mustard."),
    E("mustard-chinese-hot", "Chinese hot mustard", CSAU, "Mustards", CS, [],
      120, 5, 7, 3, 7, 1300, 1, 0.5, "Reconstituted mustard powder; takeout-condiment heat."),

    # Vinegars
    E("vinegar-champagne", "Champagne vinegar", CSAU, "Vinegars", CS, [],
      22, 5, 0, 0, 0, 5, 2, 0, "Light delicate French vinegar; vinaigrettes."),
    E("vinegar-distilled-white", "Distilled white vinegar", CSAU, "Vinegars", CS, [],
      18, 0.04, 0, 0, 0, 2, 0.04, 0, "Pure 5% acetic acid; pickling + cleaning."),
    E("vinegar-coconut", "Coconut vinegar", CSAU, "Vinegars", CS, [],
      14, 0.5, 0.1, 0, 0, 5, 0.3, 0, "Filipino tropical vinegar from coconut sap."),
    E("vinegar-banyuls", "Banyuls vinegar", CSAU, "Vinegars", CS, [],
      45, 9, 0, 0, 0, 5, 5, 0, "French sweet-fortified wine vinegar."),

    # Spreads / sesame paste
    E("tahini", "Tahini", CSAU, "Spreads", CS, ["sesame"],
      595, 21, 17, 9.3, 54, 17, 0.5, 7.6, "Sesame seed paste; hummus + halva.",
      form="paste"),
    E("anchovy-paste", "Anchovy paste", CSAU, "Mixed condiments", CS, ["fish"],
      168, 0.5, 13, 0, 13, 4480, 0, 3, "Concentrated cured anchovy paste in a tube.",
      form="paste", gw=[1, 0, 0]),
    E("liquid-smoke", "Liquid smoke", CSAU, "Mixed condiments", CS, [],
      0, 0, 0, 0, 0, 26, 0, 0, "Condensed hardwood smoke flavoring."),
    E("relish-sweet", "Sweet pickle relish", CSAU, "Pickled", CS, [],
      130, 35, 0.5, 1, 0.5, 800, 30, 0.05, "Chopped sweet pickle + sugar + spices."),
    E("dill-pickle-relish", "Dill pickle relish", CSAU, "Pickled", CS, [],
      18, 4, 0.5, 1.6, 0.2, 800, 1.4, 0.04, "Chopped dill pickle + onion."),
]


ALL_NEW = SALT_SEASONINGS + BLENDS + DRIED + FRESH_HERBS + CONDIMENTS


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
        assert len(gw) == 3 and sum(gw) == 1 and gw.count(1) == 1 and gw.count(0) == 2, \
            f"{entry['id']} violates single-group rule"
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
