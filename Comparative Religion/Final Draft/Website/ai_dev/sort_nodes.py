#!/usr/bin/env python3
"""
sort_nodes.py — Sort nodes in data.json by ID in proper tree order.

Usage:
    python sort_nodes.py
    python sort_nodes.py --check   # just report out-of-order nodes, don't fix
"""

import json
import os
import sys
import shutil
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(os.path.dirname(SCRIPT_DIR), "data.json")


def id_sort_key(node_id: str) -> tuple:
    """Convert '1.2.5.4' into a tuple for proper numeric sorting.
    Each part becomes (0, int, '') for numeric or (1, 0, str) for non-numeric."""
    parts = []
    for p in node_id.split("."):
        try:
            parts.append((0, int(p), ""))
        except ValueError:
            parts.append((1, 0, p))
    return tuple(parts)


def main():
    parser = argparse.ArgumentParser(description="Sort nodes in data.json by ID.")
    parser.add_argument("--check", action="store_true",
                        help="Only check for out-of-order nodes, don't modify")
    parser.add_argument("--data", default=None, help="Path to data.json")
    args = parser.parse_args()

    data_file = args.data or DATA_FILE

    if not os.path.exists(data_file):
        print(f"ERROR: {data_file} not found")
        sys.exit(1)

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data["nodes"]
    # Breadth-first: sort by depth first, then by ID within each depth
    sorted_nodes = sorted(nodes, key=lambda n: (len(n["id"].split(".")), id_sort_key(n["id"])))

    # Find out-of-order nodes
    out_of_order = []
    for i, (original, correct) in enumerate(zip(nodes, sorted_nodes)):
        if original["id"] != correct["id"]:
            out_of_order.append((i, original["id"], correct["id"]))

    if not out_of_order:
        print(f"All {len(nodes)} nodes are already in order.")
        return

    print(f"Found {len(out_of_order)} nodes out of position.\n")

    # Show first few mismatches
    for pos, was, should_be in out_of_order[:10]:
        print(f"  Position {pos}: has {was}, should be {should_be}")
    if len(out_of_order) > 10:
        print(f"  ... and {len(out_of_order) - 10} more")

    if args.check:
        print("\nRun without --check to fix.")
        return

    # Backup and write
    backup = data_file + ".bak"
    shutil.copy2(data_file, backup)
    print(f"\nBackup saved: {backup}")

    data["nodes"] = sorted_nodes
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Sorted {len(nodes)} nodes. Done.")


if __name__ == "__main__":
    main()
