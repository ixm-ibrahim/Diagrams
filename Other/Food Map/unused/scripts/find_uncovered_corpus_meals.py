#!/usr/bin/env python3
"""Find canonical corpus dish titles that the project's meal datasets
don't already cover, infer their ingredient_categories from the recipes'
NER ingredient lists, and write them out as a new meals file.

Inputs:
  - docs/corpus-titles.tsv               (count + sample NER per canonical title)
  - src/data/meals.json                  (curated meals)
  - src/data/compositional-meals.json    (corpus-shape compositional patterns)
  - src/data/ingredients.json            (ingredient name -> category lookup)

Outputs:
  - src/data/corpus-titled-meals.json    (the new dataset)
  - docs/corpus-titled-meals-report.txt  (audit: kept / skipped / why)

Filtering:
  - Only titles appearing in >= MIN_FREQ recipes (real dishes, not one-offs)
  - Skip titles already present (normalized) in meals.json or compositional-meals.json
  - Skip "title" entries that aren't dishes (cookbook section names, "see note", etc.)
  - Skip titles where we couldn't infer at least one meaningful category
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TSV = ROOT / "docs" / "corpus-titles.tsv"
CURATED = ROOT / "src" / "data" / "meals.json"
COMPOSITIONAL = ROOT / "src" / "data" / "compositional-meals.json"
INGREDIENTS = ROOT / "src" / "data" / "ingredients.json"
OUT_DATA = ROOT / "src" / "data" / "corpus-titled-meals.json"
OUT_REPORT = ROOT / "docs" / "corpus-titled-meals-report.txt"

MIN_FREQ = 50  # only titles with at least this many corpus occurrences

# Non-dish noise titles that show up frequently in old cookbooks. Skip outright.
NON_DISH_TITLES = {
    "cook the book", "see note", "see directions", "no name",
    "untitled", "main dish", "side dish", "dessert", "appetizer",
    "salad", "soup", "casserole",          # too generic on their own
    "bread", "cake", "cookies", "pie",     # too generic
}

# Hand-tuned synonym map: NER token / keyword → project category.
# Extends what we can derive from ingredients.json. Keys are matched as
# whole words against tokenized NER strings, longest-first to prefer
# multi-word matches ("brown sugar" before "sugar").
KEYWORD_TO_CATEGORY: dict[str, str] = {
    # --- proteins ---
    "chicken": "Poultry", "turkey": "Poultry", "duck": "Poultry", "hen": "Poultry",
    "beef": "Red meat", "steak": "Red meat", "ground beef": "Red meat",
    "hamburger": "Red meat", "veal": "Red meat", "venison": "Red meat",
    "pork": "Red meat", "lamb": "Red meat", "mutton": "Red meat",
    "bacon": "Processed meat", "ham": "Processed meat", "prosciutto": "Processed meat",
    "sausage": "Processed meat", "pepperoni": "Processed meat", "salami": "Processed meat",
    "hot dog": "Processed meat", "hot dogs": "Processed meat", "frank": "Processed meat",
    "spam": "Processed meat", "chorizo": "Processed meat",
    "liver": "Organ meats", "kidney": "Organ meats", "heart": "Organ meats",
    "tongue": "Organ meats", "tripe": "Organ meats", "sweetbreads": "Organ meats",
    "shrimp": "Shellfish", "prawn": "Shellfish", "lobster": "Shellfish",
    "crab": "Shellfish", "clam": "Shellfish", "mussel": "Shellfish",
    "oyster": "Shellfish", "scallop": "Shellfish", "crawfish": "Shellfish",
    "salmon": "Oily fish", "tuna": "Oily fish", "mackerel": "Oily fish",
    "sardine": "Oily fish", "anchovy": "Oily fish", "anchovies": "Oily fish",
    "trout": "Oily fish", "herring": "Oily fish",
    "cod": "White fish", "haddock": "White fish", "tilapia": "White fish",
    "halibut": "White fish", "sole": "White fish", "flounder": "White fish",
    "fish": "White fish",  # generic fallback for "fish"
    "egg": "Eggs", "eggs": "Eggs", "yolk": "Eggs", "yolks": "Eggs",
    "egg white": "Eggs", "egg whites": "Eggs",
    # --- dairy ---
    "milk": "Milk", "buttermilk": "Milk", "whole milk": "Milk", "skim milk": "Milk",
    "butter": "Cream & butter", "cream": "Cream & butter", "heavy cream": "Cream & butter",
    "whipping cream": "Cream & butter", "sour cream": "Cream & butter",
    "half and half": "Cream & butter", "half-and-half": "Cream & butter",
    "yogurt": "Fermented dairy", "yoghurt": "Fermented dairy", "kefir": "Fermented dairy",
    "cottage cheese": "Fresh cheese", "ricotta": "Fresh cheese", "feta": "Fresh cheese",
    "mozzarella": "Fresh cheese", "fresh mozzarella": "Fresh cheese",
    "queso fresco": "Fresh cheese", "mascarpone": "Fresh cheese",
    "cream cheese": "Fresh cheese", "philadelphia": "Fresh cheese",
    "cheddar": "Aged cheese", "parmesan": "Aged cheese", "parmigiano": "Aged cheese",
    "swiss cheese": "Aged cheese", "gouda": "Aged cheese", "gruyere": "Aged cheese",
    "blue cheese": "Aged cheese", "brie": "Aged cheese", "asiago": "Aged cheese",
    "monterey jack": "Aged cheese", "pepper jack": "Aged cheese", "provolone": "Aged cheese",
    "romano": "Aged cheese", "manchego": "Aged cheese",
    "cheese": "Aged cheese",  # generic fallback when no qualifier
    "velveeta": "Processed cheese", "american cheese": "Processed cheese",
    "cheez whiz": "Processed cheese", "cheez-whiz": "Processed cheese",
    "process cheese": "Processed cheese", "processed cheese": "Processed cheese",
    # --- vegetables ---
    "onion": "Other vegetables", "onions": "Other vegetables",
    "garlic": "Other vegetables",
    "tomato": "Other vegetables", "tomatoes": "Other vegetables",
    "pepper": "Other vegetables", "peppers": "Other vegetables", "bell pepper": "Other vegetables",
    "celery": "Other vegetables", "carrot": "Other vegetables", "carrots": "Other vegetables",
    "zucchini": "Other vegetables", "cucumber": "Other vegetables",
    "mushroom": "Other vegetables", "mushrooms": "Other vegetables",
    "eggplant": "Other vegetables", "okra": "Other vegetables", "squash": "Other vegetables",
    "leek": "Other vegetables", "leeks": "Other vegetables", "scallion": "Other vegetables",
    "scallions": "Other vegetables", "green onion": "Other vegetables", "green onions": "Other vegetables",
    "shallot": "Other vegetables", "shallots": "Other vegetables", "asparagus": "Other vegetables",
    "artichoke": "Other vegetables", "artichokes": "Other vegetables",
    "potato": "Starchy vegetables", "potatoes": "Starchy vegetables",
    "sweet potato": "Starchy vegetables", "sweet potatoes": "Starchy vegetables",
    "yam": "Starchy vegetables", "yams": "Starchy vegetables", "corn": "Starchy vegetables",
    "tater": "Starchy vegetables", "hash brown": "Starchy vegetables",
    "hash browns": "Starchy vegetables", "tater tot": "Starchy vegetables",
    "tater tots": "Starchy vegetables",
    "broccoli": "Cruciferous vegetables", "cauliflower": "Cruciferous vegetables",
    "cabbage": "Cruciferous vegetables", "brussels sprout": "Cruciferous vegetables",
    "brussels sprouts": "Cruciferous vegetables", "bok choy": "Cruciferous vegetables",
    "kale": "Leafy greens", "spinach": "Leafy greens", "lettuce": "Leafy greens",
    "arugula": "Leafy greens", "chard": "Leafy greens", "collard": "Leafy greens",
    "collards": "Leafy greens", "greens": "Leafy greens", "endive": "Leafy greens",
    "pickle": "Pickled vegetables", "pickles": "Pickled vegetables",
    "sauerkraut": "Pickled vegetables", "kimchi": "Pickled vegetables",
    "olive": "Pickled vegetables", "olives": "Pickled vegetables",
    # --- fruits ---
    "apple": "Temperate fruits", "apples": "Temperate fruits", "pear": "Temperate fruits",
    "pears": "Temperate fruits", "peach": "Temperate fruits", "peaches": "Temperate fruits",
    "plum": "Temperate fruits", "plums": "Temperate fruits", "cherry": "Temperate fruits",
    "cherries": "Temperate fruits", "apricot": "Temperate fruits", "apricots": "Temperate fruits",
    "nectarine": "Temperate fruits", "applesauce": "Temperate fruits",
    "strawberry": "Berries", "strawberries": "Berries", "blueberry": "Berries",
    "blueberries": "Berries", "raspberry": "Berries", "raspberries": "Berries",
    "blackberry": "Berries", "blackberries": "Berries", "cranberry": "Berries",
    "cranberries": "Berries", "berry": "Berries", "berries": "Berries",
    "orange": "Citrus", "oranges": "Citrus", "lemon": "Citrus",
    "lemons": "Citrus", "lime": "Citrus", "limes": "Citrus",
    "grapefruit": "Citrus", "tangerine": "Citrus",
    "banana": "Tropical fruits", "bananas": "Tropical fruits", "pineapple": "Tropical fruits",
    "mango": "Tropical fruits", "papaya": "Tropical fruits", "coconut": "Tropical fruits",
    "kiwi": "Tropical fruits", "passion fruit": "Tropical fruits", "guava": "Tropical fruits",
    "raisin": "Dried fruits", "raisins": "Dried fruits", "date": "Dried fruits",
    "dates": "Dried fruits", "prune": "Dried fruits", "prunes": "Dried fruits",
    "fig": "Dried fruits", "figs": "Dried fruits", "currant": "Dried fruits", "currants": "Dried fruits",
    "dried apricot": "Dried fruits", "dried apricots": "Dried fruits",
    # --- grains / flour / pasta / bread ---
    "rice": "Refined grains", "white rice": "Refined grains",
    "pasta": "Refined grains", "macaroni": "Refined grains", "spaghetti": "Refined grains",
    "noodle": "Refined grains", "noodles": "Refined grains", "lasagna noodle": "Refined grains",
    "ramen": "Refined grains", "linguine": "Refined grains", "penne": "Refined grains",
    "fettuccine": "Refined grains", "elbow macaroni": "Refined grains",
    "vermicelli": "Refined grains",
    "brown rice": "Whole grains", "wild rice": "Whole grains", "barley": "Whole grains",
    "quinoa": "Whole grains", "oat": "Whole grains", "oats": "Whole grains",
    "oatmeal": "Whole grains", "bulgur": "Whole grains", "millet": "Whole grains",
    "buckwheat": "Whole grains",
    "bread": "Bread & rolls", "roll": "Bread & rolls", "rolls": "Bread & rolls",
    "bun": "Bread & rolls", "buns": "Bread & rolls", "tortilla": "Bread & rolls",
    "tortillas": "Bread & rolls", "pita": "Bread & rolls", "naan": "Bread & rolls",
    "bagel": "Bread & rolls", "bagels": "Bread & rolls", "croissant": "Bread & rolls",
    "biscuit": "Bread & rolls", "biscuits": "Bread & rolls", "cornbread": "Bread & rolls",
    "muffin": "Bread & rolls", "muffins": "Bread & rolls",  # muffin is breadlike here
    "flour": "Flours", "cornmeal": "Flours", "cake mix": "Prepared mixes",
    "biscuit mix": "Prepared mixes", "pancake mix": "Prepared mixes",
    "bisquick": "Prepared mixes", "stuffing mix": "Prepared mixes",
    # --- baking / sweets ---
    "sugar": "Sugar & sweeteners", "brown sugar": "Sugar & sweeteners",
    "powdered sugar": "Sugar & sweeteners", "honey": "Sugar & sweeteners",
    "syrup": "Sugar & sweeteners", "molasses": "Sugar & sweeteners",
    "maple syrup": "Sugar & sweeteners", "corn syrup": "Sugar & sweeteners",
    "chocolate": "Sugar & sweeteners", "cocoa": "Sugar & sweeteners",
    "chocolate chip": "Sugar & sweeteners", "chocolate chips": "Sugar & sweeteners",
    "marshmallow": "Sugar & sweeteners", "marshmallows": "Sugar & sweeteners",
    "jam": "Sugar & sweeteners", "jelly": "Sugar & sweeteners",
    "baking powder": "Baking ingredients", "baking soda": "Baking ingredients",
    "soda": "Baking ingredients",  # NER often abbreviates "baking soda" to just "soda" in old recipes
    "cream of tartar": "Baking ingredients", "tartar": "Baking ingredients",
    "yeast": "Baking ingredients", "cornstarch": "Baking ingredients",
    "gelatin": "Baking ingredients", "vanilla": "Extracts & essences",
    "almond extract": "Extracts & essences", "lemon extract": "Extracts & essences",
    "salt": "Salt & seasonings", "pepper": "Salt & seasonings",
    "black pepper": "Salt & seasonings", "garlic powder": "Ground spices",
    "onion powder": "Ground spices", "paprika": "Ground spices",
    "cinnamon": "Ground spices", "nutmeg": "Ground spices", "cumin": "Ground spices",
    "chili powder": "Ground spices", "oregano": "Ground spices", "basil": "Ground spices",
    "thyme": "Ground spices",
    # --- fats / oils ---
    "oil": "Oils", "olive oil": "Oils", "vegetable oil": "Oils", "canola oil": "Oils",
    "shortening": "Margarine & shortening", "crisco": "Margarine & shortening",
    "margarine": "Margarine & shortening", "lard": "Margarine & shortening",
    # --- nuts & seeds ---
    "pecan": "Nuts", "pecans": "Nuts", "walnut": "Nuts", "walnuts": "Nuts",
    "almond": "Nuts", "almonds": "Nuts", "cashew": "Nuts", "cashews": "Nuts",
    "pistachio": "Nuts", "pistachios": "Nuts", "macadamia": "Nuts",
    "hazelnut": "Nuts", "hazelnuts": "Nuts", "peanut": "Nuts", "peanuts": "Nuts",
    "nut": "Nuts", "nuts": "Nuts",
    "peanut butter": "Nut butters", "almond butter": "Nut butters",
    "sunflower seed": "Seeds", "sunflower seeds": "Seeds", "pumpkin seed": "Seeds",
    "pumpkin seeds": "Seeds", "sesame": "Seeds", "sesame seed": "Seeds",
    "flax": "Seeds", "flaxseed": "Seeds", "chia": "Seeds", "chia seed": "Seeds",
    # --- legumes ---
    "bean": "Legumes", "beans": "Legumes", "kidney bean": "Legumes",
    "kidney beans": "Legumes", "black bean": "Legumes", "black beans": "Legumes",
    "pinto bean": "Legumes", "pinto beans": "Legumes", "navy bean": "Legumes",
    "navy beans": "Legumes", "lima bean": "Legumes", "lima beans": "Legumes",
    "chickpea": "Legumes", "chickpeas": "Legumes", "garbanzo": "Legumes",
    "lentil": "Legumes", "lentils": "Legumes", "split pea": "Legumes",
    "split peas": "Legumes", "tofu": "Legumes", "tempeh": "Legumes",
    "edamame": "Legumes", "soybean": "Legumes", "soybeans": "Legumes",
    "refried beans": "Legumes",
    # --- beverages ---
    "wine": "Alcoholic beverages", "beer": "Alcoholic beverages", "rum": "Alcoholic beverages",
    "vodka": "Alcoholic beverages", "whiskey": "Alcoholic beverages", "bourbon": "Alcoholic beverages",
    "brandy": "Alcoholic beverages", "champagne": "Alcoholic beverages", "tequila": "Alcoholic beverages",
    "sherry": "Alcoholic beverages", "vermouth": "Alcoholic beverages",
    "coffee": "Coffee & tea", "espresso": "Coffee & tea", "tea": "Coffee & tea",
    "instant coffee": "Coffee & tea",
    "juice": "Juices", "orange juice": "Juices", "apple juice": "Juices",
    "lemon juice": "Juices", "lime juice": "Juices", "pineapple juice": "Juices",
    "cranberry juice": "Juices",
    "cola": "Soft drinks", "coke": "Soft drinks",
    "sprite": "Soft drinks", "7-up": "Soft drinks", "ginger ale": "Soft drinks",
    "club soda": "Soft drinks", "soda water": "Soft drinks",
    "almond milk": "Plant milks", "soy milk": "Plant milks", "oat milk": "Plant milks",
    "coconut milk": "Plant milks",
    # --- sauces / mixes ---
    "ketchup": "Sauces", "mustard": "Sauces", "mayonnaise": "Sauces", "mayo": "Sauces",
    "soy sauce": "Sauces", "worcestershire": "Sauces", "barbecue sauce": "Sauces",
    "bbq sauce": "Sauces", "tomato sauce": "Sauces", "salsa": "Sauces",
    "ranch dressing": "Sauces", "italian dressing": "Sauces", "vinegar": "Sauces",
    "soup": "Prepared soups & broths", "broth": "Prepared soups & broths",
    "stock": "Prepared soups & broths", "bouillon": "Prepared soups & broths",
    "cream of mushroom": "Prepared soups & broths", "cream of chicken": "Prepared soups & broths",
    "cream of celery": "Prepared soups & broths",
}


def normalize_title(raw: str) -> str:
    """Lightweight normalization for comparing meal names (case + whitespace)."""
    s = raw.strip().lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_existing_meal_names() -> set[str]:
    """Return normalized form of every name already in curated + compositional."""
    names = set()
    for path in (CURATED, COMPOSITIONAL):
        data = json.loads(path.read_text(encoding="utf-8"))
        for m in data:
            names.add(normalize_title(m["name"]))
    return names


def load_ingredient_lookup() -> dict[str, str]:
    """Build keyword -> category lookup from ingredients.json + the
    hand-tuned KEYWORD_TO_CATEGORY synonym map. Lowercased keys; longer
    keys take precedence at match time.
    """
    lookup: dict[str, str] = {}
    ings = json.loads(INGREDIENTS.read_text(encoding="utf-8"))
    for ing in ings:
        name = ing.get("name", "").lower().strip()
        cat = ing.get("category")
        if name and cat:
            lookup[name] = cat
            # Also index by the bare base form (drop parentheticals)
            bare = re.sub(r"\s*\([^)]*\)", "", name).strip()
            if bare and bare not in lookup:
                lookup[bare] = cat
    # Hand map overrides ingredients.json for any clash (it should be more
    # comprehensive for the corpus vocabulary).
    for k, v in KEYWORD_TO_CATEGORY.items():
        lookup[k.lower()] = v
    return lookup


def build_matcher(lookup: dict[str, str]) -> re.Pattern:
    """Compile a single alternation regex over all lookup keys, sorted
    longest-first so multi-word ingredients ("brown sugar") win over
    their single-word substrings ("sugar")."""
    keys_sorted = sorted(lookup.keys(), key=len, reverse=True)
    pattern = r"\b(?:" + "|".join(re.escape(k) for k in keys_sorted) + r")\b"
    return re.compile(pattern, re.IGNORECASE)


def infer_categories(
    ner_lists: list[str],
    lookup: dict[str, str],
    matcher: re.Pattern,
) -> list[str]:
    """Return the set of project categories implied by the NER samples,
    ordered by how often each category appears across the samples.

    A single combined regex (built in build_matcher) finds all
    ingredient-keyword hits per NER token in one pass — ~1000× faster
    than searching key-by-key when the lookup has thousands of entries.
    """
    counter: Counter[str] = Counter()
    for raw in ner_lists:
        try:
            tokens = json.loads(raw) if raw else []
        except json.JSONDecodeError:
            continue
        seen_here: set[str] = set()
        for token in tokens:
            t = token.lower().strip()
            for match in matcher.finditer(t):
                cat = lookup.get(match.group(0).lower())
                if cat:
                    seen_here.add(cat)
        for cat in seen_here:
            counter[cat] += 1
    return [c for c, _ in counter.most_common()]


def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "meal"


def main() -> None:
    existing = load_existing_meal_names()
    lookup = load_ingredient_lookup()
    matcher = build_matcher(lookup)

    print(f"Existing meal names (curated + compositional): {len(existing)}")
    print(f"Ingredient/keyword lookup entries:             {len(lookup)}")

    out: list[dict] = []
    skipped_already_covered = 0
    skipped_non_dish = 0
    skipped_no_categories = 0
    skipped_below_freq = 0
    used_ids: set[str] = set()

    seen_titles_in_out: set[str] = set()  # normalized

    with TSV.open("r", encoding="utf-8") as f:
        header = f.readline()
        for line in f:
            parts = line.rstrip("\n").split("\t", 2)
            if len(parts) < 3:
                continue
            count_s, title, ner_s = parts
            count = int(count_s)
            if count < MIN_FREQ:
                skipped_below_freq += 1
                continue

            norm = normalize_title(title)
            if norm in existing:
                skipped_already_covered += 1
                continue
            if norm in seen_titles_in_out:
                continue
            if norm in NON_DISH_TITLES:
                skipped_non_dish += 1
                continue

            # Combine signals from both the NER sample and the title text
            # itself. The title often carries the principal ingredient
            # ("Spinach Dip", "Pumpkin Pie") even when a single NER sample
            # happens to omit it. We feed the title to the same matcher by
            # wrapping it as a JSON array so the parser path stays uniform.
            title_as_ner = json.dumps([title])
            cats = infer_categories([ner_s, title_as_ner], lookup, matcher)
            if not cats:
                skipped_no_categories += 1
                continue

            base_slug = slugify(title)
            slug = base_slug
            i = 2
            while slug in used_ids:
                slug = f"{base_slug}-{i}"
                i += 1
            used_ids.add(slug)
            seen_titles_in_out.add(norm)

            out.append({
                "id": f"corpus-titled-{slug}",
                "name": title,
                "ingredient_categories": cats,
                "notes": f"Recipe title appearing in {count:,} corpus recipes.",
                "cuisine": "Corpus",
                "diet_compatibility": [],
                "frequency": count,
                "source": "corpus-titled",
            })

    out.sort(key=lambda m: -m["frequency"])

    OUT_DATA.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines: list[str] = []
    lines.append(f"# Corpus-titled meals report")
    lines.append(f"")
    lines.append(f"Output entries:                  {len(out)}")
    lines.append(f"Skipped (already in curated/comp): {skipped_already_covered}")
    lines.append(f"Skipped (non-dish title):         {skipped_non_dish}")
    lines.append(f"Skipped (couldn't infer cats):    {skipped_no_categories}")
    lines.append(f"Skipped (below freq threshold {MIN_FREQ}): {skipped_below_freq}")
    lines.append(f"")
    lines.append(f"## Top 100 new entries by corpus frequency")
    for m in out[:100]:
        cats = " + ".join(m["ingredient_categories"][:6])
        if len(m["ingredient_categories"]) > 6:
            cats += " + …"
        lines.append(f"  freq={m['frequency']:5d}  {m['name']:40s}  ({cats})")
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {OUT_DATA.relative_to(ROOT)} ({len(out)} entries)")
    print(f"Wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
