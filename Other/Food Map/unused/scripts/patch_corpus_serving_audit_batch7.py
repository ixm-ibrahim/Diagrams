"""Corpus-titled meals serving-audit — batch 7 (meals 900-1049 by frequency).

Two mis-tier fixes (serving_grams only, no plot/rederive impact):
  - apple-kuchen: a cake-mix coffee cake (sliced) stranded at 320g -> 140g cake tier.
  - bubble-bread: literally monkey bread ("biscuit dough rolled in cinnamon-sugar,
    layered") at 320g -> 1352 kcal/74g fat; match the 110g set for monkey-bread in K1.

Logged-not-patched:
  - 320g layered "delight" desserts (lemon-delight, pineapple-delight) & noodle-
    kugel left as bowl/substantial-side tier (portion-subjective; consistent).
  - finger-jello[1026] 416 kcal/100g is a category-accuracy artifact (gelatin
    mapped to Candy & desserts; no gelatin category) — serving 60g is fine. Log.
  - All soups fine on broth; all other tiers correct.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

SERVING: dict[str, tuple[int, str]] = {
    'corpus-titled-apple-kuchen':  (140, 'cake-mix coffee cake mis-tiered at 320g -> 140g cake slice.'),
    'corpus-titled-bubble-bread':  (110, 'monkey bread at 320g->1352kcal -> 110g (match monkey-bread K1).'),
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
    print(f'\ncorpus serving-audit batch-7 applied. edited={counts["edited"]} noop={counts["noop"]} missing={counts["missing"]}')
    print('NOTE: only serving_grams changed -> no rederive needed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
