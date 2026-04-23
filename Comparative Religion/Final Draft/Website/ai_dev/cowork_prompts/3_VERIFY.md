# Cowork Prompt 3 — Verify the tree is still coherent

Paste this after the audit session is done. Short session — runs the
round-trip check and surfaces anything broken before we rebuild
data.json.

---

I just finished an audit pass that edited files under `ai_dev/nodes/`.
Before I rebuild `data.json`, I want to confirm the tree is still valid
and that a round-trip through compose+decompose is lossless.

## What to do

1. Run the round-trip verifier from the scripts folder:

   ```
   cd ai_dev/scripts
   python verify_roundtrip.py
   ```

   This decomposes the *current* `data.json` into a temp folder, composes
   that back, and deep-diffs — so it's checking the source data, not my
   edits. It should still pass (or tell me exactly what's corrupt).

2. Now check the edited tree itself. Run compose in dry-run mode:

   ```
   python compose_data.py --dry-run
   ```

   This walks `ai_dev/nodes/` and validates: every file's filename
   matches its `id`, every folder path matches the id parts, no
   duplicate ids. If any node file drifted, this is where we catch it.

3. If either step fails, stop and show me the error. Don't try to fix
   the node files without checking with me first — a mismatch between
   filename/path/id usually means I need to decide which side to keep.

4. If both pass, tell me:
   - How many nodes compose found.
   - Anything else notable from the output.

Don't actually write `data.json` in this session — that's the next step.
