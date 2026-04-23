#!/usr/bin/env python3
"""
apply_audit.py — Merge the revised node JSONs from a campaign (or a
single session) back into data.json.

For each session folder found, reads:
    PACKET.json            — tells us which section the packet focused on
    revised/<node_id>.json — the AI's revised node output

Merge rules
-----------
  - If the packet's `section` is "all", the whole node is replaced
    (content fields only: claim, shortTitle, soWhat, search, sections).
    Metadata fields (id, parentId, nextIds, prevIds, hasDerivation)
    from the current data.json are preserved regardless of what the
    revised JSON contains.
  - If the packet focused on a specific section (observations,
    conclusion, unlocks, objections, if-rejected, eliminates, unknowns),
    ONLY that section's entry inside `sections` is replaced. Everything
    else — including other sections the revised JSON happens to carry —
    is ignored.

This is the key correctness property: in a 7-pass focused campaign,
each pass sees the same baseline data.json but is told to preserve
other sections verbatim. If we applied whole nodes in plan order,
pass 2's (ORIGINAL) observations section would overwrite pass 1's
REVISED observations. Applying only the target section per focused
packet avoids that.

Order of application
--------------------
Sessions are applied in plan order (00_plan.md order — the NN_ prefix).
For a single node audited in multiple packets, later packets that
revise the same section win. Packets that revise different sections
accumulate.

Safety
------
A backup of `data.json` is written to `data.json.bak` before the new
file is produced. Use `--dry-run` to preview changes without writing.

Usage:
    python apply_audit.py ../outputs/audits/1.1/01_all       # one session
    python apply_audit.py ../outputs/audits/1.1 --all         # whole campaign
    python apply_audit.py ../outputs/audits/1.1 --all --dry-run

Options:
    --all           Treat target as a campaign root.
    --dry-run       Print what would change, don't write data.json.
    --data          Alternate path to data.json (default: Website/data.json).
    --no-backup     Skip writing data.json.bak (not recommended).
"""

import argparse
import json
import os
import re
import shutil
import sys

from _common import die, load_json, load_data_json, write_json_atomic


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))   # ai_dev/scripts
AI_DEV_DIR = os.path.dirname(SCRIPT_DIR)                  # ai_dev
WEBSITE_DIR = os.path.dirname(AI_DEV_DIR)                 # Website root
DEFAULT_DATA_FILE = os.path.join(WEBSITE_DIR, "data.json")


# The set of fields that a revised node is allowed to change. Metadata
# is preserved from the existing node regardless of what the AI emits.
CONTENT_FIELDS = {"claim", "shortTitle", "soWhat", "search", "sections"}


# ─────────────────────────────────────────────────────────────────────
# Session discovery (mirrors run_audit.py)
# ─────────────────────────────────────────────────────────────────────

def is_session_dir(path):
    return all(
        os.path.isfile(os.path.join(path, f))
        for f in ("AUDIT_PROMPT.md", "AUDIT_CONTEXT.md", "PACKET.json")
    )


def is_campaign_dir(path):
    if not os.path.isfile(os.path.join(path, "00_plan.md")):
        return False
    for name in os.listdir(path):
        sub = os.path.join(path, name)
        if os.path.isdir(sub) and is_session_dir(sub):
            return True
    return False


def list_campaign_sessions(campaign_dir):
    """Sessions ordered by numeric prefix (plan order)."""
    entries = []
    for name in sorted(os.listdir(campaign_dir)):
        sub = os.path.join(campaign_dir, name)
        if not os.path.isdir(sub):
            continue
        if not is_session_dir(sub):
            continue
        m = re.match(r"^(\d+)_", name)
        order = int(m.group(1)) if m else 999
        entries.append((order, name, sub))
    entries.sort(key=lambda t: (t[0], t[1]))
    return [e[2] for e in entries]


def load_packet(session_dir):
    return load_json(os.path.join(session_dir, "PACKET.json"),
                     what="PACKET.json")


def load_revised_nodes(session_dir):
    """Return list of {path, node_id, data} for each revised/*.json in
    the session folder.

    A malformed revised JSON is a hard failure: the whole point of this
    script is to merge the AI's output back in, so silently dropping a
    revised node means data.json ends up missing an audit result we
    thought we'd applied."""
    revised_dir = os.path.join(session_dir, "revised")
    if not os.path.isdir(revised_dir):
        return []
    out = []
    for name in sorted(os.listdir(revised_dir)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(revised_dir, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            die(f"revised node file is not valid JSON: {e.msg} "
                f"(line {e.lineno}, col {e.colno}) — file: {path}")
        if not isinstance(data, dict):
            die(f"revised node file must contain a JSON object, got "
                f"{type(data).__name__} — file: {path}")
        if "id" not in data or not data["id"]:
            die(f"revised node file has no 'id' field — file: {path}")
        # Filename and id must agree. A mismatch usually means the AI
        # emitted the wrong id in the fenced block and the parser in
        # run_audit.py picked the filename from somewhere else. Either
        # way, merging it risks overwriting the wrong node.
        expected_id = name[:-len(".json")]
        if data["id"] != expected_id:
            die(f"revised node file id mismatch: filename says "
                f"'{expected_id}' but payload id is '{data['id']}' — "
                f"file: {path}")
        out.append({"path": path, "node_id": data["id"], "data": data})
    return out


# ─────────────────────────────────────────────────────────────────────
# Section lookup inside a node
# ─────────────────────────────────────────────────────────────────────

def find_section_index(node, section_title):
    """Return the index of the section with the given title inside the
    node's `sections` list, or None if not present."""
    for i, s in enumerate(node.get("sections", []) or []):
        if s.get("title") == section_title:
            return i
    return None


def validate_section_shape(section, where):
    """Every section must be an object with at least `title` and
    `items` (items can be an empty list, but the key must exist).
    A section missing these would silently break the UI renderer
    and we'd have no idea which audit introduced the bad data.

    `where` is a human-readable location string for the error."""
    if not isinstance(section, dict):
        die(f"revised section is not an object (got "
            f"{type(section).__name__}) at {where}")
    if "title" not in section or not isinstance(section["title"], str):
        die(f"revised section missing string 'title' at {where}")
    if "items" not in section:
        die(f"revised section missing 'items' key at {where}")
    if not isinstance(section["items"], list):
        die(f"revised section 'items' must be a list, got "
            f"{type(section['items']).__name__} at {where}")


# ─────────────────────────────────────────────────────────────────────
# Merge logic — one session at a time
# ─────────────────────────────────────────────────────────────────────

def apply_session(nodes_by_id, session_dir, packet, revised, change_log):
    """Apply one session's revised nodes to `nodes_by_id` (mutates in
    place). Appends a record per revision to `change_log`.

    Returns counts: {applied, skipped, warnings}."""
    section = packet.get("section", "all")
    section_title = packet.get("section_title")   # None for "all"
    session_label = os.path.basename(session_dir)

    applied = 0
    skipped = 0
    warnings = 0

    for item in revised:
        node_id = item["node_id"]
        revised_node = item["data"]

        current = nodes_by_id.get(node_id)
        if current is None:
            print(f"  WARNING [{session_label}]: node {node_id} "
                  "not found in data.json — skipping")
            warnings += 1
            continue

        if section == "all":
            # Whole-node replacement of content fields only.
            before = {k: current.get(k) for k in CONTENT_FIELDS}
            for k in CONTENT_FIELDS:
                if k in revised_node:
                    current[k] = revised_node[k]
            after = {k: current.get(k) for k in CONTENT_FIELDS}
            if before == after:
                # No content actually changed. Still count as applied
                # (the AI explicitly confirmed the node is clean).
                change_log.append({
                    "session": session_label,
                    "node_id": node_id,
                    "section": "all",
                    "effect": "no-change",
                })
            else:
                change_log.append({
                    "session": session_label,
                    "node_id": node_id,
                    "section": "all",
                    "effect": "replaced-whole-node",
                })
            applied += 1
            continue

        # Focused pass: replace only the target section.
        if not section_title:
            print(f"  ERROR [{session_label}]: packet section='{section}' "
                  "but section_title is empty in PACKET.json — skipping")
            skipped += 1
            warnings += 1
            continue

        rev_idx = find_section_index(revised_node, section_title)
        if rev_idx is None:
            print(f"  WARNING [{session_label}]: revised node {node_id} "
                  f"has no `{section_title}` section — skipping this node")
            skipped += 1
            warnings += 1
            continue

        cur_idx = find_section_index(current, section_title)
        new_section = revised_node["sections"][rev_idx]
        validate_section_shape(
            new_section,
            where=f"{session_label} / {node_id} / section '{section_title}'",
        )
        # Ensure current has a sections list.
        if "sections" not in current or current["sections"] is None:
            current["sections"] = []

        if cur_idx is None:
            # Target section didn't exist in current data.json;
            # append it. (Unusual — worth flagging.)
            current["sections"].append(new_section)
            print(f"  NOTE [{session_label}]: added new `{section_title}` "
                  f"section to {node_id}")
            change_log.append({
                "session": session_label,
                "node_id": node_id,
                "section": section_title,
                "effect": "added-section",
            })
        else:
            if current["sections"][cur_idx] == new_section:
                change_log.append({
                    "session": session_label,
                    "node_id": node_id,
                    "section": section_title,
                    "effect": "no-change",
                })
            else:
                current["sections"][cur_idx] = new_section
                change_log.append({
                    "session": session_label,
                    "node_id": node_id,
                    "section": section_title,
                    "effect": "replaced-section",
                })
        applied += 1

    return {"applied": applied, "skipped": skipped, "warnings": warnings}


# ─────────────────────────────────────────────────────────────────────
# Campaign / single-session orchestration
# ─────────────────────────────────────────────────────────────────────

def collect_sessions(target, run_all):
    """Return an ordered list of session_dirs."""
    target = os.path.abspath(target)
    if not os.path.exists(target):
        print(f"ERROR: {target} does not exist")
        sys.exit(1)
    if run_all:
        if not is_campaign_dir(target):
            print(f"ERROR: {target} is not a campaign folder")
            sys.exit(1)
        return list_campaign_sessions(target)
    if not is_session_dir(target):
        if is_campaign_dir(target):
            print(f"ERROR: {target} is a campaign folder — add --all "
                  "to apply every session.")
        else:
            print(f"ERROR: {target} is not a session folder.")
        sys.exit(1)
    return [target]


def print_change_summary(change_log):
    """Group the change log by node_id and print a compact summary."""
    by_node = {}
    for rec in change_log:
        by_node.setdefault(rec["node_id"], []).append(rec)

    if not by_node:
        print("  (no changes)")
        return

    for nid in sorted(by_node):
        recs = by_node[nid]
        effects = []
        for r in recs:
            tag = f"[{r['session']}] {r['section']}: {r['effect']}"
            effects.append(tag)
        print(f"  {nid}")
        for e in effects:
            print(f"    - {e}")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Merge revised nodes from an audit campaign back into "
            "data.json. Backs up to data.json.bak before writing."
        )
    )
    parser.add_argument(
        "target",
        help="Path to a session folder, or — with --all — a campaign folder.",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Apply every session in the campaign (plan order).",
    )
    parser.add_argument(
        "--data", default=None,
        help=f"Path to data.json (default: {DEFAULT_DATA_FILE}).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Report what would change; don't touch data.json.",
    )
    parser.add_argument(
        "--no-backup", action="store_true",
        help="Skip writing data.json.bak before overwriting (not recommended).",
    )
    args = parser.parse_args()

    data_file = args.data or DEFAULT_DATA_FILE

    sessions = collect_sessions(args.target, args.all)
    print(f"Sessions to apply: {len(sessions)}")
    for s in sessions:
        print(f"  - {os.path.basename(s)}")

    # Loud-fail on corrupt or malformed data.json before doing any work.
    # Catching this here (rather than letting json.load raise a bare
    # traceback) is what we owe the user when the whole run is about
    # to write back to this same file.
    data = load_data_json(data_file)
    nodes = data["nodes"]
    nodes_by_id = {n["id"]: n for n in nodes}
    print(f"data.json: {data_file} ({len(nodes)} nodes)")

    change_log = []
    totals = {"applied": 0, "skipped": 0, "warnings": 0}
    for session_dir in sessions:
        packet = load_packet(session_dir)
        revised = load_revised_nodes(session_dir)
        print(f"\n── {os.path.basename(session_dir)} "
              f"(section={packet.get('section')}, "
              f"revised files={len(revised)}) ──")
        if not revised:
            print("  (no revised/*.json found — did you run run_audit.py? "
                  "Skipping.)")
            continue
        stats = apply_session(nodes_by_id, session_dir, packet, revised,
                              change_log)
        print(f"  applied={stats['applied']}, skipped={stats['skipped']}, "
              f"warnings={stats['warnings']}")
        for k in totals:
            totals[k] += stats[k]

    print(f"\nTotals: applied={totals['applied']}, "
          f"skipped={totals['skipped']}, warnings={totals['warnings']}")
    print(f"Unique nodes touched: "
          f"{len({r['node_id'] for r in change_log})}")

    print("\nChange summary (per node):")
    print_change_summary(change_log)

    if args.dry_run:
        print(f"\n(--dry-run: data.json NOT modified.)")
        return

    if totals["applied"] == 0:
        print("\nNo revisions applied. Not writing data.json.")
        return

    if not args.no_backup:
        backup = data_file + ".bak"
        shutil.copy2(data_file, backup)
        print(f"\nBackup: {backup}")

    # Atomic: write to <data_file>.tmp, then os.replace. A crash
    # between json.dump and rename cannot leave data.json half-written.
    write_json_atomic(data_file, data)
    print(f"Wrote: {data_file}")


if __name__ == "__main__":
    main()
