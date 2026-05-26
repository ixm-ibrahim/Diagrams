"""Corpus-titled meals audit — batch 2 (next 150 by frequency, 541 -> 319).

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
    'corpus-titled-pumpkin-cake': {'action': 'edit', 'patch': {
        'name': 'Pumpkin cake',
        'notes': 'A spiced oil-based cake of pumpkin puree, eggs, and warm spices, usually frosted with cream cheese icing.',
        'cuisine': 'American',
    }},
    'corpus-titled-frozen-fruit-salad': {'action': 'edit', 'patch': {
        'name': 'Frozen fruit salad',
        'tags': ['dessert'],
        'notes': 'Mixed canned and fresh fruit folded with sweetened cream cheese and whipped topping, frozen in a pan and sliced — a retro Southern picnic dessert.',
        'cuisine': 'American',
    }},
    'corpus-titled-scalloped-corn': {'action': 'edit', 'patch': {
        'name': 'Scalloped corn',
        'notes': 'Sweet corn baked in a custard of eggs, milk, and butter under a buttered cracker topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-marinated-carrots': {'action': 'edit', 'patch': {
        'name': 'Marinated carrots',
        'notes': 'Blanched carrot slices tossed with peppers and onions in a sweet tomato-vinegar marinade — chilled overnight as a Southern side.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-meatloaf': {'action': 'edit', 'patch': {
        'name': 'Classic meatloaf',
        'notes': 'A ground-beef loaf bound with breadcrumbs and egg, seasoned with onions and herbs, glazed with ketchup, and baked.',
        'cuisine': 'American',
    }},
    'corpus-titled-russian-tea': {'action': 'edit', 'patch': {
        'name': 'Russian tea',
        'ingredient_categories': ['Coffee & tea', 'Juices', 'Sugar & sweeteners', 'Whole spices', 'Ground spices', 'Citrus'],
        'tags': ['snack'],
        'notes': 'A powdered hot-drink mix of instant tea, Tang, sugar, and warm spices — stirred into hot water; non-alcoholic despite the name.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-yeast-rolls': {'action': 'edit', 'patch': {
        'name': 'Yeast rolls',
        'notes': 'Soft enriched yeasted rolls of flour, milk, butter, sugar, and egg — proofed twice and baked until golden.',
        'serving_grams': 50,
    }},
    'corpus-titled-chocolate-fudge': {'action': 'edit', 'patch': {
        'name': 'Chocolate fudge',
        'notes': 'Sugar, butter, chocolate, and evaporated milk cooked to soft-ball and beaten until creamy — poured to set and cut into squares.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-cole-slaw': {'action': 'edit', 'patch': {
        'name': 'Coleslaw',
        'notes': 'Shredded cabbage and carrot in a sweet-tangy mayonnaise dressing — the picnic-and-barbecue staple.',
        'cuisine': 'American',
    }},
    'corpus-titled-cucumber-salad': {'action': 'edit', 'patch': {
        'name': 'Cucumber salad',
        'notes': 'Thinly sliced cucumber and onion tossed in a sweet vinegar dressing — chilled until crisp.',
    }},
    'corpus-titled-chicken': {'action': 'edit', 'patch': {
        'name': 'Roast chicken',
        'notes': 'Seasoned whole chicken or pieces roasted with vegetables — the unadorned baseline preparation.',
        'serving_grams': 260,
    }},
    'corpus-titled-party-punch': {'action': 'edit', 'patch': {
        'name': 'Party punch',
        'ingredient_categories': ['Juices', 'Tropical fruits', 'Citrus', 'Sugar & sweeteners', 'Soft drinks'],
        'tags': ['snack'],
        'notes': 'A non-alcoholic gathering drink of mixed juices, ginger ale, and sherbet — ladled from a bowl over ice.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-pineapple-cake': {'action': 'edit', 'patch': {
        'name': 'Pineapple cake',
        'notes': 'A moist cake folded with crushed pineapple in its juice, often glazed with cream cheese frosting.',
        'cuisine': 'American',
    }},
    'corpus-titled-dinner-tonight': {'action': 'drop', 'reason': 'non-specific placeholder, not a coherent meal'},
    'corpus-titled-dill-dip': {'action': 'edit', 'patch': {
        'name': 'Dill dip',
        'tags': ['snack'],
        'notes': 'Sour cream and mayo seasoned with dill, parsley, onion, and Beau Monde — served chilled with vegetables or bread.',
        'serving_grams': 60,
    }},
    'corpus-titled-quiche': {'action': 'edit', 'patch': {
        'name': 'Quiche',
        'notes': 'A pastry shell filled with an egg-and-cream custard, cheese, and vegetables or bacon — baked until just set.',
        'cuisine': 'French',
        'contains_add': ['pork'],
    }},
    'corpus-titled-corn-fritters': {'action': 'edit', 'patch': {
        'name': 'Corn fritters',
        'notes': 'Sweet corn folded into a leavened batter and pan-fried in spoonfuls until crisp and golden.',
        'cuisine': 'American',
    }},
    'corpus-titled-jello-salad': {'action': 'edit', 'patch': {
        'name': 'Jello salad',
        'tags': ['dessert'],
        'notes': 'A molded Southern dessert-salad of fruit-flavored gelatin set with canned pineapple, cream cheese, and sometimes marshmallows.',
        'cuisine': 'American',
    }},
    'corpus-titled-lemon-bars': {'action': 'edit', 'patch': {
        'name': 'Lemon bars',
        'tags': ['dessert'],
        'notes': 'A shortbread crust topped with a baked lemon-egg curd, cooled and dusted with powdered sugar.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-seven-layer-salad': {'action': 'edit', 'patch': {
        'name': 'Seven-layer salad',
        'notes': 'Lettuce, peas, onion, bacon, cheese, and other layers built in a glass bowl, sealed under a mayo-sugar topping, and chilled overnight.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-eggplant-casserole': {'action': 'edit', 'patch': {
        'name': 'Eggplant casserole',
        'notes': 'Sliced eggplant baked with eggs, milk, cheese, and a buttered cracker topping — a Southern-style side.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-salmon-loaf': {'action': 'edit', 'patch': {
        'name': 'Salmon loaf',
        'notes': 'Canned salmon mixed with breadcrumbs, egg, milk, lemon, and onion, baked in a loaf — a Depression-era pantry dish.',
        'cuisine': 'American',
    }},
    'corpus-titled-pot-roast': {'action': 'edit', 'patch': {
        'name': 'Pot roast',
        'notes': 'A tough beef cut (chuck or round) seared and slow-braised in broth with onions, carrots, and potatoes until fork-tender.',
        'cuisine': 'American',
    }},
    'corpus-titled-cream-of-broccoli-soup': {'action': 'edit', 'patch': {
        'name': 'Cream of broccoli soup',
        'notes': 'Broccoli simmered in chicken broth, pureed, and thickened with a milk-and-butter roux.',
    }},
    'corpus-titled-sweet-and-sour-chicken': {'action': 'edit', 'patch': {
        'name': 'Sweet and sour chicken',
        'notes': 'Battered chicken chunks deep-fried and tossed in a glossy sauce of vinegar, sugar, ketchup, and pineapple — served over rice.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-granola': {'action': 'edit', 'patch': {
        'name': 'Granola',
        'notes': 'Rolled oats baked with honey or maple, oil, nuts, seeds, and dried fruit until clustery and crisp.',
        'serving_grams': 55,
    }},
    'corpus-titled-layered-salad': {'action': 'edit', 'patch': {
        'name': 'Layered salad',
        'notes': 'A bowl-built salad of lettuce, peas, eggs, cheese, and bacon under a mayonnaise-and-sugar seal, chilled overnight — a variant of seven-layer.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-rice-casserole': {'action': 'edit', 'patch': {
        'name': 'Rice casserole',
        'notes': 'Raw rice baked with broth, beef or mushrooms, and butter until tender — the consommé-rice pantry side.',
    }},
    'corpus-titled-puppy-chow': {'action': 'edit', 'patch': {
        'name': 'Puppy chow (muddy buddies)',
        'tags': ['snack', 'dessert'],
        'notes': 'Chex cereal coated in melted chocolate and peanut butter, then tossed with powdered sugar — a sweet snack mix.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-jambalaya': {'action': 'edit', 'patch': {
        'name': 'Jambalaya',
        'notes': 'A Creole one-pot rice dish with andouille, chicken, shrimp, the holy trinity of vegetables, and Cajun seasoning.',
        'cuisine': 'Creole',
        'contains_add': ['pork'],
    }},
    'corpus-titled-broccoli-soup': {'action': 'edit', 'patch': {
        'name': 'Broccoli soup',
        'notes': 'Broccoli florets simmered with onion and broth, sometimes blended, sometimes left chunky — finished with milk or cream.',
    }},
    'corpus-titled-hot-chocolate-mix': {'action': 'edit', 'patch': {
        'name': 'Hot chocolate mix',
        'ingredient_categories': ['Sugar & sweeteners', 'Milk', 'Candy & desserts'],
        'tags': ['snack'],
        'notes': 'A dry pantry mix of powdered milk, cocoa, sugar, and powdered creamer — stirred into hot water for instant cocoa.',
        'serving_grams': 240,
    }},
    'corpus-titled-calico-beans': {'action': 'edit', 'patch': {
        'name': 'Calico beans',
        'notes': 'A baked-bean medley of kidney, butter, and pork-and-beans simmered with ground beef, bacon, brown sugar, and barbecue sauce.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-cauliflower-salad': {'action': 'edit', 'patch': {
        'name': 'Cauliflower salad',
        'notes': 'Raw cauliflower florets tossed with bacon, cheese, and red onion in a sweet mayonnaise dressing — broccoli-salad style.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-gingerbread': {'action': 'edit', 'patch': {
        'name': 'Gingerbread',
        'tags': ['dessert', 'snack'],
        'notes': 'A dark spiced quick bread or cake leavened with baking soda and sweetened with molasses — served warm with whipped cream or lemon sauce.',
    }},
    'corpus-titled-fruit-cake': {'action': 'edit', 'patch': {
        'name': 'Fruitcake',
        'notes': 'A dense holiday cake packed with candied fruit, dried fruit, and nuts in a spiced butter batter — often soaked in spirits and aged.',
    }},
    'corpus-titled-irish-soda-bread': {'action': 'edit', 'patch': {
        'name': 'Irish soda bread',
        'notes': 'A quick bread of flour, buttermilk, and baking soda — sometimes sweetened with raisins, baked as a round loaf with a deep cross slashed on top.',
        'cuisine': 'Irish',
        'serving_grams': 55,
    }},
    'corpus-titled-clam-chowder': {'action': 'edit', 'patch': {
        'name': 'New England clam chowder',
        'notes': 'Diced potatoes and clams simmered in a salt-pork-and-onion base, finished with milk and cream — the chowder house classic.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-red-beans-and-rice': {'action': 'edit', 'patch': {
        'name': 'Red beans and rice',
        'notes': 'Red beans slow-simmered with andouille sausage and the holy trinity, served over long-grain rice — a New Orleans Monday standard.',
        'cuisine': 'Creole',
        'contains_add': ['pork'],
    }},
    'corpus-titled-fresh-strawberry-pie': {'action': 'edit', 'patch': {
        'name': 'Fresh strawberry pie',
        'notes': 'Whole or sliced fresh strawberries piled in a baked crust and set with a cooked sugar-and-cornstarch glaze — chilled and served with whipped cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-pizza': {'action': 'edit', 'patch': {
        'name': 'Pizza',
        'notes': 'A yeasted dough crust topped with tomato sauce, mozzarella, and toppings (commonly pepperoni or sausage), baked at high heat.',
        'cuisine': 'Italian-American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-enchiladas': {'action': 'edit', 'patch': {
        'name': 'Enchiladas',
        'notes': 'Corn tortillas dipped in chile sauce, rolled around a meat-or-cheese filling, baked, and topped with more sauce and crumbled cheese.',
        'cuisine': 'Mexican',
    }},
    'corpus-titled-lemon-squares': {'action': 'edit', 'patch': {
        'name': 'Lemon squares',
        'tags': ['dessert'],
        'notes': 'A shortbread crust topped with a baked tart lemon custard — cut into squares and dusted with powdered sugar.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-broccoli-and-rice-casserole': {'action': 'edit', 'patch': {
        'name': 'Broccoli and rice casserole',
        'notes': 'Cooked rice baked with broccoli florets, cream of mushroom soup, Cheez Whiz or processed cheese, and butter — a Southern potluck mainstay.',
        'cuisine': 'American',
    }},
    'corpus-titled-coconut-cream-pie': {'action': 'edit', 'patch': {
        'name': 'Coconut cream pie',
        'notes': 'A baked pastry shell filled with a coconut-milk custard pudding, topped with whipped cream and toasted coconut.',
        'cuisine': 'American',
    }},
    'corpus-titled-spaghetti-pie': {'action': 'edit', 'patch': {
        'name': 'Spaghetti pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'Cooked spaghetti pressed into a pie pan with egg and Parmesan as the "crust", filled with ricotta and meat sauce and baked.',
        'cuisine': 'Italian-American',
        'serving_grams': 320,
    }},
    'corpus-titled-hummingbird-cake': {'action': 'edit', 'patch': {
        'name': 'Hummingbird cake',
        'notes': 'A spiced banana-pineapple layer cake with chopped pecans, frosted with cream cheese icing — a Southern classic.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-orange-salad': {'action': 'edit', 'patch': {
        'name': 'Orange salad',
        'tags': ['dessert', 'snack'],
        'notes': 'A molded gelatin salad of mandarin oranges, crushed pineapple, and cottage cheese set with orange Jello.',
        'cuisine': 'American',
    }},
    'corpus-titled-mississippi-mud-cake': {'action': 'edit', 'patch': {
        'name': 'Mississippi mud cake',
        'notes': 'A dense chocolate sheet cake topped with marshmallow creme and a layer of chocolate-pecan frosting — gooey and rich.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-crab-cakes': {'action': 'edit', 'patch': {
        'name': 'Crab cakes',
        'tags': ['dinner', 'lunch'],
        'notes': 'Lump crab bound with mayo, egg, and a little breadcrumb or cracker, formed into patties and pan-fried or broiled.',
        'cuisine': 'American',
        'serving_grams': 170,
    }},
    'corpus-titled-blueberry-salad': {'action': 'edit', 'patch': {
        'name': 'Blueberry salad',
        'tags': ['dessert'],
        'notes': 'A molded gelatin salad of blueberries and crushed pineapple topped with a sour cream and cream cheese layer — a Southern potluck dish.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-potato-chip-cookies': {'action': 'edit', 'patch': {
        'name': 'Potato chip cookies',
        'notes': 'A butter shortbread-style cookie with crushed potato chips and chopped pecans folded into the dough — salty-sweet and crunchy.',
        'cuisine': 'American',
    }},
    'corpus-titled-pistachio-salad': {'action': 'edit', 'patch': {
        'name': 'Pistachio salad',
        'tags': ['dessert'],
        'notes': 'Crushed pineapple folded with instant pistachio pudding mix, miniature marshmallows, and whipped topping — the green "Watergate" cousin.',
        'cuisine': 'American',
    }},
    'corpus-titled-tea-cakes': {'action': 'edit', 'patch': {
        'name': 'Southern tea cakes',
        'notes': 'A simple sugar-butter cookie scented with vanilla and nutmeg — soft, cake-like, traditionally served with tea.',
        'cuisine': 'Southern',
        'serving_grams': 60,
    }},
    'corpus-titled-baked-corn': {'action': 'edit', 'patch': {
        'name': 'Baked corn',
        'notes': 'Corn kernels baked in a sweet milk-and-egg custard with butter — a Pennsylvania Dutch side dish.',
        'cuisine': 'American',
    }},
    'corpus-titled-fried-green-tomatoes': {'action': 'edit', 'patch': {
        'name': 'Fried green tomatoes',
        'notes': 'Slices of unripe green tomatoes dredged in egg and cornmeal, then pan-fried until crisp — a Southern summer side.',
        'cuisine': 'Southern',
        'serving_grams': 150,
    }},
    'corpus-titled-brunswick-stew': {'action': 'edit', 'patch': {
        'name': 'Brunswick stew',
        'notes': 'A thick Southern stew of pulled pork, chicken, lima beans, corn, potatoes, and tomato in barbecue-spiced broth.',
        'cuisine': 'Southern',
        'contains_add': ['pork'],
    }},
    'corpus-titled-chicken-noodle-soup': {'action': 'edit', 'patch': {
        'name': 'Chicken noodle soup',
        'notes': 'Chicken simmered in broth with carrots, celery, onion, and egg noodles — the home-remedy classic.',
        'cuisine': 'American',
    }},
    'corpus-titled-vegetable-salad': {'action': 'edit', 'patch': {
        'name': 'Marinated vegetable salad',
        'notes': 'Mixed cooked or canned vegetables tossed in a sweet vinaigrette and chilled overnight — a make-ahead picnic side.',
    }},
    'corpus-titled-divinity': {'action': 'edit', 'patch': {
        'name': 'Divinity',
        'tags': ['dessert'],
        'notes': 'A white, fluffy confection of hot sugar syrup whipped into stiff egg whites with vanilla and pecans — dropped onto wax paper to set.',
        'cuisine': 'Southern',
        'serving_grams': 40,
    }},
    'corpus-titled-cabbage-rolls': {'action': 'edit', 'patch': {
        'name': 'Cabbage rolls',
        'notes': 'Blanched cabbage leaves wrapped around ground beef, rice, and onion, then baked in tomato sauce — Eastern European golabki style.',
        'cuisine': 'Eastern European',
    }},
    'corpus-titled-pineapple-upside-down-cake': {'action': 'edit', 'patch': {
        'name': 'Pineapple upside-down cake',
        'notes': 'A skillet cake baked over pineapple rings and maraschino cherries set in a brown-sugar-butter glaze, inverted to serve.',
        'cuisine': 'American',
    }},
    'corpus-titled-italian-cream-cake': {'action': 'edit', 'patch': {
        'name': 'Italian cream cake',
        'notes': 'A Southern layer cake of buttermilk batter folded with coconut and pecans, frosted with cream cheese icing — despite the name, an American creation.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-pea-salad': {'action': 'edit', 'patch': {
        'name': 'Pea salad',
        'notes': 'Sweet green peas tossed with hard-boiled egg, cheddar, red onion, and bacon in a mayo dressing — a Southern picnic side.',
        'cuisine': 'Southern',
        'contains_add': ['pork'],
    }},
    'corpus-titled-cheese-dip': {'action': 'edit', 'patch': {
        'name': 'Cheese dip',
        'tags': ['snack'],
        'notes': 'Velveeta-style processed cheese melted with diced tomatoes and chiles (Rotel) — served warm with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-sweet-and-sour-meatballs': {'action': 'edit', 'patch': {
        'name': 'Sweet and sour meatballs',
        'notes': 'Pan-fried meatballs simmered in a sweet-tangy sauce of vinegar, brown sugar, and pineapple — served over rice or as an appetizer.',
        'cuisine': 'American',
    }},
    'corpus-titled-vanilla-ice-cream': {'action': 'edit', 'patch': {
        'name': 'Vanilla ice cream',
        'notes': 'A churned custard of milk, cream, sugar, egg yolks, and vanilla — the baseline frozen dessert.',
        'serving_grams': 85,
    }},
    'corpus-titled-poppy-seed-cake': {'action': 'edit', 'patch': {
        'name': 'Poppy seed cake',
        'notes': 'A pound-style cake folded with poppy seeds — sometimes lemon-glazed, sometimes baked from a mix with pudding stirred in.',
    }},
    'corpus-titled-popcorn-balls': {'action': 'edit', 'patch': {
        'name': 'Popcorn balls',
        'notes': 'Popped corn pressed into balls with a hot caramel or marshmallow syrup — a Halloween-and-fair treat.',
        'cuisine': 'American',
    }},
    'corpus-titled-cheese-straws': {'action': 'edit', 'patch': {
        'name': 'Cheese straws',
        'tags': ['snack'],
        'notes': 'A short crisp savory biscuit of butter, sharp cheddar, flour, and cayenne — piped into thin straws and baked.',
        'cuisine': 'Southern',
        'serving_grams': 30,
    }},
    'corpus-titled-pumpkin-cookies': {'action': 'edit', 'patch': {
        'name': 'Pumpkin cookies',
        'notes': 'Soft drop cookies of pumpkin puree, butter, brown sugar, and warm spices — often with raisins or a maple glaze.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-veg-all-casserole': {'action': 'edit', 'patch': {
        'name': 'Veg-All casserole',
        'ingredient_categories': ['Other vegetables', 'Aged cheese', 'Baked snacks & pastries', 'Extracts & essences', 'Margarine & shortening'],
        'notes': 'Canned Veg-All mixed vegetables baked with mayo, onion, and shredded cheese under a buttered cracker topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-refrigerator-rolls': {'action': 'edit', 'patch': {
        'name': 'Refrigerator rolls',
        'notes': 'A make-ahead enriched yeast dough mixed and chilled overnight, then shaped and baked the next day for soft dinner rolls.',
        'cuisine': 'American',
        'serving_grams': 50,
    }},
    'corpus-titled-baked-chicken': {'action': 'edit', 'patch': {
        'name': 'Baked chicken',
        'notes': 'Bone-in chicken pieces seasoned and roasted in a hot oven until skin is crisp and juices run clear.',
        'serving_grams': 260,
    }},
    'corpus-titled-cherry-salad': {'action': 'edit', 'patch': {
        'name': 'Cherry salad',
        'tags': ['dessert'],
        'notes': 'A molded cherry-gelatin salad set with crushed pineapple, condensed milk, and chopped pecans — a Southern picnic dessert.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-cherry-delight': {'action': 'edit', 'patch': {
        'name': 'Cherry delight',
        'tags': ['dessert'],
        'notes': 'A no-bake layered dessert of graham crust, sweet cream cheese, cherry pie filling, and whipped topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-orange-julius': {'action': 'edit', 'patch': {
        'name': 'Orange Julius',
        'ingredient_categories': ['Citrus', 'Juices', 'Milk', 'Sugar & sweeteners', 'Extracts & essences'],
        'tags': ['snack'],
        'notes': 'Frozen orange juice concentrate, milk, sugar, vanilla, and ice blended into a frothy creamsicle-flavored drink.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-spiced-tea': {'action': 'edit', 'patch': {
        'name': 'Spiced tea',
        'ingredient_categories': ['Coffee & tea', 'Juices', 'Citrus', 'Sugar & sweeteners', 'Whole spices', 'Ground spices'],
        'tags': ['snack'],
        'notes': 'Black tea simmered with orange juice, cinnamon sticks, and cloves — sweetened and served hot.',
        'serving_grams': 240,
    }},
    'corpus-titled-refrigerator-pickles': {'action': 'drop', 'reason': 'pickled condiment, not a coherent meal'},
    'corpus-titled-molasses-cookies': {'action': 'edit', 'patch': {
        'name': 'Molasses cookies',
        'notes': 'Soft chewy cookies of butter, molasses, brown sugar, and warm spices — rolled in sugar before baking.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-bean-salad': {'action': 'edit', 'patch': {
        'name': 'Three-bean salad',
        'notes': 'Green, wax, and kidney beans tossed with onion and peppers in a sweet vinegar dressing — chilled overnight.',
        'cuisine': 'American',
    }},
    'corpus-titled-lemon-meringue-pie': {'action': 'edit', 'patch': {
        'name': 'Lemon meringue pie',
        'notes': 'A baked crust filled with tangy lemon custard and topped with billows of sweetened meringue, browned in the oven.',
        'cuisine': 'American',
    }},
    'corpus-titled-million-dollar-pie': {'action': 'edit', 'patch': {
        'name': 'Million dollar pie',
        'notes': 'A no-bake pie of sweetened condensed milk whipped with lemon juice and folded with crushed pineapple, pecans, and whipped topping — in a graham crust.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-impossible-pie': {'action': 'edit', 'patch': {
        'name': 'Impossible pie',
        'notes': 'A blender custard of eggs, milk, sugar, butter, coconut, and Bisquick that self-separates into crust and filling as it bakes.',
        'cuisine': 'American',
    }},
    'corpus-titled-poppy-seed-bread': {'action': 'edit', 'patch': {
        'name': 'Poppy seed bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A sweet quick bread folded with poppy seeds and finished with a citrus glaze.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-delight': {'action': 'edit', 'patch': {
        'name': 'Chocolate delight',
        'tags': ['dessert'],
        'notes': 'A no-bake layered dessert of pecan-shortbread crust, sweet cream cheese, chocolate pudding, and whipped topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-sweet-potato-souffle': {'action': 'edit', 'patch': {
        'name': 'Sweet potato souffle',
        'notes': 'Mashed sweet potato whipped with eggs, sugar, butter, and milk, baked under a brown-sugar-pecan or marshmallow topping.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-hot-crab-dip': {'action': 'edit', 'patch': {
        'name': 'Hot crab dip',
        'tags': ['snack'],
        'notes': 'Cream cheese, mayo, and lump crab seasoned with Worcestershire and Old Bay, baked until bubbling and served with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-tamale-pie': {'action': 'edit', 'patch': {
        'name': 'Tamale pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'A seasoned beef-and-corn-chili filling topped with cornbread batter and baked — a one-pan Tex-Mex casserole.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 320,
    }},
    'corpus-titled-hamburger-pie': {'action': 'edit', 'patch': {
        'name': 'Hamburger pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'Browned ground beef and vegetables in a savory base, topped with mashed potatoes and cheese, baked like a shepherd\'s pie.',
        'cuisine': 'American',
        'serving_grams': 320,
    }},
    'corpus-titled-taco-pie': {'action': 'edit', 'patch': {
        'name': 'Taco pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'Seasoned ground beef baked over a crescent-roll or cornmeal crust, topped with sour cream, cheese, tomatoes, and crushed chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 320,
    }},
    'corpus-titled-waldorf-salad': {'action': 'edit', 'patch': {
        'name': 'Waldorf salad',
        'notes': 'Diced apples, celery, and walnuts tossed in mayonnaise — sometimes with grapes or raisins; named for the Waldorf-Astoria.',
        'cuisine': 'American',
    }},
    'corpus-titled-oven-fried-chicken': {'action': 'edit', 'patch': {
        'name': 'Oven-fried chicken',
        'notes': 'Chicken pieces dredged in seasoned flour or cornflake crumbs and baked on a buttered sheet — a lighter take on fried chicken.',
        'cuisine': 'American',
        'serving_grams': 260,
    }},
    'corpus-titled-pumpkin-roll': {'action': 'edit', 'patch': {
        'name': 'Pumpkin roll',
        'tags': ['dessert'],
        'notes': 'A thin pumpkin sponge cake baked on a sheet pan, rolled with a cream-cheese filling, chilled and sliced into pinwheels.',
        'cuisine': 'American',
    }},
    'corpus-titled-copper-pennies': {'action': 'edit', 'patch': {
        'name': 'Copper pennies',
        'notes': 'Sliced cooked carrots ("pennies") tossed with bell pepper and onion in a tangy tomato-soup-and-vinegar marinade — chilled overnight.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-tuna-noodle-casserole': {'action': 'edit', 'patch': {
        'name': 'Tuna noodle casserole',
        'notes': 'Egg noodles baked with canned tuna, peas, and cream of mushroom soup under a buttered breadcrumb or crushed-potato-chip topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-salad-dressing': {'action': 'drop', 'reason': 'dressing component, not a coherent meal'},
    'corpus-titled-cheesy-potatoes': {'action': 'edit', 'patch': {
        'name': 'Cheesy potatoes',
        'notes': 'Frozen hash browns baked with sour cream, cream of chicken soup, and shredded cheddar — a potluck staple also called funeral potatoes.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-eclair-cake': {'action': 'edit', 'patch': {
        'name': 'Chocolate eclair cake',
        'notes': 'A no-bake icebox cake of graham crackers layered with vanilla pudding, topped with chocolate frosting — softens to cake-like texture overnight.',
        'cuisine': 'American',
    }},
    'corpus-titled-poppy-seed-chicken': {'action': 'edit', 'patch': {
        'name': 'Poppy seed chicken',
        'notes': 'Shredded chicken baked in sour cream and cream of chicken soup under a buttery Ritz-cracker-and-poppy-seed topping.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-chocolate-chip-cake': {'action': 'edit', 'patch': {
        'name': 'Chocolate chip cake',
        'notes': 'A Bundt-style cake made from yellow cake mix with sour cream, chocolate chips, and a swirl of cinnamon-sugar.',
        'cuisine': 'American',
    }},
    'corpus-titled-monster-cookies': {'action': 'edit', 'patch': {
        'name': 'Monster cookies',
        'notes': 'Oversized drop cookies of peanut butter, oats, M&Ms, and chocolate chips — often flourless and chewy.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-buttermilk-biscuits': {'action': 'edit', 'patch': {
        'name': 'Buttermilk biscuits (Southern)',
        'tags': ['breakfast'],
        'notes': 'A flaky quick bread of flour, baking powder, cold butter or shortening, and buttermilk — patted, cut, and baked until tall.',
        'cuisine': 'Southern',
        'serving_grams': 55,
    }},
    'corpus-titled-cornbread-salad': {'action': 'edit', 'patch': {
        'name': 'Cornbread salad',
        'notes': 'Crumbled cornbread layered with beans, tomatoes, cheese, bacon, and ranch-style dressing in a glass bowl — a Southern potluck dish.',
        'cuisine': 'Southern',
        'contains_add': ['pork'],
    }},
    'corpus-titled-salisbury-steak': {'action': 'edit', 'patch': {
        'name': 'Salisbury steak',
        'notes': 'A seasoned ground-beef patty shaped like a steak, pan-fried, then simmered in a mushroom-and-onion brown gravy.',
        'cuisine': 'American',
    }},
    'corpus-titled-fudge-pie': {'action': 'edit', 'patch': {
        'name': 'Fudge pie',
        'notes': 'A thin crustless chocolate pie of butter, sugar, eggs, cocoa, and flour — brownie-like with a glossy top.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-chocolate-mousse': {'action': 'edit', 'patch': {
        'name': 'Chocolate mousse',
        'notes': 'Melted chocolate folded with whipped cream and beaten egg whites or yolks into an airy chilled dessert.',
        'cuisine': 'French',
        'serving_grams': 100,
    }},
    'corpus-titled-mexican-lasagna': {'action': 'edit', 'patch': {
        'name': 'Mexican lasagna',
        'notes': 'Layered tortillas, seasoned ground beef, enchilada or salsa sauce, beans, and cheese — baked into a lasagna-style casserole.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-hamburger-soup': {'action': 'edit', 'patch': {
        'name': 'Hamburger soup',
        'notes': 'Ground beef simmered with mixed vegetables, tomatoes, and herbs in beef broth — a stockpot weeknight soup.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-sheet-cake': {'action': 'edit', 'patch': {
        'name': 'Texas chocolate sheet cake',
        'notes': 'A thin chocolate-buttermilk sheet cake topped warm with a poured cocoa-pecan icing that sets to a fudge-like crust.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-carrot-salad': {'action': 'edit', 'patch': {
        'name': 'Carrot raisin salad',
        'notes': 'Shredded carrots tossed with raisins, crushed pineapple, and a mayonnaise-and-sugar dressing — chilled before serving.',
        'cuisine': 'American',
    }},
    'corpus-titled-salmon-patties': {'action': 'edit', 'patch': {
        'name': 'Salmon patties',
        'notes': 'Canned salmon mixed with egg, onion, and crushed crackers or cornmeal, formed into patties and pan-fried until crisp.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-corn-salad': {'action': 'edit', 'patch': {
        'name': 'Corn salad',
        'notes': 'Sweet corn kernels tossed with bell pepper, red onion, and tomato in a vinaigrette — a summer picnic side.',
        'cuisine': 'American',
    }},
    'corpus-titled-tortilla-soup': {'action': 'edit', 'patch': {
        'name': 'Tortilla soup',
        'notes': 'A spiced tomato-chicken broth with onion, garlic, and chiles, served over crispy tortilla strips and topped with avocado, cheese, and lime.',
        'cuisine': 'Mexican',
    }},
    'corpus-titled-lentil-soup': {'action': 'edit', 'patch': {
        'name': 'Lentil soup',
        'notes': 'Brown or green lentils simmered with onions, carrots, celery, and herbs in broth — sometimes with bacon or ham hock.',
    }},
    'corpus-titled-broccoli-cheese-soup': {'action': 'edit', 'patch': {
        'name': 'Broccoli cheese soup',
        'notes': 'Broccoli simmered in a milk-and-roux base, blended with sharp cheddar and Velveeta — a Panera-style chowder.',
        'cuisine': 'American',
    }},
    'corpus-titled-buckeyes': {'action': 'edit', 'patch': {
        'name': 'Buckeyes',
        'tags': ['dessert', 'snack'],
        'notes': 'Peanut butter and powdered sugar balls partially dipped in chocolate to resemble the buckeye nut — an Ohio holiday candy.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-chocolate-oatmeal-cookies': {'action': 'edit', 'patch': {
        'name': 'Chocolate oatmeal cookies',
        'notes': 'A no-bake cookie of cocoa, sugar, milk, butter, and peanut butter cooked to fudge stage, then stirred with oats and dropped to set.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-prune-cake': {'action': 'edit', 'patch': {
        'name': 'Prune cake',
        'notes': 'A spiced buttermilk cake folded with cooked pureed prunes and walnuts, often glazed with a buttermilk-soda icing.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-chicken-broccoli-casserole': {'action': 'edit', 'patch': {
        'name': 'Chicken broccoli casserole',
        'notes': 'Cooked chicken and steamed broccoli baked in a mayo, lemon, and cream-of-chicken-soup sauce under a buttered breadcrumb and cheese top.',
        'cuisine': 'American',
    }},
    'corpus-titled-hash-brown-potato-casserole': {'action': 'edit', 'patch': {
        'name': 'Hash brown potato casserole',
        'notes': 'A variant of cheesy hash-brown casserole baked with sour cream, cream of chicken soup, cheese, and a buttery cornflake topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-cobbler': {'action': 'edit', 'patch': {
        'name': 'Fruit cobbler',
        'notes': 'Sweetened fruit baked under a tender biscuit or batter topping — served warm with ice cream.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-ham-loaf': {'action': 'edit', 'patch': {
        'name': 'Ham loaf',
        'notes': 'Ground ham mixed with ground pork, crackers, milk, and egg, baked in a loaf with a sweet brown-sugar mustard glaze — a Pennsylvania Dutch dish.',
        'cuisine': 'American',
    }},
    'corpus-titled-black-bean-soup': {'action': 'edit', 'patch': {
        'name': 'Black bean soup',
        'notes': 'Black beans simmered with onion, garlic, cumin, and broth — sometimes with ham or sausage; often garnished with lime, sour cream, and cilantro.',
        'cuisine': 'Cuban',
    }},
    'corpus-titled-dill-pickles': {'action': 'drop', 'reason': 'pickled condiment, not a coherent meal'},
    'corpus-titled-gingersnaps': {'action': 'edit', 'patch': {
        'name': 'Gingersnaps',
        'tags': ['dessert'],
        'notes': 'Crisp spiced cookies of molasses, butter, and ginger — rolled in sugar and baked until they crackle on top.',
        'serving_grams': 30,
    }},
    'corpus-titled-beer-bread': {'action': 'edit', 'patch': {
        'name': 'Beer bread',
        'notes': 'A quick yeasted-tasting loaf of self-rising flour, sugar, and a bottle of beer — baked with melted butter on top for a crackly crust.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
        'serving_grams': 55,
    }},
    'corpus-titled-texas-sheet-cake': {'action': 'edit', 'patch': {
        'name': 'Texas sheet cake',
        'notes': 'A thin chocolate-buttermilk sheet cake topped warm with a poured cocoa-pecan icing — sliced in squares from the pan.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-cream-puffs': {'action': 'edit', 'patch': {
        'name': 'Cream puffs',
        'tags': ['dessert'],
        'notes': 'A pâte à choux dough piped into mounds, baked into hollow shells, and filled with whipped cream or vanilla custard.',
        'cuisine': 'French',
        'serving_grams': 50,
    }},
    'corpus-titled-harvard-beets': {'action': 'edit', 'patch': {
        'name': 'Harvard beets',
        'notes': 'Sliced cooked beets glazed in a sweet-tart sauce of sugar, vinegar, and cornstarch with a knob of butter.',
        'cuisine': 'American',
    }},
    'corpus-titled-stuffed-green-peppers': {'action': 'edit', 'patch': {
        'name': 'Stuffed green peppers',
        'notes': 'Bell peppers blanched and filled with seasoned ground beef and rice in tomato sauce, baked until tender.',
    }},
    'corpus-titled-death-by-chocolate': {'action': 'edit', 'patch': {
        'name': 'Death by chocolate',
        'ingredient_categories': ['Candy & desserts', 'Prepared mixes', 'Milk', 'Cream & butter', 'Alcoholic beverages'],
        'tags': ['dessert'],
        'notes': 'A layered trifle of crumbled brownies, chocolate pudding (often spiked with Kahlúa), toffee bits, and whipped topping.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-pickled-beets': {'action': 'drop', 'reason': 'pickled side, not a coherent meal'},
    'corpus-titled-wassail': {'action': 'edit', 'patch': {
        'name': 'Wassail',
        'ingredient_categories': ['Juices', 'Coffee & tea', 'Citrus', 'Whole spices', 'Ground spices', 'Sugar & sweeteners'],
        'tags': ['snack'],
        'notes': 'A hot holiday drink of apple cider, orange and lemon juice, and warm spices — slow-simmered; American versions are usually non-alcoholic.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-japanese-fruit-pie': {'action': 'edit', 'patch': {
        'name': 'Japanese fruit pie',
        'notes': 'A Southern pie of eggs, sugar, and butter folded with coconut, raisins, and pecans baked in a single crust — Southern despite the name.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-broccoli-rice-casserole': {'action': 'edit', 'patch': {
        'name': 'Broccoli rice casserole (variant)',
        'notes': 'A cheesy-rice version with broccoli, cream of chicken or mushroom soup, and processed cheese — baked until bubbling.',
        'cuisine': 'American',
    }},
    'corpus-titled-strawberry-delight': {'action': 'edit', 'patch': {
        'name': 'Strawberry delight',
        'tags': ['dessert'],
        'notes': 'A no-bake layered dessert of shortbread crust, sweet cream cheese, strawberry pie filling, and whipped topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-peach-pie': {'action': 'edit', 'patch': {
        'name': 'Peach pie',
        'notes': 'A double-crust pie of sliced ripe peaches tossed with sugar and a thickener, baked until juices bubble and crust browns.',
        'cuisine': 'American',
    }},
    'corpus-titled-cheese-soup': {'action': 'edit', 'patch': {
        'name': 'Cheese soup',
        'notes': 'A creamy soup of diced vegetables and broth thickened with milk-and-roux and finished with Velveeta or processed cheese.',
        'cuisine': 'American',
    }},
    'corpus-titled-cheese-balls': {'action': 'edit', 'patch': {
        'name': 'Cheese ball bites',
        'tags': ['snack'],
        'notes': 'Mini cheese balls of cream cheese and shredded cheese rolled in chopped nuts or herbs — served as appetizers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-parmesan-chicken': {'action': 'edit', 'patch': {
        'name': 'Parmesan-crusted chicken',
        'notes': 'Chicken breasts coated in Parmesan, breadcrumbs, and herbs, then baked or pan-fried until golden — distinct from saucy chicken parmigiana.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-cheese-biscuits': {'action': 'edit', 'patch': {
        'name': 'Cheese biscuits',
        'tags': ['breakfast', 'snack'],
        'notes': 'A buttermilk biscuit dough mixed with sharp cheddar — sometimes brushed with garlic butter (Red Lobster style).',
        'cuisine': 'Southern',
        'serving_grams': 55,
    }},
    'corpus-titled-chicken-curry': {'action': 'edit', 'patch': {
        'name': 'Chicken curry',
        'notes': 'Chicken simmered in a spiced sauce — generic enough to span Indian, Thai, or Anglo-Indian preparations.',
    }},
    'corpus-titled-sour-cream-coffee-cake': {'action': 'edit', 'patch': {
        'name': 'Sour cream coffee cake',
        'tags': ['breakfast', 'dessert'],
        'notes': 'A tender Bundt or square cake enriched with sour cream and swirled with a cinnamon-sugar-pecan streusel.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-soup': {'action': 'edit', 'patch': {
        'name': 'Chicken soup',
        'notes': 'Chicken simmered with carrots, celery, onion, and herbs in broth — the universal stockpot comfort food.',
    }},
    'corpus-titled-wacky-cake': {'action': 'edit', 'patch': {
        'name': 'Wacky cake',
        'notes': 'A Depression-era one-bowl chocolate cake with no eggs, milk, or butter — leavened with baking soda and vinegar, mixed right in the pan.',
        'cuisine': 'American',
    }},
    'corpus-titled-coconut-pound-cake': {'action': 'edit', 'patch': {
        'name': 'Coconut pound cake',
        'notes': 'A dense pound cake folded with shredded coconut and coconut extract, often soaked with a coconut-rum or coconut-milk glaze.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-pralines': {'action': 'edit', 'patch': {
        'name': 'Pralines',
        'tags': ['dessert'],
        'notes': 'A creamy New Orleans confection of pecans simmered in butter, sugar, cream, and vanilla, beaten and dropped to set.',
        'cuisine': 'Creole',
        'serving_grams': 40,
    }},
    'corpus-titled-chicken-tortilla-soup': {'action': 'edit', 'patch': {
        'name': 'Chicken tortilla soup',
        'notes': 'A spiced tomato-chicken broth with shredded chicken, beans, and corn, ladled over crispy tortilla strips and topped with cheese, avocado, and lime.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-shrimp-salad': {'action': 'edit', 'patch': {
        'name': 'Shrimp salad',
        'notes': 'Cooked shrimp tossed with celery, hard-boiled egg, and a lemony mayo dressing — served chilled on greens or in a sandwich.',
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

    print('corpus-titled batch-2 audit applied (entries 151-300 by frequency).')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
