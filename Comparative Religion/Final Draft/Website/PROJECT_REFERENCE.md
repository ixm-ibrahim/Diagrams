# Sieve of Truth — Project Reference

## 1. What This Project Is

An interactive website that presents the **Sieve of Truth** — a hierarchical,
eliminative filter that starts from everyday observations and progressively
narrows to the conclusion that Islam is the only worldview that remains
distinguishable from falsehood at every level.

The website displays a tree of connected claims. Each claim can be expanded to
reveal its internal reasoning (observations, conclusions, objections, etc.),
and many claims have a "Derivation" button that opens a sub-page showing the
child claims that build up to it. The hierarchy goes as deep as it needs to.

There are **8 top-level nodes** (the sieve layers). Each node's output is
the next node's input — the conclusion of one layer sets up the question
of the next:

| Node | Name | What It Establishes |
|------|------|-------------------|
| 1 | Pursuit of Truth | That truth and falsehood exist, and pursuing the distinction requires honest motivation |
| 2 | Discovering Reality | That reality presents stable, inferable patterns despite our limitations |
| 3 | Building Confidence | Anti-fabrication and anti-circularity standards for logical and historical claims |
| 4 | Defining God | God's necessary properties, deduced from reality; what a "true religion" must look like |
| 5 | Alignment with Reality | Tests fundamental worldview categories against the inferred definition of God |
| 6 | Historical Comparison | Compares the scriptures of surviving worldviews on preservation, transmission, and fabrication resistance |
| 7 | Non-Fundamental Comparison | Compares the theological principles of surviving scriptures to verify the conclusion |
| 8 | Results & Conclusion | Synthesizes the sieve + cost of disagreement |

**Why this order:**

1. **Pursuit of Truth** — Before examining anything, the motivation to
   honestly distinguish truth from falsehood must be established. Without it,
   every subsequent step is vulnerable to rationalization. Output: a commitment
   to follow reasoning wherever it leads.

2. **Discovering Reality** — With honest motivation established, we observe
   and identify the patterns of reality using reasoning. Output: a working
   understanding of how reality behaves and how we come to know it.

3. **Building Confidence** — Knowing how reality works isn't enough — we
   need standards for evaluating claims about it, especially claims that
   resist direct observation (logical and historical). Output: anti-fabrication
   and anti-circularity filters that distinguish reliable claims from
   unreliable ones.

4. **Defining God** — Applying those standards to what reality reveals about
   its source, we deduce what God must be like if God exists. Output: a
   definition of God grounded in reality, and criteria for what a true
   religion must look like.

5. **Alignment with Reality** — Every world religion falls under a
   fundamental category (atheism, polytheism, trinitarianism, monotheism).
   Each category is tested against the inferred definition of God. Output:
   which categories survive, and which are eliminated.

6. **Historical Comparison** — The surviving categories have scriptures that
   claim divine authority. Each scripture is tested on preservation,
   transmission chains, and resistance to fabrication using the standards
   from Node 3. Output: which scriptures withstand historical scrutiny.

7. **Non-Fundamental Comparison** — The surviving scriptures present
   theological principles (soteriology, divine nature, accountability). These
   are compared against each other and against reality to verify the
   conclusion. Output: which faith's principles most consistently correspond
   with reality.

8. **Results & Conclusion** — Synthesizes the full sieve: what survived
   every filter, what was eliminated at each stage, and the cost of
   disagreeing at each point.

The old project (text files, attached separately) contains the original content.
The new project restructures and deepens it into the website's hierarchical format.

---

## 2. The Data Format

Each node in `data.json` follows this structure:

```json
{
  "id": "1.2.3",
  "parentId": "1.2",
  "nextIds": ["1.2.4"],
  "prevIds": ["1.2.2"],
  "hasDerivation": true,
  "claim": "The one-line conclusion at this level",
  "soWhat": "Why this matters / what it enables",
  "search": "keywords for search indexing",
  "sections": [
    { "type": "row", "title": "Observations", "numbered": true, "items": [...] },
    { "type": "row", "title": "Conclusion", "numbered": true, "items": [...] },
    { "type": "row", "title": "If Rejected", "numbered": false, "items": [...] },
    { "type": "tab", "title": "Unlocks", "numbered": false, "items": [...] },
    { "type": "tab", "title": "Eliminates", "numbered": false, "items": [...] },
    { "type": "tab", "title": "Unknowns", "numbered": false, "items": [...] },
    { "type": "tab", "title": "Objections", "numbered": true, "items": [...] }
  ]
}
```

**Section types:**
- `row` sections (Observations, Conclusion, If Rejected) — always visible,
  stacked vertically
- `tab` sections (Unlocks, Eliminates, Unknowns, Objections) — shown as
  switchable tabs

**Items** can be plain strings or objects with `title`, `detail`, and optional
`children` (for nested "If Rejected" entries) or `subSections` (for Objections
with `label` + `items` arrays).

**Objection format:**
```json
{
  "title": "The objection stated in its strongest form",
  "subSections": [
    { "label": "Objection Basis", "items": ["Why someone would hold this..."] },
    { "label": "What's Missing", "items": ["What the objection overlooks..."] },
    { "label": "Correction", "items": ["The resolution..."] }
  ]
}
```

**`hasDerivation`**: `true` means this node has child nodes on a sub-page.
`false` means it's a terminal node (all reasoning is contained in its own
sections).

**Navigation**: `nextIds`/`prevIds` connect siblings at the same level.
`parentId` points up.

**Inline markdown**: The website renders `**bold**`, `*italic*`,
`` `code` ``, and `"quoted text"` (auto-italicized) in all text fields.

---

## 3. Development Methodology

### Phase 1: Structuring (Top-Down)
For each node, identify its child claims. Recurse until we reach terminal
nodes (claims supportable by direct observation or a single inference).
Validate: no hidden assumptions, no circular dependencies, final child
synonymous with parent.

### Phase 2: Fleshing Out (Bottom-Up, DFS)
Starting from the deepest terminal node, fully write all sections. Move to
next sibling. When all siblings are done, ascend to parent (parent becomes
synthesis/summary of children). Continue DFS.

### Continuous: Iterative Refinement
Claims are provisional until the full tree beneath them is done. Fleshing
out may reveal structural issues upstream. Cross-branch dependencies may
surface. Language converges toward precision + accessibility over time.
Parent claims refine as children solidify — a parent's claim is only truly
locked once its deepest descendants are done.

---

## 4. Conventions and Rules

The tree is built by the same reasoning process it defines (1.5.9): observe
→ identify → induce → deduce → verify. The conventions below are organized
to reflect this: formatting makes the structure visible, structural rules
enforce the dependency order that valid reasoning requires, and content rules
ensure each node is verifiable by the reader.

### Formatting Conventions

1. **Quotation marks** are for personal statements ONLY — e.g., Node 1's
   claim: `"Some things are true and some are false — and I want to be able
   to tell which is which."` and Node 1.7: `"I want to know what is actually
   true — not what I want to be true."` Do NOT put every claim in quotes.

2. **Title prefixes** are only used where they add qualifying context.
   Example: `Phenomenological Grounding: "distinct things occur in my
   awareness."` — the label "Phenomenological Grounding" qualifies what
   follows. But a claim like `Reasoning verifies whether a statement is true
   or not` does NOT need a prefix because the claim already makes the topic
   clear.

3. **Page structure** uses indentation to show hierarchy:
   - 4-space indent = children within the same page (displayed together)
   - Deeper dot notation (e.g., 1.2.5.1.x under 1.2.5.1) = a new sub-page
     (separate derivation page in the website)

### Structural Rules (Observation → Identification → Induction)

These ensure that the tree's dependency order mirrors the reasoning pipeline:
observations ground identifications, which ground inductions, which ground
deductions.

4. **Observation before abstraction.** When a node identifies a general
   pattern or rule, the specific observation that grounds it must appear
   first (either in a prior node or as a prior sibling). The general pattern
   is identified *from* the observation, not the other way around.

5. **States before processes.** When a state (an observable condition) and a
   process (an act that operates on that state) appear to depend on each
   other, define the state first. The state is identified through
   observation; the process operates on the state and requires it.

6. **No circular dependencies.** Every concept used in a node's definition
   must be grounded in a prior node or direct observation. If A uses B, then
   B must not use A. When potential circularity is detected, resolve using
   rules 4 and 5.

7. **No hidden assumptions.** Every dependency is either a prior node or a
   direct observation.

8. **Lowest depth has no gaps in reasoning.** Terminal nodes must be
   self-evident from direct experience.

9. **Ontological simultaneity, epistemological ordering.** Everything in the
   tree exists simultaneously in experience — every definition is itself a
   phenomenon, a piece of information, an awareness, etc. But the
   *identification* of what each thing is happens in a specific order, where
   each term is picked out using only terms that have been picked out before
   it. The tree models the order of identification, not the order of
   existence. This is why the structure is not circular even though every
   node is ontologically an instance of earlier nodes: each node performs a
   different epistemic act — noticing something new *using* what was already
   noticed.

    **9b. Parent squishing rule.** Parent nodes of sub-pages can use terms
    that are defined by their children. Act as if all the children are
    squished into the parent node. This is because the parent header is a
    *summary* read after its children are understood. (This does NOT apply to
    children within the same page — those follow strict sibling ordering.)

### Structural Rules (Deduction → Verification)

These ensure that the tree's conclusions follow validly and can be checked.

10. **Dependencies must be obvious.** When a node uses a concept from another
    node, it should be traceable. Every term in a claim should be either
    (a) a previously defined term, (b) a term being defined right now, or
    (c) a common English word that needs no definition.

11. **Vocabulary-building approach.** Each section builds a vocabulary of
    defined terms. Later nodes use ONLY previously defined terms or terms from
    earlier/ancestor nodes. Do not redefine a term that already exists
    elsewhere in the tree — reference it. Synonyms are allowed, as long as
    they don't carry any ungrounded meanings into the definition.

12. **Name concepts that will be reused.** When applying existing definitions
    to name something recognizable that downstream nodes will reference, it
    earns its own node. A term that names a reusable concept IS adding
    something to the vocabulary, not redundancy.

13. **Final child in every chain should be synonymous with the parent's
    claim.** Reading the children's claims in order should feel like a natural
    progression that arrives at the parent. However, do NOT create redundant
    echo nodes just to satisfy this — if the last substantive child naturally
    arrives at the parent's meaning, that is sufficient.

14. **No nodes forced into existence.** Each node should represent a genuine
    atomic step. Don't create nodes just for structural completeness — but at
    the same time, don't skip steps.

### Content Rules (Verification by the Reader)

These ensure that each node is verifiable, accessible, and honestly presented.

15. **Accessibility + precision.** Content readable by middle schoolers yet
    precise enough for philosophy PhD academics. Plain language, but no loss
    of rigor.

16. **Steelmanning.** Every objection presented in its strongest form before
    being addressed.

17. **Cost of disagreement.** Every rejection in "If Rejected" shows what
    specifically becomes indistinguishable from what — not vague "things go
    wrong."

18. **Readability over formal minimality.** When a node is technically
    redundant (its content is derivable from definitions alone) but aids
    natural recognition for the everyday reader, it can stay. The redundancy
    costs nothing and helps the reader.

---

## 5. Derivation Principles

These are reusable reasoning patterns that govern how nodes are derived,
ordered, and understood. They were discovered through iterative work and
should be applied automatically when creating or reviewing nodes.

### 5.1 Ordering Principles

**Break circularity by finding the more primitive concept.** When two
concepts appear mutually dependent, one is always more primitive —
identifiable from direct experience without the other. Find it and define
it first. Example: knowledge and truth seem interdependent, but knowledge
(when an answer occurs) is identifiable without truth. Truth (correct
knowledge) comes after.

**Prefer weaker claims grounded in observation over stronger metaphysical
claims.** When a weaker claim is sufficient for the tree's downstream needs
and follows directly from observation, use it instead of a stronger claim
that requires unverifiable inference. Example: "not all objects are currently
observed" rather than "objects exist when unobserved."

**Scope terms must be grounded before universal claims.** A universal claim
("all X are Y") requires "all" to be defined. If "all" includes things
beyond knowledge, that scope must be explicitly grounded. Example: "all"
(1.2.7) is defined as including instances in both knowledge and ignorance
*before* "reality is all objects" (1.3.5).

**Types are children, not siblings.** When concept B is a *type of* concept
A (distinguished by some property), B is a child of A, not a sibling.
Example: assumption and judgment are types of belief (distinguished by
evidential basis), so they are children of belief — not siblings alongside
it.

**Group children into sub-pages when a main page gets too flat.** When a
page accumulates many children (roughly 8+), look for natural groupings —
children that build toward a common sub-conclusion. The sub-page's header
should encompass what its children establish, and the final child should
arrive at the parent's meaning.

**Ground rules in observed cases before inducing.** When establishing a
general rule or meta-constraint, first identify the specific observable
cases that exhibit the pattern. Then induce the rule from those cases. Do
not state the rule directly and justify it after the fact — that inverts
the observe → identify → induce pipeline. Example: "a method that justifies
falsehood can't distinguish truth" was first grounded in observed cases
(hope about something false, assumption about something false) before the
general principle was induced.

**Dependency ordering governs sibling order.** Within a page, siblings that
depend on earlier siblings must come after them. This applies to types of
phenomena, definitions that reference each other, etc. Example: mental
phenomena come after temporal because imagination depends on memory.

**Observe the specific before naming the general.** When two specific cases
of a general pattern exist, observe both specific cases first, then abstract
the general term from them — not the other way around. Example: "necessary"
and "sufficient" are observed first, then "condition" is abstracted as the
general pattern encompassing both.

### 5.2 Grounding Principles

**Avoid capacity/possibility language before those concepts are defined.**
Words like "can," "able," "capable," "possible," and the suffix "-able"
(e.g., "visualizable") all smuggle in possibility, which may not yet be
defined at the point of use. Replace with observational language that
describes what *happens*, not what *could* happen. Example: instead of "a
concept can be visualized," say "imagining a concept results in a
visualization." **Exception:** After "possible" is defined (1.4.4.1), "can"
is grounded and usable. Parent nodes of sub-pages that define "possible" may
use "can" via the squishing rule (convention 9b).

**Ground logical concepts in experiential acts.** Abstract logical concepts
(contradiction, compatibility, implication) should be traceable to something
the reader *does* in their own experience. Example: contradiction is grounded
in the act of imagining definitions together and failing to produce a
visualization — not in an abstract formal rule.

**Two levels of visualization.** When testing a concept, there are two
distinct experiential acts: (1) imagining the *definitions together* (tests
compatibility/contradiction), and (2) imagining *the object itself* (tests
comprehensibility/incomprehensibility). These are independent. Example:
infinity — the definitions are compatible (you can imagine "add one" + "never
stop" working together), but the object is incomprehensible (you can't
picture the completed result).

**Definition is epistemologically prior to contradiction.** You must know
what things *are* (their definitions/identities) before you can discover
that their features clash. The act of identifying a contradiction requires
combining definitions and noticing mismatch — which requires definitions to
exist first.

**Avoid causal/agentive language before causation is fully grounded.**
Words like "make," "determine," "produce," and "generate" smuggle in
causation beyond the willful cause defined in 1.2.5.7.8. "Cause" in the
tree is currently limited to want-direction correlation. Non-willful
causation is deferred to Node 2. When describing relationships, use
established terms: "correlates with," "independent from," "results in,"
"matches/mismatches." Example: "wanting doesn't *make* it true" was
rephrased to "truth is independent from wanting" — using independence
(1.2.5.7.4) instead of ungrounded causation.

**Nest effects under their structural causes.** When a phenomenon exists
*because of* a structural fact, the phenomenon should be a child of that
structural fact. Example: truth and falsehood exist because descriptions are
independent from what they describe. So truth and falsehood are children of
the independence observation.

**Distinguish observing an occurrence from knowing its mechanism.** A
phenomenon can be observed (it happens) without knowing the mechanism behind
it (how it happens). The occurrence earns a node; the mechanism is deferred
until its prerequisites are built. Example: inference is observed as a new
statement resulting from others — without needing to explain the internal
mechanism of how recognition of premises leads to the conclusion appearing.

### 5.3 Language Principles

**Prefer neutral terms over assertive ones when willful connotations are
ungrounded.** If a term carries connotations of agency, assertion, or
intention, and those concepts haven't been defined yet, use a neutral
alternative. Example: "statement" (neutral description about reality) instead
of "claim" (implies someone asserting it).

**When a definition doesn't match immediate recognition, rework it.** If a
reader reads a definition and doesn't recognize the concept they already
know, the definition is wrong or incomplete — even if it's formally correct.
The definition should make the reader think "yes, that's exactly what I
already understand by that word."

**Use "results in" for outcomes, not "produces" or "generates."** When
describing what happens when you perform an experiential act (like imagining),
"results in" maps directly to "outcome" (1.2.5.1.5) without implying
causation or production mechanisms that aren't yet defined.

**"When" is a definitional marker, not a temporal or conditional term.**
Throughout the tree, "when" is used to introduce definitions: "Truth is when
a description matches what it describes," "Knowledge is when an answer
occurs." It functions as plain English for "the case in which" and does not
depend on temporal or conditional vocabulary.

**Never sidestep a definition for convenience.** When a term carries a
genuine distinction beyond existing vocabulary, define it precisely rather
than rephrasing to avoid it. Sidestepping trades precision for convenience
and violates convention 15 (accessibility + precision). If a term is needed
and its prerequisites are met, define it. If its prerequisites are not met,
note the deferral — don't rephrase the claim to hide the gap. Example:
"method" (class of processes) carries a real distinction from "process"
(a specific sequence) — it was defined rather than rephrased away.

### 5.4 Audit Principles

**Run dependency audits regularly.** After any restructuring, check every
term in every affected node. For each term ask: is it (a) previously defined,
(b) being defined right now, or (c) a common English word needing no
definition? Flag anything that fails.

**Parent headers must encompass their children and contain no new
information.** The parent claim should describe what the page establishes.
Every piece of information in the parent header should be present in at least
one child node. If the parent header says something that no child says,
either a child is missing or the header is too broad.

**Check for synonym collisions.** When a term appears that already exists in
the vocabulary with a different meaning, it must be renamed. The
vocabulary-building approach requires one term = one meaning. Example:
"consistency" (temporal sameness) vs. logical compatibility — the latter was
renamed to "compatibility."

**Check that terms used match their definitions, not common connotations.**
When a term is used in a node claim, substitute its formal definition and
verify the claim still reads correctly. If the formal definition doesn't fit
but the common English connotation does, the usage is ungrounded.

**Check if a proposed node says anything new.** Before including any node,
verify it is not merely an instance of an already-established principle
applied to already-defined terms. If the claim follows trivially from
substituting definitions, it doesn't earn a node (convention 14) unless it
both aids recognition (convention 18) AND represents a genuinely new
application that downstream nodes depend on. Example: "truth is independent
from wanting" follows directly from "phenomena occur independently from
want" (1.3.1) applied to truth (a phenomenon) — it was absorbed rather than
given its own node.

**Check where a definition structurally belongs.** When a new definition is
needed, trace its dependencies and place it where it fits structurally, not
where it is first needed. A logical structure belongs in the logical
vocabulary section (1.4), not in the node that first uses it. A process
term belongs with the process vocabulary (1.5). Example: "justification"
(a valid argument whose conclusion is a belief) is a logical structure — it
belongs in 1.4.5 (Argumentation), not in 1.6 where it is first used.

---

## 6. Specific Clarifications

These are particular questions that were resolved during development. Each
one instantiates a general principle from Section 5 — the principle is noted
so that similar questions in the future can be resolved the same way.
Deferrals are tentative and open for discussion as the tree develops.

### Resolved

- **Purpose = direction (1.2.5.1.2).** "What is wanted." No separate node
  needed. *Principle: don't create nodes that name something already captured
  by an existing definition (convention 14).* Cause is grounded first in the
  will-body relationship; generalization to non-willful causation is a
  separate concept with unbuilt prerequisites.

- **Sensation = intensity without wanting.** Intensity is a cross-cutting
  attribute (dim/strong) of all phenomena. Sensation is the experience of
  intensity. Not a type of phenomenon — it's the qualitative feel of any
  phenomenon's intensity. *Principle: types are children, not siblings (5.1).
  Sensation is not a sibling type alongside willful/temporal/etc. — it cuts
  across all of them.*

- **Correlation is strict.** A single observed break means no direct
  correlation. Will is a *factor*, not the determining cause. *Principle:
  prefer weaker claims grounded in observation (5.1).*

- **Knowledge is defined without truth.** Knowledge = when an answer occurs.
  It can be right or wrong. *Principle: break circularity by finding the more
  primitive concept (5.1). Knowledge is identifiable from experience without
  truth; truth requires knowledge to already be defined.*

- **Will is a specific type of want.** Will (1.2.5.1.8) = a wanted want.
  Desire (1.2.5.1.7) = an unwanted want. "I"
  (1.3.7.1) is identified through will (deliberate, endorsed wanting), not
  through desire (involuntary craving). *Principle: types are children, not
  siblings (5.1). Will and desire are types of want, distinguished by
  whether the want is itself wanted.*

- **"I want to know what is true" (Node 1.7) is compatible with "a method
  that justifies falsehood can't distinguish truth" (Node 1.6).** The former
  is a want to submit to reality's verdict; the latter warns against methods
  whose results are independent from truth. Wanting to know the truth is
  wanting knowledge (1.2.6.3), indifferent to which answer — not wanting a
  specific description to match reality. *Principle: check that terms used
  match their definitions, not common connotations (5.4).*

- **Truth corresponds with rationality, not comprehensibility.** All four
  combinations of rational/irrational × comprehensible/incomprehensible
  exist. This distinction is critical downstream (mysteries vs.
  contradictions in Node 4). *Principle: two levels of visualization (5.2) —
  testing definitions together vs. testing the object itself are independent
  acts.*

- **"Condition" grounds "if."** The word "if" introduces a condition.
  Therefore "if" cannot be used in node claims before "condition" is defined
  (1.4.4.6). *Principle: avoid capacity/possibility language before those
  concepts are defined (5.2) — extended to all logical connectives.*

- **Necessary is experientially prior to sufficient.** The experience of
  "removing breaks it" (necessity) is recognized before "having guarantees
  it" (sufficiency). Both are observed before "condition" is abstracted as
  the general term. *Principle: observe the specific before naming the
  general (5.1).*

- **Possible/impossible are epistemic, not metaphysical.** A statement is
  "possible" when it doesn't contradict what is currently known. It can
  become "impossible" after new learning. *Principle: prefer weaker claims
  grounded in observation (5.1).*

- **The 1.4/1.5 boundary.** 1.4 = structural vocabulary (what logical things
  ARE — states and structures). 1.5 = process (what you DO with them — acts
  and methods). The key test: if the concept names a static relationship or
  component, it's 1.4. If it names an act, a method, or a quality standard
  for the process, it's 1.5. *Principle: states before processes (convention
  5).*

- **"Argument" carries willful connotations but is correctly non-willful.**
  The formal definition (a set of premises and their conclusion) is purely
  structural — a structure in the 1.3.3 sense, since premises and conclusions
  are connected by implication, which traces back through sufficiency →
  contradiction → visualization failure, all independent from want. The
  willful act of constructing or recognizing arguments is correctly captured
  by 1.5's process terms (inference, deduction, reasoning). *Principle:
  check that terms used match their definitions, not common connotations
  (5.4). Also: states before processes (convention 5) — the structure exists
  independently; the willful act operates on it.*

- **Three-layer distinction: implication / inference / mechanism.**
  Implication (1.4.4.7) is the static structural relationship between
  statements. Inference (1.5.1) is the observable event of arriving at a new
  statement. Mechanism is how inference happens internally. Each layer is
  observable without the one above it. *Principle: distinguish observing an
  occurrence from knowing its mechanism (5.2).*

- **Logical "why" vs. causal "why."** The logical "why" asks for the
  premises that imply a statement's truth — this is justification, fully
  groundable in 1.4 vocabulary. The causal "why" asks what produced an
  event — this requires non-willful causation, projection, and the
  model/representation chain. *Principle: states before processes (convention
  5), and distinguish occurrence from mechanism (5.2). The logical "why"
  points at static structure; the causal "why" points at mechanism.*

- **Old 1.6 ("Wanting something to be true doesn't make it true") absorbed
  into new 1.6.** The claim "truth is independent from wanting" follows
  trivially from 1.3.1 (phenomena occur independently from want) applied to
  truth (a phenomenon). It said nothing new and used "make" (ungrounded
  causation). The substantive content — hope ≠ evidence, assumption about
  falsehood, the wanting-to-know vs. wanting-a-specific-answer distinction
  — was redistributed: the first two became observed cases in 1.6
  (grounding the meta-constraint on reasoning), and the third moved to 1.7
  (the commitment). *Principles: check if a proposed node says anything new
  (5.4); avoid causal/agentive language (5.2).*

- **Justification belongs in 1.4.5, not 1.6.** A justification is a valid
  argument whose conclusion is a belief — a logical structure, not a
  process. The 1.4/1.5 boundary test: it names a static structure
  (a specific type of argument), not an act or method. *Principle: check
  where a definition structurally belongs (5.4); states before processes
  (convention 5).*

- **Method belongs in 1.5, between process and reasoning.** A method is a
  class of processes — it depends on class (1.2.1.9) and process (1.5.8).
  "Reasoning" is more precisely a method (a class of processes sharing the
  observe→identify→induce→deduce→verify pattern) than a single process.
  Each instance of reasoning is a specific process; reasoning itself is the
  method. *Principle: never sidestep a definition for convenience (5.3);
  check where a definition structurally belongs (5.4).*

### Open / Tentative Deferrals

These concepts have identified prerequisites that aren't yet built. They
may belong where noted below, or may find a better home as the tree
develops.

- **Non-willful causation.** Extending "cause" beyond willful wanting to
  natural correlations. Likely requires projection, analogy, or model.
  Possibly Node 2.

- **Reason, why, explanation.** Deferred until both the logical sense
  (justification) and the causal sense (mechanism) can be grounded together.
  Likely requires non-willful causation. Possibly Node 2.

- **Model, understanding, accuracy.** Model = an internal representation of
  reality. Understanding = having a model that matches reality. Accuracy =
  when a model matches reality. All require representation/analogy. Possibly
  Node 2.

- **Representation / Analogy.** One structure standing for another based on
  shared pattern. Depends on structure (1.3.3), match (1.2.3), and possibly
  abstraction (1.4.1.1). Possibly Node 2.

- **Projection.** Extending a concept from one domain (direct experience) to
  another (observed patterns in reality) based on structural similarity. The
  bridge between subjective experience and objective knowledge. Depends on
  analogy/representation. Possibly Node 2.

- **Scope, resolution, context, meaning.** Scope = the portion of reality a
  statement covers. Resolution = the smallest detail distinguished within a
  scope. Context = what is contained between a scope and its resolution.
  Meaning = when a statement operates within its context. The full chain
  depends on model/representation. Possibly Node 2 or 3.

- **Certainty / Uncertainty.** Degree of confidence. Not needed for Node 1.
  Possibly Node 2 or 3.

- **Compulsion / Volition.** Compulsion = willing something when you don't
  want to will it. Volition = willing something when you want to will it.
  Both require three layers of wanting and probably "I" (1.3.7.1). Possibly
  children of 1.3.7 or later.

- **Verification confirming unobserved existence.** If you derive a
  conclusion about something unobserved, then observe it matching, and
  reality is independent from your observations (1.3.4.6) — then the match
  confirms the unobserved thing's nature was already there. Synthesizes
  1.3 + 1.5. Possibly Node 2.

- **Logical system.** A model of statements. Meta-logical concept. Possibly
  Node 3.

---

## 7. Current State of Node 1

Node 1's claim: **"Some things are true and some are false — and I want to
be able to tell which is which."**

Node 1 has 7 children:

| # | Claim |
|---|-------|
| 1.1 | Phenomenological Grounding: "distinct things occur in my awareness." |
| 1.2 | Epistemological Grounding: information about phenomena can be identified, compared, and known. |
| 1.3 | Ontological Grounding: reality is what exists independently of want — including myself. |
| 1.4 | Logical Grounding: statements can be true or false, and new statements can be derived from existing ones. |
| 1.5 | Reasoning verifies whether a statement is true or not. |
| 1.6 | A method of reasoning that justifies falsehood can't distinguish it from truth. |
| 1.7 | "I want to know what is actually true — not what I want to be true." |

### Full Tree (Phase 1 structuring)

Indentation convention:
- No indent = top-level node (its own page)
- 4-space indent = child within that page (displayed together)
- Deeper dot notation (e.g., 1.2.5.1.x under 1.2.5.1) = a new sub-page

---

#### 1.1

```
1.1. Phenomenological Grounding: "distinct things occur in my awareness."
    1.1.1. Phenomena occur.
    1.1.2. Distinct phenomena occur.
    1.1.3. Qualities occur.
    1.1.4. Associations occur.
    1.1.5. Awareness is the occurrence of a quality or association.
```

#### 1.2 main page

```
1.2. Epistemological Grounding: information about phenomena can be identified, compared, and known.
    1.2.1. Phenomena are identified by features and patterns.
    1.2.2. A comparison is observing sameness or variation between information.
        1.2.3. A match is sameness between compared information.
        1.2.4. A mismatch is variation between compared information.
    1.2.5. Phenomena are associated in distinct "types".
    1.2.6. Questions result in knowledge or ignorance.
    1.2.7. "All" of a class includes its instances in both knowledge and ignorance.
```

#### 1.2.1 sub-page — Features and Patterns

```
1.2.1. Phenomena are identified by features and patterns.
    1.2.1.1. Information is a quality or association.
        1.2.1.2. Information belongs with a phenomenon.
    1.2.1.3. A feature is a distinct piece of information.
        1.2.1.4. An identity is a set of features belonging to only one phenomenon.
        1.2.1.5. Identification is the awareness of a phenomenon's identity.
    1.2.1.6. A pattern is a similar quality that a set of features have.
        1.2.1.7. Sameness is the similarity of a pattern across its features.
        1.2.1.8. Variation is the difference of a pattern across its features.
    1.2.1.9. A class is a similar quality that a set of patterns have.
```

#### 1.2.5 sub-page — Types of Phenomena

```
1.2.5. Phenomena are associated in distinct "types".
    1.2.5.1. Willful phenomena occur.
    1.2.5.2. Intensities occur.
    1.2.5.3. Temporal phenomena occur.
    1.2.5.4. Physical phenomena occur.
    1.2.5.5. Emotional phenomena occur.
    1.2.5.6. Mental phenomena occur.
    1.2.5.7. Relational phenomena occur.
```

#### 1.2.5.1 sub-page — Willful Phenomena

```
1.2.5.1. Willful phenomena occur.
    1.2.5.1.1. Wantings occur.
        1.2.5.1.2. Direction is the wanted information.
        1.2.5.1.3. Success is the occurrence of what is wanted.
        1.2.5.1.4. Failure is the non-occurrence of what is wanted.
        1.2.5.1.5. An outcome is a success or failure.
    1.2.5.1.6. Wanted wants occur.
        1.2.5.1.7. A desire is an unwanted want.
        1.2.5.1.8. A will is a wanted want.
```

#### 1.2.5.2 sub-page — Intensities

```
1.2.5.2. Intensities occur.
    1.2.5.2.1. Phenomena occur with intensity.
    1.2.5.2.2. Sensation is intensity without wanting.
    1.2.5.2.3. Perception is the occurrence of a sensation.
    1.2.5.2.4. Satisfaction is when a wanted sensation occurs.
    1.2.5.2.5. Frustration is when a wanted sensation does not occur.
```

#### 1.2.5.3 sub-page — Temporal Phenomena

```
1.2.5.3. Temporal phenomena occur.
    1.2.5.3.1. Phenomena occur presently.
        1.2.5.3.2. Past phenomena are those that occur before the present.
        1.2.5.3.3. A memory is a present phenomenon about a past phenomenon.
        1.2.5.3.4. Recognition is when a phenomenon is like a memory.
        1.2.5.3.5. A phenomenon is new when it occurs without recognition.
    1.2.5.3.6. Phenomena occur sequentially.
        1.2.5.3.7. A step is a phenomenon in a sequence.
        1.2.5.3.8. Change is the difference of a quality in a sequence.
        1.2.5.3.9. An event is the transition from "not-occurring" to "occurring".
```

#### 1.2.5.6 sub-page — Mental Phenomena

```
1.2.5.6. Mental phenomena occur.
    1.2.5.6.1. Imagination is information from different memories.
        1.2.5.6.2. A visualization is the sensation of an imagination.
        1.2.5.6.3. A thought is a set of imaginations and their associations.
    1.2.5.6.4. A possibility is a thought that matches recognized patterns.
        1.2.5.6.5. The future is a possibility of what occurs after the present.
```

#### 1.2.5.7 sub-page — Relational Phenomena

```
1.2.5.7. Relational phenomena occur.
    1.2.5.7.1. A correlation is when one event often follows another.
        1.2.5.7.2. An expectation is a possibility based on a correlation.
        1.2.5.7.3. A hope is a possibility based on a want.
    1.2.5.7.4. Independence is when the variations in one set of features do not correlate with the variations in another.
    1.2.5.7.5. Consistency is sameness across a sequence.
        1.2.5.7.6. A fundamental feature is one that is consistent.
        1.2.5.7.7. A superficial feature is variation within a fundamental feature.
    1.2.5.7.8. A cause is a want whose direction correlates with an event.
        1.2.5.7.9. An effect is an event that correlates with a cause's direction.
```

#### 1.2.6 sub-page — Questions and Knowledge

```
1.2.6. Questions result in knowledge or ignorance.
    1.2.6.1. A question is a want for specific information.
    1.2.6.2. An answer is the occurrence of a question's wanted information.
    1.2.6.3. Knowledge is when an answer occurs.
        1.2.6.4. Ignorance is when an answer does not occur.
    1.2.6.5. Learning is the change from ignorance to knowledge.
        1.2.6.6. Forgetting is the change from knowledge to ignorance.
```

#### 1.3 main page

```
1.3. Ontological Grounding: reality is what exists independently of want — including myself.
    1.3.1. Phenomena occur independently from want — a limit.
        1.3.2. Nature is the set of features for a limit.
        1.3.3. A structure is a set of limits.
    1.3.4. Ontological Bridge: objects exist independently of observation and want.
    1.3.5. Reality is all objects.
    1.3.6. A relationship is an association between objects.
    1.3.7. "I am an object in reality."
```

#### 1.3.1 sub-page — Limits

```
1.3.1. Phenomena occur independently from want — a limit.
    1.3.1.1. Outcomes do not correlate with want.
    1.3.1.2. Wants do not correlate with sensations.
    1.3.1.3. What is thought about is independent from what occurs.
    1.3.1.4. A limit is what is independent from want.
```

#### 1.3.4 sub-page — Objects

```
1.3.4. Ontological Bridge: objects exist independently of observation and want.
    1.3.4.1. An object is a structure with nature.
    1.3.4.2. Existence is the occurrence of an object.
    1.3.4.3. An observation is the perception of an object.
    1.3.4.4. New objects appear in observation.
        1.3.4.5. An object's nature is consistent across observations.
        1.3.4.6. An object's nature is independent from its observation.
    1.3.4.7. Not all objects are currently observed.
```

#### 1.3.7 sub-page — Self

```
1.3.7. "I am an object in reality."
    1.3.7.1. "I" is the object that will is.
    1.3.7.2. "My body is the object that my will affects."
    1.3.7.3. "Not all of my body's events are caused by my will."
    1.3.7.4. "My body limits my will."
    1.3.7.5. "I am not my body."
```

#### 1.4 main page

```
1.4. Logical Grounding: statements can be true or false, and new statements can be derived from existing ones.
    1.4.1. Statements about reality are true or false, and are held as beliefs.
    1.4.2. Concepts have rationality and comprehensibility, and are either compatible or contradictory.
    1.4.3. Rationality and comprehensibility are independent, and truth corresponds with rationality.
    1.4.4. A statement's truth depends on others.
    1.4.5. Valid arguments derive new statements, including about what is not observed.
```

#### 1.4.1 sub-page — Statements and Beliefs

```
1.4.1. Statements about reality are true or false, and are held as beliefs.
    1.4.1.1. An abstraction is information about a pattern or class.
    1.4.1.2. Descriptions are either true or false.
    1.4.1.3. A statement is a description about reality.
    1.4.1.4. Evidence is an observation that matches or mismatches what a statement describes.
    1.4.1.5. A belief is a statement thought to be true.
        1.4.1.6. An assumption is a belief without evidence.
        1.4.1.7. A judgment is a belief with evidence.
```

#### 1.4.1.2 sub-page — Descriptions and Truth

```
1.4.1.2. Descriptions are either true or false.
    1.4.1.2.1. A description is information about an object.
    1.4.1.2.2. A definition is a description of an identity.
    1.4.1.2.3. Descriptions match or mismatch what they describe.
    1.4.1.2.4. A description is independent from what it describes.
        1.4.1.2.5. Truth is when a description matches reality.
        1.4.1.2.6. Falsehood is when a description mismatches reality.
```

#### 1.4.2 sub-page — Concepts and Contradiction

```
1.4.2. Concepts have rationality and comprehensibility, and are either compatible or contradictory.
    1.4.2.1. A concept is a set of definitions.
        1.4.2.2. Compatibility is when imagining a concept's definitions results in a visualization.
        1.4.2.3. A contradiction is when imagining a concept's definitions does not result in a visualization.
    1.4.2.4. A concept is rational when its definitions are compatible.
    1.4.2.5. A concept is comprehensible when imagining its object results in a visualization.
```

#### 1.4.3 sub-page — Rationality and Truth

```
1.4.3. Rationality and comprehensibility are independent, and truth corresponds with rationality.
    1.4.3.1. A concept is either rational or irrational.
    1.4.3.2. A concept is either comprehensible or incomprehensible.
    1.4.3.3. A concept's rationality is independent from its comprehensibility.
        1.4.3.4. Some concepts are rational and comprehensible.
        1.4.3.5. Some concepts are irrational yet comprehensible.
        1.4.3.6. Some concepts are rational yet incomprehensible.
        1.4.3.7. Some concepts are irrational and incomprehensible.
    1.4.3.8. Truth corresponds with rationality, not comprehensibility.
```

#### 1.4.4 sub-page — Dependency and Implication

```
1.4.4. A statement's truth depends on others.
    1.4.4.1. A possible statement is one that does not contradict what is known.
    1.4.4.2. An impossible statement is one that contradicts what is known.
    1.4.4.3. A dependency is when one statement's truth or falsehood contradicts another's.
        1.4.4.4. A statement is necessary for another when its falsehood contradicts the other's truth.
        1.4.4.5. A statement is sufficient for another when its truth contradicts the other's falsehood.
    1.4.4.6. A condition is a statement that is necessary or sufficient for another.
    1.4.4.7. An implication is the relationship between a sufficient statement and what it is sufficient for.
```

#### 1.4.5 sub-page — Argumentation

```
1.4.5. Valid arguments derive new statements, including about what is not observed.
    1.4.5.1. A premise is a statement from which an implication follows.
    1.4.5.2. A conclusion is a statement that an implication leads to.
    1.4.5.3. An argument is a set of premises and their conclusion.
        1.4.5.4. An argument is valid when its premises are sufficient for its conclusion.
    1.4.5.5. A derivation is the conclusion of a valid argument.
    1.4.5.6. A justification is a valid argument whose conclusion is a belief.
    1.4.5.7. Unobserved derivations occur from valid arguments.
```

#### 1.5

```
1.5. Reasoning verifies whether a statement is true or not.
    1.5.1. An inference is a new statement that results from other statements or observations.
        1.5.2. Induction is an inference from a pattern in observations to an abstraction.
        1.5.3. Deduction is an inference from premises through valid implication.
    1.5.4. A deduction is sound when its premises are true.
    1.5.5. Verification is comparing a derivation against observation.
        1.5.6. A prediction is a derivation about what is not yet observed.
    1.5.7. A proof is a sequence of sound deductions from premises to a conclusion.
    1.5.8. A process is a sequence where each step depends on the one before it.
    1.5.9. A method is a class of processes.
    1.5.10. Reasoning is the method of observation → identification → induction → deduction → verification.
```

#### 1.6

```
1.6. A method of reasoning that justifies falsehood can't distinguish it from truth.
    1.6.1. A hope about something false can occur.
    1.6.2. An assumption about something false can occur.
    1.6.3. The outcome of reasoning can be false.
    1.6.4. A method of reasoning that justifies falsehood is independent from truth.
    1.6.5. Truth and falsehood lack distinction in a method of reasoning that is independent from truth.
```

#### 1.7 (children TBD)

```
1.7. "I want to know what is actually true — not what I want to be true."
    (children TBD — synthesis of all prior nodes)
```

---

## 8. Planned Content for Upcoming Nodes

### 1.6 — A method of reasoning that justifies falsehood can't distinguish it from truth

**Structured.** Absorbs the old 1.6 ("wanting something to be true doesn't
make it true") and old 1.7 into a single node. The old 1.6's content was
already established by 1.3.1; its substantive observations (hope about
falsehood, assumption about falsehood) became grounding cases for the
meta-constraint. The "wanting to know vs. wanting a specific answer"
distinction moved to 1.7.

Children: 1.6.1 (hope about something false), 1.6.2 (assumption about
something false), 1.6.3 (outcome of reasoning can be false), 1.6.4 (method
that justifies falsehood is independent from truth), 1.6.5 (truth and
falsehood lack distinction through such a method). All terminal.

**Objections to consider (Phase 2):**
- "All reasoning starts from assumptions — isn't every system ultimately
  circular?" (The tree starts from direct observation, not assumptions.
  Observations are not claims that need justification — they are the ground
  floor.)
- "Some truths can't be verified empirically — does this rule eliminate
  metaphysics entirely?" (Verification in 1.5.5 compares derivations against
  observation. Metaphysical claims that are derived through valid implication
  from observable premises survive — only those that bypass reasoning
  entirely are eliminated.)
- "Doesn't this rule eliminate itself — can it equally justify its own
  falsehood?" (The rule is self-reinforcing: rejecting it means accepting
  that methods which can't distinguish truth from falsehood are acceptable,
  which is self-defeating for anyone pursuing truth.)
- "But motivation itself is a want — doesn't that undermine the whole
  project?" (Resolved by the 1.7 wanting-to-know vs. wanting-a-specific-
  answer distinction.)
- "Doesn't desire influence what we observe and how we reason, making pure
  objectivity impossible?" (The node doesn't claim objectivity is easy — it
  claims that a method independent from truth can't distinguish truth from
  falsehood, even if the reasoner finds it difficult to avoid such methods.)
- "What about self-fulfilling prophecies — cases where wanting something
  does make it happen?" (These operate through willful causation — will
  affecting body, which affects reality. The description's truth still
  depends on whether it matches reality, not on the wanting itself.)

### 1.7 — "I want to know what is actually true — not what I want to be true."

Synthesis of all prior nodes. Synonymous with Node 1's claim. Combines:
truth and falsehood exist (1.4), reasoning is how we check (1.5), methods
that justify falsehood can't distinguish truth (1.6). The result is a
personal commitment — stated in first person — to follow reasoning wherever
it leads. Includes the wanting-to-know vs. wanting-a-specific-answer
distinction (moved from old 1.6).

**Objections to consider:**
- "This is just a personal preference, not a logical necessity — why should
  anyone adopt it?" (The commitment follows from the preceding nodes: if
  truth exists, reasoning can check it, and bad methods can't find it —
  then the only coherent posture is to commit to reasoning honestly.
  Rejecting the commitment while accepting the premises is a contradiction.)
- "What if the truth is unknowable — isn't this commitment futile?" (The
  tree has already established that reasoning produces knowledge through
  verification. Whether *all* truth is knowable is a separate question —
  the commitment is to pursue what can be known honestly.)
- "But motivation itself is a want — doesn't that undermine 1.6?" (Wanting
  to know what is true = wanting knowledge, indifferent to which answer.
  Wanting something specific to be true = wanting a particular description
  to match reality. 1.6 applies to the second; the first is compatible.)

### Node 2 — Discovering Reality

This is where the deferred concepts from Section 6 likely land:
representation, analogy, model, projection, non-willful causation, reason,
why, explanation, understanding, accuracy. Also the verification →
unobserved existence insight (synthesizing 1.3 + 1.5). The scope →
resolution → context → meaning chain may begin here or in Node 3.

**Objections to consider:**
- "Projection is just anthropomorphism — why think reality actually works
  like our experience?" (Projection is validated by verification: if the
  projected concept produces accurate predictions, the structural similarity
  is real, not merely imagined.)
- "Models are always simplifications — can they ever match reality?" (This
  is where accuracy vs. truth may need to be distinguished. A model can be
  accurate within its scope without being exhaustively true.)
- "Our senses are unreliable — how can observation ground anything?" (Node 1
  already addresses this: observation is the perception of an object, and
  objects' natures are consistent across observations and independent from
  observation. Reliability is about consistency, not infallibility.)

### Nodes 3–8

Content exists in the old project files (attached separately). Each node
will be restructured into the tree format following the same Phase 1 → Phase
2 methodology used for Node 1. The old files are numbered and roughly correspond
by sieve layer:

- `0` = Rules, intro, background, and methodology
- `1` = Pursuit of Truth (maps to Node 1)
- `2` = Discovering Reality (maps to Node 2)
- `3` and `3.2` = Building Confidence (maps to Node 3)
- `4` and `4.1` = Defining God (maps to Node 4)
- `5` = Alignment with Reality (maps to Node 5)
- `6` and `6.1` = Historical Comparison (maps to Node 6)
- `7` and `7.1` = Non-Fundamental Comparison (maps to Node 7)
- `8` = Results and Conclusion (maps to Node 8)
- `9` = Appendices (incomplete)

---

## 9. What to Work On Next

In order of priority:

1. **Structure children for 1.7:**
   - 1.7 (Personal contract): Synthesis of all prior. Synonymous with
     Node 1's claim. Includes the wanting-to-know vs.
     wanting-a-specific-answer distinction.

2. **Begin Phase 2 for Node 1** — DFS fleshing out from deepest terminal
   nodes upward.

3. **Update data.json** — Remove filler content, insert real tree.

4. **Continue to Nodes 2–8** following the sieve layer order.

---

## 10. AI Thinking Procedure

These are the steps the AI must follow when proposing, reviewing, or
restructuring nodes. The procedure exists because the AI consistently
forgets to apply specific principles after a few messages — especially
auditing, redundancy checking, and observe-before-abstracting. This section
is designed to be re-read at the start of every response where nodes are
being created or modified.

### Before Proposing Any Node

Run these checks in order. Each one is a gate — if it fails, stop and fix
before proceeding.

**1. Does this node say anything new?**
Substitute all defined terms with their formal definitions. Does the
resulting statement express something not already captured by an existing
node? If it follows trivially from combining existing definitions applied
to already-defined terms, it does not earn a node (convention 14) unless it
both aids recognition (convention 18) AND is a genuinely new application
that downstream nodes depend on. If redundant, absorb or remove.

**2. Is every term grounded?**
For each term in the claim: is it (a) defined in a prior node, (b) being
defined right now, or (c) common English needing no definition? Flag any
term that fails. Pay special attention to:
- Causal/agentive language: "make," "determine," "produce," "generate"
- Capacity/possibility language: "can," "able," "capable," "-able" suffix
  (only grounded after 1.4.4.1)
- Logical connectives: "if" (only grounded after 1.4.4.6)

**3. Does the claim use terms by their definitions, not connotations?**
Substitute each defined term's formal definition into the claim. Does it
still read correctly? If the formal definition doesn't fit but the common
English connotation does, the usage is ungrounded.

**4. If defining a new term — where does it structurally belong?**
Trace the definition's dependencies. Place it where it fits structurally
(logical structures in 1.4, processes in 1.5, etc.), not where it is first
needed. Types are children of their parent concept. Classes of X go after
X is defined.

**5. If stating a general rule — are the observed cases grounded first?**
The tree derives rules from observations, not the other way around. Before
stating any general principle, identify the specific observable cases that
exhibit the pattern. These cases must appear as prior siblings or children.
Do not state the rule and then justify it — observe, then induce.

### After Proposing a Node or Set of Nodes

**6. Dependency audit.**
For every term in every proposed claim, confirm it passes check #2.
Cross-check: does any proposed node use a term defined by a later sibling?
If so, reorder.

**7. Synonym collision check.**
Does any term in the proposal already exist in the vocabulary with a
different meaning? If so, rename. One term = one meaning.

**8. Final child test.**
Does the last substantive child naturally arrive at the parent's meaning
(convention 13)? If not, either a child is missing or the parent header
needs adjusting.

**9. Convention 14 sweep.**
Is every node a genuine atomic step? Remove any node that exists only for
structural completeness. But also: are there any skipped steps — cases
where the logical gap between two siblings requires an intermediate node?

### Common Mistakes to Watch For

These are specific failure patterns observed in previous sessions. Treat
them as red flags.

- **Jumping to the abstraction.** Proposing a general rule without first
  grounding it in observed cases. Fix: identify the observations first,
  then induce.

- **Sidestepping definitions.** Rephrasing a claim to avoid defining a
  needed term. Fix: if the term carries a genuine distinction and its
  prerequisites are met, define it. Don't hide the gap.

- **Placing definitions where first used.** A definition belongs where it
  fits structurally, not where it's first needed. Fix: trace dependencies
  and place accordingly.

- **Including redundant recall nodes.** Restating an existing definition
  in slightly different language. Fix: check if the node says anything new
  (check #1). If not, the existing definition already does the job.

- **Proposing before auditing.** Presenting a full structure and then
  auditing only when prompted. Fix: audit every proposal before presenting
  it. The checks above are not optional.