"""Compositional meals serving-audit — batch 2 (meals 150-299 by frequency).

Two kinds of edit (mirrors curated batch shape):

1. serving_grams (P9 — density-blind templated servings). Dense small-format
   desserts/snacks/candy inherit a 220-280g meal-slot serving and read 2-5x too
   high per serving. Per-family targets reused from batch 1:
     cookies/biscotti/shortbread -> 50g · candy -> 40g · no-bake bars -> 50g ·
     savory cheese-pastry snack -> 60g · ricotta cannoli/sfogliatella -> 90g.
   Plus one bread outlier: 'whole-wheat-bread' (a plain loaf modeled from Flours,
   not Bread & rolls) carried the generic 280g while every sibling bread loaf is
   80g -> normalize to 80g (one-slice-ish portion, consistent with the family).
   serving_grams only rescales the displayed per-serving; per-100g/plot untouched.

2. ingredient_categories (P5 — brothy dish missing the liquid category).
   'lentil-peanut-stew' notes say it is "simmered in a peanut-butter broth" yet
   its categories are only Legumes/Nut butters/Sugar, so the plate reads 240
   kcal/100g (real West-African groundnut stew ~140-170). Add 'Prepared soups &
   broths' to supply the liquid mass. THIS edit touches categories ->
   rerun rederive_diet_compatibility.py afterward.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'compositional-meals.json'
BROTH = 'Prepared soups & broths'

# id -> (new_serving_grams, why)
SERVING: dict[str, tuple[int, str]] = {
    'corpus-peanut-butter-oat-squares': (50, 'no-bake oat bar: 280g->1053kcal/73g fat; one square.'),
    'corpus-peanut-butter-eggs':        (40, 'PB candy eggs: 280g->1460kcal/110g fat; 2 confections.'),
    'corpus-nut-shortbread-4':          (50, 'cookie dessert: 220g->1095kcal; 2-3 cookies.'),
    'corpus-cheese-pastry':             (60, 'savory cheese-pastry snack: 280g->1118kcal; cheese-straw portion.'),
    'corpus-cheese-pastry-2':           (90, 'ricotta cannoli/sfogliatella: 220g->743kcal; one pastry.'),
    'corpus-pecan-biscotti':            (50, 'biscotti (cookie family): 140g->504kcal; 2 biscotti.'),
    'corpus-whole-wheat-bread':         (80, 'plain loaf: 280g->953kcal; every sibling bread loaf is 80g.'),
}

# id -> (category_to_add, why)
ADD_CATEGORY: dict[str, tuple[str, str]] = {
    'corpus-lentil-peanut-stew': (BROTH, 'notes say "peanut-butter broth"; no liquid cat -> 240 kcal/100g (real ~140-170).'),
}


def main() -> int:
    data = json.loads(SRC.read_text(encoding='utf-8'))
    by_id = {m['id']: m for m in data}
    counts = {'serv': 0, 'cat': 0, 'noop': 0, 'missing': 0}

    for mid, (grams, why) in SERVING.items():
        meal = by_id.get(mid)
        if meal is None:
            counts['missing'] += 1; print(f'  MISSING: {mid}', file=sys.stderr); continue
        if meal.get('serving_grams') == grams:
            counts['noop'] += 1; continue
        print(f'  serv {mid:34s} {meal.get("serving_grams")} -> {grams}')
        meal['serving_grams'] = grams
        counts['serv'] += 1

    for mid, (cat, why) in ADD_CATEGORY.items():
        meal = by_id.get(mid)
        if meal is None:
            counts['missing'] += 1; print(f'  MISSING: {mid}', file=sys.stderr); continue
        cats = list(meal.get('ingredient_categories') or [])
        if cat in cats:
            counts['noop'] += 1; continue
        cats.append(cat)
        meal['ingredient_categories'] = cats
        counts['cat'] += 1
        print(f'  +cat {mid:34s} +{cat}')

    SRC.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('\ncompositional serving-audit batch-2 applied.')
    print(f'  serving edits:  {counts["serv"]}')
    print(f'  category adds:  {counts["cat"]}')
    print(f'  noop:           {counts["noop"]}')
    print(f'  missing:        {counts["missing"]}')
    print('\nNOTE: category was edited -> run rederive_diet_compatibility.py')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
