# Node Writing Checklist

Run every check before presenting work. Each is a gate — if it fails, stop and fix
before proceeding. **Never defend a failure; fix it.**

Every check here is a specific application of the writing goal at the top of
`WRITING_GUIDE.md`. When in doubt, reread it.

---

## Before proposing a node

- [ ] **1. Says something new?** Substitute all defined terms with their formal
  definitions. If the result is already captured by an existing node, absorb or
  remove — unless it aids recognition AND downstream nodes depend on it.

- [ ] **2. Every term grounded?** For each term in the claim: (a) defined in a
  prior node, (b) being defined now, or (c) common English with no technical
  weight. **If a check fails, stop and fix — do not construct a defense for keeping
  it.** Synonym test: if any synonym of the word appears in any node's Unlocks, it
  is NOT common English. Watch for:
  - Causal: *make, determine, produce, generate*
  - Capacity: *can, able, -able* (only after 1.4.4.1)
  - Logical: *if* (only after 1.4.4.6)
  - Temporal: *before, after, then* (grounded by Sequence)

- [ ] **3. Terms used by definition, not connotation?** Substitute each formal
  definition into the claim. Still reads correctly?

- [ ] **4. Structurally placed correctly?** Trace dependencies. Logical structures
  → 1.4. Processes → 1.5. Types → children of the parent concept.

- [ ] **5. General rule grounded in observed cases?** Observe → identify → induce.
  Never state the rule then justify after.

---

## Before writing section content

- [ ] **6. Section Writing Guide applied?**
  - Observations: raw material only — no conclusions, arguments, meta-commentary,
    vocabulary labeling, or explanatory gloss?
  - Observations: only grounded terms?
  - Conclusion: near-verbatim to claim?
  - Definitions: direct (*"X IS..."*), not meta (*"X is the label for..."*)?
  - If Rejected: forward-looking costs, not backward-echoing?
  - Objections: steelmanned with all four subSections (Basis, Commitments, What's
    Missing, Correction)?
  - No section justifies the current node by citing a future node?

---

## Stance checks (thinking quality, not just structure)

- [ ] **S1. Inhabit the objector.** Before any Correction: *why would a reasonable
  person hold this objection even after reading the node?* If you can't say it in
  one sentence, you don't understand it yet. Would the holder feel accurately
  represented?

- [ ] **S2. Ontological smuggling check.** For every claim in an objection
  response: am I describing what is observed, or claiming what exists / doesn't
  exist? Replace *"X is not Y"* (ontological denial) with *"whether or not X is Y
  is not addressed here"* (scope). Also valid: *"Positing Y has no observational
  ground at this level."*

- [ ] **S3. If Rejected: name one downstream concept that breaks.** If you can't
  name one, you're about to restate the claim in the negative. Match the framing
  verb to the node type (*Without X / Without recognizing X / Without distinguishing
  X*).

- [ ] **S4. Raw material test.** Could each observation be presented to someone who
  hasn't heard the claim, and they'd recognize it? If it only makes sense *in light
  of* the conclusion, it's a conclusion in disguise.

- [ ] **S5. Stop after the resolution.** Once the Correction resolves the
  objection, stop. No softening, qualifying, hedging.

- [ ] **S6. Root-cause commitment check.** Do the Objection Commitments isolate
  the root-cause — the assumption that actually makes the objection fail? Or do
  they list every assumption? Commitments should set up the load-bearer, not be
  independent claims.

- [ ] **S7. Observations woven in?** Does at least one objection reference the
  node's own observations as concrete examples?

- [ ] **S8. Correction neutrality check.** Does the Correction endorse the node's
  position *as though already proven*? At early levels especially, Corrections
  should show the objection fails on its own terms — not that the node is *"right."*

- [ ] **S9. Scope-defense quality.** If a Correction uses *"not addressed here,"*
  does it explain WHY the vocabulary isn't available? When the objection imports
  ungrounded terms, does the Correction avoid agreeing/disagreeing with those
  terms?

- [ ] **S10. Bullet size check.** Any bullets exceed ~400 chars? Split at sentence
  boundaries or restructure with nested `{text, items}`.

---

## After completing a node

- [ ] **7. Dependency audit.** Every term in every claim passes check 2. No term
  uses a later sibling's definition.

- [ ] **8. Synonym collision.** Any term already in vocabulary with a different
  meaning? Rename.

- [ ] **9. Final child test.** Does the last child naturally arrive at the parent's
  meaning?

- [ ] **10. Convention 14 sweep.** Every node is a genuine atomic step? No
  structural-completeness-only nodes? No skipped steps?

- [ ] **11. If Rejected consequence audit.** For each consequence: does a real
  position exist where someone rejects the claim but disputes the consequence? If
  so → missing Objection.

- [ ] **12. Real-world objection audit.** Are there real philosophical positions or
  commonly held views that challenge this claim and aren't represented?

- [ ] **13. Parallel symmetry check.** Sibling nodes with parallel structures get
  parallel treatment?

- [ ] **14. Skeptical reader test.** Read as a person, not a checklist. Does it
  land? Low cognitive load? Every section addresses what a skeptic would wonder?
  Any sentence needs re-reading?

- [ ] **15. Independent reasoning check.** Am I thinking, or implementing
  mechanically? Flag anything weak, incorrect, or imprecise — propose a fix.
