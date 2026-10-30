# 03 Derivation Rules

How new nodes get derived: the rules, the node format, and the templates. New rules get added as they are discovered.

## Deriving nodes

- The core inferential principle governing everything: a method of reasoning that justifies falsehood can't distinguish what is true from what is not.
- Sound, clear logic is the highest priority of the whole effort. The concept layer — each argument actually establishing what it claims — comes before the language layer; see the two-layer rule in [[04 - Demystification]] and the logic helper in [[01 - Processing Queries]]. This applies to all pages and all parts of a page.
- Children nodes are a specific manifestation of a parent node.
- Children nodes can only introduce one new term.
- Children nodes must use terms from ancestral nodes.
- A node's observations should diversely encompass its children nodes.
- Inheritance lists only the nearest connections: if A -> B -> C, then C explicitly inherits from B only, because B already includes A in its inheritance.
- The Definition property and the Conclusion's concluding statement must match word for word.
- Nodes grow over time — going back to add links or material is proofreading, not new derivation; the work itself stays one node at a time.
- Two structures, two pairs of properties.
	- Inherits From / Leads To carry derivation — what builds on what, the chains.
	- Nested In / Encompasses carry zoom — which node a node sits inside, and which nodes unpack it — so a reader can walk the record at any depth.
	- A section's higher-level node is an ordinary node, general enough to encompass its nested nodes; any node can gain nested nodes later, at any depth, without anything renumbering.
	- Once nesting exists, an ID's number no longer promises reading order — reading order lives in the chains, and reader-facing decimal numbering (like the old website's 1.1.2) is computed for display, never stored.
	- Both directions of each pair are kept consistent, like pending links.
- The author is the initial author of everything in the record: he writes and accepts improvements, or explicitly accepts a suggestion. Suggestions are always welcome — from the master thread and every section thread, about the current piece or anything else noticed.
- Terms Introduced are listed alphabetically.
- An introduced term covers its grammatical forms — "appear" brings "appearance" and "appearing" along with it.
- Node text is written in standard markdown, so words can be emphasized and the files can later be consumed by the website project.
- No justification travels between nodes: PP2 is not deduced from PP1 — each claim's support is what occurs, looked at again. The parent is needed as the lens, not as a premise.
- The lens-not-premise line is re-earned at every node, not assumed: the checkers ask whether the child's new feature is displayed in what occurs independently of the concept.
- A rule of reasoning may be used only downstream of the node that ratifies it.
- What the record's own support-words mean: "derivation" and "what builds on what" in the rules above name the order of specification — what hands subject, words, and question to what — not a transmission of support; and "the bottom of the structure" in PP1's objection 2 names the claim whose fact every other claim presupposes and whose denial would take everything down — not a premise the structure draws warrant from. PP1's "on which all other ideas are built" reads the same way: built out of what it names, not resting on its say-so.
- The four bullets above get amended when the account in [[02 - Project Purpose]] is figured out and ratified.

## What "Terms Introduced" means

A node's introduced terms are the words that, used in later sentences, refer back to this node's concept. The author's example: in "what is that?", the "what" asks to describe a particular phenomenon that occurred, so it refers back to the distinction node. Homonyms keep their other meanings elsewhere ("feeling" can also mean an emotion); a term's listing covers only the usage that refers back to its node. The check this creates: when a later node uses an introduced word, verify it is used in the sense that points back to its node, not in a homonym sense. The text sections are everyday-language explanation, not term-granting — only Terms Introduced grants words, and only the Definition is bound to build from ancestral terms.

The reason: the writing is "us looking back a posteriori — we already have all of these terms/concepts/definitions ingrained in us, and we're just exposing and discovering them here". So the Motivation, Conclusion, and every other text section speak with full ordinary language (PP1's Motivation says "or it does not" although "not" is introduced at PP2); what the nodes put in order is which concept exposes which, not which words the prose may use.

## Process

The full working routine — what to read at thread start, how to handle each of the author's messages, when to consult which reference file, how to verify and when to loop — lives in [[01 - Processing Queries]]. Threads follow it, and re-read it whenever unsure.

## The node format

Properties: ID (section initials plus a number — PP1, PP2,...), Title, Definition, Inherits From (nearest parents only, as links), Leads To (nearest children, as links, added as they get made), Nested In (the encompassing node this one sits inside, as a link), Encompasses (the nodes nested inside this one, as links, added as they get made), Terms Introduced (alphabetical), plus one bookkeeping field filled by the thread: metadata_date.

Text sections, in this order, any section absent when empty:

1. Motivation — the question or short statement that gives the node its point.
2. Observations — the set of things pointed at; not exhaustive unless the node's set is small and finite. Examples live here. A bracketed type tag, like "[taste] strawberry", is optional: "observations don't need the type" — PP1 carries them only in case readers got confused about what a bare observation meant, like whether "the earth is flat" is a thought that occurred or a claim being made.
3. Conclusion — the definition again, word for word, in bold, with any relevant explanations under it.
4. If Rejected — what you have to accept if you reject the node, as one or more outcomes; an outcome may carry "Proof by Contradiction" and "Consequences" sub-parts. The Proof by Contradiction header carries the reminder "(assume the opposite, and show how it breaks itself)" — the reminder belongs to the Obsidian page format only; the brainstorming format goes without it. Consequences are ordered with the one most directly related to the Proof by Contradiction at the top — "it seems more intuitive like this".
5. Unlocks — two guaranteed subsections, Concepts first: Concepts (the doors this node opens), then Vocabulary (introduced terms in bold, each with a one-line meaning and italic synonyms — the word "Synonyms" sits inside the italics; a term may sit inside another entry's italic synonyms instead of carrying its own bold entry). Vocabulary entries are listed alphabetically, like Terms Introduced. A grouped entry that is not a term by itself (like PP2's singling-out and comparing words) comes after all the vocabulary terms are done, in a separate alphabetically ordered section, as needed — not required in every node.
6. Eliminates — what the node rules out.
7. Unknowns — what the node deliberately does not answer, each with a pointer to the answering node once it exists.
8. Objections — objections at this node's level, with their refutations; an objection belonging to a different level goes to [[09 - Unresolved Objections]] until its node exists.
	- An objection may refer to the result of an objection on another page, but concisely — the shape is "see ___, which addresses ___".
	- An objection may be referred to by its number, with a brief header as needed — like "see objection 2 ("made, not found")"; the rule against pointing by number alone keeps applying to everything else, like commitments.
	- Objections must be genuinely different objections: before adding one, name the commitment it stands on that no listed objection already carries — two objections sharing their core commitment get merged, keeping the strongest form. More objections is not more rigor; padding a node with restatements of one doubt is hyperskepticism wearing the process as a disguise (see [[05 - Common Biases#Hyperskepticism]]) — checkers verify this on every node.
	- Objections are organized pedagogically: a point fully explained once is not re-explained — later spots refer to it in the ruled shape; and the same objection reframed does not get several entries — one sub-bullet naming each reframing is enough, so long as the commitments exposed apply to each of them. This holds across pages too; [[08 - Objection Index]] is the cross-page tool for it.
	- Each objection's parts, in order: Objection Basis (the objection at full strength), Objection Commitments (what the objector must stand behind), Shared Ground (only what both sides already agree on — the reply starts from listening, and everything after works outward from that footing; the disagreement itself belongs to the later parts, never here), What's Missing, Correction.
9. Relevant Links — a basic list of relevant nodes the reader can navigate to: an id plus definition as a link, with the relevancy stated for each link, like "(parent)". Always present, even before its nodes exist — the header may sit empty until then: "no placeholder is necessary, as long as we know that it's there", with what it waits for tracked in [[06 - Pending Links]]. It fills in as those nodes are created.
10. Notes — as long as needed, or absent. Not a place for development thoughts or process material — open rulings, term questions, and working notes live in chat and the reference files, never in the node.

Formatting:

- A blank line follows each section header and separates a paragraph from a following list (optional after a short bold lead-in line, like the Conclusion's concluding statement).
- Bullet counts everywhere are dynamic: any section or list, in any part of a node, holds as many items as it needs — more or fewer; no count is a pattern to copy.
- Inside a list, a blank line separates labeled sub-blocks (like "Proof by Contradiction" from "Consequences", or "Concepts" from "Vocabulary"); otherwise no blank lines inside a list.
- Sub-bullets are indented with a tab; a paragraph-length bullet becomes a parent point with nested sub-bullets, per the bite-sized rule in [[04 - Demystification]]. Nesting — like every other piece of formatting — exists to make reading easier.
- The long dash (—) marks sentence breaks and asides; the short dash (-) appears only inside compound words.
- Double quotes for every quoted word, label, or claim; single quotes only inside double quotes.
- The same kind of thing gets the same mark every time.
- Where a sentence's point is invisible without an example, the example goes right there, in parentheses or a sub-bullet ("a three-sided shape has three sides").
- No sentence should point at an earlier item by number alone — restate in a few words what the item said ("the second commitment — that X — is true, but..."). Exception: objections may be referenced by their number, with a brief header as needed.

Naming: section folders are numbered, like "1. Phenomenological Primitives"; node files are named like "PP1 - Phenomena"; the numbered reference files live in the "0. Reference" folder and are named like "07 - Phenomenological Dictionary".

## The two formats

The work has two formats, not one: "there should be two different things: the brainstorming/deriving format, and the obsidian page format". The brainstorming format is what threads paste at every new entry and what he fills while deriving — deliberately simpler, "like removing markdown". The Obsidian page format is the node format described above, applied only when the ratified node is written to disk.

### The brainstorming template (pasted at every new entry)

```
---
ID: 
Title: 
Definition: 
Inherits From: 
Leads To: 
Nested In: 
Encompasses: 
Terms Introduced: {}
---

Motivation: 

Observations
- 

Conclusion
- 
 - 

If Rejected
- 
 - Proof by Contradiction
 1. 
 - Consequences
 1. 

Unlocks
- Concepts:
 - 
- Vocabulary:
 - "{term}" — {one-line meaning}. Synonyms: {synonyms}

Eliminates
- 

Unknowns
- 

Objections
1. {the objection, stated as its title}
 - Objection Basis
 - 
 - Objection Commitments
 1. 
 - Shared Ground
 - 
 - What's Missing
 - 
 - Correction
 - 

Relevant Links
- {id} ({relevancy})

Notes
- 
```

### The Obsidian page format (applied when the node goes to disk)

Rendered like [[PP1 - Phenomena]]: YAML frontmatter with the properties as lists, Inherits From as quoted wikilinks, and the bookkeeping field (metadata_date); "##" headers for the sections and "### 1." headers for objection titles; the Conclusion's statement and each If Rejected outcome in bold; bold part labels inside objections; italics for quoted thoughts and for synonyms; wikilinks in Relevant Links, each with its relevancy in parentheses.
