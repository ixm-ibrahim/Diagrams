#!/usr/bin/env python3
"""
Split a structured plain-text document into one file per logical section.

Usage:
    python split_sections.py <input_file> [output_dir]

Section detection (generalized; not hardcoded to any particular document):
    1. Title blocks bounded by horizontal rule lines (--- or ===).
       The first non-blank line after the opening rule is taken as the
       section title.
    2. Standalone ALL-CAPS heading lines, preceded and followed by blank
       lines (and not immediately preceded by a horizontal rule), which
       are interpreted as sub-section markers nested inside rule-bounded
       blocks (e.g. an outer === ... === wrapper that contains several
       caps-titled subsections).

Output:
    One .txt file per detected section, prefixed with a zero-padded
    ordinal and a slugified version of the section title. Files are
    written to <output_dir> (default: same folder as the input file).
"""

import os
import re
import sys
from pathlib import Path


RULE_MIN_LEN = 10  # a line of at least this many '-' or '=' counts as a rule
NAME_MAX_LEN = 80

# Words that stay lowercase in title case (unless first word).
SMALL_WORDS = {
    "a", "an", "and", "as", "at", "but", "by", "for", "from", "if",
    "in", "into", "nor", "of", "on", "onto", "or", "so", "the", "to",
    "up", "vs", "via", "with", "yet",
}


def rule_type(line):
    """Return '=' or '-' if `line` is a horizontal rule; otherwise None."""
    stripped = line.rstrip("\n").strip()
    if len(stripped) >= RULE_MIN_LEN:
        if all(c == "=" for c in stripped):
            return "="
        if all(c == "-" for c in stripped):
            return "-"
    return None


def is_caps_heading(line):
    """Does this line look like a standalone all-caps heading?"""
    s = line.rstrip("\n").strip()
    if not s or len(s) > 80:
        return False
    if not re.search(r"[A-Z]", s):
        return False
    if re.search(r"[a-z]", s):
        return False
    # Allow uppercase letters, digits, spaces, and a small set of punctuation
    if not re.match(r"^[A-Z0-9 ()/\-,.:&'\"]+$", s):
        return False
    return True


def is_isolated_caps(lines, i):
    """
    True if `lines[i]` is a caps heading flanked by blank lines (above
    and below) and not immediately preceded by a horizontal rule.
    """
    n = len(lines)
    if not is_caps_heading(lines[i]):
        return False
    prev_blank = (i == 0) or (lines[i - 1].strip() == "")
    next_blank = (i == n - 1) or (lines[i + 1].strip() == "")
    prev_is_rule = (i > 0) and (rule_type(lines[i - 1]) is not None)
    return prev_blank and next_blank and not prev_is_rule


def find_section_starts(lines):
    """
    Return a list of (start_idx, title) tuples in document order — one
    entry per detected section.
    """
    starts = []
    n = len(lines)
    i = 0
    while i < n:
        rt = rule_type(lines[i])
        if rt is not None:
            # Rule line: is it followed by a title (non-blank, non-rule)?
            if i + 1 < n:
                nxt = lines[i + 1]
                if nxt.strip() and rule_type(nxt) is None:
                    title = nxt.strip()
                    starts.append((i, title))
                    i += 2
                    continue
            # Otherwise it's a closing rule or stray separator — skip.
            i += 1
            continue
        if is_isolated_caps(lines, i):
            starts.append((i, lines[i].strip()))
        i += 1
    return starts


def _cap_token(token):
    """Capitalize a single token, preserving any internal hyphenation."""
    parts = token.split("-")
    capped = []
    for p in parts:
        if not p:
            capped.append(p)
        else:
            capped.append(p[0].upper() + p[1:].lower())
    return "-".join(capped)


def friendly_name(title, max_len=NAME_MAX_LEN):
    """
    Build a user-friendly filename from a section title:

      - Title-cased ("Discourse Dynamics" not "DISCOURSE DYNAMICS")
      - Parenthesized acronyms preserved as-is (e.g. "(DD)")
      - Common small words kept lowercase ("of", "and", "in", ...)
      - Filesystem-unsafe characters replaced with safe equivalents
    """
    # Replace filesystem-problematic characters with safe alternatives.
    # ':' becomes ' -'; '/' and '\\' become '-'; <>"|?* are dropped.
    title = title.replace("/", "-").replace("\\", "-")
    title = title.replace(":", " -")
    for ch in '<>|?*"':
        title = title.replace(ch, "")

    out = []
    for i, w in enumerate(title.split()):
        # Preserve parenthesized acronyms like "(DD)" or "(VAWA)"
        if re.match(r"^\([A-Z][A-Z0-9]*\)[.,;]?$", w):
            out.append(w)
            continue
        bare = re.sub(r"[^A-Za-z]", "", w).lower()
        if i > 0 and bare in SMALL_WORDS:
            out.append(w.lower())
        else:
            out.append(_cap_token(w))

    name = re.sub(r"\s+", " ", " ".join(out)).strip()
    if not name:
        name = "Untitled"
    if len(name) > max_len:
        name = name[:max_len].rstrip(" -,;")
    return name


def split_file(input_path, output_dir):
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    starts = find_section_starts(lines)
    if not starts:
        return []

    n_sections = len(starts)
    width = max(2, len(str(n_sections)))
    written = []
    used_names = set()

    for idx, (start, title) in enumerate(starts, start=1):
        end = starts[idx][0] if idx < n_sections else len(lines)
        section_lines = lines[start:end]

        nice = friendly_name(title)
        out_name = f"{idx:0{width}d} - {nice}.txt"
        # Ensure uniqueness even with duplicate titles
        base = out_name
        counter = 2
        while out_name in used_names:
            out_name = f"{base[:-4]} ({counter}).txt"
            counter += 1
        used_names.add(out_name)

        out_path = output_dir / out_name
        with open(out_path, "w", encoding="utf-8") as f:
            f.writelines(section_lines)
        written.append((out_path, title, len(section_lines)))

    return written


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: split_sections.py <input_file> [output_dir]",
            file=sys.stderr,
        )
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.is_file():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = (
        Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.parent
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    written = split_file(input_path, output_dir)
    if not written:
        print("No sections detected.", file=sys.stderr)
        sys.exit(1)

    print(f"Wrote {len(written)} sections to {output_dir}:")
    for path, title, n_lines in written:
        print(f"  {path.name}  ({n_lines} lines)  -- {title}")


if __name__ == "__main__":
    main()
