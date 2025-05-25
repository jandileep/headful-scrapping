#!/usr/bin/env python3
"""
Recursive Crawler

This script:
1. Traverses all subdirectories to locate every output_links.json file
2. For each discovered file, extracts and processes all contained links
3. Creates a structured subfolder for each crawled link containing:
   - Downloaded images
   - output_content.json with extracted content
   - output_links.json with discovered links
4. Implements proper error handling, rate limiting, and logging
5. Preserves the same parsing logic and content extraction methodology as the original crawler

Usage:
    # For recursive crawling with default settings:
    python recursive_crawler.py [--start-dir=.] [--headless] [--max-depth=2] [--delay=3]
    
    # For deduplicating links in an existing JSON file:
    python recursive_crawler.py --dedupe-file <input_file> [<output_file>]
"""

import os
import json
import time
import logging
import argparse
import sys
from pathlib import Path
from urllib.error import URLError, HTTPError
from selenium.common.exceptions import TimeoutException, WebDriverException

# Import from other modules
from crawler_html import HtmlCrawler
from combined_crawler import dedupe_command, dedupe_links

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("recursive_crawler.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("RecursiveCrawler")

class RecursiveCrawler:
    """Class to handle recursive crawling of links found in output_links.json files"""
    
    def __init__(self, max_depth=2, delay=3, headless=True, respect_robots_txt=True):
        """Initialize the recursive crawler
        
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
        self.processed_files = set()  # Keep track of already processed output_links.json files
        
        logger.info(f"Initialized RecursiveCrawler with max_depth={max_depth}, delay={delay}s")
    
    def find_links_files(self, start_dir):
        """Find all output_links.json files in the given directory and its subdirectories
        
        Args:
            start_dir (str): Directory to start searching from
            
        Returns:
            list: List of paths to output_links.json files
        """
        links_files = []
        
        try:
            logger.info(f"Searching for output_links.json files in {start_dir} and subdirectories")
            
            # Use pathlib for better path handling
            start_path = Path(start_dir)
            
            # Walk through all subdirectories
            for path in start_path.rglob('output_links.json'):
                links_files.append(str(path))
            
            logger.info(f"Found {len(links_files)} output_links.json files")
            return links_files
            
        except Exception as e:
            logger.error(f"Error finding output_links.json files: {str(e)}")
            return []
    
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
    
    def process_links_file(self, links_file):
        """Process a single output_links.json file
        
        Args:
            links_file (str): Path to the links JSON file
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        # Check if we've already processed this file
        if links_file in self.processed_files:
            logger.info(f"File already processed, skipping: {links_file}")
            return True
        
        # Add file to processed set
        self.processed_files.add(links_file)
        
        logger.info(f"Processing links file: {links_file}")
        
        # Parse the links file
        urls = self.parse_links_file(links_file)
        
        # Get the parent directory of the links file
        parent_dir = os.path.dirname(links_file)
        
        # Create an HTML crawler instance
        crawler = HtmlCrawler(
            max_depth=self.max_depth,
            delay=self.delay,
            headless=self.headless,
            respect_robots_txt=self.respect_robots_txt
        )
        
        # Process each URL
        for i, url in enumerate(urls):
            logger.info(f"Processing URL {i+1}/{len(urls)}: {url}")
            
            # Add delay between requests to avoid rate limiting
            if i > 0:
                logger.info(f"Waiting {self.delay} seconds before next request...")
                time.sleep(self.delay)
            
            # Crawl the URL
            try:
                # Check if we've already crawled this URL
                if url in self.crawled_urls:
                    logger.info(f"URL already crawled, skipping: {url}")
                    continue
                
                # Add URL to crawled set
                self.crawled_urls.add(url)
                
                # Crawl the URL recursively
                crawler.crawl_url_recursive(url, current_depth=0, parent_folder=parent_dir)
                
            except HTTPError as e:
                logger.error(f"HTTP Error during crawling {url}: {e.code} - {e.reason}")
            except URLError as e:
                logger.error(f"URL Error during crawling {url}: {str(e.reason)}")
            except WebDriverException as e:
                logger.error(f"WebDriver Error during crawling {url}: {str(e)}")
            except TimeoutException:
                logger.error(f"Timeout Error during crawling {url}")
            except Exception as e:
                logger.error(f"Unexpected error during crawling {url}: {str(e)}")
        
        return True
    
    def start_recursive_crawling(self, start_dir="."):
        """Start the recursive crawling process from a given directory
        
        Args:
            start_dir (str): Directory to start searching from
            
        Returns:
            bool: True if crawling was successful, False otherwise
        """
        logger.info(f"Starting recursive crawling from directory: {start_dir}")
        logger.info(f"Maximum depth: {self.max_depth}, Delay between requests: {self.delay}s")
        
        start_time = time.time()
        
        # Find all output_links.json files
        links_files = self.find_links_files(start_dir)
        
        # Process each links file
        for links_file in links_files:
            self.process_links_file(links_file)
            
            # After processing each file, look for new output_links.json files
            # that might have been created during crawling
            new_links_files = self.find_links_files(start_dir)
            
            # Filter out already processed files
            new_links_files = [f for f in new_links_files if f not in self.processed_files]
            
            # Add new files to the list
            links_files.extend(new_links_files)
        
        end_time = time.time()
        
        duration = end_time - start_time
        logger.info(f"Recursive crawling completed in {duration:.2f} seconds")
        logger.info(f"Total URLs crawled: {len(self.crawled_urls)}")
        logger.info(f"Total files processed: {len(self.processed_files)}")
        
        return True


def main():
    """Main entry point for the recursive crawler script"""
    parser = argparse.ArgumentParser(
        description="Recursive Crawler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Directory argument for starting the search
    parser.add_argument("--start-dir", default=".", help="Directory to start searching for output_links.json files")
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
        dedupe_args = argparse.Namespace(input=args.dedupe_file, output=args.output)
        dedupe_command(dedupe_args)
    else:
        # Handle recursive crawling
        crawler = RecursiveCrawler(
            max_depth=args.max_depth,
            delay=args.delay,
            headless=args.headless,
            respect_robots_txt=not args.no_robots
        )
        crawler.start_recursive_crawling(args.start_dir)


if __name__ == "__main__":
    main()