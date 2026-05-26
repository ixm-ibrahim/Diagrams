"""Corpus-titled meals audit — batch 16 (entries 2251-2400 by frequency, 55 -> 52)."""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'src' / 'data' / 'corpus-titled-meals.json'

DECISIONS: dict[str, dict] = {
    'corpus-titled-blueberry-jello-salad': {'action': 'edit', 'patch': {
        'name': 'Blueberry Jello salad',
        'tags': ['dessert'],
        'notes': 'Blackberry or grape Jello set with crushed pineapple and blueberries, layered with sweetened cream cheese-and-sour-cream topping — a Southern molded dessert.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-polish-mistakes': {'action': 'edit', 'patch': {
        'name': 'Polish mistakes',
        'tags': ['snack'],
        'notes': 'Browned ground beef and Italian sausage mixed with Velveeta and oregano, spread on cocktail rye slices and baked or broiled — a tailgate appetizer.',
        'cuisine': 'American',
        'contains_add': ['pork'],
        'serving_grams': 80,
    }},
    'corpus-titled-fried-ice-cream': {'action': 'edit', 'patch': {
        'name': 'Fried ice cream',
        'notes': 'Scoops of ice cream rolled in crushed cornflakes or cookie crumbs, refrozen hard, and briefly deep-fried so the coating crisps without melting the ice cream.',
        'cuisine': 'Mexican',
    }},
    'corpus-titled-chocolate-sheath-cake': {'action': 'edit', 'patch': {
        'name': 'Chocolate sheath cake (Texas)',
        'notes': 'A thin chocolate-buttermilk sheet cake topped warm with a poured cocoa-pecan icing that sets to a fudge-like crust — same as Texas sheet cake.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-okra-gumbo': {'action': 'edit', 'patch': {
        'name': 'Okra gumbo',
        'notes': 'A Louisiana stew thickened with sliced okra (instead of roux), with chicken, andouille, and the trinity of vegetables — served over rice.',
        'cuisine': 'Creole',
        'contains_add': ['pork'],
    }},
    'corpus-titled-millionaires': {'action': 'edit', 'patch': {
        'name': 'Millionaires (candy)',
        'tags': ['dessert'],
        'notes': 'Pecans tossed in a hot caramel, dropped onto wax paper into clusters, then dipped in melted chocolate — a Southern turtle-candy cousin.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-cream-cheese-cupcakes': {'action': 'edit', 'patch': {
        'name': 'Cream cheese cupcakes',
        'notes': 'Mini cheesecakes baked in muffin tins over a vanilla-wafer crust, topped with fruit pie filling — same family as mini cheesecakes.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-smoked-salmon-spread': {'action': 'edit', 'patch': {
        'name': 'Smoked salmon spread',
        'tags': ['snack'],
        'notes': 'Smoked salmon blended with cream cheese, sour cream, lemon, capers, and dill — served chilled with bagel chips or crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-vegetable-chili': {'action': 'edit', 'patch': {
        'name': 'Vegetable chili',
        'notes': 'A bean-and-vegetable chili of black, kidney, and pinto beans simmered with tomatoes, peppers, corn, and chili spices — meatless and hearty.',
        'cuisine': 'American',
    }},
    'corpus-titled-lasagna-roll-ups': {'action': 'edit', 'patch': {
        'name': 'Lasagna roll-ups',
        'notes': 'Cooked lasagna noodles spread with a ricotta-spinach filling, rolled into individual portions, sauced with marinara, and baked under mozzarella.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-barbecue-meat-loaf': {'action': 'edit', 'patch': {
        'name': 'Barbecue meatloaf',
        'notes': 'A ground-beef loaf bound with breadcrumbs and egg, glazed with barbecue sauce instead of ketchup, and baked.',
        'cuisine': 'American',
    }},
    'corpus-titled-cornbread-stuffing': {'action': 'edit', 'patch': {
        'name': 'Cornbread stuffing',
        'notes': 'Crumbled cornbread mixed with sautéed onions, celery, sage, broth, and eggs, baked into a Southern Thanksgiving dressing.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-irish-potato-casserole': {'action': 'edit', 'patch': {
        'name': 'Irish potato casserole',
        'notes': 'Mashed potatoes whipped with cream cheese, sour cream, butter, and seasonings, baked under shredded cheese — funeral-potatoes-style with an Irish name.',
        'cuisine': 'American',
    }},
    'corpus-titled-pecan-cake': {'action': 'edit', 'patch': {
        'name': 'Pecan cake',
        'notes': 'A spiced butter cake folded with chopped pecans and dried or candied fruit, baked in a Bundt or tube pan — a fruitcake-cousin.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-bacon-wrapped-water-chestnuts': {'action': 'edit', 'patch': {
        'name': 'Bacon wrapped water chestnuts',
        'tags': ['snack'],
        'notes': 'Water chestnuts wrapped in bacon strips, baked or broiled, and served with a sweet soy or barbecue glaze — a retro cocktail-party appetizer.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-chocolate-ganache': {'action': 'drop', 'reason': 'topping / icing component, not a coherent meal'},
    'corpus-titled-frittata': {'action': 'edit', 'patch': {
        'name': 'Frittata',
        'notes': 'Eggs whisked with cheese and seasonings, poured over sautéed vegetables in a skillet, finished in the oven — an Italian open-face omelet.',
        'cuisine': 'Italian',
        'serving_grams': 200,
    }},
    'corpus-titled-smoothie': {'action': 'edit', 'patch': {
        'name': 'Fruit smoothie',
        'notes': 'Frozen fruit blended with yogurt or milk, ice, and a touch of sweetener — sometimes with protein powder or greens.',
        'serving_grams': 240,
    }},
    'corpus-titled-garam-masala': {'action': 'drop', 'reason': 'spice blend, not a coherent meal'},
    'corpus-titled-cocoa-brownies': {'action': 'edit', 'patch': {
        'name': 'Cocoa brownies',
        'notes': 'Brownies made with cocoa powder instead of melted chocolate — a streamlined butter-and-cocoa-based bar.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-sausage-and-peppers': {'action': 'edit', 'patch': {
        'name': 'Sausage and peppers',
        'notes': 'Italian sausage links browned and braised with sliced peppers and onions in tomato sauce — served on a hoagie or over pasta.',
        'cuisine': 'Italian-American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-cinnamon-ornaments': {'action': 'drop', 'reason': 'cinnamon-applesauce ornament dough (craft, not food), not a coherent meal'},
    'corpus-titled-crab-puffs': {'action': 'edit', 'patch': {
        'name': 'Crab puffs',
        'tags': ['snack'],
        'notes': 'Pâte à choux mounds filled with crab salad, or English-muffin halves topped with cream cheese, crab, and cheese, broiled until puffed and golden.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-chicken-broth': {'action': 'drop', 'reason': 'cooking component (broth), not a coherent meal'},
    'corpus-titled-grilled-vegetables': {'action': 'edit', 'patch': {
        'name': 'Grilled vegetables',
        'notes': 'Mixed vegetables (zucchini, peppers, eggplant, onions, mushrooms) tossed in oil and herbs, then grilled hot until charred and tender.',
    }},
    'corpus-titled-sticky-toffee-pudding': {'action': 'edit', 'patch': {
        'name': 'Sticky toffee pudding',
        'tags': ['dessert'],
        'notes': 'A dense date-cake baked tender and served warm with a hot toffee sauce and whipped cream or ice cream — the British classic.',
        'cuisine': 'British',
    }},
    'corpus-titled-eat-for-eight-bucks': {'action': 'drop', 'reason': 'magazine/blog series name, not a specific meal'},
    'corpus-titled-pecan-kisses': {'action': 'edit', 'patch': {
        'name': 'Pecan kisses (meringue)',
        'tags': ['dessert'],
        'notes': 'Beaten egg whites and sugar folded with chopped pecans, dropped onto sheets and baked into crisp meringue cookies.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-chicken-cheese-ball': {'action': 'edit', 'patch': {
        'name': 'Chicken cheese ball',
        'tags': ['snack'],
        'notes': 'Cream cheese mixed with chopped cooked chicken, peppers, and seasonings, shaped into a ball and rolled in chopped pecans — served with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-apricot-cake': {'action': 'edit', 'patch': {
        'name': 'Apricot cake',
        'notes': 'A yellow oil-based cake folded with chopped dried apricots, soaked after baking with an apricot-juice-and-sugar glaze.',
        'cuisine': 'American',
    }},
    'corpus-titled-white-chocolate-cake': {'action': 'edit', 'patch': {
        'name': 'White chocolate cake',
        'notes': 'A vanilla layer cake folded with melted white chocolate and coconut or almonds, often filled with a white-chocolate buttercream.',
        'cuisine': 'American',
    }},
    'corpus-titled-french-dip-sandwiches': {'action': 'edit', 'patch': {
        'name': 'French dip sandwiches',
        'notes': 'Sliced roast beef piled on a long roll with Swiss cheese, served with a small bowl of beef au jus for dipping.',
        'cuisine': 'American',
    }},
    'corpus-titled-apricot-nut-bread': {'action': 'edit', 'patch': {
        'name': 'Apricot nut bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A sweet quick bread folded with chopped dried apricots and walnuts, brightened with orange zest — moist with a tender crumb.',
        'cuisine': 'American',
    }},
    'corpus-titled-lazy-daisy-cake': {'action': 'edit', 'patch': {
        'name': 'Lazy daisy cake',
        'notes': 'A simple buttermilk butter cake topped warm with a broiled brown-sugar-coconut-pecan glaze — a Depression-era one-pan dessert.',
        'cuisine': 'American',
    }},
    'corpus-titled-hearty-vegetable-soup': {'action': 'edit', 'patch': {
        'name': 'Hearty vegetable soup',
        'notes': 'Mixed vegetables, beans, and sometimes ground beef simmered with tomatoes and herbs in broth — a stockpot weeknight soup.',
    }},
    'corpus-titled-strawberry-slush': {'action': 'edit', 'patch': {
        'name': 'Strawberry slush cocktail',
        'tags': ['snack'],
        'notes': 'Frozen strawberries and lemonade concentrate blended with vodka or rum, frozen in a container, then scooped slushy with lemon-lime soda.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
        'serving_grams': 240,
    }},
    'corpus-titled-s-chocolate-cake': {'action': 'edit', 'patch': {
        'name': 'Sour cream chocolate cake (Southern)',
        'notes': 'A cocoa cake enriched with sour cream — moist, tangy crumb that pairs especially well with chocolate fudge frosting.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-raisin-oatmeal-cookies': {'action': 'edit', 'patch': {
        'name': 'Raisin oatmeal cookies',
        'notes': 'Drop cookies of butter, brown sugar, oats, raisins, and warm spices — chewy and homey.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-pear-bread': {'action': 'edit', 'patch': {
        'name': 'Pear bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A spiced quick bread folded with chopped fresh pears and walnuts — moist and lightly sweet, fall and winter favorite.',
        'cuisine': 'American',
        'serving_grams': 90,
    }},
    'corpus-titled-skillet-dinner': {'action': 'edit', 'patch': {
        'name': 'Skillet dinner',
        'notes': 'Ground beef browned with onions, peppers, and tomato, then simmered with rice or noodles into a one-skillet weeknight dish.',
        'cuisine': 'American',
    }},
    'corpus-titled-green-pea-casserole': {'action': 'edit', 'patch': {
        'name': 'English pea casserole (variant)',
        'notes': 'Sweet green peas baked with mushrooms, water chestnuts, mushroom soup, and cheese under buttered cracker crumbs.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-russian-tea-mix': {'action': 'edit', 'patch': {
        'name': 'Russian tea mix',
        'ingredient_categories': ['Coffee & tea', 'Juices', 'Sugar & sweeteners', 'Whole spices', 'Ground spices', 'Citrus'],
        'tags': ['snack'],
        'notes': 'A pantry mix of instant tea, powdered Tang, sugar, and warm spices — stirred into hot water for a non-alcoholic spiced hot drink.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-buffalo-chip-cookies': {'action': 'edit', 'patch': {
        'name': 'Buffalo chip cookies',
        'notes': 'A giant kitchen-sink drop cookie packed with oats, cornflakes, coconut, chocolate chips, and chopped pecans — chewy with crunch.',
        'cuisine': 'American',
    }},
    'corpus-titled-reese-s-cups': {'action': 'edit', 'patch': {
        'name': "Homemade Reese's peanut butter cups",
        'tags': ['dessert', 'snack'],
        'notes': 'A peanut butter, powdered sugar, and graham-cracker filling sandwiched between layers of melted chocolate in muffin cups.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-lazy-lasagna': {'action': 'edit', 'patch': {
        'name': 'Lazy lasagna',
        'notes': 'Cooked rotini or shell pasta tossed with ground beef, marinara, ricotta, and mozzarella, then baked — lasagna without rolling the noodles.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-flank-steak': {'action': 'edit', 'patch': {
        'name': 'Marinated flank steak',
        'notes': 'Flank steak marinated in soy sauce, oil, garlic, and a sweetener, then grilled hot and sliced thin across the grain.',
        'cuisine': 'American',
    }},
    'corpus-titled-cheesy-hash-browns': {'action': 'edit', 'patch': {
        'name': 'Cheesy hash browns',
        'notes': 'Frozen hash browns baked with sour cream, cream of chicken soup, butter, and cheddar — funeral-potatoes-style breakfast.',
        'cuisine': 'American',
    }},
    'corpus-titled-polynesian-chicken': {'action': 'edit', 'patch': {
        'name': 'Polynesian chicken',
        'notes': 'Chicken pieces baked or simmered in a sweet-tangy pineapple-soy-and-ginger sauce with bell peppers — served over rice.',
        'cuisine': 'American',
    }},
    'corpus-titled-fried-pies': {'action': 'edit', 'patch': {
        'name': 'Fried pies',
        'tags': ['dessert'],
        'notes': 'Hand-held pastry rounds filled with spiced cooked fruit (apple, peach, apricot), sealed, and deep-fried until golden — Southern.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-filled-cookies': {'action': 'edit', 'patch': {
        'name': 'Filled (raisin) cookies',
        'notes': 'Rolled sugar-cookie dough cut into rounds, filled with a cooked raisin-or-date filling, sealed, and baked into stuffed cookies.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-cottage-cheese-pancakes': {'action': 'edit', 'patch': {
        'name': 'Cottage cheese pancakes',
        'notes': 'Eggs whisked with cottage cheese and a small amount of flour, cooked thin on a griddle — high-protein, blintz-like pancakes.',
        'cuisine': 'Jewish',
        'serving_grams': 200,
    }},
    'corpus-titled-salmon-stew': {'action': 'edit', 'patch': {
        'name': 'Salmon stew',
        'notes': 'Canned or cooked salmon simmered with diced potatoes, onion, butter, and milk into a chowder-like stew.',
        'cuisine': 'American',
    }},
    'corpus-titled-stir-fry-chicken': {'action': 'edit', 'patch': {
        'name': 'Stir-fry chicken',
        'notes': 'Diced chicken stir-fried in a hot wok with peppers, onions, broccoli, and a soy-sugar-cornstarch sauce — served over rice.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-taffy-apple-dip': {'action': 'edit', 'patch': {
        'name': 'Taffy apple dip',
        'tags': ['snack', 'dessert'],
        'notes': 'Cream cheese whipped with brown sugar, vanilla, and chopped peanuts or toffee bits — served with sliced apples for dipping.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-corn-soup': {'action': 'edit', 'patch': {
        'name': 'Corn soup',
        'notes': 'Sweet corn simmered with onion, potato, and broth, blended (or partially) and finished with milk or cream — a creamy corn chowder.',
    }},
    'corpus-titled-chile-verde': {'action': 'edit', 'patch': {
        'name': 'Chile verde (variant)',
        'notes': 'Pork shoulder slow-simmered with tomatillos, green chiles, onion, and cumin until tender — served with tortillas or over rice.',
        'cuisine': 'Mexican',
        'contains_add': ['pork'],
    }},
    'corpus-titled-mushroom-chicken': {'action': 'edit', 'patch': {
        'name': 'Mushroom chicken',
        'notes': 'Chicken breasts simmered with sliced mushrooms and onions in a cream-of-mushroom-soup gravy or sour-cream sauce.',
        'cuisine': 'American',
    }},
    'corpus-titled-seven-layer-casserole': {'action': 'edit', 'patch': {
        'name': 'Seven layer casserole',
        'notes': 'Layers of rice, corn, ground beef, peppers, onions, tomato sauce, and bacon strips baked together — a Pennsylvania-Dutch hot dish.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-chicken-and-rice-soup': {'action': 'edit', 'patch': {
        'name': 'Chicken and rice soup',
        'notes': 'Chicken simmered with rice, carrots, celery, onion, and herbs in broth — a stockpot weeknight cold-fighter.',
    }},
    'corpus-titled-chile-relleno-casserole': {'action': 'edit', 'patch': {
        'name': 'Chile relleno casserole',
        'notes': 'Whole green chiles split open and layered with cheese, poured over with an egg-and-milk batter and baked — deconstructed chile relleno.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-cherries-jubilee': {'action': 'edit', 'patch': {
        'name': 'Cherries jubilee',
        'tags': ['dessert'],
        'notes': 'Pitted cherries simmered in a sugar-and-orange syrup, flambéed tableside with kirsch or brandy, and ladled over vanilla ice cream.',
        'cuisine': 'French',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-pina-colada': {'action': 'edit', 'patch': {
        'name': 'Piña colada',
        'tags': ['snack'],
        'notes': 'Coconut cream, pineapple juice, and white rum blended with ice into a creamy frozen cocktail — Puerto Rican.',
        'cuisine': 'Caribbean',
        'contains_add': ['alcohol'],
        'serving_grams': 240,
    }},
    'corpus-titled-cheesy-chicken-enchiladas': {'action': 'edit', 'patch': {
        'name': 'Cheesy chicken enchiladas',
        'notes': 'Tortillas rolled around shredded chicken and cheese, baked in enchilada sauce, topped with more cheese and broiled bubbly.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-strawberry-banana-smoothie': {'action': 'edit', 'patch': {
        'name': 'Strawberry banana smoothie',
        'notes': 'Frozen strawberries and ripe banana blended with milk or yogurt and a touch of honey — a classic breakfast or post-workout drink.',
        'serving_grams': 240,
    }},
    'corpus-titled-gluten-free-tuesday': {'action': 'drop', 'reason': 'magazine/blog series name, not a specific meal'},
    'corpus-titled-grilling': {'action': 'drop', 'reason': 'cooking technique placeholder, not a specific meal'},
    'corpus-titled-heavenly-pie': {'action': 'edit', 'patch': {
        'name': 'Heavenly pie',
        'notes': 'A meringue shell filled with whipped cream folded with lemon curd and crushed pineapple — chilled and topped with chopped pecans.',
        'cuisine': 'American',
    }},
    'corpus-titled-baked-chicken-reuben': {'action': 'edit', 'patch': {
        'name': 'Baked chicken Reuben',
        'notes': 'Chicken breasts layered with sauerkraut and Swiss cheese, drizzled with Thousand Island dressing, and baked — Reuben sandwich as a dinner.',
        'cuisine': 'American',
    }},
    'corpus-titled-teriyaki-chicken-wings': {'action': 'edit', 'patch': {
        'name': 'Teriyaki chicken wings',
        'tags': ['snack', 'dinner'],
        'notes': 'Chicken wings marinated and baked in a soy-mirin-brown-sugar-ginger glaze until sticky and bronzed.',
        'cuisine': 'Japanese',
        'serving_grams': 170,
    }},
    'corpus-titled-glazed-sweet-potatoes': {'action': 'edit', 'patch': {
        'name': 'Orange glazed sweet potatoes',
        'notes': 'Sliced sweet potatoes baked in a butter-brown-sugar-orange-juice glaze — sticky and bright with citrus.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-pork-chops-supreme': {'action': 'edit', 'patch': {
        'name': 'Pork chops supreme',
        'notes': 'Pork chops baked in a sweet-tangy sauce of ketchup, brown sugar, lemon, and onion — a 1960s entertaining dish.',
        'cuisine': 'American',
    }},
    'corpus-titled-barbecue-baked-beans': {'action': 'edit', 'patch': {
        'name': 'Barbecue baked beans',
        'notes': 'Canned beans baked with ground beef, bacon, brown sugar, and barbecue sauce — thick and sweet cowboy-style.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-cracker-salad': {'action': 'edit', 'patch': {
        'name': 'Cracker salad',
        'notes': 'Crushed saltines tossed with diced tomatoes, onion, hard-boiled egg, and mayo — a Southern picnic side, somewhere between salad and stuffing.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-layered-nacho-dip': {'action': 'edit', 'patch': {
        'name': 'Layered nacho dip',
        'tags': ['snack'],
        'notes': 'Refried beans layered with seasoned sour cream, salsa, cheese, jalapeños, and olives — served chilled with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-chicken-dish': {'action': 'edit', 'patch': {
        'name': 'Chicken dish (mushroom)',
        'notes': 'Generic name for a baked or sautéed chicken with mushrooms and onions in a creamy sauce — a placeholder for several variants.',
        'cuisine': 'American',
    }},
    'corpus-titled-spinach-soup': {'action': 'edit', 'patch': {
        'name': 'Cream of spinach soup',
        'notes': 'Chopped spinach simmered in chicken broth with onion, then blended and finished with milk, cream, and a touch of nutmeg.',
    }},
    'corpus-titled-trash': {'action': 'edit', 'patch': {
        'name': 'White trash candy (variant)',
        'tags': ['snack', 'dessert'],
        'notes': 'Chex, pretzels, peanuts, Cheerios, and M&Ms tossed with melted white chocolate and almond bark, spread to set and broken into pieces.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-chili-pie': {'action': 'edit', 'patch': {
        'name': 'Chili pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'Layered chili, cheese, and tortilla chips or cornmeal-batter topping, baked together — a Tex-Mex casserole / Frito-pie variant.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 320,
    }},
    'corpus-titled-icebox-pickles': {'action': 'drop', 'reason': 'refrigerator pickle (canning preserve), not a coherent meal'},
    'corpus-titled-pepperoni-pizza-dip': {'action': 'edit', 'patch': {
        'name': 'Pepperoni pizza dip',
        'tags': ['snack'],
        'notes': 'Cream cheese spread topped with marinara, mozzarella, pepperoni, and Italian seasoning, baked until melty — served with breadsticks or chips.',
        'cuisine': 'Italian-American',
        'serving_grams': 60,
    }},
    'corpus-titled-tiger-butter': {'action': 'edit', 'patch': {
        'name': 'Tiger butter',
        'tags': ['dessert'],
        'notes': 'White chocolate and peanut butter melted together, drizzled with melted dark chocolate and swirled with a knife, then broken into pieces.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-pancake-syrup': {'action': 'drop', 'reason': 'sugar syrup / pancake topping, not a coherent meal'},
    'corpus-titled-date-nut-roll': {'action': 'edit', 'patch': {
        'name': 'Date nut roll',
        'tags': ['dessert'],
        'notes': 'Cooked dates folded with nuts and crushed graham crackers, rolled into a log and chilled, then sliced into rounds — Southern cookie-candy.',
        'cuisine': 'Southern',
        'serving_grams': 30,
    }},
    'corpus-titled-pumpkin-spice-cake': {'action': 'edit', 'patch': {
        'name': 'Pumpkin spice cake',
        'notes': 'A spice cake mix combined with pumpkin puree, eggs, and oil, baked into a moist spiced cake — often frosted with cream cheese icing.',
        'cuisine': 'American',
    }},
    'corpus-titled-s-cookies': {'action': 'edit', 'patch': {
        'name': 'Sour cream cookies (Southern)',
        'notes': 'Soft, cake-like sugar cookies made tender by sour cream and a touch of nutmeg — often glazed with vanilla icing.',
        'cuisine': 'Southern',
        'serving_grams': 60,
    }},
    'corpus-titled-herb-bread': {'action': 'edit', 'patch': {
        'name': 'Herb bread',
        'notes': 'A loaf of bread split, brushed with herbed butter (parsley, dill, garlic), and broiled until golden — Italian-restaurant style.',
        'cuisine': 'Italian-American',
        'serving_grams': 80,
    }},
    'corpus-titled-ham-and-noodle-casserole': {'action': 'edit', 'patch': {
        'name': 'Ham and noodle casserole',
        'notes': 'Cooked egg noodles baked with cubed ham, peas, cheese, and a cream-soup sauce — a leftover-ham one-dish meal.',
        'cuisine': 'American',
    }},
    'corpus-titled-frogmore-stew': {'action': 'edit', 'patch': {
        'name': 'Frogmore stew (Lowcountry boil)',
        'notes': 'Shrimp, smoked sausage, corn on the cob, and red potatoes boiled with Old Bay in a big pot — a Carolina Lowcountry one-pot.',
        'cuisine': 'Southern',
        'contains_add': ['pork'],
    }},
    'corpus-titled-chicken-and-sausage-jambalaya': {'action': 'edit', 'patch': {
        'name': 'Chicken and sausage jambalaya',
        'notes': 'Chicken and andouille sausage cooked with rice, the trinity of vegetables, and Cajun seasoning — a Louisiana one-pot.',
        'cuisine': 'Creole',
        'contains_add': ['pork'],
    }},
    'corpus-titled-ants-on-a-log': {'action': 'edit', 'patch': {
        'name': 'Ants on a log',
        'tags': ['snack'],
        'notes': 'Celery sticks filled with peanut butter and topped with raisins — a kids\' classic snack.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-pimiento-cheese': {'action': 'edit', 'patch': {
        'name': 'Pimiento cheese',
        'tags': ['snack'],
        'notes': 'Shredded sharp cheddar bound with mayo and diced pimentos, seasoned with cayenne — the Southern "caviar" spread for sandwiches or crackers.',
        'cuisine': 'Southern',
        'serving_grams': 60,
    }},
    'corpus-titled-cream-of-crab-soup': {'action': 'edit', 'patch': {
        'name': 'Cream of crab soup',
        'notes': 'Lump crab simmered in a milk-and-butter-roux base with a splash of sherry, Old Bay, and herbs — Maryland-style.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-oyster-cracker-snacks': {'action': 'edit', 'patch': {
        'name': 'Seasoned oyster cracker snacks',
        'ingredient_categories': ['Baked snacks & pastries', 'Oils', 'Fresh herbs', 'Ground spices', 'Dressings & dips'],
        'tags': ['snack'],
        'notes': 'Oyster crackers tossed with oil, dry ranch mix, dill, and lemon pepper, baked until aromatic — a seasoned party snack.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-party-dip': {'action': 'edit', 'patch': {
        'name': 'Party dip',
        'tags': ['snack'],
        'notes': 'Generic name for a chilled sour cream and mayo dip seasoned with dried herbs, onion, and Worcestershire — served with chips or vegetables.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-mystery-pie': {'action': 'edit', 'patch': {
        'name': 'Mystery pie (Ritz cracker)',
        'notes': 'A meringue-style pie of beaten egg whites, sugar, vanilla, and crushed Ritz crackers folded with chopped pecans — bakes into a chewy nut-pie.',
        'cuisine': 'American',
    }},
    'corpus-titled-steak': {'action': 'edit', 'patch': {
        'name': 'Pan-seared steak',
        'notes': 'A beef steak (ribeye, New York strip, or sirloin) seasoned and seared in a hot pan with butter, garlic, and herbs.',
        'cuisine': 'American',
    }},
    'corpus-titled-baked-onions': {'action': 'edit', 'patch': {
        'name': 'Baked onions',
        'notes': 'Whole sweet onions hollowed and stuffed with butter, herbs, and cheese, then slow-baked until tender and caramelized.',
        'cuisine': 'American',
    }},
    'corpus-titled-steak-and-gravy': {'action': 'edit', 'patch': {
        'name': 'Steak and gravy',
        'notes': 'Cube steak or round steak dredged in flour and browned, then braised slowly with onions and mushrooms in a brown gravy.',
        'cuisine': 'American',
    }},
    'corpus-titled-lemon-cream-pie': {'action': 'edit', 'patch': {
        'name': 'Lemon cream pie',
        'notes': 'A baked pastry shell filled with a cooked lemon-pudding custard and topped with whipped cream — chilled until set.',
        'cuisine': 'American',
    }},
    'corpus-titled-spanish-chicken': {'action': 'edit', 'patch': {
        'name': 'Spanish chicken',
        'notes': 'Chicken pieces braised with onions, peppers, tomatoes, paprika, and saffron — Spanish-style with rice.',
        'cuisine': 'Spanish',
    }},
    'corpus-titled-lemon-cheese-bars': {'action': 'edit', 'patch': {
        'name': 'Lemon cheese bars',
        'tags': ['dessert'],
        'notes': 'A yellow cake-mix base topped with a sweetened lemon-cream-cheese filling, baked into bars — chess-square-style with lemon.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-people-puppy-chow': {'action': 'edit', 'patch': {
        'name': 'Puppy chow (people)',
        'tags': ['snack', 'dessert'],
        'notes': 'Chex cereal coated in melted chocolate and peanut butter, then tossed with powdered sugar — same as muddy buddies.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-marinated-olives': {'action': 'edit', 'patch': {
        'name': 'Marinated olives',
        'tags': ['snack'],
        'notes': 'Mixed olives tossed with olive oil, garlic, lemon zest, herbs, and red pepper flakes — chilled and served as an antipasto.',
        'cuisine': 'Mediterranean',
        'serving_grams': 60,
    }},
    'corpus-titled-russian-chicken': {'action': 'edit', 'patch': {
        'name': 'Russian chicken',
        'notes': 'Chicken pieces baked over a sauce of Russian dressing, apricot preserves, and onion soup mix — a retro pantry casserole.',
        'cuisine': 'American',
    }},
    'corpus-titled-gingerbread-pancakes': {'action': 'edit', 'patch': {
        'name': 'Gingerbread pancakes',
        'notes': 'Spiced buttermilk pancake batter with molasses, ginger, cinnamon, and cloves — a holiday breakfast.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-banana-cookies': {'action': 'edit', 'patch': {
        'name': 'Banana cookies',
        'notes': 'Soft drop cookies of mashed banana, butter, sugar, eggs, and oats or flour — sometimes spiced, sometimes with raisins or chocolate chips.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-summer-pasta-salad': {'action': 'edit', 'patch': {
        'name': 'Summer pasta salad',
        'notes': 'Cooked rotini or shells tossed with diced cucumber, tomato, peppers, onion, and Italian dressing — chilled.',
        'cuisine': 'American',
    }},
    'corpus-titled-roasted-cauliflower': {'action': 'edit', 'patch': {
        'name': 'Roasted cauliflower',
        'notes': 'Cauliflower florets tossed with olive oil, garlic, and salt, roasted hot until tender and lightly charred — sometimes finished with Parmesan.',
    }},
    'corpus-titled-breakfast-burrito': {'action': 'edit', 'patch': {
        'name': 'Breakfast burrito',
        'notes': 'A flour tortilla wrapped around scrambled eggs, breakfast sausage or bacon, cheese, and potatoes — sometimes salsa and beans too.',
        'cuisine': 'Tex-Mex',
        'contains_add': ['pork'],
    }},
    'corpus-titled-blt-salad': {'action': 'edit', 'patch': {
        'name': 'BLT salad',
        'notes': 'Romaine, diced tomatoes, crisp bacon, and croutons tossed with mayo or ranch dressing — BLT sandwich flavors as a salad.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-cherry-torte': {'action': 'edit', 'patch': {
        'name': 'Cherry torte',
        'tags': ['dessert'],
        'notes': 'A graham crust topped with sweetened cream cheese, cherry pie filling, and whipped topping — same family as cherry delight.',
        'cuisine': 'American',
        'serving_grams': 140,
    }},
    'corpus-titled-buns': {'action': 'edit', 'patch': {
        'name': 'Yeast buns',
        'tags': ['dinner', 'lunch'],
        'notes': 'A soft enriched yeasted dough mixed and proofed, shaped into rolls, and baked until golden — for hamburgers, hot dogs, or dinner.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-mini-cheese-cakes': {'action': 'edit', 'patch': {
        'name': 'Mini cheesecakes (variant)',
        'notes': 'Individual cheesecakes baked in muffin tins over a vanilla-wafer crust, topped with fruit pie filling.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-blond-brownies': {'action': 'edit', 'patch': {
        'name': 'Blond brownies (blondies)',
        'notes': 'Brown-sugar-and-butter bars in brownie shape but with vanilla in place of chocolate — sometimes with butterscotch or chocolate chips.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-chocolate-cherry-bars': {'action': 'edit', 'patch': {
        'name': 'Chocolate cherry bars',
        'tags': ['dessert'],
        'notes': 'A chocolate cake mix combined with canned cherry pie filling and eggs, baked and topped with a chocolate-fudge frosting — cut into bars.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-buttermilk-brownies': {'action': 'edit', 'patch': {
        'name': 'Buttermilk brownies (Texas sheet cake)',
        'notes': 'A thin chocolate-buttermilk sheet "brownie" topped warm with a poured cocoa-pecan icing — same as Texas sheet cake.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-hanky-panky': {'action': 'edit', 'patch': {
        'name': 'Hanky panky',
        'tags': ['snack'],
        'notes': 'Browned ground beef and Italian sausage mixed with Velveeta and oregano, spread on cocktail rye and baked — same as Polish mistakes.',
        'cuisine': 'American',
        'contains_add': ['pork'],
        'serving_grams': 80,
    }},
    'corpus-titled-anadama-bread': {'action': 'edit', 'patch': {
        'name': 'Anadama bread',
        'notes': 'A yeasted New England loaf sweetened with molasses and enriched with cornmeal — soft, brown, and faintly sweet.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-corn': {'action': 'edit', 'patch': {
        'name': 'Buttered corn',
        'notes': 'Fresh or frozen sweet corn cooked tender and tossed with butter, salt, and pepper — a simple side.',
    }},
    'corpus-titled-lime-congealed-salad': {'action': 'edit', 'patch': {
        'name': 'Lime congealed salad',
        'tags': ['dessert'],
        'notes': 'Lime gelatin set with crushed pineapple, cottage cheese, whipped topping, and chopped pecans — a Southern molded dessert salad.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-macaroni': {'action': 'edit', 'patch': {
        'name': 'Macaroni and cheese (variant)',
        'notes': 'Elbow macaroni in a cheddar-bechamel sauce — generic "macaroni" recipe is typically mac and cheese.',
        'cuisine': 'American',
    }},
    'corpus-titled-italian-potato-salad': {'action': 'edit', 'patch': {
        'name': 'Italian potato salad',
        'notes': 'Boiled potatoes tossed with olive oil, white wine vinegar, garlic, herbs, capers, and red onion — no mayo, served warm or chilled.',
        'cuisine': 'Italian',
    }},
    'corpus-titled-coke-cake': {'action': 'edit', 'patch': {
        'name': 'Coca-Cola cake (variant)',
        'notes': 'A buttermilk-and-cocoa sheet cake with a bottle of Coca-Cola stirred into the batter, finished with a warm cola-pecan icing.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-zucchini': {'action': 'edit', 'patch': {
        'name': 'Sautéed zucchini',
        'notes': 'Sliced zucchini sautéed in olive oil with garlic, salt, and Parmesan — a simple summer side.',
        'cuisine': 'Italian',
    }},
    'corpus-titled-pickled-mushrooms': {'action': 'edit', 'patch': {
        'name': 'Marinated mushrooms (variant)',
        'tags': ['snack'],
        'notes': 'Whole button mushrooms tossed in a herb-and-vinegar marinade with oil, lemon, and seasonings — chilled as an appetizer.',
        'serving_grams': 80,
    }},
    'corpus-titled-old-fashion-tea-cakes': {'action': 'edit', 'patch': {
        'name': 'Old-fashioned tea cakes',
        'notes': 'A simple Southern butter-sugar-flour cookie scented with vanilla and nutmeg — soft, cake-like, traditionally served with tea.',
        'cuisine': 'Southern',
        'serving_grams': 60,
    }},
    'corpus-titled-marble-cake': {'action': 'edit', 'patch': {
        'name': 'Marble cake',
        'notes': 'A butter cake batter split in two and tinted dark with cocoa, then swirled together for a marbled chocolate-and-vanilla effect.',
        'cuisine': 'American',
    }},
    'corpus-titled-paprika-chicken': {'action': 'edit', 'patch': {
        'name': 'Paprika chicken',
        'notes': 'Chicken pieces browned and simmered in a sour-cream-and-paprika sauce — a Hungarian-American variant of paprikash.',
        'cuisine': 'Hungarian',
    }},
    'corpus-titled-truffles': {'action': 'edit', 'patch': {
        'name': 'Chocolate truffles',
        'notes': 'Chocolate ganache (chocolate and warm cream) chilled, scooped into balls, and rolled in cocoa, nuts, or coatings.',
        'cuisine': 'French',
        'serving_grams': 30,
    }},
    'corpus-titled-marinated-chicken-breasts': {'action': 'edit', 'patch': {
        'name': 'Marinated chicken breasts',
        'notes': 'Chicken breasts marinated in Italian dressing or a soy-citrus mixture and then grilled, baked, or pan-cooked.',
        'cuisine': 'American',
    }},
    'corpus-titled-walnut-pie': {'action': 'edit', 'patch': {
        'name': 'Walnut pie',
        'notes': 'A pecan-pie-style filling of eggs, sugar, butter, and corn syrup studded with walnut halves instead of pecans — toasty and rich.',
        'cuisine': 'American',
    }},
    'corpus-titled-chicken-broccoli': {'action': 'edit', 'patch': {
        'name': 'Chicken broccoli (Divan-style)',
        'notes': 'Cooked chicken and broccoli baked in a mayo-and-mushroom-soup sauce with curry powder, topped with cheese and breadcrumbs.',
        'cuisine': 'American',
    }},
    'corpus-titled-pecan-crispies': {'action': 'edit', 'patch': {
        'name': 'Pecan crispies (sandies)',
        'tags': ['dessert'],
        'notes': 'A butter-and-powdered-sugar shortbread folded with finely chopped pecans — same family as pecan sandies and snowballs.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-almond-crescents': {'action': 'edit', 'patch': {
        'name': 'Almond crescents',
        'tags': ['dessert'],
        'notes': 'A butter-shortbread folded with ground almonds, shaped into crescents and baked, then rolled in powdered sugar — German Vanillekipferl style.',
        'cuisine': 'German',
        'serving_grams': 30,
    }},
    'corpus-titled-strawberry-jello-cake': {'action': 'edit', 'patch': {
        'name': 'Strawberry Jello cake (poke)',
        'notes': 'A baked white cake poked all over and saturated with strawberry Jello, then chilled and topped with whipped topping and fresh strawberries.',
        'cuisine': 'American',
    }},
    'corpus-titled-almond-cake': {'action': 'edit', 'patch': {
        'name': 'Almond cake',
        'notes': 'A dense butter cake folded with ground almonds and almond extract, often soaked or glazed with a sugar-almond syrup.',
        'cuisine': 'European',
    }},
    'corpus-titled-margaritas': {'action': 'edit', 'patch': {
        'name': 'Margaritas (pitcher)',
        'tags': ['snack'],
        'notes': 'Tequila, lime juice, and triple sec or Cointreau mixed with ice and served in salt-rimmed glasses — Mexico\'s most-exported cocktail.',
        'cuisine': 'Mexican',
        'contains_add': ['alcohol'],
        'serving_grams': 100,
    }},
    'corpus-titled-mexican-pinwheels': {'action': 'edit', 'patch': {
        'name': 'Mexican pinwheels',
        'tags': ['snack'],
        'notes': 'Tortillas spread with seasoned cream cheese, salsa, olives, and green chiles, rolled into a log and sliced into pinwheels.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-seven-up-salad': {'action': 'edit', 'patch': {
        'name': '7-Up salad (variant)',
        'ingredient_categories': ['Tropical fruits', 'Citrus', 'Candy & desserts', 'Fresh cheese', 'Sugar & sweeteners', 'Nuts', 'Soft drinks'],
        'tags': ['dessert'],
        'notes': 'Lemon-lime Jello set with crushed pineapple, mandarin oranges, and a bottle of 7-Up, folded with whipped topping and pecans.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-hot-milk-sponge-cake': {'action': 'edit', 'patch': {
        'name': 'Hot milk sponge cake',
        'notes': 'A foam-leavened cake of beaten eggs and sugar whisked with hot scalded milk and melted butter — moist, fine-crumbed, served plain or with fruit.',
        'cuisine': 'American',
    }},
    'corpus-titled-beef-pot-roast': {'action': 'edit', 'patch': {
        'name': 'Beef pot roast',
        'notes': 'A chuck or round roast seared and slow-braised in beef broth with onions, carrots, potatoes, and herbs until fork-tender.',
        'cuisine': 'American',
    }},
    'corpus-titled-cheese-potato-casserole': {'action': 'edit', 'patch': {
        'name': 'Cheese potato casserole',
        'notes': 'Cubed or shredded potatoes baked with sour cream, butter, cream of chicken soup, and shredded cheddar — funeral-potatoes-style.',
        'cuisine': 'American',
    }},
    'corpus-titled-dilly-casserole-bread': {'action': 'edit', 'patch': {
        'name': 'Dilly casserole bread',
        'notes': 'A cottage-cheese yeast bread folded with dill and onion, baked in a casserole dish — chewy, savory, and tangy.',
        'cuisine': 'American',
        'serving_grams': 55,
    }},
    'corpus-titled-peanut-butter-roll': {'action': 'edit', 'patch': {
        'name': 'Peanut butter roll',
        'tags': ['dessert'],
        'notes': 'Mashed potato kneaded with powdered sugar into a pliable dough, rolled around peanut butter, and sliced into pinwheels — Appalachian.',
        'cuisine': 'Appalachian',
        'serving_grams': 30,
    }},
    'corpus-titled-churros': {'action': 'edit', 'patch': {
        'name': 'Churros',
        'tags': ['dessert', 'snack'],
        'notes': 'A piped pâte-à-choux-like dough deep-fried into ridged sticks and tossed in cinnamon sugar — served with chocolate dipping sauce.',
        'cuisine': 'Spanish',
        'serving_grams': 80,
    }},
    'corpus-titled-vegetable-pie': {'action': 'edit', 'patch': {
        'name': 'Vegetable pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'A pastry shell or crustless pan filled with mixed vegetables baked in an egg-and-cheese custard — meatless quiche-style.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-dream-cake': {'action': 'edit', 'patch': {
        'name': 'Dream cake',
        'notes': 'A yellow cake mix with crushed pineapple, vanilla pudding, eggs, and oil — finished with cream cheese frosting and chopped pecans.',
        'cuisine': 'American',
    }},
    'corpus-titled-veggie-casserole': {'action': 'edit', 'patch': {
        'name': 'Veggie casserole',
        'notes': 'A mix of vegetables baked with cheese, mayo, and a buttery cracker or breadcrumb topping.',
    }},
    'corpus-titled-bourbon-slush': {'action': 'edit', 'patch': {
        'name': 'Bourbon slush',
        'ingredient_categories': ['Juices', 'Citrus', 'Sugar & sweeteners', 'Alcoholic beverages', 'Coffee & tea'],
        'tags': ['snack'],
        'notes': 'Frozen tea-and-fruit-juice concentrate spiked with bourbon, then topped with lemon-lime soda at serving — a slushy Kentucky cocktail.',
        'cuisine': 'Southern',
        'contains_add': ['alcohol'],
        'serving_grams': 240,
    }},
    'corpus-titled-butter-pecan-cake': {'action': 'edit', 'patch': {
        'name': 'Butter pecan cake',
        'notes': 'A butter cake mix combined with vanilla pudding and toasted pecans, baked into a Bundt cake — sometimes glazed with caramel.',
        'cuisine': 'Southern',
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

    print('corpus-titled batch-16 audit applied (entries 2251-2400 by frequency).')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
