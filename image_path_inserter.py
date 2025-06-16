#!/usr/bin/env python3

import argparse
import json
import mimetypes
from pathlib import Path


def gather_images(img_dir: Path, crawl_root: Path) -> list:
    """Collect image file data to insert into output_content.json"""
    images = []
    for img in sorted(img_dir.glob("*")):
        if img.is_file():
            rel_path = img.relative_to(crawl_root).as_posix()
            content_type = mimetypes.guess_type(img.name)[0] or "application/octet-stream"
            images.append({
                "url": "",  # External link not available
                "local_path": rel_path,
                "content_type": content_type
            })
    return images


def process_directory(page_dir: Path, crawl_root: Path) -> bool:
    json_path = page_dir / "output_content.json"
    img_dir = page_dir / "images"

    if not json_path.exists() or not img_dir.is_dir():
        return False

    images = gather_images(img_dir, crawl_root)
    if not images:
        return False

    data = json.loads(json_path.read_text(encoding="utf-8"))
    data["images"] = images
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def recursive_update(root: Path) -> int:
    updated = 0
    for dir_path in root.rglob("*"):
        if dir_path.is_dir():
            if process_directory(dir_path, root):
                updated += 1
    # Also process the root itself in case it's a crawl directory
    if process_directory(root, root):
        updated += 1
    return updated


def main():
    parser = argparse.ArgumentParser(description="Update images field in output_content.json with local image links")
    parser.add_argument("target_dir", help="Directory to begin scan (itself or subfolders may have content)")
    args = parser.parse_args()

    root = Path(args.target_dir).resolve()
    if not root.is_dir():
        parser.error(f"{root} is not a directory")

    count = recursive_update(root)
    print(f"✓ Updated {count} directories with image entries.")


if __name__ == "__main__":
    main()
