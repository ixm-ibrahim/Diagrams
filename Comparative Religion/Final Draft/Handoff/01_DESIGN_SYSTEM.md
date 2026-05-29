# Design system

## Core principle

The user's previous website attempt felt "stale" because it rendered 140+ visually identical white cards regardless of section, with color reserved only for agreement state (green/red). The diagram, by contrast, uses a **7-color rainbow palette** semantically — colors mean something. The new build reinstates that semantic color system as the visual identity.

## The 7-color rainbow palette

Same palette across all archetypes. The *meaning* of the colors shifts per archetype:

- **In Rainbow Ladder and Convergent Tree**: colors encode **tier elevation** (epistemic depth). Tier 1 (foundation) = red, Tier 7 (apex) = pink/mauve.
- **In Comparison Matrix and Evidence Cards**: same palette encodes **worldview position** on a spectrum from atheism (red) to monotheism (blue), with extension slots at coral, amber, green, purple, pink for future worldviews.

### Tier → color mapping (Rainbow Ladder, Convergent Tree)

| Tier | Name (default) | Hex 400 | 800 (light-mode text) | 100 (dark-mode text) | Used in |
|------|---|---|---|---|---|
| 1 | Subject / Foundation | `#E24B4A` red | `#791F1F` | `#F7C1C1` | Building Confidence: Historical event, Philosophical claim |
| 2 | Evidence | `#D85A30` coral | `#712B13` | `#F5C4B3` | Building Confidence: Eyewitness testimony, archaeological alignment |
| 3 | Corroboration | `#EF9F27` amber | `#633806` | `#FAC775` | Building Confidence: Multiple independent corroborations |
| 4 | Integrity | `#639922` green | `#27500A` | `#C0DD97` | Building Confidence: Unbroken chain of transmission |
| 5 | Coherence | `#378ADD` blue | `#0C447C` | `#B5D4F4` | Building Confidence: Consistency with broader context |
| 6 | Robustness | `#7F77DD` purple | `#3C3489` | `#CECBF6` | Building Confidence: Resistance to fabrication |
| 7 | Verification | `#D4537E` pink | `#72243E` | `#F4C0D1` | Building Confidence: Scientific / iterative verification |

### Spectrum → worldview mapping (Comparison Matrix, Evidence Cards)

Same hex codes, different semantic. Worldviews are positioned along an atheism→monotheism spectrum:

| Slot | Hex | Used for (current) | Reserved for (future) |
|---|---|---|---|
| 1 (red) | `#E24B4A` | Atheism | — |
| 2 (coral) | `#D85A30` | — | Pantheism, deistic naturalism |
| 3 (amber) | `#EF9F27` | Polytheism | — |
| 4 (green) | `#639922` | Trinitarianism / Christianity | — |
| 5 (blue) | `#378ADD` | Monotheism / Islam | — |
| 6 (purple) | `#7F77DD` | — | Deism |
| 7 (pink) | `#D4537E` | — | Other |

**Critical**: when a worldview appears in multiple sections, it uses the same color across all of them. Christianity in Section 5, 6, and 7 is always green. Islam is always blue. Color identity is global.

## Background tints

Each color has a corresponding background tint at very low opacity for visual zones (Convergent Tree lanes, all matrix/evidence cells):

- **Light mode**: `rgba(R, G, B, 0.025)` to `0.035` — very faint
- **Dark mode**: `rgba(R, G, B, 0.045)` to `0.05` — bumped slightly so it stays perceptible on dark bg

This is **halved** from the user's first reaction ("too bright") — the tints recede behind the cards rather than competing with them.

## Neutral tokens

```
Light mode:
  --bg-frame: #FFFFFF
  --text: #2C2C2A
  --text-tertiary: #888780  (called --tt in mockups)
  --border: rgba(0,0,0,0.08)
  --divider: rgba(0,0,0,0.12)
  --quote-line: rgba(0,0,0,0.15)
  --synth-bg: rgba(0,0,0,0.025)
  --synth-border: rgba(0,0,0,0.15)

Dark mode:
  --bg-frame: #1F1D1B
  --text: #E5E2DD
  --text-tertiary: #B4B2A9
  --border: rgba(255,255,255,0.08)
  --divider: rgba(255,255,255,0.1)
  --quote-line: rgba(255,255,255,0.18)
  --synth-bg: rgba(255,255,255,0.04)
  --synth-border: rgba(255,255,255,0.18)
```

The "root" cards (synthesized top-level claims like "Historical claim" and "Logical claim" in Building Confidence) use neutral gray instead of any tier color — they sit *above* the rainbow, not in it. See `--root` and `--rootn` in the mockups.

## Typography

- Default body: sans-serif (system Anthropic Sans or fallback), weight 400, line-height 1.4–1.5
- Headings: weight 500 only. Never 600/700.
- Quoted material (Evidence Cards): `var(--font-serif)` italic — editorial blockquote treatment
- Sentence case everywhere. Never Title Case. Never ALL CAPS (small uppercase used for labels: eyebrow tags, source refs, tier tags).
- Tier tags and source refs: 9.5–10px, weight 500, letter-spacing 0.04–0.06em, uppercase
- Card body text: 10.5–11px

## Critical CSS gotcha (encountered during design)

The Claude.ai widget host **pre-styles `h2` with `color: var(--color-text-primary)`**, which auto-flips with the host's light/dark mode. Inside a hardcoded-light-mode preview frame, the h2 would render in the host's dark-mode color (light text) on white background — invisible.

**Fix**: every text element inside a mockup frame must use `color: inherit` or an explicit hardcoded color. Never rely on `--color-text-primary` inside the frame.

The same fix applies to the production build: frame containers establish their own `color` and text elements inherit.

## What gets preserved from the old site

These features in `Final Draft/Website/` are worth keeping (lift the logic, rewrite the UI):

- Agreement tracking with propagation (clicking disagree on a node turns it red, propagates to dependents)
- Inline derivation expansion (click "Derivation" to drill into a node's sub-claims)
- Global search across all nodes (with filter for current page only)
- Tab expander for terminal nodes
- Light/dark theme toggle (with localStorage persistence)
- Keyboard navigation
- "Your Positions" panel showing all active agree/disagree votes
- JSON export of current view
- Breadcrumb navigation
- Mobile-responsive layout

## What gets discarded from the old site

- Uniform white-card rendering of all nodes (the "stale" feeling — see `05_OLD_SITE_AUDIT.md`)
- Per-sibling hue rotation (color-by-position-in-group with no global meaning)
- The single `nodeRow()` template applied to all 140+ nodes regardless of section
- Color tokens defined only for agree/disagree, nothing else

## Source-of-truth files

- **Source content**: `AI/Comparative Religion Diagram/0–9 + appendices A–F.txt` (sections 0 through Appendix F, plus LDS Addendum)
- **Source diagram**: `Comparative Religion (High Level).drawio` (40-page master)
- **SVG exports**: `AI/SVG Export/` (40 SVG files, one per diagram page)
- **Earlier spec**: `Final Draft/AI/diagram and website structure.txt` (the user's v1 spec — node templates, move types, objection taxonomy; the v2 design preserves the per-node rigor but lets map pages vary per archetype)
- **Old website** (reference only): `Final Draft/Website/`
- **New build target**: `Final Draft/Website-v2/` (does not exist yet)
