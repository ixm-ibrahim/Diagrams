# Handoff — The Coherence Audit project

A cold-start summary, written so a fresh chat can pick this up with no prior reading. It says why the project exists, what is in the document, and what we have not done yet.

---

## Why this exists (the starting goal)

The aim was one practical thing: **a single document you can paste alongside any request to an AI, so the AI reasons soundly and writes clearly** — and in particular, stops treating weak arguments as if they were strong (the "sounds deep but isn't" problem).

We built it by *deriving* it from one starting idea, instead of just listing rules — so every part traces back to that idea rather than being asserted. The document lives here:

`Sound Reasoning/Coherence Audit - Control Document (v1).md`

---

## The one idea everything is built on

**Truth must be distinguishable from falsehood.** Any move that — used evenly — would prop up a claim and its opposite equally is not reasoning.

This rule defends itself: to argue against it, you have to treat your own argument as true rather than false, which already uses the rule. Everything else in the document is worked out from this one starting point.

---

## What's in the document, section by section (plain terms)

1. **The goal** — the one rule above.

2. **Coherence** — the document's word for "conceptual fit." Falsehood shows up as a *clash between two named things*. Whenever "coherence" is used, it must name the two things that fit or clash — otherwise the word is empty.

3. **The six checks** — the places a claim can come apart:
   1. *word ↔ world* — do the terms point to something real?
   2. *word ↔ word* — do the terms fit each other (scope)?
   3. *claim ↔ foundations* — is it actually supported, traced down to something solid (not made up, not circular)?
   4. *claim ↔ the rest* — does it clash with what's known, and is the standard applied evenly to all sides?
   5. *claim ↔ its own assertion* — does it survive being turned on itself?
   6. *claim ↔ the question* — does it actually answer what was asked? (only when judging an argument)

4. **Common moves to expose** — a catalog of weak moves with a *tell* for spotting each and the check that exposes it (e.g. the bare "couldn't it be…", demanding a higher bar for one side only, treating "no-X" as the free default, begging the question, mismatched comparisons, self-undermining standards, and smuggled background models / conventionalism). It also gives one general question to catch moves not on the list, and a caveat so the list isn't used to dodge genuine objections.

5. **The exposition layer** — how to write so the reader can actually check it: use words people already know, pin down scope, put foundations first, and never sound more sure than the support allows. The test: anyone can point to what each sentence *claims*, what it *rests on*, and *how to check it*.

6. **The claim container** — a fill-in form (Question / Claim / Terms+scope / Support / Distinguisher / Fit / Confidence) that runs all the checks at once. A slot you can't fill is exactly where the claim fails.

7. **Limits, self-test, and turning the checks on the checks** — the document admits it reports best-available warrant, not certainty; it passes its own checks; and it marks the difference between its bedrock (the one rule) and its finer details (a best guess, open to revision).

8. **Worked examples** — a table showing where each kind of false statement breaks.

---

## What we have NOT done yet (open threads)

- **Live test (most natural next step).** We never actually ran the document on a real argument. The best first test is the "will behind every outside cause" case (file: `handoff_external-causes-and-will-case.md`). Paste the control document + that argument into a fresh chat and check two things: (a) which checks fire on the argument, and (b) whether the AI's *own* writing obeys the exposition layer.

- **The deep companion.** The control document is the short, paste-able version. We have not built the longer reference that maps your earlier work — the 86 principles and the DAG (in your Comparative Religion and Phenomenology Diagram folders) — onto each check.

- **One unresolved question.** Is "phenomenological grounding" (your account of what makes a term grounded) a *bedrock* truth or your *best current model*? We flagged it but didn't settle it. It matters because it sets how firmly Check 1 stands. Settling it means deciding whether there's an argument that grounding-in-experience *can't be denied without already using it.*

- **Reliability in practice.** A document can't force an AI to apply the checks every time. The real hit-rate is unknown until it's used; expect it to miss subtle cases and to need a v2 shaped by real friction.

---

## How to use this handoff

Start a new chat, paste this file, and name the thread you want to pick up — most naturally, the live test. Point the chat to the control document at the path above (and the causality case file, if testing). Ask it to keep its own answers plain and checkable, the way the document requires.
