"""Corpus-titled meals serving-audit — batch 2 (meals 150-299 by frequency).

One clear mis-tier fix (serving_grams only, no plot/rederive impact):
  - gingerbread: a sliced spiced quick-bread/CAKE parked on the 320g bowl-dessert
    tier; belongs on the 140g cake tier with every sibling cake (320g->697 kcal).

Logged-not-patched:
  - The 320g bowl/pan desserts (chocolate-delight 887 kcal, cherry-delight,
    death-by-chocolate, baked-pineapple, harvard-beets) are rich and high, but
    they are genuinely scooped/shared layered desserts or sweet sides — the
    portion is subjective, not a clear template bug like a sliced cake. Left
    (mirrors the conservative curated discipline).
  - hot-chocolate-mix[179]: a DRY pantry mix on a 240g drink serving (504 kcal).
    240g of powder is not a serving, but its per-100g is also understated because
    powdered milk maps to the liquid `Milk` category (~60 vs ~440 for powder), so
    the two errors partly cancel. No clean fix (no powdered-milk category);
    cutting serving alone would push it too low. Logged as a dry-mix edge case.
  - P8: veg-all-casserole[219] plate=169g -> 250 kcal/100g, 900 kcal/56g fat
    (mayo+cheese+crackers, little veg mass) — sparse-dense, not serving-fixable.
  - P2 (deferred): pea-salad[211] mayo-bound but no Dressings & dips cat (123 vs
    ~160). Note: most corpus mayo-salads DO carry Dressings & dips, so P2 is
    sparser here than feared. Still deferred to the single P2 sweep.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

SERVING: dict[str, tuple[int, str]] = {
    'corpus-titled-gingerbread': (140, 'sliced spiced cake/quick-bread mis-tiered at 320g -> 140g cake slice.'),
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
    print(f'\ncorpus serving-audit batch-2 applied. edited={counts["edited"]} noop={counts["noop"]} missing={counts["missing"]}')
    print('NOTE: only serving_grams changed -> no rederive needed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
