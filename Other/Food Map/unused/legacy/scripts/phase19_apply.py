"""Phase 19: Sweets, Prepared mixes, Jams & preserves expansion.

Adds ~65 new Sweets-food_group entries:
  - Cake/cookie mixes, frostings, whipped cream  (~10)
  - Puddings, gelatins, pie fillings              (~10)
  - Jams & preserves                              (~12)
  - Confectionery                                 (~12)
  - Chocolate items                               (~6)
  - Syrups & toppings                             (~8)
  - Misc sweets / sugar                           (~5)

Tag rules:
  - `caffeine` on cocoa-containing items (chocolate bars, truffles, syrups,
    hot fudge, nutella, peanut-butter cup, candy with cocoa).
  - `dairy` on cream-based items (frostings, fudge sauce, peanut butter cup).
  - `gluten` on cake/cookie mixes (most contain wheat flour).
  - `tree_nut` on nutella (hazelnut), marzipan (almond), pistachio pudding mix.
  - `peanut` on peanut-butter cup, peanut brittle.
  - `eggs` on lemon curd, meringue cookie, marzipan (egg white).

Single-group rule:
  - plant [0,1,0] for grain/fruit/sugar-based.
  - dairy [0,0,1] for cream-based and chocolate-bar-style (mass-dominant cream/milk).

Idempotent.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ING_PATH = ROOT / "src" / "data" / "ingredients.json"

FG = "Sweets"


def S(id, name, cat, sub, contains, gw, kcal, c, p, fb, fat, na, sg, sf, notes,
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
DAIRY = [0, 0, 1]

PM = "Prepared mixes"
JP = "Jams & preserves"
SW = "Sweets"


# ---------------------------------------------------------------------------
# Cake/cookie mixes, frostings, whipped cream
# ---------------------------------------------------------------------------
MIXES = [
    S("cake-mix-chocolate", "Cake mix (chocolate)", PM, "Cake mixes",
      ["gluten", "caffeine"], PLANT,
      410, 78, 4.5, 1.5, 9, 600, 47, 2.5,
      "Dry mix; eggs/oil/water added at use.", form="powdered"),
    S("cake-mix-white", "Cake mix (white)", PM, "Cake mixes", ["gluten"], PLANT,
      414, 79, 4.5, 0.5, 9, 580, 46, 2.4,
      "Dry mix made without egg yolks.", form="powdered"),
    S("cake-mix-devils-food", "Cake mix (devil's food)", PM, "Cake mixes",
      ["gluten", "caffeine"], PLANT,
      410, 78, 4.5, 1.5, 9, 600, 47, 2.5,
      "Dark chocolate cake mix.", form="powdered"),
    S("cake-mix-carrot", "Cake mix (carrot)", PM, "Cake mixes", ["gluten"], PLANT,
      400, 75, 4, 1.5, 9, 550, 44, 2.4,
      "Spiced carrot cake mix.", form="powdered"),
    S("cake-mix-angel-food", "Cake mix (angel food)", PM, "Cake mixes", ["gluten"], PLANT,
      359, 81, 8, 0.2, 0.2, 446, 60, 0.05,
      "Egg-white-only cake mix; ultra-low fat.", form="powdered"),
    S("brownie-mix", "Brownie mix", PM, "Cookie mixes", ["gluten", "caffeine"], PLANT,
      420, 80, 4, 2.5, 11, 360, 50, 4,
      "Chocolate brownie dry mix.", form="powdered"),
    S("cookie-mix", "Cookie mix (chocolate-chip)", PM, "Cookie mixes",
      ["gluten", "dairy", "caffeine"], PLANT,
      461, 71, 5, 2, 18, 380, 41, 8,
      "Dry mix for chocolate chip cookies.", form="powdered"),
    S("frosting-vanilla-canned", "Frosting (vanilla, canned)", PM, "Cake mixes",
      ["dairy"], PLANT,
      425, 71, 0.4, 0, 17, 110, 67, 5.5,
      "Ready-to-spread canned frosting."),
    S("frosting-chocolate-canned", "Frosting (chocolate, canned)", PM, "Cake mixes",
      ["dairy", "caffeine"], PLANT,
      415, 70, 1, 1, 16, 110, 65, 5.5,
      "Ready-to-spread canned chocolate frosting."),
    S("whipped-cream-aerosol", "Whipped cream (aerosol)", PM, "Whipped toppings",
      ["dairy"], DAIRY,
      257, 13, 3, 0, 22, 50, 7, 14,
      "Real dairy whipped cream in a can (Reddi-Whip).", form="frozen"),
]


# ---------------------------------------------------------------------------
# Puddings, gelatins, pie fillings
# ---------------------------------------------------------------------------
PUDDINGS = [
    S("pudding-mix-chocolate", "Pudding mix (chocolate, instant)", PM, "Puddings",
      ["caffeine"], PLANT,
      370, 92, 1, 1, 0, 900, 80, 0,
      "Dry mix; milk added at use.", form="powdered"),
    S("pudding-mix-butterscotch", "Pudding mix (butterscotch, instant)", PM, "Puddings",
      [], PLANT,
      370, 92, 0, 0, 0, 900, 84, 0,
      "Dry mix; milk added at use.", form="powdered"),
    S("pudding-mix-lemon", "Pudding mix (lemon, cook & serve)", PM, "Puddings",
      [], PLANT,
      370, 92, 0, 0, 0, 700, 84, 0,
      "Dry mix; cook with water + egg yolks.", form="powdered"),
    S("pudding-mix-pistachio", "Pudding mix (pistachio, instant)", PM, "Puddings",
      ["tree_nut"], PLANT,
      370, 92, 0.5, 0, 0, 700, 80, 0,
      "Pistachio-flavored. Sometimes contains real nuts.", form="powdered"),
    S("rice-pudding", "Rice pudding (prepared)", PM, "Puddings", ["dairy"], DAIRY,
      136, 22, 3.5, 0.4, 3.6, 50, 11, 2,
      "Sweet rice cooked in milk; cinnamon dusted."),
    S("gelatin-cherry", "Gelatin dessert (cherry)", PM, "Gelatins",
      ["animal_byproduct"], PLANT,
      382, 91, 6.4, 0, 0, 410, 84, 0,
      "Dry mix; sugar + flavored gelatin powder.", form="powdered"),
    S("gelatin-lime", "Gelatin dessert (lime)", PM, "Gelatins",
      ["animal_byproduct"], PLANT,
      382, 91, 6.4, 0, 0, 410, 84, 0,
      "Dry mix; lime-flavored.", form="powdered"),
    S("gelatin-unflavored", "Gelatin (unflavored)", PM, "Gelatins",
      ["animal_byproduct"], PLANT,
      335, 0, 85, 0, 0.1, 196, 0, 0,
      "Knox-style; pure protein hydrocolloid.", form="powdered"),
    S("cherry-pie-filling", "Cherry pie filling (canned)", PM, "Pie fillings", [], PLANT,
      104, 26, 0.4, 0.4, 0.1, 18, 22, 0,
      "Sweet cherries in starch-thickened syrup.", form="canned"),
    S("apple-pie-filling", "Apple pie filling (canned)", PM, "Pie fillings", [], PLANT,
      87, 22, 0.2, 0.7, 0.1, 49, 19, 0,
      "Cinnamon-spiced apples in syrup.", form="canned"),
    S("blueberry-pie-filling", "Blueberry pie filling (canned)", PM, "Pie fillings", [], PLANT,
      130, 32, 0.4, 1.2, 0.2, 32, 25, 0.05,
      "Blueberries in starch-thickened sweet syrup.", form="canned"),
    S("fruit-cocktail-canned", "Fruit cocktail (canned)", PM, "Pie fillings", [], PLANT,
      57, 14.5, 0.4, 1.0, 0.05, 6, 12.7, 0.005,
      "Pears + peaches + grapes + cherries in light syrup.", form="canned"),
    S("mincemeat", "Mincemeat (filling)", PM, "Pie fillings", ["alcohol"], PLANT,
      274, 64, 1.7, 3.0, 1.5, 178, 47, 0.5,
      "Spiced dried-fruit + brandy filling for pies."),
]


# ---------------------------------------------------------------------------
# Jams & preserves
# ---------------------------------------------------------------------------
JAMS = [
    S("jam-raspberry", "Raspberry jam", JP, "Fruit preserves", [], PLANT,
      261, 65, 0.4, 1.5, 0.1, 24, 49, 0.05,
      "Cooked raspberries + sugar + pectin."),
    S("jam-blueberry", "Blueberry jam", JP, "Fruit preserves", [], PLANT,
      263, 65, 0.4, 1.0, 0.1, 27, 50, 0.05,
      "Cooked blueberries + sugar + pectin."),
    S("jelly-grape", "Grape jelly", JP, "Fruit preserves", [], PLANT,
      255, 66, 0.2, 0.3, 0.05, 38, 47, 0.005,
      "Clear strained grape juice + sugar + pectin."),
    S("preserves-mixed-berry", "Mixed berry preserves", JP, "Fruit preserves", [], PLANT,
      258, 64, 0.5, 1.5, 0.1, 25, 48, 0.05,
      "Whole-fruit chunky preserves."),
    S("marmalade-orange", "Orange marmalade", JP, "Fruit preserves", [], PLANT,
      246, 64, 0.5, 1.0, 0.05, 39, 60, 0.005,
      "Citrus peel + sugar + pectin; characteristic bitterness."),
    S("preserves-apricot", "Apricot preserves", JP, "Fruit preserves", [], PLANT,
      264, 65, 0.4, 0.7, 0.05, 12, 53, 0.005,
      "Cooked apricots + sugar."),
    S("lemon-curd", "Lemon curd", JP, "Sweet spreads",
      ["dairy", "eggs"], DAIRY,
      300, 50, 3, 0.2, 9, 110, 49, 5.5,
      "Cooked lemon juice + sugar + egg yolks + butter."),
    S("pumpkin-butter", "Pumpkin butter", JP, "Sweet spreads", [], PLANT,
      213, 54, 0.6, 1.7, 0.1, 24, 47, 0.05,
      "Spiced reduced pumpkin paste.", form="paste"),
    S("fruit-chutney", "Fruit chutney (Indian-style)", JP, "Sweet spreads", [], PLANT,
      195, 48, 1.0, 1.5, 0.4, 720, 41, 0.05,
      "Sweet-and-sour spiced fruit condiment."),
    S("nutella", "Chocolate-hazelnut spread (Nutella-style)", JP, "Sweet spreads",
      ["dairy", "tree_nut", "soy", "caffeine"], PLANT,
      539, 58, 6.3, 3.4, 30, 32, 56, 11,
      "Hazelnut + cocoa + sugar + milk solids spread.", form="paste"),
    S("biscoff-spread", "Cookie butter (Biscoff-style)", JP, "Sweet spreads",
      ["gluten", "soy"], PLANT,
      535, 57, 4.4, 0, 31, 357, 45, 13,
      "Speculoos-cookie based spread.", form="paste"),
    S("almond-butter-sweetened", "Almond butter (sweetened)", JP, "Sweet spreads",
      ["tree_nut"], PLANT,
      557, 25, 16, 8, 49, 38, 18, 4,
      "Sweetened spread for toast.", form="paste"),
]


# ---------------------------------------------------------------------------
# Confectionery
# ---------------------------------------------------------------------------
CONFEC = [
    S("gummy-bear", "Gummy bears", SW, "Confectionery", ["animal_byproduct"], PLANT,
      325, 78, 6.9, 0, 0, 35, 47, 0,
      "Sugar + gelatin + fruit flavors."),
    S("jelly-bean", "Jelly beans", SW, "Confectionery", [], PLANT,
      375, 94, 0, 0, 0, 38, 70, 0,
      "Sugar shell + jelly center."),
    S("lollipop", "Lollipop (hard candy)", SW, "Confectionery", [], PLANT,
      394, 98, 0, 0, 0, 27, 63, 0,
      "Sugar + corn syrup on a stick."),
    S("candy-corn", "Candy corn", SW, "Confectionery", [], PLANT,
      375, 92, 0, 0, 0, 75, 79, 0,
      "Tri-colored Halloween candy; sugar + corn syrup + wax."),
    S("hard-candy", "Hard candy", SW, "Confectionery", [], PLANT,
      394, 98, 0, 0, 0, 38, 63, 0,
      "Generic boiled-sugar candy."),
    S("peppermint-candy", "Peppermint candy", SW, "Confectionery", [], PLANT,
      394, 98, 0, 0, 0, 32, 87, 0,
      "After-dinner mints / candy canes."),
    S("licorice-black", "Black licorice", SW, "Confectionery", [], PLANT,
      375, 81, 3.5, 0.5, 1.0, 220, 60, 0.5,
      "Anise-flavored chewy candy. Note: real licorice root affects blood pressure."),
    S("licorice-red", "Red licorice (Twizzlers-style)", SW, "Confectionery",
      ["gluten"], PLANT,
      350, 80, 2.5, 0, 1.5, 230, 50, 0.5,
      "Wheat-based strawberry candy. Despite the name, no real licorice."),
    S("gum-chewing", "Chewing gum (sweetened)", SW, "Confectionery", [], PLANT,
      360, 95, 0, 0, 0, 5, 65, 0,
      "Sugar-based gum (Hubba Bubba-style)."),
    S("marzipan", "Marzipan", SW, "Confectionery",
      ["tree_nut", "eggs"], PLANT,
      483, 56, 9, 5, 26, 5, 50, 2,
      "Almond + sugar + egg white paste.", form="paste"),
    S("meringue-cookie", "Meringue cookies", SW, "Confectionery", ["eggs"], PLANT,
      391, 95, 4, 0, 0, 100, 90, 0,
      "Baked egg-white + sugar; very light."),
    S("amaretti", "Amaretti", SW, "Confectionery", ["tree_nut", "eggs"], PLANT,
      425, 76, 7, 2, 11, 60, 55, 1,
      "Italian almond cookies; crisp or soft."),
    S("brittle-peanut", "Peanut brittle", SW, "Confectionery", ["peanut"], PLANT,
      486, 70, 7, 2, 21, 320, 56, 4,
      "Sugar caramelized around peanuts."),
    S("praline", "Praline (pecan)", SW, "Confectionery", ["tree_nut", "dairy"], PLANT,
      460, 65, 4, 2.5, 22, 100, 54, 5,
      "Southern US sugar + pecan candy."),
]


# ---------------------------------------------------------------------------
# Chocolate items
# ---------------------------------------------------------------------------
CHOC = [
    S("chocolate-bar-milk", "Chocolate bar (milk)", SW, "Chocolate",
      ["dairy", "soy", "caffeine"], PLANT,
      535, 59, 7.6, 3.4, 30, 79, 51, 19,
      "Standard candy bar (Hershey-style)."),
    S("chocolate-truffle", "Chocolate truffle", SW, "Chocolate",
      ["dairy", "caffeine"], DAIRY,
      540, 47, 5, 3, 38, 80, 41, 22,
      "Ganache center, cocoa-dusted."),
    S("peanut-butter-cup", "Peanut butter cup", SW, "Chocolate",
      ["dairy", "peanut", "soy", "caffeine"], PLANT,
      515, 56, 10, 3, 28, 320, 48, 11,
      "Reese's-style PB cup."),
    S("chocolate-syrup", "Chocolate syrup", SW, "Syrup",
      ["caffeine"], PLANT,
      279, 65, 2.0, 2.6, 1.1, 71, 50, 0.6,
      "Hershey's-style pourable syrup.", form="paste"),
    S("hot-fudge-sauce", "Hot fudge sauce", SW, "Syrup",
      ["dairy", "caffeine"], DAIRY,
      350, 60, 3, 2, 12, 180, 50, 7,
      "Rich chocolate sauce for ice cream."),
    S("white-chocolate-chips", "White chocolate chips", SW, "Chocolate", ["dairy", "soy"], PLANT,
      539, 59, 5.9, 0.2, 32, 90, 59, 19,
      "Cocoa butter + milk + sugar; no cocoa solids → no caffeine."),
]


# ---------------------------------------------------------------------------
# Syrups & toppings
# ---------------------------------------------------------------------------
SYRUPS = [
    S("pancake-syrup", "Pancake syrup (table)", SW, "Syrup", [], PLANT,
      265, 67, 0, 0, 0, 49, 60, 0,
      "Corn-syrup-based imitation maple; not real maple syrup."),
    S("caramel-sauce", "Caramel sauce", SW, "Syrup", ["dairy"], DAIRY,
      316, 78, 1, 0, 4, 175, 70, 2.5,
      "Cooked sugar + cream pouring sauce."),
    S("strawberry-topping", "Strawberry ice cream topping", SW, "Syrup", [], PLANT,
      265, 67, 0.3, 0.8, 0.1, 32, 56, 0,
      "Sundae topping syrup with fruit pieces."),
    S("simple-syrup", "Simple syrup", SW, "Syrup", [], PLANT,
      265, 67, 0, 0, 0, 5, 67, 0,
      "Equal parts sugar + water; cocktail/coffee sweetener."),
    S("grenadine", "Grenadine", SW, "Syrup", [], PLANT,
      265, 67, 0, 0, 0, 6, 67, 0,
      "Pomegranate-flavored sweetener; non-alcoholic mixer."),
    S("rose-syrup", "Rose syrup", SW, "Syrup", [], PLANT,
      280, 70, 0, 0, 0, 4, 68, 0,
      "Sweetened rose-water syrup; falooda / drinks."),
]


# ---------------------------------------------------------------------------
# Misc Sweets / Sugar
# ---------------------------------------------------------------------------
MISC = [
    S("maple-sugar", "Maple sugar (granulated)", SW, "Sugar", [], PLANT,
      354, 90, 0.1, 0, 0.2, 12, 90, 0.05,
      "Dehydrated maple syrup crystals.", form="powdered"),
    S("cane-syrup", "Cane syrup", SW, "Sweeteners", [], PLANT,
      278, 69, 0, 0, 0, 25, 65, 0,
      "Pure sugar cane reduction; richer than corn syrup."),
    S("date-syrup", "Date syrup", SW, "Sweeteners", [], PLANT,
      275, 70, 1.5, 1.5, 0, 5, 60, 0,
      "Reduced date paste; Middle Eastern sweetener."),
    S("rock-candy", "Rock candy", SW, "Confectionery", [], PLANT,
      387, 100, 0, 0, 0, 1, 100, 0,
      "Crystallized cane sugar on a stick."),
    S("dragees", "Dragées (silver-coated)", SW, "Confectionery", [], PLANT,
      390, 98, 0, 0, 0, 12, 78, 0,
      "Decorative candy beads for cake decoration."),
]


ALL_NEW = MIXES + PUDDINGS + JAMS + CONFEC + CHOC + SYRUPS + MISC


def main() -> None:
    with ING_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    by_id = {ing["id"]: ing for ing in data}

    appended = 0
    skipped = 0
    for entry in ALL_NEW:
        if entry["id"] in by_id:
            print(f"  ! skipped — id {entry['id']} already exists", file=sys.stderr)
            skipped += 1
            continue
        gw = entry["group_weights"]
        assert len(gw) == 3 and sum(gw) == 1 and gw.count(1) == 1 and gw.count(0) == 2, \
            f"{entry['id']} violates single-group rule: {gw}"
        assert entry["food_group"] == "Sweets", f"{entry['id']} has food_group={entry['food_group']}"
        data.append(entry)
        appended += 1

    print(f"\nSummary: {appended} new entries appended, {skipped} skipped.")
    write_compact(data, ING_PATH)
    print(f"Wrote {len(data)} entries to {ING_PATH}.")


def write_compact(data, path: Path) -> None:
    lines = ["["]
    for i, ing in enumerate(data):
        sep = "," if i < len(data) - 1 else ""
        lines.append("  " + json.dumps(ing, ensure_ascii=False, separators=(", ", ": ")) + sep)
    lines.append("]")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
