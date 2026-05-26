"""Corpus-titled meals audit — batch 12 (entries 1651-1800 by frequency, 73 -> 68)."""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

DECISIONS: dict[str, dict] = {
    'corpus-titled-cream-puff-cake': {'action': 'edit', 'patch': {
        'name': 'Cream puff cake',
        'notes': 'A pâte-à-choux base baked in a sheet pan, then topped with vanilla pudding mixed with cream cheese and finished with whipped topping and chocolate drizzle.',
        'cuisine': 'American',
    }},
    'corpus-titled-chile-con-queso': {'action': 'edit', 'patch': {
        'name': 'Chile con queso',
        'tags': ['snack'],
        'notes': 'Processed cheese melted with green chiles, tomatoes, onion, and cumin — served warm as a Tex-Mex dipping sauce for tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-cheese-enchiladas': {'action': 'edit', 'patch': {
        'name': 'Cheese enchiladas',
        'notes': 'Corn tortillas dipped in red chile sauce, rolled around shredded cheese and onion, baked in more sauce and topped with cheese — vegetarian Tex-Mex.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-salmon-chowder': {'action': 'edit', 'patch': {
        'name': 'Salmon chowder',
        'notes': 'Diced potatoes and salmon simmered in chicken broth with onions and dill, finished with milk and cream — Pacific-Northwest style.',
        'cuisine': 'American',
    }},
    'corpus-titled-strawberry-spinach-salad': {'action': 'edit', 'patch': {
        'name': 'Strawberry spinach salad',
        'notes': 'Baby spinach tossed with sliced strawberries, red onion, and toasted almonds in a poppy-seed-and-balsamic vinaigrette.',
        'cuisine': 'American',
    }},
    'corpus-titled-carnitas': {'action': 'edit', 'patch': {
        'name': 'Carnitas',
        'notes': 'Pork shoulder slow-braised with citrus, onion, and Mexican spices until tender, then crisped — served in tortillas with onion, cilantro, and salsa.',
        'cuisine': 'Mexican',
    }},
    'corpus-titled-moroccan-chicken': {'action': 'edit', 'patch': {
        'name': 'Moroccan chicken',
        'notes': 'Chicken braised with preserved lemon, olives, dried fruit (apricots or prunes), onion, and warm spices like cumin, cinnamon, and ginger — tagine-style.',
        'cuisine': 'Moroccan',
    }},
    'corpus-titled-delicious': {'action': 'drop', 'reason': 'corpus-title artifact ("& Delicious"), not a coherent meal'},
    'corpus-titled-pizza-cups': {'action': 'edit', 'patch': {
        'name': 'Pizza cups',
        'tags': ['snack'],
        'notes': 'Browned ground beef simmered in pizza sauce and pepperoni, spooned into biscuit-dough-lined muffin cups, topped with mozzarella, and baked.',
        'cuisine': 'American',
        'contains_add': ['pork'],
        'serving_grams': 100,
    }},
    'corpus-titled-church-windows': {'action': 'edit', 'patch': {
        'name': 'Church windows',
        'tags': ['dessert'],
        'notes': 'A no-bake confection of melted chocolate stirred with colored mini marshmallows and chopped nuts, rolled into a log and sliced into stained-glass-pattern rounds.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-potatoes-romanoff': {'action': 'edit', 'patch': {
        'name': 'Potatoes Romanoff',
        'notes': 'Shredded or sliced cooked potatoes mixed with sour cream, cottage cheese, garlic, and shredded cheese, baked until hot and bubbly.',
        'cuisine': 'American',
    }},
    'corpus-titled-squash-souffle': {'action': 'edit', 'patch': {
        'name': 'Squash soufflé',
        'notes': 'Cooked yellow squash mashed with eggs, butter, sugar, and milk and baked under a buttered cracker top until puffed.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-three-bean-casserole': {'action': 'edit', 'patch': {
        'name': 'Three bean casserole',
        'notes': 'Mixed beans baked with ground beef, bacon, brown sugar, and barbecue sauce — same family as calico beans / cowboy beans.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-chocolate-mousse-pie': {'action': 'edit', 'patch': {
        'name': 'Chocolate mousse pie',
        'notes': 'A chocolate cookie crust filled with an airy chocolate mousse of melted chocolate, whipped cream, and beaten egg whites — chilled and served with whipped cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-black-magic-cake': {'action': 'edit', 'patch': {
        'name': 'Black magic cake',
        'notes': 'A buttermilk-and-oil cocoa cake brought to extra moistness with strong brewed coffee in the batter — tall, tender, and intensely chocolate.',
        'cuisine': 'American',
    }},
    'corpus-titled-impossible-taco-pie': {'action': 'edit', 'patch': {
        'name': 'Impossible taco pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'Seasoned ground beef and Tex-Mex toppings baked under a Bisquick-egg-milk crust that self-crusts as it bakes — taco flavors in pie form.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 320,
    }},
    'corpus-titled-instant-spiced-tea': {'action': 'edit', 'patch': {
        'name': 'Instant spiced tea',
        'ingredient_categories': ['Coffee & tea', 'Juices', 'Sugar & sweeteners', 'Whole spices', 'Ground spices', 'Citrus'],
        'tags': ['snack'],
        'notes': 'A pantry mix of instant tea, powdered Tang, sugar, and warm spices — stirred into hot water; same family as Russian/friendship tea.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-chicken-loaf': {'action': 'edit', 'patch': {
        'name': 'Chicken loaf',
        'notes': 'Ground or finely chopped cooked chicken bound with breadcrumbs, eggs, milk, and seasonings, baked in a loaf — a leftover-chicken meatloaf.',
        'cuisine': 'American',
    }},
    'corpus-titled-turkey-loaf': {'action': 'edit', 'patch': {
        'name': 'Turkey loaf',
        'notes': 'Ground turkey bound with breadcrumbs, eggs, herbs, and onion, baked in a loaf with a ketchup glaze — a leaner meatloaf.',
        'cuisine': 'American',
    }},
    'corpus-titled-italian-spaghetti': {'action': 'edit', 'patch': {
        'name': 'Italian spaghetti',
        'notes': 'Spaghetti topped with a long-simmered tomato sauce of ground beef, onions, garlic, peppers, and Italian herbs — finished with Parmesan.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-cherry-cream-cheese-pie': {'action': 'edit', 'patch': {
        'name': 'Cherry cream cheese pie',
        'notes': 'A no-bake pie of sweetened cream cheese filling in a graham crust, topped with canned cherry pie filling.',
        'cuisine': 'American',
    }},
    'corpus-titled-oreo-delight': {'action': 'edit', 'patch': {
        'name': 'Oreo delight',
        'tags': ['dessert'],
        'notes': 'A no-bake layered dessert of crushed Oreos, sweetened cream cheese, chocolate or vanilla pudding, and whipped topping — same family as dirt pudding.',
        'cuisine': 'American',
    }},
    'corpus-titled-stuffed-celery': {'action': 'edit', 'patch': {
        'name': 'Stuffed celery',
        'tags': ['snack'],
        'notes': 'Celery stalks cut into pieces and filled with sweetened cream cheese, pimento cheese, or peanut butter — a retro relish-tray appetizer.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-pineapple-cream-pie': {'action': 'edit', 'patch': {
        'name': 'Pineapple cream pie',
        'notes': 'A baked or no-bake pie of vanilla cream filling mixed with crushed pineapple, in a graham crust, topped with whipped cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-nanaimo-bars': {'action': 'edit', 'patch': {
        'name': 'Nanaimo bars',
        'tags': ['dessert'],
        'notes': 'A three-layer no-bake Canadian bar — a chocolate-coconut-graham crust, a vanilla custard buttercream middle, and a chocolate top.',
        'cuisine': 'Canadian',
        'serving_grams': 60,
    }},
    'corpus-titled-barbecue-spareribs': {'action': 'edit', 'patch': {
        'name': 'Barbecue spareribs',
        'notes': 'Pork spareribs slow-roasted or grilled and basted with a sweet-tangy barbecue sauce until the meat pulls cleanly from the bone.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-zucchini-brownies': {'action': 'edit', 'patch': {
        'name': 'Zucchini brownies',
        'notes': 'A moist cocoa brownie made with oil and grated zucchini — chewy, dairy-free, and packed with chocolate chips and walnuts.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-asparagus-soup': {'action': 'edit', 'patch': {
        'name': 'Asparagus soup',
        'notes': 'Asparagus simmered with onion and broth, blended smooth, and finished with cream and butter — a springtime classic.',
    }},
    'corpus-titled-tortillas': {'action': 'edit', 'patch': {
        'name': 'Flour tortillas (homemade)',
        'notes': 'Soft unleavened wheat flatbreads of flour, salt, water, and shortening or lard — rolled thin and griddled.',
        'cuisine': 'Mexican',
        'serving_grams': 55,
    }},
    'corpus-titled-zucchini-chocolate-cake': {'action': 'edit', 'patch': {
        'name': 'Zucchini chocolate cake',
        'notes': 'A moist cocoa cake folded with grated zucchini and chocolate chips — vegetable garden meets chocolate dessert.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-corn-chowder': {'action': 'edit', 'patch': {
        'name': 'Chicken corn chowder',
        'notes': 'Sweet corn and diced chicken simmered in a milk-or-cream base with potatoes, onion, and herbs.',
        'cuisine': 'American',
    }},
    'corpus-titled-italian-bread': {'action': 'edit', 'patch': {
        'name': 'Italian bread',
        'notes': 'A crusty oval yeasted loaf of flour, water, yeast, salt, and a touch of olive oil and sugar — pliable interior, deep golden crust.',
        'cuisine': 'Italian-American',
        'serving_grams': 55,
    }},
    'corpus-titled-pumpkin-dip': {'action': 'edit', 'patch': {
        'name': 'Pumpkin dip',
        'tags': ['snack', 'dessert'],
        'notes': 'Cream cheese whipped with pumpkin puree, powdered sugar, and warm spices — served with ginger snaps or apple slices.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-crustless-quiche': {'action': 'edit', 'patch': {
        'name': 'Crustless quiche',
        'notes': 'Eggs, cream, cheese, and fillings (ham, broccoli, mushrooms) baked in a buttered pie dish without a pastry crust — a low-carb quiche.',
        'cuisine': 'French',
    }},
    'corpus-titled-fish-stew': {'action': 'edit', 'patch': {
        'name': 'Fish stew',
        'notes': 'Cubed white fish simmered with tomatoes, onions, peppers, potatoes, and herbs in broth — a Mediterranean coastal stew.',
    }},
    'corpus-titled-armadillo-eggs': {'action': 'edit', 'patch': {
        'name': 'Armadillo eggs',
        'tags': ['snack'],
        'notes': 'Cream cheese-stuffed jalapeños wrapped in seasoned ground sausage, coated in shake-and-bake or breadcrumbs, and baked — Texan tailgate appetizer.',
        'cuisine': 'Tex-Mex',
        'contains_add': ['pork'],
        'serving_grams': 80,
    }},
    'corpus-titled-roasted-chicken': {'action': 'edit', 'patch': {
        'name': 'Roasted chicken',
        'notes': 'A whole chicken seasoned inside and out with salt, herbs, and butter, then roasted hot until the skin is crisp and golden.',
        'cuisine': 'American',
    }},
    'corpus-titled-tamale-casserole': {'action': 'edit', 'patch': {
        'name': 'Tamale casserole',
        'notes': 'Seasoned ground beef and corn baked under a cornmeal batter or layered with tamales — Tex-Mex casserole adaptation of tamale pie.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-cabbage-and-noodles': {'action': 'edit', 'patch': {
        'name': 'Cabbage and noodles',
        'notes': 'Shredded cabbage and onion sautéed in butter until softened, tossed with cooked egg noodles — a Hungarian/Polish comfort dish (haluski).',
        'cuisine': 'Eastern European',
    }},
    'corpus-titled-cream-cheese-squares': {'action': 'edit', 'patch': {
        'name': 'Cream cheese squares (sopapilla)',
        'tags': ['dessert'],
        'notes': 'Crescent-roll dough sandwiched around a sweetened cream-cheese filling, topped with cinnamon-sugar butter, and baked — sopapilla cheesecake bars.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-no-bake-peanut-butter-cookies': {'action': 'edit', 'patch': {
        'name': 'No-bake peanut butter cookies',
        'notes': 'Sugar, milk, butter, and peanut butter cooked to a fudge, stirred with oats, and dropped onto wax paper to set.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-barbecue-shrimp': {'action': 'edit', 'patch': {
        'name': 'New Orleans barbecue shrimp',
        'notes': 'Whole shrimp baked in a buttery-garlicky-Worcestershire-pepper sauce — served peel-on with crusty bread for sopping; "barbecue" in name only.',
        'cuisine': 'Creole',
    }},
    'corpus-titled-turkey-stuffing': {'action': 'edit', 'patch': {
        'name': 'Turkey stuffing',
        'notes': 'Cubed bread mixed with sautéed onions, celery, sage, broth, and butter, sometimes with sausage — stuffed in the bird or baked separately.',
        'cuisine': 'American',
    }},
    'corpus-titled-scalloped-potatoes-and-ham': {'action': 'edit', 'patch': {
        'name': 'Scalloped potatoes and ham',
        'notes': 'Sliced potatoes and cubed ham baked in a milk-and-cheese sauce — a leftover-ham one-dish meal.',
        'cuisine': 'American',
    }},
    'corpus-titled-barbecue-brisket': {'action': 'edit', 'patch': {
        'name': 'Barbecue brisket',
        'notes': 'A whole beef brisket rubbed with spices, slow-smoked or oven-braised at low heat, sliced against the grain and served with barbecue sauce.',
        'cuisine': 'American',
    }},
    'corpus-titled-turkey-soup': {'action': 'edit', 'patch': {
        'name': 'Turkey soup',
        'notes': 'Leftover turkey carcass simmered into broth with vegetables, herbs, and rice or noodles — a Thanksgiving-leftover stockpot soup.',
        'cuisine': 'American',
    }},
    'corpus-titled-brandy-slush': {'action': 'edit', 'patch': {
        'name': 'Brandy slush',
        'ingredient_categories': ['Juices', 'Citrus', 'Sugar & sweeteners', 'Alcoholic beverages', 'Coffee & tea', 'Soft drinks'],
        'tags': ['snack'],
        'notes': 'Frozen fruit-juice-and-tea concentrate spiked with brandy, then topped with lemon-lime soda at serving — a Midwestern party slushie.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
        'serving_grams': 240,
    }},
    'corpus-titled-leek-and-potato-soup': {'action': 'edit', 'patch': {
        'name': 'Leek and potato soup',
        'notes': 'Sliced leeks sweated in butter and simmered with potatoes in chicken stock, then blended smooth and finished with cream — French country classic.',
        'cuisine': 'French',
    }},
    'corpus-titled-frog-eye-salad': {'action': 'edit', 'patch': {
        'name': 'Frog eye salad',
        'tags': ['dessert'],
        'notes': 'Cooked acini di pepe pasta folded with crushed pineapple, mandarin oranges, marshmallows, and whipped topping — a Mormon-Midwest dessert salad.',
        'cuisine': 'American',
    }},
    'corpus-titled-lemon-cheese-cake': {'action': 'edit', 'patch': {
        'name': 'Lemon cheesecake (variant)',
        'notes': 'A cream-cheese cheesecake brightened with lemon juice and zest, set on a graham crust and topped with lemon curd or whipped cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-banana-chocolate-chip-muffins': {'action': 'edit', 'patch': {
        'name': 'Banana chocolate chip muffins',
        'tags': ['breakfast', 'snack'],
        'notes': 'Tender muffins of mashed banana, butter, eggs, and flour folded with chocolate chips — banana bread\'s portion-control cousin.',
        'serving_grams': 60,
    }},
    'corpus-titled-s-banana-bread': {'action': 'edit', 'patch': {
        'name': 'Sour cream banana bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'Banana bread made extra moist by sour cream stirred into the batter, often folded with chopped walnuts or pecans.',
        'cuisine': 'American',
    }},
    'corpus-titled-sweet-potato-bake': {'action': 'edit', 'patch': {
        'name': 'Sweet potato bake',
        'notes': 'Mashed sweet potatoes whipped with eggs, butter, sugar, and milk, baked under a brown-sugar-pecan streusel — the Ruth\'s Chris style.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-apple-torte': {'action': 'edit', 'patch': {
        'name': 'Apple torte',
        'tags': ['dessert'],
        'notes': 'A short-crust base topped with sliced apples and a butter-sugar-cinnamon syrup, baked into a thin layered cake.',
        'cuisine': 'German',
        'serving_grams': 140,
    }},
    'corpus-titled-tomatillo-salsa': {'action': 'edit', 'patch': {
        'name': 'Tomatillo salsa (salsa verde)',
        'tags': ['snack', 'condiment'],
        'notes': 'Tomatillos, jalapeños, onion, garlic, cilantro, and lime blended into a tangy green salsa — Mexican style.',
        'cuisine': 'Mexican',
        'serving_grams': 60,
    }},
    'corpus-titled-marinated-chicken': {'action': 'edit', 'patch': {
        'name': 'Marinated chicken',
        'notes': 'Chicken pieces marinated in Italian dressing or a soy-garlic-citrus mixture and then grilled, baked, or broiled.',
        'cuisine': 'American',
    }},
    'corpus-titled-caramelized-onions': {'action': 'edit', 'patch': {
        'name': 'Caramelized onions',
        'tags': ['condiment'],
        'notes': 'Sliced onions cooked low and slow in butter and oil until deeply golden and jammy — a topping for burgers, pizza, soups, and steaks.',
        'serving_grams': 60,
    }},
    'corpus-titled-basil-pesto': {'action': 'edit', 'patch': {
        'name': 'Basil pesto',
        'tags': ['condiment'],
        'notes': 'Fresh basil, pine nuts, garlic, Parmesan, and olive oil pounded or blended into a green sauce — a Genoese classic for pasta or bread.',
        'cuisine': 'Italian',
        'serving_grams': 30,
    }},
    'corpus-titled-peanut-butter-cream-pie': {'action': 'edit', 'patch': {
        'name': 'Peanut butter cream pie',
        'notes': 'A baked pastry shell filled with vanilla pastry cream blended with peanut butter, topped with whipped cream and chopped peanuts.',
        'cuisine': 'American',
    }},
    'corpus-titled-cabbage-patch-stew': {'action': 'edit', 'patch': {
        'name': 'Cabbage patch stew',
        'notes': 'Ground beef simmered with shredded cabbage, kidney beans, tomatoes, peppers, and chili spices — a stovetop pantry stew.',
        'cuisine': 'American',
    }},
    'corpus-titled-no-crust-coconut-pie': {'action': 'edit', 'patch': {
        'name': 'No-crust coconut pie',
        'notes': 'A blender custard of eggs, milk, sugar, butter, coconut, and a touch of flour — self-crusts as it bakes; no pastry shell needed.',
        'cuisine': 'American',
    }},
    'corpus-titled-pink-punch': {'action': 'edit', 'patch': {
        'name': 'Pink punch',
        'ingredient_categories': ['Juices', 'Tropical fruits', 'Berries', 'Citrus', 'Sugar & sweeteners', 'Soft drinks'],
        'tags': ['snack'],
        'notes': 'A non-alcoholic pink punch of cranberry or strawberry juice with pineapple juice and ginger ale — for showers and weddings.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-vichyssoise': {'action': 'edit', 'patch': {
        'name': 'Vichyssoise',
        'notes': 'A cold leek-and-potato soup blended smooth and enriched with heavy cream — Louis Diat\'s French-by-way-of-New-York creation.',
        'cuisine': 'French',
        'serving_grams': 240,
    }},
    'corpus-titled-blueberry-crisp': {'action': 'edit', 'patch': {
        'name': 'Blueberry crisp',
        'tags': ['dessert'],
        'notes': 'Sweetened fresh blueberries baked under a crunchy oat-and-butter streusel — served warm with ice cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-rye-bread': {'action': 'edit', 'patch': {
        'name': 'Rye bread',
        'notes': 'A yeasted loaf of rye flour blended with bread flour, often flavored with caraway seeds and molasses — dense, tangy, and slice-friendly.',
        'cuisine': 'German',
        'serving_grams': 55,
    }},
    'corpus-titled-honey-butter': {'action': 'edit', 'patch': {
        'name': 'Honey butter',
        'tags': ['condiment'],
        'notes': 'Softened butter whipped with honey and a pinch of salt — a sweet spread for biscuits, cornbread, and pancakes.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-pecan-squares': {'action': 'edit', 'patch': {
        'name': 'Pecan squares',
        'tags': ['dessert'],
        'notes': 'A shortbread crust topped with pecan-pie custard, baked and cut into squares — pecan pie in finger-food form.',
        'cuisine': 'Southern',
        'serving_grams': 60,
    }},
    'corpus-titled-layered-bean-dip': {'action': 'edit', 'patch': {
        'name': 'Layered bean dip',
        'tags': ['snack'],
        'notes': 'Refried beans layered with sour cream, salsa, shredded cheese, lettuce, olives, and onions — served chilled with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-chicken-rolls': {'action': 'edit', 'patch': {
        'name': 'Chicken rolls',
        'notes': 'Crescent-roll dough wrapped around a chicken-and-cream-cheese filling, baked, and served with a cream-soup gravy.',
        'cuisine': 'American',
    }},
    'corpus-titled-sweet-and-sour-carrots': {'action': 'edit', 'patch': {
        'name': 'Sweet and sour carrots (copper pennies)',
        'notes': 'Sliced cooked carrots ("pennies") tossed with bell peppers and onion in a tangy tomato-soup-and-vinegar marinade — chilled overnight.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-hamburger-vegetable-soup': {'action': 'edit', 'patch': {
        'name': 'Hamburger vegetable soup',
        'notes': 'Ground beef simmered with mixed vegetables, tomato, and pasta or barley in beef broth — a stockpot weeknight soup.',
        'cuisine': 'American',
    }},
    'corpus-titled-okra-and-tomatoes': {'action': 'edit', 'patch': {
        'name': 'Okra and tomatoes',
        'notes': 'Sliced okra stewed with tomatoes, onions, peppers, and bacon — a Southern summer side, also a base for gumbo.',
        'cuisine': 'Southern',
        'contains_add': ['pork'],
    }},
    'corpus-titled-spring-salad': {'action': 'edit', 'patch': {
        'name': 'Spring salad',
        'notes': 'A light salad of seasonal greens, citrus, herbs, and a bright vinaigrette — meant to capture the freshness of early-season vegetables.',
    }},
    'corpus-titled-poor-man-s-cake': {'action': 'edit', 'patch': {
        'name': "Poor man's cake",
        'notes': 'A Depression-era spice cake with no eggs, milk, or butter — boiled raisins, brown sugar, water, shortening, and warm spices make a moist, frugal cake.',
        'cuisine': 'American',
    }},
    'corpus-titled-tuna-dip': {'action': 'edit', 'patch': {
        'name': 'Tuna dip',
        'tags': ['snack'],
        'notes': 'Canned tuna whipped with cream cheese, mayo, lemon, onion, and seasonings — served chilled with crackers or vegetables.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-no-bake-chocolate-oatmeal-cookies': {'action': 'edit', 'patch': {
        'name': 'No-bake chocolate oatmeal cookies',
        'notes': 'Cocoa, sugar, milk, and butter boiled to a fudge, stirred with peanut butter and oats, and dropped onto wax paper to set.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-texas-cake': {'action': 'edit', 'patch': {
        'name': 'Texas sheet cake (variant)',
        'notes': 'A thin chocolate-buttermilk sheet cake topped warm with a poured cocoa-pecan icing that sets to a fudge-like crust.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-chocolate-chip-pudding-cookies': {'action': 'edit', 'patch': {
        'name': 'Chocolate chip pudding cookies',
        'notes': 'Drop cookies of butter, brown sugar, eggs, instant pudding mix, and chocolate chips — the pudding keeps the cookies soft for days.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-green-rice-casserole': {'action': 'edit', 'patch': {
        'name': 'Green rice casserole',
        'notes': 'Cooked rice baked with broccoli or spinach, cream of mushroom soup, butter, and processed cheese — a Southern potluck side.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-gnocchi': {'action': 'edit', 'patch': {
        'name': 'Gnocchi',
        'notes': 'Soft Italian dumplings of mashed potato, flour, and egg — boiled briefly and sauced with butter-sage, marinara, or pesto.',
        'cuisine': 'Italian',
    }},
    'corpus-titled-pineapple-drop-cookies': {'action': 'edit', 'patch': {
        'name': 'Pineapple drop cookies',
        'notes': 'A soft drop cookie made with crushed pineapple folded into a butter-sugar-egg batter, sometimes glazed.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-salmon-salad': {'action': 'edit', 'patch': {
        'name': 'Salmon salad',
        'notes': 'Canned or cooked salmon tossed with celery, sweet pickles, eggs, and a lemon-mayo dressing — served chilled on greens or in sandwiches.',
        'cuisine': 'American',
    }},
    'corpus-titled-donuts': {'action': 'edit', 'patch': {
        'name': 'Doughnuts',
        'tags': ['dessert', 'breakfast'],
        'notes': 'A leavened or cake-style ring of dough deep-fried and finished with glaze, sugar, or cinnamon-sugar.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-ice-cream-sandwiches': {'action': 'edit', 'patch': {
        'name': 'Ice cream sandwiches',
        'notes': 'Softened ice cream sandwiched between two cookies (chocolate wafers, oatmeal cookies, or brownies), then frozen until firm.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-pineapple-zucchini-bread': {'action': 'edit', 'patch': {
        'name': 'Pineapple zucchini bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A spiced quick bread folded with grated zucchini, crushed pineapple, raisins, and walnuts — moist with a tender crumb.',
        'cuisine': 'American',
    }},
    'corpus-titled-rhubarb-upside-down-cake': {'action': 'edit', 'patch': {
        'name': 'Rhubarb upside-down cake',
        'notes': 'A skillet cake baked over rhubarb arranged in a brown-sugar-butter glaze with strawberry Jello — inverted to serve.',
        'cuisine': 'American',
    }},
    'corpus-titled-coffee-punch': {'action': 'edit', 'patch': {
        'name': 'Coffee punch',
        'ingredient_categories': ['Coffee & tea', 'Milk', 'Frozen dairy', 'Cream & butter', 'Sugar & sweeteners', 'Extracts & essences'],
        'tags': ['snack'],
        'notes': 'Cold strong coffee mixed with milk, sugar, and vanilla, ladled over scoops of vanilla ice cream — a Southern shower punch.',
        'cuisine': 'Southern',
        'serving_grams': 240,
    }},
    'corpus-titled-scotcheroos': {'action': 'edit', 'patch': {
        'name': 'Scotcheroos',
        'tags': ['dessert'],
        'notes': 'Rice Krispies stirred into a peanut-butter-and-corn-syrup mixture, pressed into a pan, and topped with melted chocolate and butterscotch.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-chicken-florentine': {'action': 'edit', 'patch': {
        'name': 'Chicken Florentine',
        'notes': 'Chicken breasts sautéed and served over sautéed spinach in a cream-and-Parmesan sauce — the "Florentine" of any sautéed-spinach preparation.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-rocky-road': {'action': 'edit', 'patch': {
        'name': 'Rocky road candy',
        'tags': ['dessert'],
        'notes': 'Melted chocolate stirred with mini marshmallows and chopped peanuts or almonds, poured to set, and cut into squares.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-risotto': {'action': 'edit', 'patch': {
        'name': 'Risotto',
        'notes': 'Short-grain rice (Arborio or Carnaroli) toasted in butter, then simmered slowly with warm broth and white wine until creamy — finished with Parmesan.',
        'cuisine': 'Italian',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-beef-and-noodles': {'action': 'edit', 'patch': {
        'name': 'Beef and noodles',
        'notes': 'Cubed or shredded beef simmered with mushrooms and onions in a brown gravy, served over wide egg noodles or mashed potatoes — Midwestern comfort.',
        'cuisine': 'American',
    }},
    'corpus-titled-spinach-and-artichoke-dip': {'action': 'edit', 'patch': {
        'name': 'Spinach and artichoke dip',
        'ingredient_categories': ['Leafy greens', 'Other vegetables', 'Fresh cheese', 'Aged cheese', 'Fermented dairy', 'Extracts & essences', 'Peppers & nightshades', 'Cream & butter'],
        'tags': ['snack'],
        'notes': 'Chopped spinach and artichoke hearts baked with cream cheese, sour cream, mayo, and Parmesan until bubbling — served warm with bread or chips.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-pastitsio': {'action': 'edit', 'patch': {
        'name': 'Pastitsio',
        'notes': 'A Greek baked-pasta dish of tubular pasta layered with cinnamon-and-clove-spiced ground beef in tomato sauce, topped with a thick bechamel and Kefalotyri.',
        'cuisine': 'Greek',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-white-sangria': {'action': 'edit', 'patch': {
        'name': 'White sangria',
        'notes': 'White wine mixed with brandy, fruit juices, and sliced fresh fruit, sweetened lightly and chilled — topped with sparkling water at serving.',
        'cuisine': 'Spanish',
        'contains_add': ['alcohol'],
        'serving_grams': 150,
    }},
    'corpus-titled-cream-puff-dessert': {'action': 'edit', 'patch': {
        'name': 'Cream puff dessert',
        'notes': 'A pâte-à-choux base baked in a sheet pan, topped with vanilla pudding and cream cheese, finished with whipped topping and chocolate drizzle.',
        'cuisine': 'American',
    }},
    'corpus-titled-s-chili': {'action': 'edit', 'patch': {
        'name': 'Southwestern chili',
        'notes': 'Ground beef simmered with tomatoes, beans, peppers, onions, and chili powder — a generic American chili.',
        'cuisine': 'American',
    }},
    'corpus-titled-wedding-cookies': {'action': 'edit', 'patch': {
        'name': 'Wedding cookies',
        'tags': ['dessert'],
        'notes': 'A butter-shortbread folded with finely chopped nuts (almonds or pecans), baked into balls and rolled in powdered sugar — Russian-tea-cake family.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-fresh-tomato-salsa': {'action': 'edit', 'patch': {
        'name': 'Fresh tomato salsa',
        'tags': ['snack', 'condiment'],
        'notes': 'Diced ripe tomato, onion, jalapeño, cilantro, lime, and salt — a fresh chunky salsa for chips and tacos.',
        'cuisine': 'Mexican',
        'serving_grams': 60,
    }},
    'corpus-titled-beef-noodle-casserole': {'action': 'edit', 'patch': {
        'name': 'Beef noodle casserole',
        'notes': 'Browned ground beef and egg noodles baked with cream cheese, sour cream, and cottage cheese under shredded cheddar — a Midwestern hot dish.',
        'cuisine': 'American',
    }},
    'corpus-titled-potato-salad-dressing': {'action': 'drop', 'reason': 'dressing component, not a coherent meal'},
    'corpus-titled-sausage-stuffing': {'action': 'edit', 'patch': {
        'name': 'Sausage stuffing',
        'notes': 'Cubed bread mixed with cooked breakfast or Italian sausage, onions, celery, sage, and broth, baked into a Thanksgiving dressing.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-carrot-cookies': {'action': 'edit', 'patch': {
        'name': 'Carrot cookies',
        'notes': 'Soft drop cookies of mashed cooked carrots, butter, sugar, and eggs — often glazed with an orange-citrus icing.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-lime-pickles': {'action': 'drop', 'reason': 'pickled condiment (cucumber-in-lime canning preserve), not a coherent meal'},
    'corpus-titled-oven-barbecued-chicken': {'action': 'edit', 'patch': {
        'name': 'Oven barbecued chicken',
        'notes': 'Chicken pieces baked in a sweet-tangy barbecue sauce until tender and glazed — a low-effort indoor alternative to grilling.',
        'cuisine': 'American',
    }},
    'corpus-titled-frozen-cherry-salad': {'action': 'edit', 'patch': {
        'name': 'Frozen cherry salad',
        'tags': ['dessert'],
        'notes': 'Cherry pie filling folded with crushed pineapple, sweetened condensed milk, and whipped topping, frozen in a pan and sliced.',
        'cuisine': 'American',
    }},
    'corpus-titled-baked-lasagna': {'action': 'edit', 'patch': {
        'name': 'Baked lasagna',
        'notes': 'Layered lasagna noodles with ricotta, ground beef in marinara, and mozzarella, baked until bubbly — the classic Italian-American casserole.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-spaghetti-pizza': {'action': 'edit', 'patch': {
        'name': 'Spaghetti pizza',
        'notes': 'Cooked spaghetti bound with eggs and milk pressed into a pan to form a "crust," topped with marinara, pepperoni, and mozzarella, then baked.',
        'cuisine': 'Italian-American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-caramel-bars': {'action': 'edit', 'patch': {
        'name': 'Caramel bars',
        'tags': ['dessert'],
        'notes': 'A brown-sugar-oat crumb crust topped with melted caramels and chocolate chips, then more crumb, baked and cut into bars.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-breakfast-souffle': {'action': 'edit', 'patch': {
        'name': 'Breakfast soufflé',
        'notes': 'A make-ahead bake of bread cubes soaked overnight in an egg-and-milk custard with sausage or ham, cheese, and spinach — puffed when baked.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-chicken-marengo': {'action': 'edit', 'patch': {
        'name': 'Chicken Marengo',
        'notes': 'Chicken pieces sautéed with tomatoes, mushrooms, onions, garlic, and white wine in olive oil — Napoleon\'s reputed post-victory dinner.',
        'cuisine': 'French',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-stuffed-acorn-squash': {'action': 'edit', 'patch': {
        'name': 'Stuffed acorn squash',
        'notes': 'Halved acorn squash hollowed and filled with apples, cranberries, sausage, or wild rice — baked until the squash is tender and the filling browns.',
    }},
    'corpus-titled-mayonnaise-biscuits': {'action': 'edit', 'patch': {
        'name': 'Mayonnaise biscuits',
        'tags': ['breakfast', 'dinner'],
        'notes': 'A three-ingredient quick biscuit of self-rising flour, mayonnaise, and milk — patted out and baked into tender drop biscuits.',
        'cuisine': 'Southern',
        'serving_grams': 55,
    }},
    'corpus-titled-creamy-tomato-soup': {'action': 'edit', 'patch': {
        'name': 'Creamy tomato soup',
        'notes': 'Tomatoes simmered with onion, broth, and herbs, blended smooth and enriched with cream and butter — often paired with grilled cheese.',
        'cuisine': 'American',
    }},
    'corpus-titled-russian-salad': {'action': 'edit', 'patch': {
        'name': 'Russian salad (American dessert variant)',
        'tags': ['dessert'],
        'notes': 'A molded gelatin dessert of crushed pineapple, oranges, cream cheese, and nuts — closer to a Southern Jello salad than the Russian Olivier salad.',
        'cuisine': 'American',
    }},
    'corpus-titled-sugar-cream-pie': {'action': 'edit', 'patch': {
        'name': 'Sugar cream pie',
        'notes': 'A Hoosier-Indiana custard of sugar, butter, cream, and a touch of cornstarch and vanilla baked in a single crust — the state pie of Indiana.',
        'cuisine': 'American',
    }},
    'corpus-titled-lemon-poppy-seed-bread': {'action': 'edit', 'patch': {
        'name': 'Lemon poppy seed bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A sweet citrus-bright quick bread with poppy seeds, finished with a tart lemon-sugar glaze.',
        'cuisine': 'American',
    }},
    'corpus-titled-breakfast': {'action': 'edit', 'patch': {
        'name': 'Breakfast bake (generic)',
        'notes': 'A generic breakfast casserole of eggs, milk, sausage or bacon, cheese, and bread — a placeholder for several variants in the corpus.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-rocky-road-brownies': {'action': 'edit', 'patch': {
        'name': 'Rocky road brownies',
        'notes': 'Fudge brownies topped with marshmallows, chopped nuts, and chocolate chips during the last few minutes of baking — gooey and stretched.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-crab-rangoon': {'action': 'edit', 'patch': {
        'name': 'Crab rangoon',
        'tags': ['snack'],
        'notes': 'Wonton wrappers filled with cream cheese, crab (or imitation crab), and scallions, folded and deep-fried — Chinese-American takeout appetizer.',
        'cuisine': 'Chinese-American',
        'serving_grams': 80,
    }},
    'corpus-titled-carrot-muffins': {'action': 'edit', 'patch': {
        'name': 'Carrot muffins',
        'tags': ['breakfast', 'snack'],
        'notes': 'Spiced muffins of grated carrot, oil, eggs, raisins, and pecans — a single-portion form of carrot cake.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-coconut-rice': {'action': 'edit', 'patch': {
        'name': 'Coconut rice',
        'notes': 'Jasmine or long-grain rice cooked in coconut milk with a touch of salt and sugar — a Southeast Asian and Caribbean side.',
        'cuisine': 'Southeast Asian',
    }},
    'corpus-titled-steak-au-poivre': {'action': 'edit', 'patch': {
        'name': 'Steak au poivre',
        'notes': 'A beef steak pressed with cracked black peppercorns, pan-seared, and finished in a cognac-cream pan sauce — French bistro classic.',
        'cuisine': 'French',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-mojito': {'action': 'edit', 'patch': {
        'name': 'Mojito',
        'notes': 'White rum, fresh mint, lime juice, simple syrup, and a splash of soda water muddled and shaken — Cuba\'s emblematic cocktail.',
        'cuisine': 'Cuban',
        'contains_add': ['alcohol'],
        'serving_grams': 100,
    }},
    'corpus-titled-blueberry-cream-pie': {'action': 'edit', 'patch': {
        'name': 'Blueberry cream pie',
        'notes': 'A graham crust filled with sweetened cream cheese, topped with blueberry pie filling and whipped topping — chilled until set.',
        'cuisine': 'American',
    }},
    'corpus-titled-fresh-broccoli-salad': {'action': 'edit', 'patch': {
        'name': 'Fresh broccoli salad',
        'notes': 'Raw broccoli florets tossed with bacon, raisins, red onion, and cheese in a sweet mayonnaise dressing.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-pork-chop-dinner': {'action': 'edit', 'patch': {
        'name': 'Pork chop sheet-pan dinner',
        'notes': 'Pork chops baked on a sheet pan with potato wedges, carrots, and onions — a one-pan weeknight meal.',
        'cuisine': 'American',
    }},
    'corpus-titled-baked-cabbage': {'action': 'edit', 'patch': {
        'name': 'Baked cabbage',
        'notes': 'Shredded cabbage baked in a cheesy milk-and-roux bechamel under buttered cracker crumbs — similar to scalloped cabbage.',
        'cuisine': 'American',
    }},
    'corpus-titled-strawberry-mousse': {'action': 'edit', 'patch': {
        'name': 'Strawberry mousse',
        'notes': 'Crushed sweetened strawberries folded into whipped cream and stabilized with a little gelatin — an airy chilled dessert.',
        'cuisine': 'French',
        'serving_grams': 130,
    }},
    'corpus-titled-broccoli': {'action': 'edit', 'patch': {
        'name': 'Steamed broccoli (cheese sauce)',
        'notes': 'Steamed broccoli florets topped with a cheese-and-mushroom-soup sauce — generic "broccoli" recipe from the corpus.',
        'cuisine': 'American',
    }},
    'corpus-titled-pita-bread': {'action': 'edit', 'patch': {
        'name': 'Pita bread',
        'notes': 'A round flat yeasted bread baked very hot so it puffs and forms a hollow pocket — Middle Eastern staple for dipping or stuffing.',
        'cuisine': 'Middle Eastern',
        'serving_grams': 60,
    }},
    'corpus-titled-marinated-salad': {'action': 'edit', 'patch': {
        'name': 'Marinated vegetable salad',
        'notes': 'Mixed cooked or raw vegetables tossed in a sweet vinaigrette and chilled overnight — a make-ahead picnic salad.',
        'cuisine': 'American',
    }},
    'corpus-titled-hot-fudge-sundae-cake': {'action': 'edit', 'patch': {
        'name': 'Hot fudge sundae cake',
        'notes': 'A self-saucing chocolate cake — batter spread in a pan, topped with cocoa-sugar and boiling water; cake rises and a fudge sauce sinks beneath.',
        'cuisine': 'American',
    }},
    'corpus-titled-mushroom-barley-soup': {'action': 'edit', 'patch': {
        'name': 'Mushroom barley soup',
        'notes': 'Sliced mushrooms and pearl barley simmered with onions, carrots, celery, and herbs in beef broth — a Jewish/Eastern-European stockpot soup.',
        'cuisine': 'Jewish',
    }},
    'corpus-titled-wine-cake': {'action': 'edit', 'patch': {
        'name': 'Wine cake',
        'notes': 'A yellow Bundt cake made from cake mix and instant pudding with a half-cup of cream sherry or other sweet wine stirred into the batter.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-hot-dip': {'action': 'edit', 'patch': {
        'name': 'Hot beef dip',
        'tags': ['snack'],
        'notes': 'Cream cheese mixed with chipped beef, peppers, onion, and sour cream, baked or microwaved until bubbly — served warm with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-tater-tot-hot-dish': {'action': 'edit', 'patch': {
        'name': 'Tater tot hot dish',
        'notes': 'Ground beef and vegetables baked in cream-of-mushroom-soup gravy under a layer of frozen tater tots — a Minnesota / Upper-Midwest hot dish.',
        'cuisine': 'American',
    }},
    'corpus-titled-apple-bars': {'action': 'edit', 'patch': {
        'name': 'Apple bars',
        'tags': ['dessert'],
        'notes': 'A short butter-flour crust topped with spiced sliced apples and a butter-sugar streusel, baked and cut into bars.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-pickled-shrimp': {'action': 'edit', 'patch': {
        'name': 'Pickled shrimp',
        'tags': ['snack'],
        'notes': 'Cooked shrimp layered with sliced onions and lemon, then marinated in an oil-vinegar-pickling-spice brine — a Southern coastal cocktail dish.',
        'cuisine': 'Southern',
        'serving_grams': 120,
    }},
    'corpus-titled-salmon-dip': {'action': 'edit', 'patch': {
        'name': 'Salmon dip',
        'tags': ['snack'],
        'notes': 'Smoked or canned salmon mixed with cream cheese, sour cream, dill, lemon, and onion — served chilled with crackers or rye toasts.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-crunchy-pea-salad': {'action': 'edit', 'patch': {
        'name': 'Crunchy pea salad',
        'notes': 'Frozen sweet peas tossed with chopped cauliflower, peanuts, bacon, and sour-cream-mayo dressing — chilled.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-parker-house-rolls': {'action': 'edit', 'patch': {
        'name': 'Parker House rolls',
        'tags': ['dinner', 'lunch'],
        'notes': 'Soft enriched yeasted rolls shaped as a folded-over half, brushed with butter, and baked — created at Boston\'s Parker House Hotel.',
        'cuisine': 'American',
        'serving_grams': 50,
    }},
    'corpus-titled-cheddar-cheese-soup': {'action': 'edit', 'patch': {
        'name': 'Cheddar cheese soup',
        'notes': 'Diced vegetables sautéed in butter, simmered with chicken broth, then thickened with milk, flour, and shredded cheddar.',
        'cuisine': 'American',
    }},
    'corpus-titled-deviled-crab': {'action': 'edit', 'patch': {
        'name': 'Deviled crab',
        'notes': 'Lump crab folded with breadcrumbs, mayo, mustard, lemon, Worcestershire, and a hint of cayenne, baked in shells or ramekins until golden.',
        'cuisine': 'American',
    }},
    'corpus-titled-mexican-roll-ups': {'action': 'edit', 'patch': {
        'name': 'Mexican roll-ups',
        'tags': ['snack'],
        'notes': 'Flour tortillas spread with seasoned cream cheese, salsa, olives, and green chiles, rolled and sliced into pinwheels — chilled appetizer.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-chicken-crunch': {'action': 'edit', 'patch': {
        'name': 'Chicken crunch',
        'notes': 'Diced chicken baked with rice, peas, mushrooms, and water chestnuts in a cream-soup sauce, topped with crushed potato chips or chow-mein noodles.',
        'cuisine': 'American',
    }},
    'corpus-titled-pork-barbecue': {'action': 'edit', 'patch': {
        'name': 'Pork barbecue (sandwich)',
        'notes': 'Slow-cooked shredded pork shoulder tossed in a vinegar-or-tomato-based barbecue sauce — served on a soft bun with coleslaw, Carolina style.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-lime-punch': {'action': 'edit', 'patch': {
        'name': 'Lime punch',
        'ingredient_categories': ['Juices', 'Citrus', 'Tropical fruits', 'Sugar & sweeteners', 'Soft drinks'],
        'tags': ['snack'],
        'notes': 'A green non-alcoholic punch of lime sherbet, pineapple juice, and ginger ale — for showers and birthday parties.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-banana-fritters': {'action': 'edit', 'patch': {
        'name': 'Banana fritters',
        'tags': ['dessert'],
        'notes': 'Sliced or mashed banana folded into a leavened batter, dropped into hot oil, fried golden, and dusted with powdered sugar.',
        'cuisine': 'American',
    }},
    'corpus-titled-lemon-poppy-seed-muffins': {'action': 'edit', 'patch': {
        'name': 'Lemon poppy seed muffins',
        'tags': ['breakfast', 'snack'],
        'notes': 'Tender muffins flavored with lemon zest, juice, and poppy seeds — often finished with a tart lemon-sugar glaze.',
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

    print('corpus-titled batch-12 audit applied (entries 1651-1800 by frequency).')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
