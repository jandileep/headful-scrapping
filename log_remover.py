#!/usr/bin/env python3
"""
Delete any file whose name contains 'logo' (case-insensitive) inside every
'images' subfolder found beneath the supplied directory.
"""

import argparse
import os
from pathlib import Path

def delete_logo_files(root_dir: Path) -> None:
    """
    Recursively walk root_dir.  Whenever a directory named 'images' is found,
    remove every file inside it whose filename (not path) contains 'logo',
    case-insensitively.
    """
    for current_dir, dirs, files in os.walk(root_dir):
        # Only act when we are *inside* an images directory
        if Path(current_dir).name.lower() == "images":
            for fname in files:
                if "logo" in fname.lower():
                    fpath = Path(current_dir) / fname
                    try:
                        fpath.unlink()          # delete the file
                        print(f"Deleted: {fpath}")
                    except Exception as e:
                        print(f"Could not delete {fpath}: {e}")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recursively delete files containing 'logo' in every "
                    "'images' folder under the given directory."
    )
    parser.add_argument(
        "folder",
        type=Path,
        help="Root folder to start the search (relative or absolute path)",
    )
    args = parser.parse_args()

    if not args.folder.exists():
        parser.error(f"{args.folder} does not exist.")
    if not args.folder.is_dir():
        parser.error(f"{args.folder} is not a directory.")

    delete_logo_files(args.folder.resolve())

if __name__ == "__main__":
    main()
