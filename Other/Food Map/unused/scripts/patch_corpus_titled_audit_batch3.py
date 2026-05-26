"""Corpus-titled meals audit — batch 3 (entries 301-450 by frequency, 318 -> 229).

Same standard: idiomatic sentence-case name, 1-2 sentence factual notes,
clean ingredient_categories, real-world tags, cuisine where the name implies
one, contains:['pork'] / ['alcohol'] only when traditionally mandatory.
Drop entries that aren't coherent meals.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

DECISIONS: dict[str, dict] = {
    'corpus-titled-minestrone-soup': {'action': 'edit', 'patch': {
        'name': 'Minestrone soup',
        'notes': 'A hearty Italian vegetable soup of beans, pasta, tomato, and seasonal vegetables in a herb-scented broth, finished with Parmesan.',
        'cuisine': 'Italian',
    }},
    'corpus-titled-mandarin-orange-cake': {'action': 'edit', 'patch': {
        'name': 'Mandarin orange cake (pig pickin\' cake)',
        'notes': 'A yellow cake folded with canned mandarin oranges, topped with a whipped-cream-and-pineapple frosting — the Southern "pig pickin\'" cake.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-candied-sweet-potatoes': {'action': 'edit', 'patch': {
        'name': 'Candied sweet potatoes',
        'notes': 'Sliced sweet potatoes baked in a butter-and-brown-sugar glaze with cinnamon — a Southern Thanksgiving side.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-zucchini-pie': {'action': 'edit', 'patch': {
        'name': 'Zucchini pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'A crustless quiche-style bake of sliced zucchini with eggs, mozzarella, Parmesan, and herbs.',
        'cuisine': 'American',
        'serving_grams': 260,
    }},
    'corpus-titled-egg-custard': {'action': 'edit', 'patch': {
        'name': 'Egg custard',
        'notes': 'A baked or steamed custard of eggs, milk, sugar, and vanilla — silky and softly set, dusted with nutmeg.',
    }},
    'corpus-titled-baked-pineapple': {'action': 'edit', 'patch': {
        'name': 'Baked pineapple',
        'notes': 'Crushed pineapple folded with eggs, sugar, and bread cubes, baked into a sweet-savory side served with ham.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-baked-macaroni-and-cheese': {'action': 'edit', 'patch': {
        'name': 'Baked macaroni and cheese',
        'notes': 'Elbow macaroni in a cheddar bechamel poured into a casserole, topped with more cheese and buttered breadcrumbs, baked until bubbly.',
        'cuisine': 'American',
    }},
    'corpus-titled-lemon-chicken': {'action': 'edit', 'patch': {
        'name': 'Lemon chicken',
        'notes': 'Chicken breasts dredged and pan-fried, then finished in a lemon-butter pan sauce — sometimes thickened with flour.',
    }},
    'corpus-titled-hamburger-stroganoff': {'action': 'edit', 'patch': {
        'name': 'Hamburger stroganoff',
        'notes': 'Browned ground beef simmered with mushrooms and onion in a sour-cream-and-mushroom-soup gravy, served over egg noodles — a quick weeknight version of stroganoff.',
        'cuisine': 'American',
    }},
    'corpus-titled-peanut-butter-bars': {'action': 'edit', 'patch': {
        'name': 'Peanut butter bars',
        'tags': ['dessert'],
        'notes': 'A buttery peanut-butter shortbread base topped with a chocolate-peanut-butter frosting — cut into bars.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-pumpkin-bars': {'action': 'edit', 'patch': {
        'name': 'Pumpkin bars',
        'tags': ['dessert'],
        'notes': 'A sheet-pan version of pumpkin cake topped with cream cheese frosting, cut into squares.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-lemonade-pie': {'action': 'edit', 'patch': {
        'name': 'Lemonade pie',
        'notes': 'Frozen lemonade concentrate folded with sweetened condensed milk and whipped topping, poured into a graham crust and chilled until set.',
        'cuisine': 'American',
        'serving_grams': 140,
    }},
    'corpus-titled-chicken-supreme': {'action': 'edit', 'patch': {
        'name': 'Chicken supreme',
        'notes': 'Chicken breasts simmered in a sour cream and cream-of-mushroom-soup sauce with onions and mushrooms — a 1950s casserole-style preparation.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-chess-pie': {'action': 'edit', 'patch': {
        'name': 'Chocolate chess pie',
        'notes': 'A Southern chess pie variant with cocoa or melted chocolate — a translucent, glossy chocolate custard in a flaky crust.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-blueberry-pie': {'action': 'edit', 'patch': {
        'name': 'Blueberry pie',
        'notes': 'A double-crust pie of fresh blueberries tossed with sugar and a thickener, baked until the filling bubbles through the lattice.',
        'cuisine': 'American',
    }},
    'corpus-titled-twice-baked-potatoes': {'action': 'edit', 'patch': {
        'name': 'Twice baked potatoes',
        'notes': 'Baked russet potatoes split, scooped, mashed with butter, sour cream, cheese, and bacon, returned to the shells, and baked again.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-chicken-and-broccoli-casserole': {'action': 'edit', 'patch': {
        'name': 'Chicken and broccoli casserole',
        'notes': 'Cooked chicken and broccoli baked in a mayo, lemon juice, and cream-of-chicken-soup sauce, topped with cheese and buttered breadcrumbs.',
        'cuisine': 'American',
    }},
    'corpus-titled-cornbread-dressing': {'action': 'edit', 'patch': {
        'name': 'Cornbread dressing',
        'notes': 'Crumbled cornbread mixed with sauteed onions, celery, herbs, and broth, bound with eggs, and baked — the Southern Thanksgiving stuffing.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-texas-hash': {'action': 'edit', 'patch': {
        'name': 'Texas hash',
        'notes': 'Browned ground beef and rice simmered with onions, peppers, and chili-spiced tomato — then sometimes baked under cheese.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-butter-cookies': {'action': 'edit', 'patch': {
        'name': 'Butter cookies',
        'notes': 'A simple piped or rolled shortbread of butter, sugar, flour, and vanilla — crisp and buttery.',
        'serving_grams': 30,
    }},
    'corpus-titled-carrot-casserole': {'action': 'edit', 'patch': {
        'name': 'Carrot casserole',
        'notes': 'Sliced cooked carrots baked under a cheesy buttered-cracker topping — a Southern side dish.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-italian-chicken': {'action': 'edit', 'patch': {
        'name': 'Italian chicken',
        'notes': 'Chicken pieces baked or simmered with Italian salad dressing or marinara — a low-effort weeknight preparation.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-butterscotch-pie': {'action': 'edit', 'patch': {
        'name': 'Butterscotch pie',
        'notes': 'A baked pastry shell filled with brown-sugar-and-butter custard, topped with whipped cream or meringue.',
        'cuisine': 'American',
    }},
    'corpus-titled-strawberry-shortcake': {'action': 'edit', 'patch': {
        'name': 'Strawberry shortcake',
        'tags': ['dessert'],
        'notes': 'A split tender biscuit or sponge cake layered with macerated strawberries and whipped cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-strawberry-pretzel-salad': {'action': 'edit', 'patch': {
        'name': 'Strawberry pretzel salad (variant)',
        'tags': ['dessert'],
        'notes': 'Crushed-pretzel crust topped with sweetened cream cheese and strawberry-Jello-with-strawberries — chilled and cut into squares.',
        'cuisine': 'Southern',
        'serving_grams': 140,
    }},
    'corpus-titled-lemon-cake': {'action': 'edit', 'patch': {
        'name': 'Lemon cake',
        'notes': 'A bright lemon-scented butter or oil cake, often soaked or glazed with a tart lemon syrup or icing.',
    }},
    'corpus-titled-baked-spaghetti': {'action': 'edit', 'patch': {
        'name': 'Baked spaghetti',
        'notes': 'Cooked spaghetti layered with meat sauce and shredded mozzarella, then baked until the cheese browns and the edges crisp.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-bean-dip': {'action': 'edit', 'patch': {
        'name': 'Bean dip',
        'tags': ['snack'],
        'notes': 'Refried beans warmed with salsa and shredded cheese — sometimes layered with sour cream for chip-dipping.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-chocolate-zucchini-cake': {'action': 'edit', 'patch': {
        'name': 'Chocolate zucchini cake',
        'notes': 'A moist cocoa cake folded with grated zucchini for tenderness — often a Bundt or sheet cake with chocolate chips on top.',
        'cuisine': 'American',
    }},
    'corpus-titled-glazed-carrots': {'action': 'edit', 'patch': {
        'name': 'Glazed carrots',
        'notes': 'Sliced or baby carrots cooked in butter, brown sugar, and a splash of orange juice or stock until glossy.',
    }},
    'corpus-titled-mexican-chicken-casserole': {'action': 'edit', 'patch': {
        'name': 'Mexican chicken casserole',
        'notes': 'Shredded chicken layered with tortilla chips, salsa or enchilada sauce, cream-of-chicken soup, and shredded cheese, baked until bubbly.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-pineapple-cheese-ball': {'action': 'edit', 'patch': {
        'name': 'Pineapple cheese ball',
        'tags': ['snack'],
        'notes': 'Cream cheese mixed with crushed pineapple, bell pepper, and onion, shaped into a ball and rolled in chopped pecans — served with crackers.',
        'cuisine': 'Southern',
        'serving_grams': 60,
    }},
    'corpus-titled-split-pea-soup': {'action': 'edit', 'patch': {
        'name': 'Split pea soup',
        'notes': 'Dried split peas simmered with a ham hock or bone, carrots, onion, and celery until thick and creamy.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-pork-chops': {'action': 'edit', 'patch': {
        'name': 'Pork chops',
        'notes': 'Bone-in or boneless pork chops seasoned and pan-seared or baked — sometimes finished in a pan sauce.',
        'cuisine': 'American',
    }},
    'corpus-titled-nacho-dip': {'action': 'edit', 'patch': {
        'name': 'Nacho dip',
        'tags': ['snack'],
        'notes': 'Browned ground beef simmered with Velveeta and Rotel — a queso-style hot dip served with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-coleslaw': {'action': 'edit', 'patch': {
        'name': 'Coleslaw (variant)',
        'notes': 'Shredded cabbage and carrot dressed in a sweet-tangy mayo or vinegar-based dressing — the picnic-staple side.',
        'cuisine': 'American',
    }},
    'corpus-titled-rhubarb-pie': {'action': 'edit', 'patch': {
        'name': 'Rhubarb pie',
        'notes': 'A double-crust or lattice pie of chopped rhubarb tossed with sugar and a thickener — tart and bright.',
        'cuisine': 'American',
    }},
    'corpus-titled-custard-pie': {'action': 'edit', 'patch': {
        'name': 'Custard pie',
        'notes': 'A baked pastry shell filled with a sweet egg-milk-vanilla custard, dusted with nutmeg before baking.',
        'cuisine': 'American',
    }},
    'corpus-titled-dumplings': {'action': 'edit', 'patch': {
        'name': 'Dumplings',
        'notes': 'Soft drop-style dough of flour, milk, fat, and baking powder — dropped into simmering broth or stew to steam-cook.',
    }},
    'corpus-titled-7-up-cake': {'action': 'edit', 'patch': {
        'name': '7-Up cake',
        'ingredient_categories': ['Eggs', 'Citrus', 'Sugar & sweeteners', 'Flours', 'Oils', 'Cream & butter', 'Soft drinks'],
        'notes': 'A lemon-lime pound cake made with a bottle of 7-Up soda — moist and citrus-bright.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-tomato-soup': {'action': 'edit', 'patch': {
        'name': 'Tomato soup',
        'notes': 'Tomatoes simmered with onion, butter, and herbs, blended smooth and enriched with cream — often paired with grilled cheese.',
    }},
    'corpus-titled-oatmeal-pie': {'action': 'edit', 'patch': {
        'name': 'Oatmeal pie',
        'notes': 'A pecan-pie-style filling of eggs, sugar, butter, and oats — chewy and toasty in a single crust.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-apricot-salad': {'action': 'edit', 'patch': {
        'name': 'Apricot salad',
        'tags': ['dessert'],
        'notes': 'A molded gelatin salad of apricots and crushed pineapple set in orange Jello, often topped with a cream cheese layer.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-fried-chicken': {'action': 'edit', 'patch': {
        'name': 'Southern fried chicken',
        'notes': 'Chicken pieces brined or buttermilk-soaked, dredged in seasoned flour, and deep-fried until crisp.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-jam-cake': {'action': 'edit', 'patch': {
        'name': 'Jam cake',
        'notes': 'A spiced Appalachian layer cake folded with blackberry or raspberry jam, often frosted with caramel icing.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-banana-muffins': {'action': 'edit', 'patch': {
        'name': 'Banana muffins',
        'tags': ['breakfast', 'snack'],
        'notes': 'Tender muffins of mashed banana, butter, sugar, and flour — a single-portion form of banana bread.',
        'serving_grams': 60,
    }},
    'corpus-titled-rhubarb-cake': {'action': 'edit', 'patch': {
        'name': 'Rhubarb cake',
        'notes': 'A tender butter or oil cake folded with chopped rhubarb, often topped with a brown-sugar streusel.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-enchilada-casserole': {'action': 'edit', 'patch': {
        'name': 'Chicken enchilada casserole',
        'notes': 'A layered "stacked" enchilada bake of tortillas, shredded chicken, enchilada sauce, and cheese — assembled lasagna-style.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 320,
    }},
    'corpus-titled-cheeseburger-pie': {'action': 'edit', 'patch': {
        'name': 'Cheeseburger pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'Browned ground beef and onions baked under a Bisquick-and-egg crust with shredded cheese on top — a Bisquick-original "impossible" casserole.',
        'cuisine': 'American',
        'serving_grams': 320,
    }},
    'corpus-titled-meat-balls': {'action': 'edit', 'patch': {
        'name': 'Meatballs (variant)',
        'notes': 'A ground beef meatball variant — bound with breadcrumbs, egg, milk, and seasonings, then browned and simmered in sauce.',
    }},
    'corpus-titled-ground-beef-casserole': {'action': 'edit', 'patch': {
        'name': 'Ground beef casserole',
        'notes': 'Browned ground beef baked with potatoes or noodles, mushrooms, vegetables, and shredded cheese — a one-dish weeknight meal.',
        'cuisine': 'American',
    }},
    'corpus-titled-forgotten-cookies': {'action': 'edit', 'patch': {
        'name': 'Forgotten cookies',
        'notes': 'Beaten egg whites folded with sugar, mini chocolate chips, and chopped pecans — piped onto sheets and left in a turned-off oven overnight to dry.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-ambrosia': {'action': 'edit', 'patch': {
        'name': 'Ambrosia',
        'tags': ['dessert', 'snack'],
        'notes': 'A Southern fruit salad of mandarin oranges, pineapple, mini marshmallows, shredded coconut, and sour cream or whipped topping.',
        'cuisine': 'Southern',
        'serving_grams': 230,
    }},
    'corpus-titled-party-mix': {'action': 'edit', 'patch': {
        'name': 'Chex party mix',
        'tags': ['snack'],
        'notes': 'Chex cereals, pretzels, and mixed nuts coated in a buttery Worcestershire-and-seasoning blend, then baked or microwaved until crisp.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-vanilla-wafer-cake': {'action': 'edit', 'patch': {
        'name': 'Vanilla wafer cake',
        'notes': 'A butter-and-egg pound cake made with crushed vanilla wafers in place of flour, often folded with coconut and pecans.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-dirty-rice': {'action': 'edit', 'patch': {
        'name': 'Dirty rice',
        'notes': 'White rice cooked with finely chopped chicken livers, gizzards, and ground meat, plus the trinity of vegetables and Cajun seasoning.',
        'cuisine': 'Creole',
    }},
    'corpus-titled-hot-rolls': {'action': 'edit', 'patch': {
        'name': 'Hot rolls',
        'tags': ['dinner', 'lunch'],
        'notes': 'A soft enriched yeast dough proofed, shaped, and baked to be served warm with butter.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-eggplant-parmesan': {'action': 'edit', 'patch': {
        'name': 'Eggplant parmesan',
        'notes': 'Breaded eggplant slices fried, then baked in tomato sauce under layers of mozzarella and Parmesan — Italian-American comfort food.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-pumpkin-muffins': {'action': 'edit', 'patch': {
        'name': 'Pumpkin muffins',
        'tags': ['breakfast', 'snack'],
        'notes': 'Spiced muffins of pumpkin puree, eggs, oil, and warm spices — often topped with streusel or chopped nuts.',
        'serving_grams': 60,
    }},
    'corpus-titled-barbecue': {'action': 'edit', 'patch': {
        'name': 'Barbecue (pulled pork)',
        'notes': 'Pulled or chopped slow-cooked pork shoulder dressed with a vinegar-or-tomato-based barbecue sauce — served on a soft bun.',
        'cuisine': 'Southern',
        'contains_add': ['pork'],
    }},
    'corpus-titled-peanut-butter-candy': {'action': 'edit', 'patch': {
        'name': 'Peanut butter candy',
        'notes': 'A no-bake confection of peanut butter, sugar, butter, and milk cooked and beaten to a fudge — sometimes dipped in chocolate.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-green-rice': {'action': 'edit', 'patch': {
        'name': 'Green rice',
        'notes': 'Rice baked with chopped broccoli or spinach, onion, cream of mushroom soup, and Cheez Whiz — a Southern church-supper side.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-lemon-chess-pie': {'action': 'edit', 'patch': {
        'name': 'Lemon chess pie',
        'notes': 'A Southern chess pie brightened with lemon juice and zest — translucent and tangy in a flaky crust.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-rice-pilaf': {'action': 'edit', 'patch': {
        'name': 'Rice pilaf',
        'notes': 'Long-grain rice toasted in butter with vermicelli or onions, then simmered in seasoned chicken broth.',
    }},
    'corpus-titled-mexican-rice': {'action': 'edit', 'patch': {
        'name': 'Mexican rice',
        'notes': 'Long-grain rice toasted in oil, then simmered with tomato sauce, garlic, and chicken broth until tender and orange-tinted.',
        'cuisine': 'Mexican',
    }},
    'corpus-titled-raw-apple-cake': {'action': 'edit', 'patch': {
        'name': 'Raw apple cake',
        'notes': 'An oil-based spice cake folded with chopped raw apples and nuts — no need to precook the fruit.',
        'cuisine': 'American',
    }},
    'corpus-titled-cowboy-cookies': {'action': 'edit', 'patch': {
        'name': 'Cowboy cookies',
        'notes': 'Drop cookies of butter, brown sugar, oats, chocolate chips, and chopped pecans — a hearty oversized cookie.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-hot-artichoke-dip': {'action': 'edit', 'patch': {
        'name': 'Hot artichoke dip',
        'ingredient_categories': ['Other vegetables', 'Fresh cheese', 'Aged cheese', 'Fermented dairy', 'Extracts & essences', 'Peppers & nightshades'],
        'tags': ['snack'],
        'notes': 'Chopped artichoke hearts baked with cream cheese, mayo, sour cream, and Parmesan until bubbling — served hot with bread or crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-lime-jello-salad': {'action': 'edit', 'patch': {
        'name': 'Lime Jello salad',
        'tags': ['dessert'],
        'notes': 'Lime gelatin set with crushed pineapple, cottage cheese, whipped topping, and chopped pecans — a green Southern molded salad.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-magic-cookie-bars': {'action': 'edit', 'patch': {
        'name': 'Magic cookie bars',
        'notes': 'A graham crust topped with a glossy pour of sweetened condensed milk, then chocolate chips, coconut, and pecans — baked until set.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-veggie-pizza': {'action': 'edit', 'patch': {
        'name': 'Veggie pizza (cold)',
        'tags': ['snack'],
        'notes': 'A cold "pizza" of crescent-roll crust spread with herbed cream cheese and topped with chopped raw vegetables and shredded cheese.',
        'cuisine': 'American',
        'serving_grams': 100,
    }},
    'corpus-titled-three-bean-salad': {'action': 'edit', 'patch': {
        'name': 'Three bean salad (variant)',
        'notes': 'Green, kidney, and wax beans tossed with onion and peppers in a sweet-tart vinegar dressing — chilled overnight.',
        'cuisine': 'American',
    }},
    'corpus-titled-pineapple-pie': {'action': 'edit', 'patch': {
        'name': 'Pineapple pie',
        'notes': 'A pie of crushed pineapple set with eggs, sugar, and a touch of flour or lemon — sometimes topped with meringue.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-apple-salad': {'action': 'edit', 'patch': {
        'name': 'Apple salad',
        'notes': 'Diced apples tossed with pineapple, celery, and pecans in a sweet whipped-topping dressing — a Waldorf-style picnic salad.',
        'cuisine': 'American',
    }},
    'corpus-titled-mandarin-orange-salad': {'action': 'edit', 'patch': {
        'name': 'Mandarin orange salad',
        'tags': ['dessert', 'snack'],
        'notes': 'Mandarin oranges layered or molded with pineapple and orange gelatin — a chilled Southern fruit salad.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-noodles': {'action': 'edit', 'patch': {
        'name': 'Homemade egg noodles',
        'tags': ['dinner', 'lunch'],
        'notes': 'A simple dough of flour, egg, milk, and salt rolled thin, cut into ribbons, and boiled in broth — served as a side or in soup.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-sticky-buns': {'action': 'edit', 'patch': {
        'name': 'Sticky buns',
        'tags': ['breakfast', 'dessert'],
        'notes': 'Yeasted dough rolled with cinnamon-sugar, baked over a pan of brown-sugar-butter syrup with pecans, then inverted to serve.',
        'cuisine': 'American',
        'serving_grams': 90,
    }},
    'corpus-titled-chess-cake': {'action': 'edit', 'patch': {
        'name': 'Chess cake (ooey gooey butter cake)',
        'notes': 'A yellow cake mix base topped with a cream-cheese-egg-and-powdered-sugar layer that bakes into a gooey "butter cake" — a St. Louis-Southern dessert.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-peanut-butter-cups': {'action': 'edit', 'patch': {
        'name': 'Homemade peanut butter cups',
        'tags': ['dessert', 'snack'],
        'notes': 'A peanut butter, powdered sugar, and graham-cracker filling sandwiched between layers of melted chocolate in muffin cups.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-stromboli': {'action': 'edit', 'patch': {
        'name': 'Stromboli',
        'notes': 'Pizza dough rolled around layers of salami, ham, cheese, and peppers, sealed and baked into a sliced log.',
        'cuisine': 'Italian-American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-blonde-brownies': {'action': 'edit', 'patch': {
        'name': 'Blondies',
        'notes': 'Brown-sugar-and-butter bars in the shape of brownies but with vanilla in place of chocolate — sometimes with butterscotch or chocolate chips.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-white-chili': {'action': 'edit', 'patch': {
        'name': 'White chicken chili',
        'notes': 'Shredded chicken simmered with white beans, green chiles, cumin, and broth — finished with sour cream or cream cheese.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-spaghetti': {'action': 'edit', 'patch': {
        'name': 'Spaghetti with meat sauce',
        'notes': 'Cooked spaghetti tossed with a long-simmered ground-beef-and-tomato sauce — the American weeknight pasta.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-chocolate-chip-pie': {'action': 'edit', 'patch': {
        'name': 'Chocolate chip pie',
        'notes': 'A gooey pecan-pie-style filling of butter, sugar, eggs, and a touch of flour, packed with chocolate chips and walnuts — like a giant cookie in a pie shell.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-marsala': {'action': 'edit', 'patch': {
        'name': 'Chicken marsala',
        'notes': 'Pounded chicken cutlets dredged in flour, browned in butter, and finished in a Marsala-wine and mushroom pan sauce.',
        'cuisine': 'Italian-American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-german-chocolate-cake': {'action': 'edit', 'patch': {
        'name': 'German chocolate cake',
        'notes': 'A sweet-mild-chocolate layer cake filled and topped with a coconut-pecan caramel frosting — invented in Texas, named after German\'s baking chocolate.',
        'cuisine': 'American',
    }},
    'corpus-titled-heavenly-hash': {'action': 'edit', 'patch': {
        'name': 'Heavenly hash',
        'tags': ['dessert'],
        'notes': 'Crushed pineapple, mandarin oranges, mini marshmallows, and chopped pecans folded with whipped cream — a Southern dessert salad.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-stuffed-shells': {'action': 'edit', 'patch': {
        'name': 'Stuffed shells',
        'notes': 'Jumbo pasta shells filled with seasoned ricotta and spinach, nested in marinara, topped with mozzarella, and baked.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-southern-pecan-pie': {'action': 'edit', 'patch': {
        'name': 'Southern pecan pie',
        'notes': 'A custard of eggs, sugar, butter, and corn syrup or molasses studded with pecan halves, baked in a flaky crust until set.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-7-layer-salad': {'action': 'edit', 'patch': {
        'name': 'Seven layer salad (variant)',
        'notes': 'Lettuce, frozen peas, red onion, eggs, bacon, and cheese layered in a glass bowl, sealed under a mayo-and-sugar topping — chilled overnight.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-banana-split-pie': {'action': 'edit', 'patch': {
        'name': 'Banana split pie',
        'notes': 'A graham crust filled with sweet whipped cream cheese, sliced bananas, crushed pineapple, and whipped topping — banana-split flavors in pie form.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-fajitas': {'action': 'edit', 'patch': {
        'name': 'Chicken fajitas',
        'notes': 'Marinated chicken strips seared with bell peppers and onions, served sizzling with warm tortillas and toppings.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-kahlua': {'action': 'edit', 'patch': {
        'name': 'Homemade Kahlúa',
        'ingredient_categories': ['Sugar & sweeteners', 'Coffee & tea', 'Alcoholic beverages', 'Extracts & essences'],
        'tags': ['snack'],
        'notes': 'A homemade coffee liqueur of strong brewed coffee, sugar, vanilla, and vodka — aged in a jar for a few weeks.',
        'contains_add': ['alcohol'],
        'serving_grams': 45,
    }},
    'corpus-titled-mexican-salad': {'action': 'edit', 'patch': {
        'name': 'Mexican salad',
        'notes': 'Lettuce tossed with seasoned ground beef, beans, cheese, tomatoes, and crushed tortilla chips with a creamy salsa dressing.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-cabbage-soup': {'action': 'edit', 'patch': {
        'name': 'Cabbage soup',
        'notes': 'Shredded cabbage simmered with ground beef, tomatoes, and other vegetables in a savory broth — sometimes the diet "cabbage soup".',
    }},
    'corpus-titled-marinated-mushrooms': {'action': 'edit', 'patch': {
        'name': 'Marinated mushrooms',
        'tags': ['snack'],
        'notes': 'Whole button mushrooms tossed in a herb-and-vinegar marinade with oil, lemon, and seasonings — chilled as an appetizer.',
        'serving_grams': 80,
    }},
    'corpus-titled-buttermilk-pancakes': {'action': 'edit', 'patch': {
        'name': 'Buttermilk pancakes',
        'notes': 'A baking-soda-leavened buttermilk batter cooked in butter on a griddle — fluffy and tangy.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-mixed-vegetable-casserole': {'action': 'edit', 'patch': {
        'name': 'Mixed vegetable casserole',
        'notes': 'A medley of mixed vegetables (often canned Veg-All) baked with mayo, onion, and shredded cheese under a buttered cracker top.',
        'cuisine': 'American',
    }},
    'corpus-titled-lemon-pound-cake': {'action': 'edit', 'patch': {
        'name': 'Lemon pound cake',
        'notes': 'A dense pound cake brightened with lemon zest and juice, drizzled with a lemon-sugar glaze while still warm.',
    }},
    'corpus-titled-banana-cream-pie': {'action': 'edit', 'patch': {
        'name': 'Banana cream pie',
        'notes': 'A baked crust filled with vanilla pastry cream and sliced bananas, topped with whipped cream — chilled before serving.',
        'cuisine': 'American',
    }},
    'corpus-titled-bean-soup': {'action': 'edit', 'patch': {
        'name': 'Bean soup',
        'notes': 'Dried beans simmered slowly with a ham hock or smoked meat, onion, celery, and broth until thick and rich.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-corned-beef-casserole': {'action': 'edit', 'patch': {
        'name': 'Corned beef casserole',
        'notes': 'Canned corned beef baked with egg noodles, cream of chicken or mushroom soup, peas, and Swiss cheese.',
        'cuisine': 'American',
    }},
    'corpus-titled-stuffed-bell-peppers': {'action': 'edit', 'patch': {
        'name': 'Stuffed bell peppers (variant)',
        'notes': 'Bell peppers hollowed and filled with seasoned ground beef, rice, onion, and tomato sauce, baked until tender.',
    }},
    'corpus-titled-turkey-chili': {'action': 'edit', 'patch': {
        'name': 'Turkey chili',
        'notes': 'Ground turkey simmered with beans, tomatoes, peppers, and chili spices — a lighter take on classic chili.',
        'cuisine': 'American',
    }},
    'corpus-titled-baked-apples': {'action': 'edit', 'patch': {
        'name': 'Baked apples',
        'tags': ['dessert'],
        'notes': 'Whole cored apples stuffed with brown sugar, butter, raisins, and cinnamon, baked until tender — served warm with cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-cheese-potatoes': {'action': 'edit', 'patch': {
        'name': 'Cheesy potatoes (variant)',
        'notes': 'Sliced or shredded potatoes baked with sour cream, shredded cheddar, and butter — the "funeral potatoes" comfort side.',
        'cuisine': 'American',
    }},
    'corpus-titled-orange-slice-cake': {'action': 'edit', 'patch': {
        'name': 'Orange slice cake',
        'notes': 'A dense buttermilk Bundt cake folded with chopped orange-slice candies, dates, coconut, and pecans, soaked with orange juice and sugar after baking.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-egg-custard-pie': {'action': 'edit', 'patch': {
        'name': 'Egg custard pie',
        'notes': 'A baked pastry shell filled with a milk-egg-sugar custard, dusted with nutmeg — served chilled or barely warm.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-pineapple-salad': {'action': 'edit', 'patch': {
        'name': 'Pineapple salad',
        'tags': ['dessert', 'snack'],
        'notes': 'Crushed pineapple set with whipped topping, cream cheese, mini marshmallows, and pecans — a sweet Southern molded salad.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-oatmeal-raisin-cookies': {'action': 'edit', 'patch': {
        'name': 'Oatmeal raisin cookies',
        'notes': 'Drop cookies of butter, brown sugar, oats, raisins, and warm spices — chewy and homey.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-banana-split-dessert': {'action': 'edit', 'patch': {
        'name': 'Banana split dessert',
        'notes': 'A no-bake layered dessert of graham crust, whipped butter-sugar-egg cream, sliced bananas, crushed pineapple, whipped topping, nuts, and cherries.',
        'cuisine': 'American',
    }},
    'corpus-titled-marinated-vegetables': {'action': 'edit', 'patch': {
        'name': 'Marinated vegetables',
        'notes': 'Mixed cooked or raw vegetables tossed in an oil-and-vinegar marinade with sugar and herbs — chilled overnight as a make-ahead salad.',
    }},
    'corpus-titled-baked-potato-soup': {'action': 'edit', 'patch': {
        'name': 'Baked potato soup',
        'notes': 'A creamy potato soup garnished like a loaded baked potato — sour cream, cheddar, bacon, and chives.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-new-england-clam-chowder': {'action': 'edit', 'patch': {
        'name': 'New England clam chowder (variant)',
        'notes': 'Diced potatoes, salt pork or bacon, onions, and clams simmered in milk and cream — thick, creamy, and white.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-chili-sauce': {'action': 'drop', 'reason': 'cooked condiment / canning preserve, not a coherent meal'},
    'corpus-titled-chocolate-pecan-pie': {'action': 'edit', 'patch': {
        'name': 'Chocolate pecan pie',
        'notes': 'A classic pecan-pie custard with melted chocolate or chocolate chips stirred in — fudgy beneath the toasted pecans.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-baked-ziti': {'action': 'edit', 'patch': {
        'name': 'Baked ziti',
        'notes': 'Ziti tossed with marinara and ricotta, layered with mozzarella, and baked until the top blisters — Italian-American comfort food.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-congealed-salad': {'action': 'edit', 'patch': {
        'name': 'Congealed salad',
        'tags': ['dessert'],
        'notes': 'A molded gelatin salad of canned fruit, cream cheese, nuts, and whipped topping — a Southern potluck staple.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-barbecue-chicken': {'action': 'edit', 'patch': {
        'name': 'Barbecue chicken',
        'notes': 'Bone-in chicken pieces grilled or baked and basted with a sweet-tangy barbecue sauce.',
        'cuisine': 'American',
    }},
    'corpus-titled-french-coconut-pie': {'action': 'edit', 'patch': {
        'name': 'French coconut pie',
        'notes': 'A custard of eggs, sugar, butter, vinegar, and vanilla folded with shredded coconut, baked into a single crust until golden.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-haystacks': {'action': 'edit', 'patch': {
        'name': 'Haystacks',
        'tags': ['dessert', 'snack'],
        'notes': 'Melted butterscotch or chocolate stirred with chow mein noodles and peanuts, dropped onto wax paper to set into clustered "haystacks".',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-vegetable-beef-soup': {'action': 'edit', 'patch': {
        'name': 'Vegetable beef soup',
        'notes': 'Cubed or ground beef simmered with mixed vegetables, tomatoes, and herbs in beef broth — a stockpot weeknight soup.',
    }},
    'corpus-titled-coconut-macaroons': {'action': 'edit', 'patch': {
        'name': 'Coconut macaroons',
        'notes': 'Shredded coconut bound with egg whites and sweetened condensed milk, mounded onto sheets and baked until golden on top.',
        'serving_grams': 30,
    }},
    'corpus-titled-german-chocolate-upside-down-cake': {'action': 'edit', 'patch': {
        'name': 'German chocolate upside-down cake',
        'notes': 'A coconut-pecan layer on the bottom, batter on top, and a cream-cheese-and-powdered-sugar layer that swirls down through the cake — earthquake-cake style.',
        'cuisine': 'American',
    }},
    'corpus-titled-cottage-cheese-salad': {'action': 'edit', 'patch': {
        'name': 'Cottage cheese salad',
        'tags': ['snack'],
        'notes': 'Cottage cheese folded with crushed pineapple and mandarin oranges or other fruit — a high-protein chilled side.',
        'serving_grams': 170,
    }},
    'corpus-titled-spoon-bread': {'action': 'edit', 'patch': {
        'name': 'Spoon bread',
        'notes': 'A souffle-style cornmeal-milk-and-egg pudding baked until just set — soft enough to scoop with a spoon.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-spaghetti-casserole': {'action': 'edit', 'patch': {
        'name': 'Spaghetti casserole',
        'notes': 'Cooked spaghetti tossed with ground beef, mushrooms, and tomato sauce, then baked under shredded cheese.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-chicken-wings': {'action': 'edit', 'patch': {
        'name': 'Chicken wings',
        'tags': ['snack', 'dinner'],
        'notes': 'Whole or split chicken wings baked or fried, then tossed in a sauce (Buffalo, honey-garlic, barbecue) — game-day finger food.',
        'cuisine': 'American',
        'serving_grams': 170,
    }},
    'corpus-titled-cabbage-salad': {'action': 'edit', 'patch': {
        'name': 'Cabbage salad',
        'notes': 'Shredded cabbage tossed with a sweet vinaigrette and sometimes ramen noodles or almonds — a crunchy slaw variant.',
    }},
    'corpus-titled-mayonnaise-cake': {'action': 'edit', 'patch': {
        'name': 'Mayonnaise cake',
        'notes': 'A Depression-era chocolate cake using mayonnaise in place of butter and eggs — the mayo carries the fat and emulsion.',
        'cuisine': 'American',
    }},
    'corpus-titled-popovers': {'action': 'edit', 'patch': {
        'name': 'Popovers',
        'notes': 'A thin egg-milk-flour batter baked at high heat in hot buttered tins until they balloon into hollow rolls — close cousin of Yorkshire pudding.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-banana-nut-cake': {'action': 'edit', 'patch': {
        'name': 'Banana nut cake',
        'notes': 'A banana butter cake with chopped walnuts or pecans folded in, often frosted with cream cheese icing.',
        'cuisine': 'American',
    }},
    'corpus-titled-salmon-croquettes': {'action': 'edit', 'patch': {
        'name': 'Salmon croquettes',
        'notes': 'Canned salmon mixed with egg, onion, and crackers or breadcrumbs, formed into patties and pan-fried until golden.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-better-than-sex-cake': {'action': 'edit', 'patch': {
        'name': 'Better-than-sex cake',
        'notes': 'A chocolate cake poked and drenched with sweetened condensed milk and caramel, topped with whipped topping and crushed toffee bits.',
        'cuisine': 'American',
    }},
    'corpus-titled-lemon-lush': {'action': 'edit', 'patch': {
        'name': 'Lemon lush',
        'tags': ['dessert'],
        'notes': 'A no-bake layered dessert of pecan-shortbread crust, sweetened cream cheese, lemon pudding, and whipped topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-zucchini-cake': {'action': 'edit', 'patch': {
        'name': 'Zucchini cake',
        'notes': 'An oil-based spice cake folded with grated zucchini, often frosted with cream cheese icing — a non-chocolate sibling of carrot cake.',
        'cuisine': 'American',
    }},
    'corpus-titled-strawberry-dessert': {'action': 'edit', 'patch': {
        'name': 'Strawberry dessert',
        'notes': 'Strawberry-and-pretzel or strawberry-and-cake-mix layered dessert with whipped cream — generic name for several Southern strawberry pan desserts.',
        'cuisine': 'American',
    }},
    'corpus-titled-porcupine-meatballs': {'action': 'edit', 'patch': {
        'name': 'Porcupine meatballs',
        'notes': 'Ground beef and uncooked rice meatballs simmered in tomato sauce — the rice grains poke out as they cook, giving the "porcupine" look.',
        'cuisine': 'American',
    }},
    'corpus-titled-cranberry-bread': {'action': 'edit', 'patch': {
        'name': 'Cranberry bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A holiday quick bread of fresh or dried cranberries, orange zest, and walnuts in a tender batter.',
        'cuisine': 'American',
    }},
    'corpus-titled-manicotti': {'action': 'edit', 'patch': {
        'name': 'Manicotti',
        'notes': 'Pasta tubes filled with a ricotta-Parmesan-egg mixture, nested in marinara with mozzarella, and baked until bubbling.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-cake-mix-cookies': {'action': 'edit', 'patch': {
        'name': 'Cake mix cookies',
        'notes': 'A box of cake mix combined with eggs and oil to make a quick drop cookie — flavored with chocolate chips, sprinkles, or extracts.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-kraut-salad': {'action': 'edit', 'patch': {
        'name': 'Sauerkraut salad',
        'notes': 'Drained sauerkraut tossed with chopped onion, bell pepper, and a sweet vinegar-and-oil dressing — chilled until tangy-sweet.',
        'cuisine': 'German-American',
    }},
    'corpus-titled-beef-burgundy': {'action': 'edit', 'patch': {
        'name': 'Beef burgundy',
        'notes': 'Cubed beef braised slowly in Burgundy wine with mushrooms, onions, and herbs — the American-home version of boeuf bourguignon.',
        'cuisine': 'French',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-pina-colada-cake': {'action': 'edit', 'patch': {
        'name': 'Piña colada cake',
        'notes': 'A yellow cake poked and soaked with sweetened condensed milk and cream of coconut, topped with whipped topping and pineapple.',
        'cuisine': 'American',
    }},
    'corpus-titled-baked-pork-chops': {'action': 'edit', 'patch': {
        'name': 'Baked pork chops',
        'notes': 'Seasoned pork chops baked over rice, potatoes, or stuffing — sometimes covered in cream-of-mushroom soup or barbecue sauce.',
        'cuisine': 'American',
    }},
    'corpus-titled-clam-dip': {'action': 'edit', 'patch': {
        'name': 'Clam dip',
        'tags': ['snack'],
        'notes': 'Cream cheese and sour cream whipped with minced clams, lemon, and Worcestershire — served chilled with chips or crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-vegetarian-chili': {'action': 'edit', 'patch': {
        'name': 'Vegetarian chili',
        'notes': 'A bean-and-vegetable chili of kidney, black, or pinto beans simmered with tomatoes, peppers, onions, and chili spices.',
        'cuisine': 'American',
    }},
    'corpus-titled-buttermilk-pound-cake': {'action': 'edit', 'patch': {
        'name': 'Buttermilk pound cake',
        'notes': 'A dense, fine-crumb pound cake made tangy by buttermilk and lifted slightly by a touch of baking soda.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-sweet-potato-biscuits': {'action': 'edit', 'patch': {
        'name': 'Sweet potato biscuits',
        'tags': ['breakfast', 'dinner'],
        'notes': 'A biscuit dough enriched with mashed sweet potato — slightly sweet, orange-tinted, with a tender crumb.',
        'cuisine': 'Southern',
        'serving_grams': 55,
    }},
    'corpus-titled-nachos': {'action': 'edit', 'patch': {
        'name': 'Nachos',
        'tags': ['snack', 'dinner'],
        'notes': 'Tortilla chips piled with seasoned ground beef, beans, melted cheese, jalapeños, salsa, sour cream, and guacamole.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 260,
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

    print('corpus-titled batch-3 audit applied (entries 301-450 by frequency).')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
