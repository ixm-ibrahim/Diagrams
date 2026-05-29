# Website v2

Greenfield rebuild of the Comparative Religion / objective-truths argument map. Design system locked in `../Handoff/`. This codebase scaffolds the locked archetypes.

## Status

**All four archetypes + Section 7 topic cluster wrapper are scaffolded with sample data.** Smoke-tested: every renderer module loads cleanly, every section in `data.json` parses, all assets serve over HTTP.

- ✅ Tokens, base styles, frame shell, section picker
- ✅ Light/dark theme toggle with localStorage persistence
- ✅ Universal collapsible-sections affordance with collapse-all/expand-all
- ✅ Rainbow Ladder renderer (Section 1)
- ✅ Convergent Tree renderer (Section 3)
- ✅ Comparison Matrix renderer with filter pills + scroll-sync + per-criterion synthesis (Section 5)
- ✅ Evidence Cards renderer — extends Matrix with serif-italic quote treatment (Section 6)
- ✅ Section 7 topic-cluster wrapper with topic synthesis (clustered Matrix variant)
- ✅ Node-card internals (Claim / So-what / Unlocks / Eliminates / Unknown / Objections + Derivation / Agree / Disagree / Cost)
- ✅ Sample data exercising all five sections

Still TODO (post first-pass build):

- ⏳ Global search across all sections + nodes
- ⏳ Agreement propagation logic (clicking disagree turns dependents red, computes Cost-of-disagreement automatically)
- ⏳ Derivation page (full deep-dive per node — the `Derivation →` button currently renders but doesn't navigate yet)
- ⏳ Real content migration from `../Website/data.json` (Section 1 is most developed here) and `../../AI/Comparative Religion Diagram/*.txt` (Sections 2+ are more developed in the text files)
- ⏳ Animation polish (chevron rotation works; could add height transitions on collapse)
- ⏳ Keyboard navigation
- ⏳ Mobile breakpoint verification on real devices

## Run locally

This is plain HTML/CSS/JS. ES modules require an `http://` origin — `file://` won't work. Quick options:

```sh
# From this directory:
python3 -m http.server 8080
# Then open http://localhost:8080/
```

or:

```sh
npx serve .
```

## File layout

```
Website-v2/
├── index.html               # shell — header, breadcrumb, section picker, content mount
├── data.json                # all section data (currently: samples for 5 sections)
├── css/
│   ├── tokens.css           # design system: colors, type, spacing
│   ├── base.css             # body, frame, headers, section picker
│   ├── collapsible.css      # universal section collapse
│   ├── archetype-ladder.css # Rainbow Ladder layout (Section 1, 8 conclusions)
│   ├── archetype-tree.css   # Convergent Tree layout (Sections 3, 4)
│   ├── archetype-matrix.css # Comparison Matrix + Evidence Cards + topic clusters (Sections 5, 6, 7)
│   └── node-card.css        # expanded-card internal strips (shared by all)
└── js/
    ├── main.js              # entry — loads data, dispatches to renderer, wires section picker
    ├── theme.js             # light/dark toggle
    ├── collapsible.js       # universal section collapse with localStorage
    ├── render-ladder.js     # Rainbow Ladder renderer
    ├── render-tree.js       # Convergent Tree renderer
    ├── render-matrix.js     # Matrix + Evidence + Section 7 clustered (one renderer, three modes)
    └── node-card.js         # expanded-state strips renderer
```

## What's new in v2 vs the old site

- **Color is semantic.** Each tier (1–7) has its own hue. Same palette redeployed for worldview-position in matrix/evidence archetypes. The old site reserved color only for agree/disagree state.
- **Per-archetype layouts.** Section pages don't all use the same card template. Convergent Tree differs from Comparison Matrix differs from Rainbow Ladder.
- **Per-node-card internals**: Claim / So-what / Unlocks / Eliminates / Unknown / Objections strips with a typed-objection taxonomy.
- **Cost-of-disagreement readout**: clicking disagree on a node shows the count of downstream nodes that would be invalidated.
- **Universal collapsibility**: every section (lane, criterion, topic cluster) collapses with a chevron header.

See `../Handoff/` for full design system spec, decisions log, and the locked mockups.
