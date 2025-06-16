#!/usr/bin/env python3
"""
Integrated Web Crawler with Image Extraction

This script combines the functionality of aawler.py and adv_extract_image.py to:
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

import argparse
import logging
import sys
from combined_crawler import dedupe_command

# Import the crawler module
from crawler import IntegratedCrawler

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