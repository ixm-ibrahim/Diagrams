# Data coverage — final dataset summary (Phase 32 + Phase 39 audit)

Authored as the closing audit of Phases 14–31. Verifies the project meets
the targets set out in `food-map-development-plan.md` and
`PROJECT_UPDATES_NEEDED.txt` (section J), and documents what was
intentionally left out of scope. Phase 39 re-audited the taxonomy against
the Phase 36 corpus extraction (see "Phase 39 taxonomy audit" below).

## Headline metrics

| Metric                  | Final     | Phase 14 start | Δ      |
|-------------------------|-----------|----------------|--------|
| Ingredients             | **1,362** | 864            | +498   |
| Meals                   | **333**   | 25             | +308   |
| Food groups             | 12        | 11             | +1 (Beverages) |
| Categories              | 66        | 40             | +26    |
| Subcategories           | 368       | 292            | +76    |
| Distinct cuisines (meals) | 86      | 0              | +86    |

## RecipeNLG coverage

The `recipe_taxonomy.csv` reference (~2.2M recipes from RecipeNLG) was
scanned to verify the project's category taxonomy is exhaustive enough that
real cooking can be described against it. After the Phase 25 split remap is
applied:

- Recipes scanned: **2,231,142**
- Total category-occurrences: **13,545,298**
- Mapped to a current project category: **13,545,298 (100.00 %)**
- Unmapped: 0
- Target: ≥95 % mapped — **PASSED**

This 100 % result follows from the sibling agent having drawn its
category proposals from the same NLG corpus, so the Phase 16 cleanup and
Phase 25 split together fully cover that vocabulary.

## Per-food_group ingredient counts

| Food group              | Count |
|-------------------------|-------|
| Protein (animal)        | 188   |
| Grains                  | 170   |
| Vegetables              | 154   |
| Condiments & sauces     | 145   |
| Dairy                   | 133   |
| Herbs & spices          | 129   |
| Sweets                  | 113   |
| Fruits                  | 107   |
| Beverages               | 90    |
| Fats & oils             | 49    |
| Protein (plant)         | 44    |
| Nuts & seeds            | 40    |

## Structural invariants — all PASS

- ✅ No category contains >50 ingredients (Phase 25 split the 6 that did).
- ✅ Every food_group has ≥2 categories (Phase 25 split Legumes to satisfy this for Protein (plant)).
- ✅ Every category has ≥2 subcategories (Phase 25 sub-split the 7 single-subcategory categories).
- ✅ Every ingredient passes `validateIngredient()` (schema, single-group rule, FORMS, TAGS, CONTAINS_TAGS).
- ✅ Every meal's `ingredient_categories` resolve to current categories.

## Tag distribution (Phase 26)

| Tag           | Count | Approx. semantic |
|---------------|-------|------------------|
| low-cal       | 454   | <100 kcal/100g |
| high-sodium   | 284   | ≥600 mg/100g |
| high-protein  | 263   | Protein supplies ≥40 % of cal (or ≥20 g/100g) |
| breakfast     | 244   | Identity-tagged via keywords + categories |
| high-fiber    | 207   | ≥6 g fiber/100g |
| dessert       | 174   | |
| condiment     | 131   | |
| snack         | 120   | |
| fermented     | 102   | |
| iron-rich     | 86    | |
| cured         | 52    | |
| omega3-rich   | 41    | |
| garnish       | 31    | |
| smoked        | 24    | |

158 ingredients carry no tag (flours, sugars, raw spices, sweeteners —
items with unremarkable nutrient profiles that don't fit any identity
keyword).

## Cuisine distribution (top 20 meal cuisines)

| Cuisine            | Meals |
|--------------------|-------|
| American           | 45    |
| Indian             | 17    |
| Japanese           | 17    |
| Italian            | 15    |
| French             | 14    |
| Mexican            | 13    |
| Levantine          | 12    |
| British            | 10    |
| Korean             | 9     |
| Thai               | 8     |
| Turkish            | 8     |
| Chinese-Cantonese  | 7     |
| Vietnamese         | 7     |
| Chinese-Sichuan    | 6     |
| Filipino           | 5     |
| Iranian            | 5     |
| Moroccan           | 5     |
| Peruvian           | 5     |
| Spanish            | 5     |
| Argentine          | 4     |

Plus a long tail of 66 cuisines with 1–3 meals each (Brazilian, Cuban,
Polish, Hungarian, Russian, Ethiopian, etc.).

## Deliberately-skipped scope

Items the data expansion **did not** attempt to cover, with reasons:

### Low-confidence candidates from MISSING_INGREDIENTS_CLEAN.csv
The Phase 16 cleanup produced **3,556 candidate canonical names**: 339
high-confidence (cv≥2 — multiple raw NLG-rows collapsed into one) plus
3,217 low-confidence (cv=1 long-tail). Phases 17–24 added ~498 ingredients
drawing primarily from the high-confidence tier and obvious gaps. The
remaining low-confidence tail was **not** added because:
- Many are recipe-language artifacts ("salad croutons", "dish pie crusts")
  rather than distinct ingredients.
- Many are brand-specific variants we already cover generically.
- Many are form / preparation variants of existing ingredients (e.g.,
  "freshly grated parmesan" vs. existing "Parmesan").
- The `form` field lets future entries handle real form-variants without
  exploding the ingredient list.

A future phase could re-run the cleanup against a stricter near-duplicate
detector and surface remaining genuine gaps.

### Sub-regional cuisine specificity
Meals are tagged at the country / major-region level (e.g., `Chinese-
Sichuan`, `Chinese-Cantonese`, `Indian-Punjabi`, `Indian-South`,
`Pakistani-Pashtun`). Finer subdivisions (Indian state-by-state, Chinese
city-by-city, regional French) are out of scope — the meal patterns at
this level are mostly indistinguishable in `ingredient_categories` shape.

### Alcoholic-beverage nutrient nuance
Wines/beers/spirits use representative per-100g values for the broad
class. Vintage / varietal / ABV-specific entries (e.g., "Beer (10 % IPA)"
vs. "Beer (4 % lager)") were not added — calorie differences are real but
the project's per-100g granularity is appropriate.

### Caffeine-content quantification
The `caffeine` `contains` tag is binary (present / absent). Per-100g
caffeine in mg is not tracked. A future enhancement could add a numeric
nutrient if the use case justifies the extra column.

### Highly-processed multi-ingredient entries
Items like "frozen pizza", "TV dinner", "fast-food burger meal" are not
ingredients — they're meals composed of multiple ingredients. The meals
layer handles them where the cuisine fit is clear.

## Future expansion candidates

If the dataset grows further, these are the next obvious areas:

1. **Per-100g caffeine + alcohol % numeric fields** on Beverages — opens
   up "Caffeine total" axis option.
2. **More Indian / Chinese regional sub-meals** — current coverage is
   strong at the broad-cuisine level but thin at the sub-regional level.
3. **More African sub-cuisines** — Ethiopian/Kenyan/South African are
   reasonable but West African (Nigerian, Ghanaian, Senegalese,
   Ivoirian) could expand further.
4. **More fresh-vs-cooked / canned-vs-frozen variants** for produce
   (currently mostly the fresh form is canonical) — but this should use
   the `form` field rather than ingredient duplication.
5. **Subcategory taxonomy review** — 368 subcategories is high; some
   (especially in Aged cheese, Mushrooms after the Phase 25 split) could
   be consolidated if the filter tree feels noisy.

## Reproducibility

Every Phase 14–32 change was applied by an idempotent script under
`scripts/`. Re-running them in order against the Phase 13 baseline reproduces
this final state. The full validation toolkit:

```sh
python scripts/validate_full_dataset.py     # schema + invariants
python scripts/validate_meal_pattern.py --all   # CSV-validate every meal
python scripts/coverage_report.py           # NLG corpus coverage
python scripts/analyze_extraction.py        # Phase 39 taxonomy diagnostic
python scripts/phase39_taxonomy.py          # Phase 39 applier (no-op in current state)
```

## Phase 39 taxonomy audit

After Phase 36 extracted 2,409 compositional patterns from the
RecipeNLG corpus, Phase 39 re-audited the current 64-category taxonomy
to surface merge / split / rename candidates. The diagnostic
(`scripts/analyze_extraction.py`) emits a human-readable report plus a
machine-readable sidecar at `docs/phase39-analysis.json`.

**Findings:**

- **Merge candidates surfaced (lift ≥ 8.0):** 16 high-lift pairs were
  flagged, but every one is a correlation between semantically distinct
  categories (e.g. `Aged cheese + Refined grains` co-occur because of
  pasta dishes; `Organ meats + Shellfish` co-occur because both land in
  surf-and-turf / seafood-platter contexts). None reflect actual
  redundancy in the taxonomy.
- **Split signal:** no category is disproportionately used in tiny
  patterns. Phase 25's earlier subcategory split work appears to have
  fully addressed the granularity gaps.
- **Low-coverage categories:** 4 categories appear in < 5 corpus
  patterns AND < 3 curated meals — `Dried herbs`, `Meat alternatives`,
  `Plant milks`, `Freshwater fish`. All four are populated with real
  ingredients (5–12 entries each) and exist for taxonomic completeness.
  Their low usage reflects bias in the RecipeNLG corpus (Western,
  baking-heavy) and the curated meal library (dinner-leaning), not a
  taxonomy bug.
- **Vocabulary gap:** 9 categories appear in corpus patterns but no
  curated meal references them (`Baking ingredients`, `Flours`,
  `Margarine & shortening`, `Prepared mixes`, `Juices`, `Soft drinks`,
  etc.). These are content gaps — the curated meal library is dinner-
  focused; baking and beverages aren't covered. Future expansion could
  add baking / beverage meal templates; the taxonomy itself is correct.
- **Name-similarity review:** 25 category pairs share a long token
  (e.g. `Aged cheese / Fresh cheese`, `Whole grains / Whole spices`).
  All are appropriately distinct on inspection — no renames needed.

**Decision: no taxonomy changes applied.** The current 64-category
structure is stable and well-supported by the data. `scripts/phase39_taxonomy.py`
runs end-to-end as a no-op (empty `CATEGORY_RENAMES` / `MERGES` /
`DROPS` dicts) but still exercises the invariant checks so a future
pass can plug in changes through the same code path.

**Invariants re-verified after Phase 39:**

- ✅ No category contains > 50 ingredients.
- ✅ Every food_group has ≥ 2 categories.
- ✅ Every category has ≥ 2 subcategories.
- ✅ Every meal's `ingredient_categories` resolves to a current category.
- ✅ `validate_full_dataset.py` clean.
