"""Corpus-titled meals audit — batch 13 (entries 1801-1950 by frequency, 68 -> 63)."""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

DECISIONS: dict[str, dict] = {
    'corpus-titled-thai-beef-salad': {'action': 'edit', 'patch': {
        'name': 'Thai beef salad',
        'notes': 'Sliced grilled beef tossed with cucumber, shallot, mint, cilantro, and a lime-fish-sauce-chili dressing — Thai street-food classic.',
        'cuisine': 'Thai',
    }},
    'corpus-titled-cakespy': {'action': 'drop', 'reason': 'website/blog name, not a coherent meal'},
    'corpus-titled-meatloaf-recipe': {'action': 'edit', 'patch': {
        'name': 'Meatloaf (recipe variant)',
        'notes': 'A ground-beef loaf bound with breadcrumbs and egg, seasoned with onions and herbs, glazed with ketchup, and baked.',
        'cuisine': 'American',
    }},
    'corpus-titled-carrot-bars': {'action': 'edit', 'patch': {
        'name': 'Carrot bars',
        'tags': ['dessert'],
        'notes': 'A sheet-pan version of carrot cake — spiced oil-and-egg batter folded with grated carrots, baked and frosted with cream cheese.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-chocolate-chip-cookie': {'action': 'edit', 'patch': {
        'name': 'Chocolate chip cookie (singular)',
        'notes': 'A drop cookie of brown-and-white sugar butter dough studded with semisweet chocolate chips and pecans — Toll House standard.',
        'cuisine': 'American',
    }},
    'corpus-titled-linguini-salad': {'action': 'edit', 'patch': {
        'name': 'Linguini salad (variant)',
        'notes': 'Cooked linguini tossed with chopped peppers, onions, olives, and a Salad Supreme-seasoned Italian dressing — chilled overnight.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-savory-pot-roast': {'action': 'edit', 'patch': {
        'name': 'Savory pot roast',
        'notes': 'A chuck or round roast seared and slow-braised with onions, mushrooms, and root vegetables in seasoned broth until fork-tender.',
        'cuisine': 'American',
    }},
    'corpus-titled-cheesy-chicken-casserole': {'action': 'edit', 'patch': {
        'name': 'Cheesy chicken casserole',
        'notes': 'Cooked chicken baked with vegetables and cheese in a creamy soup-based sauce — generic comfort casserole.',
        'cuisine': 'American',
    }},
    'corpus-titled-ladyfingers': {'action': 'edit', 'patch': {
        'name': 'Ladyfingers',
        'tags': ['dessert'],
        'notes': 'A sponge-cake batter piped into fingers and baked into light, dry biscuits — used as the base for tiramisu and trifle.',
        'cuisine': 'Italian',
        'serving_grams': 30,
    }},
    'corpus-titled-oreo-cake': {'action': 'edit', 'patch': {
        'name': 'Oreo cake',
        'notes': 'A vanilla butter cake folded with crushed Oreos and frosted with cookies-and-cream buttercream — chocolate-cookie pieces throughout.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-enchilada': {'action': 'edit', 'patch': {
        'name': 'Chicken enchilada',
        'notes': 'A tortilla rolled around shredded chicken and cheese, baked in a red or green chile sauce, and topped with more cheese.',
        'cuisine': 'Mexican',
    }},
    'corpus-titled-banana-bars': {'action': 'edit', 'patch': {
        'name': 'Banana bars',
        'tags': ['dessert'],
        'notes': 'A sheet-pan version of banana cake — moist banana butter-and-egg batter baked and frosted with cream cheese icing.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-creamy-fruit-salad': {'action': 'edit', 'patch': {
        'name': 'Creamy fruit salad',
        'tags': ['dessert'],
        'notes': 'Mixed fruit folded with sweetened cream cheese and whipped topping or marshmallow fluff — a Southern picnic dessert salad.',
        'cuisine': 'American',
    }},
    'corpus-titled-stewed-tomatoes': {'action': 'edit', 'patch': {
        'name': 'Stewed tomatoes',
        'notes': 'Canned or fresh tomatoes simmered with onion, sugar, and butter, sometimes thickened with bread cubes — a Southern side.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-hello-dolly-cookies': {'action': 'edit', 'patch': {
        'name': 'Hello Dolly bars',
        'tags': ['dessert'],
        'notes': 'Graham crust topped with chocolate chips, butterscotch chips, coconut, and pecans, drizzled with sweetened condensed milk and baked.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-fruit-cookies': {'action': 'edit', 'patch': {
        'name': 'Fruit cookies (candied fruit)',
        'notes': 'Drop cookies of butter-sugar dough folded with candied cherries, citron, dates, raisins, and pecans — fruitcake-flavored cookies.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-chicken-ala-king': {'action': 'edit', 'patch': {
        'name': 'Chicken à la king',
        'notes': 'Diced cooked chicken in a cream sauce with mushrooms, pimientos, and sherry — served over toast points or rice.',
        'cuisine': 'American',
    }},
    'corpus-titled-buttermilk-rolls': {'action': 'edit', 'patch': {
        'name': 'Buttermilk rolls',
        'tags': ['dinner', 'lunch'],
        'notes': 'A soft yeasted roll made tangy and tender by buttermilk in the dough — pulled apart warm with butter at dinner.',
        'cuisine': 'American',
        'serving_grams': 50,
    }},
    'corpus-titled-deep-dish-pizza': {'action': 'edit', 'patch': {
        'name': 'Deep dish pizza',
        'notes': 'A Chicago-style pizza baked in a tall buttered pan with cheese on the bottom, fillings in the middle, and chunky tomato sauce on top.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-french-breakfast-puffs': {'action': 'edit', 'patch': {
        'name': 'French breakfast puffs',
        'notes': 'Soft butter-and-sugar muffins baked plain, then dunked in melted butter and rolled in cinnamon sugar — like a baked donut.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-broccoli-and-cheese-soup': {'action': 'edit', 'patch': {
        'name': 'Broccoli and cheese soup',
        'notes': 'Broccoli simmered in chicken broth with onion, blended (or partially), and thickened with a milk-and-butter roux finished with cheddar or Velveeta.',
        'cuisine': 'American',
    }},
    'corpus-titled-honey-baked-chicken': {'action': 'edit', 'patch': {
        'name': 'Honey baked chicken',
        'notes': 'Chicken pieces brushed with a butter-honey-mustard-curry glaze and baked until caramelized — a Sandra Lee semi-homemade staple.',
        'cuisine': 'American',
    }},
    'corpus-titled-broccoli-chicken-casserole': {'action': 'edit', 'patch': {
        'name': 'Broccoli chicken casserole (variant)',
        'notes': 'Cooked chicken and broccoli baked in mayo-lemon-cream-of-chicken-soup sauce under cheese and buttered breadcrumbs.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-dumplings': {'action': 'edit', 'patch': {
        'name': 'Chicken and dumplings (variant)',
        'notes': 'Chicken simmered in broth with vegetables, finished with soft dough dumplings dropped on top to steam-cook.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-vegetarian-lasagna': {'action': 'edit', 'patch': {
        'name': 'Vegetarian lasagna',
        'notes': 'Layered lasagna noodles with ricotta, sautéed vegetables (zucchini, mushrooms, spinach), mozzarella, and marinara — the meatless lasagna.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-sour-cream-chocolate-cake': {'action': 'edit', 'patch': {
        'name': 'Sour cream chocolate cake',
        'notes': 'A cocoa cake enriched with sour cream — moist, tangy crumb that pairs especially well with chocolate buttercream.',
        'cuisine': 'American',
    }},
    'corpus-titled-overnight-coffee-cake': {'action': 'edit', 'patch': {
        'name': 'Overnight coffee cake',
        'tags': ['breakfast', 'dessert'],
        'notes': 'A spiced butter cake batter mixed the night before, refrigerated, then topped with cinnamon-pecan streusel and baked in the morning.',
        'cuisine': 'American',
    }},
    'corpus-titled-ranch-beans': {'action': 'edit', 'patch': {
        'name': 'Ranch beans',
        'notes': 'Pinto beans simmered with ground beef, bacon, brown sugar, barbecue sauce, and chili powder — a Tex-Mex cowboy-bean side.',
        'cuisine': 'Tex-Mex',
        'contains_add': ['pork'],
    }},
    'corpus-titled-frozen-dessert': {'action': 'edit', 'patch': {
        'name': 'Frozen fruit dessert',
        'notes': 'Mixed fruit folded with sweetened condensed milk and whipped topping, frozen in a pan and sliced — Southern frozen-salad style.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-dutch-apple-cake': {'action': 'edit', 'patch': {
        'name': 'Dutch apple cake',
        'notes': 'A tender butter-and-egg cake topped with sliced apples and a cinnamon-sugar streusel before baking.',
        'cuisine': 'Dutch',
    }},
    'corpus-titled-blue-cheese-dip': {'action': 'edit', 'patch': {
        'name': 'Blue cheese dip',
        'tags': ['snack', 'condiment'],
        'notes': 'Crumbled blue cheese folded into sour cream, mayo, and a touch of buttermilk — served chilled with Buffalo wings, celery, or chips.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-blueberry-pound-cake': {'action': 'edit', 'patch': {
        'name': 'Blueberry pound cake',
        'notes': 'A dense pound cake folded with fresh or frozen blueberries — sometimes finished with a lemon-sugar glaze.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-crinkle-cookies': {'action': 'edit', 'patch': {
        'name': 'Chocolate crinkle cookies',
        'notes': 'Fudgy chocolate cookies rolled twice (granulated then powdered sugar) before baking — the powdered sugar cracks into a "crinkle" pattern.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-banana-smoothie': {'action': 'edit', 'patch': {
        'name': 'Banana smoothie',
        'notes': 'Frozen banana blended with milk or yogurt, a touch of honey, and ice — sometimes with peanut butter or cocoa.',
        'serving_grams': 240,
    }},
    'corpus-titled-chocolate-torte': {'action': 'edit', 'patch': {
        'name': 'Chocolate torte',
        'tags': ['dessert'],
        'notes': 'A dense, often flourless chocolate cake leaning on butter, dark chocolate, eggs, and ground nuts — fudgy and intense.',
        'cuisine': 'European',
        'serving_grams': 140,
    }},
    'corpus-titled-chicken-spaghetti-casserole': {'action': 'edit', 'patch': {
        'name': 'Chicken spaghetti casserole',
        'notes': 'Spaghetti baked with shredded chicken, peppers, mushrooms, and Velveeta-style cheese sauce — Southern church-supper casserole.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-creamy-lemon-pie': {'action': 'edit', 'patch': {
        'name': 'Creamy lemon pie',
        'notes': 'A no-bake pie of lemon juice whipped into sweetened condensed milk and folded into whipped topping or whipped cream, set in a graham crust.',
        'cuisine': 'American',
    }},
    'corpus-titled-mexican-hot-chocolate': {'action': 'edit', 'patch': {
        'name': 'Mexican hot chocolate',
        'notes': 'Milk warmed with bittersweet chocolate (or cocoa), cinnamon, vanilla, and a pinch of chili powder — frothy and spiced.',
        'cuisine': 'Mexican',
        'serving_grams': 240,
    }},
    'corpus-titled-pink-lemonade-pie': {'action': 'edit', 'patch': {
        'name': 'Pink lemonade pie',
        'notes': 'Frozen pink lemonade concentrate folded with sweetened condensed milk and whipped topping, set in a graham crust — chilled until firm.',
        'cuisine': 'American',
        'serving_grams': 140,
    }},
    'corpus-titled-biscuit-mix': {'action': 'drop', 'reason': 'pantry mix component, not a coherent meal'},
    'corpus-titled-fettucine-alfredo': {'action': 'edit', 'patch': {
        'name': 'Fettuccine alfredo (variant)',
        'notes': 'Fresh fettuccine tossed with butter and grated Parmesan until emulsified into a creamy sauce — American versions add heavy cream.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-sausage-stuffed-mushrooms': {'action': 'edit', 'patch': {
        'name': 'Sausage stuffed mushrooms',
        'tags': ['snack'],
        'notes': 'Mushroom caps filled with cooked Italian sausage, cream cheese, and Parmesan, baked until bubbling.',
        'cuisine': 'Italian-American',
        'contains_add': ['pork'],
        'serving_grams': 80,
    }},
    'corpus-titled-tabouli': {'action': 'edit', 'patch': {
        'name': 'Tabouli',
        'notes': 'Cracked bulgur wheat tossed with finely chopped parsley, tomato, mint, scallions, lemon juice, and olive oil — Levantine herb salad.',
        'cuisine': 'Middle Eastern',
    }},
    'corpus-titled-turkey-gravy': {'action': 'drop', 'reason': 'sauce / gravy component, not a coherent meal'},
    'corpus-titled-peanut-butter-bonbons': {'action': 'edit', 'patch': {
        'name': 'Peanut butter bonbons',
        'tags': ['dessert'],
        'notes': 'Peanut butter, butter, and powdered sugar mixed with Rice Krispies, rolled into balls, and dipped in melted chocolate.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-fruit-dessert': {'action': 'edit', 'patch': {
        'name': 'Fruit dessert',
        'notes': 'A generic name for chilled fruit dishes — sweetened mixed fruit folded with whipped topping, pudding, or Jello.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-italiano': {'action': 'edit', 'patch': {
        'name': 'Chicken Italiano',
        'notes': 'Chicken pieces baked or simmered in Italian dressing or marinara with mozzarella, peppers, and herbs — served over pasta.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-coconut-bonbons': {'action': 'edit', 'patch': {
        'name': 'Coconut bonbons (variant)',
        'tags': ['dessert'],
        'notes': 'Sweetened coconut mixed with butter, sweetened condensed milk, and pecans, rolled into balls and dipped in chocolate — Martha-Washington-style.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-breakfast-pie': {'action': 'edit', 'patch': {
        'name': 'Breakfast pie',
        'tags': ['breakfast', 'lunch'],
        'notes': 'A pastry shell filled with eggs, sausage or bacon, cheese, and vegetables, baked into a savory breakfast tart.',
        'cuisine': 'American',
        'contains_add': ['pork'],
        'serving_grams': 320,
    }},
    'corpus-titled-turtle-brownies': {'action': 'edit', 'patch': {
        'name': 'Turtle brownies',
        'notes': 'Fudge brownies layered with melted caramel and chopped pecans, baked into a turtle-candy-style bar.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-escalloped-corn': {'action': 'edit', 'patch': {
        'name': 'Escalloped corn',
        'notes': 'Corn kernels baked in a custard of eggs, milk, butter, and sugar under a buttered cracker top — a Midwest church-supper side.',
        'cuisine': 'American',
    }},
    'corpus-titled-chess-bars': {'action': 'edit', 'patch': {
        'name': 'Chess bars',
        'tags': ['dessert'],
        'notes': 'A yellow-cake-mix base topped with a cream-cheese-egg-and-powdered-sugar filling that bakes into a gooey center — same family as gooey butter cake.',
        'cuisine': 'Southern',
        'serving_grams': 80,
    }},
    'corpus-titled-dilly-beans': {'action': 'drop', 'reason': 'pickled condiment, not a coherent meal'},
    'corpus-titled-white-trash': {'action': 'edit', 'patch': {
        'name': 'White trash candy',
        'tags': ['snack', 'dessert'],
        'notes': 'Chex, pretzels, peanuts, Cheerios, and M&Ms tossed with melted white chocolate and almond bark, spread to set and broken into pieces.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-asparagus-salad': {'action': 'edit', 'patch': {
        'name': 'Asparagus salad',
        'notes': 'Blanched asparagus tossed with lemon vinaigrette, almonds, and Parmesan — sometimes folded with hard-boiled egg.',
    }},
    'corpus-titled-7-layer-cookies': {'action': 'edit', 'patch': {
        'name': 'Seven layer bars (variant)',
        'tags': ['dessert'],
        'notes': 'Graham crust topped with chocolate chips, butterscotch chips, coconut, and pecans, drizzled with sweetened condensed milk and baked.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-fried-eggplant': {'action': 'edit', 'patch': {
        'name': 'Fried eggplant',
        'notes': 'Sliced eggplant dipped in egg and milk, dredged in seasoned flour, and pan-fried in oil until golden.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-mushroom-casserole': {'action': 'edit', 'patch': {
        'name': 'Mushroom casserole',
        'notes': 'Sliced mushrooms baked with onions, butter, eggs, milk, and bread cubes under shredded cheese — a hearty mushroom strata.',
        'cuisine': 'American',
    }},
    'corpus-titled-beef-and-broccoli': {'action': 'edit', 'patch': {
        'name': 'Beef and broccoli',
        'notes': 'Strips of beef stir-fried with broccoli florets in a soy-garlic-ginger sauce thickened with cornstarch — served over rice.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-s-pecan-pie': {'action': 'edit', 'patch': {
        'name': 'Southern pecan pie',
        'notes': 'A custard of eggs, sugar, butter, and corn syrup or molasses studded with pecan halves, baked in a flaky crust until set.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-breaded-pork-chops': {'action': 'edit', 'patch': {
        'name': 'Breaded pork chops',
        'notes': 'Pork chops dipped in egg and milk, dredged in seasoned breadcrumbs or crushed crackers, and pan-fried until crisp.',
        'cuisine': 'American',
    }},
    'corpus-titled-pierogi': {'action': 'edit', 'patch': {
        'name': 'Pierogi',
        'notes': 'Dough pockets filled with potato-and-cheese, sauerkraut, or sweet farmer cheese, boiled and then pan-fried in butter with onions.',
        'cuisine': 'Polish',
    }},
    'corpus-titled-sweet-potato-fries': {'action': 'edit', 'patch': {
        'name': 'Sweet potato fries',
        'tags': ['snack', 'dinner'],
        'notes': 'Sweet potato wedges or strips tossed in oil and salt, baked or fried until crisp — often dusted with smoked paprika or cinnamon.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-strawberry-lemonade': {'action': 'edit', 'patch': {
        'name': 'Strawberry lemonade',
        'ingredient_categories': ['Juices', 'Berries', 'Citrus', 'Sugar & sweeteners'],
        'tags': ['snack'],
        'notes': 'Fresh-squeezed lemon juice and pureed strawberries with sugar and water — served cold over ice.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-shrimp-bisque': {'action': 'edit', 'patch': {
        'name': 'Shrimp bisque',
        'notes': 'A creamy seafood-broth soup of shrimp, aromatics, and tomato simmered with sherry, blended smooth, and finished with heavy cream.',
        'cuisine': 'French',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-panzanella': {'action': 'edit', 'patch': {
        'name': 'Panzanella',
        'notes': 'Stale bread cubes toasted and tossed with ripe tomatoes, cucumber, red onion, basil, and a red-wine vinaigrette — Tuscan bread salad.',
        'cuisine': 'Italian',
    }},
    'corpus-titled-spaghetti-bolognese': {'action': 'edit', 'patch': {
        'name': 'Spaghetti bolognese',
        'notes': 'Spaghetti topped with ragù alla bolognese — beef and pork slow-simmered with onion, carrot, celery, tomato, milk, and wine.',
        'cuisine': 'Italian',
        'contains_add': ['alcohol', 'pork'],
    }},
    'corpus-titled-blackberry-pie': {'action': 'edit', 'patch': {
        'name': 'Blackberry pie',
        'notes': 'A double-crust or lattice pie of fresh blackberries tossed with sugar and a thickener — sweet-tart with deep purple juice.',
        'cuisine': 'American',
    }},
    'corpus-titled-french-fries': {'action': 'edit', 'patch': {
        'name': 'French fries',
        'tags': ['snack', 'dinner'],
        'notes': 'Russet potato strips deep-fried in two stages — once at lower heat to cook through, then hot to crisp the outside — salted while hot.',
        'cuisine': 'American',
        'serving_grams': 130,
    }},
    'corpus-titled-fried-apple-pies': {'action': 'edit', 'patch': {
        'name': 'Fried apple pies',
        'notes': 'Hand-held pastry rounds filled with spiced cooked apples, sealed, and deep-fried until golden — McDonald\'s-original style.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-raw-vegetable-dip': {'action': 'edit', 'patch': {
        'name': 'Raw vegetable dip',
        'tags': ['snack'],
        'notes': 'Sour cream and mayo seasoned with dried herbs, dill, garlic, and onion — served chilled with raw vegetables.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-barbecue-pork-chops': {'action': 'edit', 'patch': {
        'name': 'Barbecue pork chops',
        'notes': 'Pork chops baked or grilled and basted with a sweet-tangy barbecue sauce until lacquered.',
        'cuisine': 'American',
    }},
    'corpus-titled-applesauce-bread': {'action': 'edit', 'patch': {
        'name': 'Applesauce bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A spiced quick bread made moist by applesauce in place of much of the fat — often with raisins and chopped walnuts.',
        'cuisine': 'American',
    }},
    'corpus-titled-berry-cobbler': {'action': 'edit', 'patch': {
        'name': 'Berry cobbler',
        'notes': 'Mixed berries baked under a buttery cake or biscuit topping — served warm with ice cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-oatmeal-scotchies': {'action': 'edit', 'patch': {
        'name': 'Oatmeal scotchies',
        'tags': ['dessert'],
        'notes': 'Oatmeal drop cookies studded with butterscotch chips — chewy and toffee-sweet.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-mulligatawny-soup': {'action': 'edit', 'patch': {
        'name': 'Mulligatawny soup',
        'notes': 'A British-Indian curry soup of chicken, vegetables, lentils, and apple in a curry-spiced broth — Madras-style.',
        'cuisine': 'British',
    }},
    'corpus-titled-s-pumpkin-pie': {'action': 'edit', 'patch': {
        'name': 'Southern pumpkin pie',
        'notes': 'A custard pie of pumpkin puree, eggs, evaporated milk, brown sugar, and warm spices baked in a flaky shell — a Thanksgiving classic.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-elephant-ears': {'action': 'edit', 'patch': {
        'name': 'Elephant ears',
        'tags': ['dessert', 'snack'],
        'notes': 'A yeasted dough rolled flat, fried, and coated in cinnamon-sugar — large, flat fair-style pastries.',
        'cuisine': 'American',
        'serving_grams': 90,
    }},
    'corpus-titled-sweet-and-sour-cabbage': {'action': 'edit', 'patch': {
        'name': 'Sweet and sour cabbage',
        'notes': 'Shredded cabbage cooked with onions, bacon, sugar, and vinegar — a German-Pennsylvania-Dutch braised side.',
        'cuisine': 'German',
        'contains_add': ['pork'],
    }},
    'corpus-titled-sour-cream-chicken': {'action': 'edit', 'patch': {
        'name': 'Sour cream chicken',
        'notes': 'Chicken breasts baked in a sauce of sour cream, mushroom soup, and seasonings — served over rice or noodles.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-caramel-bars': {'action': 'edit', 'patch': {
        'name': 'Chocolate caramel bars',
        'tags': ['dessert'],
        'notes': 'A brown-sugar-oat crumb crust topped with melted caramels and chocolate chips, then more crumb, baked and cut into bars.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-french-salad-dressing': {'action': 'drop', 'reason': 'dressing component, not a coherent meal'},
    'corpus-titled-baby-food-cake': {'action': 'edit', 'patch': {
        'name': 'Baby food cake',
        'notes': 'A spiced oil-based cake using jars of pureed baby food (carrots, prunes, or plums) in place of mashed fresh fruit — easy and moist.',
        'cuisine': 'American',
    }},
    'corpus-titled-pastry': {'action': 'drop', 'reason': 'pie-crust pastry component, not a coherent meal'},
    'corpus-titled-beef-goulash': {'action': 'edit', 'patch': {
        'name': 'American goulash',
        'notes': 'Ground beef simmered with elbow macaroni, tomato, onion, peppers, and paprika — a one-pot stovetop dish (unlike Hungarian goulash).',
        'cuisine': 'American',
    }},
    'corpus-titled-buffalo-chicken-wings': {'action': 'edit', 'patch': {
        'name': 'Buffalo chicken wings',
        'tags': ['snack', 'dinner'],
        'notes': 'Deep-fried chicken wings tossed in Frank\'s RedHot and butter — Buffalo, NY style; served with celery and blue cheese.',
        'cuisine': 'American',
        'serving_grams': 170,
    }},
    'corpus-titled-no-bake-cheese-cake': {'action': 'edit', 'patch': {
        'name': 'No-bake cheesecake (variant)',
        'notes': 'Cream cheese whipped with sweetened condensed milk, lemon juice, and whipped topping, poured into a graham crust and chilled until set.',
        'cuisine': 'American',
    }},
    'corpus-titled-chili-verde': {'action': 'edit', 'patch': {
        'name': 'Chile verde',
        'notes': 'Pork shoulder slow-simmered with tomatillos, green chiles, onion, garlic, and cumin until tender — served with tortillas or over rice.',
        'cuisine': 'Mexican',
        'contains_add': ['pork'],
    }},
    'corpus-titled-fig-preserves': {'action': 'drop', 'reason': 'jam / canning preserve, not a coherent meal'},
    'corpus-titled-double-chocolate-chip-cookies': {'action': 'edit', 'patch': {
        'name': 'Double chocolate chip cookies',
        'notes': 'Drop cookies of cocoa-and-butter dough studded with chocolate chips — chocolate from both the dough and the chips.',
        'cuisine': 'American',
    }},
    'corpus-titled-chinese-casserole': {'action': 'edit', 'patch': {
        'name': 'Chinese casserole',
        'notes': 'Ground beef or chicken baked with rice, water chestnuts, celery, mushrooms, mushroom soup, and soy sauce, topped with chow-mein noodles.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-sweet-potato-crunch': {'action': 'edit', 'patch': {
        'name': 'Sweet potato crunch',
        'notes': 'Mashed sweet potatoes baked under a brown-sugar-flour-butter-pecan streusel — same family as sweet potato casserole.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-dill-weed-dip': {'action': 'edit', 'patch': {
        'name': 'Dill weed dip',
        'tags': ['snack'],
        'notes': 'Sour cream and mayo seasoned with fresh or dried dill, parsley, onion, and Beau Monde — served chilled with vegetables in a bread bowl.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-baked-potato-casserole': {'action': 'edit', 'patch': {
        'name': 'Baked potato casserole',
        'notes': 'Cubed potatoes baked with sour cream, bacon, cheese, and chives — loaded-baked-potato flavors in casserole form.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-unbaked-cookies': {'action': 'edit', 'patch': {
        'name': 'Unbaked cookies (no-bake)',
        'notes': 'Cocoa, sugar, milk, and butter boiled to a fudge, stirred with peanut butter and oats, and dropped onto wax paper to set.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-chicken-caesar-salad': {'action': 'edit', 'patch': {
        'name': 'Chicken Caesar salad',
        'notes': 'Romaine tossed with grilled or roasted chicken, Caesar dressing (egg-anchovy-Parmesan), croutons, and shaved Parmesan.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-breakfast-cookies': {'action': 'edit', 'patch': {
        'name': 'Breakfast cookies',
        'tags': ['breakfast', 'snack'],
        'notes': 'Oat-based drop cookies folded with dried fruit, banana, nuts, and warm spices — a portable breakfast.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-christmas-cake': {'action': 'edit', 'patch': {
        'name': 'Christmas cake (fruitcake)',
        'tags': ['dessert'],
        'notes': 'A dense holiday cake packed with candied fruit, dried fruit, nuts, and warm spices — often soaked in brandy or rum and aged.',
        'cuisine': 'British',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-crispy-chicken': {'action': 'edit', 'patch': {
        'name': 'Crispy chicken',
        'notes': 'Chicken pieces dipped in milk or buttermilk and dredged in seasoned flour or crushed cornflakes, then baked or pan-fried until crisp.',
        'cuisine': 'American',
    }},
    'corpus-titled-cheeseburger-soup': {'action': 'edit', 'patch': {
        'name': 'Cheeseburger soup',
        'notes': 'Ground beef simmered with potatoes, carrots, celery, and onion in a milk-and-cheese-thickened broth — cheeseburger flavors as soup.',
        'cuisine': 'American',
    }},
    'corpus-titled-cream-of-cauliflower-soup': {'action': 'edit', 'patch': {
        'name': 'Cream of cauliflower soup',
        'notes': 'Cauliflower simmered with onion and chicken broth, blended smooth, and finished with milk, cream, and a touch of cheddar or nutmeg.',
    }},
    'corpus-titled-pineapple-punch': {'action': 'edit', 'patch': {
        'name': 'Pineapple punch',
        'ingredient_categories': ['Juices', 'Tropical fruits', 'Citrus', 'Sugar & sweeteners', 'Soft drinks'],
        'tags': ['snack'],
        'notes': 'A non-alcoholic punch of pineapple juice, frozen lemonade, and ginger ale or sherbet — for showers and birthday parties.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-shrimp-and-grits': {'action': 'edit', 'patch': {
        'name': 'Shrimp and grits',
        'notes': 'Sautéed shrimp with bacon, peppers, and tasso ham over creamy cheese grits — a Lowcountry Southern classic.',
        'cuisine': 'Southern',
        'contains_add': ['pork'],
    }},
    'corpus-titled-bbq-chicken-pizza': {'action': 'edit', 'patch': {
        'name': 'BBQ chicken pizza',
        'notes': 'A pizza crust spread with barbecue sauce in place of marinara, topped with shredded chicken, red onion, cilantro, and smoked gouda — California Pizza Kitchen original.',
        'cuisine': 'American',
        'serving_grams': 260,
    }},
    'corpus-titled-chili-con-queso-dip': {'action': 'edit', 'patch': {
        'name': 'Chili con queso dip',
        'tags': ['snack'],
        'notes': 'Velveeta-style processed cheese melted with Rotel tomatoes and chiles — served warm with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-sunshine-cake': {'action': 'edit', 'patch': {
        'name': 'Sunshine cake',
        'notes': 'A bright yellow chiffon-style cake made with orange juice and zest, sometimes from cake mix with mandarin oranges folded in.',
        'cuisine': 'American',
    }},
    'corpus-titled-crab-meat-dip': {'action': 'edit', 'patch': {
        'name': 'Crab meat dip',
        'tags': ['snack'],
        'notes': 'Cream cheese, mayo, and lemon whipped with chopped crab, scallions, and Worcestershire — served chilled or warm with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-chicken-creole': {'action': 'edit', 'patch': {
        'name': 'Chicken Creole',
        'notes': 'Chicken simmered in a Louisiana sauce of tomato, onion, peppers, celery, garlic, and Creole spices — served over rice.',
        'cuisine': 'Creole',
    }},
    'corpus-titled-butterhorns': {'action': 'edit', 'patch': {
        'name': 'Butterhorns',
        'tags': ['breakfast', 'dessert'],
        'notes': 'Soft enriched yeast dough rolled into wedges, brushed with butter and cinnamon-sugar, and rolled into crescents — pulled-apart with a drizzle.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-oysters-rockefeller': {'action': 'edit', 'patch': {
        'name': 'Oysters Rockefeller',
        'tags': ['snack', 'dinner'],
        'notes': 'Half-shell oysters topped with sautéed spinach, butter, herbs, breadcrumbs, and Pernod or absinthe, then baked or broiled — Antoine\'s of New Orleans.',
        'cuisine': 'Creole',
        'contains_add': ['alcohol'],
        'serving_grams': 170,
    }},
    'corpus-titled-baked-brie': {'action': 'edit', 'patch': {
        'name': 'Baked Brie',
        'tags': ['snack'],
        'notes': 'A wheel of Brie wrapped in puff pastry with fruit preserves and pecans, baked until the pastry is golden and the cheese melts inside.',
        'cuisine': 'French',
        'serving_grams': 60,
    }},
    'corpus-titled-barbecued-beans': {'action': 'edit', 'patch': {
        'name': 'Barbecued beans (variant)',
        'notes': 'Canned beans simmered with ground beef, bacon, onions, brown sugar, and barbecue sauce — thick and sweet, cowboy-style.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-blueberry-bread': {'action': 'edit', 'patch': {
        'name': 'Blueberry bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A sweet quick bread folded with fresh or frozen blueberries, finished with a tart lemon-sugar glaze.',
        'cuisine': 'American',
    }},
    'corpus-titled-hawaiian-salad': {'action': 'edit', 'patch': {
        'name': 'Hawaiian fruit salad',
        'tags': ['dessert'],
        'notes': 'Tropical fruits (pineapple, mandarin oranges) folded with mini marshmallows, coconut, and sour cream or whipped topping — same family as ambrosia.',
        'cuisine': 'American',
    }},
    'corpus-titled-marinated-tomatoes': {'action': 'edit', 'patch': {
        'name': 'Marinated tomatoes',
        'notes': 'Sliced ripe tomatoes layered with red onion in a sweet vinaigrette with fresh herbs — chilled briefly and served as a summer salad.',
    }},
    'corpus-titled-kosher-dill-pickles': {'action': 'drop', 'reason': 'pickled condiment, not a coherent meal'},
    'corpus-titled-pecan-rolls': {'action': 'edit', 'patch': {
        'name': 'Pecan rolls (sticky buns)',
        'tags': ['breakfast', 'dessert'],
        'notes': 'Yeasted dough rolled with cinnamon-sugar, baked over a brown-sugar-butter syrup with pecans, and inverted to serve.',
        'cuisine': 'American',
        'serving_grams': 90,
    }},
    'corpus-titled-jewish-coffee-cake': {'action': 'edit', 'patch': {
        'name': 'Jewish coffee cake (sour cream)',
        'tags': ['breakfast', 'dessert'],
        'notes': 'A sour-cream Bundt cake swirled with cinnamon-sugar-pecan streusel — Bubbe\'s coffee cake.',
        'cuisine': 'Jewish',
    }},
    'corpus-titled-fruit-crisp': {'action': 'edit', 'patch': {
        'name': 'Fruit crisp',
        'tags': ['dessert'],
        'notes': 'Sweetened sliced fruit (apples, peaches, berries) baked under a crunchy oat-and-butter streusel — served warm with ice cream.',
    }},
    'corpus-titled-angel-cookies': {'action': 'edit', 'patch': {
        'name': 'Angel cookies',
        'notes': 'A buttery sugar cookie of butter, oil, sugars, eggs, and cream of tartar — soft, lightly sweet, and topped with sugar.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-date-nut-bars': {'action': 'edit', 'patch': {
        'name': 'Date nut bars',
        'tags': ['dessert'],
        'notes': 'Cooked dates and nuts in a butter-egg batter, baked and cut into squares, dusted with powdered sugar — chewy and rich.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-percolator-punch': {'action': 'edit', 'patch': {
        'name': 'Percolator punch',
        'ingredient_categories': ['Juices', 'Berries', 'Tropical fruits', 'Sugar & sweeteners', 'Whole spices', 'Ground spices'],
        'tags': ['snack'],
        'notes': 'A hot punch of cranberry and pineapple juice "brewed" in a coffee percolator with brown sugar and warm spices in the basket.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-pasta-sauce': {'action': 'drop', 'reason': 'sauce component, not a coherent meal'},
    'corpus-titled-butter-balls': {'action': 'edit', 'patch': {
        'name': 'Butter balls (snowballs)',
        'tags': ['dessert'],
        'notes': 'A butter-and-powdered-sugar shortbread folded with finely chopped pecans, baked into balls and rolled in powdered sugar — Russian-tea-cake family.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-mexican-lasagne': {'action': 'edit', 'patch': {
        'name': 'Mexican lasagne (variant)',
        'notes': 'Layered tortillas with seasoned ground beef, enchilada or salsa sauce, beans, and cheese — baked lasagna-style.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-peaches-and-cream': {'action': 'edit', 'patch': {
        'name': 'Peaches and cream cake',
        'tags': ['dessert'],
        'notes': 'A vanilla cake base topped with sliced peaches and a sweet cream-cheese custard, baked into a fruit-and-cream square.',
        'cuisine': 'American',
        'serving_grams': 140,
    }},
    'corpus-titled-cottage-potatoes': {'action': 'edit', 'patch': {
        'name': 'Cottage potatoes',
        'notes': 'Cubed cooked potatoes baked with milk, cheese, and bread cubes or crackers — a Pennsylvania-Dutch potato casserole.',
        'cuisine': 'American',
    }},
    'corpus-titled-garlic-shrimp': {'action': 'edit', 'patch': {
        'name': 'Garlic shrimp (gambas al ajillo)',
        'notes': 'Shrimp sautéed hot in olive oil with sliced garlic, chiles, and a splash of sherry or white wine — Spanish tapa.',
        'cuisine': 'Spanish',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-barbecued-shrimp': {'action': 'edit', 'patch': {
        'name': 'Barbecued shrimp (New Orleans)',
        'notes': 'Whole shrimp baked in a buttery-garlicky-Worcestershire-pepper sauce — served peel-on with crusty bread; "barbecue" in name only.',
        'cuisine': 'Creole',
    }},
    'corpus-titled-pizza-snacks': {'action': 'edit', 'patch': {
        'name': 'Pizza snacks',
        'notes': 'English muffins or biscuit-dough rounds topped with pizza sauce, pepperoni, and mozzarella, baked until bubbly — bite-size pizzas.',
        'cuisine': 'American',
        'contains_add': ['pork'],
        'serving_grams': 100,
    }},
    'corpus-titled-baked-lima-beans': {'action': 'edit', 'patch': {
        'name': 'Baked lima beans',
        'notes': 'Lima beans baked with bacon, brown sugar, ketchup, and mustard — a sweet-savory Southern bean side.',
        'cuisine': 'Southern',
        'contains_add': ['pork'],
    }},
    'corpus-titled-field-s-cookies': {'action': 'edit', 'patch': {
        'name': "Mrs. Fields cookies (copycat)",
        'notes': 'A copycat of the Mrs. Fields chocolate chip cookie — butter, brown sugar, oats ground fine, chocolate chips and chopped chocolate, and pecans.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-sausage-biscuits': {'action': 'edit', 'patch': {
        'name': 'Sausage biscuits',
        'tags': ['snack', 'breakfast'],
        'notes': 'Bite-size baked balls of breakfast sausage, shredded cheddar, and biscuit mix — same family as sausage balls.',
        'cuisine': 'American',
        'contains_add': ['pork'],
        'serving_grams': 60,
    }},
    'corpus-titled-greek-chicken': {'action': 'edit', 'patch': {
        'name': 'Greek chicken',
        'notes': 'Chicken pieces marinated in lemon, olive oil, garlic, oregano, and red wine vinegar, then roasted or grilled — sometimes finished with feta and olives.',
        'cuisine': 'Greek',
    }},
    'corpus-titled-mexican-chicken-soup': {'action': 'edit', 'patch': {
        'name': 'Mexican chicken soup (caldo de pollo)',
        'notes': 'Chicken simmered with onions, garlic, carrots, potatoes, and corn in a tomato-and-chile broth — finished with cilantro, lime, and avocado.',
        'cuisine': 'Mexican',
    }},
    'corpus-titled-strawberry-muffins': {'action': 'edit', 'patch': {
        'name': 'Strawberry muffins',
        'tags': ['breakfast', 'snack'],
        'notes': 'Tender muffins of chopped fresh strawberries, butter, sugar, eggs, and flour — often topped with a sugar streusel.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-roasted-asparagus': {'action': 'edit', 'patch': {
        'name': 'Roasted asparagus',
        'notes': 'Trimmed asparagus tossed with olive oil, salt, and pepper, then roasted hot until tender and slightly charred — sometimes finished with lemon and Parmesan.',
    }},
    'corpus-titled-mayonnaise-rolls': {'action': 'edit', 'patch': {
        'name': 'Mayonnaise rolls',
        'tags': ['dinner', 'lunch'],
        'notes': 'A three-ingredient muffin-tin roll of self-rising flour, mayonnaise, and milk — quick, tender, drop-style.',
        'cuisine': 'Southern',
        'serving_grams': 55,
    }},
    'corpus-titled-dirt-pie': {'action': 'edit', 'patch': {
        'name': 'Dirt pie',
        'notes': 'A graham crust filled with chocolate pudding mixed with cream cheese and whipped topping, topped with crushed Oreos to look like dirt.',
        'cuisine': 'American',
    }},
    'corpus-titled-cheese-sticks': {'action': 'edit', 'patch': {
        'name': 'Cheese sticks (cheese straws)',
        'tags': ['snack'],
        'notes': 'A short cheddar-and-butter dough piped or sliced from a log and baked into thin crisp savory sticks — Southern.',
        'cuisine': 'Southern',
        'serving_grams': 30,
    }},
    'corpus-titled-sweet-and-sour-chicken-wings': {'action': 'edit', 'patch': {
        'name': 'Sweet and sour chicken wings',
        'tags': ['snack', 'dinner'],
        'notes': 'Battered chicken wings tossed in a sweet-and-sour sauce of pineapple, vinegar, ketchup, and brown sugar — Chinese-American restaurant style.',
        'cuisine': 'Chinese-American',
        'serving_grams': 170,
    }},
    'corpus-titled-bacon-roll-ups': {'action': 'edit', 'patch': {
        'name': 'Bacon roll-ups',
        'tags': ['snack'],
        'notes': 'Crustless bread rolled around cream cheese and asparagus or pickles, wrapped in bacon, and broiled until crisp.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-fruit-delight': {'action': 'edit', 'patch': {
        'name': 'Fruit delight',
        'tags': ['dessert'],
        'notes': 'A no-bake layered fruit dessert of pineapple, oranges, cherries, and bananas folded with sweetened cream cheese, whipped topping, and nuts.',
        'cuisine': 'American',
    }},
    'corpus-titled-old-fashioned-bread-pudding': {'action': 'edit', 'patch': {
        'name': 'Old-fashioned bread pudding',
        'notes': 'Cubed stale bread soaked overnight in a custard of eggs, milk, sugar, butter, cinnamon, and raisins — baked until set and served warm with a vanilla or bourbon sauce.',
        'cuisine': 'American',
    }},
    'corpus-titled-cranberry-pie': {'action': 'edit', 'patch': {
        'name': 'Cranberry pie (Nantucket)',
        'notes': 'Whole cranberries layered in a buttered pan with sugar and walnuts, topped with a simple butter-flour-egg batter, baked until golden.',
        'cuisine': 'American',
    }},
    'corpus-titled-five-flavor-pound-cake': {'action': 'edit', 'patch': {
        'name': 'Five flavor pound cake',
        'notes': 'A pound cake flavored with extracts of vanilla, lemon, coconut, rum, and butter, soaked after baking with a five-flavor sugar glaze.',
        'cuisine': 'Southern',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-pumpkin-cheesecake-bars': {'action': 'edit', 'patch': {
        'name': 'Pumpkin cheesecake bars',
        'tags': ['dessert'],
        'notes': 'Pumpkin-spiced cheesecake baked on a yellow-cake-mix or gingersnap crust, cut into bars after chilling.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-fruit-compote': {'action': 'edit', 'patch': {
        'name': 'Baked fruit compote',
        'notes': 'Mixed canned and dried fruits (pineapple, peaches, pears, cherries, prunes) baked with brown sugar and warm spices — served warm as a side.',
        'cuisine': 'American',
    }},
    'corpus-titled-peach-dessert': {'action': 'edit', 'patch': {
        'name': 'Peach dessert',
        'notes': 'A peach pie filling baked under a yellow-cake-mix-and-butter streusel — same family as peach dump cake.',
        'cuisine': 'American',
    }},
    'corpus-titled-toffee-squares': {'action': 'edit', 'patch': {
        'name': 'Toffee squares',
        'tags': ['dessert'],
        'notes': 'A brown-sugar-and-butter shortbread topped with melted chocolate while warm, sometimes dusted with chopped nuts — cut into squares.',
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

    print('corpus-titled batch-13 audit applied (entries 1801-1950 by frequency).')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
