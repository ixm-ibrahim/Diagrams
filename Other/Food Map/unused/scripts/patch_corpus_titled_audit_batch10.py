"""Corpus-titled meals audit — batch 10 (entries 1351-1500 by frequency, 87 -> 79).
Same standard.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

DECISIONS: dict[str, dict] = {
    'corpus-titled-turkey-meatballs': {'action': 'edit', 'patch': {
        'name': 'Turkey meatballs',
        'notes': 'Ground turkey bound with breadcrumbs, egg, herbs, and Parmesan, rolled into balls and baked or simmered in marinara — a leaner meatball.',
        'cuisine': 'American',
    }},
    'corpus-titled-baked-tomatoes': {'action': 'edit', 'patch': {
        'name': 'Baked tomatoes',
        'notes': 'Halved tomatoes topped with seasoned breadcrumbs, herbs, and Parmesan, drizzled with olive oil and baked until tender.',
        'cuisine': 'Italian-American',
        'serving_grams': 200,
    }},
    'corpus-titled-divinity-fudge': {'action': 'edit', 'patch': {
        'name': 'Divinity fudge',
        'notes': 'A fluffy white candy of hot sugar syrup whipped into stiff egg whites with vanilla and pecans — dropped onto wax paper to set, between fudge and meringue.',
        'cuisine': 'Southern',
        'serving_grams': 40,
    }},
    'corpus-titled-salmon-casserole': {'action': 'edit', 'patch': {
        'name': 'Salmon casserole',
        'notes': 'Canned salmon baked with egg noodles, peas, cream of mushroom soup, and cheese under a buttered breadcrumb topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-one-dish-meal': {'action': 'edit', 'patch': {
        'name': 'One-dish skillet meal',
        'notes': 'Ground beef browned with onions, peppers, potatoes, and tomato, then simmered with rice or noodles into a one-skillet weeknight dish.',
        'cuisine': 'American',
    }},
    'corpus-titled-shrimp-ball': {'action': 'edit', 'patch': {
        'name': 'Shrimp ball',
        'tags': ['snack'],
        'notes': 'Cream cheese mixed with chopped shrimp, onion, and seasonings, shaped into a ball and rolled in chopped parsley or pecans — served with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-pot-pie': {'action': 'edit', 'patch': {
        'name': 'Pot pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'Diced chicken or beef and vegetables in a creamy gravy baked under a flaky pastry or biscuit crust.',
        'cuisine': 'American',
        'serving_grams': 320,
    }},
    'corpus-titled-dried-beef-cheese-ball': {'action': 'edit', 'patch': {
        'name': 'Dried beef cheese ball',
        'tags': ['snack'],
        'notes': 'Cream cheese mixed with sour cream, dried (chipped) beef, onion, and Worcestershire, shaped into a ball — served chilled with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-ham-and-potato-casserole': {'action': 'edit', 'patch': {
        'name': 'Ham and potato casserole',
        'notes': 'Cubed ham baked with sliced or shredded potatoes in a cream-of-chicken-soup-and-cheese sauce — a hands-off leftover-ham bake.',
        'cuisine': 'American',
    }},
    'corpus-titled-kahlua-cake': {'action': 'edit', 'patch': {
        'name': 'Kahlúa cake',
        'notes': 'A chocolate Bundt cake from chocolate cake mix and chocolate pudding mix, with Kahlúa stirred into the batter and brushed on after baking.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-coconut-cream-cake': {'action': 'edit', 'patch': {
        'name': 'Coconut cream cake',
        'notes': 'A white cake poked and saturated with sweetened cream of coconut, topped with whipped topping and toasted coconut.',
        'cuisine': 'American',
    }},
    'corpus-titled-orange-slice-cookies': {'action': 'edit', 'patch': {
        'name': 'Orange slice cookies',
        'notes': 'Drop cookies with chopped orange-slice candies (gumdrop-style) folded into the dough with coconut and oats.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-strawberry-pudding': {'action': 'edit', 'patch': {
        'name': 'Strawberry pudding',
        'notes': 'Vanilla pudding folded with sliced strawberries and whipped topping, layered with vanilla wafers — Southern banana-pudding cousin.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-cheesy-scalloped-potatoes': {'action': 'edit', 'patch': {
        'name': 'Cheesy scalloped potatoes',
        'notes': 'Thinly sliced potatoes layered with onions in a milk-and-cream bechamel with shredded cheddar, baked until bubbling and golden.',
        'cuisine': 'American',
    }},
    'corpus-titled-shortcake': {'action': 'edit', 'patch': {
        'name': 'Shortcake biscuits',
        'tags': ['dessert'],
        'notes': 'Sweet split biscuits of flour, sugar, butter, eggs, and milk — the foundation for strawberry shortcake when layered with macerated berries and whipped cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-rice-dressing': {'action': 'edit', 'patch': {
        'name': 'Rice dressing (Cajun)',
        'notes': 'Cooked rice mixed with browned ground beef, pork, and chicken livers, the trinity of vegetables, and Cajun seasoning — a Louisiana stuffing alternative.',
        'cuisine': 'Creole',
    }},
    'corpus-titled-molasses-crinkles': {'action': 'edit', 'patch': {
        'name': 'Molasses crinkles',
        'tags': ['dessert'],
        'notes': 'Soft spiced cookies of molasses, brown sugar, butter, and warm spices rolled in granulated sugar — the surface crinkles as they bake.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-italian-casserole': {'action': 'edit', 'patch': {
        'name': 'Italian casserole',
        'notes': 'A baked pasta with ground beef, peppers, mushrooms, ricotta, mozzarella, and marinara — a lasagna-style one-dish meal.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-buttermilk-coconut-pie': {'action': 'edit', 'patch': {
        'name': 'Buttermilk coconut pie',
        'notes': 'A Southern custard pie of buttermilk, eggs, sugar, butter, and shredded coconut baked in a flaky shell — tangy and chewy.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-scalloped-cabbage': {'action': 'edit', 'patch': {
        'name': 'Scalloped cabbage',
        'notes': 'Shredded cabbage baked in a cheesy milk-and-roux bechamel under buttered cracker crumbs — a hearty Pennsylvania-Dutch side.',
        'cuisine': 'American',
    }},
    'corpus-titled-frozen-strawberry-salad': {'action': 'edit', 'patch': {
        'name': 'Frozen strawberry salad',
        'tags': ['dessert'],
        'notes': 'Sliced strawberries and crushed pineapple folded with sweetened cream cheese, sour cream, and chopped pecans, frozen in a pan and sliced.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-stuffed-eggplant': {'action': 'edit', 'patch': {
        'name': 'Stuffed eggplant',
        'notes': 'Halved eggplants hollowed and filled with seasoned breadcrumbs, herbs, and Parmesan (sometimes ground beef), baked until tender.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-chicken-marinade': {'action': 'drop', 'reason': 'marinade component, not a coherent meal'},
    'corpus-titled-oreo-dessert': {'action': 'edit', 'patch': {
        'name': 'Oreo dessert',
        'notes': 'A no-bake icebox dessert of crushed Oreos layered with whipped sweetened cream cheese, chocolate pudding, and whipped topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-crescent-rolls': {'action': 'edit', 'patch': {
        'name': 'Homemade crescent rolls',
        'tags': ['dinner', 'lunch'],
        'notes': 'A buttery yeasted dough rolled out, cut into wedges, rolled up from the wide end, and baked into curved crescents.',
        'cuisine': 'American',
        'serving_grams': 50,
    }},
    'corpus-titled-baked-caramel-corn': {'action': 'edit', 'patch': {
        'name': 'Baked caramel corn',
        'tags': ['snack', 'dessert'],
        'notes': 'Popped corn tossed with a butter-brown-sugar-corn-syrup caramel and slow-baked until crisp and shiny — same family as Cracker Jack.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-layered-mexican-dip': {'action': 'edit', 'patch': {
        'name': 'Layered Mexican dip',
        'tags': ['snack'],
        'notes': 'A cold layered dip of refried beans or seasoned sour cream, salsa, shredded cheese, lettuce, and olives — served with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-couscous-salad': {'action': 'edit', 'patch': {
        'name': 'Couscous salad',
        'notes': 'Cooked couscous tossed with diced peppers, cucumber, tomato, herbs, lemon, and olive oil — sometimes with feta and chickpeas.',
        'cuisine': 'Mediterranean',
    }},
    'corpus-titled-navy-bean-soup': {'action': 'edit', 'patch': {
        'name': 'Navy bean soup',
        'notes': 'Dried navy beans slow-simmered with a ham hock or bone, carrots, celery, and onion — the U.S. Senate dining-room classic.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-chicken-with-rice': {'action': 'edit', 'patch': {
        'name': 'Chicken with rice',
        'notes': 'Chicken pieces baked or simmered with rice in seasoned broth or cream-soup gravy until both are tender — generic "chicken and rice".',
        'cuisine': 'American',
    }},
    'corpus-titled-pavlova': {'action': 'edit', 'patch': {
        'name': 'Pavlova',
        'notes': 'A crisp-edged, marshmallow-centered meringue base topped with whipped cream and fresh fruit (often kiwi and berries) — Australian/New Zealand dessert.',
        'cuisine': 'Australian',
        'serving_grams': 130,
    }},
    'corpus-titled-diabetic-cake': {'action': 'edit', 'patch': {
        'name': 'Diabetic spice cake',
        'notes': 'A sugar-free spiced cake sweetened by raisins or applesauce instead of granulated sugar — a diabetic-friendly variant.',
        'cuisine': 'American',
    }},
    'corpus-titled-mexican-wedding-cake': {'action': 'edit', 'patch': {
        'name': 'Mexican wedding cake (sheet)',
        'notes': 'A one-bowl sheet cake of crushed pineapple, sugar, eggs, flour, and pecans, baked and topped with cream cheese frosting — the Southern "Mexican fruit cake".',
        'cuisine': 'American',
    }},
    'corpus-titled-sherbet-punch': {'action': 'edit', 'patch': {
        'name': 'Sherbet punch',
        'ingredient_categories': ['Juices', 'Citrus', 'Tropical fruits', 'Frozen dairy', 'Soft drinks'],
        'tags': ['snack'],
        'notes': 'Scoops of orange or rainbow sherbet floated in a bowl of fruit juices and ginger ale — a creamy non-alcoholic party punch.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-cream-cheese-bars': {'action': 'edit', 'patch': {
        'name': 'Cream cheese bars',
        'tags': ['dessert'],
        'notes': 'A yellow-cake-mix base topped with a sweetened cream cheese filling, baked and cut into bars — same family as gooey butter cake.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-apple-dessert': {'action': 'edit', 'patch': {
        'name': 'Apple dessert',
        'notes': 'Spiced sliced apples baked under a butter-and-flour crumb topping — generic name for apple crisp / crumble / square.',
        'cuisine': 'American',
    }},
    'corpus-titled-scalloped-chicken': {'action': 'edit', 'patch': {
        'name': 'Scalloped chicken',
        'notes': 'Cooked chicken layered with herbed bread cubes and cream-of-chicken-soup gravy, baked into a moist Southern-style dressing-and-chicken bake.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-chocolate-dessert': {'action': 'edit', 'patch': {
        'name': 'Chocolate dessert',
        'notes': 'A no-bake layered dessert of pecan-shortbread crust, sweetened cream cheese, chocolate pudding, and whipped topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-cocktail-wieners': {'action': 'edit', 'patch': {
        'name': 'Cocktail wieners',
        'tags': ['snack'],
        'notes': 'Mini hot dogs (Lit\'l Smokies) simmered in a sweet-tangy sauce of grape jelly and chili sauce or barbecue sauce — held warm in a slow cooker.',
        'cuisine': 'American',
        'contains_add': ['pork'],
        'serving_grams': 80,
    }},
    'corpus-titled-no-bake-fruit-cake': {'action': 'edit', 'patch': {
        'name': 'No-bake fruitcake',
        'notes': 'Crushed graham crackers or vanilla wafers mixed with candied fruit, dates, nuts, and sweetened condensed milk — pressed in a pan and chilled.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-sawdust-salad': {'action': 'edit', 'patch': {
        'name': 'Sawdust salad',
        'tags': ['dessert'],
        'notes': 'Layered lemon-and-orange Jello set with crushed pineapple, then topped with a cooked pudding-and-whipped-topping layer — the "sawdust" is shredded cheese sprinkled on top.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-red-rice': {'action': 'edit', 'patch': {
        'name': 'Red rice (Lowcountry)',
        'notes': 'Long-grain rice cooked with tomato, bacon, peppers, and onions — a Charleston Gullah-Geechee Lowcountry side dish.',
        'cuisine': 'Southern',
        'contains_add': ['pork'],
    }},
    'corpus-titled-mississippi-mud': {'action': 'edit', 'patch': {
        'name': 'Mississippi mud',
        'tags': ['dessert'],
        'notes': 'A dense chocolate sheet cake or brownie base topped with marshmallow creme and a layer of chocolate-pecan frosting — gooey and sweet.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-pizza-bread': {'action': 'edit', 'patch': {
        'name': 'Pizza bread',
        'notes': 'A loaf of bread split or sliced, spread with pizza sauce, topped with cheese and pepperoni, and baked — open-faced pizza on bread.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-potato-skins': {'action': 'edit', 'patch': {
        'name': 'Potato skins',
        'tags': ['snack'],
        'notes': 'Hollowed-out baked potato halves brushed with butter, filled with cheese, bacon, and chives, and broiled until crisp — bar-and-grill appetizer.',
        'cuisine': 'American',
        'contains_add': ['pork'],
        'serving_grams': 120,
    }},
    'corpus-titled-english-muffin-bread': {'action': 'edit', 'patch': {
        'name': 'English muffin bread',
        'notes': 'A no-knead yeasted bread baked in a loaf pan dusted with cornmeal — when toasted, slices have the nooks and crannies of English muffins.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-chinese-chicken': {'action': 'edit', 'patch': {
        'name': 'Chinese chicken',
        'notes': 'A generic Chinese-American stir-fry of chicken with peppers, onions, water chestnuts, and a soy-and-sugar sauce — served over rice.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-flourless-chocolate-cake': {'action': 'edit', 'patch': {
        'name': 'Flourless chocolate cake',
        'notes': 'A dense gluten-free torte of butter, dark chocolate, eggs, and sugar baked low — fudgy, intense, and naturally crackled on top.',
        'cuisine': 'French',
    }},
    'corpus-titled-lemon-fluff': {'action': 'edit', 'patch': {
        'name': 'Lemon fluff',
        'tags': ['dessert'],
        'notes': 'Lemon pudding folded with sweetened condensed milk and whipped topping, poured into a graham crust and chilled — same family as lemon icebox pie.',
        'cuisine': 'American',
    }},
    'corpus-titled-cornflake-cookies': {'action': 'edit', 'patch': {
        'name': 'Cornflake cookies',
        'notes': 'Drop cookies with cornflakes, coconut, and chopped pecans folded into a peanut-butter-and-sugar dough — chewy with crunch.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-snack-crackers': {'action': 'edit', 'patch': {
        'name': 'Seasoned snack crackers',
        'ingredient_categories': ['Baked snacks & pastries', 'Oils', 'Fresh herbs', 'Citrus', 'Ground spices'],
        'notes': 'Saltines or oyster crackers tossed with oil, dry ranch mix, and seasonings, baked until aromatic — a seasoned party snack.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-beef-vegetable-soup': {'action': 'edit', 'patch': {
        'name': 'Beef vegetable soup',
        'notes': 'Cubed beef simmered with potatoes, carrots, celery, tomato, and herbs in beef broth — a stockpot weeknight soup.',
    }},
    'corpus-titled-lemon-chiffon-pie': {'action': 'edit', 'patch': {
        'name': 'Lemon chiffon pie',
        'notes': 'A lemon custard lightened with gelatin and beaten egg whites, poured into a baked crust and chilled — airier than lemon meringue.',
        'cuisine': 'American',
    }},
    'corpus-titled-porcupine-meat-balls': {'action': 'edit', 'patch': {
        'name': 'Porcupine meatballs (variant)',
        'notes': 'Ground beef and uncooked rice meatballs simmered in tomato sauce — the rice pokes out as it cooks.',
        'cuisine': 'American',
    }},
    'corpus-titled-seafood-pasta-salad': {'action': 'edit', 'patch': {
        'name': 'Seafood pasta salad',
        'notes': 'Cooked rotini or shells tossed with shrimp or imitation crab, broccoli, peppers, and a creamy or Italian dressing — chilled.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-dressing-casserole': {'action': 'edit', 'patch': {
        'name': 'Chicken and dressing casserole',
        'notes': 'Shredded chicken layered with cornbread or stuffing dressing and mushroom-soup gravy, baked into the Southern Thanksgiving-leftover staple.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-strawberry-congealed-salad': {'action': 'edit', 'patch': {
        'name': 'Strawberry congealed salad',
        'tags': ['dessert'],
        'notes': 'Strawberry Jello set with frozen strawberries and crushed pineapple, layered with sour cream — a chilled Southern molded dessert.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-chicken-rotel': {'action': 'edit', 'patch': {
        'name': 'Chicken Rotel',
        'notes': 'Shredded chicken baked with cooked pasta or rice, Rotel tomatoes-and-chiles, mushroom soup, and Velveeta — same family as Rotel chicken / King Ranch.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-amish-sugar-cookies': {'action': 'edit', 'patch': {
        'name': 'Amish sugar cookies',
        'notes': 'Soft cake-like sugar cookies made tender by both butter and oil with powdered sugar in the dough — light, pillowy, and easy.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-crabbies': {'action': 'edit', 'patch': {
        'name': 'Crabbies (crab melts)',
        'tags': ['snack'],
        'notes': 'English-muffin halves topped with a mixture of crab, mayo, Old Bay, and shredded cheese, broiled or baked until bubbly.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-velveeta-fudge': {'action': 'edit', 'patch': {
        'name': 'Velveeta fudge',
        'notes': 'A surprising fudge that melts Velveeta with butter, sugar, cocoa, and vanilla — the cheese acts as an emulsifier for a smooth set.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-rhubarb-cream-pie': {'action': 'edit', 'patch': {
        'name': 'Rhubarb cream pie',
        'notes': 'Chopped rhubarb baked in a sour-cream-and-egg custard within a single crust — silky and tart.',
        'cuisine': 'American',
    }},
    'corpus-titled-shipwreck': {'action': 'edit', 'patch': {
        'name': 'Shipwreck casserole',
        'notes': 'Layered raw potatoes, onions, ground beef, rice, beans, and tomato soup baked slow until everything is tender — a Depression-era one-pan dinner.',
        'cuisine': 'American',
    }},
    'corpus-titled-shrimp-butter': {'action': 'edit', 'patch': {
        'name': 'Shrimp butter',
        'tags': ['snack'],
        'notes': 'Cream cheese, butter, and chopped shrimp blended smooth with lemon and seasonings — a chilled spread for crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-colcannon': {'action': 'edit', 'patch': {
        'name': 'Colcannon',
        'notes': 'Mashed potatoes folded with sautéed kale or cabbage and scallions, enriched with milk and butter — Ireland\'s celebratory mash.',
        'cuisine': 'Irish',
    }},
    'corpus-titled-stuffed-artichokes': {'action': 'edit', 'patch': {
        'name': 'Stuffed artichokes',
        'notes': 'Whole artichokes spread leaves filled with seasoned breadcrumbs, garlic, Parmesan, and olive oil, then steamed or braised — Italian-American.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-cowboy-stew': {'action': 'edit', 'patch': {
        'name': 'Cowboy stew',
        'notes': 'A hearty stew of ground beef, potatoes, beans, corn, and tomato seasoned with chili powder — campfire-friendly one-pot.',
        'cuisine': 'American',
    }},
    'corpus-titled-sauteed-mushrooms': {'action': 'edit', 'patch': {
        'name': 'Sautéed mushrooms',
        'notes': 'Whole or sliced mushrooms cooked hard in butter and oil until golden, then finished with garlic and herbs — a steakhouse side.',
    }},
    'corpus-titled-scotch-eggs': {'action': 'edit', 'patch': {
        'name': 'Scotch eggs',
        'tags': ['snack'],
        'notes': 'Hard-boiled eggs wrapped in sausage meat, coated in breadcrumbs, and deep-fried or baked golden — a British pub snack.',
        'cuisine': 'British',
        'contains_add': ['pork'],
        'serving_grams': 120,
    }},
    'corpus-titled-pink-stuff': {'action': 'edit', 'patch': {
        'name': 'Pink stuff',
        'tags': ['dessert'],
        'notes': 'Cherry pie filling folded with sweetened condensed milk, crushed pineapple, mini marshmallows, and whipped topping — a Southern dessert salad.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-four-bean-salad': {'action': 'edit', 'patch': {
        'name': 'Four-bean salad',
        'notes': 'Green, kidney, garbanzo, and wax beans tossed with onion, peppers, and a sweet vinegar dressing — chilled overnight.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-and-spaghetti': {'action': 'edit', 'patch': {
        'name': 'Chicken and spaghetti',
        'notes': 'Spaghetti baked with shredded chicken, peppers, onions, mushrooms, and Velveeta cheese sauce — Southern church-supper casserole.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-snowball-cookies': {'action': 'edit', 'patch': {
        'name': 'Snowball cookies (variant)',
        'notes': 'A butter-and-powdered-sugar shortbread folded with finely chopped pecans, baked into balls and rolled twice in powdered sugar.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-snickerdoodle-cookies': {'action': 'edit', 'patch': {
        'name': 'Snickerdoodle cookies',
        'notes': 'Soft butter cookies rolled in cinnamon-sugar before baking, with a slight tang from cream of tartar.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-stir-fry': {'action': 'edit', 'patch': {
        'name': 'Stir-fry',
        'notes': 'A generic name for vegetables and meat (chicken, beef, or shrimp) tossed quickly in a hot wok with soy-based sauce, served over rice or noodles.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-orange-sherbet-salad': {'action': 'edit', 'patch': {
        'name': 'Orange sherbet salad',
        'tags': ['dessert'],
        'notes': 'Orange Jello set with orange sherbet, mandarin oranges, and crushed pineapple — a chilled Southern dessert salad.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-refrigerator-cookies': {'action': 'edit', 'patch': {
        'name': 'Refrigerator cookies',
        'notes': 'A butter-sugar dough rolled into a log, chilled until firm, then sliced and baked — same as icebox cookies.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-crab-soup': {'action': 'edit', 'patch': {
        'name': 'Maryland crab soup',
        'notes': 'Lump crab and chopped vegetables simmered in a tomato-and-beef broth with Old Bay and a splash of sherry — Chesapeake-style.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-million-dollar-pound-cake': {'action': 'edit', 'patch': {
        'name': 'Million dollar pound cake',
        'notes': 'A classic pound cake with a high ratio of butter and eggs — exceptionally rich, fine-crumbed, and tall.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-marinated-chicken-wings': {'action': 'edit', 'patch': {
        'name': 'Marinated chicken wings',
        'tags': ['snack'],
        'notes': 'Chicken wings marinated in soy sauce, ginger, garlic, and brown sugar, then baked until sticky and bronzed.',
        'cuisine': 'American',
        'serving_grams': 170,
    }},
    'corpus-titled-hot-chicken-salad-casserole': {'action': 'edit', 'patch': {
        'name': 'Hot chicken salad casserole',
        'notes': 'Shredded chicken bound with mayo, celery, and water chestnuts, topped with crushed potato chips or cornflakes and cheese, baked hot.',
        'cuisine': 'American',
        'serving_grams': 320,
    }},
    'corpus-titled-hamburger-quiche': {'action': 'edit', 'patch': {
        'name': 'Hamburger quiche',
        'notes': 'A pastry shell filled with browned ground beef, onion, cheese, eggs, and cream, baked into a savory custard tart.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-chip-banana-bread': {'action': 'edit', 'patch': {
        'name': 'Chocolate chip banana bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'Banana bread folded with chocolate chips — moist quick bread with melty chocolate pockets.',
        'cuisine': 'American',
        'serving_grams': 90,
    }},
    'corpus-titled-peanut-butter-oatmeal-cookies': {'action': 'edit', 'patch': {
        'name': 'Peanut butter oatmeal cookies',
        'notes': 'Drop cookies of peanut butter, oats, butter, and brown sugar — chewy and protein-rich.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-banana-salad': {'action': 'edit', 'patch': {
        'name': 'Banana salad',
        'tags': ['dessert'],
        'notes': 'Sliced bananas tossed with a cooked custard dressing of egg, sugar, vinegar, and flour, topped with chopped peanuts — a Southern picnic dessert.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-mincemeat-cookies': {'action': 'edit', 'patch': {
        'name': 'Mincemeat cookies',
        'notes': 'Drop cookies of butter-sugar-and-egg dough folded with prepared mincemeat (spiced fruit-and-suet preserve) — holiday favorite.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-double-chocolate-brownies': {'action': 'edit', 'patch': {
        'name': 'Double chocolate brownies',
        'notes': 'Fudgy brownies made with both cocoa and melted chocolate, often with chocolate chips folded in — three forms of chocolate in one bar.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-creamy-potato-salad': {'action': 'edit', 'patch': {
        'name': 'Creamy potato salad',
        'notes': 'Boiled potatoes tossed with mayo, mustard, eggs, celery, sweet pickle, and onion — the classic picnic potato salad.',
        'cuisine': 'American',
    }},
    'corpus-titled-sour-cream-potatoes': {'action': 'edit', 'patch': {
        'name': 'Sour cream potatoes',
        'notes': 'Potato cubes baked with sour cream, butter, cream of chicken soup, and shredded cheese — funeral-potatoes variant.',
        'cuisine': 'American',
    }},
    'corpus-titled-barbecued-pork-chops': {'action': 'edit', 'patch': {
        'name': 'Barbecued pork chops',
        'notes': 'Pork chops baked or grilled and basted with a sweet-tangy barbecue sauce until lacquered.',
        'cuisine': 'American',
    }},
    'corpus-titled-s-tea-cakes': {'action': 'edit', 'patch': {
        'name': 'Sour cream tea cakes',
        'notes': 'A simple sugar-butter cookie enriched with sour cream — soft, lightly sweet, and nutmeg-scented in the Southern tradition.',
        'cuisine': 'Southern',
        'serving_grams': 60,
    }},
    'corpus-titled-angel-pie': {'action': 'edit', 'patch': {
        'name': 'Angel pie',
        'notes': 'A baked meringue shell filled with lemon curd and topped with sweetened whipped cream — sometimes with strawberries on top.',
        'cuisine': 'American',
    }},
    'corpus-titled-layer-salad': {'action': 'edit', 'patch': {
        'name': 'Layer salad (variant)',
        'notes': 'Lettuce, peas, onion, eggs, bacon, and cheese layered in a glass bowl, sealed under a mayo-and-sugar topping — chilled overnight.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-strawberry-rhubarb-pie': {'action': 'edit', 'patch': {
        'name': 'Strawberry rhubarb pie',
        'notes': 'A double-crust pie of sliced strawberries and rhubarb tossed with sugar and a thickener — sweet-tart with a pink interior.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-pizza': {'action': 'edit', 'patch': {
        'name': 'Chocolate pizza',
        'tags': ['dessert', 'snack'],
        'notes': 'A round of melted chocolate poured onto parchment and topped with chopped nuts, dried fruit, and crispy cereal — broken into pieces.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-blueberry-cheesecake': {'action': 'edit', 'patch': {
        'name': 'Blueberry cheesecake',
        'notes': 'A baked or no-bake cream-cheese cheesecake topped with blueberry pie filling on a graham crust.',
        'cuisine': 'American',
    }},
    'corpus-titled-special-k-bars': {'action': 'edit', 'patch': {
        'name': 'Special K bars',
        'tags': ['dessert', 'snack'],
        'notes': 'Special K cereal stirred into a hot peanut-butter-and-sugar syrup, pressed into a pan, and topped with melted chocolate and butterscotch.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-indian-fry-bread': {'action': 'edit', 'patch': {
        'name': 'Indian fry bread',
        'notes': 'A leavened flour-and-baking-powder dough rolled flat and deep-fried until puffed and golden — Native American (Navajo) staple, served with savory or sweet toppings.',
        'cuisine': 'Native American',
        'serving_grams': 100,
    }},
    'corpus-titled-chicken-divine': {'action': 'edit', 'patch': {
        'name': 'Chicken Divan (variant)',
        'notes': 'Cooked chicken and steamed broccoli baked in a sherry-and-curry-laced cream sauce topped with cheese and breadcrumbs.',
        'cuisine': 'American',
    }},
    'corpus-titled-baked-corn-casserole': {'action': 'edit', 'patch': {
        'name': 'Baked corn casserole',
        'notes': 'A spoon-bread-style bake of corn kernels, creamed corn, eggs, butter, and sour cream — sweet, custardy, almost pudding-like.',
        'cuisine': 'American',
    }},
    'corpus-titled-fresh-peach-cobbler': {'action': 'edit', 'patch': {
        'name': 'Fresh peach cobbler',
        'notes': 'Sliced fresh peaches baked under a buttery cake or biscuit topping — a Southern dessert served warm with ice cream.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-skillet-lasagna': {'action': 'edit', 'patch': {
        'name': 'Skillet lasagna',
        'notes': 'Broken lasagna noodles cooked in a skillet with ground beef, marinara, ricotta, and mozzarella — all the lasagna flavor in one pan.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-eggs-benedict': {'action': 'edit', 'patch': {
        'name': 'Eggs Benedict',
        'notes': 'Toasted English muffin halves topped with Canadian bacon, poached eggs, and hollandaise sauce — the brunch classic.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-chicken-fried-steak': {'action': 'edit', 'patch': {
        'name': 'Chicken fried steak',
        'notes': 'Cube steak dredged in seasoned flour and milk, pan-fried until crisp, and served smothered in milk-or-cream gravy — Texas comfort.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-zucchini-squares': {'action': 'edit', 'patch': {
        'name': 'Zucchini squares',
        'tags': ['snack'],
        'notes': 'Grated zucchini baked with eggs, flour, Parmesan, and herbs in a sheet pan, then cut into bite-size squares — appetizer family of zucchini appetizers.',
        'cuisine': 'Italian-American',
        'serving_grams': 60,
    }},
    'corpus-titled-polenta': {'action': 'edit', 'patch': {
        'name': 'Polenta',
        'notes': 'Coarse cornmeal simmered slowly in water or stock with butter and Parmesan until thick and creamy — Italian cornmeal porridge.',
        'cuisine': 'Italian',
    }},
    'corpus-titled-shoe-peg-corn-casserole': {'action': 'edit', 'patch': {
        'name': 'Shoepeg corn casserole',
        'notes': 'Canned white shoepeg corn baked with sour cream, butter, French-fried onions, and shredded cheese — a Midwestern potluck side.',
        'cuisine': 'American',
    }},
    'corpus-titled-maryland-crab-cakes': {'action': 'edit', 'patch': {
        'name': 'Maryland crab cakes',
        'tags': ['dinner', 'lunch'],
        'notes': 'Lump blue-crab bound with mayo, egg, and a small amount of breadcrumb (very little filler), seasoned with Old Bay and broiled or pan-fried.',
        'cuisine': 'American',
        'serving_grams': 170,
    }},
    'corpus-titled-pineapple-chicken': {'action': 'edit', 'patch': {
        'name': 'Pineapple chicken',
        'notes': 'Chicken pieces simmered in a sweet-sour sauce of pineapple, soy, vinegar, and brown sugar — served over rice with peppers.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-noodle-casserole': {'action': 'edit', 'patch': {
        'name': 'Noodle casserole',
        'notes': 'Cooked egg noodles baked with ground beef, mushrooms, peppers, and cheese in a tomato or cream-soup sauce.',
        'cuisine': 'American',
    }},
    'corpus-titled-steak-diane': {'action': 'edit', 'patch': {
        'name': 'Steak Diane',
        'notes': 'Pounded steaks pan-seared and finished in a pan sauce of butter, mushrooms, shallots, Worcestershire, mustard, cream, and brandy — flambéed tableside.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-salmon-spread': {'action': 'edit', 'patch': {
        'name': 'Salmon spread',
        'tags': ['snack'],
        'notes': 'Canned salmon mixed with cream cheese, lemon, horseradish, and chopped onion — chilled as a cracker spread.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-potato-leek-soup': {'action': 'edit', 'patch': {
        'name': 'Potato leek soup',
        'notes': 'Sliced leeks sweated in butter, simmered with potatoes and broth, then blended smooth and finished with cream — French country classic.',
        'cuisine': 'French',
    }},
    'corpus-titled-barbecue-cups': {'action': 'edit', 'patch': {
        'name': 'Barbecue cups',
        'tags': ['snack', 'dinner'],
        'notes': 'Browned ground beef simmered with barbecue sauce, brown sugar, and onion, spooned into biscuit-dough-lined muffin cups, topped with cheese, and baked.',
        'cuisine': 'American',
        'serving_grams': 100,
    }},
    'corpus-titled-onion-dip': {'action': 'edit', 'patch': {
        'name': 'Onion dip',
        'tags': ['snack'],
        'notes': 'Sour cream mixed with a packet of Lipton onion soup mix — the original chip-and-dip pairing.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-welsh-rarebit': {'action': 'edit', 'patch': {
        'name': 'Welsh rarebit',
        'tags': ['dinner', 'lunch'],
        'notes': 'A bechamel-based melted cheddar sauce flavored with beer, mustard, and Worcestershire, poured hot over toast and broiled.',
        'cuisine': 'British',
        'contains_add': ['alcohol'],
        'serving_grams': 200,
    }},
    'corpus-titled-pineapple-coconut-pie': {'action': 'edit', 'patch': {
        'name': 'Pineapple coconut pie',
        'notes': 'A custard pie of eggs, sugar, butter, crushed pineapple, and shredded coconut baked in a single crust.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-strawberry-nut-salad': {'action': 'edit', 'patch': {
        'name': 'Strawberry nut salad',
        'tags': ['dessert'],
        'notes': 'Strawberry Jello set with crushed pineapple, frozen strawberries, and chopped pecans, layered with sour cream — Southern dessert salad.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-marinated-shrimp': {'action': 'edit', 'patch': {
        'name': 'Marinated shrimp',
        'tags': ['snack'],
        'notes': 'Cooked shrimp tossed with sliced onions, capers, lemon, and an oil-and-vinegar marinade — chilled overnight as an appetizer.',
        'cuisine': 'American',
        'serving_grams': 120,
    }},
    'corpus-titled-shoo-fly-cake': {'action': 'edit', 'patch': {
        'name': 'Shoofly cake',
        'notes': 'A Pennsylvania Dutch cake-style version of shoofly pie — molasses-and-water layer baked under a sandy crumb topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-corned-beef-hash': {'action': 'edit', 'patch': {
        'name': 'Corned beef hash',
        'tags': ['breakfast', 'dinner'],
        'notes': 'Diced cooked potatoes and chopped corned beef pan-fried with onions and peppers until crisp — served with eggs at diner breakfast.',
        'cuisine': 'American',
    }},
    'corpus-titled-shrimp-mousse': {'action': 'edit', 'patch': {
        'name': 'Shrimp mousse',
        'tags': ['snack'],
        'notes': 'A molded appetizer of chopped shrimp folded into cream cheese, mayo, and gelatin, set in a fish-shaped mold and turned out — served with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-spiced-peaches': {'action': 'drop', 'reason': 'spiced fruit preserve / pickle, not a coherent meal'},
    'corpus-titled-shrimp-cocktail': {'action': 'edit', 'patch': {
        'name': 'Shrimp cocktail',
        'tags': ['snack'],
        'notes': 'Poached chilled shrimp served with a horseradish-laced tomato-ketchup cocktail sauce — a classic appetizer.',
        'cuisine': 'American',
        'serving_grams': 120,
    }},
    'corpus-titled-brown-sugar-pie': {'action': 'edit', 'patch': {
        'name': 'Brown sugar pie',
        'notes': 'A Quebec/Southern chess-pie variant of brown sugar, butter, eggs, flour, and a splash of milk or cream baked in a single crust — caramel-toned.',
        'cuisine': 'American',
    }},
    'corpus-titled-shrimp-curry': {'action': 'edit', 'patch': {
        'name': 'Shrimp curry',
        'notes': 'Shrimp simmered in a curry-spiced cream or coconut sauce with peppers and onions — served over rice with chutney.',
    }},
    'corpus-titled-ham-delights': {'action': 'edit', 'patch': {
        'name': 'Ham delights',
        'tags': ['snack'],
        'notes': 'Hawaiian sweet rolls split, filled with ham and Swiss, brushed with a butter-mustard-poppy-seed-onion glaze, and baked until melty.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-french-fried-onion-rings': {'action': 'edit', 'patch': {
        'name': 'French-fried onion rings',
        'tags': ['snack', 'dinner'],
        'notes': 'Sliced onion rings dipped in a milk-and-egg batter, dredged in seasoned flour, and deep-fried until crisp and golden.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-string-bean-casserole': {'action': 'edit', 'patch': {
        'name': 'String bean casserole',
        'ingredient_categories': ['Other vegetables', 'Mushrooms', 'Milk', 'Aged cheese', 'Baked snacks & pastries'],
        'notes': 'Green beans baked in cream-of-mushroom soup with milk and topped with crispy fried onions — the Campbell\'s green-bean casserole.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-liver-pate': {'action': 'edit', 'patch': {
        'name': 'Chicken liver pâté',
        'tags': ['snack'],
        'notes': 'Chicken livers sautéed with onions and herbs, then blended smooth with butter, brandy, and seasonings — chilled and served with toasts.',
        'cuisine': 'French',
        'contains_add': ['alcohol'],
        'serving_grams': 60,
    }},
    'corpus-titled-indian-pudding': {'action': 'edit', 'patch': {
        'name': 'Indian pudding',
        'notes': 'Cornmeal slow-baked in milk with molasses, butter, eggs, and warm spices — a New England colonial dessert served warm with cream or ice cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-wild-rice-salad': {'action': 'edit', 'patch': {
        'name': 'Wild rice salad',
        'notes': 'Cooked wild and long-grain rice tossed with chicken or turkey, dried cranberries, pecans, peppers, and a citrus vinaigrette.',
        'cuisine': 'American',
    }},
    'corpus-titled-glazed-pecans': {'action': 'edit', 'patch': {
        'name': 'Glazed pecans',
        'tags': ['snack'],
        'notes': 'Pecan halves coated in an egg-white-and-sugar slurry with cinnamon and salt, baked slowly until crisp — same family as candied/spiced pecans.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-banana-pancakes': {'action': 'edit', 'patch': {
        'name': 'Banana pancakes',
        'notes': 'Buttermilk pancake batter folded with mashed banana and a touch of cinnamon — served with maple syrup or fresh fruit.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-broccoli-slaw': {'action': 'edit', 'patch': {
        'name': 'Broccoli slaw (ramen)',
        'notes': 'Bagged broccoli slaw tossed with crushed ramen noodles, slivered almonds, sesame seeds, and a soy-vinegar-sugar dressing — chilled.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-chex-party-mix': {'action': 'edit', 'patch': {
        'name': 'Chex party mix (canonical)',
        'tags': ['snack'],
        'notes': 'Chex cereals, pretzels, and mixed nuts coated in a buttery Worcestershire-and-seasoning blend, then baked until crisp — the canonical Chex Mix recipe.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-chicken-vegetable-soup': {'action': 'edit', 'patch': {
        'name': 'Chicken vegetable soup',
        'notes': 'Chicken simmered with mixed vegetables, herbs, and broth — a clear-broth weeknight soup, often with rice or noodles.',
    }},
    'corpus-titled-apple-pound-cake': {'action': 'edit', 'patch': {
        'name': 'Apple pound cake',
        'notes': 'A dense oil-based pound cake folded with diced fresh apples and pecans, often soaked with a caramel-brown-sugar glaze.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-busy-day-casserole': {'action': 'edit', 'patch': {
        'name': 'Busy day casserole',
        'notes': 'A 1950s pantry casserole of ground beef, peppers, rice, mushroom soup, and tomato baked together with cheese on top — minimal prep.',
        'cuisine': 'American',
    }},
    'corpus-titled-pumpkin-pudding': {'action': 'edit', 'patch': {
        'name': 'Pumpkin pudding',
        'notes': 'Pumpkin puree, eggs, sugar, evaporated milk, and warm spices baked in a dish without a crust — pumpkin pie filling, crustless.',
        'cuisine': 'American',
    }},
    'corpus-titled-biscotti': {'action': 'edit', 'patch': {
        'name': 'Biscotti',
        'notes': 'A twice-baked Italian almond cookie — dough baked in a log, sliced, then baked again until dry and crisp, made for dipping in coffee or wine.',
        'cuisine': 'Italian',
        'serving_grams': 30,
    }},
    'corpus-titled-whipping-cream-pound-cake': {'action': 'edit', 'patch': {
        'name': 'Whipping cream pound cake',
        'notes': 'A dense pound cake enriched with heavy whipping cream in place of butter — exceptionally moist, tender, and fine-crumbed.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-caramel-apple-salad': {'action': 'edit', 'patch': {
        'name': 'Caramel apple salad',
        'tags': ['dessert'],
        'notes': 'Diced apples, crushed pineapple, and peanuts folded with a cooked egg-and-flour dressing (mimicking caramel-apple coating) and whipped topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-crabmeat-casserole': {'action': 'edit', 'patch': {
        'name': 'Crabmeat casserole',
        'notes': 'Lump crab mixed with mayonnaise, eggs, milk, and seasonings, baked under buttered cracker crumbs and cheese — a Chesapeake casserole.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-continental': {'action': 'edit', 'patch': {
        'name': 'Chicken Continental',
        'notes': 'Chicken pieces baked with raw rice in cream of mushroom soup and onion soup mix — same family as no-peek chicken.',
        'cuisine': 'American',
    }},
    'corpus-titled-pizza-hot-dish': {'action': 'edit', 'patch': {
        'name': 'Pizza hot dish',
        'notes': 'Cooked pasta layered with ground beef, pepperoni, marinara, and mozzarella, baked until bubbly — a Midwestern "hot dish" pizza casserole.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-pumpkin-pie-squares': {'action': 'edit', 'patch': {
        'name': 'Pumpkin pie squares',
        'tags': ['dessert'],
        'notes': 'A pumpkin-pie filling poured over a yellow-cake-mix-and-butter crust, topped with cinnamon-streusel and chopped pecans, baked into bars.',
        'cuisine': 'American',
        'serving_grams': 100,
    }},
    'corpus-titled-apricot-jello-salad': {'action': 'edit', 'patch': {
        'name': 'Apricot Jello salad',
        'tags': ['dessert'],
        'notes': 'Orange Jello set with canned apricots, crushed pineapple, and miniature marshmallows, layered with a cream-cheese-and-whipped-topping topping.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-banana-ice-cream': {'action': 'edit', 'patch': {
        'name': 'Banana ice cream',
        'notes': 'A custard ice cream churned with pureed ripe bananas, milk, cream, sugar, and egg yolks.',
        'serving_grams': 85,
    }},
    'corpus-titled-creamy-coleslaw': {'action': 'edit', 'patch': {
        'name': 'Creamy coleslaw',
        'notes': 'Shredded cabbage and carrot dressed in a sweet mayo-and-vinegar dressing with celery seed — KFC-style classic.',
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

    print('corpus-titled batch-10 audit applied (entries 1351-1500 by frequency).')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
