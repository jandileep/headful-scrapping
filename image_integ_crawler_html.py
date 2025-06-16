#!/usr/bin/env python3
"""
Integrated HTML-and-Asset Crawler  – v2
✨  Now also scrapes each page’s HTML with Beautiful Soup and, when it finds a
    canonical image URL (link[rel=image_src] or meta[property=og:image]),
    passes that URL straight to DigitalRepoImageExtractor so the file is saved
    beside any indcultureImages/digirepo assets.

Usage (unchanged):
    python image_integr_html.py https://indianculture.gov.in/food-and-culture
    python image_integr_html.py ./my_crawl_root --headless
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from urllib.parse import urljoin, urlparse
import logging
from bs4 import BeautifulSoup

from combined_crawler import dedupe_command
from crawler_html import HtmlCrawler
from digital_repo_image_extracter import DigitalRepoImageExtractor   # ⬅ updated module name

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("integrated_crawler_html.log"),
              logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("IntegratedHtmlCrawler")


# ───────────────────────── helper utilities ──────────────────────────
def is_probable_url(value: str) -> bool:
    """Very small heuristic to decide whether *value* looks like a URL."""
    return urlparse(value).scheme in {"http", "https"}


def walk_output_content(folder_root: str):
    """Yield (path, parsed-json) for every *output_content.json* under *folder_root*."""
    for dirpath, _, filenames in os.walk(folder_root):
        if "output_content.json" in filenames:
            path = os.path.join(dirpath, "output_content.json")
            try:
                with open(path, encoding="utf-8") as f:
                    yield path, json.load(f)
            except Exception as exc:
                logger.warning("Skipping malformed %s – %s", path, exc)


# ───────────────────────── soup-level scraping ────────────────────────
def extract_image_urls_from_html(html: str, base_url: str) -> list[str]:
    """
    Pull any obvious ‘primary’ images from the page.

    Priority order:
      • <link rel="image_src" href="…">
      • <meta property="og:image" content="…">
      • <meta property="og:image:url" …> / og:image:secure_url
    """
    soup = BeautifulSoup(html, "html.parser")
    found: set[str] = set()

    # link[rel=image_src]
    for link in soup.find_all("link", rel=lambda v: v and "image_src" in v):
        if href := link.get("href"):
            found.add(urljoin(base_url, href))

    # Open-Graph variants
    for prop in ("og:image", "og:image:url", "og:image:secure_url"):
        for meta in soup.find_all("meta", property=prop):
            if content := meta.get("content"):
                found.add(urljoin(base_url, content))

    

    return list(found)


def extract_images_from_folder(folder_root: str, headless: bool):

    """Folder-mode: pull HTML-derived image URLs and pass them to the extractor."""
    processed = 0
    for json_path, data in walk_output_content(folder_root):
        url = data.get("url")
        html = data.get("html")          # HtmlCrawler stores raw markup here
        if not (url and html):
            logger.debug("output_content.json missing 'url' or 'html' – %s", json_path)
            continue

        image_urls = extract_image_urls_from_html(html, url)
        if not image_urls:
            logger.debug("No canonical image URL in %s", url)

        out_dir = os.path.join(os.path.dirname(json_path), "images")
        os.makedirs(out_dir, exist_ok=True)

        logger.info("⬇️  [%s]  ➜  %s  (seed=%d)", url, out_dir, len(image_urls))
        try:
            extractor = DigitalRepoImageExtractor(
                url,
                out_dir,
                seed_urls=image_urls            # ⬅ inject here
            )
            extractor.crawl(headless=headless)
            processed += 1
        except Exception as exc:
            logger.error("Image extraction failed for %s – %s", url, exc)

    logger.info("Done. Processed %d output_content.json files.", processed)


# ─────────────────────────────── main ─────────────────────────────────
def main() -> None:
    p = argparse.ArgumentParser(
        description="Integrated HTML crawler + indcultureImages extractor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("target", help="URL to crawl *or* folder of output_content.json files")
    p.add_argument("--headless", action="store_true", help="Run Chrome headless")
    p.add_argument("--max-depth", type=int, default=2)
    p.add_argument("--delay", type=int, default=3)
    p.add_argument("--no-robots", action="store_true")
    p.add_argument("--dedupe-file")
    p.add_argument("--output")
    p.add_argument("--log-level", default="INFO",
                   choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    args = p.parse_args()
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    if args.dedupe_file:
        dedupe_command(argparse.Namespace(input=args.dedupe_file, output=args.output))
        return

    # Decide mode
    if os.path.isdir(args.target) and not is_probable_url(args.target):
        extract_images_from_folder(args.target, headless=args.headless)
    else:
        crawler = HtmlCrawler(
            max_depth=args.max_depth,
            delay=args.delay,
            headless=args.headless,
            respect_robots_txt=not args.no_robots,
        )
        crawler.start_crawling(args.target)


if __name__ == "__main__":
    main()
