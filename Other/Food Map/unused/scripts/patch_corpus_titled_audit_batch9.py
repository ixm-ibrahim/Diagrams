"""Corpus-titled meals audit — batch 9 (entries 1201-1350 by frequency, 96 -> 87).
Same standard.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

DECISIONS: dict[str, dict] = {
    'corpus-titled-venison-roast': {'action': 'edit', 'patch': {
        'name': 'Venison roast',
        'notes': 'A whole venison roast larded with bacon or covered with strips, slow-roasted with onions, broth, and herbs until tender.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-old-fashioned-sugar-cookies': {'action': 'edit', 'patch': {
        'name': 'Old-fashioned sugar cookies',
        'notes': 'A classic rolled-and-cut sugar cookie of butter, sugar, egg, flour, and vanilla — crisp at the edges, often glazed.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-english-muffins': {'action': 'edit', 'patch': {
        'name': 'English muffins',
        'tags': ['breakfast'],
        'notes': 'Yeasted dough rounds griddled (not baked) until golden, with the signature nooks and crannies — split with a fork and toasted.',
        'cuisine': 'British',
        'serving_grams': 60,
    }},
    'corpus-titled-dilly-bread': {'action': 'edit', 'patch': {
        'name': 'Dilly bread',
        'notes': 'A cottage-cheese yeast bread folded with dill and onion — chewy, savory, and tangy.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-four-layer-dessert': {'action': 'edit', 'patch': {
        'name': 'Four layer dessert',
        'notes': 'A no-bake layered dessert of pecan-shortbread crust, sweetened cream cheese, chocolate or vanilla pudding, and whipped topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-peanut-butter-chocolate-chip-cookies': {'action': 'edit', 'patch': {
        'name': 'Peanut butter chocolate chip cookies',
        'notes': 'Drop cookies of peanut butter, butter, brown sugar, and eggs studded with chocolate chips — softer than classic peanut butter cookies.',
        'cuisine': 'American',
    }},
    'corpus-titled-spritz-cookies': {'action': 'edit', 'patch': {
        'name': 'Spritz cookies',
        'notes': 'A butter-and-egg dough pressed through a cookie press into shapes (wreaths, trees, stars) and baked into crisp Scandinavian holiday cookies.',
        'cuisine': 'Scandinavian',
        'serving_grams': 30,
    }},
    'corpus-titled-cherries-in-the-snow': {'action': 'edit', 'patch': {
        'name': 'Cherries in the snow',
        'tags': ['dessert'],
        'notes': 'A trifle-style dessert of cubed angel food cake folded with sweetened cream cheese, whipped topping, and cherry pie filling.',
        'cuisine': 'American',
    }},
    'corpus-titled-cheese-strata': {'action': 'edit', 'patch': {
        'name': 'Cheese strata',
        'tags': ['breakfast', 'dinner'],
        'notes': 'Bread cubes layered with cheese and ham or sausage, soaked overnight in an egg-and-milk custard, baked into a puffy strata.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-croutons': {'action': 'drop', 'reason': 'salad/soup topping component, not a coherent meal'},
    'corpus-titled-macaroni-cheese': {'action': 'edit', 'patch': {
        'name': 'Macaroni & cheese (variant)',
        'notes': 'Elbow macaroni in a cheddar-bechamel sauce — same as macaroni and cheese.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-eclair-dessert': {'action': 'edit', 'patch': {
        'name': 'Chocolate eclair dessert',
        'notes': 'A no-bake icebox cake of graham crackers layered with vanilla pudding, topped with chocolate frosting — softens to eclair-like texture overnight.',
        'cuisine': 'American',
    }},
    'corpus-titled-banana-nut-muffins': {'action': 'edit', 'patch': {
        'name': 'Banana nut muffins',
        'tags': ['breakfast', 'snack'],
        'notes': 'Tender muffins of mashed banana, eggs, butter, and chopped walnuts or pecans.',
        'serving_grams': 60,
    }},
    'corpus-titled-corned-beef-salad': {'action': 'edit', 'patch': {
        'name': 'Corned beef salad',
        'tags': ['dessert'],
        'notes': 'A molded lemon-gelatin salad set with diced corned beef, hard-boiled egg, celery, and pickles — a retro Southern luncheon dish.',
        'cuisine': 'American',
    }},
    'corpus-titled-fried-apples': {'action': 'edit', 'patch': {
        'name': 'Fried apples',
        'notes': 'Sliced tart apples cooked in butter with cinnamon and brown sugar until tender — a Southern breakfast side served with bacon and grits.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-company-potatoes': {'action': 'edit', 'patch': {
        'name': 'Company potatoes',
        'notes': 'Frozen hash browns baked with sour cream, butter, cream of chicken soup, and shredded cheese under a cornflake topping — funeral potatoes variant.',
        'cuisine': 'American',
    }},
    'corpus-titled-collard-greens': {'action': 'edit', 'patch': {
        'name': 'Collard greens',
        'notes': 'Tough leafy collards slow-cooked for an hour or more with smoked pork (ham hock, bacon, or fatback) and a touch of vinegar.',
        'cuisine': 'Southern',
        'contains_add': ['pork'],
    }},
    'corpus-titled-pecan-puffs': {'action': 'edit', 'patch': {
        'name': 'Pecan puffs (snowballs)',
        'tags': ['dessert'],
        'notes': 'A butter-and-powdered-sugar shortbread folded with finely chopped pecans, baked into balls and rolled in powdered sugar — Russian-tea-cake family.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-drop-sugar-cookies': {'action': 'edit', 'patch': {
        'name': 'Drop sugar cookies',
        'notes': 'A soft, cake-like sugar cookie dropped from a spoon (no rolling and cutting) — often glazed with a powdered-sugar icing.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-cauliflower-casserole': {'action': 'edit', 'patch': {
        'name': 'Cauliflower casserole',
        'notes': 'Cauliflower florets baked in a cheese-and-cream sauce under a buttered cracker topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-s-mores': {'action': 'edit', 'patch': {
        'name': "S'mores",
        'tags': ['dessert', 'snack'],
        'notes': 'Toasted marshmallow and a square of chocolate sandwiched between two graham crackers — the campfire dessert.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-beet-pickles': {'action': 'drop', 'reason': 'pickled condiment, not a coherent meal'},
    'corpus-titled-chicken-fricassee': {'action': 'edit', 'patch': {
        'name': 'Chicken fricassee',
        'notes': 'Chicken pieces lightly browned, then braised in a white-wine-and-cream sauce with mushrooms, onions, and herbs.',
        'cuisine': 'French',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-green-tomato-pie': {'action': 'edit', 'patch': {
        'name': 'Green tomato pie',
        'notes': 'A double-crust pie of sliced unripe green tomatoes tossed with sugar, vinegar, and spices — eats like a mock apple pie.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-blackberry-jam-cake': {'action': 'edit', 'patch': {
        'name': 'Blackberry jam cake',
        'notes': 'A spiced buttermilk layer cake with blackberry jam folded into the batter, often frosted with caramel icing — Appalachian classic.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-cherry-pudding': {'action': 'edit', 'patch': {
        'name': 'Cherry pudding cake',
        'notes': 'A self-saucing pudding cake — batter spread with cherries, topped with sugar and boiling water, baked so the cake rises while a cherry sauce sinks beneath.',
        'cuisine': 'American',
    }},
    'corpus-titled-enchilada-sauce': {'action': 'drop', 'reason': 'sauce component, not a coherent meal'},
    'corpus-titled-yogurt-pie': {'action': 'edit', 'patch': {
        'name': 'Yogurt pie',
        'notes': 'A no-bake pie of flavored yogurt folded with whipped topping, poured into a graham crust and chilled until set.',
        'cuisine': 'American',
    }},
    'corpus-titled-sausage-dip': {'action': 'edit', 'patch': {
        'name': 'Sausage dip',
        'tags': ['snack'],
        'notes': 'Browned breakfast sausage simmered with Velveeta and Rotel tomatoes — served warm with tortilla chips.',
        'cuisine': 'American',
        'contains_add': ['pork'],
        'serving_grams': 60,
    }},
    'corpus-titled-never-fail-fudge': {'action': 'edit', 'patch': {
        'name': 'Never fail fudge',
        'notes': 'A foolproof fudge of evaporated milk, sugar, butter, chocolate chips, and marshmallow creme — same family as million dollar fudge.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-lace-cookies': {'action': 'edit', 'patch': {
        'name': 'Lace cookies',
        'notes': 'A thin, crisp drop cookie of butter, sugar, oats (or almonds), and a touch of flour — spreads to a lacy net as it bakes.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-fried-corn': {'action': 'edit', 'patch': {
        'name': 'Fried corn',
        'notes': 'Fresh corn kernels sautéed with butter and bacon, finished with cream and a touch of sugar — a Southern summer side.',
        'cuisine': 'Southern',
        'contains_add': ['pork'],
    }},
    'corpus-titled-apple-pudding': {'action': 'edit', 'patch': {
        'name': 'Apple pudding cake',
        'notes': 'A spiced apple batter baked in a pan and served warm with a butter-sugar sauce — a homey one-pan dessert.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-cupcakes': {'action': 'edit', 'patch': {
        'name': 'Chocolate cupcakes',
        'notes': 'Individual cocoa cakes baked in muffin tins, frosted with chocolate buttercream or ganache.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-banana-oatmeal-cookies': {'action': 'edit', 'patch': {
        'name': 'Banana oatmeal cookies',
        'notes': 'Drop cookies of mashed banana, oats, brown sugar, butter, and warm spices — chewy and naturally sweet.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-potato-rolls': {'action': 'edit', 'patch': {
        'name': 'Potato rolls',
        'tags': ['dinner', 'lunch'],
        'notes': 'Soft yeasted dinner rolls enriched with mashed potato — extra tender, slightly sweet, with a long shelf life.',
        'cuisine': 'American',
        'serving_grams': 50,
    }},
    'corpus-titled-pork-roast': {'action': 'edit', 'patch': {
        'name': 'Pork roast',
        'notes': 'A pork loin, shoulder, or rib roast seasoned with garlic, herbs, and brown sugar, oven-roasted until the crust is glazed and the meat tender.',
        'cuisine': 'American',
    }},
    'corpus-titled-bagels': {'action': 'edit', 'patch': {
        'name': 'Bagels',
        'tags': ['breakfast'],
        'notes': 'Ring-shaped yeasted breads briefly boiled in malted water, then baked — chewy interior, glossy crust; the New York Jewish staple.',
        'cuisine': 'Jewish',
        'serving_grams': 100,
    }},
    'corpus-titled-cranberry-mold': {'action': 'edit', 'patch': {
        'name': 'Cranberry mold',
        'tags': ['dessert'],
        'notes': 'A molded cranberry-gelatin salad set with whole-berry cranberry sauce, crushed pineapple, oranges, celery, and chopped nuts.',
        'cuisine': 'American',
    }},
    'corpus-titled-vidalia-onion-pie': {'action': 'edit', 'patch': {
        'name': 'Vidalia onion pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'Sliced sweet Vidalia onions sautéed in butter, layered in a pastry crust, and baked under an egg-and-cheese custard.',
        'cuisine': 'Southern',
        'serving_grams': 200,
    }},
    'corpus-titled-molasses-cake': {'action': 'edit', 'patch': {
        'name': 'Molasses cake',
        'notes': 'A dark spiced butter or oil cake leavened with baking soda and sweetened heavily with molasses — moist and gingerbread-like.',
        'cuisine': 'American',
    }},
    'corpus-titled-cucumber-pickles': {'action': 'drop', 'reason': 'pickled condiment, not a coherent meal'},
    'corpus-titled-greek-pasta-salad': {'action': 'edit', 'patch': {
        'name': 'Greek pasta salad',
        'notes': 'Cooked pasta tossed with cucumber, tomato, red onion, olives, feta, and oregano in a lemon-olive-oil dressing.',
        'cuisine': 'Greek',
    }},
    'corpus-titled-fruitcake-cookies': {'action': 'edit', 'patch': {
        'name': 'Fruitcake cookies (variant)',
        'notes': 'Drop cookies of candied fruit, dates, raisins, and pecans bound by a buttermilk-and-bourbon-style spiced batter — fruitcake flavor in cookie form.',
        'cuisine': 'Southern',
        'serving_grams': 30,
    }},
    'corpus-titled-chocolate-chip-muffins': {'action': 'edit', 'patch': {
        'name': 'Chocolate chip muffins',
        'tags': ['breakfast', 'snack'],
        'notes': 'Tender muffins of butter, sugar, eggs, and milk folded with chocolate chips — a sweeter morning treat.',
        'cuisine': 'American',
    }},
    'corpus-titled-sourdough-biscuits': {'action': 'edit', 'patch': {
        'name': 'Sourdough biscuits',
        'tags': ['breakfast', 'dinner'],
        'notes': 'A biscuit dough leavened in part by sourdough starter discard — tangy crumb with a flaky baking-powder lift.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-pickled-peaches': {'action': 'drop', 'reason': 'pickled / preserve, not a coherent meal'},
    'corpus-titled-poor-man-s-steak': {'action': 'edit', 'patch': {
        'name': "Poor man's steak",
        'notes': 'Ground beef mixed with crushed crackers, milk, and seasonings, chilled, sliced like steak, browned, and baked in cream of mushroom soup.',
        'cuisine': 'American',
    }},
    'corpus-titled-porcupine-balls': {'action': 'edit', 'patch': {
        'name': 'Porcupine meatballs (variant)',
        'notes': 'Ground beef and uncooked rice meatballs simmered in tomato sauce — the rice grains poke out as they cook.',
        'cuisine': 'American',
    }},
    'corpus-titled-broccoli-souffle': {'action': 'edit', 'patch': {
        'name': 'Broccoli soufflé',
        'notes': 'Chopped broccoli folded into a cheese bechamel base, lightened with beaten egg whites, and baked until puffed.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-dijon': {'action': 'edit', 'patch': {
        'name': 'Chicken Dijon',
        'notes': 'Pan-seared chicken breasts finished in a cream-and-Dijon-mustard sauce with herbs — French bistro style.',
        'cuisine': 'French',
    }},
    'corpus-titled-cinnamon-buns': {'action': 'edit', 'patch': {
        'name': 'Cinnamon buns',
        'tags': ['breakfast', 'dessert'],
        'notes': 'Yeasted dough rolled around cinnamon-butter-sugar, sliced into pinwheels, baked, and drizzled with a powdered-sugar or cream-cheese glaze.',
        'cuisine': 'American',
        'serving_grams': 90,
    }},
    'corpus-titled-rice-krispies-treats': {'action': 'edit', 'patch': {
        'name': 'Rice Krispies treats',
        'tags': ['dessert', 'snack'],
        'notes': 'Rice Krispies cereal stirred into melted butter and marshmallows, pressed into a pan, cooled, and cut into squares.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-fruit-salad-dressing': {'action': 'edit', 'patch': {
        'name': 'Fruit salad dressing (cooked)',
        'tags': ['condiment'],
        'notes': 'A cooked dressing of pineapple juice, egg, sugar, and butter (sometimes lemon) cooled and folded with whipped cream — for ambrosia-style fruit salads.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-candy-cane-cookies': {'action': 'edit', 'patch': {
        'name': 'Candy cane cookies',
        'notes': 'A butter-and-powdered-sugar dough divided in two, one half tinted red and peppermint-flavored, twisted into candy-cane shapes and baked.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-caramel-cake': {'action': 'edit', 'patch': {
        'name': 'Caramel cake',
        'notes': 'A yellow butter layer cake frosted with a poured-and-set caramel icing made by cooking sugar to a dark amber and beating in cream and butter.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-pumpkin-pancakes': {'action': 'edit', 'patch': {
        'name': 'Pumpkin pancakes',
        'notes': 'Buttermilk pancake batter folded with pumpkin puree and warm spices — served with maple syrup or cinnamon-butter.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-creamy-chicken-enchiladas': {'action': 'edit', 'patch': {
        'name': 'Creamy chicken enchiladas',
        'notes': 'Tortillas rolled around shredded chicken and cheese, baked in a sour-cream-and-green-chile bechamel sauce topped with more cheese.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-black-beans-and-rice': {'action': 'edit', 'patch': {
        'name': 'Black beans and rice',
        'notes': 'Black beans simmered with peppers, onions, garlic, and cumin, served over white rice — a Cuban-style "Moros y Cristianos" weeknight base.',
        'cuisine': 'Cuban',
    }},
    'corpus-titled-spice-tea': {'action': 'edit', 'patch': {
        'name': 'Spice tea',
        'ingredient_categories': ['Coffee & tea', 'Juices', 'Citrus', 'Sugar & sweeteners', 'Whole spices', 'Ground spices'],
        'tags': ['snack'],
        'notes': 'Black tea simmered with orange juice, cinnamon sticks, and cloves — sweetened and served hot; same family as Russian tea.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-no-bake-chocolate-cookies': {'action': 'edit', 'patch': {
        'name': 'No-bake chocolate cookies',
        'notes': 'Cocoa, sugar, milk, and butter boiled to a fudge, then stirred with peanut butter and oats and dropped onto wax paper to set.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-oven-fried-potatoes': {'action': 'edit', 'patch': {
        'name': 'Oven-fried potatoes',
        'notes': 'Wedges or slices of potato tossed in oil and seasonings, then baked at high heat until crisp outside and tender inside.',
    }},
    'corpus-titled-layered-taco-dip': {'action': 'edit', 'patch': {
        'name': 'Layered taco dip',
        'tags': ['snack'],
        'notes': 'A cold layered dip of refried beans or seasoned sour cream, salsa, cheese, lettuce, and olives — served with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-sour-cream-coconut-cake': {'action': 'edit', 'patch': {
        'name': 'Sour cream coconut cake',
        'notes': 'A layered yellow cake split horizontally and saturated with a sour-cream-sugar-coconut mixture, then refrigerated for several days to mellow.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-cherry-cake': {'action': 'edit', 'patch': {
        'name': 'Cherry cake',
        'notes': 'A butter cake studded with maraschino or fresh cherries, often topped with a cherry or vanilla glaze.',
        'cuisine': 'American',
    }},
    'corpus-titled-zucchini-lasagna': {'action': 'edit', 'patch': {
        'name': 'Zucchini lasagna',
        'notes': 'Strips of zucchini in place of pasta sheets, layered with ricotta, mozzarella, marinara, and ground beef — a low-carb lasagna variant.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-pineapple-pound-cake': {'action': 'edit', 'patch': {
        'name': 'Pineapple pound cake',
        'notes': 'A dense pound cake with crushed pineapple and its juice folded into the batter, often glazed with a pineapple-sugar syrup.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-chewy-chocolate-cookies': {'action': 'edit', 'patch': {
        'name': 'Chewy chocolate cookies',
        'notes': 'Cocoa drop cookies of butter, eggs, brown sugar, and a little flour — baked just until the centers set for a chewy texture.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-rhubarb-bread': {'action': 'edit', 'patch': {
        'name': 'Rhubarb bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A spiced quick bread folded with chopped rhubarb, often topped with a brown-sugar-cinnamon streusel.',
        'cuisine': 'American',
        'serving_grams': 90,
    }},
    'corpus-titled-english-pea-salad': {'action': 'edit', 'patch': {
        'name': 'English pea salad',
        'notes': 'Sweet green peas tossed with hard-boiled eggs, cheddar, sweet pickles, and a mayo-based dressing — a Southern picnic side.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-pecan-balls': {'action': 'edit', 'patch': {
        'name': 'Pecan balls',
        'tags': ['dessert'],
        'notes': 'A butter-and-powdered-sugar shortbread folded with finely chopped pecans, baked into balls and rolled in powdered sugar — same family as pecan puffs.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-raspberry-salad': {'action': 'edit', 'patch': {
        'name': 'Raspberry Jello salad',
        'tags': ['dessert'],
        'notes': 'Raspberry gelatin set with frozen raspberries and crushed pineapple, layered with sour cream — a chilled Southern dessert salad.',
        'cuisine': 'American',
    }},
    'corpus-titled-snack-mix': {'action': 'edit', 'patch': {
        'name': 'Snack mix (Chex)',
        'notes': 'Chex cereals, pretzels, and mixed nuts coated in a buttery Worcestershire-and-seasoning blend, baked until crisp — Chex party mix family.',
        'cuisine': 'American',
    }},
    'corpus-titled-cream-of-tomato-soup': {'action': 'edit', 'patch': {
        'name': 'Cream of tomato soup',
        'notes': 'Tomatoes simmered with onion, butter, and herbs, blended smooth and enriched with milk and cream — often paired with grilled cheese.',
        'cuisine': 'American',
    }},
    'corpus-titled-brownie-pie': {'action': 'edit', 'patch': {
        'name': 'Brownie pie',
        'notes': 'A pecan-pie-style filling of eggs, butter, sugar, and flour, packed with chocolate chips and walnuts — like a gooey brownie in a pie shell.',
        'cuisine': 'American',
    }},
    'corpus-titled-zucchini-muffins': {'action': 'edit', 'patch': {
        'name': 'Zucchini muffins',
        'tags': ['breakfast', 'snack'],
        'notes': 'Spiced muffins of grated zucchini, eggs, oil, and walnuts — moist with a tender crumb.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-reuben-dip': {'action': 'edit', 'patch': {
        'name': 'Reuben dip',
        'tags': ['snack'],
        'notes': 'Cream cheese, sour cream, Swiss cheese, sauerkraut, and corned beef baked until bubbly — Reuben sandwich flavors as a hot dip.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-chili-rellenos': {'action': 'edit', 'patch': {
        'name': 'Chiles rellenos',
        'notes': 'Roasted poblano chiles stuffed with cheese, dipped in an egg-white batter, and fried golden — served in tomato sauce.',
        'cuisine': 'Mexican',
    }},
    'corpus-titled-chicken-lasagna': {'action': 'edit', 'patch': {
        'name': 'Chicken lasagna',
        'notes': 'Layered lasagna noodles with shredded chicken, ricotta, mozzarella, mushrooms, and either a tomato or alfredo sauce.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-stuffed-potatoes': {'action': 'edit', 'patch': {
        'name': 'Stuffed potatoes',
        'notes': 'Baked russet potatoes split, scooped, mashed with butter, sour cream, cheese, and bacon, returned to the shells and baked again — twice-baked potatoes.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-chocolate-peanut-butter-pie': {'action': 'edit', 'patch': {
        'name': 'Chocolate peanut butter pie',
        'notes': 'A no-bake pie of peanut butter whipped with cream cheese and folded into whipped topping, layered with chocolate pudding in an Oreo crust.',
        'cuisine': 'American',
    }},
    'corpus-titled-cream-cheese-cake': {'action': 'edit', 'patch': {
        'name': 'Cream cheese cake',
        'notes': 'A baked cream-cheese cheesecake — same family as classic cheesecake but sometimes folded with whipped cream for lightness.',
        'cuisine': 'American',
    }},
    'corpus-titled-pumpkin-cake-roll': {'action': 'edit', 'patch': {
        'name': 'Pumpkin cake roll',
        'tags': ['dessert'],
        'notes': 'A thin pumpkin sponge cake baked on a sheet pan, rolled while warm with a tea-towel, then unrolled, spread with cream cheese filling, and re-rolled.',
        'cuisine': 'American',
    }},
    'corpus-titled-party-meatballs': {'action': 'edit', 'patch': {
        'name': 'Party meatballs',
        'tags': ['snack'],
        'notes': 'Pan-fried meatballs simmered in a sauce of grape jelly and chili sauce — held warm in a slow cooker for cocktail parties.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-seven-up-cake': {'action': 'edit', 'patch': {
        'name': '7-Up cake (variant)',
        'ingredient_categories': ['Eggs', 'Citrus', 'Sugar & sweeteners', 'Flours', 'Tropical fruits', 'Oils', 'Soft drinks'],
        'notes': 'A citrus pound cake made with a bottle of 7-Up, sometimes glazed with pineapple-coconut topping — Southern dessert.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-porcupines': {'action': 'edit', 'patch': {
        'name': 'Porcupine meatballs',
        'notes': 'Ground beef and uncooked rice meatballs simmered in tomato sauce — the rice grains poke out as they cook, giving the "porcupine" look.',
        'cuisine': 'American',
    }},
    'corpus-titled-margarita': {'action': 'edit', 'patch': {
        'name': 'Margarita',
        'notes': 'Tequila, lime juice, and triple sec (or Cointreau) shaken with ice and served in a salt-rimmed glass — Mexico\'s most-exported cocktail.',
        'cuisine': 'Mexican',
        'contains_add': ['alcohol'],
        'serving_grams': 100,
    }},
    'corpus-titled-scottish-shortbread': {'action': 'edit', 'patch': {
        'name': 'Scottish shortbread',
        'tags': ['dessert'],
        'notes': 'A traditional Scottish biscuit of just butter, sugar, and flour in a 1:2:3 ratio — pressed flat, pricked, baked low, and cut into wedges.',
        'cuisine': 'British',
        'serving_grams': 30,
    }},
    'corpus-titled-london-broil': {'action': 'edit', 'patch': {
        'name': 'London broil',
        'notes': 'A flank or top-round steak marinated in soy, garlic, and Worcestershire, broiled hot, and sliced thin across the grain.',
        'cuisine': 'American',
    }},
    'corpus-titled-taco-pizza': {'action': 'edit', 'patch': {
        'name': 'Taco pizza',
        'notes': 'A crescent-roll or pizza-dough crust spread with refried beans or seasoned beef, baked, then topped cold with lettuce, tomato, cheese, and salsa.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-potato-cakes': {'action': 'edit', 'patch': {
        'name': 'Potato cakes',
        'tags': ['dinner', 'lunch', 'breakfast'],
        'notes': 'Leftover mashed potatoes mixed with egg, onion, and flour, formed into patties and pan-fried until golden — a thrifty leftover dish.',
        'cuisine': 'American',
        'serving_grams': 120,
    }},
    'corpus-titled-peanut-butter-bread': {'action': 'edit', 'patch': {
        'name': 'Peanut butter bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A simple quick bread with peanut butter creamed into the butter-sugar base — tender and lightly nutty.',
        'cuisine': 'American',
    }},
    'corpus-titled-golden-punch': {'action': 'edit', 'patch': {
        'name': 'Golden punch',
        'ingredient_categories': ['Juices', 'Citrus', 'Tropical fruits', 'Sugar & sweeteners', 'Soft drinks'],
        'tags': ['snack'],
        'notes': 'A non-alcoholic punch of pineapple juice, orange juice, lemon juice, sugar, and ginger ale — golden and sparkling.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-chicken-teriyaki': {'action': 'edit', 'patch': {
        'name': 'Chicken teriyaki',
        'notes': 'Chicken pieces marinated or glazed in a soy-mirin-sugar sauce, then grilled or pan-cooked until lacquered — served over rice.',
        'cuisine': 'Japanese',
    }},
    'corpus-titled-italian-vegetable-soup': {'action': 'edit', 'patch': {
        'name': 'Italian vegetable soup',
        'notes': 'A minestrone-style soup of mixed vegetables, beans, pasta, and ground beef simmered in a tomato-and-broth base with Italian herbs.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-lemon-pudding-cake': {'action': 'edit', 'patch': {
        'name': 'Lemon pudding cake',
        'notes': 'A self-saucing cake — batter separates as it bakes into a tender cake top over a tart lemon-curd pudding bottom.',
        'cuisine': 'American',
    }},
    'corpus-titled-pretzels': {'action': 'edit', 'patch': {
        'name': 'Soft pretzels (homemade)',
        'notes': 'Yeasted dough shaped into pretzels, briefly dipped in a baking-soda bath, salted, and baked until deep brown and chewy.',
        'cuisine': 'German-American',
        'serving_grams': 100,
    }},
    'corpus-titled-sad-cake': {'action': 'edit', 'patch': {
        'name': 'Sad cake',
        'notes': 'A simple bar dessert with brown sugar, eggs, oil, vanilla, coconut, and pecans baked in a Bundt or sheet pan — sinks and "looks sad" but tastes rich.',
        'cuisine': 'American',
    }},
    'corpus-titled-chow-mein': {'action': 'edit', 'patch': {
        'name': 'Chow mein',
        'notes': 'Stir-fried noodles tossed with vegetables, soy sauce, and chicken, pork, or beef — Chinese-American restaurant style.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-yeast-bread': {'action': 'edit', 'patch': {
        'name': 'Yeast bread',
        'notes': 'A basic enriched yeasted sandwich loaf of flour, milk, sugar, butter, and eggs — soft crumb, golden crust.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-fruitcake': {'action': 'edit', 'patch': {
        'name': 'Fruitcake (holiday)',
        'tags': ['dessert'],
        'notes': 'A dense holiday cake packed with candied fruit, dried fruit, nuts, and warm spices — often soaked in brandy or bourbon and aged.',
    }},
    'corpus-titled-chinese-fried-rice': {'action': 'edit', 'patch': {
        'name': 'Chinese fried rice',
        'notes': 'Day-old cold rice stir-fried in a hot wok with eggs, scallions, peas and carrots, soy sauce, and often diced pork or shrimp.',
        'cuisine': 'Chinese-American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-pinwheels': {'action': 'edit', 'patch': {
        'name': 'Tortilla pinwheels',
        'tags': ['snack'],
        'notes': 'Tortillas spread with herbed cream cheese, peppers, and olives, rolled and sliced into pinwheel rounds — a chilled appetizer.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-green-tomato-pickles': {'action': 'drop', 'reason': 'pickled condiment, not a coherent meal'},
    'corpus-titled-spiced-tea-mix': {'action': 'edit', 'patch': {
        'name': 'Spiced tea mix',
        'ingredient_categories': ['Coffee & tea', 'Juices', 'Sugar & sweeteners', 'Whole spices', 'Ground spices', 'Citrus'],
        'tags': ['snack'],
        'notes': 'A pantry mix of instant tea, powdered Tang, sugar, and warm spices — stirred into hot water; non-alcoholic.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-popsicles': {'action': 'edit', 'patch': {
        'name': 'Popsicles',
        'tags': ['snack', 'dessert'],
        'notes': 'Sweetened fruit juice or pudding frozen in molds with sticks — a kids\' summer treat.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-potato-dumplings': {'action': 'edit', 'patch': {
        'name': 'Potato dumplings',
        'notes': 'Mashed or grated potato bound with egg, flour, and breadcrumbs, formed into balls and boiled — German Kartoffelknödel, served with roast meats.',
        'cuisine': 'German',
    }},
    'corpus-titled-candied-pecans': {'action': 'edit', 'patch': {
        'name': 'Candied pecans',
        'tags': ['snack'],
        'notes': 'Pecans tossed in an egg-white-and-sugar slurry with cinnamon and salt, baked slowly until crisp.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-cheese-danish': {'action': 'edit', 'patch': {
        'name': 'Cheese Danish',
        'notes': 'Sweet enriched dough wrapped around a sweetened cream-cheese filling and baked, finished with a powdered-sugar glaze.',
        'cuisine': 'Danish',
        'serving_grams': 80,
    }},
    'corpus-titled-s-meat-loaf': {'action': 'edit', 'patch': {
        'name': 'Saucy meatloaf',
        'notes': 'A ground-beef loaf bound with crumbs, milk, and egg, glazed with a sweet ketchup-brown-sugar-mustard sauce, and baked.',
        'cuisine': 'American',
    }},
    'corpus-titled-italian-spaghetti-sauce': {'action': 'edit', 'patch': {
        'name': 'Italian spaghetti sauce',
        'notes': 'A long-simmered tomato sauce with ground beef or Italian sausage, onions, garlic, mushrooms, and Italian herbs — served over spaghetti.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-cocoa-mix': {'action': 'edit', 'patch': {
        'name': 'Hot cocoa mix (pantry)',
        'ingredient_categories': ['Sugar & sweeteners', 'Milk', 'Candy & desserts'],
        'tags': ['snack'],
        'notes': 'A dry pantry mix of powdered milk, cocoa, sugar, and powdered creamer — stirred into hot water for instant cocoa.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-pumpkin-chocolate-chip-cookies': {'action': 'edit', 'patch': {
        'name': 'Pumpkin chocolate chip cookies',
        'notes': 'Soft cake-like drop cookies of pumpkin puree, butter, and warm spices folded with chocolate chips.',
        'cuisine': 'American',
    }},
    'corpus-titled-stuffed-baked-potatoes': {'action': 'edit', 'patch': {
        'name': 'Stuffed baked potatoes (variant)',
        'notes': 'Baked russets split, scooped, mashed with butter, sour cream, cheese, and herbs, returned to the shell and baked again — twice-baked potatoes.',
        'cuisine': 'American',
    }},
    'corpus-titled-oreo-cookie-cake': {'action': 'edit', 'patch': {
        'name': 'Oreo cookie cake',
        'notes': 'A no-bake icebox cake of crushed Oreos layered with sweetened cream cheese and chocolate pudding, topped with whipped topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-potato-latkes': {'action': 'edit', 'patch': {
        'name': 'Potato latkes',
        'notes': 'Grated potato and onion mixed with egg, salt, and a little flour, pan-fried into crisp pancakes — Ashkenazi Jewish Hanukkah staple.',
        'cuisine': 'Jewish',
        'serving_grams': 120,
    }},
    'corpus-titled-blondies': {'action': 'edit', 'patch': {
        'name': 'Blondies (variant)',
        'tags': ['dessert'],
        'notes': 'Brown-sugar-and-butter bars in the shape of brownies but with vanilla in place of chocolate — sometimes with butterscotch or chocolate chips.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-hobo-dinner': {'action': 'edit', 'patch': {
        'name': 'Hobo dinner (foil packets)',
        'notes': 'Ground beef patties, sliced potatoes, carrots, and onions sealed in foil packets and baked or grilled — a campfire-or-oven one-packet meal.',
        'cuisine': 'American',
    }},
    'corpus-titled-salami': {'action': 'edit', 'patch': {
        'name': 'Homemade salami',
        'tags': ['snack'],
        'notes': 'Ground beef mixed with Morton Tender Quick cure, seasonings, garlic, and liquid smoke, shaped into logs and slow-baked — a homemade summer-sausage-style salami.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-veggie-dip': {'action': 'edit', 'patch': {
        'name': 'Veggie dip',
        'tags': ['snack'],
        'notes': 'Sour cream and mayo seasoned with dried dill, parsley, onion, and Beau Monde or ranch mix — served chilled with raw vegetables.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-orange-delight': {'action': 'edit', 'patch': {
        'name': 'Orange delight',
        'tags': ['dessert'],
        'notes': 'Orange Jello set with mandarin oranges, crushed pineapple, and sweetened cream cheese — a Southern molded dessert salad.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-impossible-quiche': {'action': 'edit', 'patch': {
        'name': 'Impossible quiche',
        'notes': 'A blender custard of eggs, milk, Bisquick, cheese, and ham or sausage — self-crusts as it bakes; no pastry shell needed.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-coconut-balls': {'action': 'edit', 'patch': {
        'name': 'Coconut balls',
        'tags': ['dessert'],
        'notes': 'Sweetened coconut mixed with butter, sweetened condensed milk, and pecans, rolled into balls and dipped in melted chocolate — Martha Washington-style.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-ham-salad': {'action': 'edit', 'patch': {
        'name': 'Ham salad',
        'notes': 'Ground or finely chopped cooked ham bound with mayo, sweet pickle relish, mustard, and chopped egg — served as a sandwich filling or with crackers.',
        'cuisine': 'American',
    }},
    'corpus-titled-sour-cream-biscuits': {'action': 'edit', 'patch': {
        'name': 'Sour cream biscuits',
        'tags': ['breakfast', 'dinner'],
        'notes': 'A drop biscuit made tangy and tender by sour cream stirred into butter and self-rising flour — no rolling required.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-sauerkraut-balls': {'action': 'edit', 'patch': {
        'name': 'Sauerkraut balls',
        'tags': ['snack'],
        'notes': 'Sausage, sauerkraut, and cream cheese mixed and chilled, formed into balls, breaded, and fried — an Ohio cocktail-party appetizer.',
        'cuisine': 'German-American',
        'contains_add': ['pork'],
        'serving_grams': 80,
    }},
    'corpus-titled-fruit-slush': {'action': 'edit', 'patch': {
        'name': 'Fruit slush',
        'tags': ['snack', 'dessert'],
        'notes': 'Crushed fruit and juices sweetened and frozen in a container, then scooped slushy into glasses — sometimes topped with lemon-lime soda.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-baked-potatoes': {'action': 'edit', 'patch': {
        'name': 'Baked potatoes',
        'notes': 'Whole russet potatoes baked in their skins at high heat until tender, split open and topped with butter, sour cream, chives, and cheese.',
        'cuisine': 'American',
    }},
    'corpus-titled-sandwich-spread': {'action': 'edit', 'patch': {
        'name': 'Sweet sandwich spread',
        'tags': ['condiment'],
        'notes': 'A cooked sweet-tart spread of ground vegetables (cucumber, peppers, onion) bound with a flour-and-egg mayonnaise — spread on bread for "ladies\' lunch" sandwiches.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-mexican-wedding-cakes': {'action': 'edit', 'patch': {
        'name': 'Mexican wedding cakes (variant)',
        'notes': 'A butter shortbread folded with finely ground nuts (almonds or pecans), baked into balls and rolled in powdered sugar — same family as Russian tea cakes.',
        'cuisine': 'Mexican',
        'serving_grams': 30,
    }},
    'corpus-titled-sausage-breakfast-casserole': {'action': 'edit', 'patch': {
        'name': 'Sausage breakfast casserole',
        'notes': 'Browned breakfast sausage layered with bread, eggs, milk, and shredded cheese — assembled overnight and baked in the morning.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-oatmeal-crispies': {'action': 'edit', 'patch': {
        'name': 'Oatmeal crispies',
        'tags': ['dessert'],
        'notes': 'Thin crisp drop cookies of butter, brown sugar, oats, and chopped nuts — like an oatmeal cookie pressed flat.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-crab-bisque': {'action': 'edit', 'patch': {
        'name': 'Crab bisque',
        'notes': 'A rich seafood-broth-and-cream soup with lump crab, sherry, and aromatics, thickened with a buttery roux.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-french-toast-casserole': {'action': 'edit', 'patch': {
        'name': 'French toast casserole',
        'notes': 'Cubed bread soaked overnight in an egg-cream-cinnamon custard, then baked into a strata-style breakfast — sometimes with a streusel topping.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-yum-yum-salad': {'action': 'edit', 'patch': {
        'name': 'Yum yum salad',
        'tags': ['dessert'],
        'notes': 'A molded orange-gelatin salad set with crushed pineapple, shredded cheese, and whipped topping — a Southern church-supper dish.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-s-pound-cake': {'action': 'edit', 'patch': {
        'name': 'Sour cream pound cake',
        'notes': 'A dense pound cake enriched with sour cream — tender, fine-crumbed, and slightly tangy.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-mincemeat': {'action': 'edit', 'patch': {
        'name': 'Mincemeat',
        'tags': ['dessert'],
        'notes': 'A spiced preserve of chopped beef (or suet), apples, dried fruit, citrus, brandy or rum, and warm spices — used as pie filling at the holidays.',
        'cuisine': 'British',
        'contains_add': ['alcohol'],
        'serving_grams': 80,
    }},
    'corpus-titled-zucchini-cookies': {'action': 'edit', 'patch': {
        'name': 'Zucchini cookies',
        'notes': 'Soft drop cookies of grated zucchini, butter, brown sugar, oats or raisins, and warm spices.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-hot-cocoa': {'action': 'edit', 'patch': {
        'name': 'Hot cocoa',
        'notes': 'Cocoa, sugar, milk, and a pinch of salt heated until steaming — the from-scratch version of hot chocolate.',
        'serving_grams': 240,
    }},
    'corpus-titled-mud-pie': {'action': 'edit', 'patch': {
        'name': 'Mud pie',
        'notes': 'Softened coffee or chocolate ice cream spread into a chocolate-cookie crust, frozen, then topped with fudge sauce and whipped cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-chili-mac': {'action': 'edit', 'patch': {
        'name': 'Chili mac',
        'notes': 'Cooked elbow macaroni mixed with chili (ground beef, beans, tomatoes, chili spices), often topped with shredded cheese — quick weeknight comfort.',
        'cuisine': 'American',
    }},
    'corpus-titled-onion-roasted-potatoes': {'action': 'edit', 'patch': {
        'name': 'Onion-roasted potatoes',
        'notes': 'Potato chunks tossed with a packet of onion soup mix and oil, roasted hot until crisp and golden — Lipton recipe-card classic.',
        'cuisine': 'American',
    }},
    'corpus-titled-friendship-cake': {'action': 'edit', 'patch': {
        'name': 'Friendship cake',
        'notes': 'A cake baked using a "friendship starter" of brandy-soaked fermenting fruit passed between bakers — the fruit is folded into cake-mix batter with pecans.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-pineapple-sheet-cake': {'action': 'edit', 'patch': {
        'name': 'Pineapple sheet cake',
        'notes': 'A one-bowl sheet cake folded with crushed pineapple and its juice, often topped with cream cheese frosting.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-hot-clam-dip': {'action': 'edit', 'patch': {
        'name': 'Hot clam dip',
        'tags': ['snack'],
        'notes': 'Cream cheese and butter melted with minced clams, lemon, and Worcestershire, baked until bubbly — served warm with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-cherry-chocolate-cake': {'action': 'edit', 'patch': {
        'name': 'Cherry chocolate cake (dump)',
        'notes': 'A chocolate cake mix combined with canned cherry pie filling and eggs (no oil or water), baked and topped with chocolate fudge frosting.',
        'cuisine': 'American',
    }},
    'corpus-titled-mandarin-salad': {'action': 'edit', 'patch': {
        'name': 'Mandarin salad',
        'notes': 'Romaine and red leaf lettuce tossed with mandarin oranges, sugared almonds, scallions, and a sweet vinaigrette.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-green-enchiladas': {'action': 'edit', 'patch': {
        'name': 'Green enchiladas',
        'notes': 'Corn tortillas rolled around shredded chicken and cheese, baked in salsa verde (tomatillo-based green sauce), and topped with more cheese.',
        'cuisine': 'Mexican',
    }},
    'corpus-titled-cream-pie': {'action': 'edit', 'patch': {
        'name': 'Cream pie',
        'notes': 'A baked pastry shell filled with a cooked vanilla, chocolate, banana, or coconut custard pudding and topped with whipped cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-frozen-peanut-butter-pie': {'action': 'edit', 'patch': {
        'name': 'Frozen peanut butter pie',
        'notes': 'Peanut butter whipped with cream cheese and folded into whipped topping, poured into an Oreo crust, and frozen until firm.',
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

    print('corpus-titled batch-9 audit applied (entries 1201-1350 by frequency).')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
