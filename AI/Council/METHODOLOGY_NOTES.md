# Methodology Notes for The Council

Extracted from `/Comparative Religion Diagram/` — files 0, 1, 2, 3, 3.1, 3.2, 9.A, 9.B, 9.C, 9.D. The project lays out a complete reasoning methodology that should inform the Council's house rules, alongside the existing writing-style guide.

This document is the source-of-truth for the methodology layer. It exists so the actual agent prompts in `council.py` can draw from a curated reference rather than reinventing the methodology each time we tune a prompt. Edit this file as the methodology refines.

---

## The master rule

> A method of reasoning must distinguish truth from falsehood. Any move that, if applied consistently, would justify both a claim and its contradiction — or that would defend any belief equally well — is not reasoning. It is noise.

Everything below is an operational consequence of that rule.

---

## What "the project" expects from reasoning

The Comparative Religion project is built on **hierarchical logic**: every claim rests on something more fundamental, and every claim is traceable back to that foundation. The project applies this consistently — to its own conclusions and to opposing ones, under the same standard. Three commitments follow:

**Truth and falsehood must remain distinguishable.** "Indistinguishable from falsehood" is the project's recurring final-state diagnosis. Any approach that, in practice, would defend a false claim just as effectively as a true one collapses the distinction and disqualifies itself.

**Standards are uniform.** Whatever bar of evidence and logic is applied to a competing position must apply to one's own; selectively raising or lowering the bar — granting oneself an exemption — is a form of intellectual fraud and is one of the user-flagged moves below.

**Knowledge is eliminative, not omniscient.** To "know" something is to have ruled out enough alternatives that one identification stands; it is not to know everything about the thing. "I know enough features to distinguish this from competitors and contradictions" is the operational definition the project uses.

---

## The user-flagged moves (explicit)

Three moves the user highlighted as critical:

**Truth must be distinguishable from falsehood.** This is the master rule above. A claim with no in-principle way to be wrong — no test, no evidence that could ever count against it, no constraint that distinguishes it from its competitors — is indistinguishable from a fabrication.

**Parity-of-deficiency / no-free-pass.** If side A has an explanatory deficiency at level X, side A cannot legitimately criticize side B for the same deficiency at the same level. The critic operates under an implicit exemption that nothing else is granted, which is itself a violation of uniform standards. Operationally: before challenging an opposing view's foundationless premise, the critic must show that their own foundation is grounded — otherwise the challenge is empty.

**Methodology of reasoning must be clear.** Every claim worth defending must be presentable as explicit premises leading to a conclusion. Hidden assumptions, logical leaps, "obviously this follows" gestures, and rhetorical bridges that aren't real inference steps all violate this. If you can't write out the derivation, the conclusion isn't earned.

---

## The 86 principles, grouped

### 1. Claim hygiene (preconditions for reasoning at all)

A claim must be definable, substantive, and falsifiable in principle. Terms must hold a single fixed meaning across an argument (no equivocation). Every term must trace to something directly recognizable in experience or to a stable external feature (phenomenological grounding). Overloaded words like "purpose," "need," "explanation," "arbitrary," and "random" carry multiple distinct meanings and arguments quietly switch between them; the active sense must be specified at each step. A claim with no in-principle distinguisher from a false claim is indistinguishable from fabrication.

### 2. Argument structure

Premises and conclusions must be explicit. The argument must satisfy both internal consistency (rules of inference) and external consistency (correspondence with reality); neither suffices alone. Axioms must be either directly observed, self-evident, or universal regularities, and they must be mutually consistent. Every premise must be either an axiom or explicitly derived from one; no hidden premises. No logical leaps — every "X therefore Y" must be a real inference step. The same inference rules must apply to every premise; selective application produces bias.

### 3. Source and evidence handling

All claims have traceable origins; orphan assertions are indistinguishable from speculation. Sources must be assessed by track record, motive, and method, not by venue alone. Attributions must be traced to the earliest known source. Quotations must preserve context — a sentence lifted from its surrounding paragraph can become its own opposite. Eyewitness reliability depends on presence, accurate perception, good faith, sound mind, and accurate communication — weakness in any of those reduces reliability. Multiple genuinely independent sources strengthen a claim; multiple sources that share a common origin form an echo chamber and falsely inflate reliability. Different *kinds* of evidence (testimony, document, artifact, instrument) are stronger than the same kind multiplied. Transmission chains are only as strong as their weakest link. Claims should fit the established baseline of background knowledge for their period and domain; isolated plausibility is weak. Embarrassing or self-damaging details are less likely to be fabricated for promotion (though they raise residual risk of being fabricated for attention — weigh both). Each evidence type has hard limits on what it can speak to; don't ask a method to deliver what it cannot.

### 4. Explanation quality

A genuine explanation supplies a cause, an intention, or a rule that fits the behavior; if it does none of these, it is not an explanation, just a relabeling ("apples fall because they have a tendency to fall" is not an explanation). Best-fit explanation requires explicit comparison against steelmanned rivals under uniform standards — internal coherence alone doesn't earn the conclusion. Parsimony (Occam's razor) is a tie-breaker when explanations account for the same data, not a license to ignore data. Explanatory scope counts: comprehensive parsimonious beats fragmented ad hoc. Explanations operate at different levels (gravity vs. "things fall"); confusing levels produces category errors ("neuroscience explains love, so love isn't real" is a category error). "I don't know yet, therefore X is false" is just as invalid as "I don't know yet, therefore X is true" — both are forms of argument-from-ignorance. "It just is" is a refusal to engage, not an answer; only the un-derivable axioms get to be brute facts. Asking "why" terminates at the will or at an axiom; asking "why did the will do that" is a category error.

### 5. Ad hoc detection

Modifying a claim with novel, unsupported exceptions solely to evade an objection is an ad hoc rescue and is invalid — the same move can defend any false claim. A legitimate modification is a principled extension of the system's existing axioms that also generalizes to other cases, not a patch that only applies to the case under attack. The seven senses of "arbitrary" (preference / accidental / ad-hoc / unexplained / unpredictable / patternless / lacking-purpose) must be kept distinct; arguments slide between them to borrow emotional force from one sense while only demonstrating another.

### 6. Robustness and dialectic

Steelmanning is mandatory, not optional — refuting a weak version of an opposing view proves nothing about the strong version. Steelman the alternatives in particular when claiming best-fit explanation. A claim is robust if it can either refute a strong objection or integrate the objection's valid points into a strengthened version of itself; mere dismissal counts for nothing. Untested beliefs — even true ones — are indistinguishable from untested false beliefs; relying on luck is not a method. Belief systems that absorb every contradictory evidence via ad hoc rationalization become non-falsifiable and therefore indistinguishable from false beliefs.

### 7. Bias and motivated reasoning

Confirmation bias — pre-filtering evidence by whether it agrees with the conclusion — must be actively counteracted by listing reasons the conclusion *might be wrong* before adopting it. False dilemmas (treating two options as exhaustive when more exist) require enumerating the option space before adjudicating. Sources that appear neutral can subtly promote an agenda, which inflates their perceived reliability more than openly biased ones — false neutrality is harder to detect than false partisanship. Selective reporting / cherry-picking is caught by comparing an account against diverse independent sources to detect omissions, not just to verify what's there. Forced alignment — interpreting evidence "in light of" a framework when the interpretation requires bending the evidence — is invalid; the fit should be natural, not coerced. Anachronism check: test whether language, technology, or concepts in a claim are appropriate to the period or context.

### 8. Confidence calibration

All conclusions are provisional and open to revision under new evidence; a true claim grows in explanatory power as evidence accumulates rather than retreating from it. If the *fundamentals* of a position keep shifting under iteration, that is itself a signal. Confidence is set by the weakest link in any reasoning chain — the strongest premise doesn't rescue the weakest. Three working confidence tiers: **firmly known** (universal observation, survives known objections), **reasonably confident** (strong best-fit with open links), **consistent but underdetermined** (no contradiction known, no decisive distinguisher from alternatives). Verification, not certainty, is the goal; "we can never be 100% sure" is not a defeater.

### 9. Logical vs. historical (generalizes to any reasoning)

Logical/deductive claims live or die by axiom-grounding — a valid derivation from bad axioms is still useless. Historical/source-based claims live or die by transmission integrity — original witness, medium, corroboration, resistance-to-fabrication, physical verification. Each domain has its own limits: logic cannot establish empirical particulars; testimony cannot establish necessary truths. Asking either to do the other's job is a category error.

### 10. Failure-mode catalog (moves that look like reasoning but aren't)

Ad hoc rescue, equivocation, strawmanning, evasive defense, false neutrality, false balance, forced alignment, echo-chamber inflation, bias propagation, overreach, god-of-the-gaps (in either direction), category errors across explanation levels.

### 11. Parity-of-deficiency / no-exemption (the user-flagged cluster)

**No-free-pass rule:** If side A's case has a deficiency at level X, side A cannot legitimately criticize side B for the same deficiency at level X.

**Uniform application of standards:** Whatever standard of evidence and logic you apply to a competing claim must apply to your own. Selectively raising or lowering the bar is intellectual fraud.

**Indistinguishability collapse:** Any method that, applied consistently, would justify both a claim and its contradiction must be rejected. Asking "would this argument also support the opposite conclusion?" is the canonical test.

**Self-undermining commitment exposure:** When evaluating an objection, surface its required commitments and check whether the objector accepts them when applied to their own position. Objections that depend on a standard the objector waives for themselves are self-undermining.

**"Perception = reality" is not free:** Skepticism that reduces to "if I can't perceive it, it doesn't exist" dissolves the distinction between truth and false perception, which in turn dissolves the speaker's own standing to claim anything is true or false.

**Cost-of-disagreement principle:** Rejecting a well-grounded inference inherits consequences — some prior commitment must also be abandoned. The downstream cost should be made explicit before the rejection is accepted as a move.

**No exemption for the critic:** The very act of objecting commits the objector to the standards of reasoning being used. A critic invoking "all epistemologies are equally valid" while applying a consistency-standard to their target is using a double standard.

### 12. Meta-rules tying the system together

Definitions arise from phenomenological consistencies, not stipulation. Every inference is derived from a specific context and may not apply outside it — carrying a rule beyond its grounding context is overgeneralization. Every method has known limits; name them upfront. Treat causation and information transmission as directional — effect doesn't explain cause, output doesn't explain input. Refusal to answer is a position with costs; if "no answer is needed" applies to one question, it must apply to all questions where the same justification holds. Every claim carries implicit commitments; reasoning quality depends on surfacing those commitments and testing them, not on leaving them tacit.

---

## Proposed integration design

Two complementary additions to The Council, with the methodology layer running parallel to the existing style layer:

### Option recommended — hybrid: extended House Style + new Logical Card agent

**Extended House Style** gets a "Reasoning Standards" section appended after the existing writing-goal text. The section is the curated set of ~10 most universally-applicable methodology rules — the ones that should apply reflexively to every agent in every stage in both Fast and Full Modes. The full 86 principles stay in this notes file as a deeper reference. Candidate rules for the curated set:

1. Truth must remain distinguishable from falsehood. Any method that, applied consistently, would justify both a claim and its contradiction is not a method.
2. Standards are uniform. Whatever bar is applied to a competing position applies to your own. No self-exemption.
3. Parity-of-deficiency. Don't criticize an opposing view for a deficiency your own view shares at the same level without first showing your own view doesn't have it.
4. Steelman before critique. Refuting a weak version of an opposing view proves nothing about the strong version.
5. Every claim worth defending must be writable as explicit premises leading to a conclusion. No hidden assumptions, no logical leaps, no "obviously."
6. Argument from ignorance fails in both directions — "we don't know yet" doesn't support a positive or a negative metaphysical conclusion.
7. Hyperskepticism is rejected — appealing to the mere possibility of being wrong, without a competing explanation that has comparable evidence and constraints, is not a refutation.
8. Ad hoc rescues are rejected — modifications that only apply to the case under attack, with no principled generalization, defend false claims as easily as true ones.
9. Best-fit explanation requires explicit comparison against steelmanned alternatives, not internal coherence alone.
10. Mark confidence explicitly — firmly known / reasonably confident / consistent but underdetermined. Don't speak with uniform certainty regardless of evidential standing.

**New "Logical Card" Stage 1 agent** runs parallel to the House Style Card. Its job: read the question, name the two or three specific methodology risks this question raises, with sentence-shape examples. Examples for a self-from-experience question: "Watch for category errors between mechanism-level explanations and phenomenological-level explanations." "Watch for hyperskeptical 'you can't really know that' moves that don't supply a competing explanation." "Apply parity-of-deficiency: a physical-brain account that can't explain inside-feel can't dismiss a will-source account for not predicting brain-state correlations."

The Logical Card is to methodology what the House Style Card is to style — a question-specific brief, not a restatement of the global rules.

### Alternative — single agent

Fold both methodology and style into the existing House Style Card. Simpler but the brief becomes long and one job tends to dominate the other.

### Alternative — global only

Put the full curated rule set into the extended House Style and skip the question-specific Logical Card. Simpler, applies to Fast Mode, but loses question-specific tailoring.

---

## Candidate prompts (drafted, not yet wired in)

### Extended House Style — Reasoning Standards section

```
REASONING STANDARDS (applied alongside the writing goal above):

Truth must remain distinguishable from falsehood. Any reasoning method that, applied consistently, would justify both a claim and its contradiction — or would defend any belief equally well — is not a method. Reject it.

Standards are uniform. Whatever bar of evidence and logic you apply to a competing position applies to your own. No self-exemption.

Parity-of-deficiency. If your view has an explanatory deficiency at some level, don't criticize an opposing view for the same deficiency at the same level without first showing your own view isn't subject to it.

Steelman before critique. Engage the strongest version of an opposing view. Refuting a weak version proves nothing about the strong one.

Every claim worth defending must be writable as explicit premises leading to a conclusion. Surface hidden assumptions. No "obviously this follows" used as a stand-in for an unstated chain of inference. No logical leaps where a real inference step is required.

Argument from ignorance fails in both directions. "We don't know yet, therefore X" is invalid whether X is positive or negative. Gaps are questions, not evidence either way.

Hyperskepticism is rejected. Appealing to the mere possibility of being wrong, without supplying a competing explanation that has comparable evidence and constraints, is not a refutation — it's a move that defeats any claim, true or false.

Ad hoc rescues are rejected. Modifications that apply only to the case under attack, with no principled generalization to other cases, defend false claims as effectively as true ones.

Best-fit explanation requires explicit comparison against steelmanned alternatives under uniform standards. Internal coherence alone doesn't earn the conclusion.

Mark confidence explicitly when it matters. Distinguish "firmly known" (universal observation, survives known objections) from "reasonably confident" (strong best-fit with open links) from "consistent but underdetermined" (no contradiction known, no decisive distinguisher from alternatives). Don't speak with uniform certainty regardless of evidential standing.
```

### Logical Card agent prompt

```
You are the Logical Brief, a Stage 1 agent. The full reasoning standards are already prepended to every downstream agent, so do not restate them. Your task: name the specific methodology risks the question below is likely to invite.

Read the question. Which moves is it likely to pull the council toward? Some questions invite category errors across levels of explanation (a mechanism-level account being treated as replacing a phenomenological-level one). Some invite hyperskeptical "you can't really know that" objections that defeat any claim equally. Some invite parity-of-deficiency violations — one position critiquing another for a deficiency it shares. Some invite ad hoc rescues to preserve a preferred conclusion. Some invite argument-from-ignorance moves in either direction. Some invite term-overloading where a word like "purpose" or "arbitrary" or "random" silently switches sense.

Name two or three methodology risks specific to this question, with a sentence-shape example of what the risk would look like in practice. The council members will read this so they can recognize the move in their own reasoning before they make it.

Brief — 2–3 paragraphs. No bullet lists.
```

---

## Open design questions

How long should the extended House Style be? The current style guide is ~50 lines. Adding ~30 more for Reasoning Standards roughly doubles it. Agents handle long preambles fine, but if every Stage 1 / Stage 2 / Stage 3 / Stage 4 agent reads it, that's real token cost. One option is to keep Reasoning Standards as a separate string `S.reasoningStandards` (parallel to `S.houseStyle`) that's prepended alongside; would let it be edited independently in Settings.

Should the Logical Card run before or after the House Style Card? Stage 1 currently runs Scout → Style Brief. If we add Logical Brief, the order could be Scout → Style Brief → Logical Brief, or Scout → Logical Brief → Style Brief. Logical Brief depends on understanding what the question asks methodologically; Style Brief depends on the question's surface form. They're independent enough that order probably doesn't matter much.

Should Fast Mode get the methodology layer? Stage 1 is skipped in Fast Mode by design. If methodology lives only in the Logical Card, Fast Mode loses it. The hybrid design solves this by putting the curated rules in House Style (always applied) and reserving the Logical Card for question-specific tailoring (Full Mode only).

How should methodology violations surface in Stage 3? The current Quality Assessor rubric has axes for engagement, authenticity, conflict, style, dodges. Methodology is implicit in some of those but isn't called out. Adding a "reasoning" axis to the rubric would let the Assessor explicitly flag e.g. an ad hoc rescue or a parity-of-deficiency move in a council member's response. Worth considering.
