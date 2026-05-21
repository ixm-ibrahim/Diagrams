"""Phase 31: snacks, desserts, cross-cultural beverages, composed plates.

~52 new meals rounding out coverage with meal-adjacent categories that
span cuisines:
  - Snacks (~13): charcuterie boards, dip & chip combos, popcorn, trail mix
  - Desserts (~18): cakes, pies, ice cream, mochi, halwa, churros, etc.
  - Beverages (~13): smoothies, lattes, lassis, chai, boba, horchata
  - Composed plates (~8): continental breakfast, afternoon tea, brunch

Each carries a `cuisine` tag where regionally distinct; cross-cultural ones
use 'Cross-cultural' or the dominant origin.
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
    # ---------- Snacks ----------
    M("charcuterie-board", "Charcuterie board",
      ["Processed meat", "Aged cheese", "Bread & rolls", "Pickled vegetables"],
      "European", "Cured meats, cheeses, crackers, olives, mustard, fruit."),
    M("antipasto-platter", "Antipasto platter",
      ["Processed meat", "Aged cheese", "Pickled vegetables", "Other non-starchy"],
      "Italian", "Salumi, cheeses, marinated vegetables, olives, peperoncini."),
    M("popcorn-buttered", "Buttered popcorn",
      ["Whole grains", "Cream & butter", "Salt & seasonings"],
      "American", "Stovetop or air-popped popcorn tossed with melted butter and salt."),
    M("popcorn-caramel", "Caramel popcorn",
      ["Whole grains", "Sugar & sweeteners", "Cream & butter", "Nuts"],
      "American", "Popcorn coated in caramel; often peanut + Cracker Jack-style."),
    M("chips-and-salsa", "Chips & salsa",
      ["Baked snacks & pastries", "Sauces", "Peppers & nightshades"],
      "Mexican-American", "Tortilla chips with fresh tomato salsa."),
    M("chips-and-guacamole", "Chips & guacamole",
      ["Baked snacks & pastries", "Sauces", "Citrus", "Fresh herbs"],
      "Mexican", "Tortilla chips with avocado dip + lime + cilantro."),
    M("chips-and-queso", "Chips & queso",
      ["Baked snacks & pastries", "Processed cheese", "Peppers & nightshades"],
      "Tex-Mex", "Chips with hot melted-cheese-and-pepper dip."),
    M("nut-mix-roasted", "Roasted nut mix",
      ["Nuts", "Salt & seasonings", "Oils"],
      "Cross-cultural", "Roasted, lightly salted mixed nuts."),
    M("trail-mix", "Trail mix",
      ["Nuts", "Dried fruits", "Seeds", "Candy & desserts"],
      "American", "Nuts + raisins + M&Ms or chocolate chips."),
    M("crudite-platter", "Crudité platter",
      ["Other non-starchy", "Peppers & nightshades", "Dressings & dips", "Leafy greens"],
      "Cross-cultural", "Raw vegetable sticks with ranch or hummus dip."),
    M("fruit-platter", "Fruit platter",
      ["Tropical fruits", "Berries", "Temperate fruits", "Citrus"],
      "Cross-cultural", "Cut fresh fruit assortment."),
    M("snack-board-mediterranean", "Mediterranean snack board",
      ["Legumes", "Pickled vegetables", "Aged cheese", "Bread & rolls"],
      "Mediterranean", "Hummus, olives, feta, pita, cucumber, peppers."),
    M("pretzels-mustard", "Pretzels with mustard",
      ["Baked snacks & pastries", "Sauces"],
      "German-American", "Soft pretzel with grainy or German mustard."),

    # ---------- Desserts ----------
    M("chocolate-cake-slice", "Chocolate cake slice",
      ["Candy & desserts", "Cream & butter", "Eggs", "Sugar & sweeteners"],
      "American", "Layer cake with chocolate ganache or buttercream frosting."),
    M("carrot-cake-slice", "Carrot cake with cream cheese frosting",
      ["Bread & rolls", "Starchy vegetables", "Cream & butter", "Nuts"],
      "American", "Spiced cake with shredded carrot and cream-cheese icing."),
    M("cheesecake-plain", "New York cheesecake",
      ["Fresh cheese", "Eggs", "Sugar & sweeteners", "Cream & butter"],
      "American", "Dense cream-cheese cake on a graham-cracker crust."),
    M("cheesecake-strawberry", "Strawberry cheesecake",
      ["Fresh cheese", "Berries", "Sugar & sweeteners", "Cream & butter"],
      "American", "Cheesecake topped with strawberry compote."),
    M("tres-leches-cake", "Tres leches cake",
      ["Bread & rolls", "Milk", "Cream & butter", "Sugar & sweeteners"],
      "Latin American", "Sponge cake soaked in three milks; whipped cream topping."),
    M("red-velvet-cake", "Red velvet cake",
      ["Bread & rolls", "Cream & butter", "Sugar & sweeteners", "Fresh cheese"],
      "American-Southern", "Cocoa-tinted layer cake with cream-cheese frosting."),
    M("apple-pie", "Apple pie",
      ["Temperate fruits", "Baked snacks & pastries", "Sugar & sweeteners", "Ground spices"],
      "American", "Double-crust pie with cinnamon-spiced apples; à la mode optional."),
    M("pumpkin-pie", "Pumpkin pie",
      ["Starchy vegetables", "Baked snacks & pastries", "Sugar & sweeteners", "Whole spices"],
      "American", "Custard pie of spiced pumpkin purée; Thanksgiving classic."),
    M("pecan-pie", "Pecan pie",
      ["Nuts", "Baked snacks & pastries", "Sugar & sweeteners", "Eggs"],
      "American-Southern", "Corn-syrup + brown sugar + pecan filling in pastry."),
    M("key-lime-pie", "Key lime pie",
      ["Citrus", "Milk", "Baked snacks & pastries", "Eggs"],
      "American-Floridian", "Key-lime + condensed-milk custard in graham crust."),
    M("ice-cream-sundae", "Ice cream sundae",
      ["Frozen dairy", "Candy & desserts", "Cream & butter", "Nuts"],
      "American", "Scoops with hot fudge, whipped cream, nuts, cherry."),
    M("tiramisu", "Tiramisu",
      ["Baked snacks & pastries", "Fresh cheese", "Coffee & tea", "Eggs"],
      "Italian", "Layers of espresso-soaked ladyfingers + mascarpone cream + cocoa."),
    M("halwa-semolina", "Suji halwa",
      ["Refined grains", "Cream & butter", "Sugar & sweeteners", "Nuts"],
      "Indian", "Semolina cooked in ghee + sugar + cardamom + cashew + raisin."),
    M("mochi-ice-cream", "Mochi ice cream",
      ["Refined grains", "Frozen dairy", "Sugar & sweeteners"],
      "Japanese-American", "Ice cream wrapped in soft glutinous-rice dough."),
    M("churros-chocolate", "Churros with chocolate",
      ["Baked snacks & pastries", "Sugar & sweeteners", "Candy & desserts", "Milk"],
      "Spanish", "Fried-dough sticks rolled in cinnamon sugar; thick chocolate dip."),
    M("creme-brulee", "Crème brûlée",
      ["Eggs", "Cream & butter", "Sugar & sweeteners", "Extracts & essences"],
      "French", "Vanilla custard with a torched caramelized sugar lid."),
    M("panna-cotta", "Panna cotta",
      ["Cream & butter", "Sugar & sweeteners", "Berries", "Extracts & essences"],
      "Italian", "Set-cream dessert; berry coulis on top."),
    M("crepe-suzette", "Crêpes Suzette",
      ["Bread & rolls", "Citrus", "Cream & butter", "Alcoholic beverages"],
      "French", "Thin crêpes flambéed in orange-Grand Marnier butter sauce."),
    M("bread-pudding", "Bread pudding",
      ["Bread & rolls", "Milk", "Eggs", "Sugar & sweeteners"],
      "American", "Custard-soaked stale bread baked with raisins + spice."),
    M("chocolate-fondue", "Chocolate fondue",
      ["Candy & desserts", "Cream & butter", "Temperate fruits", "Berries"],
      "Swiss", "Melted chocolate-cream dip with fruit + cake skewers."),
    M("affogato", "Affogato",
      ["Coffee & tea", "Frozen dairy"],
      "Italian", "Hot espresso poured over a scoop of vanilla gelato."),

    # ---------- Beverages ----------
    M("berry-smoothie", "Berry smoothie",
      ["Berries", "Yogurt", "Milk", "Sugar & sweeteners"],
      "American", "Blended berries + yogurt + milk + honey."),
    M("green-smoothie", "Green smoothie",
      ["Leafy greens", "Temperate fruits", "Seeds", "Milk"],
      "American", "Spinach/kale + banana + chia + plant milk."),
    M("protein-smoothie", "Protein smoothie",
      ["Milk", "Berries", "Nut butters", "Seeds"],
      "American", "Milk + protein powder + frozen berries + nut butter."),
    M("vanilla-latte", "Vanilla latte",
      ["Coffee & tea", "Milk", "Sugar & sweeteners", "Extracts & essences"],
      "American", "Espresso + steamed milk + vanilla syrup."),
    M("masala-chai-latte", "Masala chai latte",
      ["Coffee & tea", "Milk", "Whole spices", "Sugar & sweeteners"],
      "Indian", "Black tea simmered with milk + cardamom + ginger + cinnamon."),
    M("matcha-latte", "Matcha latte",
      ["Coffee & tea", "Milk", "Sugar & sweeteners"],
      "Japanese", "Whisked matcha + steamed milk."),
    M("boba-milk-tea", "Boba milk tea",
      ["Coffee & tea", "Milk", "Refined grains", "Sugar & sweeteners"],
      "Taiwanese", "Sweetened milk tea with chewy tapioca pearls."),
    M("sweet-lassi", "Sweet lassi",
      ["Yogurt", "Milk", "Sugar & sweeteners", "Whole spices"],
      "Indian", "Sweet yogurt-milk drink with cardamom + rose."),
    M("mango-lassi", "Mango lassi",
      ["Yogurt", "Tropical fruits", "Milk", "Sugar & sweeteners"],
      "Indian", "Yogurt + ripe mango + sugar; blended cold."),
    M("horchata-mexican", "Mexican horchata",
      ["Refined grains", "Milk", "Sugar & sweeteners", "Ground spices"],
      "Mexican", "Rice + cinnamon + milk + sugar blended drink."),
    M("agua-fresca-watermelon", "Watermelon agua fresca",
      ["Temperate fruits", "Citrus", "Sugar & sweeteners"],
      "Mexican", "Blended watermelon + lime + water + a touch of sugar."),
    M("hot-chocolate", "Hot chocolate",
      ["Milk", "Candy & desserts", "Sugar & sweeteners"],
      "Cross-cultural", "Steamed milk with cocoa and sugar; marshmallow optional."),
    M("turkish-coffee", "Turkish coffee",
      ["Coffee & tea", "Sugar & sweeteners", "Whole spices"],
      "Turkish", "Unfiltered finely-ground coffee; cardamom-laced."),

    # ---------- Composed plates ----------
    M("continental-breakfast", "Continental breakfast",
      ["Baked snacks & pastries", "Coffee & tea", "Jams & preserves", "Cream & butter"],
      "European", "Croissant + butter + jam + coffee + juice."),
    M("afternoon-tea-spread", "Afternoon tea spread",
      ["Baked snacks & pastries", "Coffee & tea", "Cream & butter", "Jams & preserves"],
      "British", "Tea, scones with cream + jam, finger sandwiches, petits fours."),
    M("brunch-platter", "Brunch platter",
      ["Eggs", "Processed meat", "Bread & rolls", "Temperate fruits"],
      "American", "Eggs Benedict-style with bacon, toast, fruit, mimosa."),
    M("kids-lunchbox", "Kids' lunchbox",
      ["Bread & rolls", "Processed meat", "Aged cheese", "Temperate fruits"],
      "American", "PB&J or ham-and-cheese sandwich, apple, crackers, juice."),
    M("bistro-plate", "Bistro plate",
      ["Aged cheese", "Processed meat", "Pickled vegetables", "Baked snacks & pastries"],
      "French", "Charcuterie + cheese + cornichon + crusty bread."),
    M("japanese-breakfast", "Japanese breakfast",
      ["Refined grains", "Oily fish", "Soy products", "Pastes & ferments"],
      "Japanese", "Steamed rice + grilled fish + miso soup + pickles + natto."),
    M("dim-sum-brunch", "Dim sum brunch",
      ["Bread & rolls", "Shellfish", "Coffee & tea", "Leafy greens"],
      "Chinese-Cantonese", "Multiple steamed/fried small plates with tea."),
    M("indian-breakfast", "South Indian breakfast",
      ["Whole grains", "Legumes", "Pastes & ferments", "Coffee & tea"],
      "Indian-South", "Idli or dosa with sambar + coconut chutney + filter coffee."),
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
