"""Corpus-titled meals serving-audit — batch 5 (meals 600-749 by frequency).

One clear mis-tier fix (serving_grams only, no plot/rederive impact):
  - rhubarb-crunch: a crisp/crunch dessert on the 320g tier; siblings apple-crunch
    and peach-crisp (same batch) are 140g. Normalize 320->140 (731 kcal -> ~320).

Logged-not-patched:
  - 320g bowl-desserts/sweet sides (blueberry-delight 826 kcal, scalloped-
    pineapple, candied-yams) rich but portion-subjective (consistent with K2/K3).
  - All soups carry broth; cakes/pies/cookies/candy/breads/dips/dessert-salads
    (all 230) correctly tiered.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

SERVING: dict[str, tuple[int, str]] = {
    'corpus-titled-rhubarb-crunch': (140, 'crisp/crunch dessert mis-tiered at 320g -> 140g (matches apple-crunch/peach-crisp).'),
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
        print(f'  {mid:38s} {old} -> {grams}')

    SRC.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'\ncorpus serving-audit batch-5 applied. edited={counts["edited"]} noop={counts["noop"]} missing={counts["missing"]}')
    print('NOTE: only serving_grams changed -> no rederive needed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
