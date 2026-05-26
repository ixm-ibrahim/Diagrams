"""Corpus-titled meals serving-audit — batch 6 (meals 750-899 by frequency).

Three mis-tier fixes (serving_grams only, no plot/rederive impact) — all the
sliced-cake/crisp/bowl-dessert-at-320 pattern, normalized to the 140g tier:
  - blueberry-crunch: pie-filling crisp/crunch (cf. cherry-crunch, rhubarb-crunch).
  - blueberry-buckle: a "tender butter cake" with blueberries -> cake slice 140g.
  - dirt: Oreo/cream-cheese pudding dessert — its twins dirt-pudding,
    oreo-cookie-dessert are 140g; this one was stranded at 320g (806 kcal).

Logged-not-patched:
  - sweet-potato-balls[824] 320g looks big for "balls" but it's a candied sweet-
    potato SIDE (tagged dinner/lunch) and matches the sweet-potato-side tier
    (mashed-sweet-potatoes is also 320g). Left.
  - All soups carry/are-fine on broth; all other tiers correct.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

SERVING: dict[str, tuple[int, str]] = {
    'corpus-titled-blueberry-crunch': (140, 'crisp/crunch dessert mis-tiered at 320g -> 140g.'),
    'corpus-titled-blueberry-buckle': (140, 'butter cake (buckle) mis-tiered at 320g -> 140g cake slice.'),
    'corpus-titled-dirt':            (140, 'Oreo pudding dessert; twins dirt-pudding/oreo-dessert are 140g.'),
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
    print(f'\ncorpus serving-audit batch-6 applied. edited={counts["edited"]} noop={counts["noop"]} missing={counts["missing"]}')
    print('NOTE: only serving_grams changed -> no rederive needed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
