"""Corpus-titled meals audit — batch 1 (top 150 by frequency).

Standard per meal: idiomatic sentence-case name, 1-2 sentence factual notes,
clean ingredient_categories, real-world tags, cuisine where the name implies
one, contains:['pork'] / ['alcohol'] only when traditionally mandatory.
Drop entries that aren't coherent meals.

Re-run scripts/rederive_diet_compatibility.py after this script.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

DECISIONS: dict[str, dict] = {
    'corpus-titled-chicken-casserole': {'action': 'edit', 'patch': {
        'name': 'Chicken casserole',
        'notes': 'A baked casserole of cooked chicken, vegetables, and mushrooms bound in a creamy soup-based sauce and topped with bread or crackers.',
    }},
    'corpus-titled-broccoli-casserole': {'action': 'edit', 'patch': {
        'name': 'Broccoli casserole',
        'notes': 'Broccoli florets baked with eggs, cheese, and a buttery cracker topping — a Southern potluck staple.',
        'cuisine': 'American',
    }},
    'corpus-titled-banana-bread': {'action': 'edit', 'patch': {
        'name': 'Banana bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A moist quick bread sweetened by mashed ripe bananas, with butter, eggs, and flour — typically served sliced.',
        'cuisine': 'American',
    }},
    'corpus-titled-cheese-ball': {'action': 'edit', 'patch': {
        'name': 'Cheese ball',
        'tags': ['snack'],
        'notes': 'A blend of cream cheese, shredded cheese, and seasonings shaped into a ball and rolled in chopped nuts — served as an appetizer with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-squash-casserole': {'action': 'edit', 'patch': {
        'name': 'Squash casserole',
        'notes': 'Sliced yellow squash baked with eggs, cheese, and a buttered cracker topping — a Southern side dish.',
        'cuisine': 'American',
    }},
    'corpus-titled-zucchini-bread': {'action': 'edit', 'patch': {
        'name': 'Zucchini bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A spiced quick bread folded with grated zucchini — moist, lightly sweet, often with nuts.',
        'cuisine': 'American',
    }},
    'corpus-titled-chili': {'action': 'edit', 'patch': {
        'name': 'Chili',
        'notes': 'Ground beef simmered with tomatoes, beans, peppers, and chili powder until thick — the American bowl-of-red.',
        'cuisine': 'American',
    }},
    'corpus-titled-meat-loaf': {'action': 'edit', 'patch': {
        'name': 'Meatloaf',
        'notes': 'Ground beef mixed with breadcrumbs, egg, and onion, baked in a loaf shape and glazed with ketchup — a diner classic.',
        'cuisine': 'American',
    }},
    'corpus-titled-baked-beans': {'action': 'edit', 'patch': {
        'name': 'Baked beans',
        'notes': 'Navy beans slow-baked with bacon, molasses, brown sugar, and mustard in a tomato sauce — a barbecue side.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-fruit-salad': {'action': 'edit', 'patch': {
        'name': 'Fruit salad',
        'notes': 'Diced fresh fruit tossed together — sometimes with whipped topping or marshmallows in the American picnic style.',
    }},
    'corpus-titled-pumpkin-bread': {'action': 'edit', 'patch': {
        'name': 'Pumpkin bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A spiced quick bread made with pumpkin puree, eggs, oil, and warm spices — moist and lightly sweet.',
        'cuisine': 'American',
    }},
    'corpus-titled-carrot-cake': {'action': 'edit', 'patch': {
        'name': 'Carrot cake',
        'notes': 'A spiced layer cake with grated carrots, oil, and walnuts, topped with cream cheese frosting.',
        'cuisine': 'American',
    }},
    'corpus-titled-corn-casserole': {'action': 'edit', 'patch': {
        'name': 'Corn casserole',
        'notes': 'A spoon-bread-style bake of corn kernels, cream-style corn, eggs, butter, and sour cream — sweet, custardy, almost pudding-like.',
        'cuisine': 'American',
    }},
    'corpus-titled-cranberry-salad': {'action': 'edit', 'patch': {
        'name': 'Cranberry salad',
        'notes': 'A holiday gelatin salad of cranberries, pineapple, and other fruit set in sweetened gelatin — a Thanksgiving side.',
        'cuisine': 'American',
    }},
    'corpus-titled-potato-casserole': {'action': 'edit', 'patch': {
        'name': 'Potato casserole',
        'notes': 'Hash browns or sliced potatoes baked with sour cream, cheese, and cream of chicken soup, topped with butter or crushed crackers.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-chip-cookies': {'action': 'edit', 'patch': {
        'name': 'Chocolate chip cookies',
        'notes': 'Drop cookies of brown-and-white sugar butter dough studded with semisweet chocolate chips — the Toll House standard.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-broccoli-salad': {'action': 'edit', 'patch': {
        'name': 'Broccoli salad',
        'notes': 'Raw broccoli florets tossed with bacon, cheese, raisins, and red onion in a sweet-tangy mayonnaise dressing.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-brownies': {'action': 'edit', 'patch': {
        'name': 'Brownies',
        'notes': 'A dense fudgy chocolate bar baked with butter, eggs, cocoa or melted chocolate, sugar, and flour — cut into squares.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-banana-nut-bread': {'action': 'edit', 'patch': {
        'name': 'Banana nut bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'Banana bread with chopped walnuts or pecans folded into the batter.',
        'cuisine': 'American',
    }},
    'corpus-titled-sweet-potato-casserole': {'action': 'edit', 'patch': {
        'name': 'Sweet potato casserole',
        'notes': 'Mashed sweet potatoes baked under a brown-sugar-and-pecan streusel or toasted-marshmallow topping — a Southern Thanksgiving side.',
        'cuisine': 'American',
    }},
    'corpus-titled-taco-salad': {'action': 'edit', 'patch': {
        'name': 'Taco salad',
        'notes': 'Seasoned ground beef and beans over lettuce with cheese, tomatoes, and crushed tortilla chips in a creamy salsa-mayo dressing.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-apple-crisp': {'action': 'edit', 'patch': {
        'name': 'Apple crisp',
        'tags': ['dessert'],
        'notes': 'Spiced sliced apples baked under a crunchy oat-and-butter streusel topping — served warm, often with ice cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-sugar-cookies': {'action': 'edit', 'patch': {
        'name': 'Sugar cookies',
        'notes': 'Rolled or drop cookies of sweet butter dough — crisp at the edges, often glazed or sprinkled.',
        'serving_grams': 60,
    }},
    'corpus-titled-peanut-butter-pie': {'action': 'edit', 'patch': {
        'name': 'Peanut butter pie',
        'notes': 'A no-bake pie of peanut butter whipped with cream cheese and folded into whipped topping, set in a graham or chocolate-cookie crust.',
        'cuisine': 'American',
    }},
    'corpus-titled-peach-cobbler': {'action': 'edit', 'patch': {
        'name': 'Peach cobbler',
        'notes': 'Sliced peaches baked under a buttery cake or biscuit topping — a Southern dessert served warm with ice cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-peanut-butter-fudge': {'action': 'edit', 'patch': {
        'name': 'Peanut butter fudge',
        'notes': 'A no-cook fudge of peanut butter, sugar, butter, and milk cooked to soft-ball, beaten, and poured to set.',
        'serving_grams': 40,
    }},
    'corpus-titled-beef-stroganoff': {'action': 'edit', 'patch': {
        'name': 'Beef stroganoff',
        'notes': 'Strips of beef sautéed with mushrooms and onion in a sour-cream-and-mustard sauce, served over egg noodles.',
        'cuisine': 'Russian',
    }},
    'corpus-titled-sausage-balls': {'action': 'edit', 'patch': {
        'name': 'Sausage balls',
        'ingredient_categories': ['Processed meat', 'Aged cheese', 'Prepared mixes'],
        'tags': ['snack', 'breakfast'],
        'notes': 'Bite-size baked balls of breakfast sausage, shredded cheddar, and biscuit mix — a Southern appetizer.',
        'cuisine': 'American',
        'contains_add': ['pork'],
        'serving_grams': 60,
    }},
    'corpus-titled-corn-pudding': {'action': 'edit', 'patch': {
        'name': 'Corn pudding',
        'notes': 'Sweet corn kernels baked in a custard of eggs, milk, sugar, and butter — soft-set and lightly sweet.',
        'cuisine': 'American',
    }},
    'corpus-titled-breakfast-casserole': {'action': 'edit', 'patch': {
        'name': 'Breakfast casserole',
        'notes': 'A make-ahead bake of bread or hash browns layered with sausage, eggs, milk, and cheese — set overnight and baked in the morning.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-strawberry-pie': {'action': 'edit', 'patch': {
        'name': 'Strawberry pie',
        'notes': 'A pre-baked crust filled with fresh strawberries set in a sweet glaze — chilled and served with whipped cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-green-bean-casserole': {'action': 'edit', 'patch': {
        'name': 'Green bean casserole',
        'notes': 'Green beans baked in cream-of-mushroom soup with milk and topped with crispy fried onions — the Campbell\'s Thanksgiving side.',
        'cuisine': 'American',
    }},
    'corpus-titled-potato-soup': {'action': 'edit', 'patch': {
        'name': 'Potato soup',
        'notes': 'Diced potatoes simmered in broth with onion and milk or cream, finished with butter and herbs.',
    }},
    'corpus-titled-dump-cake': {'action': 'edit', 'patch': {
        'name': 'Dump cake',
        'notes': 'Canned fruit pie filling topped with a dry yellow-cake mix and pats of butter, baked until golden — no mixing required.',
        'cuisine': 'American',
    }},
    'corpus-titled-spinach-dip': {'action': 'edit', 'patch': {
        'name': 'Spinach dip',
        'ingredient_categories': ['Leafy greens', 'Fermented dairy', 'Fresh cheese', 'Prepared soups & broths', 'Other vegetables'],
        'tags': ['snack'],
        'notes': 'Chopped spinach mixed with sour cream, mayo, and a packet of soup mix — served cold in a hollowed bread bowl.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-fresh-apple-cake': {'action': 'edit', 'patch': {
        'name': 'Fresh apple cake',
        'notes': 'A spiced oil-based cake folded with chopped fresh apples and nuts — moist and tender.',
        'cuisine': 'American',
    }},
    'corpus-titled-banana-pudding': {'action': 'edit', 'patch': {
        'name': 'Banana pudding',
        'notes': 'Layers of vanilla pudding, sliced bananas, and vanilla wafers, topped with whipped cream or meringue — a Southern icebox dessert.',
        'cuisine': 'American',
    }},
    'corpus-titled-monkey-bread': {'action': 'edit', 'patch': {
        'name': 'Monkey bread',
        'tags': ['breakfast', 'dessert'],
        'notes': 'Pieces of biscuit dough rolled in cinnamon sugar, layered in a Bundt pan, and baked with a brown-sugar-butter glaze — pulled apart by hand.',
        'cuisine': 'American',
    }},
    'corpus-titled-potato-salad': {'action': 'edit', 'patch': {
        'name': 'Potato salad',
        'notes': 'Boiled potatoes tossed with mayo, mustard, chopped eggs, celery, pickles, and onion — chilled and served as a picnic side.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-pie': {'action': 'edit', 'patch': {
        'name': 'Chocolate pie',
        'notes': 'A pre-baked pastry shell filled with a cooked chocolate pudding or custard and topped with whipped cream or meringue.',
        'cuisine': 'American',
    }},
    'corpus-titled-oatmeal-cookies': {'action': 'edit', 'patch': {
        'name': 'Oatmeal cookies',
        'notes': 'Drop cookies of oats, butter, brown sugar, and spices — often with raisins or chocolate chips folded in.',
        'serving_grams': 60,
    }},
    'corpus-titled-macaroni-and-cheese': {'action': 'edit', 'patch': {
        'name': 'Macaroni and cheese',
        'notes': 'Elbow macaroni in a cheddar-bechamel sauce, often baked with a buttered breadcrumb topping — the American comfort classic.',
        'cuisine': 'American',
    }},
    'corpus-titled-fudge': {'action': 'edit', 'patch': {
        'name': 'Fudge',
        'notes': 'A dense sugar-and-cream confection cooked to soft-ball, beaten until creamy, and poured to set — usually chocolate flavored.',
        'serving_grams': 40,
    }},
    'corpus-titled-shrimp-dip': {'action': 'edit', 'patch': {
        'name': 'Shrimp dip',
        'tags': ['snack'],
        'notes': 'Cream cheese whipped with chopped shrimp, lemon, and seasonings — served chilled with crackers.',
        'serving_grams': 60,
    }},
    'corpus-titled-punch': {'action': 'edit', 'patch': {
        'name': 'Party punch',
        'ingredient_categories': ['Juices', 'Tropical fruits', 'Citrus', 'Sugar & sweeteners', 'Soft drinks'],
        'tags': ['snack'],
        'notes': 'A non-alcoholic party drink of fruit juices and ginger ale or sherbet, served from a punch bowl over ice.',
        'serving_grams': 240,
    }},
    'corpus-titled-spaghetti-sauce': {'action': 'edit', 'patch': {
        'name': 'Spaghetti meat sauce',
        'notes': 'A long-simmered tomato sauce with ground beef, onions, peppers, and Italian herbs — served over spaghetti.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-chicken-salad': {'action': 'edit', 'patch': {
        'name': 'Chicken salad',
        'notes': 'Chopped cooked chicken tossed with mayo, celery, grapes, and nuts — served as a sandwich filling or over greens.',
        'cuisine': 'American',
    }},
    'corpus-titled-taco-dip': {'action': 'edit', 'patch': {
        'name': 'Taco dip',
        'tags': ['snack'],
        'notes': 'Layers of refried beans or seasoned cream cheese with sour cream, salsa, shredded cheese, lettuce, and olives — served cold with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-chocolate-cake': {'action': 'edit', 'patch': {
        'name': 'Chocolate cake',
        'notes': 'A layer or sheet cake of cocoa-based butter or oil batter, frosted with chocolate buttercream or ganache.',
    }},
    'corpus-titled-scalloped-potatoes': {'action': 'edit', 'patch': {
        'name': 'Scalloped potatoes',
        'notes': 'Sliced potatoes layered with onions and baked in a cream-and-cheese sauce until tender and golden on top.',
        'cuisine': 'American',
    }},
    'corpus-titled-banana-split-cake': {'action': 'edit', 'patch': {
        'name': 'Banana split cake',
        'notes': 'A no-bake layered dessert of graham-cracker crust, whipped cream cheese filling, sliced bananas, crushed pineapple, and whipped topping with cherries.',
        'cuisine': 'American',
    }},
    'corpus-titled-fruit-dip': {'action': 'edit', 'patch': {
        'name': 'Fruit dip',
        'tags': ['snack', 'dessert'],
        'notes': 'A sweet cream-cheese-and-marshmallow-fluff dip served chilled with sliced fresh fruit.',
        'serving_grams': 60,
    }},
    'corpus-titled-pasta-salad': {'action': 'edit', 'patch': {
        'name': 'Pasta salad',
        'notes': 'Cooked pasta tossed with chopped vegetables, cheese, and Italian or mayo-based dressing — served cold.',
        'cuisine': 'American',
    }},
    'corpus-titled-zucchini-casserole': {'action': 'edit', 'patch': {
        'name': 'Zucchini casserole',
        'notes': 'Sliced zucchini baked with onions, sour cream, and shredded cheese under a buttered cracker or stuffing topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-enchiladas': {'action': 'edit', 'patch': {
        'name': 'Chicken enchiladas',
        'notes': 'Tortillas rolled around shredded chicken and cheese, lined in a baking dish, covered in red or green chile sauce and more cheese, and baked.',
        'cuisine': 'Mexican',
    }},
    'corpus-titled-vegetable-casserole': {'action': 'edit', 'patch': {
        'name': 'Vegetable casserole',
        'notes': 'A mix of vegetables baked with cheese and a buttery cracker or breadcrumb topping.',
    }},
    'corpus-titled-sweet-potato-pie': {'action': 'edit', 'patch': {
        'name': 'Sweet potato pie',
        'notes': 'A custard pie of mashed sweet potato, eggs, evaporated milk, and warm spices in a butter crust — a Southern Thanksgiving classic.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-rice-pudding': {'action': 'edit', 'patch': {
        'name': 'Rice pudding',
        'notes': 'Cooked rice simmered slowly in milk and sugar with vanilla and cinnamon — served warm or chilled.',
    }},
    'corpus-titled-caramel-corn': {'action': 'edit', 'patch': {
        'name': 'Caramel corn',
        'tags': ['snack', 'dessert'],
        'notes': 'Popped corn coated in a hot caramel of butter, brown sugar, and corn syrup, then baked until crisp.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-macaroni-salad': {'action': 'edit', 'patch': {
        'name': 'Macaroni salad',
        'notes': 'Elbow macaroni tossed with mayo, mustard, chopped celery, onion, pickle, and hard-boiled egg — chilled as a picnic side.',
        'cuisine': 'American',
    }},
    'corpus-titled-hot-chicken-salad': {'action': 'edit', 'patch': {
        'name': 'Hot chicken salad',
        'notes': 'Chopped cooked chicken bound with mayo and lemon, mixed with celery and almonds, topped with cheese and crushed potato chips, and baked until bubbling.',
        'cuisine': 'American',
    }},
    'corpus-titled-coconut-pie': {'action': 'edit', 'patch': {
        'name': 'Coconut pie',
        'notes': 'A custard pie of eggs, milk, sugar, and shredded coconut — sometimes self-crusting (impossible pie) without a separate pastry shell.',
        'cuisine': 'American',
    }},
    'corpus-titled-hamburger-casserole': {'action': 'edit', 'patch': {
        'name': 'Hamburger casserole',
        'notes': 'Browned ground beef baked with potatoes or noodles, vegetables, and shredded cheese under a tomato or cream-soup sauce.',
        'cuisine': 'American',
    }},
    'corpus-titled-mexican-cornbread': {'action': 'edit', 'patch': {
        'name': 'Mexican cornbread',
        'notes': 'A skillet cornbread loaded with jalapeños, cheddar cheese, corn kernels, and sometimes onion or peppers — savory and rich.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-mexican-casserole': {'action': 'edit', 'patch': {
        'name': 'Mexican casserole',
        'notes': 'Layered tortillas, seasoned meat, salsa, beans, and cheese baked together — a homestyle Tex-Mex one-dish meal.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-sloppy-joes': {'action': 'edit', 'patch': {
        'name': 'Sloppy joes',
        'notes': 'Ground beef simmered in a sweet-tangy tomato-and-ketchup sauce with onions and peppers, served piled on soft hamburger buns.',
        'cuisine': 'American',
    }},
    'corpus-titled-stuffed-mushrooms': {'action': 'edit', 'patch': {
        'name': 'Stuffed mushrooms',
        'tags': ['snack'],
        'notes': 'Mushroom caps filled with a mixture of sausage or breadcrumbs, herbs, and Parmesan, then baked until golden.',
        'serving_grams': 80,
    }},
    'corpus-titled-hush-puppies': {'action': 'edit', 'patch': {
        'name': 'Hush puppies',
        'tags': ['snack'],
        'notes': 'Small balls of cornmeal batter with onion, deep-fried until crisp — a Southern fish-fry side.',
        'cuisine': 'Southern',
        'serving_grams': 60,
    }},
    'corpus-titled-cheese-cake': {'action': 'edit', 'patch': {
        'name': 'Cheesecake',
        'notes': 'A baked or no-bake dessert of sweetened cream cheese set on a graham-cracker crust — dense and tangy.',
    }},
    'corpus-titled-chicken-divan': {'action': 'edit', 'patch': {
        'name': 'Chicken divan',
        'notes': 'Cooked chicken and steamed broccoli baked in a sherry-and-curry-laced cream sauce topped with cheese and breadcrumbs.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-and-rice': {'action': 'edit', 'patch': {
        'name': 'Chicken and rice',
        'notes': 'Chicken pieces baked or simmered with rice in a seasoned broth or cream-soup sauce until both are tender.',
    }},
    'corpus-titled-blueberry-muffins': {'action': 'edit', 'patch': {
        'name': 'Blueberry muffins',
        'tags': ['breakfast', 'snack'],
        'notes': 'Tender muffins studded with fresh or frozen blueberries, often topped with a sugar streusel.',
        'serving_grams': 60,
    }},
    'corpus-titled-taco-soup': {'action': 'edit', 'patch': {
        'name': 'Taco soup',
        'notes': 'Ground beef simmered with diced tomatoes, beans, corn, and taco seasoning — a soupy chili-style one-pot.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-chicken-spaghetti': {'action': 'edit', 'patch': {
        'name': 'Chicken spaghetti',
        'notes': 'Cooked spaghetti tossed with shredded chicken, peppers, onions, and Velveeta-style cheese sauce, then baked until bubbly.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-watergate-salad': {'action': 'edit', 'patch': {
        'name': 'Watergate salad',
        'ingredient_categories': ['Tropical fruits', 'Candy & desserts', 'Nuts', 'Cream & butter'],
        'tags': ['dessert'],
        'notes': 'A green fluffy salad-dessert of pistachio pudding mix, crushed pineapple, miniature marshmallows, and Cool Whip with chopped pecans.',
        'cuisine': 'American',
    }},
    'corpus-titled-tuna-casserole': {'action': 'edit', 'patch': {
        'name': 'Tuna casserole',
        'notes': 'Cooked egg noodles baked with canned tuna, cream of mushroom soup, peas, and cheese, topped with crushed potato chips or breadcrumbs.',
        'cuisine': 'American',
    }},
    'corpus-titled-fruit-pizza': {'action': 'edit', 'patch': {
        'name': 'Fruit pizza',
        'tags': ['dessert'],
        'notes': 'A sugar-cookie crust spread with sweetened cream cheese and topped with sliced fresh fruit and a citrus glaze.',
        'cuisine': 'American',
    }},
    'corpus-titled-applesauce-cake': {'action': 'edit', 'patch': {
        'name': 'Applesauce cake',
        'notes': 'A spiced cake made moist with applesauce, often with raisins and walnuts folded in — a classic depression-era bake.',
        'cuisine': 'American',
    }},
    'corpus-titled-spanish-rice': {'action': 'edit', 'patch': {
        'name': 'Spanish rice',
        'notes': 'Long-grain rice toasted in oil, then simmered with tomato sauce, onions, peppers, and broth — Tex-Mex rather than Iberian despite the name.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-hash-brown-casserole': {'action': 'edit', 'patch': {
        'name': 'Hash brown casserole',
        'notes': 'Frozen shredded hash browns baked with cream of chicken soup, sour cream, and shredded cheese under a cornflake topping — the "funeral potatoes" classic.',
        'cuisine': 'American',
    }},
    'corpus-titled-vegetable-dip': {'action': 'edit', 'patch': {
        'name': 'Vegetable dip',
        'tags': ['snack'],
        'notes': 'A sour-cream-and-mayo dip seasoned with dried herbs, garlic, and onion — served chilled with raw vegetables.',
        'serving_grams': 60,
    }},
    'corpus-titled-no-bake-cookies': {'action': 'edit', 'patch': {
        'name': 'No-bake cookies',
        'notes': 'Cocoa, sugar, milk, and butter cooked to a fudge, then stirred with peanut butter and oats and dropped onto wax paper to set.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-dirt-cake': {'action': 'edit', 'patch': {
        'name': 'Dirt cake',
        'notes': 'A layered no-bake dessert of crushed chocolate cookies, vanilla pudding mixed with cream cheese and whipped topping — served in a flowerpot for novelty.',
        'cuisine': 'American',
    }},
    'corpus-titled-peanut-butter-balls': {'action': 'edit', 'patch': {
        'name': 'Peanut butter balls',
        'tags': ['dessert', 'snack'],
        'notes': 'No-bake balls of peanut butter, powdered sugar, and butter rolled and dipped in melted chocolate — buckeye-style.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-tater-tot-casserole': {'action': 'edit', 'patch': {
        'name': 'Tater tot casserole',
        'notes': 'Ground beef and vegetables baked under a layer of frozen tater tots with cream of mushroom soup and shredded cheese — a Midwestern hot-dish.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-pie': {'action': 'edit', 'patch': {
        'name': 'Chicken pot pie',
        'ingredient_categories': ['Poultry', 'Other vegetables', 'Flours', 'Milk', 'Margarine & shortening', 'Salt & seasonings'],
        'tags': ['dinner', 'lunch'],
        'notes': 'Diced chicken and vegetables in a creamy gravy baked under a flaky pastry crust.',
        'cuisine': 'American',
        'serving_grams': 320,
    }},
    'corpus-titled-chicken-and-dumplings': {'action': 'edit', 'patch': {
        'name': 'Chicken and dumplings',
        'notes': 'Chicken simmered in broth with vegetables, finished with soft dough dumplings dropped on top to steam-cook.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-vegetable-soup': {'action': 'edit', 'patch': {
        'name': 'Vegetable soup',
        'notes': 'A clear-broth soup of mixed vegetables — sometimes with ground beef and tomato — simmered until tender.',
    }},
    'corpus-titled-buttermilk-pie': {'action': 'edit', 'patch': {
        'name': 'Buttermilk pie',
        'notes': 'A Southern custard pie of buttermilk, eggs, sugar, butter, and a touch of flour — tangy and silky in a flaky shell.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-vegetable-pizza': {'action': 'edit', 'patch': {
        'name': 'Vegetable pizza',
        'tags': ['snack'],
        'notes': 'A cold "pizza" of crescent-roll crust spread with herbed cream cheese and topped with chopped raw vegetables and shredded cheese.',
        'cuisine': 'American',
        'serving_grams': 100,
    }},
    'corpus-titled-coconut-cake': {'action': 'edit', 'patch': {
        'name': 'Coconut cake',
        'notes': 'A white layer cake brushed with coconut milk and frosted with cream-cheese or buttercream icing, covered in shredded coconut.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-french-onion-soup': {'action': 'edit', 'patch': {
        'name': 'French onion soup',
        'notes': 'Slow-caramelized onions simmered in beef broth with wine and herbs, topped with a toasted bread round and broiled with melted Gruyère.',
        'cuisine': 'French',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-pizza-casserole': {'action': 'edit', 'patch': {
        'name': 'Pizza casserole',
        'notes': 'Cooked pasta layered with ground beef, pepperoni, marinara, and mozzarella, baked until bubbly — pizza flavors in a casserole.',
        'cuisine': 'Italian-American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-angel-biscuits': {'action': 'edit', 'patch': {
        'name': 'Angel biscuits',
        'tags': ['breakfast'],
        'notes': 'A tender Southern biscuit leavened with both yeast and baking powder for an exceptionally light, fluffy rise.',
        'cuisine': 'Southern',
        'serving_grams': 55,
    }},
    'corpus-titled-snickerdoodles': {'action': 'edit', 'patch': {
        'name': 'Snickerdoodles',
        'tags': ['dessert'],
        'notes': 'Soft butter cookies rolled in cinnamon sugar before baking, with a slight tang from cream of tartar.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-corn-bread': {'action': 'edit', 'patch': {
        'name': 'Cornbread',
        'notes': 'A quick bread of cornmeal, flour, eggs, and milk, baked in a hot skillet or pan — Southern style is unsweetened and crisp-edged.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-cabbage-casserole': {'action': 'edit', 'patch': {
        'name': 'Cabbage casserole',
        'notes': 'Shredded cabbage baked with ground beef, tomato, and cheese — a deconstructed cabbage-roll bake.',
        'cuisine': 'American',
    }},
    'corpus-titled-guacamole': {'action': 'edit', 'patch': {
        'name': 'Guacamole',
        'tags': ['snack', 'condiment'],
        'notes': 'Mashed ripe avocado mixed with lime, salt, onion, jalapeño, and cilantro — served with tortilla chips.',
        'cuisine': 'Mexican',
        'serving_grams': 60,
    }},
    'corpus-titled-lasagne': {'action': 'edit', 'patch': {
        'name': 'Lasagna',
        'notes': 'Layered pasta sheets with ricotta, ground beef in tomato sauce, and melted mozzarella, baked until bubbly.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-ice-cream': {'action': 'edit', 'patch': {
        'name': 'Ice cream',
        'notes': 'A frozen custard of milk, cream, eggs, sugar, and vanilla churned in an ice-cream maker until set.',
        'serving_grams': 85,
    }},
    'corpus-titled-punch-bowl-cake': {'action': 'edit', 'patch': {
        'name': 'Punch bowl cake',
        'notes': 'A layered trifle of cubed cake, pudding, fruit, and whipped topping assembled in a glass punch bowl.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-chicken-tetrazzini': {'action': 'edit', 'patch': {
        'name': 'Chicken tetrazzini',
        'notes': 'Cooked spaghetti or linguine baked with chicken, mushrooms, and a sherry-cream sauce under a Parmesan and breadcrumb topping.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-pretzel-salad': {'action': 'edit', 'patch': {
        'name': 'Strawberry pretzel salad',
        'ingredient_categories': ['Baked snacks & pastries', 'Cream & butter', 'Fresh cheese', 'Sugar & sweeteners', 'Berries'],
        'tags': ['dessert'],
        'notes': 'A layered dessert of crushed-pretzel crust, sweet whipped cream cheese, and strawberry gelatin with fresh strawberries — salty-sweet.',
        'cuisine': 'American',
        'serving_grams': 140,
    }},
    'corpus-titled-spaghetti-salad': {'action': 'edit', 'patch': {
        'name': 'Spaghetti salad',
        'notes': 'Cold cooked spaghetti tossed with Italian dressing, chopped vegetables, olives, and Parmesan — a picnic pasta variant.',
        'cuisine': 'American',
    }},
    'corpus-titled-strawberry-salad': {'action': 'edit', 'patch': {
        'name': 'Strawberry salad',
        'notes': 'Sliced strawberries layered with whipped cream or yogurt and toasted nuts — sometimes set with gelatin.',
    }},
    'corpus-titled-strawberry-cake': {'action': 'edit', 'patch': {
        'name': 'Strawberry cake',
        'notes': 'A pink layer cake made from white cake mix and strawberry gelatin with fresh or frozen strawberries folded in.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-artichoke-dip': {'action': 'edit', 'patch': {
        'name': 'Artichoke dip',
        'ingredient_categories': ['Other vegetables', 'Fresh cheese', 'Aged cheese', 'Fermented dairy', 'Extracts & essences'],
        'tags': ['snack'],
        'notes': 'Chopped artichoke hearts mixed with mayo, sour cream, and Parmesan, baked until bubbly — served hot with crackers or bread.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-bread-and-butter-pickles': {'action': 'drop', 'reason': 'pickled condiment, not a coherent meal'},
    'corpus-titled-rolls': {'action': 'edit', 'patch': {
        'name': 'Dinner rolls',
        'tags': ['dinner', 'lunch'],
        'notes': 'Soft yeasted rolls of enriched dough — pulled-apart and served warm with butter at dinner.',
        'serving_grams': 50,
    }},
    'corpus-titled-pepper-steak': {'action': 'edit', 'patch': {
        'name': 'Pepper steak',
        'notes': 'Strips of beef stir-fried with sliced bell peppers and onions in a soy-and-ginger sauce, served over rice.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-bran-muffins': {'action': 'edit', 'patch': {
        'name': 'Bran muffins',
        'tags': ['breakfast'],
        'notes': 'High-fiber muffins of wheat bran, flour, buttermilk or molasses, and often raisins — moist and slightly sweet.',
        'serving_grams': 60,
    }},
    'corpus-titled-chicken-and-rice-casserole': {'action': 'edit', 'patch': {
        'name': 'Chicken and rice casserole',
        'notes': 'Raw rice and chicken pieces baked together with cream of mushroom soup and a packet of onion soup mix until rice absorbs the broth.',
        'cuisine': 'American',
    }},
    'corpus-titled-broccoli-cornbread': {'action': 'edit', 'patch': {
        'name': 'Broccoli cornbread',
        'tags': ['dinner', 'lunch'],
        'notes': 'A skillet cornbread enriched with chopped broccoli, cottage cheese, and butter — a moist, savory side.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-cream-cheese-pound-cake': {'action': 'edit', 'patch': {
        'name': 'Cream cheese pound cake',
        'notes': 'A dense, fine-crumb pound cake made tender by a block of cream cheese beaten into the butter-and-sugar base.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-pork-chop-casserole': {'action': 'edit', 'patch': {
        'name': 'Pork chop casserole',
        'ingredient_categories': ['Red meat', 'Starchy vegetables', 'Other vegetables', 'Mushrooms', 'Salt & seasonings', 'Peppers & nightshades', 'Refined grains'],
        'notes': 'Bone-in pork chops baked over rice or sliced potatoes in cream of mushroom soup.',
        'cuisine': 'American',
    }},
    'corpus-titled-lemon-pie': {'action': 'edit', 'patch': {
        'name': 'Lemon pie',
        'notes': 'A pre-baked crust filled with tangy lemon custard and topped with meringue or whipped cream — typically lemon meringue or icebox style.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-cacciatore': {'action': 'edit', 'patch': {
        'name': 'Chicken cacciatore',
        'notes': 'Bone-in chicken braised hunter-style in tomatoes, peppers, mushrooms, onions, and wine with herbs.',
        'cuisine': 'Italian',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-crab-dip': {'action': 'edit', 'patch': {
        'name': 'Crab dip',
        'tags': ['snack'],
        'notes': 'Lump crab mixed with cream cheese, mayo, lemon, and Old Bay — served hot or cold with crackers or crostini.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-deviled-eggs': {'action': 'edit', 'patch': {
        'name': 'Deviled eggs',
        'tags': ['snack'],
        'notes': 'Hard-boiled eggs halved and filled with a yolk paste of mayo, mustard, and seasonings — dusted with paprika.',
        'cuisine': 'American',
        'serving_grams': 50,
    }},
    'corpus-titled-mexican-corn-bread': {'action': 'edit', 'patch': {
        'name': 'Mexican cornbread (variant)',
        'notes': 'Cornbread baked with cheddar, creamed corn, and chopped jalapeños — slightly sweeter than the skillet-Tex-Mex version.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-stuffed-peppers': {'action': 'edit', 'patch': {
        'name': 'Stuffed peppers',
        'notes': 'Bell peppers hollowed and filled with seasoned ground beef and rice in tomato sauce, baked until tender.',
    }},
    'corpus-titled-swiss-steak': {'action': 'edit', 'patch': {
        'name': 'Swiss steak',
        'notes': 'Round steak pounded thin, dredged in flour, browned, then braised slowly with onions and tomato until fork-tender.',
        'cuisine': 'American',
    }},
    'corpus-titled-mexican-chicken': {'action': 'edit', 'patch': {
        'name': 'Mexican chicken',
        'notes': 'Cooked chicken layered with tortilla chips, salsa, peppers, and cheese, baked into a Tex-Mex casserole.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-asparagus-casserole': {'action': 'edit', 'patch': {
        'name': 'Asparagus casserole',
        'notes': 'Canned or fresh asparagus baked with hard-boiled eggs, cheese, and mushroom soup under a cracker-crumb topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-cinnamon-rolls': {'action': 'edit', 'patch': {
        'name': 'Cinnamon rolls',
        'tags': ['breakfast', 'dessert'],
        'notes': 'Yeasted dough rolled around butter, brown sugar, and cinnamon, sliced into spirals, baked, and drizzled with sweet glaze or cream-cheese frosting.',
        'serving_grams': 90,
    }},
    'corpus-titled-cornbread': {'action': 'edit', 'patch': {
        'name': 'Cornbread (skillet)',
        'notes': 'A skillet-baked quick bread of cornmeal, eggs, milk, and a little flour — slightly sweet in the Northern style, savory in the Southern.',
        'cuisine': 'American',
    }},
    'corpus-titled-german-potato-salad': {'action': 'edit', 'patch': {
        'name': 'German potato salad',
        'notes': 'Sliced warm potatoes tossed with crisp bacon, onions, and a tangy bacon-fat-and-vinegar dressing — served warm rather than cold.',
        'cuisine': 'German',
        'contains_add': ['pork'],
    }},
    'corpus-titled-oatmeal-cake': {'action': 'edit', 'patch': {
        'name': 'Oatmeal cake',
        'notes': 'A spiced cake made with oatmeal soaked in hot water, topped with a broiled brown-sugar-coconut-pecan glaze.',
        'cuisine': 'American',
    }},
    'corpus-titled-meatballs': {'action': 'edit', 'patch': {
        'name': 'Meatballs',
        'notes': 'Ground beef mixed with breadcrumbs, egg, and seasonings, rolled and baked or browned, then simmered in tomato or cream sauce.',
    }},
    'corpus-titled-taco-casserole': {'action': 'edit', 'patch': {
        'name': 'Taco casserole',
        'notes': 'Layered casserole of seasoned ground beef, tortilla chips, salsa, beans, and shredded cheese — baked until bubbly.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-mexican-dip': {'action': 'edit', 'patch': {
        'name': 'Mexican layer dip',
        'tags': ['snack'],
        'notes': 'A cold layered dip of refried beans, sour cream and seasonings, salsa, cheese, lettuce, and olives — served with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-chocolate-pound-cake': {'action': 'edit', 'patch': {
        'name': 'Chocolate pound cake',
        'notes': 'A dense pound cake enriched with cocoa or melted chocolate, baked in a tube or loaf pan and often glazed.',
        'cuisine': 'American',
    }},
    'corpus-titled-biscuits': {'action': 'edit', 'patch': {
        'name': 'Buttermilk biscuits',
        'tags': ['breakfast'],
        'notes': 'A flaky Southern quick bread of flour, baking powder, cold butter or shortening, and buttermilk — cut and baked until risen.',
        'cuisine': 'Southern',
        'serving_grams': 55,
    }},
    'corpus-titled-sauerkraut-salad': {'action': 'edit', 'patch': {
        'name': 'Sauerkraut salad',
        'notes': 'Drained sauerkraut tossed with chopped peppers, onion, celery, and a sweet vinegar dressing — chilled overnight.',
        'cuisine': 'German-American',
    }},
    'corpus-titled-turtle-cake': {'action': 'edit', 'patch': {
        'name': 'Turtle cake',
        'notes': 'Chocolate cake layered with caramel sauce, chopped pecans, and chocolate chips — turtle-candy flavors baked into a sheet cake.',
        'cuisine': 'American',
    }},
    'corpus-titled-shrimp-creole': {'action': 'edit', 'patch': {
        'name': 'Shrimp creole',
        'notes': 'Shrimp simmered in a Louisiana sauce of tomatoes, peppers, onion, celery, and Creole seasoning, served over rice.',
        'cuisine': 'Creole',
    }},
    'corpus-titled-sausage-casserole': {'action': 'edit', 'patch': {
        'name': 'Sausage casserole',
        'notes': 'Breakfast sausage browned and baked with eggs, milk, bread or rice, cheese, and vegetables — a hearty one-dish meal.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-enchilada-casserole': {'action': 'edit', 'patch': {
        'name': 'Enchilada casserole',
        'notes': 'A layered "stacked" enchilada bake of tortillas, seasoned meat, enchilada sauce, and cheese — easier than rolling.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-spinach-balls': {'action': 'edit', 'patch': {
        'name': 'Spinach balls',
        'tags': ['snack'],
        'notes': 'Bite-size baked balls of chopped spinach, herbed stuffing mix, eggs, butter, and Parmesan — a freezer-friendly appetizer.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-fried-rice': {'action': 'edit', 'patch': {
        'name': 'Fried rice',
        'notes': 'Day-old cold rice stir-fried with eggs, scallions, peas and carrots, soy sauce, and often diced meat — fast wok-style.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-chess-pie': {'action': 'edit', 'patch': {
        'name': 'Chess pie',
        'notes': 'A Southern custard pie of butter, sugar, eggs, and a touch of cornmeal or flour — translucent and rich.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-fruit-cocktail-cake': {'action': 'edit', 'patch': {
        'name': 'Fruit cocktail cake',
        'notes': 'A one-bowl sheet cake folded with canned fruit cocktail and its syrup, often with a brown-sugar-coconut broiled topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-spinach-salad': {'action': 'edit', 'patch': {
        'name': 'Spinach salad',
        'notes': 'Baby spinach with crisp bacon, sliced mushrooms, hard-boiled egg, and red onion in a sweet warm bacon dressing.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-strawberry-bread': {'action': 'edit', 'patch': {
        'name': 'Strawberry bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A spiced quick bread folded with chopped fresh or frozen strawberries — moist and lightly sweet, often with nuts.',
        'cuisine': 'American',
    }},
    'corpus-titled-earthquake-cake': {'action': 'edit', 'patch': {
        'name': 'Earthquake cake',
        'notes': 'A German-chocolate-style sheet cake with coconut and pecans on the bottom and a cream-cheese-and-powdered-sugar layer that swirls down through the batter while baking.',
        'cuisine': 'American',
    }},
    'corpus-titled-pineapple-casserole': {'action': 'edit', 'patch': {
        'name': 'Pineapple casserole',
        'tags': ['dinner', 'lunch'],
        'notes': 'Canned pineapple chunks baked with sharp cheddar, sugar, and a buttery cracker topping — a Southern sweet-savory side.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-corn-chowder': {'action': 'edit', 'patch': {
        'name': 'Corn chowder',
        'notes': 'Sweet corn simmered in a milk-or-cream base with diced potatoes, onion, and bacon until thickened.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-spinach-casserole': {'action': 'edit', 'patch': {
        'name': 'Spinach casserole',
        'notes': 'Chopped spinach baked in a custard with cream cheese, eggs, and butter under a Parmesan or cheddar top.',
    }},
    'corpus-titled-banana-cake': {'action': 'edit', 'patch': {
        'name': 'Banana cake',
        'notes': 'A soft layer or sheet cake of mashed bananas, butter, sugar, and eggs — often frosted with cream-cheese icing.',
        'cuisine': 'American',
    }},
    'corpus-titled-breakfast-pizza': {'action': 'edit', 'patch': {
        'name': 'Breakfast pizza',
        'notes': 'A crescent-roll or pizza-dough crust topped with scrambled eggs, breakfast sausage or bacon, cheese, and sometimes hash browns — baked until set.',
        'cuisine': 'American',
        'contains_add': ['pork'],
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

    print('corpus-titled batch-1 audit applied (top 150 by frequency).')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
