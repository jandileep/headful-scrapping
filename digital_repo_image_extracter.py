#!/usr/bin/env python3
"""
Digital Repo Image Extractor – v2.5

Key changes
─────────────────
• Accepts images whose URL path contains **/paintingimage/** or **/digirepo/**  (unchanged) **or /digitalfilesicweb/** (v2.4)
• NEW (v2.5): Detects canonical image URLs declared in the page head via
  `<meta property="og:image" …>` or `<link rel="image_src" …>` (plus
  `twitter:image`) so that those images are also downloaded when they match
  the `_ALLOWED_PATH_KEYS` rules.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from media_extractor import MediaExtractor

logger = logging.getLogger("DigitalRepoImageExtractor")

_IMAGE_EXTS = (
    ".jpg", ".jpeg", ".png", ".gif",
    ".webp", ".tif", ".tiff", ".bmp", ".svg"
)

# ──────────────────────────────────────────────────────────────
# Every URL‑path substring that makes an image eligible
# Added "/digitalfilesicweb/" for og:image URLs like
# “…/system/files/digitalFilesICWeb/…jpg”
# ──────────────────────────────────────────────────────────────
_ALLOWED_PATH_KEYS = (
    "/digirepo/",
    "/paintingimage/",
    "/digitalfilesicweb/",   # ← NEW (v2.4)
)


class DigitalRepoImageExtractor(MediaExtractor):
    """
    Downloads every image whose URL path contains any element of
    `_ALLOWED_PATH_KEYS` (case‑insensitive) and passes the usual
    MediaExtractor filters.  If *repo_id* is supplied, the stricter
    “…/digirepo/<repo_id>/…” rule is enforced **only** for digirepo paths.
    """

    def __init__(
        self,
        url: str,
        output_dir: str | Path,
        repo_id: int | None = None,
        *,
        seed_urls: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        headers: dict | None = None,
    ):
        self.repo_id = repo_id
        self._seed_urls = list({*(seed_urls or [])})  # de‑dupe, keep order
        self.exclude_patterns = exclude_patterns or [
            "sprite", "placeholder", "thumb"
        ]

        super().__init__(
            url,
            output_dir,
            file_patterns=list(_ALLOWED_PATH_KEYS),
            exclude_patterns=self.exclude_patterns,
            headers=headers,
        )

    # ─────────────────── helpers ────────────────────
    def _path_ok(self, path: str) -> bool:
        """Return True if *path* meets every rule."""
        p = path.lower()

        # must include one of the allowed substrings
        if not any(key in p for key in _ALLOWED_PATH_KEYS):
            return False

        # optional repo‑specific filtering, but only for digirepo
        if self.repo_id is not None and "/digirepo/" in p:
            if f"/digirepo/{self.repo_id}/" not in p:
                return False

        if any(bad in p for bad in self.exclude_patterns):
            return False

        return p.endswith(_IMAGE_EXTS)
    
    def download_media(self, urls: set[str] | list[str]):
        urls = sorted(urls)
        if not urls:
            logger.info("No URLs to download.")
            return

        logger.info("Downloading the following URLs:")
        for u in urls:
            logger.info("📥 %s", u)

        super().download_media(urls)


    def _collect_from_soup(self, soup: BeautifulSoup, found: set[str]):
        """DOM scan for <img>, <source>, lazy‑load attrs, canonical tags—and gallery anchors."""

        def add(candidate: str):
            abs_u = urljoin(self.url, candidate)
            if self._path_ok(urlparse(abs_u).path):
                found.add(abs_u)

        # ①  <img> / <source> tags and their variants
        for tag in soup.find_all(["img", "source"]):
            if (src := tag.get("src")):
                add(src)

            # common lazy‑load attributes
            for attr in (
                "data-src", "data-lazy-src",
                "data-original", "data-srcset"
            ):
                if (val := tag.get(attr)):
                    for piece in val.split(","):
                        add(piece.strip().split()[0])

            if (srcset := tag.get("srcset")):
                for item in srcset.split(","):
                    add(item.strip().split()[0])

        # ②  Canonical/Open‑Graph/Twitter image declarations
        for tag in soup.find_all("meta", attrs={"property": "og:image"}):
            if (content := tag.get("content")):
                add(content)
        for tag in soup.find_all("meta", attrs={"name": "twitter:image"}):
            if (content := tag.get("content")):
                add(content)

        # ③  <link rel="image_src" href="…"> (older convention)
        for tag in soup.find_all("link"):
            rel = tag.get("rel") or []
            if any(r.lower() == "image_src" for r in rel):
                if (href := tag.get("href")):
                    add(href)

        # ── NEW ──
        # ④  Gallery anchors inside <div class="row">
        for div in soup.find_all("div", class_="row"):
            for a in div.find_all("a", attrs={"data-magnify": "gallery"}):
                if (href := a.get("href")):
                    add(href)

    # ─────────────────── main entrypoint ────────────────────
    def crawl(self, *, headless: bool = True):
        """
        • If *seed_urls* were provided, download them immediately.
        • Otherwise use Selenium + DOM + network‑log strategy.
        """
        if self._seed_urls:
            logger.info("Downloading %d pre‑supplied image(s)…", len(self._seed_urls))
            self.download_media(self._seed_urls)
            return

        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        opts = Options()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
        opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        driver = webdriver.Chrome(options=opts)
        try:
            logger.info("▶ Visiting %s", self.url)
            driver.get(self.url)

            found: set[str] = set()

            # 1️⃣  DevTools network log
            for entry in driver.get_log("performance"):
                try:
                    msg = json.loads(entry["message"]) ["message"]
                    if msg["method"] == "Network.responseReceived":
                        u = msg["params"]["response"]["url"]
                        if self._path_ok(urlparse(u).path):
                            found.add(u)
                except Exception:
                    continue

            # 2️⃣  DOM pass
            soup = BeautifulSoup(driver.page_source, "html.parser")
            self._collect_from_soup(soup, found)

            logger.info("Found %d matching image(s)", len(found))
            if found:
                self.download_media(found)
            else:
                logger.info("No eligible images detected.")
        finally:
            driver.quit()


# ───────────────────────── CLI helper ─────────────────────────
if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="Download images under …/digirepo/…, …/paintingimage/… or …/digitalfilesicweb/… paths, including canonical og:image declarations."
    )
    ap.add_argument("--url", required=True, help="Page URL to scan")
    ap.add_argument("--out", default="images_digirepo", help="Output directory")
    ap.add_argument("--repo-id", type=int, help="Optional digirepo repository ID filter")
    ap.add_argument("--headless", action="store_true", help="Run the browser in headless mode")
    args = ap.parse_args()

    DigitalRepoImageExtractor(
        args.url,
        args.out,
        repo_id=args.repo_id,
    ).crawl(headless=args.headless)
