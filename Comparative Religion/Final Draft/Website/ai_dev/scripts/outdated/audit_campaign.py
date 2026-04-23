#!/usr/bin/env python3
"""
audit_campaign.py — End-to-end audit orchestrator.

One command that runs the full pipeline:

    1. Plan       →  `plan_audit.plan_sessions` chunks the target and
                     writes packet folders under ai_dev/outputs/audits/.
    2. Run        →  `run_audit.run_packet` invokes Claude CLI on every
                     packet and saves revised/<id>.json files.
    3. Apply      →  `apply_audit.apply_session` merges revised nodes
                     back into data.json. A fresh data.json.bak is
                     produced immediately before the overwrite.
    4. Report     →  A summary of what was planned, what was run, what
                     was applied, and where to find the raw chat logs.

The orchestrator imports the other scripts (doesn't shell out), so the
summary aggregates real in-process state.

Usage:
    python audit_campaign.py 1.1
    python audit_campaign.py 1.1.1-1.1.8 --model sonnet
    python audit_campaign.py 1.1 --no-apply
    python audit_campaign.py 1.1 --clean
    python audit_campaign.py 1.1 --data ../../data.json

Options:
    --data              Alternate path to data.json.
    --include-incomplete
                        Also audit nodes without sections yet.
    --output-root       Alternate campaign root
                        (default: ai_dev/outputs/audits).
    --model             Claude CLI model (default: opus).
    --timeout           Per-packet CLI timeout in seconds (default: 600).
    --clean             Wipe the existing campaign folder before planning
                        (use if the last plan's chunking no longer
                        applies and you want a clean slate).
    --no-overwrite      Keep existing revised/*.json files (default is
                        to overwrite them on re-run).
    --no-apply          Plan and run, but don't merge into data.json.
    --continue-on-error Keep running later packets if one fails.
    --dry-run           Print the plan and what each step would do;
                        don't invoke Claude CLI or modify data.json.
"""

import argparse
import json
import os
import shutil
import sys
import time
from types import SimpleNamespace

from _common import load_data_json, write_json_atomic

# Import sibling scripts (same directory).
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))   # ai_dev/scripts
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from prep_session import (  # noqa: E402
    get_node,
    load_data,
    parse_targets,
)
from audit_session import SECTION_PROFILES  # noqa: E402
from plan_audit import (  # noqa: E402
    label_for_targets,
    plan_sessions,
    sanitize_for_path,
    session_folder_name,
    write_plan_file,
    write_session_packet,
)
from run_audit import (  # noqa: E402
    is_session_dir,
    list_campaign_sessions,
    load_packet,
    run_packet,
)
from apply_audit import (  # noqa: E402
    apply_session,
    load_revised_nodes,
    print_change_summary,
)


# ─────────────────────────────────────────────────────────────────────
# Pretty-printing helpers
# ─────────────────────────────────────────────────────────────────────

def banner(title, width=72):
    line = "═" * width
    print(f"\n{line}")
    print(f"  {title}")
    print(line)


def sub_banner(title, width=72):
    print(f"\n── {title} " + "─" * max(0, width - len(title) - 5))


# ─────────────────────────────────────────────────────────────────────
# Step 1: Plan
# ─────────────────────────────────────────────────────────────────────

def do_plan(nodes, target_ids, reference_dir, outputs_dir, output_root,
            include_incomplete, clean):
    """Run the planner and write all packets. Returns a dict with the
    campaign_dir, sessions list, and aggregate stats."""
    sessions, audit_nodes, skipped = plan_sessions(
        nodes, target_ids, include_incomplete=include_incomplete
    )
    if not sessions:
        raise RuntimeError(
            "No content-bearing nodes found in the target scope. "
            "Re-run with --include-incomplete to audit scaffolds too."
        )

    top_label = label_for_targets(target_ids)
    audits_root = output_root or os.path.join(outputs_dir, "audits")
    campaign_dir = os.path.join(audits_root, sanitize_for_path(top_label))

    if clean and os.path.isdir(campaign_dir):
        print(f"  --clean: removing existing campaign folder "
              f"{campaign_dir}")
        shutil.rmtree(campaign_dir)
    os.makedirs(campaign_dir, exist_ok=True)

    print(f"  Target(s):          {', '.join(target_ids)}")
    print(f"  Content nodes:      {len(audit_nodes)}")
    if skipped:
        print(f"  Skipped (scaffold): {len(skipped)} "
              "(use --include-incomplete to audit them)")
    print(f"  Planned sessions:   {len(sessions)}")
    print(f"  Campaign folder:    {campaign_dir}")

    packets = []
    for i, session in enumerate(sessions, 1):
        folder_name = session_folder_name(i, session)
        session_dir = os.path.join(campaign_dir, folder_name)
        packet_info = write_session_packet(
            session, nodes, reference_dir, session_dir,
            include_incomplete=include_incomplete,
            plan_index=i,
        )
        packet_info["folder"] = session_dir
        packet_info["folder_name"] = folder_name
        packet_info["section"] = session["section"]
        packet_info["target_ids"] = session["target_ids"]
        packet_info["note"] = session["note"]
        packets.append(packet_info)

    plan_path = os.path.join(campaign_dir, "00_plan.md")
    write_plan_file(
        plan_path, top_label, target_ids,
        len(audit_nodes), len(skipped), sessions, packets,
    )
    print(f"  Wrote plan summary: {plan_path}")

    return {
        "top_label": top_label,
        "campaign_dir": campaign_dir,
        "sessions": sessions,
        "packets": packets,
        "audit_nodes": audit_nodes,
        "skipped": skipped,
    }


# ─────────────────────────────────────────────────────────────────────
# Step 2: Run
# ─────────────────────────────────────────────────────────────────────

def do_run(campaign_dir, model, timeout, overwrite, continue_on_error,
           dry_run):
    """Run every session packet in plan order via Claude CLI. Returns
    stats per session."""
    sessions = list_campaign_sessions(campaign_dir)
    if not sessions:
        raise RuntimeError(
            f"No session folders found in {campaign_dir}"
        )

    run_args = SimpleNamespace(
        model=model,
        timeout=timeout,
        overwrite=overwrite,
        dry_run=dry_run,
        manual=False,
        continue_on_error=continue_on_error,
    )

    results = []
    any_failed = False
    start = time.time()

    print(f"  Sessions to run: {len(sessions)}")
    print(f"  Model: {model}  |  Timeout: {timeout}s  |  "
          f"Overwrite: {overwrite}  |  Dry-run: {dry_run}")

    for i, session_dir in enumerate(sessions, 1):
        packet = load_packet(session_dir)
        print(f"\n[{i}/{len(sessions)}] {os.path.basename(session_dir)} "
              f"(section={packet.get('section')}, "
              f"nodes={len(packet.get('audit_queue', []))})")

        ok = run_packet(session_dir, run_args)

        # Count revised nodes produced this run.
        revised = load_revised_nodes(session_dir)
        results.append({
            "session_dir": session_dir,
            "folder_name": os.path.basename(session_dir),
            "section": packet.get("section"),
            "queue_size": len(packet.get("audit_queue", [])),
            "success": bool(ok),
            "revised_count": len(revised),
        })

        if not ok:
            any_failed = True
            if not continue_on_error:
                print(f"\n  Aborting: session {os.path.basename(session_dir)} "
                      "failed. Re-run with --continue-on-error to push "
                      "through later sessions.")
                break

    elapsed = time.time() - start
    print(f"\n  Run step elapsed: {elapsed:.1f}s")

    return {
        "results": results,
        "any_failed": any_failed,
        "elapsed_s": elapsed,
    }


# ─────────────────────────────────────────────────────────────────────
# Step 3: Apply
# ─────────────────────────────────────────────────────────────────────

def do_apply(campaign_dir, data_file, dry_run):
    """Merge every session's revised nodes back into data.json.

    Returns an apply-stats dict. Creates a fresh data.json.bak
    immediately before overwriting data.json (unless dry_run)."""
    # Validate data.json before touching anything downstream — a corrupt
    # data.json caught here is a one-line error; caught later it is a
    # half-applied merge.
    data = load_data_json(data_file)
    nodes = data["nodes"]
    nodes_by_id = {n["id"]: n for n in nodes}
    print(f"  Source: {data_file}  ({len(nodes)} nodes)")

    sessions = list_campaign_sessions(campaign_dir)
    change_log = []
    totals = {"applied": 0, "skipped": 0, "warnings": 0}
    empty_sessions = []

    for session_dir in sessions:
        packet = load_packet(session_dir)
        revised = load_revised_nodes(session_dir)
        if not revised:
            empty_sessions.append(os.path.basename(session_dir))
            continue
        stats = apply_session(nodes_by_id, session_dir, packet, revised,
                              change_log)
        for k in totals:
            totals[k] += stats[k]

    touched_ids = {r["node_id"] for r in change_log}
    print(f"  Sessions with revisions: "
          f"{len(sessions) - len(empty_sessions)}/{len(sessions)}")
    if empty_sessions:
        print(f"  Empty sessions (no revised/*.json): "
              f"{', '.join(empty_sessions)}")
    print(f"  Node revisions applied: {totals['applied']}  "
          f"(unique nodes touched: {len(touched_ids)})")
    if totals["warnings"]:
        print(f"  Warnings: {totals['warnings']}")

    if dry_run or totals["applied"] == 0:
        print("  (dry-run or no revisions — data.json not modified.)")
        return {
            "change_log": change_log,
            "totals": totals,
            "touched_ids": touched_ids,
            "wrote": False,
            "backup_path": None,
            "empty_sessions": empty_sessions,
        }

    # Update data.json.bak from the CURRENT (pre-apply) data.json.
    backup = data_file + ".bak"
    shutil.copy2(data_file, backup)
    print(f"  Backup:  {backup}  "
          f"({os.path.getsize(backup):,} bytes, pre-apply state)")

    write_json_atomic(data_file, data)
    print(f"  Wrote:   {data_file}  "
          f"({os.path.getsize(data_file):,} bytes, post-apply state)")

    return {
        "change_log": change_log,
        "totals": totals,
        "touched_ids": touched_ids,
        "wrote": True,
        "backup_path": backup,
        "empty_sessions": empty_sessions,
    }


# ─────────────────────────────────────────────────────────────────────
# Step 4: Final report
# ─────────────────────────────────────────────────────────────────────

def do_report(plan_info, run_info, apply_info, args, target_ids):
    banner("Summary")

    # Plan recap
    print(f"\nTarget:           {', '.join(target_ids)}")
    print(f"Campaign folder:  {plan_info['campaign_dir']}")
    print(f"Chunking tier:    {describe_tier(plan_info)}")
    print(f"Sessions planned: {len(plan_info['sessions'])}")
    print(f"Content nodes:    {len(plan_info['audit_nodes'])}")
    if plan_info["skipped"]:
        print(f"Skipped (scaffold only): {len(plan_info['skipped'])}")

    # Run recap
    if run_info is None:
        print("\nRun step: SKIPPED (--dry-run on plan).")
    else:
        ok_sessions = sum(1 for r in run_info["results"] if r["success"])
        total_sessions = len(run_info["results"])
        total_revised = sum(r["revised_count"] for r in run_info["results"])
        print(f"\nRun step:")
        print(f"  Sessions run: {ok_sessions}/{total_sessions} succeeded "
              f"(in {run_info['elapsed_s']:.1f}s)")
        print(f"  Revised node JSONs produced: {total_revised}")
        failed = [r for r in run_info["results"] if not r["success"]]
        if failed:
            print("  Failures:")
            for r in failed:
                print(f"    - {r['folder_name']} "
                      f"(section={r['section']})")

    # Apply recap
    if apply_info is None:
        print("\nApply step: SKIPPED.")
    else:
        t = apply_info["totals"]
        print(f"\nApply step:")
        if apply_info["wrote"]:
            print(f"  data.json updated. Backup at: {apply_info['backup_path']}")
        else:
            print("  data.json NOT modified "
                  "(dry-run, or no revisions to apply).")
        print(f"  Sessions with revisions applied: "
              f"{len(list_campaign_sessions(plan_info['campaign_dir'])) - len(apply_info['empty_sessions'])}")
        print(f"  Unique nodes touched: {len(apply_info['touched_ids'])}")
        print(f"  Node revisions merged: {t['applied']}  "
              f"(warnings: {t['warnings']})")

        if apply_info["change_log"]:
            print("\n  Per-node change summary:")
            print_change_summary(apply_info["change_log"])

    # Next steps
    banner("Next Steps")
    print(f"\nRaw chat logs (to spot-check audits):")
    for packet in plan_info["packets"]:
        raw = os.path.join(packet["folder"], "RAW_RESPONSE.md")
        if os.path.isfile(raw):
            print(f"  {raw}")

    print(f"\nPacket folder (for full inspection): {plan_info['campaign_dir']}")
    print(f"Plan summary: {os.path.join(plan_info['campaign_dir'], '00_plan.md')}")

    # Workflow note re: coherence pass on focused campaigns
    has_focused = any(
        s["section"] != "all" for s in plan_info["sessions"]
    )
    has_coherence = any(
        s["section"] == "all" and "coherence" in s.get("note", "")
        for s in plan_info["sessions"]
    )
    if has_focused and has_coherence and apply_info and apply_info["wrote"]:
        print("\nNote: the final `all`-section coherence pass ran against "
              "the ORIGINAL data.json, not the post-focused-revision "
              "content. If you want coherence to see the revised text, "
              "re-run this command — it will re-plan, re-run, and re-apply "
              "with the updated baseline.")


def describe_tier(plan_info):
    n = len(plan_info["audit_nodes"])
    sessions = plan_info["sessions"]
    has_subbranch = any(s.get("scope") == "subbranch" for s in sessions)
    if n <= 6:
        return f"single full audit ({n} content nodes)"
    if not has_subbranch:
        return (f"7 focused passes + 1 coherence "
                f"({n} content nodes, 7–20 tier)")
    return (f"subdivided by sub-branches + final coherence "
            f"({n} content nodes, >20 tier)")


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=(
            "End-to-end audit orchestrator: plan + run (Claude CLI) + "
            "apply to data.json, with a final summary. Writes a fresh "
            "data.json.bak immediately before overwriting data.json."
        )
    )
    parser.add_argument(
        "target",
        help="Target node ID (e.g., 1.1.3), range (1.2.5.1-1.2.5.8 or "
             "shorthand 1.2.5.1-8), or comma-separated list (1.1,1.2.5).",
    )
    parser.add_argument("--data", default=None, help="Path to data.json")
    parser.add_argument("--include-incomplete", action="store_true",
                        help="Also audit scaffold nodes (no sections yet).")
    parser.add_argument("--output-root", default=None,
                        help="Override audits root "
                             "(default: ai_dev/outputs/audits).")
    parser.add_argument("--model", default="opus",
                        help="Claude CLI model (default: opus).")
    parser.add_argument("--timeout", type=int, default=600,
                        help="Per-packet CLI timeout seconds (default: 600).")
    parser.add_argument("--clean", action="store_true",
                        help="Wipe existing campaign folder before planning.")
    parser.add_argument("--no-overwrite", action="store_true",
                        help="Keep existing revised/*.json files "
                             "(default is to overwrite on re-run).")
    parser.add_argument("--no-apply", action="store_true",
                        help="Plan and run, but don't merge into data.json.")
    parser.add_argument("--continue-on-error", action="store_true",
                        help="Keep running later packets if one fails.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the plan and describe what each step "
                             "would do; don't call Claude CLI or modify "
                             "data.json.")
    args = parser.parse_args()

    script_dir = _SCRIPT_DIR
    ai_dev_dir = os.path.dirname(script_dir)
    reference_dir = os.path.join(ai_dev_dir, "reference")
    outputs_dir = os.path.join(ai_dev_dir, "outputs")
    website_dir = os.path.dirname(ai_dev_dir)
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

    # ── Step 1: Plan ────────────────────────────────────────────────
    banner(f"Step 1 · Plan — target {args.target}")
    try:
        plan_info = do_plan(
            nodes, target_ids, reference_dir, outputs_dir,
            args.output_root,
            include_incomplete=args.include_incomplete,
            clean=args.clean,
        )
    except RuntimeError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

    # ── Step 2: Run ─────────────────────────────────────────────────
    banner("Step 2 · Run — invoke Claude CLI on each packet")
    run_info = do_run(
        plan_info["campaign_dir"],
        model=args.model,
        timeout=args.timeout,
        overwrite=not args.no_overwrite,
        continue_on_error=args.continue_on_error,
        dry_run=args.dry_run,
    )

    # ── Step 3: Apply ───────────────────────────────────────────────
    apply_info = None
    if args.dry_run:
        banner("Step 3 · Apply — SKIPPED (--dry-run)")
        print("\n  Would merge revised nodes into data.json, "
              "after backing up to data.json.bak.")
    elif args.no_apply:
        banner("Step 3 · Apply — SKIPPED (--no-apply)")
        print("\n  Run `python3 apply_audit.py <campaign> --all` when "
              "you're ready to merge.")
    else:
        banner("Step 3 · Apply — merge revisions into data.json")
        apply_info = do_apply(
            plan_info["campaign_dir"],
            data_file=data_file,
            dry_run=False,
        )

    # ── Step 4: Report ──────────────────────────────────────────────
    do_report(plan_info, run_info, apply_info, args, target_ids)


if __name__ == "__main__":
    main()
