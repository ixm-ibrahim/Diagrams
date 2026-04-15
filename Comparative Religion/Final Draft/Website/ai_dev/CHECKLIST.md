# Node Writing Checklist

Run every check before presenting work. Each is a gate — if it fails, stop
and fix before proceeding.

---

## Before proposing a node

- [ ] **1. Says something new?** Substitute all defined terms with formal
  definitions. If the result is already captured by an existing node, absorb
  or remove — unless it aids recognition AND downstream nodes depend on it.

- [ ] **2. Every term grounded?** For each term in the claim: (a) defined
  in a prior node, (b) being defined now, or (c) common English? If a check
  fails, **stop and fix — do not construct a defense for keeping it.**
  Apply the synonym test: if any synonym of the word appears in any node's
  Unlocks, it is NOT common English. Watch for:
  - Causal: "make," "determine," "produce," "generate"
  - Capacity: "can," "able," "-able" (only after 1.4.4.1)
  - Logical: "if" (only after 1.4.4.6)
  - Temporal: "before," "after," "then" (grounded by Sequence)

- [ ] **3. Terms used by definition, not connotation?** Substitute each
  formal definition into the claim. Still reads correctly?

- [ ] **4. Structurally placed correctly?** Trace dependencies. Logical
  structures → 1.4. Processes → 1.5. Types → children of parent concept.

- [ ] **5. General rule grounded in observed cases?** Observe → identify →
  induce. Never state the rule then justify after.

---

## Before writing section content

- [ ] **6. Section Writing Guide applied?**
  - Observations: raw material only? No conclusions, arguments,
    meta-commentary, vocabulary labeling, or explanatory gloss?
  - Observations: only grounded terms?
  - Conclusion text: near-verbatim to claim?
  - Definitions: direct ("X IS..."), not meta ("X is the label for...")?
  - If Rejected: forward-looking costs, not backward-echoing?
  - Objections: steelmanned with four-part structure (Basis, Commitments, What's Missing, Correction)?
  - No section justifies current node by citing a future node?

---

## Stance checks (thinking quality, not just structure)

- [ ] **S1. Inhabit the objector.** Before any Objection response: why
  would a reasonable person hold this *even after reading the node*? If you
  can't say in one sentence, you don't understand the objection yet. Test:
  would the holder feel accurately represented?

- [ ] **S2. Ontological smuggling check.** For every claim in an objection
  response: am I describing what is observed, or claiming what exists /
  doesn't exist? Replace "X is not Y" (ontological denial) with "whether
  or not X is Y is not addressed here" (scope clarification). Also valid:
  "Positing Y has no observational ground at this level."

- [ ] **S3. If Rejected: name one downstream concept.** What specific
  concept becomes impossible? What collapses into what? If you can't name
  one, you're about to restate the claim in the negative. Match the framing
  verb to the node type (Without X / Without recognizing X / Without
  distinguishing X).

- [ ] **S4. Raw material test.** Could each observation be presented to
  someone who hasn't heard the claim, and they'd recognize it? If it only
  makes sense in light of the conclusion, it's a conclusion in disguise.

- [ ] **S5. Stop after the resolution.** Once the Correction resolves the
  objection, stop. No softening, qualifying, or hedging.

- [ ] **S6. Root-cause commitment check.** Do the Objection Commitments
  isolate the root-cause assumption — the one that actually makes the
  objection fail? Or do they list every assumption the objector holds?
  Commitments should set up the load-bearer, not be independent claims.

- [ ] **S7. Observations woven in?** Does at least one objection reference
  the node's own observations as concrete examples? The observations are
  the experiential data the node is grounded in — objections implicitly
  challenge them.

- [ ] **S8. Correction neutrality check.** Does the Correction endorse the
  node's position as though already proven? At early levels especially,
  Corrections should be epistemically neutral — showing the objection
  fails on its own terms, not that the node is "right."

- [ ] **S9. Scope-defense quality.** If a Correction uses "not addressed
  here," does it explain WHY the vocabulary isn't available? Or does it
  just assert scope? When the objection imports ungrounded terms, does
  the Correction avoid agreeing/disagreeing with those terms?

- [ ] **S10. Bullet size check.** Are any bullets walls of text (>400
  chars)? Split at sentence boundaries or restructure with nesting.

---

## After completing a node

- [ ] **7. Dependency audit.** Every term in every claim passes check #2.
  No term uses a later sibling's definition.

- [ ] **8. Synonym collision.** Any term already in vocabulary with a
  different meaning? Rename.

- [ ] **9. Final child test.** Does the last child naturally arrive at the
  parent's meaning?

- [ ] **10. Convention 14 sweep.** Every node is a genuine atomic step? No
  structural-completeness-only nodes? No skipped steps?

- [ ] **11. If Rejected consequence audit.** For each consequence: does a
  real position exist where someone rejects the claim but disputes the
  consequence? If so → missing Objection.

- [ ] **12. Real-world objection audit.** Are there real philosophical
  positions or commonly held views that challenge this claim and aren't
  represented?

- [ ] **13. Parallel symmetry check.** Sibling nodes with parallel
  structures get parallel treatment?

- [ ] **14. Skeptical reader test.** Read the whole node as a person, not
  a checklist. Does it land? Low cognitive load? Every section addresses
  what a skeptic would wonder? Any sentence needs re-reading?

- [ ] **15. Independent reasoning check.** Am I thinking, or implementing
  mechanically? Flag anything weak, incorrect, or imprecise — propose a
  fix.

---

## Common failure patterns

These are the most frequent mistakes. Each is a red flag:

| Pattern | What goes wrong | Fix |
|---------|----------------|-----|
| **Defending identified problems** | A check fails, AI argues to keep it | Stop, flag, fix. Never rationalize. |
| **Formulaic observation gloss** | "X — explanatory phrase" on every observation | Each observation is the datum. Period. |
| **Proposing before auditing** | Full structure presented, audit only when prompted | Audit every proposal before presenting. |
| **Circular future citation** | Justifying current node by citing unestablished node | Remove. |
| **Self-resolving Corrections** | "Maybe they just have a weaker version" | Force the real dilemma. Name the costly commitment. |
| **Backward-echoing If Rejected** | "Without X, there is no X" | Show a downstream consequence the reader cares about. |
| **Ontological denial in Corrections** | "This targets X not Y" (claims Y is wrong) | "Whether or not Y is not addressed here." |
| **Project-meta language** | "Downstream nodes," "this branch," "convention 9b" | Reader-facing language only. |
| **Overcomplicated presupposition responses** | Three paragraphs on experiential vs theoretical | Awareness of X ≠ theory of X. State, apply, stop. |
| **Listing every commitment** | Objection Commitments enumerates all assumptions | Isolate the root-cause — the one that breaks. Others set it up. |
| **Abstract objections ignoring observations** | Objection talks about "phenomena" generically | Reference the node's actual observations as concrete examples. |
| **Premature commitment in Corrections** | Correction endorses the node's truth at early levels | Stay neutral — show the objection fails on its own terms. |
| **Formulaic scope-defense** | "Not addressed here" without explanation | Explain WHY the vocabulary isn't available and what the objector needs. |
| **Wall-of-text bullets** | Single bullet >400 chars, dense paragraph | Split at sentence boundaries or restructure with nested bullets. |
| **Vocabulary-development language in objections** | "This provides vocabulary for..." in Corrections | "This grounds..." — the tree is building foundations, not a glossary. |
