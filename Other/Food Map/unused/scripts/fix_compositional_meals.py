#!/usr/bin/env python3
"""Clean compositional-meals.json.

Problems with the file as it stands:
  - 790 entries collapse to 657 distinct category-set signatures —
    same combo plotted multiple times under different names. Same dot,
    same nutrition; only the label differs. The 3D view shows visual
    clutter that doesn't represent additional information.
  - The pattern extractor emitted "noise" categories (Sugar &
    seasonings, Salt & seasonings, Extracts & essences, etc.) that
    coincidentally appeared in the source recipes but are not
    constitutive of the named dish — e.g. "Compound butter" is a
    butter-and-herbs preparation in culinary practice, but the stored
    categories are {Cream & butter, Sugar & sweeteners}. The sugar is
    a corpus-noise artifact.
  - Several names assigned to a shape are simply wrong fits — "Roux"
    is salted flour-butter paste, not "Cream & butter, Flours,
    Sugar & sweeteners".

This script:
  (1) Looks up each compositional meal name in recipe_taxonomy.csv. If
      it has >= 20 matches, replaces ingredient_categories with the
      corpus-derived set (>=35% threshold).
  (2) For each meal that doesn't have enough corpus support, applies a
      hand-written list of "fluff strips" — pulls obviously-wrong
      categories out of specific named dishes.
  (3) Dedupes the final list by category-set signature. When multiple
      meals end up with the same signature, the highest-frequency one
      wins and the rest are dropped (their frequencies are summed
      into the survivor).

The fluff strip list was built by reading every meal name + categories
and asking "does the category list match what a person eating this
dish would actually consume?" — see HAND_STRIPS below.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from audit_subcategory_map import SUB_TO_CATEGORY

TAXONOMY = ROOT / "recipe_taxonomy.csv"
COMP = ROOT / "src" / "data" / "compositional-meals.json"
DROPPED = ROOT / "docs" / "dropped-compositional-meals.json"
REPORT = ROOT / "docs" / "compositional-fixes-report.json"

INCLUDE_THR = 0.35
MIN_MATCHES = 20

POSSESSIVE_PREFIXES = re.compile(
    r"^\s*("
    r"aunt|uncle|grandma|grandpa|granny|nana|mom|mama|mother|"
    r"dad|papa|father|mrs|mr|ms|miss|my|our|"
    r"best|easy|quick|simple|amazing|delicious|favorite|favourite|perfect|"
    r"super|ultimate|classic|original|traditional|homemade|home-made|home|"
    r"world|world's|grandmother's|grandma's|grandpa's|grandfather's|"
    r"mom's|mama's|mother's|dad's|papa's|father's|the|a|an|"
    r"low-fat|low fat|low-carb|low carb|low-sodium|low sodium|"
    r"healthy|crockpot|crock-pot|crock pot|slow-cooker|slow cooker|"
    r"instant pot|microwave|easy peasy"
    r")\b[\s'.,!]+",
    re.IGNORECASE,
)
LEADING_POSSESSIVE = re.compile(r"^\s*[A-Z][a-zA-Z\-]+(\s+[A-Z][a-zA-Z\-]+)?'s\s+", re.UNICODE)
TRAILING_PAREN = re.compile(r"\s*[\(\[][^)\]]*[\)\]]\s*$")
TRAILING_DASH = re.compile(r"\s*[-:|]\s+.{1,40}$")
WHITESPACE = re.compile(r"\s+")


def normalize_title(raw: str) -> str:
    s = (raw or "").strip().strip("\"'")
    for _ in range(6):
        new = LEADING_POSSESSIVE.sub("", s)
        new = POSSESSIVE_PREFIXES.sub("", new)
        if new == s:
            break
        s = new
    s = TRAILING_PAREN.sub("", s)
    s = TRAILING_DASH.sub("", s)
    s = WHITESPACE.sub(" ", s).strip(" \t.,!\"'-")
    return s.title()


# Per-name fluff stripping for meals that don't have enough corpus
# matches to rebuild from scratch. Each entry is a name (case-
# insensitive, exact match) -> set of categories to remove from its
# stored list.
HAND_STRIPS = {
    "compound butter":         {"Sugar & sweeteners"},
    "brown butter sauce":      {"Sugar & sweeteners"},
    "glass of milk":           {"Sugar & sweeteners"},
    "warm milk":               {"Sugar & sweeteners"},
    "bechamel base":           {"Sugar & sweeteners"},
    "cream sauce":             {"Sugar & sweeteners"},
    "scrambled eggs":          {"Sugar & sweeteners", "Extracts & essences"},
    "fried eggs":              {"Sugar & sweeteners", "Extracts & essences"},
    "hard-boiled eggs":        {"Sugar & sweeteners", "Extracts & essences"},
    "omelet":                  {"Sugar & sweeteners", "Extracts & essences"},
    "roux":                    {"Sugar & sweeteners"},
    "steamed vegetable medley":{"Sugar & sweeteners", "Sauces"},
    "sautéed vegetables":      {"Sugar & sweeteners"},
    "roasted vegetables":      {"Sugar & sweeteners"},
    "fruit cocktail":          {"Alcoholic beverages"},  # canned fruit, not booze
    "trail mix with apples":   {"Sugar & sweeteners"},
    "mixed nuts":              {"Sugar & sweeteners"},
    "roasted nuts":            {"Sugar & sweeteners"},
    "sliced apples":           {"Sugar & sweeteners"},
    "fresh fruit plate":       {"Sugar & sweeteners"},
    "mixed berries":           {"Sugar & sweeteners"},
    "strawberry bowl":         {"Sugar & sweeteners"},
    "cheese plate":            {"Sugar & sweeteners"},
    "sliced cheddar":          {"Sugar & sweeteners"},
    "ricotta plate":           {"Sugar & sweeteners"},
    "cottage cheese bowl":     {"Sugar & sweeteners"},
    "fresh mozzarella":        {"Sugar & sweeteners"},
    "tossed salad":            {"Sugar & sweeteners", "Sauces"},
    "garden salad":            {"Sugar & sweeteners", "Sauces"},
    "green salad":             {"Sugar & sweeteners"},
    "sautéed greens":          {"Sugar & sweeteners"},
    "sautéed greens with veg": {"Sugar & sweeteners"},
    "cooked lentils":          {"Sugar & sweeteners"},
    "black beans":             {"Sugar & sweeteners"},
    "chickpeas":               {"Sugar & sweeteners"},
    "brown rice":              {"Sugar & sweeteners"},
    "oatmeal":                 {"Sugar & sweeteners"},
    "cooked quinoa":           {"Sugar & sweeteners"},
    "white rice":              {"Sugar & sweeteners"},
    "buttered pasta":          {"Sugar & sweeteners"},
    "buttered rice":           {"Sugar & sweeteners"},
    "buttered brown rice":     {"Sugar & sweeteners"},
    "butter-finished oatmeal": {"Sugar & sweeteners"},
    "sliced bread":            {"Sugar & sweeteners"},
    "dinner rolls":            {"Sugar & sweeteners"},
    "toast":                   {"Sugar & sweeteners"},
    "buttered bread":          {"Sugar & sweeteners"},
    "garlic bread":            {"Sugar & sweeteners"},
    "roast chicken":           {"Sugar & sweeteners"},
    "grilled chicken breast":  {"Sugar & sweeteners"},
    "roast turkey":            {"Sugar & sweeteners"},
    "roast beef":              {"Sugar & sweeteners"},
    "grilled steak":           {"Sugar & sweeteners"},
    "ground beef skillet":     {"Sugar & sweeteners"},
    "bacon":                   {"Sugar & sweeteners"},
    "ham slices":              {"Sugar & sweeteners"},
    "breakfast sausage":       {"Sugar & sweeteners"},
    "steamed shrimp":          {"Sugar & sweeteners"},
    "boiled crab":             {"Sugar & sweeteners"},
    "pan-seared liver":        {"Sugar & sweeteners"},
    "chopped liver":           {"Sugar & sweeteners"},
    "yogurt bowl":             {"Sugar & sweeteners"},
    "kefir":                   {"Sugar & sweeteners"},
    "roasted broccoli":        {"Sugar & sweeteners"},
    "sautéed cabbage":         {"Sugar & sweeteners"},
    "almond milk glass":       {"Sugar & sweeteners"},
    "glass of wine":           {"Sugar & sweeteners"},
    "cocktail":                {"Sugar & sweeteners"},
    "beer":                    {"Sugar & sweeteners"},
    "glass of juice":          {"Sugar & sweeteners"},
    "coffee":                  {"Sugar & sweeteners"},
    "hot tea":                 {"Sugar & sweeteners"},
    "coffee with cream":       {"Sugar & sweeteners"},
    "creamy latte":            {"Sugar & sweeteners"},
    "café au lait":            {"Sugar & sweeteners"},
    "milk tea":                {"Sugar & sweeteners"},
    "latte":                   {"Sugar & sweeteners"},
    "pie dough":               {"Sugar & sweeteners"},   # savory pie
    "shortcrust pastry":       {"Sugar & sweeteners"},
    "pasta dough":             {"Sugar & sweeteners"},
    "egg noodles":             {"Sugar & sweeteners"},
    "pancake batter":          set(),  # batter has sugar, keep
    "crêpe batter":            set(),
    "bechamel":                {"Sugar & sweeteners"},
    "béchamel":                {"Sugar & sweeteners"},
}


def build_title_index():
    csv.field_size_limit(min(sys.maxsize, 2**31 - 1))
    idx: dict[str, list[set]] = defaultdict(list)
    with TAXONOMY.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        for i, row in enumerate(reader, 1):
            if len(row) < 4:
                continue
            title = row[1]
            sub_cell = row[3]
            if not title or not sub_cell:
                continue
            canon = normalize_title(title)
            if not canon:
                continue
            try:
                subs = json.loads(sub_cell)
            except json.JSONDecodeError:
                continue
            if not isinstance(subs, list) or not subs:
                continue
            cats = set()
            for s in subs:
                c = SUB_TO_CATEGORY.get(s)
                if c:
                    cats.add(c)
            if cats:
                idx[canon].append(cats)
            if i % 500_000 == 0:
                print(f"  ... {i:,} rows, {len(idx):,} titles", file=sys.stderr)
    return idx


def main():
    print("Building canonical-title index...", file=sys.stderr)
    idx = build_title_index()
    print(f"  done: {len(idx):,} titles", file=sys.stderr)

    comp = json.loads(COMP.read_text(encoding="utf-8"))
    print(f"Loaded {len(comp)} compositional meals", file=sys.stderr)

    report: list[dict] = []
    rebuilt_count = 0
    stripped_count = 0

    for m in comp:
        canon = normalize_title(m["name"])
        matches = idx.get(canon) or []
        n = len(matches)
        before = list(m.get("ingredient_categories", []))

        # (1) Corpus-driven rebuild for confident cases.
        if n >= MIN_MATCHES:
            freq = Counter()
            for cats in matches:
                for c in cats:
                    freq[c] += 1
            rel = [(c, freq[c] / n) for c in freq]
            rel.sort(key=lambda kv: -kv[1])
            derived = [c for c, p in rel if p >= INCLUDE_THR]
            if derived and set(derived) != set(before):
                m["ingredient_categories"] = derived
                rebuilt_count += 1
                report.append({"name": m["name"], "kind": "corpus-rebuild",
                              "n_matches": n, "before": before, "after": derived})
            continue

        # (2) Hand fluff stripping for low-corpus-confidence items.
        strip = HAND_STRIPS.get(m["name"].lower())
        if strip:
            after = [c for c in before if c not in strip]
            if after != before:
                m["ingredient_categories"] = after
                stripped_count += 1
                report.append({"name": m["name"], "kind": "hand-strip",
                              "n_matches": n, "before": before, "after": after})

    # (3) Drop meals with empty / vacuous category lists after cleanup.
    nonempty = []
    dropped_empty = []
    for m in comp:
        if not m.get("ingredient_categories"):
            dropped_empty.append({"id": m.get("id"), "name": m["name"],
                                  "reason": "empty after fluff-strip"})
            continue
        nonempty.append(m)

    # (4) Dedupe by signature. When multiple meals share a signature,
    #     keep the highest-frequency entry; sum the others' frequencies
    #     into it; drop the rest with a record of who absorbed whom.
    by_sig: dict[tuple, list[dict]] = defaultdict(list)
    for m in nonempty:
        sig = tuple(sorted(m["ingredient_categories"]))
        by_sig[sig].append(m)

    final = []
    dedup_dropped = []
    for sig, group in by_sig.items():
        if len(group) == 1:
            final.append(group[0])
            continue
        group.sort(key=lambda m: -(m.get("frequency") or 0))
        winner = group[0]
        total = sum((m.get("frequency") or 0) for m in group)
        winner["frequency"] = total
        winner.setdefault("notes", "")
        for loser in group[1:]:
            dedup_dropped.append({
                "id": loser.get("id"), "name": loser["name"],
                "reason": f"duplicate signature; absorbed into {winner['name']!r}",
            })
        final.append(winner)

    print(f"Rebuilt {rebuilt_count} via corpus; "
          f"stripped fluff from {stripped_count}; "
          f"dropped {len(dropped_empty)} empty + {len(dedup_dropped)} dedup",
          file=sys.stderr)

    final.sort(key=lambda m: -(m.get("frequency") or 0))
    COMP.write_text(json.dumps(final, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    DROPPED.write_text(json.dumps(dropped_empty + dedup_dropped, indent=2,
                                  ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    print(f"Wrote {COMP.relative_to(ROOT)} ({len(final)} entries)", file=sys.stderr)
    print(f"Wrote {DROPPED.relative_to(ROOT)} "
          f"({len(dropped_empty) + len(dedup_dropped)} dropped)", file=sys.stderr)


if __name__ == "__main__":
    main()
