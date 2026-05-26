"""Corpus-titled meals audit — batch 8 (entries 1051-1200 by frequency, 107 -> 96).
Same standard.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

DECISIONS: dict[str, dict] = {
    'corpus-titled-cherry-dump-cake': {'action': 'edit', 'patch': {
        'name': 'Cherry dump cake',
        'notes': 'Canned cherry and pineapple pie filling topped with a yellow cake mix, pats of butter, and chopped pecans — baked until streuseled on top.',
        'cuisine': 'American',
    }},
    'corpus-titled-english-pea-casserole': {'action': 'edit', 'patch': {
        'name': 'English pea casserole',
        'notes': 'Sweet green peas baked with mushrooms, hard-boiled egg, cream of mushroom soup, and cheese under a buttered cracker crust.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-chocolate-fudge-cake': {'action': 'edit', 'patch': {
        'name': 'Chocolate fudge cake',
        'notes': 'A dense, moist cocoa cake leaning toward brownie-like richness, frosted with chocolate fudge or ganache.',
        'cuisine': 'American',
    }},
    'corpus-titled-cornbread-casserole': {'action': 'edit', 'patch': {
        'name': 'Cornbread casserole',
        'notes': 'Cornbread batter mixed with corn kernels, creamed corn, sour cream, and cheese, sometimes layered with ground beef — baked spoon-bread style.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-white-fudge': {'action': 'edit', 'patch': {
        'name': 'White fudge',
        'notes': 'A vanilla fudge of sugar, sour cream or evaporated milk, and butter cooked to soft-ball and beaten with nuts — chocolate-free.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-mexican-meat-loaf': {'action': 'edit', 'patch': {
        'name': 'Mexican meatloaf',
        'notes': 'A ground-beef loaf with crushed tortilla chips, salsa, peppers, and chili spices in place of breadcrumbs, topped with cheese.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-noodle-pudding': {'action': 'edit', 'patch': {
        'name': 'Noodle kugel',
        'tags': ['dessert', 'dinner'],
        'notes': 'Egg noodles baked in a sweet custard of cottage cheese, sour cream, eggs, butter, sugar, and raisins — the Ashkenazi Jewish noodle pudding.',
        'cuisine': 'Jewish',
    }},
    'corpus-titled-old-fashioned-tea-cakes': {'action': 'edit', 'patch': {
        'name': 'Old-fashioned tea cakes',
        'notes': 'A simple Southern butter-sugar-flour cookie scented with vanilla and nutmeg — soft and slightly cakey, served with tea.',
        'cuisine': 'Southern',
        'serving_grams': 60,
    }},
    'corpus-titled-fresh-coconut-cake': {'action': 'edit', 'patch': {
        'name': 'Fresh coconut cake',
        'notes': 'A white layer cake brushed with coconut milk or fresh coconut water and finished with seven-minute frosting and freshly grated coconut.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-peanut-butter-blossoms': {'action': 'edit', 'patch': {
        'name': 'Peanut butter blossoms (variant)',
        'tags': ['dessert'],
        'notes': 'Peanut butter cookies rolled in sugar and pressed with a Hershey\'s Kiss as soon as they come out of the oven.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-beef-roast': {'action': 'edit', 'patch': {
        'name': 'Beef roast',
        'notes': 'A larger cut of beef (chuck, rump, or round) seared and then slow-roasted or braised with vegetables and broth until fork-tender.',
        'cuisine': 'American',
    }},
    'corpus-titled-cherry-squares': {'action': 'edit', 'patch': {
        'name': 'Cherry squares',
        'tags': ['dessert'],
        'notes': 'A butter cake or shortbread base topped with cherry pie filling and a crumb topping, baked into bars.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-chicken-dressing': {'action': 'edit', 'patch': {
        'name': 'Chicken and dressing (Southern)',
        'notes': 'Shredded chicken folded into cornbread dressing with broth, sage, and onions, baked into a casserole — Southern Thanksgiving leftovers.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-hershey-bar-pie': {'action': 'edit', 'patch': {
        'name': 'Hershey bar pie',
        'notes': 'Melted Hershey almond bars folded into whipped cream, poured into a graham crust, and chilled until set.',
        'cuisine': 'American',
    }},
    'corpus-titled-mexican-fruit-cake': {'action': 'edit', 'patch': {
        'name': 'Mexican fruit cake',
        'notes': 'A one-bowl batter of crushed pineapple, sugar, eggs, flour, and pecans baked into a sheet cake — topped with cream cheese frosting; American despite the name.',
        'cuisine': 'American',
    }},
    'corpus-titled-mints': {'action': 'edit', 'patch': {
        'name': 'Cream cheese mints',
        'tags': ['dessert', 'snack'],
        'notes': 'Cream cheese kneaded with powdered sugar and peppermint extract, pressed into molds or rolled into balls and dusted with sugar — wedding-table candies.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-pear-salad': {'action': 'edit', 'patch': {
        'name': 'Pear salad',
        'notes': 'Canned pear halves on a lettuce leaf topped with a dollop of mayo and grated cheese — a retro Southern plate.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-chicken-paprika': {'action': 'edit', 'patch': {
        'name': 'Chicken paprika',
        'notes': 'Chicken pieces browned and simmered in a sour-cream-and-paprika sauce — served over egg noodles; close cousin of chicken paprikash.',
        'cuisine': 'Hungarian',
    }},
    'corpus-titled-black-bean-dip': {'action': 'edit', 'patch': {
        'name': 'Black bean dip',
        'tags': ['snack'],
        'notes': 'Black beans pureed with cumin, garlic, salsa, and lime — served warm or chilled with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-quesadillas': {'action': 'edit', 'patch': {
        'name': 'Quesadillas',
        'notes': 'Flour tortillas folded around melted cheese (often with peppers, chicken, or beef), griddled until golden — served with salsa and sour cream.',
        'cuisine': 'Mexican',
    }},
    'corpus-titled-hoppin-john': {'action': 'edit', 'patch': {
        'name': "Hoppin' John",
        'notes': 'Black-eyed peas simmered with rice, smoked pork (ham hock or bacon), onion, and peppers — a Carolina-Lowcountry New Year\'s dish.',
        'cuisine': 'Southern',
        'contains_add': ['pork'],
    }},
    'corpus-titled-nuts-and-bolts': {'action': 'edit', 'patch': {
        'name': 'Nuts and bolts (Chex mix)',
        'tags': ['snack'],
        'notes': 'Chex cereals, pretzels, and mixed nuts coated in a buttery Worcestershire-and-seasoning blend, then baked until crisp — same as Chex party mix.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-corn-bread-dressing': {'action': 'edit', 'patch': {
        'name': 'Cornbread dressing (variant)',
        'notes': 'Crumbled cornbread mixed with sautéed onions, celery, sage, broth, and eggs, baked into the Southern Thanksgiving "dressing".',
        'cuisine': 'Southern',
    }},
    'corpus-titled-apple-crumble': {'action': 'edit', 'patch': {
        'name': 'Apple crumble',
        'notes': 'Spiced sliced apples baked under a buttery flour-and-sugar crumb topping — the British cousin of apple crisp (no oats).',
        'cuisine': 'British',
    }},
    'corpus-titled-macaroons': {'action': 'edit', 'patch': {
        'name': 'Coconut macaroons',
        'notes': 'Shredded coconut bound with egg whites and sweetened condensed milk, mounded onto sheets and baked until golden.',
        'serving_grams': 30,
    }},
    'corpus-titled-hot-apple-cider': {'action': 'edit', 'patch': {
        'name': 'Hot apple cider',
        'ingredient_categories': ['Juices', 'Whole spices', 'Ground spices', 'Citrus', 'Sugar & sweeteners'],
        'tags': ['snack'],
        'notes': 'Apple cider simmered with cinnamon sticks, cloves, orange, and lemon — a non-alcoholic warming holiday drink.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-antipasto-salad': {'action': 'edit', 'patch': {
        'name': 'Antipasto salad',
        'notes': 'Romaine tossed with salami, pepperoni, mozzarella or provolone, marinated artichokes, olives, peperoncini, and an Italian-style vinaigrette.',
        'cuisine': 'Italian-American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-chicken-tacos': {'action': 'edit', 'patch': {
        'name': 'Chicken tacos',
        'notes': 'Shredded or diced seasoned chicken folded into soft or crispy tortillas, topped with lettuce, cheese, salsa, and lime crema.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-chicken-breasts': {'action': 'edit', 'patch': {
        'name': 'Chicken breasts',
        'notes': 'Boneless chicken breasts baked or sautéed with mushrooms and sour cream — a generic weeknight chicken preparation.',
        'cuisine': 'American',
    }},
    'corpus-titled-pudding-cake': {'action': 'edit', 'patch': {
        'name': 'Pudding poke cake',
        'notes': 'A baked cake poked with holes and soaked with a pudding-and-condensed-milk mixture, topped with whipped topping and crumbled candy.',
        'cuisine': 'American',
    }},
    'corpus-titled-rice-and-broccoli-casserole': {'action': 'edit', 'patch': {
        'name': 'Rice and broccoli casserole',
        'notes': 'Cooked rice baked with broccoli, cream of mushroom soup, and Cheez Whiz or shredded cheese — sometimes with chicken stirred in.',
        'cuisine': 'American',
    }},
    'corpus-titled-fudgy-brownies': {'action': 'edit', 'patch': {
        'name': 'Fudgy brownies',
        'notes': 'Dense, gooey brownies leaning toward truffle texture — high in butter and chocolate, low in flour, baked just until the center sets.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-carrot-soup': {'action': 'edit', 'patch': {
        'name': 'Carrot soup',
        'notes': 'Carrots simmered with onion, ginger, and broth, blended smooth and finished with cream — bright orange and silky.',
    }},
    'corpus-titled-cheesy-potato-soup': {'action': 'edit', 'patch': {
        'name': 'Cheesy potato soup',
        'notes': 'Diced potatoes simmered with onion and chicken broth, blended (or partially mashed), and finished with milk, butter, and shredded cheese.',
        'cuisine': 'American',
    }},
    'corpus-titled-shepherds-pie': {'action': 'edit', 'patch': {
        'name': 'Shepherd\'s pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'Ground lamb (or beef, then "cottage pie") simmered with onions, carrots, peas, and gravy, topped with mashed potatoes, and baked.',
        'cuisine': 'British',
        'serving_grams': 320,
    }},
    'corpus-titled-smothered-pork-chops': {'action': 'edit', 'patch': {
        'name': 'Smothered pork chops',
        'notes': 'Pork chops dredged in flour, browned, then braised in onion-and-mushroom gravy until tender — a Southern comfort dish.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-hot-wings': {'action': 'edit', 'patch': {
        'name': 'Hot wings (Buffalo)',
        'tags': ['snack', 'dinner'],
        'notes': 'Deep-fried chicken wings tossed in Frank\'s RedHot and butter — Buffalo, NY style; served with celery and blue cheese.',
        'cuisine': 'American',
        'serving_grams': 170,
    }},
    'corpus-titled-caramel-rolls': {'action': 'edit', 'patch': {
        'name': 'Caramel rolls',
        'tags': ['breakfast', 'dessert'],
        'notes': 'Yeasted dough rolled around cinnamon-sugar and baked over brown-sugar-butter-cream syrup with pecans, then inverted to serve sticky-side-up.',
        'cuisine': 'American',
        'serving_grams': 90,
    }},
    'corpus-titled-chewy-oatmeal-cookies': {'action': 'edit', 'patch': {
        'name': 'Chewy oatmeal cookies',
        'notes': 'Drop cookies of oats, butter, brown sugar, and warm spices baked at lower heat — chewy rather than crisp, often with raisins.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-mississippi-mud-pie': {'action': 'edit', 'patch': {
        'name': 'Mississippi mud pie',
        'notes': 'A chocolate-cookie crust filled with a fudgy chocolate-pudding-and-cream-cheese layer, topped with whipped cream and chocolate shavings.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-hermits': {'action': 'edit', 'patch': {
        'name': 'Hermits',
        'tags': ['dessert'],
        'notes': 'A New England spiced bar cookie with molasses, raisins, walnuts, and warm spices — kept in a tin to mellow.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-mexican-bean-dip': {'action': 'edit', 'patch': {
        'name': 'Mexican bean dip',
        'tags': ['snack'],
        'notes': 'Refried beans warmed with shredded cheese, salsa, sour cream, and taco seasoning — served with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-wild-rice-soup': {'action': 'edit', 'patch': {
        'name': 'Wild rice soup',
        'notes': 'Wild and long-grain rice simmered with mushrooms, onions, carrots, and chicken (or bacon) in a creamy broth — a Minnesota favorite.',
        'cuisine': 'American',
    }},
    'corpus-titled-cheese-pie': {'action': 'edit', 'patch': {
        'name': 'Cheese pie',
        'notes': 'A sweet pie of cream cheese, eggs, sugar, and vanilla baked in a graham crust — essentially a slimmer cheesecake.',
        'cuisine': 'American',
    }},
    'corpus-titled-zucchini-nut-bread': {'action': 'edit', 'patch': {
        'name': 'Zucchini nut bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A spiced quick bread folded with grated zucchini and chopped walnuts or pecans — moist with a tender crumb.',
        'cuisine': 'American',
    }},
    'corpus-titled-venison-stew': {'action': 'edit', 'patch': {
        'name': 'Venison stew',
        'notes': 'Cubed venison browned and slow-braised with potatoes, carrots, onions, and herbs in broth until tender — a hunting-camp classic.',
        'cuisine': 'American',
    }},
    'corpus-titled-chili-rellenos-casserole': {'action': 'edit', 'patch': {
        'name': 'Chiles rellenos casserole',
        'notes': 'Whole green chiles split open and layered with cheese, then poured over with an egg-and-milk batter and baked — a deconstructed chile relleno.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-lemon-jello-cake': {'action': 'edit', 'patch': {
        'name': 'Lemon Jello cake',
        'notes': 'A yellow cake baked from a mix combined with lemon Jello, eggs, and oil — poked and saturated after baking with a lemon-sugar glaze.',
        'cuisine': 'American',
    }},
    'corpus-titled-seafood-chowder': {'action': 'edit', 'patch': {
        'name': 'Seafood chowder',
        'notes': 'A creamy New England chowder of shrimp, crab, scallops, and white fish simmered with potatoes, onion, and milk-or-cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-pear-honey': {'action': 'drop', 'reason': 'fruit preserve (canning recipe), not a coherent meal'},
    'corpus-titled-upside-down-german-chocolate-cake': {'action': 'edit', 'patch': {
        'name': 'Upside-down German chocolate cake',
        'notes': 'Coconut and pecans layered on the bottom of a pan, then chocolate cake batter and a cream-cheese-powdered-sugar layer that swirls down — earthquake-cake style.',
        'cuisine': 'American',
    }},
    'corpus-titled-black-forest-cake': {'action': 'edit', 'patch': {
        'name': 'Black Forest cake',
        'notes': 'Chocolate sponge layered with sweet cherries, kirsch syrup, and whipped cream, topped with chocolate shavings — Schwarzwälder Kirschtorte.',
        'cuisine': 'German',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-chicken-quesadillas': {'action': 'edit', 'patch': {
        'name': 'Chicken quesadillas',
        'notes': 'Flour tortillas folded around shredded chicken, peppers, onions, and melted cheese — griddled until golden, served with salsa and sour cream.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-icebox-cake': {'action': 'edit', 'patch': {
        'name': 'Icebox cake',
        'notes': 'Chocolate wafers or graham crackers layered with whipped cream in a loaf pan, chilled overnight until the cookies soften into cake — Famous Wafers original.',
        'cuisine': 'American',
    }},
    'corpus-titled-zucchini-appetizers': {'action': 'edit', 'patch': {
        'name': 'Zucchini appetizers',
        'tags': ['snack'],
        'notes': 'Grated zucchini baked with eggs, flour, Parmesan, and herbs in a sheet pan, then cut into bite-size squares for appetizers.',
        'cuisine': 'Italian-American',
        'serving_grams': 60,
    }},
    'corpus-titled-barbecued-meatballs': {'action': 'edit', 'patch': {
        'name': 'Barbecued meatballs (variant)',
        'tags': ['snack', 'dinner'],
        'notes': 'Oven-baked beef meatballs simmered in barbecue sauce or a grape-jelly-and-chili-sauce glaze — held warm in a slow cooker.',
        'cuisine': 'American',
        'serving_grams': 100,
    }},
    'corpus-titled-fresh-salsa': {'action': 'edit', 'patch': {
        'name': 'Fresh salsa',
        'tags': ['snack', 'condiment'],
        'notes': 'Diced tomato, onion, jalapeño, cilantro, lime, and salt — a fresh chunky salsa for chips and tacos.',
        'cuisine': 'Mexican',
        'serving_grams': 60,
    }},
    'corpus-titled-black-bean-salsa': {'action': 'edit', 'patch': {
        'name': 'Black bean salsa',
        'tags': ['snack', 'condiment'],
        'notes': 'Black beans tossed with corn, diced tomato, peppers, red onion, cilantro, lime, and cumin — a chunky bean-corn salsa.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-apple-pie-filling': {'action': 'drop', 'reason': 'filling component / canning preserve, not a coherent meal'},
    'corpus-titled-turkey-meatloaf': {'action': 'edit', 'patch': {
        'name': 'Turkey meatloaf',
        'notes': 'Ground turkey bound with breadcrumbs, eggs, and seasonings, baked in a loaf with a ketchup glaze — a leaner meatloaf alternative.',
        'cuisine': 'American',
    }},
    'corpus-titled-baked-bean-casserole': {'action': 'edit', 'patch': {
        'name': 'Baked bean casserole (calico)',
        'notes': 'Canned beans baked with ground beef, bacon, brown sugar, and barbecue sauce — same as calico beans / cowboy beans.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-red-cabbage': {'action': 'edit', 'patch': {
        'name': 'Braised red cabbage',
        'notes': 'Shredded red cabbage slow-braised with apples, onions, vinegar, sugar, and warm spices — a German Rotkohl side.',
        'cuisine': 'German',
    }},
    'corpus-titled-mexican-cheese-dip': {'action': 'edit', 'patch': {
        'name': 'Mexican cheese dip (queso)',
        'tags': ['snack'],
        'notes': 'Velveeta-style processed cheese melted with Rotel tomatoes and chiles — served warm with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-baked-ham': {'action': 'edit', 'patch': {
        'name': 'Baked ham',
        'notes': 'A whole or half ham scored, studded with cloves, glazed with brown sugar, pineapple juice, and mustard, then baked until caramelized.',
        'cuisine': 'American',
    }},
    'corpus-titled-refrigerator-bran-muffins': {'action': 'edit', 'patch': {
        'name': 'Refrigerator bran muffins',
        'tags': ['breakfast'],
        'notes': 'A bran-and-buttermilk muffin batter mixed once and stored in the fridge — baked off in small batches as needed for fresh morning muffins.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-barbecue-ribs': {'action': 'edit', 'patch': {
        'name': 'Barbecue ribs',
        'notes': 'Pork ribs (spare or baby back) seasoned with a dry rub and slow-smoked or oven-baked, then basted repeatedly with barbecue sauce.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-hawaiian-pie': {'action': 'edit', 'patch': {
        'name': 'Hawaiian pie',
        'notes': 'A no-bake pie of sweetened condensed milk whipped with lemon juice and folded with crushed pineapple, pecans, and whipped topping — millionaire pie variant.',
        'cuisine': 'American',
    }},
    'corpus-titled-caramel-apples': {'action': 'edit', 'patch': {
        'name': 'Caramel apples',
        'tags': ['snack', 'dessert'],
        'notes': 'Whole apples on sticks dipped in hot melted caramel, sometimes rolled in chopped nuts — a fairground and Halloween treat.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-no-bake-cheesecake': {'action': 'edit', 'patch': {
        'name': 'No-bake cheesecake',
        'notes': 'Cream cheese whipped with sweetened condensed milk, lemon juice, and whipped topping or whipped cream, set in a graham crust without baking.',
        'cuisine': 'American',
    }},
    'corpus-titled-ground-beef-stroganoff': {'action': 'edit', 'patch': {
        'name': 'Ground beef stroganoff',
        'notes': 'Browned ground beef simmered with mushrooms and onion in a sour-cream-and-mushroom-soup gravy, served over egg noodles.',
        'cuisine': 'American',
    }},
    'corpus-titled-baked-french-toast': {'action': 'edit', 'patch': {
        'name': 'Baked French toast',
        'notes': 'Cubed bread soaked overnight in an egg-cream-and-sugar custard, then baked into a strata-style breakfast — sometimes with a streusel topping.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-buttermilk-cake': {'action': 'edit', 'patch': {
        'name': 'Buttermilk cake',
        'notes': 'A tender butter cake made tangy and moist by buttermilk and a little baking soda — often topped with a simple powdered-sugar glaze.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-stuffed-french-toast': {'action': 'edit', 'patch': {
        'name': 'Stuffed French toast',
        'tags': ['breakfast'],
        'notes': 'Thick slices of bread filled with sweetened cream cheese (and sometimes fruit jam), dipped in egg-and-milk custard, and griddled until golden.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-chocolate-trifle': {'action': 'edit', 'patch': {
        'name': 'Chocolate trifle',
        'tags': ['dessert'],
        'notes': 'Cubes of chocolate cake or brownies layered with chocolate pudding (sometimes spiked with Kahlúa), toffee bits, and whipped topping.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
        'serving_grams': 200,
    }},
    'corpus-titled-texas-chili': {'action': 'edit', 'patch': {
        'name': 'Texas chili',
        'notes': 'Cubed beef stewed with chiles, cumin, and broth — no beans, no tomato in the strictest "bowl of red" Texas tradition.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-baked-chicken-and-rice': {'action': 'edit', 'patch': {
        'name': 'Baked chicken and rice',
        'notes': 'Chicken pieces and raw rice baked in mushroom-soup-and-broth gravy — hands-off until the rice is tender.',
        'cuisine': 'American',
    }},
    'corpus-titled-vegetable-bars': {'action': 'edit', 'patch': {
        'name': 'Vegetable pizza bars',
        'tags': ['snack'],
        'notes': 'A crescent-roll crust spread with herbed cream cheese and topped with chopped raw vegetables and cheese — cut into squares; same as cold veggie pizza.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-slush-punch': {'action': 'edit', 'patch': {
        'name': 'Slush punch',
        'ingredient_categories': ['Juices', 'Tropical fruits', 'Citrus', 'Sugar & sweeteners', 'Soft drinks'],
        'tags': ['snack'],
        'notes': 'A non-alcoholic punch of fruit juices and sugar frozen until slushy, then scooped and topped with ginger ale or lemon-lime soda.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-hot-mulled-cider': {'action': 'edit', 'patch': {
        'name': 'Hot mulled cider',
        'ingredient_categories': ['Juices', 'Citrus', 'Whole spices', 'Ground spices', 'Sugar & sweeteners'],
        'tags': ['snack'],
        'notes': 'Apple cider simmered with cinnamon sticks, cloves, allspice, and citrus — sweetened and served hot; sometimes spiked with rum or brandy.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-rotel-chicken': {'action': 'edit', 'patch': {
        'name': 'Rotel chicken (King Ranch)',
        'notes': 'Shredded chicken baked with rice or noodles, Rotel tomatoes-and-chiles, mushroom soup, and Velveeta until creamy and bubbly.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-mini-pizzas': {'action': 'edit', 'patch': {
        'name': 'Mini pizzas',
        'tags': ['snack'],
        'notes': 'English muffins, bagels, or biscuit-dough rounds topped with pizza sauce, pepperoni, and mozzarella, baked until bubbly — kid-friendly snack-size pizzas.',
        'cuisine': 'American',
        'contains_add': ['pork'],
        'serving_grams': 100,
    }},
    'corpus-titled-apple-coffee-cake': {'action': 'edit', 'patch': {
        'name': 'Apple coffee cake',
        'tags': ['breakfast', 'dessert'],
        'notes': 'A tender butter cake folded with diced apples, topped with a brown-sugar-cinnamon-pecan streusel — served with morning coffee.',
        'cuisine': 'American',
    }},
    'corpus-titled-king-ranch-casserole': {'action': 'edit', 'patch': {
        'name': 'King Ranch casserole',
        'notes': 'Shredded chicken layered with tortillas, Rotel tomatoes-and-chiles, mushroom and chicken soups, and shredded cheese — the Texas casserole.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-carrot-souffle': {'action': 'edit', 'patch': {
        'name': 'Carrot soufflé',
        'notes': 'Pureed cooked carrots whipped with eggs, sugar, butter, and a touch of flour, baked into a puffed sweet-savory side — Piccadilly Cafeteria-style.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-butterfinger-cake': {'action': 'edit', 'patch': {
        'name': 'Butterfinger cake',
        'notes': 'A chocolate cake poked and saturated with sweetened condensed milk and caramel, topped with whipped topping and crushed Butterfinger bars.',
        'cuisine': 'American',
    }},
    'corpus-titled-smothered-chicken': {'action': 'edit', 'patch': {
        'name': 'Smothered chicken',
        'notes': 'Chicken pieces dredged in flour, browned, then braised in onion-and-mushroom gravy until tender — a Southern comfort dish.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-stuffed-chicken-breasts': {'action': 'edit', 'patch': {
        'name': 'Stuffed chicken breasts',
        'notes': 'Pounded chicken breasts rolled around fillings of cheese, herbs, spinach, or ham, then breaded and baked or pan-fried.',
    }},
    'corpus-titled-sugarless-apple-pie': {'action': 'edit', 'patch': {
        'name': 'Sugarless apple pie',
        'notes': 'A double-crust apple pie sweetened entirely by frozen apple-juice concentrate (no added sugar) — a diabetic-friendly variant.',
        'cuisine': 'American',
    }},
    'corpus-titled-dried-beef-dip': {'action': 'edit', 'patch': {
        'name': 'Dried beef dip',
        'tags': ['snack'],
        'notes': 'Cream cheese mixed with sour cream and torn dried (chipped) beef, peppers, and onion — served chilled or baked warm with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-veggie-bars': {'action': 'edit', 'patch': {
        'name': 'Veggie pizza bars (variant)',
        'tags': ['snack'],
        'notes': 'A crescent-roll crust spread with herbed cream cheese and topped with chopped raw vegetables and cheese — cut into squares.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-white-cake': {'action': 'edit', 'patch': {
        'name': 'White cake',
        'notes': 'A pure-white layer cake made with egg whites only (no yolks), butter, and milk — light, tight crumb, traditionally for weddings and birthdays.',
        'cuisine': 'American',
    }},
    'corpus-titled-cream-cheese-mints': {'action': 'edit', 'patch': {
        'name': 'Cream cheese mints (variant)',
        'tags': ['dessert', 'snack'],
        'notes': 'Cream cheese kneaded with powdered sugar and peppermint extract, pressed into rubber molds or rolled into balls — wedding-table candies.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-sour-cream-apple-pie': {'action': 'edit', 'patch': {
        'name': 'Sour cream apple pie',
        'notes': 'A single-crust apple pie with sliced apples folded into a sour-cream-and-cinnamon custard, baked under a brown-sugar-pecan streusel.',
        'cuisine': 'American',
    }},
    'corpus-titled-peach-salad': {'action': 'edit', 'patch': {
        'name': 'Peach Jello salad',
        'tags': ['dessert'],
        'notes': 'Peach gelatin set with canned peaches and crushed pineapple, layered with sweetened cream cheese or whipped topping — a Southern molded dessert.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-cranberry-jello-salad': {'action': 'edit', 'patch': {
        'name': 'Cranberry Jello salad',
        'tags': ['dessert'],
        'notes': 'Cranberry Jello set with whole-berry cranberry sauce, crushed pineapple, orange, and chopped pecans — a Thanksgiving side-as-dessert.',
        'cuisine': 'American',
    }},
    'corpus-titled-kool-aid-punch': {'action': 'edit', 'patch': {
        'name': 'Kool-Aid punch',
        'ingredient_categories': ['Juices', 'Sugar & sweeteners', 'Citrus', 'Tropical fruits', 'Soft drinks'],
        'tags': ['snack'],
        'notes': 'Kool-Aid powder mixed with pineapple juice, sugar, and ginger ale — a brightly colored kids\' party punch.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-green-pepper-steak': {'action': 'edit', 'patch': {
        'name': 'Green pepper steak',
        'notes': 'Strips of beef stir-fried with green bell peppers and onions in a soy-and-ginger sauce — served over rice.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-gourmet-potatoes': {'action': 'edit', 'patch': {
        'name': 'Gourmet potatoes (hash brown casserole)',
        'notes': 'Frozen hash browns baked with sour cream, butter, cream of chicken soup, and shredded cheddar under a buttered cornflake topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-holiday-salad': {'action': 'edit', 'patch': {
        'name': 'Holiday fruit salad',
        'tags': ['dessert'],
        'notes': 'Mandarin oranges, pineapple, cherries, cranberries, and chopped pecans folded with whipped topping or sour cream — a festive Southern dessert salad.',
        'cuisine': 'American',
    }},
    'corpus-titled-hot-and-sour-soup': {'action': 'edit', 'patch': {
        'name': 'Hot and sour soup',
        'notes': 'A Chinese soup of chicken broth, tofu, mushrooms, bamboo shoots, and egg ribbons seasoned with white pepper and rice vinegar — both hot and sour.',
        'cuisine': 'Chinese',
    }},
    'corpus-titled-layered-lettuce-salad': {'action': 'edit', 'patch': {
        'name': 'Layered lettuce salad',
        'notes': 'Lettuce, peas, onion, eggs, bacon, and cheese layered in a glass bowl, sealed under a mayo-and-sugar topping — chilled overnight (same as 7-layer/24-hour salad).',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-cucumber-dip': {'action': 'edit', 'patch': {
        'name': 'Cucumber dip',
        'tags': ['snack'],
        'notes': 'Cream cheese and sour cream whipped with grated cucumber, dill, and onion — served chilled with vegetables or chips.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-date-nut-balls': {'action': 'edit', 'patch': {
        'name': 'Date nut balls',
        'tags': ['dessert', 'snack'],
        'notes': 'Chopped dates cooked with butter, sugar, and egg, then stirred with Rice Krispies and pecans, rolled into balls and dusted in powdered sugar or coconut.',
        'cuisine': 'Southern',
        'serving_grams': 30,
    }},
    'corpus-titled-tomato-aspic': {'action': 'edit', 'patch': {
        'name': 'Tomato aspic',
        'notes': 'Tomato juice set with gelatin and seasoned with celery, onion, and Worcestershire — a savory molded "salad" of the mid-century table.',
        'cuisine': 'American',
    }},
    'corpus-titled-friendship-tea': {'action': 'edit', 'patch': {
        'name': 'Friendship tea',
        'ingredient_categories': ['Coffee & tea', 'Juices', 'Sugar & sweeteners', 'Whole spices', 'Ground spices', 'Citrus'],
        'tags': ['snack'],
        'notes': 'A powdered hot-drink mix of instant tea, powdered Tang, sugar, and warm spices — gifted in jars to friends to be stirred into hot water.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-american-chop-suey': {'action': 'edit', 'patch': {
        'name': 'American chop suey',
        'notes': 'Cooked elbow macaroni mixed with browned ground beef, peppers, onions, and tomato sauce — a New England weeknight dish (unrelated to Chinese chop suey).',
        'cuisine': 'American',
    }},
    'corpus-titled-upside-down-pizza': {'action': 'edit', 'patch': {
        'name': 'Upside-down pizza',
        'notes': 'A casserole of ground beef and pizza sauce topped with mozzarella, then a pizza-dough or biscuit "crust" baked on top — inverted to serve.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-sweet-potato-salad': {'action': 'edit', 'patch': {
        'name': 'Sweet potato salad',
        'notes': 'Cubed roasted or boiled sweet potatoes tossed with red onion, peppers, lime, and a chipotle or honey-mustard dressing.',
        'cuisine': 'American',
    }},
    'corpus-titled-shrimp-gumbo': {'action': 'edit', 'patch': {
        'name': 'Shrimp gumbo',
        'notes': 'Shrimp simmered in a dark-roux Louisiana broth with the trinity of vegetables, andouille sausage, okra, and Creole spices — served over rice.',
        'cuisine': 'Creole',
        'contains_add': ['pork'],
    }},
    'corpus-titled-fajitas': {'action': 'edit', 'patch': {
        'name': 'Fajitas',
        'notes': 'Marinated skirt or flank steak (or chicken) seared with sliced peppers and onions, served sizzling with warm tortillas and toppings.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-irish-bread': {'action': 'edit', 'patch': {
        'name': 'Irish soda bread (raisin)',
        'notes': 'A quick bread of flour, buttermilk, baking soda, and raisins — baked as a round loaf with a deep cross slashed on top.',
        'cuisine': 'Irish',
        'serving_grams': 55,
    }},
    'corpus-titled-apple-strudel': {'action': 'edit', 'patch': {
        'name': 'Apple strudel',
        'tags': ['dessert'],
        'notes': 'Thinly stretched dough rolled around spiced apples, raisins, breadcrumbs, and walnuts, baked until crisp and dusted with powdered sugar.',
        'cuisine': 'Austrian',
    }},
    'corpus-titled-hot-fudge-cake': {'action': 'edit', 'patch': {
        'name': 'Hot fudge cake',
        'notes': 'A self-saucing chocolate cake — batter spread in a pan, topped with cocoa-sugar and boiling water; the cake rises and a fudge sauce sinks beneath as it bakes.',
        'cuisine': 'American',
    }},
    'corpus-titled-curried-fruit': {'action': 'edit', 'patch': {
        'name': 'Curried fruit',
        'notes': 'Mixed canned fruit (pineapple, peaches, pears, cherries) baked with brown sugar, butter, and curry powder — a sweet-savory side served warm with ham.',
        'cuisine': 'American',
    }},
    'corpus-titled-hot-buttered-rum': {'action': 'edit', 'patch': {
        'name': 'Hot buttered rum',
        'tags': ['snack'],
        'notes': 'A creamy "batter" of butter, brown sugar, and warm spices stirred into hot water with rum — a winter cocktail.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
        'serving_grams': 240,
    }},
    'corpus-titled-salsa-dip': {'action': 'edit', 'patch': {
        'name': 'Salsa dip',
        'tags': ['snack'],
        'notes': 'Cream cheese topped with salsa and shredded cheese, baked or microwaved until melty — served with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-ham-ball': {'action': 'edit', 'patch': {
        'name': 'Ham ball',
        'tags': ['snack'],
        'notes': 'Cream cheese mixed with deviled ham, onion, and seasonings, shaped into a ball and rolled in chopped pecans — served chilled with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-lemon-cheesecake': {'action': 'edit', 'patch': {
        'name': 'Lemon cheesecake',
        'notes': 'A baked cream-cheese cheesecake brightened with lemon juice and zest, set on a graham crust — sometimes topped with lemon curd.',
        'cuisine': 'American',
    }},
    'corpus-titled-peach-delight': {'action': 'edit', 'patch': {
        'name': 'Peach delight',
        'tags': ['dessert'],
        'notes': 'A no-bake layered dessert of pecan-shortbread crust, sweet cream cheese, peach pie filling, and whipped topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-ritz-cracker-pie': {'action': 'edit', 'patch': {
        'name': 'Ritz cracker pie',
        'notes': 'A meringue-style pie of beaten egg whites, sugar, vanilla, and crushed Ritz crackers folded with chopped pecans — bakes into a chewy nut-pie.',
        'cuisine': 'American',
    }},
    'corpus-titled-black-bean-salad': {'action': 'edit', 'patch': {
        'name': 'Black bean salad',
        'notes': 'Black beans tossed with corn, red onion, peppers, tomato, lime, and cilantro in a cumin-lime vinaigrette.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-butter-pecan-ice-cream': {'action': 'edit', 'patch': {
        'name': 'Butter pecan ice cream',
        'notes': 'A custard ice cream flavored with butter and brown sugar, churned with toasted buttered pecans.',
        'cuisine': 'American',
        'serving_grams': 85,
    }},
    'corpus-titled-shrimp-jambalaya': {'action': 'edit', 'patch': {
        'name': 'Shrimp jambalaya',
        'notes': 'A Creole one-pot rice dish of shrimp, andouille, the holy trinity of vegetables, and Cajun spices.',
        'cuisine': 'Creole',
        'contains_add': ['pork'],
    }},
    'corpus-titled-strawberry-nut-bread': {'action': 'edit', 'patch': {
        'name': 'Strawberry nut bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A spiced quick bread folded with chopped fresh or frozen strawberries and walnuts — moist and lightly sweet.',
        'cuisine': 'American',
    }},
    'corpus-titled-dutch-apple-pie': {'action': 'edit', 'patch': {
        'name': 'Dutch apple pie',
        'notes': 'A single-crust apple pie topped with a buttery brown-sugar-flour crumb (Dutch streusel) in place of a top crust.',
        'cuisine': 'American',
    }},
    'corpus-titled-pecan-cookies': {'action': 'edit', 'patch': {
        'name': 'Pecan cookies',
        'notes': 'Drop or rolled butter cookies folded with finely chopped pecans — toasty, crisp, and lightly sweet.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-tomato-salad': {'action': 'edit', 'patch': {
        'name': 'Tomato salad',
        'notes': 'Sliced or wedged ripe tomatoes drizzled with olive oil, vinegar, salt, and fresh herbs — a summer salad in its simplest form.',
        'cuisine': 'Italian',
    }},
    'corpus-titled-yellow-cake': {'action': 'edit', 'patch': {
        'name': 'Yellow cake',
        'notes': 'A classic American butter cake with whole eggs (the yolks give it the yellow color) and milk — the baseline for layer cakes.',
        'cuisine': 'American',
    }},
    'corpus-titled-sausage-pinwheels': {'action': 'edit', 'patch': {
        'name': 'Sausage pinwheels',
        'tags': ['snack', 'breakfast'],
        'notes': 'A biscuit-mix dough rolled out, spread with cooked breakfast sausage, rolled into a log, sliced into pinwheels, and baked.',
        'cuisine': 'American',
        'contains_add': ['pork'],
        'serving_grams': 60,
    }},
    'corpus-titled-picadillo': {'action': 'edit', 'patch': {
        'name': 'Picadillo',
        'notes': 'Ground beef simmered with tomatoes, raisins, olives, peppers, onions, and warm spices — a Cuban-Caribbean braise served over rice or in empanadas.',
        'cuisine': 'Cuban',
    }},
    'corpus-titled-cherry-yum-yum': {'action': 'edit', 'patch': {
        'name': 'Cherry yum yum',
        'tags': ['dessert'],
        'notes': 'A no-bake layered dessert of graham crust, sweet cream cheese, cherry pie filling, and whipped topping — same family as cherry delight.',
        'cuisine': 'American',
    }},
    'corpus-titled-pumpkin-nut-bread': {'action': 'edit', 'patch': {
        'name': 'Pumpkin nut bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A spiced quick bread of pumpkin puree, eggs, oil, and warm spices folded with chopped walnuts or pecans.',
        'cuisine': 'American',
    }},
    'corpus-titled-impossible-cheeseburger-pie': {'action': 'edit', 'patch': {
        'name': 'Impossible cheeseburger pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'Browned ground beef and onions baked under a Bisquick-and-egg crust with shredded cheese on top — the Bisquick "impossible pie" classic.',
        'cuisine': 'American',
        'serving_grams': 320,
    }},
    'corpus-titled-champagne-salad': {'action': 'edit', 'patch': {
        'name': 'Champagne salad',
        'tags': ['dessert'],
        'notes': 'Crushed pineapple, strawberries, bananas, and pecans folded with sweetened whipped cream and cream cheese, frozen — sliced and served like ice cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-turkey-dressing': {'action': 'edit', 'patch': {
        'name': 'Turkey dressing',
        'notes': 'Stuffing-style dressing of cubed bread, onions, celery, sage, broth, and eggs baked alongside the turkey — Thanksgiving classic.',
        'cuisine': 'American',
    }},
    'corpus-titled-pineapple-dessert': {'action': 'edit', 'patch': {
        'name': 'Pineapple dessert',
        'notes': 'A no-bake layered dessert of graham crust, sweet cream cheese, pineapple pudding, and whipped topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-potato-bake': {'action': 'edit', 'patch': {
        'name': 'Potato bake',
        'notes': 'Sliced or shredded potatoes baked with sour cream, cheese, and butter — funeral-potatoes-style.',
        'cuisine': 'American',
    }},
    'corpus-titled-garlic-chicken': {'action': 'edit', 'patch': {
        'name': 'Garlic chicken',
        'notes': 'Chicken pieces baked or pan-seared with a generous amount of garlic, olive oil, herbs, and lemon — sometimes finished in butter.',
        'cuisine': 'American',
    }},
    'corpus-titled-beef-barley-soup': {'action': 'edit', 'patch': {
        'name': 'Beef barley soup',
        'notes': 'Cubed beef and pearl barley simmered with onions, carrots, celery, and tomatoes in beef broth until thick and hearty.',
        'cuisine': 'American',
    }},
    'corpus-titled-apple-dapple-cake': {'action': 'edit', 'patch': {
        'name': 'Apple dapple cake',
        'notes': 'A moist oil-based cake folded with diced apples and pecans, soaked after baking with a brown-sugar caramel glaze poured over the warm cake.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-coconut-cookies': {'action': 'edit', 'patch': {
        'name': 'Coconut cookies',
        'notes': 'A butter drop cookie folded with shredded coconut — sometimes with chopped almonds or chocolate chips.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-chinese-chews': {'action': 'edit', 'patch': {
        'name': 'Chinese chews',
        'tags': ['dessert'],
        'notes': 'A chewy date-and-nut bar of flour, sugar, eggs, chopped dates, and walnuts baked and cut into squares, rolled in powdered sugar.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-turkey-pot-pie': {'action': 'edit', 'patch': {
        'name': 'Turkey pot pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'Diced cooked turkey and vegetables in a creamy gravy baked under a flaky pastry or biscuit crust — Thanksgiving leftovers reborn.',
        'cuisine': 'American',
        'serving_grams': 320,
    }},
    'corpus-titled-yogurt': {'action': 'edit', 'patch': {
        'name': 'Homemade yogurt',
        'tags': ['breakfast', 'snack'],
        'notes': 'Milk heated, cooled to body temp, inoculated with a yogurt starter, and held warm overnight until set — a homemade live-culture yogurt.',
        'serving_grams': 170,
    }},
    'corpus-titled-falafel': {'action': 'edit', 'patch': {
        'name': 'Falafel',
        'notes': 'A Middle Eastern fritter of soaked dried chickpeas ground with herbs, onion, garlic, cumin, and coriander, formed into balls and deep-fried.',
        'cuisine': 'Middle Eastern',
    }},
    'corpus-titled-chocolate-fudge-pie': {'action': 'edit', 'patch': {
        'name': 'Chocolate fudge pie',
        'notes': 'A thin crustless chocolate pie of butter, sugar, eggs, cocoa, and flour — brownie-like with a glossy fudge top.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-hot-spiced-cider': {'action': 'edit', 'patch': {
        'name': 'Hot spiced cider',
        'ingredient_categories': ['Juices', 'Whole spices', 'Ground spices', 'Citrus', 'Sugar & sweeteners'],
        'tags': ['snack'],
        'notes': 'Apple cider simmered with cinnamon sticks, cloves, and citrus — a hot non-alcoholic autumn drink (alcoholic versions add rum or brandy).',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-irish-cream': {'action': 'edit', 'patch': {
        'name': 'Homemade Irish cream',
        'tags': ['snack'],
        'notes': 'Sweetened condensed milk, cream, Irish whiskey, and instant coffee blended with chocolate syrup and vanilla — a homemade Bailey\'s.',
        'cuisine': 'Irish',
        'contains_add': ['alcohol'],
        'serving_grams': 45,
    }},
    'corpus-titled-barbecued-ribs': {'action': 'edit', 'patch': {
        'name': 'Barbecued ribs',
        'notes': 'Pork ribs seasoned with a dry rub, slow-smoked or oven-baked, and basted with barbecue sauce — slip-from-the-bone tender.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-meat-pie': {'action': 'edit', 'patch': {
        'name': 'Meat pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'A generic name for a savory pastry filled with seasoned ground or chopped meat and vegetables — shepherd-pie, tourtière, or hand-pie family.',
        'serving_grams': 200,
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

    print('corpus-titled batch-8 audit applied (entries 1051-1200 by frequency).')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
