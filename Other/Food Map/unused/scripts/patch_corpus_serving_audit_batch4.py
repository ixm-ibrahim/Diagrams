"""Corpus-titled meals serving-audit — batch 4 (meals 450-599 by frequency).

One clear mis-tier fix (serving_grams only, no plot/rederive impact):
  - cherry-crunch: a cherry dump-cake/crisp ("pie filling under a cake-mix-and-
    butter topping") on the 320g tier; its siblings — blackberry/cherry/blueberry/
    apple cobbler and dump-cake — are all 140g. Normalize 320->140 (752 kcal slice
    was ~2x a cobbler portion).

Logged-not-patched:
  - funnel-cakes[452] 320g->709 kcal: fried, so per-100g is UNDER-stated (221 vs
    ~380, P1) while serving is high — they compensate to a plausible one-funnel-
    cake number. Left.
  - ice-cream-cake[523] plate=54g->462 kcal/100g (P8, only 2 cats); serving 120g
    fine. P8 density only.
  - P2 (deferred): crab-salad/seafood-salad read 60 kcal/100g (mayo likely missing;
    no Dressings & dips) — could be light vinegar versions. Deferred to P2 sweep.
  - All soups carry broth; cakes/pies/cookies/candy/breads/dips correctly tiered.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

SERVING: dict[str, tuple[int, str]] = {
    'corpus-titled-cherry-crunch': (140, 'cherry dump-cake/crisp mis-tiered at 320g -> 140g cobbler tier.'),
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
    print(f'\ncorpus serving-audit batch-4 applied. edited={counts["edited"]} noop={counts["noop"]} missing={counts["missing"]}')
    print('NOTE: only serving_grams changed -> no rederive needed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
