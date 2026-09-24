#!/usr/bin/env python3
"""One-shot: re-home shirataki into a new low-carb noodle/rice category,
add missing low-carb / high-protein ingredients, and attach search aliases
to common low-carb swaps. Idempotent-ish: re-running appends duplicates, so
run once. Preserves ingredients.json formatting (indent=2, ensure_ascii=True,
no trailing newline)."""
import json
from pathlib import Path

P = Path(__file__).resolve().parent.parent.parent / 'src' / 'data' / 'ingredients.json'
data = json.load(P.open(encoding='utf-8'))
byid = {i['id']: i for i in data}

CAT = 'Noodle & rice alternatives'
PP = 'Protein powders'

# 1) Re-home shirataki + aliases
s = byid['shirataki']
s['category'] = CAT
s['subcategory'] = 'Shirataki'
s['aliases'] = ["konjac noodles", "miracle noodle", "glucomannan noodles", "keto noodles"]

ORDER = ['id', 'name', 'category', 'subcategory', 'food_group', 'contains',
         'group_weights', 'examples', 'aliases', 'calories', 'carbs', 'protein',
         'fiber', 'fat', 'sodium', 'sugar', 'saturated_fat', 'notes', 'tags',
         'serving_grams', 'iron']


def ing(**k):
    return {f: k[f] for f in ORDER if f in k}


new = [
    ing(id='konjac-rice', name='Konjac rice', category=CAT, subcategory='Konjac rice',
        food_group='Grains', contains=[], group_weights=[0, 1, 0],
        examples=['keto fried rice', 'poke bowls', 'rice substitute'],
        aliases=['shirataki rice', 'miracle rice', 'konjac yam rice'],
        calories=10, carbs=4.0, protein=0.4, fiber=3.0, fat=0.1, sodium=10, sugar=0,
        saturated_fat=0, notes='Konjac-yam rice; near-zero calorie low-carb rice swap.',
        tags=['low-cal'], serving_grams=115, iron=0.5),
    ing(id='kelp-noodles', name='Kelp noodles', category=CAT, subcategory='Kelp noodles',
        food_group='Grains', contains=[], group_weights=[0, 1, 0],
        examples=['raw pad thai', 'cold noodle salads', 'low-carb stir-fry'],
        aliases=['seaweed noodles', 'kelp pasta'],
        calories=6, carbs=1.0, protein=0.0, fiber=0.4, fat=0.0, sodium=140, sugar=0,
        saturated_fat=0, notes='Clear noodles of kelp and sodium alginate; crunchy, near-zero calorie.',
        tags=['low-cal'], serving_grams=115, iron=0.3),
    ing(id='hearts-of-palm-pasta', name='Hearts of palm pasta', category=CAT,
        subcategory='Hearts of palm pasta', food_group='Grains', contains=[],
        group_weights=[0, 1, 0], examples=['low-carb spaghetti', 'linguine alfredo', 'pasta salad'],
        aliases=['palmini', 'palm pasta', 'hearts of palm noodles'],
        calories=25, carbs=5.0, protein=1.5, fiber=3.0, fat=0.5, sodium=200, sugar=0,
        saturated_fat=0, notes='Hearts-of-palm cut into noodle shapes; low-carb, high-fiber pasta swap.',
        tags=['low-cal', 'high-fiber'], serving_grams=115, iron=0.6),
    ing(id='tofu-shirataki', name='Tofu shirataki noodles', category=CAT, subcategory='Shirataki',
        food_group='Grains', contains=['soy'], group_weights=[0, 1, 0],
        examples=['low-carb ramen', 'fettuccine alfredo', 'noodle stir-fry'],
        aliases=['konjac tofu noodles', 'house foods shirataki'],
        calories=15, carbs=3.0, protein=1.0, fiber=2.0, fat=0.5, sodium=15, sugar=0,
        saturated_fat=0, notes='Konjac noodles blended with tofu; slightly more body than plain shirataki.',
        tags=['low-cal'], serving_grams=115, iron=0.4),
    ing(id='whey-protein-powder', name='Whey protein powder', category=PP, subcategory='Whey protein',
        food_group='Dairy', contains=['dairy'], group_weights=[0, 0, 1],
        examples=['protein shakes', 'smoothies', 'protein pancakes'],
        aliases=['whey isolate', 'wpi', 'protein powder'],
        calories=370, carbs=8, protein=80, fiber=0, fat=6, sodium=300, sugar=5,
        saturated_fat=3, notes='Dried whey isolate/concentrate; about 80% protein by weight.',
        tags=['high-protein'], serving_grams=32, iron=1.5),
    ing(id='casein-protein-powder', name='Casein protein powder', category=PP, subcategory='Casein protein',
        food_group='Dairy', contains=['dairy'], group_weights=[0, 0, 1],
        examples=['bedtime shakes', 'protein mousse', 'overnight pudding'],
        aliases=['micellar casein', 'protein powder'],
        calories=360, carbs=7, protein=78, fiber=1, fat=2, sodium=350, sugar=4,
        saturated_fat=1, notes='Slow-digesting milk protein; about 78% protein by weight.',
        tags=['high-protein'], serving_grams=32, iron=1.0),
    ing(id='pea-protein-powder', name='Pea protein powder', category=PP, subcategory='Pea protein',
        food_group='Protein (plant)', contains=[], group_weights=[0, 1, 0],
        examples=['vegan shakes', 'smoothies', 'plant protein bars'],
        aliases=['vegan protein powder', 'plant protein powder', 'protein powder'],
        calories=380, carbs=7, protein=80, fiber=6, fat=6, sodium=400, sugar=1,
        saturated_fat=1, notes='Isolated yellow-pea protein; about 80% protein, soy- and dairy-free.',
        tags=['high-protein', 'high-fiber'], serving_grams=32, iron=6.0),
    ing(id='pork-rinds', name='Pork rinds (chicharron)', category='Processed meat',
        subcategory='Fried pork skin', food_group='Protein (animal)', contains=['meat', 'pork'],
        group_weights=[1, 0, 0], examples=['keto snack', 'breading crumb', 'nacho base'],
        aliases=['chicharron', 'chicharrones', 'pork scratchings', 'pork cracklings'],
        calories=545, carbs=0, protein=61, fiber=0, fat=31, sodium=1700, sugar=0,
        saturated_fat=11, notes='Puffed fried pork skin; zero-carb, high-protein crunchy snack and breading.',
        tags=['high-protein', 'snack'], serving_grams=28, iron=1.2),
    ing(id='psyllium-husk', name='Psyllium husk', category='Seeds', subcategory='Psyllium',
        food_group='Nuts & seeds', contains=[], group_weights=[0, 1, 0],
        examples=['keto bread binder', 'fiber supplement', 'low-carb tortillas'],
        aliases=['psyllium', 'ispaghula', 'isabgol'],
        calories=200, carbs=85, protein=2, fiber=80, fat=0.5, sodium=35, sugar=0,
        saturated_fat=0, notes='Soluble-fiber seed husk; mostly fiber (net carbs near zero), gels for keto baking.',
        tags=['high-fiber'], serving_grams=5, iron=1.5),
]
data.extend(new)

# 2) Aliases on existing low-carb swaps + seaweed
add_alias = {
    'cauliflower': ['cauliflower rice', 'riced cauliflower', 'cauliflower steak'],
    'zucchini': ['zoodles', 'zucchini noodles', 'courgette'],
    'spaghetti-squash': ['spaghetti squash noodles'],
    'kombu': ['kelp', 'dried kelp'],
    'egg-white': ['egg whites', 'liquid egg whites'],
}
for k, al in add_alias.items():
    if k in byid:
        byid[k]['aliases'] = al

P.open('w', encoding='utf-8').write(json.dumps(data, indent=2, ensure_ascii=True))

print('total ingredients now:', len(data))
print('new ids:', [n['id'] for n in new])
print('Noodle & rice alternatives members:', [i['id'] for i in data if i['category'] == CAT])
print('Protein powders members:', [i['id'] for i in data if i['category'] == PP])
