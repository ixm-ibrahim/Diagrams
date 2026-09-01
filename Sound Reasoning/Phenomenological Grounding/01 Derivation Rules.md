# 01 Derivation Rules

How new nodes get derived. Rules are discovered during the work and added here, dated, in the author's words.

## The rules so far (his words)

- children nodes being a specific manifestation of a parent node (2026-09-01)
- children nodes can only introduce one new term (2026-09-01)
- children nodes must use terms from ancestral nodes (2026-09-01)
- examples for each node should diversely encompass children nodes (2026-09-01) — examples now live inside the Observations section (his ruling, 2026-09-01), so this rule reads on a node's observations
- inheritance lists only the nearest connections (2026-09-01): "because nodes inherit ancestrally, only the nearest connections are needed - like if A -> B -> C, C doesn't need to mention that it inherits from both A and B, just B, because B already includes A in its inheritance"
- the Definition property and the Conclusion section must match word for word (2026-09-01)
- nodes grow over time, still one node at a time (2026-09-01): "certainly nodes will grow over time and we may need to go back to a node to link a future node somehow ... but I should still write everything, and we should do one node at a time still - so this growth is more of a proofreading over time"
- authorship (2026-09-01): "I can still write something, give to you to improve, and then accept the improvement - or you can suggest something from the start - as long as I'm the initial author."

## What "Terms Introduced" means (his words, 2026-09-01)

A node's introduced terms are the words that, used in later sentences, refer back to this node's concept. His example: in "what is that?", the "what" asks to "describe a particular phenomena [the 'what'] that occurred" — "whenever I use the word 'what', I am referring to the concept described in this node." Homonyms keep their other meanings elsewhere: "'feeling' could also specifically refer to an emotion, or some other form of awareness, but that is not what is meant when included here - it refers to its usage in a sentence that refers back to this concept." The working check this creates: when a later node uses an introduced word, verify it is used in the sense that points back to its node, not in a homonym sense. Working reading (the master thread's, vetoable): the text sections are everyday-language explanation, not term-granting — only Terms Introduced grants words, and only the Definition is bound to build from ancestral terms.

## Process rules (his rulings, 2026-09-01)

- Section threads may update the rules files whenever the work needs it: his rules are recorded in his words, dated; anything a thread adds as its own reading is marked as the thread's, open to his veto.
- Threads do not record snapshots in the file history. When the author brings a thread's output back, the master thread reviews it, says whether it is good to go, and records the snapshot only after he gives the ok.
- Prompts to threads, and the returns threads write, are both written the way he asked to be spoken to: everyday words, full flowing sentences, no technical vocabulary, no metaphorical labels, no short punchy fragments, ordinary examples where needed.
- Every thread pastes the blank node template, unfilled, each time it opens a new entry, so he never retypes the field names.

## The node format (his design, 2026-09-01)

Every node is one note file. The properties at the top hold: ID (section initials plus a number — PP1, PP2, ...), Title, Definition, Inherits From (links to the nearest parent nodes only), Leads To (links to the nearest child nodes, added as children get made), Terms Introduced (the word list), and two bookkeeping fields filled by the thread rather than by him: metadata_status and metadata_date.

The note's text holds these sections, in this order, any section simply absent when the node has nothing to put there:

1. Motivation — the question or short statement that gives the node its point.
2. Observations — the set of things pointed at; not exhaustive, unless the node's set is small and finite. Examples live here.
3. Conclusion — the definition again, word for word, with any relevant explanations.
4. If Rejected — what you have to accept if you reject the node, as one or more outcomes. A proof by contradiction sits inside — one per outcome where one exists (the master thread's working reading of his two models, open to his veto).
5. Unlocks — two guaranteed subsections: Vocabulary (each introduced term with a one-line meaning, in his words) and Concepts (the doors this node opens).
6. Eliminates — what the node rules out.
7. Unknowns — what the node deliberately does not answer, each with a pointer to the node that answers it, once that node exists.
8. Objections — objections at this node's level, with their refutations. An objection belonging to a different level goes to [[02 Unresolved Objections]] until its node exists.
9. Notes — as long as needed, or absent.

Naming (his patterns, 2026-09-01): section folders are numbered, like "1. Phenomenological Primitives"; node files are named like "PP1 - Phenomena".

## The blank template he fills for each new node (standard in all threads and prompts)

```
ID: 
Title: 
Definition: 
Inherits From: 
Leads To: 
Terms Introduced: {}

Motivation: 

Observations:
- 

Conclusion: 

If Rejected:
- 

Unlocks:
- Vocabulary:
  - 
- Concepts:
  - 

Eliminates:
- 

Unknowns:
- 

Objections:
- 

Notes:
- 
```
