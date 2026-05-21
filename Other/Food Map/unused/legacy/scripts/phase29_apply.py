"""Phase 29: South Asian, Middle Eastern, North African meal patterns.

~62 new meals across:
  Indian (North/South/East/West)
  Pakistani / Bangladeshi
  Sri Lankan
  Levantine
  Iranian
  Turkish
  North African (Moroccan / Tunisian / Egyptian)

Note: the NLG dataset is American-leaning, so some of these patterns will
match few recipes. The CSV validator will report low-match meals; those are
documented exceptions rather than missing-pattern bugs.
"""
from __future__ import annotations

import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEALS_PATH = ROOT / "src" / "data" / "meals.json"


def M(id, name, ingredient_categories, cuisine, notes):
    return {"id": id, "name": name,
            "ingredient_categories": ingredient_categories,
            "cuisine": cuisine, "notes": notes}


NEW = [
    # ---------- Indian ----------
    M("butter-chicken", "Butter chicken",
      ["Poultry", "Sauces", "Cream & butter", "Ground spices"],
      "Indian", "Tandoori-style chicken in tomato-cream-fenugreek sauce; served with rice or naan."),
    M("chicken-tikka-masala", "Chicken tikka masala",
      ["Poultry", "Sauces", "Cream & butter", "Ground spices"],
      "Indian", "Marinated grilled chicken in creamy spiced tomato gravy."),
    M("vindaloo-pork", "Pork vindaloo",
      ["Red meat", "Pastes & ferments", "Whole spices", "Sauces"],
      "Indian", "Goan vinegar-chili pork curry; fiery and tangy."),
    M("chicken-korma", "Chicken korma",
      ["Poultry", "Cream & butter", "Nuts", "Whole spices"],
      "Indian", "Mughlai mild curry with yogurt, cashew/almond paste, cardamom."),
    M("rogan-josh", "Rogan josh",
      ["Red meat", "Sauces", "Ground spices", "Cream & butter"],
      "Indian-Kashmiri", "Lamb curry with Kashmiri chili and warm spices."),
    M("chicken-biryani", "Chicken biryani",
      ["Poultry", "Refined grains", "Whole spices", "Cream & butter"],
      "Indian", "Layered basmati rice with marinated chicken and saffron."),
    M("paneer-tikka", "Paneer tikka",
      ["Fresh cheese", "Peppers & nightshades", "Ground spices", "Sauces"],
      "Indian", "Tandoor-grilled paneer cubes marinated in spiced yogurt."),
    M("palak-paneer", "Palak paneer",
      ["Leafy greens", "Fresh cheese", "Cream & butter", "Ground spices"],
      "Indian", "Spinach purée with paneer and warm spices."),
    M("dal-makhani", "Dal makhani",
      ["Legumes", "Cream & butter", "Sauces", "Ground spices"],
      "Indian-Punjabi", "Slow-cooked black lentils + kidney beans with butter + cream."),
    M("dal-tadka", "Dal tadka",
      ["Legumes", "Oils", "Ground spices", "Other non-starchy"],
      "Indian", "Yellow lentils tempered with cumin, garlic, mustard seeds."),
    M("masala-dosa", "Masala dosa",
      ["Whole grains", "Starchy vegetables", "Pastes & ferments", "Legumes"],
      "Indian-South", "Fermented rice-lentil crêpe with spiced potato filling; sambar + chutney."),
    M("idli-sambar", "Idli sambar",
      ["Whole grains", "Legumes", "Other non-starchy", "Whole spices"],
      "Indian-South", "Steamed rice-lentil cakes with lentil-vegetable stew."),
    M("vegetarian-thali", "Vegetarian thali",
      ["Legumes", "Refined grains", "Leafy greens", "Yogurt", "Bread & rolls"],
      "Indian", "Composed plate: dal, curry, rice, roti, raita, pickle."),
    M("samosa-chaat", "Samosa chaat",
      ["Baked snacks & pastries", "Legumes", "Yogurt", "Sauces"],
      "Indian", "Crushed samosas with chickpeas, yogurt, tamarind + cilantro chutney."),
    M("chana-masala", "Chana masala",
      ["Legumes", "Peppers & nightshades", "Ground spices", "Other non-starchy"],
      "Indian", "Chickpeas in onion-tomato gravy with chana masala spice."),
    M("aloo-gobi", "Aloo gobi",
      ["Starchy vegetables", "Other non-starchy", "Ground spices", "Oils"],
      "Indian", "Dry potato + cauliflower curry."),
    M("tandoori-chicken", "Tandoori chicken",
      ["Poultry", "Yogurt", "Ground spices", "Citrus"],
      "Indian", "Yogurt-marinated chicken roasted in a clay oven."),
    M("rajma", "Rajma",
      ["Legumes", "Peppers & nightshades", "Ground spices", "Refined grains"],
      "Indian-Punjabi", "Red kidney bean curry served over rice."),

    # ---------- Pakistani / Bangladeshi ----------
    M("nihari", "Nihari",
      ["Red meat", "Ground spices", "Sauces", "Bread & rolls"],
      "Pakistani", "Slow-cooked beef shank stew in spiced gravy; eaten with naan."),
    M("haleem", "Haleem",
      ["Red meat", "Whole grains", "Legumes", "Ground spices"],
      "Pakistani", "Pounded wheat + lentils + meat porridge; Muharram tradition."),
    M("pakistani-biryani-mutton", "Pakistani mutton biryani",
      ["Red meat", "Refined grains", "Whole spices", "Yogurt"],
      "Pakistani", "Spicier and oilier than Indian; potato often layered in."),
    M("fish-curry-bengali", "Bengali fish curry",
      ["Freshwater fish", "Pastes & ferments", "Oils", "Ground spices"],
      "Bangladeshi", "Hilsa or rui in mustard-oil curry."),
    M("chapli-kebab", "Chapli kebab",
      ["Red meat", "Ground spices", "Eggs", "Peppers & nightshades"],
      "Pakistani-Pashtun", "Flat ground-beef patties with pomegranate seeds and spices."),

    # ---------- Sri Lankan ----------
    M("rice-and-curry-sri-lankan", "Sri Lankan rice & curry",
      ["Refined grains", "White fish", "Other non-starchy", "Ground spices"],
      "Sri Lankan", "Bowl of rice surrounded by 3-5 small curries (vegetable + fish + dal)."),
    M("hoppers", "Hoppers (appa)",
      ["Refined grains", "Eggs", "Cream & butter", "Sauces"],
      "Sri Lankan", "Bowl-shaped rice-coconut crêpe with an egg in the center; lunu miris."),
    M("kottu-roti", "Kottu roti",
      ["Bread & rolls", "Poultry", "Other non-starchy", "Ground spices"],
      "Sri Lankan", "Chopped roti stir-fried with vegetables, egg, meat, spiced sauce."),

    # ---------- Levantine ----------
    M("mezze-plate", "Mezze plate",
      ["Legumes", "Other non-starchy", "Bread & rolls", "Pickled vegetables"],
      "Levantine", "Hummus, baba ganoush, tabbouleh, olives, pita."),
    M("baba-ganoush", "Baba ganoush",
      ["Peppers & nightshades", "Other non-starchy", "Sauces", "Oils"],
      "Levantine", "Smoked-eggplant + tahini + lemon dip."),
    M("tabbouleh", "Tabbouleh",
      ["Fresh herbs", "Whole grains", "Peppers & nightshades", "Citrus"],
      "Levantine", "Parsley-bulgur salad with tomato + mint + lemon."),
    M("fattoush", "Fattoush",
      ["Leafy greens", "Bread & rolls", "Peppers & nightshades", "Ground spices"],
      "Levantine", "Mixed-greens salad with crispy pita + sumac dressing."),
    M("kibbeh", "Kibbeh",
      ["Red meat", "Whole grains", "Whole spices", "Oils"],
      "Levantine", "Bulgur + ground lamb football-shaped fritters."),
    M("shawarma-chicken", "Chicken shawarma",
      ["Poultry", "Bread & rolls", "Dressings & dips", "Pickled vegetables"],
      "Levantine", "Spit-roasted spiced chicken wrapped in pita with toum + pickles."),
    M("shawarma-beef", "Beef shawarma",
      ["Red meat", "Bread & rolls", "Sauces", "Pickled vegetables"],
      "Levantine", "Beef-lamb spit shaved into pita with tahini sauce."),
    M("manakish-zaatar", "Manakish (za'atar)",
      ["Bread & rolls", "Spice blends", "Oils", "Aged cheese"],
      "Levantine", "Flatbread topped with za'atar + olive oil (or cheese)."),
    M("kafta-kebab", "Kafta kebab",
      ["Red meat", "Fresh herbs", "Ground spices", "Bread & rolls"],
      "Levantine", "Ground-lamb skewers with parsley, onion, allspice."),
    M("fatteh", "Fatteh",
      ["Bread & rolls", "Legumes", "Yogurt", "Nuts"],
      "Levantine", "Toasted pita layered with chickpeas + garlicky yogurt + pine nuts."),
    M("falafel-plate", "Falafel plate",
      ["Legumes", "Bread & rolls", "Other non-starchy", "Sauces"],
      "Levantine", "Fried chickpea-fava balls with pita, hummus, tahini, salad."),

    # ---------- Iranian ----------
    M("kabab-koobideh", "Kabab koobideh",
      ["Red meat", "Other non-starchy", "Refined grains", "Whole spices"],
      "Iranian", "Saffron-onion ground-meat kebabs over saffron rice."),
    M("ghormeh-sabzi", "Ghormeh sabzi",
      ["Red meat", "Leafy greens", "Legumes", "Citrus"],
      "Iranian", "Herb stew with lamb, kidney beans, dried lime."),
    M("fesenjan", "Fesenjan",
      ["Poultry", "Nuts", "Sauces", "Whole spices"],
      "Iranian", "Chicken in pomegranate-walnut sauce."),
    M("tahdig-saffron", "Saffron tahdig",
      ["Refined grains", "Cream & butter", "Whole spices", "Oils"],
      "Iranian", "Crispy-bottomed saffron rice; centerpiece of Persian meals."),
    M("ash-reshteh", "Ash reshteh",
      ["Legumes", "Refined grains", "Leafy greens", "Yogurt"],
      "Iranian", "Thick noodle-bean-herb soup with kashk."),

    # ---------- Turkish ----------
    M("adana-kebab", "Adana kebab",
      ["Red meat", "Bread & rolls", "Peppers & nightshades", "Ground spices"],
      "Turkish", "Hand-minced spicy lamb skewers."),
    M("doner-kebab", "Döner kebab",
      ["Red meat", "Bread & rolls", "Yogurt", "Pickled vegetables"],
      "Turkish", "Vertical-spit roasted meat in flatbread with yogurt sauce."),
    M("iskender-kebab", "İskender kebab",
      ["Red meat", "Bread & rolls", "Yogurt", "Cream & butter"],
      "Turkish-Bursa", "Sliced döner over pide with tomato sauce, butter, yogurt."),
    M("dolma-stuffed-grape-leaves", "Dolma (stuffed grape leaves)",
      ["Leafy greens", "Refined grains", "Fresh herbs", "Citrus"],
      "Turkish", "Vine-leaf packets stuffed with herbed rice (vegan) or rice-and-meat."),
    M("borek-cheese", "Cheese börek",
      ["Baked snacks & pastries", "Aged cheese", "Fresh herbs", "Eggs"],
      "Turkish", "Filo-pastry pie with feta + parsley."),
    M("lahmacun", "Lahmacun",
      ["Bread & rolls", "Red meat", "Peppers & nightshades", "Fresh herbs"],
      "Turkish", "Thin flatbread topped with spiced minced lamb; lemon + parsley."),
    M("kunefe", "Künefe",
      ["Baked snacks & pastries", "Fresh cheese", "Sugar & sweeteners", "Nuts"],
      "Turkish", "Shredded-pastry + cheese soaked in sugar syrup; pistachio."),

    # ---------- North African ----------
    M("chicken-tagine", "Chicken tagine (preserved lemon)",
      ["Poultry", "Pickled vegetables", "Whole spices", "Other non-starchy"],
      "Moroccan", "Slow-braised chicken with olives and preserved lemon."),
    M("lamb-tagine", "Lamb tagine (prune & almond)",
      ["Red meat", "Dried fruits", "Nuts", "Whole spices"],
      "Moroccan", "Sweet-savory lamb with prunes, almonds, ras el hanout."),
    M("moroccan-couscous", "Moroccan couscous",
      ["Refined grains", "Poultry", "Other non-starchy", "Whole spices"],
      "Moroccan", "Steamed semolina with seven-vegetable + meat stew."),
    M("harira", "Harira",
      ["Legumes", "Red meat", "Whole spices", "Fresh herbs"],
      "Moroccan", "Tomato-lentil-chickpea Ramadan soup with lamb."),
    M("ful-medames", "Ful medames",
      ["Legumes", "Oils", "Citrus", "Ground spices"],
      "Egyptian", "Stewed fava beans with olive oil, lemon, cumin; bread on the side."),
    M("koshari", "Koshari",
      ["Refined grains", "Legumes", "Peppers & nightshades", "Other non-starchy"],
      "Egyptian", "Rice + lentils + pasta + chickpeas + tomato + fried onion."),
    M("brik", "Brik",
      ["Baked snacks & pastries", "Eggs", "Canned & cured fish", "Fresh herbs"],
      "Tunisian", "Filo pastry triangle with runny egg + tuna + capers."),
    M("shakshuka", "Shakshuka",
      ["Eggs", "Peppers & nightshades", "Ground spices", "Fresh herbs"],
      "North African", "Eggs poached in spiced tomato-pepper sauce."),
    M("bstilla", "B'stilla",
      ["Poultry", "Baked snacks & pastries", "Nuts", "Sugar & sweeteners"],
      "Moroccan", "Sweet-savory filo pie with shredded pigeon/chicken + almond + cinnamon."),
    M("mloukhia", "Mloukhia",
      ["Leafy greens", "Poultry", "Whole spices", "Oils"],
      "Egyptian", "Jute-leaf stew with chicken or rabbit, garlic, coriander."),
    M("meze-turkish", "Turkish meze plate",
      ["Yogurt", "Peppers & nightshades", "Pickled vegetables", "Bread & rolls"],
      "Turkish", "Cacık, ezme, haydari, olives, bread; small-plate appetizer board."),
]


def main() -> int:
    with MEALS_PATH.open("r", encoding="utf-8") as f:
        meals = json.load(f)
    by_id = {m["id"]: m for m in meals}

    appended = skipped = 0
    for new in NEW:
        if new["id"] in by_id:
            print(f"  ! skipped (exists): {new['id']}", file=sys.stderr)
            skipped += 1
            continue
        meals.append(new)
        appended += 1

    print(f"Summary: {appended} appended, {skipped} skipped.")
    with MEALS_PATH.open("w", encoding="utf-8") as f:
        json.dump(meals, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Wrote {len(meals)} meals to {MEALS_PATH}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
