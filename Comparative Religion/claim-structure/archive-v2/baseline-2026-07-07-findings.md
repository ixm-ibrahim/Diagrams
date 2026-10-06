# Baseline cold-read findings — 2026-07-07

**What was run:** four Claude instances with no memory of the authoring conversation each received only [raw-notes-2026-07-07.md](raw-notes-2026-07-07.md), instructed to treat the document as sole authority on its own terms. Reader 1 restated the framework; reader 2 executed all seven pipelines on "Aspirin reduces fever"; reader 3 hunted ambiguities; reader 4 flagged term collisions. Complete raw output: [baseline-2026-07-07-full.json](baseline-2026-07-07-full.json).

**Verdict:** the architecture transmits. The restater correctly reconstructed the three-stage structure (anti-circularity → definition ladder → seven pipelines) including the subtle parts: deniability as an internal event rather than a speech act, scope-layered undeniability in probabilistic domains, reason as discovered rather than decided, will-as-ontological. The applier ran all seven pipelines end-to-end and produced a verdict ("TRUE — within the pharmacological scope and at the level of statistical/probabilistic undeniability"), correctly using the microbial-life move unprompted. The pipelines are executable, not just descriptive.

**But:** the restater logged 14 places it had to guess; the applier improvised at 14 points; the ambiguity hunter filed ~58 issues; the collision reader flagged ~30 terms, 9 rated severe. The failures cluster — they are not scattered noise. Consolidated below.

---

## Consolidated questions for the author

### A. Truth and its three faces (highest stakes)

1. The notes give three formulations of truth: ladder #10 (*intellectual causality within the context of undeniability*), 12.3 (*correspondence of inferential structure with the ontic structure it refers to*), and reduction 1 (*a necessary ontological event that is an undeniable imagination*). One notion expressed three ways, or genuinely different notions? When the truth pipeline outputs "the claim's truth-value," which formulation is it outputting?
2. Undeniability is indexed to "what you know now." Can a claim's truth-value differ between two people with different knowledge, or change as knowledge grows? If not, how does knower-relative undeniability deliver knower-independent correspondence?
3. Is every truth-value scope-indexed — should the truth pipeline output "true/false *within scope S*" rather than bare true/false — and how is S fixed when the claim doesn't state its own scope?
4. In "truth = intellectual causality, within the context of undeniability": the earlier "within the context of X" moves restrict a relation to a *domain of events* (ontological events, thoughts). Undeniability isn't a domain of events — what exactly is being restricted here?
5. Reduction 1 category questions: "necessary" was defined as a relation between correlating phenomena — necessary relative to what correlate? And how is the same item both an ontological (non-willed) event and an imagination, given the rung 8/9 contrast?

### B. Deniability — the engine

6. The definition has two disjuncts: "results in an inconsistency" (a logical relation) and "knowing you're wrong" (a felt state). These can come apart — inconsistency unnoticed, or felt wrongness without inconsistency. Which governs when they diverge?
7. What is the concrete mental operation of "denying" when testing deniability — internally asserting not-P, attempting to coherently imagine not-P, something else?
8. The truth pipeline applies deniability to non-claim outputs (a meaning, a scope). What does denying a meaning or a scope concretely mean — denying "this claim means M" / "this claim lives under scope S"?
9. For a claim whose scope is probabilistic, what does the truth pipeline output — true/false-within-scope, a graded value, or "undetermined"? (The microbial-life walkthrough never states its final verdict.)

### C. Intellectual causality

10. Descriptive or normative: if a fallacious inference feels compelled and exceptionless to a particular thinker, is that transition an instance of intellectual causality? If not, what distinguishes genuine intellectual causality from a psychologically compelled mistake? (Valid, sound, truth, and falsehood all inherit this answer.)
11. Pipeline 5 says "logical/intellectual causality" — is "logical causality" a synonym, a subset, or distinct?
12. Rung 9's bracket "[in which all the above are ontological, even your own will]" — does "all the above" mean the prior ladder rungs, or the causes of intellectual events?

### D. Primitives and termini

13. Which items count as phenomenological primitives — only bare phenomena/distinctions, or everything up to some rung? How do you recognize that a grounding chain has actually bottomed out?
14. A proof is a sequence of claims (12.5), but primitives are non-claims — in a *grounded* proof, is the first step the phenomenon itself, or a claim reporting the phenomenon? If the latter, what grounds the reporting claim?
15. Is "intrinsic cause" (ontology pipeline terminus) the same as rung 8's "uncaused event"? If not, what does "intrinsic" add? And what is the method for locating it for a concrete claim? (The applier improvised: "the point where causal tracing exits the scope.")
16. The law of non-circularity founds the ladder yet note 3 says it is discovered "along the way." Where does it sit in the framework's own vocabulary — a phenomenological given, a correlation, a necessity? Can it be stated with its premises?
17. Rung 8's "we already inferred that ontological events are caused by others" — that inference isn't in the notes. Can it be stated explicitly in terms of rungs 1–7?

### E. Will and the ontological

18. Operational test for "willed": is a deliberately conjured mental image willed (hence non-ontological)? Is an intrusive thought unwilled (hence ontological)?
19. Confirm the reading of "(including will itself)": will counts as ontological because you don't will your willing — it occurs to you. Correct?
20. "including... whatever is not directly observed" — is unobservedness *sufficient* for ontological status, or merely not disqualifying?
21. Is "ontic" (12.2–12.4) exactly synonymous with rung 7's "ontological"?

### F. Pipeline mechanics

22. Truth pipeline notation mixes `&`, `<-`, parentheses, and brackets with no stated precedence. Spell out the evaluation step by step: which deniability check consumes which output, in what order, and how `&` and `<-` combine. (The applier guessed: test every prior output, conjoin with AND.)
23. Are proof (pipeline 4) and inferential (pipeline 5) the same chain viewed two ways — signs as nodes, rules of inference as links — or two separate structures? If the same, why different termini (primitives vs. intellectual causality)?
24. What fills the "..." in the scope pipeline's `(definition scope <- pattern identification <- ...)`?
25. Meaning vs. scope boundary: "what the claim is talking about" vs. "what is the claim about" are near-identical phrasings. For one concrete claim, what differs between the two outputs? Also: is the scope output a *pattern over observations* or a *part of reality* — and which does the truth pipeline consume?
26. Must the pipelines run in listed order, each consuming its predecessors' outputs? Does communication consume the truth output?
27. Ontology pipeline: does "what has to happen in reality to make this claim occur" mean conditions for the claim's being *true* (not conditions for someone making the claim)? What concrete form does "a fit" take — a consistency verdict, a mapping, a degree? What is output when the ontological conditions are unknown or contested?
28. Meaning pipeline: what's the rule for splitting a claim into its definitions? Do general ("animal"), abstract ("justice"), logical ("not", "all"), and empty ("unicorn") terms all count as "referencing something specific"?
29. Confirm notation: `A <- B` reads "A is grounded in / produced from B," and "cycle of (X <- X)" is a finite terminating chain, not a loop.

### G. Statements, proofs, gradings

30. "Statement = an inferential structure" (12.1) and "statement = a set of definitions + their associations" (note 2) — two descriptions of one thing? What makes a set of definitions and associations "inferential"?
31. Which statements *lack* a truth-value and so fail to be claims? Does an incoherent statement come out false, or truth-valueless?
32. Is a proof any ordered sequence of claims (with grounded/valid/sound as separate gradings), or must steps be inference-linked to count as a proof at all? And is 12.5 (sequence of claims) or note 5 (sequence of intellectual causality) the operative characterization — or claims-as-nodes, causality-as-links?
33. Validity: must the conclusion follow by intellectual causality from the immediately preceding step alone, or from all previous steps jointly?
34. Can a proof be sound (every link intellectual-causal) yet ungrounded? Does such a proof confer anything on its conclusion?
35. Reduction 2 vs. rung 11: is "claim" the genus covering true and false statements, or the undeniable success-case? And in reduction 2, which direction does "correlates" run between the ontological and intellectual events — and did you mean necessity rather than "often follows"?
36. Comprehensibility: imaginable *by whom* — author, audience, an idealized imaginer? Does structural/analogical imagining (a 4D cube) count?
37. Rationality: can an irrational statement be true — e.g., a novel claim contradicting all observed precedent that is later verified? Is "irrational" distinct from "deniable"?

### H. Abduction and the scientific method

38. Is an abductive preference an instance of intellectual causality — can a proof containing abductive steps be valid/sound and yield an (un)deniability verdict?
39. How is metric X selected non-arbitrarily — what determines which metric and which "data that matters" govern the preference between rivals A and B?
40. Note 5's hedged glosses: for Deduction, which reading — apply observational precedent to patterns, observe what follows intellectual causality, or both? For Induction — observe the pattern or assume it?

### I. Status questions

41. Note 6 (the "neutral default" critique): background motivation, or operative rules for the pipelines — e.g., "speculation never counts as proof/refutation," "hyperskeptical doubt does not render a claim deniable," "the prior state of ignorance is never the output of abduction"?
42. Note 4's discriminative condition (no clock-pointing-everywhere): should the truth or proof pipeline include a formal check on discriminative power? What are the other "conditions for the truth of a claim"?
43. Where do items 12.1–12.9 slot into the ladder, and what does ladder numbering encode (strict grounding dependency?)? Why do will, temporal qualia, and scope share rung 4?
44. "It basically broke it down into 7 pipelines" — what does "It" refer to, and do you endorse the breakdown as your own?

### J. Text fixes (confirm intended wording)

- "phenomena make up of all things" — composed of phenomena, or accessible only via phenomena?
- "knowledge of exoplanets and planets where we and directly see it" — "where we *can't* directly see it"?
- "not some of certainty" → "not one of certainty"; "best first the data" → "best fits the data"; "the every link" → "every link".
- "(see the above point about illusions vs. reality)" — the illusions passage is *below*, in note 6.
- "as explained earlier" (deniability) — the earlier explanation isn't in these notes; needs restating.

---

## Term-collision register (decision needed per term: keep-with-contrast, or rename)

Severity = how badly a reader silently applying the standard sense corrupts the framework.

| Term | Doc sense (short) | Collides with | Severity |
|---|---|---|---|
| cycle | finite terminating chain | loop that returns to start — i.e. the exact circularity the framework forbids | **High — inverts the central move** |
| valid | final link intellectual-causal | whole-argument form-validity | **Severe — shifted one notch from textbook** |
| sound | every link intellectual-causal | valid + true premises | **Severe — shifted one notch** |
| truth | undeniability given current knowledge, scope-indexed | absolute correspondence, knower-independent | **Severe** |
| necessity | exceptionless observed correlation | modal necessity (all possible worlds) | **Severe — makes framework overclaim** |
| causality | necessity among ontological events | productive/mechanistic relation ("correlation ≠ causation" objections become category errors) | **Severe** |
| intellectual causality | observed event-regularity among thoughts | mental causation / logical entailment | **Severe** |
| ontological | independent of will (incl. will itself) | inventory of mind-independent being | **Severe — most idiosyncratic definition** |
| deniability | denial produces internal inconsistency | plausible deniability / "undeniable = obvious" | **Severe (author already anticipates)** |
| real / reality | everything not willed (illusions ARE real) | mind-independent vs. illusory | **Severe — "illusions are real" reads self-refuting** |
| correlation | asymmetric temporal succession, "often follows" | symmetric statistical co-variation | High |
| law of non-circularity | inductive law about origins (licenses termini) | the informal fallacy rule | High |
| definition | any referring unit (concept, term) | the explanatory sentence-level act | High |
| proof | sequence of claims (can be ungrounded/invalid and still be a proof); also external signs | conclusive derivation | High |
| claim | statement with a truth-value | any contested assertion | High |
| coherence | imaginability (context-free) | logical consistency | High |
| rational/irrational | fits/conflicts with reality's precedent | good/bad reasoning by an agent | High |
| imagination | the whole domain of thought | fancy/fiction ("truth is an undeniable imagination" reads as "truth is made up") | High |
| scope | pattern joining observations; domain a claim lives under | quantifier reach / mere extent | High |
| statement | set of definitions + associations | declarative sentence / proposition | Mod-high |
| phenomenological | the pre-claim given that stops regress | Husserl; diSessa's p-prims | Mod-high |
| will | a quality that occurs (not willed itself) | faculty of volition, free-will debates | Moderate |
| independence | absence of doc-sense correlation | statistical independence | Moderate |
| hard problem | any intrinsic-nature question (generalized) | Chalmers' consciousness problem | Moderate |
| objective | the occurrence of the experience is given | mind-independent fact | Moderate |
| grounded | first step is phenomenological | "well-founded" (near-miss, passes unnoticed) | Moderate |
| truth-value | standing in possible correspondence at all | the value True/False itself | Moderate |
| falsehood | deniability-species of intellectual causality | just "being false" | Moderate |
| induction/deduction | both recast as species of observation | generalization / a priori derivation | Moderate |
| faithfulness | communicative↔inferential/ontic correspondence | loose fidelity | Low (near-miss) |
| sign/support | pointer, separated from inference rules | semiotic sign / generic evidence | Low-mod |
| abduction | metric-driven preference; ignorance never the output | inference to best explanation | Low-mod (bite is in the norms) |
| demystification | audience-tuned word choice | debunking | Low |

---

## Notable improvisations by the applier (gaps the doc must close)

- Read `<-` as "is grounded in" and ran pipelines right-to-left (never stated).
- Stopped each cycle when a term hit a ladder rung (no stated stopping rule).
- Split the claim into lexical terms for the meaning pipeline (no stated decomposition rule).
- Named the intrinsic cause as "where causal tracing exits the scope" (no stated method).
- Treated truth-pipeline `&` as logical AND over all prior outputs (no stated combination rule).
- Declared truth "at the statistical level" with no stated threshold.
- Imported minimal real-world knowledge of aspirin (the framework supplies structure, not content — the doc should say explicitly that pipelines are filled with the analyst's empirical knowledge).
- Assigned bare observables to Proof and all logic to Inferential (boundary not stated).
