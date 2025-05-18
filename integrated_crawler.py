#!/usr/bin/env python3
"""
Integrated Web Crawler with Image Extraction

This script combines the functionality of advanced_crawler.py and adv_extract_image.py to:
1. Crawl websites recursively and extract content and links
2. Extract images from each crawled website
3. Save content to output_content.json with image metadata
4. Save links to output_links.json
5. Save images to an "images" subfolder
6. Respect robots.txt and implement rate limiting

Usage:
    # For recursive crawling with default settings:
    python integrated_crawler.py <url> [--headless] [--max-depth=2] [--delay=3]
    
    # For deduplicating links in an existing JSON file:
    python integrated_crawler.py --dedupe-file <input_file> [<output_file>]
"""

import json
import time
import argparse
import os
import re
import urllib.parse
import logging
import sys
import requests
from collections import OrderedDict
from urllib.error import URLError, HTTPError
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Import from combined_crawler.py
from combined_crawler import WebsiteCrawler, dedupe_links, extract_slug_from_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("integrated_crawler.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("IntegratedCrawler")

class MediaExtractor:
    """Base class for media extraction from websites"""
    
    def __init__(self, url, output_dir, file_patterns=None, exclude_patterns=None, headers=None):
        """Initialize the media extractor
        
        Args:
            url (str): URL of the website to extract media from
            output_dir (str): Directory to save downloaded media
            file_patterns (list): List of file path patterns to match in URLs
            exclude_patterns (list): List of patterns to exclude from results
            headers (dict): HTTP headers to use for requests
        """
        # Default patterns for media files if none provided
        if file_patterns is None:
            self.file_patterns = [
                "sites/default/files",
                "system/files",
                "uploads",
                "media"
            ]
        else:
            self.file_patterns = file_patterns
        
        # Default exclude patterns if none provided
        if exclude_patterns is None:
            self.exclude_patterns = ["logo", "icon", "favicon"]
        else:
            self.exclude_patterns = exclude_patterns
            
        self.url = url
        self.output_dir = output_dir
        
        # Default headers if none provided
        if headers is None:
            self.headers = {
                "Referer": url,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        else:
            self.headers = headers
            
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
    
    def download_media(self, media_urls):
        """Download media from URLs to the output directory
        
        Args:
            media_urls (set): Set of media URLs to download
            
        Returns:
            list: List of dictionaries containing metadata about downloaded media
        """
        downloaded_media = []
        
        for i, media_url in enumerate(media_urls):
            try:
                # Parse URL to extract filename
                parsed_url = urlparse(media_url)
                filename = os.path.basename(parsed_url.path).split('?')[0]
                
                # Skip if filename contains any exclude pattern
                if any(exclude_pat.lower() in filename.lower() for exclude_pat in self.exclude_patterns):
                    logger.info(f"⏭️ Skipping excluded media: {media_url}")
                    continue
                
                logger.info(f"Downloading ({i+1}/{len(media_urls)}): {media_url}")
                
                response = requests.get(media_url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    # If filename is empty or doesn't have extension, create a default one
                    if not filename or '.' not in filename:
                        # Try to get extension from Content-Type header
                        content_type = response.headers.get('Content-Type', '')
                        ext = content_type.split('/')[-1] if '/' in content_type else 'bin'
                        filename = f"media_{i}.{ext}"
                    
                    # Create unique filename to avoid overwriting
                    file_path = os.path.join(self.output_dir, filename)
                    if os.path.exists(file_path):
                        name, ext = os.path.splitext(filename)
                        file_path = os.path.join(self.output_dir, f"{name}_{i}{ext}")
                    
                    # Save the media
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    
                    # Get file size
                    file_size = os.path.getsize(file_path)
                    
                    # Add metadata to downloaded_media list
                    media_metadata = {
                        "url": media_url,
                        "filename": os.path.basename(file_path),
                        "size_bytes": file_size,
                        "content_type": response.headers.get('Content-Type', ''),
                        "local_path": file_path
                    }
                    downloaded_media.append(media_metadata)
                    
                    logger.info(f"✅ Saved as: {os.path.basename(file_path)}")
                else:
                    logger.error(f"❌ Failed ({response.status_code}): {media_url}")
                    
                # Sleep briefly to avoid rate limiting
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"❌ Error downloading {media_url}: {str(e)}")
        
        return downloaded_media

class ImageExtractor(MediaExtractor):
    """Class to handle image extraction from websites"""
    
    def __init__(self, url, output_dir, file_patterns=None, exclude_patterns=None, headers=None):
        """Initialize the image extractor
        
        Args:
            url (str): URL of the website to extract images from
            output_dir (str): Directory to save downloaded images
            file_patterns (list): List of file path patterns to match in URLs
            exclude_patterns (list): List of patterns to exclude from results
            headers (dict): HTTP headers to use for requests
        """
        # Add image-specific patterns
        if file_patterns is None:
            file_patterns = [
                "sites/default/files",
                "system/files",
                "images",
                "img",
                "uploads",
                "media"
            ]
            
        super().__init__(url, output_dir, file_patterns, exclude_patterns, headers)
        
    def is_image_url(self, url):
        """Check if a URL is likely an image based on extension or content type.
        
        Args:
            url (str): URL to check
            
        Returns:
            bool: True if URL is likely an image, False otherwise
        """
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico']
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        # Exclude images with excluded patterns in the filename
        if any(exclude_pat.lower() in os.path.basename(path).lower() for exclude_pat in self.exclude_patterns):
            return False
        
        # Check extensions
        return any(path.endswith(ext) for ext in image_extensions)
    
    def extract_images_from_driver(self, driver):
        """Extract image URLs from a Selenium WebDriver instance
        
        Args:
            driver (WebDriver): Selenium WebDriver instance
            
        Returns:
            set: Set of image URLs
        """
        all_image_urls = set()
        
        # 1. Extract from network logs
        logger.info("Extracting image URLs from network logs...")
        try:
            logs = driver.get_log("performance")
            
            for entry in logs:
                try:
                    message = json.loads(entry["message"])["message"]
                    if message["method"] == "Network.responseReceived":
                        response_url = message["params"]["response"]["url"]
                        
                        # Check if URL contains any of the target patterns
                        if any(pattern in response_url for pattern in self.file_patterns):
                            # Check if URL is likely an image
                            if self.is_image_url(response_url):
                                # Skip if contains any exclude pattern
                                if not any(exclude_pat.lower() in response_url.lower() for exclude_pat in self.exclude_patterns):
                                    all_image_urls.add(response_url)
                except Exception as e:
                    continue
        except Exception as e:
            logger.warning(f"Could not extract from network logs: {str(e)}")
        
        # 2. Extract from HTML
        logger.info("Extracting image URLs from HTML...")
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find all img tags
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                # Convert relative URLs to absolute
                abs_url = urljoin(self.url, src)
                
                # Check if URL is likely an image
                if self.is_image_url(abs_url):
                    # Skip if contains any exclude pattern
                    if not any(exclude_pat.lower() in abs_url.lower() for exclude_pat in self.exclude_patterns):
                        all_image_urls.add(abs_url)
        
        # Also check for background images in CSS
        for elem in soup.find_all(style=True):
            style = elem['style']
            urls = re.findall(r'url\([\'"]?(.*?)[\'"]?\)', style)
            for img_url in urls:
                abs_url = urljoin(self.url, img_url)
                if self.is_image_url(abs_url):
                    # Skip if contains any exclude pattern
                    if not any(exclude_pat.lower() in abs_url.lower() for exclude_pat in self.exclude_patterns):
                        all_image_urls.add(abs_url)
        
        logger.info(f"Found {len(all_image_urls)} unique image URLs")
        return all_image_urls
    
    def download_images(self, image_urls):
        """Download images from URLs to the output directory
        
        Args:
            image_urls (set): Set of image URLs to download
            
        Returns:
            list: List of dictionaries containing metadata about downloaded images
        """
        return super().download_media(image_urls)

class VideoExtractor(MediaExtractor):
    """Class to handle video extraction from websites"""
    
    def __init__(self, url, output_dir, file_patterns=None, exclude_patterns=None, headers=None):
        """Initialize the video extractor
        
        Args:
            url (str): URL of the website to extract videos from
            output_dir (str): Directory to save downloaded videos
            file_patterns (list): List of file path patterns to match in URLs
            exclude_patterns (list): List of patterns to exclude from results
            headers (dict): HTTP headers to use for requests
        """
        # Add video-specific patterns
        if file_patterns is None:
            file_patterns = [
                "sites/default/files",
                "system/files",
                "videos",
                "video",
                "media",
                "uploads"
            ]
            
        super().__init__(url, output_dir, file_patterns, exclude_patterns, headers)
        
    def is_video_url(self, url):
        """Check if a URL is likely a video based on extension or content type.
        
        Args:
            url (str): URL to check
            
        Returns:
            bool: True if URL is likely a video, False otherwise
        """
        video_extensions = ['.mp4', '.webm', '.ogg', '.mov', '.avi', '.wmv', '.flv', '.mkv', '.m4v']
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        # Exclude videos with excluded patterns in the filename
        if any(exclude_pat.lower() in os.path.basename(path).lower() for exclude_pat in self.exclude_patterns):
            return False
        
        # Check extensions
        return any(path.endswith(ext) for ext in video_extensions)
    
    def extract_videos_from_driver(self, driver):
        """Extract video URLs from a Selenium WebDriver instance
        
        Args:
            driver (WebDriver): Selenium WebDriver instance
            
        Returns:
            set: Set of video URLs
        """
        all_video_urls = set()
        
        # 1. Extract from network logs
        logger.info("Extracting video URLs from network logs...")
        try:
            logs = driver.get_log("performance")
            
            for entry in logs:
                try:
                    message = json.loads(entry["message"])["message"]
                    if message["method"] == "Network.responseReceived":
                        response_url = message["params"]["response"]["url"]
                        
                        # Check if URL contains any of the target patterns
                        if any(pattern in response_url for pattern in self.file_patterns):
                            # Check if URL is likely a video
                            if self.is_video_url(response_url):
                                # Skip if contains any exclude pattern
                                if not any(exclude_pat.lower() in response_url.lower() for exclude_pat in self.exclude_patterns):
                                    all_video_urls.add(response_url)
                except Exception as e:
                    continue
        except Exception as e:
            logger.warning(f"Could not extract from network logs: {str(e)}")
        
        # 2. Extract from HTML
        logger.info("Extracting video URLs from HTML...")
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find all video tags
        for video in soup.find_all('video'):
            # Check source tags within video
            for source in video.find_all('source'):
                src = source.get('src')
                if src:
                    # Convert relative URLs to absolute
                    abs_url = urljoin(self.url, src)
                    
                    # Check if URL is likely a video
                    if self.is_video_url(abs_url):
                        # Skip if contains any exclude pattern
                        if not any(exclude_pat.lower() in abs_url.lower() for exclude_pat in self.exclude_patterns):
                            all_video_urls.add(abs_url)
            
            # Check video tag src attribute
            src = video.get('src')
            if src:
                # Convert relative URLs to absolute
                abs_url = urljoin(self.url, src)
                
                # Check if URL is likely a video
                if self.is_video_url(abs_url):
                    # Skip if contains any exclude pattern
                    if not any(exclude_pat.lower() in abs_url.lower() for exclude_pat in self.exclude_patterns):
                        all_video_urls.add(abs_url)
        
        # Also check for iframe embedded videos
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src')
            if src:
                # Check for common video platforms
                if any(platform in src.lower() for platform in ['youtube.com/embed', 'vimeo.com', 'dailymotion.com/embed']):
                    all_video_urls.add(src)
        
        logger.info(f"Found {len(all_video_urls)} unique video URLs")
        return all_video_urls
    
    def download_videos(self, video_urls):
        """Download videos from URLs to the output directory
        
        Args:
            video_urls (set): Set of video URLs to download
            
        Returns:
            list: List of dictionaries containing metadata about downloaded videos
        """
        return super().download_media(video_urls)
        """Initialize the video extractor
        
        Args:
            url (str): URL of the website to extract videos from
            output_dir (str): Directory to save downloaded videos
            file_patterns (list): List of file path patterns to match in URLs
            exclude_patterns (list): List of patterns to exclude from results
            headers (dict): HTTP headers to use for requests
        """
        # Add video-specific patterns
        if file_patterns is None:
            file_patterns = [
                "sites/default/files",
                "system/files",
                "videos",
                "video",
                "media",
                "uploads"
            ]
            
        super().__init__(url, output_dir, file_patterns, exclude_patterns, headers)
        
    def is_video_url(self, url):
        """Check if a URL is likely a video based on extension or content type.
        
        Args:
            url (str): URL to check
            
        Returns:
            bool: True if URL is likely a video, False otherwise
        """
        video_extensions = ['.mp4', '.webm', '.ogg', '.mov', '.avi', '.wmv', '.flv', '.mkv', '.m4v']
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        # Exclude videos with excluded patterns in the filename
        if any(exclude_pat.lower() in os.path.basename(path).lower() for exclude_pat in self.exclude_patterns):
            return False
        
        # Check extensions
        return any(path.endswith(ext) for ext in video_extensions)
    
    def extract_videos_from_driver(self, driver):
        """Extract video URLs from a Selenium WebDriver instance
        
        Args:
            driver (WebDriver): Selenium WebDriver instance
            
        Returns:
            set: Set of video URLs
        """
        all_video_urls = set()
        
        # 1. Extract from network logs
        logger.info("Extracting video URLs from network logs...")
        try:
            logs = driver.get_log("performance")
            
            for entry in logs:
                try:
                    message = json.loads(entry["message"])["message"]
                    if message["method"] == "Network.responseReceived":
                        response_url = message["params"]["response"]["url"]
                        
                        # Check if URL contains any of the target patterns
                        if any(pattern in response_url for pattern in self.file_patterns):
                            # Check if URL is likely a video
                            if self.is_video_url(response_url):
                                # Skip if contains any exclude pattern
                                if not any(exclude_pat.lower() in response_url.lower() for exclude_pat in self.exclude_patterns):
                                    all_video_urls.add(response_url)
                except Exception as e:
                    continue
        except Exception as e:
            logger.warning(f"Could not extract from network logs: {str(e)}")
        
        # 2. Extract from HTML
        logger.info("Extracting video URLs from HTML...")
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find all video tags
        for video in soup.find_all('video'):
            # Check source tags within video
            for source in video.find_all('source'):
                src = source.get('src')
                if src:
                    # Convert relative URLs to absolute
                    abs_url = urljoin(self.url, src)
                    
                    # Check if URL is likely a video
                    if self.is_video_url(abs_url):
                        # Skip if contains any exclude pattern
                        if not any(exclude_pat.lower() in abs_url.lower() for exclude_pat in self.exclude_patterns):
                            all_video_urls.add(abs_url)
            
            # Check video tag src attribute
            src = video.get('src')
            if src:
                # Convert relative URLs to absolute
                abs_url = urljoin(self.url, src)
                
                # Check if URL is likely a video
                if self.is_video_url(abs_url):
                    # Skip if contains any exclude pattern
                    if not any(exclude_pat.lower() in abs_url.lower() for exclude_pat in self.exclude_patterns):
                        all_video_urls.add(abs_url)
        
        # Also check for iframe embedded videos
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src')
            if src:
                # Check for common video platforms
                if any(platform in src.lower() for platform in ['youtube.com/embed', 'vimeo.com', 'dailymotion.com/embed']):
                    all_video_urls.add(src)
        
        logger.info(f"Found {len(all_video_urls)} unique video URLs")
        return all_video_urls
    
    def download_videos(self, video_urls):
        """Download videos from URLs to the output directory
        
        Args:
            video_urls (set): Set of video URLs to download
            
        Returns:
            list: List of dictionaries containing metadata about downloaded videos
        """
        return super().download_media(video_urls)

class IntegratedCrawler:
    """Class to handle recursive crawling of websites with image extraction"""
    
    def __init__(self, max_depth=2, delay=3, headless=True, respect_robots_txt=True):
        """Initialize the integrated crawler
        
        Args:
            max_depth (int): Maximum depth for recursive crawling
            delay (int): Delay between requests in seconds to avoid rate limiting
            headless (bool): Whether to run Chrome in headless mode
            respect_robots_txt (bool): Whether to respect robots.txt
        """
        self.max_depth = max_depth
        self.delay = delay
        self.headless = headless
        self.respect_robots_txt = respect_robots_txt
        self.crawled_urls = set()  # Keep track of already crawled URLs to avoid duplicates
        self.robots_cache = {}  # Cache for robots.txt parsers
        
        logger.info(f"Initialized IntegratedCrawler with max_depth={max_depth}, delay={delay}s")
    
    def get_robots_parser(self, url):
        """Get a RobotFileParser for the given URL
        
        Args:
            url (str): URL to get robots.txt parser for
            
        Returns:
            RobotFileParser: Parser for robots.txt
        """
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
            # Return a permissive parser if robots.txt cannot be read
            permissive_parser = RobotFileParser()
            permissive_parser.parse(['User-agent: *', 'Allow: /'])
            self.robots_cache[base_url] = permissive_parser
            return permissive_parser
    
    def can_fetch(self, url):
        """Check if the URL can be fetched according to robots.txt
        
        Args:
            url (str): URL to check
            
        Returns:
            bool: True if URL can be fetched, False otherwise
        """
        if not self.respect_robots_txt:
            return True
            
        try:
            rp = self.get_robots_parser(url)
            return rp.can_fetch("*", url)
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {str(e)}")
            return True  # Default to allowing if there's an error
    
    def sanitize_title_for_folder_name(self, title):
        """Create a safe folder name from a page title
        
        Args:
            title (str): Page title to sanitize
            
        Returns:
            str: Sanitized folder name
        """
        try:
            if not title or title == "Title not found":
                # If no title is available, return None so we can fall back to URL-based naming
                return None
                
            # Remove any part after a pipe, colon, or dash with surrounding spaces
            # This typically removes site names like "| INDIAN CULTURE" or "- Website Name"
            title = re.split(r'\s*[\|\-\:]\s*', title)[0].strip()
            
            # Limit to first 5 words for brevity
            words = title.split()
            if len(words) > 5:
                title = ' '.join(words[:5])
            
            # Replace spaces with underscores and remove any characters that aren't alphanumeric, underscore, or hyphen
            slug = re.sub(r'[^a-zA-Z0-9_-]', '_', title.replace(' ', '_'))
            
            # Ensure the slug is not too long
            if len(slug) > 100:
                slug = slug[:100]
            
            # Ensure the slug is not empty
            if not slug:
                return None
                
            return slug
            
        except Exception as e:
            logger.error(f"Error sanitizing title for folder name: {str(e)}")
            return None
    
    def sanitize_url_for_folder_name(self, url):
        """Create a safe folder name from a URL
        
        Args:
            url (str): URL to sanitize
            
        Returns:
            str: Sanitized folder name
        """
        try:
            # Parse the URL
            parsed_url = urlparse(url)
            
            # Extract the path and query components
            path = parsed_url.path
            
            # Try to extract meaningful text from the path
            if path:
                # Remove trailing slash if present
                if path.endswith('/'):
                    path = path[:-1]
                
                # Split the path by '/' and get the last part
                path_parts = path.split('/')
                last_part = path_parts[-1] if path_parts[-1] else (path_parts[-2] if len(path_parts) > 1 else "")
                
                # If we have a meaningful last part, use it
                if last_part:
                    # Replace hyphens and underscores with spaces
                    text_name = last_part.replace('-', ' ').replace('_', ' ')
                    
                    # Remove file extensions if present
                    if '.' in text_name:
                        text_name = text_name.split('.')[0]
                    
                    # Convert to title case for readability
                    text_name = ' '.join(word.capitalize() for word in text_name.split())
                    
                    # Sanitize the name to ensure it's a valid folder name
                    # Replace spaces with underscores and remove any characters that aren't alphanumeric, underscore, or hyphen
                    slug = re.sub(r'[^a-zA-Z0-9_-]', '_', text_name.replace(' ', '_'))
                    
                    # Ensure the slug is not too long
                    if len(slug) > 100:
                        slug = slug[:100]
                    
                    return slug
            
            # If we couldn't extract a meaningful name from the path, try the domain
            domain = parsed_url.netloc.replace('www.', '')
            domain_parts = domain.split('.')
            
            # Use the first part of the domain (before the first dot)
            if domain_parts:
                domain_name = domain_parts[0].capitalize()
                # Sanitize the domain name
                slug = re.sub(r'[^a-zA-Z0-9_-]', '_', domain_name)
                
                # Add a timestamp to ensure uniqueness
                timestamp = int(time.time())
                slug = f"{slug}_{timestamp}"
                
                # Ensure the slug is not too long
                if len(slug) > 100:
                    slug = slug[:100]
                
                return slug
            
            # Fallback to a descriptive name with timestamp
            timestamp = int(time.time())
            return f"Web_Page_{timestamp}"
            
        except Exception as e:
            logger.error(f"Error sanitizing URL for folder name: {str(e)}")
            # Fallback to a descriptive name with timestamp
            timestamp = int(time.time())
            return f"Web_Page_{timestamp}"
    
    def parse_links_file(self, links_file):
        """Parse the output_links.json file to extract valid URLs
        
        Args:
            links_file (str): Path to the links JSON file
            
        Returns:
            list: List of valid URLs
        """
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
        """Recursively crawl a URL up to the maximum depth
        
        Args:
            url (str): URL to crawl
            current_depth (int): Current crawling depth
            parent_folder (str): Parent folder path for nested structure
            
        Returns:
            bool: True if crawling was successful, False otherwise
        """
        # Check if we've already crawled this URL to avoid cycles
        if url in self.crawled_urls:
            logger.info(f"URL already crawled, skipping: {url}")
            return True
        
        # Check if we can fetch this URL according to robots.txt
        if not self.can_fetch(url):
            logger.info(f"URL disallowed by robots.txt, skipping: {url}")
            return True
        
        # Add URL to crawled set
        self.crawled_urls.add(url)
        
        # Check if we've reached the maximum depth
        if current_depth > self.max_depth:
            logger.info(f"Reached maximum depth ({self.max_depth}), stopping recursion for: {url}")
            return True
        
        logger.info(f"Crawling URL: {url} (Depth: {current_depth}/{self.max_depth})")
        
        # Create crawler instance
        crawler = WebsiteCrawler(headless=self.headless)
        
        try:
            # Validate URL format
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                logger.info(f"URL modified to include protocol: {url}")
            
            # Crawl the URL
            content_data, links_data = crawler.crawl(url)
            
            # Try to use the page title for the folder name
            title = content_data.get("title", "")
            slug = self.sanitize_title_for_folder_name(title)
            
            # If we couldn't get a valid slug from the title, fall back to URL-based naming
            if not slug:
                slug = self.sanitize_url_for_folder_name(url)
                
            # Create folder for this URL
            if parent_folder:
                output_folder = os.path.join(parent_folder, slug)
            else:
                output_folder = slug
                
            logger.info(f"Output folder: {output_folder}")
            
            # Create media subfolders
            images_folder = os.path.join(output_folder, "images")
            videos_folder = os.path.join(output_folder, "videos")
            os.makedirs(images_folder, exist_ok=True)
            os.makedirs(videos_folder, exist_ok=True)
            
            # Extract media
            logger.info(f"Extracting media from {url}")
            
            # Setup Chrome options for media extraction
            options = Options()
            if self.headless:
                options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
            
            media_driver = webdriver.Chrome(options=options)
            
            try:
                # Load the target page
                media_driver.get(url)
                
                # Wait for page to load
                media_driver.implicitly_wait(10)
                
                # Create image extractor
                image_extractor = ImageExtractor(url, images_folder)
                
                # Extract image URLs
                image_urls = image_extractor.extract_images_from_driver(media_driver)
                
                # Download images
                downloaded_images = image_extractor.download_images(image_urls)
                
                # Add image metadata to content_data
                content_data["images"] = downloaded_images
                
                logger.info(f"Downloaded {len(downloaded_images)} images to {images_folder}")
                
                # Create video extractor
                video_extractor = VideoExtractor(url, videos_folder)
                
                # Extract video URLs
                video_urls = video_extractor.extract_videos_from_driver(media_driver)
                
                # Download videos
                downloaded_videos = video_extractor.download_videos(video_urls)
                
                # Add video metadata to content_data
                content_data["videos"] = downloaded_videos
                
                logger.info(f"Downloaded {len(downloaded_videos)} videos to {videos_folder}")
                
            except Exception as e:
                logger.error(f"Error extracting media from {url}: {str(e)}")
                content_data["images"] = []
                content_data["videos"] = []
            finally:
                # Close the media driver
                media_driver.quit()
            
            # Define output filenames
            content_filename = os.path.join(output_folder, "output_content.json")
            links_filename = os.path.join(output_folder, "output_links.json")
            
            # Deduplicate links
            links_data = dedupe_links(links_data)
            
            # Save results to JSON files
            crawler.save_to_json(content_data, content_filename)
            crawler.save_to_json(links_data, links_filename)
            
            logger.info(f"Results saved in directory: {output_folder}/")
            
            # If we haven't reached the maximum depth, recursively crawl the links
            if current_depth < self.max_depth:
                # Parse the links file we just created
                urls_to_crawl = self.parse_links_file(links_filename)
                
                # Recursively crawl each URL
                for i, next_url in enumerate(urls_to_crawl):
                    logger.info(f"Processing link {i+1}/{len(urls_to_crawl)} from {url}")
                    
                    # Add delay between requests to avoid rate limiting
                    if i > 0:
                        logger.info(f"Waiting {self.delay} seconds before next request...")
                        time.sleep(self.delay)
                    
                    # Recursively crawl the URL
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
            # Always close the browser
            crawler.close()
            
    def start_crawling(self, start_url):
        """Start the recursive crawling process from a given URL
        
        Args:
            start_url (str): Starting URL for crawling
            
        Returns:
            bool: True if crawling was successful, False otherwise
        """
        logger.info(f"Starting recursive crawling from URL: {start_url}")
        logger.info(f"Maximum depth: {self.max_depth}, Delay between requests: {self.delay}s")
        
        start_time = time.time()
        result = self.crawl_url_recursive(start_url)
        end_time = time.time()
        
        duration = end_time - start_time
        logger.info(f"Recursive crawling completed in {duration:.2f} seconds")
        logger.info(f"Total URLs crawled: {len(self.crawled_urls)}")
        
        return result


def main():
    """Main entry point for the integrated crawler script"""
    parser = argparse.ArgumentParser(
        description="Integrated Web Crawler with Image Extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # URL argument for crawling
    parser.add_argument("url", nargs="?", help="URL to crawl")
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode")
    parser.add_argument("--max-depth", type=int, default=2, help="Maximum depth for recursive crawling")
    parser.add_argument("--delay", type=int, default=3, help="Delay between requests in seconds")
    parser.add_argument("--no-robots", action="store_true", help="Ignore robots.txt")
    
    # Dedupe file command (keeping compatibility with combined_crawler.py)
    parser.add_argument("--dedupe-file", help="Path to input JSON file for deduplication")
    parser.add_argument("--output", help="Path to output JSON file for deduplication (defaults to stdout)")
    
    # Logging level
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], 
                        default="INFO", help="Set the logging level")
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    if args.dedupe_file:
        # Handle deduplication of an existing file (reusing from combined_crawler.py)
        from combined_crawler import dedupe_command
        dedupe_args = argparse.Namespace(input=args.dedupe_file, output=args.output)
        dedupe_command(dedupe_args)
    elif args.url:
        # Handle recursive crawling
        crawler = IntegratedCrawler(
            max_depth=args.max_depth,
            delay=args.delay,
            headless=args.headless,
            respect_robots_txt=not args.no_robots
        )
        crawler.start_crawling(args.url)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()