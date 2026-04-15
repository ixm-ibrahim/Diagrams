#!/usr/bin/env python3
"""
prep_session.py — Generate CONTEXT_FOR_SESSION.md for a specific branch.

Extracts focused, relevant context using:
  - Structural analysis: tree relationships, ancestors, vocabulary, siblings
  - Keyword extraction: pulls terms from the target branch's claims and
    searches old project files at paragraph level for relevant passages
  - Phenomenology term matching: extracts only the DAG definitions that
    the target branch's vocabulary depends on

Usage:
    python prep_session.py 1.2.5.4
    python prep_session.py 1.2.5.4 --old-project-dir "../Comparative Religion Diagram"
    python prep_session.py 1.2.5.4 --phenom-dir "../Phenomenology Diagram"
    python prep_session.py 1.2.5.4 --all-dirs  # auto-detects sibling folders
"""

import json
import sys
import os
import re
import argparse
import shutil
import subprocess
import tempfile
from collections import Counter


# ─────────────────────────────────────────────────────────────────────
# Core data helpers
# ─────────────────────────────────────────────────────────────────────

def load_data(data_file: str) -> dict:
    with open(data_file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_node(nodes, nid):
    for n in nodes:
        if n["id"] == nid:
            return n
    return None


def get_children(nodes, parent_id):
    return [n for n in nodes if n.get("parentId") == parent_id]


def get_descendants(nodes, nid):
    result, queue = [], [nid]
    while queue:
        pid = queue.pop(0)
        for child in get_children(nodes, pid):
            result.append(child)
            queue.append(child["id"])
    return result


def get_ancestors(nodes, nid):
    ancestors, cur = [], get_node(nodes, nid)
    while cur and cur.get("parentId"):
        parent = get_node(nodes, cur["parentId"])
        if parent:
            ancestors.append(parent)
            cur = parent
        else:
            break
    ancestors.reverse()
    return ancestors


def get_siblings(nodes, nid):
    node = get_node(nodes, nid)
    if not node or not node.get("parentId"):
        return []
    return [n for n in nodes if n.get("parentId") == node["parentId"] and n["id"] != nid]


def has_sections(node):
    return bool(
        node.get("sections")
        and any(s.get("items") and len(s["items"]) > 0 for s in node["sections"])
    )


# ─────────────────────────────────────────────────────────────────────
# Keyword extraction from branch claims
# ─────────────────────────────────────────────────────────────────────

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "must", "can", "could", "of", "in", "to",
    "for", "with", "on", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "under",
    "again", "further", "then", "once", "here", "there", "when", "where",
    "why", "how", "all", "each", "every", "both", "few", "more", "most",
    "other", "some", "such", "no", "nor", "not", "only", "own", "same",
    "so", "than", "too", "very", "just", "about", "and", "but", "or",
    "if", "while", "because", "that", "this", "these", "those", "it",
    "its", "what", "which", "who", "whom", "whose", "they", "them",
    "their", "we", "us", "our", "he", "him", "his", "she", "her", "i",
    "me", "my", "you", "your", "one", "two", "also", "up", "out", "off",
    "over", "down", "any", "well", "back", "even", "still", "yet",
    "already", "much", "many", "like", "whether", "without", "within",
    # Project-specific stop words (too generic within this project)
    "node", "nodes", "claim", "claims", "section", "sections", "tree",
    "page", "sub-page", "branch", "parent", "child", "children", "sibling",
    "occur", "occurs", "occurring", "occurred", "occurrence", "occurrences",
    "phenomenon", "phenomena", "distinct", "quality", "qualities",
}


def extract_keywords(nodes, target_id):
    """Extract meaningful keywords from the target branch's claims."""
    target = get_node(nodes, target_id)
    if not target:
        return set()

    claims = [target["claim"]]
    for d in get_descendants(nodes, target_id):
        claims.append(d["claim"])
    if target.get("soWhat"):
        claims.append(target["soWhat"])

    words = []
    for claim in claims:
        cleaned = claim.lower()
        cleaned = re.sub(r'[^\w\s-]', ' ', cleaned)
        tokens = cleaned.split()
        for t in tokens:
            t = t.strip("-")
            if t and t not in STOP_WORDS and len(t) > 2:
                words.append(t)

    return set(Counter(words).keys())


def extract_keywords_from_vocabulary(nodes, target_id):
    """Extract vocabulary terms from ancestor/sibling Unlocks."""
    keywords = set()
    for ancestor in get_ancestors(nodes, target_id):
        unlocks_text = extract_unlocks_text(ancestor)
        if unlocks_text:
            for q in re.findall(r'"([^"]+)"', unlocks_text):
                for word in q.lower().split():
                    if word not in STOP_WORDS and len(word) > 2:
                        keywords.add(word)

    for sib in get_siblings(nodes, target_id):
        if has_sections(sib):
            unlocks_text = extract_unlocks_text(sib)
            if unlocks_text:
                for q in re.findall(r'"([^"]+)"', unlocks_text):
                    for word in q.lower().split():
                        if word not in STOP_WORDS and len(word) > 2:
                            keywords.add(word)
    return keywords


# ─────────────────────────────────────────────────────────────────────
# Smart paragraph extraction from old project files
# ─────────────────────────────────────────────────────────────────────

def split_into_paragraphs(text):
    text = text.replace('\r\n', '\n')
    raw = re.split(r'\n\s*\n', text)
    return [p.strip() for p in raw if p.strip() and len(p.strip()) > 30]


def score_paragraph(paragraph, keywords, boost_keywords=None):
    para_lower = paragraph.lower()
    score = 0
    matched = set()
    for kw in keywords:
        if kw in para_lower:
            score += 1
            matched.add(kw)
    if boost_keywords:
        for kw in boost_keywords:
            if kw in para_lower:
                score += 3
                matched.add(kw)
    if len(matched) >= 3:
        score += len(matched)
    return score, matched


def extract_relevant_passages(file_path, branch_keywords, vocab_keywords,
                               max_passages=8, min_score=3):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    paragraphs = split_into_paragraphs(content)
    if not paragraphs:
        return []

    scored = []
    for i, para in enumerate(paragraphs):
        score, matched = score_paragraph(para, vocab_keywords, boost_keywords=branch_keywords)
        if score >= min_score:
            scored.append({"index": i, "text": para, "score": score, "matched": matched})

    scored.sort(key=lambda x: x["score"], reverse=True)

    selected = []
    selected_indices = set()
    for item in scored[:max_passages]:
        if item["index"] not in selected_indices:
            selected_indices.add(item["index"])
            selected.append(item)

    selected.sort(key=lambda x: x["index"])
    return selected


# ─────────────────────────────────────────────────────────────────────
# Phenomenology Diagram smart extraction
# ─────────────────────────────────────────────────────────────────────

def extract_relevant_phenom_definitions(phenom_dir, branch_keywords, vocab_keywords):
    defs_file = os.path.join(phenom_dir, "3. DAG Definitions.txt")
    if not os.path.exists(defs_file):
        return None

    with open(defs_file, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r'\n(?=(?:PH|EP|ON|LG|RS|RP)\d)', content)
    all_keywords = branch_keywords | vocab_keywords
    relevant = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        block_lower = block.lower()
        match_count = sum(1 for kw in all_keywords if kw in block_lower)
        if match_count >= 1:
            relevant.append((match_count, block))

    relevant.sort(key=lambda x: x[0], reverse=True)
    return "\n\n".join(b for _, b in relevant) if relevant else None


# ─────────────────────────────────────────────────────────────────────
# Formatting helpers
# ─────────────────────────────────────────────────────────────────────

def extract_unlocks_text(node):
    for section in node.get("sections", []):
        if section.get("title") == "Unlocks" and section.get("items"):
            parts = []
            for item in section["items"]:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and "text" in item:
                    parts.append(item["text"])
                    for sub in item.get("items", []):
                        if isinstance(sub, str):
                            parts.append(sub)
            return " ".join(parts) if parts else None
    return None


def format_unlocks(node):
    for section in node.get("sections", []):
        if section.get("title") == "Unlocks" and section.get("items"):
            lines = []
            for item in section["items"]:
                if isinstance(item, str):
                    lines.append(f"  - {item}")
                elif isinstance(item, dict) and "text" in item:
                    lines.append(f"  - {item['text']}")
                    for sub in item.get("items", []):
                        if isinstance(sub, str):
                            lines.append(f"    - {sub}")
            return "\n".join(lines) if lines else None
    return None


def format_node_summary(node, include_unlocks=False):
    status = "DONE" if has_sections(node) else "TODO"
    line = f"[{status}] {node['id']}: {node['claim']}"
    if include_unlocks and has_sections(node):
        unlocks = format_unlocks(node)
        if unlocks:
            line += f"\n  Unlocks:\n{unlocks}"
    return line


def format_node_full(node):
    lines = [f"### {node['id']}: {node['claim']}"]
    if node.get("soWhat"):
        lines.append(f"**So What:** {node['soWhat']}")
    for section in node.get("sections", []):
        title = section.get("title", "")
        items = section.get("items", [])
        if not items:
            continue
        lines.append(f"\n**{title}:**")
        for item in items:
            if isinstance(item, str):
                lines.append(f"- {item}")
            elif isinstance(item, dict):
                if "text" in item:
                    lines.append(f"- {item['text']}")
                    for sub in item.get("items", []):
                        if isinstance(sub, str):
                            lines.append(f"  - {sub}")
                elif "title" in item:
                    lines.append(f"- **{item['title']}**")
                    if "detail" in item:
                        lines.append(f"  {item['detail']}")
                    for ss in item.get("subSections", []):
                        lines.append(f"  *{ss.get('label', '')}:*")
                        for si in ss.get("items", []):
                            if isinstance(si, str):
                                lines.append(f"    - {si}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────
# Batch planning — DFS bottom-up, sibling terminals grouped
# ─────────────────────────────────────────────────────────────────────

def plan_batches(nodes, target_id, max_terminals_per_batch=3):
    """Plan work batches in DFS bottom-up order.

    Rules:
      - Terminal sibling nodes (no children) are grouped into batches
        of up to max_terminals_per_batch.
      - Parent synthesis nodes (have children) are always solo batches.
      - Order: deepest terminals first, then their parent, then next group.
    """
    target = get_node(nodes, target_id)
    if not target:
        return []

    # Build the DFS bottom-up work order
    work_order = []
    _dfs_order(nodes, target_id, work_order)

    # Now group into batches
    batches = []
    current_terminal_batch = []
    current_parent_id = None

    for nid, node_type in work_order:
        node = get_node(nodes, nid)
        if not node:
            continue

        if node_type == "terminal":
            pid = node.get("parentId")
            # If switching to a different parent's children, flush
            if current_parent_id is not None and pid != current_parent_id:
                if current_terminal_batch:
                    batches.append(("write", current_terminal_batch))
                    current_terminal_batch = []

            current_parent_id = pid
            current_terminal_batch.append(nid)

            if len(current_terminal_batch) >= max_terminals_per_batch:
                batches.append(("write", list(current_terminal_batch)))
                current_terminal_batch = []

        elif node_type == "synthesis":
            # Flush any pending terminals first
            if current_terminal_batch:
                batches.append(("write", list(current_terminal_batch)))
                current_terminal_batch = []
                current_parent_id = None
            batches.append(("synthesize", [nid]))

    # Flush remaining terminals
    if current_terminal_batch:
        batches.append(("write", list(current_terminal_batch)))

    return batches


def _dfs_order(nodes, nid, result):
    """Recursive DFS bottom-up: children first, then parent."""
    children = get_children(nodes, nid)
    todo_children = [c for c in children if not has_sections(c)]
    done_children = [c for c in children if has_sections(c)]

    if not children:
        # Terminal node — only add if TODO
        node = get_node(nodes, nid)
        if node and not has_sections(node):
            result.append((nid, "terminal"))
        return

    # Process children first (DFS)
    for child in children:
        _dfs_order(nodes, child["id"], result)

    # Then this node as synthesis (if it has TODO children or is itself TODO)
    node = get_node(nodes, nid)
    if node and not has_sections(node):
        result.append((nid, "synthesis"))


# ─────────────────────────────────────────────────────────────────────
# Main context generation
# ─────────────────────────────────────────────────────────────────────

def get_old_project_mapping():
    return {
        "1": ["1"], "2": ["2"], "3": ["3", "3.1", "3.2"],
        "4": ["4", "4.1"], "5": ["5"], "6": ["6", "6.1"],
        "7": ["7", "7.1"], "8": ["8"],
    }


def find_old_project_files(old_dir, top_node):
    mapping = get_old_project_mapping()
    prefix = top_node.split(".")[0]
    file_nums = mapping.get(prefix, [])
    found = []
    for fn in file_nums:
        for f in os.listdir(old_dir):
            if f.startswith(f"{fn}.") or f.startswith(f"{fn} "):
                found.append(os.path.join(old_dir, f))
    return sorted(set(found))


def auto_detect_dirs(script_dir):
    """Search upward from the script directory for the two project folders.
    Walks up to 5 levels and checks every subdirectory at each level."""
    old_project, phenom = None, None
    search_dir = script_dir

    for _ in range(5):  # walk up to 5 levels
        search_dir = os.path.dirname(search_dir)
        if not search_dir or search_dir == os.path.dirname(search_dir):
            break  # reached filesystem root

        for root, dirs, _files in os.walk(search_dir):
            # Don't descend into the Website folder itself or hidden dirs
            dirs[:] = [d for d in dirs if d != "Website" and not d.startswith(".")]
            for d in dirs:
                full = os.path.join(root, d)
                d_lower = d.lower()
                if "comparative religion diagram" in d_lower and not old_project:
                    old_project = full
                elif "phenomenology diagram" in d_lower and not phenom:
                    phenom = full
            if old_project and phenom:
                return old_project, phenom

    return old_project, phenom


def run_claude_extraction(target_id, target_claim, branch_keywords,
                          structural_context, old_project_dir, phenom_dir):
    """Use Claude CLI to intelligently extract relevant context from the
    old project folders. Runs as a separate process with fresh context."""

    if not shutil.which("claude"):
        print("  WARNING: claude CLI not found, skipping AI extraction")
        return None

    # Build the prompt for Claude
    keywords_str = ", ".join(sorted(branch_keywords)[:25])

    prompt = f"""You are a research assistant extracting relevant context from project files.

TARGET: Node {target_id} — "{target_claim}"
BRANCH KEYWORDS: {keywords_str}

STRUCTURAL CONTEXT (for understanding what this node needs):
{structural_context}

YOUR TASK:
Search through ALL files in the provided directories for passages, arguments,
examples, objections, or definitions that are relevant to the target node and
its branch. Focus on:

1. Content that discusses the concepts in the branch's claims
2. Arguments or objections related to those concepts
3. How the old project framed or approached these topics
4. Definitions or distinctions that the branch will need

For each relevant passage you find, output it with:
- The source file name
- A brief note on why it's relevant (1 sentence)
- The passage itself

Be selective — only include passages that would genuinely help someone
writing the philosophical content for this branch. Skip generic or
tangential mentions. Aim for 10-20 high-quality passages total.

Do NOT include full files. Extract only the relevant paragraphs/sections.
Output in markdown format."""

    dirs_to_read = []
    if old_project_dir:
        dirs_to_read.append(old_project_dir)
    if phenom_dir:
        dirs_to_read.append(phenom_dir)

    if not dirs_to_read:
        return None

    # Add directory context to the prompt
    dir_list = "\n".join(f"  - {d}" for d in dirs_to_read)
    full_prompt = f"{prompt}\n\nDIRECTORIES TO SEARCH:\n{dir_list}\n\nRead the files in these directories and extract relevant passages."

    # Build the claude command
    # -p/--print: non-interactive, output only the response
    # --allowedTools: restrict to read-only tools
    # --add-dir: give access to the project directories
    # --model sonnet: fast model, good enough for extraction
    cmd = [
        "claude", "-p",
        "--model", "sonnet",
        "--allowedTools", "Read", "Bash(find:*)", "Bash(head:*)", "Bash(wc:*)", "Grep", "Glob",
        "--no-session-persistence",
    ]
    for d in dirs_to_read:
        cmd.extend(["--add-dir", d])

    print("  Running Claude CLI for intelligent extraction...")
    print(f"  Directories: {', '.join(os.path.basename(d) for d in dirs_to_read)}")

    try:
        result = subprocess.run(
            cmd,
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=180,  # 3 minute timeout
        )

        if result.returncode == 0 and result.stdout.strip():
            output = result.stdout.strip()
            print(f"  AI extraction complete: {len(output):,} chars")
            return output
        else:
            if result.stderr:
                print(f"  WARNING: Claude CLI error: {result.stderr[:200]}")
            return None

    except subprocess.TimeoutExpired:
        print("  WARNING: Claude CLI timed out after 120s, skipping AI extraction")
        return None
    except Exception as e:
        print(f"  WARNING: Claude CLI failed: {e}")
        return None


def generate_context(data_file, target_id, old_project_dir=None, phenom_dir=None, use_ai=False):
    data = load_data(data_file)
    nodes = data["nodes"]
    target = get_node(nodes, target_id)

    if not target:
        return f"ERROR: Node {target_id} not found in data.json"

    branch_keywords = extract_keywords(nodes, target_id)
    vocab_keywords = extract_keywords_from_vocabulary(nodes, target_id)

    lines = [f"# Context for Session: {target_id}\n"]
    lines.append(f"**Target:** {target_id} — {target['claim']}")
    lines.append(f"**Keywords extracted:** {', '.join(sorted(branch_keywords)[:20])}\n")

    # ── 1. Branch structure ──
    lines.append("---\n## Branch Structure\n")
    lines.append(f"- {target_id}: {target['claim']}")
    descendants = get_descendants(nodes, target_id)
    for d in descendants:
        depth = d["id"].count(".") - target_id.count(".")
        indent = "  " * depth
        status = "DONE" if has_sections(d) else "TODO"
        lines.append(f"  {indent}- [{status}] {d['id']}: {d['claim']}")

    # ── 1b. Batch plan with scaffolds ──
    batches = plan_batches(nodes, target_id)
    if batches:
        lines.append("\n---\n## Batch Plan\n")
        lines.append("Work through these batches in order. For each batch, draft all")
        lines.append("nodes, audit each against the checklist, then present the entire")
        lines.append("batch as a single JSON array in one code block.\n")
        lines.append("**CRITICAL:** The scaffolds below contain the exact `id`, `parentId`,")
        lines.append("`nextIds`, `prevIds`, `hasDerivation`, and `claim` from data.json.")
        lines.append("Do NOT modify these fields. You fill in `soWhat` and `sections` only.\n")

        for i, (batch_type, batch_ids) in enumerate(batches, 1):
            if batch_type == "synthesize":
                label = "SYNTHESIZE"
            else:
                label = "WRITE"

            lines.append(f"### Batch {i} ({label})\n")

            # Build scaffold JSON for each node in this batch
            scaffolds = []
            for nid in batch_ids:
                n = get_node(nodes, nid)
                if not n:
                    continue
                scaffold = {
                    "id": n["id"],
                    "parentId": n.get("parentId"),
                    "nextIds": n.get("nextIds", []),
                    "prevIds": n.get("prevIds", []),
                    "hasDerivation": n.get("hasDerivation", False),
                    "claim": n["claim"],
                    "soWhat": "FILL IN",
                    "sections": "FILL IN — see FORMAT_SPEC and JSON Examples"
                }
                scaffolds.append(scaffold)

            lines.append("```json")
            lines.append(json.dumps(scaffolds, indent=2, ensure_ascii=False))
            lines.append("```\n")

        lines.append(f"Total: {len(batches)} batches, "
                      f"{sum(len(ids) for _, ids in batches)} nodes.\n")
        lines.append("Start with Batch 1 in your first response.\n")

    # ── 2. Ancestor chain with vocabulary ──
    lines.append("\n---\n## Ancestor Chain (available vocabulary)\n")
    lines.append("Their Unlocks define the vocabulary available for this branch.\n")
    for a in get_ancestors(nodes, target_id):
        lines.append(format_node_summary(a, include_unlocks=True))
        lines.append("")

    # ── 3. Completed siblings ──
    lines.append("\n---\n## Completed Siblings\n")
    completed_siblings = [s for s in get_siblings(nodes, target_id) if has_sections(s)]
    if completed_siblings:
        for s in completed_siblings:
            lines.append(format_node_summary(s, include_unlocks=True))
            lines.append("")
    else:
        lines.append("(No completed siblings yet.)\n")

    # ── 4. Style reference ──
    lines.append("\n---\n## Style Reference (recently completed nodes)\n")
    lines.append("Use as quality and tone reference.\n")
    parent_id = target.get("parentId")
    if parent_id:
        all_sibs = get_children(nodes, parent_id)
        completed_branches = []
        for sib in all_sibs:
            if sib["id"] != target_id and has_sections(sib):
                sib_desc = get_descendants(nodes, sib["id"])
                if sib_desc and all(has_sections(d) for d in sib_desc):
                    completed_branches.append(sib)
        if completed_branches:
            ref_desc = get_descendants(nodes, completed_branches[-1]["id"])
            terminal = [d for d in ref_desc if not d.get("hasDerivation", False)]
            for tn in terminal[-3:]:
                lines.append(format_node_full(tn))
                lines.append("")
        else:
            lines.append("(No fully completed sibling branches yet.)\n")
    else:
        lines.append("(Top-level node.)\n")

    # ── 4b. JSON examples ──
    lines.append("\n---\n## JSON Examples (exact output format)\n")
    lines.append("Your output for each node must match this structure exactly.\n")

    # Find 2 completed terminal nodes to use as examples
    # Prefer nodes from the style reference branch, fall back to any completed nodes
    json_examples = []
    if parent_id:
        all_sibs = get_children(nodes, parent_id)
        for sib in all_sibs:
            if sib["id"] != target_id and has_sections(sib):
                sib_desc = get_descendants(nodes, sib["id"])
                terminal_done = [d for d in sib_desc
                                 if has_sections(d) and not d.get("hasDerivation", False)]
                json_examples.extend(terminal_done)
    if not json_examples:
        # Fall back: any completed terminal node in the tree
        for n in nodes:
            if has_sections(n) and not n.get("hasDerivation", False):
                json_examples.append(n)

    for ex in json_examples[-2:]:
        # Build a clean node dict with only the fields the AI should output
        clean = {"id": ex["id"], "claim": ex["claim"]}
        if ex.get("soWhat"):
            clean["soWhat"] = ex["soWhat"]
        if ex.get("sections"):
            clean["sections"] = ex["sections"]
        lines.append("```json")
        lines.append(json.dumps(clean, indent=2, ensure_ascii=False))
        lines.append("```\n")

    if not json_examples:
        lines.append("(No completed nodes available for examples.)\n")

    # ── 5. Old project: keyword-extracted relevant passages ──
    if old_project_dir and os.path.isdir(old_project_dir):
        lines.append("\n---\n## Old Project — Relevant Passages\n")
        lines.append("Automatically extracted by keyword relevance.")
        lines.append("Do NOT copy blindly — evaluate independently.\n")

        old_files = find_old_project_files(old_project_dir, target_id)
        total_passages = 0
        if old_files:
            for of_path in old_files:
                fname = os.path.basename(of_path)
                passages = extract_relevant_passages(
                    of_path, branch_keywords, vocab_keywords,
                    max_passages=8, min_score=3
                )
                if passages:
                    lines.append(f"\n### {fname}\n")
                    for p in passages:
                        matched_str = ", ".join(sorted(p["matched"])[:5])
                        lines.append(f"**[score {p['score']}, matched: {matched_str}]**")
                        lines.append(f"{p['text']}\n")
                        total_passages += 1

            if total_passages == 0:
                lines.append("(No strongly relevant passages found in mapped files.)\n")

        # Cross-file search for high-relevance hits in non-primary files
        lines.append("\n### Cross-file search (other files, high threshold)\n")
        cross_hits = []
        all_old_files = [os.path.join(old_project_dir, f)
                         for f in os.listdir(old_project_dir)
                         if os.path.isfile(os.path.join(old_project_dir, f))]
        for full in all_old_files:
            if full not in (old_files or []):
                passages = extract_relevant_passages(
                    full, branch_keywords, vocab_keywords,
                    max_passages=3, min_score=5
                )
                for p in passages:
                    p["source"] = os.path.basename(full)
                    cross_hits.append(p)

        cross_hits.sort(key=lambda x: x["score"], reverse=True)
        for hit in cross_hits[:8]:
            matched_str = ", ".join(sorted(hit["matched"])[:5])
            lines.append(f"**[{hit['source']}, score {hit['score']}, matched: {matched_str}]**")
            lines.append(f"{hit['text']}\n")

        if not cross_hits:
            lines.append("(No high-relevance cross-file hits.)\n")

    # ── 6. Phenomenology definitions ──
    if phenom_dir and os.path.isdir(phenom_dir):
        lines.append("\n---\n## Phenomenology Diagram — Relevant Definitions\n")
        defs = extract_relevant_phenom_definitions(phenom_dir, branch_keywords, vocab_keywords)
        if defs:
            lines.append(defs)
        else:
            lines.append("(No matching definitions found.)\n")

    # ── 7. AI-powered extraction ──
    if use_ai and (old_project_dir or phenom_dir):
        # Build a compact structural summary for Claude's context
        structural_summary_parts = [f"Branch: {target_id} — {target['claim']}"]
        for d in descendants:
            structural_summary_parts.append(f"  Child: {d['id']} — {d['claim']}")
        structural_summary_parts.append("\nCompleted sibling branches:")
        for s in completed_siblings:
            structural_summary_parts.append(f"  {s['id']}: {s['claim']}")
        structural_summary = "\n".join(structural_summary_parts)

        ai_result = run_claude_extraction(
            target_id, target["claim"], branch_keywords,
            structural_summary, old_project_dir, phenom_dir
        )
        if ai_result:
            lines.append("\n---\n## AI-Extracted Context\n")
            lines.append("The following was extracted by Claude CLI, reading the")
            lines.append("old project files intelligently for this branch.\n")
            lines.append(ai_result)
    elif not use_ai:
        lines.append("\n---\n## Note\n")
        lines.append("Run with `--ai` to use Claude CLI for intelligent")
        lines.append("extraction from old project files. Without it, only")
        lines.append("keyword-based extraction is used (sections above).\n")

    return "\n".join(lines)


def generate_current_state(nodes, target_id):
    """Auto-generate project state from data.json."""
    # Find all completed nodes (have sections with content)
    completed = sorted(
        [n["id"] for n in nodes if has_sections(n)],
        key=lambda x: id_sort_key(x)
    )
    total = len(nodes)
    done = len(completed)

    # Summarize completed ranges
    def summarize_ranges(ids):
        """Collapse consecutive IDs into ranges like '1.1.1–1.1.5'."""
        if not ids:
            return "(none yet)"
        # Group by parent prefix
        groups = {}
        for nid in ids:
            parts = nid.rsplit(".", 1)
            prefix = parts[0] if len(parts) > 1 else ""
            groups.setdefault(prefix, []).append(nid)
        ranges = []
        for prefix in sorted(groups, key=lambda x: id_sort_key(x) if x else ()):
            group = sorted(groups[prefix], key=lambda x: id_sort_key(x))
            if len(group) >= 3:
                ranges.append(f"{group[0]}–{group[-1]}")
            else:
                ranges.extend(group)
        return ", ".join(ranges)

    lines = []
    lines.append("# Current State (auto-generated from data.json)\n")
    lines.append("## Project Overview\n")
    lines.append("An interactive website presenting the **Sieve of Truth** — a hierarchical")
    lines.append("tree of connected claims. 8 top-level nodes (sieve layers):\n")
    lines.append("| Node | Name |")
    lines.append("|------|------|")
    lines.append("| 1 | Pursuit of Truth |")
    lines.append("| 2 | Discovering Reality |")
    lines.append("| 3 | Building Confidence |")
    lines.append("| 4 | Defining God |")
    lines.append("| 5 | Alignment with Reality |")
    lines.append("| 6 | Historical Comparison |")
    lines.append("| 7 | Non-Fundamental Comparison |")
    lines.append("| 8 | Results & Conclusion |\n")
    lines.append(f"**Total nodes:** {total} | **Completed:** {done} | **Remaining:** {total - done}\n")
    lines.append(f"**Completed:** {summarize_ranges(completed)}\n")
    lines.append(f"**Current target:** {target_id}\n")
    lines.append("**Methodology:** DFS bottom-up. Deepest terminal nodes first,")
    lines.append("then synthesize into parent. Continue ascending.\n")
    return "\n".join(lines)


def bundle_reference_files(script_dir, context_content, target_id, nodes):
    """Bundle all reference files + generated context into a single
    upload-ready file. Reads the reference files from the ai_dev folder
    and concatenates them in the correct reading order."""

    # Auto-generate current state instead of reading a static file
    current_state = generate_current_state(nodes, target_id)

    ref_files = [
        ("WRITING_GUIDE.md", "Writing Guide"),
        ("CHECKLIST.md", "Quality Checklist"),
        ("FORMAT_SPEC.md", "Output Format"),
    ]

    parts = []
    total_refs = 0

    # Add auto-generated current state first
    parts.append(f"\n{'=' * 72}")
    parts.append(f"SECTION: Project State (auto-generated)")
    parts.append(f"{'=' * 72}\n")
    parts.append(current_state)
    total_refs += 1
    print(f"  Generated: Project State ({len(current_state):,} chars)")

    # Bundle static reference files
    for filename, label in ref_files:
        filepath = os.path.join(script_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
            parts.append(f"\n{'=' * 72}")
            parts.append(f"FILE: {filename} ({label})")
            parts.append(f"{'=' * 72}\n")
            parts.append(content)
            total_refs += 1
            print(f"  Bundled: {filename} ({len(content):,} chars)")
        else:
            print(f"  WARNING: {filename} not found, skipping")

    # Add the generated context
    parts.append(f"\n{'=' * 72}")
    parts.append(f"SECTION: Branch-Specific Context (auto-generated)")
    parts.append(f"{'=' * 72}\n")
    parts.append(context_content)

    # Add a note about on-demand files
    parts.append(f"\n{'=' * 72}")
    parts.append("NOTE: On-Demand Files")
    parts.append(f"{'=' * 72}\n")
    parts.append("RULES_AND_PRINCIPLES.md and CLARIFICATIONS.md are NOT included.")
    parts.append("If you hit a structural question or ambiguity, ask me to paste")
    parts.append("the relevant file. This keeps your context lean for writing.\n")

    bundle = "\n".join(parts)
    print(f"\n  Bundled {total_refs} reference files + generated context")
    return bundle


def main():
    parser = argparse.ArgumentParser(
        description="Generate session context for a specific branch."
    )
    parser.add_argument("target", help="Target node ID (e.g., 1.2.5.4)")
    parser.add_argument("--data", default=None, help="Path to data.json")
    parser.add_argument("--old-project-dir", default=None,
                        help="Path to Comparative Religion Diagram folder")
    parser.add_argument("--phenom-dir", default=None,
                        help="Path to Phenomenology Diagram folder")
    parser.add_argument("--all-dirs", action="store_true",
                        help="Auto-detect old project and phenomenology folders")
    parser.add_argument("--ai", action="store_true",
                        help="Use Claude CLI for intelligent context extraction")
    parser.add_argument("--no-bundle", action="store_true",
                        help="Only generate CONTEXT_FOR_SESSION.md (don't bundle reference files)")
    parser.add_argument("--output", default=None,
                        help="Output file (default: SESSION_READY.md or CONTEXT_FOR_SESSION.md with --no-bundle)")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    website_dir = os.path.dirname(script_dir)  # parent = Website root
    data_file = args.data or os.path.join(website_dir, "data.json")

    if not os.path.exists(data_file):
        print(f"ERROR: {data_file} not found")
        sys.exit(1)

    old_dir = args.old_project_dir
    phen_dir = args.phenom_dir

    if args.all_dirs:
        auto_old, auto_phen = auto_detect_dirs(website_dir)
        if not old_dir and auto_old:
            old_dir = auto_old
            print(f"Auto-detected old project: {old_dir}")
        if not phen_dir and auto_phen:
            phen_dir = auto_phen
            print(f"Auto-detected phenomenology: {phen_dir}")

    print(f"Generating context for: {args.target}")
    print(f"Data file: {data_file}")
    if old_dir:
        print(f"Old project: {old_dir}")
    if phen_dir:
        print(f"Phenomenology: {phen_dir}")

    if args.ai:
        print("AI extraction: ENABLED (will use Claude CLI)")
    else:
        print("AI extraction: disabled (use --ai to enable)")

    context = generate_context(data_file, args.target, old_dir, phen_dir, use_ai=args.ai)

    # Print context breakdown by section
    print("\nContext breakdown:")
    sections = re.split(r'\n---\n', context)
    for sec in sections:
        # Find the first ## heading
        heading_match = re.search(r'^## (.+)', sec, re.MULTILINE)
        label = heading_match.group(1) if heading_match else "(header)"
        chars = len(sec)
        print(f"  {label}: {chars:,} chars (~{chars // 4:,} tokens)")

    # Also write standalone CONTEXT_FOR_SESSION.md (always, for reference)
    context_file = os.path.join(script_dir, "CONTEXT_FOR_SESSION.md")
    with open(context_file, "w", encoding="utf-8") as f:
        f.write(context)

    if args.no_bundle:
        output_file = args.output or context_file
        if args.output and args.output != context_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(context)
        size = len(context)
        print(f"\nWritten to: {output_file}")
        print(f"Size: {size:,} chars (~{size // 4:,} tokens)")
    else:
        # Bundle everything into one upload-ready file
        print("\nBundling reference files...")
        data = load_data(data_file)
        bundle = bundle_reference_files(script_dir, context, args.target, data["nodes"])
        output_file = args.output or os.path.join(script_dir, "SESSION_READY.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(bundle)
        size = len(bundle)
        print(f"\nWritten to: {output_file}")
        print(f"Size: {size:,} chars (~{size // 4:,} tokens)")
        print(f"\nUpload this ONE file to start your chat session.")


if __name__ == "__main__":
    main()
