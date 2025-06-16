#!/usr/bin/env python3
"""
HTML Crawler Module

This module provides the HtmlCrawler class for recursively crawling websites
and extracting structured HTML content.
"""

import os
import re
import json
import time
import logfire as logger
import sys
from urllib.error import URLError, HTTPError
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Import from other modules
from combined_crawler import WebsiteCrawler, dedupe_links, extract_slug_from_url
from html_content_extractor import HtmlContentExtractor


class HtmlCrawler:
    """Class to handle recursive crawling of websites with HTML content extraction"""

    def __init__(self, max_depth=2, delay=3, headless=True, respect_robots_txt=True):
        self.max_depth = max_depth
        self.delay = delay
        self.headless = headless
        self.respect_robots_txt = respect_robots_txt
        self.crawled_urls = set()
        self.robots_cache = {}
        logger.info(f"Initialized HtmlCrawler with max_depth={max_depth}, delay={delay}s")

    def get_robots_parser(self, url):
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        if base_url in self.robots_cache:
            return self.robots_cache[base_url]

        rp = RobotFileParser()
        robots_url = f"{base_url}/robots.txt"
        try:
            rp.set_url(robots_url)
            rp.read()
            self.robots_cache[base_url] = rp
            return rp
        except Exception as e:
            logger.warning(f"Error reading robots.txt for {base_url}: {str(e)}")
            permissive_parser = RobotFileParser()
            permissive_parser.parse(['User-agent: *', 'Allow: /'])
            self.robots_cache[base_url] = permissive_parser
            return permissive_parser

    def can_fetch(self, url):
        if not self.respect_robots_txt:
            return True
        try:
            rp = self.get_robots_parser(url)
            return rp.can_fetch("*", url)
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {str(e)}")
            return True

    def sanitize_title_for_folder_name(self, title):
        try:
            if not title or title == "Title not found":
                return None
            title = re.split(r'\s*[\|\-\:]\s*', title)[0].strip()
            words = title.split()
            if len(words) > 5:
                title = ' '.join(words[:5])
            slug = re.sub(r'[^a-zA-Z0-9_-]', '_', title.replace(' ', '_'))
            if len(slug) > 100:
                slug = slug[:100]
            if not slug:
                return None
            return slug
        except Exception as e:
            logger.error(f"Error sanitizing title for folder name: {str(e)}")
            return None

    def sanitize_url_for_folder_name(self, url):
        try:
            parsed_url = urlparse(url)
            path = parsed_url.path
            if path:
                if path.endswith('/'):
                    path = path[:-1]
                path_parts = path.split('/')
                last_part = path_parts[-1] if path_parts[-1] else (path_parts[-2] if len(path_parts) > 1 else "")
                if last_part:
                    text_name = last_part.replace('-', ' ').replace('_', ' ')
                    if '.' in text_name:
                        text_name = text_name.split('.')[0]
                    text_name = ' '.join(word.capitalize() for word in text_name.split())
                    slug = re.sub(r'[^a-zA-Z0-9_-]', '_', text_name.replace(' ', '_'))
                    if len(slug) > 100:
                        slug = slug[:100]
                    return slug

            domain = parsed_url.netloc.replace('www.', '')
            domain_parts = domain.split('.')
            if domain_parts:
                domain_name = domain_parts[0].capitalize()
                slug = re.sub(r'[^a-zA-Z0-9_-]', '_', domain_name)
                timestamp = int(time.time())
                slug = f"{slug}_{timestamp}"
                if len(slug) > 100:
                    slug = slug[:100]
                return slug

            timestamp = int(time.time())
            return f"Web_Page_{timestamp}"
        except Exception as e:
            logger.error(f"Error sanitizing URL for folder name: {str(e)}")
            timestamp = int(time.time())
            return f"Web_Page_{timestamp}"

    def parse_links_file(self, links_file):
        try:
            with open(links_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            valid_urls = []
            for link in data.get("links", []):
                url = link.get("url")
                if url and isinstance(url, str) and url.startswith(('http://', 'https://')):
                    valid_urls.append(url)
            logger.info(f"Parsed {len(valid_urls)} valid URLs from {links_file}")
            return valid_urls
        except Exception as e:
            logger.error(f"Error parsing links file {links_file}: {str(e)}")
            return []

    def crawl_url_recursive(self, url, current_depth=0, parent_folder=""):
        if url in self.crawled_urls:
            logger.info(f"URL already crawled, skipping: {url}")
            return True
        if not self.can_fetch(url):
            logger.info(f"URL disallowed by robots.txt, skipping: {url}")
            return True
        self.crawled_urls.add(url)
        if current_depth > self.max_depth:
            logger.info(f"Reached maximum depth ({self.max_depth}), stopping recursion for: {url}")
            return True

        logger.info(f"Crawling URL: {url} (Depth: {current_depth}/{self.max_depth})")
        crawler = WebsiteCrawler(headless=self.headless)

        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                logger.info(f"URL modified to include protocol: {url}")

            content_data, links_data = crawler.crawl(url)

            title = content_data.get("title", "")
            slug = self.sanitize_title_for_folder_name(title)
            if not slug:
                slug = self.sanitize_url_for_folder_name(url)

            output_folder = os.path.join(parent_folder, slug) if parent_folder else slug
            logger.info(f"Output folder: {output_folder}")

            images_folder = os.path.join(output_folder, "images")
            os.makedirs(images_folder, exist_ok=True)

            logger.info(f"Extracting HTML content from {url}")

            options = Options()
            if self.headless:
                options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            content_driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )

            try:
                content_driver.get(url)
                content_driver.implicitly_wait(10)
                html_extractor = HtmlContentExtractor(url, output_folder)
                html_content = html_extractor.extract_content_from_driver(content_driver)

                content_data["url"] = url
                content_data["paragraphs"] = html_content["paragraphs"]
                content_data["images"] = html_content["images"]
                content_data["content_type"] = html_content["content_type"]

                logger.info(f"Extracted {len(html_content['paragraphs'])} paragraphs and {len(html_content['images'])} images")

            except Exception as e:
                logger.error(f"Error extracting HTML content from {url}: {str(e)}")
                content_data["paragraphs"] = []
                content_data["images"] = []
                content_data["content_type"] = "html"
            finally:
                content_driver.quit()

            content_filename = os.path.join(output_folder, "output_content.json")
            links_filename = os.path.join(output_folder, "output_links.json")

            links_data = dedupe_links(links_data)

            crawler.save_to_json(content_data, content_filename)
            crawler.save_to_json(links_data, links_filename)

            logger.info(f"Results saved in directory: {output_folder}/")

            if current_depth < self.max_depth:
                urls_to_crawl = self.parse_links_file(links_filename)
                for i, next_url in enumerate(urls_to_crawl):
                    logger.info(f"Processing link {i+1}/{len(urls_to_crawl)} from {url}")
                    if i > 0:
                        logger.info(f"Waiting {self.delay} seconds before next request...")
                        time.sleep(self.delay)
                    self.crawl_url_recursive(next_url, current_depth + 1, output_folder)

            return True

        except HTTPError as e:
            logger.error(f"HTTP Error during crawling {url}: {e.code} - {e.reason}")
            return False
        except URLError as e:
            logger.error(f"URL Error during crawling {url}: {str(e.reason)}")
            return False
        except WebDriverException as e:
            logger.error(f"WebDriver Error during crawling {url}: {str(e)}")
            return False
        except TimeoutException:
            logger.error(f"Timeout Error during crawling {url}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during crawling {url}: {str(e)}")
            return False
        finally:
            crawler.close()

    def start_crawling(self, start_url):
        logger.info(f"Starting recursive crawling from URL: {start_url}")
        logger.info(f"Maximum depth: {self.max_depth}, Delay between requests: {self.delay}s")
        start_time = time.time()
        result = self.crawl_url_recursive(start_url)
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Recursive crawling completed in {duration:.2f} seconds")
        logger.info(f"Total URLs crawled: {len(self.crawled_urls)}")
        return result
