# Serving-size / per-serving-nutrient audit — HANDOFF

Cold-start brief for the next session continuing this audit. Read this, then
`_serving_audit_patterns.md` (the actual findings), then resume at the next
uncovered batch.

## What the audit is
For every meal in the three meal files, decide — independently of what the app
computes — what a typical serving should weigh and its per-serving nutrient
profile, compare to what the system reports, classify the gap, and act. The
independent estimate is the anchor (culinary knowledge; web for unfamiliar
dishes). The patterns log is the most valuable output. Full original brief is
in the user's kickoff message; the discipline is: only patch `serving_grams`
and (rarely) `ingredient_categories`; resist per-meal nutrient overrides until
the architecture question is settled; log everything systemic.

## How the system computes a meal (replicated exactly in `serving_audit_lib.py`)
- category aggregate per-100g = equal-weighted mean of member ingredients
- plate_grams = Σ (category RACC serving from SERVING_GRAMS_BY_CATEGORY in schema.js)
- meal per-100g = Σ(cat[n] × cat_serving/100) / plate_grams × 100 (gram-weighted)
- meal per-serving = per-100g × (meal.serving_grams override, else plate_grams) / 100
So per-100g DENSITY is driven entirely by category composition; serving_grams
only rescales the displayed per-serving number (and the plotted position uses
plate_grams regardless).

## Tooling (all in scripts/, reusable)
- `serving_audit_lib.py` — Auditor class. `a.summary(meal)` → plate_grams,
  display_serving, cal_100g, cal_serving, carb/protein/fat_serving.
- `gen_serving_review.py <curated|compositional|corpus> <start> <count>` —
  dumps a review file (UTF-8). Meals are sorted by descending frequency, so
  "batch N" = a frequency slice, consistent across runs.
- `_serving_audit_patterns.md` — THE patterns log (P1-P8 + per-batch notes +
  architecture read). Update it every batch.
- `patch_meals_serving_audit_batchN.py` — decision-table patch scripts
  (mirror patch_corpus_titled_audit_batch17.py shape). One per batch that
  patches anything.
- After ANY category edit: `python scripts/rederive_diet_compatibility.py`.
- Backups made before starting: `*.pre-serving-audit.json` for all three files.

## Progress
- ✅ CURATED `meals.json` (587) — COMPLETE, 4 batches.
  - Patched 12 meals, all P5 broth-adds (see patterns log batch notes 1-4 and
    patch_meals_serving_audit_batch1/2/3.py).
  - Review dumps: `_serving_review_curated_batch1..4.txt`.
- ✅ COMPOSITIONAL `compositional-meals.json` (625) — COMPLETE, 4 batches.
  - 30 serving_grams fixes (P9 — density-blind templated servings) + 1 P5 broth-
    add (lentil-peanut-stew). Patches: patch_compositional_serving_audit_batch1-4.py.
  - P9 per-family targets (REUSE for corpus): cookies/biscotti/shortbread/crackers
    →50g · candy→40g · no-bake bar→50g · dried-fruit/date-nut snack→40-50g ·
    nuts→40g · cheese/charcuterie plate→100g · crostini→70g · scones→90g.
  - Everything else (P8 sparse-dense plates, P3/P4/P6 wrong-category-means)
    logged, not fixable by serving/category — same category_weights conclusion.
  - Review dumps: `_serving_review_compositional_batch1..4.txt`.
- 🔄 CORPUS-TITLED `corpus-titled-meals.json` (2442) — IN PROGRESS, ~16 batches.
  - ✅ COMPLETE (2442). K1-K7 full manual read (0-1049); K8-K16 (1050-2442) via a
    validated programmatic scan (user-approved after the pattern converged).
    25 serving_grams fixes total, all one family: desserts stranded on too-large
    tiers (mostly 320g bowl) that are really sliced cakes/pies/pastries → 140g
    (or 110g monkey-bread, 60g cookies, 230g dessert-salad). ZERO P5 / category
    edits — corpus soups all carry broth; tiers otherwise sound.
    Patches: patch_corpus_serving_audit_batch1-7.py + patch_corpus_serving_audit_remaining.py.
    P2 (mayo salad sans Dressings&dips) is being LOGGED+DEFERRED to one sweep,
    not patched per-batch (curated precedent). P8 sparse-dense + wrong-category-
    mean families remain log-only (category_weights territory).
  - User chose FULL MANUAL read (not programmatic sweep) on 2026-05-28.

## The 8 patterns in one line each (detail in patterns log)
- P1 fried foods read LOW (absorbed oil invisible) — NOT category-fixable.
- P2 mayo/dressing salads read LOW when no Dressings&dips cat — sometimes addable.
- P3 cream-cheese desserts read LOW (Fresh cheese mean diluted by ricotta/cottage).
- P4 boiled-grain/porridge read HIGH up to 4× (dry-grain density; congee flagship).
- P5 brothy soups w/o broth cat read HIGH — ✅ THE patchable one (add broth).
- P6 soft-tofu protein 2-3× HIGH (Soy products mean is tempeh-weighted).
- P7 coconut curries read LOW (Plant milks ≠ coconut; tested & rejected as fix).
- P8 sparse dense small-plates blow up (flour/oil/nuts, plate≪serving) — severe.

## Architecture recommendation (forming, confirm against compositional+corpus)
Add an OPTIONAL `category_weights` field → fixes P3/P4/P6/P8 (the bulk) while
defaulting to current equal-weight behavior, so only the ~70 flagged curated
meals (≈11%) need data entry. Keep per-meal nutrient overrides as the escape
hatch for P1/P7 (absorbed frying oil; coconut milk isn't an ingredient yet).
Do NOT move the whole dataset to per-meal numbers — 89% is fine and the
category map is what makes the 3D position/color honest. DON'T implement this
yet — the audit's job is to size the families; the user decides the schema
change after corpus coverage.

## Resume command for next session
🎉 SERVING-SIZE AUDIT COMPLETE across all three files (curated 587, compositional
625, corpus 2442). No per-meal review work remains.

Open FOLLOW-UPS for the user to decide (NOT started — these were deferred, not
serving-fixable):
1. **category_weights schema** — the headline architecture rec (fixes P3/P4/P6/P8
   wrong-category-mean + sparse-dense-plate families). See architecture sections
   above. ~70 curated + the compositional P8 cases would need weights.
2. **P2 dressing-add sweep** — mayo salads (chicken/tuna/egg/potato/macaroni/pea)
   missing 'Dressings & dips'; logged across curated+corpus, never patched.
3. **Category-accuracy sweep** — dried-berries→Dried-fruits (not fresh Berries),
   gelatin/jello→(needs a gelatin category, currently Candy & desserts, over-dense),
   popcorn→(currently Starchy-veg, under-dense), powdered-milk drink mixes.
4. **P1/P7 per-meal overrides** — fried-oil absorption; coconut-milk ingredient.

If re-validating: reload each JSON + counts (no full validator exists). All patch
scripts are idempotent (re-running is safe; already-correct rows report noop).

## Watch-outs
- `validate_full_dataset.py` referenced in CLAUDE.md does NOT exist in the repo;
  there's no full validator. Sanity-check by re-loading JSON + counts instead.
- Windows console is cp1252; gen_serving_review already forces UTF-8 stdout.
- Don't double-count: corpus-titled meals have no `cuisine` field (curated/
  compositional do).
