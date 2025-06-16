#!/usr/bin/env python3
"""
Crawl “Indian Culture – Artefacts & Museums” in parallel with 4 processes.

1. Fetch the main overview page once.
2. Split the page range 0-4531 into four contiguous slices.
3. Give each slice to its own process so all four CPU cores stay busy.
4. All output (JSON, images, …) is stored under artefacts-museums/
"""

from multiprocessing import Process, set_start_method
from pathlib import Path
import os
import subprocess
import sys

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
SCRIPT = "../integrated_crawler_html.py"          # path to your crawler
ROOT_URL = "https://indianculture.gov.in/artefacts-museums"
TARGET_DIR = "artefacts-museums"
TOTAL_PAGES = 4531        # highest page index
WORKERS = 4               # exactly four parallel processes
# --------------------------------------------------------------------------- #


def crawl_page(url: str) -> None:
    """Run the crawler script once for a single URL."""
    subprocess.run([sys.executable, SCRIPT, url, "--headless"], check=True)


def crawl_range(start: int, end: int) -> None:
    """Worker: crawl every page from *start* to *end* (inclusive)."""
    for page in range(start, end + 1):
        url = f"{ROOT_URL}?search_api_fulltext=&page={page}"
        print(f"➡️  PID {os.getpid()} – Page {page}")
        crawl_page(url)


def main() -> None:
    # Create / switch into target directory so outputs stay organised
    Path(TARGET_DIR).mkdir(parents=True, exist_ok=True)
    os.chdir(TARGET_DIR)

    # First grab the overview page (single call)
    print("🎨 Crawling the main museum collections page…")
    crawl_page(ROOT_URL)
    print("✅ Finished crawling the museum collections overview page.")

    # Compute slice boundaries for each worker
    pages = TOTAL_PAGES + 1         # include page 0
    base = pages // WORKERS
    extra = pages % WORKERS         # remainder pages to distribute

    procs = []
    start = 0
    for w in range(WORKERS):
        end = start + base - 1
        if w < extra:               # give one extra page to first *extra* workers
            end += 1
        p = Process(target=crawl_range, args=(start, end))
        p.start()
        procs.append(p)
        start = end + 1

    # Wait for all workers
    for p in procs:
        p.join()

    print("🏁 All pages crawled with", WORKERS, "parallel workers.")


if __name__ == "__main__":
    # ‘spawn’ is cross-platform (Windows/macOS); Linux silently uses fork when faster
    set_start_method("spawn", force=True)
    main()
