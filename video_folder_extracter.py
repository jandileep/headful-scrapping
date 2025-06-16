#!/usr/bin/env python3
"""
Download embedded videos right into the sub-folder that contains
the corresponding output_content.json.

Usage
-----
    python download_videos.py /path/to/main_folder  --headless  --delay 3
"""

import argparse
import json
import logging
import os
import sys
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# ─────────────────────────  Selenium helper  ────────────────────────── #
def get_driver(headless: bool) -> webdriver.Chrome:
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=opts)


# ────────────────────  Extract all <video>/<source> src  ─────────────── #
def extract_video_sources(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []

    for video in soup.find_all("video"):
        if video.get("src"):
            links.append(urljoin(base_url, video["src"]))

        for src in video.find_all("source"):
            if src.get("src"):
                links.append(urljoin(base_url, src["src"]))

    # unique order-preserving
    seen = set()
    return [x for x in links if not (x in seen or seen.add(x))]


# ─────────────────────────────  Downloader  ──────────────────────────── #
def download(url: str, dest_folder: str):
    os.makedirs(dest_folder, exist_ok=True)
    filename = os.path.basename(urlparse(url).path) or "video.mp4"
    path = os.path.join(dest_folder, filename)

    if os.path.exists(path):
        logging.info("↳ already have %s", path)
        return

    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(path, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
        logging.info("✓ saved %s", path)
    except Exception as e:
        logging.warning("✗ %s – %s", url, e)


# ───────────────────────────  One sub-folder  ────────────────────────── #
def handle_subfolder(subdir: str, driver: webdriver.Chrome, delay: float):
    json_fp = os.path.join(subdir, "output_content.json")
    if not os.path.isfile(json_fp):
        return

    try:
        with open(json_fp, "r", encoding="utf-8") as f:
            data = json.load(f)
        url = data.get("url")
        if not url:
            return
    except Exception as e:
        logging.warning("Bad JSON in %s – %s", json_fp, e)
        return

    logging.info("Crawling %s", url)
    try:
        driver.get(url)
        time.sleep(delay)
        html = driver.page_source
    except Exception as e:
        logging.warning("Selenium error @ %s – %s", url, e)
        return

    videos_dir = os.path.join(subdir, "videos")        # ← store right here
    for src in extract_video_sources(html, url):
        download(src, videos_dir)


# ───────────────────────────────  Main  ──────────────────────────────── #
def main():
    p = argparse.ArgumentParser(description="Download videos into their own sub-folders.")
    p.add_argument("root", help="Root directory produced by the previous crawler.")
    p.add_argument("--headless", action="store_true", help="Run Chrome headless.")
    p.add_argument("--delay", type=float, default=3, help="Seconds wait after load.")
    args = p.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        sys.exit(f"Folder not found: {root}")

    logging.basicConfig(format="%(levelname)s %(message)s", level=logging.INFO)
    driver = get_driver(args.headless)

    try:
        for dirpath, _, filenames in os.walk(root):
            if "output_content.json" in filenames:
                handle_subfolder(dirpath, driver, args.delay)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
