# Serving-size / per-serving-nutrient audit — patterns log

The most valuable output of this audit. Each entry: dish-family · sample-ids ·
direction · magnitude · suspected cause. Per-meal serving_grams patches paper
over systemic issues; this log is where the architectural signal accumulates.

How the system computes a meal (replicated in `serving_audit_lib.py`):
- category aggregate per-100g = equal-weighted mean of member ingredients
- plate_grams = Σ (category RACC serving from SERVING_GRAMS_BY_CATEGORY)
- meal per-100g = Σ(cat[n] × cat_serving/100) / plate_grams × 100 (gram-weighted)
- meal per-serving = per-100g × (meal.serving_grams override, else plate_grams) / 100

So per-100g density is driven ENTIRELY by the category RACC servings and the
category mean nutrients. serving_grams only rescales the displayed per-serving.

---

## Systemic patterns (running)

### P1 — Deep-fried / batter-fried dishes read LOW on calories & fat (~30-45% under)
- direction: system under-estimates kcal/100g and fat
- magnitude: ~0.5-0.6× of real (e.g. fish & chips 140 kcal/100g vs real ~230-280)
- cause: absorbed frying oil is invisible to the model. The `Oils` category
  contributes only its 14g RACC serving to plate_grams (and many fried dishes
  list no Oils category at all — e.g. yuxiang-eggplant), but deep-frying adds
  ~8-15g absorbed fat per 100g of food. The gram-weighted plate can't represent
  "this food was cooked IN fat" — only "a pat of oil sits on the plate".
- samples: fish-and-chips[30] (140 vs ~250), patatas-bravas[19] (130 vs ~190),
  yuxiang-eggplant[115] (60 vs ~150, NO oil cat), tempura-platter[129]
  (165 vs ~270), salt-pepper-shrimp[121], pad-thai[145] (132 vs ~190).
  (watch: fried chicken, onion rings, churros, doughnuts, falafel, croquettes)
- candidate fix: NOT serving_grams (per-100g is the problem). Either a
  category_weights mechanism to let Oils count for more, OR a per-meal
  nutrient override for fried dishes, OR a dedicated high-absorption "Fried"
  treatment. LOG, don't paper over with serving size.

### P2 — Mayo/dressing-based salads & rolls read LOW when no dressing category
- direction: system under-estimates kcal/100g
- magnitude: ~0.4-0.6× when the binder (mayo) is omitted from categories
- cause: dish-name implies a fat-rich binder ("tuna salad", "lobster roll",
  "potato salad", "coleslaw", "chicken salad") but ingredient_categories lists
  only the solids + veg. Missing `Dressings & dips` / `Oils`.
- samples: tuna-salad[29] (81 vs ~190), lobster-roll[58] (147 vs ~250)
- candidate fix: ADD `Dressings & dips` to categories (allowed category edit) —
  content gap, not math gap. Verify per-dish the dish is actually mayo-based.
  (NOT patched in batch 1 — flagged for a targeted dressing-add sweep.)

### P3 — Cream-cheese desserts read LOW (~0.6× kcal)
- direction: under-estimate kcal/100g
- magnitude: cheesecake 187-214 kcal/100g vs real ~320-340
- cause: the `Fresh cheese` category mean is only 264 kcal/100g because it
  averages cream cheese (~340) with ricotta/cottage/mozzarella (~100-170).
  Cheesecakes are nearly pure cream cheese, so the category understates them.
- samples: cheesecake-plain[10], cheesecake-strawberry[18]. (watch: cheese
  balls, cream-cheese frostings, cannoli, tiramisu)
- candidate fix: NOT serving_grams. Needs a cream-cheese subcategory split, OR
  category_weights, OR per-meal override. LOG.

### P4 — Boiled-grain / porridge dishes read HIGH (up to ~4×) — the dry-grain trap
- direction: over-estimate kcal/100g (severe for water-cooked grains)
- magnitude: congee 265 kcal/100g vs real ~60-70 (≈4×!); oatmeal/cereal ~1.5×
- cause: grain category per-100g is a dry/cooked BLEND (Refined grains 251,
  Whole grains 187 kcal/100g). For dishes where the grain is boiled in lots of
  water (congee, jook, porridge), the real cooked density is ~50-70 kcal/100g
  but the model still uses the blend, AND the small plate has no water to
  dilute the toppings. congee[112] = 926 kcal / 66g fat for a rice porridge.
- samples: congee[112] (flagship), oatmeal-berries[37] (170 vs ~90),
  cereal-bowl[36], muesli-bowl[92]. (watch: rice pudding, grits, polenta,
  risotto-as-soup, kheer)
- candidate fix: a separate cooked/hydrated-grain treatment, OR adding the
  liquid as a broth/water category for porridge-style dishes, OR per-meal
  override. congee NOT patched (broth ≠ the water it's actually cooked in, and
  the dry-grain density would still dominate). LOG as the architecture motivator.

### P5 — Brothy soups/stews WITHOUT a 'Prepared soups & broths' category over-read  ★ PATCHABLE
- direction: over-estimate kcal/100g AND protein (no liquid mass to dilute)
- magnitude: ~1.3-1.7× kcal; protein up to ~2× on stews with two protein cats
- cause: the dish is mostly liquid but the category list has only its dense
  solids, so the gram-weighted plate behaves like a dry stir-fry. STRONG
  evidence: the SAME dish-family splits cleanly by presence/absence of the
  broth category — ramen tonkotsu/shoyu (have broth → 132-136 kcal/100g, read
  right) vs ramen miso (lacked broth → 165, read high); tom-yum/wonton-soup
  (have broth, read right) vs borscht/bouillabaisse/jjigae (lacked it, read high).
- samples FIXED in batch 1 (added broth): ramen-miso, kimchi-jjigae,
  sundubu-jjigae, shabu-shabu, borscht, bouillabaisse.
- still-watch (not broth, conceptually different): gazpacho[87] (cold raw-veg
  soup, over-reads from oil not missing broth — see P1-adjacent), mapo-tofu[107]
  (sauce dish not soup; protein issue is P6).
- candidate fix: ADD `Prepared soups & broths` to genuinely brothy meals lacking
  it — this is the cleanest honest patch the audit found. Do a vocabulary sweep
  for soup/stew/jjigae/chowder/pho/bisque names missing the broth category.

### P6 — Soft-tofu dishes massively over-read protein (and calories)
- direction: over-estimate protein 2-3×
- magnitude: mapo-tofu 73g, shabu-shabu 78g, sundubu 76g protein per serving
- cause: the `Soy products` category mean is 230 kcal / 26g protein per 100g —
  that's tempeh/edamame/dried-soy weighted. Soft/silken tofu (the actual
  ingredient in these dishes) is ~55-70 kcal / 6-8g protein. The category
  cannot represent soft tofu. Adding broth (P5) dilutes the per-serving number
  but the per-100g protein density is still wrong.
- samples: mapo-tofu[107], sundubu-jjigae[140], shabu-shabu[135], kimchi-jjigae[139]
- candidate fix: split `Soy products` into firm-tofu / soft-tofu / tempeh
  subcategories, OR category_weights. LOG — cannot fix via serving/broth alone.

### P7 — Coconut-milk curries read LOW
- direction: under-estimate kcal/100g
- magnitude: ~0.7× (green-curry 117 vs real ~160-180)
- cause: no coconut-milk category; the curry fat is carried only by
  `Pastes & ferments` (163 kcal) + `Ground spices`, which don't supply the
  coconut cream. samples: green-curry-chicken[147], red-curry-chicken[148].
- candidate fix: a coconut-milk category/ingredient. NOT patched. LOG.
- ⚠ TESTED & REJECTED (batch 3): adding `Plant milks` does NOT help — that
  category mean is light almond/oat milk (60 kcal/100g, 4g fat), so it pushes
  coconut dishes DOWN (green-curry 468→376). Worse, the South-Indian/Bahian
  curries that ALREADY use `Plant milks` for "coconut milk" (chettinad[399],
  avial[398], moqueca-baiana[409], parippu[401], puttu[400]) are therefore
  UNDER-reading their coconut fat. Real coconut milk is ~200 kcal/100g & ~21g
  fat. Two honest fixes: (1) add a coconut-milk ingredient to the dataset and a
  category for it, or (2) split `Plant milks` so coconut isn't averaged with
  nut/oat milks. Until then, coconut curries read low whether or not they use
  Plant milks.

### P8 — Sparse dense-category "small plates" blow up when serving_grams ≫ plate_grams
- direction: over-estimate kcal/100g AND per-serving (compounding)
- magnitude: up to ~1.6× per-100g; per-serving 1.5-2× because the inflated
  density is then scaled up to a realistic serving
- cause: the meal lists only a few categories, all energy-dense (Flours, Oils,
  Cream & butter, Nuts, cured/processed meat), so plate_grams is tiny (45-200g)
  and the gram-weighted per-100g is dominated by fat/dry-starch. The dish's real
  bulk (water absorbed in cooking, the mass of the corn cake / rice / bread) is
  unrepresented. Then serving_grams (220-400g) scales that wrong density up.
- flagship samples: arepas[281] plate=45g → 420 kcal/100g (real ~250), 925 kcal/srv;
  tahdig[210] plate=74g → 429 kcal/100g & 90g fat/srv (real ~280); vatapa[263]
  329 kcal/100g & 75g fat; fesenjan[209] 253 & 64g protein; com-tam[160] 245;
  bengali-fish-curry[191] 235 & carbs only 10g (no rice listed); manakish[203] 410.
- relationship to P4: same root as the dry-grain trap, generalized — any dish
  whose dominant ingredient is dry/concentrated (flour, dry rice) or pure fat,
  with no diluting bulk category, reads too dense.
- candidate fix: NOT serving_grams (per-100g/plotted position is wrong too).
  Needs category_weights (let the bulk starch count for more) or per-meal
  override. LOG. These are the strongest evidence yet FOR a weighted/override
  schema — the equal-weighted sparse plate simply can't represent them.

### P9 — Compositional templated serving_grams ignore energy density  ★ PATCHABLE (serving_grams)
- direction: per-SERVING calories massively over-stated for dense small-format items
- magnitude: 2-5× (mixed nuts 220g→1120 kcal; shortbread 280g→1142 kcal; nut-
  shortbread 280g→1244 kcal; cheese & nut plate 250g→998 kcal/88g fat)
- cause: compositional meals carry a `serving_grams` templated by MEAL-SLOT tag
  (snack/dessert/breakfast/lunch/dinner), not by density. Bulky/watery items
  (fruit bowls, smoothies, soups) at 220-350g are fine, but calorie-dense
  small-format foods (nuts, cheese/charcuterie boards, cookies/shortbread,
  crackers) inherit the same 220-280g and read like a full meal. Distinct from
  P8: here per-100g density is fine — only the serving size is wrong, so this IS
  serving_grams-fixable (the sanctioned lever) and does NOT touch the plot.
- per-family targets (apply consistently across ALL batches):
    nuts-as-snack → 40g · cheese/charcuterie/nut appetizer → 100g ·
    cookie/shortbread/cracker dessert → 50g
- batch-1 FIXED 12 (see patch_compositional_serving_audit_batch1.py). MORE await
  in later batches: nut-shortbread-4, raisin-oat-cookies, peanut-oat-butter-
  cookies, peanut-butter-oat-cookies, sesame-crackers, cheese-crackers (+ scan
  each batch for new cookie/nut/charcuterie/cracker names).
- NOTE: a global density-aware serving_grams rule would fix this whole family at
  once and is the compositional analogue of the curated category_weights ask —
  flag for the architecture decision, but per-family hand-fixes are honest and
  low-risk in the meantime.

### Minor / watch (sub-15% or isolated, not patched)
- Milk-based sweet drinks (matcha-latte[2], vanilla-latte[24], berry-smoothie[35])
  over-read ~20-40% on kcal & protein — Milk category at 240g dominates. Low priority.
- Several rich small-plate dishes over-read ~20-30% because their plate is tiny
  (dense cats, little mass) then scaled up by serving_grams: croque-monsieur[65],
  french-omelette[69], currywurst[93] (fat 83g outlier), katsudon[128],
  tonkatsu[133], bulgogi-plate[137]. Density-ish; serving_grams are realistic.

---

## Per-batch notes

### Batch 1 — curated meals 0-149 (by frequency) — DONE
- Reviewed all 150. Verdict: curated serving_grams are broadly well-set
  (mostly deliberate plate sizes 130-550g); the audit's real signal is per-100g
  DENSITY from category composition, captured as P1-P7 above.
- Patched: 6 broth-adds (P5) — the only clear, honest, category-fixable gap.
  Re-ran rederive_diet_compatibility.py (3 compat arrays changed: tofu stews
  correctly left high_protein once protein de-inflated).
- NOT patched (logged for architecture decision): all P1/P3/P4/P6/P7 cases —
  none are fixable with serving_grams or a single category add.
- Source of estimates: culinary general knowledge for these well-known dishes;
  cross-checked density against typical kcal/100g ranges (fried ~230-280,
  brothy soup ~50-90, cream cheese ~340, cooked rice ~130, silken tofu ~60).
  No web lookups needed for batch 1 (all familiar); reserve web for the
  unfamiliar long-tail in compositional/corpus batches.

### Batch 2 — curated meals 150-299 (by frequency) — DONE
- Reviewed all 150 (Asian/Indian/Levantine/African/Latin world cuisines).
  Same verdict: serving_grams sensible; density is the story.
- Patched: 3 broth-adds (P5) — mloukhia, harira, ash-reshteh (all genuine soups
  missing the liquid category). Re-ran rederive (1 compat array changed).
- Confirmed P5 is self-limiting: most soups in this batch ALREADY carried broth
  and read correctly (pho-bo/ga, bun-bo-hue, khao-soi, laksa, sinigang, egusi,
  pozole, callaloo). The broth category is doing its job where present — the
  fix is purely filling omissions.
- NEW pattern P8 (sparse dense-category small plates) is the headline of this
  batch — arepas/tahdig/vatapa/fesenjan/com-tam are the most broken meals seen
  so far (per-100g 1.5-1.7× high, per-serving up to 2×), and none are fixable by
  serving_grams or a category add. Strong evidence for category_weights/override.
- Protein over-reads recurred on thick meaty stews (kare-kare 55g, mole 51g,
  ugali 56g, doro-wat 71g, oxtail 53g) — partly P8 (small plate), partly the
  Red meat/Poultry category at full RACC weight with no starch dilution. Logged.
- Under-reads: thieboudienne[236] (oily fish-rice, 79 kcal/100g, no Oils cat → P1).
- Source: culinary knowledge; the genuinely variable/unfamiliar (fesenjan,
  vatapa, mloukhia, waakye, bobotie) cross-checked against typical bowl/plate
  kcal ranges. No single dish needed a deep web dive this batch.

### Batch 3 — curated meals 300-449 (by frequency) — DONE
- Reviewed all 150 (desserts, beverages, breakfasts, European/world mains).
  Same verdict; density is the story.
- Patched: 3 broth-adds (P5) — shchi, Ukrainian borscht (consistent w/ batch-1
  borscht), fasolada. Re-ran rederive (0 compat changes — these stayed in the
  same diets). Broth improvements were modest here (soups already veg-heavy)
  but the fix is correct for consistency + honest plotting.
- KEY refinement to P7: `Plant milks` ≠ coconut milk (60 vs ~200 kcal/100g).
  Adding it makes coconut curries worse, and curries already using it under-read.
  Rejected the coconut fix; logged the real fix (coconut-milk ingredient/category).
- P8 confirmed & extended: chapati-kenyan[355] plate=45g → 522 kcal/100g (pure
  flour+oil), kabuli-pulao[340] 1061 kcal/61g fat, toltott-kaposzta[448] 57g
  protein — all sparse dense-category small plates. (francesinha[425] reads
  1157 kcal/77g protein but that dish genuinely IS that heavy — not flagged.)
- Cream-cheese desserts (P3) vary by dilution: sernik[445]/syrniki[438] read
  OK (few cats, small plate) while NY cheesecake[10] under-read (8 cats incl.
  Flours/Baked snacks diluting the cream cheese). Severity ∝ number of light
  co-categories — another point in favor of weights.
- Milk-drink protein over-read recurs: boba[317] 22g, hot-choc[322] 23g,
  horchata[320] 26g, protein-smoothie[315] 32g — Milk/Yogurt at 240g RACC
  dominates 3-cat beverages. Minor; logged.
- Most soups in this batch ALREADY had broth and read well (soup-joumou, zurek,
  goulash-soup, caldo-verde, hot&sour, canh-chua, molokhia, abgoosht, avgolemono,
  halaszle, pepper-soup) — reinforces that P5 is just filling omissions.

### Batch 4 — curated meals 450-586 (final 137) — DONE → CURATED FILE COMPLETE
- Reviewed all 137 (European/Asian/African/Latin/American-regional mains, more
  desserts & noodle-soups). 
- Patched: 0. Every brothy soup/stew in this batch ALREADY carried
  'Prepared soups & broths' (ciorba, matzo-ball, soto-ayam, bakso, bún-riêu,
  arroz-caldo, mohinga, thukpa, khao-piak-sen, bison-stew, soupe-à-l'oignon).
  The curated dataset's soups were built well; the only P5 gaps were the 12
  caught in batches 1-3. No serving_grams looked clearly wrong.
- All remaining gaps are the non-category-fixable systemic ones, logged:
  - P8 flagship: frybread[569] plate=49g → 502 kcal/100g, 754 kcal/srv (pure
    flour+oil). Same as chapati/arepas/tahdig.
  - protein over-reads on dense plates: baked-ziti[578] 65g & 65g fat,
    hot-pot[579] 68g (Soy products density, P6), lau-lau[568] 64g w/ carbs 2.2g,
    chicken-parm[576] 69g, vepro-knedlo[460] 59g, baghali-polo[513] 61g.
  - the heaviest ones (chicken-parm 1085, baked-ziti 1040, biscuits-fried-
    chicken 924) — some genuinely ARE that heavy (chicken parm), others are
    P8-inflated (baked ziti at plate=260g). Hard to separate without per-dish
    research; flagged the clear P8 cases.
- CURATED COVERAGE: 587/587 meals seen across 4 batches. 12 broth-adds total
  (P5). Everything else logged for the architecture decision.

### Architecture read so far (after 4 batches / 587 curated meals — CURATED DONE)
The category-averaging model is honest for "assembled plate" dishes (most
curated meals land within 15%). It breaks in recurring ways, only ONE of which
is serving_grams- or category-add-fixable:
  (a) cooking method changes density invisibly — frying adds fat [P1], boiling
      dilutes grains [P4];
  (b) a category mean is wrong for a dominant ingredient — cream cheese [P3],
      soft tofu [P6];
  (c) a missing liquid category [P5] — the one we CAN and DO patch (9 soups so far);
  (d) a missing ingredient class — coconut milk [P7];
  (e) sparse dense-category small plates [P8] — equal-weighting a handful of
      concentrated categories with no bulk, then scaling up by serving_grams.

(c) is handled per-meal as we find it. (a)/(b)/(d)/(e) are NOT — and (e) in
particular cannot even be approximated by editing categories, because the
problem is the equal-weighting itself. Current lean: **keep the category-driven
3D position (it's honest as a "what's in it" map), but introduce category_weights
so a dish can say it's 60% rice / 10% butter rather than averaging them flat.**
That single mechanism would address P3/P4/P6/P8 at once (down-weight the
over-counted dense category, up-weight the bulk) and is less of a data-entry
burden than per-meal nutrient overrides for ~3,650 meals. Per-meal overrides
remain the fallback for P1/P7 where no category combination can express the
truth (absorbed frying oil, coconut cream that isn't an ingredient yet).
Hold the final call until compositional + corpus batches confirm the family
sizes — but P8's severity is already the strongest argument for weights.

### Batch C1 — COMPOSITIONAL meals 0-149 (by frequency) — DONE
- First compositional batch. Texture is exactly as the handoff predicted:
  template/pattern dishes (apple+walnut+butter combos), many sparse 2-4 category
  meals, serving sizes templated by meal-slot.
- P5 broth-adds: NONE. Only one soup in the batch (creamy-greens-soup[134]) and
  it ALREADY carries 'Prepared soups & broths'. No other soup/stew names.
- NEW pattern P9 is the headline: dense small-format items (nuts, cheese/
  charcuterie boards, cookies/shortbread) inherit a 220-280g meal-slot serving
  and read 2-5× too high per serving. PATCHED 12 via serving_grams
  (patch_compositional_serving_audit_batch1.py): nuts→40g, charcuterie/nut-
  plates→100g, cookies→50g. per-100g/plot untouched, so no rederive.
- Density patterns recur but are NOT serving-fixable (logged, not patched):
  P8 sparse-dense small plates — buttered-brown-rice[85] plate=59g→274 kcal/100g
  & 35g fat (Whole-grains dry density + butter, no bulk); nutty-buttered-eggs[45]
  327 kcal/100g/81g fat. P3 cream-cheese — none severe here (ricotta dishes read
  OK, diluted by fruit). P1 fried — vegetable-fritters[71]/crêpes-4[76] read a
  touch low (absorbed oil) but within noise.
- Beverage/fruit "snacks" (sangria, smoothies, punch, fruit salads) at 220-320g
  are CORRECT — confirms P9 is specifically a density blind-spot, not a blanket
  over-serving. Left untouched.

### Batch C2 — COMPOSITIONAL meals 150-299 (by frequency) — DONE
- P9 serving fixes (7, patch_compositional_serving_audit_batch2.py): cookies/
  biscotti/shortbread→50g (pecan-biscotti, nut-shortbread-4), candy→40g (PB
  candy eggs, was 1460 kcal/110g fat!), no-bake bar→50g (PB oat squares),
  savory cheese-pastry snack→60g, ricotta cannoli→90g. Plus one bread outlier:
  whole-wheat-bread normalized 280→80g (modeled from Flours not Bread & rolls,
  so it missed the bread-family 80g serving; every sibling loaf is 80g).
- P5 broth-add (1): lentil-peanut-stew — notes literally say "peanut-butter
  BROTH" but cats were only Legumes/Nut-butters/Sugar → 240 kcal/100g. Added
  'Prepared soups & broths' → 140 kcal/100g (real maafe/groundnut ~140-170).
  rederive: 0 compat arrays changed.
- The other three "stews" in this batch (beef-stew, beef-bean-stew, bean-veg-
  stew) read FINE (126-156 kcal/100g) — they carry Starchy/Other veg bulk, so
  no broth needed. Confirms P5 stays conservative: only add broth when the dish
  is genuinely liquid AND over-reads.
- P8 density (logged, NOT serving-fixable): buttered-pasta[276] plate=59g→323
  kcal/100g & 53g fat (Cream&butter+Refined-grains, no bulk; same as batch-1
  buttered-brown-rice); protein over-reads on dense plates beef-cheese-bowl[237]
  58g, seafood-liver-casserole[157] 52g.
- Watch (NOT patched): muffins consistently 280g (~2 large muffins, ~450-585
  kcal); borderline-high but muffins are genuinely dense and 1-2 is plausible —
  left alone, unlike the clearly-wrong cookie/candy servings.

### Batch C3 — COMPOSITIONAL meals 300-449 (by frequency) — DONE
- P9 serving fixes (4, patch_compositional_serving_audit_batch3.py): three more
  cookies→50g (raisin-oat, peanut-oat-butter, peanut-butter-oat) + dried-fruit-
  mix 220→40g (was 695 kcal/152g carb for a "snack"). No rederive (serving only).
- No P5 broth-adds: creamy-lentil-dal & milk-stewed-veg carry Milk as liquid and
  read OK (139-182 kcal/100g); curries/bourguignon/wine-clams read fine.
- P8 density (logged, not serving-fixable): cacio-e-pepe[366] plate=87g→337
  kcal/100g, 1081 kcal/66g fat (sparse cheese+butter+pasta); cheese-stuffed-
  bread[361] 884 kcal (plate=130); lentil-grain-butter-bowl[404]; seeded-
  chicken-sandwich[443] 348 kcal/100g (Seeds+Cream+Margarine). protein over-
  reads on dense plates: mixed-meat-grain-bowl[319] 57g, beef-lasagna-2[416] 55g.
- CATEGORY-ACCURACY note (NOT patched): berry-nut-snack-mix[395] is "dried
  berries + roasted nuts" but uses the fresh `Berries` category (~50 kcal/100g),
  so it under-reads density and mis-plots as a light snack (apple-date-nut-mix
  correctly uses Dried fruits for the same concept). Candidate for a future
  Berries→Dried-fruits sweep; left alone now (displayed per-serving coincidentally OK).

### Batch C4 — COMPOSITIONAL meals 450-624 (final 175) — DONE → COMPOSITIONAL FILE COMPLETE
- P9 serving fixes (7, patch_compositional_serving_audit_batch4.py): crackers→50g
  (sesame, cheese — cheese-crackers was 1272 kcal/95g fat!), date-nut bite
  snack→50g, two-cheese-plate→100g (cheese-plate family), nut crostini→70g,
  scones→90g (berry, raisin). No rederive (serving only).
- No P5 broth-add: african-peanut-stew[457] carries veg+oil+fruit bulk and reads
  157 kcal/100g (fine) — unlike batch-2's bare lentil-peanut-stew (240). Confirms
  the broth-add only fires on genuinely bare brothy dishes.
- P8 density (logged, the dominant un-fixable family here too): steak-with-
  parmesan[514] plate=113g→947 kcal/89g protein; pasta-with-bacon[523] plate=100g
  →943 kcal; cheesy-chicken[592] plate=128g→802 kcal/63g protein; chicken-grain-
  bowl[465] plate=130g→73g protein; bacon-ricotta-pasta[538], peanut-lentil-
  bake[529], potato-cheese-gratin[546], nutty-cheese-eggs[613]. All sparse dense
  plates / wrong category-mean — need category_weights, not serving.
- berry-scones under-density logged (fresh `Berries` category) — same root as
  berry-nut-snack-mix; part of the candidate Berries→Dried-fruits accuracy sweep.

### COMPOSITIONAL-COMPLETE summary (625 meals, 4 batches)
- The compositional set's headline defect is P9 (NOT the curated set's density
  story): serving_grams is templated by meal-slot and ignores energy density.
  TOTAL serving_grams fixes = 30, all dense small-format snacks/desserts:
    cookies/biscotti/shortbread→50 · candy→40 · no-bake bar→50 · crackers→50 ·
    dried-fruit/date-nut snack→40-50 · nuts→40 · cheese/charcuterie plate→100 ·
    crostini→70 · scones→90 · one bread-loaf outlier→80.
  These are honest, low-risk, and DON'T move the 3D plot (only the displayed
  per-serving). A global density-aware serving rule would do the same in one
  shot and is the compositional analogue of the curated category_weights ask.
- P5 broth-adds = 1 (lentil-peanut-stew). Compositional stews mostly carry veg/
  potato/milk bulk and read fine; the broth-add stays rare and self-limiting.
- P8 (sparse dense small plates) and the wrong-category-mean families (P3/P4/P6)
  recur heavily and remain NOT serving/category-fixable — same architecture
  conclusion as curated: category_weights is the single highest-leverage fix.
- The bulky/watery half of the set (soups, smoothies, fruit bowls, grain bowls,
  composed salads, sandwiches, bakes) reads within ~15% and was left untouched.

CURATED-COMPLETE tally of category-fixable vs not (587 meals):
- P5 (broth omission) — FIXED, 12 meals, the only honest category-add. Self-
  limiting: ~95% of curated soups already had broth.
- P1 fried, P3 cream-cheese, P4 dry-grain, P6 soft-tofu, P7 coconut, P8 sparse-
  dense-plate — NOT category-fixable. Rough frequency in curated: P8 ~15-20
  meals (severe), protein over-reads ~25-30 (mostly P6/P8 overlap), P1 ~10, P3
  ~6, P4 ~5 severe, P7 ~6. Call it ~60-70 curated meals (≈11%) materially wrong
  in a way only weights/overrides can fix; the other ~89% land within ~15%.
- Recommendation crystallizing: **category_weights** is the highest-leverage
  single change (fixes P3/P4/P6/P8 = the bulk). Keep it OPTIONAL (absent =
  current equal-weight behavior) so only the ~70 flagged meals need data entry.
  Per-meal nutrient overrides stay as the escape hatch for P1/P7 (absorbed
  frying oil; coconut milk not yet an ingredient). Do NOT move the whole
  dataset to per-meal numbers — 89% is fine as-is and the category map is what
  makes the 3D position/color honest.

---

## Corpus-titled batch notes

### Batch K1 — CORPUS-TITLED meals 0-149 (by frequency) — DONE
- FIRST corpus batch. Big contrast with compositional: corpus servings are
  well-calibrated by dish tier (cookies 60g, brownies 60g, candy/fudge/balls 40g,
  no-bake 40g, caramel-corn 30g, ice-cream 85g, dips 60g, biscuits/rolls 50-55g,
  muffins 60g, quick-breads 90g, cakes/pies 140g, casseroles 360g, soups 350g).
  So P9 nearly vanishes here — only mis-TIER assignments to catch, not a
  systemic over-serving.
- Serving fixes (2, patch_corpus_serving_audit_batch1.py): fruit-cocktail-cake
  320→140 (a sliced SHEET cake parked on the 320g bowl-dessert tier where
  trifles/punch-bowl-cake legitimately live; 320g→962 kcal); monkey-bread
  260→110 (shared pull-apart, was 1311 kcal/95g fat).
- P5: NONE. Every soup/chowder in the batch (potato, taco, vegetable, french-
  onion, corn-chowder) ALREADY carries 'Prepared soups & broths' and reads well
  (90-150 kcal/100g). Corpus soups are built correctly.
- P2 (logged, deferred): chicken-salad[46] note says "mayo" but no Dressings &
  dips cat → 97 kcal/100g (mayo chicken salad ~200). Recurring corpus theme
  (tuna/chicken/potato/macaroni salads). Keeping the curated precedent of NOT
  patching P2 piecemeal — flag a single dedicated P2 dressing-add sweep across
  curated+corpus for the user to approve alongside the schema decision.
- Category-accuracy (logged): caramel-corn[58] popcorn mapped to Starchy
  vegetables (~80 kcal/100g) → under-reads (209 vs ~430). Popcorn ≠ potato;
  candidate for the same accuracy sweep as berry mixes.
- Watch (not patched): pineapple-casserole[144] is a rich sweet SIDE on the 360g
  main-casserole tier (925 kcal/50g fat) — main/side serving ambiguous; watergate
  "salad"[74] is a dessert fluff on the 230g salad tier (525 kcal). Left as-is.
- P8/dense (logged): fruit-cocktail-cake & monkey-bread per-100g also inflated by
  sparse plates; sweet "casseroles" (pineapple, sweet-potato 769 kcal) are dense
  but genuinely rich. No category fix.

### Batch K2 — CORPUS-TITLED meals 150-299 — DONE
- Serving fix (1, patch_corpus_serving_audit_batch2.py): gingerbread 320→140
  (sliced cake mis-tiered onto the 320g bowl-dessert tier — same bug class as
  fruit-cocktail-cake in K1). All other cakes/pies/cookies/candy/breads/dips
  correctly tiered.
- P5: NONE again — every soup/chowder (cream-of-broccoli, clam-chowder, chicken-
  noodle, hamburger, tortilla, lentil, broccoli-cheese, black-bean, cheese,
  chicken, minestrone, chicken-tortilla) already carries broth.
- Logged not patched: hot-chocolate-mix (dry mix on 240g drink serving AND
  liquid-Milk-for-powder under-density — errors cancel, no clean fix);
  P8 veg-all-casserole (900 kcal/56g fat, sparse); 320g bowl-desserts/sweet sides
  (chocolate-delight 887, baked-pineapple, harvard-beets) rich but portion-
  subjective; P2 pea-salad (deferred to the P2 sweep).
- Takeaway: corpus serving template is sound; corpus work = catching rare
  sliced-cake-at-320 mis-tiers + the eventual P2 dressing sweep, NOT systemic.

### Batch K3 — CORPUS-TITLED meals 300-449 — DONE
- Serving fix (1, patch_corpus_serving_audit_batch3.py): heavenly-hash 360→230
  (fruit/marshmallow dessert-SALAD on the main-casserole tier; siblings ambrosia/
  congealed-salad are 230). A new mis-tier flavor: dessert-salad-at-360.
- No P5 (all soups carry broth); all cakes/pies/cookies/candy/breads/dips tiered
  correctly. lemon-lush & other no-bake layered desserts at 320g left (bowl tier).
- Running corpus mis-tier taxonomy: (a) sliced cake at 320 → 140 (fruit-cocktail-
  cake, gingerbread); (b) dessert-salad at 360 → 230 (heavenly-hash). Watch for
  both in later batches.
- P8 dups recur (mixed-vegetable/veg-all-casserole 900 kcal); logged, not fixable.

### Batch K4 — CORPUS-TITLED meals 450-599 — DONE
- Serving fix (1, patch_corpus_serving_audit_batch4.py): cherry-crunch 320→140
  (cherry dump-cake/crisp on wrong tier; cobblers/dump-cake siblings are 140).
  Adds a sub-case to mis-tier pattern (a): crisp/crunch/dump-cake-at-320 → 140.
- No P5 (all soups carry broth: clam-chowder, onion-soup, butternut-squash,
  minestrone; oyster-stew uses Milk and reads fine). cakes/cookies/candy/breads
  all correctly tiered.
- Logged: funnel-cakes 320g→709 kcal (fried under-density × big serving cancel,
  P1, leave); ice-cream-cake plate=54g→462 kcal/100g (P8); crab/seafood-salad
  60 kcal/100g (P2 mayo likely missing, deferred).

### Batch K5 — CORPUS-TITLED meals 600-749 — DONE
- Serving fix (1, patch_corpus_serving_audit_batch5.py): rhubarb-crunch 320→140
  (crisp/crunch; siblings apple-crunch & peach-crisp in same batch are 140).
- No P5 (all soups carry broth). All other tiers correct. 320g bowl-desserts
  (blueberry-delight 826 kcal, scalloped-pineapple) & candied-yams left as
  portion-subjective. Running total corpus serving fixes: 6.

### Batch K6 — CORPUS-TITLED meals 750-899 — DONE
- Serving fixes (3, patch_corpus_serving_audit_batch6.py): blueberry-crunch,
  blueberry-buckle, dirt — all 320→140 (crisp / butter-cake / Oreo-pudding
  dessert stranded on the 320g bowl tier; twins dirt-pudding & oreo-cookie-
  dessert are 140). The 320→140 dessert mis-tier is the dominant recurring
  corpus defect — watch every batch for cobbler/crisp/crunch/buckle/pudding/
  layered-dessert names at 320g.
- sweet-potato-balls 320g left (candied SIDE, matches sweet-potato-side tier).
- No P5; all other tiers correct. Running total corpus serving fixes: 9.

### Batch K7 — CORPUS-TITLED meals 900-1049 — DONE
- Serving fixes (2, patch_corpus_serving_audit_batch7.py): apple-kuchen 320→140
  (cake-mix coffee cake), bubble-bread 320→110 (= monkey bread, matches K1).
- Logged: layered "delight" desserts & noodle-kugel at 320 left (bowl/side);
  finger-jello 416 kcal/100g = gelatin-in-Candy category artifact (serving fine).
- No P5; all other tiers correct. Running total corpus serving fixes: 11.

### Batches K8-K16 — CORPUS-TITLED meals 1050-2442 — DONE (programmatic scan)
- After K1-K7 confirmed the pattern fully converged, the user approved finishing
  via a validated programmatic scan instead of 9 more manual dumps. Method:
  enumerate dessert-tagged @320g + treats @≥140 + dessert @360 + monkey/bubble
  names + a P5 brothless-soup safety scan over idx 1050-2442; eyeball each by
  name/notes/per-serving; patch the clear mis-tiers. (patch_corpus_serving_audit_remaining.py)
- 14 serving fixes: 11 sliced cakes/pies/pastries→140 (apple-strudel, fruitcake,
  mississippi-mud, lemonade-cake, baked-alaska, coconut-pies, apple-turnovers,
  pecan-pies [1212kcal!], buttermilk-brownies, chocolate-eclairs, pumpkin-roll —
  the last one had been missed by manual K3), cranberry-mold 320→230 (gelatin
  dessert-salad), and 2 cookies→60 (chocolate-peanut-butter-cookies 320→1232kcal!,
  chocolate-chip-cookie 140→60).
- Deliberately LEFT (eyeballed, genuine): no-bake layered bowl desserts (delight/
  lush/yum-yum/cherries-in-the-snow/punch-bowl-cake), large ice-cream desserts
  (banana-split-sundae, cherries-jubilee), deep-fried hand-helds (funnel-cake,
  apple/banana-fritters, fried-pies — P1 under-density × big serving compensate),
  glorified-rice & noodle-kugel (substantial scooped sides).
- P5: NONE in the whole corpus — chili/gumbo/stew read 142-197 kcal/100g (correct
  for thick dishes, not thin broths); every actual soup already carried broth.

### CORPUS-COMPLETE summary (2442 meals, K1-K16)
- 25 serving_grams fixes total, ALL one defect family: dessert items stranded on
  too-large tiers (mostly the 320g bowl tier) that are really single-serving
  sliced cakes/pies/pastries/cookies → 140g (or 110g monkey-bread, 60g cookies,
  230g dessert-salads). per-100g/plot untouched.
- ZERO P5 broth-adds and ZERO other category edits: corpus soups are all built
  with broth, and serving tiers are otherwise sound. The corpus generator's
  serving template is good; the only systematic leak was a subset of "bowl-style"
  desserts inheriting 320g when they're plated slices.
- Logged-not-patched (deferred to sweeps / category_weights, same as curated):
  P2 mayo-salads missing Dressings&dips; category-accuracy artifacts (gelatin/
  jello in Candy & desserts → over-dense; popcorn in Starchy-veg → under-dense);
  P8 sparse-dense plates; P1 fried under-density. None serving-fixable.
