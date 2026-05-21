"""Phase 28: East & Southeast Asian meal patterns.

~68 new meals across:
  Chinese (Cantonese / Sichuan / Northern / Shanghainese)
  Japanese
  Korean
  Thai
  Vietnamese
  Indonesian / Malay
  Filipino

Each carries a `cuisine` tag. CSV-validated via scripts/validate_meal_pattern.py.
"""
from __future__ import annotations

import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEALS_PATH = ROOT / "src" / "data" / "meals.json"


def M(id, name, ingredient_categories, cuisine, notes):
    return {
        "id": id, "name": name,
        "ingredient_categories": ingredient_categories,
        "cuisine": cuisine, "notes": notes,
    }


NEW = [
    # ---------- Chinese ----------
    M("kung-pao-chicken", "Kung pao chicken",
      ["Poultry", "Peppers & nightshades", "Nuts", "Sauces"],
      "Chinese-Sichuan", "Diced chicken stir-fried with peanuts, dried chilies, scallion."),
    M("sweet-and-sour-pork", "Sweet-and-sour pork",
      ["Red meat", "Sauces", "Peppers & nightshades", "Tropical fruits"],
      "Chinese-Cantonese", "Battered pork in a vinegar-sugar pineapple sauce."),
    M("mapo-tofu", "Mapo tofu",
      ["Soy products", "Red meat", "Pastes & ferments", "Whole spices"],
      "Chinese-Sichuan", "Silken tofu in a numbing chili-bean sauce with ground pork."),
    M("dim-sum-platter", "Dim sum platter",
      ["Bread & rolls", "Red meat", "Shellfish", "Leafy greens"],
      "Chinese-Cantonese", "Steamed dumplings (har gow, siu mai), char siu bao, gai lan."),
    M("jiaozi-pork-cabbage", "Jiaozi (pork & cabbage)",
      ["Bread & rolls", "Red meat", "Leafy greens", "Sauces"],
      "Chinese-Northern", "Boiled or pan-fried dumplings; vinegar-soy-ginger dip."),
    M("xiao-long-bao", "Xiao long bao",
      ["Bread & rolls", "Red meat", "Prepared soups & broths"],
      "Chinese-Shanghainese", "Soup-filled steamed dumplings."),
    M("wonton-soup", "Wonton soup",
      ["Bread & rolls", "Red meat", "Prepared soups & broths", "Leafy greens"],
      "Chinese-Cantonese", "Pork-shrimp wontons in light chicken broth with greens."),
    M("congee-rice", "Congee",
      ["Refined grains", "Eggs", "Processed meat", "Leafy greens"],
      "Chinese-Cantonese", "Slow-cooked rice porridge with century egg, scallions, pork."),
    M("peking-duck", "Peking duck",
      ["Poultry", "Bread & rolls", "Other non-starchy", "Sauces"],
      "Chinese-Northern", "Roast duck with thin pancakes, scallion, hoisin."),
    M("lions-head-meatball", "Lion's head meatballs",
      ["Red meat", "Leafy greens", "Sauces", "Prepared soups & broths"],
      "Chinese-Shanghainese", "Oversized pork meatballs braised over napa cabbage."),
    M("yuxiang-eggplant", "Yu-xiang eggplant",
      ["Peppers & nightshades", "Pastes & ferments", "Sauces", "Other non-starchy"],
      "Chinese-Sichuan", "Eggplant in 'fish-fragrant' chili-vinegar-garlic sauce."),
    M("twice-cooked-pork", "Twice-cooked pork",
      ["Red meat", "Other non-starchy", "Pastes & ferments", "Peppers & nightshades"],
      "Chinese-Sichuan", "Pork belly poached then stir-fried with bean paste and leeks."),
    M("dan-dan-noodles", "Dan dan noodles",
      ["Refined grains", "Red meat", "Sauces", "Peppers & nightshades"],
      "Chinese-Sichuan", "Wheat noodles in chili oil + sesame paste + minced pork."),
    M("fried-rice-egg", "Egg fried rice",
      ["Refined grains", "Eggs", "Other non-starchy", "Oils"],
      "Chinese", "Wok-tossed rice with egg, scallion, soy."),
    M("char-siu-pork-rice", "Char siu pork over rice",
      ["Red meat", "Refined grains", "Sauces", "Leafy greens"],
      "Chinese-Cantonese", "BBQ-glazed roast pork sliced over white rice."),
    M("sichuan-hot-pot", "Sichuan hot pot",
      ["Red meat", "Soy products", "Other non-starchy", "Mushrooms", "Peppers & nightshades"],
      "Chinese-Sichuan", "Communal numbing-spicy broth; meat, tofu, vegetables dipped to cook."),
    M("salt-pepper-shrimp", "Salt-and-pepper shrimp",
      ["Shellfish", "Whole spices", "Oils", "Peppers & nightshades"],
      "Chinese-Cantonese", "Fried shell-on shrimp with peppercorn-chili-salt seasoning."),

    # ---------- Japanese ----------
    M("sushi-nigiri-platter", "Sushi nigiri platter",
      ["Oily fish", "White fish", "Refined grains", "Sauces"],
      "Japanese", "Hand-pressed rice topped with raw fish; soy + wasabi."),
    M("ramen-tonkotsu", "Ramen (tonkotsu)",
      ["Refined grains", "Prepared soups & broths", "Red meat", "Eggs"],
      "Japanese", "Wheat noodles in rich pork-bone broth with chashu pork and ajitsuke egg."),
    M("ramen-shoyu", "Ramen (shoyu)",
      ["Refined grains", "Prepared soups & broths", "Poultry", "Eggs"],
      "Japanese", "Soy-based clear broth; chicken or pork chashu, scallion."),
    M("ramen-miso", "Ramen (miso)",
      ["Refined grains", "Pastes & ferments", "Red meat", "Other non-starchy"],
      "Japanese", "Hokkaido miso broth; ground pork, corn, butter optional."),
    M("donburi-gyudon", "Gyudon (beef bowl)",
      ["Red meat", "Refined grains", "Sauces", "Other non-starchy"],
      "Japanese", "Thin-sliced beef simmered with onion in soy-mirin; over rice."),
    M("donburi-oyakodon", "Oyakodon",
      ["Poultry", "Eggs", "Refined grains", "Sauces"],
      "Japanese", "Chicken + egg simmered in dashi-soy over rice."),
    M("donburi-katsudon", "Katsudon",
      ["Red meat", "Eggs", "Refined grains", "Bread & rolls"],
      "Japanese", "Breaded pork cutlet + egg over rice."),
    M("tempura-platter", "Tempura platter",
      ["White fish", "Shellfish", "Other non-starchy", "Bread & rolls"],
      "Japanese", "Light battered-fried fish + shrimp + vegetables."),
    M("okonomiyaki", "Okonomiyaki",
      ["Eggs", "Leafy greens", "Processed meat", "Sauces"],
      "Japanese", "Savory cabbage pancake with pork, mayo, okonomiyaki sauce."),
    M("soba-noodles", "Soba noodles",
      ["Whole grains", "Prepared soups & broths", "Sauces"],
      "Japanese", "Buckwheat noodles cold with tsuyu or hot in dashi broth."),
    M("udon-noodles", "Udon noodles",
      ["Refined grains", "Prepared soups & broths", "Other non-starchy"],
      "Japanese", "Thick wheat noodles in dashi-soy broth."),
    M("tonkatsu-plate", "Tonkatsu plate",
      ["Red meat", "Bread & rolls", "Leafy greens", "Sauces"],
      "Japanese", "Breaded-fried pork cutlet with shredded cabbage + tonkatsu sauce."),
    M("sukiyaki", "Sukiyaki",
      ["Red meat", "Soy products", "Leafy greens", "Sauces"],
      "Japanese", "Hot pot of beef + tofu + napa cabbage in sweet soy."),
    M("shabu-shabu", "Shabu-shabu",
      ["Red meat", "Leafy greens", "Soy products", "Mushrooms"],
      "Japanese", "Diners swish thin beef + vegetables through hot dashi."),

    # ---------- Korean ----------
    M("bibimbap", "Bibimbap",
      ["Refined grains", "Red meat", "Eggs", "Other non-starchy", "Pastes & ferments"],
      "Korean", "Stone-bowl rice topped with vegetables, beef, egg, gochujang."),
    M("bulgogi-plate", "Bulgogi plate",
      ["Red meat", "Sauces", "Refined grains", "Leafy greens"],
      "Korean", "Soy-marinated grilled beef strips over rice with lettuce wraps."),
    M("kimbap", "Kimbap",
      ["Refined grains", "Other non-starchy", "Eggs", "Processed meat"],
      "Korean", "Seaweed rice rolls with pickled radish, carrot, egg, ham."),
    M("kimchi-jjigae", "Kimchi jjigae",
      ["Other non-starchy", "Red meat", "Soy products", "Pastes & ferments"],
      "Korean", "Aged-kimchi stew with pork belly + tofu."),
    M("sundubu-jjigae", "Sundubu jjigae",
      ["Soy products", "Shellfish", "Pastes & ferments", "Eggs"],
      "Korean", "Spicy soft-tofu stew with clams and a cracked egg."),
    M("korean-bbq", "Korean BBQ platter",
      ["Red meat", "Leafy greens", "Pastes & ferments", "Other non-starchy"],
      "Korean", "Table-grilled marinated meats; ssamjang + lettuce + banchan."),
    M("japchae", "Japchae",
      ["Refined grains", "Other non-starchy", "Red meat", "Sauces"],
      "Korean", "Sweet-potato glass noodles stir-fried with beef + vegetables."),
    M("samgyetang", "Samgyetang",
      ["Poultry", "Whole grains", "Whole spices", "Prepared soups & broths"],
      "Korean", "Whole young chicken stuffed with sticky rice, ginseng, jujube."),
    M("tteokbokki", "Tteokbokki",
      ["Refined grains", "Pastes & ferments", "Sauces"],
      "Korean", "Chewy rice cakes simmered in spicy gochujang sauce."),

    # ---------- Thai ----------
    M("pad-thai", "Pad thai",
      ["Refined grains", "Shellfish", "Eggs", "Sauces", "Nuts"],
      "Thai", "Stir-fried rice noodles with shrimp, egg, tamarind, peanut."),
    M("tom-yum-goong", "Tom yum goong",
      ["Shellfish", "Prepared soups & broths", "Peppers & nightshades", "Citrus"],
      "Thai", "Hot-sour shrimp soup with lemongrass, lime, chili."),
    M("green-curry-chicken", "Green curry chicken",
      ["Poultry", "Pastes & ferments", "Other non-starchy", "Refined grains"],
      "Thai", "Coconut-green-curry-paste with chicken, eggplant, basil; over rice."),
    M("red-curry-chicken", "Red curry chicken",
      ["Poultry", "Pastes & ferments", "Peppers & nightshades", "Refined grains"],
      "Thai", "Coconut-red-curry with chicken and bamboo shoots; over rice."),
    M("massaman-curry", "Massaman curry",
      ["Red meat", "Pastes & ferments", "Starchy vegetables", "Nuts"],
      "Thai", "Mild Persian-influenced curry with beef, potato, peanut."),
    M("som-tam", "Som tam (green papaya salad)",
      ["Tropical fruits", "Peppers & nightshades", "Sauces", "Nuts"],
      "Thai", "Shredded unripe papaya pounded with chili, lime, fish sauce, peanut."),
    M("larb", "Larb",
      ["Poultry", "Fresh herbs", "Peppers & nightshades", "Citrus"],
      "Thai", "Minced meat salad with toasted rice powder, mint, chili, lime."),
    M("khao-soi", "Khao soi",
      ["Refined grains", "Poultry", "Pastes & ferments", "Prepared soups & broths"],
      "Thai-Northern", "Curried coconut-broth noodle soup; crispy noodle garnish."),
    M("pad-see-ew", "Pad see ew",
      ["Refined grains", "Red meat", "Leafy greens", "Sauces"],
      "Thai", "Wide rice noodles stir-fried with dark soy + Chinese broccoli + egg."),

    # ---------- Vietnamese ----------
    M("pho-bo", "Pho bo",
      ["Red meat", "Refined grains", "Prepared soups & broths", "Fresh herbs"],
      "Vietnamese", "Beef-bone broth with rice noodles, raw beef slices, basil, lime."),
    M("pho-ga", "Pho ga",
      ["Poultry", "Refined grains", "Prepared soups & broths", "Fresh herbs"],
      "Vietnamese", "Chicken-broth version of pho."),
    M("banh-mi", "Bánh mì",
      ["Bread & rolls", "Processed meat", "Pickled vegetables", "Fresh herbs"],
      "Vietnamese", "Baguette with cold cuts, pâté, pickled daikon-carrot, cilantro."),
    M("bun-bo-hue", "Bun bo Hue",
      ["Red meat", "Refined grains", "Prepared soups & broths", "Peppers & nightshades"],
      "Vietnamese", "Spicy beef-pork noodle soup with lemongrass + chili oil."),
    M("summer-rolls", "Summer rolls",
      ["Bread & rolls", "Shellfish", "Fresh herbs", "Leafy greens"],
      "Vietnamese", "Rice-paper rolls with shrimp, herbs, vermicelli; peanut dip."),
    M("bun-cha", "Bún chả",
      ["Red meat", "Refined grains", "Pickled vegetables", "Fresh herbs"],
      "Vietnamese", "Grilled pork patties with rice noodles, nuoc cham, herbs."),
    M("com-tam", "Cơm tấm",
      ["Refined grains", "Red meat", "Eggs", "Pickled vegetables"],
      "Vietnamese", "Broken rice with grilled pork chop, egg cake, pickles."),

    # ---------- Indonesian / Malay ----------
    M("nasi-goreng", "Nasi goreng",
      ["Refined grains", "Eggs", "Processed meat", "Sauces"],
      "Indonesian", "Indonesian fried rice with kecap manis, chili, fried egg."),
    M("rendang", "Beef rendang",
      ["Red meat", "Pastes & ferments", "Whole spices", "Nuts"],
      "Indonesian", "Coconut-curry beef slow-cooked until dark and dry."),
    M("laksa", "Laksa",
      ["Refined grains", "Shellfish", "Pastes & ferments", "Prepared soups & broths"],
      "Malay", "Coconut-curry noodle soup; shrimp, tofu puffs, fish cake."),
    M("satay-plate", "Satay plate",
      ["Poultry", "Sauces", "Nuts", "Refined grains"],
      "Indonesian", "Grilled meat skewers with peanut sauce + cucumber + rice cake."),
    M("gado-gado", "Gado-gado",
      ["Other non-starchy", "Eggs", "Soy products", "Sauces"],
      "Indonesian", "Mixed boiled vegetables with peanut sauce; egg + tofu + tempeh."),
    M("mee-goreng", "Mee goreng",
      ["Refined grains", "Shellfish", "Eggs", "Sauces"],
      "Malay", "Stir-fried egg noodles with shrimp, soy, tomato sauce, chili."),

    # ---------- Filipino ----------
    M("chicken-adobo", "Chicken adobo",
      ["Poultry", "Sauces", "Whole spices", "Refined grains"],
      "Filipino", "Chicken braised in soy + vinegar + garlic + bay; over rice."),
    M("sinigang", "Sinigang",
      ["Red meat", "Prepared soups & broths", "Other non-starchy", "Citrus"],
      "Filipino", "Sour pork-or-shrimp soup with tamarind, kangkong, daikon."),
    M("lumpia", "Lumpia",
      ["Bread & rolls", "Red meat", "Other non-starchy", "Sauces"],
      "Filipino", "Crisp spring rolls with pork-vegetable filling; sweet chili dip."),
    M("kare-kare", "Kare-kare",
      ["Red meat", "Nut butters", "Other non-starchy", "Pastes & ferments"],
      "Filipino", "Oxtail stew in peanut-annatto sauce with bok choy + eggplant."),
    M("pancit", "Pancit",
      ["Refined grains", "Poultry", "Other non-starchy", "Sauces"],
      "Filipino", "Stir-fried noodles with chicken, vegetables, soy, calamansi."),
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

    print(f"\nSummary: {appended} appended, {skipped} skipped.")
    with MEALS_PATH.open("w", encoding="utf-8") as f:
        json.dump(meals, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Wrote {len(meals)} meals to {MEALS_PATH}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
