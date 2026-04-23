#!/usr/bin/env python3
"""
verify_roundtrip.py — Confirm decompose → compose produces a data.json
that matches the source, so we know the per-node tree is a faithful
representation and nothing gets lost in the round-trip.

This is a safety check to run after migrating, after any schema
changes to node files, or any time you want to be sure `compose` and
`decompose` still agree. It does NOT modify your real data.json or
your real ai_dev/nodes/ — everything happens in a temp folder.

Usage:
    python verify_roundtrip.py                 # uses Website/data.json
    python verify_roundtrip.py --data PATH     # alternate source
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile

from _common import utf8_subprocess_kwargs, tree_sort_key


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_DEV_DIR = os.path.dirname(SCRIPT_DIR)
WEBSITE_DIR = os.path.dirname(AI_DEV_DIR)
DEFAULT_DATA_FILE = os.path.join(WEBSITE_DIR, "data.json")


def _run(cmd):
    """Run a subcommand; fail loud with its stderr on non-zero exit."""
    r = subprocess.run(
        cmd,
        capture_output=True,
        **utf8_subprocess_kwargs(),
    )
    if r.returncode != 0:
        print(f"ERROR: {' '.join(cmd)}", file=sys.stderr)
        if r.stdout:
            print(r.stdout, file=sys.stderr)
        if r.stderr:
            print(r.stderr, file=sys.stderr)
        sys.exit(r.returncode)
    return r.stdout


def _first_diff(a, b, path="$"):
    """Walk two JSON values and return a path+explanation for the
    first structural difference, or None if they're equivalent.
    Works on dicts, lists, and scalars — preserves key order implicitly
    (dicts compare by keys set + per-key recursion)."""
    if type(a) is not type(b):
        return f"{path}: type mismatch — {type(a).__name__} vs {type(b).__name__}"
    if isinstance(a, dict):
        keys_a, keys_b = set(a), set(b)
        only_a = keys_a - keys_b
        only_b = keys_b - keys_a
        if only_a:
            return f"{path}: keys in source only — {sorted(only_a)[:5]}"
        if only_b:
            return f"{path}: keys in rebuilt only — {sorted(only_b)[:5]}"
        for k in a:
            sub = _first_diff(a[k], b[k], f"{path}.{k}")
            if sub:
                return sub
        return None
    if isinstance(a, list):
        if len(a) != len(b):
            return f"{path}: length {len(a)} vs {len(b)}"
        for i, (av, bv) in enumerate(zip(a, b)):
            sub = _first_diff(av, bv, f"{path}[{i}]")
            if sub:
                return sub
        return None
    if a != b:
        # Truncate long scalar diffs so the error stays readable.
        sa, sb = repr(a), repr(b)
        if len(sa) > 80:
            sa = sa[:77] + "..."
        if len(sb) > 80:
            sb = sb[:77] + "..."
        return f"{path}: {sa} != {sb}"
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Round-trip check: decompose → compose → diff."
    )
    parser.add_argument(
        "--data", default=DEFAULT_DATA_FILE,
        help=f"Source data.json (default: {DEFAULT_DATA_FILE})",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.data):
        print(f"ERROR: source not found: {args.data}", file=sys.stderr)
        sys.exit(1)

    python = sys.executable or "python3"
    decompose = os.path.join(SCRIPT_DIR, "decompose_data.py")
    compose = os.path.join(SCRIPT_DIR, "compose_data.py")

    # All scratch work stays in a temp folder so the user's real
    # ai_dev/nodes/ and real data.json are untouched.
    with tempfile.TemporaryDirectory(prefix="roundtrip_") as tmp:
        tmp_nodes = os.path.join(tmp, "nodes")
        tmp_data = os.path.join(tmp, "rebuilt.json")

        print(f"  [1/3] decompose {args.data} → {tmp_nodes}")
        _run([python, decompose, "--data", args.data, "--out", tmp_nodes])

        print(f"  [2/3] compose   {tmp_nodes} → {tmp_data}")
        _run([python, compose, "--in", tmp_nodes, "--data", tmp_data,
              "--no-backup"])

        print(f"  [3/3] diff source vs rebuilt")
        with open(args.data, "r", encoding="utf-8") as f:
            src = json.load(f)
        with open(tmp_data, "r", encoding="utf-8") as f:
            rebuilt = json.load(f)

    # compose always emits tree-sorted node order. If the source
    # wasn't already in that order, a raw position-by-position diff
    # would be noisy about something intentional. Normalize both
    # sides to canonical order — what we actually care about here is
    # "is every node preserved with all its fields intact."
    if isinstance(src.get("nodes"), list):
        src["nodes"] = sorted(src["nodes"], key=tree_sort_key)
    if isinstance(rebuilt.get("nodes"), list):
        rebuilt["nodes"] = sorted(rebuilt["nodes"], key=tree_sort_key)

    diff = _first_diff(src, rebuilt)
    if diff is None:
        src_nodes = len(src.get("nodes", []))
        print(f"\nOK — round-trip matches. {src_nodes} nodes preserved.")
        return

    print("\nMISMATCH — first structural difference:")
    print(f"  {diff}")
    print("\nThat means decompose+compose is NOT lossless for this data. "
          "Investigate before trusting the new workflow.")
    sys.exit(2)


if __name__ == "__main__":
    main()
