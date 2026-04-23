# Cowork audit prompts

Paste-ready prompts for running an audit pass through Cowork instead of
the old Claude-CLI pipeline. Each stage is a fresh session — that keeps
scope tight and gives you a natural checkpoint between phases.

## Pipeline

1. **`1_PLAN.md`** — Pick targets, build the audit queue, write
   `PLAN.md`. Fill in the `{{...}}` placeholders before pasting.
2. **`2_AUDIT.md`** — Read the plan, audit each node in order, write
   revisions back to the per-node files, log findings. One node at a
   time with a checkpoint between each.
3. **`3_VERIFY.md`** — Dry-run compose against `ai_dev/nodes/` to confirm
   the edited tree is consistent before rebuilding. Does NOT touch the
   existing `data.json` — that's about to be overwritten in step 4.
4. **`4_APPLY.md`** — Run `compose_data.py` to rebuild `data.json`,
   with `data.json.bak` as the rollback point.

## Conventions

- Node files live at `ai_dev/nodes/<id-parts>/<id>.json`.
- Audit reports go under `ai_dev/outputs/audits/`.
- The plan document is `ai_dev/cowork_prompts/PLAN.md` (overwritten
  each pass — save a copy elsewhere if you want history).
- If any step fails, stop. `data.json.bak` (after apply) or the prior
  git commit (before apply) is the rollback.

## Why stages instead of one mega-prompt

- Planning is cheap and catches scope mistakes before any edits.
- Per-node checkpoints in the audit phase catch auditor drift early.
- Verify runs before the irreversible rebuild step.
- Apply is mechanical — once verify passes, it's one command.
