# Section Writing Guide

## Writing goal — the one rule all others reduce to

**Demystification.** Use plain, common language and keep cognitive load low, while
staying precise enough that a specialist would agree it's accurate. Be hard on the
topic, soft on the reader: anticipate where someone might feel defensive, but don't
soften what's actually true. Where something is uncertain, contested, or where an
expert would object, surface that directly in plain terms — don't hide it behind
jargon, hedging, emotional appeals, or common misreadings the reader might bring in.

**Drifts to avoid:** (1) *academic drift* — reaching for Latinate words,
nominalizations, or jargon when a common word works; (2) *bland drift* — hedging or
both-sidesing until no real claim is made; (3) *false accessibility* —
oversimplifying in a way a specialist would object to; (4) *emotional cushioning*
that buries the actual point. If accessibility and precision seem to conflict in a
sentence, flag that sentence rather than silently picking one.

**Self-check before emitting a revision.** A smart non-expert should understand it
on first read. A specialist should read it and not wince. No sentence should hedge
without saying anything. If any of those fail, rewrite before sending.

Every rule below is a specific application of that goal. When no rule fits a case,
ask: *"What would demystification require here?"* — the answer is almost always
right.

---

## Three simultaneous requirements

1. **Low cognitive load.** Every sentence does one job. Never re-read to understand.
2. **Logical precision.** PhD-rigor. No hand-waving, no fake equivalences.
3. **Atomic.** One concept per node. The tree decomposes complexity so the reader
   never hits something that depends on what hasn't been shown.

These reinforce each other. Precise definitions are more readable than vague ones.
Atomic chunks force precision. Low cognitive load forces clarity.

---

## General principles

**The reader is a conscious person.** You are pointing at what they already
experience, helping them recognize and label it — not writing from some impossible
pre-experiential stance.

**Precision without jargon — but preserve the link.** Plain language, no loss of
rigor. Err conversational over academic. When simplifying a standard philosophical
term, keep the proper term in parentheses: *"real, built-in categories in nature
(natural kinds)."*

**Grounding over vocabulary.** Foundational nodes establish *observations*, not word
lists. Only Unlocks is about vocabulary; everywhere else, the question is *what does
the reader recognize from their own experience?*

**No artificial verbosity, no formulaic phrasing.** If one sentence does it, use
one. Don't force patterns like *"The position that..."* before every Eliminates
item, or a fixed bullet count per section.

**`soWhat` can just state what the term enables.** It doesn't have to be
catastrophe-focused. *"Names the phenomenon of connection between occurrences"* is
fine for a labeling node.

**Calibrate depth to the node's role.** Keep definition/labeling nodes lean. Go
deeper on nodes with non-obvious or contested content. Forcing depth on a thin node
is academic drift; underspecifying a substantive node is false accessibility.

**Reader-facing language only.** No *"downstream nodes," "epistemological branch,"
"the rest of the tree builds on this."* The reader reads a sieve, not a development
log.

**Watch words.** *Resolve, constitute, subsume, instantiate, supervene, entail,
posit* — check for simpler alternatives (*ends / count as / include / is a case of /
describe directly / require / claim exists*). Not a ban list; the check is *"would
an average reader get this on first pass?"*

---

## Node function types

Every node does one of three things. The type determines the If-Rejected framing.

- **Occurrence node** — claims a genuinely new phenomenon exists, not describable
  using prior vocabulary. If Rejected: *"Without X, ..."*
- **Label/define node** — names a pattern already describable from prior
  vocabulary. Test: can you say what the node says using terms already established?
  If Rejected: *"Without recognizing X, ..."* — the phenomenon still happens, but
  can't be referenced compactly.
- **Distinction node** — separates two things that could be conflated. If Rejected:
  *"Without distinguishing X, ..."* — both still exist, but the difference is
  invisible.

---

## Observations

Raw material the reader recognizes from their own experience. Things you point at
and the reader goes *"yes, I see that."*

*Belongs:* specific immediate examples, verifiable right now.
*Does NOT belong:* the conclusion, meta-commentary, arguments, vocabulary labeling,
scoping/framing, explanatory gloss.

- **Each observation is the datum, period.** No dash-phrase, no clarifying gloss.
  *WRONG: "A sharp pain — vivid, immediate." RIGHT: "A sharp pain, right now."*
- **Specific examples, not abstract categories.** *"Red"* — not *"a color."*
- **Each observation gets its own bullet** when distinct.
- **Cover the range of KINDS at the node's level.** If a node is about wanting,
  show a bodily want, an aversive want, an intellectual want, a meta-want. Different
  KINDS, not variations of one kind.
- **No self-references before 1.3.7.** No *"I, my, you, your."* Say *"an arm, felt
  without looking"* — not *"your arm's position."* Reason: the self isn't grounded
  until 1.3.7, so agentive pronouns before that smuggle in a subject the tree
  hasn't earned — a specialist notices.
- **Only grounded terms.** Each word is (a) defined in a prior node, (b) the term
  being defined, or (c) common English with no technical weight. Synonym test: if
  any synonym appears in any node's Unlocks, the word is doing philosophical work
  and needs grounding.

---

## Conclusion

Synthesizes observations into a statement.

- **Near-verbatim to the node's claim.** Slight rewording for readability is fine.
  No added synthesis, logic, or framing.
- **Supporting points go in nested sub-bullets** (`text` / `items`): vocabulary
  definitions, why this matters, clarifying scope.
- **Definitions are direct.** *A "quality" is a singular distinct phenomenon* — not
  *"Quality" is the label for...*
- **Scoping statements belong in Unknowns or Objections**, not Conclusion.
- **Multiple concluding statements** are fine when a node establishes more than one
  thing — but each must be near-verbatim to something in the claim.

---

## If Rejected

The specific cost of rejecting the conclusion. Concrete, not vague.

- **Forward-looking costs, not backward-echoing.** *"Without X, there is no X"* is
  just the claim restated — not a consequence. Show what *cannot be built later*.
- **Name at least one specific downstream concept that breaks.** If you can't name
  one, you're about to restate the claim in the negative.
- **Show what becomes indistinguishable from what.** The cost is always a loss of
  distinction.
- **Apply the "so what?" test.** If the reader can shrug, the consequence is too
  weak.
- **State the vivid core; don't enumerate every downstream node that breaks.** Make
  the reader *feel* the loss.
- **Match the framing verb to the function type** (see Node function types).
- **Use expandable format when rejections cascade.** Children must be
  `{title, detail}` objects — plain strings render as empty containers.

---

## Unlocks

What accepting this node makes possible. Two categories:

- **Vocabulary** — all common words the node grounds, not just the headline term.
  Nested bullets: main term first (with synonyms), then *"Also grounded"* for
  connector words. Cross-reference the Phenomenology Diagram's term sets (PH1–RP5)
  for completeness.
- **Next steps** — what questions or observations this node enables.

Unlocks is the one place vocabulary focus IS appropriate.

---

## Eliminates

Positions ruled out by accepting this node. Each item: a specific position someone
might actually hold, stated clearly enough for the reader to evaluate it.

- **No fabricated or straw positions.** *"Nobody actually holds that"* means it
  doesn't belong here.
- **Vary phrasing.** Don't open every item with *"The position that..."*.
- **Test:** does accepting this node force you to reject this position?

---

## Unknowns

**Purpose: scope-guarding against ontological overreach.** Each Unknown should
implicitly address an objection of *"but you're assuming X"* by saying *X is not
addressed here.*

- Remove filler items nobody would mistake for overreach.
- Cite the deferred-to node where known.
- Each Unknown names a specific deferred question — not a generic hand-wave at
  future work.

---

## Objections

Every objection in its strongest form, with four subSections:

- **Objection Basis** — why someone holds this. Address the reader directly:
  *"Maybe wanting is just a label for sensations"* — not *"Reductionist positions
  hold that..."*. The holder should feel accurately represented.
- **Objection Commitments** — the numbered root-cause assumptions. Isolate the
  *load-bearer* — the one that actually makes the objection fail. Others set it up;
  don't enumerate every assumption.
- **What's Missing** — what the objection overlooks. Name which numbered commitment
  breaks and why.
- **Correction** — why the node's claim is validly derived despite the objection.
  Not *"the objection is wrong"* but what resolves the concern while demonstrating
  the claim still holds.

### Objection rules

- **Weave the node's observations into objections** as concrete examples where
  natural. *"Consider: hunger is not just stomach contractions — it includes a pull
  toward food."*
- **Include real positions** (eliminativism, monism, empiricism, etc.). Don't
  fabricate objections nobody holds.
- **Presupposition objections get one core response:** *your awareness of X is what
  theories of X are built from. You don't need the theory to have the awareness.*
  State the principle, apply it, stop.
- **Force the real commitment.** Present the genuine dilemma: either [preserves
  claim] or [specific costly commitment the objector must own]. Name the commitment.
- **No premature commitment in Corrections.** Especially at early levels,
  Corrections must not endorse the node's position as though already proven. Show
  the objection fails *on its own terms. "The question is whether X is part of what
  occurrence IS, or part of how you encounter it"* — not *"The answer is clearly X."*
- **Scope-defense must explain, not just assert.** When an objection imports
  ungrounded vocabulary, explain WHY the vocabulary isn't available and what the
  objection would need to show first. Don't agree or disagree with imported terms.
- **Grounding language, not vocabulary-development language.** *"This grounds the
  experience of X"* — not *"this provides vocabulary for X."*
- **Bullet size discipline.** If a bullet exceeds ~400 chars, split at sentence
  boundaries or restructure with nested `{text, items}`.
- **If Rejected consequences are objectable.** If someone rejects the claim but
  disputes the consequence, that's a genuine objection to address.

---

## Parent synthesis

**Parents encompass their children — they do not come "before" them.** A parent
node is a *summary* read after its children are understood. Parents can (and
should) use terms their children define. Act as if all the children are squished
into the parent. (This does NOT apply to same-page siblings — those follow strict
sibling ordering.)

When all children are written, the parent generalizes:

- **Observations** — broader phenomenon the children's observations are instances
  of. Don't repeat children.
- **Conclusion** — near-verbatim to parent's claim; sub-bullets define terms at
  parent's level.
- **If Rejected** — encompasses all children's consequences at parent level.
- **Unlocks / Eliminates** — union at parent's level of generality.
- **Unknowns** — generalized.
- **Objections** — key synthesis task. Find the higher-level concern that
  encompasses the children's objections. Don't list all children's objections —
  generalize.
