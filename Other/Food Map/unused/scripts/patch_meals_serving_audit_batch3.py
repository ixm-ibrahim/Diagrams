"""Curated meals serving-audit — batch 3 (meals 300-449 by frequency).

Heavy on desserts, beverages, breakfasts, and European/world mains. Same
verdict: serving_grams sensible; density is the story. Patchable fix is again
P5 — three brothy soups lacking 'Prepared soups & broths' (shchi, Ukrainian
borscht — consistent with the batch-1 borscht patch — and Greek fasolada).

NOT patched (logged): tested adding 'Plant milks' to coconut curries (P7) and
found it makes them WORSE — the Plant milks category mean is light almond/oat
milk (60 kcal/100g, 4g fat), not coconut milk (~200/21g). Coconut dishes that
already use Plant milks (chettinad, avial, moqueca-baiana) actually under-read.
Also logged: chapati-kenyan P8 blowup (plate 45g -> 522 kcal/100g).

Touches ingredient_categories, so rerun:
    python scripts/rederive_diet_compatibility.py
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'meals.json'
BROTH = 'Prepared soups & broths'

DECISIONS: dict[str, dict] = {
    'shchi-russian':     {'action': 'add_category', 'cat': BROTH,
                          'why': 'Russian cabbage SOUP with no liquid category; 394->347 kcal/srv.'},
    'borscht-ukrainian': {'action': 'add_category', 'cat': BROTH,
                          'why': 'Beet soup; matches the batch-1 borscht broth patch; 356->325 kcal/srv.'},
    'fasolada':          {'action': 'add_category', 'cat': BROTH,
                          'why': 'Greek bean SOUP; 443->359 kcal/srv, cal100 126->102 (right for a bean soup).'},
}


def main() -> int:
    data = json.loads(SRC.read_text(encoding='utf-8'))
    by_id = {m['id']: m for m in data}
    counts = {'edited': 0, 'noop': 0, 'missing': 0}

    for mid, d in DECISIONS.items():
        meal = by_id.get(mid)
        if meal is None:
            counts['missing'] += 1
            print(f'  MISSING: {mid}', file=sys.stderr)
            continue
        if d['action'] == 'add_category':
            cats = list(meal.get('ingredient_categories') or [])
            if d['cat'] in cats:
                counts['noop'] += 1
                continue
            cats.append(d['cat'])
            meal['ingredient_categories'] = cats
            counts['edited'] += 1
            print(f'  +{d["cat"]:24s} -> {mid}')

    SRC.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('\ncurated serving-audit batch-3 applied.')
    print(f'  edited:  {counts["edited"]}  noop: {counts["noop"]}  missing: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print('\nNOTE: touched ingredient_categories -> run rederive_diet_compatibility.py')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
