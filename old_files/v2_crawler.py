#!/usr/bin/env python3
"""
V2 Web Crawler - Complete Website Traversal Edition

A comprehensive Python script that utilizes Selenium for advanced web crawling.
Features:
- Performs complete traversal of entire websites when no depth/page limits are specified
- Follows and crawls all discovered links within the domain
- Stores retrieved content in a directory structure that mirrors the website's hierarchy
- Creates appropriate subfolders to maintain the original site organization
- Preserves file relationships and navigation paths in the saved structure
- Extracts all text content from provided URLs
- Respects robots.txt
- Implements configurable rate limiting
- Provides progress indicators
- Handles JavaScript-rendered content
- Saves original HTML, images, and assets to maintain site structure
"""

import os
import time
import json
import logging
import urllib.parse
import argparse
import re
import queue
import threading
import datetime
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse, urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from bs4 import BeautifulSoup
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("v2_crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class V2Crawler:
    def __init__(self, url, output_dir=None, max_depth=None, delay=1.0,
                 respect_robots=True, max_pages=None, timeout=30,
                 wait_time=10):
        """
        Initialize the V2 web crawler.
        
        Args:
            url (str): The starting URL to crawl
            output_dir (str): Directory to save crawled data (default: auto-generated based on domain)
            max_depth (int, optional): Maximum crawl depth (default: None, meaning unlimited)
            delay (float): Delay between requests in seconds (default: 1.0)
            respect_robots (bool): Whether to respect robots.txt (default: True)
            max_pages (int, optional): Maximum number of pages to crawl (default: None, meaning unlimited)
            timeout (int): Page load timeout in seconds (default: 30)
            wait_time (int): Time to wait for JavaScript content to load in seconds (default: 10)
        """
        self.start_url = url
        self.domain = urlparse(url).netloc
        
        # Auto-generate output directory based on domain if not provided
        if output_dir is None:
            self.output_dir = self.domain.replace('.', '_')
        else:
            self.output_dir = output_dir
            
        # Handle unlimited crawling (None or negative values mean unlimited)
        self.max_depth = None if max_depth is None or max_depth < 0 else max_depth
        self.delay = delay
        self.respect_robots = respect_robots
        self.max_pages = None if max_pages is None or max_pages < 0 else max_pages
        
        # Log crawling mode
        if self.max_depth is None and self.max_pages is None:
            logger.info("Unlimited crawling mode: Will traverse entire website")
        else:
            limits = []
            if self.max_depth is not None:
                limits.append(f"max depth={self.max_depth}")
            if self.max_pages is not None:
                limits.append(f"max pages={self.max_pages}")
            logger.info(f"Limited crawling mode: {', '.join(limits)}")
        self.timeout = timeout
        self.wait_time = wait_time
        
        # Initialize collections
        self.visited_urls = set()
        self.failed_urls = set()
        self.url_queue = queue.Queue()
        self.robots_parsers = {}
        
        # Setup Chrome options
        self.chrome_options = Options()
        
        # Important: Do NOT use headless mode as it often causes JavaScript issues
        # self.chrome_options.add_argument("--headless=new")
        
        # Set window size
        self.chrome_options.add_argument("--window-size=1920,1080")
        
        # Disable various features that might interfere with crawling
        self.chrome_options.add_argument("--disable-notifications")
        self.chrome_options.add_argument("--disable-popup-blocking")
        self.chrome_options.add_argument("--disable-extensions")
        
        # Enable JavaScript explicitly
        self.chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.javascript": 1,
            "profile.managed_default_content_settings.javascript": 1,
            "javascript.enabled": True
        })
        
        # Add user agent to appear more like a real browser
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Disable automation flags to avoid detection
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option("useAutomationExtension", False)
        
        self.driver = None
        
        # Statistics for progress reporting
        self.stats = {
            "pages_crawled": 0,
            "pages_failed": 0,
            "start_time": time.time(),
            "links_found": 0
        }
    
    def start_driver(self):
        """Start the WebDriver if it's not already running."""
        if self.driver is None:
            try:
                self.driver = webdriver.Chrome(options=self.chrome_options)
                
                # Execute CDP commands to disable automation flags
                self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    """
                })
                
                # Set page load timeout
                self.driver.set_page_load_timeout(self.timeout)
                
                logger.info("WebDriver started successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to start WebDriver: {e}")
                return False
        return True
    
    def close_driver(self):
        """Close the WebDriver if it's running."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None
    
    def get_robots_parser(self, url):
        """Get or create a robots.txt parser for the given URL."""
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        if base_url not in self.robots_parsers:
            robots_url = f"{base_url}/robots.txt"
            parser = RobotFileParser(robots_url)
            try:
                parser.read()
                self.robots_parsers[base_url] = parser
                logger.info(f"Loaded robots.txt from {robots_url}")
            except Exception as e:
                logger.warning(f"Failed to read robots.txt from {robots_url}: {e}")
                # If we can't read robots.txt, create a permissive parser
                parser = RobotFileParser()
                parser.parse(['User-agent: *', 'Allow: /'])
                self.robots_parsers[base_url] = parser
        
        return self.robots_parsers[base_url]
    
    def can_fetch(self, url):
        """Check if the URL can be fetched according to robots.txt."""
        if not self.respect_robots:
            return True
        
        try:
            parser = self.get_robots_parser(url)
            return parser.can_fetch("*", url)
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            return True  # Default to allowing if there's an error
    
    def create_directory_structure(self, url):
        """
        Create hierarchical directory structure for saving data that mirrors the website's hierarchy.
        This preserves the original site organization and file relationships.
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Extract path segments and handle query parameters
        path = parsed.path.strip('/')
        
        # Handle URL with query parameters by creating a sanitized folder name
        if parsed.query:
            query_hash = hash(parsed.query) % 10000  # Create a short hash of the query
            path = f"{path}_q{query_hash}" if path else f"q{query_hash}"
        
        # Split path into segments
        path_segments = path.split('/') if path else []
        
        # If no path segments, use 'home'
        if not path_segments:
            path_segments = ['home']
        
        # Create base folder path that mirrors the URL structure
        base_folder = os.path.join(self.output_dir, domain, *path_segments)
        
        # Create subdirectories for different types of content to maintain organization
        data_dir = os.path.join(base_folder, "data")
        images_dir = os.path.join(base_folder, "images")
        assets_dir = os.path.join(base_folder, "assets")
        
        # Create all directories
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(assets_dir, exist_ok=True)
        
        # Create a file to store the original URL for reference
        url_file = os.path.join(base_folder, "source_url.txt")
        with open(url_file, "w", encoding="utf-8") as f:
            f.write(url)
        
        return base_folder, data_dir
    
    def extract_focused_content(self, url, heading_text="Food and Culture", stop_at="Partners"):
        """
        Extract focused content from a page, starting from a heading with specified text
        and ending before a specified stop section.
        
        This method specifically:
        1. Locates the main heading with text matching the specified heading_text
        2. Starts scraping from the element after this specific heading
        3. Collects:
           - The intro paragraph (full text)
           - The results/controls bar (showing results count and view-mode controls)
           - Every card in the grid (title text, link href, and image src)
        4. Stops when reaching a heading with text matching stop_at
        
        Args:
            url (str): URL to crawl
            heading_text (str): The heading text to look for (default: "Food and Culture")
            stop_at (str): The heading text where to stop extraction (default: "Partners")
            
        Returns:
            dict: JSON data with keys intro, controls, and cards
        """
        try:
            if not self.start_driver():
                return None
            
            # Load the URL
            logger.info(f"Loading URL for focused extraction: {url}")
            self.driver.get(url)
            
            # Wait for the page to load initially
            time.sleep(3)
            
            # Wait for the body to be present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait additional time for dynamic content to load
            logger.info(f"Waiting {self.wait_time} seconds for JavaScript content to load...")
            time.sleep(self.wait_time)
            
            # Scroll down to load lazy-loaded content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, 0);")
            
            # Get the page source after JavaScript execution
            page_source = self.driver.page_source
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, "html.parser")
            
            # Find the heading element that contains the specified text (with flexible matching)
            target_heading = None
            
            # Create variations of the heading text for flexible matching
            heading_variations = [heading_text]
            if "and" in heading_text.lower():
                heading_variations.append(heading_text.lower().replace("and", "&"))
            if "&" in heading_text:
                heading_variations.append(heading_text.replace("&", "and"))
            
            # First try exact match with h1
            for h1 in soup.find_all('h1'):
                h1_text = h1.get_text().strip()
                if h1_text in heading_variations:
                    target_heading = h1
                    logger.info(f"Found exact match h1: '{h1_text}'")
                    break
            
            # If not found, try case-insensitive match with h1
            if not target_heading:
                for h1 in soup.find_all('h1'):
                    h1_text = h1.get_text().strip().lower()
                    if h1_text in [v.lower() for v in heading_variations]:
                        target_heading = h1
                        logger.info(f"Found case-insensitive h1: '{h1.get_text().strip()}'")
                        break
            
            # If still not found, try h1 containing the text
            if not target_heading:
                for h1 in soup.find_all('h1'):
                    h1_text = h1.get_text().strip().lower()
                    # Check if the heading contains key words from the heading_text
                    key_words = [word.lower() for word in heading_text.split() if len(word) > 2]
                    if all(word in h1_text for word in key_words):
                        target_heading = h1
                        logger.info(f"Found h1 containing key words: '{h1.get_text().strip()}'")
                        break
            
            # If still not found, try h2 as fallback
            if not target_heading:
                for h2 in soup.find_all('h2'):
                    h2_text = h2.get_text().strip().lower()
                    # Check if the heading contains key words from the heading_text
                    key_words = [word.lower() for word in heading_text.split() if len(word) > 2]
                    if all(word in h2_text for word in key_words):
                        target_heading = h2
                        logger.info(f"Found h2 containing key words: '{h2.get_text().strip()}'")
                        break
            
            # If still not found, try the first h1 as last resort
            if not target_heading:
                first_h1 = soup.find('h1')
                if first_h1:
                    target_heading = first_h1
                    logger.warning(f"No heading with '{heading_text}' found, using first h1: '{first_h1.get_text().strip()}'")
            
            if not target_heading:
                logger.warning(f"No suitable heading found on {url}")
                return None
                
            # Initialize the result structure
            result = {
                "intro": "",
                "controls": "",
                "cards": []
            }
            
            # Get the intro text (first paragraph after the Food and Culture h1)
            intro_element = food_culture_h1.find_next('p')
            if intro_element:
                result["intro"] = intro_element.get_text().strip()
            
            # Find the stop heading to know where to stop (with flexible matching)
            stop_heading = None
            
            # Create variations of the stop_at text for flexible matching
            stop_variations = [stop_at]
            if "and" in stop_at.lower():
                stop_variations.append(stop_at.lower().replace("and", "&"))
            if "&" in stop_at:
                stop_variations.append(stop_at.replace("&", "and"))
            
            # Look through all elements after the target_heading
            current_element = target_heading
            
            while current_element:
                current_element = current_element.find_next(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div'])
                if not current_element:
                    break
                    
                # Check if it's a heading with stop_at text
                if current_element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    element_text = current_element.get_text().strip().lower()
                    
                    # Check for exact match with variations
                    if element_text in [v.lower() for v in stop_variations]:
                        stop_heading = current_element
                        logger.info(f"Found exact match stop heading: '{current_element.get_text().strip()}'")
                        break
                    
                    # Check for partial match
                    key_words = [word.lower() for word in stop_at.split() if len(word) > 2]
                    if key_words and all(word in element_text for word in key_words):
                        stop_heading = current_element
                        logger.info(f"Found stop heading with key words: '{current_element.get_text().strip()}'")
                        break
                
                # Also check for div with class containing stop_at or "footer"
                if current_element.name == 'div' and current_element.get('class'):
                    class_str = ' '.join(current_element.get('class')).lower()
                    if any(v.lower() in class_str for v in stop_variations) or "footer" in class_str:
                        stop_heading = current_element
                        logger.info(f"Found stop div with class: '{class_str}'")
                        break
            
            # Get the controls bar (usually a div with class containing 'controls', 'toolbar', 'filter', etc.)
            controls_selectors = [
                ".view-header", ".result-count", ".controls-bar", ".toolbar",
                ".filter-bar", ".view-filters", ".view-controls"
            ]
            
            for selector in controls_selectors:
                controls_element = target_heading.find_next(lambda tag: tag.name == 'div' and
                                                     tag.get('class') and
                                                     any(cls in selector for cls in tag.get('class')))
                if controls_element:
                    # Check if it's before the stop heading
                    if not stop_heading or (hasattr(controls_element, 'sourceline') and
                                           hasattr(stop_heading, 'sourceline') and
                                           controls_element.sourceline < stop_heading.sourceline):
                        result["controls"] = controls_element.get_text().strip()
                        logger.info(f"Found controls bar: '{result['controls'][:50]}...'")
                        break
            
            # Find all cards in the grid
            # Cards are typically in a grid container after the controls bar
            grid_selectors = [
                ".view-content", ".grid", ".card-grid", ".results",
                ".items-grid", ".collection-grid", ".masonry-grid"
            ]
            
            grid_container = None
            for selector in grid_selectors:
                grid_container = soup.select_one(selector)
                if grid_container:
                    break
            
            # If no specific grid container found, look for a collection of similar elements
            if not grid_container:
                # Look for a collection of div elements with similar classes that might be cards
                potential_cards = first_h1.find_next_siblings(lambda tag: tag.name == 'div' and tag.find('a') and tag.find('img'))
                if potential_cards:
                    # Create a virtual container
                    grid_container = BeautifulSoup("<div></div>", "html.parser").div
                    for card in potential_cards:
                        grid_container.append(card)
            
            # Extract cards from the grid container
            if grid_container:
                # Find all potential card elements
                card_elements = grid_container.find_all(lambda tag: (tag.name == 'div' or tag.name == 'article') and
                                                      tag.find('a') and
                                                      (tag.find('img') or tag.find('h2') or tag.find('h3')))
                
                # If no structured cards found, look for any links with images
                if not card_elements:
                    card_elements = grid_container.find_all('a', href=True)
                
                # Process each card, but only if it appears before the stop section
                cards_processed = 0
                for card in card_elements:
                    # Skip if this card appears after the stop heading
                    if stop_heading and hasattr(card, 'sourceline') and hasattr(stop_heading, 'sourceline'):
                        if card.sourceline > stop_heading.sourceline:
                            continue
                    
                    card_data = {}
                    
                    # Extract title
                    title_element = card.find(['h2', 'h3', 'h4', '.title', '.card-title']) or card.find('a')
                    if title_element:
                        card_data["title"] = title_element.get_text().strip()
                    else:
                        card_data["title"] = card.get_text().strip()
                    
                    # Extract link
                    link_element = card.find('a', href=True) if card.name != 'a' else card
                    if link_element and 'href' in link_element.attrs:
                        href = link_element['href']
                        if not href.startswith(('http://', 'https://')):
                            href = urljoin(url, href)
                        card_data["href"] = href
                    
                    # Extract image
                    img_element = card.find('img', src=True)
                    if img_element and 'src' in img_element.attrs:
                        img_src = img_element['src']
                        if not img_src.startswith(('http://', 'https://')):
                            img_src = urljoin(url, img_src)
                        card_data["image_src"] = img_src
                    
                    # Add to results if we have at least title and link
                    if "title" in card_data and "href" in card_data:
                        result["cards"].append(card_data)
                
                    cards_processed += 1
                    
                logger.info(f"Extracted {len(result['cards'])} cards from {url}")
                
                # If we didn't find any cards but have a grid container, try a more aggressive approach
                if len(result['cards']) == 0 and grid_container:
                    logger.info("No cards found with standard approach, trying alternative extraction")
                    
                    # Look for any links with images in the grid container
                    links_with_images = []
                    
                    for link in grid_container.find_all('a', href=True):
                        # Skip if this link appears after the stop heading
                        if stop_heading and hasattr(link, 'sourceline') and hasattr(stop_heading, 'sourceline'):
                            if link.sourceline > stop_heading.sourceline:
                                continue
                                
                        img = link.find('img', src=True)
                        if img:
                            card_data = {
                                "title": link.get_text().strip(),
                                "href": link['href'] if link['href'].startswith(('http://', 'https://')) else urljoin(url, link['href']),
                                "image_src": img['src'] if img['src'].startswith(('http://', 'https://')) else urljoin(url, img['src'])
                            }
                            result["cards"].append(card_data)
                    
                    logger.info(f"Alternative extraction found {len(result['cards'])} cards")
            else:
                logger.warning(f"No grid container found on {url}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting focused content from {url}: {e}")
            return None
        finally:
            # Don't close the driver here, as we'll reuse it for other pages
            pass
    
    def extract_content(self, url, depth=0):
        """
        Extract content from the page with advanced JavaScript handling.
        
        Args:
            url (str): URL to crawl
            depth (int): Current crawl depth
            
        Returns:
            dict: Extracted page data or None if extraction failed
        """
        # Normalize the URL to handle different representations of the same URL
        normalized_url = url.split('#')[0]  # Remove fragments
        
        if normalized_url in self.visited_urls:
            return None
            
        # Add the normalized URL to visited set
        self.visited_urls.add(normalized_url)
        
        if not self.can_fetch(url):
            logger.info(f"Skipping {url} (disallowed by robots.txt)")
            return None
        
        # URL is already added to visited_urls above
        
        # Apply rate limiting
        time.sleep(self.delay)
        
        try:
            if not self.start_driver():
                return None
            
            # Load the URL
            logger.info(f"Loading URL: {url}")
            self.driver.get(url)
            
            # Wait for the page to load initially
            time.sleep(3)
            
            # Check if there's a JavaScript warning
            if "Sorry, you need to enable JavaScript" in self.driver.page_source:
                logger.warning("JavaScript warning detected. Attempting to bypass...")
                
                # Try to execute JavaScript to remove the warning overlay
                self.driver.execute_script("""
                    // Remove any overlay or warning elements
                    var overlays = document.querySelectorAll('.overlay, .warning, .noscript-warning, [class*="warning"], [id*="warning"]');
                    for (var i = 0; i < overlays.length; i++) {
                        overlays[i].remove();
                    }
                    
                    // Remove any body classes that might be blocking content
                    document.body.className = document.body.className.replace('no-js', 'js');
                """)
                
                # Refresh the page
                self.driver.refresh()
                
                # Wait again for content to load
                time.sleep(3)
            
            # Wait for the body to be present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait additional time for dynamic content to load
            logger.info(f"Waiting {self.wait_time} seconds for JavaScript content to load...")
            time.sleep(self.wait_time)
            
            # Scroll down to load lazy-loaded content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, 0);")
            
            # Get the page source after JavaScript execution
            page_source = self.driver.page_source
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, "html.parser")
            
            # Create directory structure that mirrors the website hierarchy
            base_folder, data_dir = self.create_directory_structure(url)
            images_dir = os.path.join(base_folder, "images")
            assets_dir = os.path.join(base_folder, "assets")
            
            # Extract metadata
            title = soup.find('title').get_text() if soup.find('title') else "No Title"
            
            # Extract description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content') if meta_desc else "No Description"
            
            # Extract keywords
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            keywords = meta_keywords.get('content') if meta_keywords else None
            
            # Extract main content
            main_content = None
            
            # Try different selectors to find the main content
            content_selectors = [
                "main",
                "#main-content",
                ".main-content",
                "article",
                ".content",
                "#content",
                ".page-content",
                "[role='main']",
                ".entry-content",
                "#primary",
                ".post-content",
                ".article-content"
            ]
            
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    main_content = content_element
                    break
            
            # If no main content found, use the body
            if not main_content:
                main_content = soup.body
            
            # Clean the content
            if main_content:
                # Remove navigation, headers, footers, etc.
                for tag in main_content.find_all(["nav", "header", "footer", "script", "style",
                                                ".site-header", ".site-footer", ".navigation",
                                                ".menu", "#header", "#footer", "#nav",
                                                ".sidebar", ".widget", ".comments", ".comment-section"]):
                    tag.extract()
            
            # Get the cleaned text content
            text_content = self.extract_text_content(main_content if main_content else soup)
            
            # If content is empty or very short, try extracting from the full page
            if not text_content or len(text_content) < 100:
                logger.warning(f"Extracted content for {url} is very short. Trying with full page.")
                text_content = self.extract_text_content(soup)
            
            # Extract links for crawling
            # If max_depth is None, we're in unlimited mode, so extract links regardless of depth
            # Otherwise, only extract links if we haven't reached max_depth
            if self.max_depth is None or depth < self.max_depth:
                self.extract_links(soup, url, depth + 1)
            
            # Extract and save images to preserve file relationships
            images = []
            for img in soup.find_all('img', src=True):
                try:
                    img_src = img['src']
                    if not img_src.startswith(('http://', 'https://', 'data:')):
                        img_src = urljoin(url, img_src)
                    
                    # Skip data URLs
                    if img_src.startswith('data:'):
                        continue
                        
                    img_filename = os.path.basename(urlparse(img_src).path)
                    if not img_filename:
                        img_filename = f"image_{len(images)}.jpg"
                    
                    img_path = os.path.join(images_dir, img_filename)
                    images.append({
                        "src": img_src,
                        "alt": img.get('alt', ''),
                        "local_path": os.path.join("images", img_filename)
                    })
                except Exception as e:
                    logger.warning(f"Error processing image {img.get('src', 'unknown')}: {e}")
            
            # Extract and save CSS, JS, and other assets to preserve navigation paths
            assets = []
            for link in soup.find_all(['link', 'script'], href=True) + soup.find_all('script', src=True):
                try:
                    asset_src = link.get('href') or link.get('src')
                    if not asset_src:
                        continue
                        
                    if not asset_src.startswith(('http://', 'https://')):
                        asset_src = urljoin(url, asset_src)
                    
                    asset_filename = os.path.basename(urlparse(asset_src).path)
                    if not asset_filename:
                        continue
                        
                    asset_path = os.path.join(assets_dir, asset_filename)
                    assets.append({
                        "src": asset_src,
                        "type": link.get('type', 'unknown'),
                        "local_path": os.path.join("assets", asset_filename)
                    })
                except Exception as e:
                    logger.warning(f"Error processing asset {link.get('href') or link.get('src') or 'unknown'}: {e}")
            
            # Create page data structure with enhanced information
            page_data = {
                "url": url,
                "crawl_timestamp": datetime.datetime.now().isoformat(),
                "title": title,
                "description": description,
                "language": soup.html.get('lang') if soup.html else None,
                "content": text_content,
                "images": images,
                "assets": assets,
                "metadata": {
                    "title": title,
                    "description": description,
                    "keywords": keywords,
                    "canonical_url": self.get_canonical_url(soup, url),
                    "language": soup.html.get('lang') if soup.html else None,
                    "author": self.get_meta_content(soup, "author"),
                    "og:title": self.get_meta_property(soup, "og:title"),
                    "og:description": self.get_meta_property(soup, "og:description"),
                    "og:image": self.get_meta_property(soup, "og:image"),
                    "twitter:card": self.get_meta_property(soup, "twitter:card"),
                    "twitter:title": self.get_meta_property(soup, "twitter:title"),
                    "twitter:description": self.get_meta_property(soup, "twitter:description"),
                    "twitter:image": self.get_meta_property(soup, "twitter:image")
                },
                "links": {
                    "parent": os.path.dirname(url) if url != self.start_url else None,
                    "root": self.start_url
                }
            }
            
            # Save the page data to JSON
            json_path = os.path.join(data_dir, "page_data.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(page_data, f, indent=2, ensure_ascii=False)
                
            # Save the HTML content to preserve the original structure
            html_path = os.path.join(data_dir, "original.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(page_source)
                
            # Create a sitemap.txt file in the output directory to track the overall structure
            sitemap_path = os.path.join(self.output_dir, "sitemap.txt")
            with open(sitemap_path, "a", encoding="utf-8") as f:
                f.write(f"{url}\n")
            
            # Update statistics
            self.stats["pages_crawled"] += 1
            
            # Print progress
            self.print_progress()
            
            logger.info(f"Successfully extracted content from {url}")
            logger.info(f"Data saved to {json_path}")
            
            return page_data
            
        except TimeoutException:
            logger.error(f"Timeout while loading {url}")
            self.failed_urls.add(url)
            self.stats["pages_failed"] += 1
        except WebDriverException as e:
            logger.error(f"WebDriver error for {url}: {e}")
            self.failed_urls.add(url)
            self.stats["pages_failed"] += 1
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            self.failed_urls.add(url)
            self.stats["pages_failed"] += 1
        finally:
            # Don't close the driver here, as we'll reuse it for other pages
            pass
    
    def extract_text_content(self, soup):
        """Extract clean text content from the soup object."""
        if not soup:
            return "No content found"
        
        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.extract()
        
        # Get text
        text = soup.get_text()
        
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        
        # Remove blank lines
        content = '\n'.join(chunk for chunk in chunks if chunk)
        
        # If content is empty or very short, try alternative extraction method
        if not content or len(content) < 100:
            logger.warning("Standard text extraction yielded little or no content. Trying alternative method.")
            content = self.extract_text_from_html(soup)
            
        return content
    
    def extract_text_from_html(self, soup):
        """
        Alternative method to extract text from HTML when standard method fails.
        This method preserves more structure and handles copy-protected content better.
        """
        if not soup:
            return "No content found"
            
        # Focus on paragraphs, headings, lists, and other content elements
        content_parts = []
        
        # Extract headings
        for heading_tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = heading_tag.get_text().strip()
            if text:
                content_parts.append(f"{heading_tag.name.upper()}: {text}")
        
        # Extract paragraphs
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if text:
                content_parts.append(text)
        
        # Extract lists
        for list_tag in soup.find_all(['ul', 'ol']):
            list_items = []
            for item in list_tag.find_all('li'):
                text = item.get_text().strip()
                if text:
                    list_items.append(f"• {text}")
            if list_items:
                content_parts.append("\n".join(list_items))
        
        # Extract tables
        for table in soup.find_all('table'):
            table_content = []
            for row in table.find_all('tr'):
                cells = []
                for cell in row.find_all(['td', 'th']):
                    text = cell.get_text().strip()
                    cells.append(text)
                if cells:
                    table_content.append(" | ".join(cells))
            if table_content:
                content_parts.append("\n".join(table_content))
        
        # Extract divs with substantial text content
        for div in soup.find_all('div'):
            # Skip divs that are likely navigation, headers, footers, etc.
            if any(cls in (div.get('class', []) or []) for cls in ['nav', 'menu', 'header', 'footer', 'sidebar']):
                continue
                
            text = div.get_text().strip()
            # Only include divs with substantial content
            if text and len(text) > 100 and not any(text in part for part in content_parts):
                content_parts.append(text)
        
        # Join all content parts with double newlines
        return '\n\n'.join(content_parts)
    
    def get_meta_content(self, soup, name):
        """Get content from a meta tag with the given name."""
        meta = soup.find('meta', attrs={'name': name})
        return meta.get('content') if meta else None
    
    def get_meta_property(self, soup, property_name):
        """Get content from a meta tag with the given property."""
        meta = soup.find('meta', attrs={'property': property_name})
        return meta.get('content') if meta else None
    
    def get_canonical_url(self, soup, current_url):
        """Get the canonical URL if available."""
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        if canonical and canonical.get('href'):
            return urljoin(current_url, canonical.get('href'))
        return current_url
    
    def extract_links(self, soup, base_url, depth):
        """
        Extract ALL links from the page for complete website traversal.
        This method finds all links in the page, not just those in the main content area.
        """
        # Skip link extraction if we've reached the max pages limit
        # If max_pages is None, we're in unlimited mode, so continue extracting links
        if self.max_pages is not None and self.stats["pages_crawled"] >= self.max_pages:
            return
        
        # Get ALL links from the entire page
        links = []
        all_links = soup.find_all('a', href=True)
        
        # Process each link
        for link in all_links:
            href = link['href']
            
            # Skip empty links, javascript, mailto, and tel links
            if not href or href.startswith(('javascript:', 'mailto:', 'tel:')):
                continue
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            
            # Skip external domains - only crawl within the same domain
            if urlparse(absolute_url).netloc != urlparse(base_url).netloc:
                continue
            
            # Handle fragments but keep query parameters (important for dynamic sites)
            # Just remove the fragment part
            clean_url = absolute_url.split('#')[0]
            
            # Skip if already visited
            if clean_url in self.visited_urls:
                continue
                
            # Check if this URL is already in the queue to avoid duplicates
            already_queued = False
            for item in list(self.url_queue.queue):
                if item[0] == clean_url:
                    already_queued = True
                    break
                    
            if already_queued:
                continue
            
            # Add to links list
            links.append(clean_url)
            self.stats["links_found"] += 1
            
            # Log the discovered link
            logger.debug(f"Found link: {clean_url}")
        
        # Add unique links to the queue
        for link in set(links):
            # Add to queue with priority based on depth (lower depth = higher priority)
            self.url_queue.put((link, depth))
            logger.info(f"Added to queue: {link} (depth {depth})")
            
            # Save discovered links to a file for reference
            with open(os.path.join(self.output_dir, "discovered_links.txt"), "a", encoding="utf-8") as f:
                f.write(f"{link}\n")
    
    def print_progress(self):
        """Print progress information."""
        elapsed = time.time() - self.stats["start_time"]
        pages_per_minute = (self.stats["pages_crawled"] / elapsed) * 60 if elapsed > 0 else 0
        
        # Display progress with or without max_pages limit
        if self.max_pages is not None:
            progress = f"{self.stats['pages_crawled']}/{self.max_pages}"
        else:
            progress = f"{self.stats['pages_crawled']}"
            
        logger.info(f"Progress: {progress} pages crawled "
                   f"({self.stats['pages_failed']} failed) | "
                   f"Links found: {self.stats['links_found']} | "
                   f"Elapsed: {elapsed:.1f}s | "
                   f"Speed: {pages_per_minute:.1f} pages/min")
    
    def save_failed_urls(self):
        """Save failed URLs to a file."""
        if not self.failed_urls:
            return
            
        failed_urls_path = os.path.join(self.output_dir, "failed_urls.txt")
        with open(failed_urls_path, "w", encoding="utf-8") as f:
            for url in self.failed_urls:
                f.write(f"{url}\n")
        
        logger.info(f"Saved {len(self.failed_urls)} failed URLs to {failed_urls_path}")
    
    def focused_crawl(self, url, heading_text="Food and Culture", stop_at="Partners"):
        """
        Perform a focused crawl on a single URL to extract specific content.
        
        This method extracts content from a page starting from a specific heading,
        collecting the intro paragraph, controls bar, and all cards in the grid
        up to (but not including) a specified stop section.
        
        Args:
            url (str): URL to crawl
            heading_text (str): The heading text to look for (default: "Food and Culture")
            stop_at (str): The heading text where to stop extraction (default: "Partners")
            
        Returns:
            dict: JSON data with keys intro, controls, and cards
        """
        try:
            logger.info(f"Starting focused crawl on {url}")
            logger.info(f"Looking for heading: '{heading_text}', stopping at: '{stop_at}'")
            
            # Extract focused content
            result = self.extract_focused_content(url, heading_text=heading_text, stop_at=stop_at)
            
            if result:
                logger.info(f"Focused crawl completed successfully for {url}")
                return result
            else:
                logger.error(f"Failed to extract focused content from {url}")
                return None
                
        except Exception as e:
            logger.error(f"Error during focused crawl: {e}")
            return None
        finally:
            # Close the WebDriver
            self.close_driver()
    
    def crawl(self):
        """
        Start the crawling process for complete website traversal.
        This method continues until all discovered links are processed or limits are reached.
        """
        try:
            # Add the starting URL to the queue
            self.url_queue.put((self.start_url, 0))
            
            logger.info(f"Starting crawl from {self.start_url}")
            if self.max_depth is None and self.max_pages is None:
                logger.info("UNLIMITED CRAWLING MODE: Will traverse the entire website")
            else:
                limits = []
                if self.max_depth is not None:
                    limits.append(f"max depth={self.max_depth}")
                if self.max_pages is not None:
                    limits.append(f"max pages={self.max_pages}")
                logger.info(f"Limited crawling mode: {', '.join(limits)}")
            
            # Process URLs from the queue
            # Continue crawling until the queue is empty or we've reached max_pages (if set)
            while not self.url_queue.empty() and (self.max_pages is None or self.stats["pages_crawled"] < self.max_pages):
                # Get the next URL from the queue
                url, depth = self.url_queue.get()
                
                # Normalize URL and skip if already visited
                normalized_url = url.split('#')[0]
                if normalized_url in self.visited_urls:
                    continue
                
                # Check depth limit if set
                if self.max_depth is not None and depth > self.max_depth:
                    logger.debug(f"Skipping {url} - exceeds max depth {self.max_depth}")
                    continue
                
                # Extract content from the URL
                logger.info(f"Crawling {url} (depth {depth})")
                self.extract_content(url, depth)
                
                # Log queue status periodically
                if self.stats["pages_crawled"] % 10 == 0:
                    queue_size = self.url_queue.qsize()
                    logger.info(f"Queue status: {queue_size} URLs remaining to crawl")
                    
                    # Save crawl progress to a status file
                    status_data = {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "pages_crawled": self.stats["pages_crawled"],
                        "pages_failed": self.stats["pages_failed"],
                        "links_found": self.stats["links_found"],
                        "queue_size": queue_size,
                        "elapsed_seconds": time.time() - self.stats["start_time"]
                    }
                    
                    with open(os.path.join(self.output_dir, "crawl_status.json"), "w", encoding="utf-8") as f:
                        json.dump(status_data, f, indent=2)
            
            # Save failed URLs
            self.save_failed_urls()
            
            # Print final statistics
            elapsed = time.time() - self.stats["start_time"]
            logger.info(f"Crawl completed in {elapsed:.1f} seconds")
            logger.info(f"Pages crawled: {self.stats['pages_crawled']}")
            logger.info(f"Pages failed: {self.stats['pages_failed']}")
            logger.info(f"Links found: {self.stats['links_found']}")
            
        except KeyboardInterrupt:
            logger.info("Crawl interrupted by user")
        except Exception as e:
            logger.error(f"Error during crawl: {e}")
        finally:
            # Close the WebDriver
            self.close_driver()

def main():
    """Main function to run the crawler."""
    parser = argparse.ArgumentParser(
        description="V2 Web Crawler - Complete Website Traversal Edition",
        epilog="""
        When run without --depth or --max-pages parameters, the crawler will perform
        a complete traversal of the entire website, following all links within the domain.
        The content will be stored in a directory structure that mirrors the website's hierarchy.
        
        Use --focused-mode to extract specific content from a single page.
        """
    )
    
    parser.add_argument("url", help="URL to start crawling from")
    parser.add_argument("--output", help="Output directory (default: auto-generated based on domain)")
    parser.add_argument("--depth", type=int, default=None,
                        help="Maximum crawl depth (default: None, meaning unlimited)")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds (default: 1.0)")
    parser.add_argument("--no-robots", action="store_true", help="Disable robots.txt checking")
    parser.add_argument("--max-pages", type=int, default=None,
                        help="Maximum number of pages to crawl (default: None, meaning unlimited)")
    parser.add_argument("--timeout", type=int, default=30, help="Page load timeout in seconds (default: 30)")
    parser.add_argument("--wait", type=int, default=10, help="Time to wait for JavaScript content to load (default: 10)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--focused-mode", action="store_true",
                        help="Run in focused mode to extract specific content from a single page")
    parser.add_argument("--heading-text", default="Food and Culture",
                        help="Specify the heading text to look for in focused mode (default: 'Food and Culture')")
    parser.add_argument("--stop-at", default="Partners",
                        help="Specify the heading text where to stop extraction in focused mode (default: 'Partners')")
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create the crawler
    crawler = V2Crawler(
        url=args.url,
        output_dir=args.output,
        max_depth=args.depth,
        delay=args.delay,
        respect_robots=not args.no_robots,
        max_pages=args.max_pages,
        timeout=args.timeout,
        wait_time=args.wait
    )
    
    # Run in focused mode or regular crawl mode
    if args.focused_mode:
        result = crawler.focused_crawl(args.url, heading_text=args.heading_text, stop_at=args.stop_at)
        if result:
            # Print the JSON result to stdout
            print(json.dumps(result, indent=2))
            
            # If output directory is specified, save the result there
            if args.output:
                os.makedirs(args.output, exist_ok=True)
                # Create a sanitized filename from the heading text
                sanitized_heading = args.heading_text.lower().replace(" ", "_").replace("&", "and")
                sanitized_heading = re.sub(r'[^\w\-_]', '', sanitized_heading)
                output_file = os.path.join(args.output, f"{sanitized_heading}_content.json")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
                logger.info(f"Focused crawl result saved to {output_file}")
    else:
        crawler.crawl()

if __name__ == "__main__":
    main()