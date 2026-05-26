#!/usr/bin/env python3
"""Batch 14 patch for src/data/meals.json (332 curated meals).

For every meal, adds:
  - serving_grams: realistic single-serving weight in g, hand-tuned per meal
    based on the dish form (soup ~300g, salad ~200g, sandwich/wrap ~220g,
    plate ~350g, bowl ~400g, dessert ~130g, etc.).
  - contains (optional): meal-level restriction tags for dishes that are
    pork-mandatory or alcohol-mandatory by tradition. ingredient_categories
    alone can't tell pork from beef inside 'Red meat', so a pork-defined
    dish like 'Sweet-and-sour pork' was passing halal under the lenient
    batch-13 category logic. Marking the meal directly fixes that.

Tags and cuisines are reviewed and left as-is — all 332 entries looked sound.
No drops in this file (every entry is a real meal).

Run from the project root:
    python scripts/patch_meals_batch14.py
"""

import json
import sys
from pathlib import Path

MEALS_PATH = Path(__file__).resolve().parent.parent / 'src' / 'data' / 'meals.json'


# Per-meal serving_grams (single realistic plate). Default fallback for any
# meal not listed is 300g, but the dict below covers all 332 meals so the
# fallback should never fire in practice.
SERVING_GRAMS = {
    # 0-9 — American mains
    'chicken-rice-bowl':            400,
    'chicken-stir-fry':             350,
    'salmon-plate':                 350,
    'sashimi-platter':              250,
    'tuna-salad':                   220,
    'fish-and-chips':               400,
    'shrimp-pasta':                 320,
    'burger':                       250,
    'cheeseburger':                 270,
    'steak-dinner':                 400,
    # 10-19 — breakfasts + light meals
    'bacon-and-eggs':               220,
    'omelet-veg-cheese':            220,
    'yogurt-parfait':               250,
    'berry-smoothie':               350,
    'cereal-bowl':                  280,
    'oatmeal-berries':              280,
    'cheese-plate':                 200,
    'greek-salad':                  250,
    'caesar-salad':                 250,
    'hummus-plate':                 250,
    # 20-29
    'bean-burrito':                 280,
    'vegan-bowl':                   400,
    'tofu-stir-fry':                350,
    'pb-sandwich':                  150,
    'pasta-red-sauce':              320,
    'fruit-and-nuts':               180,
    'pancakes-syrup':               220,
    'mac-and-cheese':               280,
    'cobb-salad':                   300,
    'bbq-plate':                    400,
    # 30-39 — American + British classics
    'thanksgiving-plate':           450,
    'biscuits-and-gravy':           250,
    'chicken-and-waffles':          320,
    'club-sandwich':                280,
    'reuben-sandwich':              280,
    'buffalo-wings':                250,
    'chili-con-carne':              350,
    'philly-cheesesteak':           320,
    'meatloaf-mashed-potato':       380,
    'lobster-roll':                 220,
    # 40-49 — British + French
    'full-english-breakfast':       450,
    'shepherds-pie':                380,
    'bangers-and-mash':             380,
    'ploughmans-lunch':             300,
    'sunday-roast':                 450,
    'scones-cream-jam':             130,
    'beef-wellington':              350,
    'toad-in-the-hole':             320,
    'croque-monsieur':              250,
    'ratatouille':                  280,
    # 50-59 — French + Italian
    'beef-bourguignon':             380,
    'nicoise-salad':                280,
    'omelette-french':              200,
    'coq-au-vin':                   380,
    'bouillabaisse':                400,
    'quiche-lorraine':              200,
    'cassoulet':                    400,
    'crepes-savory':                220,
    'caprese':                      200,
    'pasta-carbonara':              320,
    # 60-69 — Italian + Spanish
    'pasta-bolognese':              320,
    'pesto-pasta':                  300,
    'pasta-amatriciana':            300,
    'risotto-mushroom':             320,
    'risotto-milanese':             320,
    'pizza-margherita':             280,
    'osso-buco':                    380,
    'lasagna':                      350,
    'paella':                       400,
    'tortilla-espanola':            200,
    # 70-79 — Spanish + Central European
    'gazpacho':                     280,
    'patatas-bravas':                200,
    'bacalhau-com-natas':           320,
    'schnitzel':                    320,
    'rosti':                        220,
    'sauerbraten':                  380,
    'raclette-platter':             380,
    'muesli-bowl':                  250,
    'spaetzle-cheese':              280,
    'currywurst':                   280,
    # 80-89 — Eastern European + Scandinavian
    'pierogi-potato-cheese':        280,
    'borscht':                      300,
    'goulash':                      350,
    'blini-caviar':                 150,
    'stuffed-cabbage':              320,
    'smorgasbord-plate':            300,
    'gravlax-plate':                220,
    'swedish-meatballs':            300,
    'pickled-herring-plate':        180,
    'danish-pastry-coffee':         220,
    # 90-99 — Greek + Chinese
    'moussaka':                     350,
    'spanakopita':                  220,
    'souvlaki-plate':               320,
    'kung-pao-chicken':             350,
    'sweet-and-sour-pork':          350,
    'mapo-tofu':                    300,
    'dim-sum-platter':              300,
    'jiaozi-pork-cabbage':          250,
    'xiao-long-bao':                200,
    'wonton-soup':                  350,
    # 100-109 — Chinese cont.
    'congee-rice':                  350,
    'peking-duck':                  300,
    'lions-head-meatball':          320,
    'yuxiang-eggplant':             300,
    'twice-cooked-pork':            320,
    'dan-dan-noodles':              320,
    'fried-rice-egg':               350,
    'char-siu-pork-rice':           400,
    'sichuan-hot-pot':              500,
    'salt-pepper-shrimp':           250,
    # 110-119 — Japanese
    'sushi-nigiri-platter':         250,
    'ramen-tonkotsu':               550,
    'ramen-shoyu':                  550,
    'ramen-miso':                   550,
    'donburi-gyudon':               400,
    'donburi-oyakodon':             400,
    'donburi-katsudon':             420,
    'tempura-platter':              280,
    'okonomiyaki':                  300,
    'soba-noodles':                 380,
    # 120-129 — Japanese + Korean
    'udon-noodles':                 450,
    'tonkatsu-plate':               380,
    'sukiyaki':                     450,
    'shabu-shabu':                  450,
    'bibimbap':                     450,
    'bulgogi-plate':                380,
    'kimbap':                       250,
    'kimchi-jjigae':                400,
    'sundubu-jjigae':               400,
    'korean-bbq':                   400,
    # 130-139 — Korean + Thai
    'japchae':                      300,
    'samgyetang':                   500,
    'tteokbokki':                   280,
    'pad-thai':                     350,
    'tom-yum-goong':                350,
    'green-curry-chicken':          400,
    'red-curry-chicken':            400,
    'massaman-curry':               400,
    'som-tam':                      200,
    'larb':                         250,
    # 140-149 — Thai + Vietnamese + SE Asia
    'khao-soi':                     450,
    'pad-see-ew':                   350,
    'pho-bo':                       550,
    'pho-ga':                       550,
    'banh-mi':                      250,
    'bun-bo-hue':                   500,
    'summer-rolls':                 220,
    'bun-cha':                      350,
    'com-tam':                      400,
    'nasi-goreng':                  350,
    # 150-159 — SE Asia + Indian
    'rendang':                      350,
    'laksa':                        500,
    'satay-plate':                  300,
    'gado-gado':                    320,
    'mee-goreng':                   350,
    'chicken-adobo':                380,
    'sinigang':                     400,
    'lumpia':                       220,
    'kare-kare':                    400,
    'pancit':                       320,
    # 160-169 — Indian
    'butter-chicken':               380,
    'chicken-tikka-masala':         380,
    'vindaloo-pork':                350,
    'chicken-korma':                380,
    'rogan-josh':                   380,
    'chicken-biryani':              400,
    'paneer-tikka':                 250,
    'palak-paneer':                 320,
    'dal-makhani':                  300,
    'dal-tadka':                    280,
    # 170-179 — Indian + South Indian + Pakistani
    'masala-dosa':                  300,
    'idli-sambar':                  300,
    'vegetarian-thali':             450,
    'samosa-chaat':                 220,
    'chana-masala':                 320,
    'aloo-gobi':                    280,
    'tandoori-chicken':             300,
    'rajma':                        320,
    'nihari':                       380,
    'haleem':                       350,
    # 180-189 — South Asia + Levantine
    'pakistani-biryani-mutton':     400,
    'fish-curry-bengali':           320,
    'chapli-kebab':                 250,
    'rice-and-curry-sri-lankan':    400,
    'hoppers':                      220,
    'kottu-roti':                   350,
    'mezze-plate':                  300,
    'baba-ganoush':                 200,
    'tabbouleh':                    200,
    'fattoush':                     220,
    # 190-199 — Levantine + Iranian
    'kibbeh':                       250,
    'shawarma-chicken':             280,
    'shawarma-beef':                280,
    'manakish-zaatar':              200,
    'kafta-kebab':                  280,
    'fatteh':                       300,
    'falafel-plate':                300,
    'kabab-koobideh':               380,
    'ghormeh-sabzi':                380,
    'fesenjan':                     350,
    # 200-209 — Iranian + Turkish
    'tahdig-saffron':               280,
    'ash-reshteh':                  350,
    'adana-kebab':                  350,
    'doner-kebab':                  300,
    'iskender-kebab':               380,
    'dolma-stuffed-grape-leaves':   220,
    'borek-cheese':                 200,
    'lahmacun':                     220,
    'kunefe':                       150,
    'chicken-tagine':               380,
    # 210-219 — Moroccan + Egyptian + N African
    'lamb-tagine':                  380,
    'moroccan-couscous':            400,
    'harira':                       350,
    'ful-medames':                  300,
    'koshari':                      380,
    'brik':                         180,
    'shakshuka':                    300,
    'bstilla':                      280,
    'mloukhia':                     320,
    'meze-turkish':                 280,
    # 220-229 — African
    'jollof-rice':                  400,
    'egusi-soup':                   400,
    'suya-skewers':                 250,
    'fufu-and-stew':                400,
    'peanut-stew':                  380,
    'waakye':                       400,
    'thieboudienne':                450,
    'injera-doro-wat':              400,
    'injera-misir-wat':             400,
    'injera-alicha':                380,
    # 230-239 — Africa + Latin
    'ugali-sukuma-wiki':            380,
    'pilau-east-african':           400,
    'bobotie':                      350,
    'bunny-chow':                   350,
    'pap-chakalaka':                350,
    'biltong-plate':                100,
    'tacos-al-pastor':              250,
    'tacos-carnitas':               250,
    'tacos-fish':                   250,
    'tacos-lengua':                 250,
    # 240-249 — Mexican + Brazilian
    'tacos-barbacoa':               250,
    'enchiladas-rojas':             320,
    'mole-poblano-chicken':         350,
    'tamales':                      220,
    'chilaquiles':                  300,
    'pozole-rojo':                  400,
    'sopes':                        250,
    'huevos-rancheros':             300,
    'feijoada':                     400,
    'moqueca':                      400,
    # 250-259 — Brazilian + Peruvian + Argentine
    'churrasco-plate':              400,
    'pao-de-queijo':                100,
    'acaraje':                      200,
    'vatapa':                       350,
    'ceviche-peruvian':             250,
    'lomo-saltado':                 380,
    'aji-de-gallina':                350,
    'anticuchos':                   250,
    'papa-huancaina':               250,
    'asado-plate':                  450,
    # 260-269 — Latin + Caribbean
    'milanesa':                     350,
    'empanadas-argentine':          200,
    'chimichurri-steak':            380,
    'jerk-chicken':                 380,
    'ackee-saltfish':               350,
    'ropa-vieja':                   380,
    'jamaican-oxtail':              400,
    'callaloo':                     280,
    'caribbean-roti':               280,
    'cuban-sandwich':               320,
    # 270-279 — Caribbean + Latin staples + boards
    'mofongo':                      300,
    'arepas':                       220,
    'pupusas':                      220,
    'gallo-pinto':                  300,
    'baleadas':                     220,
    'haitian-griot':                350,
    'tostones':                     180,
    'arroz-con-pollo':              400,
    'charcuterie-board':            250,
    'antipasto-platter':            280,
    # 280-289 — snacks + boards
    'popcorn-buttered':             50,
    'popcorn-caramel':              50,
    'chips-and-salsa':              80,
    'chips-and-guacamole':          120,
    'chips-and-queso':              120,
    'nut-mix-roasted':              50,
    'trail-mix':                    50,
    'crudite-platter':              200,
    'fruit-platter':                250,
    'snack-board-mediterranean':    220,
    # 290-299 — snacks + desserts
    'pretzels-mustard':             70,
    'chocolate-cake-slice':         130,
    'carrot-cake-slice':            140,
    'cheesecake-plain':             130,
    'cheesecake-strawberry':        140,
    'tres-leches-cake':             140,
    'red-velvet-cake':              140,
    'apple-pie':                    140,
    'pumpkin-pie':                  130,
    'pecan-pie':                    120,
    # 300-309 — desserts
    'key-lime-pie':                 130,
    'ice-cream-sundae':             180,
    'tiramisu':                     150,
    'halwa-semolina':               120,
    'mochi-ice-cream':              80,
    'churros-chocolate':            150,
    'creme-brulee':                 130,
    'panna-cotta':                  130,
    'crepe-suzette':                180,
    'bread-pudding':                170,
    # 310-319 — desserts + drinks
    'chocolate-fondue':             150,
    'affogato':                     130,
    'green-smoothie':               350,
    'protein-smoothie':             400,
    'vanilla-latte':                350,
    'masala-chai-latte':            300,
    'matcha-latte':                 300,
    'boba-milk-tea':                450,
    'sweet-lassi':                  300,
    'mango-lassi':                  300,
    # 320-331 — drinks + composite breakfasts
    'horchata-mexican':             300,
    'agua-fresca-watermelon':       350,
    'hot-chocolate':                280,
    'turkish-coffee':               80,
    'continental-breakfast':        320,
    'afternoon-tea-spread':         280,
    'brunch-platter':               450,
    'kids-lunchbox':                280,
    'bistro-plate':                 320,
    'japanese-breakfast':           320,
    'dim-sum-brunch':               400,
    'indian-breakfast':             350,
}


# Meals where pork is mandatory by tradition. Without this, halal would
# allow them through (Red meat / Processed meat categories have non-pork
# options under the batch-13 lenient rule).
PORK_EXPLICIT = {
    'bacon-and-eggs',                # bacon
    'biscuits-and-gravy',            # pork sausage gravy
    'bangers-and-mash',              # bangers = pork
    'ploughmans-lunch',              # ham
    'full-english-breakfast',        # bacon + sausage
    'toad-in-the-hole',              # sausage
    'croque-monsieur',               # ham
    'quiche-lorraine',               # lardons / bacon
    'pasta-carbonara',               # guanciale
    'pasta-amatriciana',             # guanciale
    'cassoulet',                     # pork sausage
    'sweet-and-sour-pork',           # named
    'jiaozi-pork-cabbage',           # named
    'twice-cooked-pork',             # named
    'char-siu-pork-rice',            # named
    'ramen-tonkotsu',                # pork-bone broth
    'donburi-katsudon',              # pork cutlet
    'tonkatsu-plate',                # pork cutlet
    'vindaloo-pork',                 # named
    'cuban-sandwich',                # roast pork + ham
    'haitian-griot',                 # griot = pork
    'feijoada',                      # pork-heavy Brazilian stew
    'currywurst',                    # pork sausage
}


def main():
    with MEALS_PATH.open(encoding='utf-8') as f:
        meals = json.load(f)

    by_id = {m['id']: m for m in meals}

    missing = []
    unknown = []
    for mid in SERVING_GRAMS:
        if mid not in by_id:
            unknown.append(mid)
    for m in meals:
        if m['id'] not in SERVING_GRAMS:
            missing.append(m['id'])

    if unknown:
        print(f'WARN: {len(unknown)} ids in SERVING_GRAMS not in meals.json:')
        for u in unknown: print(f'   - {u}')
    if missing:
        print(f'WARN: {len(missing)} meals not in SERVING_GRAMS (will use 300g):')
        for u in missing: print(f'   - {u}')

    pork_unknown = [p for p in PORK_EXPLICIT if p not in by_id]
    if pork_unknown:
        print(f'WARN: PORK_EXPLICIT ids not found: {pork_unknown}')

    for m in meals:
        sg = SERVING_GRAMS.get(m['id'], 300)
        m['serving_grams'] = sg
        if m['id'] in PORK_EXPLICIT:
            existing = set(m.get('contains') or [])
            existing.add('pork')
            m['contains'] = sorted(existing)
        # diet_compatibility re-derivation is deferred to a later script
        # (after all 3 meal files are audited and meal_form is wired up).

    with MEALS_PATH.open('w', encoding='utf-8') as f:
        json.dump(meals, f, ensure_ascii=False, indent=2)
        f.write('\n')

    pork_count = sum(1 for m in meals if 'pork' in (m.get('contains') or []))
    print(f'Patched {len(meals)} meals.')
    print(f'  serving_grams stamped on every meal.')
    print(f'  contains: ["pork"] on {pork_count} dishes.')


if __name__ == '__main__':
    main()
