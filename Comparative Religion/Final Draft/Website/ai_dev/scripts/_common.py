"""Shared helpers used by every audit-pipeline script.

The job of this module is to fail LOUDLY and EARLY on the conditions that
have bitten us in practice — corrupt data.json, missing keys, non-atomic
writes that can leave data.json half-written, subprocess pipes that use
the host's default encoding. Nothing here is clever; it is all about
turning silent failures into a one-line error that names the offender.
"""

import json
import os
import sys
import tempfile


# ─────────────────────────────────────────────────────────────────────
# Loading — parse errors become a single clear line, not a traceback
# ─────────────────────────────────────────────────────────────────────

def die(msg, code=2):
    """Print a one-line error and exit. Used for unrecoverable states
    (corrupt file, missing required structure). Every call site should
    name the offending file so the user can go fix it directly."""
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def load_json(path, what=None):
    """Load a JSON file, exiting cleanly with file + position on parse
    failure. `what` is a human label for the file role (e.g.
    'data.json', 'PACKET.json') — defaults to the path."""
    label = what or path
    if not os.path.exists(path):
        die(f"{label} not found at: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        die(
            f"{label} is not valid JSON: {e.msg} "
            f"(line {e.lineno}, column {e.colno}, char {e.pos}) — "
            f"file: {path}"
        )
    except OSError as e:
        die(f"{label} could not be read: {e} — file: {path}")


def load_data_json(path, *, allow_duplicates=False):
    """Load + structurally validate the main data.json. Fails loud on:
       - invalid JSON
       - top-level not an object
       - missing 'nodes' key, or 'nodes' not a list
       - any node missing 'id'
       - duplicate node ids (unless `allow_duplicates=True`)
    Returns the parsed dict (with a validated `data['nodes']` list).

    `allow_duplicates=True` is for tools whose job is to clean up
    duplicates (sort_nodes.py). Everywhere else, duplicates are a bug
    we want to catch at the door."""
    data = load_json(path, what="data.json")
    if not isinstance(data, dict):
        die(f"data.json top-level must be an object, got {type(data).__name__} — file: {path}")
    if "nodes" not in data:
        die(f"data.json is missing required key 'nodes' — file: {path}")
    nodes = data["nodes"]
    if not isinstance(nodes, list):
        die(f"data.json 'nodes' must be a list, got {type(nodes).__name__} — file: {path}")
    seen = {}
    for i, n in enumerate(nodes):
        if not isinstance(n, dict):
            die(f"data.json node at index {i} is not an object — file: {path}")
        nid = n.get("id")
        if not nid:
            die(f"data.json node at index {i} has no 'id' — file: {path}")
        if nid in seen and not allow_duplicates:
            die(
                f"data.json has duplicate node id '{nid}' at indices "
                f"{seen[nid]} and {i} — file: {path}"
            )
        seen[nid] = i
    return data


# ─────────────────────────────────────────────────────────────────────
# Writing — never leave data.json half-written
# ─────────────────────────────────────────────────────────────────────

def write_json_atomic(path, data, indent=2):
    """Write JSON to `path` atomically: serialize to a sibling `.tmp`
    file, fsync, then `os.replace` onto the target. If serialization
    fails midway, `path` is untouched. If the move fails, `path` is
    still untouched (the temp is left for inspection).

    This matters because data.json is the whole tree — a truncated write
    makes the site unbootable and erases real content."""
    directory = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(directory, exist_ok=True)
    # delete=False so we control the lifecycle (os.replace handles it).
    fd, tmp_path = tempfile.mkstemp(
        prefix=os.path.basename(path) + ".",
        suffix=".tmp",
        dir=directory,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                # fsync can fail on some filesystems (e.g. network FS);
                # not fatal — the replace is still atomic on a single FS.
                pass
        os.replace(tmp_path, path)
    except Exception:
        # Serialization or replace failed — clean up the temp so we
        # don't leave litter. `path` itself is still the pre-write file.
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass
        raise


# ─────────────────────────────────────────────────────────────────────
# Tree ordering — the one canonical sort, shared by every script
# ─────────────────────────────────────────────────────────────────────
#
# Breadth-first by depth, then by id within each depth. If any script
# ever disagrees with another on this order, data.json diffs would
# churn on every rebuild. Keep the definition in one place.

def id_sort_key(node_id):
    """Convert '1.2.5.4' into a sort-friendly tuple. Numeric parts
    compare as numbers (not strings, so 10 sorts after 9); non-numeric
    parts sort after numeric ones at the same depth."""
    parts = []
    for p in node_id.split("."):
        try:
            parts.append((0, int(p), ""))
        except ValueError:
            parts.append((1, 0, p))
    return tuple(parts)


def tree_sort_key(node):
    """Node-list sort key: shallower first, then by id within depth."""
    nid = node["id"]
    return (len(nid.split(".")), id_sort_key(nid))


# ─────────────────────────────────────────────────────────────────────
# Subprocess — UTF-8 everywhere, loud on non-UTF-8 output
# ─────────────────────────────────────────────────────────────────────

def utf8_subprocess_kwargs(strict=False):
    """Keyword args to splat into subprocess.run/Popen so stdin/stdout/
    stderr are UTF-8 on every platform. Prevents the Windows cp1252
    crash we hit on '→' in the reference files.

    `strict=True` raises on non-UTF-8 bytes from the child; default
    `replace` swaps them for `?` so a stray byte in the child's output
    doesn't take down the run. Input (stdin) is always strict because
    we control it — if our own text isn't UTF-8, that's a bug to fix,
    not hide."""
    return {
        "text": True,
        "encoding": "utf-8",
        "errors": "strict" if strict else "replace",
    }
