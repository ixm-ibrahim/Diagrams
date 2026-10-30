# Rules of inference and abduction — two running lists

**Status note (2026-07-09):** List 2's structure is being re-derived properly in [step2-abduction-chain.md](step2-abduction-chain.md) — that file governs wherever the two conflict. List 1 remains the working inference list for step 3. The terminus-candidate section and scratch below are historical record of how the derivation started.

Working lists, not finished work. Add, cut, reword freely. Each inference rule now carries a **Preference underneath** note: what rival rule exists, and which abduction rule settles the preference. That note is the author's hunch-test being run per rule.

**The hunch to test (author's):** any rule of inference, whatever it is, has a terminus in a rule of abduction — because any reasoning where one way of thinking is preferred over another is abductive reasoning. This may or may not be true; the lists exist to find out.

---

## What makes something a rule of inference vs. a rule of abduction? `[DRAFT — verify]`

- A **rule of inference** *produces*: it takes statements you already have and yields a **new statement**. Input: claims. Output: another claim. The question it answers: "what follows from what I have?"
- A **rule of abduction** *selects*: it takes **rival candidates** already on the table and yields a **preference**. Input: rivals plus a metric. Output: a ranking or a choice. The question it answers: "which of these should I hold?"
- Both are discovered, not decided — patterns in when the click fires.
- The hunch, restated with these definitions: every production rule, when challenged ("why this rule and not that one?"), is defended by a selection rule.

## The deepest abduction rule — candidate terminus `[DRAFT — verify]`

Not a separate tier above the lists (the author corrected this): it is a rule of abduction like the others — the metric for preferring one *method of reasoning* over another, which is why it can also rank the other metrics. Because everything in the hunch-test landed on it, it is the current candidate for the terminus of the abduction chain:

> **Truth and falsehood are distinguishable — and a method of reasoning whose own structure arrives at falsehood cannot distinguish them, and is disqualified as a method.**

Two guards on the wording:

- *"Whose own structure"* — the law targets the method, not the knower. A person with incomplete knowledge can validly reach a wrong conclusion (time-is-infinite); that does not disqualify the method, because the same method run on the fuller inputs corrects itself — that is refinement working. The painted needle never corrects, because it certifies everything at every input state. That is the difference.
- The grounding chain, from the author's own pieces: all false claims necessarily contradict reality *(3.1 node 6)* → so falsehood always comes with a mismatch → so truth and falsehood are distinguishable in principle → so a method whose verdicts come out the same whether or not the mismatch exists is independent of truth, and defective as a method. (Full derivation: step1-terminus.md — settled 2026-07-08.)

The law appears at three places in the framework, wearing three costumes: as the **compass metric** (L2.10 — its enforcement when selecting among rivals), as **discriminative power** (§7 — its enforcement as a condition on truth), and as the **logical-gap thesis** (its structural face: gapless grounded chains are how a method avoids certifying falsehood). One law, three appearances.

**The chain-level form (the author's, 2026-07-08):** *every rule used in an inferential proof — inference and abduction alike — must itself be able to distinguish truth from falsehood: falsehood attempting to pass through any link must be detectable there.* Consequence: a chain's power to detect falsehood is bounded by its least discriminating link — one blind link is enough for falsehood to enter, which is the logical-gap thesis restated (a gap is a link with zero discrimination). This is where the author's old observation — *the structure of a claim says something about its truth* — gets its derivation: the inferential structure can be inspected for discriminating links before any content is weighed, and a structure that fails the inspection cannot establish truth no matter what it carries. Note the convergence: the 3.2 testimony rules already evaluate transmission chains by their weakest link — the chain-level compass was in use before it was derived. (Possible fourth grading of proofs alongside grounded/valid/sound — a proof whose every link discriminates; name pending the author.)

## How much of the world's catalog is here?

- **Deduction** (rules 1–5, 7): the world's list is settled and small. Logic names dozens of rules, but a small core is provably enough to build the rest. The entries below cover the family.
- **Induction / analogy / statistics** (rules 6, 8, 9): no settled complete list exists anywhere in the world — these are catalogued as patterns plus error-warnings. Open-ended by nature.
- **Abduction**: the world has no established rule-set at all — only loose criteria (see "closest cousins" under List 2). The least settled territory, and the one this project aims to ground.

**Why the world never built the catalog** The rules of induction and abduction are claims about how reality behaves, so they can only hold the way observations hold — until a counterexample. When Hume pointed out that induction cannot be justified deductively, philosophy's mainstream concluded "so this territory has no rational foundation" — instead of concluding "so the deductive standard was the wrong test for it." From there, suspending judgment became the respectable position. So the direction of cause matters: the agnostic/hyperskeptic default is not the result of the missing catalog — its standard (only certainty-provable rules count) is the reason the catalog was never assembled. Meanwhile the rules kept appearing wherever people needed real answers: medicine (differential diagnosis), law (standards of proof), historians' source criticism, statistics — and the isnad and tawatur sciences. They exist as scattered practice; they were never unified and grounded, because the discipline positioned to unify them was holding the wrong standard.

---

## List 1 — Rules of inference

### Established in the world

1. **The if-then rule** (modus ponens). If A then B; A occurred; so B. *If it rains, the ground gets wet. It rained. So the ground is wet.*
   **Preference underneath:** the rival rule ("A occurred, but deny B anyway") contradicts what "if A then B" says the moment it's used — the rival is dead on arrival. And a rule that lets true premises yield false conclusions has no discriminative power at all: compass metric (L2.10), in its most extreme form.
2. **The rule-out rule** (modus tollens). If A then B; B did not occur; so not A. *If the stove were on, the pan would be hot. The pan is cold. So the stove is off.*
   **Preference underneath:** the rival ("the test failed, keep A anyway") is the shielded-belief pattern — a claim kept despite failing its own consequence becomes indistinguishable from a false one. Compass (L2.10).
3. **The chain rule.** If A then B; if B then C; so if A then C. *If I oversleep I miss the bus; if I miss the bus I'm late; so if I oversleep I'm late.*
   **Preference underneath:** denying that the links connect contradicts the two premises taken together — rival dead on arrival. Compass (L2.10).
4. **The either-or rule.** A or B; not A; so B. *The keys are in my coat or the car. Not in my coat. So in the car.*
   **Preference underneath:** the rival survives only by quietly changing what "or" means mid-argument — term-drift. Drifting terms let you conclude anything, so the fixed-terms side wins by compass (L2.10). (Note: this preference is partly enforced upstream, by the meaning pipeline's fixed-terms condition.)
5. **The all-to-one rule.** All X are Y; this is an X; so this is Y. *All ice is cold; this is ice; so this is cold.*
   **Preference underneath:** the rival ("...but this one is exempt") is an exemption with no ground — the ad-hoc patch. Principled-extension rule (L2.11) plus compass (L2.10).
6. **Generalization** (induction). Every observed X was Y; so X's are Y, within the observed scope, until a counterexample. *Every released stone fell; so stones fall.*
   **Preference underneath:** here the rivals are *live*, not dead on arrival — "the pattern continues" vs. "the pattern reverses tomorrow" vs. "conclude nothing." Reversal has no grounding — no one has ever observed patterns systematically reversing — so it can't be preferred (L2.7). Concluding nothing is ignorance-as-output (L2.8). Continuation fits all the data with zero extra assumptions: best-fit (L2.1). The clearest case of inference running on abduction.
7. **The contradiction rule** (reductio). Assuming A leads to a contradiction with what is grounded; so not A. *Assume the number of chickens is infinite; then no first chicken; but every kind comes from what it is not — contradiction; so not infinite.*
   **Preference underneath:** the rival ("keep A despite the contradiction") makes the method certify everything — truth and falsehood alike. Compass (L2.10), maximally.
8. **Analogy.** X and Z share a pattern; X has quality Q; so Z plausibly has Q. *Both drugs bind the same receptor; drug one lowers fever; so drug two might.*
   **Preference underneath:** rivals are live and often *win* ("the shared pattern is superficial"). Analogy only counts after a compass check (does the shared pattern actually track Q, or would it "point" regardless?) and a scope check. Analogy is nearly an abduction procedure wearing an inference costume — strong support for the hunch.
9. **Statistical inference.** Most X are Y; this is an X; so probably Y — the verdict lives at the probability scope. *Most July days here are hot; tomorrow is a July day; so probably hot.*
   **Preference underneath:** the rival ("ignore the frequencies" or "expect the rare case") fits the observed data worse by construction: best-fit (L2.1), plus the scope choice from the basis-selection rules (§6.2).

### From the framework and the author's materials

10. **The causation rule.** Correlation without exception is causation, within ontological events. *(§3.8, §6.5.)*
    **Preference underneath:** rival one — "correlation twice is causation" — certifies falsehoods (lucky socks): compass (L2.10). Rival two — "no correlation ever licenses causation" — is the hyperskeptic rule; it denies grounded exceptionless patterns and outputs permanent ignorance (L2.7, L2.8).
11. **The origin rule.** Every kind of thing comes from what it is not — used at the end of chains. *(the Law, §2.)*
    **Preference underneath:** already derived in §2 — the rivals (infinite regress, self-origination) are ungrounded (L2.7), lose on best-fit (L2.1), and the regress has the structure of something that can't distinguish truth from falsehood (L2.10).
12. **The source rule.** All information requires a source. *(§2 — grounding still owed.)*
    **Preference underneath:** not yet worked. Rival: "information can be sourceless." Parked until this rule gets its grounding.
13. **The gapless-chain rule.** Every premise must trace to a grounded starting point through explicit steps, no hidden premises or leaps. *(3.1 node 5.)*
    **Preference underneath:** gaps are exactly where false conclusions sneak through from true premises (the logical-gap thesis) — allowing gaps destroys the method's ability to filter falsehood: compass (L2.10).
14. **The scope-limit rule.** A conclusion cannot speak beyond what its premises cover. *(3.1 node 2; the Newtonian rule is this applied to verdicts.)*
    **Preference underneath:** the rival (export freely) produces wrong answers outside the covered scope — support inside a scope "points at" claims outside it that it cannot distinguish from falsehoods: compass (L2.10).
15. **The reconstruction rule.** Another person's communicated experience counts as observation for you, under conditions: independent sources, enough of them, agreement on fundamentals, no shared origin or agenda, fits the historical context. *(3.2 nodes 2–5.)*
    **Preference underneath:** rival one — accept all testimony — certifies fabrications (L2.10). Rival two — reject all testimony — outputs permanent ignorance (L2.8) and defeats itself, since almost everything anyone knows arrived by reconstruction. The conditions *are* the discriminative filters: each one exists to make the support fit truth better than fabrication (L2.10, L2.1).

## List 2 — Rules of abduction

### Previously discussed (author's materials and this project)

1. **The best-fit metric.** Prefer the explanation that accounts for the most data with the fewest unsupported assumptions. *(3.1 node 8.)*
2. **Name the metric.** A preference is only usable when the metric behind it is stated. *(raw notes, microbial-life example.)*
3. **Same standards for all rivals.** Every competing explanation is judged by the same evidence and logic rules. *(3.1 node 8.)*
4. **Steelman before comparing.** Each rival is put in its strongest form first — safe, because truth never contradicts reality. *(3.1 nodes 6–8.)*
5. **Enumerate the rivals.** Find all plausible alternatives; don't accept a presented either-or. *(3.1 node 8.)*
6. **Known rivals only.** "The absence of known alternate explanations is the goal, not absence of all speculative alternate explanations." A rival counts when it is known and formulated — never by being merely conceivable. *(3.1 node 8, verbatim.)*
7. **Grounded rivals only.** A rival with no grounding at all gives a metric nothing to weigh; it cannot be preferred. *(§7; the infinite-regress rejection.)*
8. **Ignorance is never the output.** "We can't know" is the starting state, not a conclusion. An honest tie report ("no stance preferred yet") is a state of an ongoing search, not an answer. *(§7.)*
9. **Ties are a stated limit.** Equally good fits without a decisive differentiator: the method stops there until new evidence or a new metric arrives. *(3.1 node 8, Limits.)*
10. **The compass metric.** Prefer support that could not equally fit a falsehood; support that fits every rival equally supports none. *(§7 discriminative power — candidate master metric, since it also ranks metrics.)*
11. **The principled-extension rule.** When a claim is updated to answer an objection, the update must extend the claim's own foundations — an arbitrary patch that exists only to dodge the objection is disqualified. *(3.1 node 6, ad-hoc rescue.)*
12. **Speculation is neither proof nor refutation.** A merely-possible alternative cannot establish a claim and cannot refute one. Derived from the compass: if speculating X counted, speculating not-X would count equally — the painted needle. *(§0 rule 4, §7 — spotted missing from this list by the author.)*
13. **The self-application test.** When a claim's scope includes claims, methods, or knowledge in general, the claim is a member of its own scope — run it on itself, and prefer it or its negation by the result. Three possible outputs: *fails itself* ("no one can know anything" — is that known?) → the negation is preferred, structurally, before content is weighed; *passes itself necessarily* ("phenomena occur" — denying it is an occurrence) → self-grounding, which is why primitives can serve as termini; *undecidable within its own scope* (Gödel-shaped cases) → the honest output is a stated limit, and the verdict lives one scope up — the same move as the Newtonian rule. Derived from the compass (a standard that exempts itself is a blind link about itself) plus same-standards (3); exempting a claim from its own scope is an ad-hoc patch (11). Production half already in List 1 as the contradiction rule. *(Placed as a listed rule at the author's correction, 2026-07-08 — derived is not the same as not-a-rule.)*

### Proposed layers for List 2 `[DRAFT — verify]`

The rules above do four different jobs. Categorized:

1. **Admissibility rules** — what may enter the exercise at all: known rivals only (6), grounded rivals only (7), speculation is neither proof nor refutation (12).
2. **Conduct rules** — how the exercise must be run: name the metric (2), same standards for all rivals (3), steelman before comparing (4), enumerate the rivals (5).
3. **Metrics and checks** — what actually ranks the rivals: best-fit (1), the compass (10, candidate master — it also ranks metrics), and the self-application test (13 — runs whenever a rival's scope includes itself; can settle the ranking before content is weighed).
4. **Output rules** — what may be concluded, and how updates work: ignorance is never the output (8), ties are a stated limit (9), principled extension (11).

### Closest cousins in the world (for orientation — the world has no settled rule-set here)

- **"Inference to the best explanation"** — loose criteria: coverage of the evidence, simplicity, coherence with what's known, testability, no ad-hoc patches. Roughly L2.1 + L2.11, without a rule for conflicts between criteria.
- **Bayesian updating** — a formal version: start with how likely each rival was, update by how well each predicts the evidence. Powerful, but the starting likelihoods are the disputed part.
- **"Severe testing"** (philosophy of science) — a claim earns credit only from tests it would likely have *failed* if it were false. This is the compass metric (L2.10) in the world's vocabulary.
- **Differential diagnosis** (medicine) — enumerate the possible causes, order tests that discriminate between them. This is L2.5 + L2.10 as a working procedure.
- **The world's open problem:** what to do when the criteria disagree (simple-but-less-coverage vs. covers-more-but-complex). No established answer — the exact gap this project wants to close with a grounded ordering.

---

## Scratch — noticed while listing, unresolved

- **Early result of the hunch-test:** every "preference underneath" note lands on the same handful of abduction rules — compass (L2.10) dominates, with best-fit (L2.1), grounded-rivals (L2.7), ignorance-never-output (L2.8), and principled-extension (L2.11) doing the rest. Nothing so far needed a preference that List 2 doesn't have.
- **The deduction/induction difference, seen through the hunch:** for the deductive rules (1–5, 7), the rival dies the moment it's stated — the preference is real but instant. For generalization, analogy, statistics, causation, and reconstruction (6, 8–10, 15), the rivals are live and the preference machinery visibly runs. So the hunch survives in both cases, but with two speeds: rivals dead on arrival vs. rivals that must be beaten.
- The falsehood-abundance line ("falsehood is necessarily more abundant for each truth" — 3.1 node 7) might be a rule of abduction, a grounding argument for L2.5, or something else. Parked.
- The source rule (1.12) is the only inference rule with no preference-note yet — its grounding is owed first.
- **The hunch may have found its terminus.** Every preference-note landed on the compass (or a rule derived from it). The compass is the governing law enforced at the selection layer. If that holds, the chain reads: rules of inference ← rules of abduction ← the governing law ← ...? What grounds the governing law itself is then the last question — the master axiom ("all false claims necessarily contradict reality") is the current candidate, and *its* grounding would be the true bottom. To test, not to assert.
- **Self-application ("a claim has to pass itself") — traced and placed (2026-07-08; corrected same day: it IS a listed rule, L2.13 — derived is not the same as not-a-rule).** Not the terminus, not a new pipeline.
- **The author's aside worth pulling later:** "idk what we're doing the comparison to if not this" — every deniability test compares a claim against its negation. If that's right, the truth pipeline's test itself has a selection shape, which would tie the truth pipeline to abduction at the root. Big if true; parked. When a claim's scope covers claims/methods/knowledge in general, the claim is a member of its own scope; the all-to-one rule (L1.5) then instantiates it on itself, the contradiction rule (L1.7) fires if the self-instance conflicts with holding it, and exempting it is an ad-hoc patch (L2.11) plus a double standard. Trigger: reflexive scope, decided in 6.2; execution: the ordinary deniability run. Relation to the terminus: its enforcement procedure for claims about claims — a standard that exempts itself is a blind link about itself. Both directions are one check: "nothing is happening" fails it; "phenomena occur" passes it necessarily (the author's own website node: "holding that position is itself something happening"), which is why primitives can serve as termini. Closes the parked "when must a claim be run on itself"; third face of structure-affects-truth placed.