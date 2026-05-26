"""Compositional meals serving-audit — batch 3 (meals 300-449 by frequency).

All edits are serving_grams (P9 — density-blind templated servings). Same
per-family targets as batches 1-2: cookies -> 50g; dried-fruit snack -> 40g.
serving_grams only rescales displayed per-serving; per-100g/plot untouched, so
NO rederive needed.

Logged-not-patched this batch (see _serving_audit_patterns.md batch C3 notes):
  - P8 sparse dense plates: cacio-e-pepe (1081 kcal/66g fat, plate=87g),
    cheese-stuffed-bread (884 kcal, plate=130g), lentil-grain-butter-bowl.
  - berry-nut-snack-mix mis-categorized: "dried berries" sits in the fresh
    `Berries` category (~50 kcal/100g) so it plots as a light snack though it
    is a dense dried mix. A Berries->Dried fruits swap would be the honest fix,
    but its displayed per-serving is coincidentally fine; left for a possible
    category-accuracy sweep rather than a fiddly per-meal swap here.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'compositional-meals.json'

SERVING: dict[str, tuple[int, str]] = {
    'corpus-raisin-oat-cookies':       (50, 'cookie dessert: 280g->819kcal; 2-3 cookies.'),
    'corpus-peanut-oat-butter-cookies':(50, 'cookie dessert: 280g->869kcal; 2-3 cookies.'),
    'corpus-peanut-butter-oat-cookies':(50, 'cookie dessert: 280g->842kcal; 2-3 cookies.'),
    'corpus-dried-fruit-mix':          (40, 'dried-fruit snack: 220g->695kcal/152g carb; ~1/4 cup serving.'),
}


def main() -> int:
    data = json.loads(SRC.read_text(encoding='utf-8'))
    by_id = {m['id']: m for m in data}
    counts = {'edited': 0, 'noop': 0, 'missing': 0}

    for mid, (grams, why) in SERVING.items():
        meal = by_id.get(mid)
        if meal is None:
            counts['missing'] += 1; print(f'  MISSING: {mid}', file=sys.stderr); continue
        old = meal.get('serving_grams')
        if old == grams:
            counts['noop'] += 1; continue
        meal['serving_grams'] = grams
        counts['edited'] += 1
        print(f'  {mid:34s} {old} -> {grams}')

    SRC.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'\ncompositional serving-audit batch-3 applied. edited={counts["edited"]} noop={counts["noop"]} missing={counts["missing"]}')
    print('NOTE: only serving_grams changed -> no rederive needed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
