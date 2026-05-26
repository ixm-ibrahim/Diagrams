"""Compositional-meals audit batch 5 — final 135 unaudited entries.

Closes out compositional-meals.json. Re-run scripts/rederive_diet_compatibility.py after this.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'compositional-meals.json'

DECISIONS: dict[str, dict] = {
    'corpus-beef-soup': {'action': 'edit', 'patch': {
        'notes': 'Beef and vegetables simmered in seasoned broth until tender.',
    }},
    'corpus-apple-spinach-butter-saut': {'action': 'edit', 'patch': {
        'name': 'Apple-spinach butter sauté',
        'notes': 'Wilted spinach with sautéed apple in browned butter, finished with warm spices.',
    }},
    'corpus-apple-walnut-cheese-pancakes': {'action': 'edit', 'patch': {
        'notes': 'Pancakes with fresh cheese, diced apple, and chopped walnuts folded into the batter.',
    }},
    'corpus-yogurt-berry-cake': {'action': 'edit', 'patch': {
        'notes': 'A tender butter cake enriched with yogurt and studded with fresh berries.',
    }},
    'corpus-berry-cheesecake-with-nuts': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Cream-cheese cheesecake topped with fresh berries on a buttery crushed-nut crust.',
    }},
    'corpus-ricotta-with-american-cheese': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'notes': 'Whipped ricotta mixed with processed cheese and folded with raw vegetables — a creamy dip-style spread.',
    }},
    'corpus-chopped-liver': {'action': 'edit', 'patch': {
        'cuisine': 'Jewish',
        'tags': ['snack'],
        'notes': 'Chicken livers and hard-cooked eggs sautéed with onions and chopped together — the Ashkenazi appetizer.',
    }},
    'corpus-cheesy-potato-veg-bake': {'action': 'edit', 'patch': {
        'notes': 'Sliced potatoes and vegetables baked under melted processed cheese.',
    }},
    'corpus-cheesy-potato-gratin-9': {'action': 'edit', 'patch': {
        'name': 'Ricotta potato gratin',
        'cuisine': 'French',
        'notes': 'Sliced potatoes baked in butter with vegetables and a layer of fresh ricotta.',
    }},
    'corpus-apple-pasta-with-butter': {'action': 'edit', 'patch': {
        'notes': 'Pasta tossed with sautéed apple, butter, and warm spices — a sweet-savory bowl.',
    }},
    'corpus-yogurt-apple-nut-muffins': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Muffins made with yogurt, diced apple, and chopped nuts — tender and lightly sweet.',
    }},
    'corpus-veggie-potato-hash': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Diced potatoes and mixed vegetables fried crisp and topped with a runny egg.',
    }},
    'corpus-chicken-cheese-potato-bake': {'action': 'edit', 'patch': {
        'notes': 'Chicken and potatoes baked together with butter and a blanket of melted processed cheese.',
    }},
    'corpus-chicken-fried-rice': {'action': 'edit', 'patch': {
        'cuisine': 'Chinese-American',
        'notes': 'Day-old rice stir-fried with diced chicken, scrambled egg, and vegetables in a soy-based sauce.',
    }},
    'corpus-ham-cheese-sandwich': {'action': 'edit', 'patch': {
        'notes': 'Sliced cured ham and fresh cheese between bread with a smear of mustard or mayo.',
    }},
    'corpus-coffee-cake-with-cream': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'A coffee-flavored butter sponge cake with a cream filling or topping.',
    }},
    'corpus-chicken-cordon-bleu': {'action': 'edit', 'patch': {
        'cuisine': 'French',
        'notes': 'Chicken breasts pounded thin, stuffed with ham and aged cheese, breaded and pan-fried.',
    }},
    'corpus-bacon-quiche': {'action': 'edit', 'patch': {
        'cuisine': 'French',
        'tags': ['breakfast', 'lunch', 'dinner'],
        'notes': 'A buttery pastry shell filled with an egg-and-cream custard, bacon, and aged cheese — quiche lorraine.',
    }},
    'corpus-steak-egg-sandwich': {'action': 'edit', 'patch': {
        'tags': ['breakfast', 'lunch'],
        'notes': 'A breakfast sandwich with seared steak and a fried egg on a soft roll.',
    }},
    'corpus-apple-wine-veg-salad': {'action': 'edit', 'patch': {
        'contains_add': ['alcohol'],
        'notes': 'Mixed vegetables with diced apple tossed in a white-wine vinaigrette.',
    }},
    'corpus-beer-beef-potato-stew': {'action': 'edit', 'patch': {
        'cuisine': 'Belgian',
        'contains_add': ['alcohol'],
        'notes': 'Beef chunks braised in dark beer with potatoes, onions, and herbs — carbonade-style.',
    }},
    'corpus-wine-braised-chicken': {'action': 'edit', 'patch': {
        'cuisine': 'French',
        'contains_add': ['alcohol'],
        'notes': 'Chicken pieces braised in wine with butter and vegetables until the sauce reduces — coq au vin style.',
    }},
    'corpus-creamy-nut-apple-dessert': {'action': 'edit', 'patch': {
        'notes': 'Sautéed apple and chopped nuts folded into a sweet cream sauce.',
    }},
    'corpus-steak-with-parmesan': {'action': 'edit', 'patch': {
        'cuisine': 'Italian',
        'notes': 'Grilled steak finished with shavings of aged parmesan — bistecca-style.',
    }},
    'corpus-sesame-crackers': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'notes': 'Thin baked crackers studded with sesame seeds.',
    }},
    'corpus-berry-buttered-toast': {'action': 'edit', 'patch': {
        'tags': ['breakfast', 'snack'],
        'notes': 'Buttered toast topped with crushed fresh berries.',
    }},
    'corpus-apple-oatmeal': {'action': 'edit', 'patch': {
        'notes': 'Oats cooked with diced apple and a touch of sweetener — a breakfast bowl.',
    }},
    'corpus-cheese-greens-sandwich': {'action': 'edit', 'patch': {
        'notes': 'Aged cheese with leafy greens and other vegetables on bread.',
    }},
    'corpus-chicken-egg-veg-bowl': {'action': 'edit', 'patch': {
        'notes': 'A bowl of seasoned chicken with vegetables topped with a soft-cooked egg.',
    }},
    'corpus-bean-potato-bacon-stew': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'A long-simmered stew of beans, potatoes, and bacon in a savory broth.',
    }},
    'corpus-bacon-buttered-veg': {'action': 'edit', 'patch': {
        'notes': 'Mixed vegetables sautéed in butter and bacon fat with crisp bacon scattered on top.',
    }},
    'corpus-bacon-potatoes': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Diced potatoes fried crisp with strips of bacon — a hearty side or breakfast.',
    }},
    'corpus-pasta-with-bacon': {'action': 'edit', 'patch': {
        'cuisine': 'Italian',
        'notes': 'Pasta tossed with crisp bacon and a touch of its rendered fat — a minimal Italian pantry dish.',
    }},
    'corpus-sour-cream-raisin-cake': {'action': 'edit', 'patch': {
        'notes': 'A tender spiced butter cake enriched with sour cream and studded with raisins.',
    }},
    'corpus-chicken-with-ricotta': {'action': 'edit', 'patch': {
        'cuisine': 'Italian',
        'notes': 'Chicken pieces simmered in a tomato sauce and finished with a spoonful of fresh ricotta.',
    }},
    'corpus-bean-potato-stew-2': {'action': 'edit', 'patch': {
        'name': 'Bean and potato stew',
        'notes': 'Beans and potatoes simmered together with a touch of sweetener — a simple vegetarian stew.',
    }},
    'corpus-berry-apple-cheese-toast-2': {'action': 'edit', 'patch': {
        'tags': ['breakfast', 'snack'],
        'notes': 'Toast spread with fresh cheese and topped with berries and diced apple.',
    }},
    'corpus-liver-with-berry-fruit-sauce': {'action': 'edit', 'patch': {
        'notes': 'Pan-seared liver served with a sweet-tart fruit-and-berry pan sauce.',
    }},
    'corpus-peanut-lentil-bake': {'action': 'edit', 'patch': {
        'notes': 'Lentils baked into a sweet-savory loaf with peanut butter, eggs, and flour.',
    }},
    'corpus-cheesesteak': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Thinly sliced steak with melted processed cheese and onions in a long roll — Philadelphia-style.',
    }},
    'corpus-apple-cheese-omelet': {'action': 'edit', 'patch': {
        'notes': 'A folded omelet with sliced apple and fresh cheese tucked inside.',
    }},
    'corpus-bean-with-peanut-butter': {'action': 'edit', 'patch': {
        'cuisine': 'West African',
        'notes': 'Beans cooked with peanut butter into a creamy stew, served over grains.',
    }},
    'corpus-chicken-apple-nut-salad': {'action': 'edit', 'patch': {
        'notes': 'Cool salad of shredded chicken with diced apple, chopped nuts, and a creamy dressing.',
    }},
    'corpus-french-toast-with-nuts': {'action': 'edit', 'patch': {
        'notes': 'French toast topped with toasted nuts and a drizzle of syrup.',
    }},
    'corpus-chicken-cheese-pasta-2': {'action': 'edit', 'patch': {
        'notes': 'Pasta tossed with sliced chicken and a quick aged-cheese pan sauce.',
    }},
    'corpus-drunken-shrimp-risotto': {'action': 'edit', 'patch': {
        'cuisine': 'Italian',
        'contains_add': ['alcohol'],
        'notes': 'Risotto with shrimp sautéed in white wine, finished with herbs and lemon.',
    }},
    'corpus-steak-eggs': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'tags': ['breakfast'],
        'notes': 'Seared steak served alongside fried or scrambled eggs — the diner power breakfast.',
    }},
    'corpus-bacon-with-ricotta-3': {'action': 'edit', 'patch': {
        'name': 'Bacon and ricotta pasta',
        'cuisine': 'Italian',
        'notes': 'Pasta tossed with crisp bacon and a spoonful of whipped ricotta.',
    }},
    'corpus-buttery-nut-potato-bake': {'action': 'edit', 'patch': {
        'notes': 'Diced potatoes baked with butter, chopped nuts, and a touch of sweetener.',
    }},
    'corpus-steak-salad': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Sliced steak over greens with peppers, tomatoes, and crumbled cheese in a tangy dressing.',
    }},
    'corpus-apple-pasta-dessert': {'action': 'edit', 'patch': {
        'cuisine': 'Jewish',
        'notes': 'Sweet noodle pudding with diced apple, eggs, butter, and sugar — kugel-style.',
    }},
    'corpus-cheese-veg-sandwich-3': {'action': 'edit', 'patch': {
        'notes': 'Fresh cheese and sliced vegetables in bread — a plain vegetarian sandwich.',
    }},
    'corpus-bacon-broccoli': {'action': 'edit', 'patch': {
        'notes': 'Broccoli florets sautéed with crisp bacon in a pan sauce.',
    }},
    'corpus-veg-stuffed-pastry': {'action': 'edit', 'patch': {
        'notes': 'A flaky butter pastry baked around a savory vegetable filling.',
    }},
    'corpus-potato-bread': {'action': 'edit', 'patch': {
        'notes': 'A soft yeast bread enriched with mashed potato in the dough for a tender crumb.',
    }},
    'corpus-potato-cheese-gratin': {'action': 'edit', 'patch': {
        'cuisine': 'French',
        'notes': 'Sliced potatoes baked under a fresh-cheese custard until golden on top.',
    }},
    'corpus-cheesy-bacon-potato-bake': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Sliced potatoes baked with crisp bacon and a blanket of melted aged cheese.',
    }},
    'corpus-loaded-carbonara': {'action': 'edit', 'patch': {
        'cuisine': 'Italian-American',
        'notes': 'A heavy carbonara loaded with extra bacon, cheese, milk, and leafy greens.',
    }},
    'corpus-bread-potato-strata': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'A make-ahead breakfast bake of bread, potato, and eggs soaked in milk and baked until set.',
    }},
    'corpus-creamy-chicken-potato-bake': {'action': 'edit', 'patch': {
        'notes': 'Chicken thighs and potatoes baked in a herb-and-cream sauce.',
    }},
    'corpus-french-toast-with-batter': {'action': 'edit', 'patch': {
        'name': 'Battered French toast',
        'notes': 'French toast dipped in a flour-thickened batter for a thicker, sturdier coating.',
    }},
    'corpus-beef-sandwich': {'action': 'edit', 'patch': {
        'notes': 'Sliced beef on bread with vegetables and a savory sauce.',
    }},
    'corpus-date-walnut-cake': {'action': 'edit', 'patch': {
        'notes': 'A sticky spiced cake with chopped dates and walnuts folded into the batter.',
    }},
    'corpus-beef-pasta-bake-3': {'action': 'edit', 'patch': {
        'cuisine': 'Italian-American',
        'notes': 'Ground beef and tomato sauce baked over pasta with a layer of fresh cheese.',
    }},
    'corpus-beef-cheesy-pasta': {'action': 'edit', 'patch': {
        'notes': 'Pasta tossed with ground beef, vegetables, and melted processed cheese.',
    }},
    'corpus-buttered-bread-with-milk': {'action': 'drop', 'reason': 'staple pairing, not a coherent meal'},
    'corpus-beer-pretzels': {'action': 'edit', 'patch': {
        'cuisine': 'German',
        'tags': ['snack'],
        'contains_add': ['alcohol'],
        'notes': 'Cold beer with soft pretzels — a Bavarian beergarden snack.',
    }},
    'corpus-raisin-apple-compote': {'action': 'edit', 'patch': {
        'tags': ['dessert', 'snack'],
        'notes': 'Diced apple and raisins simmered with sugar until softened — a spoonable compote.',
    }},
    'corpus-shrimp-scampi': {'action': 'edit', 'patch': {
        'cuisine': 'Italian-American',
        'contains_add': ['alcohol'],
        'notes': 'Shrimp sautéed in garlic butter with lemon, white wine, and parsley.',
    }},
    'corpus-carrot-raisin-apple-cake': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Spiced cake with grated carrot, diced apple, and raisins folded in.',
    }},
    'corpus-chicken-with-feta': {'action': 'edit', 'patch': {
        'cuisine': 'Greek',
        'notes': 'Chicken pieces baked in a tomato-and-herb sauce and finished with crumbled feta.',
    }},
    'corpus-yogurt-bowl-3': {'action': 'edit', 'patch': {
        'name': 'Spiced yogurt bowl',
        'tags': ['breakfast', 'snack'],
        'notes': 'Yogurt seasoned with warm spices and a drizzle of melted butter or ghee.',
    }},
    'corpus-bean-apple-salad-3': {'action': 'edit', 'patch': {
        'name': 'Bean and apple salad',
        'notes': 'Cooked beans tossed with diced apple and a sweet vinaigrette.',
    }},
    'corpus-apple-creamy-pasta-bake': {'action': 'edit', 'patch': {
        'name': 'Apple creamy pasta bake',
        'tags': ['dessert', 'dinner'],
        'notes': 'Pasta baked in a sweet milk-and-egg custard with diced apple and warm spices — noodle kugel style.',
    }},
    'corpus-cheese-green-salad': {'action': 'edit', 'patch': {
        'notes': 'Leafy greens with aged cheese and a tangy vinaigrette.',
    }},
    'corpus-beef-potato-milk-stew': {'action': 'edit', 'patch': {
        'notes': 'Beef and potatoes simmered in milk and broth — a Scandinavian-leaning stew.',
    }},
    'corpus-cheese-veg-tart': {'action': 'edit', 'patch': {
        'cuisine': 'French',
        'notes': 'A short-crust tart with aged cheese and roasted vegetables in a butter-crust shell.',
    }},
    'corpus-apple-egg-fried-rice': {'action': 'edit', 'patch': {
        'notes': 'Day-old rice stir-fried with diced apple and scrambled egg — an unusual sweet-savory bowl.',
    }},
    'corpus-beef-cheese-bake': {'action': 'edit', 'patch': {
        'notes': 'Ground beef and vegetables baked under a two-cheese blanket.',
    }},
    'corpus-cheesy-bacon-potato-bake-2': {'action': 'edit', 'patch': {
        'notes': 'Potato slices baked with bacon and aged cheese until the top bronzes.',
    }},
    'corpus-date-nut-granola': {'action': 'edit', 'patch': {
        'notes': 'Oats baked with chopped dates, nuts, and a touch of butter and sweetener.',
    }},
    'corpus-beer-battered-chicken': {'action': 'edit', 'patch': {
        'cuisine': 'British',
        'contains_add': ['alcohol'],
        'notes': 'Chicken pieces dipped in a yeasty beer-based batter and fried crisp.',
    }},
    'corpus-creamy-oat-nut-porridge': {'action': 'edit', 'patch': {
        'notes': 'Oats simmered in milk and cream with toasted chopped nuts and vanilla.',
    }},
    'corpus-creamy-veg-casserole': {'action': 'edit', 'patch': {
        'notes': 'Mixed vegetables baked in a flour-thickened milk bechamel.',
    }},
    'corpus-apple-with-walnut': {'action': 'edit', 'patch': {
        'name': 'Apple with walnut yogurt',
        'tags': ['snack', 'breakfast'],
        'notes': 'Diced apple with yogurt, chopped walnuts, and a drizzle of sweetener.',
    }},
    'corpus-b-chamel-oat-bake': {'action': 'edit', 'patch': {
        'name': 'Béchamel oat bake',
        'notes': 'Oats baked in a butter-and-flour bechamel — a porridge-style savory bake.',
    }},
    'corpus-steak-potatoes': {'action': 'edit', 'patch': {
        'name': 'Steak and potatoes',
        'cuisine': 'American',
        'notes': 'A grilled or pan-seared steak with roasted or mashed potatoes alongside.',
    }},
    'corpus-three-cheese-pasta': {'action': 'edit', 'patch': {
        'cuisine': 'Italian',
        'notes': 'Pasta tossed with three cheeses (typically parmesan, pecorino, and ricotta) in a light cream sauce.',
    }},
    'corpus-berry-walnut-apple-bread': {'action': 'edit', 'patch': {
        'notes': 'A quick bread with diced apple, fresh berries, and chopped walnuts.',
    }},
    'corpus-cheesy-grain-bowl': {'action': 'edit', 'patch': {
        'notes': 'A whole-grain bowl topped with melted aged cheese and vegetables.',
    }},
    'corpus-chicken-apple-pasta': {'action': 'edit', 'patch': {
        'notes': 'Pasta tossed with sliced chicken, sautéed apple, and herbs in oil.',
    }},
    'corpus-strawberry-milk': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'notes': 'Cold milk blended or stirred with crushed strawberries and a touch of sugar.',
    }},
    'corpus-mac-cheese': {'action': 'edit', 'patch': {
        'name': 'Mac and cheese',
        'cuisine': 'American',
        'notes': 'Elbow macaroni in a cheddar-bechamel sauce — the diner-comfort classic.',
    }},
    'corpus-loaded-green-sandwich': {'action': 'edit', 'patch': {
        'notes': 'A sub-style sandwich layered with cured meat, aged cheese, greens, and a creamy sauce.',
    }},
    'corpus-beef-cheese-sandwich-2': {'action': 'edit', 'patch': {
        'name': 'Beef and cheese sandwich',
        'notes': 'Sliced beef and aged cheese on buttered bread with vegetables and a savory sauce.',
    }},
    'corpus-triple-cheese-veg-bake': {'action': 'edit', 'patch': {
        'notes': 'Vegetables baked under a blanket of three different cheeses with butter.',
    }},
    'corpus-white-russian': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'tags': ['snack'],
        'contains_add': ['alcohol'],
        'notes': 'Vodka with coffee liqueur and cream over ice — the cocktail of The Big Lebowski.',
    }},
    'corpus-three-cheese-toast': {'action': 'edit', 'patch': {
        'notes': 'Toast topped with three melted cheeses and a smear of sauce.',
    }},
    'corpus-berry-scones': {'action': 'edit', 'patch': {
        'cuisine': 'British',
        'tags': ['breakfast', 'snack'],
        'notes': 'Buttery scones studded with fresh or dried berries — served warm with butter or cream.',
    }},
    'corpus-apple-almond-milk-drink': {'action': 'edit', 'patch': {
        'tags': ['snack', 'breakfast'],
        'notes': 'Almond milk blended with apple and a touch of sweetener — a dairy-free drink.',
    }},
    'corpus-berry-yogurt-smoothie': {'action': 'edit', 'patch': {
        'notes': 'Berries, yogurt, milk, and sliced fruit blended into a thick drinkable smoothie.',
    }},
    'corpus-cheese-stuffed-beef': {'action': 'edit', 'patch': {
        'cuisine': 'Italian',
        'notes': 'Sliced beef rolled or stuffed around fresh cheese and braised in a pan sauce — braciole-style.',
    }},
    'corpus-cheesy-chicken': {'action': 'edit', 'patch': {
        'notes': 'Chicken finished with melted aged cheese and a butter pan sauce.',
    }},
    'corpus-cheese-nut-veg-plate': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'notes': 'A grazing plate of cheeses, toasted nuts, and raw vegetables with a small dip.',
    }},
    'corpus-spiked-custard': {'action': 'edit', 'patch': {
        'contains_add': ['alcohol'],
        'notes': 'A baked egg-and-cream custard with a slug of spirit stirred in — bourbon or rum custard.',
    }},
    'corpus-veggie-cheese-strata': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'A make-ahead bake of bread, eggs, broccoli, and aged cheese soaked in milk and baked until set.',
    }},
    'corpus-berry-cheese-french-toast': {'action': 'edit', 'patch': {
        'notes': 'French toast filled with cream cheese and topped with fresh berries.',
    }},
    'corpus-date-nut-whole-wheat-cake': {'action': 'edit', 'patch': {
        'notes': 'A dense whole-wheat cake with chopped dates and walnuts folded into the batter.',
    }},
    'corpus-potato-pastry': {'action': 'edit', 'patch': {
        'notes': 'A short-crust pastry enriched with mashed potato for a tender, crumbly bite.',
    }},
    'corpus-sour-cream-apple-walnut-raisin-cake': {'action': 'edit', 'patch': {
        'notes': 'A tender butter cake with sour cream, diced apple, chopped walnuts, and raisins.',
    }},
    'corpus-salmon-fruit-cheese-salad': {'action': 'edit', 'patch': {
        'notes': 'Flaked salmon over greens with sliced fruit, crumbled cheese, and toasted nuts.',
    }},
    'corpus-curry-pasta': {'action': 'edit', 'patch': {
        'notes': 'Pasta tossed in a spiced curry-style sauce with mixed vegetables.',
    }},
    'corpus-date-nut-granola-bars': {'action': 'edit', 'patch': {
        'notes': 'Oats, chopped dates, and nuts pressed into bars bound with butter and a sweetener.',
    }},
    'corpus-raisin-scones': {'action': 'edit', 'patch': {
        'cuisine': 'British',
        'tags': ['breakfast', 'snack'],
        'notes': 'Buttery scones studded with raisins — served warm with butter, jam, or clotted cream.',
    }},
    'corpus-oatmeal-with-milk': {'action': 'edit', 'patch': {
        'name': 'Milk oatmeal',
        'notes': 'Rolled oats simmered in milk with a touch of sweetener and vanilla.',
    }},
    'corpus-beef-sesame-stir-fry': {'action': 'edit', 'patch': {
        'cuisine': 'Korean',
        'notes': 'Beef strips stir-fried with sesame oil and seeds, vegetables, and a savory-sweet sauce.',
    }},
    'corpus-ham-cheese-sub': {'action': 'edit', 'patch': {
        'cuisine': 'Italian-American',
        'notes': 'Cured ham and aged cheese on a long sub roll with lettuce and onion.',
    }},
    'corpus-apple-nut-veg-salad': {'action': 'edit', 'patch': {
        'notes': 'Mixed vegetables with sliced apple and chopped nuts in a herb vinaigrette.',
    }},
    'corpus-beef-cheese-grain-bowl': {'action': 'edit', 'patch': {
        'notes': 'A whole-grain bowl with seared beef, vegetables, and grated aged cheese.',
    }},
    'corpus-meat-lasagna': {'action': 'edit', 'patch': {
        'cuisine': 'Italian-American',
        'notes': 'Layered pasta with ricotta, ground beef, and cured meat in a tomato sauce.',
    }},
    'corpus-apple-broccoli-slaw': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Shredded broccoli stems and apple in a tangy-sweet slaw-style dressing.',
    }},
    'corpus-yogurt-dressed-veg': {'action': 'edit', 'patch': {
        'cuisine': 'Mediterranean',
        'notes': 'Raw or roasted vegetables tossed in a herbed yogurt dressing.',
    }},
    'corpus-berry-almond-smoothie': {'action': 'edit', 'patch': {
        'notes': 'Berries blended with almonds, milk, and sliced fruit into a creamy smoothie.',
    }},
    'corpus-nutty-cheese-eggs': {'action': 'edit', 'patch': {
        'tags': ['breakfast'],
        'notes': 'Scrambled eggs with fresh cheese and chopped nuts folded through.',
    }},
    'corpus-coffee-cream-cake': {'action': 'edit', 'patch': {
        'cuisine': 'British',
        'notes': 'A coffee-flavored butter cake layered with whipped cream.',
    }},
    'corpus-raisin-oat-bread': {'action': 'edit', 'patch': {
        'notes': 'A whole-grain loaf with rolled oats and raisins in the dough.',
    }},
    'corpus-berry-dried-fruit-mix': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'notes': 'Mixed dried fruit and fresh berries — a sweet trail-mix-style snack.',
    }},
    'corpus-beef-pasta-gratin': {'action': 'edit', 'patch': {
        'cuisine': 'Italian-American',
        'notes': 'Pasta baked with ground beef, greens, and a milk-and-egg custard under a cheese crust.',
    }},
    'corpus-date-pecan-bread-pudding': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Bread soaked in a sweet egg-and-milk custard with chopped dates and pecans, baked until set.',
    }},
    'corpus-cheese-crackers': {'action': 'edit', 'patch': {
        'tags': ['snack'],
        'notes': 'Crisp baked crackers with grated aged cheese in the dough.',
    }},
    'corpus-nut-bread': {'action': 'edit', 'patch': {
        'notes': 'A quick bread with chopped nuts folded into a sweet egg-and-milk batter.',
    }},
    'corpus-toasted-nut-crostini': {'action': 'edit', 'patch': {
        'cuisine': 'Italian',
        'tags': ['snack'],
        'notes': 'Toasted bread rounds topped with chopped nuts and a drizzle of butter or oil.',
    }},
    'corpus-sweet-potato-cake': {'action': 'edit', 'patch': {
        'notes': 'A spiced butter cake made with mashed sweet potato — similar to a carrot cake variant.',
    }},
    'corpus-grilled-cheese': {'action': 'edit', 'patch': {
        'cuisine': 'American',
        'notes': 'Buttered bread filled with sliced aged cheese and griddled until the outside crisps and the inside melts.',
    }},
    'corpus-cheese-on-toast': {'action': 'edit', 'patch': {
        'cuisine': 'British',
        'tags': ['snack', 'lunch'],
        'notes': 'Aged cheese melted on toast under the grill — the British snack staple.',
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

    print('compositional batch-5 audit applied (FINAL).')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
