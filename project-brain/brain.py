#!/usr/bin/env python3
"""
brain-search.py — Project Brain CLI
External search tool for the LLM memory system.
Runs OUTSIDE the LLM context window to find relevant files without consuming tokens.

Commands:
    brain init "<project name>"       Initialize a project-brain directory
    brain deposit --type TYPE --tags "tags"  Add a new knowledge file
    brain search "<query>"            Search fat indexes by tags and summary
    brain recall "<task description>" Generate a RESET file for a task
    brain status                      Project overview and health check
    brain ingest "<source file>"      Process source material into LTM files
"""

import argparse
import datetime
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

# Ensure UTF-8 output on Windows (avoids charmap encoding errors)
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BRAIN_DIR_NAME = "project-brain"
INDEX_MASTER = "INDEX-MASTER.md"
HASH_MANIFEST = ".content-hashes.json"

FILE_TYPES = {
    "SPEC": {"dir": "specs", "purpose": "Design decisions, architecture"},
    "CODE": {"dir": "code", "purpose": "Implementation"},
    "RULE": {"dir": "rules", "purpose": "Business/trading rules and their evolution"},
    "LEARN": {"dir": "learnings", "purpose": "Discovered knowledge (edge cases, gotchas)"},
    "LOG": {"dir": "logs", "purpose": "Decision rationale, debugging history"},
    "RESET": {"dir": "reset-files", "purpose": "Curated context packages for specific tasks"},
}

DIRECTORIES = [
    "indexes",
    "reset-files",
    "templates",
    "specs",
    "code",
    "rules",
    "learnings",
    "logs",
]

TODAY = datetime.date.today().isoformat()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def find_brain_root(start: Path | None = None) -> Path | None:
    """Walk up from `start` (default: cwd) looking for a project-brain/ directory."""
    current = start or Path.cwd()
    # Check if we're already inside project-brain/
    for parent in [current] + list(current.parents):
        candidate = parent / BRAIN_DIR_NAME
        if candidate.is_dir() and (candidate / INDEX_MASTER).exists():
            return candidate
        # Also check if current dir IS the brain root
        if parent.name == BRAIN_DIR_NAME and (parent / INDEX_MASTER).exists():
            return parent
    return None


def require_brain_root() -> Path:
    root = find_brain_root()
    if root is None:
        print("ERROR: No project-brain/ directory found.")
        print('Run `brain init "<project name>"` to create one.')
        sys.exit(1)
    return root


def next_id(brain_root: Path, file_type: str) -> str:
    """Find the next available ID number for a given file type."""
    type_dir = brain_root / FILE_TYPES[file_type]["dir"]
    existing = list(type_dir.glob(f"{file_type}-*.md"))
    if not existing:
        return f"{file_type}-001"
    numbers = []
    for f in existing:
        match = re.match(rf"{file_type}-(\d+)", f.stem)
        if match:
            numbers.append(int(match.group(1)))
    next_num = max(numbers) + 1 if numbers else 1
    return f"{file_type}-{next_num:03d}"


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_file(path: Path, content: str):
    path.write_text(content, encoding="utf-8")


def get_editor() -> str:
    return os.environ.get("EDITOR", os.environ.get("VISUAL", "notepad" if os.name == "nt" else "nano"))


def open_in_editor(path: Path):
    editor = get_editor()
    subprocess.call([editor, str(path)])


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English markdown."""
    return len(text) // 4


def hash_file(path: Path) -> str:
    """SHA-256 hash of file content."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(brain_root: Path) -> dict:
    """Load .content-hashes.json or return empty dict."""
    manifest_path = brain_root / HASH_MANIFEST
    if manifest_path.exists():
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    return {}


def save_manifest(brain_root: Path, manifest: dict):
    """Write .content-hashes.json."""
    manifest_path = brain_root / HASH_MANIFEST
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )


def build_manifest(brain_root: Path) -> dict:
    """Scan all brain files and compute hashes. Returns {relative_path: {hash, id, updated}}."""
    manifest = {}
    for file_type, info in FILE_TYPES.items():
        type_dir = brain_root / info["dir"]
        if not type_dir.exists():
            continue
        for f in type_dir.glob(f"{file_type}-*.md"):
            rel = f"{info['dir']}/{f.name}"
            manifest[rel] = {
                "hash": hash_file(f),
                "id": f.stem.split("_")[0],
                "updated": datetime.date.fromtimestamp(f.stat().st_mtime).isoformat(),
            }
    return manifest


def check_content_duplicate(brain_root: Path, new_file_path: Path) -> list[str]:
    """Check if a file's content hash matches any existing file. Returns list of matching relative paths."""
    manifest = load_manifest(brain_root)
    new_hash = hash_file(new_file_path)
    return [path for path, info in manifest.items() if info["hash"] == new_hash]


def parse_index_entries(index_text: str) -> list[dict]:
    """Parse fat index entries from an index markdown file.

    Returns a list of dicts with keys: id, type, file, tags, links, summary,
    interface, known_issues, and raw (the full entry text).
    """
    entries = []
    # Split on ### headings which denote individual entries
    chunks = re.split(r"^### ", index_text, flags=re.MULTILINE)
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        lines = chunk.split("\n")
        entry_id = lines[0].strip()
        # Must look like a file ID (e.g. SPEC-000, CODE-001)
        if not re.match(r"^[A-Z]+-\d+", entry_id):
            continue
        raw = "### " + chunk
        entry = {"id": entry_id, "raw": raw}
        for line in lines[1:]:
            line = line.strip().lstrip("- ")
            if line.startswith("**Type:**"):
                entry["type"] = line.split("**Type:**")[1].strip()
            elif line.startswith("**File:**"):
                entry["file"] = line.split("**File:**")[1].strip()
            elif line.startswith("**Tags:**"):
                entry["tags"] = line.split("**Tags:**")[1].strip()
            elif line.startswith("**Links:**"):
                entry["links"] = line.split("**Links:**")[1].strip()
            elif line.startswith("**Summary:**"):
                entry["summary"] = line.split("**Summary:**")[1].strip()
            elif line.startswith("**Interface:**"):
                entry["interface"] = line.split("**Interface:**")[1].strip()
            elif line.startswith("**Known issues:**"):
                entry["known_issues"] = line.split("**Known issues:**")[1].strip()
        # Capture multi-line summary (lines after **Summary:** until next **)
        summary_match = re.search(
            r"\*\*Summary:\*\*\s*(.*?)(?=\n-\s*\*\*|\Z)", raw, re.DOTALL
        )
        if summary_match:
            entry["summary"] = " ".join(summary_match.group(1).split())
        entries.append(entry)
    return entries


def collect_all_entries(brain_root: Path) -> list[dict]:
    """Collect fat index entries from INDEX-MASTER and all sub-indexes."""
    entries = []
    master_path = brain_root / INDEX_MASTER
    if master_path.exists():
        entries.extend(parse_index_entries(read_file(master_path)))
    index_dir = brain_root / "indexes"
    if index_dir.exists():
        for idx_file in index_dir.glob("INDEX-*.md"):
            entries.extend(parse_index_entries(read_file(idx_file)))
    return entries



# ---------------------------------------------------------------------------
# Text processing — stopwords, stemming, tokenization
# ---------------------------------------------------------------------------

STOPWORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "and", "but", "or",
    "not", "no", "nor", "so", "yet", "both", "each", "this", "that",
    "these", "those", "it", "its", "they", "them", "their", "we", "our",
    "you", "your", "he", "she", "his", "her", "which", "what", "when",
    "where", "who", "whom", "how", "all", "any", "some", "none", "if",
    "then", "than", "too", "very", "just", "also", "about", "up", "out",
})


def stem(word: str) -> str:
    """Lightweight suffix stemmer for English. Not a full Porter stemmer,
    but handles the most common inflections found in technical documentation.
    """
    if len(word) <= 3:
        return word
    # Order matters — try longest suffixes first
    if word.endswith("ational"):
        return word[:-7] + "ate"
    if word.endswith("ization"):
        return word[:-7] + "ize"
    if word.endswith("iveness"):
        return word[:-7] + "ive"
    if word.endswith("fulness"):
        return word[:-7] + "ful"
    if word.endswith("ousness"):
        return word[:-7] + "ous"
    if word.endswith("ement") and len(word) > 7:
        return word[:-5]
    if word.endswith("ment") and len(word) > 6:
        return word[:-4]
    if word.endswith("ation") and len(word) > 7:
        return word[:-5] + "e"
    if word.endswith("ating"):
        return word[:-3] + "e"
    if word.endswith("ling") and len(word) > 5 and word[-5] != "l":
        return word[:-3] + "e"
    if word.endswith("ying"):
        return word[:-4] + "y"
    if word.endswith("ting") and len(word) > 5 and not word.endswith("sting"):
        base = word[:-3]
        # Skip if base ends with 't' — let the general -ing rule handle it
        # (e.g., "setting" -> "sett" -> general rule deduplicates -> "set")
        if not base.endswith("t"):
            return base
    if word.endswith("sses"):
        return word[:-2]
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("ness") and len(word) > 5:
        return word[:-4]
    if word.endswith("less"):
        return word[:-4]
    if word.endswith("able") and len(word) > 5:
        return word[:-4]
    if word.endswith("ible") and len(word) > 5:
        return word[:-4]
    if word.endswith("ally"):
        return word[:-4] + "al"
    if word.endswith("ing") and len(word) > 4:
        base = word[:-3]
        if len(base) >= 2 and base[-1] == base[-2]:
            return base[:-1]  # "running" -> "run", "setting" -> "set"
        if len(base) > 2:
            return base
    if word.endswith("ment") and len(word) > 5:
        return word[:-4]
    if word.endswith("ful") and len(word) > 4:
        return word[:-3]
    if word.endswith("ous") and len(word) > 4:
        return word[:-3]
    if word.endswith("ive") and len(word) > 4:
        return word[:-3]
    if word.endswith("ized"):
        return word[:-4] + "ize"
    if word.endswith("ised"):
        return word[:-4] + "ise"
    if word.endswith("tion"):
        return word[:-4] + "t"
    if word.endswith("ed") and len(word) > 3:
        base = word[:-2]
        if base.endswith("i"):
            return base[:-1] + "y"  # "applied" -> "apply"
        if len(base) >= 2 and base[-1] == base[-2]:
            return base[:-1]  # "stopped" -> "stop"
        return base
    if word.endswith("er") and len(word) > 4:
        return word[:-2]
    if word.endswith("ly") and len(word) > 4:
        return word[:-2]
    if word.endswith("es") and len(word) > 3:
        if word.endswith("ches") or word.endswith("shes") or word.endswith("sses"):
            return word[:-2]
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
    return word


def tokenize(text: str) -> list[str]:
    """Tokenize text with hyphen expansion, stopword removal, and stemming.

    Improvements over v1 (LEARN-030 Phase 1):
    - Hyphenated terms expanded: "session-handoff" -> ["session", "handoff", "session-handoff"]
    - Common English stopwords removed
    - Lightweight suffix stemming to match inflections ("searching" -> "search")
    """
    raw_tokens = re.findall(r"[a-z0-9][-a-z0-9]*", text.lower())
    expanded = []
    for t in raw_tokens:
        expanded.append(t)
        if "-" in t:
            expanded.extend(part for part in t.split("-") if part)
    return [stem(t) for t in expanded if t not in STOPWORDS and len(t) > 1]


def entry_to_corpus_doc(entry: dict) -> list[str]:
    """Convert a fat index entry to a tokenized document for BM25.

    Field repetition approximates field boosting (LEARN-030 Section 3):
    - Tags 5x  — curated metadata, highest signal density
    - ID 4x    — direct reference lookup (e.g., "LEARN-008")
    - Title 3x — human-curated summary of content
    - Summary 1x (base) — bulk curated content
    - Type/file/known_issues 0.5x — low signal, included once
    """
    parts = []
    # Tags repeated 5x — curated metadata, highest signal
    tags = entry.get("tags", "")
    parts.extend([tags] * 5)
    # ID repeated 4x — direct reference
    parts.extend([entry.get("id", "")] * 4)
    # Summary — bulk of the content (1x, base weight)
    parts.append(entry.get("summary", ""))
    # Type and file — minor signal
    parts.append(entry.get("type", ""))
    parts.append(entry.get("file", ""))
    # Known issues — sometimes the answer is that a file explicitly lacks something
    parts.append(entry.get("known_issues", ""))
    return tokenize(" ".join(parts))


def build_bm25_index(entries: list[dict]):
    """Build a BM25 index from fat index entries. Returns BM25Okapi instance.

    Parameters tuned for fat-index corpus (LEARN-030):
    - k1=1.0 (lower than default 1.5 — short docs, term repetition rare)
    - b=0.4  (lower than default 0.75 — entries are similar length)
    """
    from rank_bm25 import BM25Okapi

    corpus = [entry_to_corpus_doc(e) for e in entries]
    bm25 = BM25Okapi(corpus, k1=1.0, b=0.4)
    return bm25


def score_entries_bm25(
    entries: list[dict], query_terms: list[str]
) -> list[tuple[float, dict]]:
    """Score all entries using BM25 + structural boosts + link propagation.

    Returns a sorted list of (score, entry) tuples, highest first.
    Only entries with score > 0 are included.
    """
    bm25 = build_bm25_index(entries)
    query_tokens = tokenize(" ".join(query_terms))

    if not query_tokens:
        return []

    # Stage 1: BM25 scores
    raw_scores = bm25.get_scores(query_tokens)

    # Stage 2: Structural boosts (exact tag match, ID match)
    boosted = []
    for i, entry in enumerate(entries):
        score = float(raw_scores[i])
        for term in query_terms:
            term_lower = term.lower()
            # Exact tag match — curated metadata, strongest signal
            tags = [t.strip().lower() for t in entry.get("tags", "").split(",")]
            if term_lower in tags:
                score += 5.0
            # ID match (e.g., searching "LEARN-008")
            if term_lower in entry.get("id", "").lower():
                score += 4.0
        boosted.append((score, entry))

    # Stage 3: Link propagation — files linked by high-scoring results get a boost.
    # This is the "neuron connection" effect: if LEARN-008 scores high and links
    # to LEARN-005, LEARN-005 gets a relevance boost even if the query terms
    # don't appear as strongly there.
    id_to_score = {e.get("id", ""): s for s, e in boosted}
    link_boost = {}
    for score, entry in boosted:
        if score <= 0:
            continue
        links_str = entry.get("links", "")
        if not links_str or links_str.startswith("_"):
            continue
        linked_ids = [lid.strip() for lid in re.split(r"[,;]+", links_str) if lid.strip()]
        for lid in linked_ids:
            # Propagate a fraction of this entry's score to linked entries
            propagated = score * 0.15
            link_boost[lid] = link_boost.get(lid, 0.0) + propagated

    # Apply link boosts
    final = []
    for score, entry in boosted:
        entry_id = entry.get("id", "")
        total = score + link_boost.get(entry_id, 0.0)
        if total > 0:
            final.append((total, entry))

    final.sort(key=lambda x: x[0], reverse=True)
    return final


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_init(args):
    """Initialize a project-brain directory with all scaffolding."""
    project_name = args.name
    brain_root = Path.cwd() / BRAIN_DIR_NAME

    if brain_root.exists():
        print(f"ERROR: {BRAIN_DIR_NAME}/ already exists in current directory.")
        sys.exit(1)

    # Create directories
    for d in DIRECTORIES:
        (brain_root / d).mkdir(parents=True, exist_ok=True)
    print(f"Created {BRAIN_DIR_NAME}/ with subdirectories.")

    # Copy templates from this script's directory or create them
    script_dir = Path(__file__).parent
    template_source = script_dir / "templates"
    template_dest = brain_root / "templates"

    if template_source.exists() and template_source != template_dest:
        for tmpl in template_source.glob("TEMPLATE-*.md"):
            shutil.copy2(tmpl, template_dest / tmpl.name)
        print(f"Copied {len(list(template_dest.glob('TEMPLATE-*.md')))} templates.")
    else:
        print("Templates directory is co-located; no copy needed.")

    # Create INDEX-MASTER.md
    index_content = textwrap.dedent(f"""\
    # INDEX-MASTER
    <!-- type: INDEX -->
    <!-- updated: {TODAY} -->
    <!-- project: {project_name} -->
    <!-- total-files: 0 -->
    <!-- Load this file at the start of every Claude Code session. -->

    ## How to Use This Index
    1. Read this file first in every session.
    2. Scan entries below to find what you need.
    3. Use `brain-search.py` for keyword search OUTSIDE context when possible.

    ---

    ## Sub-Indexes
    _None yet._

    ---

    ## SPEC Files
    _None yet._

    ---

    ## CODE Files
    _None yet._

    ---

    ## RULE Files
    _None yet._

    ---

    ## LEARN Files
    _None yet._

    ---

    ## LOG Files
    _None yet._
    """)
    write_file(brain_root / INDEX_MASTER, index_content)
    print(f"Created {INDEX_MASTER}.")

    # Create INIT.md — self-explanatory file for LLMs starting a new session
    init_content = textwrap.dedent(f"""\
    # INIT — Read This First

    You are an LLM starting a new session. This folder is a **Project Brain** — a persistent long-term memory system designed for you.

    ## What to do right now

    1. Read `INDEX-MASTER.md` in this directory. It contains a fat index of every knowledge file in this brain. Each entry has enough detail to tell you whether you need to open the full file or not.
    2. The user will give you a task. Use the index to find relevant files, load only what you need, and get to work.

    ## How this system works

    - **You have no memory between sessions.** This brain is your memory. Everything you need to know is stored as `.md` files in typed directories.
    - **Fat indexes save your context tokens.** INDEX-MASTER.md summarizes every file so you can skip files you don't need without opening them.
    - **File types:** SPEC (design decisions), CODE (implementation docs), RULE (business rules), LEARN (discovered knowledge), LOG (decision rationale), RESET (pre-built context packages for specific tasks).

    ## Directory layout

    ```
    project-brain/
    ├── INIT.md              ← You are here
    ├── INDEX-MASTER.md      ← Load this first. Fat index of everything.
    ├── brain.py             ← CLI search tool (user runs this, not you)
    ├── indexes/             ← Sub-indexes when file count exceeds ~75
    ├── reset-files/         ← Pre-built context packages for tasks
    ├── templates/           ← File templates for each type
    ├── specs/               ← SPEC files (design, architecture)
    ├── code/                ← CODE files (implementation docs)
    ├── rules/               ← RULE files (business rules)
    ├── learnings/           ← LEARN files (discovered knowledge)
    └── logs/                ← LOG files (decision rationale)
    ```

    ## Key rules

    - **Don't open files speculatively.** Read the fat index first. Every file you open costs tokens you can't get back.
    - **Deposit new knowledge.** If you discover something during a session (edge case, bug, decision), write it as a LEARN or LOG file and update INDEX-MASTER.md before the session ends.
    - **RESET files bridge sessions.** If the current task will continue in a future session, generate a RESET file listing exactly what files and context the next session needs.

    ## CLI tool (brain.py)

    The user can run these commands from a terminal (you don't need to — you read files directly):

    ```
    uv run brain.py status                  # Overview of the brain
    uv run brain.py search "query"          # Search fat indexes
    uv run brain.py recall "task"           # Generate a RESET file
    uv run brain.py deposit --type TYPE --tags "tags"  # Add a new file
    uv run brain.py ingest "source.md"      # Extract knowledge from a source
    uv run brain.py init "Project Name"     # Scaffold a new brain (for new projects)
    ```
    """)
    write_file(brain_root / "INIT.md", init_content)
    print("Created INIT.md.")

    # Copy brain.py into the brain root
    script_path = Path(__file__).resolve()
    dest_script = brain_root / "brain.py"
    if script_path != dest_script:
        shutil.copy2(script_path, dest_script)
        print("Copied brain.py into project-brain/.")

    print(f'\nProject Brain initialized for "{project_name}".')
    print("Next: deposit your first knowledge file with `brain deposit`.")


def cmd_deposit(args):
    """Add a new knowledge file to the brain."""
    brain_root = require_brain_root()
    file_type = args.type.upper()

    if file_type not in FILE_TYPES:
        print(f"ERROR: Unknown type '{file_type}'. Valid types: {', '.join(FILE_TYPES.keys())}")
        sys.exit(1)

    tags = args.tags
    file_id = next_id(brain_root, file_type)

    # Prompt for title
    title = input(f"Title for {file_id}: ").strip()
    if not title:
        print("ERROR: Title is required.")
        sys.exit(1)

    # Create file from template
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    filename = f"{file_id}_{slug}.md"
    type_dir = brain_root / FILE_TYPES[file_type]["dir"]
    file_path = type_dir / filename

    template_path = brain_root / "templates" / f"TEMPLATE-{file_type}.md"
    if template_path.exists():
        content = read_file(template_path)
        # Fill in template placeholders
        content = content.replace(f"{file_type}-NNN", file_id)
        content = content.replace("[Title]", title)
        content = content.replace("[Module/Script Name]", title)
        content = content.replace("[Rule Name]", title)
        content = content.replace("[What Was Learned]", title)
        content = content.replace("[Decision / Event Title]", title)
        content = content.replace("[Task Name]", title)
        content = content.replace("[comma-separated tags]", tags)
        content = content.replace("YYYY-MM-DD", TODAY)
    else:
        content = f"# {file_id} — {title}\n<!-- type: {file_type} -->\n<!-- tags: {tags} -->\n<!-- created: {TODAY} -->\n\n"

    write_file(file_path, content)
    print(f"Created: {file_path}")

    # Open in editor
    open_in_editor(file_path)

    # After editor closes, check for content duplicates
    final_content = read_file(file_path)
    tokens = estimate_tokens(final_content)

    duplicates = check_content_duplicate(brain_root, file_path)
    if duplicates:
        print(f"\nWARNING: Content hash matches existing file(s):")
        for dup in duplicates:
            print(f"  - {dup}")
        proceed = input("Continue with deposit anyway? (y/N): ").strip().lower()
        if proceed != "y":
            file_path.unlink()
            print("Deposit aborted. File removed.")
            return

    print(f"\n--- Fat Index Entry (auto-generated, edit as needed) ---")
    fat_entry = textwrap.dedent(f"""\
    ### {file_id}
    - **Type:** {file_type}
    - **File:** {FILE_TYPES[file_type]['dir']}/{filename}
    - **Tags:** {tags}
    - **Links:** _none yet_
    - **Summary:** [TODO: Write a 1-2 sentence summary that answers "do I need to open this file?"]
    - **Known issues:** None open
    """)
    print(fat_entry)

    # Append to INDEX-MASTER.md under the correct section
    master_path = brain_root / INDEX_MASTER
    master_content = read_file(master_path)

    section_header = f"## {file_type} Files"
    placeholder = f"_None yet._"

    # Find the section and insert
    if section_header in master_content:
        section_idx = master_content.index(section_header)
        # Find the placeholder or the next section
        rest = master_content[section_idx:]
        if placeholder in rest:
            # Replace placeholder with entry
            master_content = master_content.replace(
                section_header + "\n" + placeholder,
                section_header + "\n\n" + fat_entry.strip(),
                1,
            )
        else:
            # Append entry before next section (## heading)
            next_section = re.search(r"\n## ", rest[len(section_header):])
            if next_section:
                insert_pos = section_idx + len(section_header) + next_section.start()
                master_content = (
                    master_content[:insert_pos]
                    + "\n\n"
                    + fat_entry.strip()
                    + "\n"
                    + master_content[insert_pos:]
                )
            else:
                master_content += "\n\n" + fat_entry.strip() + "\n"

    # Update total-files count
    count_match = re.search(r"<!-- total-files: (\d+) -->", master_content)
    if count_match:
        old_count = int(count_match.group(1))
        master_content = master_content.replace(
            f"<!-- total-files: {old_count} -->",
            f"<!-- total-files: {old_count + 1} -->",
        )

    # Update timestamp
    master_content = re.sub(
        r"<!-- updated: .* -->",
        f"<!-- updated: {TODAY} -->",
        master_content,
    )

    write_file(master_path, master_content)
    print(f"Updated {INDEX_MASTER} (total files: {old_count + 1 if count_match else '?'}).")
    print(f"Estimated tokens for this file: ~{tokens}")
    print("\nIMPORTANT: Edit the [TODO] summary in INDEX-MASTER.md to complete the fat index entry.")

    # Update content hash manifest
    manifest = load_manifest(brain_root)
    rel_path = f"{FILE_TYPES[file_type]['dir']}/{filename}"
    manifest[rel_path] = {
        "hash": hash_file(file_path),
        "id": file_id,
        "updated": TODAY,
    }
    save_manifest(brain_root, manifest)
    print(f"Updated {HASH_MANIFEST} with content hash.")


def cmd_search(args):
    """Search fat indexes using BM25 ranking with structural boosts and link propagation."""
    brain_root = require_brain_root()
    query = args.query
    query_terms = [t.strip() for t in re.split(r"[\s,]+", query) if t.strip()]

    if not query_terms:
        print("ERROR: Empty query.")
        sys.exit(1)

    entries = collect_all_entries(brain_root)
    if not entries:
        print("No index entries found. Deposit some files first.")
        return

    # BM25 + structural boosts + link propagation
    scored = score_entries_bm25(entries, query_terms)

    if not scored:
        print(f'No results for "{query}".')
        print(f"Searched {len(entries)} index entries.")
        return

    print(f'Search results for "{query}" ({len(scored)} matches):\n')
    for rank, (score, entry) in enumerate(scored, 1):
        print(f"  {rank}. [{score:5.1f}] {entry['id']}")
        if "file" in entry:
            print(f"       File: {entry['file']}")
        if "tags" in entry:
            print(f"       Tags: {entry['tags']}")
        if "summary" in entry:
            summary = entry["summary"]
            if len(summary) > 120:
                summary = summary[:117] + "..."
            print(f"       {summary}")
        print()


def cmd_recall(args):
    """Search for relevant files and generate a RESET file."""
    brain_root = require_brain_root()
    task = args.task
    query_terms = [t.strip() for t in re.split(r"[\s,]+", task) if t.strip()]

    entries = collect_all_entries(brain_root)
    scored = score_entries_bm25(entries, query_terms)

    # Take top results (up to 10)
    top = scored[:10]

    # Estimate token costs
    total_tokens = 0
    file_lines = []
    for _score, entry in top:
        file_path = brain_root / entry.get("file", "")
        if file_path.exists():
            content = read_file(file_path)
            tokens = estimate_tokens(content)
            total_tokens += tokens
            line_count = content.count("\n") + 1
            file_lines.append(
                f"1. `{entry['id']}` — (full file, ~{line_count} lines, ~{tokens} tokens) — {entry.get('summary', 'no summary')[:80]}"
            )
        else:
            file_lines.append(
                f"1. `{entry['id']}` — (file not found: {entry.get('file', '?')}) — {entry.get('summary', 'no summary')[:80]}"
            )

    slug = re.sub(r"[^a-z0-9]+", "-", task.lower()).strip("-")[:40]
    reset_filename = f"RESET-{slug}-{TODAY}.md"
    reset_path = brain_root / "reset-files" / reset_filename

    reset_tokens = 500  # estimate for the reset file itself
    usable_context = 140000  # rough usable tokens

    reset_content = textwrap.dedent(f"""\
    # RESET — {task}
    <!-- generated: {TODAY} -->
    <!-- search-session: found {len(top)} relevant entries from {len(entries)} total -->

    ## Task Objective
    {task}

    ## Required Context Files (load these)
    {chr(10).join(file_lines) if file_lines else '_No matching files found._'}

    ## Key Decisions Already Made
    - [Review the files above and fill in relevant decisions]

    ## Relevant Learnings
    - [Review LEARN files and fill in relevant gotchas]

    ## Active Rules
    - [Review RULE files and fill in relevant rules]

    ## Estimated Context Load
    - ~{total_tokens} tokens for listed files
    - ~{reset_tokens} tokens for this reset file
    - = ~{total_tokens + reset_tokens} tokens total starting context
    - Remaining for work: ~{usable_context - total_tokens - reset_tokens:,} tokens
    """)

    write_file(reset_path, reset_content)
    print(f"Generated: {reset_path}")
    print(f"Included {len(top)} files, estimated ~{total_tokens + reset_tokens} tokens.")
    print(f"Remaining context budget: ~{usable_context - total_tokens - reset_tokens:,} tokens.")
    print("\nReview and edit the RESET file before using it in a work session.")


def cmd_status(args):
    """Project overview: file counts, index health, orphan detection."""
    brain_root = require_brain_root()

    print(f"Project Brain: {brain_root}\n")

    # Count files by type
    total = 0
    for file_type, info in FILE_TYPES.items():
        type_dir = brain_root / info["dir"]
        files = list(type_dir.glob(f"{file_type}-*.md"))
        count = len(files)
        total += count
        status = f"  {file_type:6s}  {count:3d} files   ({info['dir']}/)"
        print(status)

    print(f"  {'TOTAL':6s}  {total:3d} files")

    # Index health
    entries = collect_all_entries(brain_root)
    print(f"\nIndex entries: {len(entries)}")

    # Check for orphans (files without index entries)
    indexed_files = set()
    for e in entries:
        if "file" in e:
            indexed_files.add(e["file"])

    orphans = []
    for file_type, info in FILE_TYPES.items():
        if file_type == "RESET":
            continue  # RESET files don't need index entries
        type_dir = brain_root / info["dir"]
        for f in type_dir.glob(f"{file_type}-*.md"):
            relative = f"{info['dir']}/{f.name}"
            if relative not in indexed_files:
                orphans.append(relative)

    if orphans:
        print(f"\nOrphans (files without index entries): {len(orphans)}")
        for o in orphans:
            print(f"  - {o}")
    else:
        print("\nNo orphans detected. All files are indexed.")

    # Check for stale entries (index entries pointing to missing files)
    stale = []
    for e in entries:
        if "file" in e:
            file_path = brain_root / e["file"]
            if not file_path.exists():
                stale.append(f"{e['id']} -> {e['file']}")

    if stale:
        print(f"\nStale entries (index points to missing file): {len(stale)}")
        for s in stale:
            print(f"  - {s}")

    # Content hash manifest health
    manifest = load_manifest(brain_root)
    if manifest:
        # Count files on disk
        disk_files = build_manifest(brain_root)
        mismatches = []
        missing_from_manifest = []
        deleted_from_disk = []
        for rel, info in disk_files.items():
            if rel not in manifest:
                missing_from_manifest.append(rel)
            elif manifest[rel]["hash"] != info["hash"]:
                mismatches.append(rel)
        for rel in manifest:
            if rel not in disk_files:
                deleted_from_disk.append(rel)

        print(f"\nContent hash manifest: {len(manifest)} entries")
        if mismatches:
            print(f"  Changed since last hash: {len(mismatches)}")
            for m in mismatches:
                print(f"    - {m}")
        if missing_from_manifest:
            print(f"  Missing from manifest: {len(missing_from_manifest)}")
            for m in missing_from_manifest:
                print(f"    - {m}")
        if deleted_from_disk:
            print(f"  In manifest but deleted from disk: {len(deleted_from_disk)}")
            for d in deleted_from_disk:
                print(f"    - {d}")
        if not mismatches and not missing_from_manifest and not deleted_from_disk:
            print("  All hashes up to date.")
    else:
        print(f"\nNo content hash manifest. Run `brain reindex` to create one.")

    # Last modified
    all_md = list(brain_root.rglob("*.md"))
    if all_md:
        newest = max(all_md, key=lambda p: p.stat().st_mtime)
        mod_time = datetime.datetime.fromtimestamp(newest.stat().st_mtime)
        print(f"\nLast modified: {newest.name} ({mod_time.strftime('%Y-%m-%d %H:%M')})")

    # Token budget estimate
    master_path = brain_root / INDEX_MASTER
    if master_path.exists():
        master_tokens = estimate_tokens(read_file(master_path))
        print(f"INDEX-MASTER.md: ~{master_tokens} tokens")


def cmd_reindex(args):
    """Rebuild the content hash manifest from all brain files on disk."""
    brain_root = require_brain_root()

    old_manifest = load_manifest(brain_root)
    new_manifest = build_manifest(brain_root)

    # Compute diff
    new_files = []
    changed_files = []
    deleted_files = []

    for rel, info in new_manifest.items():
        if rel not in old_manifest:
            new_files.append(rel)
        elif old_manifest[rel]["hash"] != info["hash"]:
            changed_files.append(rel)

    for rel in old_manifest:
        if rel not in new_manifest:
            deleted_files.append(rel)

    # Print report
    print(f"Content hash reindex: {len(new_manifest)} files hashed\n")

    if new_files:
        print(f"New files (not in previous manifest): {len(new_files)}")
        for f in new_files:
            print(f"  + {f}")
        print()

    if changed_files:
        print(f"Changed files (hash differs): {len(changed_files)}")
        for f in changed_files:
            print(f"  ~ {f}")
        print()

    if deleted_files:
        print(f"Deleted files (in manifest but gone from disk): {len(deleted_files)}")
        for f in deleted_files:
            print(f"  - {f}")
        print()

    if not new_files and not changed_files and not deleted_files:
        print("No changes detected.")

    # Save updated manifest
    save_manifest(brain_root, new_manifest)
    print(f"\nManifest saved: {HASH_MANIFEST} ({len(new_manifest)} entries)")


def cmd_ingest(args):
    """Process a source document into LTM files.

    NOTE: Full AI-powered ingestion requires an LLM API call.
    This command provides the scaffolding: reads the source, estimates size,
    and creates stub files for manual or AI-assisted extraction.
    """
    brain_root = require_brain_root()
    source_path = Path(args.source)

    if not source_path.exists():
        print(f"ERROR: Source file not found: {source_path}")
        sys.exit(1)

    content = read_file(source_path)
    tokens = estimate_tokens(content)
    lines = content.count("\n") + 1

    print(f"Source: {source_path.name}")
    print(f"  Size: {len(content):,} chars, ~{lines} lines, ~{tokens:,} estimated tokens")
    print()

    if tokens > 100000:
        print("WARNING: Source is very large. Consider splitting it into sections first.")
        print()

    print("Ingestion is EXTRACTION, not storage.")
    print("A 40-page chapter should become ~5 files totaling ~300 lines.")
    print()
    print("Recommended process:")
    print("  1. Load this source into an LLM session")
    print("  2. Extract knowledge relevant to YOUR project")
    print("  3. Create typed LTM files using `brain deposit`")
    print("  4. Each file gets its own fat index entry")
    print()

    # Ask what types of knowledge to extract
    print("What types of knowledge should be extracted?")
    for ft, info in FILE_TYPES.items():
        if ft != "RESET":
            print(f"  {ft}: {info['purpose']}")

    print()
    types_input = input("Types to extract (comma-separated, e.g. LEARN,RULE,SPEC): ").strip()
    if not types_input:
        print("No types selected. Exiting.")
        return

    selected_types = [t.strip().upper() for t in types_input.split(",")]
    for st in selected_types:
        if st not in FILE_TYPES:
            print(f"WARNING: Unknown type '{st}', skipping.")
            continue

        file_id = next_id(brain_root, st)
        slug = re.sub(r"[^a-z0-9]+", "-", source_path.stem.lower()).strip("-")
        filename = f"{file_id}_from-{slug}.md"
        type_dir = brain_root / FILE_TYPES[st]["dir"]
        file_path = type_dir / filename

        template_path = brain_root / "templates" / f"TEMPLATE-{st}.md"
        if template_path.exists():
            tmpl_content = read_file(template_path)
            tmpl_content = tmpl_content.replace(f"{st}-NNN", file_id)
            tmpl_content = tmpl_content.replace("YYYY-MM-DD", TODAY)
            tmpl_content = tmpl_content.replace("[comma-separated tags]", f"ingested, {source_path.stem}")
        else:
            tmpl_content = f"# {file_id}\n<!-- type: {st} -->\n<!-- created: {TODAY} -->\n<!-- source: {source_path.name} -->\n\n"

        # Add source reference
        tmpl_content += f"\n\n<!-- Ingested from: {source_path.name} ({tokens:,} tokens) -->\n"

        write_file(file_path, tmpl_content)
        print(f"  Created stub: {file_path}")

    print(f"\nStub files created. Open them and extract knowledge from {source_path.name}.")
    print("Then update INDEX-MASTER.md with fat index entries for each new file.")


# ---------------------------------------------------------------------------
# CLI Argument Parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="brain",
        description="Project Brain — LLM Memory System CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init
    p_init = subparsers.add_parser("init", help="Initialize a project-brain directory")
    p_init.add_argument("name", help="Project name")

    # deposit
    p_dep = subparsers.add_parser("deposit", help="Add a new knowledge file")
    p_dep.add_argument("--type", "-t", required=True, help="File type (SPEC, CODE, RULE, LEARN, LOG)")
    p_dep.add_argument("--tags", required=True, help="Comma-separated tags")

    # search
    p_search = subparsers.add_parser("search", help="Search fat indexes")
    p_search.add_argument("query", help="Search query (tags, keywords)")

    # recall
    p_recall = subparsers.add_parser("recall", help="Generate a RESET file for a task")
    p_recall.add_argument("task", help="Task description")

    # status
    subparsers.add_parser("status", help="Project overview and health check")

    # reindex
    subparsers.add_parser("reindex", help="Rebuild content hash manifest from all brain files")

    # ingest
    p_ingest = subparsers.add_parser("ingest", help="Process source material into LTM files")
    p_ingest.add_argument("source", help="Path to source file")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "init": cmd_init,
        "deposit": cmd_deposit,
        "search": cmd_search,
        "recall": cmd_recall,
        "status": cmd_status,
        "reindex": cmd_reindex,
        "ingest": cmd_ingest,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
