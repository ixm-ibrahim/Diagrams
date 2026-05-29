# The four archetypes

Every section page in the new build uses **one** of these four layouts. Map page layout varies; the per-node internal structure (Claim, So-what, Eliminates, Unknown remainder, Objections) is consistent across all archetypes.

See mockups in `mockups/*.html` for visual reference (open in a browser; all four contexts shown per file).

---

## 1. Rainbow Ladder

**File**: `mockups/01_rainbow_ladder.html`

**Use for**: Sections that are a *sequential walk* through a fixed number of tiered steps. Each tier has exactly one claim. Currently:
- Section 1 (Pursuit of Truth) — 6 steps
- Section 8 (Results and Conclusion) — summary ladder
- Any future "recipe" or "summary" section with ≤7 tiers and one claim per tier

**Layout**:
- Centered column
- Each tier is one row: `[outlined numbered circle] [tier title text] [tier-colored bookend dot]`
- Row widths taper from 96% (base, widest) to 56% (apex, narrowest) creating a pyramid
- **Apex-on-top orientation**: Tier N at top, Tier 1 at bottom (different from other archetypes — see `03_DECISIONS.md`)
- Mobile uses same widths (responsive percentage caps); pyramid shape preserved at smaller scale

**Hover/expand state** (not in mockup, to be wired during build):
- Hovered row: filled circle (instead of outlined) + faint tier wash on the row
- Click row: opens the node card with internal strips

**Key CSS variables used**: `--w1` through `--w6` (or `--t1`–`--t7` in the matrix sense — both naming conventions appear in mockups, pick one for build)

---

## 2. Convergent Tree

**File**: `mockups/02_convergent_tree.html`

**Use for**: Sections where multiple supporting claims at lower tiers converge upward into one or two top-level claims. Currently:
- Section 3 (Building Confidence) — Historical claim + Logical claim roots, supported by 7 tiers
- Section 4 (Defining God) — deductive cascade from observation to god-attributes
- Any section with multiple claims per tier

**Layout**:
- Two root claim "pill" cards at the top (neutral gray, not tier-colored — they sit *above* the rainbow)
- Below: stack of tier lanes, ordered **top-to-bottom = 1→N** (foundations first, apex last)
- Each lane: `[name text — right-aligned] [numbered circle]` chip on left, horizontal row of cards on right
- Cards have tier-colored left border (3px) and very faint tier-colored background
- Lane has subtle tier-colored background tint (~3% light, ~5% dark) creating tier "zones"
- Crowded tiers (>3 cards) use "+N more" affordance: dashed border pill

**Critical detail**: chip contents are right-aligned so the numbered circle sits flush against the cards, closing the visual gap between the lane header and the cells.

**Mobile**: cards in each lane wrap (since this archetype doesn't use horizontal scroll — TBD if it should align with Matrix/Evidence on this).

---

## 3. Comparison Matrix

**File**: `mockups/03_comparison_matrix.html`

**Use for**: Sections comparing competing worldviews against shared criteria. Currently:
- Section 5 (Alignment with Reality) — 4 worldviews × N epistemic tests
- Section 7 (Theological Comparison) — 2 worldviews × N theological topics

**Layout**:
- **Filter pills at top** — show/hide individual worldviews
- Worldviews ordered along the **atheism→monotheism spectrum** (red → amber → green → blue, with slot reservation for future positions)
- Each criterion section: `[tier tag "↳ Ties back to Tier X"][criterion header][horizontal scroll pane with cells][synthesis card]`
- Cells have fixed width (180px) — no responsive wrapping
- **Horizontal scroll with row synchronization**: scrolling one row scrolls all rows (via JS). This maintains column alignment.
- **Synthesis card** below each criterion: neutral gray background, dashed left border, italic prose isolating the comparative takeaway

**Cell structure**:
```
[Worldview name (small uppercase)] [Verdict (Yes / Maybe / No)]
[Brief reasoning text]
```

Verdict and worldview name are both in the worldview-numeral color. Reasoning is in body color at reduced opacity.

**Tier tag**: links the criterion back to Building Confidence's tier framework (Section 3). E.g., a "manuscript dating" criterion links back to Tier 2 (Evidence). Clickable in the production build.

---

## 4. Evidence Cards

**File**: `mockups/04_evidence_cards.html`

**Use for**: Sections where cells carry actual source material — quoted text, manuscript dates, archaeological evidence. Currently:
- Section 6 (Historical Reliability) — paired scripture/source quotations across worldviews

**Layout**: identical to Comparison Matrix structurally — same filter pills, scroll sync, synthesis cards, tier tags — but cells have a richer internal structure:

```
[Source attribution (small uppercase)]
"Quoted material" (serif italic, with subtle left rule)
[Brief analysis (body sans, reduced opacity)]
```

The serif italic for quotes is the editorial blockquote treatment — distinguishes "what the source says" from "what we observe about it" (which is the analysis below).

Synthesis card per criterion isolates the comparative takeaway across all worldview cells.

---

## Universal: collapsible sections

Every archetype's "section" units are collapsible. The unit differs per archetype but the affordance is consistent.

**What collapses in each:**

| Archetype | Collapsible unit | When collapsed, shows |
|---|---|---|
| Rainbow Ladder | Each tier row | Numbered title only (no node-card internals) |
| Convergent Tree | Each tier lane | Chip with count (e.g., `Corroboration · 3`) |
| Comparison Matrix | Each criterion section | Criterion header only |
| Evidence Cards | Each criterion section | Criterion header only |
| Section 7 topic-cluster | Each topic cluster | Topic header only (and inner criterion sections also collapse independently) |

**Affordance**:
- Small chevron at the right end of each section header: `▾` expanded, `▸` collapsed
- Header (including chevron region) is the click target
- Animate the rotation (`transform: rotate(-90deg)` for collapsed state); body uses `max-height` transition or `display: none` if no animation needed
- Default state: all expanded
- Per-section state persists in `localStorage` keyed by node ID

**Section-level controls**:
- "Collapse all / Expand all" pill at the top of each page (next to or below the filter bar for matrix/evidence archetypes; below the page header for ladder/tree)
- Useful for dense sections (especially Section 7 with many topic clusters)

**Collapse hierarchy** (Section 7):
- Collapsing a topic cluster hides its inner criterion sections, regardless of their individual collapse state
- Re-expanding the topic restores whatever inner state was set before
- Visually, parent collapse takes precedence; inner collapse state is preserved but hidden

**CSS additions over the locked archetype styles**:
- `.section-header` becomes a flex row with chevron at the right (`justify-content: space-between`)
- `.section-header[data-collapsed="true"] .chevron { transform: rotate(-90deg); }`
- `.section-body[data-collapsed="true"] { display: none; }` (or animate with max-height)
- Cursor: pointer on the header

**Build phase**: this is a single `collapsible.js` module shared across all archetype renderers. The per-section data has an optional `collapsed: true` initial state for cases where the user wants a section closed by default (e.g., deep-dive criteria that aren't first-time-reader essential).

## When archetypes share infrastructure

**Comparison Matrix and Evidence Cards share**:
- Filter pills (top of page)
- Tier tag pattern (`↳ Ties back to Tier X · NAME`)
- Horizontal scroll with row sync (JS)
- Synthesis card per criterion (neutral gray, dashed border)
- Cell color = worldview position (spectrum-mapped)

**Rainbow Ladder and Convergent Tree share**:
- Tier color = elevation (rainbow palette)
- Numbered circle indicator
- Top-down reading orientation differs (see decisions)

**All archetypes share** (for the build):
- Frame container (`.cmp-frame`) with mode tokens
- Eyebrow + title + subtitle header
- Same neutral text and tertiary color tokens
- Same dark-mode flipping logic
- Same node-card internals when a card is expanded (locked — see `mockups/05_node_internals.html`)

---

## Section 7 topic-cluster wrapper

Section 7 (Theological Comparison) uses Comparison Matrix as its base, but criteria are **grouped into topic clusters** (christology, soteriology, atonement, scripture-authority, etc.), and each cluster ends with a heavier "topic synthesis" that distills the cumulative pattern across all of its criteria.

See `mockups/06_section7_topic_clusters.html` for the locked design.

**Structure**:
```
Section 7 header
  [Filter pills]
  Topic 7.1 · Christology
    (small eyebrow + larger title + italic subtitle, with thin solid rule above)
    Criterion 1 (with cells + per-criterion synthesis)
    Criterion 2 (with cells + per-criterion synthesis)
    Criterion 3 (with cells + per-criterion synthesis)
    Topic synthesis · Christology
      (heavier card: solid 4px left border, deeper bg tint, 12.5px text)
  Topic 7.2 · Soteriology
    ...
  Topic 7.3 · Atonement
    ...
```

**Visual hierarchy distinguishes the three synthesis levels**:
- Per-criterion synthesis: 3px **dashed** left border, compact 11px italic, faint bg
- Topic synthesis: 4px **solid** left border, 12.5px italic, slightly deeper bg, label "Topic synthesis · [name]"
- (Possible future) Section synthesis: even heavier treatment if needed

The dashed-vs-solid distinction does real work — readers learn to scan dashed=row-level, solid=topic-level.

**CSS additions over Comparison Matrix**:
- `.topic-cluster` — wrapper with `border-top: 1px solid var(--topic-rule)` and padding-top, demarcating cluster boundary
- `.topic-eyebrow` — "Topic 7.1" small uppercase tertiary
- `.topic-header` — 14px title (between section 15px and criterion 12px)
- `.topic-sub` — small italic description
- `.topic-synth` / `.topic-synth-label` / `.topic-synth-text` — the heavier synthesis card
- New CSS variables: `--topic-synth-bg`, `--topic-synth-border`, `--topic-rule`

**Renderer dispatch** (build phase): Section 7's data shape adds a `topics` array between `section` and `criteria`:
```json
{
  "id": "section-7",
  "archetype": "comparison-matrix-clustered",
  "worldviews": [{ "id": "christianity", ... }, { "id": "islam", ... }],
  "topics": [
    {
      "id": "christology",
      "eyebrow": "Topic 7.1",
      "title": "Christology",
      "subtitle": "The nature, mission, and return of Jesus",
      "criteria": [ ... ],
      "synthesis": "Across all christological tests..."
    },
    ...
  ]
}
```

The renderer iterates topics, each one a Comparison Matrix sub-block with its own synthesis. Section 5 (Religious Comparison) uses plain `comparison-matrix` without topics; Section 7 uses `comparison-matrix-clustered`.

---

## What's still open

**Section-level synthesis** (if needed): if Section 7 also needs a *section-wide* synthesis that goes one level above topic synthesis (distilling across all topics), that's a possible third tier. Not yet designed. Likely wouldn't need new CSS — just reuse the topic synthesis style at the section level with a different label ("Section synthesis").

**Evidence Cards clustering**: if Section 6 also benefits from topic-cluster grouping (e.g., grouping criteria by which Confidence tier they tie back to), the same pattern applies. Not yet designed but trivially reusable.
