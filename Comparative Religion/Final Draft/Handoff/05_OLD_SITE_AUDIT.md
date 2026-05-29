# Old site diagnosis (Final Draft/Website/)

The user described the old site as "boring to look at" and "stale" relative to the colorful, structurally varied draw.io diagram. A focused audit confirmed the user's intuition with code-level evidence. Don't repeat these mistakes in the v2 build.

## Color palette + tokens

`css/tokens.css` defines a **monochromatic palette with a single accent**:
- 5 background tokens (all blueish, monochromatic)
- 2 text tokens (achromatic grayscale)
- Only 2 *semantic* colors: `--agree-color` (green #22c55e) and `--disagree-color` (red #ef4444)
- Spine/glow are achromatic + one blue accent (#6e8cff)

**Color carries zero semantic meaning** for sections, move-types, or node categories. Every node across "Discovering Reality," "Historical Comparison," "Religious Comparison" etc. is rendered with the **same border/gradient palette** — only hue-by-position-in-sibling-group, no global meaning.

Light/dark theme support exists; both modes have the same single-accent limitation.

## Per-section variation: confirmed missing

**The data already encodes section variety** (per `data.json`):
- Nodes 1–8 are root-level (no expansion, no sections)
- Node 9+ have a `.sections` array with `type: "row"` or `type: "tab"` (tabs hold definitions, rows hold logic/evidence)

**The renderer ignores this**. Specifically:
- `templates.js:167–229` — the `nodeRow()` function renders every card identically. No per-section class, no type-aware styling, no contextual slot differentiation.
- `data-store.js:58–75` — color assigned purely by `parentId` + position. Sections are never consulted during color assignment.
- CSS has zero per-section card styling. Cards are identical white boxes with identical border colors across all 140+ nodes.
- The data tracks node type (conceptual vs. empirical vs. comparative) but the expander `sections.type` only controls *internal panel layout*, not card appearance.

## Visual energy at rest

First paint shows:
- Header (breadcrumbs, search, theme toggle) — adequate, glassmorphic
- Grid of 7–8 white cards (at root level) all with:
  - Same corner radius (18px)
  - Same 2px border (color varies, but all equally subtle)
  - Same minimal shadow
  - Same header + so-what + vote-button layout
  - Zero color differentiation between card purposes

What a reader sees: a uniform product-comparison grid, not a knowledge structure. No visual "weight" or "importance" hierarchy.

## Root causes of the "stale" feeling

1. **No section-type card styling** (`/css/node-card.css` + `/js/templates.js:196`)
   - Cards for "Discovering Reality" (epistemology), "Historical Comparison" (textual analysis), and "Defining God" (metaphysics) are pixel-identical despite serving radically different epistemic roles
   - The expander knows the difference; the card does not

2. **Monochromatic background + single accent** (`/css/tokens.css` lines 18–178)
   - No semantic color slots for "This is a claim," "This is an example," "This is a derivation"
   - Resting state is uniformly bland

3. **All-nodes-are-siblings visual weight** (`/css/base.css:126–127`, `/css/node-card.css:64–66`)
   - Hover animation (2px lift + shadow) is the *only* interactive feedback at card level
   - No resting hierarchy between root nodes and their children

## What's worth preserving from the old site

These are real features. Lift the *logic* into v2 but rewrite the UI on top of the new design system:

- **Agreement tracking + glow system** — clicking agree/disagree lights cards green/red, propagates through expanders (`agreement.css`, `expander.css`)
- **Inline derivation** — "Derivation" button expands full logic/evidence under each card without navigation
- **Per-sibling hue rotation** — within a group, each node gets a distinct hue (so immediate siblings are visually distinct). This still works *locally*; the global semantic was missing.
- **Breadcrumb + search** — instant navigation and full-text search across nodes
- **Responsive spine + marker column** — the timeline metaphor scales well to mobile
- **Light/dark theme toggle** — smooth transitions, stored in localStorage
- **Tab-based expander panels** — "Definition," "Logic," "Evidence" tabs for terminal nodes prevent content overload

## Specific files to read in old site (when building)

- `Final Draft/Website/index.html` — shell + header + breadcrumb + search structure
- `Final Draft/Website/js/main.js` — entry point, module loading
- `Final Draft/Website/js/templates.js:167–229` — nodeRow() (the template to replace)
- `Final Draft/Website/js/data-store.js:58–75` — color assignment (replace with tier/spectrum semantic)
- `Final Draft/Website/css/agreement.css` — agree/disagree glow patterns
- `Final Draft/Website/css/expander.css` — expander tabs
- `Final Draft/Website/data.json` — sample data format (1 MB; don't read fully, sample)
- `Final Draft/Website/README.md` — user's own description of the site's features

The agent that audited this was given specific line numbers as evidence — those line ranges are real and useful.
