#!/usr/bin/env python3
"""Apply hand-authored example_ingredients corrections to one meal file.

The corrections file (scripts/_audit_examples_corrections.json) is a JSON object:
    { "<meal_id>": ["<ingredient_id>", ...], ... }
Each value REPLACES that meal's example_ingredients wholesale. Only listed
meals change; everything else is re-serialized byte-identically (same 2-space /
CRLF formatter the data was generated with).

Before writing, every correction is validated the same way
validate_meal_example_ingredients.py validates the whole corpus:
  - all ids real, no dupes
  - every non-skip meal category keeps >=1 representative (a pick whose own
    category == that category). Heroes (out-of-cat) are allowed as extras.
Any violation aborts the whole apply (no partial writes).

Usage:
  python scripts/apply_examples_audit.py meals.json
  python scripts/apply_examples_audit.py meals.json --dry-run
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data"
CORR = ROOT / "scripts" / "_audit_examples_corrections.json"

SKIP_DEFAULT_CATEGORIES = {
    "Extracts & essences", "Pastes & ferments", "Pickled vegetables",
}


def load(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_meal_json(path: Path, data) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2).replace("\n", "\r\n")
    path.write_bytes((text + "\r\n").encode("utf-8"))


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    fn = sys.argv[1]
    dry = "--dry-run" in sys.argv

    ings = load(DATA / "ingredients.json")
    cat_of = {i["id"]: i["category"] for i in ings}
    name_of = {i["id"]: i["name"] for i in ings}

    corrections = load(CORR) if CORR.exists() else {}
    meals = load(DATA / fn)
    by_id = {m.get("id"): m for m in meals}

    errors = []
    applied = []
    for mid, new_ex in corrections.items():
        m = by_id.get(mid)
        if m is None:
            # Correction targets another file; skip silently here.
            continue
        cats = set(m.get("ingredient_categories") or [])
        if not isinstance(new_ex, list) or not new_ex:
            errors.append(f"{mid}: empty/invalid list")
            continue
        if len(new_ex) != len(set(new_ex)):
            errors.append(f"{mid}: duplicate ids")
        covered = set()
        for iid in new_ex:
            if iid not in cat_of:
                errors.append(f"{mid}: unknown id {iid!r}")
                continue
            covered.add(cat_of[iid])
        for c in cats:
            if c in SKIP_DEFAULT_CATEGORIES:
                continue
            if c not in covered:
                errors.append(f"{mid}: category {c!r} would lose its representative")
        if not errors:
            old = m.get("example_ingredients", [])
            if old != new_ex:
                applied.append((mid, m.get("name"), old, new_ex))

    if errors:
        print("VALIDATION FAILED — no files written:")
        for e in errors:
            print("  " + e)
        return 1

    print(f"{len(applied)} meal(s) changed in {fn}:")
    for mid, name, old, new in applied:
        o = ", ".join(name_of.get(i, i) for i in old)
        n = ", ".join(name_of.get(i, i) for i in new)
        print(f"\n  {name}  ({mid})")
        print(f"    - {o}")
        print(f"    + {n}")

    if dry:
        print("\n(dry-run — nothing written)")
        return 0
    if not applied:
        print("Nothing to write.")
        return 0

    backup = (DATA / fn).with_name((DATA / fn).stem + ".pre-examples-audit.json")
    if not backup.exists():
        import shutil
        shutil.copyfile(DATA / fn, backup)
        print(f"\nBackup: {backup.name}")
    for mid, _name, _old, new in applied:
        by_id[mid]["example_ingredients"] = new
    write_meal_json(DATA / fn, meals)
    print(f"Wrote {fn}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
