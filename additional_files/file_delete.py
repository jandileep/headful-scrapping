#!/usr/bin/env python3
"""
purge_extras.py
────────────────
Delete **everything except**

* the folder named  images/   (and its entire contents)
* output_content.json
* output_links.json

within a crawl-tree.

Only *files* are removed; empty directories (other than images/) are removed
at the end to keep the tree tidy.

Usage
-----
python purge_extras.py <crawl_root>  [--dry-run]

• --dry-run   → show what would be deleted without actually removing anything
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

KEEP_FILES = {"output_content.json", "output_links.json"}
KEEP_DIR   = "images"


# ───────────────────────── helpers ──────────────────────────
def should_skip_dir(path: Path) -> bool:
    """Return True if *path* is (or is inside) an images/ directory."""
    parts = [p.lower() for p in path.parts]
    return KEEP_DIR in parts


def purge(root: Path, dry_run: bool = False) -> list[Path]:
    """
    Delete unwanted files; return list of deleted paths.
    """
    removed: list[Path] = []

    # First pass: remove files
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        if current.name.lower() == KEEP_DIR:
            # skip walking inside images/
            dirnames[:] = []
            continue

        for fname in filenames:
            if fname in KEEP_FILES:
                continue
            target = current / fname
            removed.append(target)
            if not dry_run:
                try:
                    target.unlink()
                except Exception as exc:
                    print(f"⚠️  Could not delete {target}: {exc}")

    # Second pass: remove empty directories (except images/)
    for dirpath, dirnames, _ in os.walk(root, topdown=False):
        current = Path(dirpath)
        if current.name.lower() == KEEP_DIR:
            continue
        # if directory now empty, remove it
        if not any(Path(dirpath).iterdir()):
            removed.append(current)
            if not dry_run:
                try:
                    current.rmdir()
                except Exception as exc:
                    print(f"⚠️  Could not remove dir {current}: {exc}")

    return removed


# ───────────────────────── main ──────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Clean crawl tree of extra files")
    parser.add_argument("crawl_root", help="Top-level directory of the crawl")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without deleting anything",
    )
    args = parser.parse_args()

    root = Path(args.crawl_root).resolve()
    if not root.is_dir():
        sys.exit(f"❌  {root} is not a directory")

    removed = purge(root, dry_run=args.dry_run)

    action = "WOULD delete" if args.dry_run else "Deleted"
    for p in removed:
        print(f"{action}: {p.relative_to(root)}")

    summary = f"{'Would remove' if args.dry_run else 'Removed'} {len(removed)} items."
    print(f"\n✅  {summary}")


if __name__ == "__main__":
    main()
