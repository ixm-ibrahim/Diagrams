"""Corpus-titled meals audit — batch 7 (entries 901-1050 by frequency, 123 -> 107).

Same standard.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

DECISIONS: dict[str, dict] = {
    'corpus-titled-graham-cracker-cake': {'action': 'edit', 'patch': {
        'name': 'Graham cracker cake',
        'notes': 'A tender layer cake using crushed graham crackers in place of much of the flour, often filled with pineapple-and-coconut and whipped cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-7-up-pound-cake': {'action': 'edit', 'patch': {
        'name': '7-Up pound cake',
        'ingredient_categories': ['Eggs', 'Sugar & sweeteners', 'Flours', 'Citrus', 'Cream & butter', 'Margarine & shortening', 'Extracts & essences', 'Soft drinks'],
        'notes': 'A lemon-lime Bundt cake leavened in part by a bottle of 7-Up — soft crumb, citrus-bright.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-swedish-pancakes': {'action': 'edit', 'patch': {
        'name': 'Swedish pancakes',
        'notes': 'Thin crepe-like pancakes of flour, eggs, milk, and a touch of sugar — rolled with lingonberry jam and whipped cream.',
        'cuisine': 'Swedish',
        'serving_grams': 120,
    }},
    'corpus-titled-rhubarb-crisp': {'action': 'edit', 'patch': {
        'name': 'Rhubarb crisp',
        'tags': ['dessert'],
        'notes': 'Sweetened chopped rhubarb baked under a crunchy oat-and-butter streusel — tart, juicy, and served warm with ice cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-twinkie-cake': {'action': 'edit', 'patch': {
        'name': 'Twinkie cake',
        'notes': 'Split Twinkies arranged in a pan with sliced bananas and topped with vanilla pudding and whipped topping — an icebox dessert.',
        'cuisine': 'American',
    }},
    'corpus-titled-apple-nut-cake': {'action': 'edit', 'patch': {
        'name': 'Apple nut cake',
        'notes': 'A spiced oil-based cake folded with chopped apples and walnuts or pecans — moist with a tender crumb.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-and-broccoli': {'action': 'edit', 'patch': {
        'name': 'Chicken and broccoli',
        'notes': 'Cooked chicken and broccoli baked in a mayo-and-cream-of-chicken-soup sauce under cheese and breadcrumbs.',
        'cuisine': 'American',
    }},
    'corpus-titled-skillet-cookies': {'action': 'edit', 'patch': {
        'name': 'Skillet cookies (date balls)',
        'notes': 'Chopped dates cooked with butter, sugar, and egg in a skillet, then stirred with Rice Krispies, coconut, and pecans — rolled into balls or pressed into bars.',
        'cuisine': 'Southern',
        'serving_grams': 30,
    }},
    'corpus-titled-creme-brulee': {'action': 'edit', 'patch': {
        'name': 'Crème brûlée',
        'notes': 'A baked vanilla-cream custard chilled, then topped with a thin layer of sugar that is torched into a glassy caramel crust.',
        'cuisine': 'French',
        'serving_grams': 120,
    }},
    'corpus-titled-pinto-bean-pie': {'action': 'edit', 'patch': {
        'name': 'Pinto bean pie',
        'notes': 'A Southern pie of mashed pinto beans, sugar, eggs, butter, and vanilla baked into a single crust — tastes pecan-pie-like, not bean-like.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-pumpkin-squares': {'action': 'edit', 'patch': {
        'name': 'Pumpkin squares',
        'tags': ['dessert'],
        'notes': 'A pumpkin-pie filling poured over a yellow-cake-mix base, topped with cinnamon-streusel and chopped pecans, baked into bars.',
        'cuisine': 'American',
        'serving_grams': 100,
    }},
    'corpus-titled-chess-squares': {'action': 'edit', 'patch': {
        'name': 'Chess squares (ooey-gooey bars)',
        'tags': ['dessert'],
        'notes': 'A yellow-cake-mix base topped with a cream-cheese-egg-and-powdered-sugar layer that bakes into a gooey filling — chess pie in bar form.',
        'cuisine': 'Southern',
        'serving_grams': 80,
    }},
    'corpus-titled-oreo-cookie-dessert': {'action': 'edit', 'patch': {
        'name': 'Oreo cookie dessert',
        'notes': 'A crushed-Oreo crust topped with sweetened whipped cream cheese, chocolate pudding, and whipped topping — same family as dirt pudding.',
        'cuisine': 'American',
    }},
    'corpus-titled-taco-bake': {'action': 'edit', 'patch': {
        'name': 'Taco bake',
        'notes': 'Layered ground beef, salsa, beans, and cheese baked over tortilla chips or a crescent-dough crust — a Tex-Mex one-pan casserole.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 320,
    }},
    'corpus-titled-heath-bar-cake': {'action': 'edit', 'patch': {
        'name': 'Heath bar cake',
        'notes': 'A chocolate cake poked and saturated with sweetened condensed milk and caramel, topped with whipped topping and crushed Heath bars.',
        'cuisine': 'American',
    }},
    'corpus-titled-hawaiian-cake': {'action': 'edit', 'patch': {
        'name': 'Hawaiian cake',
        'notes': 'A yellow cake topped with crushed pineapple, vanilla pudding, whipped topping, and shredded coconut — chilled before slicing.',
        'cuisine': 'American',
    }},
    'corpus-titled-cream-cheese-brownies': {'action': 'edit', 'patch': {
        'name': 'Cream cheese brownies',
        'notes': 'Chocolate brownie batter swirled with a sweetened cream cheese layer for marbled, cheesecake-topped fudgy bars.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-hot-fudge-pudding-cake': {'action': 'edit', 'patch': {
        'name': 'Hot fudge pudding cake',
        'notes': 'A self-saucing cake — batter spread in a pan, topped with cocoa-sugar and boiling water, baked so the cake rises and a fudge sauce sinks beneath.',
        'cuisine': 'American',
    }},
    'corpus-titled-jalapeno-corn-bread': {'action': 'edit', 'patch': {
        'name': 'Jalapeño cornbread (variant)',
        'notes': 'A skillet cornbread enriched with cheddar, creamed corn, and chopped jalapeños — same as jalapeño cornbread.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-green-pea-salad': {'action': 'edit', 'patch': {
        'name': 'Green pea salad',
        'notes': 'Sweet green peas tossed with hard-boiled egg, cheddar, red onion, and bacon in a mayo dressing — a Southern picnic side.',
        'cuisine': 'Southern',
        'contains_add': ['pork'],
    }},
    'corpus-titled-lemon-sponge-pie': {'action': 'edit', 'patch': {
        'name': 'Lemon sponge pie',
        'notes': 'A lemon-custard filling lightened by beaten egg whites baked into a flaky shell — sets into a sponge-cake top over a tangy curd bottom.',
        'cuisine': 'American',
    }},
    'corpus-titled-million-dollar-fudge': {'action': 'edit', 'patch': {
        'name': 'Million dollar fudge',
        'notes': 'A long-cooked fudge of evaporated milk, sugar, butter, chocolate chips, and marshmallow creme, mixed with nuts — Mamie Eisenhower\'s recipe.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-pumpkin-dessert': {'action': 'edit', 'patch': {
        'name': 'Pumpkin dessert',
        'notes': 'A pumpkin-pie custard poured over a yellow-cake-mix base, topped with butter and pecans, baked — same as pumpkin pie cake.',
        'cuisine': 'American',
    }},
    'corpus-titled-apricot-bars': {'action': 'edit', 'patch': {
        'name': 'Apricot bars',
        'tags': ['dessert'],
        'notes': 'Cooked dried apricots layered between an oat-and-brown-sugar crumble, baked into bars — chewy, tart-sweet.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-spinach-souffle': {'action': 'edit', 'patch': {
        'name': 'Spinach soufflé',
        'notes': 'Chopped spinach folded into a cheese bechamel base, lightened with beaten egg whites, and baked until puffed.',
        'cuisine': 'French',
    }},
    'corpus-titled-icebox-rolls': {'action': 'edit', 'patch': {
        'name': 'Icebox rolls',
        'tags': ['dinner', 'lunch'],
        'notes': 'A sweet yeast dough mixed, refrigerated overnight, then shaped and baked into soft dinner rolls — proofed cold for convenience.',
        'cuisine': 'American',
        'serving_grams': 50,
    }},
    'corpus-titled-tacos': {'action': 'edit', 'patch': {
        'name': 'Tacos',
        'notes': 'Seasoned ground beef in crisp corn shells (or soft flour tortillas), topped with lettuce, tomato, cheese, and salsa.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-peanut-patties': {'action': 'edit', 'patch': {
        'name': 'Peanut patties',
        'tags': ['dessert'],
        'notes': 'A pink Texas candy of sugar, corn syrup, milk, and peanuts cooked to soft-ball and dropped onto wax paper into patties.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-fish-tacos': {'action': 'edit', 'patch': {
        'name': 'Fish tacos',
        'notes': 'Battered or seasoned white fish in soft tortillas with shredded cabbage, crema, and lime — Baja-style.',
        'cuisine': 'Mexican',
    }},
    'corpus-titled-hot-spiced-tea': {'action': 'edit', 'patch': {
        'name': 'Hot spiced tea',
        'ingredient_categories': ['Coffee & tea', 'Juices', 'Citrus', 'Sugar & sweeteners', 'Whole spices', 'Ground spices'],
        'tags': ['snack'],
        'notes': 'Black tea simmered with orange and lemon juices, cinnamon sticks, and cloves — sweetened and served hot.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-chicken-stroganoff': {'action': 'edit', 'patch': {
        'name': 'Chicken stroganoff',
        'notes': 'Sliced chicken sautéed with mushrooms and onion in a sour-cream-and-mustard sauce — served over noodles or rice.',
        'cuisine': 'American',
    }},
    'corpus-titled-dirt-dessert': {'action': 'edit', 'patch': {
        'name': 'Dirt dessert',
        'notes': 'Vanilla pudding folded with cream cheese, butter, and whipped topping, layered with crushed Oreos — same as dirt pudding/cake.',
        'cuisine': 'American',
    }},
    'corpus-titled-sour-cream-chicken-enchiladas': {'action': 'edit', 'patch': {
        'name': 'Sour cream chicken enchiladas',
        'notes': 'Tortillas rolled around shredded chicken and cheese, baked in a creamy sour-cream-and-green-chile sauce topped with more cheese.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-beans': {'action': 'edit', 'patch': {
        'name': 'Cowboy-style beans',
        'notes': 'Canned beans simmered with ground beef, bacon, brown sugar, and barbecue sauce — a thick sweet-savory bean side; the generic "Beans" recipe.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-3-bean-salad': {'action': 'edit', 'patch': {
        'name': 'Three bean salad (3-bean)',
        'notes': 'Green, kidney, and wax beans tossed with peppers, onion, and a sweet vinegar dressing — chilled overnight.',
        'cuisine': 'American',
    }},
    'corpus-titled-toffee': {'action': 'edit', 'patch': {
        'name': 'Toffee',
        'tags': ['dessert'],
        'notes': 'Butter and sugar cooked to hard-crack stage, poured into a sheet, topped with melted chocolate and chopped nuts, then broken into shards.',
        'cuisine': 'British',
        'serving_grams': 30,
    }},
    'corpus-titled-sausage-quiche': {'action': 'edit', 'patch': {
        'name': 'Sausage quiche',
        'notes': 'A pastry shell filled with cooked breakfast sausage, cheese, and an egg-and-cream custard, baked until set.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-zucchini-bake': {'action': 'edit', 'patch': {
        'name': 'Zucchini bake',
        'notes': 'Sliced zucchini baked with eggs, cheese, and herbs in a crustless quiche-like dish.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-baked-rice': {'action': 'edit', 'patch': {
        'name': 'Baked rice',
        'notes': 'Long-grain rice baked in beef or chicken broth with mushrooms, onions, and butter — Texas hands-off rice pilaf.',
        'cuisine': 'American',
    }},
    'corpus-titled-cream-cheese-ball': {'action': 'edit', 'patch': {
        'name': 'Cream cheese ball',
        'tags': ['snack'],
        'notes': 'Cream cheese mixed with cheddar, dried beef or ham, peppers, and pineapple, shaped into a ball and rolled in chopped pecans — served with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-fried-okra': {'action': 'edit', 'patch': {
        'name': 'Fried okra',
        'notes': 'Sliced okra dredged in seasoned cornmeal and pan- or deep-fried until crisp — a Southern summer side.',
        'cuisine': 'Southern',
        'serving_grams': 100,
    }},
    'corpus-titled-chocolate-crinkles': {'action': 'edit', 'patch': {
        'name': 'Chocolate crinkles',
        'tags': ['dessert'],
        'notes': 'Fudgy chocolate cookies rolled twice (granulated then powdered sugar) before baking — the powdered sugar cracks into a "crinkle" pattern as they spread.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-lemon-delight': {'action': 'edit', 'patch': {
        'name': 'Lemon delight',
        'tags': ['dessert'],
        'notes': 'A no-bake layered dessert of pecan-shortbread crust, sweetened cream cheese, lemon pudding, and whipped topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-cincinnati-chili': {'action': 'edit', 'patch': {
        'name': 'Cincinnati chili',
        'notes': 'A finely ground beef chili scented with cinnamon, allspice, cocoa, and clove — served over spaghetti and topped with shredded cheese, onions, and beans (the "five-way").',
        'cuisine': 'American',
    }},
    'corpus-titled-moist-chocolate-cake': {'action': 'edit', 'patch': {
        'name': 'Moist chocolate cake',
        'notes': 'A buttermilk-and-oil cocoa cake brought to extra moistness with hot coffee or hot water in the batter — tall and tender.',
        'cuisine': 'American',
    }},
    'corpus-titled-mulled-cider': {'action': 'edit', 'patch': {
        'name': 'Mulled cider',
        'ingredient_categories': ['Juices', 'Citrus', 'Whole spices', 'Ground spices', 'Sugar & sweeteners'],
        'tags': ['snack'],
        'notes': 'Apple cider simmered with cinnamon sticks, cloves, orange, and lemon — a hot non-alcoholic holiday drink (alcoholic versions add rum or brandy).',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-martha-washington-candy': {'action': 'edit', 'patch': {
        'name': 'Martha Washington candy',
        'notes': 'A fondant-style candy of sweetened condensed milk, butter, powdered sugar, coconut, and pecans rolled into balls and dipped in chocolate.',
        'cuisine': 'Southern',
        'serving_grams': 30,
    }},
    'corpus-titled-instant-russian-tea': {'action': 'edit', 'patch': {
        'name': 'Instant Russian tea',
        'ingredient_categories': ['Coffee & tea', 'Juices', 'Sugar & sweeteners', 'Whole spices', 'Ground spices', 'Citrus'],
        'tags': ['snack'],
        'notes': 'A pantry mix of instant tea, powdered Tang, sugar, and warm spices — stirred into hot water; non-alcoholic.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-neiman-marcus-cake': {'action': 'edit', 'patch': {
        'name': 'Neiman Marcus cake',
        'notes': 'A yellow-cake-mix base topped with a cream-cheese-egg-and-powdered-sugar layer baked into a gooey "Neiman Marcus bar" — same family as gooey butter cake.',
        'cuisine': 'American',
    }},
    'corpus-titled-holiday-cheese-ball': {'action': 'edit', 'patch': {
        'name': 'Holiday cheese ball',
        'tags': ['snack'],
        'notes': 'Cream cheese mixed with sharp cheddar, pineapple, peppers, and seasonings, shaped into a ball and rolled in chopped pecans — Christmas-table appetizer.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-sausage-and-rice-casserole': {'action': 'edit', 'patch': {
        'name': 'Sausage and rice casserole',
        'notes': 'Browned sausage baked with rice, chicken broth, mushrooms, peppers, and onions until rice absorbs the liquid.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-chipped-beef-dip': {'action': 'edit', 'patch': {
        'name': 'Chipped beef dip',
        'tags': ['snack'],
        'notes': 'Cream cheese mixed with sour cream and torn chipped (dried) beef, peppers, and onions — baked or served chilled with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-enchilada-pie': {'action': 'edit', 'patch': {
        'name': 'Enchilada pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'A layered "stacked" enchilada casserole of tortillas, seasoned meat, enchilada sauce, and cheese, baked lasagna-style.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 320,
    }},
    'corpus-titled-garlic-mashed-potatoes': {'action': 'edit', 'patch': {
        'name': 'Garlic mashed potatoes',
        'notes': 'Boiled potatoes mashed with butter, milk or cream, and roasted or simmered garlic — a side dish with subtle garlic warmth.',
    }},
    'corpus-titled-tzatziki': {'action': 'edit', 'patch': {
        'name': 'Tzatziki',
        'tags': ['snack', 'condiment'],
        'notes': 'Strained Greek yogurt mixed with grated cucumber, garlic, dill, lemon, and olive oil — served chilled with pita.',
        'cuisine': 'Greek',
        'serving_grams': 60,
    }},
    'corpus-titled-chicken-roll-ups': {'action': 'edit', 'patch': {
        'name': 'Chicken roll-ups',
        'notes': 'Crescent-roll dough wrapped around a chicken-and-cream-cheese filling, baked, and served with a cream-soup gravy.',
        'cuisine': 'American',
    }},
    'corpus-titled-persimmon-cookies': {'action': 'edit', 'patch': {
        'name': 'Persimmon cookies',
        'notes': 'A soft spice drop cookie made with persimmon pulp folded into a butter batter with raisins or nuts.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-pineapple-delight': {'action': 'edit', 'patch': {
        'name': 'Pineapple delight',
        'tags': ['dessert'],
        'notes': 'A no-bake layered dessert of graham crust, sweetened cream cheese, pineapple-pudding filling, and whipped topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-hamburger-stew': {'action': 'edit', 'patch': {
        'name': 'Hamburger stew',
        'notes': 'Browned ground beef simmered with potatoes, carrots, onions, and tomatoes — a stockpot weeknight stew.',
        'cuisine': 'American',
    }},
    'corpus-titled-barbecue-meatballs': {'action': 'edit', 'patch': {
        'name': 'Barbecue meatballs',
        'tags': ['snack', 'dinner'],
        'notes': 'Oven-baked meatballs simmered in barbecue sauce or grape-jelly-and-chili-sauce — held warm in a slow cooker for parties.',
        'cuisine': 'American',
        'serving_grams': 100,
    }},
    'corpus-titled-turkey-burgers': {'action': 'edit', 'patch': {
        'name': 'Turkey burgers',
        'notes': 'Ground turkey patties seasoned and grilled or pan-cooked, served on buns with the usual burger toppings — a leaner burger alternative.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-sour-cream-cornbread': {'action': 'edit', 'patch': {
        'name': 'Sour cream cornbread',
        'notes': 'A skillet cornbread enriched with sour cream and creamed corn — moist, slightly sweet, with a tender crumb.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-orange-sherbet': {'action': 'edit', 'patch': {
        'name': 'Orange sherbet',
        'tags': ['dessert'],
        'notes': 'A frozen dessert of orange juice or concentrate blended with sugar, a small amount of milk or cream, and sometimes egg whites — lighter than ice cream.',
        'cuisine': 'American',
        'serving_grams': 85,
    }},
    'corpus-titled-oven-beef-stew': {'action': 'edit', 'patch': {
        'name': 'Oven beef stew (variant)',
        'notes': 'Cubed beef and root vegetables tossed with tomato juice, tapioca, and seasonings, sealed and oven-braised low for hours.',
        'cuisine': 'American',
    }},
    'corpus-titled-applesauce-muffins': {'action': 'edit', 'patch': {
        'name': 'Applesauce muffins',
        'tags': ['breakfast', 'snack'],
        'notes': 'Spiced muffins made tender by applesauce in place of much of the fat — often with raisins or chopped nuts.',
        'serving_grams': 60,
    }},
    'corpus-titled-yeast-biscuits': {'action': 'edit', 'patch': {
        'name': 'Yeast biscuits (angel biscuits)',
        'tags': ['breakfast', 'dinner'],
        'notes': 'A Southern biscuit leavened with both yeast and baking powder — exceptionally tall and light, also called angel biscuits.',
        'cuisine': 'Southern',
        'serving_grams': 55,
    }},
    'corpus-titled-sponge-cake': {'action': 'edit', 'patch': {
        'name': 'Sponge cake',
        'notes': 'A foam-leavened cake of beaten whole eggs (or separated yolks and whites) folded with sugar and flour — fat-free or lightly enriched.',
    }},
    'corpus-titled-chocolate-covered-cherries': {'action': 'edit', 'patch': {
        'name': 'Chocolate covered cherries',
        'tags': ['dessert'],
        'notes': 'Maraschino cherries wrapped in a fondant of butter, powdered sugar, and corn syrup, dipped in chocolate, and aged so the fondant liquefies inside.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-no-peek-chicken': {'action': 'edit', 'patch': {
        'name': 'No peek chicken',
        'notes': 'Raw rice and chicken pieces sealed in a covered dish with mushroom soup and onion soup mix — baked an hour without lifting the lid.',
        'cuisine': 'American',
    }},
    'corpus-titled-slush': {'action': 'edit', 'patch': {
        'name': 'Slush cocktail',
        'ingredient_categories': ['Juices', 'Citrus', 'Sugar & sweeteners', 'Tropical fruits', 'Alcoholic beverages'],
        'tags': ['snack'],
        'notes': 'Sweetened fruit juices and vodka or brandy frozen in a container, then scooped slushy and topped with lemon-lime soda — a party drink.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
        'serving_grams': 240,
    }},
    'corpus-titled-cucumber-sandwiches': {'action': 'edit', 'patch': {
        'name': 'Cucumber tea sandwiches',
        'tags': ['snack'],
        'notes': 'Thin-sliced bread spread with seasoned cream cheese or herb butter and topped with cucumber slices — finger sandwiches for tea or bridal showers.',
        'cuisine': 'British',
        'serving_grams': 60,
    }},
    'corpus-titled-strawberry-trifle': {'action': 'edit', 'patch': {
        'name': 'Strawberry trifle',
        'tags': ['dessert'],
        'notes': 'Cubes of angel food or pound cake layered with vanilla pudding, sliced strawberries, and whipped topping — assembled in a glass bowl.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-1-2-3-4-cake': {'action': 'edit', 'patch': {
        'name': '1-2-3-4 cake',
        'notes': 'A classic American butter cake with 1 cup butter, 2 cups sugar, 3 cups flour, and 4 eggs — the easy-to-remember ratio cake.',
        'cuisine': 'American',
    }},
    'corpus-titled-salsa-chicken': {'action': 'edit', 'patch': {
        'name': 'Salsa chicken',
        'notes': 'Chicken breasts baked in a jar of salsa and topped with shredded cheese — a three-ingredient Tex-Mex weeknight bake.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-cherry-cheese-cake': {'action': 'edit', 'patch': {
        'name': 'Cherry cheesecake (no-bake)',
        'notes': 'A no-bake or baked cream-cheese cheesecake topped with canned cherry pie filling — same family as cherry cheesecake.',
        'cuisine': 'American',
    }},
    'corpus-titled-company-casserole': {'action': 'edit', 'patch': {
        'name': 'Company casserole',
        'notes': 'A retro entertaining bake of ground beef, sour cream, cream cheese, tomato sauce, and noodles topped with cheddar — assembled the night before.',
        'cuisine': 'American',
    }},
    'corpus-titled-mini-cheesecakes': {'action': 'edit', 'patch': {
        'name': 'Mini cheesecakes',
        'notes': 'Individual cheesecakes baked in muffin tins over a vanilla wafer or graham crust, then topped with fruit pie filling.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-jelly-roll': {'action': 'edit', 'patch': {
        'name': 'Jelly roll',
        'tags': ['dessert'],
        'notes': 'A thin sponge cake baked on a sheet pan, rolled while warm with a tea-towel, then unrolled, spread with jam, and re-rolled into a spiral.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-apple-brownies': {'action': 'edit', 'patch': {
        'name': 'Apple brownies',
        'notes': 'A spiced butter-and-brown-sugar bar folded with chopped apples and walnuts — chewy and apple-fragrant, not chocolaty.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-blackberry-cake': {'action': 'edit', 'patch': {
        'name': 'Blackberry jam cake',
        'notes': 'A spiced buttermilk layer cake with blackberry jam folded into the batter, often frosted with caramel icing — Appalachian classic.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-apple-squares': {'action': 'edit', 'patch': {
        'name': 'Apple squares',
        'tags': ['dessert'],
        'notes': 'A spiced sheet-pan version of apple cake — moist butter or oil batter folded with chopped apples, cut into squares.',
        'cuisine': 'American',
        'serving_grams': 100,
    }},
    'corpus-titled-baked-potato-salad': {'action': 'edit', 'patch': {
        'name': 'Baked potato salad',
        'notes': 'A hot potato salad of cubed potatoes baked with sour cream or mayo, bacon, scallions, and cheese — loaded-baked-potato flavors in a casserole.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-bubble-bread': {'action': 'edit', 'patch': {
        'name': 'Bubble bread (monkey bread)',
        'tags': ['breakfast', 'dessert'],
        'notes': 'Pieces of biscuit dough rolled in cinnamon-sugar, layered in a Bundt pan, and baked with brown-sugar-butter syrup — pulled apart to serve.',
        'cuisine': 'American',
    }},
    'corpus-titled-marinated-flank-steak': {'action': 'edit', 'patch': {
        'name': 'Marinated flank steak',
        'notes': 'Flank steak marinated in soy sauce, oil, garlic, and a sweetener, then grilled hot and sliced thin across the grain.',
        'cuisine': 'American',
    }},
    'corpus-titled-pistachio-dessert': {'action': 'edit', 'patch': {
        'name': 'Pistachio dessert',
        'notes': 'A no-bake layered dessert of pecan-shortbread crust, sweetened cream cheese, pistachio pudding, and whipped topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-caesar-salad-dressing': {'action': 'edit', 'patch': {
        'name': 'Caesar salad dressing',
        'tags': ['condiment'],
        'notes': 'An emulsion of olive oil, lemon, egg yolk, anchovy, garlic, Parmesan, and Worcestershire — tossed with romaine for Caesar salad.',
        'cuisine': 'Italian-American',
        'serving_grams': 30,
    }},
    'corpus-titled-hawaiian-wedding-cake': {'action': 'edit', 'patch': {
        'name': 'Hawaiian wedding cake',
        'notes': 'A yellow pineapple cake topped with sweetened cream cheese and whipped topping, finished with coconut and pineapple — similar to pig pickin\' cake.',
        'cuisine': 'American',
    }},
    'corpus-titled-crab-imperial': {'action': 'edit', 'patch': {
        'name': 'Crab imperial',
        'notes': 'Lump crab folded with a mayo-and-mustard bechamel, mounded in shells or a casserole, topped with buttered breadcrumbs, and baked — a Chesapeake classic.',
        'cuisine': 'American',
    }},
    'corpus-titled-sauerkraut': {'action': 'drop', 'reason': 'fermented condiment/side, not a coherent meal'},
    'corpus-titled-rocky-road-candy': {'action': 'edit', 'patch': {
        'name': 'Rocky road candy',
        'notes': 'Melted chocolate stirred with mini marshmallows and chopped peanuts or almonds, poured to set and cut into squares.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-baked-chicken-salad': {'action': 'edit', 'patch': {
        'name': 'Baked chicken salad',
        'notes': 'Diced chicken bound with mayo, celery, water chestnuts, and almonds, topped with crushed potato chips or cornflakes and cheese, baked until bubbling.',
        'cuisine': 'American',
    }},
    'corpus-titled-grits-casserole': {'action': 'edit', 'patch': {
        'name': 'Grits casserole',
        'notes': 'Cooked grits folded with eggs, milk, sharp cheddar, and butter, baked into a fluffy casserole — sometimes with sausage stirred in.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-rice': {'action': 'edit', 'patch': {
        'name': 'Seasoned rice',
        'notes': 'White rice cooked in broth with butter and seasonings — a base side dish for chicken, beef, or vegetable mains.',
    }},
    'corpus-titled-yum-yum-cake': {'action': 'edit', 'patch': {
        'name': 'Yum yum cake',
        'notes': 'A yellow cake topped with crushed pineapple, vanilla pudding, sweetened cream cheese, and whipped topping — chilled before serving.',
        'cuisine': 'American',
    }},
    'corpus-titled-hot-broccoli-dip': {'action': 'edit', 'patch': {
        'name': 'Hot broccoli dip',
        'tags': ['snack'],
        'notes': 'Chopped broccoli baked with cream of mushroom soup, butter, and processed cheese until bubbly — served warm with crackers or bread.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-steak-marinade': {'action': 'drop', 'reason': 'marinade component, not a coherent meal'},
    'corpus-titled-brown-bread': {'action': 'edit', 'patch': {
        'name': 'Brown bread',
        'notes': 'A steamed or baked molasses-sweetened bread of whole wheat, rye, and cornmeal flours, often with raisins — a Boston/New England tradition.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-triple-chocolate-cake': {'action': 'edit', 'patch': {
        'name': 'Triple chocolate cake',
        'notes': 'A chocolate cake mix combined with chocolate pudding and chocolate chips — three forms of chocolate in one Bundt.',
        'cuisine': 'American',
    }},
    'corpus-titled-shrimp-fried-rice': {'action': 'edit', 'patch': {
        'name': 'Shrimp fried rice',
        'notes': 'Day-old cold rice stir-fried with shrimp, scrambled egg, peas, scallions, and soy sauce — Chinese-American takeout style.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-butterscotch-cookies': {'action': 'edit', 'patch': {
        'name': 'Butterscotch cookies',
        'notes': 'Drop cookies sweetened with brown sugar and butterscotch chips — chewy and caramel-toned.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-chocolate-zucchini-bread': {'action': 'edit', 'patch': {
        'name': 'Chocolate zucchini bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A spiced cocoa quick bread made moist by grated zucchini — folded with chocolate chips for double chocolate.',
        'cuisine': 'American',
    }},
    'corpus-titled-boston-brown-bread': {'action': 'edit', 'patch': {
        'name': 'Boston brown bread',
        'tags': ['breakfast', 'dinner'],
        'notes': 'A steamed New England bread of whole wheat, rye, and cornmeal with molasses and raisins — cooked in a covered can in a water bath.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-chicken-spectacular': {'action': 'edit', 'patch': {
        'name': 'Chicken spectacular',
        'notes': 'Cooked chicken baked with wild and white rice, water chestnuts, French-cut green beans, mushrooms, and mayo — a 1970s entertaining casserole.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-bread-pudding': {'action': 'edit', 'patch': {
        'name': 'Chocolate bread pudding',
        'notes': 'Cubed bread soaked in a chocolate-and-cream custard with melted chocolate chips, baked until set — rich and pudding-like.',
        'cuisine': 'American',
    }},
    'corpus-titled-mexican-pizza': {'action': 'edit', 'patch': {
        'name': 'Mexican pizza',
        'notes': 'Crispy fried or baked tortillas layered with refried beans, seasoned beef, salsa, and shredded cheese — the Taco Bell classic, homemade.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 200,
    }},
    'corpus-titled-oyster-crackers': {'action': 'edit', 'patch': {
        'name': 'Seasoned oyster crackers',
        'ingredient_categories': ['Baked snacks & pastries', 'Oils', 'Fresh herbs', 'Ground spices', 'Salt & seasonings'],
        'tags': ['snack'],
        'notes': 'Oyster crackers tossed with oil, dill, dry ranch mix, and garlic powder, baked until aromatic — a seasoned party snack.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-molasses-sugar-cookies': {'action': 'edit', 'patch': {
        'name': 'Molasses sugar cookies',
        'notes': 'Chewy spiced cookies of butter, molasses, brown sugar, and warm spices — rolled in sugar before baking.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-coca-cola-salad': {'action': 'edit', 'patch': {
        'name': 'Coca-Cola salad',
        'tags': ['dessert'],
        'notes': 'A molded gelatin salad of cherry Jello dissolved in hot Coca-Cola, set with crushed pineapple, cherries, and chopped pecans.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-dump-salad': {'action': 'edit', 'patch': {
        'name': 'Dump salad',
        'tags': ['dessert'],
        'notes': 'Cans of fruit (pineapple, mandarin oranges, cherries) dumped together with vanilla pudding and whipped topping — Southern dessert salad.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-sour-cream-raisin-pie': {'action': 'edit', 'patch': {
        'name': 'Sour cream raisin pie',
        'notes': 'A spiced custard pie of sour cream, eggs, sugar, and plumped raisins — sometimes topped with meringue.',
        'cuisine': 'American',
    }},
    'corpus-titled-sopaipillas': {'action': 'edit', 'patch': {
        'name': 'Sopaipillas',
        'tags': ['dessert'],
        'notes': 'Squares of leavened wheat dough deep-fried until puffy and hollow — served warm with honey, cinnamon-sugar, or savory fillings.',
        'cuisine': 'Mexican',
        'serving_grams': 60,
    }},
    'corpus-titled-company-chicken': {'action': 'edit', 'patch': {
        'name': 'Company chicken',
        'notes': 'Chicken breasts wrapped in bacon, topped with dried beef, and baked in sour cream and cream of mushroom soup — same as party chicken.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-spinach-squares': {'action': 'edit', 'patch': {
        'name': 'Spinach squares',
        'tags': ['snack'],
        'notes': 'Chopped spinach baked with eggs, flour, milk, and cheese in a sheet pan, then cut into bite-size squares as an appetizer.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-apple-kuchen': {'action': 'edit', 'patch': {
        'name': 'Apple kuchen',
        'tags': ['breakfast', 'dessert'],
        'notes': 'A cake-mix-and-butter base topped with sliced apples, cinnamon-sugar, and a sour cream layer — a Pennsylvania Dutch coffee cake.',
        'cuisine': 'German',
    }},
    'corpus-titled-swiss-chicken': {'action': 'edit', 'patch': {
        'name': 'Swiss chicken',
        'notes': 'Chicken breasts topped with Swiss cheese and cream of chicken soup, blanketed in herbed stuffing mix and butter, and baked.',
        'cuisine': 'American',
    }},
    'corpus-titled-broccoli-supreme': {'action': 'edit', 'patch': {
        'name': 'Broccoli supreme',
        'notes': 'Broccoli baked with eggs, mushrooms, and onion in a cream-of-mushroom sauce under buttered stuffing crumbs and cheese.',
        'cuisine': 'American',
    }},
    'corpus-titled-chinese-pepper-steak': {'action': 'edit', 'patch': {
        'name': 'Chinese pepper steak',
        'notes': 'Strips of beef stir-fried with sliced bell peppers and onions in a soy-and-ginger sauce — served over rice.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-bananas-foster': {'action': 'edit', 'patch': {
        'name': 'Bananas Foster',
        'tags': ['dessert'],
        'notes': 'Sliced bananas sautéed in butter, brown sugar, and cinnamon, flambéed with rum, and served over vanilla ice cream — Brennan\'s of New Orleans original.',
        'cuisine': 'Creole',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-pecan-tassies': {'action': 'edit', 'patch': {
        'name': 'Pecan tassies',
        'tags': ['dessert'],
        'notes': 'Mini cream-cheese pastry shells pressed into muffin tins, filled with a brown-sugar-egg-butter custard and chopped pecans — pecan pie in bite-size form.',
        'cuisine': 'Southern',
        'serving_grams': 30,
    }},
    'corpus-titled-mock-apple-pie': {'action': 'edit', 'patch': {
        'name': 'Mock apple pie',
        'notes': 'A double-crust "apple" pie made entirely from Ritz crackers simmered in lemon-and-cinnamon syrup — a Depression-era pantry deception.',
        'cuisine': 'American',
    }},
    'corpus-titled-curried-chicken-salad': {'action': 'edit', 'patch': {
        'name': 'Curried chicken salad',
        'notes': 'Diced cooked chicken bound with mayo and curry powder, mixed with grapes, apples, almonds, and celery — served chilled.',
        'cuisine': 'American',
    }},
    'corpus-titled-trifle': {'action': 'edit', 'patch': {
        'name': 'Trifle',
        'tags': ['dessert'],
        'notes': 'Cubed cake or ladyfingers layered with pudding or custard, fruit, jam, and whipped cream — assembled in a glass bowl.',
        'cuisine': 'British',
        'serving_grams': 200,
    }},
    'corpus-titled-burritos': {'action': 'edit', 'patch': {
        'name': 'Burritos',
        'notes': 'Large flour tortillas wrapped around seasoned meat, beans, rice, cheese, and salsa — Tex-Mex / Mission-style.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-manhattan-clam-chowder': {'action': 'edit', 'patch': {
        'name': 'Manhattan clam chowder',
        'notes': 'A tomato-and-broth-based clam chowder with diced potatoes, peppers, onions, and bacon — the red, broth-style cousin of New England chowder.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-hot-milk-cake': {'action': 'edit', 'patch': {
        'name': 'Hot milk cake',
        'notes': 'A foam-leavened cake of beaten eggs and sugar whisked with hot scalded milk and melted butter — moist, fine-crumbed, served plain or with fruit.',
        'cuisine': 'American',
    }},
    'corpus-titled-tuna-burgers': {'action': 'edit', 'patch': {
        'name': 'Tuna burgers',
        'notes': 'Canned tuna bound with egg, breadcrumbs, lemon, and onion, formed into patties and pan-fried — served on buns with the usual burger toppings.',
        'cuisine': 'American',
    }},
    'corpus-titled-double-layer-pumpkin-pie': {'action': 'edit', 'patch': {
        'name': 'Double layer pumpkin pie',
        'notes': 'A graham crust topped with a sweetened cream-cheese layer, then a layer of spiced pumpkin pudding — chilled until set.',
        'cuisine': 'American',
    }},
    'corpus-titled-rhubarb-dessert': {'action': 'edit', 'patch': {
        'name': 'Rhubarb dessert',
        'notes': 'A rhubarb-and-strawberry filling baked under a yellow-cake-mix-and-butter streusel — a rhubarb dump cake.',
        'cuisine': 'American',
    }},
    'corpus-titled-peach-cake': {'action': 'edit', 'patch': {
        'name': 'Peach cake',
        'notes': 'A spiced butter cake topped with sliced fresh peaches, sometimes finished with a brown-sugar streusel — a German Pfirsichkuchen-style dessert.',
        'cuisine': 'American',
    }},
    'corpus-titled-black-eyed-pea-salad': {'action': 'edit', 'patch': {
        'name': 'Black-eyed pea salad',
        'notes': 'Black-eyed peas marinated with diced peppers, onions, and herbs in Italian dressing — a Tex-Mex twist on three-bean salad.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-potato-cheese-soup': {'action': 'edit', 'patch': {
        'name': 'Potato cheese soup',
        'notes': 'Diced potatoes simmered in chicken broth with onion, then thickened with milk, butter, and shredded cheddar.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-tortilla-casserole': {'action': 'edit', 'patch': {
        'name': 'Chicken tortilla casserole',
        'notes': 'Layered tortillas, shredded chicken, mushroom soup, salsa or enchilada sauce, and cheese, baked until bubbly — a King-Ranch-style bake.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-overnight-salad': {'action': 'edit', 'patch': {
        'name': 'Overnight salad',
        'notes': 'Lettuce, peas, eggs, bacon, cheese, and red onion layered in a glass bowl, sealed under a mayo-and-sugar topping — chilled overnight before serving.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-peanut-butter-fingers': {'action': 'edit', 'patch': {
        'name': 'Peanut butter fingers',
        'tags': ['dessert'],
        'notes': 'A baked oat-and-peanut-butter cookie bar topped with melted chocolate and a peanut-butter-powdered-sugar drizzle, then cut into fingers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-baked-squash': {'action': 'edit', 'patch': {
        'name': 'Baked squash',
        'notes': 'Sliced yellow squash baked with eggs, butter, and shredded cheese, topped with buttered cracker crumbs or breadcrumbs.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-chinese-chicken-wings': {'action': 'edit', 'patch': {
        'name': 'Chinese chicken wings',
        'tags': ['snack', 'dinner'],
        'notes': 'Whole or split chicken wings marinated in soy sauce, ginger, garlic, and sugar, then baked until sticky and bronzed.',
        'cuisine': 'Chinese-American',
        'serving_grams': 170,
    }},
    'corpus-titled-honey-mustard-chicken': {'action': 'edit', 'patch': {
        'name': 'Honey mustard chicken',
        'notes': 'Chicken pieces glazed with a sauce of honey, Dijon mustard, butter, and curry powder, baked until caramelized.',
        'cuisine': 'American',
    }},
    'corpus-titled-hot-cross-buns': {'action': 'edit', 'patch': {
        'name': 'Hot cross buns',
        'tags': ['breakfast'],
        'notes': 'Sweet enriched yeast buns studded with currants or raisins and spices, marked with a flour-paste cross — an Easter / Good Friday tradition.',
        'cuisine': 'British',
        'serving_grams': 80,
    }},
    'corpus-titled-lima-bean-casserole': {'action': 'edit', 'patch': {
        'name': 'Lima bean casserole',
        'notes': 'Lima beans simmered tender, then baked with onions, peppers, and cream of mushroom soup under a cheese-and-cracker topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-pecan-sandies': {'action': 'edit', 'patch': {
        'name': 'Pecan sandies',
        'tags': ['dessert'],
        'notes': 'A butter-and-powdered-sugar shortbread cookie folded with finely chopped pecans — sandy, melt-in-the-mouth crumb.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-cauliflower-soup': {'action': 'edit', 'patch': {
        'name': 'Cauliflower soup',
        'notes': 'Cauliflower florets simmered in chicken broth with onion, blended smooth and finished with milk, cream, and cheese.',
    }},
    'corpus-titled-candy': {'action': 'drop', 'reason': 'generic placeholder ("Candy"), not a coherent meal'},
    'corpus-titled-cioppino': {'action': 'edit', 'patch': {
        'name': 'Cioppino',
        'notes': 'A San Francisco Italian-American seafood stew of shrimp, scallops, mussels, clams, and white fish simmered in a tomato-and-white-wine broth.',
        'cuisine': 'Italian-American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-glorified-rice': {'action': 'edit', 'patch': {
        'name': 'Glorified rice',
        'tags': ['dessert'],
        'notes': 'Cooked white rice folded with crushed pineapple, mini marshmallows, and sweetened whipped cream — a Midwestern dessert-salad.',
        'cuisine': 'American',
    }},
    'corpus-titled-pasta': {'action': 'edit', 'patch': {
        'name': 'Pasta with vegetables',
        'notes': 'A generic pasta dish — cooked pasta tossed with sautéed vegetables, herbs, and oil or a light sauce.',
        'cuisine': 'Italian',
    }},
    'corpus-titled-chocolate-drop-cookies': {'action': 'edit', 'patch': {
        'name': 'Chocolate drop cookies',
        'notes': 'Soft cake-like cocoa cookies of butter, sugar, eggs, and buttermilk, often glazed with a chocolate icing.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-chocolate-chip-pound-cake': {'action': 'edit', 'patch': {
        'name': 'Chocolate chip pound cake',
        'notes': 'A yellow or chocolate cake-mix-based Bundt with sour cream and chocolate pudding, folded with chocolate chips.',
        'cuisine': 'American',
    }},
    'corpus-titled-eggplant-parmigiana': {'action': 'edit', 'patch': {
        'name': 'Eggplant parmigiana (variant)',
        'notes': 'Breaded eggplant slices fried, then baked in tomato sauce under layers of mozzarella and Parmesan — same dish as eggplant parmesan.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-raisin-cake': {'action': 'edit', 'patch': {
        'name': 'Raisin cake',
        'notes': 'A spiced butter cake folded with plumped raisins, sometimes with walnuts — moist and warmly spiced.',
        'cuisine': 'American',
    }},
    'corpus-titled-finger-jello': {'action': 'edit', 'patch': {
        'name': 'Finger Jello',
        'tags': ['dessert', 'snack'],
        'notes': 'Concentrated Jello set with extra gelatin so it firms enough to cut into squares and eat by hand — a kids\' lunchbox treat.',
        'cuisine': 'American',
        'serving_grams': 60,
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

    print('corpus-titled batch-7 audit applied (entries 901-1050 by frequency).')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
