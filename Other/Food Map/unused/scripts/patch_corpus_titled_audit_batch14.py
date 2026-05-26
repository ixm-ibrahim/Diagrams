"""Corpus-titled meals audit — batch 14 (entries 1951-2100 by frequency, 63 -> 59)."""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

DECISIONS: dict[str, dict] = {
    'corpus-titled-melting-moments': {'action': 'edit', 'patch': {
        'name': 'Melting moments',
        'tags': ['dessert'],
        'notes': 'A short butter-and-cornstarch cookie that melts on the tongue — Scottish/New Zealand classic, sometimes sandwiched with lemon buttercream.',
        'cuisine': 'British',
        'serving_grams': 30,
    }},
    'corpus-titled-green-chili': {'action': 'edit', 'patch': {
        'name': 'Green chili',
        'notes': 'Pork or beef simmered with roasted green chiles, onions, garlic, and tomatillos — served as a stew or as a topping for burritos.',
        'cuisine': 'Mexican',
        'contains_add': ['pork'],
    }},
    'corpus-titled-cucumbers-in-sour-cream': {'action': 'edit', 'patch': {
        'name': 'Cucumbers in sour cream',
        'notes': 'Thinly sliced cucumber and onion folded into a sour cream-and-vinegar dressing with dill and sugar — chilled briefly before serving.',
        'cuisine': 'German-American',
    }},
    'corpus-titled-sauerkraut-casserole': {'action': 'edit', 'patch': {
        'name': 'Sauerkraut casserole',
        'notes': 'Drained sauerkraut baked with kielbasa or smoked sausage, apples, onions, and brown sugar — a Pennsylvania-Dutch hot pot.',
        'cuisine': 'German-American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-pork-chop-bake': {'action': 'edit', 'patch': {
        'name': 'Pork chop bake',
        'notes': 'Pork chops baked over rice or sliced potatoes with mushrooms, onions, and cream of mushroom soup — a hands-off oven dinner.',
        'cuisine': 'American',
    }},
    'corpus-titled-pierogi-casserole': {'action': 'edit', 'patch': {
        'name': 'Pierogi lasagna',
        'notes': 'Layers of lasagna noodles, mashed potatoes, cheddar, and caramelized onions baked together — pierogi flavors as a casserole.',
        'cuisine': 'Polish-American',
    }},
    'corpus-titled-mint-julep': {'action': 'edit', 'patch': {
        'name': 'Mint julep',
        'tags': ['snack'],
        'notes': 'Bourbon whisky stirred with simple syrup and bruised mint, served over crushed ice in a frosty silver cup — the Kentucky Derby cocktail.',
        'cuisine': 'Southern',
        'contains_add': ['alcohol'],
        'serving_grams': 100,
    }},
    'corpus-titled-sweet-dill-pickles': {'action': 'drop', 'reason': 'pickled condiment, not a coherent meal'},
    'corpus-titled-poppy-seed-chicken-casserole': {'action': 'edit', 'patch': {
        'name': 'Poppy seed chicken casserole',
        'notes': 'Shredded chicken baked in sour cream and cream of chicken soup under a buttery Ritz-cracker-and-poppy-seed topping.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-breakfast-muffins': {'action': 'edit', 'patch': {
        'name': 'Breakfast muffins',
        'notes': 'Tender muffins of flour, sugar, eggs, milk, and butter — a generic base for fruit, oat, or savory breakfast muffins.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-strawberry-pretzel-dessert': {'action': 'edit', 'patch': {
        'name': 'Strawberry pretzel dessert',
        'notes': 'A crushed-pretzel crust topped with sweetened cream cheese and strawberry-Jello-with-frozen-strawberries — chilled and cut into squares.',
        'cuisine': 'Southern',
        'serving_grams': 140,
    }},
    'corpus-titled-date-loaf': {'action': 'edit', 'patch': {
        'name': 'Date loaf candy',
        'tags': ['dessert'],
        'notes': 'A cooked candy of sugar, milk, butter, and chopped dates, beaten and shaped into a log with pecans, then sliced into rounds.',
        'cuisine': 'Southern',
        'serving_grams': 30,
    }},
    'corpus-titled-chewy-cake': {'action': 'edit', 'patch': {
        'name': 'Chewy cake (brookie)',
        'notes': 'A dense, brownie-textured cake of butter, brown sugar, eggs, vanilla, flour, and pecans — somewhere between brownie and blondie.',
        'cuisine': 'American',
    }},
    'corpus-titled-hot-crabmeat-dip': {'action': 'edit', 'patch': {
        'name': 'Hot crabmeat dip',
        'tags': ['snack'],
        'notes': 'Cream cheese, mayo, and lump crab seasoned with Worcestershire, lemon, and horseradish, baked until bubbling and served with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-shoney-s-strawberry-pie': {'action': 'edit', 'patch': {
        'name': "Shoney's strawberry pie (copycat)",
        'notes': 'Fresh strawberries piled into a baked pie crust and set with a strawberry-Jello-and-cornstarch glaze — a Shoney\'s restaurant copycat.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-antipasto': {'action': 'edit', 'patch': {
        'name': 'Antipasto platter',
        'notes': 'A mixed Italian appetizer plate of cured meats (salami, prosciutto), olives, marinated artichokes, peppers, cheeses, and anchovies.',
        'cuisine': 'Italian',
        'contains_add': ['pork'],
        'serving_grams': 100,
    }},
    'corpus-titled-fettucini-alfredo': {'action': 'edit', 'patch': {
        'name': 'Fettuccine alfredo (variant)',
        'notes': 'Fresh fettuccine tossed with butter and grated Parmesan until emulsified into a creamy sauce — American versions add heavy cream.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-egg-pie': {'action': 'edit', 'patch': {
        'name': 'Egg custard pie',
        'notes': 'A baked pastry shell filled with a sweet egg-milk-sugar-vanilla custard, dusted with nutmeg — same as custard pie.',
        'cuisine': 'American',
    }},
    'corpus-titled-venison-jerky': {'action': 'edit', 'patch': {
        'name': 'Venison jerky',
        'notes': 'Strips of venison marinated in soy sauce, Worcestershire, brown sugar, and spices, then slow-dried in a low oven or dehydrator until chewy.',
        'cuisine': 'American',
    }},
    'corpus-titled-frito-pie': {'action': 'edit', 'patch': {
        'name': 'Frito pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'Chili spooned over corn chips and topped with shredded cheese, onions, and pickled jalapeños — sometimes served right in the chip bag.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 320,
    }},
    'corpus-titled-apple-tart': {'action': 'edit', 'patch': {
        'name': 'Apple tart',
        'notes': 'A thin butter-pastry shell topped with sliced apples and sugar, baked until the apples caramelize — French or Dutch style.',
        'cuisine': 'French',
    }},
    'corpus-titled-stuffed-jalapenos': {'action': 'edit', 'patch': {
        'name': 'Stuffed jalapeños (poppers)',
        'tags': ['snack'],
        'notes': 'Halved jalapeños filled with cream cheese and cheddar, wrapped in bacon or breaded, and baked or fried until crisp.',
        'cuisine': 'Tex-Mex',
        'contains_add': ['pork'],
        'serving_grams': 80,
    }},
    'corpus-titled-chicken-mole': {'action': 'edit', 'patch': {
        'name': 'Chicken mole',
        'notes': 'Chicken simmered in a complex Mexican sauce of dried chiles, tomatoes, nuts, seeds, dried fruit, warm spices, and a square of bitter chocolate.',
        'cuisine': 'Mexican',
    }},
    'corpus-titled-empanadas': {'action': 'edit', 'patch': {
        'name': 'Empanadas',
        'tags': ['snack', 'dinner'],
        'notes': 'Folded pastry turnovers filled with seasoned ground beef, raisins, olives, and onion, then baked or fried — a Latin American hand-pie.',
        'cuisine': 'Latin American',
        'serving_grams': 120,
    }},
    'corpus-titled-dream-pie': {'action': 'edit', 'patch': {
        'name': 'Dream pie',
        'notes': 'A no-bake pie of vanilla pastry cream or pudding folded with whipped topping, set in a graham crust and topped with fruit or nuts.',
        'cuisine': 'American',
    }},
    'corpus-titled-cheese-squares': {'action': 'edit', 'patch': {
        'name': 'Cream cheese squares (variant)',
        'tags': ['dessert'],
        'notes': 'A yellow-cake-mix base topped with a sweetened cream-cheese-egg filling and cinnamon-sugar butter, baked into bars — sopapilla cheesecake style.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-cinnamon-twists': {'action': 'edit', 'patch': {
        'name': 'Cinnamon twists',
        'tags': ['breakfast', 'dessert'],
        'notes': 'Yeasted dough rolled with cinnamon-sugar, cut into strips, twisted, and baked — drizzled with a powdered-sugar glaze.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-seafoam-salad': {'action': 'edit', 'patch': {
        'name': 'Seafoam salad',
        'tags': ['dessert'],
        'notes': 'Lime Jello whipped with sweetened cream cheese, crushed pineapple, and whipped topping, chilled until set — a Southern molded dessert salad.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-whole-wheat-banana-bread': {'action': 'edit', 'patch': {
        'name': 'Whole wheat banana bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'Banana bread made with whole-wheat flour for a denser, nuttier crumb — sweetened with honey or brown sugar.',
        'cuisine': 'American',
    }},
    'corpus-titled-bing-cherry-salad': {'action': 'edit', 'patch': {
        'name': 'Bing cherry salad',
        'tags': ['dessert'],
        'notes': 'A molded gelatin salad of cherry Jello set with Bing cherries, crushed pineapple, cream cheese, and chopped pecans.',
        'cuisine': 'American',
    }},
    'corpus-titled-chewy-chocolate-chip-cookies': {'action': 'edit', 'patch': {
        'name': 'Chewy chocolate chip cookies',
        'notes': 'A version of chocolate chip cookies leaning on brown sugar and extra egg yolk for chew, with chocolate chips folded in.',
        'cuisine': 'American',
    }},
    'corpus-titled-zucchini-pineapple-bread': {'action': 'edit', 'patch': {
        'name': 'Zucchini pineapple bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A spiced quick bread folded with grated zucchini, crushed pineapple, raisins, and walnuts — moist and tropical.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-squares': {'action': 'edit', 'patch': {
        'name': 'Chicken squares',
        'notes': 'Crescent-roll dough folded around a chicken-and-cream-cheese filling, brushed with butter and breadcrumbs, and baked into single-serving squares.',
        'cuisine': 'American',
    }},
    'corpus-titled-black-walnut-pound-cake': {'action': 'edit', 'patch': {
        'name': 'Black walnut pound cake',
        'notes': 'A dense pound cake folded with finely chopped black walnuts — earthier than English walnut versions.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-chocolate-peanut-butter-cookies': {'action': 'edit', 'patch': {
        'name': 'Chocolate peanut butter cookies',
        'notes': 'Chocolate-cocoa drop cookies with peanut butter chips or with chocolate-and-peanut-butter swirled in the dough.',
        'cuisine': 'American',
    }},
    'corpus-titled-black-eyed-peas': {'action': 'edit', 'patch': {
        'name': 'Black-eyed peas (slow-cooked)',
        'notes': 'Dried black-eyed peas slow-simmered with a ham hock or bacon, onion, garlic, and a touch of vinegar — a Southern New Year\'s tradition.',
        'cuisine': 'Southern',
        'contains_add': ['pork'],
    }},
    'corpus-titled-buttermilk-fried-chicken': {'action': 'edit', 'patch': {
        'name': 'Buttermilk fried chicken',
        'notes': 'Chicken pieces brined overnight in buttermilk, dredged in seasoned flour, and deep-fried until golden — the Southern Sunday-supper standard.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-orange-congealed-salad': {'action': 'edit', 'patch': {
        'name': 'Orange congealed salad',
        'tags': ['dessert'],
        'notes': 'Orange Jello set with mandarin oranges, crushed pineapple, and cottage cheese, layered with sweetened cream cheese — a Southern molded dessert.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-apple-spice-cake': {'action': 'edit', 'patch': {
        'name': 'Apple spice cake',
        'notes': 'A spiced oil-or-butter cake folded with grated or diced apples — moist with warm cinnamon-clove-nutmeg notes.',
        'cuisine': 'American',
    }},
    'corpus-titled-striped-delight': {'action': 'edit', 'patch': {
        'name': 'Striped delight',
        'tags': ['dessert'],
        'notes': 'A no-bake layered dessert of graham crust, sweetened cream cheese, chocolate pudding, and whipped topping — Oreo-pudding family.',
        'cuisine': 'American',
    }},
    'corpus-titled-lemonade-cake': {'action': 'edit', 'patch': {
        'name': 'Lemonade cake',
        'notes': 'A yellow cake poked all over and saturated with frozen lemonade concentrate whisked into sweetened condensed milk — chilled and topped with whipped topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-enchilada-soup': {'action': 'edit', 'patch': {
        'name': 'Chicken enchilada soup',
        'notes': 'Shredded chicken simmered in a tomato-and-enchilada-sauce broth with hominy or corn, masa, and chili spices — Chili\'s copycat-style.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-crispy-baked-chicken': {'action': 'edit', 'patch': {
        'name': 'Crispy baked chicken',
        'notes': 'Chicken pieces dipped in milk or buttermilk and dredged in seasoned flour or crushed cornflakes, then baked until crisp.',
        'cuisine': 'American',
    }},
    'corpus-titled-tuna-ball': {'action': 'edit', 'patch': {
        'name': 'Tuna ball',
        'tags': ['snack'],
        'notes': 'Cream cheese mixed with canned tuna, lemon, onion, and seasonings, shaped into a ball and rolled in chopped parsley or pecans — served with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-no-peek-stew': {'action': 'edit', 'patch': {
        'name': 'No-peek beef stew',
        'notes': 'Cubed beef and vegetables sealed in a Dutch oven with tomato juice, tapioca, and onion soup mix — baked low for hours without lifting the lid.',
        'cuisine': 'American',
    }},
    'corpus-titled-posole': {'action': 'edit', 'patch': {
        'name': 'Pozole (posole)',
        'notes': 'A Mexican stew of pork or chicken with hominy in a red or green chile broth, garnished with shredded cabbage, radish, lime, and oregano.',
        'cuisine': 'Mexican',
        'contains_add': ['pork'],
    }},
    'corpus-titled-hot-cranberry-punch': {'action': 'edit', 'patch': {
        'name': 'Hot cranberry punch',
        'ingredient_categories': ['Juices', 'Berries', 'Tropical fruits', 'Citrus', 'Whole spices', 'Ground spices', 'Sugar & sweeteners'],
        'tags': ['snack'],
        'notes': 'Cranberry and pineapple juice simmered with cinnamon sticks, cloves, and citrus — a hot non-alcoholic holiday drink.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-pineapple-cheese-salad': {'action': 'edit', 'patch': {
        'name': 'Pineapple cheese salad',
        'tags': ['dessert'],
        'notes': 'Pineapple Jello set with crushed pineapple, shredded cheddar, and whipped topping — a Southern molded dessert salad.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-rouladen': {'action': 'edit', 'patch': {
        'name': 'Rouladen',
        'notes': 'Thinly sliced beef wrapped around bacon, onion, pickle, and mustard, then browned and slow-braised in red wine and broth — German classic.',
        'cuisine': 'German',
        'contains_add': ['pork'],
    }},
    'corpus-titled-chicken-croquettes': {'action': 'edit', 'patch': {
        'name': 'Chicken croquettes',
        'notes': 'Diced cooked chicken bound with a thick bechamel, chilled, shaped into cones or balls, breaded, and deep-fried — sometimes served with a sherry-mushroom sauce.',
        'cuisine': 'American',
    }},
    'corpus-titled-linguine-with-white-clam-sauce': {'action': 'edit', 'patch': {
        'name': 'Linguine with white clam sauce',
        'notes': 'Linguine tossed with clams, garlic, parsley, white wine, butter, and olive oil — Italian-American classic, no tomato.',
        'cuisine': 'Italian-American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-tomato-basil-soup': {'action': 'edit', 'patch': {
        'name': 'Tomato basil soup',
        'notes': 'Roasted or canned tomatoes simmered with onion, garlic, basil, and broth, blended smooth and enriched with cream.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-seven-layer-dip': {'action': 'edit', 'patch': {
        'name': 'Seven layer dip',
        'tags': ['snack'],
        'notes': 'Refried beans layered with seasoned sour cream or guacamole, salsa, cheese, lettuce, tomatoes, and olives — served chilled with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-iced-coffee': {'action': 'edit', 'patch': {
        'name': 'Iced coffee',
        'notes': 'Strong brewed coffee chilled and served over ice with milk, cream, or sugar — sometimes sweetened with vanilla syrup.',
        'serving_grams': 240,
    }},
    'corpus-titled-strawberry-smoothie': {'action': 'edit', 'patch': {
        'name': 'Strawberry smoothie',
        'notes': 'Frozen strawberries blended with yogurt or milk, banana, and a touch of honey or sugar — sometimes with protein powder.',
        'serving_grams': 240,
    }},
    'corpus-titled-preserved-lemons': {'action': 'drop', 'reason': 'pickled / preserved fruit, not a coherent meal'},
    'corpus-titled-honey-cake': {'action': 'edit', 'patch': {
        'name': 'Honey cake (Lekach)',
        'notes': 'A spiced honey-and-coffee cake of flour, eggs, oil, and warm spices — a Rosh Hashanah Jewish tradition.',
        'cuisine': 'Jewish',
    }},
    'corpus-titled-pickled-squash': {'action': 'drop', 'reason': 'pickled condiment, not a coherent meal'},
    'corpus-titled-almond-roca': {'action': 'edit', 'patch': {
        'name': 'Almond roca',
        'tags': ['dessert'],
        'notes': 'A buttery toffee cooked to hard-crack stage, poured over chopped almonds, and topped with melted chocolate — a Tacoma, Washington original.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-potato-cheese-casserole': {'action': 'edit', 'patch': {
        'name': 'Potato cheese casserole',
        'notes': 'Cubed or shredded potatoes baked with sour cream, butter, cream of chicken soup, and shredded cheddar — funeral-potatoes-style.',
        'cuisine': 'American',
    }},
    'corpus-titled-sandies': {'action': 'edit', 'patch': {
        'name': 'Pecan sandies',
        'tags': ['dessert'],
        'notes': 'A butter-and-powdered-sugar shortbread cookie folded with finely chopped pecans — sandy, melt-in-the-mouth crumb.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-harvey-wallbanger-cake': {'action': 'edit', 'patch': {
        'name': 'Harvey Wallbanger cake',
        'notes': 'A yellow Bundt cake from cake mix and instant vanilla pudding with orange juice and a generous splash of vodka and Galliano — the cocktail in cake form.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-banana-bran-muffins': {'action': 'edit', 'patch': {
        'name': 'Banana bran muffins',
        'tags': ['breakfast'],
        'notes': 'High-fiber muffins of wheat bran, mashed banana, buttermilk, and brown sugar — moist with fruit-and-grain heartiness.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-tomato-pudding': {'action': 'edit', 'patch': {
        'name': 'Tomato pudding',
        'tags': ['dinner', 'lunch'],
        'notes': 'A Pennsylvania-Dutch baked side of tomato puree, sugar, and butter poured over cubed bread — sweet, savory, and pudding-textured.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-s-chocolate-pie': {'action': 'edit', 'patch': {
        'name': 'Southern chocolate pie',
        'notes': 'A baked pastry shell filled with a cooked chocolate-pudding custard and topped with meringue or whipped cream — Southern diner classic.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-s-best-cookies': {'action': 'edit', 'patch': {
        'name': "The best cookies",
        'notes': 'A loaded drop cookie of butter, oats, cornflakes, coconut, and chocolate chips — sometimes folded with chopped pecans or potato chips.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-peanut-butter-chews': {'action': 'edit', 'patch': {
        'name': 'Peanut butter chews',
        'tags': ['dessert'],
        'notes': 'A no-bake bar of corn syrup, sugar, and peanut butter cooked to soft-ball, stirred with cornflakes or Rice Krispies and pressed into a pan.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-swedish-nut-cake': {'action': 'edit', 'patch': {
        'name': 'Swedish nut cake',
        'notes': 'A one-bowl cake of crushed pineapple, eggs, flour, sugar, and chopped pecans, baked and topped with cream cheese frosting and more pecans.',
        'cuisine': 'American',
    }},
    'corpus-titled-hamburger-dip': {'action': 'edit', 'patch': {
        'name': 'Hamburger dip',
        'tags': ['snack'],
        'notes': 'Browned ground beef simmered with Velveeta processed cheese and Rotel tomatoes-and-chiles — served warm with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-chicken-fingers': {'action': 'edit', 'patch': {
        'name': 'Chicken fingers',
        'tags': ['snack', 'dinner'],
        'notes': 'Strips of chicken breast dipped in egg and milk, dredged in seasoned flour or breadcrumbs, and pan-fried or baked until golden.',
        'cuisine': 'American',
        'serving_grams': 170,
    }},
    'corpus-titled-carrot-raisin-salad': {'action': 'edit', 'patch': {
        'name': 'Carrot raisin salad',
        'notes': 'Shredded carrots tossed with raisins, crushed pineapple, and a mayonnaise-and-sugar dressing — chilled before serving.',
        'cuisine': 'American',
    }},
    'corpus-titled-baked-acorn-squash': {'action': 'edit', 'patch': {
        'name': 'Baked acorn squash',
        'notes': 'Halved acorn squash baked with butter, brown sugar, and cinnamon in the cavity — a simple sweet-savory side.',
    }},
    'corpus-titled-baked-eggs': {'action': 'edit', 'patch': {
        'name': 'Baked eggs',
        'tags': ['breakfast'],
        'notes': 'Eggs baked in ramekins with cream, cheese, and herbs (oeufs en cocotte) — sometimes with ham or sausage on the bottom.',
        'cuisine': 'French',
        'contains_add': ['pork'],
        'serving_grams': 200,
    }},
    'corpus-titled-snow-ice-cream': {'action': 'edit', 'patch': {
        'name': 'Snow ice cream',
        'notes': 'Fresh clean snow folded with sweetened condensed milk (or milk and sugar) and vanilla — a winter kids\' treat.',
        'cuisine': 'American',
        'serving_grams': 130,
    }},
    'corpus-titled-caramel-apple-pie': {'action': 'edit', 'patch': {
        'name': 'Caramel apple pie',
        'notes': 'A double-crust or streusel-topped apple pie with caramel sauce or chopped caramels stirred into the spiced apple filling.',
        'cuisine': 'American',
    }},
    'corpus-titled-brownie-pudding': {'action': 'edit', 'patch': {
        'name': 'Brownie pudding cake',
        'notes': 'A self-saucing cake — chocolate batter spread in a pan, topped with cocoa-sugar and boiling water, baked so a brownie top sits over fudge sauce.',
        'cuisine': 'American',
    }},
    'corpus-titled-seafood-lasagna': {'action': 'edit', 'patch': {
        'name': 'Seafood lasagna',
        'notes': 'Layered lasagna noodles with shrimp, crab, or scallops in a sherry-cream-and-Parmesan sauce, baked under mozzarella.',
        'cuisine': 'Italian-American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-heath-bars': {'action': 'edit', 'patch': {
        'name': 'Heath bars (toffee bars)',
        'tags': ['dessert'],
        'notes': 'A brown-sugar-and-butter shortbread topped with melted chocolate and crushed Heath bars or pecans — cut into bars.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-mongolian-beef': {'action': 'edit', 'patch': {
        'name': 'Mongolian beef',
        'notes': 'Sliced flank steak stir-fried in a hot wok with scallions in a glossy soy-ginger-brown-sugar-and-sherry sauce — Chinese-American restaurant classic.',
        'cuisine': 'Chinese-American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-italian-salad': {'action': 'edit', 'patch': {
        'name': 'Italian salad',
        'notes': 'Mixed greens with peperoncini, olives, salami or pepperoni, mozzarella, peppers, and Italian dressing.',
        'cuisine': 'Italian-American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-linguine-with-clam-sauce': {'action': 'edit', 'patch': {
        'name': 'Linguine with clam sauce',
        'notes': 'Linguine tossed with clams, garlic, parsley, white wine, butter, and olive oil — sometimes with tomato (red sauce) or without (white sauce).',
        'cuisine': 'Italian-American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-seafoam-candy': {'action': 'edit', 'patch': {
        'name': 'Seafoam candy (honeycomb)',
        'tags': ['dessert'],
        'notes': 'Sugar, corn syrup, water, and vinegar cooked to hard-crack, then baking soda whisked in to create airy bubbles — set firm and broken into pieces.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-black-bean-chili': {'action': 'edit', 'patch': {
        'name': 'Black bean chili',
        'notes': 'Black beans simmered with ground beef or turkey, onions, peppers, tomatoes, and chili spices — a southwestern chili variant.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-fresh-blueberry-pie': {'action': 'edit', 'patch': {
        'name': 'Fresh blueberry pie',
        'notes': 'Whole fresh blueberries piled in a baked crust and set with a cooked sugar-and-cornstarch glaze — chilled and topped with whipped cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-german-slaw': {'action': 'edit', 'patch': {
        'name': 'German slaw',
        'notes': 'Shredded cabbage and onions tossed with a sweet-tart vinegar-oil-and-mustard-seed dressing — keeps for days in the fridge.',
        'cuisine': 'German-American',
    }},
    'corpus-titled-lemon-supreme-cake': {'action': 'edit', 'patch': {
        'name': 'Lemon supreme cake',
        'notes': 'A yellow Bundt cake from lemon cake mix and lemon pudding mix, sometimes with apricot nectar — soaked with lemon glaze.',
        'cuisine': 'American',
    }},
    'corpus-titled-cream-cheese-danish': {'action': 'edit', 'patch': {
        'name': 'Cream cheese Danish',
        'tags': ['breakfast', 'dessert'],
        'notes': 'Crescent-roll dough wrapped around a sweetened cream-cheese filling, baked, and drizzled with a powdered-sugar glaze.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-salmon-mousse': {'action': 'edit', 'patch': {
        'name': 'Salmon mousse',
        'tags': ['snack'],
        'notes': 'A molded appetizer of canned or smoked salmon blended with cream cheese, mayo, lemon, and gelatin — turned out and served with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-lemon-poppy-seed-cake': {'action': 'edit', 'patch': {
        'name': 'Lemon poppy seed cake',
        'notes': 'A bright lemon-scented Bundt cake folded with poppy seeds and yogurt or sour cream, soaked with a tart lemon glaze.',
        'cuisine': 'American',
    }},
    'corpus-titled-date-and-nut-bread': {'action': 'edit', 'patch': {
        'name': 'Date and nut bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A spiced quick bread folded with chopped dates and walnuts — moist and lightly sweet, traditionally served with cream cheese.',
        'cuisine': 'American',
    }},
    'corpus-titled-tourtiere': {'action': 'edit', 'patch': {
        'name': 'Tourtière',
        'notes': 'A French-Canadian meat pie of finely ground pork (and sometimes beef) seasoned with cinnamon, clove, and allspice, baked in a double crust.',
        'cuisine': 'Canadian',
        'contains_add': ['pork'],
    }},
    'corpus-titled-kentucky-pie': {'action': 'edit', 'patch': {
        'name': 'Kentucky Derby pie',
        'notes': 'A baked pie of eggs, butter, sugar, and flour packed with chocolate chips, pecans, and a splash of bourbon — May-Derby-Day tradition.',
        'cuisine': 'Southern',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-ham-and-cheese-rolls': {'action': 'edit', 'patch': {
        'name': 'Ham and cheese sliders',
        'tags': ['snack'],
        'notes': 'Hawaiian sweet rolls split, filled with ham and Swiss, brushed with a poppy-seed-onion-mustard butter, and baked until melty.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-butter-tarts': {'action': 'edit', 'patch': {
        'name': 'Butter tarts',
        'tags': ['dessert'],
        'notes': 'Mini pastry shells filled with a runny brown-sugar-butter-egg-and-raisin filling, baked into Canadian-style mini tarts.',
        'cuisine': 'Canadian',
        'serving_grams': 50,
    }},
    'corpus-titled-chicken-alfredo': {'action': 'edit', 'patch': {
        'name': 'Chicken alfredo',
        'notes': 'Sliced grilled chicken tossed with fettuccine in a butter-and-Parmesan alfredo sauce, often enriched with heavy cream.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-mediterranean-pasta-salad': {'action': 'edit', 'patch': {
        'name': 'Mediterranean pasta salad',
        'notes': 'Cooked pasta tossed with diced cucumber, tomato, red onion, olives, feta, herbs, and a lemon-olive-oil vinaigrette.',
        'cuisine': 'Mediterranean',
    }},
    'corpus-titled-roasted-tomato-soup': {'action': 'edit', 'patch': {
        'name': 'Roasted tomato soup',
        'notes': 'Tomatoes roasted with onion, garlic, and olive oil until charred, then simmered with broth, blended, and finished with cream and basil.',
        'cuisine': 'American',
    }},
    'corpus-titled-french-in-a-flash': {'action': 'drop', 'reason': 'corpus title artifact ("French in a Flash"), not a specific meal'},
    'corpus-titled-beer-biscuits': {'action': 'edit', 'patch': {
        'name': 'Beer biscuits',
        'tags': ['dinner', 'lunch'],
        'notes': 'A three-ingredient drop biscuit of self-rising flour, sugar, and a bottle of beer — quick, tender, and lightly hopped.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
        'serving_grams': 55,
    }},
    'corpus-titled-chocolate-silk-pie': {'action': 'edit', 'patch': {
        'name': 'Chocolate silk pie',
        'notes': 'A chocolate mousse-style pie of butter, sugar, eggs, and melted chocolate whipped until airy, poured into a baked crust and chilled.',
        'cuisine': 'American',
    }},
    'corpus-titled-hamburger-hot-dish': {'action': 'edit', 'patch': {
        'name': 'Hamburger hot dish',
        'notes': 'Ground beef baked with potatoes or noodles, vegetables, and mushroom soup — a Minnesota / Upper-Midwest one-pan dinner.',
        'cuisine': 'American',
    }},
    'corpus-titled-crab-mold': {'action': 'edit', 'patch': {
        'name': 'Crab mold',
        'tags': ['snack'],
        'notes': 'Cream cheese, mayo, and chopped crab blended with gelatin, set in a decorative mold, and unmolded — served with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-praline-cookies': {'action': 'edit', 'patch': {
        'name': 'Praline cookies',
        'notes': 'Drop cookies of brown sugar, butter, and pecans — sometimes a thin shortbread topped with praline icing.',
        'cuisine': 'Southern',
        'serving_grams': 30,
    }},
    'corpus-titled-baked-rice-pudding': {'action': 'edit', 'patch': {
        'name': 'Baked rice pudding',
        'notes': 'Cooked rice baked slowly with milk, eggs, sugar, raisins, and warm spices until the top browns and the pudding sets.',
    }},
    'corpus-titled-jello-punch': {'action': 'edit', 'patch': {
        'name': 'Jello punch',
        'ingredient_categories': ['Juices', 'Tropical fruits', 'Citrus', 'Candy & desserts', 'Sugar & sweeteners', 'Soft drinks'],
        'tags': ['snack'],
        'notes': 'Fruit-flavored Jello dissolved in hot water, mixed with pineapple juice and lemonade, chilled and topped with ginger ale — a brightly-colored party punch.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-kentucky-pound-cake': {'action': 'edit', 'patch': {
        'name': 'Kentucky pound cake',
        'notes': 'A pound cake folded with crushed pineapple and pecans, baked in a Bundt pan and finished with a pineapple-sugar glaze.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-meatball-soup': {'action': 'edit', 'patch': {
        'name': 'Italian meatball soup',
        'notes': 'A clear broth with tiny meatballs, acini di pepe pasta, spinach, and Parmesan — a meatball-based wedding-soup variant.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-lobster-bisque': {'action': 'edit', 'patch': {
        'name': 'Lobster bisque',
        'notes': 'A rich seafood-broth-and-cream soup of lobster, aromatics, brandy, and tomato, thickened with a buttery roux and finished with cream.',
        'cuisine': 'French',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-chicken-and-sausage-gumbo': {'action': 'edit', 'patch': {
        'name': 'Chicken and sausage gumbo',
        'notes': 'Chicken and andouille sausage simmered in a dark-roux broth with the trinity of vegetables, file powder, and Creole spices — served over rice.',
        'cuisine': 'Creole',
        'contains_add': ['pork'],
    }},
    'corpus-titled-cranberry-muffins': {'action': 'edit', 'patch': {
        'name': 'Cranberry muffins',
        'tags': ['breakfast', 'snack'],
        'notes': 'Tender muffins folded with fresh or frozen cranberries and orange zest — a tart-bright morning bake.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-hershey-bar-cake': {'action': 'edit', 'patch': {
        'name': 'Hershey bar cake',
        'notes': 'A chocolate-buttermilk cake baked with melted Hershey almond bars folded into the batter — frosted with chocolate buttercream.',
        'cuisine': 'American',
    }},
    'corpus-titled-mexican-soup': {'action': 'edit', 'patch': {
        'name': 'Mexican soup',
        'notes': 'A spiced beef or chicken soup with hominy or beans, peppers, tomato, and chili powder — generic name for Mexican-style soups.',
        'cuisine': 'Mexican',
    }},
    'corpus-titled-corn-flake-candy': {'action': 'edit', 'patch': {
        'name': 'Corn flake candy',
        'tags': ['dessert'],
        'notes': 'Corn flakes stirred into a hot peanut-butter-and-sugar syrup or melted chocolate, dropped onto wax paper to set into clusters.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-chicken-breast-casserole': {'action': 'edit', 'patch': {
        'name': 'Chicken breast casserole',
        'notes': 'Chicken breasts baked with mushrooms and sour cream — a generic weeknight bake.',
        'cuisine': 'American',
    }},
    'corpus-titled-italian-sausage-soup': {'action': 'edit', 'patch': {
        'name': 'Italian sausage soup',
        'notes': 'Italian sausage simmered with tomatoes, peppers, beans, pasta, and herbs in broth — a hearty stockpot soup.',
        'cuisine': 'Italian-American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-breakfast-sausage-casserole': {'action': 'edit', 'patch': {
        'name': 'Breakfast sausage casserole',
        'notes': 'Browned breakfast sausage layered with bread, eggs, milk, and cheese — assembled overnight and baked in the morning.',
        'cuisine': 'American',
    }},
    'corpus-titled-lemon-bisque': {'action': 'edit', 'patch': {
        'name': 'Lemon bisque',
        'tags': ['dessert'],
        'notes': 'A chilled lemon dessert of evaporated milk whipped to a froth and folded with lemon Jello, sugar, and crushed graham crackers.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-butterfinger-ice-cream': {'action': 'edit', 'patch': {
        'name': 'Butterfinger ice cream',
        'notes': 'A custard ice cream churned with crushed Butterfinger candy bars — peanut butter, chocolate, and toffee in every bite.',
        'cuisine': 'American',
        'serving_grams': 85,
    }},
    'corpus-titled-orange-bread': {'action': 'edit', 'patch': {
        'name': 'Orange bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A sweet quick bread bright with orange zest and juice, sometimes folded with cranberries or nuts and finished with an orange glaze.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-peanut-butter-fudge': {'action': 'edit', 'patch': {
        'name': 'Chocolate peanut butter fudge',
        'notes': 'Two layers (chocolate and peanut butter) of fudge cooked separately and poured to set on top of each other — peanut-butter cup in fudge form.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-baked-zucchini': {'action': 'edit', 'patch': {
        'name': 'Baked zucchini',
        'notes': 'Sliced zucchini baked with butter, eggs, Parmesan, and breadcrumbs until tender and lightly browned.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-chuck-wagon-beans': {'action': 'edit', 'patch': {
        'name': 'Chuck wagon beans',
        'notes': 'A mix of canned beans baked with ground beef, bacon, brown sugar, and barbecue sauce — same family as calico / cowboy / ranch beans.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-chicken-corn-soup': {'action': 'edit', 'patch': {
        'name': 'Chicken corn soup',
        'notes': 'Chicken simmered with sweet corn, hard-boiled egg, and rivels (small dumplings) in broth — a Pennsylvania-Dutch farmhouse soup.',
        'cuisine': 'American',
    }},
    'corpus-titled-raspberry-bars': {'action': 'edit', 'patch': {
        'name': 'Raspberry bars',
        'tags': ['dessert'],
        'notes': 'A short butter-oat-and-flour crumb crust topped with raspberry jam and more crumb, baked and cut into bars.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-iced-tea': {'action': 'edit', 'patch': {
        'name': 'Sweet iced tea',
        'ingredient_categories': ['Coffee & tea', 'Sugar & sweeteners', 'Citrus'],
        'tags': ['snack'],
        'notes': 'Black tea brewed strong, sweetened heavily with sugar while hot, then cooled and served over ice with lemon — the Southern table drink.',
        'cuisine': 'Southern',
        'serving_grams': 240,
    }},
    'corpus-titled-chimichangas': {'action': 'edit', 'patch': {
        'name': 'Chimichangas',
        'notes': 'A burrito (seasoned meat, rice, beans, cheese) wrapped tightly in a flour tortilla and deep-fried until crisp — Sonoran-Arizona-style.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-peanut-butter': {'action': 'drop', 'reason': 'pantry condiment (homemade peanut butter), not a coherent meal'},
    'corpus-titled-cowboy-caviar': {'action': 'edit', 'patch': {
        'name': 'Cowboy caviar',
        'tags': ['snack'],
        'notes': 'Black-eyed peas and corn tossed with diced bell peppers, tomatoes, onion, jalapeño, and Italian-style vinaigrette — served as a chip dip.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 80,
    }},
    'corpus-titled-focaccia': {'action': 'edit', 'patch': {
        'name': 'Focaccia',
        'notes': 'A flat yeasted Italian bread baked with olive oil, sea salt, and rosemary on top — tender interior, dimpled crust.',
        'cuisine': 'Italian',
        'serving_grams': 80,
    }},
    'corpus-titled-chicken-saltimbocca': {'action': 'edit', 'patch': {
        'name': 'Chicken saltimbocca',
        'notes': 'Pounded chicken cutlets topped with prosciutto and sage, dredged in flour, sautéed, and finished with a white-wine-butter pan sauce.',
        'cuisine': 'Italian',
        'contains_add': ['alcohol', 'pork'],
    }},
    'corpus-titled-hello-dolly-bars': {'action': 'edit', 'patch': {
        'name': 'Hello Dolly bars (variant)',
        'tags': ['dessert'],
        'notes': 'A graham crust topped with chocolate chips, butterscotch chips, coconut, and pecans, drizzled with sweetened condensed milk and baked.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-strawberry-fluff': {'action': 'edit', 'patch': {
        'name': 'Strawberry fluff',
        'tags': ['dessert'],
        'notes': 'Crushed sweetened strawberries folded with whipped cream or whipped topping — a quick chilled "fluff" dessert.',
        'cuisine': 'American',
    }},
    'corpus-titled-butter-rolls': {'action': 'edit', 'patch': {
        'name': 'Butter rolls',
        'tags': ['dinner', 'lunch'],
        'notes': 'A buttery yeasted dough shaped into rolls, brushed with melted butter before baking, and pulled apart warm.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-ribs': {'action': 'edit', 'patch': {
        'name': 'Barbecue ribs (generic)',
        'notes': 'Pork ribs rubbed with spices and slow-smoked or baked low, basted with barbecue sauce — generic "ribs" recipe.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-green-bean-bake': {'action': 'edit', 'patch': {
        'name': 'Green bean bake (casserole)',
        'notes': 'Green beans baked in cream-of-mushroom soup with milk, topped with crispy fried onions — the Campbell\'s Thanksgiving side.',
        'cuisine': 'American',
    }},
    'corpus-titled-spaghetti-bake': {'action': 'edit', 'patch': {
        'name': 'Spaghetti bake',
        'notes': 'Cooked spaghetti tossed with ground beef, mushrooms, and tomato sauce, baked under shredded mozzarella.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-buttermilk-cornbread': {'action': 'edit', 'patch': {
        'name': 'Buttermilk cornbread',
        'notes': 'A skillet cornbread of cornmeal, flour, eggs, and buttermilk — tender, slightly tangy, with a crisp bottom from a hot buttered pan.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-o-henry-bars': {'action': 'edit', 'patch': {
        'name': "O'Henry bars",
        'tags': ['dessert'],
        'notes': 'A baked oat-and-brown-sugar bar topped with melted chocolate and peanut butter — chewy, peanut-butter-cup-flavored.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-dried-beef-casserole': {'action': 'edit', 'patch': {
        'name': 'Dried beef casserole',
        'notes': 'Cooked noodles baked with chopped dried (chipped) beef, mushrooms, and milk-and-butter sauce under shredded cheese.',
        'cuisine': 'American',
    }},
    'corpus-titled-rotel-dip': {'action': 'edit', 'patch': {
        'name': 'Rotel dip',
        'tags': ['snack'],
        'notes': 'Velveeta processed cheese melted with ground beef or sausage and Rotel tomatoes-and-chiles — served warm with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'contains_add': ['pork'],
        'serving_grams': 60,
    }},
    'corpus-titled-white-bean-soup': {'action': 'edit', 'patch': {
        'name': 'White bean soup',
        'notes': 'Cannellini or great northern beans simmered with ham hock or pancetta, onions, carrots, celery, and herbs in broth.',
        'cuisine': 'Italian',
        'contains_add': ['pork'],
    }},
    'corpus-titled-sweet-and-sour-green-beans': {'action': 'edit', 'patch': {
        'name': 'Sweet and sour green beans',
        'notes': 'Cooked green beans tossed warm with crisp bacon, onion, and a sweet vinegar-bacon-fat dressing.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-cream-of-carrot-soup': {'action': 'edit', 'patch': {
        'name': 'Cream of carrot soup',
        'notes': 'Carrots simmered with onion in chicken broth, blended smooth, and finished with milk, cream, and a touch of nutmeg.',
    }},
    'corpus-titled-oatmeal-drop-cookies': {'action': 'edit', 'patch': {
        'name': 'Oatmeal drop cookies',
        'notes': 'Drop cookies of butter, brown sugar, oats, and warm spices — sometimes with raisins or chopped nuts; chewier than rolled oatmeal cookies.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-chicken-jambalaya': {'action': 'edit', 'patch': {
        'name': 'Chicken jambalaya',
        'notes': 'Chicken and andouille sausage cooked with rice, the trinity of vegetables, tomato, and Cajun seasoning into a one-pot dish.',
        'cuisine': 'Creole',
        'contains_add': ['pork'],
    }},
    'corpus-titled-oven-fries': {'action': 'edit', 'patch': {
        'name': 'Oven fries',
        'notes': 'Potato wedges or sticks tossed in oil and seasonings, baked hot until crisp outside and tender inside — a healthier alternative to deep-fried fries.',
        'cuisine': 'American',
    }},
    'corpus-titled-unstuffed-cabbage': {'action': 'edit', 'patch': {
        'name': 'Unstuffed cabbage',
        'notes': 'Shredded cabbage simmered in a pot with ground beef, rice, tomato, onion, and seasonings — cabbage-roll flavors without the rolling.',
        'cuisine': 'Eastern European',
    }},
    'corpus-titled-veal-marsala': {'action': 'edit', 'patch': {
        'name': 'Veal Marsala',
        'notes': 'Pounded veal cutlets dredged in flour, browned in butter, and finished in a Marsala-wine and mushroom pan sauce.',
        'cuisine': 'Italian-American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-shrimp-chowder': {'action': 'edit', 'patch': {
        'name': 'Shrimp chowder',
        'notes': 'Diced potatoes and shrimp simmered in a milk-and-cream base with onion, peppers, and herbs — Pacific-Northwest or New England style.',
        'cuisine': 'American',
    }},
    'corpus-titled-baked-alaska': {'action': 'edit', 'patch': {
        'name': 'Baked Alaska',
        'tags': ['dessert'],
        'notes': 'A cake base topped with ice cream, sealed under a thick layer of meringue, and briefly baked or torched so the meringue browns without melting the ice cream.',
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

    print('corpus-titled batch-14 audit applied (entries 1951-2100 by frequency).')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
