"""Corpus-titled meals audit — batch 11 (entries 1501-1650 by frequency, 79 -> 73)."""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

DECISIONS: dict[str, dict] = {
    'corpus-titled-linguine-salad': {'action': 'edit', 'patch': {
        'name': 'Linguine salad',
        'notes': 'Cooked linguine tossed with chopped peppers, onions, olives, and a Salad Supreme-seasoned Italian dressing — chilled overnight.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-mostaccioli': {'action': 'edit', 'patch': {
        'name': 'Mostaccioli',
        'notes': 'Penne-style tubes baked with seasoned ground beef in marinara, layered with ricotta and topped with mozzarella — a Midwestern Italian-American casserole.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-fig-cake': {'action': 'edit', 'patch': {
        'name': 'Fig cake',
        'notes': 'A spiced oil-based cake folded with fig preserves and pecans — moist, jammy, with a brown-sugar glaze.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-s-potato-salad': {'action': 'edit', 'patch': {
        'name': 'Southern potato salad',
        'notes': 'Boiled potatoes tossed with mayo, mustard, chopped egg, sweet pickle relish, and onion — the classic Southern picnic dish.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-corn-dip': {'action': 'edit', 'patch': {
        'name': 'Corn dip',
        'tags': ['snack'],
        'notes': 'Canned corn (often shoepeg) mixed with sour cream, cheese, mayo, and diced jalapeños — served chilled with tortilla chips.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-sugar-free-apple-pie': {'action': 'edit', 'patch': {
        'name': 'Sugar-free apple pie',
        'notes': 'A double-crust apple pie sweetened by frozen apple-juice concentrate in place of granulated sugar — a diabetic-friendly variant.',
        'cuisine': 'American',
    }},
    'corpus-titled-curry-chicken': {'action': 'edit', 'patch': {
        'name': 'Curry chicken',
        'notes': 'Chicken pieces simmered in a curry-spiced sauce with peppers and onions — served over rice with chutney.',
    }},
    'corpus-titled-sour-cream-potato-salad': {'action': 'edit', 'patch': {
        'name': 'Sour cream potato salad',
        'notes': 'Boiled potatoes tossed with sour cream and mayo, hard-boiled eggs, scallions, and bacon — tangier than mayo-only potato salad.',
        'cuisine': 'American',
    }},
    'corpus-titled-broccoli-and-chicken-casserole': {'action': 'edit', 'patch': {
        'name': 'Broccoli and chicken casserole',
        'notes': 'Cooked chicken and broccoli baked in a mayo, lemon, and cream-of-chicken-soup sauce under buttered breadcrumbs and cheese.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-pasta-salad': {'action': 'edit', 'patch': {
        'name': 'Chicken pasta salad',
        'notes': 'Cooked rotini or shells tossed with diced chicken, vegetables, cheese, and Italian or ranch dressing — chilled.',
        'cuisine': 'American',
    }},
    'corpus-titled-orange-cookies': {'action': 'edit', 'patch': {
        'name': 'Orange cookies',
        'notes': 'Soft drop cookies of orange juice, zest, butter, and sugar — glazed with a tangy orange-sugar icing while still warm.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-tortilla-pinwheels': {'action': 'edit', 'patch': {
        'name': 'Tortilla pinwheels (variant)',
        'tags': ['snack'],
        'notes': 'Flour tortillas spread with seasoned cream cheese, salsa, olives, and green chiles, rolled and sliced into pinwheels — a Tex-Mex appetizer.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-avocado-salad': {'action': 'edit', 'patch': {
        'name': 'Avocado salad',
        'notes': 'Diced avocado tossed with tomato, onion, peppers, lime, and cilantro — a chunky guacamole-adjacent salad.',
        'cuisine': 'Mexican',
    }},
    'corpus-titled-bread-sticks': {'action': 'edit', 'patch': {
        'name': 'Breadsticks',
        'tags': ['snack', 'dinner'],
        'notes': 'A buttery yeasted dough cut into long sticks, brushed with garlic butter and Parmesan, and baked until golden — Olive Garden style.',
        'cuisine': 'Italian-American',
        'serving_grams': 60,
    }},
    'corpus-titled-strawberry-preserves': {'action': 'drop', 'reason': 'jam / canning preserve, not a coherent meal'},
    'corpus-titled-apricot-bread': {'action': 'edit', 'patch': {
        'name': 'Apricot bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A sweet quick bread folded with chopped dried apricots, soaked first in orange juice, and finished with a citrus glaze.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-crab-stuffed-mushrooms': {'action': 'edit', 'patch': {
        'name': 'Crab-stuffed mushrooms',
        'tags': ['snack'],
        'notes': 'Mushroom caps filled with a mixture of lump crab, cream cheese, breadcrumbs, lemon, and Old Bay, baked until golden.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-lamb-stew': {'action': 'edit', 'patch': {
        'name': 'Lamb stew',
        'notes': 'Cubed lamb shoulder slow-braised with potatoes, carrots, onions, and herbs in seasoned broth — Mediterranean comfort.',
    }},
    'corpus-titled-rumaki': {'action': 'edit', 'patch': {
        'name': 'Rumaki',
        'tags': ['snack'],
        'notes': 'Chicken livers and water chestnuts wrapped in bacon, marinated in soy and brown sugar, then broiled — a tiki-bar appetizer.',
        'cuisine': 'American',
        'contains_add': ['pork'],
        'serving_grams': 60,
    }},
    'corpus-titled-zucchini-bars': {'action': 'edit', 'patch': {
        'name': 'Zucchini bars',
        'tags': ['dessert'],
        'notes': 'A spiced sheet-pan version of zucchini cake folded with grated zucchini and chopped pecans, topped with cream cheese frosting.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-cinnamon-coffee-cake': {'action': 'edit', 'patch': {
        'name': 'Cinnamon coffee cake',
        'tags': ['breakfast', 'dessert'],
        'notes': 'A tender butter or sour-cream cake swirled with a cinnamon-sugar-pecan streusel — served with morning coffee.',
        'cuisine': 'American',
    }},
    'corpus-titled-noodle-kugel': {'action': 'edit', 'patch': {
        'name': 'Noodle kugel (variant)',
        'notes': 'Egg noodles baked in a sweet custard of cottage cheese, sour cream, eggs, butter, sugar, and raisins — the Ashkenazi Jewish noodle pudding.',
        'cuisine': 'Jewish',
    }},
    'corpus-titled-baked-eggplant': {'action': 'edit', 'patch': {
        'name': 'Baked eggplant',
        'notes': 'Sliced eggplant dipped in egg, breaded, layered with tomato and Parmesan, and baked — a lighter eggplant parm.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-vegetable-stock': {'action': 'drop', 'reason': 'cooking component (stock), not a coherent meal'},
    'corpus-titled-cranberry-tea': {'action': 'edit', 'patch': {
        'name': 'Cranberry tea',
        'ingredient_categories': ['Juices', 'Coffee & tea', 'Citrus', 'Sugar & sweeteners', 'Whole spices', 'Ground spices'],
        'tags': ['snack'],
        'notes': 'Cranberry juice simmered with cinnamon sticks, cloves, lemon, and orange — a hot non-alcoholic holiday drink.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-pea-soup': {'action': 'edit', 'patch': {
        'name': 'Split pea soup (variant)',
        'notes': 'Dried split peas slow-simmered with a ham hock or bone, carrots, celery, and onion until thick and creamy.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-apple-brown-betty': {'action': 'edit', 'patch': {
        'name': 'Apple brown Betty',
        'tags': ['dessert'],
        'notes': 'Spiced sliced apples layered with buttered breadcrumbs and brown sugar, baked until the topping browns — a colonial American dessert.',
        'cuisine': 'American',
        'serving_grams': 140,
    }},
    'corpus-titled-oven-caramel-corn': {'action': 'edit', 'patch': {
        'name': 'Oven caramel corn',
        'tags': ['snack', 'dessert'],
        'notes': 'Popped corn tossed with a butter-brown-sugar-corn-syrup caramel and slow-baked until crisp and shiny.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-ribbon-salad': {'action': 'edit', 'patch': {
        'name': 'Ribbon Jello salad',
        'tags': ['dessert'],
        'notes': 'Layered colored Jello set with sweetened cream-and-cream-cheese layers between — chilled in a glass dish to show the colored ribbons.',
        'cuisine': 'American',
    }},
    'corpus-titled-peaches-and-cream-pie': {'action': 'edit', 'patch': {
        'name': 'Peaches and cream pie',
        'notes': 'Sliced peaches baked in a pie pan with a butter-flour-egg cake-like base, finished with a cream-cheese-and-sugar topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-sock-it-to-me-cake': {'action': 'edit', 'patch': {
        'name': 'Sock-it-to-me cake',
        'notes': 'A yellow Bundt cake from cake mix and sour cream with a cinnamon-pecan streusel swirled through the middle — Duncan Hines original.',
        'cuisine': 'American',
    }},
    'corpus-titled-no-fail-pie-crust': {'action': 'drop', 'reason': 'pie-crust component, not a coherent meal'},
    'corpus-titled-salad-dressing-cake': {'action': 'edit', 'patch': {
        'name': 'Salad dressing (mayonnaise) cake',
        'notes': 'A Depression-era chocolate cake using salad dressing or mayonnaise in place of butter and eggs — the dressing carries the fat and emulsion.',
        'cuisine': 'American',
    }},
    'corpus-titled-cheese-garlic-biscuits': {'action': 'edit', 'patch': {
        'name': 'Cheese garlic biscuits',
        'tags': ['dinner', 'lunch'],
        'notes': 'A Bisquick drop biscuit mixed with sharp cheddar, brushed after baking with garlic-parsley butter — Red Lobster style.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-oriental-chicken': {'action': 'edit', 'patch': {
        'name': 'Oriental chicken',
        'notes': 'Chicken pieces stir-fried or baked with a sweet-soy-and-ginger sauce, peppers, and onions — served over rice; a vintage Chinese-American name.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-zucchini-pickles': {'action': 'drop', 'reason': 'pickled condiment, not a coherent meal'},
    'corpus-titled-wilted-lettuce': {'action': 'edit', 'patch': {
        'name': 'Wilted lettuce salad',
        'notes': 'Leaf lettuce and scallions dressed with a hot bacon-fat-and-vinegar dressing — wilts the greens slightly; an Appalachian classic.',
        'cuisine': 'Appalachian',
        'contains_add': ['pork'],
    }},
    'corpus-titled-chip-dip': {'action': 'edit', 'patch': {
        'name': 'Chip dip',
        'tags': ['snack'],
        'notes': 'A generic name for a chilled sour-cream-and-mayonnaise dip seasoned with herbs and onion — served with potato chips.',
        'cuisine': 'American',
    }},
    'corpus-titled-cherry-crisp': {'action': 'edit', 'patch': {
        'name': 'Cherry crisp',
        'tags': ['dessert'],
        'notes': 'Sweetened cherries baked under a crunchy oat-and-butter streusel — served warm with ice cream.',
        'cuisine': 'American',
    }},
    'corpus-titled-kidney-bean-salad': {'action': 'edit', 'patch': {
        'name': 'Kidney bean salad',
        'notes': 'Drained kidney beans tossed with chopped eggs, sweet pickles, onion, celery, and a mayo-vinegar dressing — chilled.',
        'cuisine': 'American',
    }},
    'corpus-titled-mexican-dish': {'action': 'edit', 'patch': {
        'name': 'Mexican dish (casserole)',
        'notes': 'Layered seasoned ground beef, salsa, beans, cheese, and tortilla chips baked together — a generic Tex-Mex casserole.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-tuna-macaroni-salad': {'action': 'edit', 'patch': {
        'name': 'Tuna macaroni salad',
        'notes': 'Cooked elbow macaroni tossed with canned tuna, sweet pickle relish, celery, onion, and mayo — chilled as a picnic salad.',
        'cuisine': 'American',
    }},
    'corpus-titled-sweet-rolls': {'action': 'edit', 'patch': {
        'name': 'Sweet rolls',
        'tags': ['breakfast', 'dessert'],
        'notes': 'Soft enriched yeasted dough rolled around butter, sugar, and cinnamon, sliced into spirals and baked — drizzled with a powdered-sugar glaze.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-barbecued-beef': {'action': 'edit', 'patch': {
        'name': 'Barbecued beef (sandwich)',
        'notes': 'Slow-cooked shredded beef (chuck or brisket) tossed in a sweet-tangy barbecue sauce — served on soft buns with coleslaw.',
        'cuisine': 'American',
    }},
    'corpus-titled-chili-soup': {'action': 'edit', 'patch': {
        'name': 'Chili soup',
        'notes': 'A thinner, soupier version of chili — ground beef simmered with tomatoes, beans, peppers, and chili powder in more broth.',
        'cuisine': 'American',
    }},
    'corpus-titled-german-pancakes': {'action': 'edit', 'patch': {
        'name': 'German pancakes (Dutch baby)',
        'notes': 'A thin batter of eggs, milk, flour, and salt poured into a hot buttered skillet and baked until it puffs at the edges — served with lemon and powdered sugar.',
        'cuisine': 'German',
        'serving_grams': 200,
    }},
    'corpus-titled-sugared-pecans': {'action': 'edit', 'patch': {
        'name': 'Sugared pecans',
        'tags': ['snack'],
        'notes': 'Pecan halves tossed in an egg-white-and-sugar slurry with cinnamon and salt, baked slowly until crisp.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-curried-chicken': {'action': 'edit', 'patch': {
        'name': 'Curried chicken',
        'notes': 'Chicken pieces simmered in a curry-spiced cream sauce with peppers, onions, and a touch of fruit — served over rice with chutney.',
    }},
    'corpus-titled-balsamic-vinaigrette': {'action': 'drop', 'reason': 'dressing component, not a coherent meal'},
    'corpus-titled-fruit-bars': {'action': 'edit', 'patch': {
        'name': 'Fruit bars',
        'tags': ['dessert'],
        'notes': 'A short butter-flour crust topped with dried-or-candied-fruit-and-nut filling, baked and cut into bars — fruitcake-bar family.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-rocky-road-fudge': {'action': 'edit', 'patch': {
        'name': 'Rocky road fudge',
        'notes': 'A microwave or stovetop chocolate fudge folded with mini marshmallows and chopped peanuts or almonds.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-japanese-fruit-cake': {'action': 'edit', 'patch': {
        'name': 'Japanese fruit cake (Southern)',
        'notes': 'A Southern layer cake with spiced raisin-and-pecan layers alternating with white-coconut layers, filled with lemon-coconut filling — American despite the name.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-cherry-coke-salad': {'action': 'edit', 'patch': {
        'name': 'Cherry Coke salad',
        'tags': ['dessert'],
        'notes': 'Cherry Jello dissolved in hot Coca-Cola, set with crushed pineapple, cherries, and chopped pecans — a Southern molded dessert.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-drop-biscuits': {'action': 'edit', 'patch': {
        'name': 'Drop biscuits',
        'tags': ['breakfast', 'dinner'],
        'notes': 'A quick biscuit dough dropped from a spoon (no rolling and cutting) — tender, slightly craggy, and ready in under 20 minutes.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-coke-salad': {'action': 'edit', 'patch': {
        'name': 'Coca-Cola salad',
        'tags': ['dessert'],
        'notes': 'Cherry Jello dissolved in Coca-Cola, set with crushed pineapple, cherries, and pecans, layered with sweetened cream cheese — Southern dessert.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-succotash': {'action': 'edit', 'patch': {
        'name': 'Succotash',
        'notes': 'Lima beans (or butter beans) and sweet corn simmered with onion, peppers, butter, and a touch of cream — a Native-American-rooted Southern side.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-blueberry-pancakes': {'action': 'edit', 'patch': {
        'name': 'Blueberry pancakes',
        'notes': 'Buttermilk pancake batter folded with fresh blueberries — griddled until golden and served with maple syrup.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-turkey-salad': {'action': 'edit', 'patch': {
        'name': 'Turkey salad',
        'notes': 'Diced cooked turkey bound with mayo, celery, grapes, and nuts — a Thanksgiving leftovers chicken-salad cousin.',
        'cuisine': 'American',
    }},
    'corpus-titled-cinnamon-bread': {'action': 'edit', 'patch': {
        'name': 'Cinnamon swirl bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A soft enriched yeasted loaf with a cinnamon-sugar swirl rolled into the dough — sliceable for cinnamon toast.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-zucchini-patties': {'action': 'edit', 'patch': {
        'name': 'Zucchini patties',
        'notes': 'Grated zucchini mixed with eggs, flour, Parmesan, and seasonings, dropped into oil and pan-fried into golden patties.',
        'cuisine': 'American',
    }},
    'corpus-titled-bonbons': {'action': 'edit', 'patch': {
        'name': 'Coconut bonbons',
        'tags': ['dessert'],
        'notes': 'Sweetened coconut mixed with butter, sweetened condensed milk, and pecans, rolled into balls and dipped in melted chocolate — Martha-Washington-style.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-fresh-fruit-salad': {'action': 'edit', 'patch': {
        'name': 'Fresh fruit salad',
        'notes': 'Diced fresh fruit (pineapple, strawberries, grapes, oranges) lightly tossed in a citrus-honey syrup — a clean, juice-bound fruit salad.',
    }},
    'corpus-titled-dream-bars': {'action': 'edit', 'patch': {
        'name': 'Dream bars',
        'tags': ['dessert'],
        'notes': 'A butter-shortbread crust topped with a coconut, brown-sugar, and pecan custard, baked into bars — same family as magic cookie / hello dollies bars.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-hash-browns': {'action': 'edit', 'patch': {
        'name': 'Hash browns',
        'notes': 'Grated or diced potato fried hot in butter or oil until crisp and golden — a diner breakfast side.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-cream-cheese-dip': {'action': 'edit', 'patch': {
        'name': 'Cream cheese dip',
        'tags': ['snack'],
        'notes': 'Cream cheese whipped smooth with sour cream, peppers, onion, and seasonings — served chilled with crackers or chips.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-potato-wedges': {'action': 'edit', 'patch': {
        'name': 'Potato wedges',
        'tags': ['snack', 'dinner'],
        'notes': 'Russet potatoes cut into wedges, tossed in oil and seasonings, and roasted hot until crisp outside and tender inside.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-nacho-cheese-dip': {'action': 'edit', 'patch': {
        'name': 'Nacho cheese dip',
        'tags': ['snack'],
        'notes': 'Velveeta-style processed cheese melted with Rotel tomatoes and chiles, sometimes with seasoned ground beef — served warm with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-strawberry-cream-pie': {'action': 'edit', 'patch': {
        'name': 'Strawberry cream pie',
        'notes': 'A graham crust filled with sweetened cream cheese, sliced strawberries, and a strawberry-Jello-and-gelatin glaze — chilled until set.',
        'cuisine': 'American',
    }},
    'corpus-titled-grilled-chicken': {'action': 'edit', 'patch': {
        'name': 'Grilled chicken',
        'notes': 'Chicken pieces marinated in oil, lemon, and herbs, then grilled hot over coals or a gas grill until charred and juicy.',
    }},
    'corpus-titled-cherry-winks': {'action': 'edit', 'patch': {
        'name': 'Cherry winks',
        'tags': ['dessert'],
        'notes': 'Drop cookies of butter, sugar, eggs, and chopped maraschino cherries and pecans, rolled in crushed cornflakes and topped with a cherry before baking.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-zucchini-parmesan': {'action': 'edit', 'patch': {
        'name': 'Zucchini parmesan',
        'notes': 'Sliced zucchini breaded with Parmesan, baked or fried, and layered with marinara and mozzarella — eggplant-parm style with zucchini.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-zucchini-appetizer': {'action': 'edit', 'patch': {
        'name': 'Zucchini appetizer squares',
        'tags': ['snack'],
        'notes': 'Grated zucchini baked with eggs, flour, Parmesan, and herbs in a sheet pan, then cut into bite-size squares.',
        'cuisine': 'Italian-American',
        'serving_grams': 60,
    }},
    'corpus-titled-tuna-patties': {'action': 'edit', 'patch': {
        'name': 'Tuna patties',
        'notes': 'Canned tuna bound with egg, breadcrumbs, onion, and seasonings, formed into patties and pan-fried until golden.',
        'cuisine': 'American',
    }},
    'corpus-titled-oyster-dressing': {'action': 'edit', 'patch': {
        'name': 'Oyster dressing',
        'notes': 'Cornbread or bread cubes mixed with sautéed onions, celery, oysters, and broth, baked into a Thanksgiving dressing — Southern coastal tradition.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-corn-flake-cookies': {'action': 'edit', 'patch': {
        'name': 'Cornflake cookies (variant)',
        'notes': 'Drop cookies with cornflakes, coconut, and pecans folded into a peanut-butter-and-sugar dough — chewy with crunch.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-turkey-meat-loaf': {'action': 'edit', 'patch': {
        'name': 'Turkey meatloaf (variant)',
        'notes': 'Ground turkey bound with breadcrumbs, eggs, herbs, and seasonings, baked in a loaf with a ketchup glaze — a leaner meatloaf.',
        'cuisine': 'American',
    }},
    'corpus-titled-mediterranean-chicken': {'action': 'edit', 'patch': {
        'name': 'Mediterranean chicken',
        'notes': 'Chicken pieces baked with tomatoes, olives, capers, garlic, and oregano in olive oil and lemon — a one-pan Mediterranean bake.',
        'cuisine': 'Mediterranean',
    }},
    'corpus-titled-asian-chicken-salad': {'action': 'edit', 'patch': {
        'name': 'Asian chicken salad',
        'notes': 'Shredded cabbage and lettuce tossed with chicken, crispy ramen or wonton strips, almonds, sesame seeds, and a soy-and-sesame-oil dressing.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-pinto-beans': {'action': 'edit', 'patch': {
        'name': 'Pinto beans',
        'notes': 'Dried pinto beans slow-simmered with bacon or ham hock, onion, garlic, and chiles — a Southern and Southwestern staple.',
        'cuisine': 'Southern',
        'contains_add': ['pork'],
    }},
    'corpus-titled-oyster-cracker-snack': {'action': 'edit', 'patch': {
        'name': 'Seasoned oyster cracker snack',
        'ingredient_categories': ['Baked snacks & pastries', 'Oils', 'Fresh herbs', 'Ground spices', 'Dressings & dips'],
        'tags': ['snack'],
        'notes': 'Oyster crackers tossed with oil, dry ranch mix, dill, garlic, and lemon pepper, baked until aromatic — a seasoned party snack.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-green-bean-bundles': {'action': 'edit', 'patch': {
        'name': 'Green bean bundles',
        'notes': 'Groups of green beans wrapped in bacon strips, brushed with a brown-sugar-butter glaze, and baked until the bacon crisps.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-caramel-dip': {'action': 'edit', 'patch': {
        'name': 'Caramel apple dip',
        'tags': ['snack', 'dessert'],
        'notes': 'Sweetened condensed milk and brown sugar whipped with cream cheese and vanilla — served with sliced apples for dipping.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-chocolate-balls': {'action': 'edit', 'patch': {
        'name': 'Chocolate balls',
        'tags': ['dessert'],
        'notes': 'A no-bake confection of crushed graham crackers or vanilla wafers mixed with peanut butter, coconut, and pecans, rolled into balls and dipped in chocolate.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-pasta-fagioli': {'action': 'edit', 'patch': {
        'name': 'Pasta e fagioli (variant)',
        'notes': 'A rustic Italian soup of small pasta and beans in a tomato-and-broth base with garlic, herbs, and a Parmesan rind.',
        'cuisine': 'Italian',
    }},
    'corpus-titled-broccoli-puff': {'action': 'edit', 'patch': {
        'name': 'Broccoli puff',
        'notes': 'Frozen broccoli baked with eggs, milk, mayo, and cream of mushroom soup under a buttered crumb-and-cheese topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-gumdrop-cookies': {'action': 'edit', 'patch': {
        'name': 'Gumdrop cookies',
        'notes': 'Drop cookies with chopped gumdrops folded into a butter-and-oat batter — chewy and colorful.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-tortilla-casserole': {'action': 'edit', 'patch': {
        'name': 'Tortilla casserole',
        'notes': 'Layered tortillas with seasoned beef or chicken, enchilada sauce, and cheese — a Tex-Mex stacked enchilada bake.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-pork-fried-rice': {'action': 'edit', 'patch': {
        'name': 'Pork fried rice',
        'notes': 'Day-old cold rice stir-fried with diced pork, eggs, peas, scallions, and soy sauce — Chinese-American takeout style.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-sour-cream-corn-bread': {'action': 'edit', 'patch': {
        'name': 'Sour cream cornbread (variant)',
        'notes': 'A skillet cornbread enriched with sour cream and creamed corn — moist, slightly sweet, with a tender crumb.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-oat-bran-muffins': {'action': 'edit', 'patch': {
        'name': 'Oat bran muffins',
        'tags': ['breakfast'],
        'notes': 'A high-fiber muffin of oat bran, raisins, applesauce, and milk — slightly sweet and moist.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-creamed-chicken': {'action': 'edit', 'patch': {
        'name': 'Creamed chicken',
        'notes': 'Diced cooked chicken in a milk-and-butter bechamel with onions and peppers — served over biscuits, toast, or noodles.',
        'cuisine': 'American',
    }},
    'corpus-titled-scotch-shortbread': {'action': 'edit', 'patch': {
        'name': 'Scotch shortbread (variant)',
        'tags': ['dessert'],
        'notes': 'A traditional Scottish biscuit of butter, sugar, and flour — pressed flat, pricked, baked low, and cut into wedges or fingers.',
        'cuisine': 'British',
        'serving_grams': 30,
    }},
    'corpus-titled-dog-biscuits': {'action': 'drop', 'reason': 'pet food, not a coherent meal for humans'},
    'corpus-titled-salmon-burgers': {'action': 'edit', 'patch': {
        'name': 'Salmon burgers',
        'notes': 'Fresh or canned salmon bound with egg, breadcrumbs, lemon, dill, and onion, formed into patties and pan-fried — served on buns with tartar sauce.',
        'cuisine': 'American',
    }},
    'corpus-titled-banana-split': {'action': 'edit', 'patch': {
        'name': 'Banana split sundae',
        'tags': ['dessert'],
        'notes': 'A split banana lengthwise served with three scoops of ice cream, hot fudge, strawberry, pineapple, whipped cream, nuts, and cherries — the ice-cream-parlor classic.',
        'cuisine': 'American',
        'serving_grams': 320,
    }},
    'corpus-titled-beef-tips': {'action': 'edit', 'patch': {
        'name': 'Beef tips and gravy',
        'notes': 'Cubed sirloin browned and slow-simmered with mushrooms and onions in a brown gravy — served over rice or egg noodles.',
        'cuisine': 'American',
    }},
    'corpus-titled-butter-cake': {'action': 'edit', 'patch': {
        'name': 'Butter cake',
        'notes': 'A classic American layer cake with a high butter ratio, made with creamed butter, sugar, eggs, and milk — moist and yellow-tinted.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-peanut-butter-balls': {'action': 'edit', 'patch': {
        'name': 'Chocolate peanut butter balls (buckeyes)',
        'tags': ['dessert', 'snack'],
        'notes': 'Peanut butter and powdered sugar balls partially dipped in melted chocolate — same as buckeyes.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-cottage-pie': {'action': 'edit', 'patch': {
        'name': 'Cottage pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'Ground beef simmered with onions, carrots, peas, and gravy, topped with mashed potatoes and baked — British shepherd-pie-with-beef.',
        'cuisine': 'British',
        'serving_grams': 320,
    }},
    'corpus-titled-gingerbread-men': {'action': 'edit', 'patch': {
        'name': 'Gingerbread men',
        'tags': ['dessert'],
        'notes': 'Rolled spiced cookies of butter, brown sugar, and molasses cut into human shapes, baked crisp, and decorated with royal icing.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-seven-layer-bars': {'action': 'edit', 'patch': {
        'name': 'Seven layer bars',
        'tags': ['dessert'],
        'notes': 'Graham crust topped with chocolate chips, butterscotch chips, coconut, and pecans, drizzled with sweetened condensed milk and baked — same as Hello Dollies / Magic Cookie Bars.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-breakfast-quiche': {'action': 'edit', 'patch': {
        'name': 'Breakfast quiche',
        'notes': 'A pastry shell filled with eggs, cream, breakfast sausage or bacon, and cheese, baked until just set — a brunch staple.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-challah': {'action': 'edit', 'patch': {
        'name': 'Challah',
        'notes': 'A braided egg-enriched yeasted bread of flour, eggs, oil, sugar, and yeast — the Jewish Sabbath and holiday loaf.',
        'cuisine': 'Jewish',
        'serving_grams': 55,
    }},
    'corpus-titled-bread-baking': {'action': 'drop', 'reason': 'generic "bread baking" placeholder, not a coherent meal'},
    'corpus-titled-cheese-ring': {'action': 'edit', 'patch': {
        'name': 'Cheese ring (Atlanta)',
        'tags': ['snack'],
        'notes': 'Shredded sharp cheddar mixed with mayo, onion, garlic, and pecans, molded into a ring and filled with strawberry preserves — Southern cocktail-party appetizer.',
        'cuisine': 'Southern',
        'serving_grams': 60,
    }},
    'corpus-titled-deer-jerky': {'action': 'edit', 'patch': {
        'name': 'Deer (venison) jerky',
        'notes': 'Strips of venison marinated in soy, Worcestershire, brown sugar, and spices, then slow-dried in a low oven or dehydrator until chewy.',
        'cuisine': 'American',
    }},
    'corpus-titled-honey-chicken': {'action': 'edit', 'patch': {
        'name': 'Honey chicken',
        'notes': 'Chicken pieces glazed with a sauce of honey, butter, mustard, and curry or paprika, baked until caramelized and sticky.',
        'cuisine': 'American',
    }},
    'corpus-titled-strawberry-butter': {'action': 'edit', 'patch': {
        'name': 'Strawberry butter',
        'tags': ['condiment'],
        'notes': 'Softened butter whipped with crushed fresh or frozen strawberries and powdered sugar — a sweet spread for scones, biscuits, and toast.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-sweet-and-sour-pork-chops': {'action': 'edit', 'patch': {
        'name': 'Sweet and sour pork chops',
        'notes': 'Pork chops browned and braised in a sweet-tangy sauce of pineapple juice, vinegar, brown sugar, soy, and ketchup — served over rice.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-pork-tenderloin': {'action': 'edit', 'patch': {
        'name': 'Pork tenderloin',
        'notes': 'A whole pork tenderloin rubbed with garlic, herbs, and spices, seared and roasted, or grilled — sliced into medallions.',
        'cuisine': 'American',
    }},
    'corpus-titled-skillet-cabbage': {'action': 'edit', 'patch': {
        'name': 'Skillet cabbage',
        'notes': 'Shredded cabbage sautéed in bacon fat with onions, peppers, and a touch of sugar — a Southern stovetop side.',
        'cuisine': 'Southern',
        'contains_add': ['pork'],
    }},
    'corpus-titled-chicken-and-stuffing-casserole': {'action': 'edit', 'patch': {
        'name': 'Chicken and stuffing casserole',
        'notes': 'Cooked chicken baked under herbed stuffing mix soaked in chicken broth and cream of mushroom soup — Thanksgiving-leftovers style.',
        'cuisine': 'American',
    }},
    'corpus-titled-cream-of-asparagus-soup': {'action': 'edit', 'patch': {
        'name': 'Cream of asparagus soup',
        'notes': 'Asparagus simmered in chicken broth with onion, blended smooth, and finished with cream and butter.',
    }},
    'corpus-titled-baked-salmon': {'action': 'edit', 'patch': {
        'name': 'Baked salmon',
        'notes': 'A salmon fillet baked with butter, lemon, herbs, and seasonings until the flesh just flakes — simple and lean.',
    }},
    'corpus-titled-peanut-butter-kisses': {'action': 'edit', 'patch': {
        'name': 'Peanut butter kisses',
        'tags': ['dessert'],
        'notes': 'Peanut butter cookies rolled in sugar and pressed with a Hershey\'s Kiss right out of the oven — same as peanut butter blossoms.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-caponata': {'action': 'edit', 'patch': {
        'name': 'Caponata',
        'tags': ['snack', 'condiment'],
        'notes': 'Diced eggplant cooked with tomato, onion, celery, capers, olives, and a sweet-and-sour vinegar-and-sugar glaze — a Sicilian relish.',
        'cuisine': 'Italian',
        'serving_grams': 80,
    }},
    'corpus-titled-creamy-broccoli-soup': {'action': 'edit', 'patch': {
        'name': 'Creamy broccoli soup',
        'notes': 'Broccoli simmered with onion in chicken broth, blended (or partially), and thickened with a milk-and-butter roux finished with cheddar.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-and-wild-rice-casserole': {'action': 'edit', 'patch': {
        'name': 'Chicken and wild rice casserole',
        'notes': 'Cooked chicken baked with a wild rice mix, mushrooms, and cream-of-mushroom-soup gravy — a Minnesota potluck staple.',
        'cuisine': 'American',
    }},
    'corpus-titled-pecan-bars': {'action': 'edit', 'patch': {
        'name': 'Pecan bars',
        'tags': ['dessert'],
        'notes': 'A shortbread crust topped with pecan-pie custard, baked and cut into bars — pecan pie in finger-food form.',
        'cuisine': 'Southern',
        'serving_grams': 60,
    }},
    'corpus-titled-boston-cream-pie': {'action': 'edit', 'patch': {
        'name': 'Boston cream pie',
        'notes': 'Two yellow sponge layers sandwiched with vanilla pastry cream and topped with a thin chocolate glaze — Massachusetts state dessert.',
        'cuisine': 'American',
    }},
    'corpus-titled-dirt-cups': {'action': 'edit', 'patch': {
        'name': 'Dirt cups',
        'tags': ['dessert'],
        'notes': 'Chocolate pudding portioned into cups, topped with crushed Oreos to look like dirt, and garnished with gummy worms — a kids\' party dessert.',
        'cuisine': 'American',
        'serving_grams': 120,
    }},
    'corpus-titled-tuna-pasta-salad': {'action': 'edit', 'patch': {
        'name': 'Tuna pasta salad',
        'notes': 'Cooked rotini or shells tossed with canned tuna, peas, peppers, celery, and a creamy mayo-mustard dressing — chilled.',
        'cuisine': 'American',
    }},
    'corpus-titled-marinated-cucumbers': {'action': 'edit', 'patch': {
        'name': 'Marinated cucumbers',
        'notes': 'Thinly sliced cucumber and onion tossed in a sweet vinegar dressing — chilled until crisp.',
    }},
    'corpus-titled-oven-roasted-potatoes': {'action': 'edit', 'patch': {
        'name': 'Oven-roasted potatoes',
        'notes': 'Cubed potatoes tossed with oil, herbs, and seasonings, roasted hot until crisp outside and tender inside.',
    }},
    'corpus-titled-raisin-cookies': {'action': 'edit', 'patch': {
        'name': 'Raisin cookies',
        'notes': 'Soft drop cookies of butter, brown sugar, eggs, flour, and plumped raisins — sometimes spiced, sometimes plain.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-hash-brown-potatoes': {'action': 'edit', 'patch': {
        'name': 'Hash brown potatoes',
        'notes': 'Shredded hash brown potatoes baked with sour cream, cream of chicken soup, and shredded cheddar — also called funeral potatoes.',
        'cuisine': 'American',
    }},
    'corpus-titled-ceviche': {'action': 'edit', 'patch': {
        'name': 'Ceviche',
        'tags': ['snack', 'lunch'],
        'notes': 'Raw shrimp or white fish diced and "cooked" in lime juice, then tossed with tomato, onion, jalapeño, cilantro, and avocado.',
        'cuisine': 'Mexican',
        'serving_grams': 200,
    }},
    'corpus-titled-egg-and-sausage-casserole': {'action': 'edit', 'patch': {
        'name': 'Egg and sausage casserole',
        'tags': ['breakfast'],
        'notes': 'Browned breakfast sausage layered with bread, eggs, milk, and cheese — assembled overnight and baked in the morning.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-celery-casserole': {'action': 'edit', 'patch': {
        'name': 'Celery casserole',
        'notes': 'Sliced celery baked with mushroom or chicken soup, water chestnuts, slivered almonds, and shredded cheese under a buttered cracker top.',
        'cuisine': 'American',
    }},
    'corpus-titled-custard': {'action': 'edit', 'patch': {
        'name': 'Vanilla custard',
        'notes': 'Eggs, milk, sugar, and vanilla cooked gently or baked in a water bath until softly set — silky and lightly sweetened.',
    }},
    'corpus-titled-jello-dessert': {'action': 'edit', 'patch': {
        'name': 'Jello dessert',
        'notes': 'Layered or molded gelatin desserts with fruit, cream cheese, and whipped topping — generic name for several Southern Jello desserts.',
        'cuisine': 'American',
    }},
    'corpus-titled-cheese-cookies': {'action': 'edit', 'patch': {
        'name': 'Cheese cookies (savory)',
        'tags': ['snack'],
        'notes': 'A short cheddar-and-butter dough piped or sliced from a log into thin crisp savory rounds — same family as cheese straws.',
        'cuisine': 'Southern',
        'serving_grams': 30,
    }},
    'corpus-titled-marinated-slaw': {'action': 'edit', 'patch': {
        'name': 'Marinated slaw',
        'notes': 'Shredded cabbage and peppers tossed with a sweet vinegar-and-oil dressing rather than mayo — chilled overnight, holds for days.',
        'cuisine': 'American',
    }},
    'corpus-titled-smothered-steak': {'action': 'edit', 'patch': {
        'name': 'Smothered steak',
        'notes': 'Round or cube steak dredged in flour and browned, then braised slowly with onions and gravy until fork-tender — Southern comfort.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-soft-chocolate-chip-cookies': {'action': 'edit', 'patch': {
        'name': 'Soft chocolate chip cookies',
        'notes': 'Drop cookies leaning on brown sugar and extra egg yolk for chew, with chocolate chips folded in — pillowy and underbaked.',
        'cuisine': 'American',
    }},
    'corpus-titled-vanilla-pudding': {'action': 'edit', 'patch': {
        'name': 'Vanilla pudding',
        'notes': 'Sugar, cornstarch, milk, eggs, and vanilla cooked into a thick stovetop pudding, finished with butter — chilled before serving.',
    }},
    'corpus-titled-hobo-bread': {'action': 'edit', 'patch': {
        'name': 'Hobo bread (coffee-can)',
        'tags': ['breakfast', 'snack'],
        'notes': 'A spiced quick bread of raisins, sugar, baking soda, flour, and oil baked in a coffee can — Depression-era road-cook bread.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-meatball-stew': {'action': 'edit', 'patch': {
        'name': 'Meatball stew',
        'notes': 'Browned meatballs simmered with potatoes, carrots, onions, and tomato in seasoned broth — a thick, comforting one-pot.',
        'cuisine': 'American',
    }},
    'corpus-titled-sausage-and-cheese-balls': {'action': 'edit', 'patch': {
        'name': 'Sausage and cheese balls',
        'ingredient_categories': ['Processed meat', 'Aged cheese', 'Prepared mixes'],
        'tags': ['snack', 'breakfast'],
        'notes': 'Bite-size baked balls of breakfast sausage, shredded cheddar, and biscuit mix — same as sausage balls.',
        'cuisine': 'American',
        'contains_add': ['pork'],
        'serving_grams': 60,
    }},
    'corpus-titled-beer-cheese-soup': {'action': 'edit', 'patch': {
        'name': 'Beer cheese soup',
        'notes': 'Vegetables sautéed in butter, simmered with beer and chicken broth, and finished with milk and shredded cheddar — a Wisconsin classic.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-seafood-dip': {'action': 'edit', 'patch': {
        'name': 'Seafood dip',
        'tags': ['snack'],
        'notes': 'Cream cheese, mayo, and sour cream mixed with shrimp, crab, lemon, and seasonings — served chilled or warm with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-finger-paint': {'action': 'drop', 'reason': 'craft / non-food recipe, not a coherent meal'},
    'corpus-titled-oriental-chicken-salad': {'action': 'edit', 'patch': {
        'name': 'Oriental chicken salad',
        'notes': 'Shredded chicken and cabbage tossed with crushed ramen noodles, slivered almonds, sesame seeds, and a soy-vinegar-sugar dressing.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-hard-candy': {'action': 'edit', 'patch': {
        'name': 'Hard candy',
        'notes': 'Sugar, water, and corn syrup cooked to hard-crack stage (300°F), flavored with extract and food color, poured to set and broken into pieces.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-almond-joy-cake': {'action': 'edit', 'patch': {
        'name': 'Almond Joy cake',
        'notes': 'A chocolate sheet cake topped with a coconut-and-marshmallow layer and a chocolate-almond ganache — Almond Joy candy flavors in cake form.',
        'cuisine': 'American',
    }},
    'corpus-titled-venison-chili': {'action': 'edit', 'patch': {
        'name': 'Venison chili',
        'notes': 'Ground or cubed venison simmered with tomatoes, beans, peppers, onions, and chili spices — a leaner game-meat take on chili.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-meringue-pie': {'action': 'edit', 'patch': {
        'name': 'Chocolate meringue pie',
        'notes': 'A baked pastry shell filled with cooked chocolate pudding and topped with a billowing toasted meringue.',
        'cuisine': 'American',
    }},
    'corpus-titled-cheese-krispies': {'action': 'edit', 'patch': {
        'name': 'Cheese krispies',
        'tags': ['snack'],
        'notes': 'Sharp cheddar, butter, and flour mixed with Rice Krispies and cayenne, dropped and pressed, then baked into crisp savory bites — Southern.',
        'cuisine': 'Southern',
        'serving_grams': 30,
    }},
    'corpus-titled-blt-dip': {'action': 'edit', 'patch': {
        'name': 'BLT dip',
        'tags': ['snack'],
        'notes': 'Sour cream and mayo mixed with crumbled bacon, diced tomato, and chopped lettuce — BLT-sandwich flavors as a chilled dip.',
        'cuisine': 'American',
        'contains_add': ['pork'],
        'serving_grams': 60,
    }},
    'corpus-titled-butterscotch-bars': {'action': 'edit', 'patch': {
        'name': 'Butterscotch bars',
        'tags': ['dessert'],
        'notes': 'A brown-sugar-and-butter blondie packed with butterscotch chips and pecans — chewy and toffee-toned.',
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

    print('corpus-titled batch-11 audit applied (entries 1501-1650 by frequency).')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
