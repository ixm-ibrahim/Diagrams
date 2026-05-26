"""Compositional meals serving-audit — batch 4 / FINAL (meals 450-624 by freq).

All edits are serving_grams (P9 — density-blind templated servings). Targets
consistent with batches 1-3 plus two new small-format families:
  crackers -> 50g · date-nut bite snack -> 50g · cheese plate -> 100g ·
  nut crostini appetizer -> 70g · scone -> 90g (one generous scone).
serving_grams only rescales displayed per-serving; per-100g/plot untouched ->
NO rederive needed.

Note on berry-scones: its per-100g is under-stated because it uses the fresh
`Berries` category (~50 kcal/100g) rather than a buttery-dough density, so at
90g it now displays a bit low. We still set the correct 90g PORTION rather than
keep an inflated 280g serving to mask a density bug (that compensation is the
exact anti-pattern this audit avoids). The under-density is logged separately
(same root as berry-nut-snack-mix in batch C3).

No P5 broth-add this batch: african-peanut-stew carries Other-veg + Oils + fruit
bulk and reads 157 kcal/100g (within range), unlike batch-2's bare lentil-peanut
stew (240) — so it is left as-is.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'compositional-meals.json'

SERVING: dict[str, tuple[int, str]] = {
    'corpus-sesame-crackers':      (50,  'cracker snack: 280g->1022kcal/68g fat; a handful.'),
    'corpus-cheese-crackers':      (50,  'cracker snack: 280g->1272kcal/95g fat; a handful.'),
    'corpus-date-nut-snack':       (50,  'nut-stuffed dates: 220g->861kcal; a few bites.'),
    'corpus-two-cheese-plate':     (100, 'cheese-plate snack: 250g->621kcal/45g fat; small plate (cheese-plate family).'),
    'corpus-toasted-nut-crostini': (70,  'crostini appetizer: 200g->865kcal/57g fat; a few rounds.'),
    'corpus-berry-scones':         (90,  'scone: 280g (~3 scones) -> one generous scone.'),
    'corpus-raisin-scones':        (90,  'scone: 280g->616kcal (~3 scones) -> one generous scone (~197kcal).'),
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
    print(f'\ncompositional serving-audit batch-4 applied. edited={counts["edited"]} noop={counts["noop"]} missing={counts["missing"]}')
    print('NOTE: only serving_grams changed -> no rederive needed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
