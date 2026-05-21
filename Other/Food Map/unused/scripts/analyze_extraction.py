"""Phase 39: surface taxonomy-refinement candidates from the Phase 36
extraction output.

Reads:
  src/data/compositional-meals.json   — corpus patterns (with frequency)
  src/data/meals.json                 — curated meals
  src/data/ingredients.json           — current category vocabulary

Reports:
  1. Top patterns by frequency (sanity check).
  2. Per-category coverage:
       - in how many distinct corpus patterns each category appears
       - total weighted (by pattern frequency) occurrences
  3. Pair co-occurrence ranked by *lift*  L(A,B) = P(A,B) / (P(A)·P(B)):
       - high lift on co-occurrence + high coverage  → MERGE candidate
       - both have >5 patterns BUT lift >= 5         → strongly tied pair
  4. Categories with many SMALL patterns (size <=3) and few large ones:
       potential SPLIT candidate (the corpus uses the category in many
       narrow contexts, suggesting subdivision would be useful).
  5. Singletons-or-tiny categories: those appearing in <5 corpus
       patterns AND <3 curated meals (RENAME / DROP candidates — the
       corpus doesn't really exhibit them, may be over-fragmented).
  6. Categories used in curated meals but missing from corpus patterns
       (or vice-versa): vocabulary gaps.

The script writes both a human-readable text report to stdout AND a
machine-readable JSON sidecar (`docs/phase39-analysis.json`) so a
follow-up `phase39_taxonomy.py` can act on it deterministically.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
ING_PATH       = ROOT / "src" / "data" / "ingredients.json"
MEALS_PATH     = ROOT / "src" / "data" / "meals.json"
CORPUS_PATH    = ROOT / "src" / "data" / "compositional-meals.json"
OUTPUT_PATH    = ROOT / "docs" / "phase39-analysis.json"

# Report-cutoffs. All knobs in one place.
TOP_PATTERNS_N        = 25
TOP_PAIRS_N           = 30
TOP_CATEGORIES_N      = 25
SMALL_PATTERN_SIZE    = 3
LOW_COVERAGE_PATTERNS = 5     # categories present in fewer patterns than this
LOW_COVERAGE_CURATED  = 3     # ... AND fewer curated meals than this
HIGH_LIFT             = 5.0   # threshold flagging "strongly tied" pairs
MERGE_CANDIDATE_LIFT  = 8.0   # higher bar for an actual merge proposal


def load_json(p: pathlib.Path):
    return json.loads(p.read_text(encoding="utf-8"))


def all_current_categories(ingredients):
    return sorted({i["category"] for i in ingredients})


def per_category_coverage(patterns):
    """For each category: (n_patterns_containing, total_weighted_frequency).
    Weighted by each pattern's `frequency` so a category that appears in
    rare patterns counts less than one in common patterns."""
    pat_count: Counter[str] = Counter()
    weighted: Counter[str] = Counter()
    for p in patterns:
        cats = p.get("ingredient_categories", [])
        freq = max(1, int(p.get("frequency", 1)))
        for c in cats:
            pat_count[c] += 1
            weighted[c]  += freq
    return pat_count, weighted


def pair_cooccurrence(patterns):
    """Build co-occurrence counts and lift on category PAIRS.

    Each pattern contributes one row of occurrences for each of its
    pairs. We weight by frequency, since a pattern that appears in 10000
    recipes is much stronger evidence than one in 100.
    """
    cat_w: Counter[str] = Counter()
    pair_w: Counter[tuple] = Counter()
    total = 0
    for p in patterns:
        cats = sorted(set(p.get("ingredient_categories", [])))
        if not cats:
            continue
        freq = max(1, int(p.get("frequency", 1)))
        total += freq
        for c in cats:
            cat_w[c] += freq
        for i, a in enumerate(cats):
            for b in cats[i + 1:]:
                pair_w[(a, b)] += freq

    if total == 0:
        return [], cat_w, total

    rows = []
    for (a, b), w in pair_w.items():
        pa = cat_w[a] / total
        pb = cat_w[b] / total
        pab = w / total
        # Guard against single-pattern blips.
        if cat_w[a] < 20 or cat_w[b] < 20:
            continue
        lift = pab / (pa * pb) if (pa > 0 and pb > 0) else 0.0
        rows.append({
            "a": a, "b": b,
            "weight": w,
            "p_a": pa, "p_b": pb, "p_ab": pab,
            "lift": lift,
            "support_a": cat_w[a],
            "support_b": cat_w[b],
        })
    # Sort by lift desc, then by weight desc for ties.
    rows.sort(key=lambda r: (r["lift"], r["weight"]), reverse=True)
    return rows, cat_w, total


def split_signal_per_category(patterns):
    """For each category, count how often it appears in SMALL vs LARGE
    patterns. A category disproportionately in small patterns might
    benefit from a sub-split (it's used as a coarse bucket)."""
    small: Counter[str] = Counter()
    large: Counter[str] = Counter()
    for p in patterns:
        cats = p.get("ingredient_categories", [])
        sz = len(cats)
        target = small if sz <= SMALL_PATTERN_SIZE else large
        for c in cats:
            target[c] += 1
    return small, large


def category_curated_usage(meals):
    counts: Counter[str] = Counter()
    for m in meals:
        for c in m.get("ingredient_categories", []):
            counts[c] += 1
    return counts


def name_pairs_to_review(categories):
    """Cheap text-similarity check: pairs of category names that share a
    long common token are worth a manual look for potential rename or
    merge."""
    SKIP = {"and", "or", "of", "the", "&", "fresh", "dried", "ground"}
    seen = []
    out = []
    for i, a in enumerate(categories):
        tokens_a = {t.lower().strip(",.") for t in a.replace("&", " ").split()} - SKIP
        for b in categories[i + 1:]:
            tokens_b = {t.lower().strip(",.") for t in b.replace("&", " ").split()} - SKIP
            shared = tokens_a & tokens_b
            if not shared:
                continue
            # Require at least one long shared token (>=4 chars) so we
            # don't flag every pair sharing "tea" or "oil".
            if any(len(t) >= 4 for t in shared):
                out.append({"a": a, "b": b, "shared": sorted(shared)})
    return out


def main():
    if not ING_PATH.exists() or not MEALS_PATH.exists() or not CORPUS_PATH.exists():
        print("Missing one of: ingredients.json / meals.json / compositional-meals.json",
              file=sys.stderr)
        return 2

    ingredients = load_json(ING_PATH)
    meals       = load_json(MEALS_PATH)
    corpus      = load_json(CORPUS_PATH)
    current_cats = all_current_categories(ingredients)

    pat_count, weighted = per_category_coverage(corpus)
    curated_use = category_curated_usage(meals)
    pair_rows, cat_w, total_weight = pair_cooccurrence(corpus)
    small_use, large_use = split_signal_per_category(corpus)

    # 1) Top patterns
    top_patterns = sorted(corpus, key=lambda p: int(p.get("frequency", 1)), reverse=True)[:TOP_PATTERNS_N]

    # 2) Per-category coverage table
    coverage_rows = []
    for c in current_cats:
        coverage_rows.append({
            "category": c,
            "corpus_patterns": pat_count.get(c, 0),
            "corpus_weighted": weighted.get(c, 0),
            "curated_meals":   curated_use.get(c, 0),
            "small_patterns":  small_use.get(c, 0),
            "large_patterns":  large_use.get(c, 0),
        })
    coverage_rows.sort(key=lambda r: r["corpus_weighted"], reverse=True)

    # 3) Merge candidates: high lift + both sides well-supported
    merge_candidates = [
        r for r in pair_rows
        if r["lift"] >= MERGE_CANDIDATE_LIFT and r["support_a"] >= 100 and r["support_b"] >= 100
    ][:TOP_PAIRS_N]

    # Tied pairs (lift in [HIGH_LIFT, MERGE_CANDIDATE_LIFT))
    tied_pairs = [
        r for r in pair_rows
        if HIGH_LIFT <= r["lift"] < MERGE_CANDIDATE_LIFT
    ][:TOP_PAIRS_N]

    # 4) Split candidates
    split_candidates = []
    for r in coverage_rows:
        if r["corpus_patterns"] < 20:
            continue
        small = r["small_patterns"]
        large = r["large_patterns"]
        if small == 0 and large == 0:
            continue
        ratio = small / max(1, small + large)
        if ratio >= 0.55 and r["corpus_patterns"] >= 50:
            split_candidates.append({**r, "small_ratio": ratio})
    split_candidates.sort(key=lambda r: r["small_ratio"], reverse=True)

    # 5) Low-coverage categories (rename / drop candidates)
    low_coverage = [
        r for r in coverage_rows
        if r["corpus_patterns"] < LOW_COVERAGE_PATTERNS
           and r["curated_meals"] < LOW_COVERAGE_CURATED
    ]

    # 6) Gaps
    in_curated_not_corpus = [
        c for c in current_cats
        if curated_use.get(c, 0) > 0 and pat_count.get(c, 0) == 0
    ]
    in_corpus_not_curated = [
        c for c in current_cats
        if pat_count.get(c, 0) > 0 and curated_use.get(c, 0) == 0
    ]

    # 7) Name-similarity rename review
    rename_review = name_pairs_to_review(current_cats)

    # ----- Stdout report -----
    def header(title):
        print()
        print("=" * 72)
        print(f" {title}")
        print("=" * 72)

    header("Phase 39 taxonomy analysis")
    print(f"corpus patterns: {len(corpus):>6}")
    print(f"curated meals:   {len(meals):>6}")
    print(f"distinct categories in current taxonomy: {len(current_cats)}")
    print(f"total weighted occurrences in corpus:    {total_weight:,}")

    header(f"Top {TOP_PATTERNS_N} corpus patterns by frequency")
    for p in top_patterns:
        cats = "+".join(p.get("ingredient_categories", []))
        print(f"  {p.get('frequency',0):>6,}  {cats}")

    header(f"Per-category coverage (top {TOP_CATEGORIES_N})")
    print(f"  {'category':<28}  {'corpus#':>7}  {'wgt':>9}  {'curated':>7}  {'small':>6}  {'large':>6}")
    for r in coverage_rows[:TOP_CATEGORIES_N]:
        print(f"  {r['category']:<28}  {r['corpus_patterns']:>7}  "
              f"{r['corpus_weighted']:>9,}  {r['curated_meals']:>7}  "
              f"{r['small_patterns']:>6}  {r['large_patterns']:>6}")

    header(f"Merge candidates (lift >= {MERGE_CANDIDATE_LIFT})")
    if not merge_candidates:
        print("  (none)")
    for r in merge_candidates:
        print(f"  lift={r['lift']:>5.1f}  weight={r['weight']:>6,}  "
              f"{r['a']:<28} + {r['b']}")

    header(f"Tied pairs ({HIGH_LIFT} <= lift < {MERGE_CANDIDATE_LIFT})")
    if not tied_pairs:
        print("  (none)")
    for r in tied_pairs[:TOP_PAIRS_N]:
        print(f"  lift={r['lift']:>5.1f}  weight={r['weight']:>6,}  "
              f"{r['a']:<28} + {r['b']}")

    header("Split candidates (>=55% appearances in patterns of size <=3)")
    if not split_candidates:
        print("  (none)")
    for r in split_candidates:
        print(f"  small/total={r['small_ratio']:.0%}  small={r['small_patterns']:<4} "
              f"large={r['large_patterns']:<4}  {r['category']}")

    header("Low-coverage categories (rename / drop review)")
    if not low_coverage:
        print("  (none)")
    for r in low_coverage:
        print(f"  corpus#={r['corpus_patterns']:<3}  curated#={r['curated_meals']:<3}  "
              f"{r['category']}")

    header("Vocabulary gaps")
    if in_curated_not_corpus:
        print("  In curated meals but NOT any corpus pattern:")
        for c in in_curated_not_corpus:
            print(f"    {c}")
    if in_corpus_not_curated:
        print("  In corpus patterns but NOT any curated meal:")
        for c in in_corpus_not_curated:
            print(f"    {c}")
    if not in_curated_not_corpus and not in_corpus_not_curated:
        print("  (none)")

    header("Name-similarity pairs to review")
    if not rename_review:
        print("  (none)")
    for r in rename_review:
        print(f"  shared={r['shared']!r:<30}  {r['a']}  /  {r['b']}")

    # ----- JSON sidecar -----
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps({
        "summary": {
            "corpus_patterns": len(corpus),
            "curated_meals": len(meals),
            "categories": len(current_cats),
            "total_weight": total_weight,
        },
        "top_patterns": [
            {"frequency": int(p.get("frequency", 1)),
             "ingredient_categories": list(p.get("ingredient_categories", []))}
            for p in top_patterns
        ],
        "coverage": coverage_rows,
        "merge_candidates": merge_candidates,
        "tied_pairs": tied_pairs,
        "split_candidates": split_candidates,
        "low_coverage": low_coverage,
        "in_curated_not_corpus": in_curated_not_corpus,
        "in_corpus_not_curated": in_corpus_not_curated,
        "rename_review": rename_review,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote analysis sidecar -> {OUTPUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
