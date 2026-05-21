"""Phase 25: subcategory refinement & category splits.

Refactors `category` and `subcategory` fields on existing ingredients
(no new entries) to satisfy:
  - no category has >50 ingredients
  - every category has >=2 subcategories (no singletons)
  - plural/singular subcategory typos consolidated

Steps:
  1. Subcategory plural/singular dedup (Allium -> Alliums, Mushroom -> Mushrooms,
     Tomato -> Tomatoes, Stone fruit -> Stone fruits, Melon -> Melons,
     Pseudocereal -> Pseudocereals, Potato -> Potatoes, Lentil -> Lentils).
  2. Split 6 oversized categories into balanced peer categories.
  3. Move singleton Protein (plant) / Flours entry into Legumes / Chickpea.

Idempotent; safe to re-run.
"""
from __future__ import annotations

import json, sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
ING_PATH = ROOT / "src" / "data" / "ingredients.json"


# ---------------------------------------------------------------------------
# Pass 1 — Subcategory plural/singular canonicalization
# Map applied wherever the subcategory matches, regardless of food_group/category.
# ---------------------------------------------------------------------------
SUBCATEGORY_RENAMES = {
    "Allium": "Alliums",
    "Mushroom": "Mushrooms",
    "Tomato": "Tomatoes",
    "Stone fruit": "Stone fruits",
    "Melon": "Melons",
    "Pseudocereal": "Pseudocereals",
    "Potato": "Potatoes",
    "Lentil": "Lentils",
}


# ---------------------------------------------------------------------------
# Pass 2 — Category splits
# For each oversized category, map (current_category, subcategory) -> new_category.
# subcategory stays unchanged (it's already the natural grouping).
# Specified by (food_group, current_category, subcategory_set) -> new_category.
# ---------------------------------------------------------------------------

# Condiments & sauces (131) -> 3 categories
CONDIMENTS_SPLIT = {
    # Sauces (~45 entries)
    "Sauces": {
        "Asian sauces", "Hot sauces", "Mixed condiments", "Mustards",
        "Tomato condiments",
    },
    # Pastes & ferments (~38 entries)
    "Pastes & ferments": {
        "Curry pastes", "Indian curry pastes",
        "Chinese pantry", "Japanese pantry", "Korean pantry",
        "Thai pantry", "Vietnamese pantry", "Southeast Asian pantry",
        "Mexican pastes", "Latin American pastes",
        "Fermented pastes", "Chili pastes", "Chutneys",
    },
    # Dressings & dips (~48 entries)
    "Dressings & dips": {
        "Salad dressings", "Emulsions", "Dairy sauces", "Herb sauces",
        "Avocado", "Spreads", "Pickled", "Vinegars", "Syrups",
    },
}

# Fruits (74) -> 3 categories
FRUITS_SPLIT = {
    "Tropical fruits": {"Tropical"},
    "Citrus": {"Citrus"},
    "Temperate fruits": {
        "Apple", "Pear", "Stone fruits", "Grape", "Melons",
        "Other fruits", "Banana", "Avocado",
    },
}

# Grains / Bread & baked goods (65) -> 2 categories
BAKED_SPLIT = {
    "Bread & rolls": {
        "Bread", "Rolls", "Flatbread", "Bread crumbs", "Cornbread",
        "Tortillas", "Pizza dough", "Croutons", "Wrappers",
    },
    "Baked snacks & pastries": {
        "Cookies", "Crackers", "Pastries", "Biscuits", "Graham crackers",
        "Muffins", "Pretzels",
    },
}

# Herbs & spices / Dried spices (64) -> 3 categories
SPICES_SPLIT = {
    "Whole spices": {"Whole spices", "Seed spices", "Pods"},
    "Ground spices": {"Ground spices", "Peppers", "Chili powders"},
    "Dried herbs": {"Dried herbs"},
}

# Sweets / Sweets (68) -> 2 categories
SWEETS_SPLIT = {
    "Sugar & sweeteners": {"Sugar", "Sweeteners", "Sugar substitutes",
                            "Syrup", "Honey"},
    "Candy & desserts": {"Confectionery", "Chocolate", "Pastries"},
}

# Vegetables / Non-starchy vegetables (79) -> 3 categories
# NB: applies AFTER Pass 1 renames (Allium -> Alliums, Mushroom -> Mushrooms,
# Tomato -> Tomatoes).
VEG_SPLIT = {
    "Mushrooms": {"Mushrooms"},
    "Peppers & nightshades": {
        "Chili peppers", "Bell pepper", "Tomatoes", "Tomato products",
        "Eggplant",
    },
    "Other non-starchy": {
        "Alliums", "Sea vegetables", "Summer squash", "Pods",
        "Root vegetables", "Aromatics", "Gourds", "Aquatic",
        "Cucumber", "Asparagus", "Green beans", "Celery", "Bulbs",
        "Flower vegetables", "Sprouts", "Shoots", "Other",
        "Fermented vegetables",
    },
}


def reverse_split(split: dict[str, set[str]]) -> dict[str, str]:
    """{old_sub -> new_cat} for fast lookup."""
    out = {}
    for new_cat, subs in split.items():
        for sub in subs:
            out[sub] = new_cat
    return out


SPLIT_RULES = [
    # (food_group, current_category, subcategory -> new_category)
    ("Condiments & sauces", "Condiments & sauces", reverse_split(CONDIMENTS_SPLIT)),
    ("Fruits", "Fruits", reverse_split(FRUITS_SPLIT)),
    ("Grains", "Bread & baked goods", reverse_split(BAKED_SPLIT)),
    ("Herbs & spices", "Dried spices", reverse_split(SPICES_SPLIT)),
    ("Sweets", "Sweets", reverse_split(SWEETS_SPLIT)),
    ("Vegetables", "Non-starchy vegetables", reverse_split(VEG_SPLIT)),
]


def main() -> int:
    with ING_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    starting_count = len(data)

    # --- Pass 1: subcategory plural/singular dedup ---
    sub_renames = 0
    for ing in data:
        new = SUBCATEGORY_RENAMES.get(ing["subcategory"])
        if new and new != ing["subcategory"]:
            ing["subcategory"] = new
            sub_renames += 1
    print(f"Pass 1: subcategory renames applied: {sub_renames}")

    # --- Pass 2: category splits ---
    cat_changes = 0
    for fg, cat, sub_map in SPLIT_RULES:
        for ing in data:
            if ing["food_group"] != fg or ing["category"] != cat:
                continue
            new_cat = sub_map.get(ing["subcategory"])
            if new_cat is None:
                print(f"  WARN: no rule for {fg} / {cat} / {ing['subcategory']} "
                      f"(id={ing['id']}); leaving unchanged", file=sys.stderr)
                continue
            ing["category"] = new_cat
            cat_changes += 1
    print(f"Pass 2: category reassignments: {cat_changes}")

    # --- Pass 3: move singleton chickpea-flour-besan ---
    singleton_moves = 0
    for ing in data:
        if ing["id"] == "chickpea-flour-besan":
            if ing["category"] == "Flours":
                ing["category"] = "Legumes"
                ing["subcategory"] = "Chickpea"
                singleton_moves += 1
            break
    print(f"Pass 3: singleton moves: {singleton_moves}")

    # --- Pass 4: split categories with only one subcategory into >=2 ---
    sub_resplits = 0
    for ing in data:
        fg = ing["food_group"]; cat = ing["category"]; sub = ing["subcategory"]; iid = ing["id"]

        # Vegetables / Mushrooms — Cultivated vs Wild
        if fg == "Vegetables" and cat == "Mushrooms":
            wild = {"chanterelle", "morel", "porcini", "wood ear",
                    "lions-mane", "maitake", "nameko", "truffle",
                    "mushroom-chanterelle"}
            new_sub = "Wild mushrooms" if any(w in iid for w in wild) \
                      else "Cultivated mushrooms"
            if new_sub != sub:
                ing["subcategory"] = new_sub; sub_resplits += 1

        # Fruits / Citrus — Sweet citrus vs Sour citrus
        elif fg == "Fruits" and cat == "Citrus":
            sour = {"lemon", "lime", "grapefruit", "yuzu", "kumquat",
                    "calamansi", "finger-lime", "key-lime", "meyer-lemon",
                    "pomelo"}
            new_sub = "Sour citrus" if any(s in iid for s in sour) \
                      else "Sweet citrus"
            if new_sub != sub:
                ing["subcategory"] = new_sub; sub_resplits += 1

        # Fruits / Tropical fruits — Major tropical vs Other tropical
        elif fg == "Fruits" and cat == "Tropical fruits":
            major = {"mango", "pineapple", "papaya", "banana", "kiwi",
                     "guava", "passion-fruit", "coconut"}
            new_sub = "Major tropical" if any(m in iid for m in major) \
                      else "Other tropical"
            if new_sub != sub:
                ing["subcategory"] = new_sub; sub_resplits += 1

        # Dairy / Plant milks — Nut/seed plant milks vs Grain/legume plant milks
        elif fg == "Dairy" and cat == "Plant milks":
            nut_seed = {"almond", "cashew", "coconut", "hazelnut", "hemp"}
            new_sub = "Nut & seed plant milks" if any(n in iid for n in nut_seed) \
                      else "Grain & legume plant milks"
            if new_sub != sub:
                ing["subcategory"] = new_sub; sub_resplits += 1

        # Beverages / Prepared soups & broths — Broths & stocks vs Prepared soups
        elif fg == "Beverages" and cat == "Prepared soups & broths":
            stocks = {"broth", "bouillon", "dashi", "stock"}
            new_sub = "Broths & stocks" if any(s in iid for s in stocks) \
                      else "Prepared soups"
            if new_sub != sub:
                ing["subcategory"] = new_sub; sub_resplits += 1

        # Herbs & spices / Dried herbs — split by leaf-type intuition
        elif fg == "Herbs & spices" and cat == "Dried herbs":
            mediterranean = {"oregano", "thyme", "rosemary", "sage",
                             "marjoram", "basil", "bay", "tarragon",
                             "summer-savory", "fines-herbes"}
            new_sub = "Mediterranean dried herbs" \
                      if any(m in iid for m in mediterranean) \
                      else "Other dried herbs"
            if new_sub != sub:
                ing["subcategory"] = new_sub; sub_resplits += 1

        # Protein (animal) / Freshwater fish — Bass & perch vs Other freshwater
        elif fg == "Protein (animal)" and cat == "Freshwater fish":
            bass = {"perch", "bass"}
            new_sub = "Bass & perch" if any(b in iid for b in bass) \
                      else "Other freshwater fish"
            if new_sub != sub:
                ing["subcategory"] = new_sub; sub_resplits += 1

    print(f"Pass 4: subcategory re-splits: {sub_resplits}")

    # --- Pass 5: split Protein (plant) / Legumes into 3 categories so
    # Protein (plant) food_group has >=2 categories. ---
    pp_changes = 0
    SOY_SUBS = {"Soy"}
    MEAT_ALT_SUBS = {"Plant protein", "Wheat protein"}
    for ing in data:
        if ing["food_group"] != "Protein (plant)" or ing["category"] != "Legumes":
            continue
        if ing["subcategory"] in SOY_SUBS:
            ing["category"] = "Soy products"
            pp_changes += 1
        elif ing["subcategory"] in MEAT_ALT_SUBS:
            ing["category"] = "Meat alternatives"
            pp_changes += 1
    print(f"Pass 5: Protein (plant) category splits: {pp_changes}")

    # --- Pass 6: split Protein (plant) / Soy products into 2 subcategories ---
    sp_changes = 0
    TOFU_IDS = {"tofu-firm", "tofu-silken", "yuba-tofu-skin", "aburaage",
                "smoked-tofu"}
    for ing in data:
        if ing["food_group"] != "Protein (plant)" or ing["category"] != "Soy products":
            continue
        new_sub = "Tofu & tofu products" if ing["id"] in TOFU_IDS \
                  else "Whole & fermented soy"
        if new_sub != ing["subcategory"]:
            ing["subcategory"] = new_sub
            sp_changes += 1
    print(f"Pass 6: Soy products subcategory splits: {sp_changes}")

    # --- Pass 7: split Meat alternatives into 2 subcategories ---
    ma_changes = 0
    WHEAT_IDS = {"seitan", "vital-wheat-gluten"}
    for ing in data:
        if ing["food_group"] != "Protein (plant)" or ing["category"] != "Meat alternatives":
            continue
        new_sub = "Wheat-based meat alternatives" if ing["id"] in WHEAT_IDS \
                  else "Other meat alternatives"
        if new_sub != ing["subcategory"]:
            ing["subcategory"] = new_sub
            ma_changes += 1
    print(f"Pass 7: Meat alternatives subcategory splits: {ma_changes}")

    assert len(data) == starting_count, "ingredient count must not change"

    print()
    # --- Post-summary: per-category counts ---
    cat_counts = Counter((ing["food_group"], ing["category"]) for ing in data)
    over = [(k, c) for k, c in cat_counts.items() if c > 50]
    if over:
        print("STILL OVERSIZED:")
        for k, c in over:
            print(f"  {k}: {c}")
    else:
        print("All categories now <= 50 entries.")
    print()

    sub_counts = Counter((ing["food_group"], ing["category"], ing["subcategory"])
                         for ing in data)
    subs_per_cat = Counter()
    for (fg, cat, _sub) in sub_counts:
        subs_per_cat[(fg, cat)] += 1
    singleton_cats = [k for k, n in subs_per_cat.items() if n < 2]
    if singleton_cats:
        print("CATEGORIES WITH <2 SUBCATEGORIES:")
        for k in singleton_cats:
            print(f"  {k}")
    else:
        print("Every category has >=2 subcategories.")
    print()

    print(f"Total ingredients: {len(data)} (unchanged)")

    write_compact(data, ING_PATH)
    print(f"Wrote {ING_PATH}")
    return 0


def write_compact(data, path: Path) -> None:
    lines = ["["]
    for i, ing in enumerate(data):
        sep = "," if i < len(data) - 1 else ""
        lines.append("  " + json.dumps(ing, ensure_ascii=False, separators=(", ", ": ")) + sep)
    lines.append("]")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
