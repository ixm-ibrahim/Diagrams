"""Phase 15: critical anchor ingredients.

Applies two kinds of changes to src/data/ingredients.json:

  1. Moves existing entries into the new Phase 15 categories
     (saltine-crackers, breads, pickles, olives, lard, shortening, jam-strawberry).
  2. Appends 26 new anchor ingredients across all 12 new categories,
     beginning with the highest-impact gap: plain salt.

Run with:  python scripts/phase15_apply.py

Idempotent: re-running is a no-op (the moves are skipped if already done,
new entries are skipped if their id is already in the file).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ING_PATH = ROOT / "src" / "data" / "ingredients.json"

# --- Moves: id -> (new_category, new_subcategory, new_food_group_or_None) ----------
# food_group=None means keep existing food_group; otherwise reassign.
MOVES = {
    # Bread & baked goods — anchors that establish the new category.
    "white-bread":        ("Bread & baked goods", "Bread",     "Grains"),
    "whole-wheat-bread":  ("Bread & baked goods", "Bread",     "Grains"),
    "saltine-crackers":   ("Bread & baked goods", "Crackers",  "Grains"),
    # Margarine & shortening — fold the existing fat entries into the new category.
    "lard":               ("Margarine & shortening", "Animal fats", "Fats & oils"),
    "shortening":         ("Margarine & shortening", "Shortening",  "Fats & oils"),
    # Pickled vegetables — promote to its own category under Condiments & sauces food_group.
    "pickle-dill":  ("Pickled vegetables", "Pickled cucumber & cabbage", "Condiments & sauces"),
    "olives-green": ("Pickled vegetables", "Other pickled",              "Condiments & sauces"),
    "olives-black": ("Pickled vegetables", "Other pickled",              "Condiments & sauces"),
    # Jams & preserves — pull jam-strawberry out of Sweets/Preserves.
    "jam-strawberry": ("Jams & preserves", "Fruit preserves", "Sweets"),
}

# --- New anchor ingredients ---------------------------------------------------------
# Per-100g USDA-style values. Each ingredient follows the single-group rule:
# exactly one channel = 1 in group_weights.
NEW = [
    # ---------------- Salt & seasonings (Herbs & spices food_group) -----------------
    {
        "id": "salt-table", "name": "Salt (table)",
        "category": "Salt & seasonings", "subcategory": "Salt",
        "food_group": "Herbs & spices", "contains": [],
        "group_weights": [0, 1, 0],
        "examples": ["seasoning", "baking", "everyday cooking"],
        "calories": 0, "carbs": 0, "protein": 0, "fiber": 0,
        "fat": 0, "sodium": 38758, "sugar": 0, "saturated_fat": 0,
        "notes": "Refined sodium chloride with anti-caking + often iodine. Mineral, not animal/plant/dairy; filed as plant per the single-group rule (same convention as baking soda)."
    },
    {
        "id": "salt-kosher", "name": "Salt (kosher)",
        "category": "Salt & seasonings", "subcategory": "Salt",
        "food_group": "Herbs & spices", "contains": [],
        "group_weights": [0, 1, 0],
        "examples": ["meat curing", "rim-of-glass", "finishing salt"],
        "calories": 0, "carbs": 0, "protein": 0, "fiber": 0,
        "fat": 0, "sodium": 37500, "sugar": 0, "saturated_fat": 0,
        "notes": "Coarse flaky crystals; lower sodium per teaspoon than table salt due to crystal size. Per-100g sodium is similar."
    },
    {
        "id": "salt-sea", "name": "Salt (sea)",
        "category": "Salt & seasonings", "subcategory": "Salt",
        "food_group": "Herbs & spices", "contains": [],
        "group_weights": [0, 1, 0],
        "examples": ["finishing", "baking", "table seasoning"],
        "calories": 0, "carbs": 0, "protein": 0, "fiber": 0,
        "fat": 0, "sodium": 38758, "sugar": 0, "saturated_fat": 0,
        "notes": "Evaporated seawater; trace minerals beyond NaCl. Sodium content essentially identical to table salt."
    },
    {
        "id": "seasoned-salt", "name": "Seasoned salt",
        "category": "Salt & seasonings", "subcategory": "Seasoned salts",
        "food_group": "Herbs & spices", "contains": [],
        "group_weights": [0, 1, 0], "form": "powdered",
        "examples": ["fries seasoning", "popcorn", "roast chicken rub"],
        "calories": 20, "carbs": 4, "protein": 0.5, "fiber": 0.5,
        "fat": 0.5, "sodium": 27000, "sugar": 0.5, "saturated_fat": 0.1,
        "notes": "Lawry's-style blend: salt + paprika + garlic powder + turmeric + onion powder."
    },

    # ---------------- Bread & baked goods (Grains food_group) -----------------------
    {
        "id": "bread-crumbs", "name": "Bread crumbs",
        "category": "Bread & baked goods", "subcategory": "Bread crumbs",
        "food_group": "Grains", "contains": ["gluten"],
        "group_weights": [0, 1, 0], "form": "dried",
        "examples": ["breading for cutlets", "meatball binder", "casserole topping"],
        "calories": 395, "carbs": 72, "protein": 14, "fiber": 4.5,
        "fat": 5, "sodium": 735, "sugar": 3, "saturated_fat": 1.1,
        "notes": "Plain dry crumbs (not panko). Italian-seasoned variants would carry extra sodium."
    },
    {
        "id": "graham-crackers", "name": "Graham crackers",
        "category": "Bread & baked goods", "subcategory": "Graham crackers",
        "food_group": "Grains", "contains": ["gluten"],
        "group_weights": [0, 1, 0],
        "examples": ["s'mores", "pie crust base", "snack with milk"],
        "calories": 423, "carbs": 78, "protein": 7, "fiber": 2.7,
        "fat": 10, "sodium": 566, "sugar": 24, "saturated_fat": 2,
        "notes": "Lightly sweetened whole-wheat-flour crackers; honey/molasses sweetened."
    },

    # ---------------- Margarine & shortening (Fats & oils food_group) ---------------
    {
        "id": "margarine-stick", "name": "Margarine (stick)",
        "category": "Margarine & shortening", "subcategory": "Margarine",
        "food_group": "Fats & oils", "contains": [],
        "group_weights": [0, 1, 0],
        "examples": ["baking substitute for butter", "spreading on toast", "frying"],
        "calories": 717, "carbs": 0.7, "protein": 0.2, "fiber": 0,
        "fat": 80, "sodium": 659, "sugar": 0, "saturated_fat": 15,
        "notes": "Hydrogenated vegetable oil + water + emulsifiers. Plant-dominant per the single-group rule even when blended with milk solids."
    },

    # ---------------- Alcoholic beverages (Beverages food_group) --------------------
    {
        "id": "wine-red", "name": "Red wine",
        "category": "Alcoholic beverages", "subcategory": "Wine",
        "food_group": "Beverages", "contains": ["alcohol"],
        "group_weights": [0, 1, 0],
        "examples": ["dinner pairing", "braising liquid", "sangria base"],
        "calories": 85, "carbs": 2.6, "protein": 0.07, "fiber": 0,
        "fat": 0, "sodium": 4, "sugar": 0.6, "saturated_fat": 0,
        "notes": "Typical dry red, ~12% ABV. Most calories come from ethanol (7 kcal/g)."
    },
    {
        "id": "beer-lager", "name": "Beer (lager)",
        "category": "Alcoholic beverages", "subcategory": "Beer",
        "food_group": "Beverages", "contains": ["alcohol", "gluten"],
        "group_weights": [0, 1, 0],
        "examples": ["with pizza", "beer can chicken", "summer pour"],
        "calories": 43, "carbs": 3.6, "protein": 0.46, "fiber": 0,
        "fat": 0, "sodium": 4, "sugar": 0, "saturated_fat": 0,
        "notes": "Standard American lager, ~4-5% ABV. Carries gluten from barley malt."
    },
    {
        "id": "vodka", "name": "Vodka",
        "category": "Alcoholic beverages", "subcategory": "Vodka",
        "food_group": "Beverages", "contains": ["alcohol"],
        "group_weights": [0, 1, 0],
        "examples": ["martini", "vodka tonic", "marinara enhancer"],
        "calories": 231, "carbs": 0, "protein": 0, "fiber": 0,
        "fat": 0, "sodium": 1, "sugar": 0, "saturated_fat": 0,
        "notes": "80-proof (40% ABV). Pure ethanol + water; carb-free."
    },

    # ---------------- Prepared mixes (Sweets food_group) ----------------------------
    {
        "id": "cake-mix-yellow", "name": "Cake mix (yellow)",
        "category": "Prepared mixes", "subcategory": "Cake mixes",
        "food_group": "Sweets", "contains": ["gluten"],
        "group_weights": [0, 1, 0], "form": "powdered",
        "examples": ["birthday cake base", "cupcakes", "trifle layers"],
        "calories": 412, "carbs": 80, "protein": 4.4, "fiber": 0.5,
        "fat": 7.6, "sodium": 575, "sugar": 46, "saturated_fat": 2,
        "notes": "Dry mix; eggs / oil / water added at use. Betty Crocker-style."
    },
    {
        "id": "pudding-mix-vanilla", "name": "Pudding mix (vanilla, instant)",
        "category": "Prepared mixes", "subcategory": "Puddings",
        "food_group": "Sweets", "contains": [],
        "group_weights": [0, 1, 0], "form": "powdered",
        "examples": ["pudding cups", "pie filling", "icebox cake"],
        "calories": 370, "carbs": 92, "protein": 0, "fiber": 0,
        "fat": 0, "sodium": 900, "sugar": 84, "saturated_fat": 0,
        "notes": "Dry instant mix (sugar + modified starch + flavor). Milk added at use."
    },
    {
        "id": "whipped-topping-frozen", "name": "Whipped topping (frozen)",
        "category": "Prepared mixes", "subcategory": "Whipped toppings",
        "food_group": "Sweets", "contains": ["dairy"],
        "group_weights": [0, 0, 1], "form": "frozen",
        "examples": ["pie topping", "Jell-O salad", "fruit dip"],
        "calories": 259, "carbs": 23, "protein": 1, "fiber": 0,
        "fat": 18, "sodium": 70, "sugar": 23, "saturated_fat": 15,
        "notes": "Cool Whip-style. Contains skim milk + light cream; dairy-dominant per the single-group rule."
    },

    # ---------------- Processed cheese (Dairy food_group) ---------------------------
    {
        "id": "american-cheese", "name": "American cheese (slices)",
        "category": "Processed cheese", "subcategory": "Processed cheese",
        "food_group": "Dairy", "contains": ["dairy"],
        "group_weights": [0, 0, 1],
        "examples": ["grilled cheese", "burger topping", "deli sandwich"],
        "calories": 375, "carbs": 7, "protein": 18, "fiber": 0,
        "fat": 31, "sodium": 1671, "sugar": 4, "saturated_fat": 20,
        "notes": "Pasteurized process cheese product. Melts evenly; very salty."
    },
    {
        "id": "velveeta", "name": "Velveeta-style processed cheese",
        "category": "Processed cheese", "subcategory": "Processed cheese",
        "food_group": "Dairy", "contains": ["dairy"],
        "group_weights": [0, 0, 1],
        "examples": ["queso dip", "mac and cheese", "Rotel dip"],
        "calories": 300, "carbs": 10, "protein": 15, "fiber": 0,
        "fat": 20, "sodium": 1500, "sugar": 10, "saturated_fat": 14,
        "notes": "Pasteurized cheese product loaf. Smoother melt than American slices; more carbs from whey/milk solids."
    },

    # ---------------- Pickled vegetables (Condiments & sauces food_group) ----------
    {
        "id": "capers", "name": "Capers",
        "category": "Pickled vegetables", "subcategory": "Capers",
        "food_group": "Condiments & sauces", "contains": [],
        "group_weights": [0, 1, 0], "form": "pickled",
        "examples": ["chicken piccata", "pasta puttanesca", "tartar sauce"],
        "calories": 23, "carbs": 4.9, "protein": 2.4, "fiber": 3.2,
        "fat": 0.9, "sodium": 2960, "sugar": 0.4, "saturated_fat": 0.2,
        "notes": "Brined flower buds. Drained values; the brine itself is much saltier."
    },

    # ---------------- Prepared soups & broths (Beverages food_group) ----------------
    {
        "id": "chicken-broth", "name": "Chicken broth (canned)",
        "category": "Prepared soups & broths", "subcategory": "Broths & stocks",
        "food_group": "Beverages", "contains": ["meat"],
        "group_weights": [1, 0, 0], "form": "canned",
        "examples": ["soup base", "rice cooking liquid", "deglazing"],
        "calories": 15, "carbs": 0.4, "protein": 2.6, "fiber": 0,
        "fat": 0.5, "sodium": 343, "sugar": 0, "saturated_fat": 0.1,
        "notes": "Standard reduced-sodium canned/boxed broth. Plain unflavored regular has ~700mg sodium per 100g."
    },
    {
        "id": "beef-broth", "name": "Beef broth (canned)",
        "category": "Prepared soups & broths", "subcategory": "Broths & stocks",
        "food_group": "Beverages", "contains": ["meat"],
        "group_weights": [1, 0, 0], "form": "canned",
        "examples": ["French onion soup", "gravy base", "pot roast"],
        "calories": 7, "carbs": 0.1, "protein": 1.2, "fiber": 0,
        "fat": 0.2, "sodium": 363, "sugar": 0, "saturated_fat": 0.1,
        "notes": "Canned/boxed. Animal-derived per the single-group rule."
    },
    {
        "id": "cream-of-mushroom-soup", "name": "Cream of mushroom soup (condensed)",
        "category": "Prepared soups & broths", "subcategory": "Broths & stocks",
        "food_group": "Beverages", "contains": ["dairy", "gluten"],
        "group_weights": [0, 0, 1], "form": "canned",
        "examples": ["green bean casserole", "chicken & rice bake", "tuna casserole"],
        "calories": 99, "carbs": 8, "protein": 1.6, "fiber": 0.3,
        "fat": 7, "sodium": 683, "sugar": 0.4, "saturated_fat": 2,
        "notes": "Condensed (undiluted) per-100g values. Dairy-dominant per the single-group rule (cream + mushroom — cream is mass-dominant)."
    },

    # ---------------- Coffee & tea (Beverages food_group) ---------------------------
    {
        "id": "coffee-brewed", "name": "Coffee (brewed)",
        "category": "Coffee & tea", "subcategory": "Coffee",
        "food_group": "Beverages", "contains": ["caffeine"],
        "group_weights": [0, 1, 0],
        "examples": ["morning cup", "pour-over", "drip coffee"],
        "calories": 1, "carbs": 0, "protein": 0.1, "fiber": 0,
        "fat": 0.02, "sodium": 2, "sugar": 0, "saturated_fat": 0,
        "notes": "Black, unsweetened, no milk. Brewed strength assumes ~60mg caffeine per 100g."
    },
    {
        "id": "tea-black-brewed", "name": "Black tea (brewed)",
        "category": "Coffee & tea", "subcategory": "Tea",
        "food_group": "Beverages", "contains": ["caffeine"],
        "group_weights": [0, 1, 0],
        "examples": ["English breakfast", "Assam", "iced tea base"],
        "calories": 1, "carbs": 0.3, "protein": 0, "fiber": 0,
        "fat": 0, "sodium": 3, "sugar": 0, "saturated_fat": 0,
        "notes": "Plain brewed, no milk or sugar. ~20-40mg caffeine per 100g."
    },

    # ---------------- Soft drinks (Beverages food_group) ----------------------------
    {
        "id": "cola", "name": "Cola",
        "category": "Soft drinks", "subcategory": "Soft drinks",
        "food_group": "Beverages", "contains": ["caffeine"],
        "group_weights": [0, 1, 0],
        "examples": ["with pizza", "rum & coke base", "kids' party"],
        "calories": 42, "carbs": 10.6, "protein": 0.1, "fiber": 0,
        "fat": 0, "sodium": 4, "sugar": 8.7, "saturated_fat": 0,
        "notes": "Standard sugar-sweetened cola (Coke/Pepsi). ~10mg caffeine per 100g."
    },
    {
        "id": "ginger-ale", "name": "Ginger ale",
        "category": "Soft drinks", "subcategory": "Soft drinks",
        "food_group": "Beverages", "contains": [],
        "group_weights": [0, 1, 0],
        "examples": ["upset stomach remedy", "cocktail mixer", "kids' soda"],
        "calories": 34, "carbs": 8.8, "protein": 0, "fiber": 0,
        "fat": 0, "sodium": 7, "sugar": 8.6, "saturated_fat": 0,
        "notes": "Sugar-sweetened (Canada Dry-style). Caffeine-free."
    },

    # ---------------- Juices (Beverages food_group) ---------------------------------
    {
        "id": "orange-juice", "name": "Orange juice",
        "category": "Juices", "subcategory": "Fruit juices",
        "food_group": "Beverages", "contains": [],
        "group_weights": [0, 1, 0],
        "examples": ["breakfast", "mimosa", "marinade"],
        "calories": 45, "carbs": 10.4, "protein": 0.7, "fiber": 0.2,
        "fat": 0.2, "sodium": 1, "sugar": 8.4, "saturated_fat": 0,
        "notes": "Fresh-squeezed, unsweetened. Carton varieties similar; calcium-fortified ones add minerals not nutrients tracked here."
    },
    {
        "id": "apple-juice", "name": "Apple juice",
        "category": "Juices", "subcategory": "Fruit juices",
        "food_group": "Beverages", "contains": [],
        "group_weights": [0, 1, 0],
        "examples": ["kids' juice box", "marinade", "winter cider base"],
        "calories": 46, "carbs": 11.3, "protein": 0.1, "fiber": 0.2,
        "fat": 0.1, "sodium": 4, "sugar": 9.6, "saturated_fat": 0,
        "notes": "Clear filtered juice. Cloudy/unfiltered has more fiber."
    },

    # ---------------- Jams & preserves (Sweets food_group) --------------------------
    {
        "id": "apple-butter", "name": "Apple butter",
        "category": "Jams & preserves", "subcategory": "Sweet spreads",
        "food_group": "Sweets", "contains": [],
        "group_weights": [0, 1, 0], "form": "paste",
        "examples": ["toast spread", "biscuit topping", "pork tenderloin glaze"],
        "calories": 173, "carbs": 43, "protein": 0.4, "fiber": 1.8,
        "fat": 0.4, "sodium": 8, "sugar": 34, "saturated_fat": 0.05,
        "notes": "Slow-cooked spiced apple paste. No actual butter — named for its consistency."
    },
]


def apply():
    with ING_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    by_id = {ing["id"]: ing for ing in data}

    moves_applied = 0
    moves_skipped = 0
    for mid, (cat, sub, fg) in MOVES.items():
        if mid not in by_id:
            print(f"  ! move skipped — {mid} not in dataset", file=sys.stderr)
            moves_skipped += 1
            continue
        ing = by_id[mid]
        before = (ing["category"], ing["subcategory"], ing["food_group"])
        ing["category"] = cat
        ing["subcategory"] = sub
        if fg is not None:
            ing["food_group"] = fg
        after = (ing["category"], ing["subcategory"], ing["food_group"])
        if before == after:
            moves_skipped += 1
        else:
            moves_applied += 1
            print(f"  moved {mid}: {before} -> {after}")

    new_appended = 0
    new_skipped = 0
    for entry in NEW:
        if entry["id"] in by_id:
            print(f"  ! new skipped — {entry['id']} already exists", file=sys.stderr)
            new_skipped += 1
            continue
        data.append(entry)
        new_appended += 1

    print(f"\nSummary: {moves_applied} moves applied, {moves_skipped} moves skipped, "
          f"{new_appended} new entries appended, {new_skipped} new entries skipped.")

    # Write back with the same one-line-per-entry format used throughout the file.
    write_compact(data, ING_PATH)
    print(f"Wrote {len(data)} entries to {ING_PATH}.")


def write_compact(data, path: Path) -> None:
    """Preserve the existing one-entry-per-line layout that the file uses."""
    lines = ["["]
    for i, ing in enumerate(data):
        sep = "," if i < len(data) - 1 else ""
        lines.append("  " + json.dumps(ing, ensure_ascii=False, separators=(", ", ": ")) + sep)
    lines.append("]")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    apply()
