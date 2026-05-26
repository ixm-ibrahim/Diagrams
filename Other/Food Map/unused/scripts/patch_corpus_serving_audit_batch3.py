"""Corpus-titled meals serving-audit — batch 3 (meals 300-449 by frequency).

One clear mis-tier fix (serving_grams only, no plot/rederive impact):
  - heavenly-hash: a fruit/marshmallow/nut dessert "salad" (same as ambrosia,
    congealed-salad — all 230g) sitting on the 360g main-casserole tier ->
    584 kcal. Normalize to the 230g dessert-salad tier.

Logged-not-patched:
  - lemon-lush[427] / other no-bake layered "lush/delight" desserts on the 320g
    bowl/pan-dessert tier are rich (660 kcal) but genuinely scooped/shared —
    portion subjective, not a sliced-cake mis-tier. Left (as in K2).
  - P8: mixed-vegetable-casserole[391]/veg-all (dup) plate=169g -> 900 kcal/56g
    fat (mayo+cheese+crackers, little veg); carrot-casserole 705 kcal. Sparse-
    dense, not serving-fixable.
  - P2 (deferred): apple-salad[367] possibly mayo/whipped but no dressing cat;
    most corpus salads already carry Dressings & dips. Deferred to the P2 sweep.
  - All soups carry broth; all cakes/pies/cookies/candy/breads correctly tiered.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

SERVING: dict[str, tuple[int, str]] = {
    'corpus-titled-heavenly-hash': (230, 'fruit/marshmallow dessert-salad mis-tiered at 360g -> 230g (matches ambrosia).'),
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
    print(f'\ncorpus serving-audit batch-3 applied. edited={counts["edited"]} noop={counts["noop"]} missing={counts["missing"]}')
    print('NOTE: only serving_grams changed -> no rederive needed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
