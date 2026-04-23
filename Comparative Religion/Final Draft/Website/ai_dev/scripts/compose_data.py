#!/usr/bin/env python3
"""
compose_data.py — Rebuild data.json from the ai_dev/nodes/ tree.

Walks every `<id>.json` under ai_dev/nodes/, verifies the id inside
each file matches its filename AND folder path (catches hand-edits
that rename the file but forget the `id` field, or vice versa),
sorts the collected list using the canonical tree order from
`_common.tree_sort_key` (same order sort_nodes.py writes), and
atomically writes the result to data.json.

nodes/_meta.json is merged back in as the top-level non-`nodes` keys,
so the output is structurally a faithful rebuild of the original.

Usage:
    python compose_data.py                     # rebuild data.json in place
    python compose_data.py --dry-run           # report what would be written
    python compose_data.py --in PATH           # alternate nodes/ folder
    python compose_data.py --data PATH         # alternate output data.json
    python compose_data.py --no-backup         # skip data.json.bak
"""

import argparse
import json
import os
import shutil
import sys

from _common import (
    die,
    load_json,
    write_json_atomic,
    tree_sort_key,
)


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))   # ai_dev/scripts
AI_DEV_DIR = os.path.dirname(SCRIPT_DIR)                  # ai_dev
WEBSITE_DIR = os.path.dirname(AI_DEV_DIR)                 # Website root
DEFAULT_DATA_FILE = os.path.join(WEBSITE_DIR, "data.json")
DEFAULT_IN_DIR = os.path.join(AI_DEV_DIR, "nodes")

META_FILENAME = "_meta.json"


def collect_nodes(nodes_dir):
    """Walk `nodes_dir` and return every node as (id, node_dict).

    Validates aggressively: filename must match id, folder path must
    match id parts. A mismatch here means someone edited one side
    without updating the other — if we silently picked one over the
    other, compose would produce a wrong data.json and the next
    decompose would revert the edit. Fail loud instead."""
    found = []
    for dirpath, _, filenames in os.walk(nodes_dir):
        for name in filenames:
            if name == META_FILENAME or not name.endswith(".json"):
                continue
            path = os.path.join(dirpath, name)
            node = load_json(path, what=name)

            if not isinstance(node, dict):
                die(f"Node file must contain a JSON object: {path}")
            nid = node.get("id")
            if not nid:
                die(f"Node file has no 'id' field: {path}")

            # Filename must match the id so hand-editing the id without
            # renaming the file (or vice versa) can't produce a silent
            # mis-merge.
            if name != f"{nid}.json":
                die(
                    f"Filename/id mismatch: file is '{name}' but the "
                    f"node's id is '{nid}' — path: {path}. "
                    f"Rename the file to '{nid}.json' or fix the id."
                )

            # Folder path must match id parts. Split the relative dir
            # into its components and compare to the id's dotted parts.
            rel_dir = os.path.relpath(dirpath, nodes_dir)
            # Normalize to forward-slash for comparison (Windows).
            rel_parts = [] if rel_dir == "." else rel_dir.replace("\\", "/").split("/")
            expected_parts = nid.split(".")
            if rel_parts != expected_parts:
                die(
                    f"Path/id mismatch: node '{nid}' found at "
                    f"'{'/'.join(rel_parts) or '.'}' "
                    f"(expected '{'/'.join(expected_parts)}') — "
                    f"path: {path}"
                )
            found.append(node)
    return found


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compose the nodes/ tree back into a single data.json. "
            "Use after editing individual node files."
        )
    )
    parser.add_argument(
        "--in", dest="input_dir", default=DEFAULT_IN_DIR,
        help=f"Nodes folder (default: {DEFAULT_IN_DIR})",
    )
    parser.add_argument(
        "--data", default=DEFAULT_DATA_FILE,
        help=f"Output data.json (default: {DEFAULT_DATA_FILE})",
    )
    parser.add_argument(
        "--no-backup", action="store_true",
        help="Skip writing data.json.bak before overwriting.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Report what would be written; don't touch disk.",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        die(f"Nodes folder not found: {args.input_dir} — "
            f"run decompose_data.py first.")

    # Meta is optional; it's an empty dict today but the round-trip
    # carries whatever was at the top-level alongside `nodes`.
    meta_path = os.path.join(args.input_dir, META_FILENAME)
    if os.path.exists(meta_path):
        meta = load_json(meta_path, what=META_FILENAME)
        if not isinstance(meta, dict):
            die(f"{META_FILENAME} must be a JSON object — path: {meta_path}")
    else:
        meta = {}
        print(f"Note: no {META_FILENAME} found — output will only have 'nodes' key.")

    nodes = collect_nodes(args.input_dir)
    if not nodes:
        die(f"No node files found under {args.input_dir}")

    # Duplicate check. collect_nodes already validates filename and
    # path match id, so a duplicate id here means the user created
    # two parallel folder paths by hand — unusual but worth calling out.
    seen_ids = {}
    for n in nodes:
        nid = n["id"]
        if nid in seen_ids:
            die(
                f"Duplicate node id '{nid}' in nodes tree — "
                f"shouldn't happen if filenames and paths match ids."
            )
        seen_ids[nid] = True

    # Canonical order — same as sort_nodes.py.
    nodes.sort(key=tree_sort_key)
    print(f"Collected: {len(nodes)} nodes from {args.input_dir}")
    if meta:
        print(f"Meta keys: {list(meta)}")

    # Meta first, then nodes — so the output has nodes after any
    # top-level fields, which matches how data.json looks today.
    merged = dict(meta)
    merged["nodes"] = nodes

    if args.dry_run:
        print(f"\n(--dry-run: would write {args.data} "
              f"with {len(nodes)} nodes.)")
        return

    if not args.no_backup and os.path.exists(args.data):
        backup = args.data + ".bak"
        shutil.copy2(args.data, backup)
        print(f"Backup: {backup}")

    write_json_atomic(args.data, merged)
    print(f"Wrote: {args.data}")


if __name__ == "__main__":
    main()
