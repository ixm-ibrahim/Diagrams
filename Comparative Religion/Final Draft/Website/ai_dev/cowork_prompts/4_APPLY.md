# Cowork Prompt 4 — Rebuild data.json

Paste this after verify passed. This session rebuilds `data.json` from
the edited `ai_dev/nodes/` tree and confirms the result.

---

The verify session passed, so the `ai_dev/nodes/` tree is consistent.
Now rebuild `data.json` from it.

## What to do

1. Run compose from the scripts folder:

   ```
   cd ai_dev/scripts
   python compose_data.py
   ```

   This will:
   - Walk `ai_dev/nodes/` and validate filenames/paths/ids again.
   - Save a backup to `data.json.bak` before overwriting.
   - Atomically write the rebuilt `data.json`.

2. Confirm the write succeeded:
   - Check that `data.json.bak` exists and is the pre-audit version.
   - Check that `data.json` has been updated (compare mtime or size).

3. Sanity-check the diff. Don't paste the whole thing — just summarize:
   - How many node files had their focus section rewritten (count
     entries in today's audit log at `ai_dev/outputs/audits/`).
   - Spot-check one of them: open the corresponding node in `data.json`
     and confirm the revised focus section matches what's in the
     `ai_dev/nodes/<id-parts>/<id>.json` file.
   - Confirm no other fields on any audited node were changed
     (a quick `grep -n '"id":'` comparison between `data.json` and
     `data.json.bak` at the audited ids, if that's easy).

4. Report back with:
   - Number of nodes in the rebuilt `data.json`.
   - Whether the backup looks right.
   - Any surprise diffs outside the audited focus sections — that's the
     signal to stop and investigate.

If anything looks off, tell me before I commit. `data.json.bak` is the
rollback point.
