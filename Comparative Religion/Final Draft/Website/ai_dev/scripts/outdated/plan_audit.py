#!/usr/bin/env python3
"""
plan_audit.py — Plan and pre-generate a full set of audit sessions for
a target range, laying them out as numbered, self-contained packets.

The script walks the subtree rooted at the target(s), counts
content-bearing nodes (via `audit_session.collect_audit_nodes`), and
chooses how to chunk the audit work. For every planned session it
writes a ready-to-use pair —

    AUDIT_PROMPT.md    (paste into a new chat)
    AUDIT_CONTEXT.md   (attach as the one file)

— into its own subfolder under:

    ai_dev/outputs/audits/<label>/

so you can work through the packets one chat at a time without re-running
any scripts.

Chunking heuristic
------------------
  content nodes  →  plan
  -------------     ---------------------------------------------------
  ≤ 6              one full `--section all` session.
  7 – 20           7 focused per-section passes across the whole range,
                   in priority order (observations → conclusion →
                   unlocks → objections → if-rejected → eliminates →
                   unknowns), then a final `--section all` coherence
                   pass.
  > 20             subdivide by direct sub-branches: each sub-branch
                   gets its own 7-pass focused set. Finally a single
                   `--section all` coherence pass over the full range.

Usage
-----
    python plan_audit.py 1.1
    python plan_audit.py 1.1.1-1.1.8
    python plan_audit.py 1.1,1.2 --include-incomplete
    python plan_audit.py 1.1 --data ../../data.json.bak

Then:
    open ai_dev/outputs/audits/1.1/00_plan.md
    → work through the numbered subfolders in order, one chat per folder.
"""

import argparse
import json
import os
import re
import sys

# Import shared helpers from the other scripts (same directory).
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from prep_session import (  # noqa: E402
    get_children,
    get_node,
    id_sort_key,
    load_data,
    parse_targets,
)
from audit_session import (  # noqa: E402
    SECTION_PROFILES,
    bundle_audit_files,
    collect_audit_nodes,
    generate_audit_context,
    generate_audit_first_prompt,
)


# ─────────────────────────────────────────────────────────────────────
# Planning constants
# ─────────────────────────────────────────────────────────────────────

# Ordered sequence for focused passes. Priority: surface-level raw
# material (observations) first, then the claim itself (conclusion),
# then vocabulary (unlocks) — these three feed the argumentative work
# (objections / if-rejected / eliminates) — and finally scope-guards
# (unknowns). An 'all' coherence pass closes out a range.
FOCUSED_SECTION_ORDER = [
    "observations",
    "conclusion",
    "unlocks",
    "objections",
    "if-rejected",
    "eliminates",
    "unknowns",
]

SINGLE_PASS_THRESHOLD = 6   # ≤ this → one full audit
FOCUSED_PASS_THRESHOLD = 20  # ≤ this → 7 focused + coherence


# ─────────────────────────────────────────────────────────────────────
# Label helpers
# ─────────────────────────────────────────────────────────────────────

def label_for_targets(target_ids):
    """Return a short human/filesystem-safe label for a target set."""
    if len(target_ids) == 1:
        return target_ids[0]
    # Range or list — use first-last joined with a hyphen. Already
    # filesystem-safe (only digits, dots, hyphens).
    return f"{target_ids[0]}-{target_ids[-1]}"


def sanitize_for_path(s):
    """Keep digits, letters, dots, hyphens, and underscores. Everything
    else becomes '_'. (Target IDs are already safe; this guards against
    unusual inputs.)"""
    return re.sub(r"[^0-9A-Za-z._-]", "_", s)


# ─────────────────────────────────────────────────────────────────────
# Sub-branch enumeration (for >20 node subdivision)
# ─────────────────────────────────────────────────────────────────────

def enumerate_sub_branches(nodes, target_ids):
    """Return a list of sub-branch target lists to subdivide into.

    If the user gave a single target, sub-branches are that target's
    direct children (each child is its own one-element target list).
    If the user gave multiple targets (range or comma-list), each one
    is already its own sub-branch.
    """
    if len(target_ids) > 1:
        return [[tid] for tid in target_ids]

    tid = target_ids[0]
    children = sorted(get_children(nodes, tid), key=lambda n: id_sort_key(n["id"]))
    if not children:
        # No children — cannot subdivide; fall back to treating the
        # single target as one sub-branch (caller will just run
        # focused passes on it regardless of size).
        return [[tid]]
    return [[c["id"]] for c in children]


# ─────────────────────────────────────────────────────────────────────
# Planning
# ─────────────────────────────────────────────────────────────────────

def plan_sessions(nodes, target_ids, include_incomplete):
    """Return (sessions, audit_nodes, skipped).

    `sessions` is a list of dicts, each describing one planned packet:
        {
            "target_ids": [...],
            "section":    "observations" | "conclusion" | ... | "all",
            "node_count": int,
            "note":       str (short description),
            "scope":      "full" | "subbranch",
        }
    """
    audit_nodes, skipped = collect_audit_nodes(
        nodes, target_ids, include_incomplete=include_incomplete
    )
    if not audit_nodes:
        return [], audit_nodes, skipped

    sessions = _plan_recursive(
        nodes, target_ids, include_incomplete,
        is_top_level=True,
    )
    return sessions, audit_nodes, skipped


def _plan_recursive(nodes, target_ids, include_incomplete, is_top_level):
    """Recursively plan sessions for `target_ids`.

    Rules:
      - ≤ SINGLE_PASS_THRESHOLD content nodes  → one `--section all` pass.
      - ≤ FOCUSED_PASS_THRESHOLD               → 7 focused passes (+
          coherence pass iff at the top level).
      - otherwise → subdivide by sub-branches and recurse on each. The
          coherence pass is only emitted at the top level so we don't
          accumulate one at every depth.
    """
    audit_nodes, _ = collect_audit_nodes(
        nodes, target_ids, include_incomplete=include_incomplete
    )
    n = len(audit_nodes)
    if n == 0:
        return []

    scope = "full" if is_top_level else "subbranch"
    sessions = []

    if n <= SINGLE_PASS_THRESHOLD:
        if is_top_level:
            note = f"single full audit ({n} nodes — small range)"
        else:
            note = f"small sub-branch — single full audit ({n} nodes)"
        sessions.append({
            "target_ids": list(target_ids),
            "section": "all",
            "node_count": n,
            "note": note,
            "scope": scope,
        })
        return sessions

    if n <= FOCUSED_PASS_THRESHOLD:
        for section in FOCUSED_SECTION_ORDER:
            display = SECTION_PROFILES[section]["display"]
            note = (f"focused {display} pass" if is_top_level
                    else f"focused {display} pass (sub-branch)")
            sessions.append({
                "target_ids": list(target_ids),
                "section": section,
                "node_count": n,
                "note": note,
                "scope": scope,
            })
        if is_top_level:
            sessions.append({
                "target_ids": list(target_ids),
                "section": "all",
                "node_count": n,
                "note": "full-range cross-section coherence pass",
                "scope": scope,
            })
        return sessions

    # n > FOCUSED_PASS_THRESHOLD → subdivide and recurse.
    sub_branches = enumerate_sub_branches(nodes, target_ids)
    # Guard against pathological non-decreasing recursion: if the only
    # sub-branch is the same single target we started with (no children
    # to expand into), fall back to the focused-pass set rather than
    # looping forever.
    same_shape = (len(sub_branches) == 1
                  and tuple(sub_branches[0]) == tuple(target_ids))
    if same_shape:
        for section in FOCUSED_SECTION_ORDER:
            display = SECTION_PROFILES[section]["display"]
            sessions.append({
                "target_ids": list(target_ids),
                "section": section,
                "node_count": n,
                "note": (f"focused {display} pass (large, no further "
                         "subdivision available)"),
                "scope": scope,
            })
        if is_top_level:
            sessions.append({
                "target_ids": list(target_ids),
                "section": "all",
                "node_count": n,
                "note": "full-range cross-section coherence pass",
                "scope": scope,
            })
        return sessions

    for sb_ids in sub_branches:
        sessions.extend(_plan_recursive(
            nodes, sb_ids, include_incomplete,
            is_top_level=False,
        ))

    if is_top_level:
        sessions.append({
            "target_ids": list(target_ids),
            "section": "all",
            "node_count": n,
            "note": "full-range cross-section coherence pass (final)",
            "scope": "full",
        })
    return sessions


# ─────────────────────────────────────────────────────────────────────
# Packet generation (pre-writes every AUDIT_PROMPT / AUDIT_CONTEXT pair)
# ─────────────────────────────────────────────────────────────────────

def session_folder_name(index, session):
    """Build the '01_observations_1.1' style folder name."""
    nn = f"{index:02d}"
    section = session["section"]
    branch_label = label_for_targets(session["target_ids"])
    if session["scope"] == "subbranch":
        # Include the sub-branch id to disambiguate when many passes are
        # in the same parent folder.
        base = f"{nn}_{sanitize_for_path(branch_label)}_{section}"
    else:
        # Full-range pass (either the small-plan single pass, the 7-pass
        # focused sequence on the whole target, or the final coherence
        # pass). No need to embed the label — the parent folder already
        # carries it.
        base = f"{nn}_{section}"
    # Mark the final coherence pass explicitly for quick scanning.
    if session.get("note", "").startswith("full-range cross-section"):
        base = f"{nn}_all_coherence"
    return base


def write_session_packet(session, nodes, reference_dir, session_dir,
                         include_incomplete, plan_index):
    """Regenerate audit_nodes for the session's targets, build the
    prompt + context + packet-metadata files, and write them into
    `session_dir`.

    PACKET.json captures what this packet did so `run_audit.py` and
    `apply_audit.py` don't have to re-derive it from the folder name.
    """
    os.makedirs(session_dir, exist_ok=True)
    target_ids = session["target_ids"]
    section = session["section"]

    audit_nodes, skipped = collect_audit_nodes(
        nodes, target_ids, include_incomplete=include_incomplete
    )
    target_label = label_for_targets(target_ids)

    audit_context = generate_audit_context(
        nodes, target_ids, audit_nodes, skipped, section=section
    )
    bundle = bundle_audit_files(
        reference_dir, audit_context, target_label, nodes
    )
    prompt = generate_audit_first_prompt(
        target_ids, audit_nodes, skipped, section=section
    )

    context_path = os.path.join(session_dir, "AUDIT_CONTEXT.md")
    prompt_path = os.path.join(session_dir, "AUDIT_PROMPT.md")
    with open(context_path, "w", encoding="utf-8") as f:
        f.write(bundle)
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(prompt)

    # Machine-readable packet metadata. Downstream scripts
    # (run_audit.py, apply_audit.py) read this to know which section
    # was focused, which nodes are in-queue, and the plan order so
    # revisions can be merged back into data.json correctly.
    section_title = SECTION_PROFILES[section]["section_title"]  # None for "all"
    packet_meta = {
        "plan_index": plan_index,
        "target_ids": list(target_ids),
        "section": section,
        "section_title": section_title,
        "scope": session["scope"],
        "note": session["note"],
        "audit_queue": [{"id": n["id"], "claim": n["claim"]}
                        for n in audit_nodes],
        "skipped": [{"id": n["id"], "claim": n["claim"]} for n in skipped],
    }
    packet_path = os.path.join(session_dir, "PACKET.json")
    with open(packet_path, "w", encoding="utf-8") as f:
        json.dump(packet_meta, f, indent=2, ensure_ascii=False)

    return {
        "context_path": context_path,
        "prompt_path": prompt_path,
        "packet_path": packet_path,
        "context_size": len(bundle),
        "prompt_size": len(prompt),
        "audit_count": len(audit_nodes),
        "skipped_count": len(skipped),
    }


# ─────────────────────────────────────────────────────────────────────
# 00_plan.md
# ─────────────────────────────────────────────────────────────────────

def write_plan_file(plan_path, top_label, target_ids, total_nodes,
                    skipped_count, sessions, packets):
    """Write the human-readable plan summary at the top of the audits
    folder."""
    lines = [
        f"# Audit Plan — {top_label}",
        "",
        f"**Target(s):** {', '.join(target_ids)}",
        f"**Content nodes in scope:** {total_nodes}",
    ]
    if skipped_count:
        lines.append(
            f"**Skipped (no sections yet):** {skipped_count} "
            "(re-run with `--include-incomplete` to include them)"
        )
    lines += [
        f"**Planned sessions:** {len(sessions)}",
        "",
        "## How to use",
        "",
        "Each numbered subfolder is a fully self-contained audit packet:",
        "",
        "1. Open the next subfolder in numeric order.",
        "2. Start a fresh chat.",
        "3. Paste the contents of `AUDIT_PROMPT.md` into the chat.",
        "4. Attach `AUDIT_CONTEXT.md` as a single file.",
        "5. Work through the audit; paste each revised node back into "
        "`data.json` as confirmed.",
        "6. Close the chat. Move to the next subfolder.",
        "",
        "No re-running scripts between sessions. The plan already chunked "
        "the work.",
        "",
        "## Session queue",
        "",
        "| # | Folder | Scope | Section | Nodes | Notes |",
        "|---|--------|-------|---------|-------|-------|",
    ]

    for i, (session, packet) in enumerate(zip(sessions, packets), 1):
        folder = os.path.basename(packet["folder"])
        scope = session["scope"]
        section_display = SECTION_PROFILES[session["section"]]["display"]
        ids_str = ", ".join(session["target_ids"])
        note = session["note"]
        lines.append(
            f"| {i:02d} | `{folder}/` | {scope} ({ids_str}) | "
            f"{section_display} | {packet['audit_count']} | {note} |"
        )

    lines.append("")
    lines.append("## Per-session detail")
    lines.append("")
    for i, (session, packet) in enumerate(zip(sessions, packets), 1):
        folder = os.path.basename(packet["folder"])
        section_display = SECTION_PROFILES[session["section"]]["display"]
        ids_str = ", ".join(session["target_ids"])
        lines += [
            f"### {i:02d}. `{folder}/`",
            "",
            f"- **Target(s):** {ids_str}",
            f"- **Section:** {section_display}",
            f"- **Audit queue size:** {packet['audit_count']} node(s)",
            f"- **AUDIT_CONTEXT.md size:** "
            f"{packet['context_size']:,} chars "
            f"(~{packet['context_size'] // 4:,} tokens)",
            f"- **AUDIT_PROMPT.md size:** "
            f"{packet['prompt_size']:,} chars "
            f"(~{packet['prompt_size'] // 4:,} tokens)",
            f"- **Note:** {session['note']}",
            "",
        ]

    with open(plan_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ─────────────────────────────────────────────────────────────────────
# CLI entrypoint
# ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Plan an audit campaign for a target range and pre-generate "
            "every AUDIT_PROMPT.md + AUDIT_CONTEXT.md packet into its "
            "own numbered subfolder. You then work through the packets "
            "in order, one chat per packet."
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
        "--output-root", default=None,
        help="Override the root folder under which <label>/ is created "
             "(default: ai_dev/outputs/audits).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print the plan but don't write any packets to disk.",
    )
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))   # ai_dev/scripts
    ai_dev_dir = os.path.dirname(script_dir)                  # ai_dev
    reference_dir = os.path.join(ai_dev_dir, "reference")
    outputs_dir = os.path.join(ai_dev_dir, "outputs")
    audits_root = args.output_root or os.path.join(outputs_dir, "audits")
    website_dir = os.path.dirname(ai_dev_dir)                 # Website root
    data_file = args.data or os.path.join(website_dir, "data.json")

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

    top_label = label_for_targets(target_ids)
    print(f"Planning audit for: {args.target}  →  {top_label}")
    print(f"Data file: {data_file}")

    sessions, audit_nodes, skipped = plan_sessions(
        nodes, target_ids, include_incomplete=args.include_incomplete
    )
    if not sessions:
        print("ERROR: no content-bearing nodes in target scope. "
              "Re-run with --include-incomplete to audit scaffolds.")
        sys.exit(1)

    total_nodes = len(audit_nodes)
    print(f"Content nodes in scope: {total_nodes}")
    if skipped:
        print(f"Skipped (no sections): {len(skipped)} node(s)")
    print(f"Planned sessions: {len(sessions)}")
    print()

    for i, s in enumerate(sessions, 1):
        section_display = SECTION_PROFILES[s["section"]]["display"]
        ids_str = ", ".join(s["target_ids"])
        print(f"  {i:02d}. {section_display:<18}  "
              f"scope={s['scope']:<9}  targets=[{ids_str}]  "
              f"nodes={s['node_count']}  — {s['note']}")

    if args.dry_run:
        print("\n(--dry-run: no packets written.)")
        return

    # Write packets.
    campaign_dir = os.path.join(audits_root, sanitize_for_path(top_label))
    os.makedirs(campaign_dir, exist_ok=True)
    print(f"\nWriting packets to: {campaign_dir}")

    packets = []
    for i, session in enumerate(sessions, 1):
        folder_name = session_folder_name(i, session)
        session_dir = os.path.join(campaign_dir, folder_name)
        print(f"\n── Packet {i:02d}: {folder_name} "
              f"(section={session['section']}, "
              f"targets={', '.join(session['target_ids'])}) ──")
        packet_info = write_session_packet(
            session, nodes, reference_dir, session_dir,
            include_incomplete=args.include_incomplete,
            plan_index=i,
        )
        packet_info["folder"] = session_dir
        packets.append(packet_info)
        print(f"  → AUDIT_PROMPT.md  ({packet_info['prompt_size']:,} chars)")
        print(f"  → AUDIT_CONTEXT.md ({packet_info['context_size']:,} chars)")

    # Write 00_plan.md.
    plan_path = os.path.join(campaign_dir, "00_plan.md")
    write_plan_file(
        plan_path, top_label, target_ids,
        total_nodes, len(skipped), sessions, packets,
    )
    print(f"\nWritten plan summary: {plan_path}")

    print(f"\nDone. {len(sessions)} packets laid out under:")
    print(f"  {campaign_dir}")
    print("Open 00_plan.md to see the recommended order, then work "
          "through the subfolders one chat at a time.")


if __name__ == "__main__":
    main()
