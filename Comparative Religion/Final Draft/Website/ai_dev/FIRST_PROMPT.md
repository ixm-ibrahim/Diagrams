# Sieve of Truth — Session Start

I'm continuing a project from a previous chat. I've attached a file
called SESSION_READY.md that contains all reference material and
branch-specific context bundled together.

## How to read SESSION_READY.md

The attached file contains several sections, each marked with a
`========` header. Read them in this order:

1. **Project State** — What the project is, progress so far, current target.
2. **WRITING_GUIDE.md** — How to write each section type.
3. **CHECKLIST.md** — The checks to run before and after every node.
4. **FORMAT_SPEC.md** — The JSON structure for node output.
5. **Branch-Specific Context** — Branch structure, batch plan with
   scaffolds, available vocabulary, style reference, extracted passages.

If a structural question or ambiguity comes up, ask me to paste in
`RULES_AND_PRINCIPLES.md` or `CLARIFICATIONS.md`.

## The governing goal

The content exists to demystify. Three requirements, simultaneously:
readable (lowest cognitive load), precise (philosophy-PhD rigor), and atomic
(one concept per node). These reinforce each other.

## Workflow

### Per batch:

The Batch Plan tells you which nodes to write in each batch and in what
order. Each batch includes JSON scaffolds with the exact metadata fields
pre-filled — do NOT modify id, parentId, nextIds, prevIds, or
hasDerivation. You fill in soWhat and sections only.

For each batch:

1. **Draft** all nodes in the batch.
2. **Audit** each node against CHECKLIST.md. Fix any failures.
3. **Present** the entire batch as a **single JSON array** in one code
   block. This lets me copy the whole batch at once.

Start with Batch 1 in your first response.

### Per session:

- Follow the batch plan in order. Present each batch before moving to
  the next.
- Output JSON arrays — do NOT edit data.json directly.
- When all siblings are done, the batch plan will include a synthesis
  batch for the parent node (see "Parent Synthesis" in WRITING_GUIDE).

## Stance — the hardest part

**Be a thinking collaborator, not an executor.** Independently analyze
reasoning. Flag anything weak and propose a fix.

**Inhabit the objector.** One sentence: why would a reasonable person hold
this even after reading the node? If you can't, you don't understand the
objection yet.

**Ontological smuggling.** Replace "X is not Y" with "whether or not X is Y
is not addressed here." This is the single most common failure.

**Stop after the resolution.** Correction resolves the objection. No
softening.

**If Rejected = forward-looking.** Name one downstream concept that breaks.
Match the framing verb to the node type.

**Observations = raw material.** Could someone who hasn't read the claim
recognize this as something they experience? No explanatory gloss.

**Term grounding is non-negotiable.** Apply the synonym test. If a check
fails, the ONLY response is: flag it and fix it.

Continue from where we left off.
