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
import logging
import sys
from urllib.error import URLError, HTTPError
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

# Import from other modules
from combined_crawler import WebsiteCrawler, dedupe_links, extract_slug_from_url
from html_content_extractor import HtmlContentExtractor

# Configure logging
logger = logging.getLogger("HtmlCrawler")

class HtmlCrawler:
    """Class to handle recursive crawling of websites with HTML content extraction"""
    
    def __init__(self, max_depth=2, delay=3, headless=True, respect_robots_txt=True):
        """Initialize the HTML crawler
        
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
        
        logger.info(f"Initialized HtmlCrawler with max_depth={max_depth}, delay={delay}s")
    
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
            
            # Create images folder
            images_folder = os.path.join(output_folder, "images")
            os.makedirs(images_folder, exist_ok=True)
            
            # Extract HTML content
            logger.info(f"Extracting HTML content from {url}")
            
            # Setup Chrome options for content extraction
            options = Options()
            if self.headless:
                options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            
            content_driver = webdriver.Chrome(options=options)
            
            try:
                # Load the target page
                content_driver.get(url)
                
                # Wait for page to load
                content_driver.implicitly_wait(10)
                
                # Create HTML content extractor
                html_extractor = HtmlContentExtractor(url, output_folder)
                
                # Extract HTML content
                html_content = html_extractor.extract_content_from_driver(content_driver)
                
                # Add URL to content data
                content_data["url"] = url
                
                # Add HTML content to content data
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
                # Close the content driver
                content_driver.quit()
            
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