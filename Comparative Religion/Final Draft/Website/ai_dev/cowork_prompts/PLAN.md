# Audit Plan — 1.1 (all nested descendants) — all sections

## Scope
- Target: `1.1` and all nested descendants with content
- Focus section: all (Observations, Conclusion, If Rejected, Unlocks, Eliminates, Unknowns, Objections — plus Claim, Short Title, So What, Search)
- Total nodes in queue: 6
- All six are within a single page — 1.1 is a sub-page whose children (1.1.1–1.1.5) live on the same page, with no further sub-pages beneath them.
- Prior audit attempt: `ai_dev/outputs/audits/1.1/01_all/RAW_RESPONSE.md` timed out with empty output. Treat as no prior findings.

## Reference
- **Ancestor chain:** `1` (claim: *"Some things are true and some are false — and I want to be able to tell which is which."*). Node 1 is a scaffold only — `ai_dev/nodes/1/1.json` has `sections: []`, so there is no upstream section content to cross-check against. Use its claim and `shortTitle` ("Truth & Falsehood") only.
- **Relevant completed siblings of 1.1:** `1.2` (Epistemological Grounding) — `ai_dev/nodes/1/2/1.2.json` is fleshed out (221 lines). Use it to check that 1.1's Unlocks / soWhat framing hands off cleanly into what 1.2 expects as input, and to check that cross-references from 1.1.* into 1.2.* (e.g., "addressed in 1.2.1 / 1.2.2 / 1.2.5.*") actually land on real claims. `1.3`–`1.7` are scaffolds only (12–14 lines each) and can be ignored for coherence purposes.
- **Relevant grounding (internal) nodes for each queue item:**
  - `1.1.1` — no predecessors; terminal floor node.
  - `1.1.2` — depends on `1.1.1`.
  - `1.1.3` — depends on `1.1.1`, `1.1.2`.
  - `1.1.4` — depends on `1.1.1`, `1.1.3`.
  - `1.1.5` — depends on `1.1.3`, `1.1.4` (and `1.1.1`).
  - `1.1` — parent synthesis of `1.1.1`–`1.1.5`; audit last so revised children are in place before the synthesis is re-checked.
- **Governing reference docs** (re-read before each node, in this priority):
  `WRITING_GUIDE.md` (section-by-section rules + the demystification goal), `CHECKLIST.md` (the gates to run), `RULES_AND_PRINCIPLES.md` (structural conventions), `CLARIFICATIONS.md` (axioms — don't re-open), `FORMAT_SPEC.md` (JSON shape), `PROJECT_REFERENCE.md` for background.
- **Axioms from `CLARIFICATIONS.md` that bind this pass:** "All phenomena are qualities," "Associations are a kind of quality," "Awareness is a quality (the quality of occurrence)," "Term-grounding = claims only" (section content may use English words that get formally defined later). Do not re-litigate these during the audit.

## Queue (audit in this order — deepest first, then ascending by id, with the parent last)

1. **1.1.1** — `ai_dev/nodes/1/1/1/1.1.1.json` — *Phenomena occur.*
   - Skim note: Observations look clean (specific raw tokens: Red, Hot, Pressure, Hungry, …). Four objections are thorough and include real positions (coherentism/BonJour/Rorty, Carnap pseudo-statements, Strawson/Buddhist subject-requirement, eliminativism). Two things to watch:
     (a) **Title-quoting bug** — the fourth objection's `title` starts with `Consciousness is an illusion …"` (closing quote, no opening). Decide whether the style is *"full sentence in quotes"* (then add the opening `\"`) or *unquoted title with a trailing label* (then strip the stray `\"`). Same pattern recurs in 1.1.2 obj #3 and 1.1.5 obj #4.
     (b) **Correction neutrality (S8)** — in objection #1 the Correction asserts the foundation holds ("the structure built on it will collapse. It hasn't."). Check whether this endorses the claim as already proven rather than showing the objection fails on its own terms.

2. **1.1.2** — `ai_dev/nodes/1/1/2/1.1.2.json` — *Distinct phenomena occur.*
   - Skim note: Observations are clean negation pairs ("Red is not hot", "2 is not an arm position"). "is" / "not" / "different" are grounded or pre-definitional-English OK. Two things to watch:
     (a) **Monism Correction** opens with a lowercase `"whether or not distinctions are ultimately real …"` — sentence-case slip; compare the parallel phrasing in 1.1.3 obj #2 Correction which uses capitalized "The question of whether or not …". Normalize.
     (b) **Objection title quoting** — obj #3 has the same unmatched-quote pattern as 1.1.1 obj #4 (`… unreal — reality is one undifferentiated whole." (Monism)`). Resolve consistently with whatever style is chosen for 1.1.1.
     (c) Obj #2 uses James's *"blooming, buzzing confusion"* — is "confusion" OK as explanatory prose? (Axiom: section content may use later-defined English — flag only if it's doing philosophical work in the claim chain; here it's explanatory.)

3. **1.1.3** — `ai_dev/nodes/1/1/3/1.1.3.json` — *Qualities occur.*
   - Skim note: Definition is direct ("A 'quality' is a singular distinct phenomenon") — good. Three objections cover Sellars-myth-of-the-given, subjectivity, and structural realism — all real positions. Watch:
     (a) Obj #2 Correction only says *"deferred, not denied"* — check S9 (does it explain *why* the subjective/objective vocabulary isn't yet available, not just that it isn't?).
     (b) Obj #3 (structural realism) uses the framing *"causally downstream but observationally upstream"* in the Correction — verify this isn't using ungrounded causal language in a way that imports commitments beyond 1.2.5.7.8's willful cause. This is section content, so it's allowed in principle, but check whether the sentence reads like it's *claiming* something causal vs. *describing how the objector's picture relates to observation*.
     (c) `soWhat` frames the cost as loss of "specific character" — forward-looking ✓, but does it name at least one specific downstream concept that breaks (S3)? "Features, patterns, classes" appears in *If Rejected* but not in `soWhat` — consider tightening.

4. **1.1.4** — `ai_dev/nodes/1/1/4/1.1.4.json` — *Associations occur.*
   - Skim note: Observations mix similarity-associations ("Red is like blue", "Two is like three") with co-occurrence-associations ("Redness and sweetness — together in a strawberry"). That spread is intentional — cover the KINDS (S Writing Guide, Observations section). Watch:
     (a) **Reference slip** — in the Hume objection's "What's Missing" and the learning-objection's "Correction", the text says things like *"felt connections between phenomena occur — as established at (1.1.1)"* and *"The observation that felt connections between phenomena occur (1.1.1)"*. But (1.1.1) established occurrence, not felt connection — the felt-connection observation IS this node (1.1.4). The reference either points at the wrong node or is being used as *"just as phenomena occur (1.1.1), so do associations."* Disambiguate or drop the cite.
     (b) **Conclusion definition** — *"a quality that occurs with multiple phenomena"*. Cross-check with the 1.1.3 definition of quality (*a singular distinct phenomenon*). A quality that "occurs with multiple phenomena" is still singular (the association itself is one quality), but audit the wording — specialist might worry this blurs singularity. Axiom: associations ARE qualities, so this is fine, but phrasing should make the singularity unambiguous.
     (c) Obj #3 (*"'like' smuggles in comparison"*) — good steel-manning. Check the Correction cites convention 4 correctly.

5. **1.1.5** — `ai_dev/nodes/1/1/5/1.1.5.json` — *Awareness is the occurrence of a quality or association.*
   - Skim note: Four objections — hard-problem (Nagel/Chalmers), background-vs-focused attention, panpsychism, watcher-model. Serious and substantive. Watch:
     (a) **Observations use a gloss** — every item is `"X occurring"` (Red occurring, Hot occurring, …). The Writing Guide says each observation is the datum, no dash-phrase, no clarifying gloss. Here the "occurring" suffix is arguably part of the datum (the node is about the occurrence *itself* as a quality), but compare with 1.1.1 which uses bare "Red, Hot, …". Decide whether "Red occurring" is a legitimate pointing-at-occurrence observation or a conclusion in disguise.
     (b) Obj #2 Correction uses forward citations to `(1.2.5.2.1)` intensity and `(1.2.5.1.2)` direction. Confirm those IDs land on real claims (the tree has been restructured; stale IDs are a known risk).
     (c) Obj #4 Correction uses "no observational ground at this level" — good S9 style. Check it's applied consistently with the other "not addressed here" moments elsewhere in 1.1.*.
     (d) Title-quoting bug recurs in obj #4 (see 1.1.1 note).

6. **1.1** — `ai_dev/nodes/1/1/1.1.json` — *Phenomenological Grounding: distinct things occur in awareness.* (parent synthesis)
   - Skim note: Five observations generalize the children's material, conclusion is near-verbatim, Unlocks list consolidates the connector vocabulary. Biggest concerns:
     (a) **Objection-synthesis gap.** The parent's three Objections are (1) "this is too basic", (2) "it could all be an illusion / brain-in-a-vat", (3) "the five steps could be collapsed". These are meta-structural objections. The children collectively steelman eliminativism (1.1.1 #4), Sellars / myth-of-the-given (1.1.3 #1), monism (1.1.2 #3), structural realism (1.1.3 #3), Humean associationism (1.1.4 #1), hard-problem / Chalmers (1.1.5 #1), panpsychism (1.1.5 #3), watcher-model (1.1.5 #4). **None of these substantive positions is clearly generalized at the parent level.** WRITING_GUIDE Parent-synthesis rule: *"find the higher-level concern that encompasses the children's objections."* Needs either a synthesis objection like *"your phenomenology is a [framework] — qualities/associations/awareness are artifacts of [theory], not data"*, or an explicit justification for why only meta-objections are promoted.
     (b) **Unlocks coverage.** The parent's "Also grounded" connector list is missing at least *uniform* (grounded at 1.1.2) and *seem* (grounded at 1.1.3). Cross-check the full union against all five children's Unlocks.
     (c) **Claim wording vs. PROJECT_REFERENCE.** `PROJECT_REFERENCE.md` §10 lists the claim as *"distinct things occur in my awareness."* The JSON claim drops "my" — which is correct (self-pronouns are deferred until 1.3.7 per the Observations no-self-reference rule). This is a reference-doc staleness flag, not a node defect — note it in the audit report but don't change the JSON.
     (d) **If-Rejected scope.** A single consequence ("No grounded starting point exists") with no children. Forward-looking ✓ (names downstream concepts that break: information, identity, truth, reality, reasoning). Check whether the cost is vivid enough or just enumerative — WRITING_GUIDE: *"State the vivid core; don't enumerate every downstream node that breaks. Make the reader feel the loss."*
     (e) **Eliminates** list duplicates some bullets that already appear in children's Eliminates (e.g., "Experience is a single undifferentiated occurrence…" is in 1.1.2). Per parent-synthesis rule: *"union at parent's level of generality"* — these should be restated at a more general level, not copy-pasted.

## Structural concerns to resolve before auditing
- **Title-quoting style across objection `title` fields.** The pattern `… text." (Label)` (closing quote with no opening) appears in 1.1.1 obj #4, 1.1.2 obj #3, and 1.1.5 obj #4. Pick one convention (either full-quoted statement with a trailing label outside the quote, or an unquoted sentence with a parenthetical label) and apply it across all three before auditing content — otherwise the auditor will re-flag the same style issue per node.
- **Cross-reference validity.** Several nodes cite forward IDs: `(1.2.5.7)` in 1.1.2 and 1.1.3, `(1.2.1)` in 1.1.3 and 1.1.4, `(1.2.2)` in 1.1.4, `(1.2.5.3)` and `(1.2.6.5)` in 1.1.4, `(1.2.5.2.1)`, `(1.2.5.1.2)`, `(1.3.7)`, `(1.2.1.4)`, `(Node 2)` in 1.1.5. Before auditing, spot-check that these IDs still resolve — the tree was restructured during Phase 1 and stale forward references are a known failure mode.
- **Reference misuse in 1.1.4.** Two citations of `(1.1.1)` are used to prop up claims about associations ("felt connections between phenomena occur — as established at (1.1.1)"). 1.1.1 does not establish felt connection. Resolve as either (i) remove the citation, or (ii) reframe as "just as phenomena occur (1.1.1)", depending on the author's intent. Decide the policy before auditing 1.1.4's Objections.
- **Claim-doc drift.** `PROJECT_REFERENCE.md` §10 shows 1.1's claim with "my", but the node JSON (correctly) drops it. Also the same doc says 1.1 is "next" — but 1.1 now has full sections. Update the reference doc as a follow-up; flag in the audit report, do not change JSON.
- **Parent-level objection synthesis (1.1).** See queue item 6 concern (a). This is the single biggest structural issue — if the parent audit decides synthesis objections are needed, they'll be net-new writing that materially changes 1.1. Whoever runs the audit should be prepared to author new steelmanned objections at the parent level, or to justify in the audit report why the current three meta-objections are the correct encompassing set.

## Notes on context / queue size
- The full audit queue is 6 nodes totaling ~1337 lines of JSON plus ~2414 lines of reference docs. Fits comfortably in one long audit session but would be tight if combined with heavy rewriting — plan on checkpointing after each node (per `2_AUDIT.md`'s per-node flow) and writing partial results to `ai_dev/outputs/audits/1.1/` as you go. No explicit max queue size was requested; flag at the session level if the auditor's context is trending over ~70% during the 1.1 parent synthesis (that node alone may require loading all five children again for coherence checks).
