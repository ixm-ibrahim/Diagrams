# Handoff — read this first

You're picking up a project in progress. Here's the situation in 250 words.

## What this project is

The user (Ibrahim) is rebuilding an interactive web page that navigates how objective truths are derived from first principles, structured as a comparative epistemology + comparative religion argument. Source material lives in `Final Draft/../AI/Comparative Religion Diagram/` (text files, sections 0–9 + appendices A–F) and in the draw.io diagrams at `Comparative Religion (High Level).drawio` (40-page master). An earlier website attempt exists at `Final Draft/Website/` — DO NOT modify it. The rebuild lives at `Final Draft/Website-v2/` and the v1 scaffold is done.

## Where we are in the work

**Phase 1 (design) is locked.** Six pieces, each verified across desktop+mobile and light+dark:
1. Rainbow Ladder — Section 1, conclusion summaries
2. Convergent Tree — Sections 3, 4
3. Comparison Matrix — Section 5
4. Evidence Cards — Section 6
5. Node-card internals — shared expanded-state strips
6. Section 7 topic-cluster wrapper

All locked HTML mockups in `mockups/`. Open in a browser to see the design.

**Phase 2 (build) is scaffolded.** `Final Draft/Website-v2/` contains a working multi-archetype site with sample data exercising all five archetype variants. See `Final Draft/Website-v2/README.md` for current state and how to run locally (requires a local HTTP server — ES modules don't work over `file://`).

**Phase 3 (real content + advanced features) is the remaining work** — tracked in `04_NEXT_STEPS.md`. Four follow-up tasks:
- Content migration (Section 1 from old website, Sections 2+ from text files)
- Agreement propagation + cost-of-disagreement graph traversal
- Derivation pages (deep-dive per node)
- Global search across nodes

## Read order for a fresh session

1. **This file** — done.
2. `Final Draft/Website-v2/README.md` — what's currently built and runnable.
3. `01_DESIGN_SYSTEM.md` — palette, tokens, principles, dark-mode-CSS-gotcha.
4. `02_ARCHETYPES.md` — when to use which of the locked archetypes + Section 7 wrapper spec.
5. `03_DECISIONS.md` — every design choice and why (so you don't re-litigate).
6. `04_NEXT_STEPS.md` — the build roadmap and follow-up tasks.
7. `05_OLD_SITE_AUDIT.md` — diagnosis of the previous attempt; what to lift, what to discard.

Mockups in `mockups/` are the source of truth for visual design. The Website-v2 build implements these.

## The most important rules (won't be re-litigated)

- **Demystification, not persuasion.** Content presented transparently and evidence-led. Claims aren't asserted before they're derived. Tone is neutral but evidence-led — takes sides only where evidence leads, never as an entry posture.
- **Color carries semantic meaning.** Tier elevation (Rainbow Ladder, Convergent Tree) or worldview position (Comparison Matrix, Evidence Cards). The old site discarded this; the new build preserves it.
- **Per-archetype orientation.** Rainbow Ladder has apex-on-top (pyramid). Other archetypes go 1→N top to bottom (inductive). Locked.
- **Sentence case everywhere.** Never Title Case, never ALL CAPS (small uppercase used only for labels).
- **CSS gotcha**: every text element inside a hardcoded-mode frame must use `color: inherit` or explicit color. `var(--color-text-primary)` flips with the host theme and breaks mockups.

## What you should NOT do

- Don't modify `Final Draft/Website/` (the old attempt — keep as reference)
- Don't re-litigate locked design decisions without checking `03_DECISIONS.md` first
- Don't paste mockup content into production (mockup text is illustrative — real content per `04_NEXT_STEPS.md` content-migration plan)
- Don't add features the user hasn't asked for (the previous site over-engineered)

## Quick orientation check

If the new session starts and the user says something like "let's continue" or "what's next":

- Skim this file + `Website-v2/README.md` (in that order)
- Confirm understanding briefly
- Ask: **content migration first (real data), or feature work (search/propagation/derivation) first?** Either is unblocked; recommend content migration so the site shows real material instead of placeholder.
