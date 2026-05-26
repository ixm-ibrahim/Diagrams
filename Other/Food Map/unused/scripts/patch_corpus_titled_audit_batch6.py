"""Corpus-titled meals audit — batch 6 (entries 751-900 by frequency, 143 -> 123).

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
    'corpus-titled-bourbon-balls': {'action': 'edit', 'patch': {
        'name': 'Bourbon balls',
        'tags': ['dessert'],
        'notes': 'Crushed vanilla wafers mixed with cocoa, powdered sugar, corn syrup, pecans, and bourbon — rolled into balls and dusted in sugar.',
        'cuisine': 'Southern',
        'contains_add': ['alcohol'],
        'serving_grams': 30,
    }},
    'corpus-titled-potatoes-au-gratin': {'action': 'edit', 'patch': {
        'name': 'Potatoes au gratin',
        'notes': 'Sliced potatoes layered with onions and Gruyère or cheddar in a milk-and-cream sauce, baked until bubbling with a golden cheese crust.',
        'cuisine': 'French',
    }},
    'corpus-titled-seven-layer-cookies': {'action': 'edit', 'patch': {
        'name': 'Seven layer bars',
        'notes': 'Graham-cracker crust layered with chocolate chips, butterscotch chips, coconut, and pecans, drizzled with sweetened condensed milk and baked — same as Hello Dollies.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-chili-beans': {'action': 'edit', 'patch': {
        'name': 'Chili beans',
        'notes': 'Pinto or kidney beans simmered with ground beef, tomatoes, onions, peppers, and chili spices — a softer chili-style stew.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-fudge-cake': {'action': 'edit', 'patch': {
        'name': 'Fudge cake',
        'notes': 'A dense, rich chocolate cake leaning toward brownie texture — moist crumb, deep cocoa, often glazed or frosted with ganache.',
        'cuisine': 'American',
    }},
    'corpus-titled-flour-tortillas': {'action': 'edit', 'patch': {
        'name': 'Flour tortillas',
        'notes': 'A soft unleavened wheat flatbread of flour, salt, water, and shortening or lard — rolled thin and griddled.',
        'cuisine': 'Mexican',
        'serving_grams': 55,
    }},
    'corpus-titled-sesame-chicken': {'action': 'edit', 'patch': {
        'name': 'Sesame chicken',
        'notes': 'Battered chicken pieces deep-fried and tossed in a glossy sweet-soy sauce with toasted sesame seeds — Chinese-American restaurant style.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-baked-fish': {'action': 'edit', 'patch': {
        'name': 'Baked fish',
        'notes': 'White-fish fillets baked in butter, lemon, and herbs until just flaking — a low-effort weeknight preparation.',
    }},
    'corpus-titled-cowboy-beans': {'action': 'edit', 'patch': {
        'name': 'Cowboy beans',
        'notes': 'Pinto or kidney beans baked with ground beef, bacon, brown sugar, and barbecue sauce — a heartier, sweeter take on chili.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-salmon-cakes': {'action': 'edit', 'patch': {
        'name': 'Salmon cakes',
        'tags': ['dinner', 'lunch'],
        'notes': 'Canned or cooked salmon mixed with egg, breadcrumbs, lemon, and onion, formed into patties and pan-fried until crisp.',
        'cuisine': 'American',
    }},
    'corpus-titled-apricot-chicken': {'action': 'edit', 'patch': {
        'name': 'Apricot chicken',
        'notes': 'Chicken pieces baked over apricot preserves whisked with French dressing and onion soup mix — a sweet-savory potluck favorite.',
        'cuisine': 'American',
    }},
    'corpus-titled-barbecue-beans': {'action': 'edit', 'patch': {
        'name': 'Barbecue beans',
        'notes': 'Canned beans simmered with ground beef, bacon, onions, brown sugar, and barbecue sauce — a thick, sweet cowboy-style bean side.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-creamy-potato-soup': {'action': 'edit', 'patch': {
        'name': 'Creamy potato soup',
        'notes': 'Diced potatoes simmered in broth with onion and bacon, finished with milk and cream — sometimes topped with cheese and chives.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-apple-muffins': {'action': 'edit', 'patch': {
        'name': 'Apple muffins',
        'tags': ['breakfast', 'snack'],
        'notes': 'Tender muffins folded with diced apples and cinnamon — sometimes topped with a sugar streusel.',
        'serving_grams': 60,
    }},
    'corpus-titled-squash-pickles': {'action': 'drop', 'reason': 'pickled condiment, not a coherent meal'},
    'corpus-titled-sourdough-starter': {'action': 'drop', 'reason': 'bread starter (cooking component), not a coherent meal'},
    'corpus-titled-dirt-pudding': {'action': 'edit', 'patch': {
        'name': 'Dirt pudding',
        'notes': 'Vanilla pudding folded with cream cheese, butter, and whipped topping, layered with crushed Oreos — served in cups, often with gummy worms.',
        'cuisine': 'American',
    }},
    'corpus-titled-caramel-apple-dip': {'action': 'edit', 'patch': {
        'name': 'Caramel apple dip',
        'tags': ['snack', 'dessert'],
        'notes': 'Cream cheese whipped with brown sugar, vanilla, and toffee bits — served with sliced apples for dipping.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-chocolate-eclair': {'action': 'edit', 'patch': {
        'name': 'Chocolate éclairs',
        'notes': 'Pâte-à-choux fingers baked hollow, filled with vanilla pastry cream, and topped with a chocolate glaze.',
        'cuisine': 'French',
    }},
    'corpus-titled-cracker-jacks': {'action': 'edit', 'patch': {
        'name': 'Cracker Jack (caramel-peanut popcorn)',
        'tags': ['snack', 'dessert'],
        'notes': 'Popped corn and peanuts coated in a hot molasses-and-brown-sugar caramel, then baked until crisp.',
        'cuisine': 'American',
    }},
    'corpus-titled-lime-salad': {'action': 'edit', 'patch': {
        'name': 'Lime salad',
        'tags': ['dessert'],
        'notes': 'Lime gelatin set with crushed pineapple, cottage cheese, whipped topping, and chopped pecans — a Southern molded dessert salad.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-pulled-pork': {'action': 'edit', 'patch': {
        'name': 'Pulled pork',
        'notes': 'Pork shoulder rubbed with spices and slow-cooked (smoked, braised, or in a slow cooker) until it shreds with a fork, then tossed in barbecue sauce.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-boiled-custard': {'action': 'edit', 'patch': {
        'name': 'Boiled custard',
        'notes': 'A pourable Southern custard of milk, sugar, eggs, and vanilla cooked gently on the stove until thickened — served chilled in mugs.',
        'cuisine': 'Southern',
        'serving_grams': 120,
    }},
    'corpus-titled-sour-cream-enchiladas': {'action': 'edit', 'patch': {
        'name': 'Sour cream enchiladas',
        'notes': 'Tortillas rolled around shredded chicken or beef and cheese, baked in a creamy sour-cream-and-green-chile sauce topped with more cheese.',
        'cuisine': 'Tex-Mex',
    }},
    'corpus-titled-sausage-and-egg-casserole': {'action': 'edit', 'patch': {
        'name': 'Sausage and egg casserole',
        'tags': ['breakfast'],
        'notes': 'Breakfast sausage browned, layered with bread and cheese, soaked in egg-and-milk custard overnight, and baked until set.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-date-pudding': {'action': 'edit', 'patch': {
        'name': 'Date pudding',
        'notes': 'A sticky baked pudding-cake of chopped dates folded into a butter-and-brown-sugar batter, served warm with a toffee sauce.',
        'cuisine': 'British',
    }},
    'corpus-titled-chicken-chow-mein': {'action': 'edit', 'patch': {
        'name': 'Chicken chow mein',
        'notes': 'Stir-fried chicken with celery, onions, mushrooms, and bean sprouts in a soy-thickened sauce — served over crispy chow mein noodles or rice.',
        'cuisine': 'Chinese-American',
    }},
    'corpus-titled-apple-crumb-pie': {'action': 'edit', 'patch': {
        'name': 'Apple crumb pie',
        'notes': 'A single-crust apple pie topped with a buttery brown-sugar-and-flour crumb streusel in place of a second crust.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-chip-oatmeal-cookies': {'action': 'edit', 'patch': {
        'name': 'Chocolate chip oatmeal cookies',
        'notes': 'Drop cookies of oats, butter, brown sugar, eggs, and chocolate chips — chewier than chocolate chip thanks to the oats.',
        'cuisine': 'American',
    }},
    'corpus-titled-pimento-cheese': {'action': 'edit', 'patch': {
        'name': 'Pimento cheese',
        'tags': ['snack'],
        'notes': 'Shredded sharp cheddar bound with mayo and diced pimentos, seasoned with cayenne — the Southern "caviar" spread for sandwiches or crackers.',
        'cuisine': 'Southern',
        'serving_grams': 60,
    }},
    'corpus-titled-chocolate-cherry-cake': {'action': 'edit', 'patch': {
        'name': 'Chocolate cherry cake',
        'notes': 'A chocolate cake mix combined with canned cherry pie filling and eggs, baked and topped with a chocolate-fudge frosting.',
        'cuisine': 'American',
    }},
    'corpus-titled-white-fruit-cake': {'action': 'edit', 'patch': {
        'name': 'White fruitcake',
        'notes': 'A pale fruitcake of butter, eggs, candied pineapple and cherries, coconut, and pecans — lighter and not spiced, unlike the dark holiday fruitcake.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-oatmeal-pancakes': {'action': 'edit', 'patch': {
        'name': 'Oatmeal pancakes',
        'notes': 'Pancakes made with rolled oats soaked in buttermilk and folded into a flour-and-baking-soda batter — tender and hearty.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-german-apple-cake': {'action': 'edit', 'patch': {
        'name': 'German apple cake',
        'notes': 'A dense oil-and-egg cake layered or studded with apples and spices — typically a single-pan bake with a sugar dust or simple glaze.',
        'cuisine': 'German',
    }},
    'corpus-titled-brown-sugar-cookies': {'action': 'edit', 'patch': {
        'name': 'Brown sugar cookies',
        'notes': 'Drop or rolled cookies sweetened with brown sugar instead of white — chewy with caramel-toffee notes.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-chocolate-mayonnaise-cake': {'action': 'edit', 'patch': {
        'name': 'Chocolate mayonnaise cake',
        'notes': 'A cocoa cake using mayonnaise in place of butter and eggs (mayo carries both fat and emulsion) — moist and rich.',
        'cuisine': 'American',
    }},
    'corpus-titled-macaroni-and-cheese-casserole': {'action': 'edit', 'patch': {
        'name': 'Macaroni and cheese casserole',
        'notes': 'Cooked elbow macaroni baked in a milk-and-flour-thickened cheddar sauce under buttered breadcrumbs or more cheese.',
        'cuisine': 'American',
    }},
    'corpus-titled-broccoli-and-cheese-casserole': {'action': 'edit', 'patch': {
        'name': 'Broccoli and cheese casserole',
        'notes': 'Broccoli florets baked with rice, cream of mushroom soup, and cheddar or Velveeta — a Southern potluck side.',
        'cuisine': 'American',
    }},
    'corpus-titled-pepperoni-bread': {'action': 'edit', 'patch': {
        'name': 'Pepperoni bread',
        'notes': 'Frozen bread dough rolled around pepperoni, mozzarella, and Italian herbs, then baked into a sliceable savory loaf.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-beef-enchiladas': {'action': 'edit', 'patch': {
        'name': 'Beef enchiladas',
        'notes': 'Tortillas rolled around seasoned ground beef and cheese, lined in a pan, covered in red chile sauce and more cheese, and baked.',
        'cuisine': 'Mexican',
    }},
    'corpus-titled-boston-baked-beans': {'action': 'edit', 'patch': {
        'name': 'Boston baked beans',
        'notes': 'Navy beans slow-baked overnight with salt pork, molasses, brown sugar, and mustard in a covered crock — the New England original.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-zucchini-fritters': {'action': 'edit', 'patch': {
        'name': 'Zucchini fritters',
        'notes': 'Grated zucchini squeezed dry, mixed with egg, flour, and cheese, dropped into oil and pan-fried until golden.',
    }},
    'corpus-titled-cheese-fondue': {'action': 'edit', 'patch': {
        'name': 'Cheese fondue',
        'notes': 'Gruyère and Emmentaler melted in white wine with garlic, kirsch, and a touch of cornstarch — kept warm over a flame for dipping bread cubes.',
        'cuisine': 'Swiss',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-grape-salad': {'action': 'edit', 'patch': {
        'name': 'Grape salad',
        'tags': ['dessert'],
        'notes': 'Halved grapes folded with sweetened cream cheese and sour cream, topped with brown sugar and chopped pecans — a Southern potluck dessert.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-watergate-cake': {'action': 'edit', 'patch': {
        'name': 'Watergate cake',
        'notes': 'A green-tinted pistachio-pudding-and-cake-mix Bundt with chopped pecans and 7-Up — companion of the Watergate (pistachio) salad.',
        'cuisine': 'American',
    }},
    'corpus-titled-black-walnut-cake': {'action': 'edit', 'patch': {
        'name': 'Black walnut cake',
        'notes': 'A buttery layer cake folded with finely chopped black walnuts and frosted with cream cheese icing — earthier than English walnut versions.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-chicken-parmigiana': {'action': 'edit', 'patch': {
        'name': 'Chicken parmigiana',
        'notes': 'Breaded chicken cutlets fried, then baked under marinara and melted mozzarella with grated Parmesan — Italian-American comfort.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-pumpkin-chiffon-pie': {'action': 'edit', 'patch': {
        'name': 'Pumpkin chiffon pie',
        'notes': 'Pumpkin custard lightened with gelatin and beaten egg whites, poured into a baked crust and chilled until set — airier than baked pumpkin pie.',
        'cuisine': 'American',
    }},
    'corpus-titled-cream-of-potato-soup': {'action': 'edit', 'patch': {
        'name': 'Cream of potato soup',
        'notes': 'Diced potatoes simmered with onion and broth, then blended (or partially mashed) and thickened with milk, cream, and butter.',
    }},
    'corpus-titled-southern-fried-chicken': {'action': 'edit', 'patch': {
        'name': 'Southern fried chicken',
        'notes': 'Chicken pieces brined or buttermilk-soaked, dredged in seasoned flour, and deep-fried until crisp — the Southern Sunday-supper classic.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-turtles': {'action': 'edit', 'patch': {
        'name': 'Turtles (pecan candy)',
        'tags': ['dessert'],
        'notes': 'Pecans arranged in clusters, topped with a soft caramel, then drizzled or dipped in melted chocolate — resembling turtle shapes.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-cheeseburger-casserole': {'action': 'edit', 'patch': {
        'name': 'Cheeseburger casserole',
        'notes': 'Ground beef cooked with onions, peppers, and tomato, layered in a pan with cheese and tater tots or crescent dough, baked.',
        'cuisine': 'American',
    }},
    'corpus-titled-strawberry-ice-cream': {'action': 'edit', 'patch': {
        'name': 'Strawberry ice cream',
        'notes': 'A churned custard of pureed fresh strawberries blended with milk, cream, sugar, and egg yolks — pink and fruity.',
        'serving_grams': 85,
    }},
    'corpus-titled-vegetable-medley': {'action': 'edit', 'patch': {
        'name': 'Vegetable medley',
        'notes': 'A mix of seasonal vegetables (carrots, broccoli, cauliflower, squash) roasted or sautéed together with butter and seasonings.',
    }},
    'corpus-titled-peanut-butter-squares': {'action': 'edit', 'patch': {
        'name': 'Peanut butter squares',
        'tags': ['dessert'],
        'notes': 'A no-bake bar of peanut butter, butter, and powdered sugar pressed into a pan and topped with melted chocolate.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-squash-fritters': {'action': 'edit', 'patch': {
        'name': 'Squash fritters',
        'notes': 'Grated yellow squash mixed with egg, flour, and seasonings, dropped into oil and pan-fried until golden.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-shoo-fly-pie': {'action': 'edit', 'patch': {
        'name': 'Shoofly pie',
        'notes': 'A Pennsylvania-Dutch molasses pie with a wet, gooey bottom and a sandy crumb topping baked into a single crust.',
        'cuisine': 'American',
    }},
    'corpus-titled-champagne-punch': {'action': 'edit', 'patch': {
        'name': 'Champagne punch',
        'notes': 'Champagne or sparkling wine mixed with fruit juices, brandy, and a sweetener — served from a bowl with citrus floats.',
        'cuisine': 'American',
        'contains_add': ['alcohol'],
        'serving_grams': 150,
    }},
    'corpus-titled-broccoli-cauliflower-salad': {'action': 'edit', 'patch': {
        'name': 'Broccoli-cauliflower salad',
        'notes': 'Raw broccoli and cauliflower florets tossed with bacon, red onion, sugar, and a mayonnaise dressing — broccoli-salad style.',
        'cuisine': 'American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-spice-cake': {'action': 'edit', 'patch': {
        'name': 'Spice cake',
        'notes': 'A butter cake heavily scented with cinnamon, cloves, nutmeg, and allspice — often frosted with cream cheese or caramel icing.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-pudding-cake': {'action': 'edit', 'patch': {
        'name': 'Chocolate pudding cake',
        'notes': 'A self-saucing cake — batter poured into a pan, topped with cocoa and sugar, then boiling water, which sinks to form a pudding sauce as the cake bakes.',
        'cuisine': 'American',
    }},
    'corpus-titled-crabmeat-dip': {'action': 'edit', 'patch': {
        'name': 'Crabmeat dip',
        'tags': ['snack'],
        'notes': 'Cream cheese whipped with crab, lemon, and Worcestershire — served chilled or warm with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-beet-salad': {'action': 'edit', 'patch': {
        'name': 'Beet salad',
        'notes': 'Sliced cooked beets tossed with vinaigrette and orange or onion — or molded with citrus gelatin in the Southern style.',
    }},
    'corpus-titled-cranberry-punch': {'action': 'edit', 'patch': {
        'name': 'Cranberry punch',
        'ingredient_categories': ['Juices', 'Berries', 'Citrus', 'Sugar & sweeteners', 'Tropical fruits', 'Soft drinks'],
        'tags': ['snack'],
        'notes': 'Cranberry juice mixed with orange or pineapple juice and ginger ale or sparkling water — a non-alcoholic holiday punch.',
        'cuisine': 'American',
        'serving_grams': 240,
    }},
    'corpus-titled-irish-stew': {'action': 'edit', 'patch': {
        'name': 'Irish stew',
        'notes': 'Lamb or mutton stewed slowly with potatoes, onions, and carrots in a simple broth — traditional Irish farmhouse fare.',
        'cuisine': 'Irish',
    }},
    'corpus-titled-broccoli-dip': {'action': 'edit', 'patch': {
        'name': 'Broccoli dip',
        'tags': ['snack'],
        'notes': 'Chopped broccoli baked with cream of mushroom soup, butter, and processed cheese — a hot dip served with crackers or bread cubes.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-swedish-apple-pie': {'action': 'edit', 'patch': {
        'name': 'Swedish apple pie',
        'notes': 'A crustless single-pan apple "pie" with sliced apples on the bottom and a butter-sugar-flour-pecan batter poured on top — bakes into a self-streuseled crust.',
        'cuisine': 'Swedish',
    }},
    'corpus-titled-gumbo': {'action': 'edit', 'patch': {
        'name': 'Gumbo',
        'notes': 'A Louisiana stew built on a dark roux with the trinity of vegetables, andouille and chicken or shrimp, okra, and Creole seasoning — served over rice.',
        'cuisine': 'Creole',
        'contains_add': ['pork'],
    }},
    'corpus-titled-sausage-rolls': {'action': 'edit', 'patch': {
        'name': 'Sausage rolls',
        'tags': ['snack'],
        'notes': 'Seasoned sausage meat wrapped in puff pastry and baked into golden logs — a British pub snack.',
        'cuisine': 'British',
        'contains_add': ['pork'],
        'serving_grams': 80,
    }},
    'corpus-titled-chicken-bake': {'action': 'edit', 'patch': {
        'name': 'Chicken bake',
        'notes': 'Chicken pieces baked with rice, vegetables, and mushroom or cream-soup sauce — a low-effort one-dish meal.',
    }},
    'corpus-titled-pecan-tarts': {'action': 'edit', 'patch': {
        'name': 'Pecan tarts (tassies)',
        'notes': 'Mini cream-cheese pastry shells pressed into muffin tins, filled with a brown-sugar-egg-butter custard and chopped pecans, baked into bite-size tarts.',
        'cuisine': 'Southern',
        'serving_grams': 30,
    }},
    'corpus-titled-vinegar-pie': {'action': 'edit', 'patch': {
        'name': 'Vinegar pie',
        'notes': 'A Depression-era chess pie made tart with apple-cider vinegar in place of lemon juice — sugar, eggs, butter, flour, and a splash of vinegar baked into a custard.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-sweet-potato-bread': {'action': 'edit', 'patch': {
        'name': 'Sweet potato bread',
        'tags': ['breakfast', 'snack'],
        'notes': 'A spiced quick bread of mashed sweet potato, eggs, oil, and brown sugar — folded with raisins or pecans.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-snowball-cake': {'action': 'edit', 'patch': {
        'name': 'Snowball cake',
        'notes': 'Cubes of yellow cake folded with whipped topping and crushed pineapple, set with gelatin in a bowl, and unmolded covered with shredded coconut.',
        'cuisine': 'American',
    }},
    'corpus-titled-egg-salad': {'action': 'edit', 'patch': {
        'name': 'Egg salad',
        'notes': 'Chopped hard-boiled eggs bound with mayo, mustard, celery, and pickle — served as a sandwich filling or on greens.',
        'cuisine': 'American',
    }},
    'corpus-titled-toll-house-pie': {'action': 'edit', 'patch': {
        'name': 'Toll House pie',
        'notes': 'A pecan-pie-style filling of eggs, butter, sugar, and flour, packed with chocolate chips and pecans — like a giant chocolate chip cookie baked in a pie shell.',
        'cuisine': 'American',
    }},
    'corpus-titled-fried-cabbage': {'action': 'edit', 'patch': {
        'name': 'Fried cabbage',
        'notes': 'Shredded cabbage sautéed in bacon fat with onions and a touch of sugar, finished with crisp bacon — a Southern side.',
        'cuisine': 'Southern',
        'contains_add': ['pork'],
    }},
    'corpus-titled-black-bottom-cupcakes': {'action': 'edit', 'patch': {
        'name': 'Black bottom cupcakes',
        'notes': 'Chocolate cupcake batter topped with a swirl of sweetened cream cheese and chocolate chips — bakes with a cheesecake-like cap.',
        'cuisine': 'American',
        'serving_grams': 80,
    }},
    'corpus-titled-russian-tea-cakes': {'action': 'edit', 'patch': {
        'name': 'Russian tea cakes',
        'notes': 'A butter-and-powdered-sugar shortbread folded with finely chopped pecans, baked into balls and rolled twice in powdered sugar — same as snowball cookies.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-freezer-slaw': {'action': 'edit', 'patch': {
        'name': 'Freezer slaw',
        'notes': 'Shredded cabbage salted to draw out water, then tossed in a sweet vinegar dressing and frozen — keeps crisp for months in the freezer.',
        'cuisine': 'American',
    }},
    'corpus-titled-spaghetti-carbonara': {'action': 'edit', 'patch': {
        'name': 'Spaghetti carbonara',
        'notes': 'Spaghetti tossed off-heat with eggs, grated Pecorino, and crisped guanciale or pancetta — the pasta\'s residual heat sets the egg into a silky sauce.',
        'cuisine': 'Italian',
        'contains_add': ['pork'],
    }},
    'corpus-titled-hot-cheese-dip': {'action': 'edit', 'patch': {
        'name': 'Hot cheese dip',
        'tags': ['snack'],
        'notes': 'Velveeta or processed cheese melted with Rotel-style tomatoes and chiles — served warm with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-ham-balls': {'action': 'edit', 'patch': {
        'name': 'Ham balls',
        'notes': 'Ground ham mixed with ground pork, crackers, milk, and egg, formed into balls and baked in a sweet brown-sugar-and-mustard glaze — Pennsylvania Dutch.',
        'cuisine': 'American',
    }},
    'corpus-titled-crab-quiche': {'action': 'edit', 'patch': {
        'name': 'Crab quiche',
        'notes': 'A pastry shell filled with crab, Swiss cheese, eggs, and cream, baked into a savory custard tart.',
        'cuisine': 'American',
    }},
    'corpus-titled-graham-cracker-cookies': {'action': 'edit', 'patch': {
        'name': 'Graham cracker cookies',
        'notes': 'A no-bake bar of graham crackers topped with a boiled brown-sugar-and-butter caramel, sometimes with chopped nuts.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-chip-bars': {'action': 'edit', 'patch': {
        'name': 'Chocolate chip bars',
        'notes': 'A sheet-pan version of chocolate chip cookies — same dough pressed into a pan and baked, then cut into bars.',
        'cuisine': 'American',
    }},
    'corpus-titled-squash-patties': {'action': 'edit', 'patch': {
        'name': 'Squash patties',
        'notes': 'Grated yellow squash bound with egg, flour, and onion, dropped into oil and pan-fried into golden cakes.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-roast': {'action': 'edit', 'patch': {
        'name': 'Pot roast',
        'notes': 'A tough beef cut (chuck or round) seared, then slow-braised with onions, carrots, and potatoes in seasoned broth until fork-tender.',
        'cuisine': 'American',
    }},
    'corpus-titled-chocolate-cheesecake': {'action': 'edit', 'patch': {
        'name': 'Chocolate cheesecake',
        'notes': 'A baked cream-cheese cheesecake with melted chocolate folded into the batter — dense and chocolaty.',
    }},
    'corpus-titled-creamed-corn': {'action': 'edit', 'patch': {
        'name': 'Creamed corn',
        'notes': 'Sweet corn kernels simmered with butter, cream, milk, and a touch of sugar, thickened slightly with flour — a Southern side.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-spaghetti-and-meatballs': {'action': 'edit', 'patch': {
        'name': 'Spaghetti and meatballs',
        'notes': 'Cooked spaghetti topped with marinara and oven-baked or simmered meatballs of beef, breadcrumbs, egg, and Parmesan.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-tex-mex-dip': {'action': 'edit', 'patch': {
        'name': 'Tex-Mex layered dip',
        'tags': ['snack'],
        'notes': 'A cold layered dip of refried beans, seasoned sour cream, salsa, cheese, lettuce, and olives — served with tortilla chips.',
        'cuisine': 'Tex-Mex',
        'serving_grams': 60,
    }},
    'corpus-titled-cream-cheese-pie': {'action': 'edit', 'patch': {
        'name': 'Cream cheese pie',
        'notes': 'A no-bake or lightly baked pie of sweetened cream cheese in a graham crust, topped with fruit, lemon curd, or cherry pie filling.',
        'cuisine': 'American',
    }},
    'corpus-titled-sweet-potato-balls': {'action': 'edit', 'patch': {
        'name': 'Sweet potato balls',
        'notes': 'Mashed sweet potatoes formed around marshmallows, rolled in crushed cornflakes or coconut, and baked until crisp — a Southern side-as-dessert.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-blueberry-crunch': {'action': 'edit', 'patch': {
        'name': 'Blueberry crunch',
        'tags': ['dessert'],
        'notes': 'Canned blueberry pie filling and crushed pineapple baked under a yellow-cake-mix and butter streusel with pecans — blueberry dump cake.',
        'cuisine': 'American',
    }},
    'corpus-titled-ice-cream-pie': {'action': 'edit', 'patch': {
        'name': 'Ice cream pie',
        'notes': 'Softened ice cream spread into a chocolate-cookie or graham crust and frozen, topped with whipped cream or fudge sauce.',
        'cuisine': 'American',
    }},
    'corpus-titled-blueberry-coffee-cake': {'action': 'edit', 'patch': {
        'name': 'Blueberry coffee cake',
        'tags': ['breakfast', 'dessert'],
        'notes': 'A tender butter cake folded with blueberries and topped with a cinnamon-sugar streusel — served with morning coffee.',
        'cuisine': 'American',
    }},
    'corpus-titled-teriyaki-chicken': {'action': 'edit', 'patch': {
        'name': 'Teriyaki chicken',
        'notes': 'Chicken pieces marinated or glazed in a soy-mirin-sugar sauce, then grilled or pan-cooked until lacquered — served over rice.',
        'cuisine': 'Japanese',
    }},
    'corpus-titled-cheesy-potato-casserole': {'action': 'edit', 'patch': {
        'name': 'Cheesy potato casserole',
        'notes': 'Frozen hash browns baked with sour cream, cream of chicken soup, and shredded cheese under a cornflake or buttered-cracker topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-no-bake-oatmeal-cookies': {'action': 'edit', 'patch': {
        'name': 'No-bake oatmeal cookies',
        'notes': 'Cocoa, sugar, milk, and butter boiled to a fudge, then stirred with peanut butter and oats and dropped onto wax paper to set.',
        'cuisine': 'American',
        'serving_grams': 40,
    }},
    'corpus-titled-s-sugar-cookies': {'action': 'edit', 'patch': {
        'name': 'Sour cream sugar cookies',
        'notes': 'A soft, cake-like sugar cookie made tender by sour cream — rolled and cut or dropped, often frosted with a vanilla glaze.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-cheese-roll': {'action': 'edit', 'patch': {
        'name': 'Cheese roll',
        'tags': ['snack'],
        'notes': 'Cream cheese mixed with cheddar, seasonings, and chiles or pimentos, rolled into a log and coated in chopped pecans or paprika — sliced and served on crackers.',
        'cuisine': 'Southern',
        'serving_grams': 60,
    }},
    'corpus-titled-funnel-cake': {'action': 'edit', 'patch': {
        'name': 'Funnel cake (single)',
        'notes': 'A pancake-like batter drizzled in concentric circles into hot oil, fried crisp, and dusted heavily with powdered sugar — fairground classic.',
        'cuisine': 'American',
    }},
    'corpus-titled-scalloped-tomatoes': {'action': 'edit', 'patch': {
        'name': 'Scalloped tomatoes',
        'notes': 'Sliced or stewed tomatoes layered with bread cubes, butter, sugar, and herbs and baked until bubbly — sweet-savory Southern side.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-salmon-ball': {'action': 'edit', 'patch': {
        'name': 'Salmon ball',
        'tags': ['snack'],
        'notes': 'Canned salmon mixed with cream cheese, lemon, and seasonings, shaped into a ball and rolled in chopped pecans or parsley — served with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-dirt': {'action': 'edit', 'patch': {
        'name': 'Dirt (cookies and cream dessert)',
        'tags': ['dessert'],
        'notes': 'Crushed Oreos layered with whipped cream cheese, butter, vanilla pudding, and whipped topping — a cousin of dirt pudding.',
        'cuisine': 'American',
    }},
    'corpus-titled-avocado-dip': {'action': 'edit', 'patch': {
        'name': 'Avocado dip',
        'tags': ['snack'],
        'notes': 'Mashed avocado mixed with sour cream, lime, jalapeño, and salsa — served chilled with tortilla chips.',
        'cuisine': 'Mexican',
        'serving_grams': 60,
    }},
    'corpus-titled-italian-meat-loaf': {'action': 'edit', 'patch': {
        'name': 'Italian meatloaf',
        'notes': 'A ground-beef loaf with Italian breadcrumbs, Parmesan, herbs, and marinara, baked under mozzarella — meatloaf in lasagna-flavor form.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-refried-beans': {'action': 'edit', 'patch': {
        'name': 'Refried beans',
        'notes': 'Pinto beans simmered then fried with onion and lard or oil, mashed to a creamy paste — a Mexican staple side.',
        'cuisine': 'Mexican',
    }},
    'corpus-titled-pasta-e-fagioli': {'action': 'edit', 'patch': {
        'name': 'Pasta e fagioli',
        'notes': 'A rustic Italian soup of small pasta and beans in a tomato-and-broth base with garlic, herbs, and a Parmesan rind.',
        'cuisine': 'Italian',
    }},
    'corpus-titled-spinach-artichoke-dip': {'action': 'edit', 'patch': {
        'name': 'Spinach artichoke dip',
        'ingredient_categories': ['Leafy greens', 'Other vegetables', 'Fresh cheese', 'Aged cheese', 'Fermented dairy', 'Extracts & essences', 'Peppers & nightshades', 'Salt & seasonings'],
        'tags': ['snack'],
        'notes': 'Chopped spinach and artichoke hearts baked with cream cheese, sour cream, mayo, and Parmesan until bubbling — served hot with bread or chips.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-mango-salsa': {'action': 'edit', 'patch': {
        'name': 'Mango salsa',
        'tags': ['snack', 'condiment'],
        'notes': 'Diced ripe mango, red onion, jalapeño, cilantro, and lime — a fresh sweet-spicy salsa served with grilled fish or tortilla chips.',
        'cuisine': 'Mexican',
        'serving_grams': 60,
    }},
    'corpus-titled-dishpan-cookies': {'action': 'edit', 'patch': {
        'name': 'Dishpan cookies',
        'notes': 'A huge-batch drop cookie of oats, coconut, cornflakes (or Rice Krispies), and chocolate chips — mixed in a dishpan to fit it all.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-creamy-banana-pudding': {'action': 'edit', 'patch': {
        'name': 'Creamy banana pudding',
        'notes': 'Vanilla pudding folded with sweetened condensed milk and whipped topping, layered with sliced bananas and vanilla wafers — the Southern classic.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-fruit-pie': {'action': 'edit', 'patch': {
        'name': 'Fruit pie',
        'notes': 'A generic name for a sweetened fruit filling baked or chilled into a pastry crust — apple, peach, berry, or mixed fruits.',
    }},
    'corpus-titled-chicken-kiev': {'action': 'edit', 'patch': {
        'name': 'Chicken Kiev',
        'notes': 'Pounded chicken breast rolled around an herb-and-garlic butter, breaded, and pan-fried or baked — the butter melts into a sauce when cut.',
        'cuisine': 'Russian',
    }},
    'corpus-titled-french-silk-pie': {'action': 'edit', 'patch': {
        'name': 'French silk pie',
        'notes': 'A chocolate mousse-style pie of butter, sugar, eggs, and melted chocolate whipped until airy, poured into a baked crust and chilled.',
        'cuisine': 'American',
    }},
    'corpus-titled-pickles': {'action': 'drop', 'reason': 'pickled condiment, not a coherent meal'},
    'corpus-titled-baked-oatmeal': {'action': 'edit', 'patch': {
        'name': 'Baked oatmeal',
        'notes': 'Rolled oats combined with milk, eggs, sugar, butter, and cinnamon, baked into a soft cake-like breakfast — served with fruit and cream.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-blueberry-buckle': {'action': 'edit', 'patch': {
        'name': 'Blueberry buckle',
        'tags': ['breakfast', 'dessert'],
        'notes': 'A tender butter cake studded with blueberries and topped with a thick streusel — the streusel "buckles" the cake top as it bakes.',
        'cuisine': 'American',
    }},
    'corpus-titled-impossible-pumpkin-pie': {'action': 'edit', 'patch': {
        'name': 'Impossible pumpkin pie',
        'notes': 'A blender custard of pumpkin, eggs, milk, sugar, and Bisquick — self-crusts as it bakes, no separate pastry shell needed.',
        'cuisine': 'American',
    }},
    'corpus-titled-broccoli-and-rice': {'action': 'edit', 'patch': {
        'name': 'Broccoli and rice',
        'notes': 'Cooked rice tossed or baked with steamed broccoli, butter, cream of mushroom soup, and shredded cheese.',
        'cuisine': 'American',
    }},
    'corpus-titled-divinity-candy': {'action': 'edit', 'patch': {
        'name': 'Divinity candy',
        'notes': 'A fluffy, white, nougat-like confection of hot sugar syrup whipped into stiff egg whites with vanilla and pecans — dropped onto wax paper to set.',
        'cuisine': 'Southern',
        'serving_grams': 40,
    }},
    'corpus-titled-onion-pie': {'action': 'edit', 'patch': {
        'name': 'Onion pie',
        'tags': ['dinner', 'lunch'],
        'notes': 'Sliced sweet onions cooked tender, layered in a pastry crust with cheese and herbs, and baked in an egg-cream custard.',
        'cuisine': 'American',
        'serving_grams': 200,
    }},
    'corpus-titled-ice-cream-dessert': {'action': 'edit', 'patch': {
        'name': 'Ice cream dessert',
        'notes': 'Softened ice cream layered with crushed cookies and chocolate or caramel sauce in a pan, frozen, and cut into squares.',
        'cuisine': 'American',
    }},
    'corpus-titled-cherry-cheesecake': {'action': 'edit', 'patch': {
        'name': 'Cherry cheesecake',
        'notes': 'A baked or no-bake cream-cheese cheesecake topped with canned cherry pie filling on a graham crust.',
        'cuisine': 'American',
    }},
    'corpus-titled-italian-wedding-soup': {'action': 'edit', 'patch': {
        'name': 'Italian wedding soup',
        'notes': 'A clear chicken broth with tiny meatballs, acini di pepe pasta, spinach or escarole, and Parmesan — Italian-American banquet starter.',
        'cuisine': 'Italian-American',
    }},
    'corpus-titled-salsa-verde': {'action': 'edit', 'patch': {
        'name': 'Salsa verde',
        'tags': ['snack', 'condiment'],
        'notes': 'Tomatillos, jalapeños, onion, garlic, cilantro, and lime blended into a tangy green salsa — Mexican style.',
        'cuisine': 'Mexican',
        'serving_grams': 60,
    }},
    'corpus-titled-crab-spread': {'action': 'edit', 'patch': {
        'name': 'Crab spread',
        'tags': ['snack'],
        'notes': 'Cream cheese mixed with lump crab, lemon, Worcestershire, and seasonings — served chilled with crackers.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-blueberry-dessert': {'action': 'edit', 'patch': {
        'name': 'Blueberry dessert',
        'notes': 'A no-bake layered dessert of pecan-shortbread crust, sweetened cream cheese, blueberry pie filling, and whipped topping.',
        'cuisine': 'American',
    }},
    'corpus-titled-corn-muffins': {'action': 'edit', 'patch': {
        'name': 'Corn muffins',
        'tags': ['breakfast', 'dinner'],
        'notes': 'Cornmeal-and-flour muffins of milk, eggs, butter, and sugar — tender and lightly sweet, often served with butter and honey.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-cheese-log': {'action': 'edit', 'patch': {
        'name': 'Cheese log',
        'tags': ['snack'],
        'notes': 'Cream cheese mixed with sharp cheddar and seasonings, shaped into a log and rolled in chopped pecans or parsley — served with crackers.',
        'cuisine': 'Southern',
        'serving_grams': 60,
    }},
    'corpus-titled-mushroom-soup': {'action': 'edit', 'patch': {
        'name': 'Mushroom soup',
        'notes': 'Sautéed mushrooms simmered with onion, chicken broth, and herbs, blended (or partially) and thickened with milk-and-butter roux.',
    }},
    'corpus-titled-lemon-cookies': {'action': 'edit', 'patch': {
        'name': 'Lemon cookies',
        'notes': 'A bright lemon-scented butter cookie made with lemon juice, zest, and sometimes a lemon glaze.',
        'serving_grams': 30,
    }},
    'corpus-titled-stuffed-tomatoes': {'action': 'edit', 'patch': {
        'name': 'Stuffed tomatoes',
        'notes': 'Tomatoes hollowed and filled with seasoned breadcrumbs, herbs, and Parmesan (or tuna salad in cold versions), then baked or chilled.',
        'cuisine': 'Italian',
    }},
    'corpus-titled-cheese-souffle': {'action': 'edit', 'patch': {
        'name': 'Cheese soufflé',
        'notes': 'A bechamel base enriched with grated cheese and yolks, lightened with beaten whites, and baked in a hot oven until puffed and golden.',
        'cuisine': 'French',
    }},
    'corpus-titled-hot-dog-chili': {'action': 'edit', 'patch': {
        'name': 'Hot dog chili sauce',
        'tags': ['condiment'],
        'notes': 'A finely ground beef sauce seasoned with chili powder, paprika, and a touch of vinegar — spooned over hot dogs in Southern coney-style fashion.',
        'cuisine': 'American',
        'serving_grams': 60,
    }},
    'corpus-titled-broccoli-quiche': {'action': 'edit', 'patch': {
        'name': 'Broccoli quiche',
        'notes': 'A pastry shell filled with an egg-and-cream custard, blanched broccoli, and Swiss or cheddar cheese — a meatless quiche variant.',
        'cuisine': 'French',
    }},
    'corpus-titled-gingerbread-cookies': {'action': 'edit', 'patch': {
        'name': 'Gingerbread cookies',
        'notes': 'Rolled spiced cookies of butter, brown sugar, and molasses — cut into shapes (men, houses) and baked crisp, often royal-iced.',
        'cuisine': 'American',
        'serving_grams': 30,
    }},
    'corpus-titled-cabbage-slaw': {'action': 'edit', 'patch': {
        'name': 'Cabbage slaw',
        'notes': 'Shredded cabbage and carrot tossed with a sweet vinegar or mayo dressing — a slimmer name for coleslaw.',
    }},
    'corpus-titled-sunshine-salad': {'action': 'edit', 'patch': {
        'name': 'Sunshine salad',
        'tags': ['dessert'],
        'notes': 'Orange Jello set with crushed pineapple, shredded carrots, and mandarin oranges — a bright molded Southern salad-dessert.',
        'cuisine': 'Southern',
    }},
    'corpus-titled-lemon-dessert': {'action': 'edit', 'patch': {
        'name': 'Lemon dessert',
        'notes': 'A no-bake layered dessert of pecan-shortbread crust, sweetened cream cheese, lemon pudding, and whipped topping — same family as Lemon Lush.',
        'cuisine': 'American',
    }},
    'corpus-titled-mexican-wedding-cookies': {'action': 'edit', 'patch': {
        'name': 'Mexican wedding cookies',
        'notes': 'A butter-shortbread folded with finely ground nuts (almonds or pecans), baked into balls and rolled in powdered sugar — Russian-tea-cake family.',
        'cuisine': 'Mexican',
        'serving_grams': 30,
    }},
    'corpus-titled-tortellini-salad': {'action': 'edit', 'patch': {
        'name': 'Tortellini salad',
        'notes': 'Cooked cheese tortellini tossed with peppers, olives, pepperoni, and Italian dressing — a pasta-salad variant.',
        'cuisine': 'Italian-American',
        'contains_add': ['pork'],
    }},
    'corpus-titled-sliced-baked-potatoes': {'action': 'edit', 'patch': {
        'name': 'Hasselback (sliced baked) potatoes',
        'notes': 'Whole potatoes sliced almost through, drizzled with butter and topped with cheese, baked until the slices fan open and crisp.',
        'cuisine': 'Swedish',
    }},
    'corpus-titled-impossible-coconut-pie': {'action': 'edit', 'patch': {
        'name': 'Impossible coconut pie',
        'notes': 'A blender custard of eggs, milk, sugar, butter, vanilla, coconut, and Bisquick — self-crusts as it bakes; no pastry shell needed.',
        'cuisine': 'American',
    }},
    'corpus-titled-english-trifle': {'action': 'edit', 'patch': {
        'name': 'English trifle',
        'tags': ['dessert'],
        'notes': 'Layered sponge cake soaked in sherry, custard, jam or berries, and whipped cream, assembled in a glass bowl.',
        'cuisine': 'British',
        'contains_add': ['alcohol'],
    }},
    'corpus-titled-chicken-paprikash': {'action': 'edit', 'patch': {
        'name': 'Chicken paprikash',
        'notes': 'Chicken pieces browned and simmered in a sour-cream-and-paprika sauce — served over egg noodles or dumplings.',
        'cuisine': 'Hungarian',
    }},
    'corpus-titled-baked-custard': {'action': 'edit', 'patch': {
        'name': 'Baked custard',
        'notes': 'Eggs, milk, sugar, and vanilla baked in a water bath until just set — silky and nutmeg-dusted.',
    }},
    'corpus-titled-ambrosia-salad': {'action': 'edit', 'patch': {
        'name': 'Ambrosia salad',
        'tags': ['dessert'],
        'notes': 'Mandarin oranges, pineapple, mini marshmallows, shredded coconut, and sour cream or whipped topping — the canonical Southern fruit-salad-dessert.',
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

    print('corpus-titled batch-6 audit applied (entries 751-900 by frequency).')
    print(f'  edited:  {counts["edited"]}')
    print(f'  dropped: {counts["dropped"]} -> {dropped_ids}')
    print(f'  missing-ids: {counts["missing"]}')
    print(f'  total decisions: {len(DECISIONS)}')
    print(f'  remaining meals: {len(data)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
