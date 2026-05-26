"""Compositional-meals audit batch 1 — entries 0-99 (by index in the source file).

For each ID, the decision is one of:
  - 'drop'                — remove the meal entry entirely.
  - 'edit' with a `patch` dict — merge patch into the meal; lists overwrite,
    scalars overwrite. Patch field `contains_add` appends to contains (de-duped).
  - omitted               — no change.

Re-run scripts/rederive_diet_compatibility.py after this.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'compositional-meals.json'

# Decision table keyed by meal id. Only the listed fields are modified.
DECISIONS: dict[str, dict] = {
    # 000
    'corpus-sliced-apples': {'action': 'drop', 'reason': 'single-ingredient prep, not a meal'},
    # 001
    'corpus-pancakes': {'action': 'edit', 'patch': {
        'name': 'Pancakes',
        'cuisine': 'American',
        'notes': 'Stacked breakfast pancakes from a milk-and-egg batter, cooked golden on a griddle and served with butter and syrup.',
    }},
    # 002
    'corpus-poached-pears': {'action': 'edit', 'patch': {
        'cuisine': 'French',
        'tags': ['dessert'],
        'contains_add': ['alcohol'],
        'notes': 'Whole pears simmered in spiced red wine syrup until tender and stained ruby — a classic French winter dessert.',
    }},
    # 003
    'corpus-fruit-nut-platter': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'notes': 'Sliced fruit and roasted nuts arranged on a board — a light grazing snack.',
    }},
    # 004
    'corpus-buttered-apples': {'action': 'edit', 'patch': {
        'tags': ['dessert', 'snack'],
        'notes': 'Apple slices sautéed in butter with a touch of sugar until softened and caramelized — a quick fruit side or dessert.',
    }},
    # 005
    'corpus-mixed-fruit-salad': {'action': 'edit', 'patch': {
        'ingredient_categories': ['Tropical fruits', 'Citrus', 'Temperate fruits', 'Berries'],
        'tags': ['snack'],
        'notes': 'Diced seasonal fruit tossed together — a light snack or breakfast side.',
    }},
    # 006
    'corpus-berry-peach-bowl': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'serving_grams': 280,
        'notes': 'Mixed berries with sliced peaches and a sprinkle of sugar — a summer fruit bowl.',
    }},
    # 007
    'corpus-almond-cookies': {'action': 'edit', 'patch': {
        'name': 'Almond cookies',
        'notes': 'Buttery shortbread-style cookies enriched with ground or sliced almonds.',
    }},
    # 008
    'corpus-buttered-nuts': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'notes': 'Toasted nuts coated in butter and salt — a savory snack.',
    }},
    # 009
    'corpus-ricotta-with-fruit': {'action': 'edit', 'patch': {
        'tags': ['snack', 'breakfast'],
        'notes': 'A scoop of fresh ricotta topped with sliced fruit — a light breakfast or dessert.',
    }},
    # 010
    'corpus-nut-cake': {'action': 'edit', 'patch': {
        'notes': 'Butter cake folded with chopped nuts for crunch — a sliceable dessert loaf.',
    }},
    # 011
    'corpus-mixed-berries': {'action': 'edit', 'patch': {
        'tags': ['snack', 'breakfast'],
        'notes': 'A bowl of assorted fresh berries — eaten plain as a snack or breakfast topping.',
    }},
    # 012
    'corpus-waldorf-style-salad': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Apple, celery, and walnut salad tossed in a creamy dressing — the classic American Waldorf preparation.',
    }},
    # 013
    'corpus-apple-walnut-butter-saut': {'action': 'edit', 'patch': {
        'notes': 'Apples and walnuts sautéed in butter with sugar — a warm fruit side served over toast or ice cream.',
    }},
    # 014
    'corpus-roasted-vegetables': {'action': 'edit', 'patch': {
        'notes': 'A mix of root and peppers tossed in oil and herbs, roasted until caramelized.',
    }},
    # 015
    'corpus-pound-cake': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Dense butter-and-egg loaf cake named for its equal-weight ratio of pound each of butter, sugar, eggs, and flour.',
    }},
    # 016
    'corpus-shortbread-cookies': {'action': 'edit', 'patch': {
        'cuisine': 'Scottish',
        'notes': 'Buttery crumbly cookies made from three ingredients — butter, sugar, and flour — in roughly a 1:2:3 ratio.',
    }},
    # 017
    'corpus-saut-ed-vegetables': {'action': 'edit', 'patch': {
        'notes': 'Mixed vegetables tossed in a hot pan with oil and seasonings until tender-crisp.',
    }},
    # 018
    'corpus-steamed-vegetable-medley': {'action': 'edit', 'patch': {
        'notes': 'Assorted vegetables steamed until just tender, finished with salt and ground pepper.',
    }},
    # 019
    'corpus-sangria': {'action': 'edit', 'patch': {
        'cuisine': 'Spanish',
        'tags': ['snack'],
        'contains_add': ['alcohol'],
        'notes': 'Spanish red-wine punch with citrus, sliced fruit, sugar, and a splash of soda.',
    }},
    # 020
    'corpus-mulled-apple-wine': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'contains_add': ['alcohol'],
        'notes': 'Red wine warmed with apple, citrus peel, and whole spices — a winter sipping drink.',
    }},
    # 021
    'corpus-beef-vegetables': {'action': 'edit', 'patch': {
        'notes': 'Sliced beef cooked with a medley of vegetables — a stir-fry or skillet supper.',
    }},
    # 022
    'corpus-apple-pancakes-5': {'action': 'edit', 'patch': {
        'name': 'Apple pancakes',
        'cuisine': 'American',
        'notes': 'Pancakes with grated or sliced apple folded into the batter, spiced with cinnamon.',
    }},
    # 023
    'corpus-apple-walnut-muffin': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Cinnamon-spiced muffins studded with apple chunks and chopped walnuts.',
    }},
    # 024
    'corpus-peanut-butter-cookies': {'action': 'edit', 'patch': {
        'name': 'Peanut butter cookies',
        'cuisine': 'American',
        'notes': 'Soft cookies forked in the classic crisscross pattern, made with peanut butter, sugar, and egg.',
    }},
    # 025
    'corpus-fruit-clafoutis': {'action': 'edit', 'patch': {
        'cuisine': 'French',
        'tags': ['dessert'],
        'notes': 'A custard-like baked French dessert with whole fruit suspended in a thin pancake-style batter.',
    }},
    # 026
    'corpus-mixed-nuts': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'notes': 'A blend of roasted nuts eaten as a savory snack.',
    }},
    # 027
    'corpus-berry-sangria': {'action': 'edit', 'patch': {
        'cuisine': 'Spanish',
        'tags': ['snack'],
        'contains_add': ['alcohol'],
        'notes': 'Sangria-style wine punch made with mixed berries and stone fruit.',
    }},
    # 028
    'corpus-nutty-buttered-milk-bread': {'action': 'edit', 'patch': {
        'notes': 'Soft enriched milk-bread studded with nuts, served sliced and buttered.',
    }},
    # 029
    'corpus-nut-shortbread': {'action': 'edit', 'patch': {
        'name': 'Nut shortbread',
        'cuisine': 'Scottish',
        'tags': ['dessert'],
        'notes': 'Buttery shortbread with chopped nuts pressed into the dough.',
    }},
    # 030
    'corpus-roasted-root-medley': {'action': 'edit', 'patch': {
        'notes': 'Carrots, parsnips, and potatoes tossed in oil and herbs, roasted until edges caramelize.',
    }},
    # 031
    'corpus-strawberry-apple-compote': {'action': 'edit', 'patch': {
        'tags': ['dessert', 'snack'],
        'notes': 'Strawberries and apples simmered with butter until softened — spooned over toast, yogurt, or ice cream.',
    }},
    # 032
    'corpus-potato-pancakes': {'action': 'edit', 'patch': {
        'cuisine': 'Eastern European',
        'notes': 'Grated potato bound with egg and flour, fried into crisp pancakes — latkes-style.',
    }},
    # 033
    'corpus-cheesecake': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'A baked custard of cream cheese, eggs, and sugar over a graham-cracker base — the New York-style dessert.',
    }},
    # 034
    'corpus-cheese-charcuterie': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'contains_add': ['pork'],
        'notes': 'A board of sliced cured meats and aged cheeses — the European appetizer staple.',
    }},
    # 035
    'corpus-peanut-butter-oatmeal': {'action': 'edit', 'patch': {
        'name': 'Peanut butter oatmeal',
        'tags': ['breakfast'],
        'notes': 'Hot oats cooked in milk and finished with a swirl of peanut butter and a drizzle of sweetener.',
    }},
    # 036
    'corpus-yogurt-flatbread': {'action': 'edit', 'patch': {
        'notes': 'Soft flatbread made with yogurt in the dough for a tender, slightly tangy crumb.',
    }},
    # 037
    'corpus-greens-potato-salad': {'action': 'edit', 'patch': {
        'notes': 'Boiled potatoes tossed with leafy greens and a vinaigrette-style dressing.',
    }},
    # 038
    'corpus-sweet-potato-fritter': {'action': 'edit', 'patch': {
        'notes': 'Grated or mashed sweet potato bound with egg and flour, fried into crisp spiced fritters.',
    }},
    # 039
    'corpus-apple-egg-pancake': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'A single oven-baked pancake with apple slices set into the egg-rich batter.',
    }},
    # 040
    'corpus-whole-wheat-apple-crisp': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'tags': ['dessert'],
        'notes': 'Sliced apples baked under a buttery whole-wheat oat-and-flour streusel until bubbling.',
    }},
    # 041
    'corpus-cheesy-roasted-veg': {'action': 'edit', 'patch': {
        'notes': 'Roasted vegetables blanketed with grated aged cheese and broiled until melted.',
    }},
    # 042
    'corpus-apple-turnover': {'action': 'edit', 'patch': {
        'tags': ['dessert', 'snack'],
        'notes': 'Folded pastry parcel filled with spiced apple — a hand-held bakery pastry.',
    }},
    # 043
    'corpus-sour-cream-pound-cake': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Tender pound cake enriched with sour cream for extra moisture and a faint tang.',
    }},
    # 044
    'corpus-peanut-milk-oats': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Oats cooked in milk and finished with peanut butter — a stovetop breakfast bowl.',
    }},
    # 045
    'corpus-apple-pecan-cake': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Butter cake with diced apple and chopped pecans folded through — a Southern coffee-cake style.',
    }},
    # 046
    'corpus-nutty-buttered-eggs': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Scrambled eggs cooked in butter and finished with toasted nuts.',
    }},
    # 047
    'corpus-fruit-smoothie': {'action': 'edit', 'patch': {
        'notes': 'Blended fruit, yogurt, and milk — a drinkable breakfast or snack.',
    }},
    # 048
    'corpus-apple-milkshake': {'action': 'edit', 'patch': {
        'tags': ['snack', 'dessert'],
        'notes': 'Blended ice cream, milk, and apple — a sweet diner-style shake.',
    }},
    # 049
    'corpus-apple-egg-butter-dessert': {'action': 'edit', 'patch': {
        'name': 'Apple butter custard',
        'tags': ['dessert'],
        'notes': 'Apples folded into a baked egg-and-butter custard — a homey old-fashioned pudding.',
    }},
    # 050
    'corpus-yorkshire-pudding': {'action': 'edit', 'patch': {
        'cuisine': 'British',
        'notes': 'Egg-and-milk batter baked in hot drippings until puffed — the traditional accompaniment to British roast beef.',
    }},
    # 051
    'corpus-egg-with-milk': {'action': 'edit', 'patch': {
        'name': 'Baked custard',
        'tags': ['dessert'],
        'notes': 'Eggs, milk, sugar, and vanilla baked in a water bath into a set custard.',
    }},
    # 052
    'corpus-peanut-butter-oatmeal-2': {'action': 'edit', 'patch': {
        'notes': 'Plain hot oats stirred with peanut butter and a sweetener — a minimal pantry breakfast.',
    }},
    # 053
    'corpus-whole-wheat-cookies': {'action': 'edit', 'patch': {
        'notes': 'Drop cookies made with whole-wheat flour for a nuttier, denser bite.',
    }},
    # 054
    'corpus-ricotta-plate': {'action': 'drop', 'reason': 'single-category cheese serving, not a coherent meal'},
    # 055
    'corpus-beef-brown-rice': {'action': 'edit', 'patch': {
        'notes': 'Browned beef and vegetables served over brown rice — a hearty grain bowl.',
    }},
    # 056
    'corpus-strawberries-with-cream': {'action': 'edit', 'patch': {
        'tags': ['dessert', 'snack'],
        'notes': 'Fresh strawberries sugared lightly and served with whipped or pouring cream.',
    }},
    # 057
    'corpus-beef-beans': {'action': 'edit', 'patch': {
        'notes': 'Beef simmered with beans and aromatics — chili- or stew-style.',
    }},
    # 058
    'corpus-berry-nut-fruit-bowl': {'action': 'edit', 'patch': {
        'tags': ['snack', 'breakfast'],
        'serving_grams': 280,
        'notes': 'Berries and sliced fruit topped with chopped nuts — a hearty fruit bowl.',
    }},
    # 059
    'corpus-buttered-vegetables': {'action': 'edit', 'patch': {
        'notes': 'Steamed or sautéed vegetables tossed in melted butter — a simple side.',
    }},
    # 060
    'corpus-beef-stir-fry': {'action': 'edit', 'patch': {
        'cuisine': 'Chinese-American',
        'notes': 'Sliced beef and vegetables tossed in a screaming-hot wok with a savory sauce, served over rice.',
    }},
    # 061
    'corpus-bacon-stewed-greens': {'action': 'edit', 'patch': {
        'cuisine': 'Southern American',
        'notes': 'Collards or other tough greens simmered low and slow with bacon, broth, and vinegar.',
    }},
    # 062
    'corpus-buttered-bread': {'action': 'drop', 'reason': 'component, not a coherent meal'},
    # 063
    'corpus-garlic-bread': {'action': 'edit', 'patch': {
        'cuisine': 'Italian-American',
        'notes': 'Crusty bread spread with garlic butter and herbs, often topped with grated cheese and broiled.',
    }},
    # 064
    'corpus-chicken-vegetables': {'action': 'edit', 'patch': {
        'notes': 'Chicken pieces cooked with a mix of vegetables — a skillet or sheet-pan dinner.',
    }},
    # 065
    'corpus-chicken-with-apples': {'action': 'edit', 'patch': {
        'name': 'Chicken with apples',
        'notes': 'Chicken pan-fried or roasted with apple wedges, herbs, and pan jus.',
    }},
    # 066
    'corpus-buttered-nut-bread': {'action': 'edit', 'patch': {
        'notes': 'Slightly sweet nut-studded quick bread, sliced and buttered.',
    }},
    # 067
    'corpus-fruit-cobbler': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'tags': ['dessert'],
        'notes': 'Sweetened fruit baked under a biscuit or batter topping until golden and bubbling.',
    }},
    # 068
    'corpus-buttered-rum': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'tags': ['snack'],
        'contains_add': ['alcohol'],
        'notes': 'Hot buttered rum — dark rum stirred with butter, brown sugar, and hot water or cider.',
    }},
    # 069
    'corpus-beef-greens-salad': {'action': 'edit', 'patch': {
        'notes': 'Sliced steak over leafy greens with a savory-sweet dressing — a steakhouse-style salad.',
    }},
    # 070
    'corpus-carbonara': {'action': 'edit', 'patch': {
        'name': 'Pasta carbonara',
        'cuisine': 'Italian',
        'notes': 'Spaghetti tossed with eggs, pecorino, black pepper, and crispy guanciale — the Roman classic.',
    }},
    # 071
    'corpus-nutty-milk-bread': {'action': 'edit', 'patch': {
        'notes': 'Soft milk-bread loaf with chopped nuts folded into the dough.',
    }},
    # 072
    'corpus-cr-pes-2': {'action': 'edit', 'patch': {
        'name': 'Crêpes',
        'cuisine': 'French',
        'notes': 'Thin French pancakes cooked in butter, folded around sweet or savory fillings.',
    }},
    # 073
    'corpus-cake': {'action': 'edit', 'patch': {
        'name': 'Tropical fruit cake',
        'tags': ['dessert'],
        'notes': 'A simple butter sponge cake with tropical fruit folded in or layered on top.',
    }},
    # 074
    'corpus-vegetable-fritters': {'action': 'edit', 'patch': {
        'tags': ['dinner', 'lunch'],
        'notes': 'Grated mixed vegetables bound with egg and flour, fried into crisp savory fritters.',
    }},
    # 075
    'corpus-zucchini-pancakes': {'action': 'edit', 'patch': {
        'notes': 'Grated zucchini bound with egg, flour, and cheese, pan-fried into savory pancakes.',
    }},
    # 076
    'corpus-oat-cookies-2': {'action': 'edit', 'patch': {
        'name': 'Oatmeal cookies',
        'cuisine': 'American',
        'notes': 'Drop cookies made with rolled oats, brown sugar, and warm spices.',
    }},
    # 077
    'corpus-apple-milk-toast': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Toast topped with warm milk and sliced apple — a nursery-style breakfast.',
    }},
    # 078
    'corpus-sliced-bread': {'action': 'drop', 'reason': 'component, not a coherent meal'},
    # 079
    'corpus-berry-cheese-toast': {'action': 'edit', 'patch': {
        'tags': ['breakfast', 'snack'],
        'notes': 'Toast smeared with fresh cheese and topped with berries — a quick breakfast or snack.',
    }},
    # 080
    'corpus-cr-pes-4': {'action': 'edit', 'patch': {
        'cuisine': 'French',
        'notes': 'Thin French pancakes made from a simple egg-and-flour batter, cooked lacy and folded.',
    }},
    # 081
    'corpus-beef-with-ricotta': {'action': 'edit', 'patch': {
        'notes': 'Braised or simmered beef served with a dollop of fresh ricotta and a tomato or pan sauce.',
    }},
    # 082
    'corpus-buttered-veg-potatoes': {'action': 'edit', 'patch': {
        'notes': 'Boiled potatoes and mixed vegetables tossed in melted butter and seasoning — a hearty side.',
    }},
    # 083
    'corpus-apple-potato-bake': {'action': 'edit', 'patch': {
        'notes': 'Layered apple and potato baked with herbs, oil, and seasoning — a sweet-savory casserole.',
    }},
    # 084
    'corpus-french-custard': {'action': 'edit', 'patch': {
        'cuisine': 'French',
        'notes': 'A simple baked custard of eggs, milk, sugar, and vanilla — the foundation of crème caramel and crème brûlée.',
    }},
    # 085
    'corpus-cheese-nut-plate': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'notes': 'Fresh cheese with mixed nuts and a drizzle of honey — a simple grazing plate.',
    }},
    # 086
    'corpus-berry-fruit-veg-salad': {'action': 'edit', 'patch': {
        'notes': 'Mixed greens and vegetables tossed with berries and sliced fruit in a light dressing.',
    }},
    # 087
    'corpus-egg-cheese-sandwich': {'action': 'edit', 'patch': {
        'tags': ['breakfast', 'lunch'],
        'notes': 'Scrambled or fried egg with melted cheese on toasted bread — the breakfast sandwich.',
    }},
    # 088
    'corpus-nut-meringue': {'action': 'edit', 'patch': {
        'cuisine': 'French',
        'notes': 'Crisp meringues with chopped or ground nuts folded into the whipped whites.',
    }},
    # 089
    'corpus-buttered-brown-rice': {'action': 'edit', 'patch': {
        'notes': 'Steamed brown rice tossed with butter and salt — a plain whole-grain side.',
    }},
    # 090
    'corpus-irish-coffee': {'action': 'edit', 'patch': {
        'cuisine': 'Irish',
        'tags': ['snack'],
        'contains_add': ['alcohol'],
        'notes': 'Hot coffee spiked with Irish whiskey and topped with a float of cream — the Dublin classic.',
    }},
    # 091
    'corpus-caprese-with-veg': {'action': 'edit', 'patch': {
        'cuisine': 'Italian',
        'notes': 'Sliced fresh mozzarella with tomato and basil — the Italian caprese salad, here with extra vegetables.',
    }},
    # 092
    'corpus-sweet-potato-nut-bread': {'action': 'edit', 'patch': {
        'notes': 'Spiced quick bread with mashed sweet potato and chopped nuts folded through the batter.',
    }},
    # 093
    'corpus-bacon-with-ricotta': {'action': 'edit', 'patch': {
        'notes': 'Crisp bacon piled with whipped ricotta on toast or alongside vegetables — a salty-creamy starter.',
    }},
    # 094
    'corpus-cheesy-potato-gratin': {'action': 'edit', 'patch': {
        'name': 'Cheesy potato gratin',
        'cuisine': 'French',
        'notes': 'Sliced potatoes layered with cream and grated cheese, baked until the top is bronzed and the inside silky.',
    }},
    # 095
    'corpus-apple-dumplings': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'tags': ['dessert'],
        'notes': 'Whole apples wrapped in pastry and baked in spiced syrup until tender — a Pennsylvania Dutch classic.',
    }},
    # 096
    'corpus-bacon-beef-salad': {'action': 'edit', 'patch': {
        'notes': 'Steakhouse-style salad of greens with steak and crisp bacon, tossed in a tangy dressing.',
    }},
    # 097
    'corpus-egg-with-potato': {'action': 'edit', 'patch': {
        'name': 'Egg and potato bake',
        'tags': ['breakfast'],
        'notes': 'Baked egg-and-milk custard with diced potato — a savory breakfast strata.',
    }},
    # 098
    'corpus-ricotta-with-apple': {'action': 'edit', 'patch': {
        'tags': ['snack', 'breakfast'],
        'notes': 'Fresh ricotta scooped over sliced apple and topped with chopped nuts — a light breakfast or snack.',
    }},
    # 099
    'corpus-lentil-meat-salad-with-greens': {'action': 'edit', 'patch': {
        'notes': 'Lentils tossed with cured meat, leafy greens, and a tangy dressing — a Mediterranean-leaning bowl.',
    }},
}


def apply_patch(meal: dict, patch: dict) -> None:
    """Merge `patch` into `meal` in-place.

    Special keys:
      contains_add  → appended (de-duped) to the existing `contains` list.
    All other keys overwrite directly.
    """
    contains_add = patch.get('contains_add', [])
    for k, v in patch.items():
        if k == 'contains_add':
            continue
        meal[k] = v
    if contains_add:
        existing = list(meal.get('contains') or [])
        for tag in contains_add:
            if tag not in existing:
                existing.append(tag)
        meal['contains'] = existing


def main() -> int:
    data = json.loads(SRC.read_text(encoding='utf-8'))
    by_id = {m['id']: m for m in data}

    counts = {'edited': 0, 'dropped': 0, 'kept_implicit': 0, 'missing': 0}
    dropped_ids: list[str] = []

    for mid, decision in DECISIONS.items():
        meal = by_id.get(mid)
        if meal is None:
            counts['missing'] += 1
            print(f'  MISSING: {mid}', file=sys.stderr)
            continue
        action = decision['action']
        if action == 'drop':
            dropped_ids.append(mid)
            counts['dropped'] += 1
        elif action == 'edit':
            apply_patch(meal, decision['patch'])
            counts['edited'] += 1
        else:
            counts['kept_implicit'] += 1

    if dropped_ids:
        drop_set = set(dropped_ids)
        data = [m for m in data if m['id'] not in drop_set]

    SRC.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    print('compositional batch-1 audit applied.')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
