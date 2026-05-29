# Next steps

The v1 build is scaffolded. All four archetypes + Section 7 cluster wrapper work end-to-end with sample data. Remaining work is in four buckets, in roughly the order you'd tackle them.

## State of the build

See `Final Draft/Website-v2/README.md` for the canonical, current state. Summary:

**Working**: Tokens, base styles, theme toggle, universal collapsibility, section picker, Rainbow Ladder, Convergent Tree (+ `+N more` affordance), Comparison Matrix (filter pills + scroll-sync + synthesis), Evidence Cards (serif quotes), Section 7 topic clusters with topic synthesis, node-card internals (Claim / So-what / Unlocks / Eliminates / Unknown / Objections + Derivation / Agree / Disagree / Cost-of-disagreement display).

**Sample data**: 5 sections in `Website-v2/data.json` exercising each archetype variant. Content is illustrative.

**Smoke-tested**: every JS module loads cleanly, JSON parses, all assets serve over HTTP.

## Bucket 1: real content migration (recommended first)

The current site renders placeholder content. Real content lives in two places, depending on the section:

| Section | Primary source | Cross-reference |
|---|---|---|
| Section 1 (Pursuit of Truth) | `Final Draft/Website/data.json` — user invested heavily here | `AI/Comparative Religion Diagram/1. Pusuit of Truth.txt` |
| Sections 2 through 9 | `AI/Comparative Religion Diagram/*.txt` files | `Final Draft/Website/data.json` (less developed) |
| Appendices A–F | `AI/.../9.A` through `9.F.txt` | Some content folds into main sections per `05_OLD_SITE_AUDIT.md` |
| LDS material | `AI/.../LDS Addendum.txt` (314 KB) | TBD whether becomes a separate worldview slot |

**Filename note**: `1. Pusuit of Truth.txt` has a typo (`Pusuit` instead of `Pursuit`). Preserve when reading; correct when writing display copy.

**Migration approach** (suggested):
1. Read source for Section 1 from BOTH the old website's `data.json` and the text file. Pick the canonical claim wording from the website (the user's most refined draft).
2. Translate into `Website-v2/data.json` format — see existing sample structure for each archetype.
3. Verify all ties-back-to-tier links match the Section 3 tier names you give the canonical names.
4. Move section by section. Don't bulk-translate everything before verifying each.
5. Confirm tier names with user before locking them site-wide. Current placeholders: Subject / Evidence / Corroboration / Integrity / Coherence / Robustness / Verification.

**Pre-flight checks for user**:
- Confirm tier names (the seven names above are derived from card content, not the user's canon)
- Confirm worldview names in section 5 spectrum order: Atheism / Polytheism / Trinitarianism / Monotheism
- Confirm whether LDS gets a separate worldview slot
- Confirm Section 7 topic list (only Christology + Soteriology stub in current sample — actual topics TBD from text files)

## Bucket 2: agreement propagation + cost-of-disagreement

The Agree/Disagree buttons in `node-card.js` currently toggle local visual state. The full feature requires:

**Data**: each node lists its dependencies (which lower-tier nodes it relies on). Add `dependencies: [nodeId, ...]` to the node data shape.

**Logic**:
- Clicking "Disagree" on node X marks X red AND walks the dependents graph: any node whose dependency chain *passes through X* gets marked red.
- The "Cost of disagreement: N nodes" readout in the node footer is the count of dependents that would be invalidated.
- "Agree" on a downstream node *narrows the disagreement range* — the disagreement is now between the two marked points.
- "Your Positions" panel (from the old site) lists all currently marked nodes.

**Reference**: `Final Draft/Website/js/agreement.js` (or wherever the old site implements this) has working logic — lift the graph traversal, rewrite the UI on top of the new design system.

## Bucket 3: derivation pages (deep-dive per node)

The `Derivation →` button currently renders but doesn't navigate.

**Per the v1 spec at `Final Draft/AI/diagram and website structure.txt`** (sections "DEEP DIVE (DERIVATION MAP) TEMPLATE"): each derivation page is its own map page showing the sub-claims that build up to the parent node. One derivation per node.

**Implementation**:
- Route by URL hash: `#derivation/<node-id>`
- Render the parent node at the top (pinned header)
- Below: a sub-page using whichever archetype fits the node's derivation structure (often Convergent Tree, sometimes a simple list)
- Return-to-parent link at the footer
- Next-unlocked-node link if applicable

## Bucket 4: global search

Header gets a search input. Filter dropdown: current page / all pages / include internals / whole words.

**Index** every node's title + claim + so-what + unlocks + eliminates + unknown + objections (per the spec — "Search node contents" toggle in the old site does this).

**Results** group by parent section, with matched text highlighted. Cap at 100, with refine-query notice if exceeded (same as old site).

**Reference**: `Final Draft/Website/js/search.js` (or wherever) for working logic.

## Optional later work

- Animation polish (chevron rotates ✓; could add height transitions on collapse)
- Keyboard navigation (tab through nodes, enter to expand, escape to collapse)
- Mobile breakpoint testing on real devices
- "Collapse all / Expand all" UX — currently exists in Convergent Tree / Matrix renderers; verify it surfaces correctly in Ladder
- Hover states for the agree/disagree buttons (currently only active state distinct)
- Print stylesheet
- JSON export (mentioned in old site README; reuse old logic)

## What stays untouched

`Final Draft/Website/` — the old attempt. Reference only. Don't modify.

`Final Draft/Handoff/mockups/*.html` — the locked design references. The build matches these. Don't change the mockups without first updating the build to match.

Anything outside `Final Draft/Website-v2/` for the build phase — every code change goes inside v2.
