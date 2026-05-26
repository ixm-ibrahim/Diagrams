"""Corpus-titled meals serving-audit — batch 1 (meals 0-149 by frequency).

Corpus-titled servings are well-calibrated by dish tier (cookies 60g, candy 40g,
breads 90g, dips 60g, cakes 140g, casseroles 360g, soups 350g w/ broth) — far
better than the compositional set. So batch 1 has only two clear mis-tier fixes
(P9-adjacent), both serving_grams (no plot/rederive impact):

  - fruit-cocktail-cake: a one-bowl SHEET cake mistakenly on the 320g bowl-dessert
    tier (trifles/punch-bowl live there). A sliced sheet cake belongs on the 140g
    cake tier with the other 425 cakes; 320g->962 kcal is ~2.5x a slice.
  - monkey-bread: a shared pull-apart at 260g->1311 kcal/95g fat; a portion is
    ~3-4 pieces (~110g). (per-100g is also P8-inflated by the sparse 5-cat plate;
    that part is logged, not serving-fixable.)

Logged-not-patched (consistent with curated discipline):
  - P2 chicken-salad[46]: note says "mayo" but categories omit Dressings & dips,
    so it under-reads (97 kcal/100g vs ~200 for mayo chicken salad). Deferred to
    a dedicated P2 dressing-add sweep (curated left P2 unpatched too).
  - caramel-corn[58] under-reads (209 vs ~430 kcal/100g): popcorn is mapped to
    Starchy vegetables (~80) — a category-accuracy issue, not serving.
  - pineapple-casserole[144]: rich sweet Southern SIDE on the 360g main-casserole
    tier -> 925 kcal/50g fat; main-vs-side serving is genuinely ambiguous, left.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

SERVING: dict[str, tuple[int, str]] = {
    'corpus-titled-fruit-cocktail-cake': (140, 'sheet cake mis-tiered at 320g bowl-dessert -> 140g cake slice.'),
    'corpus-titled-monkey-bread':        (110, 'shared pull-apart: 260g->1311kcal/95g fat -> ~3-4 pieces.'),
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
    print(f'\ncorpus serving-audit batch-1 applied. edited={counts["edited"]} noop={counts["noop"]} missing={counts["missing"]}')
    print('NOTE: only serving_grams changed -> no rederive needed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
