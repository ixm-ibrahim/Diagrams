"""Phase 30: Sub-Saharan African, Latin American, Caribbean meal patterns.

~58 new meals across:
  West African
  East African (Ethiopian / Kenyan)
  Southern African
  Mexican
  Brazilian
  Peruvian
  Argentine / Uruguayan
  Caribbean
  Latin / Central American (Cuban, Salvadoran, Honduran, Puerto Rican, Haitian)

Each carries a `cuisine` tag. NLG dataset is American-leaning, so Mexican
patterns will match many recipes while some African / Andean ones may match
few — those are documented exceptions, not bugs.
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
    # ---------- West African ----------
    M("jollof-rice", "Jollof rice",
      ["Refined grains", "Peppers & nightshades", "Poultry", "Ground spices"],
      "West African", "One-pot tomato-pepper rice with chicken; Nigerian/Ghanaian classic."),
    M("egusi-soup", "Egusi soup",
      ["Seeds", "Leafy greens", "Red meat", "Peppers & nightshades"],
      "West African-Nigerian", "Ground-melon-seed stew with bitter leaf and meat."),
    M("suya-skewers", "Suya skewers",
      ["Red meat", "Spice blends", "Nuts", "Peppers & nightshades"],
      "West African", "Hausa peanut-spice-crusted grilled beef skewers."),
    M("fufu-and-stew", "Fufu and palm-nut stew",
      ["Starchy vegetables", "Red meat", "Oils", "Peppers & nightshades"],
      "West African", "Pounded cassava/plantain dumpling with palm-nut + meat stew."),
    M("peanut-stew", "West African peanut stew",
      ["Nut butters", "Poultry", "Starchy vegetables", "Peppers & nightshades"],
      "West African", "Groundnut + tomato + chili stew with chicken or sweet potato."),
    M("waakye", "Waakye",
      ["Refined grains", "Legumes", "Ground spices", "Sauces"],
      "Ghanaian", "Rice and beans cooked with millet leaves; served with shito sauce."),
    M("thieboudienne", "Thieboudienne",
      ["White fish", "Refined grains", "Other non-starchy", "Peppers & nightshades"],
      "Senegalese", "Senegal's national dish: fish + jollof-style rice + vegetables."),

    # ---------- East African ----------
    M("injera-doro-wat", "Injera with doro wat",
      ["Bread & rolls", "Poultry", "Spice blends", "Eggs"],
      "Ethiopian", "Sourdough teff flatbread with spicy chicken-egg berbere stew."),
    M("injera-misir-wat", "Injera with misir wat",
      ["Bread & rolls", "Legumes", "Spice blends", "Oils"],
      "Ethiopian", "Injera with red-lentil berbere stew (vegan)."),
    M("injera-alicha", "Injera with alicha",
      ["Bread & rolls", "Other non-starchy", "Ground spices", "Cream & butter"],
      "Ethiopian", "Injera with mild turmeric vegetable stew."),
    M("ugali-sukuma-wiki", "Ugali with sukuma wiki",
      ["Whole grains", "Leafy greens", "Red meat", "Oils"],
      "Kenyan", "Stiff cornmeal porridge with sautéed collard greens."),
    M("pilau-east-african", "East African pilau",
      ["Refined grains", "Red meat", "Whole spices", "Other non-starchy"],
      "East African-Kenyan", "Spiced rice with beef; cardamom, cumin, cinnamon."),

    # ---------- Southern African ----------
    M("bobotie", "Bobotie",
      ["Red meat", "Eggs", "Dried fruits", "Ground spices"],
      "South African", "Curried minced beef baked under an egg-milk topping."),
    M("bunny-chow", "Bunny chow",
      ["Bread & rolls", "Poultry", "Ground spices", "Sauces"],
      "South African-Durban", "Hollowed half-loaf filled with curry."),
    M("pap-chakalaka", "Pap and chakalaka",
      ["Whole grains", "Other non-starchy", "Peppers & nightshades", "Ground spices"],
      "South African", "Stiff maize porridge with spicy tomato-pepper relish."),
    M("biltong-plate", "Biltong plate",
      ["Processed meat", "Aged cheese", "Pickled vegetables", "Bread & rolls"],
      "South African", "Cured beef strips with cheese, pickle, dried fruit."),

    # ---------- Mexican ----------
    M("tacos-al-pastor", "Tacos al pastor",
      ["Red meat", "Bread & rolls", "Tropical fruits", "Fresh herbs"],
      "Mexican", "Spit-roasted spiced pork in corn tortillas with pineapple, cilantro."),
    M("tacos-carnitas", "Tacos carnitas",
      ["Red meat", "Bread & rolls", "Pickled vegetables", "Fresh herbs"],
      "Mexican", "Slow-confit pork shoulder in tortillas with onion + cilantro + salsa."),
    M("tacos-fish", "Baja fish tacos",
      ["White fish", "Bread & rolls", "Leafy greens", "Dressings & dips"],
      "Mexican-Baja", "Beer-battered fish with cabbage slaw + crema in corn tortillas."),
    M("tacos-lengua", "Tacos de lengua",
      ["Red meat", "Bread & rolls", "Other non-starchy", "Fresh herbs"],
      "Mexican", "Braised beef tongue tacos with onion + cilantro + salsa verde."),
    M("tacos-barbacoa", "Tacos de barbacoa",
      ["Red meat", "Bread & rolls", "Other non-starchy", "Sauces"],
      "Mexican", "Pit-cooked spiced lamb/beef in corn tortillas."),
    M("enchiladas-rojas", "Enchiladas rojas",
      ["Bread & rolls", "Poultry", "Sauces", "Aged cheese"],
      "Mexican", "Tortillas rolled with chicken, smothered in red chile sauce + cheese."),
    M("mole-poblano-chicken", "Mole poblano with chicken",
      ["Poultry", "Pastes & ferments", "Refined grains", "Nuts"],
      "Mexican-Puebla", "Chicken in a complex chocolate-chile sauce; rice on the side."),
    M("tamales", "Tamales",
      ["Whole grains", "Red meat", "Sauces", "Oils"],
      "Mexican", "Masa dough with savory filling, steamed in corn husks."),
    M("chilaquiles", "Chilaquiles",
      ["Bread & rolls", "Eggs", "Sauces", "Aged cheese"],
      "Mexican", "Fried tortilla chips simmered in salsa with egg + queso."),
    M("pozole-rojo", "Pozole rojo",
      ["Red meat", "Whole grains", "Peppers & nightshades", "Prepared soups & broths"],
      "Mexican", "Hominy + pork stew with dried red chiles."),
    M("sopes", "Sopes",
      ["Whole grains", "Legumes", "Aged cheese", "Sauces"],
      "Mexican", "Thick fried-masa boats with refried beans, cheese, salsa, lettuce."),
    M("huevos-rancheros", "Huevos rancheros",
      ["Eggs", "Bread & rolls", "Sauces", "Legumes"],
      "Mexican", "Fried eggs over warm tortillas with salsa ranchera + beans."),

    # ---------- Brazilian ----------
    M("feijoada", "Feijoada",
      ["Legumes", "Red meat", "Processed meat", "Refined grains"],
      "Brazilian", "Black-bean + smoked-meat stew over rice with farofa + orange slices."),
    M("moqueca", "Moqueca",
      ["White fish", "Peppers & nightshades", "Oils", "Fresh herbs"],
      "Brazilian-Bahian", "Coconut-milk fish stew with palm oil + tomato + bell pepper."),
    M("churrasco-plate", "Churrasco plate",
      ["Red meat", "Sauces", "Refined grains", "Legumes"],
      "Brazilian", "Open-flame grilled meats with chimichurri, rice + beans, farofa."),
    M("pao-de-queijo", "Pão de queijo",
      ["Refined grains", "Aged cheese", "Eggs", "Oils"],
      "Brazilian", "Tapioca-cheese bread puffs."),
    M("acaraje", "Acarajé",
      ["Legumes", "Shellfish", "Oils", "Peppers & nightshades"],
      "Brazilian-Bahian", "Black-eyed-pea fritters in palm oil with shrimp + vatapa filling."),
    M("vatapa", "Vatapa",
      ["Shellfish", "Bread & rolls", "Nut butters", "Oils"],
      "Brazilian-Bahian", "Creamy shrimp-bread-peanut paste; afro-Brazilian classic."),

    # ---------- Peruvian ----------
    M("ceviche-peruvian", "Peruvian ceviche",
      ["White fish", "Citrus", "Peppers & nightshades", "Other non-starchy"],
      "Peruvian", "Raw fish cured in lime juice with aji amarillo + red onion + sweet potato."),
    M("lomo-saltado", "Lomo saltado",
      ["Red meat", "Starchy vegetables", "Peppers & nightshades", "Sauces"],
      "Peruvian", "Stir-fried beef + onion + tomato + fries over rice."),
    M("aji-de-gallina", "Ají de gallina",
      ["Poultry", "Pastes & ferments", "Bread & rolls", "Nuts"],
      "Peruvian", "Shredded chicken in a creamy ají-amarillo-walnut sauce."),
    M("anticuchos", "Anticuchos",
      ["Organ meats", "Peppers & nightshades", "Whole spices", "Sauces"],
      "Peruvian", "Marinated grilled beef-heart skewers."),
    M("papa-huancaina", "Papa a la huancaína",
      ["Starchy vegetables", "Aged cheese", "Pastes & ferments", "Eggs"],
      "Peruvian", "Boiled potato with ají-cheese sauce + olive + boiled egg."),

    # ---------- Argentine / Uruguayan ----------
    M("asado-plate", "Asado plate",
      ["Red meat", "Sauces", "Other non-starchy", "Bread & rolls"],
      "Argentine", "Long-grilled cuts (ribs, chorizo, sweetbreads) with chimichurri."),
    M("milanesa", "Milanesa",
      ["Red meat", "Bread & rolls", "Eggs", "Citrus"],
      "Argentine", "Breaded-fried beef cutlet; often topped with ham + cheese."),
    M("empanadas-argentine", "Empanadas argentinas",
      ["Baked snacks & pastries", "Red meat", "Eggs", "Pickled vegetables"],
      "Argentine", "Baked turnovers with beef, hard-boiled egg, olive, raisin."),
    M("chimichurri-steak", "Chimichurri grilled steak",
      ["Red meat", "Sauces", "Fresh herbs", "Oils"],
      "Argentine", "Grilled steak with parsley-garlic-vinegar herb sauce."),

    # ---------- Caribbean ----------
    M("jerk-chicken", "Jerk chicken",
      ["Poultry", "Spice blends", "Peppers & nightshades", "Refined grains"],
      "Jamaican", "Allspice-Scotch-bonnet-marinated grilled chicken; rice and peas."),
    M("ackee-saltfish", "Ackee and saltfish",
      ["Tropical fruits", "Canned & cured fish", "Peppers & nightshades", "Other non-starchy"],
      "Jamaican", "Boiled ackee with salt cod, peppers, onion; the national dish."),
    M("ropa-vieja", "Ropa vieja",
      ["Red meat", "Peppers & nightshades", "Sauces", "Refined grains"],
      "Cuban", "Shredded braised flank steak in tomato-pepper sauce; black beans + rice."),
    M("jamaican-oxtail", "Jamaican oxtail",
      ["Red meat", "Legumes", "Refined grains", "Sauces"],
      "Jamaican", "Slow-braised oxtail with butter beans, over rice and peas."),
    M("callaloo", "Callaloo",
      ["Leafy greens", "Shellfish", "Oils", "Peppers & nightshades"],
      "Caribbean", "Amaranth/taro leaves cooked with coconut milk + crab or salt fish."),
    M("caribbean-roti", "Caribbean curry roti",
      ["Bread & rolls", "Poultry", "Starchy vegetables", "Ground spices"],
      "Trinidadian", "Curried chicken or goat wrapped in a dhalpuri roti."),
    M("cuban-sandwich", "Cuban sandwich",
      ["Bread & rolls", "Processed meat", "Aged cheese", "Pickled vegetables"],
      "Cuban", "Pressed sandwich with roast pork, ham, Swiss, pickles, mustard."),
    M("mofongo", "Mofongo",
      ["Starchy vegetables", "Processed meat", "Shellfish", "Sauces"],
      "Puerto Rican", "Mashed fried green plantains with garlic + chicharron; shrimp on top."),

    # ---------- Latin / Central American ----------
    M("arepas", "Arepas",
      ["Whole grains", "Aged cheese", "Eggs", "Other non-starchy"],
      "Venezuelan-Colombian", "Corn-flour cakes split and filled with cheese, egg, or shredded meat."),
    M("pupusas", "Pupusas",
      ["Whole grains", "Aged cheese", "Legumes", "Pickled vegetables"],
      "Salvadoran", "Thick masa cakes stuffed with cheese, beans, or pork; curtido on top."),
    M("gallo-pinto", "Gallo pinto",
      ["Legumes", "Refined grains", "Eggs", "Sauces"],
      "Costa Rican", "Black-bean-and-rice breakfast with egg + sour cream + Lizano sauce."),
    M("baleadas", "Baleadas",
      ["Bread & rolls", "Legumes", "Aged cheese", "Eggs"],
      "Honduran", "Folded flour tortilla with beans, cheese, crema, optional egg."),
    M("haitian-griot", "Haitian griot",
      ["Red meat", "Starchy vegetables", "Citrus", "Peppers & nightshades"],
      "Haitian", "Marinated fried pork with pikliz + fried plantains."),
    M("tostones", "Tostones",
      ["Starchy vegetables", "Oils", "Sauces"],
      "Caribbean", "Twice-fried green plantain rounds; garlic dip."),
    M("arroz-con-pollo", "Arroz con pollo",
      ["Poultry", "Refined grains", "Peppers & nightshades", "Whole spices"],
      "Latin American", "Saffron/achiote rice cooked with chicken + peas + bell pepper."),
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
