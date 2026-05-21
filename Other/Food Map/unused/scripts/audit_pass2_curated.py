"""Report on every curated meal in src/data/meals.json:
  - name, current categories, corpus matches (if any), corpus 30/40% derived set
  - flag entries whose match count is below the 20-recipe threshold
    used by the first pass (those are the ones we need to spot-check
    by hand because the corpus wasn't trusted to override them).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from audit_pass2_index import load_index, normalize_title

MEALS = ROOT / "src" / "data" / "meals.json"
OUT = ROOT / "docs" / "pass2-curated-report.json"


def corpus_summary(canon, idx):
    matches = idx.get(canon) or []
    n = len(matches)
    if n == 0:
        return None, 0, [], []
    freq = Counter()
    for cats in matches:
        for c in cats:
            freq[c] += 1
    rel = sorted(((c, freq[c] / n) for c in freq), key=lambda kv: -kv[1])
    at30 = [c for c, p in rel if p >= 0.30]
    at40 = [c for c, p in rel if p >= 0.40]
    return rel, n, at30, at40


def main():
    idx = load_index()
    meals = json.loads(MEALS.read_text(encoding="utf-8"))
    report = []
    untouched = []
    for m in meals:
        name = m["name"]
        canon = normalize_title(name)
        rel, n, at30, at40 = corpus_summary(canon, idx)
        entry = {
            "id": m.get("id"),
            "name": name,
            "current": list(m.get("ingredient_categories", [])),
            "n_matches": n,
            "top_freq": [(c, round(p, 3)) for c, p in (rel or [])[:15]],
            "corpus_30": at30,
            "corpus_40": at40,
            "cuisine": m.get("cuisine"),
            "frequency": m.get("frequency"),
        }
        report.append(entry)
        if n < 20:
            untouched.append(entry)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(report)} entries")
    print(f"Untouched (n<20): {len(untouched)} / {len(report)}")

    # Also write the untouched-only list, sorted by current frequency desc
    untouched.sort(key=lambda e: -(e.get("frequency") or 0))
    out2 = ROOT / "docs" / "pass2-curated-untouched.json"
    out2.write_text(json.dumps(untouched, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out2.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
