"""Compositional-meals audit batch 2 — entries 100-249 (by original index).

Same shape as batch 1: id → {action, patch?, reason?}.
Re-run scripts/rederive_diet_compatibility.py after this.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'compositional-meals.json'

DECISIONS: dict[str, dict] = {
    # 100
    'corpus-coffee-with-cream': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'notes': 'Brewed coffee softened with a splash of cream — the everyday hot beverage.',
    }},
    # 101
    'corpus-mixed-meat-butter-braise': {'action': 'edit', 'patch': {
        'notes': 'Chicken, beef, and cured meats braised together in butter with vegetables until tender.',
    }},
    # 102
    'corpus-apple-juice-with-fruit': {'action': 'edit', 'patch': {
        'notes': 'Apple juice poured over sliced fruit — a child-friendly mock punch.',
    }},
    # 103
    'corpus-berry-nut-apple-crisp': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'tags': ['dessert'],
        'notes': 'Apples and berries baked beneath a buttery oat-and-nut streusel until bubbling and golden.',
    }},
    # 104
    'corpus-peanut-sweet-potato': {'action': 'edit', 'patch': {
        'notes': 'Sweet potatoes finished with a peanut-butter glaze and a touch of sugar — a sweet-savory side.',
    }},
    # 105
    'corpus-pecan-zucchini-bread': {'action': 'edit', 'patch': {
        'notes': 'Quick bread loaf with grated zucchini and chopped pecans folded into a cinnamon-spiced batter.',
    }},
    # 106
    'corpus-cheesy-pasta': {'action': 'edit', 'patch': {
        'notes': 'Pasta tossed with grated aged cheese, herbs, oil, and a touch of vegetable — a simple weeknight bowl.',
    }},
    # 107
    'corpus-ricotta-with-berry': {'action': 'edit', 'patch': {
        'tags': ['breakfast', 'snack'],
        'notes': 'Whipped ricotta on toast with fresh berries and a drizzle of sweetener.',
    }},
    # 108
    'corpus-fruit-punch': {'action': 'edit', 'patch': {
        'ingredient_categories': ['Citrus', 'Tropical fruits', 'Sugar & sweeteners', 'Juices'],
        'tags': ['snack'],
        'notes': 'A party punch of citrus and tropical juices sweetened to taste — non-alcoholic.',
    }},
    # 109 — bug fix: bogus pork tag.
    'corpus-cheese-stuffed-french-toast': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'contains': [],
        'notes': 'French toast filled with a sweet cream-cheese stuffing, dipped in egg-and-milk batter, and pan-fried.',
    }},
    # 110
    'corpus-whole-wheat-nut-cookies': {'action': 'edit', 'patch': {
        'notes': 'Drop cookies made with whole-wheat flour and chopped nuts for a denser, nuttier bite.',
    }},
    # 111
    'corpus-buttered-chicken-veg': {'action': 'edit', 'patch': {
        'notes': 'Chicken and vegetables finished in melted butter — a one-pan supper.',
    }},
    # 112
    'corpus-tossed-salad': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Lettuce, cucumbers, tomatoes, and shredded vegetables tossed with bottled dressing — the diner-style side salad.',
    }},
    # 113
    'corpus-garden-salad': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Mixed lettuces and raw vegetables with bottled dressing — the everyday American side salad.',
    }},
    # 114
    'corpus-saut-ed-greens-with-veg': {'action': 'edit', 'patch': {
        'notes': 'Leafy greens wilted in a hot pan with garlic and mixed vegetables, finished with a pan sauce.',
    }},
    # 115
    'corpus-two-cheese-veg-bake': {'action': 'edit', 'patch': {
        'notes': 'Mixed vegetables baked under a blanket of aged and fresh cheese until melted and bubbling.',
    }},
    # 116
    'corpus-ricotta-with-apple-2': {'action': 'edit', 'patch': {
        'name': 'Ricotta with apple and veg',
        'tags': ['lunch', 'snack'],
        'notes': 'Whipped ricotta plated with sliced apple, raw vegetables, and chopped nuts — a light savory-sweet plate.',
    }},
    # 117
    'corpus-omelet': {'action': 'edit', 'patch': {
        'name': 'Omelet',
        'cuisine': 'French',
        'notes': 'Whisked eggs cooked in butter until just set, folded over a simple filling.',
    }},
    # 118
    'corpus-berry-ricotta-with-fruit': {'action': 'edit', 'patch': {
        'tags': ['breakfast', 'snack'],
        'notes': 'Ricotta with mixed berries and sliced fruit — a light breakfast bowl.',
    }},
    # 119
    'corpus-shrimp-with-feta': {'action': 'edit', 'patch': {
        'name': 'Shrimp with feta',
        'cuisine': 'Greek',
        'notes': 'Shrimp baked in a tomato-and-herb sauce, finished with crumbled feta — Greek shrimp saganaki style.',
    }},
    # 120
    'corpus-buttered-mashed-potatoes': {'action': 'edit', 'patch': {
        'notes': 'Boiled potatoes mashed with plenty of butter and a touch of seasoning.',
    }},
    # 121
    'corpus-apple-cinnamon-roll': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Yeasted dough rolled around spiced apple and cinnamon, baked into a soft sweet bun.',
    }},
    # 122 — was "Apple with milk"; categories suggest an apple milk pudding.
    'corpus-apple-with-milk': {'action': 'edit', 'patch': {
        'name': 'Apple milk pudding',
        'tags': ['dessert'],
        'notes': 'A baked apple pudding bound with milk, flour, and butter — an English nursery dessert.',
    }},
    # 123
    'corpus-cheesy-chicken-potato-bake': {'action': 'edit', 'patch': {
        'notes': 'Chicken and potato slices baked under a cheesy cream sauce until the top browns.',
    }},
    # 124
    'corpus-potato-custard': {'action': 'edit', 'patch': {
        'notes': 'A baked custard of mashed potato, eggs, butter, and sugar — a sweet-savory regional pudding.',
    }},
    # 125
    'corpus-pecan-pancakes': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Pancakes with chopped pecans folded into the batter, cooked until the nuts toast.',
    }},
    # 126
    'corpus-oat-nut-cookies': {'action': 'edit', 'patch': {
        'notes': 'Drop cookies with rolled oats and chopped nuts — chewy and hearty.',
    }},
    # 127
    'corpus-buttered-beans': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Beans simmered with butter and a hint of sweetness — a Southern-style side.',
    }},
    # 128
    'corpus-spritzer-with-fruit': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'contains_add': ['alcohol'],
        'notes': 'White wine topped with sparkling water and sliced fruit — a long, easy aperitif.',
    }},
    # 129
    'corpus-chicken-potatoes': {'action': 'edit', 'patch': {
        'notes': 'Chicken roasted or braised with potatoes and vegetables — a one-pan dinner.',
    }},
    # 130
    'corpus-apple-yogurt': {'action': 'edit', 'patch': {
        'tags': ['breakfast', 'snack'],
        'notes': 'Yogurt with diced apple and a drizzle of sweetener — a quick breakfast or snack.',
    }},
    # 131
    'corpus-berry-smoothie-with-fruit': {'action': 'edit', 'patch': {
        'notes': 'Mixed berries and fruit blended with milk into a drinkable smoothie.',
    }},
    # 132
    'corpus-apple-mimosa': {'action': 'edit', 'patch': {
        'cuisine': 'French',
        'tags': ['breakfast', 'snack'],
        'contains_add': ['alcohol'],
        'notes': 'Sparkling wine cut with apple juice — a brunch-style mimosa variant.',
    }},
    # 133
    'corpus-beef-with-apples': {'action': 'edit', 'patch': {
        'name': 'Beef with apples',
        'notes': 'Seared beef finished with apple wedges, herbs, and pan jus — a Normandy-leaning preparation.',
    }},
    # 134
    'corpus-apple-with-bread': {'action': 'drop', 'reason': 'pairing of two staples, not a meal'},
    # 135
    'corpus-creamy-greens-soup': {'action': 'edit', 'patch': {
        'notes': 'Leafy greens simmered in broth and puréed with cream — a velvety green soup.',
    }},
    # 136
    'corpus-cheese-omelet': {'action': 'edit', 'patch': {
        'cuisine': 'French',
        'notes': 'A French omelet folded around grated or sliced fresh cheese.',
    }},
    # 137
    'corpus-sweet-potato-raisin-bread': {'action': 'edit', 'patch': {
        'notes': 'Spiced quick bread with mashed sweet potato and raisins folded into the batter.',
    }},
    # 138
    'corpus-berry-crepes': {'action': 'edit', 'patch': {
        'cuisine': 'French',
        'tags': ['breakfast', 'dessert'],
        'notes': 'Thin French pancakes wrapped around fresh berries and dusted with sugar.',
    }},
    # 139
    'corpus-apple-walnut-milk-bread': {'action': 'edit', 'patch': {
        'notes': 'Soft milk-bread loaf with diced apple and chopped walnuts folded into the dough.',
    }},
    # 140
    'corpus-apple-french-toast': {'action': 'edit', 'patch': {
        'notes': 'French toast topped with sautéed apples and a dusting of cinnamon sugar.',
    }},
    # 141
    'corpus-pickled-bean-potato-salad': {'action': 'edit', 'patch': {
        'notes': 'Cool potato salad tossed with green beans, pickled vegetables, and a tangy vinaigrette.',
    }},
    # 142
    'corpus-nutty-stuffed-bread': {'action': 'edit', 'patch': {
        'notes': 'Sweet enriched bread filled with a buttery nut-and-sugar paste.',
    }},
    # 143
    'corpus-toast-with-juice-milk': {'action': 'drop', 'reason': 'three breakfast staples on a tray; not a coherent meal pattern'},
    # 144
    'corpus-cheesy-veg-melt': {'action': 'edit', 'patch': {
        'tags': ['lunch'],
        'notes': 'Open-faced sandwich of vegetables blanketed with melted processed cheese and broiled.',
    }},
    # 145
    'corpus-bacon-hash': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'tags': ['breakfast'],
        'notes': 'Diced potatoes and bacon fried in a skillet until crisp and browned — a diner breakfast staple.',
    }},
    # 146
    'corpus-nutty-custard': {'action': 'edit', 'patch': {
        'notes': 'Baked egg-and-milk custard with toasted chopped nuts folded through.',
    }},
    # 147
    'corpus-cheesy-mashed-potatoes': {'action': 'edit', 'patch': {
        'notes': 'Mashed potatoes whipped with butter, sour cream, and grated aged cheese.',
    }},
    # 148
    'corpus-date-walnut-butter-cake': {'action': 'edit', 'patch': {
        'notes': 'Butter cake with chopped dates and walnuts — a sticky, lightly spiced loaf.',
    }},
    # 149
    'corpus-berry-cocktail': {'action': 'edit', 'patch': {
        'contains_add': ['alcohol'],
        'notes': 'A spirit-based cocktail muddled with fresh berries and a touch of citrus.',
    }},
    # 150
    'corpus-apple-raisin-muffins': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Cinnamon-spiced muffins studded with diced apple and plump raisins.',
    }},
    # 151
    'corpus-yogurt-pancakes': {'action': 'edit', 'patch': {
        'notes': 'Pancakes made with yogurt in the batter for a tangy, extra-fluffy crumb.',
    }},
    # 152
    'corpus-sour-cream-loaf': {'action': 'edit', 'patch': {
        'notes': 'Quick-bread loaf enriched with sour cream for a moist, tender texture.',
    }},
    # 153
    'corpus-peanut-butter-oat-squares': {'action': 'edit', 'patch': {
        'tags': ['snack', 'dessert'],
        'notes': 'No-bake oat bars bound with peanut butter, butter, and a sweetener — chewy snack squares.',
    }},
    # 154
    'corpus-berry-apple-yogurt-parfait': {'action': 'edit', 'patch': {
        'notes': 'Layered yogurt parfait with fresh berries and diced apple.',
    }},
    # 155
    'corpus-chicken-with-raisin-veg': {'action': 'edit', 'patch': {
        'cuisine': 'Moroccan',
        'notes': 'Chicken stewed with vegetables and plump raisins in a savory-sweet sauce — tagine-style.',
    }},
    # 156
    'corpus-paneer-in-milk': {'action': 'edit', 'patch': {
        'cuisine': 'Indian',
        'tags': ['dessert'],
        'notes': 'Fresh paneer simmered in sweetened milk with cardamom and ghee — a North Indian milk sweet.',
    }},
    # 157
    'corpus-iced-tea-with-juice': {'action': 'edit', 'patch': {
        'notes': 'Iced black tea cut with fruit juice — a Southern-style refreshment.',
    }},
    # 158 — categories describe a pancake/breakfast batter rather than literally "egg and peanut butter".
    'corpus-egg-with-peanut-butter': {'action': 'edit', 'patch': {
        'name': 'Peanut butter pancakes',
        'tags': ['breakfast'],
        'notes': 'Pancakes enriched with peanut butter folded into the milk-and-egg batter.',
    }},
    # 159
    'corpus-seafood-liver-casserole': {'action': 'edit', 'patch': {
        'notes': 'A rich baked casserole layering shellfish, organ meats, and vegetables under a cheesy sauce.',
    }},
    # 160
    'corpus-broccoli-whole-grain-bake': {'action': 'edit', 'patch': {
        'notes': 'Broccoli and whole grains baked with butter and a touch of cheese until the top crisps.',
    }},
    # 161
    'corpus-peanut-butter-eggs': {'action': 'edit', 'patch': {
        'name': 'Peanut butter candy eggs',
        'cuisine': 'American',
        'tags': ['dessert'],
        'notes': 'Easter-style confections of peanut butter and butter shaped into eggs and coated in chocolate.',
    }},
    # 162
    'corpus-cheesy-saut-ed-veg': {'action': 'edit', 'patch': {
        'notes': 'Pan-sautéed vegetables finished with melted butter and grated aged cheese.',
    }},
    # 163
    'corpus-apple-spiced-tea': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'notes': 'Hot tea steeped with apple slices, cinnamon, and clove — a winter sipping drink.',
    }},
    # 164
    'corpus-chicken-milk-grain-bowl': {'action': 'edit', 'patch': {
        'notes': 'Whole-grain bowl with chicken and a creamy milk-based sauce poured over vegetables.',
    }},
    # 165
    'corpus-fried-eggs': {'action': 'edit', 'patch': {
        'notes': 'Eggs cracked into a hot pan and cooked sunny-side up or over-easy.',
    }},
    # 166
    'corpus-chicken-grain-bowl-in-butter': {'action': 'edit', 'patch': {
        'name': 'Buttered chicken grain bowl',
        'notes': 'Whole grains topped with chicken and vegetables, finished with a melted-butter sauce.',
    }},
    # 167
    'corpus-cheese-apple-milk-toast': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Toast topped with fresh cheese, sliced apple, and a drizzle of warm milk.',
    }},
    # 168
    'corpus-apple-nut-sangria': {'action': 'edit', 'patch': {
        'cuisine': 'Spanish',
        'tags': ['snack'],
        'contains_add': ['alcohol'],
        'notes': 'White-wine sangria with apple slices, toasted nuts, and a touch of brandy.',
    }},
    # 169
    'corpus-beef-egg-grain-bowl': {'action': 'edit', 'patch': {
        'notes': 'Whole-grain bowl with seared beef, a runny egg, and vegetables — a hearty one-bowl dinner.',
    }},
    # 170
    'corpus-french-toast': {'action': 'edit', 'patch': {
        'cuisine': 'French',
        'notes': 'Bread soaked in milk and beaten eggs, spiced with cinnamon and vanilla, then pan-fried in butter.',
    }},
    # 171
    'corpus-fruity-green-salad': {'action': 'edit', 'patch': {
        'notes': 'Mixed greens tossed with sliced fruit and a tangy-sweet vinaigrette.',
    }},
    # 172
    'corpus-beef-potato-cheese-bake': {'action': 'edit', 'patch': {
        'notes': 'Ground beef and potato slices baked under a blanket of aged cheese.',
    }},
    # 173
    'corpus-apple-walnut-cake': {'action': 'edit', 'patch': {
        'notes': 'Butter cake folded with diced apple and chopped walnuts — a classic fall coffee cake.',
    }},
    # 174
    'corpus-bacon-raisin-broccoli-salad': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Raw broccoli florets tossed with raisins, crisp bacon, and a creamy-sweet dressing — a classic American salad.',
    }},
    # 175
    'corpus-sweet-potato-muffins': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Spiced muffins with mashed sweet potato, raisins, and chopped nuts.',
    }},
    # 176
    'corpus-beef-stir-fry-with-rice': {'action': 'edit', 'patch': {
        'cuisine': 'Chinese-American',
        'notes': 'Wok-tossed beef and vegetables in a savory sauce served over steamed white rice.',
    }},
    # 177
    'corpus-beef-in-butter-sauce': {'action': 'edit', 'patch': {
        'notes': 'Seared beef tips finished in a pan butter sauce with sautéed vegetables.',
    }},
    # 178
    'corpus-spiced-vegetable-curry': {'action': 'edit', 'patch': {
        'cuisine': 'Indian',
        'notes': 'Mixed vegetables simmered in a spiced tomato-onion gravy — a workaday Indian curry.',
    }},
    # 179
    'corpus-apple-raisin-compote': {'action': 'edit', 'patch': {
        'tags': ['dessert', 'snack'],
        'notes': 'Apples and raisins simmered with sugar and a splash of water into a chunky spoonable compote.',
    }},
    # 180
    'corpus-berry-vegetable-salad': {'action': 'edit', 'patch': {
        'notes': 'Raw vegetables tossed with fresh berries and a tangy-sweet vinaigrette.',
    }},
    # 181
    'corpus-nutty-cheese-pancakes': {'action': 'edit', 'patch': {
        'notes': 'Pancakes enriched with fresh cheese and chopped nuts in the batter.',
    }},
    # 182
    'corpus-shrimp-apple-cheese-salad': {'action': 'edit', 'patch': {
        'notes': 'Salad of poached shrimp, diced apple, and crumbled fresh cheese in a creamy dressing.',
    }},
    # 183
    'corpus-beef-grain-butter-bowl': {'action': 'edit', 'patch': {
        'name': 'Buttered beef grain bowl',
        'notes': 'Whole-grain bowl with seared beef and vegetables, finished with a melted-butter pan sauce.',
    }},
    # 184
    'corpus-carrot-raisin-cake': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Spiced cake with grated carrot and plump raisins folded in — a classic carrot-cake variant.',
    }},
    # 185
    'corpus-pecan-biscotti': {'action': 'edit', 'patch': {
        'cuisine': 'Italian',
        'notes': 'Twice-baked Italian biscuits with chopped pecans, crisp enough to dip in coffee.',
    }},
    # 186
    'corpus-potato-strata': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'tags': ['breakfast'],
        'notes': 'A make-ahead breakfast bake layering potato, eggs, and milk-soaked bread before the oven.',
    }},
    # 187 — categories suggest a sweet noodle pudding.
    'corpus-apple-egg-pasta': {'action': 'edit', 'patch': {
        'name': 'Apple noodle kugel',
        'cuisine': 'Jewish',
        'tags': ['dessert'],
        'notes': 'Egg noodles baked with butter, eggs, sugar, and grated apple — a sweet Ashkenazi kugel.',
    }},
    # 188
    'corpus-berry-toast': {'action': 'edit', 'patch': {
        'tags': ['breakfast', 'snack'],
        'notes': 'Toast topped with crushed fresh berries and a dusting of sugar.',
    }},
    # 189
    'corpus-cheese-sandwich': {'action': 'edit', 'patch': {
        'notes': 'Sliced fresh cheese between two pieces of bread with a smear of sauce — a plain lunch sandwich.',
    }},
    # 190
    'corpus-nut-horchata': {'action': 'edit', 'patch': {
        'cuisine': 'Mexican',
        'notes': 'A cold drink of ground nuts and rice steeped in sweetened milk and cinnamon.',
    }},
    # 191
    'corpus-coffee-cake': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'A tender butter cake spiced with cinnamon and topped with crumb streusel — served alongside coffee.',
    }},
    # 192
    'corpus-beef-stew': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Chunks of beef simmered low with potatoes, carrots, and aromatics until tender — a winter staple.',
    }},
    # 193
    'corpus-pot-roast-with-potatoes': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'A tough cut of beef braised in liquid for hours alongside potatoes and root vegetables until fork-tender.',
    }},
    # 194
    'corpus-shrimp-with-feta-2': {'action': 'edit', 'patch': {
        'cuisine': 'Greek',
        'notes': 'Shrimp baked in a tomato sauce with crumbled feta and herbs — Greek-style.',
    }},
    # 195
    'corpus-raisin-pound-cake': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'A dense butter pound cake studded with raisins and lightly spiced.',
    }},
    # 196
    'corpus-raisin-bread-pudding': {'action': 'edit', 'patch': {
        'name': 'Raisin bread pudding',
        'cuisine': 'American',
        'notes': 'Stale bread soaked in a sweet egg-and-milk custard with raisins and cinnamon, baked until set.',
    }},
    # 197
    'corpus-black-beans': {'action': 'edit', 'patch': {
        'cuisine': 'Latin American',
        'notes': 'Black beans simmered low with peppers, aromatics, and herbs into a soupy stew.',
    }},
    # 198
    'corpus-bacon-spinach-salad': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Baby spinach tossed with crisp bacon, sliced egg, and a warm bacon-fat vinaigrette.',
    }},
    # 199
    'corpus-berry-shortcake': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'tags': ['dessert'],
        'notes': 'Buttery sweet biscuit split and layered with macerated berries and whipped cream.',
    }},
    # 200
    'corpus-apple-pancake-batter': {'action': 'edit', 'patch': {
        'name': 'Quick apple pancakes',
        'notes': 'Pancakes from a quick mix-style batter with grated apple folded in.',
    }},
    # 201
    'corpus-ham-cheese-on-bread': {'action': 'edit', 'patch': {
        'name': 'Ham and cheese sandwich',
        'notes': 'Sliced cured ham and aged cheese between bread — the everyday deli sandwich.',
    }},
    # 202
    'corpus-beef-bean-stew': {'action': 'edit', 'patch': {
        'notes': 'A long-simmered stew of beef chunks and beans with potatoes and aromatics.',
    }},
    # 203
    'corpus-veggie-omelet-with-cheese': {'action': 'edit', 'patch': {
        'notes': 'A folded omelet stuffed with sautéed vegetables and grated aged cheese.',
    }},
    # 204
    'corpus-ham-sandwich': {'action': 'edit', 'patch': {
        'notes': 'Sliced cured ham between bread, often with mustard — the diner-deli classic.',
    }},
    # 205
    'corpus-beer-with-nuts-bread': {'action': 'edit', 'patch': {
        'cuisine': 'German',
        'tags': ['snack'],
        'contains_add': ['alcohol'],
        'notes': 'Cold beer with a pretzel-style bread and roasted nuts — a beergarden snack.',
    }},
    # 206
    'corpus-berry-pancakes-3': {'action': 'edit', 'patch': {
        'notes': 'Pancakes with fresh berries folded into or scattered onto the batter as it cooks.',
    }},
    # 207
    'corpus-apple-cheese-milk': {'action': 'drop', 'reason': 'apple+cheese+milk staple combo; not a coherent meal'},
    # 208
    'corpus-apple-grain-bowl': {'action': 'edit', 'patch': {
        'notes': 'Whole-grain bowl with diced apple, herbs, and seasoned vegetables in a light oil dressing.',
    }},
    # 209
    'corpus-berry-meringue': {'action': 'edit', 'patch': {
        'cuisine': 'French',
        'notes': 'Crisp baked meringues topped with whipped cream and fresh berries — Eton-mess style.',
    }},
    # 210
    'corpus-dinner-rolls': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Soft enriched yeast rolls served warm with butter alongside the main meal.',
    }},
    # 211
    'corpus-apple-bread-roll': {'action': 'edit', 'patch': {
        'notes': 'A sweet yeast roll filled with cinnamon-spiced apple, baked until the crust is golden.',
    }},
    # 212
    'corpus-shrimp-apple-salad': {'action': 'edit', 'patch': {
        'notes': 'Poached shrimp and diced apple tossed with herbs and a citrus-oil vinaigrette.',
    }},
    # 213
    'corpus-butter-chicken-with-potatoes': {'action': 'edit', 'patch': {
        'notes': 'Chicken roasted with potatoes in plenty of butter — a French-leaning skillet roast.',
    }},
    # 214
    'corpus-berry-apple-cobbler': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Mixed berries and apple baked beneath a soft biscuit topping until the fruit bubbles up.',
    }},
    # 215
    'corpus-apple-pasta': {'action': 'edit', 'patch': {
        'notes': 'Pasta tossed with sautéed apple, herbs, and oil — an unusual sweet-savory bowl.',
    }},
    # 216
    'corpus-cheesy-apple-french-toast': {'action': 'edit', 'patch': {
        'notes': 'French toast filled with cream cheese and apple slices, dusted with cinnamon sugar.',
    }},
    # 217
    'corpus-cheese-veg-sandwich': {'action': 'edit', 'patch': {
        'notes': 'Aged cheese and vegetables layered in bread — a hearty vegetarian sandwich.',
    }},
    # 218
    'corpus-bacon-cheese-broccoli': {'action': 'edit', 'patch': {
        'notes': 'Broccoli florets baked with crisp bacon and a cheese sauce until bubbling.',
    }},
    # 219
    'corpus-sour-cream-apple-muffins': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Tender muffins with sour cream and diced apple in the batter for extra moisture.',
    }},
    # 220
    'corpus-butter-roasted-chicken': {'action': 'edit', 'patch': {
        'notes': 'A whole chicken roasted with a butter rub until the skin crisps and the meat stays juicy.',
    }},
    # 221
    'corpus-fruit-muffins': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Spiced muffins studded with berries, dried fruit, and diced fresh fruit.',
    }},
    # 222
    'corpus-cheesy-nut-pasta': {'action': 'edit', 'patch': {
        'notes': 'Pasta in a creamy cheese sauce with toasted chopped nuts scattered on top.',
    }},
    # 223
    'corpus-peanut-butter-cake': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'A butter cake enriched with peanut butter and crowned with peanut-butter frosting.',
    }},
    # 224
    'corpus-roast-chicken': {'action': 'edit', 'patch': {
        'notes': 'A whole chicken roasted with herbs, citrus, and aromatics — Sunday dinner standard.',
    }},
    # 225
    'corpus-roast-turkey': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Whole turkey roasted with butter and herbs — the Thanksgiving centerpiece.',
    }},
    # 226
    'corpus-bacon-wrapped-meatloaf': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Ground beef loaf wrapped in strips of bacon and baked with a glazed top.',
    }},
    # 227
    'corpus-potato-with-vegetable': {'action': 'edit', 'patch': {
        'name': 'Creamed potatoes and vegetables',
        'notes': 'Boiled potatoes and mixed vegetables tossed with butter, milk, and seasonings.',
    }},
    # 228
    'corpus-buttered-pasta-with-veg': {'action': 'edit', 'patch': {
        'notes': 'Plain pasta tossed in melted butter with sautéed vegetables — a simple weeknight dish.',
    }},
    # 229
    'corpus-apple-egg-toast': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Toast topped with scrambled egg and warm sautéed apple slices.',
    }},
    # 230
    'corpus-nut-shortbread-4': {'action': 'edit', 'patch': {
        'tags': ['dessert'],
        'notes': 'A crumbly nut shortbread made with margarine and chopped nuts.',
    }},
    # 231
    'corpus-bean-vegetable-stew': {'action': 'edit', 'patch': {
        'notes': 'A long-simmered stew of beans, vegetables, and aromatics in a savory tomato broth.',
    }},
    # 232
    'corpus-lentil-salad': {'action': 'edit', 'patch': {
        'cuisine': 'Mediterranean',
        'notes': 'Cool cooked lentils tossed with diced vegetables, herbs, and a citrus vinaigrette.',
    }},
    # 233
    'corpus-beef-egg-fried-rice': {'action': 'edit', 'patch': {
        'cuisine': 'Chinese-American',
        'notes': 'Day-old rice stir-fried with diced beef, scrambled egg, and vegetables in a savory sauce.',
    }},
    # 234
    'corpus-cheese-pastry': {'action': 'edit', 'patch': {
        'cuisine': 'British',
        'tags': ['snack'],
        'notes': 'A short, flaky pastry enriched with grated aged cheese — eaten warm as a snack.',
    }},
    # 235
    'corpus-apple-walnut-sweet-potato-bread': {'action': 'edit', 'patch': {
        'notes': 'Spiced quick bread combining sweet potato, diced apple, and chopped walnuts.',
    }},
    # 236
    'corpus-date-nut-sweet-potato-bread': {'action': 'edit', 'patch': {
        'notes': 'Spiced quick bread with mashed sweet potato, chopped dates, and toasted nuts.',
    }},
    # 237
    'corpus-berry-nut-fruit-veg-salad': {'action': 'edit', 'patch': {
        'notes': 'Mixed greens tossed with berries, sliced fruit, and chopped nuts in a sweet-tangy dressing.',
    }},
    # 238
    'corpus-cheese-apple-sandwich': {'action': 'edit', 'patch': {
        'notes': 'Sliced apple and fresh cheese between buttered bread — a sweet-savory sandwich.',
    }},
    # 239 — wrong tag (was "dessert").
    'corpus-beef-fritters': {'action': 'edit', 'patch': {
        'tags': ['dinner', 'lunch'],
        'notes': 'Spiced ground beef bound with flour and pan-fried into crisp fritters.',
    }},
    # 240
    'corpus-beef-cheese-bowl': {'action': 'edit', 'patch': {
        'notes': 'A grain or rice bowl topped with seared beef, vegetables, and grated aged cheese.',
    }},
    # 241
    'corpus-apple-cheese-tart': {'action': 'edit', 'patch': {
        'tags': ['dessert', 'snack'],
        'notes': 'A short-crust tart with sliced apple and aged cheese baked until the apple softens and the cheese melts.',
    }},
    # 242
    'corpus-chicken-pasta-3': {'action': 'edit', 'patch': {
        'notes': 'Pasta tossed with sliced chicken, vegetables, and a touch of grated cheese in oil.',
    }},
    # 243
    'corpus-chicken-parmesan': {'action': 'edit', 'patch': {
        'cuisine': 'Italian-American',
        'notes': 'Breaded chicken cutlet topped with tomato sauce and melted mozzarella, baked until bubbling.',
    }},
    # 244
    'corpus-cheese-ham-roll': {'action': 'edit', 'patch': {
        'tags': ['snack', 'lunch'],
        'notes': 'Slices of cured ham rolled around processed cheese — a kid-friendly party snack.',
    }},
    # 245
    'corpus-beef-cheese-melt': {'action': 'edit', 'patch': {
        'notes': 'An open-faced sandwich with sliced beef and processed cheese broiled until melted.',
    }},
    # 246
    'corpus-vegetable-fried-rice': {'action': 'edit', 'patch': {
        'cuisine': 'Chinese-American',
        'notes': 'Day-old rice stir-fried with mixed vegetables, scrambled egg, and a splash of soy sauce.',
    }},
    # 247
    'corpus-pasta-primavera': {'action': 'edit', 'patch': {
        'cuisine': 'Italian-American',
        'notes': 'Pasta tossed with a medley of spring vegetables in a light butter-and-cheese sauce.',
    }},
    # 248
    'corpus-potato-custard-3': {'action': 'edit', 'patch': {
        'name': 'Potato custard',
        'notes': 'A baked sweet custard of mashed potato, eggs, milk, and butter.',
    }},
    # 249
    'corpus-latte': {'action': 'edit', 'patch': {
        'cuisine': 'Italian',
        'notes': 'Espresso topped with a tall pour of steamed milk — the Italian-style café latte.',
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

    print('compositional batch-2 audit applied.')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
