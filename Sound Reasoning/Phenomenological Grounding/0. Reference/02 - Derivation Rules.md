# 02 Derivation Rules

How new nodes get derived. Everything here is the author's ruling unless marked as a thread's working reading (those are open to his veto). New rules get added as they are discovered.

## Deriving nodes

- Children nodes are a specific manifestation of a parent node.
- Children nodes can only introduce one new term.
- Children nodes must use terms from ancestral nodes.
- A node's observations should diversely encompass its children nodes.
- Inheritance lists only the nearest connections: if A -> B -> C, then C inherits from B only, because B already includes A in its inheritance.
- The Definition property and the Conclusion's concluding statement must match word for word.
- Nodes grow over time — going back to add links or material is proofreading, not new derivation; the work itself stays one node at a time.
- The author is the initial author of everything in the record: he writes and accepts improvements, or explicitly accepts a suggestion. Suggestions are always welcome — from the master thread and every section thread, about the current piece or anything else noticed.
- Terms Introduced are listed alphabetically.
- An introduced term covers its grammatical forms — "appear" brings "appearance" and "appearing" along with it.
- Node text is written in standard markdown, so words can be emphasized and the files can later be consumed by the website project.

## What "Terms Introduced" means

A node's introduced terms are the words that, used in later sentences, refer back to this node's concept. The author's example: in "what is that?", the "what" asks to describe a particular phenomenon that occurred, so it refers back to the phenomena node. Homonyms keep their other meanings elsewhere ("feeling" can also mean an emotion); a term's listing covers only the usage that refers back to its node. The check this creates: when a later node uses an introduced word, verify it is used in the sense that points back to its node, not in a homonym sense. Thread's working reading: the text sections are everyday-language explanation, not term-granting — only Terms Introduced grants words, and only the Definition is bound to build from ancestral terms.

## Process

- The full working routine — what to read at thread start, how to handle each of the author's messages, when to consult which reference file, how to verify and when to loop — lives in [[01 - Processing Queries]]. Threads follow it, and re-read it whenever unsure.
- Section threads may update the rules files whenever the work needs it; anything added as a thread's own reading is marked as such.
- Threads do not record snapshots in the file history; the master thread reviews finished work and records the snapshot after the author's ok.
- All writing — nodes, prompts, returns, chat — follows [[03 - Demystification]]: everyday words, full flowing sentences, examples where a point is invisible without one, bite-sized bullets, no ambiguity, no bare references. Writing and checking both consult [[04 - Common Biases]] — a shared bias does not look like a bias.
- [[04 - Common Biases]] grows with the work: any thread that meets a new bias, or a new example of a listed one, adds it to that page.
- When checking a finished node, spawn one fresh helper per kind of effort — one for format against these rules, one for the writing against [[03 - Demystification]] and [[04 - Common Biases]], one for consistency across the reference files — each helper seeing only what its check needs, and each disclosed in one line.
- When finishing any node, add its objections to [[07 - Objection Index]]: under the right category, numbered, with the general objection (the form anyone might raise about any claim) as the title and the node's specific form beneath it, linked. Consult the index first when a new objection arrives — a recurring objection may already have its answer at another level.
- Every thread pastes the blank node template, unfilled, each time it opens a new entry.
- Any issue a check finds is stated to the author in chat, plainly, with the problem described. This binds all threads.
- When finishing any node: check [[05 - Pending Links]] (add the waiting links if this node is the one being waited for; log new entries when this node points at future nodes), and update [[06 - Phenomenological Dictionary]] (each introduced term, its one-line meaning, its node).
- metadata_status is "in-progress" while a node is being worked or proofread, and becomes "ratified" only when the author gives his ok; the snapshot is recorded at that same moment.

## The node format

Properties: ID (section initials plus a number — PP1, PP2, ...), Title, Definition, Inherits From (nearest parents only, as links), Leads To (nearest children, as links, added as they get made), Terms Introduced (alphabetical), plus two bookkeeping fields filled by the thread: metadata_status and metadata_date.

Text sections, in this order, any section absent when empty:

1. Motivation — the question or short statement that gives the node its point.
2. Observations — the set of things pointed at; not exhaustive unless the node's set is small and finite. Examples live here. Each observation carries a bracketed type tag, like "[taste] strawberry" or "[thought] "the earth is flat"".
3. Conclusion — the definition again, word for word, in bold, with any relevant explanations under it.
4. If Rejected — what you have to accept if you reject the node, as one or more outcomes; an outcome may carry "Proof by Contradiction" and "Consequences" sub-parts.
5. Unlocks — two guaranteed subsections, Concepts first: Concepts (the doors this node opens), then Vocabulary (introduced terms in bold, each with a one-line meaning and italic synonyms — the word "Synonyms" sits inside the italics; a term may sit inside another entry's italic synonyms instead of carrying its own bold entry).
6. Eliminates — what the node rules out.
7. Unknowns — what the node deliberately does not answer, each with a pointer to the answering node once it exists.
8. Objections — objections at this node's level, with their refutations; an objection belonging to a different level goes to [[08 - Unresolved Objections]] until its node exists. Each objection's parts, in order: Objection Basis (the objection at full strength), Objection Commitments (what the objector must stand behind), Shared Ground (only what both sides already agree on — the reply starts from listening, and everything after works outward from that footing; the disagreement itself belongs to the later parts, never here), What's Missing, Correction.
9. Relevant Links — a basic list of relevant nodes the reader can navigate to: an id plus definition as a link. Always present, even before its nodes exist — it holds a placeholder naming what it waits for, and fills in as those nodes are created.
10. Notes — as long as needed, or absent.

Formatting: a blank line follows each section header and separates a paragraph from a following list (optional after a short bold lead-in line, like the Conclusion's concluding statement). Bullet counts everywhere are dynamic: any section or list, in any part of a node, holds as many items as it needs — more or fewer; no count is a pattern to copy. Inside a list, a blank line separates labeled sub-blocks (like "Proof by Contradiction" from "Consequences", or "Concepts" from "Vocabulary"); otherwise no blank lines inside a list. The long dash (—) marks sentence breaks and asides; the short dash (-) appears only inside compound words. Double quotes for every quoted word, label, or claim; single quotes only inside double quotes. The same kind of thing gets the same mark every time. Where a sentence's point is invisible without an example, the example goes right there, in parentheses or a sub-bullet ("a three-sided shape has three sides"). No sentence should point at an earlier item by number alone — restate in a few words what the item said ("the second commitment — that X — is true, but ...").

Naming: section folders are numbered, like "1. Phenomenological Primitives"; node files are named like "PP1 - Phenomena"; the numbered reference files live in the "0. Reference" folder and are named like "06 - Phenomenological Dictionary".

## The blank template (pasted at every new entry)

```
ID: 
Title: 
Definition: 
Inherits From: 
Leads To: 
Terms Introduced: {}

Motivation: 

Observations:
- [type] 

Conclusion: 

If Rejected:
- 

Unlocks:
- Concepts:
  - 
- Vocabulary:
  - 

Eliminates:
- 

Unknowns:
- 

Objections:
- 

Relevant Links:
- 

Notes:
- 
```
