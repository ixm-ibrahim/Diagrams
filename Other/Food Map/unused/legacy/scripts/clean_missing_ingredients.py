"""Phase 16: canonicalize and clean MISSING_INGREDIENTS.txt.

Input:  MISSING_INGREDIENTS.txt (the raw ~4500-row sibling-agent output)
Output: MISSING_INGREDIENTS_CLEAN.csv (deduplicated, garbage-filtered, ~600-1500 rows)

This script never modifies ingredients.json. It only produces the cleaned candidate
list that Phases 17–24 will draw from. Idempotent — re-running produces an identical
CSV (sorted by canonical name).

Run:  python scripts/clean_missing_ingredients.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "MISSING_INGREDIENTS.txt"
OUT = ROOT / "MISSING_INGREDIENTS_CLEAN.csv"
ING = ROOT / "src" / "data" / "ingredients.json"

# ---------------------------------------------------------------------------
# Filter vocabulary
# ---------------------------------------------------------------------------

# Words that turn an ingredient name into a recipe-modifier phrase. Strip from
# the start; what remains gets canonicalized. If nothing remains, drop the row.
MODIFIER_PREFIXES = {
    "additional", "amount", "any", "some", "extra", "more", "less", "other",
    "optional", "leftover", "prepared", "enough", "few", "several", "remaining",
    "needed", "necessary", "favorite", "preferred", "your", "good", "fresh",
    "best", "quality", "fine", "coarse", "premium", "deluxe", "fancy",
    "homemade", "store-bought", "name-brand", "generic",
    "rolled", "assorted", "made", "dish", "side", "main", "course",
    "style", "blend", "variety", "selection",
    # Quantity descriptors that the NLG dataset embedded into "names":
    "fifth", "jigger", "pinch", "handful", "drop", "splash", "dash", "shot",
    "shots", "bottle", "bottles", "can", "cans", "bag", "bags", "box", "boxes",
    "pack", "packs", "package", "packages", "slice", "slices", "piece", "pieces",
    "head", "heads", "bunch", "bunches", "jar", "jars", "sprig", "sprigs",
    "clove", "cloves", "ounce", "cup", "tablespoon", "teaspoon", "pound",
    "gallon", "quart", "pint", "stick", "sticks", "loaf", "loaves",
    "of", "with", "from", "for",
}

# Sub-tokens to also strip when they appear immediately after a modifier.
# e.g. "amount of salt" -> strip "amount" -> " of salt" -> strip "of" -> "salt"
SECOND_PASS_PREFIXES = {"of", "the", "a", "an"}

# Prep / cut / texture descriptors. These describe what happened to an
# ingredient, not the ingredient itself. Drop wherever they appear so
# "grated parmesan" / "shredded parmesan" / "parmesan" all collapse.
PREP_WORDS = {
    "chopped", "minced", "sliced", "diced", "grated", "shredded", "crushed",
    "mashed", "pureed", "cubed", "quartered", "halved", "ground", "flaked",
    "freshly", "finely", "coarsely", "julienned", "riced", "crumbled", "packed",
    "peeled", "seeded", "sectioned", "wedged", "trimmed", "deveined", "shelled",
    "boned", "boneless", "skinless", "skin-on", "stemmed", "pitted", "cored",
    "instant", "long-grain", "short-grain", "medium-grain",
    "thick", "thin", "thick-cut", "thin-cut",
    "raw", "uncooked",  # "raw chicken" / "uncooked rice" collapse to canonical
    "unsalted", "salted",  # butter/nuts/etc. — Phase 17 can split if needed
    "low-fat", "reduced-fat", "non-fat", "nonfat", "full-fat", "low-sodium",
    "sweetened", "unsweetened",
    "softened", "melted", "warmed", "chilled", "room-temperature",
}

# Form prefixes - become the `proposed_form` column rather than part of the
# canonical name. "dried apricot" -> canonical="apricot", form='dried'.
FORM_PREFIXES = {
    "dried":    "dried",
    "canned":   "canned",
    "frozen":   "frozen",
    "cured":    "cured",
    "pickled":  "pickled",
    "powdered": "powdered",
    "smoked":   "cured",      # closest FORM bucket
}

# Head-word equipment / non-ingredient nouns. If the canonical name ENDS
# (or IS) one of these, drop the row.
EQUIPMENT_TAILS = {
    "pan", "pans", "bowl", "bowls", "cloth", "mold", "molds", "tray", "trays",
    "sheet", "sheets", "paper", "wrap", "dish", "dishes", "knife", "grater",
    "board", "boards", "pot", "pots", "skillet", "skillets", "tin", "tins",
    "rack", "racks", "spoon", "fork", "blender", "mixer",
    "topping", "filling", "layer", "layers", "crust",
    "garnish", "drizzle", "smear",
}

# Names too generic to add as a single ingredient. The dataset already has
# specific variants (e.g., red wine, beer-lager); a bare "wine" or "beer" entry
# would just confuse the filter tree.
TOO_GENERIC = {
    "cheese", "oil", "wine", "tea", "coffee", "salt", "sugar", "flour", "milk",
    "water", "pepper", "spice", "spices", "herb", "herbs", "fruit", "fruits",
    "vegetable", "vegetables", "meat", "fish", "nut", "nuts", "seed", "seeds",
    "bread", "rice", "pasta", "noodles", "noodle", "cereal", "broth", "stock",
    "juice", "syrup", "vinegar", "sauce", "spread", "dressing", "extract",
    "color", "coloring", "flavoring", "flavour", "flavor", "topping", "filling",
    "mix", "frosting", "icing", "marinade", "seasoning", "rub", "glaze", "paste",
    "dough", "batter", "root", "leaf", "leaves", "stem", "skin", "shell",
    "meat", "meats", "fat", "fats", "cream", "butter", "honey", "salt-free",
    "lard", "shortening", "margarine", "yogurt", "cheese-flavored",
    "candy", "candies", "chocolate", "cocoa", "ice", "drink", "drinks",
    "liquid", "powder", "granule", "granules", "alcohol",
    "roast", "grill", "fry", "saute", "boil", "bake", "steam", "broil",
    "cake", "pie", "tart", "loaf", "biscuit", "muffin", "scone", "roll",
    "bun", "cookie", "cracker", "wafer", "pretzel", "tortilla",  # bare forms
    "soup", "stew", "broth", "stock",  # bare forms — Phase 18 covers specifics
    "dressing", "marinade", "sauce", "condiment", "spread",  # bare
}

# Leading brand names that contribute no useful semantics. Stripping them
# leaves the generic ingredient. Order matters — longer phrases first so
# "betty crocker yellow cake mix" -> "yellow cake mix", not "crocker yellow ...".
BRAND_PREFIXES = [
    "betty crocker", "duncan hines", "pillsbury", "kraft", "knorr", "swanson",
    "campbell's", "campbells", "libby's", "libbys", "hellmann's", "hellmanns",
    "heinz", "mccormick", "lawry's", "lawrys", "hidden valley", "french's",
    "frenchs", "sara lee", "smucker's", "smuckers", "ocean spray", "planters",
    "sun-maid", "sunmaid", "lipton", "nestle", "nestlé", "kelloggs", "kellogg's",
    "general mills", "morton", "morton's", "minute", "uncle ben's", "uncle bens",
    "rice-a-roni", "old el paso", "ortega", "rotel", "ro-tel", "best foods",
    "miracle whip", "kool-aid", "kool aid", "jell-o", "jello", "jiffy",
    "bisquick", "old bay", "tabasco", "del monte", "green giant", "birds eye",
    "bird's eye", "stove top", "stovetop", "shake n bake", "shake 'n bake",
    "lipton's", "maxwell house", "folgers", "folger's", "starbucks", "tazo",
    "twinings", "yorkshire", "tetley", "cracker barrel", "philadelphia",
    "land o lakes", "land o' lakes",
]
# Sort longest-first so multi-word matches win over single-word.
BRAND_PREFIXES.sort(key=len, reverse=True)

# Words to drop wherever they appear (typo / measurement abbreviations).
NOISE_WORDS = {"pwdr", "approx", "approximate", "approximately", "abt", "about",
               "circa", "roughly", "boxed", "packaged", "small", "medium",
               "large", "tiny", "huge", "regular", "standard"}

# Explicit spelling/plural normalizations. Applied as word-level substitutions
# (so "anaheim chiles" -> "anaheim chili", "tomatoes" -> "tomato").
WORD_NORMS = {
    "chile": "chili", "chiles": "chili", "chilies": "chili", "chilis": "chili",
    "chilli": "chili", "chillis": "chili", "chillies": "chili",
    "tomatoes": "tomato", "tomatos": "tomato",
    "potatoes": "potato", "potatos": "potato",
    "berries": "berry",
    "loaves": "loaf", "halves": "half", "knives": "knife",
    "leaves": "leaf",
    "anchovies": "anchovy",
    "raspberries": "raspberry", "strawberries": "strawberry",
    "blueberries": "blueberry", "blackberries": "blackberry",
    "cranberries": "cranberry", "gooseberries": "gooseberry",
    "boysenberries": "boysenberry", "elderberries": "elderberry",
    "cherries": "cherry",
    "yolks": "yolk", "whites": "white",
    "scallops": "scallop", "shrimps": "shrimp",
    # Spelling variants
    "yoghurt": "yogurt", "yogourt": "yogurt",
    "chedder": "cheddar",
    "pimiento": "pimento", "pimientos": "pimento", "pimentos": "pimento",
    "bleu": "blue",
    "doughnut": "donut", "doughnuts": "donut", "donuts": "donut",
    "molasses": "molasses",
    "ketchup": "ketchup", "catsup": "ketchup",
    "graham": "graham",
    # Common typos
    "mozzeralla": "mozzarella", "mozzerella": "mozzarella",
    "parmesian": "parmesan", "parmasan": "parmesan", "parmasian": "parmesan",
    "gorganzola": "gorgonzola",
    # Generic plurals to singular for common ingredients
    "olives": "olive",
    "pickles": "pickle",
    "carrots": "carrot",
    "onions": "onion",
    "apples": "apple", "pears": "pear", "peaches": "peach",
    "lemons": "lemon", "limes": "lime", "oranges": "orange",
    "bananas": "banana", "grapes": "grape",
    "eggs": "egg", "wings": "wing", "thighs": "thigh", "drumsticks": "drumstick",
    "beans": "bean",
    "lentils": "lentil",
    "chickpeas": "chickpea", "garbanzos": "chickpea", "garbanzo": "chickpea",
    "peas": "pea", "peanuts": "peanut", "almonds": "almond",
    "walnuts": "walnut", "pecans": "pecan", "cashews": "cashew",
    "pistachios": "pistachio", "hazelnuts": "hazelnut",
    "rolls": "roll", "buns": "bun", "biscuits": "biscuit",
    "cookies": "cookie", "crackers": "cracker", "wafers": "wafer",
    "tortillas": "tortilla", "pretzels": "pretzel",
    "noodles": "noodle",
    "mushrooms": "mushroom",
    # Brand-equivalent generics
    "parmigiano": "parmesan", "reggiano": "",
    "parmigiano-reggiano": "parmesan",
}

# Phase 14 added Beverages food_group. The sibling agent's output uses the
# original 11 food_groups, so remap proposed categories that should now sit
# under Beverages.
BEVERAGE_CATEGORIES = {
    "Alcoholic beverages",
    "Coffee & tea",
    "Juices",
    "Soft drinks",
    "Prepared soups & broths",
}

# Pickled vegetables also moved (food_group: Vegetables -> Condiments & sauces)
# in Phase 15. Remap.
CATEGORY_FOOD_GROUP_OVERRIDE = {
    "Pickled vegetables": "Condiments & sauces",
}

VALID_FOOD_GROUPS = {
    "Vegetables", "Fruits", "Grains", "Protein (animal)", "Protein (plant)",
    "Dairy", "Nuts & seeds", "Fats & oils", "Sweets", "Herbs & spices",
    "Condiments & sauces", "Beverages",
}


# ---------------------------------------------------------------------------
# Canonicalization
# ---------------------------------------------------------------------------

WS_RE = re.compile(r"\s+")
NON_WORD_RE = re.compile(r"[^a-z0-9' \-]+")


def normalize_text(s: str) -> str:
    s = s.lower().strip()
    s = s.replace("’", "'").replace("–", "-").replace("—", "-")
    s = NON_WORD_RE.sub(" ", s)
    s = WS_RE.sub(" ", s).strip()
    return s


def strip_brand_prefix(name: str) -> str:
    for brand in BRAND_PREFIXES:
        if name.startswith(brand + " "):
            return name[len(brand) + 1 :].strip()
        if name == brand:
            return ""
    return name


def strip_modifier_prefix(name: str) -> str:
    """Strip leading modifier words; bail when nothing modifier-like remains."""
    parts = name.split(" ")
    while parts and parts[0] in MODIFIER_PREFIXES:
        parts.pop(0)
        # Also drop any immediately-following "of"/"the"/etc.
        while parts and parts[0] in SECOND_PASS_PREFIXES:
            parts.pop(0)
    return " ".join(parts).strip()


def drop_noise_words(name: str) -> str:
    parts = [w for w in name.split(" ") if w and w not in NOISE_WORDS and w not in PREP_WORDS]
    return " ".join(parts).strip()


def extract_form(name: str) -> tuple[str, str]:
    """Pull a leading or trailing form word out of the name. Returns
    (name_without_form, form). Form is empty string if none found."""
    parts = name.split(" ")
    # Leading: "dried apricot" -> ("apricot", "dried")
    if parts and parts[0] in FORM_PREFIXES:
        return (" ".join(parts[1:]).strip(), FORM_PREFIXES[parts[0]])
    # Trailing: "apricot dried" (rare but appears) -> ("apricot", "dried")
    if parts and parts[-1] in FORM_PREFIXES:
        return (" ".join(parts[:-1]).strip(), FORM_PREFIXES[parts[-1]])
    return (name, "")


def is_equipment(name: str) -> bool:
    parts = name.split(" ")
    if not parts:
        return False
    if parts[-1] in EQUIPMENT_TAILS:
        return True
    if len(parts) == 1 and parts[0] in EQUIPMENT_TAILS:
        return True
    return False


def canonicalize(raw: str) -> tuple[str, str]:
    """Returns (canonical_name, proposed_form)."""
    name = normalize_text(raw)
    name = strip_brand_prefix(name)
    name = strip_modifier_prefix(name)
    name = drop_noise_words(name)
    # Word-level spelling/plural normalization.
    name = " ".join(WORD_NORMS.get(w, w) for w in name.split(" "))
    name = WS_RE.sub(" ", name).strip()
    # Form extraction (after spelling norms so we catch "smoked" / "dried" etc.).
    name, form = extract_form(name)
    name = name.strip()
    return name, form


# ---------------------------------------------------------------------------
# Category sanity flags
# ---------------------------------------------------------------------------

def category_flags(name: str, category: str, food_group: str) -> list[str]:
    """Surface obviously-wrong proposed categorizations. Returns a list of flag
    strings. Empty list = no concerns."""
    flags: list[str] = []
    # "cheese" should land under a Dairy category. The previous-agent's
    # categorizer mis-routed brand-prefixed cheeses (e.g. "sharp cracker
    # barrel cheese") into Grains/Crackers because the word "cracker"
    # appears. Flag every cheese-named entry that isn't in Dairy — the
    # reviewer can fix the category and decide if it's a real cheese.
    if "cheese" in name.split(" ") and food_group != "Dairy":
        # Only suppress when cheese is being used as a modifier in a
        # well-known non-dairy compound: "cheese cake" (Sweets), "cheese
        # cracker" (Grains), "cheese powder" (seasoning). The word right
        # AFTER "cheese" determines this, not just any nearby noun.
        words = name.split(" ")
        idx = words.index("cheese")
        tail = words[idx + 1] if idx + 1 < len(words) else ""
        non_dairy_compound = tail in {"cake", "cracker", "crackers", "powder",
                                      "board", "knife", "grater", "cloth"}
        if not non_dairy_compound:
            flags.append("cheese-not-dairy")
    if "milk" in name.split(" "):
        # "coconut milk" / "almond milk" / "soy milk" / "hemp milk" are plant
        # milks and already in the dataset; skip the flag for those.
        plant_milk = bool(re.search(r"\b(coconut|almond|soy|oat|cashew|hemp|rice)\b", name))
        if food_group != "Dairy" and not plant_milk:
            flags.append("milk-not-dairy")
    if "oil" in name.split(" ") and food_group != "Fats & oils":
        flags.append("oil-not-fats")
    if "wine" in name.split(" ") and "vinegar" not in name and food_group != "Beverages":
        # Cooking wines (Shaoxing, mirin, sake) live under Condiments — skip flag.
        cooking_wine = bool(re.search(r"\b(shaoxing|mirin|sake|cooking)\b", name))
        if not cooking_wine:
            flags.append("wine-not-beverages")
    if food_group not in VALID_FOOD_GROUPS:
        flags.append(f"invalid-food-group:{food_group}")
    return flags


def remap_food_group(category: str, food_group: str) -> str:
    """Apply Phase 14/15 remaps so the proposed food_group reflects the current
    schema (Beverages exists; Pickled vegetables sits under Condiments & sauces)."""
    if category in BEVERAGE_CATEGORIES:
        return "Beverages"
    if category in CATEGORY_FOOD_GROUP_OVERRIDE:
        return CATEGORY_FOOD_GROUP_OVERRIDE[category]
    return food_group


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_existing_canonical_names() -> set[str]:
    """Canonical-form names (form-stripped) already in ingredients.json."""
    with ING.open("r", encoding="utf-8") as f:
        data = json.load(f)
    out: set[str] = set()
    for ing in data:
        cname, _ = canonicalize(ing["name"])
        out.add(cname)
    return out


def read_raw_rows() -> list[dict]:
    rows: list[dict] = []
    with RAW.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.rstrip("\n").split(",")]
            if len(parts) < 5:
                continue
            if parts[0] == "ingredient":
                continue  # header
            rows.append({
                "name": parts[0],
                "category": parts[1],
                "subcategory": parts[2],
                "food_group": parts[3],
                "major_group": parts[4],
            })
    return rows


def main() -> None:
    existing = load_existing_canonical_names()
    rows = read_raw_rows()
    starting = len(rows)
    print(f"Loaded {starting} raw candidate rows.")

    # Pass 1: canonicalize names, drop garbage.
    cleaned: list[dict] = []
    drop_empty = drop_generic = drop_brand_only = drop_equipment = 0
    for r in rows:
        c, form = canonicalize(r["name"])
        if not c:
            drop_empty += 1
            continue
        if c in TOO_GENERIC:
            drop_generic += 1
            continue
        if len(c) < 3:
            drop_brand_only += 1
            continue
        if is_equipment(c):
            drop_equipment += 1
            continue
        r["canonical_name"] = c
        r["proposed_form"] = form
        r["food_group"] = remap_food_group(r["category"], r["food_group"])
        cleaned.append(r)
    print(f"  dropped {drop_empty} empty-after-strip, {drop_generic} too-generic, "
          f"{drop_brand_only} too-short, {drop_equipment} equipment/non-ingredient.")

    # Pass 2: group by (canonical_name, form). "apricot" and "dried apricot"
    # are separate groups so a form variant can survive even when the base
    # ingredient already exists in the project.
    by_key: dict[tuple, list[dict]] = defaultdict(list)
    for r in cleaned:
        by_key[(r["canonical_name"], r["proposed_form"])].append(r)
    print(f"  collapsed {len(cleaned)} rows -> {len(by_key)} (name, form) groups.")

    # Pass 3: drop groups whose canonical_name+no-form matches an existing entry.
    drop_existing = 0
    kept: list[dict] = []
    for (cname, form), group in by_key.items():
        # Existence check uses just canonical_name. "dried apricot" survives even
        # if "apricot" is in the dataset, because its form makes it a distinct
        # variant; "apricot" (no form) would match and be dropped.
        if not form and cname in existing:
            drop_existing += 1
            continue
        # Pick the modal proposed category.
        cat_counts: dict[tuple, int] = defaultdict(int)
        first_seen: dict[tuple, int] = {}
        for i, r in enumerate(group):
            key = (r["category"], r["subcategory"], r["food_group"])
            cat_counts[key] += 1
            first_seen.setdefault(key, i)
        best = max(cat_counts.keys(), key=lambda k: (cat_counts[k], -first_seen[k]))
        category, subcategory, food_group = best
        # Confidence tier: high if 2+ raw rows collapsed into this canonical
        # (more recipes mention it = more likely a real ingredient); low if
        # only one raw row produced it (could be a typo, a niche variant, or
        # a genuine but rarely-listed ingredient — Phase 17+ judges per row).
        vc = len(group)
        confidence = "high" if vc >= 2 else "low"
        kept.append({
            "canonical_name": cname,
            "proposed_category": category,
            "proposed_subcategory": subcategory,
            "proposed_food_group": food_group,
            "proposed_form": form,
            "proposed_contains_tags": "",  # filled by Phase 17+ batches
            "flags": ";".join(category_flags(cname, category, food_group)),
            "source_count": cat_counts[best],
            "variants_count": vc,
            "confidence": confidence,
        })
    print(f"  dropped {drop_existing} already-in-project canonical names.")

    # Pass 4: sort deterministically. High-confidence rows first within each
    # (food_group, category, subcategory) bucket so Phase 17+ reviewers see
    # the validated entries before the long tail.
    kept.sort(key=lambda r: (r["proposed_food_group"], r["proposed_category"],
                              r["proposed_subcategory"],
                              0 if r["confidence"] == "high" else 1,
                              r["canonical_name"], r["proposed_form"]))

    # Write CSV.
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "canonical_name", "proposed_category", "proposed_subcategory",
            "proposed_food_group", "proposed_form", "proposed_contains_tags",
            "flags", "source_count", "variants_count", "confidence",
        ])
        w.writeheader()
        for r in kept:
            w.writerow(r)

    # Summary.
    print()
    print(f"Output: {OUT}")
    print(f"  Starting rows:               {starting}")
    print(f"  Dropped (garbage/generic):   {drop_empty + drop_generic + drop_brand_only + drop_equipment}")
    print(f"  Dropped (already in project):{drop_existing}")
    print(f"  Collapsed duplicates:        {len(cleaned) - len(by_key)}")
    print(f"  Final cleaned candidates:    {len(kept)}")
    high = sum(1 for r in kept if r["confidence"] == "high")
    low = sum(1 for r in kept if r["confidence"] == "low")
    print(f"    high confidence (vc>=2):   {high}")
    print(f"    low confidence (vc==1):    {low}")
    print()
    flagged = [r for r in kept if r["flags"]]
    print(f"  Rows with sanity flags:      {len(flagged)}")
    # Per-flag counts
    flag_counts: dict[str, int] = defaultdict(int)
    for r in flagged:
        for f in r["flags"].split(";"):
            flag_counts[f] += 1
    for k, v in sorted(flag_counts.items(), key=lambda x: -x[1]):
        print(f"    {k}: {v}")

    # Top collapse groups (largest variants_count) — useful for human review.
    print()
    print("Top 15 collapsed groups (variants_count desc):")
    top = sorted(kept, key=lambda r: -r["variants_count"])[:15]
    for r in top:
        print(f"  {r['variants_count']:3d} × {r['canonical_name']!r:40s} -> "
              f"{r['proposed_food_group']} / {r['proposed_category']} / {r['proposed_subcategory']}")

    # Final sanity: every proposed_food_group must be in VALID_FOOD_GROUPS.
    bad_fg = [r for r in kept if r["proposed_food_group"] not in VALID_FOOD_GROUPS]
    if bad_fg:
        print(f"\nWARN: {len(bad_fg)} rows have invalid food_group; sample:")
        for r in bad_fg[:5]:
            print(f"  {r['canonical_name']} -> {r['proposed_food_group']}")


if __name__ == "__main__":
    main()
