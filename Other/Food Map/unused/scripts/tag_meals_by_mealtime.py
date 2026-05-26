#!/usr/bin/env python3
"""Tag every curated meal with the mealtimes it's commonly eaten at.

Tag vocabulary (matches src/data/schema.js TAGS):
    breakfast — morning meals
    lunch     — midday meals
    dinner    — evening meals
    snack     — between-meals / standalone items (chips, popcorn, jerky,
                drinks; also gets added when the meal is small enough to
                serve only as a snack)
    dessert   — sweet course after a meal

Classification is keyword-driven against `name + notes`:
  1. Drink pattern   → snack  (smoothies / cocktails / tea aren't meals)
  2. Dessert pattern → dessert (no lunch/dinner — desserts are a course
     of their own)
  3. Strict snack pattern → snack
  4. Tapas / appetizer pattern → snack + lunch (substantial-enough-to-eat)
  5. Brunch pattern  → breakfast + lunch
  6. Breakfast pattern → breakfast (no lunch/dinner unless the meal also
     hits a "could-be-eaten-later" cue, see BREAKFAST_BUT_ALSO_LUNCH)
  7. Else            → lunch + dinner (the long tail of main dishes)

Writes a CSV at scripts/tag_meals_report.csv enumerating every meal's
final tag set and which rule fired, so the user can spot-check.

A backup of the pre-tag file is written alongside as
meals.pre-mealtime-tags.json so the run is reversible.
"""
import csv
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR  = REPO_ROOT / 'src' / 'data'

# (meals file, backup file, per-file report). The classifier reads
# only `meal.name`, so every file in this list works without per-file
# branching even though the corpus files have no `notes` field.
TARGETS = [
    (DATA_DIR / 'meals.json',
     DATA_DIR / 'meals.pre-mealtime-tags.json',
     REPO_ROOT / 'scripts' / 'tag_meals_report.csv'),
    (DATA_DIR / 'compositional-meals.json',
     DATA_DIR / 'compositional-meals.pre-mealtime-tags.json',
     REPO_ROOT / 'scripts' / 'tag_compositional_meals_report.csv'),
    (DATA_DIR / 'corpus-titled-meals.json',
     DATA_DIR / 'corpus-titled-meals.pre-mealtime-tags.json',
     REPO_ROOT / 'scripts' / 'tag_corpus_titled_meals_report.csv'),
]

# Pattern lists deliberately use word boundaries to avoid catching
# substrings (e.g. matching "tea" inside "steak").
# Drink-as-meal: ends up tagged "snack" (these aren't proper meals).
#
# `cocktail` deliberately lives outside DRINK_PATTERNS — see
# DRINK_COCKTAIL / NON_DRINK_COCKTAIL below. Treating it as a generic
# drink word catches too many appetizer / salad / mixer names
# ("cocktail meatballs", "shrimp cocktail", "fruit cocktail cake").
DRINK_PATTERNS = [
    r'\b(smoothie|milkshake|shake)\b',
    r'\b(juice|fresh-?pressed juice)\b',
    r'\b(boba|bubble tea|milk tea)\b',
    r'\b(latte|cappuccino|espresso drink|iced coffee|cold brew)\b',
    r'\b(mocktail|highball|martini|margarita|mojito|sangria)\b',
    r'\b(hot chocolate|hot cocoa|egg ?nog)\b',
    r'\b(lassi|horchata|ayran|matcha)\b',
]
# `cocktail` as a noun typically means an alcoholic drink, but it's
# also a productive compound-modifier across appetizers ("cocktail
# meatballs/sauce/wieners") and fruit-salad-style dishes ("fruit
# cocktail [cake|salad]", "shrimp cocktail"). Treat bare `cocktail`
# as a drink UNLESS it forms one of these non-drink compounds.
DRINK_COCKTAIL = re.compile(r'\bcocktails?\b', re.IGNORECASE)
NON_DRINK_COCKTAIL = re.compile(
    r'\b(?:fruit|shrimp|prawn|oyster|seafood|salad)\s+cocktails?\b|'
    r'\bcocktails?\s+(?:meatballs?|sauce|wieners?|sausages?|shrimp|cake|salad|hour|party|recipe|mix)\b',
    re.IGNORECASE,
)
# Items that explicitly are a sweet course. Each pattern is plural-aware
# (`cookies?`, `cakes?`) so "Oatmeal Cookies" / "Strawberry Pies" don't
# fall through to the breakfast / lunch+dinner default.
DESSERT_PATTERNS = [
    r'\b(cakes?|cheesecakes?|cupcakes?)\b',
    r'\b(pies?|tarts?|galettes?|cobblers?|crumbles?)\b',
    r'\b(cookies?|biscotti|brownies?|macarons?|macaroons?|meringues?)\b',
    r'\b(ice creams?|sorbets?|gelatos?|sundaes?|frozen yogurts?|sorbettos?|granitas?)\b',
    r'\b(tiramisus?|panna cotta|custards?|puddings?|mousses?|flans?|cr[eè]me br[uû]l[eé]es?|cr[eè]me caramels?)\b',
    r'\b(souffl[eé]s?|pavlovas?|baklavas?|cannoli|[eé]clairs?|profiteroles?|tres leches)\b',
    r'\b(churros|donuts?|doughnuts?|fritters?)\b',
    r'\b(cand(?:y|ies)|fudge|truffles?|halva|mochi|gulab jamun|jalebi|kulfi|rasgulla|rasmalai)\b',
    r'\b(desserts?)\b',
    r'\b(affogato)\b',
    r'\b(bread puddings?|rice puddings?|sticky toffee puddings?|black forest)\b',
]
# Snack-only patterns (won't tip into lunch/dinner unless other cues fire).
STRICT_SNACK_PATTERNS = [
    r'\b(popcorn|chips and dip|chips ?& ?salsa|chips ?& ?queso|tortilla chips|pretzels?)\b',
    r'\b(jerky|biltong)\b',
    r'\b(edamame|trail mix|granola bars?|fruit cups?)\b',
    r'\b(crackers? and cheese|cheese plate without main|chocolate bars?)\b',
    # Generic "snack" or "snack board" in the meal name — catches
    # "Mediterranean snack board", "Snack mix", etc. without false-
    # positives from notes.
    r'\b(snacks?|crud[ií]t[ée]s?|fruit platters?)\b',
    # "Afternoon tea" / "tea service" / "tea spread" are tea-time
    # snack-style plates; lunch-shaped enough to also tag lunch.
]
# Tapas-style: snack-AND-lunch (small plates that scale to a midday meal).
TAPAS_PATTERNS = [
    r'\b(tapas|antipast[io]s?|mezze|small plates?|finger foods?|hors d.oeuvres?)\b',
    r'\b(charcuterie boards?|cheese boards?)\b',
    r'\b(dim sum)\b',
    r'\b(afternoon tea|tea spread|tea service|high tea)\b',
]
BRUNCH_PATTERNS = [
    r'\b(brunch)\b',
    r'\b(eggs benedict|huevos rancheros)\b',
    # Scandinavian buffet table — typically a late breakfast / lunch
    # spread, so brunch (breakfast + lunch) is the right slot.
    r'\b(sm[öo]rg[åa]sbord)\b',
]
# Breakfast cues. A meal hitting any of these gets `breakfast`. By
# default it does NOT also get lunch/dinner — see overrides below for
# the few breakfast items that often double as lunch.
BREAKFAST_PATTERNS = [
    r'\b(breakfast|morning meal)\b',
    r'\b(pancakes?|waffles?|french toast)\b',
    r'\b(omelet|omelette|frittata|shakshuka|shakshouka)\b',
    r'\b(scrambled eggs?|fried eggs?|poached eggs?|sunny[- ]?side|soft[- ]?boiled eggs?)\b',
    r'\b(granola|muesli|oatmeal|porridge|cereal|congee)\b',
    r'\b(yogurt parfait|acai bowl|smoothie bowl|chia pudding)\b',
    r'\b(bagel|english muffin|scone|croissant|danish)\b',
    r'\b(hash browns?|breakfast burrito|breakfast sandwich)\b',
    r'\b(biscuits? and gravy|sausage gravy)\b',
    r'\b(toast with jam|avocado toast|cinnamon roll|kolache)\b',
    # Specific dishes the generic patterns above don't catch — these
    # are widely recognized breakfast meals whose names don't carry a
    # breakfast token (bacon-and-eggs, Costa Rican gallo pinto, etc.).
    r'\b(bacon and eggs)\b',
    r'\b(gallo pinto)\b',
    r'\b(kedgeree)\b',
]
# Breakfast items that are also legitimately eaten at lunch (heartier
# than a typical breakfast). They get lunch tagged alongside breakfast.
BREAKFAST_BUT_ALSO_LUNCH_PATTERNS = [
    r'\b(breakfast burrito|breakfast sandwich)\b',
    r'\b(huevos rancheros|chilaquiles)\b',
    r'\b(frittata|shakshuka|shakshouka)\b',
    r'\b(croque[- ]?madame|croque[- ]?monsieur)\b',
    r'\b(quiche)\b',
    r'\b(bagel sandwich|breakfast bowl)\b',
]


def matches_any(text, patterns):
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


# Meal NAMES that contain dessert-sounding tokens but are actually
# savory dishes. Matching dessert patterns against the meal name catches
# 99% of real desserts, but a few savory dishes carry dessert words —
# "Shepherd's pie" (savory meat pie), "Quiche" (savory tart with
# custard), "B'stilla" (savory phyllo pie). This regex screens those out
# BEFORE the dessert classifier fires. Patterns are intentionally
# specific so they don't accidentally exclude real desserts.
SAVORY_NAME_OVERRIDES = re.compile(
    r"(shepherd'?s pie|cottage pie|meat pie|pork pie|fish pie|"
    r"chicken pot pie|steak and kidney pie|pot pie|"
    r"sunday roast|toad in the hole|"
    r"quiche|b'?stilla|bobotie|kids'? lunchbox|"
    r"ploughman'?s lunch|kung pao|tteokbokki|satay|fattoush|fesenjan|"
    r"chips ?& ?guacamole|"
    # Savory puddings — Yorkshire (UK roast side), corn (Southern US
    # casserole), noodle (kugel), black / blood (sausage), suet
    # (British savory). Steak-and-kidney pudding is a British meat pie.
    r"\b(?:yorkshire|corn|noodle|black|blood|suet|steak[- ]and[- ]kidney)[- ]puddings?\b|"
    # Savory soufflés — vegetable / cheese / protein-led names. Dessert
    # soufflés (chocolate / lemon / Grand Marnier / raspberry) aren't in
    # this list, so they still classify as dessert via the souffl[eé] token.
    r"\b(?:cheese|broccoli|carrot|spinach|squash|corn|sweet[- ]potato|"
    r"potato|onion|tomato|asparagus|mushroom|cauliflower|leek|"
    r"salmon|crab|lobster|tuna|chicken|ham|bacon|sausage|"
    r"zucchini|pea|breakfast)[- ]souffl[eé]s?\b|"
    # Savory tarts — vegetable / cheese / protein. Sweet tarts
    # (apple / lemon / strawberry) aren't in the modifier list.
    r"\b(?:cheese|veg|vegetable|onion|leek|spinach|mushroom|tomato|"
    r"asparagus|broccoli|pea|bacon|ham|salmon|crab|goat[- ]?cheese|"
    r"feta|gruy[eè]re|parmesan|caramelized[- ]?onion)[- ]tarts?\b|"
    # Savory fritters — vegetable / seafood / cheese. Sweet fritters
    # (apple / banana / pineapple) aren't in the modifier list.
    r"\b(?:corn|crab|salt[- ]?cod|zucchini|potato|fish|"
    r"cheese|cauliflower|spinach|onion|shrimp|clam|conch|chickpea|"
    r"broccoli|squash|pea|carrot|ham|chicken)[- ]fritters?\b)",
    re.IGNORECASE,
)


MEALTIME_TAGS = frozenset({'breakfast', 'lunch', 'dinner', 'snack', 'dessert'})


def is_drink(name):
    """Whether the meal name reads as a drink (smoothie, latte, etc.).

    `cocktail` is treated as a drink by default, but suppressed when the
    name is a known non-drink compound ("cocktail meatballs", "shrimp
    cocktail", "fruit cocktail [cake|salad]"). Names that match another
    drink pattern (e.g. "Sangria cocktail meatballs") still count as
    drinks via that other pattern.
    """
    if matches_any(name, DRINK_PATTERNS):
        return True
    if DRINK_COCKTAIL.search(name) and not NON_DRINK_COCKTAIL.search(name):
        return True
    return False


def classify(meal):
    """Return (tag_set, primary_reason) for the meal.

    Tester feedback: an earlier pass matched dessert / drink keywords
    against the meal's NOTES, which fired false positives for words
    used in non-dessert context ("lime juice" in ceviche notes,
    "fior di latte" in pizza notes, "rice cakes" in tteokbokki notes).
    The fix: classify on the meal NAME only, and use a savory-overrides
    regex to screen out a handful of savory dishes whose names happen
    to contain dessert tokens (Shepherd's pie, Quiche, Sunday roast,
    Yorkshire pudding, Cheese soufflé, Corn fritter, etc.).
    """
    name = meal.get('name') or ''
    tags = set()
    reasons = []

    # Savory-sounding-but-not-dessert short-circuit.
    is_savory_override = bool(SAVORY_NAME_OVERRIDES.search(name))

    if is_drink(name):
        tags.add('snack')
        reasons.append('drink → snack')
        return tags, '; '.join(reasons)

    if not is_savory_override and matches_any(name, DESSERT_PATTERNS):
        tags.add('dessert')
        reasons.append('dessert')
        return tags, '; '.join(reasons)

    if matches_any(name, STRICT_SNACK_PATTERNS):
        tags.add('snack')
        reasons.append('strict snack')
        return tags, '; '.join(reasons)

    if matches_any(name, TAPAS_PATTERNS):
        tags.add('snack')
        tags.add('lunch')
        reasons.append('tapas → snack + lunch')
        return tags, '; '.join(reasons)

    if matches_any(name, BRUNCH_PATTERNS):
        tags.add('breakfast')
        tags.add('lunch')
        reasons.append('brunch → breakfast + lunch')
        return tags, '; '.join(reasons)

    if matches_any(name, BREAKFAST_PATTERNS):
        tags.add('breakfast')
        reasons.append('breakfast')
        if matches_any(name, BREAKFAST_BUT_ALSO_LUNCH_PATTERNS):
            tags.add('lunch')
            reasons.append('also lunch')
        return tags, '; '.join(reasons)

    # Default: a substantive main dish, eat-at-lunch-or-dinner.
    tags.add('lunch')
    tags.add('dinner')
    reasons.append('default main → lunch + dinner')
    return tags, '; '.join(reasons)


def process_file(meals_path: Path, backup_path: Path, report_path: Path):
    meals = json.loads(meals_path.read_text(encoding='utf-8'))
    if not backup_path.exists():
        backup_path.write_text(json.dumps(meals, indent=2), encoding='utf-8')
        print(f'[tag_meals] wrote backup: {backup_path.name}')

    report = []
    summary = {'breakfast': 0, 'lunch': 0, 'dinner': 0, 'snack': 0, 'dessert': 0}
    for meal in meals:
        if not isinstance(meal, dict):
            continue
        new_tags, reason = classify(meal)
        # Strip prior mealtime tags before union so a re-run with
        # updated regex actually un-tags previously-misclassified items.
        # Non-mealtime tags (high-protein, fermented, etc.) are preserved.
        existing = set(meal.get('tags') or []) - MEALTIME_TAGS
        merged = sorted(existing | new_tags)
        meal['tags'] = merged
        for t in new_tags:
            summary[t] = summary.get(t, 0) + 1
        report.append({
            'id':    meal.get('id', ''),
            'name':  meal.get('name', ''),
            'tags':  ','.join(merged),
            'rule':  reason,
        })

    meals_path.write_text(json.dumps(meals, indent=2), encoding='utf-8')

    with report_path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'name', 'tags', 'rule'])
        writer.writeheader()
        writer.writerows(report)

    print(f'[tag_meals] {meals_path.name}: tagged {len(meals)} meals')
    for tag, n in summary.items():
        print(f'  {tag:12s} {n}')
    print(f'[tag_meals] report: {report_path.name}')
    return summary


def main():
    grand = {'breakfast': 0, 'lunch': 0, 'dinner': 0, 'snack': 0, 'dessert': 0}
    for meals_path, backup_path, report_path in TARGETS:
        if not meals_path.exists():
            print(f'[tag_meals] skip: {meals_path} (not found)')
            continue
        s = process_file(meals_path, backup_path, report_path)
        for tag, n in s.items():
            grand[tag] = grand.get(tag, 0) + n

    print('[tag_meals] grand totals across all files:')
    for tag, n in grand.items():
        print(f'  {tag:12s} {n}')


if __name__ == '__main__':
    main()
