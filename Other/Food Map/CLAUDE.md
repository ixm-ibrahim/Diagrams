# Food Map — project context for Claude Code

This file is the cold-start brief for a fresh Claude Code session. Read it before touching code.

## What this is

A single-page 3D visualization that plots foods in a `(calories, carbs, protein)` space. Origin = "best" (low cal, low carbs, **high** protein — the protein axis is inverted). Each food is a sphere; its color is an additive RGB blend of three food-group weights (Animal red, Plant green, Dairy blue). UI rails on the left (filters + nutrient thresholds + meal builder) and right (selected-food detail panel). Light/dark mode. Mobile-first.

Full product and phase-by-phase spec: `food-map-development-plan.md`. **Always consult that file when picking up a phase.** Each phase has a validation checklist — do not skip it.

## Current phase

See the last commit message and the file tree. Phase 1 (project bootstrap) creates scaffolding; later phases fill stubs in `src/`.

## Architecture

```
food-map/
├── index.html                  # Shell: header, canvas container, left/right rails
├── CLAUDE.md                   # This file
├── README.md
├── food-map-development-plan.md
├── dev_server.py               # Tiny Python static server with no-cache headers
└── src/
    ├── main.js                 # Entry point — boots scene + rails
    ├── state.js                # Observable global state (subscribe/set/get)
    ├── data/
    │   ├── foods.json          # Exhaustive dataset (Phase 2)
    │   └── schema.js           # Validation + helpers (Phase 2)
    ├── core/
    │   ├── normalize.js        # Nutrient → [0,1] axis position (Phase 2)
    │   ├── filters.js          # Composed filter logic (Phase 6/7)
    │   └── scoring.js          # Composite score, target distance (Phase 7/8)
    ├── scene/
    │   ├── setup.js            # Three.js renderer, scene, camera (Phase 3)
    │   ├── controls.js         # Arcball + touch (Phase 3)
    │   ├── axes.js             # Axis lines, ticks, labels (Phase 3)
    │   ├── points.js           # InstancedMesh of food spheres (Phase 4)
    │   ├── picking.js          # Raycaster + hover (Phase 5)
    │   └── meals.js            # Meal centroid rings (Phase 9)
    ├── ui/
    │   ├── left-rail.js        # Container + collapse logic (Phase 6)
    │   ├── ingredient-filter.js  # 3-level checkbox tree (Phase 6)
    │   ├── nutrient-thresholds.js # Dual-handle sliders, modes (Phase 7)
    │   ├── detail-panel.js     # Right rail (Phase 5)
    │   ├── table-view.js       # Sortable table (Phase 8)
    │   ├── meal-builder.js     # Meal authoring UI (Phase 9)
    │   ├── view-toggle.js      # 3D ↔ table (Phase 8)
    │   ├── theme-toggle.js     # Light/dark (Phase 11)
    │   ├── legend.js           # Food-group legend (Phase 4)
    │   └── shortcuts.js        # Keyboard handling (Phase 11)
    └── styles/
        ├── tokens.css          # CSS custom properties (theme tokens)
        ├── layout.css          # Reset, app shell grid, responsive rails
        └── components.css      # Buttons, inputs, primitives
```

## Conventions

**Modules.** ES modules only (`<script type="module">`). No bundler. Files import each other by relative path. Stub files export named functions so import sites compile before the implementation lands.

**State.** One shared observable in `src/state.js`. Views subscribe via a selector and re-render only when their slice changes. No framework. Phase 1 sets up the API; later phases extend the shape.

**Theming via CSS custom properties.** All colors, spacing, type sizes, z-indexes, and motion durations live in `src/styles/tokens.css`. Light is the default on `:root`; dark overrides apply when `prefers-color-scheme: dark` is reported by the OS **or** when `[data-theme="dark"]` is set on the root. Phase 11's theme toggle just sets that attribute. **Three.js code must read scene colors via `getComputedStyle(document.documentElement).getPropertyValue('--color-axis')` etc., so the scene tracks theme changes for free.**

**Responsive.** One breakpoint at **768px**. Mobile (≤768) treats rails as overlays / bottom sheets; desktop (>768) docks them as side panels via CSS Grid (`grid-template-areas: "left canvas right"`).

**Touch targets.** Minimum 44×44 px for interactive elements (Phase 10 audit; bake it in earlier).

**Mobile gestures.** `touch-action: none` on the canvas so Three.js controls own pointer/touch gestures with no scroll conflict.

**Performance.** Spheres render as one `InstancedMesh`. Per-instance color uses the food-group RGB blend. Don't add per-food draw calls.

**Schema (Phase 14–32 baseline).** `src/data/schema.js` exports `FOOD_GROUPS` (12 entries — Beverages joined the original 11 in Phase 14), `FOOD_GROUP_COLORS` (11 hues at 32.7° spacing + cream Dairy), `FOOD_GROUPS_BY_HUE` (legend display order), `FORMS` (optional `form` field: `fresh|canned|frozen|dried|cured|cooked|powdered|paste|pickled`), and `TAGS` (Phase 26 cross-category vocabulary — high-protein / high-fiber / low-cal / high-sodium computed from nutrient values, plus identity tags breakfast / snack / dessert / condiment / garnish / fermented / cured / smoked / omega3-rich / iron-rich). The contains-tag vocabulary lives in `src/core/restrictions.js` as `CONTAINS_TAGS` and includes `caffeine` (drives the "Caffeine-free" dietary restriction). The **single-group rule** still holds: every individual ingredient has exactly one `group_weights` channel = 1 — color blending only emerges at the meal / category aggregate level.

**Dataset (Phase 32 final).** 1,362 ingredients across 12 food groups / 66 categories / 368 subcategories. 333 curated meals across 86 cuisine tags. 100 % coverage of the RecipeNLG corpus's category vocabulary. Full breakdown + skipped-scope notes in `docs/data-coverage.md`. Validate anytime with `python scripts/validate_full_dataset.py`.

**No comments that narrate the obvious.** Comment WHY when a constraint, invariant, or workaround isn't visible in the code. Don't comment WHAT — the names already say that. Skip comments referencing the current task or PR.

## Produce complete files, not diffs

When asked to modify a file, **output its full current contents** at the end of the change. Patches and diffs across long sessions drift. If a file ever feels patchy in your output, the user will (and should) ask you to dump the whole file again. This applies even for one-line edits inside a long session.

## Workflow per phase

1. Read `food-map-development-plan.md` and find the current phase.
2. State the deliverables in your own words and list the files you'll touch.
3. Call out decisions not specified by the plan (fonts, exact spacing, etc.).
4. Implement.
5. Walk the phase's validation checklist yourself before handing off.
6. Wait for the user to run the dev server and verify before moving on.

## Running locally

```sh
python dev_server.py            # http://localhost:8000
python dev_server.py --port 8080
```

Or any static server (`python -m http.server 8000`, `npx serve`, etc.).
