"""Corpus-titled meals audit — batch 17 (FINAL, all remaining 123 entries; freq 52 -> 50)."""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

DECISIONS: dict[str, dict] = {
    'corpus-titled-pistachio-pudding': {'action': 'edit', 'patch': {
        'name': 'Pistachio pudding salad',
        'tags': ['dessert'],
        'notes': 'Instant pistachio pudding mix folded with crushed pineapple, mini marshmallows, and whipped topping — same family as Watergate salad.',
        'cuisine': 'American',
    }},
    'corpus-titled-canadian-cheese-soup': {'action': 'edit', 'patch': {
        'name': 'Canadian cheese soup',
        'notes': 'Cubed potatoes simmered with chicken broth, milk, and shredded cheddar — sometimes with carrots and onion; Wisconsin/Canadian-border style.',
        'cuisine': 'American',
    }},
    'corpus-titled-raisin-bars': {'action': 'edit', 'patch': {
        'name': 'Raisin bars',
        'tags': ['dessert'],
        'notes': 'Plumped raisins folded into a spiced butter-sugar-egg-and-flour batter, baked into bars — sometimes glazed with powdered sugar.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-watermelon-salad': {'action': 'edit', 'patch': {
        'name': 'Watermelon feta salad',
        'notes': 'Cubed watermelon tossed with crumbled feta, mint, red onion, lime, and olive oil — a bright summer salad.',
        'cuisine': 'Mediterranean',
    }},
    'corpus-titled-bulgogi': {'action': 'edit', 'patch': {
        'name': 'Bulgogi',
        'notes': 'Thin-sliced beef marinated in soy sauce, sesame oil, sugar, garlic, and Asian pear, then grilled or pan-cooked hot — Korean classic.',
        'cuisine': 'Korean',
    }},
    'corpus-titled-potato-chowder': {'action': 'edit', 'patch': {
        'name': 'Potato chowder',
        'notes': 'Diced potatoes simmered in broth with onion and bacon, finished with milk and cream — sometimes topped with cheddar and chives.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-chicken-nachos': {'action': 'edit', 'patch': {
        'name': 'Chicken nachos',
        'tags': ['snack', 'dinner'],
        'notes': 'Tortilla chips piled with shredded chicken, salsa or enchilada sauce, melted cheese, jalapeños, and sour cream.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 260,
    }},
    'corpus-titled-mexican-pie': {'action': 'edit', 'patch': {
        'name': 'Mexican pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'Layered ground beef, beans, salsa, and cheese baked over a cornbread or biscuit crust — same family as tamale pie / impossible taco pie.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 320,
    }},
    'corpus-titled-chunky-guacamole': {'action': 'edit', 'patch': {
        'name': 'Chunky guacamole',
        'tags': ['snack', 'condiment'],
        'notes': 'Mashed ripe avocados mixed with diced tomato, red onion, jalapeño, cilantro, lime, and salt — chunky rather than smooth.',
        'cuisine': 'Mexican',
        'serving_grams': 60,
    }},
    'corpus-titled-sweet-potato-soup': {'action': 'edit', 'patch': {
        'name': 'Sweet potato soup',
        'notes': 'Roasted sweet potatoes simmered with onion, ginger, and chicken broth, blended smooth and finished with cream and warm spices.',
    }},
    'corpus-titled-grilled-shrimp': {'action': 'edit', 'patch': {
        'name': 'Grilled shrimp',
        'notes': 'Shrimp marinated in olive oil, lemon, garlic, and herbs, then threaded on skewers and grilled hot until just opaque.',
    }},
    'corpus-titled-vermicelli-salad': {'action': 'edit', 'patch': {
        'name': 'Vermicelli salad',
        'notes': 'Cooked vermicelli or fine pasta tossed with diced peppers, olives, and Italian-style dressing — chilled overnight.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-texas-trash': {'action': 'edit', 'patch': {
        'name': 'Texas trash (party mix)',
        'tags': ['snack'],
        'notes': 'Chex cereals, pretzels, and mixed nuts coated in a buttery Worcestershire-and-seasoning blend, baked until crisp — Chex-mix Texas variant.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-peanut-blossom-cookies': {'action': 'edit', 'patch': {
        'name': 'Peanut blossom cookies (variant)',
        'notes': 'Peanut butter cookies rolled in sugar and pressed with a Hershey\'s Kiss as soon as they come out of the oven.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-taco-sauce': {'action': 'drop', 'reason': 'sauce component, not a coherent meal'},
    'corpus-titled-potato-cake': {'action': 'edit', 'patch': {
        'name': 'Mashed potato cake',
        'notes': 'A spiced sweet cake with mashed potato folded into the batter for moistness, often with raisins, nuts, and chocolate.',
        'cuisine': 'American',
    }},
    'corpus-titled-cherry-fluff': {'action': 'edit', 'patch': {
        'name': 'Cherry fluff',
        'tags': ['dessert'],
        'notes': 'Cherry pie filling folded with sweetened condensed milk, crushed pineapple, mini marshmallows, and whipped topping — a Southern dessert salad.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-marshmallow-treats': {'action': 'edit', 'patch': {
        'name': 'Marshmallow treats (Rice Krispies)',
        'tags': ['dessert', 'snack'],
        'notes': 'Rice Krispies stirred into melted butter and marshmallows, pressed into a pan, and cut into squares.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-pineapple-cheese-casserole': {'action': 'edit', 'patch': {
        'name': 'Pineapple cheese casserole',
        'tags': ['dinner', 'lunch'],
        'notes': 'Canned pineapple chunks baked with sharp cheddar, sugar, and a buttery cracker topping — a Southern sweet-savory side.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-drop-cookies': {'action': 'edit', 'patch': {
        'name': 'Drop cookies',
        'notes': 'A generic name for any butter-sugar-egg-flour cookie dough dropped from a spoon onto a sheet (no rolling and cutting).',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-seafood-pasta': {'action': 'edit', 'patch': {
        'name': 'Seafood pasta',
        'notes': 'Linguine or fettuccine tossed with shrimp, scallops, or crab in a garlic-butter-olive-oil sauce with white wine and herbs.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-apple-pie-cake': {'action': 'edit', 'patch': {
        'name': 'Apple pie cake',
        'tags': ['dessert'],
        'notes': 'A moist butter cake folded with chopped apples, sometimes with pecans — eats more like a pie filling baked into a cake.',
        'cuisine': 'American',
    }},
    'corpus-titled-marzetti': {'action': 'edit', 'patch': {
        'name': 'Johnny Marzetti casserole',
        'notes': 'Cooked elbow macaroni mixed with ground beef, mushrooms, onions, peppers, and tomato sauce, topped with cheese and baked — an Ohio classic.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-baked-chicken-parmesan': {'action': 'edit', 'patch': {
        'name': 'Baked chicken parmesan',
        'notes': 'Breaded chicken breasts baked, then topped with marinara and mozzarella and broiled briefly to melt — a lighter chicken parm.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-dessert-pizza': {'action': 'edit', 'patch': {
        'name': 'Dessert pizza',
        'notes': 'A sugar-cookie crust spread with sweetened cream cheese and topped with sliced fresh fruit and a citrus glaze.',
        'cuisine': 'American',
    }},
    'corpus-titled-piccalilli': {'action': 'drop', 'reason': 'pickled relish / canning preserve, not a coherent meal'},
    'corpus-titled-cheese-rolls': {'action': 'edit', 'patch': {
        'name': 'Cheese pinwheels',
        'tags': ['snack'],
        'notes': 'Tortillas or crescent dough spread with seasoned cream cheese and shredded cheddar, rolled and sliced into pinwheels.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-hearty-potato-soup': {'action': 'edit', 'patch': {
        'name': 'Hearty potato soup',
        'notes': 'Diced potatoes simmered with onion and chicken broth, blended (or partially mashed), and finished with milk, cream, and butter.',
        'cuisine': 'American',
    }},
    'corpus-titled-cherry-cream-pie': {'action': 'edit', 'patch': {
        'name': 'Cherry cream pie',
        'notes': 'A no-bake pie of sweetened cream cheese filling in a graham crust, topped with canned cherry pie filling.',
        'cuisine': 'American',
    }},
    'corpus-titled-corn-pie': {'action': 'edit', 'patch': {
        'name': 'Corn pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'Sweet corn kernels baked in a custard of eggs, milk, sugar, and butter in a single crust — a Pennsylvania-Dutch sweet-savory pie.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-butterscotch-cake': {'action': 'edit', 'patch': {
        'name': 'Butterscotch cake',
        'notes': 'A yellow cake mix combined with butterscotch pudding mix, baked into a Bundt and finished with butterscotch glaze.',
        'cuisine': 'American',
    }},
    'corpus-titled-gingersnap-cookies': {'action': 'edit', 'patch': {
        'name': 'Gingersnap cookies',
        'notes': 'Crisp spiced cookies of molasses, butter, brown sugar, and ginger — rolled in sugar and baked until they crackle on top.',
        'serving_grams': 30,
    }},
    'corpus-titled-venison-stroganoff': {'action': 'edit', 'patch': {
        'name': 'Venison stroganoff',
        'notes': 'Strips of venison sautéed with mushrooms and onion in a sour-cream-and-mustard sauce, served over egg noodles.',
        'cuisine': 'American',
    }},
    'corpus-titled-party-salad': {'action': 'edit', 'patch': {
        'name': 'Party fruit salad',
        'tags': ['dessert'],
        'notes': 'A no-bake fruit salad of pineapple, mandarin oranges, and bananas folded with cream cheese, marshmallows, and whipped topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-strawberry-surprise': {'action': 'edit', 'patch': {
        'name': 'Strawberry surprise',
        'tags': ['dessert'],
        'notes': 'A no-bake layered dessert of pretzel or cake-mix crust, sweetened cream cheese, and strawberry-Jello-with-frozen-strawberries.',
        'cuisine': 'American',
    }},
    'corpus-titled-orange-muffins': {'action': 'edit', 'patch': {
        'name': 'Orange muffins',
        'tags': ['breakfast', 'snack'],
        'notes': 'Tender muffins bright with orange juice and zest, sometimes folded with raisins or cranberries — finished with an orange glaze.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-cherry-coffee-cake': {'action': 'edit', 'patch': {
        'name': 'Cherry coffee cake',
        'tags': ['breakfast', 'dessert'],
        'notes': 'A tender butter cake topped with canned cherry pie filling and a buttery streusel — served with morning coffee.',
        'cuisine': 'American',
    }},
    'corpus-titled-crazy-chocolate-cake': {'action': 'edit', 'patch': {
        'name': 'Crazy chocolate cake (wacky)',
        'notes': 'A Depression-era one-bowl cocoa cake with no eggs, butter, or milk — leavened by vinegar reacting with baking soda; mixed right in the pan.',
        'cuisine': 'American',
    }},
    'corpus-titled-buttermilk-fudge': {'action': 'edit', 'patch': {
        'name': 'Buttermilk fudge',
        'tags': ['dessert'],
        'notes': 'Sugar, butter, buttermilk, and baking soda cooked to soft-ball and beaten until creamy — a tangy white fudge often with pecans.',
        'cuisine': 'Southern',
        'serving_grams': 40,
    }},
    'corpus-titled-mounds-cake': {'action': 'edit', 'patch': {
        'name': 'Mounds cake',
        'notes': 'A chocolate sheet cake topped warm with a coconut-and-marshmallow layer and a chocolate-almond ganache — Mounds candy bar flavors.',
        'cuisine': 'American',
    }},
    'corpus-titled-caramel-pecan-pie': {'action': 'edit', 'patch': {
        'name': 'Caramel pecan pie',
        'notes': 'A pecan pie with melted caramels stirred into the egg-sugar-corn-syrup custard — extra-chewy and toffee-sweet.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-braised-short-ribs': {'action': 'edit', 'patch': {
        'name': 'Braised short ribs',
        'notes': 'Beef short ribs seared, then slow-braised in red wine and broth with carrots, onion, garlic, and herbs until the meat falls off the bone.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-pumpkin-torte': {'action': 'edit', 'patch': {
        'name': 'Pumpkin torte',
        'tags': ['dessert'],
        'notes': 'A no-bake layered dessert of graham-cracker crust, sweetened cream cheese, spiced pumpkin pudding, and whipped topping.',
        'cuisine': 'American',
        'serving_grams': 140,
    }},
    'corpus-titled-hot-punch': {'action': 'edit', 'patch': {
        'name': 'Hot punch',
        'ingredient_categories': ['Juices', 'Tropical fruits', 'Berries', 'Citrus', 'Whole spices', 'Ground spices', 'Sugar & sweeteners'],
        'tags': ['snack'],
        'notes': 'Cranberry and pineapple juice simmered with cinnamon sticks, cloves, and citrus — a hot non-alcoholic holiday drink.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-pineapple-bake': {'action': 'edit', 'patch': {
        'name': 'Pineapple bake',
        'notes': 'Crushed pineapple folded with eggs, sugar, butter, and bread cubes, baked into a sweet-savory side served with ham — same as scalloped pineapple.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-squash-puppies': {'action': 'edit', 'patch': {
        'name': 'Squash puppies',
        'notes': 'Grated yellow squash mixed with cornmeal, eggs, and onion, dropped into oil and fried — hush-puppy variant with summer squash.',
        'cuisine': 'Southern',
        'serving_grams': 60,
    }},
    'corpus-titled-mexican-fudge': {'action': 'edit', 'patch': {
        'name': 'Mexican fudge',
        'tags': ['snack'],
        'notes': 'A savory bake of layered Monterey Jack and cheddar with chopped chiles, bound by an egg custard — baked and cut into squares like fudge.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-fluffy-pancakes': {'action': 'edit', 'patch': {
        'name': 'Fluffy pancakes',
        'notes': 'A baking-soda-leavened buttermilk batter cooked on a hot griddle with butter — extra fluffy from beaten egg whites folded in.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-grilled-salmon': {'action': 'edit', 'patch': {
        'name': 'Grilled salmon',
        'notes': 'A salmon fillet brushed with oil and lemon, seasoned with salt and herbs, and grilled hot until just flaking.',
    }},
    'corpus-titled-frozen-fruit-cups': {'action': 'edit', 'patch': {
        'name': 'Frozen fruit cups',
        'tags': ['snack', 'dessert'],
        'notes': 'Mixed fruit and juice frozen in muffin cups or paper cups — a chilled summer treat, half snack and half dessert.',
        'cuisine': 'American',
        'serving_grams': 130,
    }},
    'corpus-titled-southern-biscuits': {'action': 'edit', 'patch': {
        'name': 'Southern biscuits',
        'tags': ['breakfast', 'dinner'],
        'notes': 'A flaky quick bread of self-rising flour, cold butter or shortening, and buttermilk — patted, cut, and baked until tall.',
        'cuisine': 'Southern',
        'serving_grams': 55,
    }},
    'corpus-titled-chinese-cabbage-salad': {'action': 'edit', 'patch': {
        'name': 'Chinese cabbage salad',
        'notes': 'Shredded napa or green cabbage tossed with crushed ramen noodles, slivered almonds, sesame seeds, and a soy-sesame-sugar dressing.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-butter-pecan-cookies': {'action': 'edit', 'patch': {
        'name': 'Butter pecan cookies',
        'notes': 'Drop cookies of brown sugar, butter, and toasted pecans — chewy and toffee-toned, often glazed with brown-butter icing.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-chocolate-eclairs': {'action': 'edit', 'patch': {
        'name': 'Chocolate eclairs',
        'tags': ['dessert'],
        'notes': 'Pâte-à-choux fingers baked hollow, filled with vanilla pastry cream, and topped with a chocolate glaze.',
        'cuisine': 'French',
    }},
    'corpus-titled-hawaiian-meatballs': {'action': 'edit', 'patch': {
        'name': 'Hawaiian meatballs',
        'tags': ['snack', 'dinner'],
        'notes': 'Pan-fried meatballs simmered in a sweet-and-sour sauce of pineapple, vinegar, brown sugar, and soy — served over rice or as an appetizer.',
        'cuisine': 'American',
        'serving_grams': 100,
    }},
    'corpus-titled-spring-rolls': {'action': 'edit', 'patch': {
        'name': 'Spring rolls',
        'tags': ['snack', 'dinner'],
        'notes': 'Wheat or rice wrappers rolled around shredded vegetables (and sometimes pork or shrimp), deep-fried crisp or served fresh — Chinese/Vietnamese.',
        'cuisine': 'Chinese',
        'serving_grams': 100,
    }},
    'corpus-titled-rosemary-chicken': {'action': 'edit', 'patch': {
        'name': 'Rosemary chicken',
        'notes': 'Chicken pieces marinated in olive oil, lemon, garlic, and fresh rosemary, then roasted or grilled until the skin is crisp.',
        'cuisine': 'Italian',
    }},
    'corpus-titled-rhubarb-muffins': {'action': 'edit', 'patch': {
        'name': 'Rhubarb muffins',
        'tags': ['breakfast', 'snack'],
        'notes': 'Tender muffins folded with chopped rhubarb, brown sugar, and cinnamon — often topped with a sugar-cinnamon streusel.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-brown-sugar-brownies': {'action': 'edit', 'patch': {
        'name': 'Brown sugar brownies (blondies)',
        'notes': 'Brown-sugar-and-butter bars in the shape of brownies — chewy with toffee notes and chopped pecans.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-fish-batter': {'action': 'drop', 'reason': 'frying batter component, not a coherent meal'},
    'corpus-titled-skillet-cornbread': {'action': 'edit', 'patch': {
        'name': 'Skillet cornbread',
        'notes': 'A buttermilk cornmeal batter poured into a hot bacon-fat- or butter-greased cast-iron skillet — crisp-edged Southern cornbread.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-mock-pecan-pie': {'action': 'edit', 'patch': {
        'name': 'Mock pecan pie (oatmeal)',
        'notes': 'A pecan-pie-style filling using oats instead of pecans — eggs, sugar, butter, corn syrup, and oats baked in a single crust.',
        'cuisine': 'American',
    }},
    'corpus-titled-hash-browns-casserole': {'action': 'edit', 'patch': {
        'name': 'Hash browns casserole',
        'notes': 'Frozen hash browns baked with sour cream, cream of chicken soup, and shredded cheddar under a cornflake topping — funeral-potatoes-style.',
        'cuisine': 'American',
    }},
    'corpus-titled-peppermint-bark': {'action': 'edit', 'patch': {
        'name': 'Peppermint bark',
        'tags': ['dessert'],
        'notes': 'White chocolate melted and poured over a layer of dark chocolate, topped with crushed peppermint candy canes — Christmas candy.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-prime-rib': {'action': 'edit', 'patch': {
        'name': 'Prime rib',
        'notes': 'A whole standing rib roast of beef seasoned and slow-roasted at low heat, then seared at high heat for a crust — served with horseradish cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-naan': {'action': 'edit', 'patch': {
        'name': 'Naan',
        'notes': 'A leavened flatbread of flour, yogurt, and yeast, slapped against a hot tandoor (or skillet) and finished with butter — Indian.',
        'cuisine': 'Indian',
        'serving_grams': 80,
    }},
    'corpus-titled-harissa': {'action': 'drop', 'reason': 'spice paste / condiment, not a coherent meal'},
    'corpus-titled-fried-onion-rings': {'action': 'edit', 'patch': {
        'name': 'Fried onion rings',
        'tags': ['snack', 'dinner'],
        'notes': 'Sliced onions dipped in milk-and-egg batter, dredged in seasoned flour, and deep-fried until crisp and golden.',
        'cuisine': 'American',
        'serving_grams': 100,
    }},
    'corpus-titled-stuffed-chicken-breast': {'action': 'edit', 'patch': {
        'name': 'Stuffed chicken breast',
        'notes': 'Pounded chicken breasts rolled around herbed stuffing, spinach-and-feta, or ham-and-cheese, then breaded and baked or pan-fried.',
    }},
    'corpus-titled-hot-dish': {'action': 'edit', 'patch': {
        'name': 'Hot dish',
        'notes': 'A Midwestern catch-all casserole of ground beef, vegetables, and cream-of-soup gravy, often topped with tater tots or potato chips.',
        'cuisine': 'American',
    }},
    'corpus-titled-copper-penny-salad': {'action': 'edit', 'patch': {
        'name': 'Copper penny salad',
        'notes': 'Sliced cooked carrots ("pennies") tossed with bell pepper and onion in a tangy tomato-soup-and-vinegar marinade — chilled overnight.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-tuna-spread': {'action': 'edit', 'patch': {
        'name': 'Tuna spread',
        'tags': ['snack'],
        'notes': 'Canned tuna mixed with cream cheese, mayo, lemon, and seasonings — served chilled with crackers or as a sandwich filling.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-walnut-cake': {'action': 'edit', 'patch': {
        'name': 'Walnut cake',
        'notes': 'A buttery layer cake folded with finely chopped walnuts and often frosted with cream cheese or maple icing.',
        'cuisine': 'American',
    }},
    'corpus-titled-fruit-soup': {'action': 'edit', 'patch': {
        'name': 'Scandinavian fruit soup',
        'tags': ['dessert'],
        'notes': 'A sweet "soup" of mixed dried fruit (prunes, apricots, raisins) simmered with sugar, tapioca, cinnamon, and lemon — chilled or warm.',
        'cuisine': 'Scandinavian',
        'serving_grams': 240,
    }},
    'corpus-titled-lefse': {'action': 'edit', 'patch': {
        'name': 'Lefse',
        'notes': 'A thin Norwegian potato flatbread cooked on a hot griddle — rolled with butter and sugar (or jam) for a sweet snack.',
        'cuisine': 'Norwegian',
        'serving_grams': 80,
    }},
    'corpus-titled-old-fashioned-pound-cake': {'action': 'edit', 'patch': {
        'name': 'Old-fashioned pound cake',
        'notes': 'A classic pound cake of equal parts butter, sugar, eggs, and flour — dense, fine-crumbed, baked in a tube or loaf pan.',
        'cuisine': 'American',
    }},
    'corpus-titled-honey-wheat-bread': {'action': 'edit', 'patch': {
        'name': 'Honey wheat bread',
        'notes': 'A yeasted sandwich loaf of whole-wheat and bread flour sweetened with honey — soft crumb, nutty wheat-flour flavor.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-sausage-roll': {'action': 'edit', 'patch': {
        'name': 'Sausage roll',
        'tags': ['snack'],
        'notes': 'Seasoned sausage meat wrapped in puff pastry and baked into a sliceable log — a British pub snack.',
        'cuisine': 'British',
        'contains_add': ['pork'],
        'serving_grams': 80,
    }},
    'corpus-titled-sausage-pie': {'action': 'edit', 'patch': {
        'name': 'Sausage pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'Browned breakfast sausage layered with eggs, cheese, and peppers in a pastry shell, baked into a savory quiche-style pie.',
        'cuisine': 'American',
        'contains_add': ['pork'],
        'serving_grams': 200,
    }},
    'corpus-titled-ham-and-bean-soup': {'action': 'edit', 'patch': {
        'name': 'Ham and bean soup',
        'notes': 'Dried navy or great northern beans slow-simmered with a ham hock or cubed ham, onion, carrots, celery, and herbs in broth.',
        'cuisine': 'American',
    }},
    'corpus-titled-tortilla-rolls': {'action': 'edit', 'patch': {
        'name': 'Tortilla pinwheels (variant)',
        'tags': ['snack'],
        'notes': 'Flour tortillas spread with seasoned cream cheese, salsa, olives, and green chiles, rolled and sliced into pinwheels.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-marinated-broccoli': {'action': 'edit', 'patch': {
        'name': 'Marinated broccoli',
        'notes': 'Blanched broccoli florets tossed in an oil-and-vinegar marinade with garlic, herbs, and red pepper — chilled overnight.',
    }},
    'corpus-titled-banana-loaf': {'action': 'edit', 'patch': {
        'name': 'Banana loaf',
        'tags': ['breakfast', 'snack'],
        'notes': 'A moist quick bread sweetened by mashed ripe bananas, with butter, eggs, and flour — same as banana bread.',
        'cuisine': 'American',
    }},
    'corpus-titled-pea-casserole': {'action': 'edit', 'patch': {
        'name': 'Pea casserole',
        'notes': 'Sweet peas baked with mushrooms, water chestnuts, mushroom soup, and butter — sometimes with shrimp folded in.',
        'cuisine': 'American',
    }},
    'corpus-titled-nut-roll': {'action': 'edit', 'patch': {
        'name': 'Nut roll',
        'tags': ['dessert', 'breakfast'],
        'notes': 'A sweet yeasted dough rolled around a ground-walnut-and-sugar filling, baked into a log, sliced into spirals — Eastern European holiday bread.',
        'cuisine': 'Eastern European',
        'serving_grams': 80,
    }},
    'corpus-titled-sunday-chicken': {'action': 'edit', 'patch': {
        'name': 'Sunday chicken',
        'notes': 'Chicken pieces baked with rice and cream of mushroom soup in a covered pan — a hands-off Sunday-dinner casserole.',
        'cuisine': 'American',
    }},
    'corpus-titled-saucy-pork-chops': {'action': 'edit', 'patch': {
        'name': 'Saucy pork chops',
        'notes': 'Pork chops simmered in a sweet-tangy sauce of ketchup, brown sugar, and Worcestershire — served over rice or noodles.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-broccoli-bake': {'action': 'edit', 'patch': {
        'name': 'Chicken broccoli bake',
        'notes': 'Cooked chicken and broccoli baked in a mayo-lemon-cream-of-chicken-soup sauce under cheese and buttered breadcrumbs.',
        'cuisine': 'American',
    }},
    'corpus-titled-fresh-spinach-salad': {'action': 'edit', 'patch': {
        'name': 'Fresh spinach salad',
        'notes': 'Baby spinach with crisp bacon, sliced mushrooms, hard-boiled egg, and red onion in a sweet warm-bacon dressing.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-tuna-cakes': {'action': 'edit', 'patch': {
        'name': 'Tuna cakes',
        'tags': ['dinner', 'lunch'],
        'notes': 'Canned tuna bound with egg, breadcrumbs, lemon, and onion, formed into patties and pan-fried — a tuna-version of crab cakes.',
        'cuisine': 'American',
        'serving_grams': 170,
    }},
    'corpus-titled-self-filled-cupcakes': {'action': 'edit', 'patch': {
        'name': 'Self-filled cupcakes (black bottom)',
        'tags': ['dessert'],
        'notes': 'Chocolate cupcake batter topped with a spoonful of sweetened cream cheese and chocolate chips — bakes with a cheesecake-like cap.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-tang-pie': {'action': 'edit', 'patch': {
        'name': 'Tang pie',
        'notes': 'Frozen Tang concentrate (or orange juice) whipped into sweetened condensed milk and folded with whipped topping, set in a graham crust.',
        'cuisine': 'American',
    }},
    'corpus-titled-six-week-muffins': {'action': 'edit', 'patch': {
        'name': 'Six-week refrigerator muffins',
        'tags': ['breakfast'],
        'notes': 'A bran-and-buttermilk muffin batter mixed once and stored in the fridge up to six weeks — bake off in small batches as needed.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-jumbo-raisin-cookies': {'action': 'edit', 'patch': {
        'name': 'Jumbo raisin cookies',
        'notes': 'Large soft drop cookies of butter, brown sugar, oats, plumped raisins, and warm spices — chewy and homey.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-corn-bake': {'action': 'edit', 'patch': {
        'name': 'Corn bake',
        'notes': 'A spoon-bread-style bake of corn kernels, creamed corn, eggs, butter, and sour cream — sweet, custardy, almost pudding-like.',
        'cuisine': 'American',
    }},
    'corpus-titled-beef-nacho-casserole': {'action': 'edit', 'patch': {
        'name': 'Beef nacho casserole',
        'notes': 'Layered seasoned ground beef, salsa, beans, and cheese baked over tortilla chips — a Tex-Mex one-pan casserole.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-turkey-lasagna': {'action': 'edit', 'patch': {
        'name': 'Turkey lasagna',
        'notes': 'Layered lasagna noodles with ground turkey, ricotta, mozzarella, and marinara — a leaner alternative to beef lasagna.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-almond-chicken': {'action': 'edit', 'patch': {
        'name': 'Almond chicken',
        'notes': 'Diced chicken stir-fried with sliced almonds, water chestnuts, peppers, and onions in a soy-garlic sauce — Chinese-American.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-butter-pound-cake': {'action': 'edit', 'patch': {
        'name': 'Butter pound cake',
        'notes': 'A classic pound cake of equal parts butter, sugar, eggs, and flour — dense, fine-crumbed, and golden.',
        'cuisine': 'American',
    }},
    'corpus-titled-pecan-fingers': {'action': 'edit', 'patch': {
        'name': 'Pecan fingers (sandies)',
        'tags': ['dessert'],
        'notes': 'A butter-and-powdered-sugar shortbread folded with finely chopped pecans, shaped into fingers and rolled in powdered sugar.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-german-sweet-chocolate-cake': {'action': 'edit', 'patch': {
        'name': 'German sweet chocolate cake',
        'notes': 'A sweet-mild-chocolate layer cake filled and topped with a coconut-pecan caramel frosting — invented in Texas, named for German\'s baking chocolate.',
        'cuisine': 'American',
    }},
    'corpus-titled-gumdrop-cake': {'action': 'edit', 'patch': {
        'name': 'Gumdrop cake',
        'notes': 'A spiced fruit-and-nut cake with chopped gumdrops, candied fruit, and dates folded into the batter — fruitcake variant with a candy-store twist.',
        'cuisine': 'American',
    }},
    'corpus-titled-bread-and-butter-pudding': {'action': 'edit', 'patch': {
        'name': 'Bread and butter pudding',
        'notes': 'Slices of buttered bread layered in a dish with raisins, soaked in an egg-milk-cream custard, and baked until set — British comfort dessert.',
        'cuisine': 'British',
    }},
    'corpus-titled-dill-bread': {'action': 'edit', 'patch': {
        'name': 'Dill bread',
        'notes': 'A cottage-cheese yeast bread folded with fresh or dried dill and onion — chewy, savory, and tangy.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-braised-red-cabbage': {'action': 'edit', 'patch': {
        'name': 'Braised red cabbage',
        'notes': 'Shredded red cabbage slow-braised with apples, onions, vinegar, sugar, red wine, and warm spices — a German Rotkohl side.',
        'cuisine': 'German',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-taco-seasoning-mix': {'action': 'drop', 'reason': 'spice mix component, not a coherent meal'},
    'corpus-titled-strawberry-sorbet': {'action': 'edit', 'patch': {
        'name': 'Strawberry sorbet',
        'notes': 'Strawberries blended with sugar syrup and lemon juice, churned or frozen and stirred until smooth — dairy-free fruit ice.',
        'cuisine': 'European',
        'serving_grams': 100,
    }},
    'corpus-titled-creamy-chicken-casserole': {'action': 'edit', 'patch': {
        'name': 'Creamy chicken casserole',
        'notes': 'Cooked chicken and rice baked with sour cream, cream of chicken soup, mushrooms, and shredded cheese — a hands-off comfort casserole.',
        'cuisine': 'American',
    }},
    'corpus-titled-cinnamon-cookies': {'action': 'edit', 'patch': {
        'name': 'Cinnamon cookies',
        'notes': 'Butter sugar cookies heavily cinnamon-spiced, sometimes rolled in cinnamon-sugar before baking — same family as snickerdoodles.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-roast-leg-of-lamb': {'action': 'edit', 'patch': {
        'name': 'Roast leg of lamb',
        'notes': 'A whole leg of lamb studded with garlic and rosemary, roasted to medium-rare and served with mint jelly or pan jus — Easter centerpiece.',
        'cuisine': 'British',
    }},
    'corpus-titled-orange-fluff': {'action': 'edit', 'patch': {
        'name': 'Orange fluff',
        'tags': ['dessert'],
        'notes': 'Orange Jello set with mandarin oranges, crushed pineapple, and whipped topping — a Southern molded dessert salad.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-heavenly-salad': {'action': 'edit', 'patch': {
        'name': 'Heavenly fruit salad',
        'tags': ['dessert'],
        'notes': 'Mandarin oranges, pineapple, and grapes folded with sweetened cream cheese and whipped topping — a chilled Southern dessert salad.',
        'cuisine': 'American',
    }},
    'corpus-titled-cranberry-coffee-cake': {'action': 'edit', 'patch': {
        'name': 'Cranberry coffee cake',
        'tags': ['breakfast', 'dessert'],
        'notes': 'A sour-cream butter cake folded with cranberries and orange zest, topped with cinnamon-streusel or a powdered-sugar glaze.',
        'cuisine': 'American',
    }},
    'corpus-titled-burgers': {'action': 'edit', 'patch': {
        'name': 'Burgers',
        'notes': 'Ground beef patties seasoned with salt and pepper, seared or grilled, served on soft buns with lettuce, tomato, onion, pickle, and condiments.',
        'cuisine': 'American',
    }},
    'corpus-titled-glazed-fruit-salad': {'action': 'edit', 'patch': {
        'name': 'Glazed fruit salad',
        'notes': 'Mixed fresh fruit tossed with a cooked pudding-mix-and-pineapple-juice glaze — a chilled Southern picnic dessert salad.',
        'cuisine': 'American',
    }},
    'corpus-titled-coconut-shrimp': {'action': 'edit', 'patch': {
        'name': 'Coconut shrimp',
        'tags': ['snack', 'dinner'],
        'notes': 'Shrimp dipped in egg, coated in shredded coconut and breadcrumbs, and fried golden — served with a sweet-spicy dipping sauce.',
        'cuisine': 'American',
        'serving_grams': 170,
    }},
    'corpus-titled-date-squares': {'action': 'edit', 'patch': {
        'name': 'Date squares (matrimonial cake)',
        'tags': ['dessert'],
        'notes': 'Cooked dates sandwiched between two layers of an oat-and-brown-sugar crumble, baked and cut into squares — Canadian "matrimonial cake".',
        'cuisine': 'Canadian',
        'serving_grams': 60,
    }},
    'corpus-titled-white-bean-chicken-chili': {'action': 'edit', 'patch': {
        'name': 'White bean chicken chili',
        'notes': 'Shredded chicken simmered with white beans, green chiles, cumin, and broth, finished with sour cream — Tex-Mex white chili.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-tuna-melt': {'action': 'edit', 'patch': {
        'name': 'Tuna melt',
        'tags': ['lunch'],
        'notes': 'Tuna salad piled on toasted bread, topped with cheese, and broiled or griddled until the cheese melts — a diner classic.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-pickled-red-onions': {'action': 'drop', 'reason': 'pickled condiment, not a coherent meal'},
    'corpus-titled-dulce-de-leche': {'action': 'drop', 'reason': 'sweet milk caramel / topping, not a coherent meal'},
    'corpus-titled-pasta-puttanesca': {'action': 'edit', 'patch': {
        'name': 'Pasta puttanesca',
        'notes': 'Spaghetti tossed with a punchy sauce of tomatoes, olives, capers, anchovies, garlic, and chili flakes — a Neapolitan classic.',
        'cuisine': 'Italian',
    }},
    'corpus-titled-round-2-recipe': {'action': 'drop', 'reason': 'TV-series segment name (Sandra Lee), not a specific meal'},
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

    print('corpus-titled batch-17 audit applied (FINAL — entries 2401-end by frequency).')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
