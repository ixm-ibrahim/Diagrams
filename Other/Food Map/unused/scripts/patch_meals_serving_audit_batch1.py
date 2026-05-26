"""Curated meals serving-audit — batch 1 (meals 0-149 by frequency).

The batch-1 (calibration) pass found that almost all curated serving_grams
are sensible; the real signal is per-100g DENSITY, driven by category
composition. Most density gaps are systemic and logged in
_serving_audit_patterns.md (fried-oil absorption, soft-tofu density,
cream-cheese desserts, dry-grain hydration) — those can't be fixed with a
serving_grams tweak and are deliberately NOT patched here pending the
architecture decision.

The one clear, honest, per-meal fix this batch: brothy soups/stews that are
genuinely mostly liquid but lack a 'Prepared soups & broths' category, so the
plate model averages only their dense solids and over-reads calories +
protein. Adding the broth category (which sibling dishes like shoyu/tonkotsu
ramen already carry) supplies the liquid mass and brings both per-100g and
per-serving readings in line. See pattern P5 in the log.

Touches ingredient_categories, so rerun:
    python scripts/rederive_diet_compatibility.py
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'meals.json'

BROTH = 'Prepared soups & broths'

# id -> {action, patch}. Mirrors the content-audit decision-table shape.
DECISIONS: dict[str, dict] = {
    'ramen-miso':      {'action': 'add_category', 'cat': BROTH,
                        'why': 'Siblings shoyu/tonkotsu already carry broth; miso omitted it (909->643 kcal, 67->43g protein).'},
    'kimchi-jjigae':   {'action': 'add_category', 'cat': BROTH,
                        'why': 'Jjigae is a broth stew; was reading 685 kcal/69g protein on solids-only plate (->495/43).'},
    'sundubu-jjigae':  {'action': 'add_category', 'cat': BROTH,
                        'why': 'Soft-tofu broth stew; 852->571 kcal. Residual protein over-read is the Soy-products density issue (logged P6).'},
    'shabu-shabu':     {'action': 'add_category', 'cat': BROTH,
                        'why': 'Cooked in dashi/water broth; 719->530 kcal, 78->49g protein.'},
    'borscht':         {'action': 'add_category', 'cat': BROTH,
                        'why': 'Beet broth soup with no liquid category; 323->292 kcal, closer to a real 300g bowl.'},
    'bouillabaisse':   {'action': 'add_category', 'cat': BROTH,
                        'why': 'Provencal fish broth/stew; had Bread but no broth; 567->493 kcal.'},
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
    print('\ncurated serving-audit batch-1 applied.')
    print(f'  edited:  {counts["edited"]}')
    print(f'  noop:    {counts["noop"]}')
    print(f'  missing: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print('\nNOTE: touched ingredient_categories -> run rederive_diet_compatibility.py')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
