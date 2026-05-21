# Meal audit — conflicts with prior project decisions

This document captures places where the audit's findings (derived from
my own culinary knowledge and the RecipeNLG corpus alone) contradict
decisions already encoded in the project. The user asked the audit to
proceed independently of project decisions and to surface conflicts.

## 1. Compositional meal categories were noise-padded

**Project decision (Phase 36 / `scripts/extract_meal_patterns.py` /
`scripts/rename_compositional_meals.py`):** compositional meals are
"exact category-set patterns" extracted from the corpus. Each entry's
`ingredient_categories` is the literal set of categories the source
recipes happened to use. Names were assigned by stripping a NOISE list
(sugar, salt, oils, spices, baking ingredients, extracts, herbs,
sauces, margarine, prepared mixes) and looking up the residue in a
hand-written `SHAPE_TO_NAMES` table.

**Audit finding:** that pipeline preserves noise in the stored
categories even when the name implies the dish doesn't contain it. The
visible effect:

- "Compound butter" was `[Cream & butter, Sugar & sweeteners]`. In
  culinary practice compound butter is butter blended with herbs /
  garlic / citrus — never sugar.
- "Brown butter sauce" carried sugar for the same reason.
- "Glass of milk" / "Warm milk" carried sugar.
- "Béchamel base" / "Cream sauce" carried sugar. Béchamel is a roux +
  milk; no sugar.
- "Scrambled eggs" / "Fried eggs" / "Hard-boiled eggs" / "Omelet" all
  carried sugar and extracts.
- "Roux" carried sugar.
- Plain produce items ("Sliced apples", "Mixed berries", "Cheese
  plate", "Roasted vegetables", etc.) carried sugar.
- "Fruit cocktail" was tagged Alcoholic beverages — fruit cocktail is
  canned mixed fruit in syrup, not a drink.

**Resolution:** I (a) replaced categories from the corpus distribution
for meals with ≥20 corpus matches, and (b) hand-stripped sugar / sauces
/ extracts from the items listed above. See
`scripts/strip_compositional_sugar.py` for the substring list.

## 2. Compositional shape-to-name aliasing produced duplicate dots

**Project decision (`SHAPE_TO_NAMES` in
`scripts/rename_compositional_meals.py`):** a single category-set is
mapped to up to ~6 candidate dish names. Each emerges as its own meal
entry sharing the same `ingredient_categories`.

**Audit finding:** same category-set ⇒ same plotted position and same
computed nutrition. The 3D view rendered 2-5 dots on top of each other
labelled with different names. Examples that collapsed to one signature:

- {Cream & butter, Sugar & sweeteners}: Compound butter, Brown butter
  sauce
- {Eggs, Extracts & essences, Sugar & sweeteners}: Omelet, Scrambled
  eggs, Fried eggs, Hard-boiled eggs (also broken by issue #1)
- {Alcoholic beverages, Temperate fruits}: Sangria, Mulled apple wine,
  Fruit cocktail
- {Baking ingredients, Cream & butter, Eggs, Extracts, Flours,
  Salt & seasonings, Sugar & sweeteners}: Pound cake, Shortbread
  cookies, Pastry dough, Pie crust (4 different dishes, identical
  position!)

**Resolution:** deduped 93 entries (790 → 697). For each colliding
signature, the highest-frequency name wins; the others' frequencies
sum into it.

## 3. Corpus-titled categories were inferred from a 3-NER sample

**Project decision (`scripts/find_uncovered_corpus_meals.py`):** for
each canonical title, the script kept up to 3 NER ingredient bags and
mapped each NER token to a category via a small keyword table. The
resulting category set became the meal's `ingredient_categories`.

**Audit finding:** a 3-recipe sample of a title that appears in
thousands of recipes is too thin to characterise the dish. The
hand-tuned keyword table also missed many ingredients. Concrete
examples (categories that should be present, % of corpus recipes
containing them):

| Meal | Stored before | Corpus says missing |
|---|---|---|
| Lemon Bread (220 corpus matches) | Citrus, Oils, Seeds, Eggs, Prepared mixes, Extracts, Bread & rolls | Flours (85%), Sugar (85%), Baking (81%), Milk (78%), Salt (76%) |
| Crazy Cake (180) | Nuts, Tropical fruits, Cream & butter, Prepared mixes | Sugar (94%), Flours (89%), Baking (87%), Extracts (85%), Oils (81%) |
| English Muffins (96) | Aged cheese, Spice blends, Pickled veg, Bread & rolls | Flours (96%), Baking (92%), Salt (91%), Sugar (85%) |
| Ginger Cookies (198) | Ground spices, Milk, Salt, Temperate fruits | Sugar (99%), Flours (98%), Baking (91%), Eggs (86%) |
| German Chocolate Cake (262) | Sugar, Oils, Candy & desserts | Eggs (81%), Extracts (71%), Flours (65%), Baking (63%) |
| Caramel Pecan Pie (51) | Candy & desserts, Nuts, Tropical fruits, Milk, Fresh cheese | Sugar (96%), Eggs (86%), Extracts (78%), Salt (63%) |

**Resolution:** for every corpus-titled meal with ≥20 corpus matches
(all 2659 of them — corpus matches were guaranteed), I rebuilt
`ingredient_categories` from the actual corpus distribution using a
≥30% threshold. 2620 of 2659 entries got fresh categories.

## 4. Curated meals were intentionally minimal, but that made nutrition wrong

**Project decision (implicit in the hand-curated meals.json):** each
curated meal lists a small set of "essential" categories — the dish
concept rather than the full ingredient list. Salt, oils, spices,
extracts, and supporting vegetables are omitted by design.

**Audit finding:** the project's `aggregateMeals` function (see
`src/core/aggregations.js`) computes per-100g and per-serving
nutrition by adding one typical serving of EACH listed category. With
the minimal category list, the per-100g profile is overweighted by the
small number of categories listed. E.g.:

- **Bobotie** stored as `[Red meat, Eggs, Dried fruits, Ground
  spices]`. Corpus matches in 30/30 recipes include onions, bread
  crumbs, milk, peppers, herbs. A bobotie computed without bread,
  milk, or onion is roughly 50 % meat by weight — far from a real
  serving.
- **Beef bourguignon** stored as `[Red meat, Mushrooms, Other veg,
  Alcoholic beverages]`. Corpus has 109 matches; fresh herbs (86%),
  flour (77%), peppers (77%), salt (61%), starchy veg (58%), cream &
  butter (38%), processed meat / bacon (56%) all missing.
- **Bibimbap** stored as `[Refined grains, Red meat, Eggs, Other veg,
  Pastes & ferments]`. Corpus has 22 matches; oils (96%), sauces
  (86%), starchy veg / sweet potato (77%), seeds / sesame (68%),
  peppers (59%), mushrooms (55%) all missing.

**Resolution:** for curated meals with ≥20 corpus matches, replaced
the categories with corpus-derived (≥40% threshold) — looser than the
30% used for corpus-titled because curated meals are a less noisy
starting point. 108 curated meals got updated; the remainder
(low-corpus-confidence) retained their original categories. This
conflicts with the project's "dish concept" design, but matches the
user's stated goal of accurate nutrition.

## 5. Cakes were tagged as `Bread & rolls`

**Project decision (3 entries in meals.json):**

- Carrot cake → `[Bread & rolls, Starchy vegetables, Cream & butter, Nuts]`
- Red velvet cake → `[Bread & rolls, Cream & butter, Sugar & sweeteners, Fresh cheese]`
- Tres leches cake → `[Bread & rolls, Milk, Cream & butter, Sugar & sweeteners]`

**Audit finding:** none of these are bread. The corpus distribution
shows zero "Bread & rolls" occurrences across hundreds of matching
recipes. The dishes are baked desserts; they should plot in the
sweet/baked region, not the bread region. Putting a cake in the bread
bucket also distorts the additive RGB color blend (the meal centroid
inherits Grains hue weights instead of Sweets).

**Resolution:** hand-fixed all three (and `Crêpes Suzette`, which had
the same issue) with corpus-validated category lists.

## 6. Greek salad had `Aged cheese` instead of `Fresh cheese`

**Project decision (meals.json):** Greek salad → `[..., Aged cheese,
...]`. Feta was apparently treated as an aged cheese in this entry.

**Audit finding:** the project's own `ingredients.json` classifies
feta under `Fresh cheese` (along with mozzarella, ricotta, cottage
cheese, queso fresco — all brined / fresh styles). The audit corpus
confirms: 77 % of "Greek salad" corpus recipes carry the Fresh cheese
subcategory tag (driven by feta), 4 % carry Aged cheese.

**Resolution:** swapped to `Fresh cheese`.

## 7. Duplicate "Berry smoothie" entry

**Project decision (meals.json):** two separate entries both named
"Berry smoothie" with different ids (`smoothie` and `berry-smoothie`)
and different category lists.

**Audit finding:** name lookup in the UI is ambiguous; both plot under
the same label. The shorter / older entry (`smoothie`) doesn't match
the newer dataset's id-naming convention.

**Resolution:** merged into a single entry with id `berry-smoothie`
and corpus-derived categories.

## 8. CSV taxonomy uses "Fruits" — project remap is lossy

**Project decision (`CSV_TO_CURRENT_CATEGORY` in extract scripts):**
the old taxonomy CSV's coarse `"Fruits"` category is mapped to
`"Temperate fruits"` for backfill purposes.

**Audit finding:** that lumps banana, mango, pineapple, coconut into
the Temperate bucket, when they're actually Tropical. Banana Bread's
corpus distribution would have shown 98 % "Temperate fruits" presence
with that remap (i.e. wrong), instead of the correct 98 % "Tropical
fruits".

**Resolution:** my audit uses the CSV's `subcategories` column
(Apple / Banana / Pear / Tropical / Strawberry / Blueberry / etc.) and
maps each subcategory directly to the current taxonomy via
`scripts/audit_subcategory_map.py`. This preserves the fruit-class
distinction. I did NOT touch the existing `CSV_TO_CURRENT_CATEGORY`
remap — other scripts still rely on it — but I avoided it for any
audit-driven rebuilds.

## 9. Pass 1's 40% threshold dropped some definitionally required categories

**Pass 1 decision (`scripts/fix_curated_meals.py`):** curated meals
with ≥20 corpus matches got their `ingredient_categories` replaced by
the corpus-derived set at a ≥40% threshold.

**Pass 2 finding:** a few defining ingredients land just below 40% in
the corpus because of recipe-listing quirks rather than because the
dish doesn't contain them. The threshold filtered them out anyway.
Concrete cases (corpus % shown):

| Meal | Category dropped | Corpus % | Why it belongs |
|---|---|---|---|
| Burger | Bread & rolls | 32 | A burger by definition is in a bun. |
| Pesto pasta | Nuts | 25 | Pine nuts are defining in pesto; corpus underweights them when recipes use jarred "pesto" as a single NER token. |
| Wonton soup | Prepared soups & broths | <30 | It is literally a soup; corpus tags water+bouillon, not "broth". |
| Caramel popcorn | Whole grains | 38 | Popcorn IS the substrate — without it, this is just caramel. |
| Biscuits and gravy | Processed meat | 38 | Sausage gravy is defining; the 38% Processed + 38% Red meat split underweights the meat. |
| Pierogi (potato-cheese) | Starchy vegetables, Fresh cheese | 35, 21 | The name explicitly states the filling. |
| Swedish meatballs | Cream & butter | 35 | Served in cream gravy; lingonberry jam was below 10 % and was not restored. |

**Resolution (Pass 2, `scripts/audit_pass2_apply.py`):** for each entry
above, the dropped category was restored. This is a soft conflict with
Pass 1's threshold-driven approach: when the name explicitly names a
component (e.g. "Pierogi (potato-cheese)") or the dish category itself
encodes the component (e.g. "X soup" implies broth), the threshold
should yield to culinary definition.

## 10. Untouched curated meals (n<20) had defining ingredients missing

**Pass 1 decision:** curated meals with fewer than 20 corpus matches
were left alone — the corpus sample was too small to trust as an
override of the curator's choice.

**Pass 2 finding:** several untouched entries had clearly wrong or
incomplete categories that the curator had assigned, regardless of
corpus support:

- **Pancakes & syrup** — tagged `Bread & rolls`. Pancakes are
  batter-based, not bread. Pass 1 hand-fixed `Crêpes Suzette` for this
  same reason; pancakes were missed.
- **Peanut butter sandwich** — tagged `Temperate fruits` (a proxy for
  jelly). The correct category is `Jams & preserves`.
- **Hummus plate** — missing `Nut butters` (tahini is defining) and
  `Citrus` (lemon juice).
- **Cheeseburger** — missing `Sauces` (ketchup/mustard) and `Pickled
  vegetables` (pickles).
- **Mole poblano with chicken** — missing `Candy & desserts`
  (chocolate is the defining ingredient that distinguishes mole
  poblano from other moles).
- **Egg fried rice / Larb / Tom yum goong / Tofu stir-fry / Sashimi
  platter** — all missing `Sauces` (soy / fish sauce / etc).
- **Yogurt parfait** — missing `Whole grains` (granola).
- **Cereal bowl** — missing `Sugar & sweeteners` (most breakfast
  cereals are sweetened).

**Resolution (Pass 2):** added the missing categories. Documented in
`docs/pass2-fixes-report.json`. This conflicts with Pass 1's "small-n
means trust the curator" policy: low corpus support is a reason to be
cautious about *removing* the curator's choices, not a reason to leave
wrong choices in place.

## 11. Compositional strip removed only noise, leaving semantically empty entries

**Pass 1 decision (`scripts/strip_compositional_sugar.py`):**
compositional meals on a hand-list had sugar / sauces / extracts
stripped from their categories because the corpus-pattern pipeline had
falsely included them (e.g. "Compound butter" carrying Sugar).

**Pass 2 finding:** the strip was correct but didn't add back the
*right* defining ingredients. The resulting entries are now too
narrow:

- **Compound butter** — stripped to `[Cream & butter]`, identical to
  plain butter. Compound butter is *defined* by aromatics — herbs,
  garlic, citrus zest — added to the butter.
- **Béchamel base** — stripped to `[Cream & butter, Milk]`. Béchamel
  is roux (butter + flour) + milk + salt; without `Flours` it's just
  buttered milk.
- **Mulled apple wine** — stripped to `[Alcoholic beverages, Temperate
  fruits]`. Mulled wine requires `Whole spices` (cinnamon, cloves) and
  `Sugar & sweeteners`.
- **Apple milkshake** — `[Milk, Temperate fruits]`. A milkshake by
  definition has `Frozen dairy` (ice cream) and sugar.
- **Bread pudding base** — `[Bread & rolls, Milk, Sugar & sweeteners]`,
  missing `Eggs`. Bread pudding custard is bread + milk + eggs + sugar.

**Resolution (Pass 2):** added the missing defining categories. The
strip pipeline should have a corresponding "restore" list for shapes
where the strip leaves the entry meaningless. See
`scripts/audit_pass2_apply.py` for the full list.

## 12. Compositional meal "Apple-walnut milk" doesn't represent any real dish

**Pass 1 outcome (`scripts/rename_compositional_meals.py`'s
`SHAPE_TO_NAMES`):** the shape `[Milk, Nuts, Temperate fruits]` was
named "Apple-walnut milk" — presumably a plant-milk drink. After
deduplication it was the only surviving name for that shape.

**Pass 2 finding:** there is no real-world dish called "apple-walnut
milk". Almond-milk-with-fruit smoothies exist, but they wouldn't be
named this. The category set is too generic to anchor a recognisable
dish, and the name was hallucinated by the SHAPE_TO_NAMES mapping.

**Resolution (Pass 2):** dropped the entry. 696 compositional entries
remain.

## 13. Corpus oddities I left as-is

Two corpus distributions surfaced findings I trust but they may
surprise readers:

- "Spinach Dip" includes Shellfish in 52 % of corpus recipes. This
  reflects the popular "Spinach Artichoke Crab Dip" variant; the
  corpus genuinely treats Shellfish as a near-core ingredient. I left
  it in.
- "Punch" includes Pickled vegetables in 51 % of corpus recipes. This
  is driven by maraschino cherries, which the CSV taxonomy classifies
  as a pickled / brined fruit. The category is genuinely there.
- "Mac and Cheese" only shows Aged cheese at 71 %; most home recipes
  use Velveeta (Processed cheese, 32 %), mild cheddar (Aged cheese),
  or fresh shredded mixes. The audit kept all of them above threshold.
