"""Phase 27: Western & European meal patterns (CSV-validated).

Two passes:
  1. Fix existing 26 meals: rename categories broken by the Phase 25 split
     ("Fruits" -> "Temperate fruits", "Non-starchy vegetables" -> "Other
     non-starchy" or "Peppers & nightshades" depending on context). Backfill
     `cuisine` on the ones that already fit a Western/European cuisine.
  2. Append ~70 new meal patterns across American, UK/Irish, French,
     Italian, Spanish/Portuguese, German/Austrian/Swiss, Eastern European,
     and Scandinavian cuisines. Each carries `cuisine`.

After this script, run:
   python scripts/validate_meal_pattern.py --all
to verify every meal pattern matches >=10 NLG recipes.
"""
from __future__ import annotations

import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEALS_PATH = ROOT / "src" / "data" / "meals.json"


# ---------------------------------------------------------------------------
# Pass 1: fixes to existing meals.
# ---------------------------------------------------------------------------

# id -> {'ingredient_categories': [...], 'cuisine': ...}
EXISTING_PATCHES = {
    "chicken-rice-bowl": {
        "ingredient_categories": ["Poultry", "Whole grains", "Other non-starchy"],
        "cuisine": "American",
    },
    "chicken-stir-fry": {
        "ingredient_categories": ["Poultry", "Other non-starchy", "Oils", "Whole grains"],
        "cuisine": "Chinese-American",
    },
    "tuna-salad": {
        "ingredient_categories": ["Oily fish", "Leafy greens", "Other non-starchy"],
        "cuisine": "American",
    },
    "burger": {
        "ingredient_categories": ["Red meat", "Bread & rolls", "Other non-starchy"],
        "cuisine": "American",
    },
    "cheeseburger": {
        "ingredient_categories": ["Red meat", "Bread & rolls", "Aged cheese", "Other non-starchy"],
        "cuisine": "American",
    },
    "omelet-veg-cheese": {
        "ingredient_categories": ["Eggs", "Other non-starchy", "Aged cheese"],
        "cuisine": "French",
    },
    "greek-salad": {
        "ingredient_categories": ["Leafy greens", "Aged cheese",
                                  "Peppers & nightshades", "Pickled vegetables", "Oils"],
        "cuisine": "Greek",
    },
    "caesar-salad": {
        "ingredient_categories": ["Leafy greens", "Aged cheese", "Bread & rolls", "Oils"],
        "cuisine": "American",
    },
    "hummus-plate": {
        "ingredient_categories": ["Legumes", "Oils", "Bread & rolls", "Other non-starchy"],
        "cuisine": "Levantine",
    },
    "bean-burrito": {
        "ingredient_categories": ["Legumes", "Bread & rolls", "Aged cheese", "Other non-starchy"],
        "cuisine": "Mexican-American",
    },
    "vegan-bowl": {
        "ingredient_categories": ["Legumes", "Whole grains", "Leafy greens", "Other non-starchy"],
        "cuisine": "American",
    },
    "tofu-stir-fry": {
        "ingredient_categories": ["Soy products", "Other non-starchy", "Whole grains", "Oils"],
        "cuisine": "Asian",
    },
    "pasta-red-sauce": {
        "ingredient_categories": ["Refined grains", "Peppers & nightshades", "Aged cheese"],
        "cuisine": "Italian",
    },
    "salmon-plate": {
        "ingredient_categories": ["Oily fish", "Starchy vegetables", "Leafy greens"],
        "cuisine": "American",
    },
    "fish-and-chips": {
        "ingredient_categories": ["White fish", "Starchy vegetables", "Oils"],
        "cuisine": "British",
    },
    "shrimp-pasta": {
        "ingredient_categories": ["Shellfish", "Refined grains", "Cream & butter", "Aged cheese"],
        "cuisine": "Italian-American",
    },
    "steak-dinner": {
        "ingredient_categories": ["Red meat", "Starchy vegetables", "Leafy greens", "Cream & butter"],
        "cuisine": "American",
    },
    "bacon-and-eggs": {
        "ingredient_categories": ["Processed meat", "Eggs"],
        "cuisine": "American",
    },
    "yogurt-parfait": {
        "ingredient_categories": ["Yogurt", "Berries", "Nuts"],
        "cuisine": "American",
    },
    "smoothie": {
        "ingredient_categories": ["Yogurt", "Berries", "Temperate fruits", "Seeds"],
        "cuisine": "American",
    },
    "cereal-bowl": {
        "ingredient_categories": ["Refined grains", "Milk", "Temperate fruits"],
        "cuisine": "American",
    },
    "oatmeal-berries": {
        "ingredient_categories": ["Whole grains", "Berries", "Nuts", "Milk"],
        "cuisine": "American",
    },
    "cheese-plate": {
        "ingredient_categories": ["Aged cheese", "Fresh cheese", "Dried fruits", "Nuts"],
        "cuisine": "European",
    },
    "pb-sandwich": {
        "ingredient_categories": ["Nut butters", "Bread & rolls", "Temperate fruits"],
        "cuisine": "American",
    },
    "fruit-and-nuts": {
        "ingredient_categories": ["Temperate fruits", "Nuts"],
        "cuisine": "Mediterranean",
    },
    "sashimi-platter": {
        "ingredient_categories": ["Oily fish", "White fish", "Refined grains"],
        "cuisine": "Japanese",
    },
}


# ---------------------------------------------------------------------------
# Pass 2: new Western & European meals.
# Each meal: id, name, ingredient_categories, cuisine, notes.
# ---------------------------------------------------------------------------
NEW_MEALS = [
    # ----- American -----
    dict(id="pancakes-syrup", name="Pancakes & syrup",
         ingredient_categories=["Bread & rolls", "Sugar & sweeteners", "Cream & butter", "Eggs"],
         cuisine="American", notes="Buttermilk pancakes stacked with butter and maple syrup."),
    dict(id="mac-and-cheese", name="Mac and cheese",
         ingredient_categories=["Refined grains", "Aged cheese", "Cream & butter", "Milk"],
         cuisine="American", notes="Baked or stovetop macaroni in a cheese-cream-butter sauce."),
    dict(id="cobb-salad", name="Cobb salad",
         ingredient_categories=["Leafy greens", "Poultry", "Eggs", "Aged cheese", "Processed meat"],
         cuisine="American", notes="Composed salad: chicken, bacon, egg, blue cheese, avocado over romaine."),
    dict(id="bbq-plate", name="BBQ plate",
         ingredient_categories=["Red meat", "Sauces", "Other non-starchy", "Bread & rolls"],
         cuisine="American", notes="Smoked brisket / ribs with BBQ sauce, slaw, and a bun."),
    dict(id="thanksgiving-plate", name="Thanksgiving plate",
         ingredient_categories=["Poultry", "Starchy vegetables", "Sauces", "Bread & rolls"],
         cuisine="American", notes="Roast turkey, mashed potatoes, gravy, and stuffing."),
    dict(id="biscuits-and-gravy", name="Biscuits and gravy",
         ingredient_categories=["Baked snacks & pastries", "Processed meat", "Sauces"],
         cuisine="American", notes="Buttermilk biscuits smothered in sausage cream gravy."),
    dict(id="chicken-and-waffles", name="Chicken and waffles",
         ingredient_categories=["Poultry", "Bread & rolls", "Sugar & sweeteners"],
         cuisine="American", notes="Fried chicken on a sweet waffle drizzled with syrup."),
    dict(id="club-sandwich", name="Club sandwich",
         ingredient_categories=["Processed meat", "Poultry", "Bread & rolls",
                                 "Aged cheese", "Peppers & nightshades"],
         cuisine="American", notes="Triple-decker turkey, bacon, lettuce, tomato, cheese."),
    dict(id="reuben-sandwich", name="Reuben sandwich",
         ingredient_categories=["Processed meat", "Aged cheese", "Bread & rolls", "Pickled vegetables"],
         cuisine="American", notes="Corned beef, Swiss, sauerkraut, Russian dressing on rye."),
    dict(id="buffalo-wings", name="Buffalo wings",
         ingredient_categories=["Poultry", "Sauces", "Dressings & dips"],
         cuisine="American", notes="Fried chicken wings tossed in hot sauce; blue cheese dip."),
    dict(id="chili-con-carne", name="Chili con carne",
         ingredient_categories=["Red meat", "Legumes", "Peppers & nightshades", "Ground spices"],
         cuisine="American", notes="Beef and bean stew with chili powder + cumin."),
    dict(id="philly-cheesesteak", name="Philly cheesesteak",
         ingredient_categories=["Red meat", "Aged cheese", "Bread & rolls", "Other non-starchy"],
         cuisine="American", notes="Thin-sliced beef + provolone + sautéed onions on a hoagie."),
    dict(id="meatloaf-mashed-potato", name="Meatloaf with mashed potato",
         ingredient_categories=["Red meat", "Starchy vegetables", "Eggs", "Sauces"],
         cuisine="American", notes="Baked ground-beef loaf with a tomato glaze."),
    dict(id="lobster-roll", name="Lobster roll",
         ingredient_categories=["Shellfish", "Bread & rolls", "Dressings & dips"],
         cuisine="American", notes="Chunked lobster meat in mayo on a butter-toasted bun."),

    # ----- UK / Irish -----
    dict(id="full-english-breakfast", name="Full English breakfast",
         ingredient_categories=["Eggs", "Processed meat", "Peppers & nightshades",
                                 "Mushrooms", "Legumes", "Bread & rolls"],
         cuisine="British", notes="Bacon, sausage, eggs, beans, tomato, mushrooms, toast."),
    dict(id="shepherds-pie", name="Shepherd's pie",
         ingredient_categories=["Red meat", "Starchy vegetables", "Other non-starchy"],
         cuisine="British", notes="Ground lamb / vegetables under a mashed-potato crust."),
    dict(id="bangers-and-mash", name="Bangers and mash",
         ingredient_categories=["Processed meat", "Starchy vegetables", "Sauces"],
         cuisine="British", notes="Pork sausage over mashed potato with onion gravy."),
    dict(id="ploughmans-lunch", name="Ploughman's lunch",
         ingredient_categories=["Aged cheese", "Processed meat", "Pickled vegetables",
                                 "Bread & rolls", "Temperate fruits"],
         cuisine="British", notes="Cheese, ham, pickle, bread, apple, chutney on a board."),
    dict(id="sunday-roast", name="Sunday roast",
         ingredient_categories=["Red meat", "Starchy vegetables", "Other non-starchy", "Sauces"],
         cuisine="British", notes="Roast beef, roast potatoes, vegetables, gravy."),
    dict(id="scones-cream-jam", name="Scones with cream and jam",
         ingredient_categories=["Baked snacks & pastries", "Cream & butter", "Jams & preserves"],
         cuisine="British", notes="Cream tea: scones, clotted cream, strawberry jam."),
    dict(id="beef-wellington", name="Beef Wellington",
         ingredient_categories=["Red meat", "Mushrooms", "Baked snacks & pastries", "Cream & butter"],
         cuisine="British", notes="Filet wrapped in mushroom duxelles + puff pastry."),
    dict(id="toad-in-the-hole", name="Toad in the hole",
         ingredient_categories=["Processed meat", "Bread & rolls", "Eggs"],
         cuisine="British", notes="Sausages baked in Yorkshire-pudding batter."),

    # ----- French -----
    dict(id="croque-monsieur", name="Croque-monsieur",
         ingredient_categories=["Processed meat", "Aged cheese", "Bread & rolls", "Cream & butter"],
         cuisine="French", notes="Grilled ham + Gruyère sandwich with béchamel."),
    dict(id="ratatouille", name="Ratatouille",
         ingredient_categories=["Peppers & nightshades", "Other non-starchy", "Oils", "Fresh herbs"],
         cuisine="French", notes="Provençal stew of eggplant, zucchini, tomatoes, herbs."),
    dict(id="beef-bourguignon", name="Beef bourguignon",
         ingredient_categories=["Red meat", "Mushrooms", "Other non-starchy", "Alcoholic beverages"],
         cuisine="French", notes="Beef braised in red wine with mushrooms + pearl onions."),
    dict(id="nicoise-salad", name="Salade niçoise",
         ingredient_categories=["Leafy greens", "Oily fish", "Eggs", "Pickled vegetables", "Starchy vegetables"],
         cuisine="French", notes="Tuna, egg, olives, potato, beans over salad greens."),
    dict(id="omelette-french", name="French omelette",
         ingredient_categories=["Eggs", "Aged cheese", "Cream & butter"],
         cuisine="French", notes="Soft-curd butter-rich rolled egg omelette."),
    dict(id="coq-au-vin", name="Coq au vin",
         ingredient_categories=["Poultry", "Alcoholic beverages", "Mushrooms", "Processed meat"],
         cuisine="French", notes="Chicken braised in red wine with lardons + mushrooms."),
    dict(id="bouillabaisse", name="Bouillabaisse",
         ingredient_categories=["White fish", "Shellfish", "Peppers & nightshades", "Prepared soups & broths"],
         cuisine="French", notes="Provençal fisherman's stew, saffron-tomato broth."),
    dict(id="quiche-lorraine", name="Quiche Lorraine",
         ingredient_categories=["Eggs", "Aged cheese", "Processed meat", "Baked snacks & pastries"],
         cuisine="French", notes="Egg + cream custard with bacon in a pastry shell."),
    dict(id="cassoulet", name="Cassoulet",
         ingredient_categories=["Legumes", "Processed meat", "Poultry"],
         cuisine="French", notes="White beans slow-cooked with duck confit + sausage."),
    dict(id="crepes-savory", name="Savory crêpes",
         ingredient_categories=["Eggs", "Aged cheese", "Processed meat", "Bread & rolls"],
         cuisine="French", notes="Buckwheat galette with ham, cheese, egg."),

    # ----- Italian -----
    dict(id="caprese", name="Caprese salad",
         ingredient_categories=["Fresh cheese", "Peppers & nightshades", "Fresh herbs", "Oils"],
         cuisine="Italian", notes="Mozzarella, tomato, basil, olive oil."),
    dict(id="pasta-carbonara", name="Pasta carbonara",
         ingredient_categories=["Refined grains", "Processed meat", "Eggs", "Aged cheese"],
         cuisine="Italian", notes="Spaghetti, guanciale, egg, pecorino, black pepper."),
    dict(id="pasta-bolognese", name="Pasta bolognese",
         ingredient_categories=["Refined grains", "Red meat", "Peppers & nightshades", "Aged cheese"],
         cuisine="Italian", notes="Tagliatelle with slow-cooked beef-tomato ragù."),
    dict(id="pesto-pasta", name="Pesto pasta",
         ingredient_categories=["Refined grains", "Sauces", "Aged cheese", "Nuts"],
         cuisine="Italian", notes="Pasta with basil-pine-nut-Parmesan pesto."),
    dict(id="pasta-amatriciana", name="Pasta all'amatriciana",
         ingredient_categories=["Refined grains", "Processed meat", "Peppers & nightshades", "Aged cheese"],
         cuisine="Italian", notes="Bucatini with guanciale, tomato, pecorino."),
    dict(id="risotto-mushroom", name="Mushroom risotto",
         ingredient_categories=["Refined grains", "Mushrooms", "Cream & butter", "Aged cheese"],
         cuisine="Italian", notes="Arborio rice creamy-cooked with mushrooms + Parmesan."),
    dict(id="risotto-milanese", name="Risotto Milanese",
         ingredient_categories=["Refined grains", "Whole spices", "Cream & butter", "Aged cheese"],
         cuisine="Italian", notes="Saffron-yellow risotto, classic ossobuco partner."),
    dict(id="pizza-margherita", name="Pizza margherita",
         ingredient_categories=["Bread & rolls", "Fresh cheese", "Peppers & nightshades", "Fresh herbs"],
         cuisine="Italian", notes="Naples-style tomato + mozzarella + basil pizza."),
    dict(id="osso-buco", name="Osso buco",
         ingredient_categories=["Red meat", "Other non-starchy", "Sauces", "Alcoholic beverages"],
         cuisine="Italian", notes="Braised veal shanks; Milanese gremolata garnish."),
    dict(id="lasagna", name="Lasagna",
         ingredient_categories=["Refined grains", "Red meat", "Fresh cheese", "Aged cheese", "Peppers & nightshades"],
         cuisine="Italian", notes="Layered pasta, ragù, ricotta, mozzarella, Parmesan."),

    # ----- Spanish / Portuguese -----
    dict(id="paella", name="Paella",
         ingredient_categories=["Refined grains", "Shellfish", "Poultry", "Peppers & nightshades", "Whole spices"],
         cuisine="Spanish", notes="Saffron rice with chicken, shrimp, mussels, peppers."),
    dict(id="tortilla-espanola", name="Tortilla española",
         ingredient_categories=["Eggs", "Starchy vegetables", "Oils"],
         cuisine="Spanish", notes="Thick potato + egg omelette."),
    dict(id="gazpacho", name="Gazpacho",
         ingredient_categories=["Peppers & nightshades", "Other non-starchy", "Oils", "Dressings & dips"],
         cuisine="Spanish", notes="Chilled raw-vegetable soup; tomato + cucumber + pepper + vinegar."),
    dict(id="patatas-bravas", name="Patatas bravas",
         ingredient_categories=["Starchy vegetables", "Sauces"],
         cuisine="Spanish", notes="Fried potatoes with spicy tomato sauce + aioli."),
    dict(id="bacalhau-com-natas", name="Bacalhau com natas",
         ingredient_categories=["Canned & cured fish", "Starchy vegetables", "Cream & butter"],
         cuisine="Portuguese", notes="Salt-cod casserole with potato and cream."),

    # ----- German / Austrian / Swiss -----
    dict(id="schnitzel", name="Wiener schnitzel",
         ingredient_categories=["Red meat", "Bread & rolls", "Eggs", "Citrus"],
         cuisine="Austrian", notes="Breaded-fried veal cutlet with lemon."),
    dict(id="rosti", name="Rösti",
         ingredient_categories=["Starchy vegetables", "Oils"],
         cuisine="Swiss", notes="Pan-fried grated potato cake."),
    dict(id="sauerbraten", name="Sauerbraten",
         ingredient_categories=["Red meat", "Pickled vegetables", "Sauces"],
         cuisine="German", notes="Vinegar-marinated braised pot roast."),
    dict(id="raclette-platter", name="Raclette platter",
         ingredient_categories=["Aged cheese", "Starchy vegetables", "Processed meat", "Pickled vegetables"],
         cuisine="Swiss", notes="Melted raclette over potatoes with charcuterie + cornichons."),
    dict(id="muesli-bowl", name="Muesli bowl",
         ingredient_categories=["Whole grains", "Dried fruits", "Nuts", "Milk"],
         cuisine="Swiss", notes="Bircher-style oats with fruit, nuts, milk."),
    dict(id="spaetzle-cheese", name="Käsespätzle",
         ingredient_categories=["Refined grains", "Aged cheese", "Other non-starchy"],
         cuisine="German", notes="Soft egg noodles tossed with cheese + caramelized onion."),
    dict(id="currywurst", name="Currywurst",
         ingredient_categories=["Processed meat", "Sauces", "Ground spices"],
         cuisine="German", notes="Sliced sausage with curry-ketchup sauce."),

    # ----- Eastern European -----
    dict(id="pierogi-potato-cheese", name="Pierogi (potato-cheese)",
         ingredient_categories=["Refined grains", "Starchy vegetables", "Fresh cheese", "Cream & butter"],
         cuisine="Polish", notes="Boiled / pan-fried dumplings; sour cream on top."),
    dict(id="borscht", name="Borscht",
         ingredient_categories=["Starchy vegetables", "Other non-starchy", "Cream & butter"],
         cuisine="Eastern European", notes="Beet soup with sour cream; Russian / Ukrainian."),
    dict(id="goulash", name="Goulash",
         ingredient_categories=["Red meat", "Peppers & nightshades", "Starchy vegetables", "Ground spices"],
         cuisine="Hungarian", notes="Paprika-rich beef stew."),
    dict(id="blini-caviar", name="Blini with caviar",
         ingredient_categories=["Bread & rolls", "Canned & cured fish", "Cream & butter"],
         cuisine="Russian", notes="Small yeasted buckwheat pancakes; caviar + sour cream."),
    dict(id="stuffed-cabbage", name="Stuffed cabbage rolls",
         ingredient_categories=["Other non-starchy", "Red meat", "Refined grains", "Sauces"],
         cuisine="Eastern European", notes="Gołąbki: cabbage leaves stuffed with meat + rice + tomato."),

    # ----- Scandinavian -----
    dict(id="smorgasbord-plate", name="Smörgåsbord plate",
         ingredient_categories=["Bread & rolls", "Canned & cured fish", "Aged cheese", "Pickled vegetables"],
         cuisine="Scandinavian", notes="Mixed cold open-face sandwiches + cured fish + cheese."),
    dict(id="gravlax-plate", name="Gravlax plate",
         ingredient_categories=["Canned & cured fish", "Dressings & dips", "Bread & rolls"],
         cuisine="Scandinavian", notes="Cured salmon with mustard-dill sauce on rye."),
    dict(id="swedish-meatballs", name="Swedish meatballs",
         ingredient_categories=["Red meat", "Sauces", "Cream & butter", "Jams & preserves"],
         cuisine="Swedish", notes="Pork-beef meatballs with cream gravy + lingonberry jam."),
    dict(id="pickled-herring-plate", name="Pickled herring plate",
         ingredient_categories=["Canned & cured fish", "Cream & butter", "Bread & rolls"],
         cuisine="Scandinavian", notes="Pickled herring with sour cream + dark rye."),
    dict(id="danish-pastry-coffee", name="Danish pastry & coffee",
         ingredient_categories=["Baked snacks & pastries", "Coffee & tea", "Cream & butter"],
         cuisine="Danish", notes="Morning kaffe with a buttery laminated pastry."),

    # ----- Greek / Mediterranean (mix; some not strictly W/E but adjacent) -----
    dict(id="moussaka", name="Moussaka",
         ingredient_categories=["Red meat", "Other non-starchy", "Aged cheese", "Cream & butter"],
         cuisine="Greek", notes="Layered eggplant + lamb + béchamel bake."),
    dict(id="spanakopita", name="Spanakopita",
         ingredient_categories=["Leafy greens", "Aged cheese", "Baked snacks & pastries", "Eggs"],
         cuisine="Greek", notes="Spinach + feta in filo dough."),
    dict(id="souvlaki-plate", name="Souvlaki plate",
         ingredient_categories=["Red meat", "Bread & rolls", "Dairy sauces", "Other non-starchy"],
         cuisine="Greek", notes="Grilled meat skewers, tzatziki, pita, vegetables."),
]


def main() -> int:
    with MEALS_PATH.open("r", encoding="utf-8") as f:
        meals = json.load(f)
    by_id = {m["id"]: m for m in meals}

    # Pass 1: patch existing
    patched = 0
    for mid, patch in EXISTING_PATCHES.items():
        if mid in by_id:
            m = by_id[mid]
            changed = False
            for k, v in patch.items():
                if m.get(k) != v:
                    m[k] = v
                    changed = True
            if changed:
                patched += 1
    print(f"Pass 1: existing meals patched: {patched}")

    # Pass 2: append new
    appended = 0
    skipped = 0
    for new in NEW_MEALS:
        if new["id"] in by_id:
            print(f"  ! skipped (id exists): {new['id']}", file=sys.stderr)
            skipped += 1
            continue
        meals.append(new)
        appended += 1
    print(f"Pass 2: new meals appended: {appended} ({skipped} skipped)")

    with MEALS_PATH.open("w", encoding="utf-8") as f:
        json.dump(meals, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\nWrote {len(meals)} meals to {MEALS_PATH}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
