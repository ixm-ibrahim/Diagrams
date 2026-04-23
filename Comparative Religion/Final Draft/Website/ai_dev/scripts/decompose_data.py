#!/usr/bin/env python3
"""
decompose_data.py — Explode data.json into an editable one-file-per-node tree.

Each node gets its own JSON file, nested by the dot-parts of its id:

    ai_dev/nodes/
      1/
        1.json                       ← node 1
        1/
          1.1.json                   ← node 1.1
          1/
            1.1.1.json               ← node 1.1.1
        2/
          1.2.json                   ← node 1.2
        ...

Filename = the full dotted id so it's unambiguous at a glance and grep-
friendly. Folder path = id parts so selecting a subfolder selects a
sub-tree (e.g. `nodes/1/2/5/` is everything rooted at 1.2.5).

Any top-level keys in data.json that AREN'T `nodes` are preserved in
`nodes/_meta.json` so compose_data.py can rebuild a byte-identical file.

Usage:
    python decompose_data.py               # writes to ai_dev/nodes/
    python decompose_data.py --force       # wipe existing nodes/ first
    python decompose_data.py --data PATH   # alternate data.json source
    python decompose_data.py --out PATH    # alternate output folder
"""

import argparse
import json
import os
import shutil
import sys

from _common import die, load_data_json


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))   # ai_dev/scripts
AI_DEV_DIR = os.path.dirname(SCRIPT_DIR)                  # ai_dev
WEBSITE_DIR = os.path.dirname(AI_DEV_DIR)                 # Website root
DEFAULT_DATA_FILE = os.path.join(WEBSITE_DIR, "data.json")
DEFAULT_OUT_DIR = os.path.join(AI_DEV_DIR, "nodes")

# Everything that isn't a node lives here so compose can restore it.
META_FILENAME = "_meta.json"


def node_paths(out_dir, node_id):
    """Return (folder, file_path) for the node's on-disk location.

    Node 1.2.5.4 → (out_dir/1/2/5/4, out_dir/1/2/5/4/1.2.5.4.json)"""
    parts = node_id.split(".")
    folder = os.path.join(out_dir, *parts)
    return folder, os.path.join(folder, f"{node_id}.json")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Decompose data.json into a nested one-file-per-node tree. "
            "Intended for editing; compose_data.py rebuilds data.json "
            "from the tree."
        )
    )
    parser.add_argument(
        "--data", default=DEFAULT_DATA_FILE,
        help=f"Path to data.json (default: {DEFAULT_DATA_FILE})",
    )
    parser.add_argument(
        "--out", default=DEFAULT_OUT_DIR,
        help=f"Output folder (default: {DEFAULT_OUT_DIR})",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="If the output folder exists, wipe it before writing.",
    )
    args = parser.parse_args()

    # Validated load — corrupt/missing/duplicate-id data.json bails
    # with a clear one-liner (see _common.load_data_json).
    data = load_data_json(args.data)
    nodes = data["nodes"]
    print(f"Loaded: {args.data}  ({len(nodes)} nodes)")

    # Refuse to clobber a populated output folder unless --force.
    # Unambiguous: either it's empty and we own it, or the user has
    # signed off on the wipe.
    if os.path.isdir(args.out) and os.listdir(args.out):
        if not args.force:
            die(
                f"Output folder already has content: {args.out} — "
                f"pass --force to wipe and rewrite."
            )
        print(f"Wiping: {args.out}")
        shutil.rmtree(args.out)

    os.makedirs(args.out, exist_ok=True)

    # Preserve every non-`nodes` top-level key so compose can restore
    # the exact data.json shape. Today data.json might only have
    # `nodes`, but this keeps the round-trip honest if that ever
    # changes (schema version, a top-level title, etc.).
    meta = {k: v for k, v in data.items() if k != "nodes"}
    meta_path = os.path.join(args.out, META_FILENAME)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    if meta:
        print(f"Wrote meta ({len(meta)} key(s)): {meta_path}")
    else:
        print(f"Wrote meta (empty): {meta_path}")

    # Write each node into its computed path.
    written = 0
    skipped = 0
    for n in nodes:
        nid = n.get("id")
        if not nid:
            die(f"Node at index {written + skipped} has no id — "
                f"file: {args.data}")
        folder, path = node_paths(args.out, nid)
        os.makedirs(folder, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(n, f, indent=2, ensure_ascii=False)
        written += 1

    print(f"Wrote {written} node files under {args.out}")
    print()
    print("Next: edit individual files, or point Cowork at a sub-tree")
    print("(e.g. ai_dev/nodes/1/2/5/). When ready, run compose_data.py")
    print("to rebuild data.json.")


if __name__ == "__main__":
    main()
