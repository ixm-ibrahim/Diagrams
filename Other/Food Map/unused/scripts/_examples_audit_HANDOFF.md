# example_ingredients manual audit — HANDOFF

Tester follow-up to Batch 2 (the `example_ingredients` generation). The generated
picks "often just copy the categories" — i.e. when a meal's category got no
name/notes/NER signal, `gen_meal_example_ingredients.py` fell back to a generic
`CATEGORY_DEFAULT`, and token-bleed mis-picked specifics. The task: hand-audit
**every meal, one by one**, and replace picks that aren't legitimate examples of
that dish.

## Locked decisions (2026-05-29)
- **Scope:** ALL three files, pure manual one-by-one. Order: `meals.json` (587,
  most visible) → `compositional-meals.json` (625) → `corpus-titled-meals.json` (2442).
- **Generic case:** when a category has no dish-specific example, KEEP the neutral
  default (salt-table, olive-oil, white-rice). Only replace picks that are
  *actively wrong* for the dish. Don't drop the example (validator needs coverage).

## Known systematic error classes (what to look for)
- **Salt bleed:** `onion-salt` / `garlic-salt` / `celery-salt` / `seasoned-salt`
  picked for "Salt & seasonings" just because the dish mentions onion/garlic/celery.
  → almost always should be `salt-table`. (~900 meals corpus-wide.)
- **Sauces default = `soy-sauce`:** wrong for Western dishes → ketchup / gravy /
  mustard / hot sauce as the dish dictates.
- **Cream & butter bleed = `beef-tallow`** (from "beef") → usually `butter`.
- **Ground spices** wrong default in sweet dishes (`paprika`/`cayenne`/`black-pepper`
  → `cinnamon-ground` / `nutmeg`).
- **Forced irrelevant defaults:** `potato-russet` (Starchy), `chickpea`/`lima-beans`
  (Legumes), `padron-pepper` (Peppers), `lotus-root` (Other veg) shoved into dishes
  that don't contain them → swap to the dish's real member or the neutral default.
- **Category quirks:** the dish's signature ingredient sometimes lives in a
  category the meal doesn't list (feta=Aged cheese, flour tortilla=`white-tortilla`
  in Refined grains, corn-flakes=Prepared mixes, sauerkraut=Other veg). Either pick
  the best IN-category proxy (queso-fresco for feta, lavash for tortilla) or add the
  real one as an out-of-category **hero** (allowed by the validator).

## Workflow / tooling
1. `python scripts/audit_examples_dump.py catindex` → `_audit_examples_catindex.txt`
   (grep-able category→members; pick valid ids from here).
2. `python scripts/audit_examples_dump.py review <file> <start> <end>`
   → `_audit_examples_review_<file>.txt` (per-meal: name, notes, picks-as-names).
3. Read the review, hand-author corrections into
   `scripts/_audit_examples_corrections.json` = `{ "<meal_id>": [ids...], ... }`
   (full replacement list per changed meal; unchanged meals omitted). **This file is
   scratch — overwrite it per batch** (git history of the data file is the record).
4. `python scripts/apply_examples_audit.py <file> --dry-run` → review the diff.
5. `python scripts/apply_examples_audit.py <file>` → writes (format-preserving:
   2-space, CRLF; backs up once to `*.pre-examples-audit.json`).
6. `python scripts/validate_meal_example_ingredients.py` → must PASS.

The applier validates every correction (real ids, no dupes, each non-skip meal
category keeps ≥1 in-category representative) and aborts the whole write on any
violation. SKIP-coverage categories: Extracts & essences, Pastes & ferments,
Pickled vegetables.

## Progress
- [x] **meals.json 0–59** (2026-05-29): 27/60 meals corrected, validated, applied.
      Backup: `src/data/meals.pre-examples-audit.json`.
- [ ] meals.json 60–587
- [ ] compositional-meals.json (all)
- [ ] corpus-titled-meals.json (all)

Resume: `python scripts/audit_examples_dump.py review meals.json 60 120`.
