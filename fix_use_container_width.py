"""
fix_use_container_width.py
==========================
One-time migration for Streamlit >= 1.40.

Replaces the deprecated `use_container_width` parameter with the new `width`
parameter across every .py file in the dashboard:

    use_container_width=True   ->  width="stretch"
    use_container_width=False  ->  width="content"

Usage (run from the dashboard root):
    python fix_use_container_width.py

It scans the current folder recursively, skips virtualenvs / caches, edits
files in place, and prints a summary of what changed. Safe to run more than
once (idempotent — nothing left to change on a second run).
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Folders we never want to touch
SKIP_DIRS = {".venv", "venv", "__pycache__", ".git", "node_modules", ".streamlit"}

# Order matters: handle explicit True/False first, then any stray bare uses.
REPLACEMENTS = [
    (re.compile(r"use_container_width\s*=\s*True"),  'width="stretch"'),
    (re.compile(r"use_container_width\s*=\s*False"), 'width="content"'),
]


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def main() -> None:
    py_files = [p for p in ROOT.rglob("*.py")
                if not should_skip(p) and p.name != Path(__file__).name]

    total_files_changed = 0
    total_replacements = 0

    for path in py_files:
        text = path.read_text(encoding="utf-8")
        original = text
        file_count = 0
        for pattern, repl in REPLACEMENTS:
            text, n = pattern.subn(repl, text)
            file_count += n
        if text != original:
            path.write_text(text, encoding="utf-8")
            rel = path.relative_to(ROOT)
            print(f"  {rel}  ({file_count} replaced)")
            total_files_changed += 1
            total_replacements += file_count

    print("-" * 50)
    if total_replacements == 0:
        print("Nothing to change — no use_container_width found. All clean.")
    else:
        print(f"Done: {total_replacements} replacements across "
              f"{total_files_changed} file(s).")
        print("Restart Streamlit to see the change: streamlit run app.py")


if __name__ == "__main__":
    main()
