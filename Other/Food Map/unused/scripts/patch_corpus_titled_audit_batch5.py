"""Corpus-titled meals audit — batch 5 (entries 601-750 by frequency, 180 -> 144).

Same standard: idiomatic sentence-case name, 1-2 sentence factual notes,
clean ingredient_categories, real-world tags, cuisine where the name implies
one, contains:['pork'] / ['alcohol'] only when traditionally mandatory.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

DECISIONS: dict[str, dict] = {
    'corpus-titled-yellow-squash-casserole': {'action': 'edit', 'patch': {
        'name': 'Yellow squash casserole',
        'notes': 'Sliced yellow squash baked with eggs, sour cream, and cheese under a buttered cracker topping — a Southern church-supper side.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-7-up-salad': {'action': 'edit', 'patch': {
        'name': '7-Up salad',
        'ingredient_categories': ['Tropical fruits', 'Citrus', 'Candy & desserts', 'Fresh cheese', 'Sugar & sweeteners', 'Soft drinks'],
        'tags': ['dessert'],
        'notes': 'Lemon-lime Jello set with crushed pineapple, mandarin oranges, and a bottle of 7-Up, sometimes folded with cream cheese topping.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-seafood-salad': {'action': 'edit', 'patch': {
        'name': 'Seafood salad',
        'notes': 'Cooked shrimp, crab, or imitation crab tossed with celery, onion, and a lemon-mayo dressing — served chilled on greens or in sandwiches.',
        'cuisine': 'American',
    }},
    'corpus-titled-ranger-cookies': {'action': 'edit', 'patch': {
        'name': 'Ranger cookies',
        'notes': 'A chewy drop cookie with oats, coconut, cornflakes (or Rice Krispies), and brown sugar — sometimes with chocolate chips or raisins.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-granola-bars': {'action': 'edit', 'patch': {
        'name': 'Granola bars',
        'notes': 'Oats, nuts, seeds, and dried fruit bound by a honey-and-butter syrup, pressed into a pan and baked or chilled until set.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-pizza-dip': {'action': 'edit', 'patch': {
        'name': 'Pizza dip',
        'tags': ['snack'],
        'notes': 'Cream cheese spread topped with marinara, mozzarella, and pepperoni, baked until melty — served with breadsticks or chips.',
        'cuisine': 'Italian-American',
        'contains_add': ['pork'],
        'serving_grams': 60,
    }},
    'corpus-titled-sweet-potatoes': {'action': 'edit', 'patch': {
        'name': 'Mashed sweet potatoes',
        'notes': 'Boiled or baked sweet potatoes mashed with butter, brown sugar, eggs, and warm spices — sometimes baked under marshmallows or streusel.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-stroganoff': {'action': 'edit', 'patch': {
        'name': 'Stroganoff',
        'notes': 'Strips of beef sautéed with mushrooms and onion in a sour-cream-and-mustard sauce — served over noodles or rice.',
        'cuisine': 'Russian',
    }},
    'corpus-titled-chop-suey': {'action': 'edit', 'patch': {
        'name': 'Chop suey',
        'notes': 'A Chinese-American stir-fry of beef or chicken with celery, bean sprouts, onions, and mushrooms in a soy-thickened sauce, served over rice or noodles.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-baklava': {'action': 'edit', 'patch': {
        'name': 'Baklava',
        'notes': 'Layers of buttered phyllo and chopped nuts baked until crisp, then soaked in a honey-and-citrus syrup — a Levantine and Eastern-Mediterranean pastry.',
        'cuisine': 'Mediterranean',
        'serving_grams': 60,
    }},
    'corpus-titled-christmas-salad': {'action': 'edit', 'patch': {
        'name': 'Christmas salad',
        'tags': ['dessert'],
        'notes': 'A holiday Jello mold or fruit salad of cranberries, oranges, pineapple, and pecans set with red or green gelatin and cream cheese.',
        'cuisine': 'American',
    }},
    'corpus-titled-creamed-spinach': {'action': 'edit', 'patch': {
        'name': 'Creamed spinach',
        'notes': 'Chopped spinach folded into a nutmeg-scented bechamel and finished with grated Parmesan — a steakhouse classic.',
        'cuisine': 'American',
    }},
    'corpus-titled-rhubarb-custard-pie': {'action': 'edit', 'patch': {
        'name': 'Rhubarb custard pie',
        'notes': 'Chopped rhubarb set in a sweet eggs-and-cream custard, baked in a single crust — tangy filling against a tender custard.',
        'cuisine': 'American',
    }},
    'corpus-titled-oatmeal-chocolate-chip-cookies': {'action': 'edit', 'patch': {
        'name': 'Oatmeal chocolate chip cookies',
        'notes': 'Drop cookies of oats, butter, brown sugar, and chocolate chips — chewier than chocolate chip cookies thanks to the oats.',
        'cuisine': 'American',
    }},
    'corpus-titled-pumpkin-soup': {'action': 'edit', 'patch': {
        'name': 'Pumpkin soup',
        'notes': 'Pumpkin puree simmered with onion, chicken stock, and warm spices, blended smooth and finished with cream.',
    }},
    'corpus-titled-fresh-peach-pie': {'action': 'edit', 'patch': {
        'name': 'Fresh peach pie',
        'notes': 'Sliced fresh peaches arranged in a pre-baked crust and set with a cooked sugar-and-cornstarch glaze — chilled rather than baked.',
        'cuisine': 'American',
    }},
    'corpus-titled-candied-yams': {'action': 'edit', 'patch': {
        'name': 'Candied yams',
        'notes': 'Sliced sweet potatoes baked in a butter-and-brown-sugar syrup with cinnamon and nutmeg — sometimes finished with marshmallows.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-jalapeno-cornbread': {'action': 'edit', 'patch': {
        'name': 'Jalapeño cornbread',
        'notes': 'A skillet cornbread enriched with cheddar, creamed corn, and chopped jalapeños — moist and lightly spicy.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-potato-candy': {'action': 'edit', 'patch': {
        'name': 'Potato candy',
        'notes': 'Mashed potato kneaded with powdered sugar into a pliable dough, rolled around peanut butter, and sliced into pinwheels.',
        'cuisine': 'Appalachian',
        'serving_grams': 30,
    }},
    'corpus-titled-bruschetta': {'action': 'edit', 'patch': {
        'name': 'Bruschetta',
        'tags': ['snack'],
        'notes': 'Toasted slices of crusty bread rubbed with garlic and topped with diced tomatoes, basil, and olive oil.',
        'cuisine': 'Italian',
        'serving_grams': 80,
    }},
    'corpus-titled-coconut-custard-pie': {'action': 'edit', 'patch': {
        'name': 'Coconut custard pie',
        'notes': 'A baked egg-milk-sugar custard with shredded coconut, set in a single pastry shell — the cooked version of a coconut cream pie.',
        'cuisine': 'American',
    }},
    'corpus-titled-apple-crunch': {'action': 'edit', 'patch': {
        'name': 'Apple crunch',
        'tags': ['dessert'],
        'notes': 'Spiced sliced apples baked under a brown-sugar-flour-butter streusel — a simpler cousin of apple crisp without oats.',
        'cuisine': 'American',
        'serving_grams': 140,
    }},
    'corpus-titled-rum-balls': {'action': 'edit', 'patch': {
        'name': 'Rum balls',
        'tags': ['dessert'],
        'notes': 'Crushed vanilla wafers or graham crackers mixed with cocoa, powdered sugar, corn syrup, pecans, and a slug of rum — rolled into balls and dusted in sugar.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
        'serving_grams': 30,
    }},
    'corpus-titled-chicken-delight': {'action': 'edit', 'patch': {
        'name': 'Chicken delight',
        'notes': 'A casserole or skillet of chicken breasts simmered with cream of mushroom soup, white wine or sherry, and mushrooms over rice or noodles.',
        'cuisine': 'American',
    }},
    'corpus-titled-barbecued-spareribs': {'action': 'edit', 'patch': {
        'name': 'Barbecued spareribs',
        'notes': 'Pork spareribs slow-roasted or grilled with a sweet-tangy barbecue sauce until the meat pulls cleanly from the bone.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-strawberry-punch': {'action': 'edit', 'patch': {
        'name': 'Strawberry punch',
        'ingredient_categories': ['Juices', 'Berries', 'Citrus', 'Sugar & sweeteners', 'Tropical fruits', 'Soft drinks'],
        'tags': ['snack'],
        'notes': 'Strawberries blended with pineapple juice, lemonade, and ginger ale — a pink non-alcoholic party drink.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-rice-salad': {'action': 'edit', 'patch': {
        'name': 'Rice salad',
        'notes': 'Cooked white rice tossed with chopped vegetables, olives, and an oil-and-vinegar dressing — served chilled as a picnic side.',
        'cuisine': 'American',
    }},
    'corpus-titled-sour-cream-cookies': {'action': 'edit', 'patch': {
        'name': 'Sour cream cookies',
        'notes': 'Soft, cakey drop cookies enriched with sour cream and a hint of nutmeg — sometimes topped with a powdered-sugar glaze.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-jewish-apple-cake': {'action': 'edit', 'patch': {
        'name': 'Jewish apple cake',
        'notes': 'A dairy-free tube-pan cake of oil, eggs, orange juice, and cinnamon-sugar-tossed apples layered into the batter — a Pennsylvania-Jewish standard.',
        'cuisine': 'Jewish',
    }},
    'corpus-titled-scalloped-pineapple': {'action': 'edit', 'patch': {
        'name': 'Scalloped pineapple',
        'notes': 'Crushed pineapple folded with eggs, sugar, butter, and bread cubes, baked into a sweet-savory side served alongside ham.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-macaroni-casserole': {'action': 'edit', 'patch': {
        'name': 'Macaroni casserole',
        'notes': 'Cooked macaroni baked with cheese, vegetables, and a creamy soup-based sauce — sometimes with ground beef stirred in.',
        'cuisine': 'American',
    }},
    'corpus-titled-sour-cream-cake': {'action': 'edit', 'patch': {
        'name': 'Sour cream cake',
        'notes': 'A tender Bundt or pound cake enriched with sour cream — sometimes swirled with cinnamon-pecan streusel.',
        'cuisine': 'American',
    }},
    'corpus-titled-onion-rings': {'action': 'edit', 'patch': {
        'name': 'Onion rings',
        'tags': ['snack', 'dinner'],
        'notes': 'Sliced onion rings dipped in a milk-and-egg batter or breaded, then deep-fried until crisp and golden.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-egg-nog': {'action': 'edit', 'patch': {
        'name': 'Eggnog',
        'ingredient_categories': ['Eggs', 'Milk', 'Cream & butter', 'Sugar & sweeteners', 'Ground spices', 'Alcoholic beverages'],
        'notes': 'Beaten eggs whipped with sugar, milk, cream, and spiced spirits (bourbon, rum, or brandy), topped with nutmeg — a holiday drink.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
        'serving_grams': 120,
    }},
    'corpus-titled-crumb-cake': {'action': 'edit', 'patch': {
        'name': 'Crumb cake',
        'tags': ['breakfast', 'dessert'],
        'notes': 'A tender butter cake topped with a thick brown-sugar-cinnamon-and-butter streusel — New York coffee-shop style.',
        'cuisine': 'American',
    }},
    'corpus-titled-congo-squares': {'action': 'edit', 'patch': {
        'name': 'Congo squares',
        'tags': ['dessert'],
        'notes': 'A brown-sugar-butter blondie packed with chocolate chips and chopped pecans, baked in a sheet pan and cut into squares.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-milky-way-cake': {'action': 'edit', 'patch': {
        'name': 'Milky Way cake',
        'notes': 'A chocolate-caramel butter cake made by melting Milky Way candy bars into the batter, often frosted with a chocolate-marshmallow icing.',
        'cuisine': 'American',
    }},
    'corpus-titled-pickled-okra': {'action': 'drop', 'reason': 'pickled condiment, not a coherent meal'},
    'corpus-titled-oatmeal-bread': {'action': 'edit', 'patch': {
        'name': 'Oatmeal bread',
        'notes': 'A soft yeasted sandwich loaf with rolled oats soaked in hot water and worked into the dough — hearty and slightly sweet.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-corn-bread-salad': {'action': 'edit', 'patch': {
        'name': 'Cornbread salad',
        'notes': 'Crumbled cornbread layered with beans, tomatoes, bacon, cheese, and ranch dressing in a glass bowl — a Southern potluck dish.',
        'cuisine': 'Southern',
        'contains_add': ['pork'],
    }},
    'corpus-titled-vegetable-lasagna': {'action': 'edit', 'patch': {
        'name': 'Vegetable lasagna',
        'notes': 'Layered pasta sheets with ricotta, sautéed mixed vegetables (zucchini, spinach, mushrooms), mozzarella, and marinara — the meatless lasagna.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-crawfish-etouffee': {'action': 'edit', 'patch': {
        'name': 'Crawfish étouffée',
        'notes': 'Crawfish tails simmered in a blond roux with the holy trinity of vegetables and Creole seasoning, served over rice.',
        'cuisine': 'Creole',
    }},
    'corpus-titled-frozen-cranberry-salad': {'action': 'edit', 'patch': {
        'name': 'Frozen cranberry salad',
        'tags': ['dessert'],
        'notes': 'Cranberry sauce folded with crushed pineapple, cream cheese, whipped cream, and pecans, frozen in a pan and sliced — a holiday side-as-dessert.',
        'cuisine': 'American',
    }},
    'corpus-titled-green-bean-salad': {'action': 'edit', 'patch': {
        'name': 'Green bean salad',
        'notes': 'Cooked green beans tossed with peppers, onions, and a sweet-tart vinegar dressing — chilled overnight.',
    }},
    'corpus-titled-pink-salad': {'action': 'edit', 'patch': {
        'name': 'Pink salad',
        'tags': ['dessert'],
        'notes': 'A pink Jello-and-cream-cheese mold set with crushed pineapple, maraschino cherries, and chopped pecans — a Southern church-cookbook dessert.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-zucchini-soup': {'action': 'edit', 'patch': {
        'name': 'Zucchini soup',
        'notes': 'Sliced zucchini simmered with onion, herbs, and chicken broth, blended smooth and finished with cream or yogurt.',
    }},
    'corpus-titled-pineapple-cookies': {'action': 'edit', 'patch': {
        'name': 'Pineapple cookies',
        'notes': 'A soft drop cookie made with crushed pineapple folded into a butter-sugar-egg batter, sometimes glazed.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-pumpkin-cheesecake': {'action': 'edit', 'patch': {
        'name': 'Pumpkin cheesecake',
        'notes': 'A baked cheesecake of cream cheese, pumpkin puree, and warm spices on a graham-cracker or pecan crust — a Thanksgiving alternative to pumpkin pie.',
        'cuisine': 'American',
    }},
    'corpus-titled-peach-crisp': {'action': 'edit', 'patch': {
        'name': 'Peach crisp',
        'tags': ['dessert'],
        'notes': 'Sweetened sliced peaches baked under a crunchy oat-and-butter streusel — served warm, often with ice cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-beef-jerky': {'action': 'edit', 'patch': {
        'name': 'Beef jerky',
        'notes': 'Strips of lean beef marinated in soy, Worcestershire, and spices, then slowly dried in a low oven or dehydrator until chewy.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-chocolate-truffles': {'action': 'edit', 'patch': {
        'name': 'Chocolate truffles',
        'notes': 'Chocolate ganache (chocolate and warm cream) chilled, scooped into balls, and rolled in cocoa, nuts, or coatings.',
        'cuisine': 'French',
        'serving_grams': 30,
    }},
    'corpus-titled-oven-stew': {'action': 'edit', 'patch': {
        'name': 'Oven beef stew',
        'notes': 'Cubed beef and root vegetables tossed with tomato juice or soup and seasonings, sealed in a Dutch oven, and baked low for hours.',
        'cuisine': 'American',
    }},
    'corpus-titled-5-cup-salad': {'action': 'edit', 'patch': {
        'name': 'Five cup salad (variant)',
        'tags': ['dessert'],
        'notes': 'Equal cups of mandarin oranges, pineapple chunks, mini marshmallows, shredded coconut, and sour cream — same Southern dessert as five-cup salad.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-caramel-brownies': {'action': 'edit', 'patch': {
        'name': 'Caramel brownies',
        'notes': 'A chocolate-cake-mix batter with a layer of melted caramel-and-evaporated-milk filling and chocolate chips, baked into bars.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-cherry-cheese-pie': {'action': 'edit', 'patch': {
        'name': 'Cherry cheese pie',
        'notes': 'A no-bake pie of sweetened cream cheese filling in a graham crust, topped with canned cherry pie filling.',
        'cuisine': 'American',
    }},
    'corpus-titled-pork-chops-and-rice': {'action': 'edit', 'patch': {
        'name': 'Pork chops and rice',
        'notes': 'Bone-in pork chops baked over raw rice and broth (or cream of mushroom soup) until both are tender.',
        'cuisine': 'American',
    }},
    'corpus-titled-barbecue-beef': {'action': 'edit', 'patch': {
        'name': 'Barbecue beef',
        'notes': 'Slow-cooked shredded beef (chuck or brisket) tossed in a sweet-tangy barbecue sauce, served on buns or over rice.',
        'cuisine': 'American',
    }},
    'corpus-titled-spinach-pie': {'action': 'edit', 'patch': {
        'name': 'Spinach pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'Chopped spinach baked in a pastry crust or phyllo with eggs, feta, and herbs — a quiche-or-spanakopita-style bake.',
        'cuisine': 'Greek',
        'serving_grams': 200,
    }},
    'corpus-titled-ham-rolls': {'action': 'edit', 'patch': {
        'name': 'Ham rolls',
        'tags': ['snack'],
        'notes': 'Slices of ham spread with cream cheese, rolled around a pickle spear or asparagus, and sliced into pinwheels — a cocktail appetizer.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-chicken-noodle-casserole': {'action': 'edit', 'patch': {
        'name': 'Chicken noodle casserole',
        'notes': 'Cooked egg noodles baked with shredded chicken, peas, and cream of mushroom or chicken soup under a cheese-and-crumb topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-egg-drop-soup': {'action': 'edit', 'patch': {
        'name': 'Egg drop soup',
        'notes': 'Chicken broth thickened with cornstarch, into which beaten egg is streamed to form delicate ribbons — a Chinese-American restaurant staple.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-carrot-bread': {'action': 'edit', 'patch': {
        'name': 'Carrot bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A spiced quick bread folded with grated carrots — moist and lightly sweet, often with raisins or nuts.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-date-bars': {'action': 'edit', 'patch': {
        'name': 'Date bars',
        'tags': ['dessert'],
        'notes': 'Cooked dates sandwiched between layers of an oat-and-brown-sugar crumble, baked and cut into bars.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-broccoli-bake': {'action': 'edit', 'patch': {
        'name': 'Broccoli bake',
        'notes': 'Broccoli florets baked in a cheese-and-cream-of-mushroom-soup sauce with mushrooms and an egg-bound topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-baked-chicken-breasts': {'action': 'edit', 'patch': {
        'name': 'Baked chicken breasts',
        'notes': 'Boneless chicken breasts baked with sour cream and cream of mushroom soup until tender — a low-effort weeknight bake.',
        'cuisine': 'American',
    }},
    'corpus-titled-broccoli-cheese-casserole': {'action': 'edit', 'patch': {
        'name': 'Broccoli cheese casserole',
        'notes': 'Broccoli florets baked with rice, cream of mushroom soup, and Cheez Whiz or shredded cheddar — a Southern potluck side.',
        'cuisine': 'American',
    }},
    'corpus-titled-wedding-punch': {'action': 'edit', 'patch': {
        'name': 'Wedding punch',
        'ingredient_categories': ['Juices', 'Citrus', 'Tropical fruits', 'Sugar & sweeteners', 'Soft drinks'],
        'tags': ['snack'],
        'notes': 'A non-alcoholic punch of mixed juices and ginger ale or sherbet — served from a bowl at receptions.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-brunch-casserole': {'action': 'edit', 'patch': {
        'name': 'Brunch casserole',
        'notes': 'A make-ahead bake of eggs, milk, cheese, bread, and ham or sausage — assembled overnight and baked in the morning.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-plum-cake': {'action': 'edit', 'patch': {
        'name': 'Plum cake',
        'notes': 'A spiced oil-based cake folded with chopped fresh plums or strained baby-food plums — moist and lightly fruity.',
        'cuisine': 'American',
    }},
    'corpus-titled-holiday-punch': {'action': 'edit', 'patch': {
        'name': 'Holiday punch',
        'ingredient_categories': ['Juices', 'Citrus', 'Tropical fruits', 'Berries', 'Sugar & sweeteners', 'Soft drinks'],
        'tags': ['snack'],
        'notes': 'A festive non-alcoholic punch of cranberry, orange, and pineapple juices with ginger ale — served from a bowl with citrus floats.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-tomato-pie': {'action': 'edit', 'patch': {
        'name': 'Tomato pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'Sliced ripe tomatoes layered in a baked pie crust with basil, then topped with a mixture of mayo and shredded cheese, baked until golden.',
        'cuisine': 'Southern',
        'serving_grams': 200,
    }},
    'corpus-titled-chicken-nuggets': {'action': 'edit', 'patch': {
        'name': 'Chicken nuggets',
        'tags': ['snack', 'dinner'],
        'notes': 'Bite-size pieces of chicken breast breaded or battered and baked or fried — a kid-friendly favorite.',
        'cuisine': 'American',
        'serving_grams': 170,
    }},
    'corpus-titled-cavatini': {'action': 'edit', 'patch': {
        'name': 'Cavatini',
        'notes': 'A baked pasta casserole of ziti, rotini, or shells with ground beef, Italian sausage, peppers, marinara, and mozzarella — Pizza Hut-style.',
        'cuisine': 'Italian-American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-chili-con-queso': {'action': 'edit', 'patch': {
        'name': 'Chili con queso',
        'tags': ['snack'],
        'notes': 'Velveeta-style processed cheese melted with chiles, tomatoes, and aromatics — served warm with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-hello-dollies': {'action': 'edit', 'patch': {
        'name': 'Hello dollies (seven-layer bars)',
        'tags': ['dessert'],
        'notes': 'A graham-cracker crust topped with butterscotch chips, chocolate chips, shredded coconut, and chopped pecans, drizzled with sweetened condensed milk and baked.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-freezer-pickles': {'action': 'drop', 'reason': 'pickled condiment, not a coherent meal'},
    'corpus-titled-cashew-chicken': {'action': 'edit', 'patch': {
        'name': 'Cashew chicken',
        'notes': 'Diced chicken stir-fried with cashews, peppers, and onions in a soy-and-ginger sauce — served over rice.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-jello-cake': {'action': 'edit', 'patch': {
        'name': 'Jello poke cake',
        'notes': 'A baked white or yellow cake poked all over and saturated with fruit-flavored gelatin, then topped with whipped topping — a 1970s potluck classic.',
        'cuisine': 'American',
    }},
    'corpus-titled-ham-casserole': {'action': 'edit', 'patch': {
        'name': 'Ham casserole',
        'notes': 'Cubed ham baked with potatoes or noodles, peas, and cheese in a cream-of-mushroom or cheese sauce — a leftover-ham one-dish meal.',
        'cuisine': 'American',
    }},
    'corpus-titled-congo-bars': {'action': 'edit', 'patch': {
        'name': 'Congo bars',
        'tags': ['dessert'],
        'notes': 'Brown-sugar-and-butter blondies packed with chocolate chips and chopped nuts — chewy and toffee-flavored.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-shortbread': {'action': 'edit', 'patch': {
        'name': 'Shortbread',
        'tags': ['dessert'],
        'notes': 'A classic Scottish biscuit of just butter, sugar, and flour — pressed flat or pricked, baked low, and cut into wedges or fingers.',
        'cuisine': 'British',
        'serving_grams': 30,
    }},
    'corpus-titled-orange-chicken': {'action': 'edit', 'patch': {
        'name': 'Orange chicken',
        'notes': 'Battered chicken pieces deep-fried and tossed in a glossy orange-and-soy glaze — the Panda Express American-Chinese standard.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-breakfast-burritos': {'action': 'edit', 'patch': {
        'name': 'Breakfast burritos',
        'notes': 'Flour tortillas wrapped around scrambled eggs, breakfast sausage or bacon, cheese, and potatoes — sometimes salsa and beans too.',
        'cuisine': 'Tex-Mex',
        'contains_add': ['pork'],
        'serving_grams': 250,
    }},
    'corpus-titled-m-m-cookies': {'action': 'edit', 'patch': {
        'name': 'M&M cookies',
        'notes': 'Classic drop cookies with M&M candies pressed into a butter-brown-sugar dough — bright and chewy.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-chicken-and-noodles': {'action': 'edit', 'patch': {
        'name': 'Chicken and noodles',
        'notes': 'Shredded chicken simmered with thick egg noodles in chicken broth — served over mashed potatoes in Midwestern style.',
        'cuisine': 'American',
    }},
    'corpus-titled-italian-meatballs': {'action': 'edit', 'patch': {
        'name': 'Italian meatballs',
        'notes': 'Ground beef and pork mixed with breadcrumbs, egg, milk, Parmesan, and herbs, rolled into balls and simmered in marinara.',
        'cuisine': 'Italian-American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-chicken-stock': {'action': 'drop', 'reason': 'cooking component (stock), not a coherent meal'},
    'corpus-titled-squash-pie': {'action': 'edit', 'patch': {
        'name': 'Squash pie',
        'notes': 'A custard pie of pureed winter squash or butternut, eggs, milk, sugar, and warm spices — close cousin of pumpkin pie.',
        'cuisine': 'American',
    }},
    'corpus-titled-french-bread': {'action': 'edit', 'patch': {
        'name': 'French bread',
        'notes': 'A long, crusty yeasted loaf of flour, water, salt, and yeast — light interior, crackly crust.',
        'cuisine': 'French',
        'serving_grams': 55,
    }},
    'corpus-titled-baking-powder-biscuits': {'action': 'edit', 'patch': {
        'name': 'Baking powder biscuits',
        'tags': ['breakfast', 'dinner'],
        'notes': 'A quick bread of flour, baking powder, milk, and cold fat — patted, cut, and baked into tender flaky rounds.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-blueberry-delight': {'action': 'edit', 'patch': {
        'name': 'Blueberry delight',
        'tags': ['dessert'],
        'notes': 'A no-bake layered dessert of pecan shortbread crust, sweetened cream cheese, blueberry pie filling, and whipped topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-brisket': {'action': 'edit', 'patch': {
        'name': 'Brisket',
        'notes': 'A tough cut of beef seasoned and slowly cooked low (smoked, braised, or oven-roasted) until fork-tender.',
        'cuisine': 'American',
    }},
    'corpus-titled-scalloped-oysters': {'action': 'edit', 'patch': {
        'name': 'Scalloped oysters',
        'notes': 'Shucked oysters layered with crushed crackers, butter, and seasonings, soaked in milk or cream and baked until just set.',
        'cuisine': 'American',
    }},
    'corpus-titled-pecan-pralines': {'action': 'edit', 'patch': {
        'name': 'Pecan pralines',
        'tags': ['dessert'],
        'notes': 'Sugar, cream, butter, and pecans cooked to soft-ball, beaten, and dropped onto wax paper to set — the New Orleans candy.',
        'cuisine': 'Creole',
        'serving_grams': 40,
    }},
    'corpus-titled-zucchini-quiche': {'action': 'edit', 'patch': {
        'name': 'Zucchini quiche',
        'notes': 'Sliced zucchini baked in an egg-and-cheese custard, sometimes in a Bisquick-based crustless form.',
        'cuisine': 'American',
    }},
    'corpus-titled-chili-cheese-dip': {'action': 'edit', 'patch': {
        'name': 'Chili cheese dip',
        'tags': ['snack'],
        'notes': 'Cream cheese spread in a dish, topped with canned chili and shredded cheese, baked or microwaved until bubbly.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-tomato-soup-cake': {'action': 'edit', 'patch': {
        'name': 'Tomato soup cake',
        'notes': 'A Depression-era spice cake leavened by a can of condensed tomato soup in place of milk — moist with raisins or nuts.',
        'cuisine': 'American',
        'serving_grams': 140,
    }},
    'corpus-titled-devil-s-food-cake': {'action': 'edit', 'patch': {
        'name': "Devil's food cake",
        'notes': 'A dark, tender chocolate layer cake leavened with baking soda — moister and richer than standard chocolate cake.',
        'cuisine': 'American',
    }},
    'corpus-titled-cranberry-chicken': {'action': 'edit', 'patch': {
        'name': 'Cranberry chicken',
        'notes': 'Chicken pieces baked over a sauce of jellied cranberry sauce and Catalina or French dressing mixed with onion soup mix.',
        'cuisine': 'American',
    }},
    'corpus-titled-spiced-nuts': {'action': 'edit', 'patch': {
        'name': 'Spiced nuts',
        'tags': ['snack'],
        'notes': 'Mixed nuts coated in an egg-white-and-sugar slurry with cinnamon, ginger, and cayenne, baked slowly until crisp.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-chicken-chili': {'action': 'edit', 'patch': {
        'name': 'Chicken chili',
        'notes': 'Shredded or ground chicken simmered with beans, peppers, tomatoes, and chili spices — a lighter alternative to beef chili.',
        'cuisine': 'American',
    }},
    'corpus-titled-cold-oven-pound-cake': {'action': 'edit', 'patch': {
        'name': 'Cold oven pound cake',
        'notes': 'A dense pound cake placed in a cold oven and slow-baked as the oven heats up — gives a thick crisp crust and tender crumb.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-apricot-nectar-cake': {'action': 'edit', 'patch': {
        'name': 'Apricot nectar cake',
        'notes': 'A yellow Bundt cake made with apricot nectar and lemon-flavored gelatin, soaked after baking with a lemon-sugar glaze.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-lemon-curd': {'action': 'edit', 'patch': {
        'name': 'Lemon curd',
        'tags': ['condiment', 'dessert'],
        'notes': 'Lemon juice, sugar, eggs, and butter cooked gently until thickened to a glossy spreadable curd — used on scones, cakes, or by the spoon.',
        'cuisine': 'British',
        'serving_grams': 30,
    }},
    'corpus-titled-oriental-salad': {'action': 'edit', 'patch': {
        'name': 'Oriental ramen salad',
        'notes': 'Shredded cabbage and lettuce tossed with crushed ramen noodles, slivered almonds, sesame seeds, and a soy-vinegar dressing.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-vidalia-onion-casserole': {'action': 'edit', 'patch': {
        'name': 'Vidalia onion casserole',
        'notes': 'Sliced sweet Vidalia onions baked with butter, cream, eggs, and shredded cheese under a buttered cracker crust — a Georgia favorite.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-stuffed-pork-chops': {'action': 'edit', 'patch': {
        'name': 'Stuffed pork chops',
        'notes': 'Thick-cut pork chops cut with a pocket and filled with herbed bread stuffing, then baked or seared.',
        'cuisine': 'American',
    }},
    'corpus-titled-whoopie-pies': {'action': 'edit', 'patch': {
        'name': 'Whoopie pies',
        'notes': 'Two cake-like chocolate cookies sandwiched around a fluffy marshmallow or vanilla buttercream filling — Pennsylvania Dutch and New England favorite.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-italian-pasta-salad': {'action': 'edit', 'patch': {
        'name': 'Italian pasta salad',
        'notes': 'Cooked rotini or penne tossed with peppers, olives, pepperoni, mozzarella, and Italian dressing — a picnic staple.',
        'cuisine': 'Italian-American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-creamy-rice-pudding': {'action': 'edit', 'patch': {
        'name': 'Creamy rice pudding',
        'notes': 'Cooked rice simmered slowly in milk with sugar, vanilla, and cinnamon until thick and creamy — served warm or chilled.',
    }},
    'corpus-titled-crab-casserole': {'action': 'edit', 'patch': {
        'name': 'Crab casserole',
        'notes': 'Lump crab mixed with mayonnaise, eggs, milk, peppers, and breadcrumbs, baked under buttered cracker crumbs and cheese.',
        'cuisine': 'American',
    }},
    'corpus-titled-summer-sausage': {'action': 'edit', 'patch': {
        'name': 'Homemade summer sausage',
        'tags': ['snack'],
        'notes': 'Ground beef mixed with cure (Morton Tender Quick), seasonings, and liquid smoke, shaped into logs and baked slowly — a homemade cured sausage.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-pecan-pie-bars': {'action': 'edit', 'patch': {
        'name': 'Pecan pie bars',
        'notes': 'A shortbread crust topped with pecan-pie custard, baked and cut into bars — pecan pie in finger-food form.',
        'cuisine': 'Southern',
        'serving_grams': 60,
    }},
    'corpus-titled-corn-souffle': {'action': 'edit', 'patch': {
        'name': 'Corn soufflé',
        'notes': 'A puffed-up bake of corn kernels, cream-style corn, eggs, butter, sour cream, and a touch of cornbread mix — pudding-like and slightly sweet.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-green-beans': {'action': 'edit', 'patch': {
        'name': 'Southern green beans',
        'notes': 'Snap beans slow-cooked with bacon or salt pork, onions, and broth until tender — a Southern long-cooked side.',
        'cuisine': 'Southern',
        'contains_add': ['pork'],
    }},
    'corpus-titled-peanut-butter-brownies': {'action': 'edit', 'patch': {
        'name': 'Peanut butter brownies',
        'notes': 'A peanut butter cookie-bar topped with melted chocolate, or chocolate brownies swirled with peanut butter — both eat like a Reese\'s cup.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-cheese-grits': {'action': 'edit', 'patch': {
        'name': 'Cheese grits',
        'tags': ['breakfast', 'dinner'],
        'notes': 'Stone-ground grits simmered in water or milk, then folded with butter, eggs, and sharp cheddar — sometimes baked into a casserole.',
        'cuisine': 'Southern',
        'serving_grams': 260,
    }},
    'corpus-titled-chocolate-chip-cheesecake': {'action': 'edit', 'patch': {
        'name': 'Chocolate chip cheesecake',
        'notes': 'A baked cream-cheese cheesecake folded with mini chocolate chips, set on a graham or chocolate-cookie crust.',
        'cuisine': 'American',
    }},
    'corpus-titled-corned-beef-and-cabbage': {'action': 'edit', 'patch': {
        'name': 'Corned beef and cabbage',
        'notes': 'A brined corned-beef brisket simmered with cabbage, potatoes, and carrots — the Irish-American St. Patrick\'s Day meal.',
        'cuisine': 'Irish-American',
    }},
    'corpus-titled-beef-barbecue': {'action': 'edit', 'patch': {
        'name': 'Beef barbecue',
        'notes': 'Shredded slow-cooked beef simmered in a sweet-tangy barbecue sauce, served on a soft bun.',
        'cuisine': 'American',
    }},
    'corpus-titled-soft-sugar-cookies': {'action': 'edit', 'patch': {
        'name': 'Soft sugar cookies',
        'notes': 'A pillow-soft cake-like sugar cookie made tender by sour cream or buttermilk — frosted with vanilla or almond icing.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-thumbprint-cookies': {'action': 'edit', 'patch': {
        'name': 'Thumbprint cookies',
        'notes': 'A buttery shortbread or nut-rolled cookie pressed in the center with a thumb, then filled with jam or chocolate.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-cream-of-mushroom-soup': {'action': 'edit', 'patch': {
        'name': 'Cream of mushroom soup',
        'notes': 'Mushrooms simmered with onion and herbs, blended (or left chunky), and thickened with a milk-and-roux base into a creamy soup.',
        'cuisine': 'American',
    }},
    'corpus-titled-curry-dip': {'action': 'edit', 'patch': {
        'name': 'Curry dip',
        'tags': ['snack'],
        'notes': 'Mayo and sour cream blended with curry powder, lemon, garlic, and Worcestershire — chilled and served with raw vegetables.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-chicken-gumbo': {'action': 'edit', 'patch': {
        'name': 'Chicken gumbo',
        'notes': 'Chicken simmered in a dark-roux broth with the trinity of vegetables, okra, and andouille sausage — served over rice.',
        'cuisine': 'Creole',
    }},
    'corpus-titled-swiss-vegetable-medley': {'action': 'edit', 'patch': {
        'name': 'Swiss vegetable medley',
        'notes': 'Frozen mixed vegetables (broccoli, carrots, cauliflower) baked with sour cream, cream of mushroom soup, and Swiss cheese under a buttered fried-onion top.',
        'cuisine': 'American',
    }},
    'corpus-titled-beef-brisket': {'action': 'edit', 'patch': {
        'name': 'Beef brisket',
        'notes': 'A tough cut of beef rubbed with seasonings and slowly braised, smoked, or oven-roasted until fork-tender.',
        'cuisine': 'American',
    }},
    'corpus-titled-onion-casserole': {'action': 'edit', 'patch': {
        'name': 'Onion casserole',
        'notes': 'Sliced sweet onions baked in butter and cream of mushroom soup under a topping of buttered crackers and shredded cheese.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-turkey-casserole': {'action': 'edit', 'patch': {
        'name': 'Turkey casserole',
        'notes': 'Cubed cooked turkey baked with stuffing or noodles, mushroom soup, vegetables, and cheese — a leftover-turkey one-dish meal.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-brownies': {'action': 'edit', 'patch': {
        'name': 'Chocolate brownies',
        'notes': 'A dense fudgy bar of chocolate, butter, sugar, eggs, and a small amount of flour — baked just until the center sets.',
        'serving_grams': 60,
    }},
    'corpus-titled-shrimp-etouffee': {'action': 'edit', 'patch': {
        'name': 'Shrimp étouffée',
        'notes': 'Shrimp simmered in a blond-roux base with the trinity of vegetables, Creole seasoning, and shrimp stock, served over rice.',
        'cuisine': 'Creole',
    }},
    'corpus-titled-chow-chow': {'action': 'drop', 'reason': 'pickled relish / canning preserve, not a coherent meal'},
    'corpus-titled-ham-roll-ups': {'action': 'edit', 'patch': {
        'name': 'Ham roll-ups',
        'tags': ['snack'],
        'notes': 'Slices of ham spread with cream cheese, rolled around a pickle spear or asparagus, and sliced into pinwheel appetizers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-applesauce-cookies': {'action': 'edit', 'patch': {
        'name': 'Applesauce cookies',
        'notes': 'Soft spice-cookies sweetened and made moist by applesauce, often folded with raisins and walnuts.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-rhubarb-crunch': {'action': 'edit', 'patch': {
        'name': 'Rhubarb crunch',
        'tags': ['dessert'],
        'notes': 'Chopped rhubarb baked between layers of oat-and-brown-sugar crumble — a tart spring counterpart to apple crisp.',
        'cuisine': 'American',
    }},
    'corpus-titled-party-chicken': {'action': 'edit', 'patch': {
        'name': 'Party chicken',
        'notes': 'Chicken breasts wrapped in bacon or topped with dried beef, baked in sour cream and cream of mushroom soup — a 1960s entertaining classic.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-grasshopper-pie': {'action': 'edit', 'patch': {
        'name': 'Grasshopper pie',
        'notes': 'A chilled pie of crème de menthe and crème de cacao folded into marshmallows and whipped cream, set in a chocolate-cookie crust.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-brown-sugar-pound-cake': {'action': 'edit', 'patch': {
        'name': 'Brown sugar pound cake',
        'notes': 'A dense pound cake sweetened entirely (or mostly) with brown sugar — caramel-toned and finished with a caramel glaze.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-fish-chowder': {'action': 'edit', 'patch': {
        'name': 'Fish chowder',
        'notes': 'Cubed white fish simmered with diced potatoes, onions, and milk or cream — a New England-style fish soup.',
        'cuisine': 'American',
    }},
    'corpus-titled-pigs-in-a-blanket': {'action': 'edit', 'patch': {
        'name': 'Pigs in a blanket',
        'ingredient_categories': ['Processed meat', 'Baked snacks & pastries'],
        'tags': ['snack'],
        'notes': 'Mini hot dogs (or cocktail wieners) wrapped in crescent-roll dough and baked — a party appetizer.',
        'cuisine': 'American',
        'contains_add': ['pork'],
        'serving_grams': 80,
    }},
    'corpus-titled-tortellini-soup': {'action': 'edit', 'patch': {
        'name': 'Tortellini soup',
        'notes': 'Cheese tortellini simmered in a tomato-and-broth base with sausage, spinach, and Parmesan — Olive Garden\'s "tortellini en brodo" style.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-fresh-fruit-dip': {'action': 'edit', 'patch': {
        'name': 'Fresh fruit dip',
        'tags': ['snack', 'dessert'],
        'notes': 'Sweetened cream cheese whipped with marshmallow fluff or vanilla pudding mix — served chilled with sliced fresh fruit.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-morning-glory-muffins': {'action': 'edit', 'patch': {
        'name': 'Morning glory muffins',
        'tags': ['breakfast'],
        'notes': 'A spiced bran-or-flour muffin folded with grated carrot, apple, coconut, raisins, and walnuts — moist and hearty.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-frozen-salad': {'action': 'edit', 'patch': {
        'name': 'Frozen fruit salad',
        'tags': ['dessert'],
        'notes': 'Mixed canned and fresh fruit folded with sweetened cream cheese and whipped topping, frozen in a pan and sliced — a retro Southern dessert.',
        'cuisine': 'American',
    }},
    'corpus-titled-flan': {'action': 'edit', 'patch': {
        'name': 'Flan',
        'tags': ['dessert'],
        'notes': 'A baked egg-and-milk custard with sugar caramelized in the bottom of the mold — inverted to serve so the caramel pools over the top.',
        'cuisine': 'Spanish',
        'serving_grams': 130,
    }},
    'corpus-titled-parmesan-potatoes': {'action': 'edit', 'patch': {
        'name': 'Parmesan potatoes',
        'notes': 'Halved or quartered potatoes tossed in melted butter and grated Parmesan, then roasted until the cheese forms a crispy bottom crust.',
        'cuisine': 'American',
    }},
    'corpus-titled-soft-molasses-cookies': {'action': 'edit', 'patch': {
        'name': 'Soft molasses cookies',
        'notes': 'A soft chewy spice cookie of butter, molasses, brown sugar, and warm spices — rolled in sugar before baking.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-cranberry-nut-bread': {'action': 'edit', 'patch': {
        'name': 'Cranberry nut bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A holiday quick bread of fresh or dried cranberries, orange zest, and chopped walnuts in a tender batter.',
        'cuisine': 'American',
    }},
    'corpus-titled-peach-ice-cream': {'action': 'edit', 'patch': {
        'name': 'Peach ice cream',
        'notes': 'Custard ice cream churned with ripe pureed peaches and chunks of fresh peach — a Southern summer staple.',
        'cuisine': 'Southern',
        'serving_grams': 85,
    }},
    'corpus-titled-sunday-brunch': {'action': 'edit', 'patch': {
        'name': 'Sunday brunch bake',
        'notes': 'A generic egg-and-vegetable casserole or quiche-style bake assembled the night before and baked for Sunday brunch.',
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

    print('corpus-titled batch-5 audit applied (entries 601-750 by frequency).')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
