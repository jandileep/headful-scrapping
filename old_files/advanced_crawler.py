#!/usr/bin/env python3
"""
Advanced Web Crawler with Recursive Crawling Capability

This script extends combined_crawler.py to implement recursive crawling:
1. Executes the initial crawl and generates the standard output folder with data.json and output_links.json
2. Parses the output_links.json file to extract all valid URLs
3. For each URL in output_links.json, creates a separate subfolder named after a sanitized version of the URL
4. Recursively crawls each URL, storing its data.json and output_links.json in the corresponding subfolder
5. Implements depth control to prevent infinite crawling loops
6. Adds proper error handling for network issues, malformed URLs, and rate limiting
7. Includes logging functionality to track the crawling progress

Usage:
    # For recursive crawling with default settings:
    python advanced_crawler.py <url> [--headless] [--max-depth=2] [--delay=3]
    
    # For deduplicating links in an existing JSON file:
    python advanced_crawler.py --dedupe-file <input_file> [<output_file>]
"""

import json
import time
import argparse
import os
import re
import urllib.parse
import logging
import sys
from collections import OrderedDict
from urllib.error import URLError, HTTPError
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# Import from combined_crawler.py
from combined_crawler import WebsiteCrawler, dedupe_links, extract_slug_from_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crawler.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("AdvancedCrawler")

class RecursiveCrawler:
    """Class to handle recursive crawling of websites"""
    
    def __init__(self, max_depth=2, delay=3, headless=True):
        """Initialize the recursive crawler
        
        Args:
            max_depth (int): Maximum depth for recursive crawling
            delay (int): Delay between requests in seconds to avoid rate limiting
            headless (bool): Whether to run Chrome in headless mode
        """
        self.max_depth = max_depth
        self.delay = delay
        self.headless = headless
        self.crawled_urls = set()  # Keep track of already crawled URLs to avoid duplicates
        logger.info(f"Initialized RecursiveCrawler with max_depth={max_depth}, delay={delay}s")
    
    def sanitize_url_for_folder_name(self, url):
        """Create a safe folder name from a URL
        
        Args:
            url (str): URL to sanitize
            
        Returns:
            str: Sanitized folder name
        """
        try:
            # First try to use the extract_slug_from_url function from combined_crawler
            slug = extract_slug_from_url(url)
            
            # Further sanitize the slug to ensure it's a valid folder name
            # Remove any characters that aren't alphanumeric, underscore, or hyphen
            slug = re.sub(r'[^a-zA-Z0-9_-]', '_', slug)
            
            # Ensure the slug is not too long
            if len(slug) > 100:
                slug = slug[:100]
                
            # Ensure the slug is not empty
            if not slug:
                slug = f"page_{int(time.time())}"
                
            return slug
        except Exception as e:
            logger.error(f"Error sanitizing URL for folder name: {str(e)}")
            # Fallback to a simple timestamp
            return f"page_{int(time.time())}"
    
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
        
        # Add URL to crawled set
        self.crawled_urls.add(url)
        
        # Check if we've reached the maximum depth
        if current_depth > self.max_depth:
            logger.info(f"Reached maximum depth ({self.max_depth}), stopping recursion for: {url}")
            return True
        
        # Create folder for this URL
        slug = self.sanitize_url_for_folder_name(url)
        if parent_folder:
            output_folder = os.path.join(parent_folder, slug)
        else:
            output_folder = slug
        
        logger.info(f"Crawling URL: {url} (Depth: {current_depth}/{self.max_depth})")
        logger.info(f"Output folder: {output_folder}")
        
        # Create crawler instance
        crawler = WebsiteCrawler(headless=self.headless)
        
        try:
            # Validate URL format
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                logger.info(f"URL modified to include protocol: {url}")
            
            # Crawl the URL
            content_data, links_data = crawler.crawl(url)
            
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
    """Main entry point for the advanced crawler script"""
    parser = argparse.ArgumentParser(
        description="Advanced Web Crawler with Recursive Crawling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # URL argument for crawling
    parser.add_argument("url", nargs="?", help="URL to crawl")
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode")
    parser.add_argument("--max-depth", type=int, default=2, help="Maximum depth for recursive crawling")
    parser.add_argument("--delay", type=int, default=3, help="Delay between requests in seconds")
    
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
        crawler = RecursiveCrawler(
            max_depth=args.max_depth,
            delay=args.delay,
            headless=args.headless
        )
        crawler.start_crawling(args.url)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()