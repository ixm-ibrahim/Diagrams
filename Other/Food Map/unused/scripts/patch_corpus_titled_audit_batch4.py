"""Corpus-titled meals audit — batch 4 (entries 451-600 by frequency, 228 -> 180).

Same standard: idiomatic sentence-case name, 1-2 sentence factual notes,
clean ingredient_categories, real-world tags, cuisine where the name implies
one, contains:['pork'] / ['alcohol'] only when traditionally mandatory.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

DECISIONS: dict[str, dict] = {
    'corpus-titled-chicken-rice-casserole': {'action': 'edit', 'patch': {
        'name': 'Chicken rice casserole',
        'notes': 'Raw rice and chicken pieces baked together in cream of mushroom soup and a packet of onion soup mix — a hands-off one-dish meal.',
        'cuisine': 'American',
    }},
    'corpus-titled-millionaire-pie': {'action': 'edit', 'patch': {
        'name': 'Millionaire pie',
        'notes': 'A no-bake pie of sweetened condensed milk whipped with lemon juice and folded with crushed pineapple, pecans, and whipped topping — set in a graham crust.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-peanut-clusters': {'action': 'edit', 'patch': {
        'name': 'Peanut clusters',
        'tags': ['dessert', 'snack'],
        'notes': 'Roasted peanuts stirred into melted chocolate and dropped onto wax paper to set — a two-ingredient candy.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-white-bread': {'action': 'edit', 'patch': {
        'name': 'White bread',
        'notes': 'A basic enriched yeasted loaf of bread flour, milk, sugar, butter, and yeast — soft and sandwich-friendly.',
        'serving_grams': 55,
    }},
    'corpus-titled-scripture-cake': {'action': 'edit', 'patch': {
        'name': 'Scripture cake',
        'notes': 'A spiced fruit-and-nut cake whose ingredients are named by their Bible references (Jeremiah\'s figs, Genesis\'s butter, etc.) — a Victorian church-supper novelty.',
        'cuisine': 'American',
    }},
    'corpus-titled-orange-jello-salad': {'action': 'edit', 'patch': {
        'name': 'Orange Jello salad',
        'tags': ['dessert'],
        'notes': 'Orange gelatin set with mandarin oranges, crushed pineapple, and cottage cheese — sometimes layered with whipped topping.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-italian-beef': {'action': 'edit', 'patch': {
        'name': 'Italian beef',
        'notes': 'Thin-sliced beef slow-cooked in Italian-seasoned broth with giardiniera and bell peppers, piled on a long roll — the Chicago specialty.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-hawaiian-chicken': {'action': 'edit', 'patch': {
        'name': 'Hawaiian chicken',
        'notes': 'Chicken pieces baked or simmered in a sweet-tangy pineapple-and-soy or barbecue sauce, served over rice.',
        'cuisine': 'American',
    }},
    'corpus-titled-chili-dip': {'action': 'edit', 'patch': {
        'name': 'Chili dip',
        'tags': ['snack'],
        'notes': 'Cream cheese spread in a dish, topped with canned chili and shredded cheese, then warmed until bubbly — a tailgate favorite.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-funnel-cakes': {'action': 'edit', 'patch': {
        'name': 'Funnel cake',
        'notes': 'A pancake-like batter drizzled in concentric circles into hot oil, fried crisp, and dusted heavily with powdered sugar — a fairground classic.',
        'cuisine': 'American',
    }},
    'corpus-titled-blackberry-cobbler': {'action': 'edit', 'patch': {
        'name': 'Blackberry cobbler',
        'notes': 'Sweetened fresh blackberries baked under a tender biscuit or batter topping — served warm with ice cream.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-hungarian-goulash': {'action': 'edit', 'patch': {
        'name': 'Hungarian goulash',
        'notes': 'Cubed beef slow-stewed with onions, peppers, and a generous amount of sweet paprika in a rich tomato-paprika gravy.',
        'cuisine': 'Hungarian',
    }},
    'corpus-titled-rum-cake': {'action': 'edit', 'patch': {
        'name': 'Rum cake',
        'notes': 'A yellow-cake-mix Bundt with chopped pecans on the bottom, soaked after baking with a butter-sugar-rum syrup — Bacardi\'s classic.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-party-potatoes': {'action': 'edit', 'patch': {
        'name': 'Party potatoes',
        'notes': 'Mashed potatoes whipped with cream cheese, sour cream, butter, and onion — a make-ahead potluck side baked until golden on top.',
        'cuisine': 'American',
    }},
    'corpus-titled-icebox-cookies': {'action': 'edit', 'patch': {
        'name': 'Icebox cookies',
        'notes': 'A butter-sugar dough rolled into a log, chilled, then sliced and baked — yields uniform rounds of shortbread or spice cookie.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-applesauce': {'action': 'edit', 'patch': {
        'name': 'Applesauce',
        'tags': ['snack'],
        'notes': 'Peeled apples simmered with sugar, cinnamon, and lemon until soft, then mashed smooth or chunky — eaten as a side or snack.',
        'serving_grams': 120,
    }},
    'corpus-titled-stuffed-cabbage': {'action': 'edit', 'patch': {
        'name': 'Stuffed cabbage',
        'notes': 'Blanched cabbage leaves wrapped around seasoned ground beef and rice, then baked in tomato sauce — Eastern European golabki / golumpki.',
        'cuisine': 'Eastern European',
    }},
    'corpus-titled-egg-rolls': {'action': 'edit', 'patch': {
        'name': 'Egg rolls',
        'notes': 'Wheat wrappers rolled around stir-fried cabbage, pork, shrimp, and aromatics, then deep-fried golden — Chinese-American takeout style.',
        'cuisine': 'Chinese-American',
        'contains_add': ['pork'],
        'serving_grams': 100,
    }},
    'corpus-titled-gooey-butter-cake': {'action': 'edit', 'patch': {
        'name': 'Gooey butter cake',
        'notes': 'A yellow cake mix base topped with a cream-cheese-egg-and-powdered-sugar layer that bakes to a gooey, soft middle — St. Louis original.',
        'cuisine': 'American',
    }},
    'corpus-titled-angel-food-cake': {'action': 'edit', 'patch': {
        'name': 'Angel food cake',
        'notes': 'A fat-free white sponge cake leavened only by whipped egg whites, baked in a tube pan and inverted to cool.',
        'cuisine': 'American',
    }},
    'corpus-titled-apple-dip': {'action': 'edit', 'patch': {
        'name': 'Caramel apple dip',
        'tags': ['snack', 'dessert'],
        'notes': 'Cream cheese whipped with brown sugar, vanilla, and toffee bits — served with sliced apples for dipping.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-chocolate-cream-pie': {'action': 'edit', 'patch': {
        'name': 'Chocolate cream pie',
        'notes': 'A baked pastry shell filled with a cooked chocolate pudding, topped with whipped cream and chocolate shavings.',
        'cuisine': 'American',
    }},
    'corpus-titled-christmas-punch': {'action': 'edit', 'patch': {
        'name': 'Christmas punch',
        'ingredient_categories': ['Juices', 'Citrus', 'Sugar & sweeteners', 'Tropical fruits', 'Berries', 'Soft drinks'],
        'tags': ['snack'],
        'notes': 'A non-alcoholic holiday punch of cranberry juice, orange juice, pineapple juice, and ginger ale — served from a bowl over ice.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-blueberry-cake': {'action': 'edit', 'patch': {
        'name': 'Blueberry cake',
        'notes': 'A tender butter cake folded with fresh or frozen blueberries — sometimes a coffee-cake style with a crumb topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-persimmon-pudding': {'action': 'edit', 'patch': {
        'name': 'Persimmon pudding',
        'notes': 'A dense baked pudding-cake of persimmon pulp, sugar, eggs, milk, and spices — a Midwestern autumn dessert.',
        'cuisine': 'American',
    }},
    'corpus-titled-beef-casserole': {'action': 'edit', 'patch': {
        'name': 'Beef casserole',
        'notes': 'Ground or cubed beef baked with rice or noodles, vegetables, mushrooms, and cheese — a one-dish weeknight bake.',
    }},
    'corpus-titled-lemon-bread': {'action': 'edit', 'patch': {
        'name': 'Lemon bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A sweet quick bread bright with lemon zest and juice, finished with a tart lemon-sugar glaze.',
        'cuisine': 'American',
    }},
    'corpus-titled-summer-squash-casserole': {'action': 'edit', 'patch': {
        'name': 'Summer squash casserole',
        'notes': 'Sliced yellow squash cooked tender, mixed with sour cream and cream of chicken soup, and baked under a buttery-cracker top.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-doughnuts': {'action': 'edit', 'patch': {
        'name': 'Doughnuts',
        'tags': ['dessert', 'breakfast'],
        'notes': 'A leavened or cake-style ring of dough deep-fried and finished with glaze, sugar, or cinnamon-sugar.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-raisin-pie': {'action': 'edit', 'patch': {
        'name': 'Raisin pie',
        'notes': 'A double-crust pie of raisins simmered with sugar, lemon, and a touch of flour or cornstarch — "funeral pie" in Pennsylvania Dutch tradition.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-and-dressing-casserole': {'action': 'edit', 'patch': {
        'name': 'Chicken and dressing casserole',
        'notes': 'Cooked chicken layered with seasoned cornbread or stuffing dressing and bound with cream of mushroom soup — a Southern Thanksgiving-into-leftovers bake.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-broccoli-corn-bread': {'action': 'edit', 'patch': {
        'name': 'Broccoli cornbread',
        'tags': ['dinner', 'lunch'],
        'notes': 'A skillet cornbread enriched with chopped broccoli, cottage cheese, eggs, and butter — moist and savory.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-pumpkin-pie-cake': {'action': 'edit', 'patch': {
        'name': 'Pumpkin pie cake (pumpkin dump cake)',
        'notes': 'A pumpkin-pie custard layered under a yellow cake mix and pats of butter, baked into a self-streuseled hybrid dessert.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-piccata': {'action': 'edit', 'patch': {
        'name': 'Chicken piccata',
        'notes': 'Pounded chicken cutlets dredged in flour and pan-fried, finished in a lemon-and-white-wine pan sauce with capers and butter.',
        'cuisine': 'Italian-American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-toffee-bars': {'action': 'edit', 'patch': {
        'name': 'Toffee bars',
        'tags': ['dessert'],
        'notes': 'A brown-sugar-and-butter shortbread topped with melted chocolate and chopped nuts, cut into bars while still warm.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-pistachio-cake': {'action': 'edit', 'patch': {
        'name': 'Pistachio cake',
        'notes': 'A green-tinted Bundt cake from yellow-cake-mix and instant pistachio pudding, often made with club soda or 7-Up for tenderness.',
        'cuisine': 'American',
    }},
    'corpus-titled-reuben-casserole': {'action': 'edit', 'patch': {
        'name': 'Reuben casserole',
        'notes': 'Layered corned beef, sauerkraut, Swiss cheese, and rye breadcrumbs baked with Thousand Island dressing — Reuben sandwich flavors in casserole form.',
        'cuisine': 'American',
    }},
    'corpus-titled-cherry-dessert': {'action': 'edit', 'patch': {
        'name': 'Cherry dessert',
        'notes': 'Cherry pie filling layered with sweetened cream cheese, a graham or pretzel crust, and whipped topping — a no-bake Southern dessert.',
        'cuisine': 'American',
    }},
    'corpus-titled-king-ranch-chicken': {'action': 'edit', 'patch': {
        'name': 'King Ranch chicken',
        'notes': 'A Texas casserole of shredded chicken, tortilla strips, Rotel tomatoes-and-chiles, mushroom soup, and Velveeta — baked until creamy and bubbling.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-sweetened-condensed-milk': {'action': 'drop', 'reason': 'ingredient/component, not a coherent meal'},
    'corpus-titled-cheese-wafers': {'action': 'edit', 'patch': {
        'name': 'Cheese wafers',
        'tags': ['snack'],
        'notes': 'A short cheddar-and-butter dough piped or sliced from a log and baked into thin crisp savory rounds — cousin of cheese straws.',
        'cuisine': 'Southern',
        'serving_grams': 30,
    }},
    'corpus-titled-cheese-bread': {'action': 'edit', 'patch': {
        'name': 'Cheese bread',
        'notes': 'A quick bread or yeast loaf with shredded cheese baked into the dough and sometimes sprinkled on top.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-peanut-blossoms': {'action': 'edit', 'patch': {
        'name': 'Peanut butter blossoms',
        'tags': ['dessert'],
        'notes': 'Peanut butter cookies rolled in sugar and pressed with a Hershey\'s Kiss as soon as they come out of the oven.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-buttermilk-salad': {'action': 'edit', 'patch': {
        'name': 'Buttermilk salad',
        'tags': ['dessert'],
        'notes': 'Crushed pineapple cooked with orange Jello and folded into buttermilk and whipped topping — a tangy chilled Southern dessert salad.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-pizza-sauce': {'action': 'drop', 'reason': 'sauce component, not a coherent meal'},
    'corpus-titled-butterscotch-brownies': {'action': 'edit', 'patch': {
        'name': 'Butterscotch brownies',
        'notes': 'A brown-sugar-and-butter blondie packed with butterscotch chips and pecans — chewy and caramel-sweet.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-cocktail-meatballs': {'action': 'edit', 'patch': {
        'name': 'Cocktail meatballs',
        'tags': ['snack'],
        'notes': 'Small meatballs simmered in a sauce of grape jelly and chili sauce (or barbecue sauce) — held warm in a slow cooker for parties.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-five-cup-salad': {'action': 'edit', 'patch': {
        'name': 'Five cup salad',
        'tags': ['dessert'],
        'notes': 'Equal cups of mandarin oranges, pineapple chunks, mini marshmallows, shredded coconut, and sour cream — chilled and stirred together.',
        'cuisine': 'American',
    }},
    'corpus-titled-icebox-fruit-cake': {'action': 'edit', 'patch': {
        'name': 'Icebox fruitcake',
        'notes': 'A no-bake fruitcake of crushed graham crackers or vanilla wafers mixed with candied fruit, dates, nuts, and sweetened condensed milk — pressed in a pan and chilled.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-turkey-tetrazzini': {'action': 'edit', 'patch': {
        'name': 'Turkey tetrazzini',
        'notes': 'Cooked turkey baked with spaghetti or linguine, mushrooms, and a sherry-cream sauce under Parmesan and breadcrumbs — a Thanksgiving leftover staple.',
        'cuisine': 'Italian-American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-lemon-icebox-pie': {'action': 'edit', 'patch': {
        'name': 'Lemon icebox pie',
        'notes': 'A no-bake pie of lemon juice whisked into sweetened condensed milk and egg yolks, chilled in a graham crust — set by acid, not baking.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-caramel-pie': {'action': 'edit', 'patch': {
        'name': 'Caramel pie',
        'notes': 'A pie of brown-sugar-and-milk caramel pudding poured into a baked crust, topped with whipped cream — sometimes made with boiled sweetened condensed milk.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-hominy-casserole': {'action': 'edit', 'patch': {
        'name': 'Hominy casserole',
        'notes': 'Canned hominy baked with cheese, green chiles, and sour cream until bubbly — a Southwestern side.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-seafood-casserole': {'action': 'edit', 'patch': {
        'name': 'Seafood casserole',
        'notes': 'Shrimp, crab, or scallops baked with rice or cracker crumbs in a cream-or-mushroom-soup sauce, topped with cheese or buttered crumbs.',
        'cuisine': 'American',
    }},
    'corpus-titled-fruit-cake-cookies': {'action': 'edit', 'patch': {
        'name': 'Fruitcake cookies',
        'notes': 'Drop cookies of candied fruit, dates, raisins, and pecans bound by a buttermilk-and-bourbon-style spiced batter — fruitcake flavor in a cookie.',
        'cuisine': 'Southern',
        'serving_grams': 30,
    }},
    'corpus-titled-pico-de-gallo': {'action': 'edit', 'patch': {
        'name': 'Pico de gallo',
        'tags': ['snack', 'condiment'],
        'notes': 'Diced tomato, white onion, jalapeño, cilantro, and lime — a fresh, chunky Mexican salsa served as a dip or topping.',
        'cuisine': 'Mexican',
        'serving_grams': 60,
    }},
    'corpus-titled-christmas-cookies': {'action': 'edit', 'patch': {
        'name': 'Christmas cookies',
        'notes': 'A category-name for spiced and decorated rolled or drop cookies baked for the holidays — typically sugar, gingerbread, or fruit-and-nut.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-broccoli-bread': {'action': 'edit', 'patch': {
        'name': 'Broccoli bread',
        'notes': 'A savory cornbread enriched with chopped broccoli, cottage cheese, butter, and eggs — baked in a skillet or pan.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-potatoes': {'action': 'edit', 'patch': {
        'name': 'Cheesy baked potatoes',
        'notes': 'Sliced or cubed potatoes baked with butter, sour cream, cheese, and onions — generic "potatoes" usually means the funeral-potatoes side.',
        'cuisine': 'American',
    }},
    'corpus-titled-orange-balls': {'action': 'edit', 'patch': {
        'name': 'Orange balls',
        'tags': ['dessert', 'snack'],
        'notes': 'Crushed vanilla wafers mixed with butter, frozen orange juice concentrate, and powdered sugar, rolled into balls and coated with coconut.',
        'cuisine': 'Southern',
        'serving_grams': 30,
    }},
    'corpus-titled-chocolate-ice-cream': {'action': 'edit', 'patch': {
        'name': 'Chocolate ice cream',
        'notes': 'A churned custard of cocoa or melted chocolate, milk, cream, sugar, and egg yolks — the chocolate baseline.',
        'serving_grams': 85,
    }},
    'corpus-titled-tortilla-roll-ups': {'action': 'edit', 'patch': {
        'name': 'Tortilla roll-ups',
        'tags': ['snack'],
        'notes': 'Flour tortillas spread with seasoned cream cheese, salsa, olives, and green chiles, rolled and sliced into pinwheels.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 80,
    }},
    'corpus-titled-sweet-pickles': {'action': 'drop', 'reason': 'pickled condiment, not a coherent meal'},
    'corpus-titled-fettuccine-alfredo': {'action': 'edit', 'patch': {
        'name': 'Fettuccine alfredo',
        'notes': 'Fresh fettuccine tossed with butter and grated Parmesan until emulsified into a creamy sauce — American versions add heavy cream.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-buffalo-chicken-dip': {'action': 'edit', 'patch': {
        'name': 'Buffalo chicken dip',
        'tags': ['snack'],
        'notes': 'Shredded chicken baked with cream cheese, ranch or blue cheese dressing, and Buffalo wing sauce, topped with shredded cheese.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-german-chocolate-pie': {'action': 'edit', 'patch': {
        'name': 'German chocolate pie',
        'notes': 'A baked chocolate-and-evaporated-milk custard topped with the classic coconut-pecan caramel — German chocolate cake flavors in a pie.',
        'cuisine': 'American',
    }},
    'corpus-titled-stuffed-zucchini': {'action': 'edit', 'patch': {
        'name': 'Stuffed zucchini',
        'notes': 'Zucchini halved lengthwise, hollowed, and filled with seasoned ground beef or sausage, breadcrumbs, and cheese, then baked.',
    }},
    'corpus-titled-spinach-quiche': {'action': 'edit', 'patch': {
        'name': 'Spinach quiche',
        'notes': 'A butter pastry shell filled with an egg-and-cream custard, sautéed spinach, and Swiss or feta — a meatless quiche variant.',
        'cuisine': 'French',
    }},
    'corpus-titled-chocolate-pudding': {'action': 'edit', 'patch': {
        'name': 'Chocolate pudding',
        'notes': 'Cocoa, sugar, milk, and cornstarch cooked into a thick pudding with butter and vanilla — chilled with plastic wrap pressed on the surface.',
    }},
    'corpus-titled-broccoli-and-cauliflower-salad': {'action': 'edit', 'patch': {
        'name': 'Broccoli and cauliflower salad',
        'notes': 'Raw broccoli and cauliflower florets tossed with bacon, red onion, and a sweet mayonnaise dressing — broccoli-salad style.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-sausage-cheese-balls': {'action': 'edit', 'patch': {
        'name': 'Sausage cheese balls',
        'ingredient_categories': ['Processed meat', 'Aged cheese', 'Prepared mixes'],
        'tags': ['snack', 'breakfast'],
        'notes': 'Bite-size baked balls of breakfast sausage, shredded cheddar, and biscuit mix — the same Southern appetizer as sausage balls.',
        'cuisine': 'American',
        'contains_add': ['pork'],
        'serving_grams': 60,
    }},
    'corpus-titled-banana-punch': {'action': 'edit', 'patch': {
        'name': 'Banana punch',
        'ingredient_categories': ['Juices', 'Tropical fruits', 'Citrus', 'Sugar & sweeteners', 'Soft drinks'],
        'tags': ['snack'],
        'notes': 'Mashed bananas blended with frozen juice concentrates and sugar, frozen, then thinned with ginger ale at serving — a slushy non-alcoholic party punch.',
        'cuisine': 'Southern',
        'serving_grams': 240,
    }},
    'corpus-titled-hot-cocoa-mix': {'action': 'edit', 'patch': {
        'name': 'Hot cocoa mix',
        'ingredient_categories': ['Sugar & sweeteners', 'Milk', 'Candy & desserts'],
        'notes': 'A pantry mix of powdered milk, cocoa, sugar, and powdered creamer — stirred into hot water for instant cocoa.',
        'serving_grams': 240,
    }},
    'corpus-titled-stew': {'action': 'edit', 'patch': {
        'name': 'Beef stew',
        'notes': 'Cubed beef braised slowly with potatoes, carrots, onions, and seasonings in beef broth until thick and tender.',
    }},
    'corpus-titled-pickled-eggs': {'action': 'drop', 'reason': 'pickled preserve / bar snack, not a coherent meal'},
    'corpus-titled-cherry-cobbler': {'action': 'edit', 'patch': {
        'name': 'Cherry cobbler',
        'notes': 'Sweet-tart cherries baked under a tender biscuit or batter topping — served warm with cream or ice cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-guacamole-dip': {'action': 'edit', 'patch': {
        'name': 'Guacamole dip',
        'tags': ['snack'],
        'notes': 'Mashed avocados seasoned with lime, salt, onion, jalapeño, and cilantro — eaten with tortilla chips.',
        'cuisine': 'Mexican',
        'serving_grams': 60,
    }},
    'corpus-titled-strawberry-pizza': {'action': 'edit', 'patch': {
        'name': 'Strawberry pizza',
        'tags': ['dessert'],
        'notes': 'A sugar-cookie crust spread with sweetened cream cheese and topped with sliced fresh strawberries and a strawberry glaze.',
        'cuisine': 'American',
    }},
    'corpus-titled-oyster-stew': {'action': 'edit', 'patch': {
        'name': 'Oyster stew',
        'notes': 'Shucked oysters and their liquor simmered briefly in butter, milk, and cream with celery and onions — a New England Christmas tradition.',
        'cuisine': 'American',
    }},
    'corpus-titled-apple-fritters': {'action': 'edit', 'patch': {
        'name': 'Apple fritters',
        'tags': ['dessert', 'breakfast'],
        'notes': 'Chopped apples folded into a leavened batter, dropped into hot oil, fried golden, and finished with cinnamon-sugar or a glaze.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-and-dressing': {'action': 'edit', 'patch': {
        'name': 'Chicken and dressing',
        'notes': 'Shredded cooked chicken served alongside or layered with seasoned cornbread or bread dressing — Thanksgiving plate, Southern style.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-blueberry-cobbler': {'action': 'edit', 'patch': {
        'name': 'Blueberry cobbler',
        'notes': 'Sweetened fresh or frozen blueberries baked under a buttery biscuit or cake topping — served warm with ice cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-marinated-vegetable-salad': {'action': 'edit', 'patch': {
        'name': 'Marinated vegetable salad',
        'notes': 'Cooked or raw mixed vegetables tossed in an oil-and-vinegar dressing with sugar and herbs — chilled overnight as a make-ahead side.',
    }},
    'corpus-titled-ginger-cookies': {'action': 'edit', 'patch': {
        'name': 'Ginger cookies',
        'notes': 'Soft or crisp spiced cookies of butter, molasses, brown sugar, ground ginger, and warm spices — rolled in sugar before baking.',
        'serving_grams': 30,
    }},
    'corpus-titled-ice-cream-cake': {'action': 'edit', 'patch': {
        'name': 'Ice cream cake',
        'notes': 'Layers of ice cream pressed into a cake pan with a cookie or crumb base, frozen solid, then frosted with whipped cream.',
        'cuisine': 'American',
        'serving_grams': 120,
    }},
    'corpus-titled-sweet-potato-pudding': {'action': 'edit', 'patch': {
        'name': 'Sweet potato pudding',
        'notes': 'Grated raw or mashed cooked sweet potato baked with eggs, milk, sugar, butter, and warm spices into a soft custard-cake.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-minestrone': {'action': 'edit', 'patch': {
        'name': 'Minestrone',
        'notes': 'A thick Italian vegetable soup of beans, pasta, and seasonal vegetables in a tomato-and-Parmesan-rind broth.',
        'cuisine': 'Italian',
    }},
    'corpus-titled-raisin-bran-muffins': {'action': 'edit', 'patch': {
        'name': 'Raisin bran muffins',
        'tags': ['breakfast'],
        'notes': 'High-fiber muffins of wheat bran or bran cereal, raisins, buttermilk, and a touch of molasses — moist and lightly sweet.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-mashed-potato-casserole': {'action': 'edit', 'patch': {
        'name': 'Mashed potato casserole',
        'notes': 'Mashed potatoes whipped with cream cheese, sour cream, butter, and seasonings, baked under shredded cheese — make-ahead party potatoes.',
        'cuisine': 'American',
    }},
    'corpus-titled-corn-dogs': {'action': 'edit', 'patch': {
        'name': 'Corn dogs',
        'tags': ['snack', 'lunch'],
        'notes': 'Hot dogs on a stick dipped in a sweetened cornmeal batter and deep-fried golden — a fairground staple.',
        'cuisine': 'American',
        'contains_add': ['pork'],
        'serving_grams': 90,
    }},
    'corpus-titled-apple-cobbler': {'action': 'edit', 'patch': {
        'name': 'Apple cobbler',
        'notes': 'Spiced sliced apples baked under a tender biscuit or batter topping — a homier cousin of apple pie.',
        'cuisine': 'American',
    }},
    'corpus-titled-texas-caviar': {'action': 'edit', 'patch': {
        'name': 'Texas caviar',
        'tags': ['snack'],
        'notes': 'Black-eyed peas marinated with diced peppers, onions, and tomatoes in Italian dressing — served cold with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 80,
    }},
    'corpus-titled-coca-cola-cake': {'action': 'edit', 'patch': {
        'name': 'Coca-Cola cake',
        'notes': 'A buttermilk-and-cocoa sheet cake with a bottle of Coca-Cola stirred into the batter, finished with a warm cola-pecan icing.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-cherry-crunch': {'action': 'edit', 'patch': {
        'name': 'Cherry crunch',
        'tags': ['dessert'],
        'notes': 'Cherry pie filling baked under a yellow-cake-mix-and-butter streusel with chopped pecans — sometimes called cherry dump cake.',
        'cuisine': 'American',
    }},
    'corpus-titled-date-nut-bread': {'action': 'edit', 'patch': {
        'name': 'Date nut bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A spiced quick bread folded with chopped dates and walnuts — moist, lightly sweet, often served with cream cheese.',
        'cuisine': 'American',
    }},
    'corpus-titled-hot-german-potato-salad': {'action': 'edit', 'patch': {
        'name': 'Hot German potato salad',
        'notes': 'Sliced warm potatoes dressed with a tangy bacon-fat-and-vinegar dressing, served hot — the classic German preparation.',
        'cuisine': 'German',
        'contains_add': ['pork'],
    }},
    'corpus-titled-spiced-pecans': {'action': 'edit', 'patch': {
        'name': 'Spiced pecans',
        'tags': ['snack'],
        'notes': 'Pecan halves coated in an egg-white-and-sugar slurry with cinnamon and cayenne, baked slowly until crisp.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-orange-cake': {'action': 'edit', 'patch': {
        'name': 'Orange cake',
        'notes': 'A bright butter or oil cake scented with orange zest and juice, often soaked or glazed with an orange-sugar syrup.',
    }},
    'corpus-titled-sand-tarts': {'action': 'edit', 'patch': {
        'name': 'Sand tarts (pecan snowballs)',
        'notes': 'A butter-and-powdered-sugar shortbread cookie folded with finely chopped pecans, baked, and rolled in more powdered sugar.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-shrimp-mold': {'action': 'edit', 'patch': {
        'name': 'Shrimp mold',
        'tags': ['snack'],
        'notes': 'A chilled appetizer mold of cream cheese, mayonnaise, gelatin, and chopped shrimp — turned out and served with crackers.',
        'cuisine': 'Southern',
        'serving_grams': 60,
    }},
    'corpus-titled-shrimp-casserole': {'action': 'edit', 'patch': {
        'name': 'Shrimp casserole',
        'notes': 'Shrimp baked with rice or noodles, peppers and onions, and a creamy mushroom-soup sauce — topped with cheese and crumbs.',
        'cuisine': 'American',
    }},
    'corpus-titled-dip': {'action': 'drop', 'reason': 'generic placeholder, not a named meal'},
    'corpus-titled-date-balls': {'action': 'edit', 'patch': {
        'name': 'Date balls',
        'tags': ['dessert', 'snack'],
        'notes': 'Chopped dates cooked with butter, sugar, and egg, then stirred with Rice Krispies and pecans, rolled into balls and dusted in powdered sugar or coconut.',
        'cuisine': 'Southern',
        'serving_grams': 30,
    }},
    'corpus-titled-chicken-a-la-king': {'action': 'edit', 'patch': {
        'name': 'Chicken à la king',
        'notes': 'Diced cooked chicken in a cream sauce with mushrooms, pimientos, and sherry — served over toast points or rice.',
        'cuisine': 'American',
    }},
    'corpus-titled-cheese-puffs': {'action': 'edit', 'patch': {
        'name': 'Cheese puffs',
        'tags': ['snack'],
        'notes': 'A pâte à choux dough enriched with grated cheese, piped or dropped into mounds and baked into airy savory bites (gougères).',
        'cuisine': 'French',
        'serving_grams': 30,
    }},
    'corpus-titled-lemonade': {'action': 'edit', 'patch': {
        'name': 'Lemonade',
        'ingredient_categories': ['Juices', 'Citrus', 'Sugar & sweeteners'],
        'tags': ['snack'],
        'notes': 'Fresh-squeezed lemon juice with sugar and water — served cold over ice.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-scones': {'action': 'edit', 'patch': {
        'name': 'Scones',
        'tags': ['breakfast', 'snack'],
        'notes': 'A short, dense quick bread of flour, cold butter, sugar, and milk or cream — wedge-cut and baked, often with currants or berries.',
        'cuisine': 'British',
        'serving_grams': 60,
    }},
    'corpus-titled-fantasy-fudge': {'action': 'edit', 'patch': {
        'name': 'Fantasy fudge',
        'notes': 'A microwave or stovetop fudge of sugar, butter, evaporated milk, chocolate chips, marshmallow creme, and walnuts — Kraft\'s classic recipe.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-white-chicken-chili': {'action': 'edit', 'patch': {
        'name': 'White chicken chili (variant)',
        'notes': 'Shredded chicken simmered with white beans, green chiles, cumin, and broth, finished with sour cream or cream cheese.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-24-hour-salad': {'action': 'edit', 'patch': {
        'name': '24-hour salad',
        'notes': 'A layered icebox salad of lettuce, peas, eggs, bacon, cheese, and onion sealed under a mayo-and-sugar topping, chilled overnight (24 hours).',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-crepes': {'action': 'edit', 'patch': {
        'name': 'Crêpes',
        'tags': ['breakfast', 'dessert'],
        'notes': 'Thin pancakes of flour, eggs, and milk cooked in a buttered pan and filled or rolled with sweet or savory fillings.',
        'cuisine': 'French',
        'serving_grams': 120,
    }},
    'corpus-titled-eclair-cake': {'action': 'edit', 'patch': {
        'name': 'Eclair cake',
        'notes': 'A no-bake icebox cake of graham crackers layered with vanilla pudding, topped with chocolate frosting — softens to eclair-like texture overnight.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-stew': {'action': 'edit', 'patch': {
        'name': 'Chicken stew',
        'notes': 'Chicken pieces simmered with potatoes, carrots, onions, and herbs in seasoned broth until tender — homier than gumbo.',
    }},
    'corpus-titled-shrimp-spread': {'action': 'edit', 'patch': {
        'name': 'Shrimp spread',
        'tags': ['snack'],
        'notes': 'Cream cheese whipped with chopped shrimp, lemon, Worcestershire, and seasonings — served chilled with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-popcorn-cake': {'action': 'edit', 'patch': {
        'name': 'Popcorn cake',
        'tags': ['dessert', 'snack'],
        'notes': 'Popped corn, gumdrops, and peanuts pressed into a Bundt pan with a hot marshmallow-and-butter syrup, set, and inverted to slice.',
        'cuisine': 'American',
    }},
    'corpus-titled-oatmeal-muffins': {'action': 'edit', 'patch': {
        'name': 'Oatmeal muffins',
        'notes': 'Tender muffins of soaked oats, flour, brown sugar, eggs, and milk — sometimes with raisins or chopped nuts.',
        'serving_grams': 60,
    }},
    'corpus-titled-chinese-chicken-salad': {'action': 'edit', 'patch': {
        'name': 'Chinese chicken salad',
        'notes': 'Shredded cabbage and lettuce tossed with chicken, crushed ramen noodles or wonton strips, sesame seeds, almonds, and a soy-vinegar dressing.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-sourdough-bread': {'action': 'edit', 'patch': {
        'name': 'Sourdough bread',
        'notes': 'A bread leavened by a wild-yeast starter rather than commercial yeast — tangy, chewy, with a deeply browned crust.',
        'serving_grams': 55,
    }},
    'corpus-titled-seafood-gumbo': {'action': 'edit', 'patch': {
        'name': 'Seafood gumbo',
        'notes': 'A Louisiana stew of shrimp, crab, and sometimes oysters in a dark-roux broth with the trinity of vegetables, okra, and Creole spices — served over rice.',
        'cuisine': 'Creole',
    }},
    'corpus-titled-barbecued-chicken': {'action': 'edit', 'patch': {
        'name': 'Barbecued chicken',
        'notes': 'Bone-in chicken grilled or baked, basted repeatedly with barbecue sauce as it cooks until glazed and sticky.',
        'cuisine': 'American',
    }},
    'corpus-titled-hot-potato-salad': {'action': 'edit', 'patch': {
        'name': 'Hot potato salad',
        'notes': 'Boiled potatoes tossed warm with bacon, onion, sugar, and a vinegar dressing — the German-American hot variant.',
        'cuisine': 'German-American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-spinach-lasagna': {'action': 'edit', 'patch': {
        'name': 'Spinach lasagna',
        'notes': 'Layered pasta sheets with ricotta, chopped spinach, mozzarella, and marinara — the meatless version of lasagna.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-english-toffee': {'action': 'edit', 'patch': {
        'name': 'English toffee',
        'tags': ['dessert'],
        'notes': 'Butter and sugar cooked to hard-crack stage, poured onto a sheet, topped with melted chocolate and chopped almonds, then broken into shards.',
        'cuisine': 'British',
        'serving_grams': 30,
    }},
    'corpus-titled-caramels': {'action': 'edit', 'patch': {
        'name': 'Caramels',
        'tags': ['dessert'],
        'notes': 'Cream, butter, sugar, and corn syrup cooked slowly to firm-ball stage, poured to set, and cut into chewy squares.',
        'serving_grams': 30,
    }},
    'corpus-titled-bean-casserole': {'action': 'edit', 'patch': {
        'name': 'Bean casserole (calico)',
        'notes': 'A mix of canned baked, kidney, and butter beans baked with ground beef, bacon, brown sugar, and barbecue sauce — also called calico beans.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-cherry-pie': {'action': 'edit', 'patch': {
        'name': 'Cherry pie',
        'notes': 'A double-crust or lattice pie of pitted sweet or sour cherries tossed with sugar and a thickener.',
        'cuisine': 'American',
    }},
    'corpus-titled-onion-soup': {'action': 'edit', 'patch': {
        'name': 'Onion soup',
        'notes': 'Slowly caramelized onions simmered in beef broth with wine and herbs, ladled over toast and broiled under a cap of melted cheese.',
        'cuisine': 'French',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-honey-bun-cake': {'action': 'edit', 'patch': {
        'name': 'Honey bun cake',
        'notes': 'A yellow cake mix batter with sour cream baked with a swirl of cinnamon-brown-sugar, finished with a powdered-sugar-and-vanilla glaze — tastes like a honey bun.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-egg-casserole': {'action': 'edit', 'patch': {
        'name': 'Egg casserole',
        'tags': ['breakfast'],
        'notes': 'A breakfast bake of beaten eggs, milk, cheese, bread, and breakfast sausage or ham — assembled the night before and baked in the morning.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-spoon-rolls': {'action': 'edit', 'patch': {
        'name': 'Spoon rolls',
        'tags': ['dinner', 'lunch'],
        'notes': 'A yeasted batter dropped by the spoonful into muffin tins and baked — no kneading, no shaping, soft and roll-like.',
        'cuisine': 'Southern',
        'serving_grams': 55,
    }},
    'corpus-titled-slaw': {'action': 'edit', 'patch': {
        'name': 'Slaw',
        'notes': 'Shredded cabbage and carrot dressed with mayo or vinegar — the generic short-name for coleslaw.',
        'cuisine': 'American',
    }},
    'corpus-titled-au-gratin-potatoes': {'action': 'edit', 'patch': {
        'name': 'Au gratin potatoes',
        'notes': 'Sliced potatoes layered with onions and Gruyère or cheddar in a milk-and-cream sauce, baked until bubbling with a golden cheese crust.',
        'cuisine': 'French',
    }},
    'corpus-titled-fudge-brownies': {'action': 'edit', 'patch': {
        'name': 'Fudge brownies',
        'notes': 'Dense, rich brownies leaning fudgy rather than cakey — high butter and cocoa, low flour, baked just until the center sets.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-cream-cheese-cookies': {'action': 'edit', 'patch': {
        'name': 'Cream cheese cookies',
        'notes': 'A butter-and-cream-cheese shortbread piped or cut into delicate cookies — tender and slightly tangy.',
        'serving_grams': 30,
    }},
    'corpus-titled-butternut-squash-soup': {'action': 'edit', 'patch': {
        'name': 'Butternut squash soup',
        'notes': 'Roasted butternut squash simmered with onion, apple, and broth, blended smooth and finished with cream and warm spices.',
    }},
    'corpus-titled-swedish-meat-balls': {'action': 'edit', 'patch': {
        'name': 'Swedish meatballs',
        'notes': 'Small, allspice-and-nutmeg-spiced meatballs of beef and pork, pan-fried and finished in a creamy beef-stock gravy.',
        'cuisine': 'Swedish',
        'contains_add': ['pork'],
    }},
    'corpus-titled-elephant-stew': {'action': 'drop', 'reason': 'joke recipe (calls for one elephant), not a real meal'},
    'corpus-titled-strawberry-jello-salad': {'action': 'edit', 'patch': {
        'name': 'Strawberry Jello salad',
        'tags': ['dessert'],
        'notes': 'Strawberry gelatin set with frozen strawberries and crushed pineapple, layered with sour cream — a chilled Southern dessert salad.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-sausage-bread': {'action': 'edit', 'patch': {
        'name': 'Sausage bread',
        'notes': 'Frozen bread dough rolled around cooked Italian sausage, mozzarella, and peppers, then baked into a sliceable savory loaf.',
        'cuisine': 'Italian-American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-snowballs': {'action': 'edit', 'patch': {
        'name': 'Snowball cookies',
        'tags': ['dessert'],
        'notes': 'A butter-and-powdered-sugar shortbread folded with finely chopped pecans, baked into balls, and rolled in powdered sugar — also called Russian tea cakes.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-wild-rice-casserole': {'action': 'edit', 'patch': {
        'name': 'Wild rice casserole',
        'notes': 'Wild and long-grain rice baked with mushrooms, onions, and broth — often with chicken or sausage stirred in.',
        'cuisine': 'American',
    }},
    'corpus-titled-party-cheese-ball': {'action': 'edit', 'patch': {
        'name': 'Party cheese ball',
        'tags': ['snack'],
        'notes': 'Cream cheese mixed with shredded cheddar, Worcestershire, garlic, and seasonings, shaped into a ball and rolled in chopped pecans or parsley.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-taffy-apple-salad': {'action': 'edit', 'patch': {
        'name': 'Taffy apple salad',
        'tags': ['dessert'],
        'notes': 'Diced apples, crushed pineapple, and peanuts folded with a cooked egg-and-flour dressing (mimicking caramel apple coating) — chilled overnight.',
        'cuisine': 'American',
    }},
    'corpus-titled-boiled-cookies': {'action': 'edit', 'patch': {
        'name': 'Boiled cookies (no-bake)',
        'notes': 'Cocoa, butter, sugar, and milk boiled to a fudge, then stirred with oats and peanut butter and dropped to set — same family as no-bake cookies.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-summer-salad': {'action': 'edit', 'patch': {
        'name': 'Summer salad',
        'notes': 'A loose name for a mixed salad of fresh-from-the-garden tomatoes, cucumbers, peppers, onions, and herbs in an oil-and-vinegar dressing.',
    }},
    'corpus-titled-chocolate-cookies': {'action': 'edit', 'patch': {
        'name': 'Chocolate cookies',
        'notes': 'Drop cookies of cocoa or melted chocolate in a butter-sugar dough — sometimes with chips, sometimes plain.',
        'serving_grams': 30,
    }},
    'corpus-titled-soft-pretzels': {'action': 'edit', 'patch': {
        'name': 'Soft pretzels',
        'notes': 'A yeasted dough dipped briefly in a baking-soda water bath, shaped into pretzels, salted, and baked until deep brown — chewy and shiny.',
        'cuisine': 'German-American',
        'serving_grams': 100,
    }},
    'corpus-titled-crab-salad': {'action': 'edit', 'patch': {
        'name': 'Crab salad',
        'notes': 'Lump or imitation crab tossed with celery, onion, and a lemony mayo dressing — served chilled on greens or as a sandwich filling.',
        'cuisine': 'American',
    }},
    'corpus-titled-pizza-burgers': {'action': 'edit', 'patch': {
        'name': 'Pizza burgers',
        'notes': 'Ground beef simmered with pizza sauce and pepperoni, spooned on toasted English muffins or buns, and topped with mozzarella — broiled until bubbly.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-crazy-cake': {'action': 'edit', 'patch': {
        'name': 'Crazy cake (Wacky cake variant)',
        'notes': 'A one-bowl Depression-era chocolate cake with no eggs, butter, or milk — leavened by vinegar reacting with baking soda; mixed right in the pan.',
        'cuisine': 'American',
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

    print('corpus-titled batch-4 audit applied (entries 451-600 by frequency).')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
