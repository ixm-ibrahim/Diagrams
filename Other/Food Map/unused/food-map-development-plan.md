# Food Map — Development Plan

A single-page 3D visualization for mapping foods across three axes (calories, carbs, protein), with food-group color blending, an ingredient filter, nutrient thresholds, a meal builder, table view, light/dark mode, and full mobile support.

---

## Product overview

**The map.** All foods are plotted in a 3D space. The origin represents the "best" combination for the user's goal (low calorie, low carb, high protein). The far corner represents the "worst." Foods are spheres positioned by their nutrient values.

**The three axes.** Labeled simply: **Calories**, **Carbs**, **Protein**. Tick marks show real-world values (e.g. "100 kcal", "20g") so the axes are self-explanatory. The Calories and Carbs axes increase outward from origin (origin = 0). The Protein axis is inverted — tick values descend outward, so the origin corresponds to the highest-protein food in the dataset and the far end corresponds to zero protein. A small static "← Best" indicator at the origin makes the convention clear at a glance.

**Three food groups for color.** Every food is tagged with weights across three groups: **Animal** (red channel) — meat, poultry, seafood, eggs. **Plant** (green channel) — vegetables, fruits, legumes, grains, nuts, oils, seeds. **Dairy** (blue channel) — milk, yogurt, cheese, butter, cream. Each food's sphere color is an additive RGB blend of its group weights, so pure animal foods are red, pure plant foods green, dairy blue, and combinations blend accordingly.

**Layout.** 3D scene fills the viewport. Left rail (collapsible) holds the ingredient filter and the nutrient threshold panel. Right rail (collapsible, appears on click) shows the detail panel for a selected food. Top corners hold the view toggle (3D ↔ table), theme toggle, and camera reset. Designed mobile-first — rails collapse to bottom sheets on narrow viewports.

---

## Architecture

```
food-map/
├── index.html
├── CLAUDE.md                    # Project context for Claude Code
├── README.md
├── src/
│   ├── main.js                  # Entry point
│   ├── state.js                 # Observable global state
│   ├── data/
│   │   ├── foods.json           # The exhaustive dataset (single-group entries)
│   │   ├── meals.json           # Curated meal patterns (Phase 4.25)
│   │   └── schema.js            # Schema validation + helpers
│   ├── core/
│   │   ├── normalize.js         # Nutrient → axis position
│   │   ├── aggregations.js      # Foods → category-level aggregates (Phase 4.5)
│   │   ├── persistence.js       # localStorage + import/export (Phase 12)
│   │   ├── filters.js           # Composed filter logic
│   │   └── scoring.js           # Composite score + target distance
│   ├── scene/
│   │   ├── setup.js             # Three.js renderer, scene, camera
│   │   ├── controls.js          # Arcball + touch gestures
│   │   ├── axes.js              # Axis lines, tick marks, billboard labels
│   │   ├── points.js            # InstancedMesh of food spheres
│   │   ├── picking.js           # Raycaster + hover state
│   │   └── meals.js             # Meal centroids + connector lines
│   ├── ui/
│   │   ├── left-rail.js         # Container + collapse logic
│   │   ├── ingredient-filter.js # 3-level checkbox tree
│   │   ├── nutrient-thresholds.js
│   │   ├── detail-panel.js      # Right rail
│   │   ├── table-view.js
│   │   ├── meal-builder.js
│   │   ├── view-toggle.js
│   │   ├── view-controls.js     # Foods/Categories + Persp/Ortho + axis snap (Phase 4.5)
│   │   ├── axis-picker.js       # Per-axis nutrient + direction + range (Phase 3.5)
│   │   ├── theme-toggle.js
│   │   ├── legend.js
│   │   └── shortcuts.js         # Keyboard handling
│   └── styles/
│       ├── tokens.css           # CSS custom properties (theme)
│       ├── layout.css           # Grid, rails, responsive breakpoints
│       └── components.css       # Buttons, sliders, checkboxes, etc.
```

State is a single observable object. Views subscribe to slices and re-render only when relevant slices change. No framework; vanilla JS modules + Three.js.

---

## Phases

Each phase is sized for a single Claude Code session with Opus 4.7. Each phase ends with a validation checklist — you (the user) confirm before moving on. Don't proceed if anything fails; describe the failure precisely and ask for a fix in the same session.

---

### Phase 1 — Project bootstrap

**Goal:** Create the full folder structure, empty stub files, `index.html`, `README.md`, `CLAUDE.md`, base CSS tokens (light + dark), and a minimal "hello world" main.js that confirms the dev server works. No functionality yet — just scaffolding.

**Deliverables:**
- Complete folder/file tree per the architecture above
- `index.html` with semantic structure (header, main canvas container, rails as empty containers), viewport meta tag for mobile, no chrome
- `styles/tokens.css` defining CSS custom properties for both themes (colors, spacing, typography, z-index scale, breakpoints)
- `styles/layout.css` with the responsive grid skeleton: 3D canvas full-bleed, rails as overlays on mobile (≤768px) and side panels on desktop
- `CLAUDE.md` summarizing project goals, conventions, file layout, and "produce complete files, not diffs" rule
- `README.md` with run instructions (`python3 -m http.server 8000` or equivalent)
- `state.js` with the empty observable pattern set up (subscribe, set, get)
- `main.js` that imports state, mounts a placeholder "Food Map" title, and logs ready

**Validate before moving on:**
- [ ] Run the dev server. Open the page. You see the title, theme tokens applied, no console errors.
- [ ] Resize the window from desktop to mobile width — layout doesn't break, no horizontal scroll.
- [ ] Toggle device theme (OS-level dark mode) — colors flip if you connected `prefers-color-scheme` to the tokens.
- [ ] All files in the architecture exist, even if empty stubs.
- [ ] `CLAUDE.md` is informative enough that a fresh Claude Code session could pick up the project.

---

### Phase 2 — Data layer (the exhaustive dataset)

**Goal:** Build the food dataset and the normalization pipeline. This is the foundation; everything downstream depends on it.

**Note:** This phase ships a **starter dataset** (~150–200 ingredients) sized just enough to validate the data layer and the downstream visualization. The comprehensive multi-cuisine ingredient list — the kind a real user would research with — lands in Phase 13.

**Deliverables:**
- `data/schema.js` — JSON schema definition with validation helper. Each food has: `id`, `name`, `category`, `subcategory`, `group_weights` (3-element array summing to 1), `examples` (array of strings), and per-100g nutrients: `calories`, `carbs`, `protein`, `fiber`, `fat`, `sodium`, `sugar`, `saturated_fat`. Also a free-text `notes` field.
- `data/foods.json` — an **exhaustive** list of essential food ingredients spanning the full quality spectrum: from ideal foods (leafy greens, white fish, egg whites, shellfish, skinless poultry) through middle-tier (legumes, whole grains, fruits, lean meats, low-fat dairy) to worst-tier (oils, butter, dried fruits, refined grains, fatty processed meats, sugary foods). Coverage should be comprehensive enough that a user could plausibly find any common ingredient they cook with. The prompt should determine the right count — but err generous, not minimal.
- `core/normalize.js` — given the dataset, computes normalized [0, 1] positions on each axis. Calories and carbs map directly (0 = lowest in dataset, 1 = highest). Protein is inverted (0 = highest protein in dataset, 1 = lowest). Also exposes a function to map an arbitrary nutrient value back into normalized space for the threshold UI.
- A simple test HTML page (`test-data.html`) that loads the data, runs normalization, and dumps a sortable table to the page for inspection.

**Validate before moving on:**
- [ ] Open `test-data.html`. The table loads.
- [ ] Every food has all required fields. No nulls, no missing nutrients.
- [ ] Group weights for each food sum to 1.0 (within float tolerance).
- [ ] After normalization: egg whites, white fish, leafy greens cluster near (low, low, low). Butter, oils land near high calories. Refined sugars land near high carbs. White fish has the lowest protein-axis value (= highest protein).
- [ ] Coverage feels exhaustive. Spot-check: can you find quinoa? lentils? sardines? cottage cheese? almonds? olive oil? If common ingredients are missing, ask for additions.
- [ ] The spread is varied — foods are distributed across the 3D space, not all clumped in one region.

---

### Phase 3 — 3D scene foundation

**Goal:** Three.js scene with arcball rotation, three labeled axes, and tick marks. No data points yet.

**Deliverables:**
- `scene/setup.js` — renderer, scene, perspective camera, resize handling, render loop
- `scene/controls.js` — arcball rotation (mouse drag on desktop, touch drag on mobile, pinch-to-zoom). Smooth damping. Constraints to prevent disorienting flips if needed.
- `scene/axes.js` — three colored axis lines from origin to unit length, tick marks every 0.25 unit, billboard text labels showing real nutrient values (read from the dataset's min/max). "← Best" indicator near origin. Faint unit-cube wireframe to bound the space.
- `main.js` mounts the scene into the canvas container, axes visible, controls active.

**Validate before moving on:**
- [ ] Smooth rotation in all directions, no gimbal lock or jitter.
- [ ] Pinch-to-zoom works on mobile/trackpad.
- [ ] Tick labels are always readable (face the camera) and show real values like "100 kcal" not "0.4".
- [ ] "← Best" indicator visible at origin from any angle.
- [ ] Window resize doesn't distort the scene; camera aspect updates correctly.
- [ ] 60fps on desktop, smooth on mobile.

---

### Phase 3.5 — Configurable axes

**Goal:** Generalize the locked cal / carbs / protein axes into a per-axis `{nutrient, direction, constraint}` triple that the user can edit by clicking the axis label. The same data can be replotted under any nutrient choice.

Axes emanate from origin and extend along +X / +Y / +Z. **Origin is the fixed Worst corner; (1, 1, 1) is the fixed Best corner.** `direction` per axis controls how that axis's values are ordered:

- `direction='max'` (high is best) → tick values **ascend** from min at origin to max at tip.
- `direction='min'` (low is best)  → tick values **descend** from max at origin to min at tip.

Either way, position 1 (the tip) is the "best end" for that nutrient, so the (1,1,1) corner is always the user's best regardless of which directions they pick.

**Deliverables:**
- `state.js` — `axes: [{nutrient, direction, constraint}]` of length 3.
- `data/schema.js` — exports `NUTRIENT_META` with display label, compact `unit` (for tick labels), and `unitLong` (e.g., "kcal per 100g") for menus. All values in `foods.json` are per-100g of the food itself.
- `core/normalize.js` — `projectAxis(value, range, direction)` maps the best end of each nutrient to position 1. `effectiveRange(axis, ranges)` returns the constraint when set, else the dataset envelope. `normalizeFood` projects through the effective range, so a tightened constraint zooms the axis in.
- `scene/axes.js` — labels read from `NUTRIENT_META`; tick values come from the effective range and reflect the direction setting; axis-name sprites carry a "▾" dropdown affordance. "★ Best" sprite is fixed near (1,1,1); "✗ Worst" sprite is fixed near origin. `disposeAxes(group)` for clean rebuild after a config change.
- `ui/axis-picker.js` — click an axis-name sprite to open a popover with: nutrient picker (showing `unitLong`, disabling in-use options), Best when ↓ low / ↑ high toggle, and a Range section with min/max inputs and a ↻ Reset button. Persists open until Esc or click-outside; tracks the sprite's screen position during camera moves.
- `main.js` — sets initial axes with constraints = dataset envelopes; subscribes to `state.axes` for axis rebuilds.

**Validate before moving on:**
- [ ] Click an axis label → popover opens with units clearly shown.
- [ ] Switching nutrient resets that axis's constraint to the new nutrient's envelope.
- [ ] Tightening a constraint updates the tick labels in real time; foods outside the constraint fall outside the unit cube but stay rendered.
- [ ] "★ Best" sits at the far corner (1,1,1); "✗ Worst" sits at origin. Flipping a direction in the picker does NOT move these — it flips the tick value ordering on that axis instead.
- [ ] For default `[cal=min, carbs=min, protein=max]`: calorie ticks read `679 / 457 / 236 / 14 kcal` from origin out (descending); protein ticks read `9.5 / 19 / 28.5 / 38 g` (ascending). Chicken breast lands near (1,1,1).
- [ ] Two axes cannot share the same nutrient.

---

### Phase 4 — Plot points with food-group color blending

**Goal:** Render every food as a sphere at its normalized 3D position, colored by its food-group weights.

**Deliverables:**
- `scene/points.js` — `InstancedMesh` of small spheres, one per food. Per-instance color computed from `group_weights` as `vec3(animal, plant, dairy)`. Per-instance position from `normalize.js`.
- `ui/legend.js` — small fixed-corner legend showing the three group colors with labels (Animal / Plant / Dairy) and the color-blending concept. Hideable.
- Subtle staggered fade-in on load (~10ms per point) so the map feels alive on first render.

**Validate before moving on:**
- [ ] Every food in the dataset appears as a point.
- [ ] Clusters make intuitive sense: animal foods are warm-toned and concentrated in one region; plant foods green and spread out; dairy blue and tight.
- [ ] The Best corner (1, 1, 1) contains the expected ideal foods.
- [ ] The Worst corner (origin) contains oils, butter, refined sugars.
- [ ] Performance stays smooth on a mid-range phone in a mobile browser.
- [ ] Colors are visible against both light and dark backgrounds (we'll wire theming fully later, but check now that nothing is invisible in either mode).

---

### Phase 4.25 — Meal patterns view

**Goal:** Add a third level to the visualization — pre-curated meal patterns. Each meal is a combination of food categories ("Poultry + Whole grains + Leafy greens" = a balanced bowl). One sphere per meal, colored by the **mean of its constituent categories' group weights** — which is where the color-blending design pays off. Individual foods are single-group (pure red / green / blue); blending only emerges at the meal level.

(Note: Phase 9 introduces a user-defined meal builder; the Phase 4.25 meals are static, pre-curated exemplars for browsing.)

**Note on data:** This phase ships a **starter meal library** (~25 entries) — enough to demonstrate the meal-pattern view and validate the color-blending design. The comprehensive cross-cultural meal library is authored in Phases 15–19, organized by cuisine cluster.

**Deliverables:**
- `data/meals.json` — array of ~25 curated meal patterns. Each entry: `{ id, name, ingredient_categories: [string], notes }`.
- `core/aggregations.js` — `aggregateMeals(foods, meals)` produces meal-level pseudo-foods. Each meal's nutrient values and `group_weights` are the equal-weighted mean of its constituent categories (each computed via `aggregateByCategory`).
- **Single-group rule for individual foods**: every food in `foods.json` has `group_weights` with exactly one channel = 1 (e.g., `[1,0,0]` for animal). Borderline items (milk chocolate, ice cream) are assigned their dominant group rather than blended.
- `state.js` — extend `viewLevel` to support `'meal'` in addition to `'individual'` and `'category'`.

**Validate before moving on:**
- [ ] Toggle to Meals → ~25 spheres appear at meal-aggregate positions.
- [ ] A meal mixing Poultry + Whole grains + Leafy greens reads as a warm yellow-green (animal + plant blend).
- [ ] An all-plant meal (e.g., Vegan grain bowl) is pure green.
- [ ] A meal with animal + plant + dairy reads as a near-white / desaturated blend.
- [ ] Switching back to Foods or Categories restores the prior sphere count and pure-channel colors.

---

### Phase 4.5 — View options

**Goal:** Give the user agency over the visualization: choose between perspective and orthographic projection, and snap the camera to a head-on view down any axis (combined with orthographic, this gives a true 2D plot aligned to any pair of axes). The view-level toggle (Foods / Categories / Meals from Phase 4.25) lives in the same control cluster.

**Deliverables:**
- `state.js` — `cameraMode: 'perspective' | 'orthographic'` (default `'perspective'`).
- `scene/setup.js` — both `PerspectiveCamera` and `OrthographicCamera` created at startup. Resize updates both. Expose `setCameraMode(mode)` that swaps the active camera while preserving position + look-at.
- `scene/points.js` — rebuilds the `InstancedMesh` when `state.viewLevel` changes (Foods/Categories/Meals). Tracks the index → id mapping so Phase 5 picking works against the current dataset. Skips the fade-in on rebuild (only the first build fades).
- `ui/view-controls.js` — header-mounted segmented controls:
  - **Level**: Foods | Categories | Meals (the three view levels)
  - **Camera**: Perspective | Orthographic
  - **Snap**: X | Y | Z | ⟲ Free
  Snap moves the camera to look down the chosen axis (target = cube center). Free returns to the default isometric vantage.
- `main.js` — wires the new controls and subscriptions; `axis-picker` reads the camera via a getter so it picks up the active camera after a mode swap.

**Validate before moving on:**
- [ ] Switch to Orthographic → cube edges become parallel; camera position is preserved.
- [ ] Snap X → camera looks down the X axis. Combined with Orthographic, this is a true 2D YZ view. Rotation still works after the snap.
- [ ] Free → returns to the default isometric vantage.
- [ ] All Phase 3.5 axis-picker behavior still works after a perspective/ortho swap.

---

### Phase 5 — Hover, click, and right-side detail panel

**Goal:** Make points interactive. Hovering shows a label; clicking opens the right rail with full food details.

**Deliverables:**
- `scene/picking.js` — raycaster against the instanced mesh, with hover state (currently-hovered food id). Picking accuracy must work in dense clusters.
- Hover effect: picked instance scales up ~1.4× with a smooth tween. Small floating tooltip near cursor (or near the sphere on touch) showing the food name.
- `ui/detail-panel.js` — right rail. Slides in from the right when a food is clicked. Contents: food name, category and subcategory, group breakdown bar (a small horizontal stacked bar showing the RGB mix), all nutrient values per 100g in a clean table, examples list, notes. Close via X button, Esc key, or clicking empty space in the scene.
- On mobile: right rail becomes a bottom sheet that slides up from the bottom edge, dismissible by swipe-down or X.

**Validate before moving on:**
- [ ] Hover is pixel-accurate even where points overlap. No flickering between adjacent points.
- [ ] Click opens the right rail with the correct food's data.
- [ ] Esc closes the rail. Clicking another point swaps the contents without flicker.
- [ ] No memory leaks after rapidly clicking 30+ points (DevTools heap snapshot stays stable).
- [ ] On mobile, the bottom sheet behaves like a native one — drag-to-dismiss, snap points, no scroll conflicts with the 3D scene.

---

### Phase 6 — Left rail: ingredient filter (3-level tree)

**Goal:** A collapsible left rail with a 3-level checkbox tree organized by food group → category → individual ingredient.

**Deliverables:**
- `ui/left-rail.js` — the rail container, collapsible to a thin edge handle on desktop, full-screen drawer on mobile (slides from left).
- `ui/ingredient-filter.js` — the tree:
  - **Top level: 3 food groups** (Animal, Plant, Dairy)
  - **Mid level: categories** within each group (e.g. Plant → Leafy greens, Non-starchy vegetables, Berries, Other fruits, Legumes, Whole grains, Refined grains, Nuts & seeds, Oils, etc.)
  - **Leaf level: individual ingredients**
  - Tri-state checkboxes for parents: checked / unchecked / indeterminate (when only some children are checked). Clicking a parent toggles all descendants.
  - Search box at the top filters the visible tree (matching nodes stay visible; parents auto-expand to reveal matches).
  - Count badge: "X of Y visible"
  - Expand/collapse arrows per branch. State persists during the session.
- `core/filters.js` — central filter logic. Computes the set of "active" food ids based on filter state. Updates state when changed.
- 3D scene reacts: non-matching points fade to ~10% opacity and desaturate (don't disappear — preserves spatial context). Matching points stay full opacity.

**Validate before moving on:**
- [ ] All three food groups appear at top level. Expanding each reveals its categories. Expanding a category reveals its ingredients.
- [ ] Checking "Animal" visually highlights animal foods in the 3D scene and mutes others.
- [ ] Checking "Leafy greens" highlights only that subset.
- [ ] Tri-state works: if you check 3 of 5 ingredients in a category, the category checkbox shows the indeterminate state. The group checkbox above also goes indeterminate.
- [ ] Search filters the tree without losing checkbox state.
- [ ] Count badge updates live.
- [ ] On mobile, the rail opens as a drawer, dismisses by swipe or backdrop tap.

---

### Phase 7 — Left rail: nutrient thresholds

**Goal:** Below the ingredient filter, a panel for setting nutrient targets and thresholds across calories, carbs, protein, fiber, fat, sodium, sugar, and saturated fat.

**Deliverables:**
- `ui/nutrient-thresholds.js`:
  - Dual-handle range slider per nutrient (min and max in real units, e.g. 0–500 kcal). Optional target marker on each slider.
  - Mode selector (segmented control) at the top of the panel:
    - **Filter** — foods outside the range fade like ingredient-filtered ones
    - **Highlight** — foods inside the range get a subtle glow outline; others stay normal
    - **Score** — foods are colored by distance from each nutrient's target (gradient from green at target to red far away). This temporarily overrides the food-group coloring. The legend updates to reflect the active coloring.
  - Per-slider reset and a "Reset all" button.
  - URL hash sync so a configuration is shareable by link.
- `core/scoring.js` — score and distance-from-target computation. Composes with ingredient filter (food must pass both to be active).
- Legend updates dynamically when Score mode is active.

**Validate before moving on:**
- [ ] Dragging the calorie max from 800 down to 100 progressively fades dense foods in real time.
- [ ] Score mode: with target = 25g protein, ±5g tolerance, chicken breast and white fish glow brightest; oils glow least.
- [ ] Mode switching is instant. Switching to Score mode replaces the food-group legend with a gradient legend. Switching back restores it.
- [ ] Ingredient filter + threshold filter compose correctly. Active foods must pass both.
- [ ] URL hash updates as you drag. Reload — configuration restores.
- [ ] On mobile, sliders are large enough to drag with a thumb without precision issues.

---

### Phase 8 — Table view toggle

**Goal:** Switch between the 3D map and a sortable, filterable table view of the same data.

**Deliverables:**
- `ui/view-toggle.js` — toggle in the top-right corner, animates the transition (3D fades out, table slides in, or similar).
- `ui/table-view.js`:
  - Columns: name, category, food group, calories, carbs, protein, fiber, fat, sodium, sugar, saturated fat, and a computed composite score column.
  - Sortable by any column (click to sort, click again to reverse).
  - Column picker (checkbox menu) — user chooses which columns to show. Selection persists via localStorage.
  - Composite score uses user-weighted factors: small inline weight sliders per nutrient. Score updates live as weights change.
  - Filters from Phase 6 and 7 apply: filtered-out foods are hidden in the table (not faded).
  - Click a row to open the same detail panel from Phase 5.
  - Selected food persists across view switches.

**Validate before moving on:**
- [ ] Sort flips correctly on repeat clicks.
- [ ] Column picker shows/hides columns instantly. Choice survives reload.
- [ ] Composite score weights update the ranking live without lag.
- [ ] Ingredient and threshold filters hide rows in table; 3D view restores all foods (some faded) — consistency feels right, not buggy.
- [ ] Switching views preserves selection.
- [ ] Table scrolls cleanly on mobile; columns auto-prioritize on narrow widths (or horizontal scroll if needed).

---

### Phase 9 — Meal builder

**Goal:** Build meals by combining foods with portion sizes; visualize each meal as a centroid in the 3D scene.

**Deliverables:**
- `ui/meal-builder.js` — a third section in the left rail (below thresholds, collapsible):
  - Search-as-you-type food picker
  - Add foods to a meal with a grams slider per ingredient
  - Multiple meals supported (named meal 1, meal 2, etc., or user-named)
  - Each meal listed with its ingredients, total grams, total calories, and a quick-edit affordance
  - Delete meal button
- `scene/meals.js`:
  - Each meal renders in the 3D scene as a hollow ring (torus) at its weighted centroid position
  - Thin desaturated lines from the ring to each contributing ingredient's sphere
  - Each meal gets a distinct ring color
  - Hovering a ring shows the meal name and emphasizes its connector lines
  - Meal centroids respect active filters — if outside threshold range, ring desaturates
- Meals optionally persist to localStorage

**Validate before moving on:**
- [ ] A chicken breast + brown rice meal lands between the two points in 3D space, weighted toward the larger portion.
- [ ] Adding a third ingredient shifts the centroid correctly.
- [ ] Connector lines don't clutter the scene with 5+ ingredients (consider showing lines only on hover/focus).
- [ ] Multiple meals visible simultaneously without confusion.
- [ ] Centroid math matches an independent calculation you do by hand for one meal.
- [ ] Filter interactions feel coherent — a meal exceeding the calorie threshold desaturates appropriately.

---

### Phase 10 — Mobile responsive pass

**Goal:** Dedicated QA and refinement pass on mobile. Mobile considerations were baked in throughout, but this phase tests, fixes, and polishes.

**Deliverables:**
- Audit and fix any touch-target sizing issues (minimum 44×44px for interactive elements)
- Verify rails collapse and expand cleanly as drawers / bottom sheets
- Ensure the 3D scene is fully gestureable: one-finger rotate, two-finger pan, pinch-zoom — no conflicts with browser scrolling
- Detail panel as bottom sheet with proper snap points and drag-to-dismiss
- Test on at least: narrow phone (≤375px), standard phone (~390px), tablet (~768px), landscape orientation
- Ensure text remains readable (no overflow, no microscopic font sizes)
- Verify keyboard (on-screen) doesn't break layout when search inputs are focused
- Add `<meta name="theme-color">` matching active theme so the browser chrome on mobile follows

**Validate before moving on:**
- [ ] Open on a real phone (or device emulator at 375px width). Every feature usable with thumbs only.
- [ ] No horizontal scroll, no clipped UI, no inaccessible buttons.
- [ ] Rotating the 3D scene with one finger doesn't accidentally scroll the page.
- [ ] Bottom sheets behave naturally — snap, drag, dismiss.
- [ ] Performance: rotation is smooth on a mid-range Android. If sluggish, reduce sphere segment count or instance count budget.

---

### Phase 11 — Theme toggle, keyboard shortcuts, and final polish

**Goal:** Bring everything together as one designed object. Theme toggle, shortcuts, typography pass, empty states, motion polish. (Camera presets are now in Phase 4.5; this phase just exposes them via keyboard.)

**Deliverables:**
- `ui/theme-toggle.js` — sun/moon icon in top-right. Smooth transition when toggling. All UI colors driven by CSS custom properties; Three.js reads tokens via `getComputedStyle` so scene background, axes, gridlines, and label colors all update in lockstep. Food-group RGB colors stay vivid in both themes (slightly boost saturation in dark mode if needed for readability). Persists to localStorage, respects `prefers-color-scheme` on first load.
- `ui/shortcuts.js` — keyboard handling:
  - `R` reset camera to default isometric (== "Free" snap from Phase 4.5)
  - `T` toggle 3D/table view
  - `Esc` close panel/rail
  - `[` and `]` collapse/expand rails
  - `?` show shortcut help overlay
  - `1`/`2`/`3` trigger the X / Y / Z axis-snap buttons from Phase 4.5
- Camera reset button in the corner (== "Free" snap action).
- Subtle floor grid below the unit cube for spatial reference.
- Empty states: when no foods match the active filters, show a friendly "No foods match — try adjusting filters" overlay with a "Reset filters" button.
- Typography pass: one sans-serif throughout, consistent scale, no orphan styles.
- Final motion polish — every transition smoothed, no abrupt state changes.
- README updated with feature list, screenshots placeholder, usage notes.

**Validate before moving on:**
- [ ] Toggle theme in light and dark — one smooth transition, no flash of unstyled content.
- [ ] Reload preserves theme. Fresh browser respects OS preference.
- [ ] Every shortcut works. `?` shows a discoverable help overlay.
- [ ] Keyboard snap shortcuts (`1`/`2`/`3`/`R`) match the Phase 4.5 buttons.
- [ ] Empty state appears when filters exclude everything; reset button restores.
- [ ] The whole app feels like one designed object. Show it to a friend who hasn't seen it — they should grasp the layout in under 30 seconds.

---

### Phase 12 — Persistence and sharing

**Goal:** Make a session durable. The user's axis configuration, view choices, filters, thresholds, meals, and theme should survive page reloads. Provide an export/import mechanism for backing up or sharing a setup so research can resume in a fresh session or be handed to someone else.

**Deliverables:**
- `core/persistence.js` — load and save the serializable subset of state to `localStorage`. Debounced on changes (~300ms). Schema versioning so older saves migrate cleanly or fail loud with a useful message.
- **Persistable state**: `axes` (nutrient + direction + constraint), `viewLevel`, `cameraMode`, `theme`, `ingredientFilter`, `thresholds`, `thresholdMode`, `meals`, table column picks. Selection (hovered/selected food) is session-only.
- Initial-load hydration runs before scene mount so the user lands directly on their last setup with no flash of defaults.
- **Export button** in the header — copies a JSON blob of the persistable state to the clipboard AND offers download as `food-map-config.json`.
- **Import button** — accepts a pasted JSON or uploaded file. A confirmation modal previews what will change ("3 axes changed, 2 meals added, threshold mode → score") before overwriting current state.
- Malformed JSON triggers a clean error and does not corrupt the live state.
- Phase 7's URL hash sync for thresholds is preserved as a complementary sharing affordance (link vs. file).

**Validate before moving on:**
- [ ] Change axes, add a meal, switch to dark theme → reload → everything preserved.
- [ ] Export → clear `localStorage` → import the JSON → identical state.
- [ ] Hand the JSON to someone else (or open in a different browser) → they see your view.
- [ ] Pasting malformed JSON shows a clear error and does not break the app.
- [ ] An older or newer-schema save either migrates cleanly or fails with a useful message.

---

### Phase 13.5 — Model refactor, UX, restrictions & boot UI

**Status:** Shipped (not in the original plan; documented here so future Claude Code sessions can pick up the model and conventions).

This phase consolidates the off-plan refactors and quality-of-life fixes that landed between Phase 12 and the data-expansion phases. It changes the data model and naming throughout the codebase, so anything authored against the original Phase 6 / Phase 12 shapes will need light updates.

**Vocabulary rename.** Throughout the code and data, `food` → `ingredient`:
- `src/data/foods.json` → `src/data/ingredients.json` (file renamed; field shape unchanged on each entry).
- Variables, function names, state keys: `foods` → `ingredients`, `food` → `ingredient`, `selectedFoodId` → `selectedIngredientId`, `hoveredFoodId` → `hoveredIngredientId`, `foodId` → `ingredientId`, `getCurrentFoods` → `getCurrentIngredients`, `validateFood` → `validateIngredient`, `foodById` → `ingredientById`, etc.
- **Preserved** as historical identifiers (don't rename): `foodMap.*` localStorage keys (renaming breaks Phase 12 persistence), `window.__foodMap` and `__foodMapState` namespaces, "Food Map" project title, the `food_group` field name (food-science term), the `FOOD_GROUPS` constant.

**`food_group` field.** New required field on every ingredient — one of:
`Vegetables`, `Fruits`, `Grains`, `Protein (animal)`, `Protein (plant)`, `Dairy`, `Nuts & seeds`, `Fats & oils`, `Sweets`, `Herbs & spices`, `Condiments & sauces`. (Phase 14 added a 12th group, `Beverages`, for juices/alcohol/coffee/tea/sodas/broths.)
Exported as `FOOD_GROUPS` from `src/data/schema.js`. This is a **food-science classification** independent of `group_weights` (the 3-channel `[animal, plant, dairy]` array that still drives sphere color and meal-color blending). The two coordinates are deliberately separate: the RGB channels are locked to 3 for the visualization story (Phase 4.25), but the filter tree, table grouping, etc. read `food_group` instead.

**Ingredient filter tree restructured.** `src/ui/ingredient-filter.js`:
- Top level is `food_group` (alphabetized at render).
- Mid level: `category`.
- Leaf: individual ingredient.
- Empty `food_group`s are hidden. The animal/plant/dairy swatch on the top level is gone (it was meaningless once the top axis switched).

**`contains` field + dietary restrictions.** New required string-array field on every ingredient, populated with any of:
`meat`, `fish`, `shellfish`, `pork`, `dairy`, `eggs`, `gluten`, `tree_nut`, `peanut`, `soy`, `sesame`, `alcohol`, `honey`, `animal_byproduct`.
`src/core/restrictions.js` defines the 14 user-facing restrictions (Vegetarian / Vegan / Pescatarian / Halal / Kosher / Gluten-free / Dairy-free / Tree-nut allergy / Peanut allergy / Egg allergy / Soy allergy / Shellfish allergy / Fish allergy / Sesame allergy), each mapped to a tag set; `excludedTagsFor()` unions them. `src/ui/restrictions.js` mounts a "Dietary restrictions" section at the **top of the left rail** (above ingredient filter). Active restrictions hard-filter ingredients across the 3D scene (in every threshold mode), the table view, and the meal builder (meals containing any restricted ingredient are hidden). State key: `restrictions: string[]`, persisted.

**Meals: food_group filter.** `state.mealFilters.foodGroupsExcluded: string[]` — a new INVERSE filter slot. The Meals section's dropdowns include a "Food groups" panel showing all 11 boxes (all checked by default). Unchecking a group adds it to `foodGroupsExcluded`; a meal is hidden if any constituent ingredient's `food_group` is in that list. Applies to both the meal list and the Meals view-level scene.

**Persistence migrations.** `src/core/persistence.js` gains `migrateHydrated(key, value)`:
- `mealFilters.foodIds` → `mealFilters.ingredientIds` (Phase 14 rename).
- `userMeals[*].ingredients[*].foodId` → `ingredientId`.
- Missing `mealFilters` slots are defaulted to `[]`.
- Persisted `thresholds` whose envelope is narrower than the current dataset get expanded so newly-added high-cal/high-sodium items (lard, baking soda, tallow) don't auto-grey on first load after a data refresh. Handled in `main.js` after hydratePatch.

**Boot overlay (`index.html` + `src/main.js`).** Replaces silent failures with a visible loading screen that turns into an inline error card with stack trace + "Clear saved settings and reload" button if anything throws. Wraps `boot()` in `runBoot()`; registers `window.error` and `unhandledrejection` listeners so post-boot crashes surface too. `boot()`'s inner dataset-load `catch` rethrows so the outer handler gets a chained cause instead of returning silently.

**CSS / layout polish.**
- `.app-header` gets a `--color-bg` background so scrolled rail content doesn't show through.
- `.rail-fade` element (positioned just below the header, width tracks the left rail) provides a soft gradient so scrolled content dissolves into the header instead of cutting sharply.
- `.rail-section-toggle` font-size bumped from `--font-size-sm` to `--font-size-md` so section titles are visibly larger than their internal sub-section titles.
- `.app-header-left`'s desktop reserve adjusted so `.app-header-center`'s segmented controls don't overlap the left rail's scrollbar.

**File-organization notes.**
- `src/core/restrictions.js` — pure module: tag vocabulary + restriction definitions + `passingIngredientIds()` helper. Imported by `main.js`, `meal-builder.js`, and `ui/restrictions.js`.
- `src/ui/restrictions.js` — section that mounts at the top of the left rail.

**Validate before depending on this:**
- [ ] `python -c "import json; d=json.load(open('src/data/ingredients.json',encoding='utf-8')); assert all('food_group' in i and 'contains' in i for i in d)"` passes.
- [ ] Reload the app: no console errors, dietary restrictions section appears above Filter by ingredient.
- [ ] Toggling "Vegan" hides every meat/fish/dairy/egg ingredient in the scene and table, plus every meal containing them.
- [ ] Unchecking "Dairy" in the Meals → Food groups dropdown hides any meal whose ingredients include a dairy entry.
- [ ] Stale persisted thresholds (from before Phase 13) auto-expand on next load; high-cal items render in their group color, not grey.

#### Round 2: UX & diagnostic additions

A follow-on pass after the first round, addressing user-surfaced friction.

**Defaults flipped to collapsed.** `createRailSection`'s `initiallyCollapsed` default is now `true` so every left-rail section (Restrictions, Filter by ingredient, Nutrient thresholds, Meals) opens compact. The ingredient filter tree's food_group level also defaults to closed (was open). The Meals → Curated / Your meals sub-sections default to closed via `mealsCuratedOpen` / `mealsUserOpen` initial state.

**Chevron sizing.** The disclosure chevron on the food_group level of the filter tree (24x24 box, 17px font) and the meal sub-section toggle (24px width, 17px font) are visibly larger than category-level chevrons (22x22, 14px) — readable as sub-section headers without competing with the rail-section title chevron (16px font in a 22px box).

**Meal filters: restrictions dropdown + reorder.** A 5th "Restrictions" dropdown joins the meal filters. It writes to `state.restrictions` directly (a mirror of the global Dietary restrictions section), so toggling Vegan here is the same as toggling it above. Filters are reordered broad → specific: **Restrictions, Food groups, Categories, Ingredients, Nutrients**. `renderPanel` gained an `external` option for state-key-as-source dropdowns; `mountFilters` now syncs button counts from `state.restrictions` for the external slot.

**Fade-in speedup.** `scene/points.js` replaces `FADE_DELAY_PER_POINT_MS` with a per-build `perPointDelayMs = FADE_TOTAL_STAGGER_MS / n` (default 2000ms total). 864 ingredients now stagger over ~2 seconds instead of ~9; `FADE_DURATION_MS` trimmed to 240ms.

**Inactive-ingredient diagnostics.** `src/core/inactive-reasons.js` is a pure helper that, given an ingredient + current state, returns an array of human-readable reasons it's currently hidden (ingredient filter, dietary restrictions, threshold range — in `filter` mode only). Used by:
- The hover tooltip (`scene/picking.js`) — adds a bulleted reason block under the name when the hovered sphere is grey. Tooltip CSS conditionally widens via `:has(.ingredient-tooltip-name)`.
- The detail panel (`ui/detail-panel.js`) — adds a "Why this is greyed out" section at the bottom of the panel with the same reasons. The panel re-renders when any of `ingredientFilter`, `thresholds`, `thresholdMode`, or `restrictions` changes so the block stays in sync with current filter state.

**Rail-fade only on scroll.** The gradient under the header (`.rail-fade`) is `opacity: 0` by default and adds `.is-scrolled` once the left rail's `scrollTop > 4`. Width tightened to `var(--left-rail-w) - 14px` so the fade doesn't cover the rail's scrollbar.

**Table view: food_group + reorder.** Identity columns now go broad-to-narrow: **name → food_group → category → subcategory → group (animal/plant/dairy)**. `subcategory` is added but off by default to save horizontal room; `food_group` is on by default. Sorting and rendering for all four new column ids land in `compareForColumn` and the row renderer.

#### Round 3: layout polish, axis labels, fade replay, color schemes

**Header background matches the rail.** `.app-header` was using `--color-bg` (page bg); in dark mode that's visibly darker than the rail's `--color-surface` and created a noticeable seam. Switched to `--color-surface`. The fade gradient under the header (`.rail-fade`) follows suit so the fade dissolves into the same color.

**Left rail collapse arrow inset.** `.rail-toggle` gains `margin-right: var(--space-3)` so it sits *inside* the rail's right edge rather than past it, mirroring the right rail's collapse arrow which sits just inside its inner edge.

**Hide axis labels toggle.** New "Aa" button in the 3D camera-controls cluster. Persisted via `state.axisLabelsVisible`. In `scene/axes.js`, every text sprite (tick values, axis-name labels, Best/Worst markers) is added to a child `labelsGroup` instead of the root axes group, so visibility toggles in one shot. Useful when a label happens to sit visually over a sphere you want to click. (A "smarter" approach would auto-dim labels on raycast proximity — left for later; the explicit toggle ships now because it's predictable.)

**Threshold envelope expansion.** Three layers now ensure persisted threshold windows always cover the current dataset envelope:
- `main.js` post-hydrate migration (already existed).
- `applyHashFromUrl()` now also expands hash-loaded ranges to the envelope (`Math.min(lo, r.min)`, `Math.max(hi, r.max)`), so a stale URL with a narrower window can't re-clamp ingredients out.
- A final reconciliation pass after both — `expandThresholdsToEnvelope()` — catches anything else. This fixed the "calories min = 14" complaint: a 0-cal ingredient (baking soda, rose water) couldn't pass a 14-cal min and rendered grey.

**Fade-in replays on view switch.** `points.js` exposes `replayFadeIn()` which resets `currentScale` to 0 and restarts the stagger. `applyViewToggle` calls it whenever `view` transitions from `'table'` back to `'3d'` so the dataset pops in instead of appearing instantly.

**Table view search-by-name.** A `.table-search` input next to the Columns button filters rows by case-insensitive substring of `ingredient.name`. Session-only (no persistence — stale searches across reloads aren't useful).

**Table: removed "Group" column.** The colored dot in the Name cell already conveys the animal/plant/dairy mix, and the legend (now visible in both views) is the canonical key. Cleaner identity column block: name → food_group → category → subcategory → nutrients → score.

**Legend visible in table view too.** `applyViewToggle` no longer hides `#legend` when switching to table view. Both views share the same color story now.

**Legend: secondary blends + scheme toggle.** The RGB legend gained a "Mixes (two channels)" sub-section showing yellow (animal+plant), cyan (plant+dairy), magenta (animal+dairy), plus a tri-blend swatch for near-white. A scheme toggle at the top of the legend switches sphere coloring between:
- `rgb` — the original additive animal/plant/dairy primaries.
- `food_group` — each of the 11 food_groups gets a fixed color (vegetables green, fruits red, dairy cream, grains tan, etc., defined in `FOOD_GROUP_COLORS` in `data/schema.js`). Aggregates (categories, meals) lerp across food_group colors weighted by `food_group_weights`, a new field set by `aggregateByCategory`, `aggregateMeals`, and `aggregateUserMeal`.

`points.js` precomputes both color palettes per ingredient at build time and a `setColorScheme(scheme)` setter switches between them. State key `colorScheme: 'rgb' | 'food_group'` is persisted. The table view's row-dot color (`groupBlendCss`) follows the same scheme.

`state.legendOpen` is now persisted so collapsed/open survives reload.

#### Round 4: layout symmetry, axis defaults, equidistant palette, legend parity

**Axis label hide scope narrowed.** The "Aa" toggle now only hides the large axis-NAME labels (the "Calories ▾" sprites at each axis tip). Tick numbers and ★ Best / ✗ Worst markers stay visible since they're too small to obscure a sphere click. `scene/axes.js`'s `labelsGroup` now only contains the axis-name sprites; tick labels and Best/Worst sit directly on the root axes group.

**Calories & protein axis ranges have round defaults.** Per-nutrient default constraint table in `main.js`: calories = 0–1000, protein = 0–100. All other nutrients fall back to the dataset envelope. The persisted-axes migration runs the same expand-to-envelope safety net as thresholds — `Math.min(persisted.min, default.min)`, `Math.max(persisted.max, default.max)` — so stale narrow ranges (e.g., calories min stuck at 14 from a pre-Phase 14 dataset) get widened to the new defaults without losing user customizations that already cover the envelope. `nutrientPrefs` gets the same treatment so swapping a nutrient onto an axis lands on the new range.

**Left rail extends top-to-bottom.** `.app-header` now starts at `left: var(--left-rail-w)` instead of `left: 0` on desktop, so the header sits next to the left rail rather than over it. The rail's right border + scrollbar are visible from top to bottom. `padding-top: var(--header-height)` removed from both rails (right rail too, for symmetry).

The "Food Map" title moves from `.app-header-left` into a new `<header class="rail-chrome">` row inside the rail (with the rail-collapse button beside it, mirroring the right rail). Desktop hides `.app-header-left`; mobile keeps it for opening the drawer. The rail-chrome is hidden on mobile (the header's `.app-title` keeps that role). `.rail-fade` (from round 2) is gone — without a header overlap there's nothing to fade through.

**Food group palette: equidistant hues.** Replaced the earlier "intuitive but washed-out" colors with 10 maximally-distinguishable hues spaced 36° apart on the HSL wheel (saturation 70%, lightness 55%), plus cream off-white for Dairy (which doesn't map to any single hue). Assignment preserves intuition where possible — Fruits red, Grains yellow, Vegetables green, Protein (plant) chartreuse — but distinguishability wins ties. See `FOOD_GROUP_COLORS` in `data/schema.js`.

**Legend shape parity.** Both schemes now share the same overall shape:
- header → scheme toggle → `.legend-body` (min-height: 270px) → blurb.
- A/P/D has two sub-sections inside `.legend-body`: "Individual" (3 swatches) and "Combinations" (4 swatches — the three pairwise mixes + the tri-blend).
- Food group has one sub-section: "Food groups" (11 swatches).
- Both blurbs are the same one-liner phrasing ("Combinations blend smoothly between …") so the bottom row visually matches.

#### Round 5: quality-of-life

**Legend body fixed-height.** `.legend-body` is now exactly 280px tall (was min-height 270px), with `display: flex; flex-direction: column; justify-content: space-around;` so both modes' content centers within the same fixed area. The legend card itself has a fixed 220px width. Result: A/P/D and food_group modes have identical card dimensions.

**Food group legend: no section title, hue-ordered.** Removed the redundant "Food groups" header (the scheme toggle above already labels the mode). New `FOOD_GROUPS_BY_HUE` in `data/schema.js` lists food_groups in display order — Dairy (white/cream) first, then 0°→324° rainbow (Fruits, Protein (animal), Grains, Protein (plant), Vegetables, Herbs & spices, Fats & oils, Sweets, Nuts & seeds, Condiments & sauces). The legend renders from this array.

**Round axis defaults for every nutrient.** All eight nutrients now have explicit round-number defaults so axis ticks land on familiar values:

| Nutrient        | Default range | Dataset max |
|-----------------|--------------|-------------|
| calories        | 0–1000       | 902         |
| carbs           | 0–100        | 100         |
| protein         | 0–100        | 86          |
| fiber           | 0–100        | 78          |
| fat             | 0–100        | 100         |
| sodium          | 0–30000      | 27360       |
| sugar           | 0–100        | 100         |
| saturated_fat   | 0–100        | 82.5        |

Default thresholds now also derive from these (not the raw dataset envelope), so the sliders' initial windows match the axis ticks. The `expandThresholdsToEnvelope()` reconciliation also uses these defaults, so stale narrow persisted ranges widen to these round numbers. `defaultConstraintFor(nutrient, ranges)` is module-scope so the hash, hydrate, and reconciliation paths all share one source of truth.

**Table view: per-viewLevel column visibility.** Category aggregates now carry a `food_group` field (the dominant food_group among members, picked from `food_group_weights`). The table's `visibleColumns()` runs the candidate column set through `viewLevelHidesColumn(level, columnId)`:
- Categories view hides `category` and `subcategory` (both equal the row's name).
- Meals view hides `food_group`, `category`, and `subcategory` (meal aggregates fake all three to "Meal"/the meal's name).
- Individual view shows everything as before.

The columns menu filters the same way, so the user can't tick off columns that won't render in the current view.

**Table: resizable columns.** Each `<th>` gets a 8px-wide `.th-resize` strip on its right edge. Pointer-down captures, drag updates the column's width inline (and tracks it in a session-only `columnWidths` map keyed by column id). The data-table is `table-layout: fixed` so the width sticks. Min column width 48px so a column can't be dragged to zero. The sort handler moved from the whole `<th>` onto the `.data-th-btn` so the resize handle's clicks don't trigger sort.

#### Round 6: bug fixes from round 5

**Hidden axis labels were still clickable.** three.js's raycaster doesn't walk ancestor visibility, so the axisNameSprites under `labelsGroup.visible = false` still intercepted clicks. `pickSprite` in `scene/picking.js` now filters by walking each sprite's parent chain and dropping any whose ancestors are hidden.

**Food group colors at full saturation.** Bumped `FOOD_GROUP_COLORS` from HSL S=70% L=55% to **S=100% L=50%** so the hue brightness matches the additive A/P/D mode's primaries and pairwise blends. The food_group yellow at hue 72° now reads as bright as the (animal + plant) additive yellow. Dairy stays as warm off-white cream.

**Default column widths.** Each entry in `COLUMN_DEFS` now carries a `defaultWidth` — Name 220px, food_group 130px, category/subcategory 140px, nutrients 84px, score 110px. `table-layout: fixed` was distributing total width equally across columns when no widths were set; user-resized widths still win via the `columnWidths` Map.

**Right-aligned headers for numeric columns.** Each `<th>` now carries a `data-align="left"|"right"` attribute. CSS `th[data-align="right"] .data-th-btn { justify-content: flex-end; }` aligns the inline-flex button content right, matching the right-aligned numeric cells underneath. Previously `text-align: right` on the th had no effect on the inline-flex button's children.

**Scrollbars follow the theme.** `tokens.css` now declares `color-scheme: light` on `:root` and `color-scheme: dark` on `[data-theme="dark"]`. Browsers use this to render native widgets (scrollbars, form controls) in the right palette — so the rail scrollbar darkens in dark mode and lightens in light mode without per-property `::-webkit-scrollbar` overrides.

**Flash-of-dark-theme on first load eliminated.** Added a synchronous inline script in `<head>` that reads `localStorage.foodMap.theme` (falling back to `prefers-color-scheme`) and sets `<html data-theme>` BEFORE the stylesheets load. The loading overlay, the 3D scene background (set by `readCssColor('--color-bg')` during scene creation), and every CSS-token-driven element now paint in the correct theme from the first frame instead of flashing dark then snapping to light.

#### Round 7: dropdown categories + remaining axis-click bug

**Axis labels were *still* clickable when hidden.** Fixed in round 6 for `scene/picking.js` but `ui/axis-picker.js` has its own `spriteUnderPointer()` raycaster path with the same blind spot. Same ancestor-visibility filter ported over — hidden labels are now truly inert (neither sphere selection nor axis-picker triggers).

**Categories dropdown.** The middle button in the view-level segmented control is now a dropdown; clicking "Categories" opens a menu with three grouping options:
- **By food group** (~11 spheres)
- **By category** (~40 spheres — the previous default)
- **By subcategory** (~80 spheres)

State: new `categoryGroupBy: 'food_group' | 'category' | 'subcategory'` (default `'category'`), persisted alongside the other PERSISTABLE_KEYS. The "Categories" button label updates to reflect the active grouping (e.g., "Food group" / "Category" / "Subcategory") when the user is in category view; otherwise stays "Categories".

`aggregateByCategory(ingredients, groupBy)` now accepts the field name and groups accordingly. Main.js's `activeDataset()` passes `state.get('categoryGroupBy')`. A `state.subscribe(s => s.categoryGroupBy)` handler in main.js rebuilds the points and clears any selection when the grouping changes (only while in category view). The table view subscribes to the same slice and re-renders so its rows match the scene.

The dropdown menu uses `position: fixed` so the seg-group's `overflow: hidden` doesn't clip it; coordinates are set on open from the button's bounding rect. Dismisses on outside click, Escape, or window resize.

#### Round 8: detail-panel color block follows the scheme

The right detail panel's "Color group" section always painted the animal/plant/dairy bar regardless of which scheme drove sphere coloring. It now reads `state.colorScheme`:

- **rgb scheme:** Section heading "Color group". Bar + legend show the three A/P/D channels with non-zero weight, sorted by weight desc. (Same as before for individual ingredients — one channel at 100% — but now consistent for aggregates too.)
- **food_group scheme:** Section heading "Food group". Bar + legend show the non-zero food_group_weights with their hue-equidistant colors. For individual ingredients (single food_group), this is a single 100% bar in the right color; for category/meal aggregates, it lerps across whatever food_groups make up the row.

Shared rendering through a new `colorBlockEntries(ingredient, scheme)` helper returns `{ title, entries: [{ name, weight, css }] }`. The panel re-renders on `colorScheme` change so flipping the legend toggle updates the right panel in sync.

#### Round 9: aggregate active-set translator + dairy color

**Subcategory and food_group categorizations rendered washed.** `translateSetToCurrent()` always looked up an ingredient's `category` field to map the ingredient-id active-set onto the aggregate-id active-set. When the user picked "By subcategory" or "By food group" from the Categories dropdown, the aggregates were keyed by `subcategory` / `food_group` (their `name` field came from the new groupBy), so the `byCategory.get(cat.name)` lookup always missed — every aggregate fell into the inactive set and got the 82% gray blend. Fix: read `ingredient[groupBy]` where `groupBy` is `state.categoryGroupBy` (defaults to `'category'`), so the translation key matches the aggregate's identity. Meal view still translates by ingredient.category since meals reference category names.

**Dairy color overflowed to plain white.** With ambient 0.95 + directional 0.3 = 1.25× lighting in `scene/setup.js`, dairy `(1.0, 0.98, 0.85)` rendered as `(1, 1, 1)` once any channel × 1.25 exceeded 1 and clamped. That made dairy dots indistinguishable from pure white and very close to the lighter half of the inactive gray blend. New dairy color `(1.0, 0.98, 0.3)` keeps the B channel low so the bright lemon-cream tone survives the lighting (post-Lambert ≈ `(1, 1, 0.375)`), reading as bright creamy yellow on the spheres while still soft enough on the legend swatch.

---

### Phase 13.75 — Axis controls panel, legend filtering, threshold capture

Two related improvements landed in this phase: a discoverable way to narrow the 3D cube without driving the threshold sliders, and per-color filtering directly from the legend. (Phase developed across seven internal rounds; the description below reflects the final state — see git history for intermediate decisions.)

#### Axis controls panel (`src/ui/axis-controls.js`)

A docked panel in the bottom-right corner of the 3D view, sitting flush to the left of the legend. Per-axis row:

- **Tag + nutrient name.** Color-coded X/Y/Z chip and the nutrient label as a button. Clicking the name opens the existing axis-picker popover via `axisPicker.openForAxis(axisIndex, anchorEl)` — same UI as clicking the axis-name sprite in the scene, which means it works even when axis labels are hidden.
- **Pan / Zoom buttons.** Hold-and-drag controls. Pointer-down captures the pointer on the button (`setPointerCapture`), enters a closure-scoped `activeDrag`, and applies `clientY` delta each frame: Pan shifts the constraint by `(cumY / 200) × startRange` (sign-flipped for descending orientation); Zoom scales the range geometrically as `factor = 2^(-cumY / 220)` around the midpoint. Release or `Esc` ends the drag.
- **`↻` reset.** Restores the canonical default for that nutrient — `defaultConstraintFor(nutrient, ranges)` from `main.js`, so Calories → 0–1000, Protein → 0–100, etc. The axis-picker popover's reset uses the same path.
- **Range display.** `min – max` in the nutrient's unit, updated live during drag.

Footer button **"Filter food by ranges"** copies each axis's current `constraint` into the matching nutrient threshold — the downstream active-set logic does the rest, so anything outside the current cube is filtered immediately.

**Drag survives re-render.** Each `applyDrag` calls `state.set({ axes })`, which would normally rebuild the panel's innerHTML and detach the very button driving the drag. The axes subscriber checks the closure's `activeDrag` flag: while a drag is active it only refreshes the range text in place; `endDrag` runs a full render to reattach listeners and pick up any structural change made under the drag (e.g., a nutrient swap via the picker).

**Snap on zoom release.** `snapZoomedAxis` rounds the post-zoom min/max to `panStep(range) = 10^(floor(log10(range)) - 2)` — range 100 → step 1, 1000 → 10, 30000 → 100, 1 → 0.01 — so a release that lands at 0.31–998.7 settles cleanly on 0–1000.

**Drag cursor.** `body.axis-drag-locked` (and `body.axis-drag-locked *`, with `!important`, to beat `.btn { cursor: pointer }`) sets `cursor: ns-resize` — the vertical double-arrow — for the duration of the drag.

**Collapsible.** A `×` in the panel header collapses to an "Axes" pill that re-expands on click. State persists as `axisControlsOpen` in localStorage. The Legend's collapsed pill (`.legend-expand`) and the Axes pill (`.axis-controls-expand`) share a single CSS rule so they're guaranteed identical in shape and size — only the label inside differs.

**Flush layout.** `src/ui/legend.js` publishes the legend's rendered `offsetWidth` to `:root` as `--legend-width` via a ResizeObserver. `.axis-controls`'s `right:` reads that variable (with `transition: right` for smoothness), so the panel slides over to hug the legend's actual left edge when the legend collapses to a pill or grows under a scheme swap.

#### Legend as a filter (`src/ui/legend.js` + `src/scene/points.js`)

Each row in the color guide is now a checkbox. Unchecking filters that channel/group's ingredients in the active set; state is per-scheme as `state.legendHidden: { rgb: string[], food_group: string[] }`, persisted. Unchecked rows render with an outline-only swatch so it's clear what's filtered.

`points.js` exposes `setColorFilteredSet(Set<string>)`. `main.js` computes the filtered set by picking the dominant channel/group per ingredient and intersecting with `state.legendHidden[scheme]`. Filtered instances render at `COLOR_FILTER_SCALE = 0.35` with their color lerped 40% toward inactive gray — visibly distinct from threshold-inactive treatment (full size, heavily greyed), so the user can tell *why* something is dimmed.

#### Disabled: in-canvas axis-line drag (`src/scene/axis-drag.js`)

An earlier iteration of this phase let the user grab an axis line directly in the 3D scene to pan its range. The behavior conflicted with camera orbit and the hover affordances were unreliable, so it was retired in favor of the dedicated panel. The code is intentionally retained but gated by a single `AXIS_LINE_DRAG_DISABLED = true` flag with a banner comment — flip it to `false` to revive. `AXIS_DIRS` / `AXIS_LEN` are still exported from `scene/axes.js` for that case, and `panStep` is exported from `axis-drag.js` (the panel imports it for snap calculations).

---

## Data expansion

Phases 2 (foods), 4.25 (meals), and 6 (categories) ship with starter datasets sized just enough to validate features and surface design issues. The exhaustive datasets — the kind a real researcher would use the app with — are authored in this section. **The work here is data-only**: write JSON entries, verify against the test-data page and the live app, iterate. Implementation code generally shouldn't change.

These phases can run in any order after the feature work (Phases 1–12) is settled.

---

### Phase 13 — Comprehensive ingredient list

**Goal:** Expand `foods.json` from ~179 starter entries to a comprehensive cross-cultural list (target ~500–800 entries) covering the common cooking ingredients of major world cuisines.

**Deliverables:**
- **Animal foods**: full poultry (chicken/turkey/duck/goose/quail), red meats (beef/pork/lamb/veal/venison/bison), organ meats (liver, kidney, sweetbreads), processed meats (deli, charcuterie), fish (freshwater + saltwater + canned + smoked), shellfish, eggs (different birds).
- **Plant foods**: comprehensive vegetables (regional + exotic — bitter melon, daikon, kohlrabi, jicama, ramps, etc.), all common fruits (tropical, stone, citrus, melons, dried), legumes (lentil/bean varieties from multiple traditions), grains and pseudocereals, nuts and seeds, oils, fresh and dried herbs and spices.
- **Dairy**: cheese varieties from multiple traditions (French, Italian, Spanish, Dutch, Middle Eastern, Indian), fermented dairy (kefir, lassi, skyr, labneh), plant-milk alternatives if in scope.
- **Sweeteners, condiments, sauces, prepared foods** (miso, gochujang, harissa, tahini, hoisin, etc.).
- All entries follow the existing schema (`id`, `name`, `category`, `subcategory`, `group_weights`, `examples`, 8 per-100g nutrients, `notes`).
- All `group_weights` follow the **single-group rule** (one channel = 1).
- Realistic USDA-style per-100g values.

**Note:** This phase likely spans **multiple Claude Code sessions**. Reasonable splits: one session for animal expansion, one for plant expansion, one for dairy + processed + condiments. Each split should validate independently before the next starts.

**Validate before moving on:**
- [ ] `test-data.html` shows the table loads cleanly, no schema validation errors.
- [ ] Spot-check obscure-but-common ingredients exist (lamb sweetbreads, ramps, paneer, kefir, gochujang, anchovy paste, etc.).
- [ ] The "best corner" cluster still contains the expected lean meats; the "worst corner" still contains oils and refined sugars.
- [ ] No duplicate ids. Every `group_weights` is a pure single channel.
- [ ] The spread is well-distributed; no single octant of the cube is empty.

---

### Phases 14–32 overview: data expansion using RecipeNLG

Phases 14–32 are driven by analysis of the **RecipeNLG dataset** (~2.2M recipes) that a sibling agent ran against the current 864-ingredient project. Five support files in the project root inform the work:

- `MISSING_INGREDIENTS.txt` — ~4500 candidate ingredients (heavily duplicated and partly garbage; see Phase 16 cleanup).
- `MISSING_CATEGORIES.txt` — 12 proposed new categories.
- `MISSING_SUBCATEGORIES.txt` — ~60 proposed new subcategories.
- `recipe_taxonomy.csv` — every NLG recipe with its category-composition (huge — 797MB; **never read whole**, only sample/grep).
- `PROJECT_UPDATES_NEEDED.txt` — structural recommendations and the highest-impact gap (plain salt is missing entirely).

**Do not blindly trust the support files.** The sibling agent's output contains real garbage: brand-only entries (`"betty crocker fluffy white frosting mix"`), placeholder phrases (`"any cheese"`, `"amount of oil"`, `"additional salt"`), near-duplicate plural/singular pairs (`"anaheim chile"` / `"anaheim chiles"` / `"anaheim chili"` / `"anaheim chilies"`), and miscategorizations (`"extra sharp cracker barrel cheese"` was put under Crackers). Every phase below treats the support files as **proposals**, not facts. Each phase's prompt should re-examine its slice and reject or fix what's wrong.

**Design decisions taken before this section was authored** (see conversation that produced this plan):
- A 12th food group **Beverages** is added in Phase 14. Juices, Alcoholic beverages, Coffee & tea, Soft drinks, and Prepared soups & broths all live under it.
- A new optional `form` field on the schema (`fresh | canned | frozen | dried | cured | cooked | powdered | paste | pickled`) lets variants coexist without exploding the category tree.
- A new `caffeine` `contains` tag and a new "Caffeine-free" dietary restriction are added at the same time.
- Cuisine-based meal phases (27–31) are preserved; `recipe_taxonomy.csv` is used to **validate** that each curated meal pattern actually appears in the wild.

These phases can run in any order **within their layer** (schema → ingredients → tags → meals → audit), but the layer ordering must be respected.

---

### Phase 14 — Schema foundation: Beverages, form field, caffeine

**Goal:** Add the schema-level changes that everything downstream depends on: 12th food group, optional `form` field, `caffeine` tag, "Caffeine-free" restriction. No ingredient additions yet — this phase is infrastructure only.

**Deliverables:**
- `src/data/schema.js`:
  - Append `'Beverages'` to `FOOD_GROUPS` (12 entries now).
  - Add a Beverages entry to `FOOD_GROUP_COLORS`. Re-balance the 11 non-Dairy hues to 12 colors at ~30° spacing (12 hues + cream Dairy = 13 distinguishable slots is impractical; instead keep Dairy as the cream "no hue" slot and lay 11 hues at 360/11 ≈ 32.7° spacing). Recompute every color in `FOOD_GROUP_COLORS` to fit the new spacing rather than slotting Beverages into a leftover gap — distinguishability is the goal.
  - Add `'Beverages'` to `FOOD_GROUPS_BY_HUE` in the right position by hue.
  - Add `form` to the schema docs, the validator (optional string, must be one of the allowed values when present), and to `REQUIRED_FIELDS` as an **optional** field (not added to `REQUIRED_FIELDS` since it's optional — instead validate type when present).
- `src/core/restrictions.js`:
  - Add `'caffeine'` to the contains-tag vocabulary.
  - Add a new restriction `'Caffeine-free'` mapped to `['caffeine']`.
- `src/ui/restrictions.js` — picks up the new restriction automatically if the data flows through, but verify it renders.
- `src/ui/legend.js` — confirm the food-group legend (`FOOD_GROUPS_BY_HUE`) accommodates 12 swatches without breaking the fixed-height layout. If 12 doesn't fit cleanly in 280px tall × 220px wide, adjust grid or shrink swatches; the legend must remain symmetric with the A/P/D scheme.
- `src/data/ingredients.json`:
  - **Audit pass only** — scan existing entries for items that should now carry the `caffeine` tag (cacao, dark chocolate, chocolate, espresso flavor extracts, etc.) and add the tag. Don't add new ingredients yet.
  - Audit the `alcohol` tag: currently only ~3 entries carry it (Shaoxing wine, extracts). Confirm no existing entries should pick it up; the bulk of alcohol ingredients land in Phase 18.
- `CLAUDE.md` — bump "11 food groups" references to 12; describe `form`; describe `caffeine`.
- This `food-map-development-plan.md` — update the Phase 13.5 paragraph that lists the 11 food groups to list 12.

**Validate before moving on:**
- [ ] `node -e "import('./src/data/schema.js').then(m => console.log(m.FOOD_GROUPS.length, m.FOOD_GROUPS_BY_HUE.length))"` prints `12 12`.
- [ ] Reload the app; no console errors; the food-group legend renders 12 swatches in a layout that's still readable.
- [ ] Each food_group color is visibly distinguishable from its neighbors on the hue wheel (no two adjacent hues look the same).
- [ ] Dietary Restrictions section in the left rail now shows "Caffeine-free" as a 15th restriction; toggling it does nothing yet (no ingredient carries the `caffeine` tag after the audit — that's expected if none of the existing items contain caffeine; verify with grep).
- [ ] `validateDataset()` still passes against the unchanged ingredients.json.
- [ ] Existing aggregates (Categories view, Meals view) re-render without breakage.

---

### Phase 15 — Critical anchor ingredients (salt, one per new category)

**Goal:** Seed each of the 12 new categories with at least one canonical ingredient so the filter tree, view-levels, and aggregations have something to show. Begin with the single highest-impact gap: plain salt.

**Deliverables:**
- ~30 new entries in `src/data/ingredients.json`, each with realistic per-100g USDA values, single-group `group_weights`, and appropriate `contains` tags:
  - **Salt & seasonings** (under Herbs & spices): Salt (table), Salt (kosher), Salt (sea), Seasoned salt. Per PROJECT_UPDATES, salt is mineral, not animal/plant/dairy. Use `group_weights: [0, 1, 0]` for consistency with baking soda; document in `notes`.
  - **Bread & baked goods** (under Grains): White bread, Whole-wheat bread, Bread crumbs, Saltine crackers (rename existing if present), Graham crackers.
  - **Margarine & shortening** (under Fats & oils): Margarine (stick), Shortening (vegetable), Lard.
  - **Alcoholic beverages** (under Beverages): Red wine, Beer (lager), Vodka.
  - **Prepared mixes** (under Sweets or Grains as fits): Cake mix (yellow), Pudding mix (vanilla), Whipped topping (frozen).
  - **Processed cheese** (under Dairy): American cheese (slices), Velveeta-style processed cheese.
  - **Pickled vegetables** (under Condiments & sauces): Dill pickle, Green olives, Capers.
  - **Prepared soups & broths** (under Beverages): Chicken broth, Beef broth, Cream of mushroom soup (condensed).
  - **Coffee & tea** (under Beverages): Coffee (brewed), Black tea (brewed). Carry `caffeine` tag.
  - **Soft drinks** (under Beverages): Cola, Ginger ale. Cola carries `caffeine` tag.
  - **Jams & preserves** (under Sweets): Strawberry jam, Apple butter.
  - **Juices** (under Beverages): Orange juice, Apple juice.
- Each ingredient uses the new `form` field where meaningful (e.g., `"form": "canned"` for canned soup, `"form": "frozen"` for whipped topping, `"form": "powdered"` for cake mix).
- Apply the **single-group rule**: every ingredient picks one dominant channel. Cream of mushroom soup → `dairy` (mass-dominant). Margarine → `plant`. Eggnog edge cases not added here.
- Naming convention: parenthetical form qualifier when ambiguous: `"Salt (table)"`, `"Margarine (stick)"`, `"Cream of mushroom soup (condensed)"` — matches existing entries like "Tomato sauce (canned)".

**Validate before moving on:**
- [ ] Total ingredients grow from 864 to ~894.
- [ ] All 12 new categories now have ≥1 ingredient; the filter tree renders all 12 categories live.
- [ ] Beverages food_group appears in the tree as the 12th top-level branch with its new color from Phase 14.
- [ ] `validateDataset()` clean — no schema errors.
- [ ] In the 3D scene with default axes, salt sits at the high-sodium corner (sodium ≈ 38758 mg/100g is off the chart; verify the per-nutrient default range from `defaultConstraintFor` widens or the salt entry desaturates rather than crashes).
- [ ] Switching coloring to food_group scheme: each new category's sphere reads in the right hue.
- [ ] Each ingredient with `form` set displays it sensibly in the detail panel (chip, parenthetical in the name, or footnote — Phase 14 should have specified the UX; if it didn't, add a small chip near the category line).

---

### Phase 16 — Canonicalize and clean `MISSING_INGREDIENTS.txt`

**Goal:** Turn the ~4500-row raw candidate file into a deduplicated, garbage-filtered, categorization-sanity-checked CSV of ~700–1200 entries ready for batched addition. **No ingredients are added in this phase** — only the cleaned list is produced.

**Deliverables:**
- `scripts/clean_missing_ingredients.py` (new directory) with:
  - **Garbage filter**: drop rows whose ingredient matches placeholder prefixes (`additional`, `amount`, `any`, `extra`, `more`, `less`, `other`, `optional`, `leftover`, `prepared`, `left over`, `some`, `enough`), bare brand-only entries, and pure-quantity strings.
  - **Singular/plural canonicalization**: collapse `chiles`/`chile`/`chilies`/`chili`/`chilis` to one canonical form (`chili pepper` per dataset convention). Use a small rule table; print every collapsed group for human review.
  - **Brand stripping**: drop entries that differ only by brand name (`betty crocker x` → `x`, `kraft x` → `x`) where stripping leaves a valid generic.
  - **Form awareness**: instead of separate rows for `"dried apricot"`/`"apricot"`, collapse and produce one row plus a `proposed_form` column.
  - **Already-in-project filter**: cross-reference against `src/data/ingredients.json` and drop anything whose canonical form is already present (by `name` or close-match).
  - **Category sanity checks**: for each remaining row, run a small rule list to flag obviously-wrong proposals — e.g., any ingredient containing `"cheese"` should land under a Dairy category unless preceded by `"cracker"`, `"corn"`, `"sandwich"` (cheese cracker, corn cheese aren't cheese). Flag don't drop; output a `flags` column with reasons.
- `MISSING_INGREDIENTS_CLEAN.csv` — output file. Columns: `canonical_name`, `proposed_category`, `proposed_subcategory`, `proposed_food_group`, `proposed_form`, `proposed_contains_tags`, `flags`, `source_count` (how many raw rows collapsed into this one).
- Print a summary: starting count, dropped (garbage), dropped (already exists), collapsed (duplicates), flagged, kept.

**Validate before moving on:**
- [ ] Output CSV has 600–1500 rows (sanity range). If <600, the filter is too aggressive; if >1500, too lax.
- [ ] Spot-check 30 random rows: each looks like a real, distinct ingredient.
- [ ] Spot-check the canonicalization log: `anaheim` group collapsed into one row, `salt` group not in output (already added in Phase 15), `cracker barrel` brand stripped or flagged.
- [ ] Every row's `proposed_food_group` is one of the 12 valid food groups.
- [ ] Re-run with `--diff` to confirm idempotency: a second run produces an identical CSV.

---

### Phase 17 — Ingredient batch: Grains expansion

**Goal:** Add ingredients from the cleaned list whose `proposed_food_group` is `Grains`. Covers Bread & baked goods (the largest new category — biscuits, breads, cookies, crackers, croutons, flatbread, muffins, pastries, pizza dough, pretzels, rolls, tortillas, wrappers) plus Refined grains (pasta, noodles) and Whole grains additions.

**Deliverables:**
- ~80 new entries in `src/data/ingredients.json` selected from `MISSING_INGREDIENTS_CLEAN.csv` rows with `proposed_food_group = Grains`.
- Use the cleaned proposals as the starting point; **override category/subcategory when the proposal is wrong**.
- USDA-style per-100g nutrient values for every entry.
- `contains` tags: most carry `gluten`; egg-pasta carries `gluten` + `eggs`; some refined-grain breads carry `dairy` if milk-based.
- Single-group rule: all grains = `[0, 1, 0]` (plant) — egg noodles too (grain-dominant by mass; the `eggs` tag handles the dietary restriction side).
- `form` field set where meaningful (`fresh` for bread, `dried` for pasta, `frozen` for pre-made pizza dough).

**Validate before moving on:**
- [ ] Total ingredients ~970–980.
- [ ] Bread & baked goods now has 30–50 entries spread across 12+ subcategories from MISSING_SUBCATEGORIES.
- [ ] Filter tree renders the category tree without overflow; a search for "bread" returns 10+ results.
- [ ] In the scene, breads cluster in the high-carb / mid-cal region; saltines/crackers sit near it but with higher sodium.
- [ ] `validateDataset()` clean.

---

### Phase 18 — Ingredient batch: Beverages

**Goal:** Populate the new Beverages food group across all five of its categories: Alcoholic beverages, Coffee & tea, Soft drinks, Juices, Prepared soups & broths.

**Deliverables:**
- ~80–100 new entries from `MISSING_INGREDIENTS_CLEAN.csv` with `proposed_food_group = Beverages`.
- **Alcoholic beverages** (~30): wines (red, white, rosé, sparkling, port, sherry, vermouth), beers (lager, IPA, stout, ale, cider), spirits (vodka, gin, rum, whisky, tequila, brandy), liqueurs (amaretto, kahlua, baileys-style, triple sec, absinthe). Every entry carries `alcohol` contains tag.
- **Coffee & tea** (~10): brewed coffee, espresso, instant coffee, black tea, green tea, herbal tea (caffeine-free), matcha, chai concentrate. Every caffeinated entry carries the `caffeine` tag; herbal/decaf entries do not.
- **Soft drinks** (~15): colas (regular, diet), lemon-lime sodas, root beer, ginger ale, tonic water, sports drinks, energy drinks (caffeine), iced tea (bottled, sweetened/unsweetened).
- **Juices** (~10): orange, apple, grape, cranberry, pineapple, grapefruit, tomato, vegetable, lemonade.
- **Prepared soups & broths** (~15): chicken broth, beef broth, vegetable broth, bone broth, miso broth, cream-of varieties (mushroom, celery, chicken), chicken noodle, tomato, French onion. `form: 'canned'` or `form: 'paste'` (bouillon) as appropriate.
- All entries get realistic per-100g nutrient values. Alcoholic entries: include their ethanol-derived calorie content (~7 kcal/g alcohol). Use USDA references.
- Single-group rule: all = `[0, 1, 0]` (plant) except broths derived from animal stock (`[1, 0, 0]`) and cream-based soups (`[0, 0, 1]`).

**Validate before moving on:**
- [ ] Total ingredients ~1050–1080.
- [ ] Beverages food_group appears as a populated top-level branch in the filter tree with 5 categories under it.
- [ ] Toggle "Halal" dietary restriction → every alcohol-tagged ingredient (now 30+) disappears from the scene and table. Same for "Caffeine-free" → coffee, tea, cola, energy drinks vanish.
- [ ] Beverages cluster: most sit near low-cal / low-protein corner; sweetened sodas drift toward high-carb; liqueurs sit at moderate carb + high cal (sugar + alcohol).
- [ ] `validateDataset()` clean.

---

### Phase 19 — Ingredient batch: Sweets, Prepared mixes, Jams & preserves

**Goal:** Add cleaned candidates whose `proposed_food_group` is `Sweets`, covering Prepared mixes (cake/cookie/pudding/pie filling/gelatin/baking), Jams & preserves, and direct sweets expansions.

**Deliverables:**
- ~70 new entries.
- **Prepared mixes** (~30): cake mixes (yellow, chocolate, white, devil's food, angel food, carrot, lemon, spice), brownie mix, cookie mix, pudding mixes (vanilla, chocolate, butterscotch, pistachio), pie fillings (cherry, apple, blueberry, lemon), gelatins (assorted flavors), baking mixes (Bisquick-style, pancake), whipped toppings (frozen, aerosol). `form` field used heavily here (`powdered`, `frozen`, `canned`).
- **Jams & preserves** (~15): strawberry jam, raspberry jam, blueberry jam, grape jelly, mixed berry preserves, orange marmalade, apricot preserves, apple butter, pumpkin butter, lemon curd, fruit chutney.
- **Sweets additions** (~25): from cleaned candidates — various confections (caramel, fudge, marshmallow, fondant, taffy, brittle, toffee, butterscotch, marzipan), additional chocolates (white, milk, dark variations), syrups (corn, cane, maple — verify not already present), drink mix concentrates.
- Single-group rule: mostly `plant`; dairy-dominant items (whipped topping with dairy, dairy-cream-based mixes) get `dairy`.
- `contains` tags: dairy mixes get `dairy`; chocolate carries `caffeine` (per Phase 14 audit if not already); some baking mixes carry `gluten`, `eggs`.

**Validate before moving on:**
- [ ] Total ingredients ~1110–1150.
- [ ] Sweets food_group has 70+ entries across at least 5 subcategories.
- [ ] Prepared mixes appears as a populated category; angel food / yellow / chocolate cake mixes all show in search.
- [ ] Chocolate-related items in detail panel show `caffeine` tag (sanity check).
- [ ] Sweets cluster in 3D dominates the high-carb / high-sugar region; jams pull toward high-sugar specifically.

---

### Phase 20 — Ingredient batch: Dairy + Processed cheese

**Goal:** Expand the Dairy food_group with the new Processed cheese category and additional aged/fresh varieties surfaced by the RecipeNLG dataset.

**Deliverables:**
- ~50 new entries.
- **Processed cheese** (~12): American (slices, deli), Velveeta-style, processed shredded blends (Mexican blend, Italian blend, cheddar+Jack), cheese spreads (Cheez Whiz-style), individually-wrapped slices, processed string cheese.
- **Aged cheese additions** (~15): pecorino romano, Asiago, Manchego, Gruyère, Comté, fontina, Gouda (aged), Edam, provolone, Havarti, Monterey Jack, pepper Jack, Colby, Muenster, Limburger.
- **Fresh cheese additions** (~8): mascarpone, burrata, queso fresco, queso blanco, panela, halloumi, paneer (verify not present), cottage cheese (variants — small/large curd).
- **Frozen dairy** (~8): ice cream variants (vanilla, chocolate, strawberry, mint choc chip, cookies & cream), frozen yogurt, sorbet (note: sorbet is dairy-free; channel?), gelato, ice cream sandwiches.
- **Fermented dairy / Milk extras** (~7): buttermilk, evaporated milk, condensed milk (sweetened), kefir variants, skyr, quark.
- All `[0, 0, 1]` (dairy channel) except sorbet (plant — flag `dairy_free`).
- `contains: ['dairy']` on every entry except sorbet.
- `form` field: `'aged'` for hard cheese, `'fresh'` for soft, `'frozen'` for frozen dairy.

**Validate before moving on:**
- [ ] Total ingredients ~1160–1200.
- [ ] Dairy food_group has 120+ entries.
- [ ] Toggle "Dairy-free" restriction → every new dairy ingredient disappears.
- [ ] Aged cheese cluster in 3D sits high-fat / high-protein / mid-sodium.

---

### Phase 21 — Ingredient batch: Fats, oils, margarine, shortening

**Goal:** Round out the Fats & oils food_group with the new Margarine & shortening category and additional cooking oils.

**Deliverables:**
- ~25 new entries.
- **Margarine & shortening** (~10): margarine (stick, tub, light, with butter), shortening (vegetable, butter-flavor), lard, tallow (beef), duck fat, schmaltz (chicken fat), bacon fat.
- **Oils additions** (~15): from cleaned list — peanut oil, grapeseed oil, sunflower oil, safflower oil, rice bran oil, palm oil, walnut oil, hazelnut oil, flaxseed oil, MCT oil, ghee (clarified butter — verify category), truffle oil, chili oil (infused), tea seed oil.
- Animal-derived fats (lard, tallow, duck fat, schmaltz, bacon fat) → `[1, 0, 0]` animal channel, `contains: ['meat']` (and `pork` for lard/bacon).
- Plant oils → `[0, 1, 0]` plant.
- Margarine → `[0, 1, 0]` plant (most margarine is plant-based; carry `dairy` tag for entries that include dairy).

**Validate before moving on:**
- [ ] Total ingredients ~1185–1225.
- [ ] Margarine & shortening category renders in tree with 10 entries.
- [ ] Halal restriction now hides pork-derived fats (lard, bacon fat).
- [ ] Fats sit near high-calorie / low-carb / low-protein corner; the cluster is dense and pure.

---

### Phase 22 — Ingredient batch: Vegetables + Pickled vegetables + Fruits

**Goal:** Add cleaned candidates from Vegetables and Fruits food_groups, including the new Pickled vegetables category (under Condiments & sauces).

**Deliverables:**
- ~70 new entries combined.
- **Pickled vegetables** (~12): dill pickle (spear, chip), bread-and-butter pickle, sweet pickle, gherkin, cornichon, kalamata olive, green olive (stuffed, plain), pickled jalapeño, pickled banana pepper, sauerkraut (verify not present), kimchi (verify not present), pickled beet, pickled okra.
- **Non-starchy vegetables additions** (~20): from cleaned list — various chili pepper canonical forms (anaheim, ancho, chipotle, habanero, jalapeño, poblano, serrano, scotch bonnet — verify), additional alliums (shallot, leek, scallion variants), fiddleheads, sunchokes, watercress, bok choy, napa cabbage, daikon, lotus root, taro root, etc.
- **Starchy vegetables additions** (~10): purple potato, fingerling potato, blue potato, plantain (green/ripe), cassava (yuca), malanga, breadfruit.
- **Fruits additions** (~25): from cleaned list — exotic fruits (durian, jackfruit, dragon fruit, rambutan, lychee, longan, mangosteen, passionfruit, persimmon, quince, kumquat, sapote, soursop, tamarind, ackee), additional citrus (yuzu, blood orange, calamansi, mandarin, pomelo), additional stone fruits, additional berries (boysenberry, gooseberry, currant, elderberry).
- Carry `form` where the entry is canned/dried/frozen variant of a fresh produce item.

**Validate before moving on:**
- [ ] Total ingredients ~1255–1295.
- [ ] Pickled vegetables category renders with ~10 entries.
- [ ] Fruits and Vegetables both have ≥80 entries each.
- [ ] Filter tree's deep subcategories (Chili peppers, Stone fruits, etc.) populate further.

---

### Phase 23 — Ingredient batch: Spices, condiments, seasonings, sauces

**Goal:** Round out Herbs & spices and Condiments & sauces with cleaned candidates, including the new Spice blends expansions and Coffee & tea (handled in Phase 18 already, so this is mostly spices and sauces).

**Deliverables:**
- ~70 new entries.
- **Salt & seasonings** (additions to Phase 15 anchors, ~8): seasoned salt, garlic salt, celery salt, onion salt, Old Bay (regional blend), pickling salt, MSG.
- **Spice blends additions** (~15): from cleaned list — jerk seasoning, garam masala (verify), curry powder variants, Chinese five-spice, ras el hanout, za'atar, dukkah, herbes de Provence, fines herbes, Cajun seasoning, Creole seasoning, taco seasoning, ranch seasoning, Italian seasoning, lemon-pepper.
- **Dried spices additions** (~15): from cleaned list — long-tail spices, additional chili powders (chipotle powder, gochugaru, Aleppo, Espelette), additional whole spices (juniper, fenugreek, asafoetida, sumac, mahleb, nigella, ajwain).
- **Fresh herbs additions** (~5): chervil, lovage, lemon balm, sorrel, salad burnet.
- **Condiments & sauces additions** (~25): from cleaned list — additional hot sauces (sriracha, gochujang, sambal oelek, harissa — verify), Asian sauces (oyster, fish, hoisin, plum, black bean — verify), salad dressings (Caesar, blue cheese, thousand island, French, balsamic vinaigrette, honey mustard, Greek), mustards (Dijon, whole grain, English, Chinese hot), vinegars (sherry, malt, champagne, coconut, banyuls), nut/seed pastes (tahini variants).

**Validate before moving on:**
- [ ] Total ingredients ~1325–1365.
- [ ] Spice blends now spans most cuisines (American, Indian, Mediterranean, Middle Eastern, Mexican, Cajun).
- [ ] `validateDataset()` clean across the entire dataset.
- [ ] Filter tree's largest categories are still navigable — if any category exceeds 60 entries, consider deeper subcategorization in Phase 25.

---

### Phase 24 — Final ingredient sweep & dataset validation

**Goal:** Catch remaining cleaned-list candidates that didn't fit a prior batch (Nuts & seeds extras, Protein expansions, organ meats, regional fish, etc.), and run a comprehensive validation pass on the full dataset.

**Deliverables:**
- ~40–80 remaining new entries from `MISSING_INGREDIENTS_CLEAN.csv`:
  - **Nuts & seeds**: macadamia, Brazil nut, pine nut variants, chestnut, melon seeds, lotus seeds, watermelon seed, hemp seed (verify), chia (verify).
  - **Protein (animal)**: additional fish (catfish, perch, walleye, swordfish, mahi-mahi, bluefish, bass varieties), shellfish (abalone, octopus, squid, conch, langoustine, prawn), organ meats (sweetbreads, brain, marrow, gizzards), wild game (rabbit, venison, elk, bison, ostrich, alligator), additional cured/processed (mortadella, capicola, soppressata, andouille, kielbasa, chorizo Mexican vs Spanish).
  - **Protein (plant)**: additional legumes (edamame fresh, mung bean, urad dal, masoor dal, fava, lupini), additional soy products (yuba, natto, freeze-dried tofu).
  - Anything else cleaned but uncategorized — review and fit or document why it's dropped.
- **Comprehensive validation pass**:
  - Write or update `scripts/validate_full_dataset.py` (or inline in `test-data.html`) checking: no duplicate ids, every `food_group` ∈ FOOD_GROUPS, every category has ≥2 ingredients OR is documented as singleton-acceptable, every `group_weights` sums to 1.0 and has exactly one channel = 1, every nutrient value is non-negative, every `form` value is in the allowed set, every `contains` tag is in the vocabulary.
  - Print a coverage report: which food_groups grew most; which categories are largest; sphere distribution across the 3D cube octants (should be reasonably even).

**Validate before moving on:**
- [ ] Final ingredient count: 1300–1450.
- [ ] Every food_group has ≥3 categories; every category has ≥2 ingredients.
- [ ] No category contains >60 ingredients (if any do, flag for Phase 25 subcategory split).
- [ ] Cross-reference with `MISSING_INGREDIENTS_CLEAN.csv`: report how many cleaned candidates were added vs. skipped, with reasons for skipped.
- [ ] App launches with the full dataset; performance still acceptable on a mid-range phone.
- [ ] `validateDataset()` clean.

---

### Phase 25 — Subcategory refinement & category splits

**Goal:** Any category that grew to >50 entries from the data expansion gets split into subcategories. Existing subcategory misses surfaced by `MISSING_SUBCATEGORIES.txt` (Stalks, Bulbs, Pasta, Noodles, etc. inside existing categories) get applied.

**Deliverables:**
- For each oversized category, propose and implement a subcategory split. Update affected ingredients to point at the new subcategory.
- Apply the existing-category subcategory additions from `MISSING_SUBCATEGORIES.txt` (rows with `category_status = existing`).
- Verify subcategory aggregates (the "By subcategory" Categories view from Phase 13.5 round 7) render sensibly across the new structure.
- No new ingredients; this is a refactor of `category`/`subcategory` fields only.

**Validate before moving on:**
- [ ] No category has >50 ingredients.
- [ ] Every category has ≥2 subcategories (avoiding singletons — see PROJECT_UPDATES_NEEDED section J).
- [ ] By-subcategory view in the app renders ~120–180 aggregate spheres, well-spread.
- [ ] No ingredient lost its mapping (count unchanged from Phase 24).

---

### Phase 26 — Cross-category `tags` (original Phase 14 multi-tagging)

**Goal:** Add a `tags` array per ingredient for cross-category labels orthogonal to `food_group`/`category`/`subcategory`/`contains`. These are user-facing facets the app can filter by independent of the food hierarchy.

**Deliverables:**
- `src/data/schema.js` — add `tags` as an optional string array; document the vocabulary.
- Suggested initial vocabulary: `breakfast`, `snack`, `dessert`, `condiment`, `garnish`, `cooking-ingredient` (vs. eat-as-is), `high-protein` (computed: protein/100g ≥ 20g), `high-fiber`, `low-cal` (<100 kcal/100g), `iron-source`, `omega3-source`, `fermented`, `traditional-fermented` (kimchi/sauerkraut/miso/natto), `cured`, `smoked`, `raw-edible`. Keep the vocabulary small and meaningful — don't pad.
- Backfill `tags` across the full dataset. Most entries get 0–3 tags; some computed tags (`high-protein`, `low-cal`) can be auto-populated from nutrient values.
- `src/ui/ingredient-filter.js` — extend with a tag-filter UI section (collapsible, multi-select). Active tag filters compose with the ingredient tree filter (AND).
- `src/core/filters.js` — accept tag filters in the active-set computation.

**Validate before moving on:**
- [ ] Every ingredient has a `tags` array (possibly empty).
- [ ] Toggling `high-protein` filter highlights egg whites, chicken breast, whey, tuna, etc.
- [ ] Toggling `fermented` highlights kimchi, miso, sauerkraut, kefir, yogurt, sourdough.
- [ ] Tag filter composes with ingredient tree (AND), dietary restrictions (AND), and thresholds.
- [ ] App still loads cleanly; persistence migration adds empty `tags` to any persisted user-meals if needed.

---

### Phase 27 — Meal patterns: Western & European (CSV-validated)

**Goal:** Add Western/European meals to `meals.json`. Each authored meal is **validated** against `recipe_taxonomy.csv` — its `ingredient_categories` pattern must appear in real recipes.

This is the first cuisine phase, so it also establishes the CSV-validation tooling that the remaining cuisine phases reuse.

**Deliverables:**
- `scripts/validate_meal_pattern.py` — given a list of category names, scans `recipe_taxonomy.csv` (streaming, never loads into memory) and reports: how many recipes have all those categories present, plus sample titles. Stays under a few hundred MB of memory by streaming.
- ~60–100 new meals in `src/data/meals.json`:
  - **American**: pancakes & syrup, burgers (varieties), mac and cheese, cobb salad, BBQ plates, Thanksgiving plate, biscuits and gravy, chicken and waffles, club sandwich, Reuben.
  - **UK / Irish**: full English breakfast, fish and chips, shepherd's pie, ploughman's lunch, Sunday roast, bangers and mash, beef Wellington, scones with clotted cream.
  - **French**: croque-monsieur, ratatouille, beef bourguignon, niçoise salad, omelette, coq au vin, bouillabaisse, quiche Lorraine, cassoulet.
  - **Italian**: caprese, pasta (carbonara, bolognese, pesto, amatriciana, puttanesca, vongole), risotto (mushroom, milanese), pizza variants (margherita, marinara, quattro stagioni), osso buco.
  - **Spanish / Portuguese**: paella, tortilla española, tapas plates, gazpacho, bacalhau dishes, patatas bravas, pulpo a la gallega.
  - **German / Austrian / Swiss**: schnitzel platter, rösti, sauerbraten, raclette, muesli, spätzle, currywurst.
  - **Eastern European**: pierogies, borscht, goulash, blini and caviar, golabki, bigos.
  - **Scandinavian**: smörgåsbord, gravlax plate, meatballs and lingonberry, gravadlax, lutefisk.
- For each meal: run `validate_meal_pattern.py` with the meal's `ingredient_categories`. If the pattern matches <10 recipes in the CSV, reconsider — is the meal too narrow, too generic, or genuinely rare?
- Add a `cuisine` field on each meal for future filtering (e.g., `'American'`, `'Italian'`).

**Validate before moving on:**
- [ ] ~60+ new meals added; recognizable staples present.
- [ ] Every meal has a `cuisine` tag.
- [ ] Each meal's `ingredient_categories` appears in ≥10 NLG recipes (or is documented as a deliberate broader/narrower pattern).
- [ ] Color blending varies across the cuisine cluster.
- [ ] Meal aggregations recompute and render in the Meals view-level.

---

### Phase 28 — Meal patterns: East & Southeast Asian (CSV-validated)

**Goal:** Comprehensive Asian meal patterns; reuse `validate_meal_pattern.py` from Phase 27.

**Deliverables:**
- ~60–100 new meals:
  - **Chinese (Cantonese / Sichuan / Northern / Shanghainese)**: stir-fries (kung pao, sweet & sour, broccoli beef, twice-cooked pork), dim sum plates, mapo tofu, dumplings (har gow, siu mai, jiaozi, xiao long bao), congee, hot pot, lion's head meatballs, Peking duck.
  - **Japanese**: sushi platters (nigiri, maki), ramen variants (shoyu, miso, tonkotsu), donburi (gyudon, oyakodon, katsudon), tempura, okonomiyaki, soba/udon, tonkatsu, sukiyaki, shabu-shabu.
  - **Korean**: bibimbap, bulgogi plate, kimbap, jjigae (kimchi, sundubu, doenjang), Korean BBQ, japchae, samgyetang.
  - **Thai**: pad thai, tom yum, green/red/massaman curry, som tam, larb, khao soi.
  - **Vietnamese**: pho (bò, gà), banh mi, bun bo hue, summer rolls, bun cha, com tam.
  - **Indonesian / Malay**: nasi goreng, rendang, laksa, satay plate, gado-gado, mee goreng.
  - **Filipino**: adobo, sinigang, lumpia, kare-kare, pancit.
- Each meal CSV-validated.

**Validate:**
- [ ] Recognizable staples across every sub-cuisine.
- [ ] All meals CSV-validated against `recipe_taxonomy.csv` (≥10 matches each, or documented exception).

---

### Phase 29 — Meal patterns: South Asian, Middle Eastern, North African (CSV-validated)

**Deliverables:**
- ~60–100 new meals across:
  - **Indian (regional: North, South, East, West)**: dals, curries (butter chicken, tikka masala, vindaloo, korma, rogan josh, jalfrezi), biryanis (chicken, mutton, vegetable, hyderabadi), dosas + chutney + sambar, thali, idli, paneer dishes, chaat plates.
  - **Pakistani / Bangladeshi**: nihari, haleem, biryanis, fish curry (Bengali), chapli kebab.
  - **Sri Lankan**: rice and curry, hoppers, kottu.
  - **Levantine**: mezze plates (hummus, baba ganoush, tabbouleh, fattoush, labneh), kibbeh, shawarma, manakish, kafta, fattet.
  - **Iranian**: kabab koobideh plate, ghormeh sabzi, fesenjan, tahdig, ash reshteh.
  - **Turkish**: kebab variants (adana, urfa, döner, shish), meze, dolma, börek, lahmacun, künefe, manti.
  - **North African (Moroccan, Tunisian, Egyptian)**: tagines (chicken-preserved-lemon, lamb-prune, fish), couscous platters, harira, ful medames, koshari, brik, b'stilla.
- Each CSV-validated. Note that NLG dataset is American-leaning so some patterns will match few recipes — document where that's the case.

**Validate:**
- [ ] Recognizable staples across all three regional clusters.

---

### Phase 30 — Meal patterns: Sub-Saharan African, Latin American, Caribbean (CSV-validated)

**Deliverables:**
- ~60–100 new meals:
  - **West African**: jollof rice, egusi soup, suya, fufu and stew, peanut stew (groundnut), thieboudienne.
  - **East African (Ethiopian / Kenyan)**: injera with assorted stews (doro wat, misir wat, alicha, kitfo), ugali and sukuma wiki, pilau.
  - **Southern African**: bobotie, bunny chow, biltong plate, pap and chakalaka.
  - **Mexican**: tacos (al pastor, carnitas, fish, lengua, barbacoa), enchiladas, mole, tamales, chilaquiles, pozole, sopes, tlayudas.
  - **Brazilian**: feijoada, moqueca, churrasco plate, pão de queijo, acarajé.
  - **Peruvian**: ceviche, lomo saltado, ají de gallina, anticuchos, papa a la huancaína.
  - **Argentine / Uruguayan**: asado plate, milanesa, empanadas, chimichurri-grilled meat.
  - **Caribbean**: jerk chicken plate, ackee and saltfish, ropa vieja, oxtail stew, callaloo, roti.

**Validate:**
- [ ] Variety across continents and traditions.

---

### Phase 31 — Meal patterns: snacks, desserts, cross-cultural beverages (CSV-validated)

**Deliverables:**
- ~40–60 new meals:
  - **Snacks**: cheese plates, charcuterie, nut and dried fruit mixes, popcorn variants, chip and dip combos, fresh fruit plates, hummus and crudités.
  - **Desserts**: cakes (chocolate, carrot, cheesecake, tres leches, red velvet), pies (apple, pumpkin, pecan, key lime), ice cream sundaes, tiramisu, baklava, halwa, mochi, gulab jamun, churros, crème brûlée, panna cotta.
  - **Beverages**: smoothies (green, berry, protein), lattes/cappuccinos, matcha drinks, masala chai, boba tea, lassis, horchata, fresh juices, agua fresca.
  - **Composed plates**: continental breakfast, afternoon tea spread, brunch platter, kids' lunchbox.

**Validate:**
- [ ] Sweet-dominated meals produce visibly different color blends from savory ones.
- [ ] Beverage entries make sense as meals (or document why a separate `meal_type` field would help).

---

### Phase 32 — Final coverage audit & meta-validation

**Goal:** One final integrative pass: confirm the project meets the coverage targets PROJECT_UPDATES_NEEDED.txt section J set out, surface any remaining gaps, and document what was deliberately skipped.

**Deliverables:**
- `scripts/coverage_report.py` — runs against `recipe_taxonomy.csv` and reports:
  - Percent of recipe-ingredient occurrences in NLG that map cleanly to a project category (target: ≥95%, i.e. <5% uncategorized).
  - Distribution: ingredients per food_group; categories per food_group; subcategories per category.
  - Any food_group with fewer than 2 categories; any category with fewer than 2 subcategories.
  - Any category with >50 ingredients (should have been split in Phase 25).
- `docs/data-coverage.md` (new) — written summary of the final dataset: counts, gaps that were intentionally not filled (with reasons), and a "future expansion" section for entries we'd add given more time.
- Update `README.md` and `CLAUDE.md` data section to reflect the final ingredient/category/meal counts.
- Spot-check the 3D scene with the full dataset: every octant of the cube has at least a few ingredients; the color story still reads (animal-red, plant-green, dairy-cream/yellow); switching to food_group scheme shows 12 distinct color clusters.

**Validate before moving on:**
- [ ] Coverage report: <5% of recipe-ingredient occurrences uncategorized.
- [ ] Final counts noted in CLAUDE.md (e.g., ~1400 ingredients, ~50 categories, ~150 subcategories, ~300 meals, 12 food_groups).
- [ ] No category exceeds 50 entries; no food_group has fewer than 2 categories; no category has fewer than 2 subcategories.
- [ ] App loads with the full dataset; performance still acceptable on mobile.
- [ ] `validateDataset()` clean.
- [ ] Manual walk-through: every dietary restriction filters the expected count of items; every threshold-mode (Filter/Highlight/Score) still works; every view-level (Foods/Categories/Meals) renders.

---

## Compositional dieting (Phases 33–39)

These phases shift the meals layer from a curated set of named dishes to a compositional substrate the user can explore, mutate, and extend. The conceptual move: a *meal* is a category combination, not a fixed exemplar. Diets, restrictions, and remixes all reduce to the same primitive — sets of categories added or removed from the composition.

The named meals from Phases 27–31 remain unchanged. Everything in this section *adds*.

Two distinct filter modes are introduced and kept conceptually separate throughout:
- **Option A — visibility filtering**: hide / show meals based on whether their composition matches a rule. The chart shows a subset of the unchanged data.
- **Option B — composition modification**: recompute meal aggregates as if a category were added to or removed from every meal. Meal dots reposition; nothing is hidden.

Phase 33 completes Option A. Phase 35 introduces Option B. Phase 37 applies Option B at the per-meal level.

---

### Phase 33 — Complete Option A: bidirectional Meals filters

**Goal:** Extend the existing Meals filter UI so the Ingredients and Categories filters support both include-required and exclude-disallowed semantics. The existing slots are inclusion-only (`foodGroupsExcluded` is the only exclusion slot today); this finishes Option A before Phase 35 adds Option B, keeping the two mental models cleanly separated. The tri-state +/− control introduced here is reused by Phase 35.

**Deliverables:**
- `src/state.js` — extend `mealFilters`:
  - `ingredientIds: string[]` (existing — must contain all)
  - `ingredientIdsExcluded: string[]` (new — meals containing any are hidden)
  - `categories: string[]` (existing — must contain all)
  - `categoriesExcluded: string[]` (new — meals containing any are hidden)
- `src/ui/meal-builder.js` — each ingredient / category row in the dropdowns gains a tri-state +/− control: untouched / include / exclude. Counter chips on dropdown buttons show both directions ("3+ / 2−").
- `src/core/aggregations.js` (or the meal-visibility predicate) — extend the predicate to honor both exclusion arrays.
- Confirm `mealFilters` persists as a unit (no additional `PERSISTABLE_KEYS` changes needed).

**Validate:**
- [ ] Excluding "Aged cheese" hides carbonara, caesar, mac & cheese, etc.
- [ ] "+ Poultry" combined with "− Whole grains" shows only poultry meals without whole grains.
- [ ] Tri-state control reads correctly: untouched / + / − visibly distinct.
- [ ] Persistence round-trips through reload.

---

### Phase 34 — Diet-compatibility tags and frequency field on meals

**Goal:** Bridge the dietary-restrictions vocabulary into the meals layer, and add a frequency field that Phase 36 will populate from the corpus.

**Deliverables:**
- `src/data/schema.js` — new `DIETS` export. Suggested initial set: `keto`, `paleo`, `mediterranean`, `whole30`, `lowfodmap`, `high_protein`. Each diet maps to category exclusions / inclusions / nutrient rules.
- `src/core/diet-compatibility.js` (new) — `computeDietCompatibility(meal, categoryAggregates)` returns the array of `DIETS` keys the meal satisfies (combining category-exclusion rules and nutrient rules).
- `src/data/meals.json` — every meal gains `diet_compatibility: string[]`, `frequency: number` (1 for curated, real counts for Phase 36 corpus meals), and `source: 'curated'`.
- `scripts/phase34_apply.py` — backfills the three fields on all 333 existing meals.

**Validate:**
- [ ] Every meal has `diet_compatibility`, `frequency`, `source`.
- [ ] Spot check: pasta carbonara excludes from keto and mediterranean; vegan-bowl includes mediterranean; pho-bo includes paleo.

---

### Phase 35 — Composition overlay (left-rail compose-meals filter, Option B)

**Goal:** Add a global composition modifier — the user can force-include or force-exclude categories across every meal aggregate. Meal dots reposition in real time. This is the engine for compositional dieting.

**Deliverables:**
- `src/state.js` — new state key `mealComposition: { added: string[], removed: string[] }`.
- `src/core/aggregations.js` — extend `aggregateMeals(ingredients, meals, composition?)`. For each meal, the effective category list becomes `(meal.ingredient_categories ∪ composition.added) \ composition.removed`; aggregate recomputes with the modified list. If a meal becomes empty after removal, it's hidden.
- `src/ui/compose-meals.js` (new) — left-rail section "Compose meals" below the existing meal filters. Each category row has +/− buttons (matching Phase 33's tri-state pattern).
- `src/core/persistence.js` — `mealComposition` added to `PERSISTABLE_KEYS`.
- Visual feedback: meal dots animate to new positions (~300ms tween) when composition changes.

**Validate:**
- [ ] Removing `Refined grains` globally — every grain-containing meal shifts down on carbs.
- [ ] Adding `Oils` globally — every meal shifts toward the high-cal corner.
- [ ] Persistence survives reload.
- [ ] Removing all categories from a meal hides it (no NaN positions).
- [ ] Composition recompute + re-render < 50ms for the full meal set.

---

### Phase 36 — Corpus itemset extraction → compositional meal patterns

**Goal:** Extract frequent category itemsets from `recipe_taxonomy.csv` and add them as compositional meals (`source: 'corpus'`). The discovery layer — patterns real cooking exhibits but no human curated.

**Deliverables:**
- `scripts/extract_meal_patterns.py` (new):
  - Streams `recipe_taxonomy.csv`.
  - Runs FP-growth (or Apriori) on the `categories` field with `min_support = 100` (configurable).
  - Deduplicates against curated meals — if a curated meal already has the exact category set, increment its `frequency` instead of adding a duplicate.
  - Writes to `src/data/compositional-meals.json` (separate from `meals.json`).
- `src/main.js` — loads both files; concatenates into the meals dataset.
- `src/scene/points.js` — `source: 'corpus'` meals render at ~70% opacity and slightly smaller dot scale so curated dots stay visually anchored.
- `src/ui/view-controls.js` — sub-toggle under the Meals view-level: "Named only / Compositional only / Both" → `state.mealSourceFilter`.

**Validate:**
- [ ] Extraction completes < 5 minutes on the 800MB corpus.
- [ ] At min-support 100, output is 500–3000 patterns. If outside, document the chosen support in the script header.
- [ ] ≥80 % of named meals match an extracted pattern's category set (confirms extraction picks up known patterns).
- [ ] "Named only" / "Compositional only" / "Both" toggles behave correctly.

---

### Phase 37 — Per-meal remix (right-rail composition editor)

**Goal:** Click any meal (curated or compositional) and remix its category set in the right rail. Live recomputation; save-as-new-meal flow ties into user meals.

**Deliverables:**
- `src/ui/detail-panel.js` — adds a "Remix" section to the meal detail view:
  - Lists current `ingredient_categories` with **−** buttons; an "Add category" autocomplete adds new ones.
  - Mutations recompute the meal's centroid live; the dot moves while the panel is open.
  - "Save as new meal" prompts for a name → writes to `userMeals` (Phase 9 plumbing).
  - "Reset" reverts to the original. Draft badge visible while modified-and-unsaved.
- `src/state.js` — new `mealDraft: { mealId, categories } | null`. Session-scoped, not persisted.
- `src/scene/points.js` — when `mealDraft` is set, override that meal's position with the draft centroid.

**Validate:**
- [ ] Click carbonara → remove "Aged cheese" → dot shifts; draft badge appears.
- [ ] Save as "Carbonara minus cheese" → new entry in user meals; original carbonara unchanged.
- [ ] Reset → dot springs back; badge clears.
- [ ] Closing the panel clears the draft.

---

### Phase 38 — Active filters chip rail

**Goal:** With composition + diet-compat + ingredient filter + tag filter + restrictions + thresholds all potentially simultaneous, the user needs an at-a-glance summary of what's currently constraining the view.

**Deliverables:**
- `src/ui/active-filters.js` (new) — corner-anchored panel next to the Axes and Color guide panels. Each active filter renders as a removable chip:
  - "Vegan", "Caffeine-free", … (restrictions)
  - "Cal ≤ 500 kcal", "Protein ≥ 20g" (non-baseline thresholds)
  - "+ olive oil", "− gluten" (composition overlay)
  - "high-protein", "fermented" (tag filter)
  - "ingredients: 132/1362" (when ingredient tree is filtered)
  - "draft: carbonara" (active mealDraft)
- Each chip has an inline `×` that clears that filter; "Clear all" button at the bottom.
- Same collapse-to-pill pattern as the legend and axes panels.
- Auto-hides when no filters are active.

**Validate:**
- [ ] Toggle Vegan + protein threshold + composition removal → three chips appear; chart shifts.
- [ ] Click one chip's × → that filter clears; chart re-renders.
- [ ] "Clear all" returns view to unfiltered.
- [ ] Long filter lists wrap rather than overflow.

---

### Phase 39 — Taxonomy refinement from corpus discoveries

**Goal:** Phase 36's extraction may surface category pairs that always co-occur (merge candidates) or categories appearing in many small itemsets (split candidates). This phase examines the output and refines the taxonomy. Closes the loop opened in Phase 25.

**Deliverables:**
- `scripts/analyze_extraction.py` (new) — reports top patterns, category co-occurrence anomalies, candidates for merge/split/rename.
- Manual review → `scripts/phase39_taxonomy.py` applies decided adjustments.
- Re-runs Phase 25's invariants (no category > 50, every food_group ≥ 2 categories, etc.).
- `compositional-meals.json` regenerated if any category names changed.
- `docs/data-coverage.md` updated.

**Validate:**
- [ ] `validate_full_dataset.py` clean.
- [ ] Every existing meal's `ingredient_categories` still resolves.
- [ ] Coverage doc reflects new counts.

---

#### Rollout notes (Phases 33–39)

- **Phase 33 first** — small, fast, closes the Option-A gap, and establishes the +/− tri-state UI pattern that Phases 35 and 37 reuse.
- **Phase 34** is the cheapest data-only step (~1 hour). May already answer the original keto-spread question on its own.
- **Phase 35** is the conceptual core of compositional dieting.
- **Phase 36** is the largest data drop; if min-support 100 produces too many dots, raise to 500 or 1000.
- **Phase 38 should land before too many filter axes accumulate** — don't push past Phase 37.
- **Phase 39** could in principle go before 36 but the extraction output is what reveals the taxonomy gaps, so after is more natural.

Each phase delivers user-visible value alone. The dependency chain is 33 → 34 → 35 → 36 → 37 → 38 → 39 with no skips required.

---

### Phase 40 — Round-3 UX fixes (hard restrictions, sticky selection, ray disambiguation, size axis, search, meal thresholds, dropdown overflow)

**Goal:** A consolidated UX pass over eight rough edges that have accumulated since Phase 39. Each item is small on its own; bundling them keeps the cross-cutting state (`selectedId`, `mealFilters.nutrients`, `axes` / a new `sizeAxis`) coherent in one session.

#### 40.1 — Dietary restrictions hide instead of dim

Today `restrictionActive` (from `passingIngredientIds`) intersects into `activeIngredientSet` in `src/main.js`. In `filter` mode that already feels like a hide, but in `highlight` / `score` modes restricted ingredients still render at full size in a muted color, and the table view still shows their rows. The intent is hard exclusion.

- Introduce a new "hidden" concept distinct from "inactive": ingredients (and category / meal aggregates whose constituents all fall under a restriction) are removed from the rendered set entirely.
- `src/scene/points.js`: hidden instances get `scale = 0` (or are omitted from the instance buffer rebuild) so they neither raycast nor render. The threshold-inactive "small + grey" treatment stays for everything else.
- `src/ui/table-view.js`: hidden rows are filtered out of the row list before pagination, not just visually dimmed.
- `src/ui/meal-builder.js` & `compose-meals.js`: meal aggregates whose `ingredient_categories` resolve to zero non-restricted ingredients are dropped (already partly handled — verify).
- Active-filters chip rail (Phase 38) keeps showing the restriction so the user can lift it.

#### 40.2 — Meal-section "Nutrients" filter → per-nutrient min / max

The current `mealFilters.nutrients: string[]` (checkbox-mode, "meal ≥ dataset median on ≥1 of these") is unintuitive — checking "Protein" doesn't mean what users expect.

- Replace the shape with `mealFilters.nutrients: { [nutrient]: { min: number, max: number } }`. A nutrient with no entry is unfiltered.
- The dropdown shows one row per nutrient: a label, a dual-handle slider (same component pattern as the left-rail Nutrient Thresholds panel), numeric min / max inputs, and a "use as filter" toggle so the user can keep a row visible without it being active.
- **Defaults mirror the left-rail thresholds**: when a meal-section nutrient row is first activated, its min / max are seeded from `state.thresholds[nutrient]`. A per-row "Reset" returns to that same baseline, so changing the left-rail thresholds later doesn't silently retroactively change the meal filter.
- `src/core/filters.js` (or wherever meal filtering composes — currently in `src/main.js#filterMealsByMealFilters`): replace the `nutrients.length ? computeMedians …` branch with a straightforward per-nutrient min ≤ aggregate ≤ max test against the meal's per-100g aggregate.
- Persistence (`src/core/persistence.js`): migrate any saved old-shape `nutrients: string[]` to the new map shape on load (drop empty arrays, otherwise seed each named nutrient from current thresholds).

#### 40.3 — Selected dot highlight + cross-view sticky selection

`state.selectedId` already exists, but the 3D scene doesn't visually distinguish it (only hover does), and the table view doesn't scroll the row into view or sync from a 3D click → table switch.

- `src/scene/points.js`: render the selected instance with a treatment that reads in both themes and works for any group color. Implementation choice (use my judgement, document in code): a thin animated outline ring (a second InstancedMesh with a hollow disk shader, or a per-instance scale-pulse around 1.0×–1.25× driven by `Date.now()` in the per-frame tick). Hover treatment still wins on the hovered instance; selection persists when hover leaves.
- `src/ui/table-view.js`: the row with `id === state.selectedId` gets a `.is-selected` class, scroll-into-view on selection change, and clicking a row sets `state.selectedId` (already true) and opens the detail panel.
- Switching view (`view-toggle.js` → `state.viewMode`): on switch, if `state.selectedId` resolves in the destination view, that row scrolls into view (table) or the camera target nudges toward that dot (3D, optional — at minimum, the selection is preserved and visually surfaced).
- View-level switches (Ingredients ↔ Categories ↔ Meals) intentionally do NOT carry selection across — an ingredient id is meaningless in Meals view. When `selectedId` doesn't resolve in the new level, clear it.

#### 40.4 — Search in 3D view (dropdown)

Search currently exists only in the table view. The 3D view needs an equivalent.

- New file `src/ui/search.js` mounted in the header (or a small floating input top-center on the 3D canvas — pick the placement that doesn't crowd the existing header controls; consult `index.html`'s current header layout).
- Input is a name search across the *current* view level (ingredients, categories, or meals). Results drop down beneath the input — name + a small color swatch + a one-line context (e.g. category, or cuisine for meals).
- Clicking a result sets `state.selectedId`, and for 3D, animates the camera to recentre on the selected dot (the existing camera reset / snap helpers in `src/scene/controls.js` are a starting point).
- Shares the active-filters / restriction / threshold rules — restricted ingredients don't surface in results.
- Same control should appear in table view, replacing or augmenting the existing `.table-search` input so behavior is uniform.

#### 40.5 — Ray disambiguation menu for overlapping dots

Single-click currently picks the topmost raycast hit. When dots overlap (perfectly or near-perfectly), the user can't reach the dot behind.

- `src/scene/picking.js`: on click, collect ALL instance hits along the ray, not just the first. `Raycaster.intersectObject` already returns them sorted by distance — keep the full list, dedupe by instance id, and capture each hit's screen depth.
- Cluster threshold: hits within a small *screen-space* radius (say 8 px) of the click point AND within a small ray-distance window of the closest hit count as "overlapping" candidates. Single-hit clicks behave exactly as today.
- New file `src/ui/pick-menu.js`: a floating menu opened at the click coords (CSS `position: fixed`, above all panels), one row per candidate showing color swatch + name + group/category.
- **Hover-preview**: hovering a row temporarily sets a transient `hoveredId` in the scene (existing hover plumbing) so the user can see *which* dot a row refers to before committing.
- Clicking a row commits the selection (sets `state.selectedId`, opens the detail panel) and dismisses the menu. Clicking outside dismisses without changing selection.

#### 40.6 — Fourth (Size) axis

A fourth, optional axis that maps a nutrient to dot radius — disabled by default.

- State: extend `state.axes` with a fourth slot `state.sizeAxis = { enabled: boolean, nutrient: string|null, constraint: { min, max } }`. Defaults to `enabled: false`, no nutrient.
- `src/ui/axis-controls.js`: render the size axis as a fourth collapsible row inside the existing Axes panel. When disabled, only the row header + an "Enable" toggle is visible; when enabled, the row mirrors the X/Y/Z UI (nutrient picker, constraint min/max with pan/zoom, reset).
- `src/scene/points.js`: per-instance scale becomes `baseScale * sizeScale(i)`, where `sizeScale(i)` linearly interpolates from `MIN_SIZE_RADIUS` to `MAX_SIZE_RADIUS` over the constraint window of the size axis nutrient. **Values outside the window are clamped** (a dot at 2× the max stays at MAX_SIZE_RADIUS — same convention the three positional axes already use). When disabled, `sizeScale` returns 1.
- Score / highlight / corpus-pattern scale multipliers still compose multiplicatively on top, so the size axis layers cleanly with existing visual hierarchy.
- Tooltip / detail panel: when size is bound to a nutrient, surface that nutrient's value alongside the X/Y/Z nutrient values so the user can read why a given dot is small.

#### 40.7 — Left-panel dropdowns clipped by rail edge

Meal-builder filter dropdowns (and any popovers anchored inside the left rail) get cut off at the rail's right edge because the rail container clips overflow.

- Audit `src/styles/layout.css` and `src/styles/components.css` for `overflow: hidden` / `overflow: auto` on left-rail containers that are clipping descendants.
- Fix universally, not case-by-case: convert dropdown popovers to `position: fixed` (or render them in a body-level portal) so they're positioned relative to the trigger via JS but escape the rail's clipping context. The dropdown component pattern in `src/ui/meal-builder.js` is the canonical example — apply the same fix everywhere a popover lives inside a scrollable container (left rail, right detail panel, table-view columns menu, axis-picker popovers).
- Touch / pointer behavior must still close the popover when the user clicks outside, including on rail content.

#### 40.8 — Macro-completeness hint in detail panel (red-meat clarification)

The "Red meat" compositional meal shows ~25g protein per 100g and ~15g fat per 100g, which surprised a tester who expected ≈100g protein. The math is correct (cooked muscle is mostly water by mass), but the per-100g convention isn't visible from the panel.

- `src/ui/detail-panel.js`: render a small "Macro breakdown per 100g" line under the existing nutrients, computing `100 − protein − fat − carbs − fiber` and labeling it "water / other" (or "remainder"). Only render when the remainder is positive and the food is solid (skip for beverages where the answer is trivially ~100% water).
- No data file changes — values are already correct.
- Reuse the existing notes / examples block; this is one extra row, not a new section.

#### 40.9 — Active-filters panel: always-present empty state + persistent pill

The panel was auto-hiding whenever `chips.length === 0`, so clicking "Clear all" emptied the chips and the whole section disappeared — there was no way to bring it back beyond reactivating a filter elsewhere.

- Panel is now ALWAYS mounted (no auto-hide). When no filters are active, the expanded body shows "No active filters right now." and the "Clear all" button is disabled.
- The × button in the header always toggles between expanded panel and the corner pill. The pill reads "Filters" when chips count is 0, "Filters (N)" otherwise — so the user always has an entry point back into the panel.
- Close-button icon is `▾` (collapse cue) instead of `×` (dismiss cue), and gets `title="Collapse"` for clarity.

#### 40.10 — Move "Compose meals" into the Meals filter row as "Modify meals"

The `src/ui/compose-meals.js` left-rail section duplicates real estate that the Meals filter dropdown row in `src/ui/meal-builder.js` already owns. It should live as a sibling of the existing meal-filter dropdowns ("Restrictions / Food groups / Categories / Ingredients / Nutrients"), labeled **"Modify meals"** (or "Compose").

- Add a new filter dropdown next to the Nutrients one in `meal-builder.js`. The trigger button opens a popover with the existing `compose-meals.js` UI: search input + scrollable list of categories with the +/− tri-state controls. Reset and summary line stay.
- Source of truth still writes to `state.mealComposition` so the rest of the pipeline (aggregations, active-filters chip rail, persistence) is unchanged.
- Delete the standalone left-rail Compose meals section (or keep `compose-meals.js` as the popover body and stop mounting it as its own collapsible section in `src/main.js`).
- The popover follows the same fix as 40.7 — `position: fixed`, escapes the left-rail clipping.
- Chip-rail label and persistence keys stay as today; only the mount point changes.
- The user's note "shows the search and all the ingredients" refers to the existing category list with name search; **keep the unit as category** (not individual ingredient) — composition operates on category-aggregate meals, so per-ingredient composition would be semantically ambiguous. If a later phase wants per-ingredient composition, that's a Phase 37-style remix, not this filter.

#### 40.11 — Axis-apply button rename + chip semantics against user defaults

Two related sub-fixes that together make the active-filters panel feel honest:

- "Filter food by ranges" → "Filter food by axis ranges" so the affordance is unambiguous.
- Threshold chips now diff against the **user-default** map (the boot-initial `defaultConstraintFor` values, e.g. calories `0-1000`) rather than the dataset envelope (e.g. calories `0-902`). An untouched config has no threshold chips. Per-row reset, "Reset all", "Clear all", and the empty-filter overlay's reset button all now target the user-default map too — so a reset never produces a stale "≤ 902 kcal" chip just because the dataset's max happens to differ from the round-numbered default.
- Axis pan/zoom does NOT touch `state.thresholds`, so axis windows never generate active-filter chips on their own — only "Filter food by axis ranges" promotes them to thresholds.

#### Updated files-touched summary

Add to the list above:
- `src/styles/layout.css` — `.active-filters.is-collapsed` pill visibility / sizing.
- `src/ui/active-filters.js` — always-mounted panel; empty-state message; pill toggle; chips diff against user defaults.
- `src/ui/meal-builder.js` — host the new "Modify meals" filter dropdown; body-portaled popover; per-nutrient min/max panel.
- `src/ui/compose-meals.js` — refactor to render into an arbitrary host element, not its own rail section.
- `src/ui/nutrient-thresholds.js` — reset targets user defaults, not dataset envelope.
- `src/ui/axis-controls.js` — rename apply button; add fourth Size axis row.
- `src/core/scoring.js` — add `isThresholdsAtDefaults`, `isNutrientThresholdAtDefault` helpers.
- `src/main.js` — stop mounting `compose-meals` as a standalone section; wire `defaultThresholdsMap` to active-filters and `getDefaultThreshold` getters to meal-builder + nutrient-thresholds.

#### Additional validation

- [ ] Apply a threshold filter so the Active filters panel shows chips. Click ▾. The panel shrinks to a chip-shaped pill in the same corner; clicking the pill re-expands. The pill is visually consistent with the Legend / Axes pills opposite.
- [ ] With NO filters active, the active-filters section still shows "No active filters right now." instead of disappearing. Clicking ▾ collapses to a "Filters" pill.
- [ ] Click "Clear all" with chips active — the section stays expanded, chips disappear, "Clear all" disables itself.
- [ ] Pan a single axis (e.g. drag Pan on Calories) — no active-filter chip appears for Calories until "Filter food by axis ranges" is clicked.
- [ ] The left rail no longer has a "Compose meals" section. Open the Meals filter dropdowns — a "Modify meals" entry sits next to "Nutrients". Click it. The popover shows the search box and category list with +/− controls; behavior is identical to the old standalone section. The popover isn't clipped by the rail edge (covered by 40.7).
- [ ] After a fresh boot, no threshold chips appear in the active-filters rail (defaults match the user-default map). Tighten Calories to 0–500, a chip appears. Click the chip's × — the threshold resets to the user default (0–1000), not to dataset envelope (0–902).

#### Files touched (summary)

- `src/state.js` — `sizeAxis`, `selectedId` (already present) flowing across view changes.
- `src/main.js` — restriction → hidden pipeline; meal-nutrients filter wired to new shape.
- `src/core/filters.js` — meal filter nutrients use min/max.
- `src/core/persistence.js` — migration shim for old `nutrients: string[]`.
- `src/scene/points.js` — hidden scale=0, selection halo / pulse, size-axis radius multiplier.
- `src/scene/picking.js` — multi-hit collection on click.
- `src/scene/controls.js` — camera "focus on selected" helper (lightweight nudge, optional easing).
- `src/ui/axis-controls.js` — fourth size-axis row.
- `src/ui/meal-builder.js` — replace Nutrients dropdown with per-nutrient min/max rows; portal popovers out of rail.
- `src/ui/table-view.js` — hide restricted rows; selected-row class + scroll-into-view; integrate / replace search.
- `src/ui/detail-panel.js` — macro remainder line.
- `src/ui/search.js` (new) — 3D-view search dropdown.
- `src/ui/pick-menu.js` (new) — ray-disambiguation floating menu with hover-preview.
- `src/styles/components.css` — popover portal styles, selection halo, size-axis row, search dropdown.
- `src/styles/layout.css` — fix overflow clipping on rails / panels.

#### Validate before moving on

- [ ] Toggle Vegetarian. No meat ingredients render in 3D (no greyed husks). No meat rows in the table. Lifting the restriction restores them.
- [ ] Open Meals → Nutrients filter. Each nutrient row shows a min/max pair. Defaults match the left-rail Nutrient Thresholds. Changing the left rail after a meal filter row is active does NOT silently re-baseline that row.
- [ ] Click a dot in 3D. It visibly stays highlighted after hover leaves. Switch to table view — the same row is highlighted and scrolled into view. Click a different row — return to 3D — the new dot is highlighted.
- [ ] Search box on 3D view: typing matches across the current view level. Result click selects the dot and recentres the camera. Restricted items don't appear in results.
- [ ] Force two ingredients to perfectly overlap (e.g. by aligning axes / constraint windows). Single-click opens a floating menu with both names, hovering each row previews that dot in the scene, clicking commits.
- [ ] Open Axes panel → enable Size → pick "fat". Fatty cuts visibly grow; lean cuts shrink. Set the size constraint window to 0–10 g — dots with >10 g fat clamp to max size, dots with <0 (impossible) clamp to min.
- [ ] Open every dropdown in the left rail (meal-builder filters, axis-picker popovers, restrictions). None are clipped by the rail's right edge; all dismiss on outside click.
- [ ] Detail panel for the "Red meat" compositional meal shows protein 25g, fat ≈15g, carbs 0g, plus a "remainder (water / other) ≈60g" line per 100g.

---

## Working with Claude Code on this project

A few habits that pay off:

**Start each phase as a fresh session.** Long sessions accumulate context that anchors Claude Code to earlier decisions, which can produce drift. After validating a phase, exit (`/exit`) and start a new session for the next phase. Claude Code will pick up the project state from `CLAUDE.md` and the actual files.

**Reference the plan explicitly.** Each phase's prompt should say "execute Phase N of the development plan in `food-map-development-plan.md`." Claude Code can read the file directly.

**Demand complete files at the end of each phase.** "Produce complete files, not diffs" is in the CLAUDE.md. If output ever feels patchy, ask: "show me the full current contents of `src/ui/ingredient-filter.js`."

**Bug-report precisely.** When something's off, describe it the way you described the skip-edge DAG bug on the argumentation map: precise observation, expected behavior, preference for universal fixes over special cases. Claude Code responds well to this voice.

**End each phase with a self-check.** Ask Claude Code to walk through the validation checklist itself before you test. It often catches things before you have to.

**Don't move to the next phase until validation passes.** A small bug in Phase 5 becomes a tangled bug in Phase 9.
