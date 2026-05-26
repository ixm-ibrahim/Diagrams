"""Corpus-titled meals serving-audit — REMAINING range K8-K16 (index 1050-2442).

After 7 manual batches the corpus pattern fully converged to ONE recurring defect:
dessert items stranded on the 320g bowl-dessert tier that are really single-serving
sliced cakes / pies / pastries (→140g), plus the occasional cookie mis-tagged onto
a meal tier (→60g) and a gelatin mold that belongs on the dessert-salad tier (→230g).

This patch was produced by a programmatic scan of index 1050-2442 (validated by
eyeball against name + notes + computed per-serving), per the user's go-ahead to
finish corpus via scan rather than 9 more full manual dumps. Serving_grams only —
no plot/rederive impact.

What was deliberately LEFT (genuine 320g bowl/large desserts, eyeballed):
  - no-bake layered desserts: cherry-yum-yum, cherries-in-the-snow, fruit-delight,
    striped-delight, four-layer-delight (scooped/shared, correct on 320g).
  - large ice-cream desserts: banana-split-sundae, cherries-jubilee.
  - deep-FRIED hand-helds: banana-fritters, fried-apple-pies, fried-pies — fried
    so per-100g is under-stated (P1) and the larger serving compensates.
P5: none — corpus chili/gumbo/stew read 142-197 kcal/100g (correct for thick
dishes; they are not thin broths), consistent with K1-K7. All soups carry broth.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

# id -> (new_serving_grams, why)
SERVING: dict[str, tuple[int, str]] = {
    # sliced cakes / pies / pastries stranded at 320g -> 140g cake/pie tier
    'corpus-titled-apple-strudel':        (140, 'strudel slice: 320g->783kcal -> 140g.'),
    'corpus-titled-pumpkin-roll':         (140, 'rolled sponge cake (sliced pinwheels): 320g->439kcal -> 140g cake tier.'),
    'corpus-titled-fruitcake':            (140, 'dense holiday cake; twins fruit-cake/white-fruitcake are 140.'),
    'corpus-titled-mississippi-mud':      (140, 'chocolate sheet cake/brownie; twin mississippi-mud-cake is 140.'),
    'corpus-titled-lemonade-cake':        (140, 'poke cake -> 140g cake tier.'),
    'corpus-titled-baked-alaska':         (140, 'cake+ice-cream plated dessert: 320g->1016kcal -> 140g slice.'),
    'corpus-titled-coconut-pies':         (140, 'impossible coconut pie; twins impossible-pie/-coconut-pie are 140.'),
    'corpus-titled-apple-turnovers':      (140, 'individual turnovers: 320g->468kcal -> 140g (1-2 turnovers).'),
    'corpus-titled-pecan-pies':           (140, 'pecan pie; twin southern-pecan-pie is 140 (was 1212kcal).'),
    'corpus-titled-buttermilk-brownies':  (140, 'Texas chocolate sheet "brownie"; sheet-cake tier 140 (was 863kcal).'),
    'corpus-titled-chocolate-eclairs':    (140, 'eclairs; twin chocolate-eclair is 140 (was 800kcal).'),
    # gelatin mold -> dessert-salad tier
    'corpus-titled-cranberry-mold':       (230, 'molded cranberry-gelatin salad -> 230g dessert-salad tier.'),
    # cookies mis-tiered onto larger tiers -> 60g cookie tier
    'corpus-titled-chocolate-peanut-butter-cookies': (60, 'drop cookies at 320g->1232kcal -> 60g cookie tier.'),
    'corpus-titled-chocolate-chip-cookie':           (60, 'drop cookie at 140g -> 60g (cookies tier; cf. chocolate-chip-cookies).'),
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
        print(f'  {mid:46s} {old} -> {grams}')

    SRC.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'\ncorpus serving-audit REMAINING (1050-2442) applied. edited={counts["edited"]} noop={counts["noop"]} missing={counts["missing"]}')
    print('NOTE: only serving_grams changed -> no rederive needed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
