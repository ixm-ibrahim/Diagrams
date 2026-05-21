# Food Map

A 3D visualization that plots foods across three nutrient axes — **calories**, **carbs**, **protein** — with food-group color blending, an ingredient filter, nutrient thresholds, a meal builder, table view, and light/dark mode. Single page, no framework, vanilla JS + Three.js.

Origin = "best" (low calories, low carbs, high protein). The protein axis is inverted so the highest-protein food sits at the origin and the lowest sits at the far end.

Foods are colored by an additive RGB blend of three food-group weights:
- **Animal** — red
- **Plant** — green
- **Dairy** — blue

So pure animal foods read red, pure plant foods green, dairy blue, and combinations blend in between.

## Running locally

This is a static site. ES modules are loaded directly from disk by the browser, so you need a static HTTP server.

The included Python helper sends no-cache headers so edits show on reload without hard-refresh:

```sh
python dev_server.py
# → http://localhost:8000

# Custom port:
python dev_server.py --port 8080
```

Any static server works equally well:

```sh
python -m http.server 8000
npx serve
```

Then open <http://localhost:8000> in any modern browser.

## Project layout

See `CLAUDE.md` for the full architecture, conventions, and per-phase workflow. The development plan lives in `food-map-development-plan.md`.

## Dataset

The dataset ships in `src/data/ingredients.json` and `src/data/meals.json`:

- **1,362 ingredients** across 12 food groups, 66 categories, 368 subcategories
- **333 curated meal patterns** across 86 cuisine tags (American, European, East and Southeast Asian, South Asian, Middle Eastern, North African, Sub-Saharan African, Latin American, Caribbean, plus pan-cultural snacks, desserts, beverages)
- **100 % category coverage** of the RecipeNLG corpus (2.2M recipes) — every category referenced in real recipes maps to a current project category

Each ingredient carries per-100g nutrient values, a single-group `group_weights` color channel, dietary `contains` tags (gluten / dairy / eggs / peanut / tree-nut / soy / sesame / shellfish / fish / meat / pork / alcohol / honey / caffeine / animal_byproduct), an optional `form` field (fresh / canned / frozen / dried / etc.), and cross-category `tags` (high-protein / fermented / breakfast / dessert / etc.).

Full coverage report + intentionally-skipped scope: [`docs/data-coverage.md`](docs/data-coverage.md).

## Status

Phases 1–32 complete. Phase 1 set up scaffolding; Phases 2–13.75 built the 3D scene, filter tree, threshold sliders, meal builder, table view, theme toggle, persistence, axis controls, and legend filtering; Phases 14–32 expanded the dataset from a ~864-ingredient starter to the full cross-cultural set above.
