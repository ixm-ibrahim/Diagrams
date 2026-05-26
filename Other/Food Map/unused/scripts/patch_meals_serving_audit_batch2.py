"""Curated meals serving-audit — batch 2 (meals 150-299 by frequency).

Same verdict as batch 1: serving_grams are broadly sensible; the signal is
per-100g density from category composition. The one clean, honest, per-meal
fix is again P5 — genuinely brothy soups lacking a 'Prepared soups & broths'
category. Batch 2 also surfaced P8 (sparse dense-category small plates that
blow up when serving_grams >> plate_grams: arepas, tahdig, vatapa, fesenjan)
— those are NOT serving-fixable and are logged for the architecture decision.

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
    'mloukhia':    {'action': 'add_category', 'cat': BROTH,
                    'why': 'Egyptian jute-leaf soup served soupy over rice; solids-only plate read 789 kcal/57g protein (->423/27).'},
    'harira':      {'action': 'add_category', 'cat': BROTH,
                    'why': 'Moroccan chickpea-lentil-tomato SOUP with no liquid category; 471->405 kcal.'},
    'ash-reshteh': {'action': 'add_category', 'cat': BROTH,
                    'why': "Iranian noodle-bean ash (ash = soup); thick but liquid-based; 520->416 kcal."},
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
    print('\ncurated serving-audit batch-2 applied.')
    print(f'  edited:  {counts["edited"]}  noop: {counts["noop"]}  missing: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print('\nNOTE: touched ingredient_categories -> run rederive_diet_compatibility.py')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
