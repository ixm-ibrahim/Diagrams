#!/usr/bin/env python3
"""
audit_session.py — Generate audit session files for a specific node
(or range), including its descendants.

Produces two files:
  - AUDIT_PROMPT.md — the prompt to paste into a new chat
  - AUDIT_CONTEXT.md        — the single attachment: all reference docs
                             + audit-specific context + full current
                             content of every node being audited

The AI's job, given these two files, is to audit each node against
CHECKLIST.md / RULES_AND_PRINCIPLES.md / CLARIFICATIONS.md and output
one complete, ready-to-paste node at a time — every field populated —
as a drop-in replacement for the existing node in data.json.

Usage:
    python audit_session.py 1.1.3
    python audit_session.py 1.2.5.1-1.2.5.8          # range of siblings
    python audit_session.py 1.2.5.1-8                # range shorthand
    python audit_session.py 1.1,1.2.5                # comma-separated
    python audit_session.py 1.1.3 --include-incomplete

Section-focused auditing (sharper attention on one section at a time):
    python audit_session.py 1.1.3 --section observations
    python audit_session.py 1.1.3 --section objections
    python audit_session.py 1.1.3 --section if-rejected
Sections: observations, conclusion, if-rejected, unlocks, eliminates,
          unknowns, objections, all (default).

When --section is anything other than 'all', the AI audits only that
section but still sees the full node for cross-section coherence. The
output is still a full node JSON with every field preserved — only the
targeted section is revised. Any issues spotted in other sections get
flagged for a separate pass but are left untouched in the output.
"""

import json
import os
import re
import sys
import argparse

# Import shared helpers from prep_session.py (same directory)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from prep_session import (  # noqa: E402
    STOP_WORDS,
    extract_keywords,
    extract_keywords_from_vocabulary,
    extract_unlocks_text,
    find_grounding_nodes,
    format_node_summary,
    generate_current_state,
    get_ancestors,
    get_descendants,
    get_node,
    get_siblings,
    has_sections,
    id_sort_key,
    load_data,
    parse_targets,
    stemmed_set,
)


# ─────────────────────────────────────────────────────────────────────
# Section-focus profiles
# ─────────────────────────────────────────────────────────────────────
#
# Each profile scopes the audit to one section type. The full reference
# bundle (Writing Guide, Checklist, Rules, Clarifications) still ships
# in AUDIT_CONTEXT.md — but the first prompt's attention is pulled tight
# to the rules that matter most for this section, and the AI is told
# to leave every other section of the node untouched.
#
# `section_title` must match the exact title used in data.json.
# `guide_anchors` are the `## ...` headings inside WRITING_GUIDE.md
# worth pointing the AI at.
# `checklist_focus` are the checklist items whose numbers to call out.
# `stance` is a list of section-specific rules/reminders, phrased as
# terse bullets for the prompt.
# `failures` are the failure patterns from CHECKLIST.md's "Common
# failure patterns" table that hit this section hardest.

SECTION_PROFILES = {
    "observations": {
        "section_title": "Observations",
        "display": "Observations",
        "guide_anchors": ["The Governing Goal", "General Principles",
                          "Observations"],
        "checklist_focus": ["2 (every term grounded)",
                            "5 (general rule grounded in observed cases)",
                            "6 (Section Writing Guide applied — Observations bullet)",
                            "S4 (raw material test)",
                            "S7 (observations woven in — do the objections reference these?)",
                            "S10 (bullet size)"],
        "stance": [
            "**Each observation is the datum, period.** No explanatory gloss, "
            "no dash-phrase, no conclusion-in-disguise. "
            "WRONG: \"A sharp pain — vivid, immediate.\"  RIGHT: \"A sharp pain, right now.\"",
            "**Specific examples, not abstract categories.** \"Red\" — not \"a color.\"",
            "**Cover the range of types at the node's level.** Different KINDS, "
            "not variations of one kind. If the node is about wanting, show a "
            "bodily want, an aversive want, an intellectual want, a meta-want.",
            "**Only grounded terms.** Apply the synonym test: if any synonym "
            "of a word appears in any node's Unlocks, the word is doing "
            "philosophical work and needs grounding. Watch especially for "
            "capacity (\"can\", \"-able\"), causal (\"make\", \"produce\"), and "
            "logical (\"if\") verbs before their grounding nodes.",
            "**No self-references before 1.3.7.** No \"I\", \"my\", \"you\", "
            "\"your\". Say \"an arm, felt without looking\" — not \"your arm's position.\"",
            "**Each observation gets its own bullet** when distinct.",
            "**Raw is relative to node depth.** Raw for a deep node may be "
            "conceptually thick as long as every term is already grounded.",
        ],
        "failures": [
            "Formulaic observation gloss",
            "Conclusion-in-disguise (only makes sense after reading the claim)",
            "Ungrounded or capacity/causal/logical verbs smuggled in",
            "Abstract categories instead of specific examples",
        ],
    },

    "conclusion": {
        "section_title": "Conclusion",
        "display": "Conclusion",
        "guide_anchors": ["The Governing Goal", "Conclusion",
                          "Parent Synthesis"],
        "checklist_focus": ["1 (says something new)",
                            "2 (every term grounded)",
                            "3 (terms used by definition, not connotation)",
                            "6 (Section Writing Guide applied — Conclusion bullet)",
                            "9 (final child test)",
                            "13 (parallel symmetry)",
                            "14 (skeptical reader test)"],
        "stance": [
            "**Conclusion text must be near-verbatim to the node's claim.** "
            "Slight rewording for readability is fine. No added synthesis, "
            "logic, or framing beyond the claim itself.",
            "**Supporting points go in nested sub-bullets** (`text` / `items`): "
            "vocabulary definitions, why this matters, clarifying scope.",
            "**Definitions are direct.** Write `A \"quality\" is a singular "
            "distinct phenomenon` — not `\"Quality\" is the label for...`",
            "**Scoping statements belong in Unknowns or Objections**, not here.",
            "**Multiple concluding statements are fine** when a node "
            "establishes more than one thing — but each must be near-verbatim "
            "to something in the claim.",
            "**If this is a parent with children, apply Parent Synthesis "
            "rules:** the Conclusion summarizes what the children establish. "
            "The parent can use terms defined by its children (the parent "
            "summarizes after children are understood). Does NOT apply to "
            "same-page siblings.",
        ],
        "failures": [
            "Drift from the claim (added synthesis, logic, framing)",
            "Meta-definitions (\"X is the label for...\")",
            "Scoping statements creeping in from Unknowns/Objections",
            "Final child fails to arrive at parent's meaning",
        ],
    },

    "if-rejected": {
        "section_title": "If Rejected",
        "display": "If Rejected",
        "guide_anchors": ["Node Function Types", "If Rejected"],
        "checklist_focus": ["6 (Section Writing Guide applied — If Rejected bullet)",
                            "S3 (name one downstream concept)",
                            "11 (consequence audit)"],
        "stance": [
            "**Forward-looking costs, not backward-echoing.** Show what "
            "cannot be built later. \"Without X, there is no X\" is a "
            "restatement of the claim in the negative — not a consequence.",
            "**Name at least one specific downstream concept that breaks.** "
            "If you can't name one, you're about to restate the claim.",
            "**Match the framing verb to the node's function type:**\n"
            "    - Occurrence node: \"Without X, ...\"\n"
            "    - Label/define node: \"Without recognizing X, ...\"\n"
            "    - Distinction node: \"Without distinguishing X, ...\"",
            "**State the vivid core; don't enumerate.** Make the reader "
            "*feel* the loss. Don't follow with a list of every downstream "
            "node that breaks.",
            "**Apply the \"so what?\" test.** If the reader can shrug, the "
            "consequence is too weak.",
            "**Children must be `{title, detail}` objects**, never plain "
            "strings. Plain strings render as empty collapsible containers.",
            "**Consequence audit (checklist 11):** for each consequence, is "
            "there a real position where someone rejects the claim but "
            "disputes this consequence? If yes, that belongs in Objections.",
        ],
        "failures": [
            "Backward-echoing (\"without X there is no X\")",
            "Restating claim in the negative",
            "Listing every downstream node instead of the vivid core",
            "Consequence too weak — reader shrugs",
            "Children as plain strings instead of {title, detail}",
        ],
    },

    "unlocks": {
        "section_title": "Unlocks",
        "display": "Unlocks",
        "guide_anchors": ["Unlocks"],
        "checklist_focus": ["2 (every term grounded — Unlocks is the source)",
                            "12 (name concepts that will be reused)",
                            "S10 (bullet size)"],
        "stance": [
            "**Two categories:** vocabulary (all common words the node "
            "grounds, not just the main term) and next steps (what questions "
            "or observations this node enables).",
            "**Nested-bullet structure** for vocabulary: main term first "
            "(with synonyms), then \"Also grounded\" for connector words.",
            "**All the connector words count.** If the node grounds \"of\", "
            "\"have\", \"as\", \"with\", those belong here — not just the "
            "headline term. Later nodes will cite Unlocks for these.",
            "**Cross-reference the Phenomenology Diagram's term sets "
            "(PH1–RP5)** when judging completeness.",
            "**Every term that downstream claims will depend on should be "
            "explicitly grounded here.** If a downstream node uses a term "
            "that never appears in any node's Unlocks, that's the gap.",
            "**Unlocks is the one place vocabulary focus IS appropriate.** "
            "Everywhere else, \"grounding over vocabulary\" applies.",
        ],
        "failures": [
            "Missing connector words (the \"Also grounded\" list is thin)",
            "Vocabulary-development language leaking into Corrections "
            "(\"this provides vocabulary for X\" — say \"this grounds X\")",
            "Next-step bullet missing or generic",
        ],
    },

    "eliminates": {
        "section_title": "Eliminates",
        "display": "Eliminates",
        "guide_anchors": ["Eliminates"],
        "checklist_focus": ["1 (says something new)",
                            "6 (Section Writing Guide applied — Eliminates bullet)",
                            "14 (skeptical reader test)"],
        "stance": [
            "**Each item: a specific position someone might actually hold**, "
            "stated clearly enough that a reader can evaluate it.",
            "**No fabricated or straw positions.** Only real alternatives "
            "this node rules out. \"Nobody actually holds that\" means "
            "it doesn't belong here.",
            "**Vary phrasing — avoid formulaic openers.** Don't start every "
            "item with \"The position that...\". Read naturally.",
            "**An Eliminated position is one the node makes untenable** — "
            "not just one it happens to disagree with. Check: does accepting "
            "this node force you to reject this position?",
        ],
        "failures": [
            "Formulaic phrasing on every item",
            "Straw positions no one actually holds",
            "Vague items — reader can't evaluate",
            "Items the node doesn't actually eliminate (just disagrees with)",
        ],
    },

    "unknowns": {
        "section_title": "Unknowns",
        "display": "Unknowns",
        "guide_anchors": ["Unknowns"],
        "checklist_focus": ["6 (Section Writing Guide applied — Unknowns bullet)",
                            "14 (skeptical reader test)"],
        "stance": [
            "**Purpose: scope-guarding against ontological overreach.** Each "
            "Unknown should implicitly address an objection of \"but you're "
            "assuming X\" by saying \"X is not addressed here.\"",
            "**Remove filler items nobody would mistake for overreach.** "
            "\"Whether or not the universe is 14 billion years old\" is not "
            "a serious assumption the reader might think this node is making.",
            "**Cite the deferred-to node where known.** E.g., "
            "\"Whether or not phenomena correspond to anything beyond "
            "experience — requires ontological vocabulary (1.3).\"",
            "**Each Unknown names a specific deferred question**, not a "
            "general hand-wave at future work.",
        ],
        "failures": [
            "Filler items nobody would assume",
            "Missing scope guards (reader actually might think the node "
            "assumes X, but X isn't called out)",
            "Generic hand-waves instead of specific deferred questions",
        ],
    },

    "objections": {
        "section_title": "Objections",
        "display": "Objections",
        "guide_anchors": ["Objections", "Node Function Types"],
        "checklist_focus": ["S1 (inhabit the objector)",
                            "S2 (ontological smuggling)",
                            "S5 (stop after the resolution)",
                            "S6 (root-cause commitment)",
                            "S7 (observations woven in)",
                            "S8 (correction neutrality)",
                            "S9 (scope-defense quality)",
                            "S10 (bullet size)",
                            "11 (If Rejected consequence audit — missing objections)",
                            "12 (real-world objection audit)"],
        "stance": [
            "**Inhabit the objector.** One sentence: why would a reasonable "
            "person hold this *even after reading the node*? If you can't "
            "say it, you don't understand the objection yet. The reader who "
            "holds this view should feel accurately represented.",
            "**Four-part structure is required:** Objection Basis → "
            "Objection Commitments (numbered) → What's Missing → Correction. "
            "All four present.",
            "**Address the reader directly in Objection Basis:** \"Maybe "
            "wanting is just a label for sensations\" — not \"Reductionist "
            "positions hold that...\"",
            "**Commitments isolate the root-cause — the assumption that "
            "makes the objection fail.** Don't list every assumption; set "
            "up the load-bearer. Commitment #N should be the breaker; the "
            "others set it up.",
            "**What's Missing names which numbered commitment breaks and why.** "
            "Target the root-cause commitment, not tangential assumptions.",
            "**Ontological smuggling is the single most common failure.** "
            "Replace \"X is not Y\" (ontological denial) with \"whether or "
            "not X is Y is not addressed here\" (scope clarification). Also "
            "valid: \"Positing Y has no observational ground at this level.\"",
            "**Stop after the resolution.** Once the Correction resolves "
            "the objection, stop. No softening, qualifying, or hedging.",
            "**Correction neutrality at early levels.** Corrections should "
            "show the objection fails on its own terms, not that the node "
            "is \"right.\" Avoid premature endorsement of the claim.",
            "**Scope-defense must explain, not just assert.** When an "
            "objection imports ungrounded vocabulary, explain WHY the "
            "vocabulary isn't available and what the objection would need "
            "to show first. Don't agree or disagree with imported terms.",
            "**Weave the node's Observations into objections** as concrete "
            "examples where natural. \"Consider: hunger is not just stomach "
            "contractions — it includes a pull toward food.\"",
            "**Force the real commitment.** Present the genuine dilemma: "
            "either [preserves claim] or [specific costly commitment]. Name "
            "the commitment explicitly.",
            "**Bullet size discipline.** No bullet >400 chars. Split at "
            "sentence boundaries or nest with `{text, items}`.",
            "**Real-world audit (checklist 12).** Are there real "
            "philosophical positions or commonly held views that challenge "
            "this claim and aren't represented here? Add them if so.",
            "**Use grounding language, not vocabulary-development language.** "
            "\"This grounds the experience of X\" — not \"this provides "
            "vocabulary for X.\"",
        ],
        "failures": [
            "Ontological smuggling in Corrections (\"X is not Y\")",
            "Premature commitment — Correction endorses the claim at early levels",
            "Self-resolving Corrections (\"maybe they just have a weaker version\")",
            "Listing every commitment instead of isolating the load-bearer",
            "Abstract objections ignoring the node's own observations",
            "Wall-of-text bullets (>400 chars)",
            "Formulaic scope-defense (\"not addressed here\" without WHY)",
            "Vocabulary-development language in Corrections",
            "Missing real-world objections (position exists but isn't represented)",
        ],
    },

    "all": {
        "section_title": None,  # whole-node audit
        "display": "All sections",
        "guide_anchors": [],
        "checklist_focus": [],
        "stance": [],
        "failures": [],
    },
}


# ─────────────────────────────────────────────────────────────────────
# Audit-specific helpers
# ─────────────────────────────────────────────────────────────────────

def collect_audit_nodes(nodes, target_ids, include_incomplete=False):
    """Collect every node that should be audited: each target plus all
    its descendants. By default, nodes without sections (not yet written)
    are skipped and returned separately so they can be reported.
    """
    audit_id_set = set()
    for tid in target_ids:
        target = get_node(nodes, tid)
        if target is None:
            continue
        audit_id_set.add(tid)
        for d in get_descendants(nodes, tid):
            audit_id_set.add(d["id"])

    ordered_ids = sorted(audit_id_set, key=id_sort_key)

    to_audit = []
    skipped = []
    for nid in ordered_ids:
        n = get_node(nodes, nid)
        if n is None:
            continue
        if has_sections(n):
            to_audit.append(n)
        else:
            if include_incomplete:
                to_audit.append(n)
            else:
                skipped.append(n)
    return to_audit, skipped


def clean_node_for_output(node):
    """Return a dict of the node's fields in canonical order so the AI's
    revised output has a consistent shape to replace the existing node."""
    out = {
        "id": node["id"],
        "parentId": node.get("parentId"),
        "nextIds": node.get("nextIds", []),
        "prevIds": node.get("prevIds", []),
        "hasDerivation": node.get("hasDerivation", False),
        "claim": node.get("claim", ""),
    }
    if "shortTitle" in node:
        out["shortTitle"] = node["shortTitle"]
    out["soWhat"] = node.get("soWhat", "")
    if "search" in node:
        out["search"] = node["search"]
    out["sections"] = node.get("sections", [])
    return out


# ─────────────────────────────────────────────────────────────────────
# Context generation
# ─────────────────────────────────────────────────────────────────────

def generate_audit_context(nodes, target_ids, audit_nodes, skipped,
                           section="all"):
    """Build the audit-specific context markdown (added to the bundle
    after the reference files).

    `section` is a key in SECTION_PROFILES. When it isn't "all", a Focus
    header is added up top so the AI's first read makes the scope clear.
    """

    profile = SECTION_PROFILES[section]
    is_focused = section != "all"

    primary_id = target_ids[0]
    primary = get_node(nodes, primary_id)

    if len(target_ids) == 1:
        label = primary_id
        target_desc = f"{primary_id} — {primary['claim']}"
    else:
        label = f"{target_ids[0]}–{target_ids[-1]}"
        target_desc = ", ".join(target_ids)

    # Combine keywords across all targets (for grounding lookups)
    branch_keywords = set()
    vocab_keywords = set()
    for tid in target_ids:
        branch_keywords |= extract_keywords(nodes, tid)
        vocab_keywords |= extract_keywords_from_vocabulary(nodes, tid)

    lines = [f"# Audit Context: {label}\n"]
    lines.append(f"**Targets:** {target_desc}")
    lines.append(f"**Nodes to audit:** {len(audit_nodes)} "
                 f"(target(s) + all descendants with content)")
    if is_focused:
        lines.append(f"**Focus:** {profile['display']} section only "
                     "(other sections shown for context, left untouched on output)")
    lines.append("")

    if skipped:
        lines.append("### Nodes without content (not audited)\n")
        lines.append("These nodes fall within the target scope but have no")
        lines.append("sections yet — they are skipped. Re-run with")
        lines.append("`--include-incomplete` to include them anyway.\n")
        for n in skipped:
            lines.append(f"- {n['id']}: {n['claim']}")
        lines.append("")

    # ── 1. Branch structure ──────────────────────────────────────────
    lines.append("\n---\n## Branch Structure\n")
    for tid in target_ids:
        t = get_node(nodes, tid)
        lines.append(f"- {tid}: {t['claim']}")
        for d in get_descendants(nodes, tid):
            depth = d["id"].count(".") - tid.count(".")
            indent = "  " * depth
            status = "DONE" if has_sections(d) else "TODO"
            lines.append(f"  {indent}- [{status}] {d['id']}: {d['claim']}")
        lines.append("")

    # ── 2. Audit queue ───────────────────────────────────────────────
    lines.append("\n---\n## Audit Queue (tree order)\n")
    lines.append("Audit each node below against CHECKLIST.md, then present one")
    lines.append("full revised node JSON per response, ready to drop into")
    lines.append("data.json as a replacement. Wait for confirmation before the")
    lines.append("next node unless told otherwise.\n")
    for i, n in enumerate(audit_nodes, 1):
        lines.append(f"{i}. {n['id']}: {n['claim']}")
    lines.append("")

    # ── 3. Ancestor chain ────────────────────────────────────────────
    ancestors = get_ancestors(nodes, primary_id)
    lines.append("\n---\n## Ancestor Chain (structural context)\n")
    if ancestors:
        for a in ancestors:
            lines.append(format_node_summary(a, include_unlocks=True))
            lines.append("")
    else:
        lines.append("(No ancestors — top-level node.)\n")

    # ── 4. Grounding nodes (non-ancestor) ────────────────────────────
    ancestor_ids = {a["id"] for a in ancestors}
    all_grounding = {}
    for tid in target_ids:
        for gn in find_grounding_nodes(nodes, tid):
            all_grounding.setdefault(gn["id"], gn)

    non_ancestor_grounding = [
        g for g in sorted(all_grounding.values(),
                          key=lambda n: id_sort_key(n["id"]))
        if g["id"] not in ancestor_ids
    ]

    if non_ancestor_grounding:
        lines.append("\n---\n## Grounding Nodes (define vocabulary used)\n")
        lines.append("Prior non-ancestor nodes whose Unlocks define terms")
        lines.append("that appear in the target branch's claims. Use these")
        lines.append("to verify term grounding.\n")
        for g in non_ancestor_grounding:
            lines.append(format_node_summary(g, include_unlocks=True))
            lines.append("")

    # ── 5. Term → source lookup ──────────────────────────────────────
    target_claim_words = set()
    for tid in target_ids:
        t = get_node(nodes, tid)
        if not t:
            continue
        claims_here = [t["claim"]] + [d["claim"] for d in get_descendants(nodes, tid)]
        for cl in claims_here:
            cleaned = re.sub(r'[^\w\s-]', ' ', cl.lower())
            for w in cleaned.split():
                w = w.strip("-")
                if w and w not in STOP_WORDS and len(w) > 2:
                    target_claim_words.add(w)
    target_claim_stems = stemmed_set(target_claim_words)

    term_to_sources = {}
    all_vocab_nodes = list(ancestors) + non_ancestor_grounding
    for vn in all_vocab_nodes:
        unlocks_text = extract_unlocks_text(vn)
        if not unlocks_text:
            continue
        for phrase in re.findall(r'"([^"]+)"', unlocks_text):
            phrase_lower = phrase.lower()
            phrase_words = {
                w.strip("-") for w in re.sub(r'[^\w\s-]', ' ', phrase_lower).split()
                if w.strip("-") not in STOP_WORDS and len(w.strip("-")) > 2
            }
            if stemmed_set(phrase_words) & target_claim_stems:
                term_to_sources.setdefault(phrase_lower, []).append(vn["id"])

    if term_to_sources:
        lines.append("\n---\n## Term → Source Node Lookup\n")
        lines.append("Every term used in the audited nodes' claims should be")
        lines.append("(a) defined in a prior node below, (b) being defined in")
        lines.append("the node itself, or (c) common English. Flag failures.\n")
        for term in sorted(term_to_sources):
            ids = sorted(set(term_to_sources[term]), key=id_sort_key)
            lines.append(f"- \"{term}\" → {', '.join(ids)}")
        lines.append("")

    # ── 6. Completed siblings (parallel symmetry) ────────────────────
    target_id_set = set(target_ids)
    audit_id_set = {n["id"] for n in audit_nodes}
    completed_siblings = []
    seen = set()
    for tid in target_ids:
        for s in get_siblings(nodes, tid):
            if (has_sections(s) and s["id"] not in seen
                    and s["id"] not in target_id_set
                    and s["id"] not in audit_id_set):
                seen.add(s["id"])
                completed_siblings.append(s)

    if completed_siblings:
        lines.append("\n---\n## Completed Siblings (for parallel symmetry)\n")
        lines.append("Sibling nodes already finished. Use these to check that")
        lines.append("the audited nodes follow parallel structure where it")
        lines.append("makes sense (check 13).\n")
        for s in completed_siblings:
            lines.append(format_node_summary(s, include_unlocks=True))
            lines.append("")

    # ── 7. Full node content to audit ────────────────────────────────
    lines.append("\n---\n## Full Node Content to Audit\n")
    lines.append("The CURRENT content of every node in the audit queue, copied")
    lines.append("verbatim from data.json. Audit each against the Checklist,")
    lines.append("Writing Guide, Rules & Principles, and Clarifications above.")
    lines.append("Present the revised node as a single `json` block with every")
    lines.append("field populated — ready to paste as a drop-in replacement.\n")

    for n in audit_nodes:
        status_note = "" if has_sections(n) else " *(no sections — scaffold only)*"
        lines.append(f"\n### Node {n['id']}: {n['claim']}{status_note}\n")
        clean = clean_node_for_output(n)
        lines.append("```json")
        lines.append(json.dumps(clean, indent=2, ensure_ascii=False))
        lines.append("```\n")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────
# First-prompt generation
# ─────────────────────────────────────────────────────────────────────

def generate_audit_first_prompt(target_ids, audit_nodes, skipped,
                                section="all"):
    """Build the contents of AUDIT_PROMPT.md.

    When `section` isn't "all", the prompt narrows the auditor's attention
    to that one section type, emits the section-specific stance block, and
    instructs the AI to emit a full node where ONLY the targeted section
    has been revised — every other section preserved verbatim.
    """
    profile = SECTION_PROFILES[section]
    is_focused = section != "all"

    if len(target_ids) == 1:
        target_line = target_ids[0]
    else:
        target_line = ", ".join(target_ids)

    title_suffix = (f" — {profile['display']} Focus" if is_focused else "")

    lines = [
        f"# Sieve of Truth — Audit Session{title_suffix}",
        "",
        "I'm auditing existing content in the Sieve of Truth tree — checking",
        "it against the project's written standards and, where it falls short,",
        "fixing it. I've attached a single file, **AUDIT_CONTEXT.md**, that",
        "contains everything you need.",
        "",
    ]

    if is_focused:
        lines += [
            f"## Focus: **{profile['display']}** section only",
            "",
            f"This pass audits only the **{profile['section_title']}** section",
            "of each node. Other sections are visible for cross-section coherence",
            "— you'll reference them while judging the target section — but you",
            "**do not revise them**. The revised node JSON you emit preserves",
            "every other section verbatim from the current content. Any issues",
            "you notice in other sections: flag them at the end in a *Spotted",
            "elsewhere* list so I can queue them for a focused pass, but leave",
            "the text itself alone in your output.",
            "",
        ]

    lines += [
        "## How to read AUDIT_CONTEXT.md",
        "",
        "The file contains several sections, each marked with a `========`",
        "header. Read them in this order:",
        "",
        "1. **Project State** — What the project is and where it stands.",
        "2. **WRITING_GUIDE.md** — How each section type should be written.",
        "3. **CHECKLIST.md** — The checks to run on every node.",
        "4. **FORMAT_SPEC.md** — The JSON structure each node must follow.",
        "5. **RULES_AND_PRINCIPLES.md** — Structural rules, ordering, grounding.",
        "6. **CLARIFICATIONS.md** — Resolved design decisions; honor them.",
        "7. **Audit-Specific Context** — Audit queue, branch structure,",
        "   ancestor chain, grounding nodes, term→source lookup, completed",
        "   siblings, and — most importantly — the full current content of",
        "   every node being audited.",
        "",
    ]

    if is_focused and profile["guide_anchors"]:
        lines += [
            f"When reading WRITING_GUIDE.md, pay especially close attention to:"
        ]
        for anchor in profile["guide_anchors"]:
            lines.append(f"- `## {anchor}`")
        lines.append("")

    if is_focused and profile["checklist_focus"]:
        lines += [
            "When running CHECKLIST.md, these items are the load-bearing ones",
            f"for **{profile['display']}**:",
            "",
        ]
        for item in profile["checklist_focus"]:
            lines.append(f"- Check {item}")
        lines += [
            "",
            "Still run the rest — but these are where failures cluster for this",
            "section.",
            "",
        ]

    lines += [
        "## Scope",
        "",
        f"**Target(s):** {target_line}",
        f"**Audit queue:** {len(audit_nodes)} node(s) "
        f"(targets + all descendants with content)",
    ]
    if is_focused:
        lines.append(f"**Focus section:** {profile['display']} only")
    if skipped:
        lines.append(
            f"**Skipped:** {len(skipped)} node(s) without content "
            "(listed in AUDIT_CONTEXT.md)"
        )
    lines += [
        "",
        "The exact ordered queue is in AUDIT_CONTEXT.md under *Audit Queue*.",
        "",
        "## The governing goal",
        "",
        "The content exists to demystify. Three requirements simultaneously:",
        "readable (lowest cognitive load), precise (philosophy-PhD rigor), and",
        "atomic (one concept per node). These reinforce each other. Every",
        "audit decision flows from them.",
        "",
        "## Workflow",
        "",
        "For each node in the queue, in order:",
        "",
        "1. **Read the node's current JSON** in *Full Node Content to Audit*.",
    ]

    if is_focused:
        lines += [
            f"2. **Locate the `{profile['section_title']}` section** inside",
            "   `sections`. That's the only section you revise. Skim the other",
            "   sections for cross-section coherence (e.g., do the Objections",
            "   reference the Observations? does the Conclusion stay near-verbatim",
            "   to the claim?) but do not change them.",
            f"3. **Run every CHECKLIST.md check** that applies to",
            f"   {profile['display']} — especially the load-bearing ones listed",
            "   above. Do not skip the mechanical checks (1–15) or the stance",
            "   checks (S1–S10) that touch this section.",
            "4. **Run structural rules and clarifications.** Does the section",
            "   violate any convention in RULES_AND_PRINCIPLES.md? Does it",
            "   contradict anything in CLARIFICATIONS.md?",
            "5. **Verify term grounding inside this section.** Every term must",
            "   be (a) defined in a prior node — cross-check the Term → Source",
            "   Node Lookup and Ancestor Chain — (b) being defined in the node",
            "   itself, or (c) common English. Apply the synonym test.",
            "6. **Check parallel symmetry with completed siblings' same section.**",
            "   If prior completed nodes use a parallel shape for this section,",
            "   follow it (check 13).",
            "7. **Flag every failure** in the target section. Name the check,",
            "   quote the offending text, explain why it fails. Do not rationalize",
            "   keeping it.",
            "8. **Propose the fix** — rewrite only the target section so it",
            "   passes every check. Leave all other sections alone.",
            "9. **Emit the revised node** as a single ```json ... ``` block",
            "   containing one complete node object — every field present. The",
            f"   `{profile['section_title']}` section inside `sections` reflects",
            "   your revision; every other section is **verbatim** from the",
            "   current node content.",
            "10. **List issues spotted elsewhere** (in other sections) at the",
            "    end under *Spotted elsewhere* — don't fix them, just flag them",
            "    for a later focused pass.",
        ]
    else:
        lines += [
            "2. **Run every check in CHECKLIST.md** — the mechanical checks (1–15)",
            "   *and* the stance checks (S1–S10). Skip nothing.",
            "3. **Run the structural rules and clarifications checks.** Does the",
            "   node violate any convention in RULES_AND_PRINCIPLES.md? Does it",
            "   contradict anything resolved in CLARIFICATIONS.md? Does it use",
            "   vocabulary that isn't grounded yet?",
            "4. **Verify term grounding rigorously.** Every term in the claim",
            "   must be (a) defined in a prior node — cross-check the Term →",
            "   Source Node Lookup and Ancestor Chain — (b) being defined in the",
            "   node itself, or (c) common English with no technical weight.",
            "   Apply the synonym test: if any synonym of a term appears in any",
            "   node's Unlocks, the word is doing philosophical work and needs",
            "   grounding.",
            "5. **Check parallel symmetry.** Where completed siblings use a",
            "   parallel structure, the audited node should follow it (check 13).",
            "6. **Flag every failure.** Name the check, quote the offending text,",
            "   explain why it fails. Do not rationalize keeping it.",
            "7. **Propose the fix.** Rewrite the affected content so it passes",
            "   every check.",
            "8. **Emit the revised node** as a single ```json ... ``` block",
            "   containing one complete node object — every field (`id`,",
            "   `parentId`, `nextIds`, `prevIds`, `hasDerivation`, `claim`,",
            "   `shortTitle` if present, `soWhat`, `search` if present,",
            "   `sections`) — ready to paste into data.json as a drop-in",
            "   replacement for the existing node.",
        ]

    lines += [
        "",
        "**Do NOT modify** `id`, `parentId`, `nextIds`, `prevIds`, or",
        "`hasDerivation`. Preserve them exactly as they appear in the",
        "current JSON.",
    ]

    if is_focused:
        lines += [
            f"Only the `{profile['section_title']}` section inside `sections`",
            "is allowed to change. `claim`, `shortTitle`, `soWhat`, `search`,",
            "and every other section in `sections` must match the current",
            "content character-for-character.",
        ]
    else:
        lines += [
            "Only content fields (`claim`, `shortTitle`, `soWhat`, `search`,",
            "`sections`) may change.",
        ]

    lines += [
        "",
        "If a node passes every check with no needed changes, say so",
        "explicitly and re-emit the node unchanged (so I can paste it",
        "without special-casing anything).",
        "",
        "## Output format per node",
        "",
        "Use this shape (outer fence shown with `~~~` for clarity — you'll",
        "use markdown headings and a ```json fenced block in your actual",
        "response):",
        "",
        "~~~",
        "### <node id>",
        "",
        "**Audit Report**",
        "- Check N (name): PASS / FAIL — (if fail) quoted text + reason",
        "- Check N+1 ...",
        "  ...",
        "",
        "**Summary:** <passes cleanly | revision needed | no changes>",
        "",
        "**Revised Node**",
        "```json",
        "{ ...one complete node object... }",
        "```",
    ]

    if is_focused:
        lines += [
            "",
            "**Spotted elsewhere** *(flag-only, not fixed in this pass)*",
            "- <section name>: <issue>",
            "- ...",
        ]

    lines += [
        "~~~",
        "",
        "**Important:** Do ONE node per response unless I tell you otherwise.",
        "Wait for my confirmation (or \"next\") before moving to the next.",
        "",
    ]

    # Stance block — section-specific when focused, otherwise the generic one.
    if is_focused:
        lines += [
            f"## Stance for {profile['display']}",
            "",
            "**Be an objective, critical auditor, not a rubber stamp.** If the",
            "section is weak, imprecise, or quietly wrong, say so and propose",
            "the fix. Defending identified problems is the #1 failure mode.",
            "",
            f"The rules below are what usually goes wrong in "
            f"{profile['display']}. Audit against each:",
            "",
        ]
        for bullet in profile["stance"]:
            lines.append(f"- {bullet}")
        if profile["failures"]:
            lines += [
                "",
                f"**Failure patterns to watch for in {profile['display']}:**",
                "",
            ]
            for f in profile["failures"]:
                lines.append(f"- {f}")
        lines.append("")
    else:
        lines += [
            "## Stance — the hardest part",
            "",
            "**Be an objective, critical auditor, not a rubber stamp.** Independently",
            "analyze the reasoning. \"Looks fine\" is only acceptable when the node",
            "actually passes every single check. If something is weak, imprecise,",
            "or quietly wrong, say so and propose the fix.",
            "",
            "**Defending identified problems is the #1 failure mode.** If a check",
            "fails, the only response is: flag it and fix it. Never construct a",
            "defense for keeping broken content.",
            "",
            "**Inhabit the objector** when auditing Objections sections. One",
            "sentence: why would a reasonable person hold this *even after*",
            "reading the node? If you can't, the objection isn't yet understood.",
            "",
            "**Watch for ontological smuggling** in Corrections. Replace \"X is",
            "not Y\" with \"whether X is Y is not addressed here\" whenever the",
            "vocabulary for Y isn't yet grounded. This is the single most common",
            "failure.",
            "",
            "**If Rejected must be forward-looking.** Name a downstream concept",
            "that breaks — not a restatement of the claim in the negative.",
            "",
            "**Observations must be raw material.** Could someone who hasn't read",
            "the claim recognize each observation from their own experience, with",
            "no explanatory gloss? If not, it's a conclusion in disguise.",
            "",
        ]

    lines += [
        "Start with the first node in the Audit Queue.",
        "",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────
# Reference-file bundling
# ─────────────────────────────────────────────────────────────────────

def bundle_audit_files(reference_dir, audit_context, target_label, nodes):
    """Bundle Project State + reference files + audit context into a
    single upload-ready document.

    Auditing needs the full structural-rules and clarifications docs,
    which PREP_CONTEXT.md (for writing) deliberately omits — here we
    include them up front because the auditor applies them directly.
    """
    current_state = generate_current_state(nodes, target_label)

    ref_files = [
        ("WRITING_GUIDE.md", "Writing Guide"),
        ("CHECKLIST.md", "Quality Checklist"),
        ("FORMAT_SPEC.md", "Output Format"),
        ("RULES_AND_PRINCIPLES.md", "Structural Rules"),
        ("CLARIFICATIONS.md", "Design Clarifications"),
    ]

    parts = []

    # Project State
    parts.append(f"\n{'=' * 72}")
    parts.append("SECTION: Project State (auto-generated)")
    parts.append(f"{'=' * 72}\n")
    parts.append(current_state)
    print(f"  Generated: Project State ({len(current_state):,} chars)")

    # Reference files
    total = 1
    for filename, label in ref_files:
        fp = os.path.join(reference_dir, filename)
        if os.path.exists(fp):
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read().strip()
            parts.append(f"\n{'=' * 72}")
            parts.append(f"FILE: {filename} ({label})")
            parts.append(f"{'=' * 72}\n")
            parts.append(content)
            print(f"  Bundled: {filename} ({len(content):,} chars)")
            total += 1
        else:
            print(f"  WARNING: {filename} not found — skipping")

    # Audit-specific context
    parts.append(f"\n{'=' * 72}")
    parts.append("SECTION: Audit-Specific Context (auto-generated)")
    parts.append(f"{'=' * 72}\n")
    parts.append(audit_context)

    bundle = "\n".join(parts)
    print(f"\n  Bundled Project State + {total - 1} reference files "
          f"+ audit context")
    return bundle


# ─────────────────────────────────────────────────────────────────────
# CLI entrypoint
# ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate an audit session for a node (or range). Produces "
            "AUDIT_PROMPT.md (paste into chat) and AUDIT_CONTEXT.md "
            "(single attachment). The AI outputs one full, drop-in-ready "
            "node JSON at a time."
        )
    )
    parser.add_argument(
        "target",
        help="Target node ID (e.g., 1.1.3), range (1.2.5.1-1.2.5.8 or "
             "shorthand 1.2.5.1-8), or comma-separated list (1.1,1.2.5).",
    )
    parser.add_argument("--data", default=None, help="Path to data.json")
    parser.add_argument(
        "--include-incomplete", action="store_true",
        help="Also audit nodes that have no sections yet (default: skip).",
    )
    parser.add_argument(
        "--section",
        choices=list(SECTION_PROFILES.keys()),
        default="all",
        help=("Focus the audit on ONE section type per node. When set to "
              "anything other than 'all', the AI audits only that section "
              "but still sees the full node for cross-section coherence, "
              "and the revised-node output preserves every other section "
              "verbatim. Options: observations, conclusion, if-rejected, "
              "unlocks, eliminates, unknowns, objections, all "
              "(default: all)."),
    )
    parser.add_argument(
        "--ready-output", default=None,
        help="Output path for AUDIT_CONTEXT.md "
             "(default: ai_dev/outputs/AUDIT_CONTEXT.md)",
    )
    parser.add_argument(
        "--prompt-output", default=None,
        help="Output path for AUDIT_PROMPT.md "
             "(default: ai_dev/outputs/AUDIT_PROMPT.md)",
    )
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))   # ai_dev/scripts
    ai_dev_dir = os.path.dirname(script_dir)                  # ai_dev
    reference_dir = os.path.join(ai_dev_dir, "reference")
    outputs_dir = os.path.join(ai_dev_dir, "outputs")
    website_dir = os.path.dirname(ai_dev_dir)                 # Website root
    data_file = args.data or os.path.join(website_dir, "data.json")

    # Make sure the outputs dir exists (first-run safety).
    os.makedirs(outputs_dir, exist_ok=True)

    if not os.path.exists(data_file):
        print(f"ERROR: {data_file} not found")
        sys.exit(1)

    data = load_data(data_file)
    nodes = data["nodes"]

    target_ids = parse_targets(args.target, nodes)
    if not target_ids:
        print(f"ERROR: no valid nodes found for '{args.target}'")
        sys.exit(1)
    for tid in target_ids:
        if not get_node(nodes, tid):
            print(f"ERROR: node {tid} not found in data.json")
            sys.exit(1)

    # Resolve label for display
    if len(target_ids) == 1:
        target_label = target_ids[0]
    else:
        target_label = f"{target_ids[0]}–{target_ids[-1]}"

    print(f"Audit target: {args.target}  →  {target_label}")
    print(f"Data file: {data_file}")
    if args.section != "all":
        print(f"Section focus: {SECTION_PROFILES[args.section]['display']}")

    audit_nodes, skipped = collect_audit_nodes(
        nodes, target_ids, include_incomplete=args.include_incomplete
    )

    if not audit_nodes:
        print("ERROR: no nodes with content found in target scope. "
              "Re-run with --include-incomplete to audit scaffolds too.")
        sys.exit(1)

    print(f"Audit queue: {len(audit_nodes)} node(s)")
    if skipped:
        print(f"Skipped (no sections): {len(skipped)} node(s)")

    # Build the audit-specific context
    audit_context = generate_audit_context(
        nodes, target_ids, audit_nodes, skipped, section=args.section
    )

    # Bundle everything
    print("\nBundling reference files...")
    bundle = bundle_audit_files(reference_dir, audit_context, target_label, nodes)

    ready_file = args.ready_output or os.path.join(outputs_dir, "AUDIT_CONTEXT.md")
    with open(ready_file, "w", encoding="utf-8") as f:
        f.write(bundle)
    bsize = len(bundle)
    print(f"\nWritten: {ready_file}")
    print(f"  Size: {bsize:,} chars (~{bsize // 4:,} tokens)")

    # Generate and write the first prompt
    first_prompt = generate_audit_first_prompt(
        target_ids, audit_nodes, skipped, section=args.section
    )
    prompt_file = args.prompt_output or os.path.join(
        outputs_dir, "AUDIT_PROMPT.md"
    )
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(first_prompt)
    psize = len(first_prompt)
    print(f"Written: {prompt_file}")
    print(f"  Size: {psize:,} chars (~{psize // 4:,} tokens)")

    print("\nUsage: paste AUDIT_PROMPT.md into a new chat and attach "
          "AUDIT_CONTEXT.md as a file.")


if __name__ == "__main__":
    main()
