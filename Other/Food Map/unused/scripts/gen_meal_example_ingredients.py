#!/usr/bin/env python3
"""Assign `example_ingredients` (project ingredient ids) to every meal.

Batch 2 of the tester-feedback work. Meals carry only `ingredient_categories`;
this fills in a specific, real ingredient per category so the app can filter
meals by an actual held ingredient (fixes the "bagels matches every refined-
grain meal" bug) and show them in an ingredient-level remix.

MODEL (locked: category-faithful).
  example_ingredients is drawn ENTIRELY from the meal's own categories — one
  (occasionally two) specific project ingredient per category. This keeps the
  set consistent with the existing category aggregation (every example
  ingredient's `category` is one of the meal's `ingredient_categories`, and
  every category contributes at least one), so downstream re-aggregation maps
  cleanly back to the category model.

EVIDENCE for which specific ingredient a meal uses, per category:
  1. The meal name + notes (notes are full ingredient-rich descriptions).
  2. The RecipeNLG NER bag for the dish title (unused/docs/corpus-titles.tsv),
     when the meal name matches a canonical corpus title.
  Ingredients are scored by how many of their distinctive name/subcategory
  tokens the evidence mentions, with a strong bonus for a full multi-word
  phrase hit. When a category gets no signal (pantry categories like Oils or
  Salt that names never mention), a curated per-category default is used.

Every selected id is a real project ingredient by construction — nothing is
invented, so no ingredient additions are required (validated separately).

Outputs (in place): src/data/{meals,compositional-meals,corpus-titled-meals}.json
  - a `.pre-example-ingredients.json` backup of each is written first.
Report: scripts/_example_ingredients_report.txt
"""
from __future__ import annotations

import io
import json
import math
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data"
ING_PATH = DATA / "ingredients.json"
MEAL_FILES = ["meals.json", "compositional-meals.json", "corpus-titled-meals.json"]
CORPUS_TITLES = ROOT / "unused" / "docs" / "corpus-titles.tsv"
REPORT_PATH = ROOT / "scripts" / "_example_ingredients_report.txt"

# Tokens that carry no discriminating power for ingredient identity.
STOP = {
    "and", "of", "the", "with", "a", "an", "in", "or", "to", "on", "for",
    "style", "blend", "generic", "mix",
}
# Tokens too generic to ever justify selecting an ingredient on their own —
# they bleed across categories ("water" -> Rose water; the qualifier "plain"
# from "plain yogurt" -> "Bagel (plain)"). Removed from the evidence token set
# before matching; multi-word phrase hits (which use the raw text) are
# unaffected. Distinctive descriptors (white/brown/red/green/black/sweet/dark)
# are deliberately NOT here — they separate real ingredients (white vs brown
# rice). Only process/fat/form qualifiers that describe ANY ingredient go in.
MATCH_STOP = {
    "water", "ice", "juice",
    # Process / fat / form qualifiers (describe any ingredient).
    "plain", "whole", "fresh", "dried", "ground", "raw", "cooked", "canned",
    "frozen", "instant", "powdered", "powder", "prepared", "sweetened",
    "unsweetened", "nonfat", "reduced", "dry",
    # Generic category head-nouns. Matching these alone picks an arbitrary
    # member ("cheese" -> Blue cheese, "oil" -> Rice bran oil); stopping them
    # means a SPECIFIC name (cheddar, sesame oil) is required to override the
    # category's curated default, which is exactly what we want.
    "oil", "sauce", "paste", "cheese", "milk", "cream", "butter", "sugar",
    "flour", "bread", "syrup", "soup", "broth", "vinegar", "yogurt",
}

# Categories whose curated default is an incidental flavoring/garnish that
# would read as wrong when a dish merely lists the category without naming a
# specific (e.g. "Vanilla extract" in a potato salad). For these, emit an
# example ONLY when the evidence actually names one — no default-fill.
SKIP_DEFAULT_CATEGORIES = {
    "Extracts & essences", "Pastes & ferments", "Pickled vegetables",
}

# Measurement / packaging noise that shows up in NER bags.
NER_NOISE = {
    "c", "tsp", "tbsp", "tbs", "tb", "cup", "cups", "oz", "lb", "lbs", "pkg",
    "package", "can", "cans", "jar", "pkt", "qt", "pt", "gal", "g", "kg", "ml",
    "l", "pinch", "dash", "small", "large", "medium", "fresh", "ground",
}

# Curated per-category fallback (keyed by category NAME — meals reference names,
# and the category aggregate is grouped by name). Also serves as the tiebreak
# prototype when several ingredients match the evidence equally well. Every id
# is asserted to exist at load time.
CATEGORY_DEFAULT = {
    # Beverages
    "Alcoholic beverages": "wine-red",
    "Coffee & tea": "coffee-brewed",
    "Juices": "orange-juice",
    "Prepared soups & broths": "chicken-broth",
    "Soft drinks": "cola",
    # Condiments & sauces
    "Dressings & dips": "mayonnaise",
    "Pastes & ferments": "miso-white",
    "Pickled vegetables": "olives-green",
    "Sauces": "soy-sauce",
    # Dairy
    "Aged cheese": "cheddar",
    "Cream & butter": "butter",
    "Fermented dairy": "buttermilk",
    "Fresh cheese": "cream-cheese",
    "Frozen dairy": "ice-cream-vanilla",
    "Milk": "whole-milk",
    "Plant milks": "almond-milk",
    "Processed cheese": "american-cheese",
    "Yogurt": "yogurt-whole",
    # Fats & oils
    "Margarine & shortening": "margarine-stick",
    "Oils": "olive-oil",
    # Fruits
    "Berries": "strawberry",
    "Citrus": "lemon",
    "Dried fruits": "raisin",
    "Temperate fruits": "apple",
    "Tropical fruits": "mango",
    # Grains
    "Baked snacks & pastries": "graham-crackers",
    "Baking ingredients": "baking-powder",
    "Bread & rolls": "white-bread",
    "Flours": "all-purpose-flour",
    "Prepared mixes": "baking-mix",
    "Refined grains": "white-rice",
    "Whole grains": "brown-rice",
    # Herbs & spices
    "Dried herbs": "dried-oregano",
    "Fresh herbs": "parsley",
    "Ground spices": "black-pepper",
    "Salt & seasonings": "salt-table",
    "Spice blends": "italian-seasoning",
    "Whole spices": "cumin",
    # Nuts & seeds
    "Nut butters": "peanut-butter",
    "Nuts": "almond",
    "Seeds": "sesame-seed",
    # Protein (animal)
    "Canned & cured fish": "canned-tuna-water",
    "Eggs": "egg-whole",
    "Freshwater fish": "catfish",
    "Oily fish": "salmon",
    "Organ meats": "beef-liver",
    "Poultry": "chicken-breast",
    "Processed meat": "bacon",
    "Red meat": "ground-beef-80-20",
    "Shellfish": "shrimp",
    "White fish": "cod",
    # Protein (plant)
    "Legumes": "chickpea",
    "Meat alternatives": "seitan",
    "Soy products": "tofu-firm",
    # Sweets
    "Candy & desserts": "dark-chocolate",
    "Extracts & essences": "vanilla-extract",
    "Jams & preserves": "jam-strawberry",
    "Sugar & sweeteners": "white-sugar",
    # Vegetables
    "Cruciferous vegetables": "broccoli",
    "Leafy greens": "spinach",
    "Mushrooms": "mushroom-white",
    "Other vegetables": "onion",
    "Peppers & nightshades": "tomato",
    "Starchy vegetables": "potato-russet",
}


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def norm_text(s: str) -> str:
    """Lowercase, de-accent, &->and, collapse non-alnum to single spaces."""
    s = strip_accents(s or "").lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def tokenize(s: str, drop_noise=False) -> list[str]:
    toks = [t for t in norm_text(s).split() if len(t) >= 2 and t not in STOP]
    if drop_noise:
        toks = [t for t in toks if t not in NER_NOISE]
    return toks


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_meal_json(path: Path, data) -> None:
    """Match the existing file style exactly: 2-space indent, CRLF, trailing
    newline. json.dumps escapes any in-string newline, so the global \n->\r\n
    replace only touches structural line breaks."""
    text = json.dumps(data, ensure_ascii=False, indent=2).replace("\n", "\r\n")
    path.write_bytes((text + "\r\n").encode("utf-8"))


def build_corpus_ner(meal_norm_names: set[str]) -> dict[str, list[str]]:
    """One streaming pass over the 1.16M-row title TSV, capturing NER bags only
    for titles that match a meal name (normalized). First (highest-count) wins."""
    out: dict[str, list[str]] = {}
    if not CORPUS_TITLES.exists():
        print(f"  WARN: {CORPUS_TITLES} missing — proceeding name+notes only.")
        return out
    with CORPUS_TITLES.open("r", encoding="utf-8", newline="") as f:
        header = f.readline()  # count\ttitle\tner_sample
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            _count, title, ner_raw = parts[0], parts[1], parts[2]
            key = norm_text(title)
            if key not in meal_norm_names or key in out:
                continue
            try:
                ner = json.loads(ner_raw)
            except Exception:
                continue
            if isinstance(ner, list):
                out[key] = [str(x) for x in ner]
    return out


def main() -> int:
    ingredients = load_json(ING_PATH)
    by_id = {ing["id"]: ing for ing in ingredients}

    # Validate the curated default map up front — every default id must exist.
    bad_defaults = [(c, i) for c, i in CATEGORY_DEFAULT.items() if i not in by_id]
    if bad_defaults:
        print("ERROR: default ids not in ingredients:", bad_defaults, file=sys.stderr)
        return 1

    # Per-category candidate pools (keyed by category NAME, mirroring the
    # category aggregate which groups by name).
    by_category: dict[str, list[dict]] = defaultdict(list)
    for ing in ingredients:
        by_category[ing["category"]].append(ing)

    # Significant tokens for matching = NAME tokens only (subcategory tokens
    # like "vegetables" / "fish" are category-type words that cause spurious
    # matches — e.g. "Nori" matching the word "vegetables"). Parenthetical
    # content IS kept as tokens so a generic form ("Chicken (whole, roasted)"
    # -> {chicken, whole, roasted}) doesn't get inflated match-coverage over a
    # plainer default ({chicken, breast}).
    sig: dict[str, set[str]] = {}
    name_tokens: dict[str, set[str]] = {}
    core_name: dict[str, str] = {}  # normalized name w/ parenthetical removed
    for ing in ingredients:
        nm = ing["name"]
        nt = set(tokenize(nm))
        name_tokens[ing["id"]] = nt
        sig[ing["id"]] = nt
        core = norm_text(re.sub(r"\([^)]*\)", " ", nm))
        # Only multi-word cores qualify for a phrase bonus; a single-word core
        # is already covered by token matching and would over-match (the bare
        # word "chicken" must not phrase-beat the default cut).
        core_name[ing["id"]] = core if len(core.split()) >= 2 else ""

    # Name-hero indexes. A "hero" is an ingredient named outright in the MEAL
    # name — added even if its category isn't in the meal's list, so dishes like
    # "Banana bread" (banana is a Temperate fruit but the meal tags Tropical)
    # still surface their headline ingredient. Two precise forms only:
    #   - single_token_ing: ingredient whose whole name is one token ("Banana").
    #   - multiword cores (core_name) found as a phrase in the meal name.
    single_token_ing: dict[str, str] = {}
    for ing in ingredients:
        nt = name_tokens[ing["id"]]
        if len(nt) == 1:
            tok = next(iter(nt))
            if tok in MATCH_STOP:
                continue
            # First/shortest-id wins if two share a one-word name (rare).
            single_token_ing.setdefault(tok, ing["id"])

    # Global IDF over significant tokens (distinctive tokens score higher).
    df = Counter()
    for st in sig.values():
        for t in st:
            df[t] += 1
    n_ing = len(ingredients)
    idf = {t: math.log(n_ing / (1 + c)) for t, c in df.items()}

    def tok_idf(t: str) -> float:
        return idf.get(t, math.log(n_ing))

    # Gather every meal's normalized name first, so the corpus pass is targeted.
    meal_blobs = []  # (file, list)
    meal_norm_names: set[str] = set()
    for fn in MEAL_FILES:
        meals = load_json(DATA / fn)
        meal_blobs.append((fn, meals))
        for m in meals:
            meal_norm_names.add(norm_text(m.get("name", "")))

    print(f"Streaming corpus NER for {len(meal_norm_names)} distinct meal names…")
    corpus_ner = build_corpus_ner(meal_norm_names)
    print(f"  matched NER bags for {len(corpus_ner)} meal names.")

    def pick_for_category(category: str, ev_set: set[str], ev_norm: str,
                          name_set: set[str]):
        """Return up to 2 ingredient ids for `category` given meal evidence.
        ev_set: evidence token set; ev_norm: ' '-joined normalized evidence
        string (for phrase containment); name_set: tokens from the meal NAME
        (a match there is the strongest intent signal)."""
        pool = by_category.get(category, [])
        if not pool:
            return []
        default_id = CATEGORY_DEFAULT.get(category)
        ev_padded = f" {ev_norm} "

        scored = []
        for ing in pool:
            iid = ing["id"]
            matched = sig[iid] & ev_set
            phrase = bool(core_name[iid]) and f" {core_name[iid]} " in ev_padded
            if not matched and not phrase:
                continue
            # Confidence gate: a single matched token only counts if it covers
            # at least half the ingredient's name. This rejects modifier-only
            # bleed — "rice" matching "Rice bran oil" (1/3) or "garlic" matching
            # "Garlic-infused oil" (1/3) — while keeping real picks like
            # "Chicken breast"/"Russet potato" (1/2) and any phrase / 2-token hit.
            coverage = len(matched) / max(1, len(sig[iid]))
            confident = phrase or len(matched) >= 2 or coverage >= 0.5
            if not confident:
                continue
            key = (
                1 if phrase else 0,
                len(matched & name_set),   # meal-name token match = strongest
                len(matched),
                round(sum(tok_idf(t) for t in matched), 4),
                coverage,
                1 if iid == default_id else 0,
                -len(sig[iid]),
                -len(ing["name"]),
            )
            scored.append((key, iid, matched, phrase))

        if not scored:
            if category in SKIP_DEFAULT_CATEGORIES:
                return []
            return [default_id] if default_id else ([pool[0]["id"]] if pool else [])

        scored.sort(key=lambda x: x[0], reverse=True)
        _best_key, best_id, best_matched, _bp = scored[0]
        result = [best_id]

        # Optional 2nd pick — only when a DIFFERENT ingredient is named
        # explicitly enough to be confident on its own (a full phrase or a
        # 2-token match), with matched tokens distinct from the first pick.
        # This admits genuine multi-ingredient categories ("Red bell pepper"
        # + "Green bell pepper") while rejecting one-token bleed.
        for key, iid, matched, phrase in scored[1:]:
            if iid in result:
                continue
            distinct = (matched - best_matched) & name_tokens[iid]
            if distinct and (phrase or len(matched) >= 2):
                result.append(iid)
                break
        return result

    def heroes_from_name(name: str, already: set[str]) -> list[str]:
        """Up to 2 whole-ingredient names appearing as a token in the meal NAME
        and not already picked (e.g. "Banana bread" -> banana). Single-token
        ingredients only — a multiword-phrase path would pull in finished
        products like the "Banana bread" ingredient itself."""
        nm_tokens = [t for t in norm_text(name).split() if t not in MATCH_STOP]
        out = []
        for tok in nm_tokens:
            iid = single_token_ing.get(tok)
            if iid and iid not in already and iid not in out:
                out.append(iid)
        return out[:2]

    report = []
    stats = {
        "total": 0, "with_ner": 0, "default_only": 0,
        "two_plus_in_cat": 0, "examples_total": 0, "heroes": 0,
    }
    default_usage = Counter()
    cat_signal = Counter()  # category -> times a non-default pick was made

    for fn, meals in meal_blobs:
        for m in meals:
            stats["total"] += 1
            name = m.get("name", "")
            notes = m.get("notes", "") or ""
            ner = corpus_ner.get(norm_text(name), [])
            if ner:
                stats["with_ner"] += 1
            ev_tokens = set(tokenize(name)) | set(tokenize(notes))
            for x in ner:
                ev_tokens |= set(tokenize(x, drop_noise=True))
            ev_tokens -= MATCH_STOP
            ev_norm = norm_text(" ".join([name, notes] + ner))
            name_set = set(tokenize(name)) - MATCH_STOP

            cats = m.get("ingredient_categories", []) or []
            picked = []
            seen = set()
            all_default = True
            for cat in cats:
                ids = pick_for_category(cat, ev_tokens, ev_norm, name_set)
                if len(ids) > 1:
                    stats["two_plus_in_cat"] += 1
                default_id = CATEGORY_DEFAULT.get(cat)
                for iid in ids:
                    if iid and iid not in seen:
                        seen.add(iid)
                        picked.append(iid)
                        if iid == default_id and ids == [default_id]:
                            default_usage[cat] += 1
                        else:
                            all_default = False
                            cat_signal[cat] += 1
            # Name-hero ingredients (recognizable headline ingredient named in
            # the title but absent from the picked set / meal categories).
            heroes = heroes_from_name(name, seen)
            for iid in heroes:
                seen.add(iid)
                picked.append(iid)
            stats["heroes"] += len(heroes)

            m["_example_ingredients"] = picked  # staged; reordered on write
            stats["examples_total"] += len(picked)
            if all_default and cats and not heroes:
                stats["default_only"] += 1

            ex_names = [by_id[i]["name"] for i in picked if i in by_id]
            hero_names = {by_id[i]["name"] for i in heroes if i in by_id}
            shown = [(f"*{n}*" if n in hero_names else n) for n in ex_names]
            report.append(f"[{fn}] {name}\n    cats: {', '.join(cats)}\n"
                          f"    -> {', '.join(shown)}"
                          + ("   (NER)" if ner else ""))

    # Write back, inserting example_ingredients right after ingredient_categories
    # and preserving original key order otherwise. Back up the original file
    # bytes verbatim first (one-time) so the change is fully reversible.
    dry_run = "--dry-run" in sys.argv
    import shutil
    for fn, meals in meal_blobs:
        if dry_run:
            for m in meals:
                m.pop("_example_ingredients", None)
            continue
        backup = (DATA / fn).with_name((DATA / fn).stem + ".pre-example-ingredients.json")
        if not backup.exists():
            shutil.copyfile(DATA / fn, backup)
        rebuilt = []
        for m in meals:
            picked = m.pop("_example_ingredients")
            out = {}
            for k, v in m.items():
                out[k] = v
                if k == "ingredient_categories":
                    out["example_ingredients"] = picked
            if "example_ingredients" not in out:  # safety: meal had no categories key
                out["example_ingredients"] = picked
            rebuilt.append(out)
        write_meal_json(DATA / fn, rebuilt)

    # Report
    lines = []
    lines.append("=" * 72)
    lines.append(" MEAL example_ingredients GENERATION REPORT")
    lines.append("=" * 72)
    for k, v in stats.items():
        lines.append(f"  {k:18s} {v}")
    avg = stats["examples_total"] / max(1, stats["total"])
    lines.append(f"  avg per meal       {avg:.2f}")
    lines.append("")
    lines.append("--- Top default (no-signal) categories ---")
    for cat, c in default_usage.most_common(25):
        sig_c = cat_signal.get(cat, 0)
        lines.append(f"  {cat:28s} default={c:5d}  signal={sig_c}")
    lines.append("")
    lines.append("--- All meals (file order) ---")
    lines.extend(report)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

    print("\n".join(lines[:40]))
    print(f"\nFull report: {REPORT_PATH}")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
