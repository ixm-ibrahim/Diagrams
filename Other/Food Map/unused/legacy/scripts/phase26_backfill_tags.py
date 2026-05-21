"""Phase 26: backfill cross-category `tags` on every ingredient.

Vocabulary (mirrors TAGS in src/data/schema.js):
  Auto-computed:  high-protein, high-fiber, low-cal, high-sodium
  Identity:       breakfast, snack, dessert, condiment, garnish,
                  fermented, cured, smoked, omega3-rich, iron-rich

Idempotent: re-running produces the same result.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ING_PATH = ROOT / "src" / "data" / "ingredients.json"

VALID_TAGS = {
    "high-protein", "high-fiber", "low-cal", "high-sodium",
    "breakfast", "snack", "dessert", "condiment", "garnish",
    "fermented", "cured", "smoked", "omega3-rich", "iron-rich",
}


# ---------------------------------------------------------------------------
# Keyword sets for identity tags. Matched against ingredient name + category +
# subcategory + notes (all lowercased + joined). Token-boundary matching to
# avoid partial-word false positives.
# ---------------------------------------------------------------------------

def kw(*words):
    """Compile a single regex matching any of the words at token boundaries."""
    pat = r"\b(" + "|".join(re.escape(w) for w in words) + r")\b"
    return re.compile(pat, re.IGNORECASE)


BREAKFAST_KW = kw(
    "yogurt", "kefir", "oatmeal", "granola", "cereal", "bagel", "croissant",
    "muffin", "scone", "pancake", "waffle", "toast", "english muffin",
    "coffee", "tea", "espresso", "latte", "cappuccino", "mocha",
    "bacon", "sausage", "breakfast", "egg", "marmalade", "jam", "jelly",
    "preserves", "apple butter", "biscuit", "porridge", "milk",
)
SNACK_KW = kw(
    "chip", "chips", "cracker", "crackers", "pretzel", "popcorn", "jerky",
    "trail mix", "nut mix", "dried fruit", "raisin", "gummy", "gummies",
    "lollipop", "candy", "snack",
)
DESSERT_KW = kw(
    "cake", "ice cream", "pie", "pudding", "pastry", "pastries", "halva",
    "baklava", "gulab jamun", "mochi", "churro", "creme brulee",
    "tiramisu", "cheesecake", "tres leches", "shortbread", "biscotti",
    "amaretti", "nougat", "fudge", "toffee", "caramel", "marshmallow",
    "frosting", "icing", "sweet roll", "danish",
)
GARNISH_KW = kw(
    "parsley", "cilantro", "chive", "basil", "mint", "dill", "tarragon",
    "chervil", "lemon balm", "fresh herb", "edible flower", "microgreen",
    "sprout", "garnish", "zest", "rose petal",
)
FERMENTED_KW = kw(
    "yogurt", "kefir", "kimchi", "sauerkraut", "miso", "natto", "tempeh",
    "kombucha", "sourdough", "vinegar", "fish sauce", "soy sauce",
    "fermented", "doenjang", "gochujang", "doubanjiang", "shaoxing",
    "mirin", "sake", "lassi", "ayran", "doogh", "skyr", "fromage blanc",
    "labneh", "douchi", "iru", "buttermilk", "ssamjang", "anchovy paste",
    "garum",
)
CURED_KW = kw(
    "bacon", "ham", "prosciutto", "pancetta", "salami", "pepperoni",
    "capicola", "soppressata", "bresaola", "guanciale", "lardons",
    "jerky", "biltong", "pastrami", "corned beef", "salt cod",
    "anchov",  # anchovies, anchovy
    "gravlax", "lox", "kippered", "sucuk",
    "'nduja", "braunschweiger", "summer sausage", "head cheese",
    "mortadella", "smoked",
)
SMOKED_KW = kw(
    "smoked", "lox", "kippered", "liquid smoke", "smoke ", "smoke-",
)
OMEGA3_KW = kw(
    "salmon", "mackerel", "sardine", "sardines", "anchovy", "anchovies",
    "herring", "trout", "kipper",
    "chia", "flax", "flaxseed", "hemp seed", "walnut", "sacha inchi",
)
IRON_KW = kw(
    "liver", "heart", "kidney", "spleen", "blood sausage",
    "spinach", "swiss chard", "kale", "collard", "lentil",
    "molasses", "fortified",
)


def text_blob(ing: dict) -> str:
    parts = [
        ing.get("name", ""),
        ing.get("category", ""),
        ing.get("subcategory", ""),
        ing.get("food_group", ""),
        " ".join(ing.get("examples", [])),
        ing.get("notes", ""),
    ]
    return " ".join(parts)


def compute_tags(ing: dict) -> list[str]:
    tags: set[str] = set()

    # --- Auto-computed from per-100g nutrient values ---
    protein = ing.get("protein", 0) or 0
    calories = ing.get("calories", 0) or 0
    # high-protein: protein supplies >= 40% of calories AND >= 5g protein
    # (catches egg white at 10.9g protein / 52 kcal). Also a 20g/100g
    # absolute threshold for very dense items that fall below the ratio
    # because they pack lots of carbs/fat too.
    protein_share = (protein * 4) / calories if calories > 0 else 0
    if protein >= 20 or (protein >= 5 and protein_share >= 0.4):
        tags.add("high-protein")
    if (ing.get("fiber", 0) or 0) >= 6:
        tags.add("high-fiber")
    if calories < 100:
        tags.add("low-cal")
    if (ing.get("sodium", 0) or 0) >= 600:
        tags.add("high-sodium")

    blob = text_blob(ing)
    fg = ing.get("food_group", "")
    cat = ing.get("category", "")
    name = ing.get("name", "").lower()

    # --- condiment: entire Condiments & sauces food_group (except pickled-
    # vegetables which are more "vegetable than condiment"). Plus mustards,
    # vinegars, dressings, hot sauces wherever they sit. ---
    if fg == "Condiments & sauces" and cat != "Pickled vegetables":
        tags.add("condiment")

    # --- garnish: fresh herbs (Herbs & spices / Fresh herbs) + edible
    # flowers / zest / microgreens. Not all sprouts (some are full
    # vegetables in salads). ---
    if cat == "Fresh herbs":
        tags.add("garnish")
    if GARNISH_KW.search(blob) and ("herb" in cat.lower() or "sprout" in name or "zest" in name):
        tags.add("garnish")

    # --- fermented ---
    if FERMENTED_KW.search(blob):
        # Avoid false positives: "fish sauce" matches but is in condiments;
        # legitimate. Vinegar matches because most vinegars are fermented.
        tags.add("fermented")

    # --- cured ---
    if CURED_KW.search(blob):
        tags.add("cured")
    if ing.get("form") == "cured":
        tags.add("cured")
    # Cured pork / sausage subcategories always cured
    if "Cured" in ing.get("subcategory", "") or "Cured" in cat:
        tags.add("cured")

    # --- smoked ---
    if SMOKED_KW.search(blob) or ing.get("subcategory") == "Smoked fish":
        tags.add("smoked")

    # --- omega3-rich ---
    if OMEGA3_KW.search(blob):
        # Oily fish category should add the tag unconditionally
        tags.add("omega3-rich")
    if cat == "Oily fish":
        tags.add("omega3-rich")

    # --- iron-rich ---
    if IRON_KW.search(blob):
        tags.add("iron-rich")
    if cat == "Organ meats":
        tags.add("iron-rich")
    # Red meat is iron-source by mass
    if cat == "Red meat":
        tags.add("iron-rich")

    # --- breakfast ---
    if BREAKFAST_KW.search(blob):
        tags.add("breakfast")
        # Carefully exclude things that match keywords but aren't breakfast:
        # "bacon fat" (rendered) — still breakfast-adjacent, leave it.
        # "milk chocolate" — kw=milk would match. Filter out:
        if "chocolate" in name and ing["food_group"] == "Sweets":
            tags.discard("breakfast")

    # --- snack ---
    if SNACK_KW.search(blob):
        tags.add("snack")
    # Dried fruits + raw nuts are snack-eligible too
    if cat == "Dried fruits":
        tags.add("snack")
    if cat == "Nuts" and "butter" not in name.lower():
        tags.add("snack")

    # --- dessert ---
    if DESSERT_KW.search(blob):
        tags.add("dessert")
    if fg == "Sweets" and cat in ("Candy & desserts",):
        tags.add("dessert")
    # Prepared mixes (cake/cookie/pudding/pie) are dessert too
    if cat == "Prepared mixes" and ing.get("subcategory") in (
        "Cake mixes", "Cookie mixes", "Pie fillings", "Puddings",
        "Whipped toppings", "Gelatins",
    ):
        tags.add("dessert")

    return sorted(tags)


def main() -> int:
    with ING_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    changes = 0
    for ing in data:
        new_tags = compute_tags(ing)
        # Validate against vocabulary
        for t in new_tags:
            if t not in VALID_TAGS:
                print(f"ERROR: unknown tag {t!r} computed for {ing['id']}",
                      file=sys.stderr)
                return 1
        if ing.get("tags") != new_tags:
            ing["tags"] = new_tags
            changes += 1

    print(f"Tags rebuilt on {changes} of {len(data)} ingredients.")
    print()

    # Distribution
    from collections import Counter
    tag_counts = Counter()
    no_tags = 0
    for ing in data:
        tg = ing.get("tags") or []
        if not tg:
            no_tags += 1
        for t in tg:
            tag_counts[t] += 1
    print("--- Tag distribution ---")
    for t in sorted(VALID_TAGS):
        print(f"  {t:14s} {tag_counts.get(t, 0)}")
    print(f"  (untagged: {no_tags})")

    write_compact(data, ING_PATH)
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
