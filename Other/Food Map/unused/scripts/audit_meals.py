#!/usr/bin/env python3
"""Conservative audit + automated fixes for src/data/meals.json (curated set).

Goal: a tester reported "Fats & oils doesn't show up at all in meals — that
seems unrealistic". Many curated meals indeed omit common categories that
the meal name or notes obviously imply (grilled / fried / buttery / spiced).
This script walks the curated meals and adds high-confidence categories
based on textual keywords, leaving low-confidence cases for the audit
report so the user can review them manually.

Two-pass design:
  1. APPLY pass — keyword → required-category mappings the script is
     confident about. Only adds when the category is missing.
  2. REPORT pass — softer signals get flagged in a CSV the user can
     review. Nothing is changed for soft signals.

A backup of the pre-audit file is written alongside (meals.pre-audit.json
already exists for an earlier pass; we write .pre-batch5-audit.json so the
prior backup isn't overwritten).

This script does NOT touch compositional-meals.json or corpus-titled-
meals.json — those are algorithmically generated from the corpus and
carry richer category lists already.
"""
import csv
import json
import re
from pathlib import Path

REPO_ROOT       = Path(__file__).resolve().parents[1]
MEALS_PATH      = REPO_ROOT / 'src' / 'data' / 'meals.json'
INGREDIENTS_PATH = REPO_ROOT / 'src' / 'data' / 'ingredients.json'
BACKUP_PATH     = REPO_ROOT / 'src' / 'data' / 'meals.pre-batch5-audit.json'
REPORT_PATH     = REPO_ROOT / 'scripts' / 'audit_meals_report.csv'

# Built once at startup from ingredients.json — guards against rule
# entries pointing at non-existent categories (early version of this
# script tried to add "Pasta & noodles" which never existed; pasta sits
# under "Refined grains"). Any rule whose target isn't in this set raises
# at script start rather than silently writing junk data.
VALID_CATEGORIES = set()

# (keyword pattern, [categories to ensure present]) — these are applied
# when the keyword is found in name + notes (case-insensitive). The
# category list is conservative — only categories a reasonable cook
# would expect for that technique.
HIGH_CONFIDENCE_RULES = [
    # Cooking techniques that essentially require oil.
    (r'\b(deep[- ]?fry|deep[- ]?fried|tempura|battered)\b', ['Oils', 'Flours']),
    (r'\b(stir[- ]?fr(y|ied|ies)|pan[- ]?fr(y|ied|ies)|fry|fried|saut[eé]ed?)\b', ['Oils']),
    (r'\b(roasted?|grill(ed)?|seared)\b', ['Oils']),
    # Explicit oil mentions — common in notes that describe a finishing
    # drizzle or specific oil. Restricted to named oils so we don't
    # match "boiled" or "spoil" via a bare \boil\b.
    (r'\b(olive oil|sesame oil|coconut oil|vegetable oil|peanut oil|canola oil|chili oil|truffle oil|drizzle of oil|drizzled with oil|splash of oil)\b',
        ['Oils']),
    # Buttery / cream techniques.
    (r'\b(buttery|butter[- ]?fried|butter[- ]?braised|brown(ed)? butter)\b', ['Cream & butter']),
    (r'\b(creamy|cream sauce|cream-based|in cream|with cream\b)\b', ['Cream & butter']),
    # Wine-based dishes.
    (r'\b(wine[- ]?braised|wine sauce|braised in (red |white )?wine|coq au vin|bourguignon|marsala)\b',
        ['Alcoholic beverages']),
    # Cheese explicit.
    (r'\b(cheesy|cheese[- ]?topped|cheese[- ]?stuffed|gratin(e|ée|ed)?|au gratin|parmigian[oa])\b',
        ['Aged cheese']),
    # Honey / syrup glazes.
    (r'\b(honey[- ]?(glazed|drizzled)|maple[- ]?syrup|sweet glaze)\b', ['Sugar & sweeteners']),
    # Chocolate.
    (r'\b(chocolate|cocoa|chocolat[ée]?)\b', ['Candy & desserts']),
    # Rice mentions (when not already a rice meal).
    (r'\b(jasmine rice|basmati rice|long[- ]?grain rice|white rice|fluffy rice)\b', ['Refined grains']),
    (r'\b(brown rice|wild rice|whole[- ]?grain rice)\b', ['Whole grains']),
    # Pasta. The dataset puts pasta/noodles under "Refined grains"
    # (whole-wheat pasta sits in Whole grains, but Refined is the
    # safer default for a meal-level add since the regex matches the
    # generic mention). There's no separate "Pasta & noodles" category
    # in ingredients.json despite the name.
    (r'\b(pasta|spaghetti|noodles?|fettuccine|penne|rigatoni|linguine|lasagn[ae])\b', ['Refined grains']),
    # Bread (deliberately specific tokens — generic "bun" / "roll"
    # picked up too many non-English false positives from meal names).
    (r'\b(crusty bread|baguette|focaccia|naan|pita|tortilla|toast points?|served with bread|on toast|sandwich|wrap)\b',
        ['Bread & rolls']),
    # Citrus explicit.
    (r'\b(lemon|lemon[- ]?juice|lemon[- ]?zest|lime|orange peel|orange juice)\b', ['Citrus']),
    # Spices.
    (r'\b(curry|masala|garam masala|curry powder|chili powder|cayenne|paprika|cumin|coriander|turmeric)\b',
        ['Ground spices']),
    # Herbs (fresh).
    (r'\b(fresh herbs|fresh basil|fresh cilantro|fresh parsley|chiffonade|garnish(ed)? with herbs|sprigs?)\b',
        ['Fresh herbs']),
    # Herbs (dried).
    (r'\b(dried oregano|italian herb seasoning|herbes de provence|dried thyme|dried basil)\b',
        ['Dried herbs']),
    # Garlic.
    (r'\b(garlic|garlicky)\b', ['Other vegetables']),
    # Eggs (when not already present).
    (r'\b(scrambled eggs?|fried eggs?|poached eggs?|egg yolks?|egg whites?|whisked eggs?)\b', ['Eggs']),
    # Soy sauce / fish sauce.
    (r'\b(soy sauce|tamari|fish sauce|oyster sauce|hoisin)\b', ['Sauces']),
]

# Soft signals: flagged but not applied. These hint at categories that
# MIGHT belong but aren't certain enough to change without review.
SOFT_RULES = [
    (r'\b(salty|brined|cured)\b',                       ['Salt & seasonings']),
    (r'\b(picked herbs?|herb[- ]?oil)\b',               ['Fresh herbs']),
    (r'\b(yogurt|yoghurt)\b',                            ['Yogurt']),
    (r'\b(milk)\b',                                      ['Milk']),
    (r'\b(beans|lentils|chickpeas)\b',                  ['Legumes']),
    (r'\b(mushrooms?)\b',                                ['Mushrooms']),
    (r'\b(tomato(es)?)\b',                               ['Peppers & nightshades']),
    (r'\b(onion(s)?|shallots?)\b',                       ['Other vegetables']),
    (r'\b(sugar|caramelized|caramelised)\b',             ['Sugar & sweeteners']),
]


def search_keyword(text, pattern):
    return bool(re.search(pattern, text, re.IGNORECASE))


def haystack(meal):
    """Only match against `notes` — meal names often contain non-English
    words that collide with our English regex tokens (Vietnamese "bun"
    matched the bread pattern's `(bun)` and added Bread & rolls to
    Bun bo Hue, which is wrong). Notes are written in English and
    describe the dish directly, so they're a safer source of truth.

    Notes are also where a curator would describe the actual cooking
    technique and accompaniments (drizzle of oil, served with bread),
    so this scoping doesn't lose much signal."""
    return meal.get('notes', '') or ''


def apply_high_confidence(meal):
    """Mutates `meal['ingredient_categories']`, returns list of added cats."""
    text = haystack(meal)
    present = set(meal.get('ingredient_categories') or [])
    added = []
    for pattern, cats in HIGH_CONFIDENCE_RULES:
        if not search_keyword(text, pattern):
            continue
        for cat in cats:
            if cat not in present:
                meal.setdefault('ingredient_categories', []).append(cat)
                present.add(cat)
                added.append((pattern, cat))
    return added


def collect_soft_flags(meal):
    """Returns list of (pattern, category) suggestions worth reviewing."""
    text = haystack(meal)
    present = set(meal.get('ingredient_categories') or [])
    flags = []
    for pattern, cats in SOFT_RULES:
        if not search_keyword(text, pattern):
            continue
        for cat in cats:
            if cat not in present:
                flags.append((pattern, cat))
    return flags


def main():
    # Pre-flight: validate every rule's target category exists in the
    # ingredients dataset. Catches typos / renamed-category drift
    # before they corrupt meals.json.
    ings = json.loads(INGREDIENTS_PATH.read_text(encoding='utf-8'))
    VALID_CATEGORIES.update({ing['category'] for ing in ings if ing.get('category')})
    invalid = set()
    for _, cats in HIGH_CONFIDENCE_RULES + SOFT_RULES:
        for cat in cats:
            if cat not in VALID_CATEGORIES:
                invalid.add(cat)
    if invalid:
        raise SystemExit(
            f'[audit_meals] FATAL: rules reference unknown categories: '
            f'{sorted(invalid)}'
        )

    meals = json.loads(MEALS_PATH.read_text(encoding='utf-8'))
    if not BACKUP_PATH.exists():
        BACKUP_PATH.write_text(json.dumps(meals, indent=2), encoding='utf-8')
        print(f'[audit_meals] wrote backup: {BACKUP_PATH.name}')

    changed_meals = 0
    total_additions = 0
    report_rows = []
    for meal in meals:
        if not isinstance(meal, dict):
            continue
        added = apply_high_confidence(meal)
        if added:
            changed_meals += 1
            total_additions += len(added)
            for pattern, cat in added:
                report_rows.append({
                    'kind': 'applied',
                    'id': meal.get('id', ''),
                    'name': meal.get('name', ''),
                    'pattern': pattern,
                    'category': cat,
                })
        for pattern, cat in collect_soft_flags(meal):
            report_rows.append({
                'kind': 'review',
                'id': meal.get('id', ''),
                'name': meal.get('name', ''),
                'pattern': pattern,
                'category': cat,
            })

    MEALS_PATH.write_text(json.dumps(meals, indent=2), encoding='utf-8')

    # Sort applied first, then review entries.
    report_rows.sort(key=lambda r: (r['kind'] != 'applied', r['name']))
    with REPORT_PATH.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['kind', 'id', 'name', 'pattern', 'category'])
        writer.writeheader()
        writer.writerows(report_rows)

    applied_count = sum(1 for r in report_rows if r['kind'] == 'applied')
    review_count  = sum(1 for r in report_rows if r['kind'] == 'review')
    print(f'[audit_meals] meals touched: {changed_meals}/{len(meals)}')
    print(f'[audit_meals] high-confidence additions: {applied_count}')
    print(f'[audit_meals] soft flags for review:     {review_count}')
    print(f'[audit_meals] report written: {REPORT_PATH}')


if __name__ == '__main__':
    main()
