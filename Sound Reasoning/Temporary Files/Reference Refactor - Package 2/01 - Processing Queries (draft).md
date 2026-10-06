# 01 Processing Queries

How a thread handles anything the author sends. This file exists because past attempts drowned in their own reference files: the AI read everything once, worked from fading memory as its context filled, and made mistakes. The cure is a fixed routine with the reading built in at the moment it is needed — never from memory. When in doubt, or after any long stretch of work, re-read this file; it is short on purpose.

## At thread start

1. Read [[02 - Project Purpose]] and [[03 - Derivation Rules]] in full — what the project is doing, the rules, the node format, the template.
2. Read [[04 - Demystification]], [[05 - Common Biases]], and [[10 - Watch-list]] in full — they govern all writing and all checking.
3. Skim [[00 - Table of Contents]] to know what exists. The remaining files — [[06 - Pending Links]], [[07 - Phenomenological Dictionary]], [[08 - Objection Index]], [[09 - Unresolved Objections]], [[11 - Sentence Case Studies]] — are look-up files: consult them at the moments named below (the case studies whenever a sentence stays awkward through more than one rewording), and do not try to hold them in memory. And before proposing a fix for a listed word, re-open that word's entry in [[10 - Watch-list]].

## On each message from the author

1. Read the message twice, and list every separate request in it — his messages often carry several.
2. Decide what each request is — a filled node template, a fix or a ruling, a new rule, a question — and handle each in order. Before responding to any point of his, represent it back first — restate what he is saying, at its strongest — and only then answer; this applies to everything he says.
3. If any request is unclear, ask him: one question, told as a complete self-contained story. Never guess silently.
4. Check every response of his for new rules to add to the system, and for modifications or refinements of existing rules — he states them in passing as often as directly. Add each to the right reference file in his words — and apply it to the current work before moving on.
5. His corrections state principles, not spot-fixes: each one applies uniformly everywhere — to the whole current text, the other reference files, and all future work — not just to the instance he pointed at.
	- This mindset binds every thread, and every helper a thread spawns learns it too.
	- Whatever is newly learned — a banned word, a principle, a caught pattern — triggers a fresh sweep of all existing pages, and of the reference files' own examples where the lesson touches them.
6. If he corrects a misreading, the correction goes into the affected text itself, not just the conversation — the next reader will bring the same bias (the misreading rule in [[04 - Demystification]]).

## When working a node

1. Open the entry with three things: the question it must answer; inspiration from his own material, quoted word for word with the source file named (checked against that file first — inspiration stays in chat, never in the note); and the blank template from [[03 - Derivation Rules]].
2. He types; you verify. Check every load-bearing word of the Definition against [[07 - Phenomenological Dictionary]] — a word granted by a later node cannot be used (the Definition is the bound part; the text sections speak full ordinary language — see What "Terms Introduced" means in [[03 - Derivation Rules]]). Check each new objection against [[08 - Objection Index]] — its answer may already exist at another level; an objection belonging to a different level goes to [[09 - Unresolved Objections]].
3. Report problems one at a time in chat, each a complete story that quotes the node text it concerns — enough context that he can rule without opening the page — and each checked against [[05 - Common Biases]] before sending — a bias shared with the reader does not look like a bias. He fixes in his words; suggestions are welcome, but only what he accepts enters the record.
4. At the end of the first complete draft of any page: spawn a helper that hunts the draft for common AI words and phrases NOT yet on the [[10 - Watch-list]] — reading the list's removed entries, and the turned-back fixes recorded inside the entries, first, so it does not re-propose one — and report its finds to the author with examples, so he decides what gets added — and for anything he adds, list every instance with a proposed replacement for his agree-or-disagree, case by case.
5. When the node looks done, spawn one fresh helper per kind of effort, each seeing only what its check needs, each disclosed in one line:
	- format, against [[03 - Derivation Rules]];
	- writing, against [[04 - Demystification]] and [[05 - Common Biases]];
	- logic, for the concept layer — each argument establishes what it claims, each objection's commitments genuinely support it, each reply answers the commitment it names, nothing assumes what it concludes;
	- examples, hunting for points that are invisible without an example and have none, against the example rule in [[04 - Demystification]];
	- consistency, across the reference files (dictionary entries both directions, pending links both directions, objection index, table of contents).
6. State every finding to him in chat, plainly. Apply his fixes, re-check just the fixes, and keep looping the helpers and the fixes until the helpers return clean and he says it reads right.
7. Then finish, in one pass:
	- update [[00 - Table of Contents]];
	- check [[06 - Pending Links]]: add the waiting links if this node is the one being waited for; log new entries when this node points at future nodes;
	- update [[07 - Phenomenological Dictionary]]: each introduced term, its one-line meaning, its node;
	- add the node's objections to [[08 - Objection Index]], in the entry shape its header states;
	- go through all previously made pages and add links between relevant nodes, in both directions — beyond what [[06 - Pending Links]] already queues;
	- delete the old note on the same term from tmp-dump if one exists.
	The node awaits the author's ok.
8. The old project website is a source to mine when working any node — for objections especially: `Comparative Religion\Final Draft\Website\data.json` holds his old tree, with per-node observations, objections, eliminates, and unknowns. Material from it follows the same inspiration rules as everything else: quoted word for word, source named, checked against the file — inspiration stays in chat, and enters the record only through his acceptance.
9. All his old projects are "a source of ideas", never "a source of truth": nothing is settled by where a word or claim sat in an old file — an argument must stand on what occurs and on the current rules, and the old material only supplies candidates to consider. Arguing "the old scheme placed it there" is the mistake; see the matching entry in [[05 - Common Biases]].
10. Before printing any final output or return: re-read the current rules files (they may have changed mid-thread) and check the output against them, and scan the output itself for any ruling of his that has not yet been recorded.

## Context hygiene

- Every change carries its bookkeeping with it, in the same pass: a word replacement he ratifies goes into [[10 - Watch-list]]; a fix with a lesson goes into [[11 - Sentence Case Studies]]; a new link-in-waiting goes into [[06 - Pending Links]]; a new term ruling reaches [[07 - Phenomenological Dictionary]]; a new rule reaches its rules file. Never let a ruling live only in chat.
- Temporary and process files — handoffs, changes lists, and any other working file the AI makes that is not part of the record — live in their own folder, "Temporary Files", at the vault root beside the Phenomenological Grounding folder, so nothing process-shaped sits inside the digital brain. The tmp-dump folder is different — it holds his old notes under its own rule in [[00 - Table of Contents]].
- Section threads may update the rules files whenever the work needs it; what a thread adds on its own reading goes into its changes list for the author's veto.
- Rulings and additions are recorded in the reference files without dates.
- Snapshots in the file history belong to the master thread — threads do not run git; the master thread reviews finished work, and the snapshot is recorded at the moment the author gives his ok on a node.
- Never work from memory of a rule — open the file and look.
- After roughly every ten exchanges, or whenever unsure what the standard is, re-read this file and [[03 - Derivation Rules]].
- If context is running low, say so and write the return while quality is still high — a clean early handoff beats a degraded finish.
