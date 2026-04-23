#!/usr/bin/env python3
"""
sort_nodes.py — Deduplicate (keeping the most-worked-on copy of each id)
and sort nodes in data.json into proper tree order.

If two nodes share an id, we keep the copy with more content. "More
content" is a simple character count on the node's serialized JSON —
the node that has more text in it is the one someone spent more time
on. Ties break toward whichever appears first.

Usage:
    python sort_nodes.py                # dedupe + sort in place (with backup)
    python sort_nodes.py --check        # report duplicates + out-of-order, don't modify
    python sort_nodes.py --data PATH    # operate on a specific data.json
"""

import argparse
import json
import os
import shutil
import sys
from collections import defaultdict

from _common import (
    load_data_json,
    write_json_atomic,
    id_sort_key,
    tree_sort_key,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))   # ai_dev/scripts
# data.json lives at the Website root — two parents up from ai_dev/scripts/.
DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(SCRIPT_DIR)), "data.json"
)


# ─────────────────────────────────────────────────────────────────────
# Sorting
# ─────────────────────────────────────────────────────────────────────
# `id_sort_key` and `tree_sort_key` live in _common.py so every script
# that writes data.json (sort_nodes, compose_data) uses the exact same
# order — otherwise round-trips would churn on every rebuild.

def tree_sort(nodes):
    return sorted(nodes, key=tree_sort_key)


# ─────────────────────────────────────────────────────────────────────
# Deduplication
# ─────────────────────────────────────────────────────────────────────

def content_size(node) -> int:
    """Rough proxy for 'how much work is in this node': length of its
    serialized JSON. Not perfect — two revisions of the same content
    can differ in length by a couple chars — but it reliably picks the
    filled-in version over a bare stub, which is the only case this
    script can't resolve by hand."""
    return len(json.dumps(node, ensure_ascii=False))


def dedupe_by_id(nodes):
    """Within each group of same-id nodes, keep the one with the most
    content and drop the rest.

    Returns (kept_nodes, drop_log) where `drop_log` is a list of dicts
    describing each removed duplicate, in the original node order."""
    groups = defaultdict(list)
    for i, n in enumerate(nodes):
        groups[n["id"]].append((i, n))

    kept_by_original_idx = {}   # preserve original ordering for the survivors
    drop_log = []

    for nid, items in groups.items():
        if len(items) == 1:
            orig_idx, node = items[0]
            kept_by_original_idx[orig_idx] = node
            continue

        # Rank: biggest first, original-index as stable tiebreaker so
        # "equal size" picks the earlier copy deterministically.
        ranked = sorted(
            items,
            key=lambda t: (-content_size(t[1]), t[0]),
        )
        winner_idx, winner_node = ranked[0]
        kept_by_original_idx[winner_idx] = winner_node

        winner_size = content_size(winner_node)
        for loser_idx, loser_node in ranked[1:]:
            drop_log.append({
                "id": nid,
                "kept_index": winner_idx,
                "kept_chars": winner_size,
                "dropped_index": loser_idx,
                "dropped_chars": content_size(loser_node),
            })

    # Return survivors in original order so the subsequent sort step's
    # "what moved" diff is meaningful.
    kept = [kept_by_original_idx[i] for i in sorted(kept_by_original_idx)]
    return kept, drop_log


# ─────────────────────────────────────────────────────────────────────
# Reporting
# ─────────────────────────────────────────────────────────────────────

def print_drop_log(drop_log):
    if not drop_log:
        return
    # Group by id for readability (one id can have 3+ duplicates).
    by_id = defaultdict(list)
    for rec in drop_log:
        by_id[rec["id"]].append(rec)

    print(f"Duplicate ids: {len(by_id)} "
          f"({len(drop_log)} extra copies to drop)")
    for nid in sorted(by_id, key=id_sort_key):
        recs = by_id[nid]
        winner_chars = recs[0]["kept_chars"]
        print(f"  {nid}: keeping index {recs[0]['kept_index']} "
              f"({winner_chars:,} chars)")
        for r in recs:
            delta = r["kept_chars"] - r["dropped_chars"]
            rel = (
                "smaller" if delta > 0
                else ("larger" if delta < 0 else "equal")
            )
            print(f"    - drop index {r['dropped_index']} "
                  f"({r['dropped_chars']:,} chars, {rel} by {abs(delta):,})")


def print_move_log(out_of_order, limit=10):
    print(f"Out-of-order nodes: {len(out_of_order)}")
    for pos, was, should_be in out_of_order[:limit]:
        print(f"  Position {pos}: has {was}, should be {should_be}")
    if len(out_of_order) > limit:
        print(f"  ... and {len(out_of_order) - limit} more")


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Deduplicate and sort nodes in data.json. Duplicates are "
            "resolved by keeping the copy with the most content "
            "(longest serialized JSON)."
        )
    )
    parser.add_argument("--check", action="store_true",
                        help="Report duplicates + out-of-order nodes; don't modify.")
    parser.add_argument("--data", default=None, help="Path to data.json")
    args = parser.parse_args()

    data_file = args.data or DATA_FILE

    # Load with duplicate-check disabled — duplicates are this script's
    # whole reason to exist. Every OTHER structural problem still
    # aborts cleanly (see `_common.load_data_json`).
    data = load_data_json(data_file, allow_duplicates=True)
    original = data["nodes"]
    print(f"Loaded: {data_file}  ({len(original)} nodes)")

    # Pass 1 — dedupe by id.
    deduped, drop_log = dedupe_by_id(original)
    if drop_log:
        print()
        print_drop_log(drop_log)
    else:
        print("  No duplicate ids.")

    # Pass 2 — sort the survivors.
    sorted_nodes = tree_sort(deduped)
    out_of_order = [
        (i, deduped[i]["id"], sorted_nodes[i]["id"])
        for i in range(len(deduped))
        if deduped[i]["id"] != sorted_nodes[i]["id"]
    ]
    print()
    if out_of_order:
        print_move_log(out_of_order)
    else:
        print("  All nodes are already in order.")

    # Anything to do?
    if not drop_log and not out_of_order:
        print("\nNothing to change.")
        return

    if args.check:
        print("\n(--check: data.json NOT modified.)")
        return

    # Backup + atomic write.
    backup = data_file + ".bak"
    shutil.copy2(data_file, backup)
    print(f"\nBackup saved: {backup}")

    data["nodes"] = sorted_nodes
    write_json_atomic(data_file, data)

    final_count = len(sorted_nodes)
    dropped_count = len(original) - final_count
    print(f"Wrote {final_count} nodes "
          f"(dropped {dropped_count} duplicate(s), "
          f"reordered {len(out_of_order)}). Done.")


if __name__ == "__main__":
    main()
