# Cowork Prompt 2 — Run the audit

Paste this into a fresh Cowork session AFTER you've reviewed
`ai_dev/cowork_prompts/PLAN.md` from the planning session and are happy
with the queue. This session does the actual audit — it reads each node,
revises the focus section, writes it back to disk, and logs findings.

---

I'm auditing existing content in the Sieve of Truth tree. A prior
session wrote the plan to `ai_dev/cowork_prompts/PLAN.md`. Your job is
to execute it.

## Read first

1. `ai_dev/cowork_prompts/PLAN.md` — the queue, focus section, and
   ancestor/sibling references for this pass.
2. `ai_dev/reference/WRITING_GUIDE.md` — pay close attention to
   *The Governing Goal*, *General Principles*, and the section you're
   auditing.
3. `ai_dev/reference/CHECKLIST.md` — every check.
4. `ai_dev/reference/FORMAT_SPEC.md` — node JSON structure.
5. `ai_dev/reference/RULES_AND_PRINCIPLES.md` and
   `ai_dev/reference/CLARIFICATIONS.md` — structural rules.

Don't bundle these — just read what you need on demand.

## The governing goal

The content exists to demystify. Three requirements simultaneously:
readable (lowest cognitive load), precise (philosophy-PhD rigor), and
atomic (one concept per node). Every audit decision flows from them.

## Stance

**Be an objective, critical auditor, not a rubber stamp.** If the section
is weak, imprecise, or quietly wrong, say so and propose the fix.
Defending identified problems is the #1 failure mode.

## Workflow — one node at a time, in queue order

For each node in the queue:

1. Read the node file at the path listed in PLAN.md.
2. Read the ancestor chain and completed siblings listed in PLAN.md for
   cross-section coherence.
3. Locate the focus section inside `sections`. That's the only section
   you revise. Skim the rest but don't change them.
4. Run every CHECKLIST.md check that applies to the focus section.
   Name each check, quote offending text, explain why it fails.
5. Verify term grounding. Every term must be (a) defined in a prior
   node, (b) defined in this node, or (c) common English. Apply the
   synonym test. When in doubt, search the ancestor chain's files under
   `ai_dev/nodes/` for where the term is first introduced.
6. Rewrite the focus section to pass every check. Do NOT touch `id`,
   `parentId`, `nextIds`, `prevIds`, `hasDerivation`, `claim`,
   `shortTitle`, `soWhat`, `search`, or any other section in `sections`.
7. **Write the revised node back to its file** — overwrite the existing
   node file in place, preserving JSON indent=2 and UTF-8.
8. Append an audit report to `ai_dev/outputs/audits/{{TODAY}}_{{focus}}.md`
   with this shape:

   ```
   ## <node id> — <PASS | revised | no-change>

   **Checks**
   - Check N (name): PASS / FAIL — quote + reason if fail
   - ...

   **Changes made**
   - <one-line summary of each edit to the focus section>

   **Spotted elsewhere** (flag-only, don't fix in this pass)
   - <section>: <issue>
   ```

9. Stop after each node. Tell me what you changed in one sentence and
   wait for "next" before moving on. This lets me catch drift early
   instead of finding it after 10 nodes.

## Guardrails

- Never edit a file outside `ai_dev/nodes/<id-parts>/<id>.json` and the
  audit log file.
- If a node passes every check with no changes needed, say so and leave
  the file untouched.
- If you hit a structural problem (missing section, malformed JSON,
  sibling inconsistency that needs a decision), stop and ask me —
  don't paper over it.
- If the file you wrote would change a field you shouldn't have
  touched, don't write it. Re-draft instead.

Start with the first node in PLAN.md.
