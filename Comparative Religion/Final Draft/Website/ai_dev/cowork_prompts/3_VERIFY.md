# Cowork Prompt 3 — Verify the edited tree

Paste this after the audit session is done. Short session — validates
the `ai_dev/nodes/` tree and surfaces anything broken before we rebuild
`data.json`.

---

I just finished an audit pass that edited files under `ai_dev/nodes/`.
Before I rebuild `data.json`, I want to confirm the tree is internally
consistent.

## What to do

Run compose in dry-run mode from the scripts folder:

```
cd ai_dev/scripts
python compose_data.py --dry-run
```

This walks `ai_dev/nodes/` and validates:
- Every `<id>.json` parses as JSON.
- Every file's filename matches the `id` field inside.
- Every folder path matches the id parts (node `1.2.5.4` must live at
  `ai_dev/nodes/1/2/5/4/`).
- No duplicate ids.

It does NOT read the existing `data.json` — the node tree is the source
of truth here, and `data.json` is about to be rebuilt from it in step 4.

## If it passes

Tell me how many nodes compose found and anything else notable from the
output. Then we're clear to run step 4.

## If it fails

Stop and show me the error. Don't try to fix the node files without
checking with me first — a mismatch between filename/path/id usually
means I need to decide which side to keep.

## Note on `verify_roundtrip.py`

Don't run `verify_roundtrip.py` here. That script's job is to test
whether `decompose_data.py` + `compose_data.py` are lossless on a given
`data.json` — useful after schema changes, but it requires a valid
`data.json` as input, which is exactly what we're about to overwrite.
For routine audits, `compose_data.py --dry-run` is the right check.
