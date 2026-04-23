# Cowork Prompt 1 — Plan an audit pass

Paste this into a fresh Cowork session. Replace the `{{...}}` placeholders
before sending. This session produces a plan document; you review it
before kicking off the audit itself.

---

I'm auditing existing content in the Sieve of Truth tree. I need you to
plan the next audit pass — pick which nodes to audit and which section
of each node to focus on — and write the plan to a file I can review.

## Context you have direct access to

The project is laid out under `ai_dev/`:

- `ai_dev/reference/` — project docs. Read these first:
  - `PROJECT_REFERENCE.md` — what the project is and where it stands
  - `WRITING_GUIDE.md` — how each section type should be written
  - `CHECKLIST.md` — the checks to run on every node
  - `FORMAT_SPEC.md` — node JSON structure
  - `RULES_AND_PRINCIPLES.md` — structural rules, grounding
  - `CLARIFICATIONS.md` — resolved design decisions
- `ai_dev/nodes/` — one JSON file per node, nested by id parts. Node
  `1.2.5.4` lives at `ai_dev/nodes/1/2/5/4/1.2.5.4.json`. The subfolder
  at `ai_dev/nodes/<id-parts>/` is that node's whole sub-tree.
- `ai_dev/outputs/audits/` — prior audit reports if any exist.

Don't bundle these into a context file — just read what you need.

## This pass

- **Target(s):** {{e.g. 1.1.3, or 1.2 and all descendants}}
- **Focus section:** {{Observations | Objections | Conclusion | Unlocks | If Rejected | Derivation | Claim | Short Title | So What | Search | all}}
- **Max queue size:** {{e.g. 10 nodes — keep the batch small enough to
  actually finish}}

## What I want you to do

1. Read the reference docs listed above.
2. Walk the relevant sub-tree under `ai_dev/nodes/` and pick the audit
   queue — targets plus descendants with content, in depth-then-id order.
3. For each node in the queue, note its path and a one-line hint of what
   looks risky about its focus section (if anything jumps out from a
   skim). This is a plan, not the audit — don't rewrite anything yet.
4. Identify the ancestor chain and completed siblings each node will need
   for cross-section coherence, so the audit session can find them quickly.
5. Flag any structural concerns that should be resolved before auditing
   (missing sections, ambiguous grounding, sibling inconsistencies).

## Output

Write the plan to `ai_dev/cowork_prompts/PLAN.md` with this shape:

```
# Audit Plan — {{target}} — {{focus}}

## Scope
- Target: {{...}}
- Focus section: {{...}}
- Total nodes in queue: N

## Reference
- Ancestor chain: a.b, a.b.c, ...
- Relevant completed siblings: ...
- Relevant grounding nodes: ...

## Queue (audit in this order)
1. 1.1.3 — ai_dev/nodes/1/1/3/1.1.3.json — skim note: ...
2. 1.1.3.1 — ai_dev/nodes/1/1/3/1/1.1.3.1.json — skim note: ...
...

## Structural concerns to resolve before auditing
- ...
```

Do NOT edit any node files in this session. Stop after writing PLAN.md
and give me a short summary of what's in the queue and anything you
flagged.
