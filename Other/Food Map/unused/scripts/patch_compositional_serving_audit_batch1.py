"""Compositional meals serving-audit — batch 1 (meals 0-149 by frequency).

Compositional meals carry a templated `serving_grams` assigned by meal-slot
(snack / dessert / breakfast / lunch / dinner), NOT by energy density. For
bulky/watery items (fruit bowls, smoothies, soups) the templated 220-350g is
fine. But for calorie-DENSE small-format items it is 2-5x too large, so the
displayed per-serving balloons to implausible numbers — e.g. a 220 g "snack"
of mixed nuts reads 1120 kcal, a 280 g "dessert" of shortbread reads 1142 kcal.

This is the one clearly per-meal, honest, serving_grams-fixable gap in the
compositional set (pattern P9 in _serving_audit_patterns.md). per-100g density
and the plotted 3D position are unaffected — only the displayed serving size /
per-serving nutrients change. No category edits, so NO rederive needed.

Per-family targets (reused verbatim when the same families recur in later
batches, so cross-batch servings stay consistent):
  - nuts-as-snack (mixed/buttered nuts)          -> 40 g  (~1 oz snack)
  - cheese/charcuterie & cheese-nut appetizer    -> 100 g (small plate)
  - cookie/shortbread desserts (dense flour+fat) -> 50 g  (2-3 cookies)
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'compositional-meals.json'

# id -> (new_serving_grams, why)
DECISIONS: dict[str, tuple[int, str]] = {
    'corpus-buttered-nuts':         (40,  'snack nuts: 220g->1154kcal is absurd for a snack; 1 oz nut serving.'),
    'corpus-mixed-nuts':            (40,  'snack nuts: 220g->1120kcal; 1 oz nut serving.'),
    'corpus-cheese-charcuterie':    (100, 'appetizer plate: 220g->755kcal/45g protein; small charcuterie portion.'),
    'corpus-cheese-nut-plate':      (100, 'appetizer plate: 250g->998kcal/88g fat; small cheese+nut portion.'),
    'corpus-almond-cookies':        (50,  'cookie dessert: 280g->922kcal; 2-3 cookies.'),
    'corpus-shortbread-cookies':    (50,  'cookie dessert: 280g->1142kcal; 2-3 cookies.'),
    'corpus-peanut-butter-cookies': (50,  'cookie dessert: 280g->1028kcal; 2-3 cookies.'),
    'corpus-nut-shortbread':        (50,  'cookie dessert: 280g->1244kcal; 2-3 cookies.'),
    'corpus-whole-wheat-cookies':   (50,  'cookie dessert: 280g->719kcal; 2-3 cookies.'),
    'corpus-oat-cookies-2':         (50,  'oatmeal cookie dessert: 280g->800kcal; 2-3 cookies.'),
    'corpus-whole-wheat-nut-cookies': (50, 'cookie dessert: 280g->825kcal; 2-3 cookies.'),
    'corpus-oat-nut-cookies':       (50,  'cookie dessert: 280g->894kcal; 2-3 cookies.'),
}


def main() -> int:
    data = json.loads(SRC.read_text(encoding='utf-8'))
    by_id = {m['id']: m for m in data}
    counts = {'edited': 0, 'noop': 0, 'missing': 0}

    for mid, (grams, why) in DECISIONS.items():
        meal = by_id.get(mid)
        if meal is None:
            counts['missing'] += 1
            print(f'  MISSING: {mid}', file=sys.stderr)
            continue
        old = meal.get('serving_grams')
        if old == grams:
            counts['noop'] += 1
            continue
        meal['serving_grams'] = grams
        counts['edited'] += 1
        print(f'  {mid:34s} {old} -> {grams}')

    SRC.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('\ncompositional serving-audit batch-1 applied.')
    print(f'  edited:  {counts["edited"]}')
    print(f'  noop:    {counts["noop"]}')
    print(f'  missing: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print('\nNOTE: only serving_grams changed (no categories) -> no rederive needed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
