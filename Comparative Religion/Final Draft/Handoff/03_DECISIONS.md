# Decisions made (and why)

Don't re-litigate without checking here first. Each item records a real choice the user and Claude resolved during design.

## Framing: demystification, not persuasion

**Decision**: The site is a *demystification engine*, not a persuasive argument. Content is presented transparently in evidence-led order. Claims are not asserted before they're derived. Tone is "neutral but objective" — takes sides only where evidence leads, never as an entry posture.

**Why**: The user explicitly rejected both framings I initially proposed ("transparent persuasion" and "neutral epistemology"). Their position: the project IS the structured demonstration; readers reach conclusions by following the chain. The persuasive end is a *consequence* of structure done well, not the *goal*.

**Implication for build**: No "and here's the answer" cards above the fold. No spoiler in section headers. Section 1–7 frame content as inquiry, not conclusion. Section 8 (Results) earns its conclusion through what preceded it.

## Codebase strategy: greenfield in v2 folder

**Decision**: Build the new site at `Final Draft/Website-v2/` (does not exist yet). Keep `Final Draft/Website/` untouched as reference.

**Why**: The old renderer applies one `nodeRow()` template to all 140+ nodes regardless of section. Refactoring it would inherit the structural debt that produced the "stale" feeling. Greenfield with archetype-per-section is cleaner.

**Implication for build**: Lift agreement-tracking + search *logic* from the old `app.js` and `js/` modules as reference, but rewrite the CSS tokens, renderer, and per-archetype layout from scratch.

## Color carries semantic meaning

**Decision**: Color encodes either **tier elevation** (Rainbow Ladder, Convergent Tree) or **worldview position** (Comparison Matrix, Evidence Cards). Same 7-color rainbow palette across all sections — only the *semantic* changes.

**Why**: The diagram extraction confirmed the user uses a consistent 7-color palette deployed multi-modally. The old site discarded this entirely (color only for agree/disagree state). Re-introducing it is the single biggest fix for the "stale" feeling.

**Implication for build**: Every node, cell, and chip references a tier-or-worldview color slot. The renderer assigns colors from data, not from CSS hard-codes per element.

## Per-archetype orientation rule

**Decision**: 
- **Rainbow Ladder**: apex on top, base on bottom (tier N at top, tier 1 at bottom — pyramid orientation)
- **Convergent Tree, Comparison Matrix, Evidence Cards**: 1→N top to bottom (foundations first, conclusions later — inductive reading)

**Why**: The two archetype families serve different semantics. Rainbow Ladder content is a *temporal sequence* the reader walks through (Pursuit of Truth steps 1→6), and the pyramid visual (apex top) reinforces the "synthesis at the top" mental model. The other archetypes show *hierarchical support structures*; inductive reading from foundations is more natural for the user's actual content.

**The trade-off**: Universal "1→N top to bottom" would have been more consistent, but flipping Rainbow Ladder to that would have inverted the pyramid (foundation at top = wide top, narrow bottom = funnel). The user accepted the per-archetype rule. Revisit only if a user explicitly asks for universal ordering.

## Bookend pyramid for Rainbow Ladder

**Decision**: Pyramid shape created by tapering row widths (96% to 56%) — not indent. Each row is centered with `width: min(Xpx, Y%)`. The right edge is anchored by a small tier-colored dot (the "bookend"), mirroring the numbered circle on the left.

**Why we tried other things first**:
- **Stairstep indent** (Variant A early on): worked visually but ate horizontal space on mobile
- **Centered column with no taper** (Variant B): clean but lost the pyramid signal
- **Outlined rectangles around text** (combined attempt): added too much visual ink ("double outline" — circle + card border)
- **Tapering with no right marker**: looked like a "trapezoid / half-pyramid" because text endings varied and the right edge wasn't visually defined

The bookend dot was the smallest addition that closed the pyramid silhouette symmetrically.

## Halved background opacity

**Decision**: Lane and cell background tints use ~2.5–5% opacity in light mode, ~4.5–5% in dark mode.

**Why**: The first opacity values (5–10%) competed with cell content. Halving them lets the zones recede visually behind the cards. User asked for "half as bright" explicitly.

## Headers with names, right-aligned for adjacency

**Decision** (Convergent Tree): Lane chip is `[name][circle]` (name first, circle adjacent to cards), right-aligned within a fixed min-width chip column.

**Why**: With `[circle][name]` order, the gap between the chip's right edge and the first card created a "tracking problem" — eye had to jump from name to find the matching cards. Putting the numbered circle adjacent to the cards (with the same tier color extending into the card's left border) makes the connection visual.

## Top-to-bottom reordering (Convergent Tree)

**Decision**: Tier order in Convergent Tree is 1→7 top to bottom (foundations at top, apex at bottom). Root claims (e.g., "Historical claim" / "Logical claim") still sit above tier 1 as the section's synthesis preview.

**Why**: User asked for "organize from top to bottom" — interpreted as ascending tier number from top. This contradicts the Rainbow Ladder's apex-on-top, hence the per-archetype rule above.

## Filter pills, scroll sync, per-criterion synthesis (Matrix + Evidence)

**Decision** (Comparison Matrix and Evidence Cards):
- Top of section: filter pills, one per worldview, click to show/hide that column
- Cells use fixed widths (180px) with `overflow-x: auto` on a per-criterion scroll pane
- All scroll panes within a section sync horizontally (JS — scrolling one moves all)
- Each criterion ends with a *synthesis card* — neutral gray background, dashed left border, italic prose isolating the comparative takeaway

**Why**: User flagged three needs simultaneously:
1. "Show and hide different religions" — for focused comparison or "just for fun" hypotheticals
2. "Scrolling one row would scroll all rows, to maintain the alignment" — replaces wrap behavior, keeps columns aligned at any viewport width
3. Section 7 has *synthesis for each section* — the comparative takeaway, currently missing. Without it the matrix reads as raw data, not insight.

All three were added together because they're interdependent: filter changes cell count, scroll-sync keeps the resulting columns aligned, synthesis distills the comparison.

## Tier tag for cross-section linking

**Decision**: Each criterion in Comparison Matrix / Evidence Cards displays a "↳ Ties back to Tier X · NAME" tag above the criterion header. Currently styled as small uppercase tertiary-color text. In the build, this becomes a clickable link to Building Confidence's tier lane.

**Why**: The user wanted the tier framework from Section 3 to be visibly present whenever a criterion exercises it. The "↳" arrow signals "this references back." Used neutral gray instead of tier color to avoid color collision (e.g., Tier 4 green vs. Christianity-green worldview cells).

## Color collision rules

**Decision**: When a tier color and a worldview color share the same hex (e.g., Tier 4 green and Christianity green), the tier-tag uses **neutral gray text** rather than tier color. Avoids visual ambiguity.

**Why**: Same palette, different semantics. If a green tier-4 chip appeared next to green Christianity cells, the reader couldn't tell which "green" was which.

## "Cost of disagreement" indicator

**Decision** (planned, not yet built): Each node-card shows a small "Cost of disagreement: N nodes" indicator next to the Agree/Disagree buttons. Shows the user what their rejection commits them to downstream.

**Why**: The old site had agreement propagation infrastructure (clicking disagree turns dependent nodes red) but never showed the *count*. Surfacing the count makes the cost concrete and supports the demystification framing: "your disagreement has a measurable footprint."

## Verdict labels stay text-only

**Decision** (Comparison Matrix): Verdicts use plain text labels (Yes / No / Maybe), not icons.

**Why**: Adding a green check / red X / amber question icon would collide with the worldview palette (Christianity = green, Atheism = red, Polytheism = amber). The word itself carries the verdict; color carries the worldview.

## Polytheism cells handle "partial qualification"

**Decision** (observed pattern, not a rule yet): Polytheism cells in Evidence Cards / Comparison Matrix often need to qualify *which* polytheistic tradition is being evaluated (Vedic vs. Greek vs. Norse), since they have different evidence profiles. The cell content does this in prose; no special UI yet.

**Future**: User has ideas for breaking polytheism into per-tradition spectrum slots in future work. Out of scope for first build.

## Universal collapsibility

**Decision**: Every "section" unit in every archetype is collapsible via a small `▾`/`▸` chevron at the right of its header. Click the header to toggle. State persists in `localStorage`. A page-level "Collapse all / Expand all" affordance is added to dense sections.

**Why**: The user flagged this as a universal requirement when reviewing Section 7. Without collapsibility, dense sections (especially Section 7 with multiple topic clusters and criteria) become hard to navigate and the "wall of text" feeling returns. Collapsibility lets readers focus on what they're actively engaging with.

**Hierarchy**: Parent collapse takes precedence. Collapsing a Section 7 topic cluster hides its inner criterion sections regardless of their state; re-expanding restores inner state.

**Default**: All sections expanded by default. Reader chooses what to hide.

**Implication for build**: Single `collapsible.js` module hooked into each archetype renderer. Section header DOM gains a chevron span and a click handler. Section body wraps in a `.section-body` div for show/hide.

## Source-of-content vs. content-of-mockup

**Decision**: Mockup content (the actual claims, quotes, analyses in the cards) is illustrative — used to demonstrate the *visual pattern*, not as the final argument copy. The user's actual research content goes in `data.json` (or equivalent) when building, and the renderer fills the structure.

**Why**: Several mockup cells contain placeholder-grade text (e.g., the manuscript dates in Evidence Cards are widely-cited public figures, not the user's polished argument). Don't paste mockup text into the production build.
