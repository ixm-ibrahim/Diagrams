#!/usr/bin/env python3
"""Stream the RecipeNLG corpus and pull canonical dish-title statistics.

Goal: identify recognizable dish names that the project's curated +
compositional meal datasets don't already cover.

The corpus has ~2.2M recipes. Many titles are individual variants
("Aunt Edna's Best Apple Pie"); we normalize to a canonical form to
collapse those into a single dish bucket.

Outputs:
  - docs/corpus-title-stats.txt  -- summary + top titles by frequency
  - docs/corpus-titles.tsv       -- full title -> (count, sample NER bag) dump
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "recipeNLG_dataset_without_steps.csv"
OUT_STATS = ROOT / "docs" / "corpus-title-stats.txt"
OUT_TSV = ROOT / "docs" / "corpus-titles.tsv"

# Personal-recipe noise prefixes to strip when normalizing titles. These
# are common in old church-cookbook-era recipes and don't change the dish.
POSSESSIVE_PREFIXES = re.compile(
    r"^\s*("
    r"aunt|uncle|grandma|grandpa|granny|nana|mom|mama|mother|"
    r"dad|papa|father|"
    r"mrs|mr|ms|miss|"
    r"my|our|"
    r"best|easy|quick|simple|amazing|delicious|favorite|favourite|perfect|"
    r"super|ultimate|classic|original|traditional|homemade|home-made|home|"
    r"world|world's|grandmother's|grandma's|grandpa's|grandfather's|"
    r"mom's|mama's|mother's|dad's|papa's|father's|"
    r"the|a|an|"
    r"low-fat|low fat|low-carb|low carb|low-sodium|low sodium|"
    r"healthy|crockpot|crock-pot|crock pot|slow-cooker|slow cooker|"
    r"instant pot|microwave|easy peasy"
    r")\b[\s'.,!]+",
    re.IGNORECASE,
)

# "Aunt Edna's", "Mrs. Smith's", etc — strip a leading <Word>'s
LEADING_POSSESSIVE = re.compile(r"^\s*[A-Z][a-zA-Z\-]+(\s+[A-Z][a-zA-Z\-]+)?'s\s+", re.UNICODE)

# Trailing parenthetical or bracketed annotations
TRAILING_PAREN = re.compile(r"\s*[\(\[][^)\]]*[\)\]]\s*$")

# Trailing " - <anything>" or "  <number>" cookbook-style annotations
TRAILING_DASH = re.compile(r"\s*[-:|]\s+.{1,40}$")

WHITESPACE = re.compile(r"\s+")


def normalize_title(raw: str) -> str:
    s = raw.strip()
    s = s.strip("\"'")
    # repeatedly strip leading possessives + filler adjectives until stable
    for _ in range(6):
        new = LEADING_POSSESSIVE.sub("", s)
        new = POSSESSIVE_PREFIXES.sub("", new)
        if new == s:
            break
        s = new
    s = TRAILING_PAREN.sub("", s)
    s = TRAILING_DASH.sub("", s)
    s = WHITESPACE.sub(" ", s).strip(" \t.,!\"'-")
    return s.title()  # canonical Title Case so casing isn't a fragmentation axis


def main() -> None:
    if not CSV_PATH.exists():
        print(f"ERROR: corpus CSV not found: {CSV_PATH}", file=sys.stderr)
        sys.exit(1)

    counts: Counter[str] = Counter()
    sample_ner: dict[str, list[str]] = defaultdict(list)
    SAMPLE_CAP = 3  # store up to 3 NER lists per canonical title for category inference later

    rows = 0
    with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows += 1
            title = row.get("title") or ""
            # The _without_steps.csv header has 7 columns but rows only carry
            # 4 fields: index, title, ingredients-JSON, NER-JSON. With
            # csv.DictReader's positional mapping that puts the NER list into
            # the "directions" key. The "NER" key ends up as None.
            ner_raw = row.get("directions") or row.get("NER") or "[]"
            canon = normalize_title(title)
            if not canon:
                continue
            counts[canon] += 1
            if len(sample_ner[canon]) < SAMPLE_CAP:
                sample_ner[canon].append(ner_raw)
            if rows % 250_000 == 0:
                print(f"  ... {rows:,} rows, {len(counts):,} distinct canonical titles", file=sys.stderr)

    print(f"Total rows scanned: {rows:,}", file=sys.stderr)
    print(f"Distinct canonical titles: {len(counts):,}", file=sys.stderr)

    OUT_STATS.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append(f"# Corpus title stats")
    lines.append(f"")
    lines.append(f"Total rows: {rows:,}")
    lines.append(f"Distinct canonical titles: {len(counts):,}")
    lines.append(f"")
    bucket_thresholds = [1000, 500, 200, 100, 50, 20, 10, 5, 2, 1]
    lines.append(f"## Frequency buckets")
    for t in bucket_thresholds:
        n = sum(1 for c in counts.values() if c >= t)
        lines.append(f"  >= {t:5d}: {n:,} titles")
    lines.append(f"")
    lines.append(f"## Top 200 canonical titles by frequency")
    for title, n in counts.most_common(200):
        lines.append(f"  {n:6d}  {title}")
    OUT_STATS.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Full TSV: every canonical title with count + first NER sample
    with OUT_TSV.open("w", encoding="utf-8") as f:
        f.write("count\ttitle\tner_sample\n")
        for title, n in counts.most_common():
            ner = sample_ner[title][0] if sample_ner[title] else ""
            f.write(f"{n}\t{title}\t{ner}\n")
    print(f"Wrote {OUT_STATS}")
    print(f"Wrote {OUT_TSV}")


if __name__ == "__main__":
    main()
