# Legacy

Artifacts from Phases 14–32 (the dataset expansion). Everything here has
already done its job and is preserved as a reference / safety net — none of
it is loaded by the live app, and nothing in `scripts/` (the active one,
not this folder) depends on it.

## What's here

### `scripts/`
The phase-specific one-shot apply scripts that mutated `src/data/ingredients.json`
or `src/data/meals.json` during Phases 14–31. Each is idempotent in
principle, but re-running them out of order risks reapplying moves to an
already-mutated dataset. Keep them only as a historical record of what was
done.

| Script | What it did |
|--|--|
| `phase15_apply.py` | Salt + anchor ingredients across the 12 new categories |
| `clean_missing_ingredients.py` | Phase 16 canonicalization → MISSING_INGREDIENTS_CLEAN.csv |
| `phase17_apply.py` | Grains expansion (~80) |
| `phase18_apply.py` | Beverages expansion (~80) |
| `phase19_apply.py` | Sweets / mixes / jams (~65) |
| `phase20_apply.py` | Dairy / processed cheese (~50) |
| `phase21_apply.py` | Fats, oils, margarine (~25) |
| `phase22_apply.py` | Vegetables / pickled / fruits (~65) |
| `phase23_apply.py` | Spices, condiments, dressings (~60) |
| `phase24_apply.py` | Final ingredient sweep (~35) |
| `phase25_apply.py` | Subcategory refinement & category splits |
| `phase26_backfill_tags.py` | Cross-category `tags` array |
| `phase27_apply.py` | Western & European meals (~67) |
| `phase28_apply.py` | East & Southeast Asian meals (~67) |
| `phase29_apply.py` | South Asian / Middle Eastern / N. African (~60) |
| `phase30_apply.py` | Sub-Saharan / Latin American / Caribbean (~58) |
| `phase31_apply.py` | Snacks, desserts, beverages, composed plates (~55) |

### `sibling-agent-output/`
The five files produced by the sibling agent that processed the RecipeNLG
corpus before Phase 14. They drove Phases 14–25 (taxonomy decisions,
ingredient additions, validation references):

| File | Role |
|--|--|
| `MISSING_INGREDIENTS.txt` | ~4,500 raw ingredient candidates |
| `MISSING_INGREDIENTS_CLEAN.csv` | Phase 16's cleaned output (~3,556 candidates) |
| `MISSING_CATEGORIES.txt` | 12 proposed new categories |
| `MISSING_SUBCATEGORIES.txt` | ~60 proposed new subcategories |
| `PROJECT_UPDATES_NEEDED.txt` | Structural recommendations (salt gap, form field, etc.) |

The cleaned CSV could be revisited in a future phase if the low-confidence
long tail (~3,200 candidates the curation skipped) becomes interesting to
mine again.

## Still-active tooling

These live in the project's main `scripts/` folder (not here):

- `validate_full_dataset.py` — schema + invariants check (run anytime)
- `validate_meal_pattern.py` — meal-pattern CSV validator (used by Phase 36)
- `coverage_report.py` — RecipeNLG coverage report (run anytime)
