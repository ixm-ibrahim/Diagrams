#!/usr/bin/env python3
"""
run_audit.py — Execute an audit packet (or a whole campaign) through
Claude CLI and save the revised node JSONs alongside the packet.

Reads the session folder produced by `plan_audit.py`, runs `claude -p`
with access to AUDIT_PROMPT.md and AUDIT_CONTEXT.md, captures the raw
response, extracts every ```json``` fenced block, and writes each one
as `<session_dir>/revised/<node_id>.json`. Also saves
`<session_dir>/RAW_RESPONSE.md` for review.

The chat prompt says "one node per response, wait for confirmation." In
non-interactive runner mode that would deadlock, so this script injects
a BATCH MODE override telling the AI to emit every audited node in a
single response.

Usage:
    # Single packet
    python run_audit.py ../outputs/audits/1.1/01_all

    # Whole campaign, in plan order
    python run_audit.py ../outputs/audits/1.1 --all

    # See what would be sent to Claude without actually calling it
    python run_audit.py ../outputs/audits/1.1/01_all --dry-run

    # Manual mode: paste the chat response on stdin, parse + save
    # (skip the CLI; useful if you still want to use the web chat)
    python run_audit.py ../outputs/audits/1.1/01_all --manual < response.md

Options:
    --model        opus | sonnet | haiku (default: opus)
    --timeout      seconds for each claude-p call (default: 600)
    --overwrite    overwrite existing revised/*.json if present
    --all          treat the target path as a campaign root and run
                   every session subfolder in plan order
    --dry-run      print the composed prompt + CLI command, don't run
    --manual       read the response from stdin instead of calling CLI
"""

import argparse
import json
import os
import re
import subprocess
import sys

from _common import die, load_json, utf8_subprocess_kwargs


# ─────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))   # ai_dev/scripts
AI_DEV_DIR = os.path.dirname(SCRIPT_DIR)                  # ai_dev


# ─────────────────────────────────────────────────────────────────────
# Batch-mode rider
# ─────────────────────────────────────────────────────────────────────
#
# The chat prompt says "Do ONE node per response ... Wait for my
# confirmation". In non-interactive CLI mode that would block forever,
# so we prepend this rider that overrides the pacing instruction and
# pins the output shape to a parseable multi-block response.

BATCH_RIDER = """\
# RUNNER OVERRIDE — READ THIS FIRST

You are running in an automated audit runner (invoked via `claude -p`).
There is NO human waiting to say "next" between nodes.

**Override the pacing instruction in AUDIT_PROMPT.md below.** Do not
stop after one node. Emit EVERY node in the audit queue in this single
response. For each node, include the full Audit Report, Summary, and
a ```json``` fenced block containing the complete revised node object,
exactly as described in AUDIT_PROMPT.md's output format. For focused
passes, also include the Spotted elsewhere list per node.

**Do not ask for confirmation. Do not wait.** When the last node in the
queue has been emitted, stop.

The context file AUDIT_CONTEXT.md is in the current working directory
— read it before you begin. AUDIT_PROMPT.md is also in the current
working directory and contains the rest of the task description.

---

"""


# ─────────────────────────────────────────────────────────────────────
# Session-folder helpers
# ─────────────────────────────────────────────────────────────────────

def is_session_dir(path):
    """A session dir has AUDIT_PROMPT.md + AUDIT_CONTEXT.md + PACKET.json."""
    return all(
        os.path.isfile(os.path.join(path, f))
        for f in ("AUDIT_PROMPT.md", "AUDIT_CONTEXT.md", "PACKET.json")
    )


def is_campaign_dir(path):
    """A campaign dir has 00_plan.md and at least one session subfolder."""
    if not os.path.isfile(os.path.join(path, "00_plan.md")):
        return False
    for name in os.listdir(path):
        sub = os.path.join(path, name)
        if os.path.isdir(sub) and is_session_dir(sub):
            return True
    return False


def list_campaign_sessions(campaign_dir):
    """Return session subfolders under a campaign dir, ordered by the
    numeric prefix (01_..., 02_..., ...)."""
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


# ─────────────────────────────────────────────────────────────────────
# Claude CLI invocation
# ─────────────────────────────────────────────────────────────────────

def build_cli_command(session_dir, model, timeout):
    """Compose the `claude -p` command for this packet. The prompt
    itself is passed via stdin — the --add-dir gives the model Read
    access to the session folder so it can open AUDIT_CONTEXT.md and
    AUDIT_PROMPT.md directly."""
    cmd = [
        "claude", "-p",
        "--model", model,
        "--allowedTools", "Read", "Grep", "Glob",
        "--add-dir", session_dir,
    ]
    # --no-session-persistence may or may not be present depending on
    # Claude CLI version; harmless if unrecognized will error, so we
    # probe by feature flag below in main().
    return cmd


def _save_partial(session_dir, label, stdout, stderr):
    """Dump whatever Claude wrote before being killed / erroring out.
    A timeout with no record is useless — you can't tell if the CLI was
    making progress, stuck on input, or hit an API error halfway."""
    path = os.path.join(session_dir, "RAW_RESPONSE.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"<!-- {label} — partial capture -->\n\n")
        f.write("## stdout\n\n")
        f.write(stdout or "(empty)\n")
        if stderr:
            f.write("\n\n## stderr\n\n")
            f.write(stderr)
    return path


def _tail(text, lines):
    """Last `lines` lines of text, for a compact error print."""
    if not text:
        return "(empty)"
    parts = text.splitlines()
    return "\n".join(parts[-lines:])


def run_claude(session_dir, model, timeout, verbose=True):
    """Invoke `claude -p` on the session packet. Returns stdout string
    on success, None on failure (with error details printed)."""
    # Load prompt + rider. AUDIT_PROMPT.md is small (~5-7K chars);
    # inlining it into stdin keeps things self-contained and avoids a
    # second read by the CLI.
    prompt_path = os.path.join(session_dir, "AUDIT_PROMPT.md")
    with open(prompt_path, "r", encoding="utf-8") as f:
        audit_prompt = f.read()

    full_prompt = BATCH_RIDER + audit_prompt

    cmd = build_cli_command(session_dir, model, timeout)
    if verbose:
        print(f"  $ {' '.join(cmd)}")
        print(f"  (prompt: {len(full_prompt):,} chars, "
              f"timeout: {timeout}s, cwd: {session_dir})")

    try:
        result = subprocess.run(
            cmd,
            input=full_prompt,
            capture_output=True,
            timeout=timeout,
            cwd=session_dir,
            **utf8_subprocess_kwargs(),
        )
    except subprocess.TimeoutExpired as e:
        # TimeoutExpired carries whatever was captured before the kill.
        # Save it so the user can tell if opus was midway through node
        # 4 of 6 (→ bump --timeout) vs. stuck on an auth prompt
        # (→ stderr will show it) vs. genuinely silent (→ rare CLI bug).
        stdout = e.stdout or ""
        stderr = e.stderr or ""
        path = _save_partial(session_dir, "timeout", stdout, stderr)
        print(f"  ERROR: Claude CLI timed out after {timeout}s")
        print(f"  Captured so far: {len(stdout):,} stdout chars, "
              f"{len(stderr):,} stderr chars → {os.path.basename(path)}")
        if stderr.strip():
            print("  stderr (last 10 lines):")
            for line in _tail(stderr, 10).splitlines():
                print(f"    {line}")
        if stdout.strip():
            print("  stdout tail (last 5 lines):")
            for line in _tail(stdout, 5).splitlines():
                print(f"    {line}")
        else:
            print("  stdout: (nothing captured — CLI may be stuck before "
                  "first token; check auth / model availability / network)")
        print(f"  Suggestions: bump --timeout, try --model sonnet, or "
              f"run the command manually to reproduce.")
        return None
    except FileNotFoundError:
        print("  ERROR: `claude` CLI not on PATH. "
              "Run `npm install -g @anthropic-ai/claude-code` or use --manual.")
        return None

    if result.returncode != 0:
        # Save partial output too — failed exit still tells us what
        # came out before the error (rate limit, auth, etc.).
        path = _save_partial(
            session_dir,
            f"exit-{result.returncode}",
            result.stdout,
            result.stderr,
        )
        print(f"  ERROR: Claude CLI exit code {result.returncode} "
              f"→ {os.path.basename(path)}")
        if result.stderr:
            print("  stderr:")
            for line in result.stderr.splitlines()[:20]:
                print(f"    {line}")
        return None

    if not result.stdout.strip():
        path = _save_partial(
            session_dir, "empty-stdout", result.stdout, result.stderr
        )
        print(f"  ERROR: Claude CLI returned empty output "
              f"→ {os.path.basename(path)}")
        if result.stderr:
            print("  stderr:")
            for line in result.stderr.splitlines()[:10]:
                print(f"    {line}")
        return None

    return result.stdout


# ─────────────────────────────────────────────────────────────────────
# Response parsing → per-node revised JSONs
# ─────────────────────────────────────────────────────────────────────

_JSON_BLOCK_RE = re.compile(
    r"```(?:json|jsonc)?\s*\n(?P<body>\{.*?\})\s*\n```",
    re.DOTALL,
)


def extract_revised_nodes(response, packet):
    """Parse every ```json``` fenced block and classify problems.

    Returns (nodes, warnings, fatal) where:
      - `nodes`    = list of parsed revised-node dicts ready to write
      - `warnings` = non-fatal notes (duplicates, out-of-queue extras)
      - `fatal`    = things that mean the run didn't actually succeed,
                     even if some nodes came out — unparseable JSON
                     blocks, blocks without an `id`, and any queued
                     node that never appeared in the response.

    Separating fatal from warning matters because a silent run where
    half the queue is missing produces an empty or partial `revised/`
    folder, and `apply_audit.py` downstream happily skips those nodes.
    The run must fail loud at this boundary."""
    queue_ids = {n["id"] for n in packet.get("audit_queue", [])}
    found = []
    warnings = []
    fatal = []
    seen_ids = set()

    for match in _JSON_BLOCK_RE.finditer(response):
        body = match.group("body").strip()
        try:
            obj = json.loads(body)
        except json.JSONDecodeError as e:
            fatal.append(
                f"Unparseable JSON block at char {match.start()}: "
                f"{e.msg} (line {e.lineno}, col {e.colno})"
            )
            continue

        if not isinstance(obj, dict) or "id" not in obj:
            fatal.append(
                f"JSON block without `id` field at char {match.start()}"
            )
            continue

        node_id = obj["id"]
        if node_id in seen_ids:
            warnings.append(
                f"Duplicate node id {node_id} in response — keeping the first."
            )
            continue
        seen_ids.add(node_id)

        if queue_ids and node_id not in queue_ids:
            warnings.append(
                f"Node {node_id} is in the response but NOT in the packet's "
                "audit queue — keeping it anyway."
            )

        found.append(obj)

    missing = queue_ids - seen_ids
    if missing:
        fatal.append(
            "Audit queue nodes missing from response: "
            + ", ".join(sorted(missing))
        )

    return found, warnings, fatal


def write_revised_nodes(session_dir, nodes, overwrite):
    """Write each revised node to <session_dir>/revised/<id>.json.

    Returns (written, skipped) — ids written and ids that already existed
    and were skipped (when overwrite=False)."""
    revised_dir = os.path.join(session_dir, "revised")
    os.makedirs(revised_dir, exist_ok=True)
    written = []
    skipped = []
    for node in nodes:
        nid = node["id"]
        path = os.path.join(revised_dir, f"{nid}.json")
        if os.path.exists(path) and not overwrite:
            skipped.append(nid)
            continue
        with open(path, "w", encoding="utf-8") as f:
            json.dump(node, f, indent=2, ensure_ascii=False)
        written.append(nid)
    return written, skipped


# ─────────────────────────────────────────────────────────────────────
# One-packet runner
# ─────────────────────────────────────────────────────────────────────

def run_packet(session_dir, args):
    """Run (or dry-run / manual-parse) a single session packet."""
    if not is_session_dir(session_dir):
        print(f"ERROR: {session_dir} is not a valid session folder "
              "(expected AUDIT_PROMPT.md, AUDIT_CONTEXT.md, PACKET.json)")
        return False

    packet = load_packet(session_dir)
    section = packet.get("section", "all")
    targets = ", ".join(packet.get("target_ids", []))
    queue = packet.get("audit_queue", [])
    print(f"\n── Packet: {os.path.basename(session_dir)} ──")
    print(f"  section:     {section}")
    print(f"  target(s):   {targets}")
    print(f"  audit queue: {len(queue)} node(s)")

    if args.dry_run:
        cmd = build_cli_command(session_dir, args.model, args.timeout)
        prompt_path = os.path.join(session_dir, "AUDIT_PROMPT.md")
        with open(prompt_path, "r", encoding="utf-8") as f:
            audit_prompt = f.read()
        full_prompt = BATCH_RIDER + audit_prompt
        print("\n  [dry-run] would invoke:")
        print(f"    $ {' '.join(cmd)} (cwd={session_dir})")
        print(f"  stdin prompt size: {len(full_prompt):,} chars "
              f"(~{len(full_prompt)//4:,} tokens)")
        return True

    if args.manual:
        print("  [manual] reading response from stdin...")
        response = sys.stdin.read()
        if not response.strip():
            print("  ERROR: empty stdin")
            return False
    else:
        response = run_claude(session_dir, args.model, args.timeout)
        if response is None:
            return False

    # Save raw response (always — the extracted JSONs are lossy).
    raw_path = os.path.join(session_dir, "RAW_RESPONSE.md")
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(response)
    print(f"  Saved: RAW_RESPONSE.md ({len(response):,} chars)")

    # Extract + save revised nodes.
    nodes, warnings, fatal = extract_revised_nodes(response, packet)
    if warnings:
        print("  Parser warnings:")
        for w in warnings:
            print(f"    - {w}")
    if fatal:
        # A fatal extraction error = the AI's response is incomplete or
        # malformed for THIS packet. Return False so the campaign
        # orchestrator stops (unless the user passed --continue-on-error).
        # RAW_RESPONSE.md is already saved above — the user can inspect
        # it and decide whether to rerun or fix manually.
        print("  ERROR: response parsing failed:")
        for f in fatal:
            print(f"    - {f}")
        print(f"  See {os.path.basename(raw_path)} for the full response.")
        return False
    if not nodes:
        print("  ERROR: no revised node JSONs could be extracted.")
        return False

    written, skipped = write_revised_nodes(
        session_dir, nodes, overwrite=args.overwrite
    )
    if written:
        print(f"  Wrote {len(written)} revised node(s) to "
              f"{os.path.basename(session_dir)}/revised/: "
              f"{', '.join(written)}")
    if skipped:
        print(f"  Skipped {len(skipped)} existing file(s) "
              "(use --overwrite to replace): "
              f"{', '.join(skipped)}")
    return True


# ─────────────────────────────────────────────────────────────────────
# Campaign runner
# ─────────────────────────────────────────────────────────────────────

def run_campaign(campaign_dir, args):
    sessions = list_campaign_sessions(campaign_dir)
    if not sessions:
        print(f"ERROR: no valid session subfolders under {campaign_dir}")
        return False
    print(f"Campaign: {campaign_dir}")
    print(f"Sessions: {len(sessions)}")
    any_failed = False
    for session_dir in sessions:
        ok = run_packet(session_dir, args)
        if not ok:
            any_failed = True
            if not args.continue_on_error:
                print("\nStopping on first failure "
                      "(pass --continue-on-error to keep going).")
                return False
    return not any_failed


# ─────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run an audit packet (or a whole campaign) through Claude "
            "CLI and save revised node JSONs into the packet folder."
        )
    )
    parser.add_argument(
        "target",
        help="Path to a session folder (contains AUDIT_PROMPT.md + "
             "AUDIT_CONTEXT.md + PACKET.json), or — with --all — a "
             "campaign folder (contains 00_plan.md and NN_*/ subfolders).",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Treat `target` as a campaign root; run every session "
             "subfolder in plan order.",
    )
    parser.add_argument(
        "--model", default="opus",
        help="Model for Claude CLI (default: opus). Options: opus, "
             "sonnet, haiku.",
    )
    parser.add_argument(
        "--timeout", type=int, default=600,
        help="Per-packet timeout in seconds (default: 600).",
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Overwrite existing revised/<id>.json files.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print the CLI invocation and prompt size; don't run.",
    )
    parser.add_argument(
        "--manual", action="store_true",
        help="Read the audit response from stdin instead of calling "
             "Claude CLI. Useful when you want to keep doing the audit "
             "in the web chat but still want the outputs saved.",
    )
    parser.add_argument(
        "--continue-on-error", action="store_true",
        help="With --all, keep running later sessions even if one fails.",
    )
    args = parser.parse_args()

    target = os.path.abspath(args.target)
    if not os.path.exists(target):
        print(f"ERROR: {target} does not exist")
        sys.exit(1)

    if args.all:
        if not is_campaign_dir(target):
            print(f"ERROR: {target} is not a campaign folder "
                  "(expected 00_plan.md and NN_*/ subfolders).")
            sys.exit(1)
        ok = run_campaign(target, args)
    else:
        if not is_session_dir(target):
            print(f"ERROR: {target} is not a session folder.")
            if is_campaign_dir(target):
                print("  (Looks like a campaign folder — add --all "
                      "to run every session.)")
            sys.exit(1)
        ok = run_packet(target, args)

    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
