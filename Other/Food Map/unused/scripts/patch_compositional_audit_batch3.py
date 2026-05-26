"""Compositional-meals audit batch 3 — next 150 unaudited entries.

These were the top-frequency unaudited patterns after batch 2 (freq ~492 → ~153).
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
    'corpus-peanut-butter-milkshake': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'tags': ['snack', 'dessert'],
        'notes': 'Vanilla ice cream blended with milk and a heavy scoop of peanut butter.',
    }},
    'corpus-berry-pancakes': {'action': 'edit', 'patch': {
        'name': 'Berry pancakes',
        'notes': 'Buttermilk pancakes with fresh berries dropped onto the batter as it cooks.',
    }},
    'corpus-egg-cheese-apple-sandwich': {'action': 'edit', 'patch': {
        'tags': ['breakfast', 'lunch'],
        'notes': 'A breakfast sandwich layering egg, melted fresh cheese, and sliced apple on bread.',
    }},
    'corpus-broccoli-grain-bowl': {'action': 'edit', 'patch': {
        'notes': 'Whole-grain bowl topped with steamed broccoli, mixed vegetables, and a drizzle of butter.',
    }},
    'corpus-beef-cheesy-potatoes': {'action': 'edit', 'patch': {
        'notes': 'Browned ground beef over diced potatoes baked under a blanket of processed cheese.',
    }},
    'corpus-bloody-mary': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'tags': ['snack'],
        'contains_add': ['alcohol'],
        'notes': 'Vodka stirred with tomato juice, citrus, hot sauce, and seasonings — the brunch cocktail.',
    }},
    'corpus-chicken-sandwich': {'action': 'edit', 'patch': {
        'name': 'Chicken sandwich',
        'notes': 'Sliced or shredded chicken in a buttered bun — a diner-style lunch sandwich.',
    }},
    'corpus-mimosa': {'action': 'edit', 'patch': {
        'cuisine': 'French',
        'tags': ['breakfast', 'snack'],
        'contains_add': ['alcohol'],
        'notes': 'Sparkling wine topped with chilled orange juice — the classic brunch drink.',
    }},
    'corpus-berry-ricotta-dessert': {'action': 'edit', 'patch': {
        'notes': 'Sweetened whipped ricotta with macerated berries and a touch of vanilla — a light dessert spoon.',
    }},
    'corpus-potato-gratin': {'action': 'edit', 'patch': {
        'cuisine': 'French',
        'notes': 'Sliced potatoes baked in cream with garlic and grated aged cheese — French gratin dauphinois.',
    }},
    'corpus-date-walnut-apple-cake': {'action': 'edit', 'patch': {
        'notes': 'A spiced butter cake folded with chopped dates, walnuts, and diced apple.',
    }},
    'corpus-nutty-french-toast-filling': {'action': 'edit', 'patch': {
        'name': 'Nut-stuffed French toast',
        'notes': 'French toast filled with a sweet nut-and-butter paste.',
    }},
    'corpus-lentil-peanut-stew': {'action': 'edit', 'patch': {
        'cuisine': 'West African',
        'notes': 'Lentils simmered in a peanut-butter broth with a touch of sweetness — a West-African-leaning stew.',
    }},
    'corpus-bacon-cheese-veg-bake': {'action': 'edit', 'patch': {
        'notes': 'Mixed vegetables baked with crisp bacon and a blanket of melted aged cheese.',
    }},
    'corpus-berry-cheese-plate': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'notes': 'Fresh ricotta or other soft cheese plated with mixed berries — a light starter or snack.',
    }},
    'corpus-yogurt-with-apples': {'action': 'edit', 'patch': {
        'tags': ['breakfast', 'snack'],
        'notes': 'A bowl of yogurt with diced apple — a no-cook breakfast.',
    }},
    'corpus-chicken-brown-rice-bowl': {'action': 'edit', 'patch': {
        'notes': 'Steamed brown rice topped with seasoned chicken and vegetables.',
    }},
    'corpus-peanut-cheese-milk-toast': {'action': 'edit', 'patch': {
        'name': 'Peanut butter and cheese toast',
        'tags': ['breakfast', 'snack'],
        'notes': 'Toast spread with peanut butter and fresh cheese, served with a glass of milk.',
    }},
    'corpus-cheese-pastry-2': {'action': 'edit', 'patch': {
        'name': 'Ricotta cheese pastry',
        'tags': ['snack', 'dessert'],
        'notes': 'A short flaky pastry filled with sweetened ricotta — cannoli- or sfogliatelle-style.',
    }},
    'corpus-loaded-broccoli-salad': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Raw broccoli florets with bacon, dried fruit, seeds, and a creamy-sweet dressing.',
    }},
    'corpus-yogurt-apple-cake': {'action': 'edit', 'patch': {
        'notes': 'Tender butter cake with yogurt and grated apple folded into the batter.',
    }},
    'corpus-salmon-with-apple-veg': {'action': 'edit', 'patch': {
        'notes': 'Roasted salmon plated with sautéed apple and mixed vegetables in an herb oil.',
    }},
    'corpus-whole-grain-veg-bowl': {'action': 'edit', 'patch': {
        'notes': 'A simple whole-grain bowl topped with seasoned roasted or steamed vegetables.',
    }},
    'corpus-berry-apple-pancakes': {'action': 'edit', 'patch': {
        'notes': 'Pancakes with diced apple and fresh berries scattered on the cooking batter.',
    }},
    'corpus-lentil-flour-cake': {'action': 'edit', 'patch': {
        'cuisine': 'Indian',
        'notes': 'Cake or quick-bread made with lentil flour for a higher-protein crumb — South Asian style.',
    }},
    'corpus-apple-butter-saut': {'action': 'edit', 'patch': {
        'name': 'Apple-vegetable butter sauté',
        'notes': 'Apple wedges and mixed vegetables sautéed in butter with herbs and warm spices.',
    }},
    'corpus-buttered-sweet-potato-with-apple': {'action': 'edit', 'patch': {
        'notes': 'Sweet potato cubes and apple sautéed in butter with brown sugar and cinnamon.',
    }},
    'corpus-beef-cheese-sandwich': {'action': 'edit', 'patch': {
        'notes': 'Sliced beef and aged cheese on bread with a savory sauce.',
    }},
    'corpus-bacon-wrapped-apple': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'notes': 'Apple slices wrapped in bacon, baked until the bacon crisps and the apple softens.',
    }},
    'corpus-bean-apple-salad': {'action': 'edit', 'patch': {
        'name': 'Bean and apple salad',
        'notes': 'Beans tossed with diced apple, vegetables, herbs, and a tangy vinaigrette.',
    }},
    'corpus-apple-walnut-cheese-milk': {'action': 'drop', 'reason': 'apple+walnut+cheese+milk pantry combo; not a coherent meal'},
    'corpus-raisin-bread': {'action': 'edit', 'patch': {
        'notes': 'Sweet enriched loaf studded with raisins and lightly spiced with cinnamon.',
    }},
    'corpus-apple-flatbread': {'action': 'edit', 'patch': {
        'notes': 'A thin spiced flatbread topped with sliced apple and a dusting of sugar.',
    }},
    'corpus-chicken-cheese-pasta-bake': {'action': 'edit', 'patch': {
        'notes': 'Pasta baked with shredded chicken, vegetables, and a cheesy cream sauce.',
    }},
    'corpus-buttered-pasta': {'action': 'edit', 'patch': {
        'notes': 'Hot pasta tossed in butter and a touch of salt — a minimal pantry supper.',
    }},
    'corpus-cheese-pancakes': {'action': 'edit', 'patch': {
        'notes': 'Pancakes enriched with fresh cheese in the batter — like cottage-cheese pancakes.',
    }},
    'corpus-eggnog': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'contains_add': ['alcohol'],
        'notes': 'Cooked custard of egg yolks, sugar, milk, and cream spiked with brandy or rum — a holiday drink.',
    }},
    'corpus-cheesy-pasta-bake': {'action': 'edit', 'patch': {
        'notes': 'Pasta baked with vegetables and butter under a blanket of aged cheese.',
    }},
    'corpus-berry-nut-ricotta-plate': {'action': 'edit', 'patch': {
        'tags': ['snack', 'breakfast'],
        'notes': 'Ricotta plated with mixed berries, sliced fruit, and chopped nuts.',
    }},
    'corpus-berry-pecan-muffins': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Spiced muffins with mixed berries and chopped pecans in the batter.',
    }},
    'corpus-bean-burrito-filling': {'action': 'edit', 'patch': {
        'cuisine': 'Mexican-American',
        'notes': 'Refried or stewed beans with rice — the workhorse filling for burritos and bowls.',
    }},
    'corpus-ricotta-cake': {'action': 'edit', 'patch': {
        'cuisine': 'Italian',
        'notes': 'A light, lemon-scented Italian cake bound with fresh ricotta.',
    }},
    'corpus-date-walnut-apple-sweet-potato-cake': {'action': 'edit', 'patch': {
        'notes': 'A dense spiced cake combining dates, walnuts, apple, and grated sweet potato.',
    }},
    'corpus-whole-wheat-raisin-bread': {'action': 'edit', 'patch': {
        'notes': 'Sweet whole-wheat loaf studded with raisins and warm spices.',
    }},
    'corpus-peanut-cheese-sandwich': {'action': 'edit', 'patch': {
        'tags': ['lunch', 'snack'],
        'notes': 'Peanut butter and a slice of fresh cheese between bread — an unusual sweet-savory sandwich.',
    }},
    'corpus-whole-wheat-bread': {'action': 'edit', 'patch': {
        'notes': 'Plain yeast loaf made entirely from whole-wheat flour.',
    }},
    'corpus-apple-sweet-potato-bake': {'action': 'edit', 'patch': {
        'tags': ['dinner', 'lunch', 'dessert'],
        'notes': 'Sweet potato and apple layered with brown sugar and baked — a sweet side or simple dessert.',
    }},
    'corpus-beef-cheese-pasta': {'action': 'edit', 'patch': {
        'name': 'Beef and cheese pasta',
        'cuisine': 'Italian-American',
        'notes': 'Ground beef and sauce tossed with pasta and finished with grated aged cheese.',
    }},
    'corpus-chicken-cheese-sandwich': {'action': 'edit', 'patch': {
        'notes': 'Chicken with melted aged cheese and vegetables in a sandwich.',
    }},
    'corpus-grilled-cheese-with-veg': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'A buttered grilled cheese with sliced vegetables and a side of dipping sauce.',
    }},
    'corpus-cheese-apple-toast': {'action': 'edit', 'patch': {
        'tags': ['breakfast', 'snack'],
        'notes': 'Buttered toast topped with fresh cheese and sliced apple.',
    }},
    'corpus-nutty-apple-bread': {'action': 'edit', 'patch': {
        'notes': 'Sweet quick bread with chopped nuts and diced apple folded into the dough.',
    }},
    'corpus-broccoli-veg-medley': {'action': 'edit', 'patch': {
        'notes': 'Broccoli florets and mixed vegetables blanched or sautéed together as a simple side.',
    }},
    'corpus-chicken-sandwich-with-veg': {'action': 'edit', 'patch': {
        'notes': 'Chicken with lettuce, tomato, and other vegetables in a buttered bun.',
    }},
    'corpus-cheesy-potato-gratin-4': {'action': 'edit', 'patch': {
        'cuisine': 'French',
        'notes': 'Sliced potatoes layered with vegetables and aged cheese, baked until golden on top.',
    }},
    'corpus-chicken-sandwich-2': {'action': 'edit', 'patch': {
        'name': 'Chicken sandwich with vegetables',
        'notes': 'Chicken layered with raw vegetables in a soft roll — the everyday deli sandwich.',
    }},
    'corpus-sweet-potato-apple-bread': {'action': 'edit', 'patch': {
        'notes': 'Spiced quick bread combining mashed sweet potato and grated apple.',
    }},
    'corpus-apple-cheese-bread': {'action': 'edit', 'patch': {
        'notes': 'Quick bread with aged cheese and diced apple in the batter.',
    }},
    'corpus-apple-walnut-raisin-cake': {'action': 'edit', 'patch': {
        'notes': 'Spiced butter cake with diced apple, walnuts, and raisins folded throughout.',
    }},
    'corpus-buttered-grain-bowl': {'action': 'edit', 'patch': {
        'notes': 'Steamed whole grains tossed with butter and mixed vegetables — a plain weeknight bowl.',
    }},
    'corpus-chicken-cheese-sandwich-2': {'action': 'edit', 'patch': {
        'notes': 'Chicken with sliced processed cheese and vegetables in a soft sandwich.',
    }},
    'corpus-rice-beans-2': {'action': 'edit', 'patch': {
        'name': 'Rice and beans',
        'cuisine': 'Latin American',
        'notes': 'Cooked beans served over rice (here, whole-grain) — a staple combination across Latin America and the Caribbean.',
    }},
    'corpus-cheese-souffl': {'action': 'edit', 'patch': {
        'cuisine': 'French',
        'notes': 'An egg-and-cheese batter baked at high heat until it rises tall above the rim of the ramekin.',
    }},
    'corpus-mixed-meat-potato-bake': {'action': 'edit', 'patch': {
        'notes': 'Chicken and beef baked together over potato slices — a hearty casserole.',
    }},
    'corpus-mashed-potatoes': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Boiled potatoes mashed with butter, milk, and seasoning until creamy.',
    }},
    'corpus-liver-with-apple': {'action': 'edit', 'patch': {
        'cuisine': 'German',
        'notes': 'Pan-seared liver served with sautéed apple — a German-style preparation.',
    }},
    'corpus-berry-apple-muffins': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Cinnamon muffins with fresh berries and diced apple folded in.',
    }},
    'corpus-apple-french-toast-2': {'action': 'edit', 'patch': {
        'name': 'Apple French toast',
        'notes': 'French toast topped with sautéed cinnamon apples.',
    }},
    'corpus-apple-dutch-baby': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'tags': ['breakfast'],
        'notes': 'A single oven-baked pancake with apple slices baked into the egg-rich batter.',
    }},
    'corpus-veg-sandwich': {'action': 'edit', 'patch': {
        'name': 'Vegetable sandwich',
        'notes': 'Mixed sliced vegetables in a soft sandwich — a simple vegetarian lunch.',
    }},
    'corpus-yogurt-whole-wheat-muffins': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Whole-wheat muffins made with yogurt for tang and tenderness.',
    }},
    'corpus-chicken-apple-potato-bake': {'action': 'edit', 'patch': {
        'notes': 'Chicken thighs roasted over apple wedges and potatoes with herbs.',
    }},
    'corpus-berry-pecan-cake': {'action': 'edit', 'patch': {
        'notes': 'Butter cake with fresh berries and chopped pecans folded into the batter.',
    }},
    'corpus-roast-beef': {'action': 'edit', 'patch': {
        'cuisine': 'British',
        'notes': 'A whole cut of beef seasoned and roasted until medium-rare, served with vegetables.',
    }},
    'corpus-grilled-steak': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'A thick-cut steak grilled over high heat to a rosy interior, served with a pan or board sauce.',
    }},
    'corpus-apple-cheese-salad': {'action': 'edit', 'patch': {
        'notes': 'Mixed greens with diced apple, aged cheese, and herbs in a tangy vinaigrette.',
    }},
    'corpus-egg-with-oat': {'action': 'edit', 'patch': {
        'name': 'Egg and oat pancakes',
        'tags': ['breakfast'],
        'notes': 'Pancakes made with whole-oat flour and egg, milk, and a touch of sugar.',
    }},
    'corpus-mixed-meat-grain-bowl': {'action': 'edit', 'patch': {
        'notes': 'Whole-grain bowl topped with both chicken and beef and a savory pan sauce.',
    }},
    'corpus-apple-walnut-buttered-eggs': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Scrambled eggs cooked in butter with sautéed apple and toasted walnuts.',
    }},
    'corpus-sour-cream-nut-muffins': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Tender muffins enriched with sour cream and topped with chopped nuts.',
    }},
    'corpus-pasta-with-cheese-veg': {'action': 'edit', 'patch': {
        'notes': 'Pasta tossed with fresh cheese, vegetables, and a light tomato or cream sauce.',
    }},
    'corpus-chicken-sandwich-3': {'action': 'edit', 'patch': {
        'notes': 'Sliced or shredded chicken in a soft roll — the plain diner sandwich.',
    }},
    'corpus-berry-juice-spritzer': {'action': 'edit', 'patch': {
        'notes': 'Berries muddled with fruit juice and topped with sparkling water — a non-alcoholic spritz.',
    }},
    'corpus-ham-potato-fritters': {'action': 'edit', 'patch': {
        'notes': 'Mashed potato bound with chopped cured ham and flour, fried into spiced fritters.',
    }},
    'corpus-caf-au-lait-2': {'action': 'edit', 'patch': {
        'name': 'Café au lait',
        'cuisine': 'French',
        'tags': ['breakfast', 'snack'],
        'notes': 'Strong coffee mixed with an equal volume of hot milk — the French morning drink.',
    }},
    'corpus-apple-raisin-butter-cake': {'action': 'edit', 'patch': {
        'notes': 'Spiced butter cake with diced apple and plump raisins folded into the batter.',
    }},
    'corpus-beef-potato-pie': {'action': 'edit', 'patch': {
        'name': 'Cottage pie',
        'cuisine': 'British',
        'tags': ['dinner', 'lunch'],
        'notes': 'Seasoned ground beef under a mashed-potato lid, baked until the top browns — British cottage pie.',
    }},
    'corpus-broccoli-cheese-omelet': {'action': 'edit', 'patch': {
        'notes': 'A folded omelet stuffed with steamed broccoli and grated aged cheese.',
    }},
    'corpus-sunflower-seed-salad': {'action': 'edit', 'patch': {
        'notes': 'Mixed greens and vegetables tossed with sunflower seeds and a sweet-tangy dressing.',
    }},
    'corpus-loaded-broccoli-salad-2': {'action': 'edit', 'patch': {
        'name': 'Loaded broccoli salad with cheddar',
        'cuisine': 'American',
        'notes': 'Raw broccoli with bacon, cheddar, and greens in a sweet creamy dressing.',
    }},
    'corpus-creamed-chicken-veg': {'action': 'edit', 'patch': {
        'notes': 'Shredded chicken and vegetables simmered in a milk-based cream sauce.',
    }},
    'corpus-walnut-apple-pancakes': {'action': 'edit', 'patch': {
        'notes': 'Pancakes with chopped walnuts and diced apple in the batter.',
    }},
    'corpus-apple-spinach-salad': {'action': 'edit', 'patch': {
        'notes': 'Baby spinach with sliced apple and a sweet-tangy vinaigrette.',
    }},
    'corpus-egg-greens-potato-hash': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Diced potato fried with leafy greens and topped with a runny egg.',
    }},
    'corpus-apple-walnut-french-toast': {'action': 'edit', 'patch': {
        'notes': 'French toast topped with sautéed apple and toasted walnuts.',
    }},
    'corpus-nutty-potato-bread': {'action': 'edit', 'patch': {
        'notes': 'Soft potato-enriched quick bread with chopped nuts folded into the dough.',
    }},
    'corpus-bacon-pasta': {'action': 'edit', 'patch': {
        'cuisine': 'Italian',
        'notes': 'Pasta tossed with crisp bacon and a quick pan sauce of fat and vegetables.',
    }},
    'corpus-cheesecake-with-nut-crust': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'A baked cream-cheese cheesecake set over a buttery crushed-nut crust instead of graham crackers.',
    }},
    'corpus-apple-zucchini-bread': {'action': 'edit', 'patch': {
        'notes': 'Spiced quick bread with grated zucchini and diced apple folded in.',
    }},
    'corpus-chicken-parm-pasta': {'action': 'edit', 'patch': {
        'cuisine': 'Italian-American',
        'notes': 'Pasta tossed with breaded chicken cutlets, tomato sauce, and grated parmesan.',
    }},
    'corpus-mixed-meat-skillet': {'action': 'edit', 'patch': {
        'notes': 'A skillet of mixed chicken and beef with vegetables, browned together.',
    }},
    'corpus-apple-cheesecake': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'A cream-cheese cheesecake topped with cinnamon-sautéed apples.',
    }},
    'corpus-carrot-walnut-raisin-cake': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Carrot cake with chopped walnuts and raisins folded into the spiced batter.',
    }},
    'corpus-apple-butter-chicken': {'action': 'edit', 'patch': {
        'notes': 'Chicken pan-roasted with apple wedges and finished with a butter pan sauce.',
    }},
    'corpus-liver-casserole-with-cheese': {'action': 'edit', 'patch': {
        'notes': 'Sliced liver baked with vegetables under a cheesy cream sauce — a rib-sticking casserole.',
    }},
    'corpus-lentil-apple-cake': {'action': 'edit', 'patch': {
        'cuisine': 'Indian',
        'notes': 'A dense cake made with lentil flour and grated apple, lightly sweetened.',
    }},
    'corpus-nutty-bread-pudding': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Stale bread soaked in a sweet egg-and-milk custard with chopped nuts, baked until set.',
    }},
    'corpus-creamy-lentil-dal': {'action': 'edit', 'patch': {
        'cuisine': 'Indian',
        'notes': 'Lentils simmered with cream, butter, and aromatics until silky — dal makhani style.',
    }},
    'corpus-creamy-mashed-potatoes': {'action': 'edit', 'patch': {
        'notes': 'Mashed potatoes whipped with milk, butter, and a touch of fresh cheese for extra richness.',
    }},
    'corpus-cheese-ham-melt': {'action': 'edit', 'patch': {
        'tags': ['lunch'],
        'notes': 'Ham and processed cheese melted on bread with vegetables — a fast diner lunch.',
    }},
    'corpus-apple-oat-flatbread': {'action': 'edit', 'patch': {
        'notes': 'A whole-grain flatbread topped with sliced apple, spices, and a touch of sweetener.',
    }},
    'corpus-spinach-omelet': {'action': 'edit', 'patch': {
        'notes': 'A folded omelet stuffed with wilted spinach.',
    }},
    'corpus-scrambled-eggs': {'action': 'edit', 'patch': {
        'notes': 'Eggs whisked with milk and cooked low-and-slow in butter into soft curds.',
    }},
    'corpus-creamy-pasta-carbonara': {'action': 'edit', 'patch': {
        'cuisine': 'Italian-American',
        'notes': 'The Americanized carbonara: pasta in a creamy sauce of butter, milk, eggs, and pancetta.',
    }},
    'corpus-beef-pot-pie': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Beef stew with vegetables baked under a flaky pastry lid until golden.',
    }},
    'corpus-yogurt-bowl': {'action': 'edit', 'patch': {
        'tags': ['breakfast', 'snack'],
        'notes': 'A bowl of plain or sweetened yogurt — usually topped with fruit and granola at the table.',
    }},
    'corpus-chicken-broccoli-grain-bowl': {'action': 'edit', 'patch': {
        'notes': 'A whole-grain bowl with chicken, broccoli, and mixed vegetables.',
    }},
    'corpus-cheese-veg-quiche': {'action': 'edit', 'patch': {
        'cuisine': 'French',
        'notes': 'A butter-pastry shell filled with a cheesy egg custard and folded vegetables.',
    }},
    'corpus-baked-mac-cheese': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Elbow pasta in a cheddar bechamel, baked with a crumb topping until the top crisps.',
    }},
    'corpus-cheese-stuffed-bread': {'action': 'edit', 'patch': {
        'notes': 'Enriched bread baked around a sweet fresh-cheese filling.',
    }},
    'corpus-veg-green-omelet': {'action': 'edit', 'patch': {
        'name': 'Vegetable and greens omelet',
        'notes': 'A folded omelet with wilted greens and sautéed vegetables.',
    }},
    'corpus-ricotta-apple-tart': {'action': 'edit', 'patch': {
        'cuisine': 'Italian',
        'notes': 'A short-crust tart filled with sweetened ricotta and topped with apple slices.',
    }},
    'corpus-prosciutto-mozzarella': {'action': 'edit', 'patch': {
        'cuisine': 'Italian',
        'tags': ['snack'],
        'notes': 'Thinly sliced prosciutto draped over fresh mozzarella — an antipasto plate.',
    }},
    'corpus-chicken-pot-pie': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Chicken and vegetables in a creamy sauce baked under a flaky pastry lid.',
    }},
    'corpus-cacio-e-pepe': {'action': 'edit', 'patch': {
        'cuisine': 'Italian',
        'notes': 'Pasta tossed with grated pecorino and cracked black pepper, emulsified with pasta water and butter — the Roman classic.',
    }},
    'corpus-beef-carbonara': {'action': 'edit', 'patch': {
        'notes': 'A non-traditional carbonara made with ground beef instead of guanciale.',
    }},
    'corpus-pasta-salad-with-greens': {'action': 'edit', 'patch': {
        'notes': 'Cold pasta tossed with leafy greens, vegetables, and a tangy dressing.',
    }},
    'corpus-shrimp-stir-fry': {'action': 'edit', 'patch': {
        'cuisine': 'Chinese-American',
        'notes': 'Shrimp tossed in a hot wok with mixed vegetables, mushrooms, and a savory sauce, served over rice.',
    }},
    'corpus-ham-mac-cheese': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Macaroni in a cheddar sauce with diced ham folded in and baked until bubbling.',
    }},
    'corpus-chicken-pasta-in-butter': {'action': 'edit', 'patch': {
        'notes': 'Chicken and vegetables tossed with pasta in a melted-butter pan sauce.',
    }},
    'corpus-berry-fruit-punch': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'notes': 'A non-alcoholic punch of muddled berries, sliced fruit, and a splash of soda.',
    }},
    'corpus-berry-biscuit-shortcake': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'tags': ['dessert'],
        'notes': 'A split biscuit layered with macerated berries and whipped cream.',
    }},
    'corpus-pickled-bean-salad': {'action': 'edit', 'patch': {
        'notes': 'Green beans tossed with pickled vegetables, herbs, and a sweet-tart vinaigrette.',
    }},
    'corpus-loaded-bean-cheese-salad': {'action': 'edit', 'patch': {
        'notes': 'Mixed beans with greens, aged cheese, cured meat, and a tangy dressing — a hearty composed salad.',
    }},
    'corpus-raisin-oat-cookies': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Drop cookies with rolled oats, raisins, and warm spices.',
    }},
    'corpus-beef-grain-bowl-with-greens': {'action': 'edit', 'patch': {
        'notes': 'A whole-grain bowl with seared beef and a tangle of wilted leafy greens.',
    }},
    'corpus-chicken-with-apples-7': {'action': 'edit', 'patch': {
        'notes': 'Chicken simmered with apple in a pan sauce — a Normandy-leaning preparation.',
    }},
    'corpus-apple-custard': {'action': 'edit', 'patch': {
        'notes': 'Sliced apple baked under a sweet egg-and-milk custard.',
    }},
    'corpus-beef-lasagna': {'action': 'edit', 'patch': {
        'name': 'Beef lasagna',
        'cuisine': 'Italian-American',
        'notes': 'Layered pasta with ricotta, mozzarella, ground beef ragu, and vegetables, baked until set.',
    }},
    'corpus-peanut-oat-butter-cookies': {'action': 'edit', 'patch': {
        'notes': 'Drop cookies with peanut butter, rolled oats, and butter for a chewy bite.',
    }},
    'corpus-saut-ed-greens-with-butter': {'action': 'edit', 'patch': {
        'notes': 'Leafy greens wilted in butter with garlic and seasoning — a simple side.',
    }},
    'corpus-apple-raisin-veg-salad': {'action': 'edit', 'patch': {
        'notes': 'Mixed vegetables with diced apple, raisins, and a sweet-tangy dressing.',
    }},
    'corpus-beef-potato-butter-braise': {'action': 'edit', 'patch': {
        'notes': 'Beef chunks braised low with potatoes and vegetables in a buttery pan sauce.',
    }},
    'corpus-beans-bacon': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Baked beans simmered with bacon and vegetables — the Southern-style side.',
    }},
    'corpus-bacon-with-egg': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Bacon and eggs with toast and cheese — the classic American breakfast plate.',
    }},
    'corpus-coffee-walnut-cake': {'action': 'edit', 'patch': {
        'cuisine': 'British',
        'notes': 'A coffee-flavored butter sponge cake with walnuts in the batter and a coffee buttercream.',
    }},
    'corpus-beef-grain-potato-bowl': {'action': 'edit', 'patch': {
        'notes': 'Whole-grain bowl with seared beef, roasted potatoes, and mixed vegetables.',
    }},
    'corpus-nutty-french-toast': {'action': 'edit', 'patch': {
        'notes': 'French toast topped with toasted chopped nuts and a drizzle of butter.',
    }},
    'corpus-american-cheese-veg-sandwich': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'tags': ['lunch'],
        'notes': 'Sliced American cheese with vegetables on bread — the diner lunch sandwich.',
    }},
    'corpus-beef-bourguignon-with-potatoes': {'action': 'edit', 'patch': {
        'cuisine': 'French',
        'contains_add': ['alcohol'],
        'notes': 'Beef chuck braised in red wine with mushrooms, pearl onions, and potatoes — the Burgundian classic.',
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

    print('compositional batch-3 audit applied.')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
