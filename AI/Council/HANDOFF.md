# The Council — Handoff Prompt

Paste everything below the line into a fresh Claude chat to continue development.

---

I'm continuing work on a project called **The Council** — a multi-perspective AI deliberation tool for asking philosophical questions and demystifying contested social, political, and intellectual topics. Each session feeds into per-topic research project folders. Pick up where the prior chat left off.

**Read these files before doing anything else:**

- `/sessions/nifty-sharp-knuth/mnt/Council/council.py` — the current single-file Python HTTP server + HTML app
- `/sessions/nifty-sharp-knuth/mnt/Council/README.md` — current docs
- `/sessions/nifty-sharp-knuth/mnt/uploads/01 - Writing Goal.txt` — my writing style guide. Every output The Council produces follows this style. So does your own writing in comments, docs, and conversation.
- `/sessions/nifty-sharp-knuth/mnt/Comparative Religion/` — example of the kind of research project The Council feeds into (the deliverable shape)

**Current state.** The Council is a flat sequential council: question in, N members speak in order each reading prior responses, an Arbiter synthesizes, Markdown copied to clipboard. Two backends: `claude -p` CLI subprocess (default), Anthropic API key (optional). UI is dark, Cormorant Garamond + DM Sans, side panels for history and settings, modal for member editor.

**Constraints.**

- Claude only. No OpenRouter, no Gemini, no third-party API keys. I have unlimited Claude through my work plan, accessed via the Claude CLI. The Anthropic API key path stays as an option but isn't required.
- True multi-model diversity is unreachable under this constraint. We mitigate within Claude through (a) rich character-specific prompts naming real scholars and traditions, (b) anti-correlation scaffolding prepended to every council seat, (c) per-seat Opus / Sonnet / Haiku and temperature mixing. README must document the ceiling honestly so I know when to discount council consensus.

**Target architecture — a four-stage pipeline.**

*Stage 1 (Pre)* — A **Prior Scout** agent exposes the framings, hedges, RLHF-shaped softenings, and corporate-safe defaults Claude brings to the question. Its job is exposure, not opposition; do not name or prompt it as "anti-Claude." Plus a **House Style Card** agent that prepares the style guide for downstream agents.

*Stage 2 (Council)* — N tradition-based members deliberate sequentially. Each reads the Stage 1 cards plus prior speakers. Members are named scholars within real traditions, not generic role-cards.

*Stage 3 (Assessment)* — An **Anonymizer** strips speaker labels. A **Quality Assessor** scores each anonymized response against an explicit rubric (real engagement vs. hedging, authentic tradition vs. AI-default-helpful, productive conflict, style adherence, dodges). An optional **redo loop** sends low-scoring responses back to the originating seat with the critique attached. Cap: one redo per seat.

*Stage 4 (Synthesis)* — A **Final Synthesizer** reads the assessed, re-attributed responses and produces a polished report in house style.

A **Fast Mode** toggle skips Stages 1 and 3 (Council + simple Arbiter only) for quick questions.

**Profiles** are named bundles of Stage 2 lineup + active set + speaker order + per-seat model and temperature + optional house-style override. Five built-ins planned: Decision, Philosophy, Comparative Religion, Politics & Society, Demystify. Real prompt-writing work — named scholars, traditions, specific commitments — not colored boxes.

**Projects** are folders. Each project gets a `.council/` subdirectory: `project.json` (with optional `vault_path`), `sessions/` (JSON transcripts), `reports/` (Markdown deliverables). The vault (e.g. Obsidian) lives in a separate folder; vault features stay dormant unless `vault_path` is set, and the vault is read-only by default.

**The 11-phase plan.**

1. **Pipeline foundations.** Refactor `council.py` engine into a stage-based pipeline. Provider layer abstraction (Claude only for now, adapter-shaped). House Style persistent setting, defaulted to my style file, prepended to every agent. Fast Mode toggle. Raise `max_tokens` to 4000, CLI timeout to 300. Add per-profile speaker order + shuffle.
2. **Stage 1 agents** — Prior Scout, House Style Card.
3. **Stage 3 agents** — Anonymizer, Quality Assessor with explicit rubric, optional redo loop (one redo per seat).
4. **Stage 4 Final Synthesizer** — replaces the simple Arbiter in full-pipeline mode; simple Arbiter remains for Fast Mode.
5. **Profiles with real characters** — five built-ins, anti-correlation scaffolding in every Stage 2 seat.
6. **Folder-scoped projects** — `.council/` structure, sessions JSON, reports Markdown, `project.json` with optional `vault_path`.
7. **Within-Claude diversification** — per-seat Opus / Sonnet / Haiku and temperature pickers.
8. **Continuation rounds** — follow-up after a session, feeds prior transcript.
9. **Compose to long-form** — multiple sessions in a project become a single essay in house style.
10. **Vault integration (optional)** — Obsidian frontmatter, wikilinks, optional pre-deliberation read of matching vault notes.
11. **Local grounding** — `.council/sources/` per project, source-reader agent in Stage 1.

**Start with Phase 1.** Refactor the engine into the stage-based pipeline. The four stages exist as data structures from day one: Stage 1 empty, Stage 2 = current members, Stage 3 empty, Stage 4 = current Arbiter. Existing UI keeps working in both Fast Mode and Full Mode (which currently produces identical output until later phases populate the stages). Add the House Style setting. Bump the limits. Show me the diff when Phase 1 is done and tell me what's working before moving to Phase 2.

Set up task tracking when you begin so I can see progress. Ask before making destructive structural changes to my files. Follow my writing style guide in everything you produce.
