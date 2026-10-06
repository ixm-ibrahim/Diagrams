# Validation rounds 2–3 — CLAIM-STRUCTURE.md drafts 2/3 (2026-07-07)

**Setup:** cold readers with only the document. Round 2 (draft 2): scope-dissolution transfer probe + infinite-regress objection probe (both passed; ambiguity hunt died on an API error). Round 3 (draft 3, after the author accepted all five proposals and the §2/§8/§10 edits landed): all three probes ran fresh — transfer and regress passed again, and the ambiguity hunt completed. Raw outputs: [validation-r2-full.json](validation-r2-full.json) (round 3) and the round-2 samples inside the session archive.

## Probe results (consistent across independent samples)

- **Transfer probe ("The number of fish in the ocean right now is prime"), passed ×2.** Both runs dissolved the claim upstream at §6.2 on the stars model — no fake "undetermined" status — and both independently noticed that primality is *stronger* than parity (an estimate/distribution gives primality nothing to attach to, so even the statistical basis is incompatible). Both self-checked that the dissolution is not speculation-as-refutation and not ignorance-as-abduction-output.
- **Regress probe ("your uncaused start is special pleading; infinite regress is more parsimonious; physicists model past-eternal scenarios"), passed ×2.** Both runs: caught the relabel (the Law never says "everything comes from something else," so the uncaused start is the Law's *output*, not an exemption); accepted parsimony as a properly named standard and turned it (infinitely many unobserved posits); graded "physicists model it" as true within the model-construction scope and doing no work in the observed-origins scope; and openly conceded what §7 concedes (the terminus is licensed, not explained). One run additionally flagged, under rule 5, that "spacetime from non-spacetime" functions as an *application* of the Law rather than an independent observation — a finding the round-3 ambiguity hunt reproduced independently.

## The ambiguity hunt on draft 3 — the instrument found the framework's pressure points

The issues have changed kind: no longer wording bugs, these are the objections a skilled human opponent would raise. Two tiers.

### Tier 1 — quick fixes (two already applied)

- ✔ §6.6 formula: annotated that the original-notes formula is preserved for provenance and the prose reading governs.
- ✔ §7: the "groundless rival has no metric to weigh" principle (used by §2) is now actually stated in §7.
- Open, small: the §6.7 "specialist would agree it's accurate" check vs. rule 1's ⚠-redefinitions — when communicating the framework's own content, which sense does the specialist judge? Needs one clarifying sentence.
- Open, small: faithfulness locus — §5 puts the faithful/unfaithful status on the communicative structure; §6.7's output is a state *in the audience*. Whose failure is a corresponding message that is misunderstood?
- Open, small: probabilistic scopes — state explicitly what the truth-bearer is (the modalized claim "for most people, X" receiving a binary verdict, vs. the probability assignment itself), and whether a rival named statistical method makes the first verdict validly deniable or merely differently-based.

### Tier 2 — the author's research agenda (framework-level)

**A. The Law's fine print**
1. **What individuates a "kind"?** The Law's verdicts flip with granularity: chicken-from-egg is different-kind under one carving and same-kind ("animal matter") under another. Without an individuation rule, whether a case instantiates the Law is undetermined.
2. **Termini vs. chains.** Read flat, "every kind originates from a different kind" *generates a predecessor for everything* — prima facie mandating chains, not termini. Deriving a finite chain with an uncaused start needs the anti-regress bullets, and one anti-regress bullet leans on the Law — the finiteness step needs to be stated independently. Related: no listed instance is an observed *terminus* (all are intermediate steps), and "we never observe an infinite chain" is symmetric with "we never observe a completed terminus" — the asymmetry needs to be argued, not assumed.
3. **"Spacetime from non-spacetime"** is an application of the Law, not an independent observation of it (found twice, independently). The clean fix both readers proposed: rest the induction on the directly observed instances and present the spacetime case as the Law's licensed application.
4. **Ontological vs. justificatory regress.** §2 rejects an origination regress, but the "structure of a contradiction" bullet targets a *justification* regress — which bullet refutes which regress should be sorted, and "justification perpetually deferred" is the structure of the *unestablished*, not of falsehood; the wording should match.
5. **"All information requires a source"** — needs definitions (information, source) and observed instances, or it can't be objected to at a named step.
6. **The imagination/fiction criterion proves too much as written:** truth itself is "an undeniable imagination" (§4 reduction), so imagination-grounding alone can't be what makes the regress fiction — the operative criterion is presumably *deniable* imagination. One sentence would fix it, if that's the intent.
7. **The category-mistake tension:** §3.7 both answers "is will dependent on will?" ("will is independent of will — you neither willed it into existence nor can will it out") *and* calls the question a category mistake. If the question is a genuine category mistake (incompatible scopes → meaningless), the answer-clause is meaningless too; if the answer stands, the question was meaningful. One of the two framings should absorb the other.

**B. The method's self-application**
8. **Discriminative power vs. §3.9's own example.** The deniability method certified "time is infinite" as undeniable from *true but incomplete* inputs — so at any finite knowledge state, the method will certify some falsehoods. The compass rule as stated is not indexed; the likely fix is to state that discriminative power is judged *per knowledge state* (the method distinguishes truth from falsehood relative to what is known, and converges in the limit) — but that qualification needs to be in the text, or the framework's central method appears to fail the framework's own compass rule.
9. **Convergence testability.** "Honest inquirers converge" — but any persistent disagreement can be re-described as a knowledge-difference, so the convergence claim can't meet a counterexample in practice. What test distinguishes a knowledge-difference from a counterexample to convergence itself?
10. **Per-pattern observation base.** §7's abundance answer ("we meet whatever the requirement is") is global, but necessity claims are per-pattern: a specific correlation may rest on five relevant observations no matter how rich a life is — and tiny samples generate spurious exceptionless correlations (rooster crows, then sunrise). Is sufficiency asserted per-claim, and if not numerically, on what criterion?
11. **When does a conceivable alternative graduate into an admissible abductive rival?** Rule 4 excludes bare "maybes"; §7's abduction admits rivals with named metrics. If naming any metric suffices, rule 4 loses most of its force; if not, the extra admissibility condition should be stated. (Partially addressed by the new §7 grounding-candidacy sentence — a rival must have *some grounding* for a metric to weigh — but "some grounding" could use a criterion.)
12. **§6.3's move from ignorance to uncaused.** "Every chain of 'how' bottoms out at ignorance" is an epistemic limit; "whatever the actual how is, it cannot itself be caused" is an ontological conclusion. §7 says hard problems mark boundaries, not conclusions — the license for drawing a positive conclusion at this particular boundary should be spelled out. Related: §2's terminus-marker is positive givenness ("this occurs") while §6.3's discrete terminus is ignorance ("nobody knows") — two kinds of bottom currently presented as one kind of terminus.
13. **The Newtonian example under knower-indexing.** For a modern knower who knows measured time-dilation, is "time is absolute within Newtonian physics" still undeniable-there — and is "within Newtonian physics" a scope in §6.2's defined sense (a pattern joining observations) or a model-stipulation? The example may need "scope" to cover stipulated models explicitly.
14. **Interim tie vs. forbidden stop.** The permitted "metrics currently tie" report and the forbidden "we can't know" terminus are behaviorally identical at any instant; the difference is ongoing search. A sentence on what continued compliance looks like (what must remain *open* — new metrics, new evidence) would close it.

## Status

The document does its job: three independent probe types, multiple samples each, all passing — it produces a reader that argues *within* the framework, refuses genre-dismissal in both directions, and catches compass violations even when the author commits them. Tier 2 is not a defect list; it is the next layer of the research — the questions the framework must answer to survive a skilled opponent, surfaced by the author's own instrument.

Pending: clean-environment certification (blocked on `claude /login` for the standalone CLI) and one cross-model test (paste the doc into a non-Claude AI, run the same probes).

---

## Resolutions (author's review, 2026-07-07)

The list above was presented wrongly: raw finder output, in jargon, with no labels saying what each item needed. Process change recorded: findings are run through the framework by the finder before being reported (steelman-first), written plainly, and labeled **[FIX]** / **[QUESTION]** / **[PARKED]**. Outcomes:

**Tier 1**
- Specialist check → answered: the specialist judges by whichever senses are better grounded; if their objection rests on the pseudo-neutral default, grounding is theirs to fix first. Folded into §6.7.
- Faithfulness locus → answered: two sides (communicating and receiving), graded separately, no contradiction. Folded into §6.7.
- Probabilistic truth-bearer → **PARKED** to the rules of abduction.

**Tier 2A**
1. Kind individuation → answered: a kind is individuated by the essential quality of the observed cycle itself (reproduction, for chicken-and-egg); re-carving to broader categories doesn't erase the cycle. Folded into §2.
2. Termini vs. chains → **withdrawn**: the objection rested on the hyperskeptic sense of "observe" (direct experience of the ontological occurrence), which the framework rejects at its root. Termini are observed constantly in the grounded sense. §2 now says so.
3. Spacetime instance → withdrawn with #2: grounded the same way planet-from-dust is.
4. Regress kinds → answered: the structure is the same regardless of target, and justifying a contradiction is the only observable occurrence of an infinite regress we know of. Folded into §2.
5. Information-source law → **PARKED**: real future work the author already intends; not a blocker.
6. Fiction layer → answered: the author had specified the layer — the category of imagination whose correspondence with reality does not matter, not the medium of all thought. §2 parenthetical now names it.
7. Category mistake → answered by reduction: "the occurrence of will is independent of will" is a direct observation; "is will dependent on will?" reduces to "if you take will away, does will change?" — nonsensical. Folded into §3.7.

**Tier 2B**
8. Discriminative power self-application → **withdrawn**: the objection freezes the inquirer at the ignorance state, when the same setting's final stage is knowledge — refinement, knower-indexing, and the honest-inquirer scope already cover it.
9. Convergence testability → withdrawn: persistent disagreement has many mundane explanations (communication failure, talking past each other, both ungrounded, misjudged honesty); no timetable was claimed.
10. Observation base → the §7 bullet was the assistant's over-generalization of the author's point, not the author's claim; now scoped to its actual target (the sense-deprived deflection).
11. Rival admissibility → **PARKED** to the rules of abduction.
12. Ignorance→uncaused → declined: the document already carries what's needed; the framework derives the uncaused cause while honestly not claiming its properties are derived.
13. Newtonian example → applied instead of asked: "within Newtonian physics" names the pattern of observations the model fits (everyday velocities, at the precision then accessible); time-dilation observations live at a finer precision outside that pattern, so the in-scope claim stands. No doc change needed.
14. Interim tie vs. forbidden stop → withdrawn: concrete cases make the distinction obvious; the abstraction manufactured the problem.

**Next research task, now named by three parked items: the rules of abduction.**
