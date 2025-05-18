#!/usr/bin/env python3
"""
Advanced Web Crawler – unlimited-crawl edition (header/footer skip)
=================================================================
• Crawls an entire site when `--depth` or `--max-pages` are omitted.
• **Ignores links and text inside <header>, <footer>, or <nav>** so it
  avoids re-crawling top/bottom navigation and keeps page content clean.
• Folder layout mirrors URL path:
    <output>/<domain>/<path-segments...>/{data|images|videos}
"""

from __future__ import annotations
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0

import os, re, json, time, uuid, logging, urllib.parse
from datetime import datetime
from typing import Any, Dict, List, Tuple

import requests
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from urllib.robotparser import RobotFileParser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("crawler.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def _is_limited(value: int | None) -> bool:
    """Return True when a positive limit is enforced."""
    return value is not None and value >= 0


class WebCrawler:
    """Crawl a whole domain while skipping header/footer/nav areas."""

    # ------------------------------------------------------------------
    # construction ------------------------------------------------------
    # ------------------------------------------------------------------
    def __init__(
        self,
        root_url: str,
        *,
        max_depth: int | None = None,
        max_pages: int | None = None,
        output_dir: str = "crawled_data",
        respect_robots: bool = True,
        rate_limit: float = 1.0,
        headless: bool = False,
        interactive_elements: bool = True,
        ajax_wait: int = 5,
        extract_inline_images: bool = True,
    ) -> None:
        self.root_url = root_url.rstrip("/")
        self.max_depth = None if not _is_limited(max_depth) else max_depth
        self.max_pages = None if not _is_limited(max_pages) else max_pages
        self.output_dir = output_dir
        self.respect_robots = respect_robots
        self.rate_limit = rate_limit
        self.interactive_elements = interactive_elements
        self.ajax_wait = ajax_wait
        self.extract_inline_images = extract_inline_images

        self.visited_urls: set[str] = set()
        self.discovered_urls: List[Dict[str, Any]] = []
        self.failed_urls: List[Tuple[str, str]] = []
        self.page_count = 0
        self.last_request_time = 0.0

        parsed_root = urllib.parse.urlparse(self.root_url)
        self.root_domain = parsed_root.netloc
        self.scheme = parsed_root.scheme or "https"

        self.robots_parser = RobotFileParser()
        if respect_robots:
            try:
                robots_url = f"{self.scheme}://{self.root_domain}/robots.txt"
                self.robots_parser.set_url(robots_url)
                self.robots_parser.read()
                logger.info("Loaded robots.txt: %s", robots_url)
            except Exception as exc:
                logger.warning("robots.txt load failed (%s)", exc)

        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument("--headless=new")
        self.chrome_options.add_argument("--start-maximized")
        self.chrome_options.add_argument("--disable-notifications")
        self.chrome_options.add_argument("--disable-popup-blocking")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--window-size=1200,800")
        self.driver: webdriver.Chrome | None = None

    # ------------------------------------------------------------------
    # helpers ------------------------------------------------------------
    # ------------------------------------------------------------------
    def start_driver(self):
        if not self.driver:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.set_page_load_timeout(30)

    def close_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def is_internal_url(self, url: str) -> bool:
        try:
            p = urllib.parse.urlparse(url)
            return p.netloc == self.root_domain or not p.netloc
        except Exception:
            return False

    def can_fetch(self, url: str) -> bool:
        return (not self.respect_robots) or self.robots_parser.can_fetch("*", url)

    def apply_rate(self):
        if self.rate_limit <= 0:
            return
        dt = self.rate_limit - (time.time() - self.last_request_time)
        if dt > 0:
            time.sleep(dt)
        self.last_request_time = time.time()

    def normalize_url(self, href: str, base: str) -> str | None:
        try:
            if not href.startswith(("http://", "https://")):
                href = urllib.parse.urljoin(base, href)
            return href.split("#")[0].rstrip("/")
        except Exception:
            return None

    # ------------------------------------------------------------------
    # folder path --------------------------------------------------------
    # ------------------------------------------------------------------
    def slugify(self, text: str) -> str:
        text = re.sub(r"\W+", "_", text.lower()).strip("_")
        return text[:50] or "page"

    def get_folder_path(self, url: str) -> str:
        p = urllib.parse.urlparse(url)
        parts = list(filter(None, p.path.split("/"))) or ["home"]
        slugs = [self.slugify(x) for x in parts]
        return os.path.join(self.output_dir, p.netloc.replace(".", "_"), *slugs)

    def make_dirs(self, url: str):
        base = self.get_folder_path(url)
        d, i, v = (os.path.join(base, p) for p in ("data", "images", "videos"))
        for path in (d, i, v):
            os.makedirs(path, exist_ok=True)
        return d, i, v

    # ------------------------------------------------------------------
    # skip-section utility ----------------------------------------------
    # ------------------------------------------------------------------
    @staticmethod
    def _in_skip_section(tag: Tag | None) -> bool:
        """Return True if *tag* is inside header/footer/nav."""
        if tag is None:
            return False
        return tag.find_parent(["header", "footer", "nav"]) is not None

    # ------------------------------------------------------------------
    # extract links ------------------------------------------------------
    # ------------------------------------------------------------------
    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        links: List[str] = []
        for a in soup.find_all("a", href=True):
            if self._in_skip_section(a):
                continue  # ignore header/footer/nav anchors
            href = a["href"].strip()
            if href.startswith(("javascript:", "mailto:", "tel:")):
                continue
            norm = self.normalize_url(href, base_url)
            if norm and self.is_internal_url(norm):
                links.append(norm)
                if norm not in {d["url"] for d in self.discovered_urls}:
                    self.discovered_urls.append({
                        "url": norm,
                        "text": a.get_text(strip=True) or None,
                        "source_url": base_url,
                    })
        return links

    # ------------------------------------------------------------------
    # extract text -------------------------------------------------------
    # ------------------------------------------------------------------
    def extract_text(self, soup: BeautifulSoup) -> str:
        for tag in soup(["script", "style", "header", "footer", "nav"]):
            tag.extract()
        text = soup.get_text(" ", strip=True)
        return re.sub(r"\s+", " ", text)

    # ------------------------------------------------------------------
    # page processing (shortened – heavy lift trunc)
    # ------------------------------------------------------------------
    def process_page(self, url: str, depth: int = 0) -> List[str]:
        if url in self.visited_urls:
            return []
        if _is_limited(self.max_depth) and depth > self.max_depth:
            return []
        if _is_limited(self.max_pages) and self.page_count >= self.max_pages:
            return []
        if not self.can_fetch(url):
            logger.info("Robots.txt disallow: %s", url)
            return []

        self.apply_rate()
        self.visited_urls.add(url)
        self.page_count += 1
        logger.info("[%d] %s", self.page_count, url)

        try:
            self.start_driver()
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(self.ajax_wait)
            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            # skip non-English quickly ----------------------------------
            sample = soup.get_text(" ", strip=True)[:1000]
            try:
                if detect(sample) != "en":
                    return []
            except Exception:
                pass

            data_dir, images_dir, videos_dir = self.make_dirs(url)
            page_data = {
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "content": self.extract_text(soup),
                "images": [],
                "videos": [],
            }
            with open(os.path.join(data_dir, "page_data.json"), "w", encoding="utf-8") as f:
                json.dump(page_data, f, indent=2, ensure_ascii=False)

            return self.extract_links(soup, url)
        except Exception as exc:
            logger.error("Error processing %s: %s", url, exc)
            self.failed_urls.append((url, str(exc)))
            return []

    # ------------------------------------------------------------------
    # crawl loop ---------------------------------------------------------
    # ------------------------------------------------------------------
    def crawl(self):
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            queue: List[Tuple[str, int]] = [(self.root_url, 0)]
            while queue and (not _is_limited(self.max_pages) or self.page_count < self.max_pages):
                url, depth = queue.pop(0)
                for link in self.process_page(url, depth):
                    if link not in self.visited_urls:
                        queue.append((link, depth + 1))
            with open(os.path.join(self.output_dir, "all_discovered_urls.json"), "w", encoding="utf-8") as f:
                json.dump(self.discovered_urls, f, indent=2)
        finally:
            self.close_driver()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser("Crawl site, skipping header/footer/nav content & links")
    ap.add_argument("url")
    ap.add_argument("--depth", type=int)
    ap.add_argument("--max-pages", type=int)
    ap.add_argument("--output", default="crawled_data")
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--rate-limit", type=float, default=1.0)
    args = ap.parse_args()

    crawler = WebCrawler(
        root_url=args.url,
        max_depth=args.depth,
        max_pages=args.max_pages,
        output_dir=args.output,
        headless=args.headless,
        rate_limit=args.rate_limit,
    )
    crawler.crawl()
