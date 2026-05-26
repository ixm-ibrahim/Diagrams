"""Corpus-titled meals audit — batch 15 (entries 2101-2250 by frequency, 59 -> 55)."""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

DECISIONS: dict[str, dict] = {
    'corpus-titled-tapioca-pudding': {'action': 'edit', 'patch': {
        'name': 'Tapioca pudding',
        'notes': 'Small tapioca pearls cooked in milk with sugar, eggs, and vanilla until thickened — chilled to a soft, beaded pudding.',
        'cuisine': 'American',
    }},
    'corpus-titled-stuffed-grape-leaves': {'action': 'edit', 'patch': {
        'name': 'Stuffed grape leaves (dolmas)',
        'notes': 'Grape leaves wrapped around a rice filling with herbs, lemon, and sometimes ground lamb or beef, then braised in lemon broth — Greek/Mediterranean.',
        'cuisine': 'Greek',
    }},
    'corpus-titled-ho-ho-cake': {'action': 'edit', 'patch': {
        'name': 'Ho Ho cake',
        'notes': 'A chocolate sheet cake filled with a flour-based whipped buttercream and topped with chocolate ganache — Hostess Ho Ho flavors in cake form.',
        'cuisine': 'American',
    }},
    'corpus-titled-sugarless-cookies': {'action': 'edit', 'patch': {
        'name': 'Sugarless cookies',
        'notes': 'Drop cookies sweetened by raisins or apples and dates instead of added sugar — a diabetic-friendly oat cookie.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-stuffed-squash': {'action': 'edit', 'patch': {
        'name': 'Stuffed squash',
        'notes': 'Halved acorn or summer squash hollowed and filled with seasoned breadcrumbs, herbs, sausage, or rice, then baked until tender.',
    }},
    'corpus-titled-mushroom-rice': {'action': 'edit', 'patch': {
        'name': 'Mushroom rice',
        'notes': 'Long-grain rice baked with sliced mushrooms, onions, beef consommé, and butter — a hands-off oven pilaf.',
        'cuisine': 'American',
    }},
    'corpus-titled-cauliflower-and-broccoli-salad': {'action': 'edit', 'patch': {
        'name': 'Cauliflower and broccoli salad',
        'notes': 'Raw cauliflower and broccoli florets tossed with red onion, bacon, and a sour-cream-mayo-sugar dressing — chilled overnight.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-spinach-salad-dressing': {'action': 'drop', 'reason': 'dressing component, not a coherent meal'},
    'corpus-titled-one-bowl-brownies': {'action': 'edit', 'patch': {
        'name': 'One-bowl brownies',
        'notes': 'Brownies mixed in a single bowl — melted butter and cocoa stirred with sugar, eggs, vanilla, flour, and nuts; baked into chewy bars.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-meringue-cookies': {'action': 'edit', 'patch': {
        'name': 'Meringue cookies',
        'tags': ['dessert'],
        'notes': 'Beaten egg whites whipped with sugar to stiff glossy peaks, piped onto sheets, and baked very slowly until crisp and dry.',
        'cuisine': 'French',
        'serving_grams': 30,
    }},
    'corpus-titled-overnight-french-toast': {'action': 'edit', 'patch': {
        'name': 'Overnight French toast',
        'notes': 'Thick slices of bread soaked overnight in an egg-cream-cinnamon custard, then baked into a strata-style breakfast in the morning.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-stuffed-manicotti': {'action': 'edit', 'patch': {
        'name': 'Stuffed manicotti',
        'notes': 'Pasta tubes filled with a ricotta-Parmesan-and-egg mixture (sometimes with ground beef), nested in marinara with mozzarella, baked until bubbling.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-candied-carrots': {'action': 'edit', 'patch': {
        'name': 'Candied carrots',
        'notes': 'Sliced or baby carrots cooked in butter, brown sugar, and a touch of ginger or cinnamon until glazed and tender.',
    }},
    'corpus-titled-chocolate-candy': {'action': 'edit', 'patch': {
        'name': 'Chocolate candy (fudge)',
        'tags': ['dessert'],
        'notes': 'A long-cooked chocolate fudge of sugar, butter, evaporated milk, chocolate chips, and marshmallow creme with chopped nuts.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-raspberry-pie': {'action': 'edit', 'patch': {
        'name': 'Raspberry pie',
        'notes': 'A double-crust or lattice pie of fresh raspberries tossed with sugar and a thickener — sweet-tart with deep ruby juice.',
        'cuisine': 'American',
    }},
    'corpus-titled-chickpea-salad': {'action': 'edit', 'patch': {
        'name': 'Chickpea salad',
        'notes': 'Chickpeas tossed with diced cucumber, tomato, red onion, parsley, lemon, and olive oil — a Mediterranean lunch salad.',
        'cuisine': 'Mediterranean',
    }},
    'corpus-titled-avocado-salsa': {'action': 'edit', 'patch': {
        'name': 'Avocado salsa',
        'tags': ['snack', 'condiment'],
        'notes': 'Diced avocado folded with tomato, red onion, jalapeño, cilantro, and lime — chunkier than guacamole.',
        'cuisine': 'Mexican',
        'serving_grams': 60,
    }},
    'corpus-titled-chocolate-chunk-cookies': {'action': 'edit', 'patch': {
        'name': 'Chocolate chunk cookies',
        'notes': 'Drop cookies of butter-and-brown-sugar dough with hand-chopped chocolate chunks (rather than uniform chips) and pecans.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-sesame-noodles': {'action': 'edit', 'patch': {
        'name': 'Sesame noodles',
        'notes': 'Cold or warm noodles tossed in a sauce of toasted sesame oil, soy sauce, peanut butter or tahini, sugar, and rice vinegar — Chinese-American.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-tomato-salsa': {'action': 'edit', 'patch': {
        'name': 'Tomato salsa',
        'tags': ['snack', 'condiment'],
        'notes': 'Diced ripe tomato, onion, jalapeño, cilantro, and lime — a fresh chunky salsa for chips and tacos.',
        'cuisine': 'Mexican',
        'serving_grams': 60,
    }},
    'corpus-titled-italian-meatloaf': {'action': 'edit', 'patch': {
        'name': 'Italian meatloaf (variant)',
        'notes': 'A ground-beef loaf with Italian breadcrumbs, Parmesan, herbs, and marinara, baked under mozzarella — lasagna-flavor meatloaf.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-marshmallows': {'action': 'edit', 'patch': {
        'name': 'Marshmallows',
        'tags': ['dessert'],
        'notes': 'Sugar syrup whipped into a bloomed-gelatin base with vanilla until thick and airy, set in a pan and cut into pillowy squares.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-bible-cake': {'action': 'edit', 'patch': {
        'name': 'Bible cake (Scripture cake)',
        'notes': 'A spiced fruit-and-nut cake whose ingredients are named by their Bible references (Jeremiah\'s figs, Genesis\'s butter, etc.) — a Victorian church-supper novelty.',
        'cuisine': 'American',
    }},
    'corpus-titled-miniature-cheesecakes': {'action': 'edit', 'patch': {
        'name': 'Miniature cheesecakes',
        'notes': 'Individual cheesecakes baked in muffin tins over a vanilla-wafer crust, topped with fruit pie filling — single-portion party desserts.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-roasted-pumpkin-seeds': {'action': 'edit', 'patch': {
        'name': 'Roasted pumpkin seeds',
        'tags': ['snack'],
        'notes': 'Pumpkin seeds rinsed clean, tossed with melted butter and salt, and roasted at low heat until crisp — a fall snack from Halloween pumpkins.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-chicken-and-wild-rice': {'action': 'edit', 'patch': {
        'name': 'Chicken and wild rice',
        'notes': 'Diced chicken baked with a wild rice blend in mushroom-soup-and-broth gravy with onion and celery.',
        'cuisine': 'American',
    }},
    'corpus-titled-mexican-layered-dip': {'action': 'edit', 'patch': {
        'name': 'Mexican layered dip (variant)',
        'tags': ['snack'],
        'notes': 'Refried beans layered with seasoned sour cream or guacamole, salsa, shredded cheese, lettuce, tomatoes, and olives — chilled.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-cherry-jello-salad': {'action': 'edit', 'patch': {
        'name': 'Cherry Jello salad',
        'tags': ['dessert'],
        'notes': 'Cherry gelatin set with canned cherries, crushed pineapple, and pecans — sometimes layered with sweetened cream cheese.',
        'cuisine': 'American',
    }},
    'corpus-titled-chinese-salad': {'action': 'edit', 'patch': {
        'name': 'Chinese chicken salad (variant)',
        'notes': 'Shredded cabbage and lettuce tossed with chicken, crispy ramen or wonton strips, almonds, sesame seeds, and a soy-sesame-sugar dressing.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-french-silk-chocolate-pie': {'action': 'edit', 'patch': {
        'name': 'French silk chocolate pie',
        'notes': 'A chocolate-mousse pie of butter, sugar, eggs, and melted chocolate whipped until airy, poured into a baked crust and chilled.',
        'cuisine': 'American',
    }},
    'corpus-titled-onion-bread': {'action': 'edit', 'patch': {
        'name': 'Onion bread',
        'notes': 'A quick or yeasted bread enriched with sautéed onions and butter — moist and savory, sometimes with dill or cheese.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-coconut-pies': {'action': 'edit', 'patch': {
        'name': 'Coconut pies (impossible)',
        'notes': 'A blender batter of eggs, milk, sugar, butter, coconut, and Bisquick poured into pie pans — bakes self-crusted with a custard middle and toasted coconut top.',
        'cuisine': 'American',
    }},
    'corpus-titled-cheesecake-cookies': {'action': 'edit', 'patch': {
        'name': 'Cheesecake cookies',
        'notes': 'A graham-cracker-and-butter crust topped with sweetened cream-cheese-egg-and-lemon filling, baked and cut into squares.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-fruited-chicken-salad': {'action': 'edit', 'patch': {
        'name': 'Fruited chicken salad',
        'notes': 'Diced chicken tossed with mandarin oranges, pineapple, grapes, and chopped pecans in a creamy mayo dressing — served chilled.',
        'cuisine': 'American',
    }},
    'corpus-titled-strawberry-soup': {'action': 'edit', 'patch': {
        'name': 'Cold strawberry soup',
        'tags': ['dessert'],
        'notes': 'Crushed sweetened strawberries blended with sour cream, white wine, and citrus — a chilled summer dessert soup.',
        'cuisine': 'European',
        'contains_add': ['alcohol'],
        'serving_grams': 240,
    }},
    'corpus-titled-chocolate-no-bake-cookies': {'action': 'edit', 'patch': {
        'name': 'Chocolate no-bake cookies',
        'notes': 'Cocoa, sugar, milk, and butter boiled to a fudge, then stirred with peanut butter and oats and dropped onto wax paper to set.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-fiesta-dip': {'action': 'edit', 'patch': {
        'name': 'Fiesta dip',
        'tags': ['snack'],
        'notes': 'A cold layered Tex-Mex dip of seasoned sour cream, salsa, shredded cheese, olives, and tomatoes — served with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-lime-pie': {'action': 'edit', 'patch': {
        'name': 'Key lime pie',
        'notes': 'Lime juice whisked into sweetened condensed milk and egg yolks, poured into a graham crust, baked briefly, and chilled — Florida classic.',
        'cuisine': 'American',
        'serving_grams': 140,
    }},
    'corpus-titled-roasted-garlic': {'action': 'drop', 'reason': 'cooking component (roasted garlic), not a coherent meal'},
    'corpus-titled-cheesecake-pie': {'action': 'edit', 'patch': {
        'name': 'Cheesecake pie',
        'notes': 'A slimmer cheesecake set in a pie pan — sweetened cream cheese, eggs, and vanilla baked in a graham crust, topped with sour cream and fruit.',
        'cuisine': 'American',
    }},
    'corpus-titled-breakfast-bake': {'action': 'edit', 'patch': {
        'name': 'Breakfast bake (variant)',
        'notes': 'A make-ahead casserole of eggs, milk, sausage or bacon, cheese, and bread cubes — assembled overnight and baked in the morning.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-jello-pie': {'action': 'edit', 'patch': {
        'name': 'Jello pie',
        'notes': 'Fruit-flavored Jello dissolved in hot water, whisked with ice cream and folded with fruit, poured into a graham crust and chilled until set.',
        'cuisine': 'American',
    }},
    'corpus-titled-unbaked-fruit-cake': {'action': 'edit', 'patch': {
        'name': 'Unbaked fruitcake',
        'notes': 'Crushed graham crackers or vanilla wafers mixed with candied fruit, dates, nuts, and sweetened condensed milk — pressed in a pan and chilled.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-cranberry-cake': {'action': 'edit', 'patch': {
        'name': 'Cranberry cake',
        'notes': 'A butter cake folded with fresh cranberries and orange zest — a Thanksgiving dessert sometimes served with a warm butter sauce.',
        'cuisine': 'American',
    }},
    'corpus-titled-chinese-almond-cookies': {'action': 'edit', 'patch': {
        'name': 'Chinese almond cookies',
        'tags': ['dessert'],
        'notes': 'Shortbread-style cookies with whole almonds pressed into the center — a Chinese-bakery and Lunar-New-Year staple.',
        'cuisine': 'Chinese',
        'serving_grams': 30,
    }},
    'corpus-titled-potato-puffs': {'action': 'edit', 'patch': {
        'name': 'Potato puffs',
        'notes': 'Mashed potatoes mixed with eggs and flour, piped or scooped onto sheets, and baked into golden puffed mounds.',
        'cuisine': 'American',
    }},
    'corpus-titled-oyster-casserole': {'action': 'edit', 'patch': {
        'name': 'Oyster casserole',
        'notes': 'Shucked oysters layered with crushed crackers, butter, and seasonings, soaked in milk or cream and baked until just set.',
        'cuisine': 'American',
    }},
    'corpus-titled-apple-turnovers': {'action': 'edit', 'patch': {
        'name': 'Apple turnovers',
        'tags': ['dessert', 'breakfast'],
        'notes': 'Squares of puff pastry filled with spiced cooked apples, folded and sealed, baked until golden, and drizzled with a sugar glaze.',
        'cuisine': 'American',
    }},
    'corpus-titled-make-ahead-mashed-potatoes': {'action': 'edit', 'patch': {
        'name': 'Make-ahead mashed potatoes',
        'notes': 'Mashed potatoes whipped with cream cheese, sour cream, butter, and seasonings, refrigerated, then reheated in the oven — party-potatoes-style.',
        'cuisine': 'American',
    }},
    'corpus-titled-mustard-pickles': {'action': 'drop', 'reason': 'pickled condiment (mustard relish / canning preserve), not a coherent meal'},
    'corpus-titled-calzone': {'action': 'edit', 'patch': {
        'name': 'Calzone',
        'notes': 'Pizza dough folded around fillings of ricotta, mozzarella, cured meats, and vegetables, sealed and baked until golden — a Neapolitan stuffed pizza.',
        'cuisine': 'Italian',
        'contains_add': ['pork'],
    }},
    'corpus-titled-cupcakes': {'action': 'edit', 'patch': {
        'name': 'Cupcakes',
        'notes': 'Individual portion cakes baked in muffin tins (butter or oil base) and topped with frosting — vanilla, chocolate, red velvet, or flavored.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-mashed-sweet-potatoes': {'action': 'edit', 'patch': {
        'name': 'Mashed sweet potatoes',
        'notes': 'Boiled or baked sweet potatoes mashed with butter, brown sugar, and warm spices — sometimes finished with maple syrup or pecans.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-chicken-burritos': {'action': 'edit', 'patch': {
        'name': 'Chicken burritos',
        'notes': 'Flour tortillas wrapped around shredded chicken, rice, beans, cheese, and salsa — Tex-Mex/Mission-style.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-banana-split-salad': {'action': 'edit', 'patch': {
        'name': 'Banana split salad',
        'tags': ['dessert'],
        'notes': 'Sliced bananas, strawberries, and pineapple folded with chopped pecans and a sweet whipped-cream-and-cream-cheese dressing.',
        'cuisine': 'American',
    }},
    'corpus-titled-mulled-wine': {'action': 'edit', 'patch': {
        'name': 'Mulled wine',
        'tags': ['snack'],
        'notes': 'Red wine warmed with sugar, cinnamon sticks, cloves, orange peel, and a splash of brandy — Glühwein in the German tradition.',
        'cuisine': 'European',
        'contains_add': ['alcohol'],
        'serving_grams': 150,
    }},
    'corpus-titled-creme-de-menthe-brownies': {'action': 'edit', 'patch': {
        'name': 'Crème de menthe brownies',
        'notes': 'Fudge brownies topped with a layer of buttercream tinted with crème de menthe, then a layer of melted chocolate.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
        'serving_grams': 60,
    }},
    'corpus-titled-pecan-pies': {'action': 'edit', 'patch': {
        'name': 'Pecan pies',
        'notes': 'A custard of eggs, sugar, butter, and corn syrup studded with pecan halves, baked in a flaky crust — Southern Thanksgiving classic.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-hardee-s-biscuits': {'action': 'edit', 'patch': {
        'name': "Hardee's biscuits (copycat)",
        'tags': ['breakfast'],
        'notes': 'A copycat of the Hardee\'s drop biscuit — self-rising flour, shortening, and buttermilk; tall, tender, and slightly sweet.',
        'cuisine': 'Southern',
        'serving_grams': 55,
    }},
    'corpus-titled-texas-potatoes': {'action': 'edit', 'patch': {
        'name': 'Texas potatoes',
        'notes': 'Frozen hash browns baked with sour cream, cream of chicken soup, butter, and cheddar — funeral-potatoes-style.',
        'cuisine': 'American',
    }},
    'corpus-titled-autumn-soup': {'action': 'edit', 'patch': {
        'name': 'Autumn soup',
        'notes': 'Ground beef simmered with potatoes, carrots, celery, onion, and tomato in beef broth — a hearty stockpot soup for chilly months.',
        'cuisine': 'American',
    }},
    'corpus-titled-pear-cake': {'action': 'edit', 'patch': {
        'name': 'Pear cake',
        'notes': 'A spiced oil-based cake folded with diced ripe pears and pecans — moist with warm cinnamon-clove notes.',
        'cuisine': 'American',
    }},
    'corpus-titled-peppermint-patties': {'action': 'edit', 'patch': {
        'name': 'Homemade peppermint patties',
        'tags': ['dessert'],
        'notes': 'A fondant of powdered sugar, butter, sweetened condensed milk, and peppermint extract rolled flat and dipped in melted chocolate.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-hopping-john': {'action': 'edit', 'patch': {
        'name': "Hopping John (variant)",
        'notes': 'Black-eyed peas simmered with rice, smoked pork (ham hock or bacon), onion, and peppers — a Carolina-Lowcountry New Year\'s dish.',
        'cuisine': 'Southern',
        'contains_add': ['pork'],
    }},
    'corpus-titled-chicken-and-rice-bake': {'action': 'edit', 'patch': {
        'name': 'Chicken and rice bake',
        'notes': 'Raw rice and chicken pieces baked together in mushroom-soup-and-broth gravy with onions and peppers — hands-off oven dinner.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-peanut-butter-bars': {'action': 'edit', 'patch': {
        'name': 'Chocolate peanut butter bars',
        'tags': ['dessert'],
        'notes': 'A peanut-butter shortbread base topped with melted chocolate and a peanut-butter-powdered-sugar drizzle — cut into bars.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-fudge-brownie-pie': {'action': 'edit', 'patch': {
        'name': 'Fudge brownie pie',
        'notes': 'A fudgy brownie batter baked in a pie pan with chocolate chips and walnuts — served wedge-cut with whipped cream or ice cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-toasted-pecans': {'action': 'edit', 'patch': {
        'name': 'Buttered toasted pecans',
        'tags': ['snack'],
        'notes': 'Pecan halves tossed with melted butter and salt, then slow-roasted in the oven until aromatic and crisp.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-ham-and-cheese-quiche': {'action': 'edit', 'patch': {
        'name': 'Ham and cheese quiche',
        'notes': 'A pastry shell filled with diced ham, Swiss cheese, eggs, and cream — baked into a savory custard tart.',
        'cuisine': 'French',
    }},
    'corpus-titled-lemon-jello-salad': {'action': 'edit', 'patch': {
        'name': 'Lemon Jello salad',
        'tags': ['dessert'],
        'notes': 'Lemon gelatin set with crushed pineapple, cottage cheese or cream cheese, and whipped topping — a Southern molded dessert salad.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-fried-catfish': {'action': 'edit', 'patch': {
        'name': 'Fried catfish',
        'notes': 'Catfish fillets soaked in buttermilk, dredged in seasoned cornmeal, and pan- or deep-fried until crisp — Southern fish-fry standard.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-pineapple-pudding': {'action': 'edit', 'patch': {
        'name': 'Pineapple pudding',
        'notes': 'Vanilla pudding folded with crushed pineapple, layered with vanilla wafers and whipped topping — a Southern banana-pudding cousin.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-mexican-layer-dip': {'action': 'edit', 'patch': {
        'name': 'Mexican layer dip (variant)',
        'tags': ['snack'],
        'notes': 'A cold layered dip of refried beans or seasoned sour cream, salsa, shredded cheese, lettuce, olives, and onions — same as 7-layer dip.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-yankee-pot-roast': {'action': 'edit', 'patch': {
        'name': 'Yankee pot roast',
        'notes': 'A chuck or round roast seared, then slow-braised in beef broth with onions, carrots, potatoes, and herbs until fork-tender.',
        'cuisine': 'American',
    }},
    'corpus-titled-pear-preserves': {'action': 'drop', 'reason': 'fruit preserve / canning recipe, not a coherent meal'},
    'corpus-titled-creme-fraiche': {'action': 'drop', 'reason': 'dairy product / ingredient, not a coherent meal'},
    'corpus-titled-baked-sweet-potatoes': {'action': 'edit', 'patch': {
        'name': 'Baked sweet potatoes',
        'notes': 'Whole sweet potatoes baked in their skins at high heat until tender, split open and topped with butter, brown sugar, and cinnamon.',
    }},
    'corpus-titled-hamburgers': {'action': 'edit', 'patch': {
        'name': 'Hamburgers',
        'notes': 'Ground beef patties seasoned with salt and pepper, seared or grilled, served on a soft bun with lettuce, tomato, onion, pickle, and condiments.',
        'cuisine': 'American',
    }},
    'corpus-titled-orange-pound-cake': {'action': 'edit', 'patch': {
        'name': 'Orange pound cake',
        'notes': 'A dense pound cake bright with orange zest and juice, often soaked or glazed with an orange-sugar syrup.',
        'cuisine': 'American',
    }},
    'corpus-titled-candy-bar-pie': {'action': 'edit', 'patch': {
        'name': 'Candy bar pie',
        'notes': 'Melted Snickers or Mars bars folded with cream cheese and whipped topping, poured into an Oreo or chocolate-cookie crust and frozen.',
        'cuisine': 'American',
    }},
    'corpus-titled-sausage': {'action': 'edit', 'patch': {
        'name': 'Homemade sausage patties',
        'notes': 'Ground pork mixed with sage, thyme, salt, pepper, and a touch of brown sugar or maple, formed into patties and pan-fried.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-spaghetti-with-meat-sauce': {'action': 'edit', 'patch': {
        'name': 'Spaghetti with meat sauce',
        'notes': 'Cooked spaghetti topped with a long-simmered tomato sauce of ground beef, onions, garlic, mushrooms, and Italian herbs.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-smoked-salmon-dip': {'action': 'edit', 'patch': {
        'name': 'Smoked salmon dip',
        'tags': ['snack'],
        'notes': 'Smoked salmon blended with cream cheese, sour cream, lemon, dill, capers, and onion — served chilled with crackers or bagel chips.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-pumpkin-pecan-pie': {'action': 'edit', 'patch': {
        'name': 'Pumpkin pecan pie',
        'notes': 'A layered pie of pumpkin custard topped with a pecan-pie corn-syrup-and-pecan layer, baked together until set.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-7-layer-dip': {'action': 'edit', 'patch': {
        'name': '7 layer dip (variant)',
        'tags': ['snack'],
        'notes': 'Refried beans layered with seasoned sour cream, salsa, shredded cheese, lettuce, olives, and tomato — served chilled with chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-carrots': {'action': 'edit', 'patch': {
        'name': 'Glazed carrots (side)',
        'notes': 'Sliced or baby carrots cooked tender in butter and brown sugar with a splash of orange juice — generic "carrots" side.',
    }},
    'corpus-titled-chicken-satay': {'action': 'edit', 'patch': {
        'name': 'Chicken satay',
        'notes': 'Strips of chicken marinated in coconut milk, soy, and curry spices, threaded on skewers and grilled — served with peanut sauce.',
        'cuisine': 'Thai',
    }},
    'corpus-titled-chocolate-mousse-cake': {'action': 'edit', 'patch': {
        'name': 'Chocolate mousse cake',
        'notes': 'A chocolate cake or flourless chocolate base topped with airy chocolate mousse, chilled until set — sometimes ganache-glazed.',
        'cuisine': 'French',
    }},
    'corpus-titled-calzones': {'action': 'edit', 'patch': {
        'name': 'Calzones (variant)',
        'notes': 'Pizza dough folded around fillings of ricotta, mozzarella, cured meats, and vegetables, sealed and baked until golden.',
        'cuisine': 'Italian-American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-garlic-potatoes': {'action': 'edit', 'patch': {
        'name': 'Garlic roasted potatoes',
        'notes': 'Quartered potatoes tossed with olive oil, garlic, rosemary, and salt, then roasted hot until crisp outside and tender inside.',
    }},
    'corpus-titled-fish-cakes': {'action': 'edit', 'patch': {
        'name': 'Fish cakes',
        'tags': ['dinner', 'lunch'],
        'notes': 'Cooked white fish mixed with mashed potato, egg, onion, lemon, and herbs, formed into patties and pan-fried — British/Atlantic-Coast classic.',
        'cuisine': 'British',
        'serving_grams': 170,
    }},
    'corpus-titled-popcorn': {'action': 'edit', 'patch': {
        'name': 'Buttered popcorn',
        'notes': 'Popcorn kernels popped in oil or a hot-air popper, tossed with melted butter and salt — the classic movie snack.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-clams-casino': {'action': 'edit', 'patch': {
        'name': 'Clams casino',
        'tags': ['snack', 'dinner'],
        'notes': 'Half-shell clams topped with a savory mix of bacon, peppers, onion, garlic, butter, and breadcrumbs, then broiled until the bacon crisps.',
        'cuisine': 'Italian-American',
        'contains_add': ['pork'],
        'serving_grams': 170,
    }},
    'corpus-titled-garlic-soup': {'action': 'edit', 'patch': {
        'name': 'Garlic soup',
        'notes': 'Many cloves of garlic sautéed in olive oil, simmered with bread and broth, blended smooth — Spanish sopa de ajo or French Provençal style.',
        'cuisine': 'European',
    }},
    'corpus-titled-red-lentil-soup': {'action': 'edit', 'patch': {
        'name': 'Red lentil soup',
        'notes': 'Red lentils simmered with onion, carrot, tomato, and warm spices (cumin, paprika, ginger), blended (or partially) and finished with lemon.',
        'cuisine': 'Middle Eastern',
    }},
    'corpus-titled-quinoa-salad': {'action': 'edit', 'patch': {
        'name': 'Quinoa salad',
        'notes': 'Cooked quinoa tossed with diced cucumber, tomato, herbs, lemon, and olive oil — a Mediterranean-inflected grain salad.',
        'cuisine': 'Mediterranean',
    }},
    'corpus-titled-red-velvet-cupcakes': {'action': 'edit', 'patch': {
        'name': 'Red velvet cupcakes',
        'tags': ['dessert'],
        'notes': 'Red-tinted cocoa-buttermilk cupcakes (with vinegar for the chemical reaction with cocoa), topped with cream cheese frosting.',
        'cuisine': 'Southern',
        'serving_grams': 80,
    }},
    'corpus-titled-diabetic-cookies': {'action': 'edit', 'patch': {
        'name': 'Diabetic cookies',
        'notes': 'Drop cookies sweetened by dried fruit (raisins, dates) and apples in place of granulated sugar — diabetic-friendly oat cookies.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-butterscotch-squares': {'action': 'edit', 'patch': {
        'name': 'Butterscotch squares',
        'tags': ['dessert'],
        'notes': 'A brown-sugar-and-butter blondie packed with butterscotch chips and pecans — chewy and toffee-toned.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-oreo-pie': {'action': 'edit', 'patch': {
        'name': 'Oreo pie',
        'notes': 'Crushed Oreos mixed with melted butter for a crust, filled with sweetened cream cheese, chocolate pudding, and whipped topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-bread-stuffing': {'action': 'edit', 'patch': {
        'name': 'Bread stuffing',
        'notes': 'Cubed bread mixed with sautéed onions, celery, sage, parsley, and broth, baked into the Thanksgiving stuffing.',
        'cuisine': 'American',
    }},
    'corpus-titled-oatmeal-bars': {'action': 'edit', 'patch': {
        'name': 'Oatmeal bars',
        'notes': 'Oats, brown sugar, butter, and eggs baked into bars — sometimes layered with jam, chocolate chips, or dates.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-peanut-butter-temptations': {'action': 'edit', 'patch': {
        'name': 'Peanut butter temptations',
        'tags': ['dessert'],
        'notes': 'Peanut butter cookies baked in muffin tins and pressed warm with a Reese\'s mini peanut butter cup — same family as peanut butter blossoms.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-ugly-duckling-cake': {'action': 'edit', 'patch': {
        'name': 'Ugly Duckling cake',
        'notes': 'A yellow cake mix combined with crushed pineapple and a box of instant pudding, topped with a coconut-pecan-butter broiled glaze.',
        'cuisine': 'American',
    }},
    'corpus-titled-garlic-cheese-grits': {'action': 'edit', 'patch': {
        'name': 'Garlic cheese grits',
        'notes': 'Stone-ground grits cooked in broth or milk, then folded with butter, eggs, garlic, and sharp cheddar — baked or held creamy.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-cheese-crisps': {'action': 'edit', 'patch': {
        'name': 'Cheese crisps',
        'tags': ['snack'],
        'notes': 'Sharp cheddar, butter, flour, and Rice Krispies mixed and shaped into thin discs, baked into crisp savory bites — Southern.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-rolled-sugar-cookies': {'action': 'edit', 'patch': {
        'name': 'Rolled sugar cookies',
        'notes': 'A butter-sugar dough chilled, rolled flat, and cut into shapes — decorated with royal icing or sprinkles.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-hot-beef-dip': {'action': 'edit', 'patch': {
        'name': 'Hot beef dip',
        'tags': ['snack'],
        'notes': 'Cream cheese mixed with chipped beef, peppers, onion, and sour cream, baked until bubbly — served warm with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-pizzelles': {'action': 'edit', 'patch': {
        'name': 'Pizzelles',
        'tags': ['dessert'],
        'notes': 'A thin, crisp Italian waffle cookie of butter, eggs, sugar, flour, and anise (or vanilla) — pressed in a pizzelle iron into intricate patterns.',
        'cuisine': 'Italian',
        'serving_grams': 30,
    }},
    'corpus-titled-instant-hot-chocolate': {'action': 'edit', 'patch': {
        'name': 'Instant hot chocolate mix',
        'ingredient_categories': ['Sugar & sweeteners', 'Milk', 'Candy & desserts'],
        'notes': 'A dry pantry mix of powdered milk, cocoa, sugar, and powdered creamer — stirred into hot water for instant cocoa.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-lasagna-casserole': {'action': 'edit', 'patch': {
        'name': 'Lasagna casserole',
        'notes': 'Broken lasagna noodles or rotini layered with ground beef, marinara, ricotta, and mozzarella, baked until bubbly — lasagna without the rolling.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-date-nut-cake': {'action': 'edit', 'patch': {
        'name': 'Date nut cake',
        'notes': 'A spiced butter cake folded with chopped dates and walnuts or pecans, soaked or glazed with a brown-sugar caramel.',
        'cuisine': 'American',
    }},
    'corpus-titled-hot-bean-dip': {'action': 'edit', 'patch': {
        'name': 'Hot bean dip',
        'tags': ['snack'],
        'notes': 'Refried beans warmed with sour cream, salsa, cream cheese, and shredded cheddar — baked until bubbly, served with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-chocolate-chip-brownies': {'action': 'edit', 'patch': {
        'name': 'Chocolate chip brownies',
        'notes': 'Fudge brownies with chocolate chips folded into the batter — double-chocolate, baked just until the center sets.',
        'cuisine': 'American',
    }},
    'corpus-titled-sour-cream-muffins': {'action': 'edit', 'patch': {
        'name': 'Sour cream muffins',
        'tags': ['breakfast'],
        'notes': 'Tender muffins enriched with sour cream — soft, tangy crumb that bakes light and slightly sweet.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-pineapple-cheesecake': {'action': 'edit', 'patch': {
        'name': 'Pineapple cheesecake',
        'notes': 'A baked or no-bake cream-cheese cheesecake topped with crushed pineapple cooked with sugar and a thickener.',
        'cuisine': 'American',
    }},
    'corpus-titled-steak-soup': {'action': 'edit', 'patch': {
        'name': 'Steak soup',
        'notes': 'Cubed beef sirloin simmered with vegetables and a tomato-broth base, thickened with a flour-and-butter roux — Plaza-III Kansas City classic.',
        'cuisine': 'American',
    }},
    'corpus-titled-hot-tamale-pie': {'action': 'edit', 'patch': {
        'name': 'Hot tamale pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'A seasoned beef-and-corn-chili filling topped with cornbread batter and baked — a one-pan Tex-Mex casserole, slightly spicier.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 320,
    }},
    'corpus-titled-brown-rice-casserole': {'action': 'edit', 'patch': {
        'name': 'Brown rice casserole',
        'notes': 'Cooked brown rice baked with browned beef or chicken, mushrooms, vegetables, and mushroom soup — a hands-off oven dinner.',
        'cuisine': 'American',
    }},
    'corpus-titled-cauliflower-au-gratin': {'action': 'edit', 'patch': {
        'name': 'Cauliflower au gratin',
        'notes': 'Steamed cauliflower florets layered in a milk-and-cheese bechamel and baked under buttered breadcrumbs and more cheese.',
        'cuisine': 'French',
    }},
    'corpus-titled-golden-parmesan-potatoes': {'action': 'edit', 'patch': {
        'name': 'Golden Parmesan potatoes',
        'notes': 'Potato wedges tossed in flour, salt, paprika, and Parmesan, then roasted in butter on a hot sheet pan until golden and crisp.',
        'cuisine': 'American',
    }},
    'corpus-titled-condensed-milk': {'action': 'drop', 'reason': 'pantry ingredient (homemade sweetened condensed milk), not a coherent meal'},
    'corpus-titled-vegetable-quiche': {'action': 'edit', 'patch': {
        'name': 'Vegetable quiche',
        'notes': 'A pastry shell filled with an egg-and-cream custard, sautéed vegetables (broccoli, mushrooms, peppers), and cheese — meatless quiche.',
        'cuisine': 'French',
    }},
    'corpus-titled-beer-can-chicken': {'action': 'edit', 'patch': {
        'name': 'Beer can chicken',
        'notes': 'A whole chicken seasoned and propped upright on a half-full can of beer, then grilled or roasted — the beer steams the bird from the inside.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-belgian-waffles': {'action': 'edit', 'patch': {
        'name': 'Belgian waffles',
        'notes': 'A yeasted or chemically-leavened batter cooked in a deep-grid Belgian-style waffle iron — light, crisp, with deep pockets for syrup or fruit.',
        'cuisine': 'Belgian',
        'serving_grams': 200,
    }},
    'corpus-titled-spice-cookies': {'action': 'edit', 'patch': {
        'name': 'Spice cookies',
        'notes': 'Drop or rolled cookies of butter, brown sugar, eggs, and warm spices (cinnamon, ginger, cloves, allspice).',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-hot-fudge-pudding': {'action': 'edit', 'patch': {
        'name': 'Hot fudge pudding cake',
        'notes': 'A self-saucing chocolate cake — batter spread in a pan, topped with cocoa-sugar and boiling water, baked so a fudge sauce sinks beneath.',
        'cuisine': 'American',
    }},
    'corpus-titled-old-fashioned-rice-pudding': {'action': 'edit', 'patch': {
        'name': 'Old-fashioned rice pudding',
        'notes': 'Cooked rice simmered slowly in milk with sugar, eggs, vanilla, cinnamon, and raisins — baked or stovetop until thick and creamy.',
        'cuisine': 'American',
    }},
    'corpus-titled-potato-gnocchi': {'action': 'edit', 'patch': {
        'name': 'Potato gnocchi',
        'notes': 'Soft Italian dumplings of mashed potato, flour, and egg — boiled briefly and tossed with butter-sage, marinara, or pesto.',
        'cuisine': 'Italian',
    }},
    'corpus-titled-tunnel-of-fudge-cake': {'action': 'edit', 'patch': {
        'name': 'Tunnel of fudge cake',
        'notes': 'A walnut Bundt cake with a flour-frosting-mix center that bakes into a soft fudge tunnel — Pillsbury Bake-Off original.',
        'cuisine': 'American',
    }},
    'corpus-titled-four-layer-delight': {'action': 'edit', 'patch': {
        'name': 'Four layer delight',
        'tags': ['dessert'],
        'notes': 'A no-bake layered dessert of pecan-shortbread crust, sweetened cream cheese, chocolate or vanilla pudding, and whipped topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-energy-bars': {'action': 'edit', 'patch': {
        'name': 'Energy bars (homemade granola)',
        'tags': ['snack', 'breakfast'],
        'notes': 'Oats, dried fruit, nuts, seeds, and chocolate chips bound with peanut butter and honey or corn syrup, pressed into a pan and chilled.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-new-england-boiled-dinner': {'action': 'edit', 'patch': {
        'name': 'New England boiled dinner',
        'notes': 'A whole corned-beef brisket simmered with cabbage, potatoes, carrots, and turnips — Yankee-Irish-American St. Patrick\'s tradition.',
        'cuisine': 'American',
    }},
    'corpus-titled-chiles-rellenos': {'action': 'edit', 'patch': {
        'name': 'Chiles rellenos (variant)',
        'notes': 'Roasted poblano chiles stuffed with cheese, dipped in an egg-white batter, and fried golden — served in tomato sauce.',
        'cuisine': 'Mexican',
    }},
    'corpus-titled-corned-beef': {'action': 'edit', 'patch': {
        'name': 'Corned beef',
        'notes': 'A brined beef brisket simmered with cabbage, carrots, and potatoes — Irish-American St. Patrick\'s Day staple.',
        'cuisine': 'Irish-American',
    }},
    'corpus-titled-bbq-chicken': {'action': 'edit', 'patch': {
        'name': 'BBQ chicken',
        'notes': 'Chicken pieces brushed with barbecue sauce as they grill or roast, often after a dry rub of paprika, brown sugar, and garlic powder.',
        'cuisine': 'American',
    }},
    'corpus-titled-peanut-butter-cup-cookies': {'action': 'edit', 'patch': {
        'name': 'Peanut butter cup cookies',
        'tags': ['dessert'],
        'notes': 'Peanut butter cookies baked in muffin tins and pressed warm with a Reese\'s mini peanut butter cup — same family as peanut butter blossoms.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-hobo-stew': {'action': 'edit', 'patch': {
        'name': 'Hobo stew',
        'notes': 'A simple stockpot stew of ground beef, potatoes, carrots, onions, and tomato — Depression-era one-pot.',
        'cuisine': 'American',
    }},
    'corpus-titled-potluck-potatoes': {'action': 'edit', 'patch': {
        'name': 'Potluck potatoes',
        'notes': 'Frozen hash browns baked with sour cream, cream of chicken soup, butter, and cheddar under a cornflake topping — funeral-potatoes-style.',
        'cuisine': 'American',
    }},
    'corpus-titled-spaetzle': {'action': 'edit', 'patch': {
        'name': 'Spätzle',
        'notes': 'A soft German egg-noodle dough scraped or pressed into boiling water, then tossed with butter or browned in butter with crumbs.',
        'cuisine': 'German',
    }},
    'corpus-titled-taco-salad-dip': {'action': 'edit', 'patch': {
        'name': 'Taco salad dip',
        'tags': ['snack'],
        'notes': 'A cold layered dip of seasoned sour cream, salsa, shredded cheese, lettuce, tomatoes, and olives — served with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-hot-taco-dip': {'action': 'edit', 'patch': {
        'name': 'Hot taco dip',
        'tags': ['snack'],
        'notes': 'Cream cheese spread topped with taco-seasoned ground beef, salsa, and shredded cheese, baked or warmed until bubbly — chip dip.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-banana-pudding-cake': {'action': 'edit', 'patch': {
        'name': 'Banana pudding cake',
        'notes': 'A yellow cake mix combined with mashed banana, vanilla pudding, eggs, and oil, baked into a moist banana-flavored cake.',
        'cuisine': 'American',
    }},
    'corpus-titled-heavenly-hash-cake': {'action': 'edit', 'patch': {
        'name': 'Heavenly hash cake',
        'notes': 'A chocolate sheet cake topped warm with marshmallows, then drizzled with chocolate-cocoa-pecan frosting — Mississippi-Mud-Cake cousin.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-copper-penny-carrots': {'action': 'edit', 'patch': {
        'name': 'Copper penny carrots',
        'notes': 'Sliced cooked carrots ("pennies") tossed with bell pepper and onion in a tangy tomato-soup-and-vinegar marinade — chilled overnight.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-italian-cookies': {'action': 'edit', 'patch': {
        'name': 'Italian wedding cookies',
        'tags': ['dessert'],
        'notes': 'Soft anise-scented butter cookies, sometimes ricotta-based, dipped in a powdered-sugar glaze and topped with sprinkles — Italian-American holiday bake.',
        'cuisine': 'Italian-American',
        'serving_grams': 30,
    }},
    'corpus-titled-frozen-punch': {'action': 'edit', 'patch': {
        'name': 'Frozen punch',
        'ingredient_categories': ['Juices', 'Tropical fruits', 'Citrus', 'Sugar & sweeteners', 'Soft drinks'],
        'tags': ['snack'],
        'notes': 'Sweetened fruit juices frozen until slushy, then scooped into a punch bowl and topped with lemon-lime soda or ginger ale.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-rhubarb-cobbler': {'action': 'edit', 'patch': {
        'name': 'Rhubarb cobbler',
        'notes': 'Chopped rhubarb baked under a tender biscuit or batter topping — served warm with ice cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-cracker-candy': {'action': 'edit', 'patch': {
        'name': 'Saltine cracker candy (Christmas crack)',
        'tags': ['dessert'],
        'notes': 'Saltine crackers laid on a sheet pan, topped with a hot brown-sugar-butter caramel, sprinkled with chocolate chips that melt into a layer.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-cheesy-garlic-bread': {'action': 'edit', 'patch': {
        'name': 'Cheesy garlic bread',
        'tags': ['snack', 'dinner'],
        'notes': 'A loaf of Italian bread split, brushed with butter, garlic, and herbs, topped with mozzarella and Parmesan, baked until bubbly.',
        'cuisine': 'Italian-American',
        'serving_grams': 100,
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

    print('corpus-titled batch-15 audit applied (entries 2101-2250 by frequency).')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
