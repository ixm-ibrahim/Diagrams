"""Compositional-meals audit batch 4 — next 100 unaudited entries.

Same shape: id → {action, patch?, reason?}.
Re-run scripts/rederive_diet_compatibility.py after this.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'compositional-meals.json'

DECISIONS: dict[str, dict] = {
    'corpus-chicken-cheese-pasta': {'action': 'edit', 'patch': {
        'name': 'Chicken and cheese pasta',
        'notes': 'Sliced chicken tossed with pasta, melted processed cheese, and vegetables.',
    }},
    'corpus-american-cheese-with-broccoli': {'action': 'edit', 'patch': {
        'name': 'American cheese broccoli melt',
        'notes': 'Steamed broccoli on buttered toast topped with melted American cheese.',
    }},
    'corpus-loaded-meat-cheese-melt': {'action': 'edit', 'patch': {
        'notes': 'An open-faced sandwich piled with sliced beef and cured meat under melted processed cheese.',
    }},
    'corpus-berry-nut-snack-mix': {'action': 'edit', 'patch': {
        'notes': 'Dried berries and roasted nuts tossed with a touch of sweetener — a portable trail mix.',
    }},
    'corpus-cheese-toast-with-milk': {'action': 'edit', 'patch': {
        'tags': ['breakfast', 'snack'],
        'notes': 'Toast topped with melted fresh cheese, served with a glass of milk.',
    }},
    'corpus-wine-braised-with-soda': {'action': 'drop', 'reason': 'mixed-beverage stub, not a coherent meal'},
    'corpus-apple-zucchini-walnut-bread': {'action': 'edit', 'patch': {
        'notes': 'Spiced quick bread combining grated zucchini, diced apple, and chopped walnuts.',
    }},
    'corpus-nutty-egg-toast': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Toast topped with scrambled or fried egg and a scatter of toasted chopped nuts.',
    }},
    'corpus-apple-walnut-egg-salad': {'action': 'edit', 'patch': {
        'notes': 'A creamy egg salad with chopped walnuts and diced apple folded in.',
    }},
    'corpus-beef-with-apples-7': {'action': 'edit', 'patch': {
        'notes': 'Sliced beef pan-seared with apple wedges in a savory pan sauce.',
    }},
    'corpus-veg-potato-fritters': {'action': 'edit', 'patch': {
        'notes': 'Grated mixed vegetables and potato bound with egg and flour, fried into crisp savory fritters.',
    }},
    'corpus-milk-stewed-vegetables': {'action': 'edit', 'patch': {
        'notes': 'Mixed vegetables simmered in milk until tender — a Nordic-style braise.',
    }},
    'corpus-white-fish-with-apple-veg': {'action': 'edit', 'patch': {
        'notes': 'A fillet of white fish pan-roasted with apple slices and herb-tossed vegetables.',
    }},
    'corpus-lentil-grain-butter-bowl': {'action': 'edit', 'patch': {
        'notes': 'Lentils and whole grains tossed with butter and a touch of sweetener — a vegetarian bowl.',
    }},
    'corpus-yogurt-raisin-cake': {'action': 'edit', 'patch': {
        'notes': 'A tender butter cake enriched with yogurt and studded with raisins.',
    }},
    'corpus-berry-apple-cheese-toast': {'action': 'edit', 'patch': {
        'name': 'Berry-apple cheese toast',
        'tags': ['breakfast', 'snack'],
        'notes': 'Buttered toast spread with fresh cheese and topped with diced apple and crushed berries.',
    }},
    'corpus-veggie-omelet': {'action': 'edit', 'patch': {
        'notes': 'A folded omelet stuffed with sautéed vegetables and herbs.',
    }},
    'corpus-bacon-mac-cheese': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Macaroni in a cheddar bechamel with diced bacon stirred through and baked until bubbling.',
    }},
    'corpus-apple-date-nut-mix': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'notes': 'A trail mix of dried apple, chopped dates, and roasted nuts.',
    }},
    'corpus-beef-pasta-with-greens-eggs': {'action': 'edit', 'patch': {
        'notes': 'Pasta tossed with ground beef, wilted leafy greens, and a soft-cooked egg.',
    }},
    'corpus-seeded-vegetable-salad': {'action': 'edit', 'patch': {
        'notes': 'A green salad finished with sunflower or pumpkin seeds and a sweet-tangy dressing.',
    }},
    'corpus-apple-bread-pudding': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Bread cubes soaked in a sweet egg-and-milk custard with diced apple and raisins, baked until set.',
    }},
    'corpus-creamy-peanut-cheese': {'action': 'edit', 'patch': {
        'name': 'Peanut-cheese spread',
        'tags': ['snack'],
        'notes': 'A creamy spread of peanut butter, fresh cheese, and milk — eaten with crackers.',
    }},
    'corpus-beef-curry': {'action': 'edit', 'patch': {
        'cuisine': 'Indian',
        'notes': 'Beef chunks simmered in a spiced onion-tomato gravy with peppers and aromatics.',
    }},
    'corpus-chicken-cheese-melt': {'action': 'edit', 'patch': {
        'notes': 'Sliced chicken on bread topped with melted processed cheese and vegetables, broiled.',
    }},
    'corpus-beef-lasagna-2': {'action': 'edit', 'patch': {
        'cuisine': 'Italian-American',
        'notes': 'Layered pasta with ricotta, mozzarella, and a long-simmered beef ragu.',
    }},
    'corpus-beef-lentil-green-salad': {'action': 'edit', 'patch': {
        'notes': 'Seared beef and cooked lentils tossed over leafy greens with a tangy dressing.',
    }},
    'corpus-cheese-biscuit': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'A flaky Southern-style biscuit enriched with grated fresh cheese.',
    }},
    'corpus-apple-walnut-egg-toast': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Toast topped with sautéed apple, scrambled egg, and chopped walnuts.',
    }},
    'corpus-dried-fruit-mix': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'notes': 'A bowl of mixed dried fruit — a sweet pantry snack.',
    }},
    'corpus-american-cheese-with-broccoli-2': {'action': 'edit', 'patch': {
        'name': 'American cheese broccoli melt',
        'notes': 'Steamed broccoli over toast topped with melted American cheese.',
    }},
    'corpus-chicken-with-cheese-sauce': {'action': 'edit', 'patch': {
        'notes': 'Pan-seared chicken finished with a butter-and-aged-cheese pan sauce.',
    }},
    'corpus-apple-cheese-veg-salad': {'action': 'edit', 'patch': {
        'notes': 'Mixed vegetables tossed with diced apple and crumbled fresh cheese in a tangy dressing.',
    }},
    'corpus-bean-stuffed-bread': {'action': 'edit', 'patch': {
        'notes': 'Enriched bread baked around a savory-sweet bean filling.',
    }},
    'corpus-cheese-b-chamel-pasta': {'action': 'edit', 'patch': {
        'name': 'Cheese béchamel pasta',
        'cuisine': 'Italian',
        'notes': 'Pasta tossed in a smooth bechamel of butter, flour, and milk with grated fresh cheese.',
    }},
    'corpus-cheesy-ham-potato-bake': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Sliced potatoes, diced ham, and aged cheese baked in a cream sauce until bubbling.',
    }},
    'corpus-apple-cheese-pancakes': {'action': 'edit', 'patch': {
        'notes': 'Pancakes with fresh cheese and grated apple folded into the batter.',
    }},
    'corpus-white-wine-clams': {'action': 'edit', 'patch': {
        'cuisine': 'Italian',
        'contains_add': ['alcohol'],
        'notes': 'Clams steamed open in white wine with garlic, herbs, and chili — vongole-style.',
    }},
    'corpus-bacon-grain-bowl': {'action': 'edit', 'patch': {
        'notes': 'Whole-grain bowl topped with crisp bacon and seasoned vegetables.',
    }},
    'corpus-ham-pasta-bake': {'action': 'edit', 'patch': {
        'notes': 'Pasta baked with diced ham, vegetables, and a fresh-cheese sauce.',
    }},
    'corpus-berry-apple-walnut-cake': {'action': 'edit', 'patch': {
        'notes': 'Butter cake with diced apple, fresh berries, and chopped walnuts folded in.',
    }},
    'corpus-milky-yogurt-drink': {'action': 'edit', 'patch': {
        'name': 'Yogurt milk drink',
        'cuisine': 'South Asian',
        'tags': ['snack'],
        'notes': 'Yogurt thinned with milk — the base for lassi and similar yogurt drinks.',
    }},
    'corpus-peanut-butter-oat-cookies': {'action': 'edit', 'patch': {
        'notes': 'Drop cookies bound with peanut butter and rolled oats — chewy and rich.',
    }},
    'corpus-apple-nut-bread': {'action': 'edit', 'patch': {
        'notes': 'A simple quick bread with diced apple and chopped nuts in the batter.',
    }},
    'corpus-roast-beef-sub': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Thinly sliced roast beef in a sub roll with cheese, lettuce, and a horseradish-mayo sauce.',
    }},
    'corpus-fruit-nut-bread': {'action': 'edit', 'patch': {
        'notes': 'A bread loaf with dried and fresh fruit plus chopped nuts folded into the dough.',
    }},
    'corpus-saut-ed-greens': {'action': 'edit', 'patch': {
        'name': 'Sautéed greens',
        'notes': 'Leafy greens wilted quickly in a hot pan with garlic and a splash of sauce.',
    }},
    'corpus-green-salad': {'action': 'edit', 'patch': {
        'notes': 'Mixed lettuces and raw vegetables tossed with citrus and tropical fruit — an unusual fruit-leaning salad.',
    }},
    'corpus-creamy-oatmeal': {'action': 'edit', 'patch': {
        'notes': 'Oats simmered in milk and finished with butter and a touch of vanilla — a stovetop breakfast.',
    }},
    'corpus-apple-cheese-pasta': {'action': 'edit', 'patch': {
        'notes': 'Pasta tossed with diced apple, aged cheese, herbs, and a touch of oil.',
    }},
    'corpus-bean-nut-salad': {'action': 'edit', 'patch': {
        'notes': 'Mixed beans tossed with toasted nuts and a sweet-tangy dressing.',
    }},
    'corpus-sour-cream-apple-nut-muffins': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Tender muffins with sour cream, diced apple, and chopped nuts.',
    }},
    'corpus-seeded-chicken-sandwich': {'action': 'edit', 'patch': {
        'notes': 'Chicken on a seeded bread roll spread with butter.',
    }},
    'corpus-walnut-with-milk': {'action': 'edit', 'patch': {
        'name': 'Walnut milk pudding',
        'tags': ['dessert'],
        'notes': 'Ground walnuts simmered in sweetened milk with flour into a thickened pudding.',
    }},
    'corpus-apple-bread': {'action': 'edit', 'patch': {
        'notes': 'A spiced quick bread with diced apple folded into the batter.',
    }},
    'corpus-fruit-toast': {'action': 'edit', 'patch': {
        'tags': ['breakfast', 'snack'],
        'notes': 'Toast topped with sliced fresh fruit — a simple light breakfast.',
    }},
    'corpus-cheesy-buttered-potatoes': {'action': 'edit', 'patch': {
        'notes': 'Boiled potatoes mashed with butter and processed cheese — a kid-friendly side.',
    }},
    'corpus-apple-yogurt-smoothie': {'action': 'edit', 'patch': {
        'notes': 'Apple, yogurt, and milk blended into a creamy drinkable smoothie.',
    }},
    'corpus-beef-bean-curry-with-potatoes': {'action': 'edit', 'patch': {
        'cuisine': 'Indian',
        'notes': 'Beef chunks and beans simmered in a spiced curry gravy with potatoes.',
    }},
    'corpus-nut-crust-cheesecake': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Baked cream-cheese cheesecake on a buttery crushed-nut crust.',
    }},
    'corpus-beef-pasta-bake': {'action': 'edit', 'patch': {
        'name': 'Beef pasta bake with cheddar',
        'cuisine': 'American',
        'notes': 'Pasta tossed with seasoned ground beef and a tomato sauce, baked under shredded cheddar.',
    }},
    'corpus-cheesy-chicken-potatoes': {'action': 'edit', 'patch': {
        'notes': 'Chicken and potatoes baked together with processed cheese melted across the top.',
    }},
    'corpus-loaded-sub-sandwich': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'A long sub roll loaded with cured meat, cheese, lettuce, and vegetables in a creamy sauce.',
    }},
    'corpus-veg-stuffed-bread': {'action': 'edit', 'patch': {
        'notes': 'Enriched bread baked around a buttered vegetable filling.',
    }},
    'corpus-cheesy-scrambled-eggs': {'action': 'edit', 'patch': {
        'notes': 'Soft scrambled eggs with fresh cheese melted through.',
    }},
    'corpus-apple-buttered-oatmeal': {'action': 'edit', 'patch': {
        'notes': 'Oats cooked with diced apple, butter, and brown sugar.',
    }},
    'corpus-african-peanut-stew': {'action': 'edit', 'patch': {
        'cuisine': 'West African',
        'notes': 'Vegetables and legumes simmered in a peanut-butter and tomato broth — West African maafe-style.',
    }},
    'corpus-berry-yogurt': {'action': 'edit', 'patch': {
        'tags': ['breakfast', 'snack'],
        'notes': 'Yogurt with fresh berries and a touch of sweetener.',
    }},
    'corpus-cheese-nut-salad': {'action': 'edit', 'patch': {
        'notes': 'Mixed greens with aged cheese, toasted nuts, and a herb vinaigrette.',
    }},
    'corpus-apple-peanut-salad': {'action': 'edit', 'patch': {
        'notes': 'Mixed vegetables and diced apple tossed with a peanut-butter-and-spice dressing.',
    }},
    'corpus-liver-p-t-with-cheese': {'action': 'edit', 'patch': {
        'name': 'Liver pâté with cheese',
        'cuisine': 'French',
        'tags': ['snack'],
        'notes': 'A spreadable liver pâté plated with aged cheese — a charcuterie-board starter.',
    }},
    'corpus-two-cheese-plate': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'notes': 'A cheese plate with both aged and fresh cheeses and a small condiment.',
    }},
    'corpus-breaded-chicken': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Chicken cutlets dredged in seasoned flour and pan-fried until crisp.',
    }},
    'corpus-apple-walnut-shortcake': {'action': 'edit', 'patch': {
        'tags': ['dessert'],
        'notes': 'A buttery shortbread base topped with sautéed apple and toasted walnuts.',
    }},
    'corpus-chicken-grain-bowl': {'action': 'edit', 'patch': {
        'notes': 'A whole-grain bowl topped with seasoned chicken — minimalist meal-prep.',
    }},
    'corpus-spiced-apple-veg': {'action': 'edit', 'patch': {
        'notes': 'Mixed vegetables and apple cooked with warm spices and a touch of sauce.',
    }},
    'corpus-yogurt-nut-muffins': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Muffins with yogurt for tenderness and chopped nuts in the batter.',
    }},
    'corpus-chicken-with-bacon': {'action': 'edit', 'patch': {
        'notes': 'Chicken pan-roasted with crisp bacon, vegetables, and grain on the side.',
    }},
    'corpus-chicken-cheese-grain-bake': {'action': 'edit', 'patch': {
        'notes': 'A whole-grain casserole with chicken, vegetables, and aged cheese baked together.',
    }},
    'corpus-loaded-ham-cheese-bake': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Diced ham and vegetables baked under a blanket of fresh and aged cheese.',
    }},
    'corpus-beef-stew-with-greens': {'action': 'edit', 'patch': {
        'notes': 'A long-simmered beef stew with vegetables and a tangle of wilted greens.',
    }},
    'corpus-pickle-salad': {'action': 'edit', 'patch': {
        'notes': 'A cool salad of pickled and raw vegetables in a sweet-sour dressing.',
    }},
    'corpus-apple-bourbon-custard': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'contains_add': ['alcohol'],
        'notes': 'A baked egg-yolk custard with sautéed apple and a slug of bourbon stirred in.',
    }},
    'corpus-raisin-oatmeal': {'action': 'edit', 'patch': {
        'notes': 'Oats cooked in milk with raisins and warm spices — a basic breakfast bowl.',
    }},
    'corpus-whole-wheat-pancakes-5': {'action': 'edit', 'patch': {
        'name': 'Whole-wheat pancakes',
        'notes': 'Pancakes made with whole-wheat flour for a heartier, nuttier crumb.',
    }},
    'corpus-bean-potato-stew': {'action': 'edit', 'patch': {
        'notes': 'A stew of beans and potatoes simmered with vegetables in a spiced tomato sauce.',
    }},
    'corpus-spiked-hot-cocoa': {'action': 'edit', 'patch': {
        'contains_add': ['alcohol'],
        'notes': 'Hot cocoa enriched with cream and butter and spiked with a shot of rum or whiskey.',
    }},
    'corpus-coffee-custard': {'action': 'edit', 'patch': {
        'cuisine': 'Italian',
        'notes': 'A baked custard infused with strong coffee — like a coffee panna cotta.',
    }},
    'corpus-cheesy-potato-gratin-8': {'action': 'edit', 'patch': {
        'name': 'Cheesy potato gratin',
        'cuisine': 'French',
        'notes': 'Sliced potatoes baked in a flour-thickened milk bechamel with grated aged cheese.',
    }},
    'corpus-date-nut-snack': {'action': 'edit', 'patch': {
        'notes': 'Pitted dates stuffed with whole nuts — a no-cook bite-sized snack.',
    }},
    'corpus-loaded-cheesy-beef-bake': {'action': 'edit', 'patch': {
        'notes': 'A casserole of ground beef, vegetables, and chopped nuts baked under a creamy cheese sauce.',
    }},
    'corpus-chicken-fritters': {'action': 'edit', 'patch': {
        'notes': 'Shredded chicken bound with flour and herbs, fried into crisp savory fritters.',
    }},
    'corpus-chicken-broccoli-grain-bowl-3': {'action': 'edit', 'patch': {
        'name': 'Buttered chicken-broccoli grain bowl',
        'notes': 'Whole-grain bowl with chicken, broccoli, and vegetables tossed in melted butter.',
    }},
    'corpus-cheese-pasta': {'action': 'edit', 'patch': {
        'notes': 'Pasta tossed with fresh cheese and a simple pan sauce — a plain weeknight bowl.',
    }},
    'corpus-beef-apple-salad': {'action': 'edit', 'patch': {
        'notes': 'Sliced beef and apple over leafy greens with a tangy mustard vinaigrette.',
    }},
    'corpus-beef-cheese-pasta-4': {'action': 'edit', 'patch': {
        'name': 'Beef and cheese pasta',
        'cuisine': 'Italian-American',
        'notes': 'Pasta tossed with ground beef and a tomato sauce, finished with fresh cheese.',
    }},
    'corpus-beef-cheese-roll': {'action': 'edit', 'patch': {
        'notes': 'Sliced beef rolled around fresh cheese and vegetables, finished with butter and spices.',
    }},
    'corpus-apple-with-peanut-butter': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'notes': 'Apple slices dipped in peanut butter — the classic after-school snack.',
    }},
    'corpus-chicken-cheese-grain-bowl': {'action': 'edit', 'patch': {
        'notes': 'A whole-grain bowl with chicken and vegetables finished with grated aged cheese.',
    }},
    'corpus-oatmeal': {'action': 'edit', 'patch': {
        'notes': 'Rolled oats simmered in milk with a touch of sweetener and spice — the basic stovetop oatmeal.',
    }},
}


def apply_patch(meal: dict, patch: dict) -> None:
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

    counts = {'edited': 0, 'dropped': 0, 'missing': 0}
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

    if dropped_ids:
        drop_set = set(dropped_ids)
        data = [m for m in data if m['id'] not in drop_set]

    SRC.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    print('compositional batch-4 audit applied.')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
