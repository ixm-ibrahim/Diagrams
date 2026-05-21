#!/usr/bin/env python3
"""Second-pass strip of "Sugar & sweeteners" from compositional-meal
names that should never contain added sugar.

The previous pass used exact lowercase matching but missed entries
whose names contain accented characters (béchamel, sautéed, etc.).
This pass uses Unicode NFKD-folding before matching so 'béchamel' and
'bechamel' both hit the same key.
"""
from __future__ import annotations

import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMP = ROOT / "src" / "data" / "compositional-meals.json"


def fold(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s.lower())
        if not unicodedata.combining(c)
    )


# A meal whose name contains any of these substrings (folded) should
# have "Sugar & sweeteners" stripped from its categories.
NO_SUGAR_SUBSTRINGS = {
    "bechamel",       # white sauce, never sweetened
    "compound butter",
    "brown butter",
    "buttered apples",  # cooked savory side
    "buttered pears",
    "sauteed pear",
    "buttered peach",
    "ricotta with fruit",      # plain ricotta + fruit
    "cottage cheese & peach",
    "fruit & nut",            # fruit and nuts plate, no added sugar
    "fruit and nut",
    "trail mix",
    "mixed nut",
    "roasted nut",
    "mixed berries",
    "strawberry bowl",
    "sliced apples",
    "fresh fruit plate",
    "yogurt bowl",
    "cheese plate",
    "sliced cheddar",
    "ricotta plate",
    "cottage cheese bowl",
    "fresh mozzarella",
    "tossed salad",
    "garden salad",
    "green salad",
    "sauteed greens",
    "roasted vegetables",
    "sauteed vegetables",
    "steamed vegetable",
    "buttered vegetables",
    "buttered nuts",
    "buttered eggs",
    "scrambled eggs",
    "fried eggs",
    "hard-boiled eggs",
    "omelet",
    "roux",
    "pie dough",
    "shortcrust pastry",
    "pasta dough",
    "egg noodles",
    "white rice",
    "brown rice",
    "buttered pasta",
    "buttered rice",
    "buttered brown rice",
    "butter-finished oatmeal",
    "sliced bread",
    "dinner rolls",
    "toast",
    "buttered bread",
    "garlic bread",
    "roast chicken",
    "grilled chicken",
    "roast turkey",
    "roast beef",
    "grilled steak",
    "ground beef skillet",
    "bacon",
    "ham slices",
    "breakfast sausage",
    "steamed shrimp",
    "boiled crab",
    "pan-seared liver",
    "chopped liver",
    "kefir",
    "roasted broccoli",
    "sauteed cabbage",
    "almond milk glass",
    "glass of milk",
    "warm milk",
    "glass of wine",
    "beer",
    "glass of juice",
    "coffee",
    "hot tea",
    "milk tea",
    "creamy latte",
    "cafe au lait",
    "cream sauce",
}


def main():
    c = json.loads(COMP.read_text(encoding="utf-8"))
    changed = 0
    for m in c:
        cats = m.get("ingredient_categories") or []
        if "Sugar & sweeteners" not in cats:
            continue
        folded = fold(m["name"])
        if any(s in folded for s in NO_SUGAR_SUBSTRINGS):
            m["ingredient_categories"] = [x for x in cats if x != "Sugar & sweeteners"]
            changed += 1
    print(f"Stripped sugar from {changed} compositional meals")
    COMP.write_text(json.dumps(c, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


if __name__ == "__main__":
    main()
