#!/usr/bin/env python3
"""
Test script for the integrated crawler

This script demonstrates how to use the integrated crawler with different options.
"""

import argparse
import logging
from integrated_crawler import IntegratedCrawler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_crawler.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("TestCrawler")

def main():
    """Main entry point for the test script"""
    parser = argparse.ArgumentParser(
        description="Test the integrated crawler with different options",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # URL argument for crawling
    parser.add_argument("url", help="URL to crawl")
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode")
    parser.add_argument("--max-depth", type=int, default=1, help="Maximum depth for recursive crawling")
    parser.add_argument("--delay", type=int, default=3, help="Delay between requests in seconds")
    parser.add_argument("--no-robots", action="store_true", help="Ignore robots.txt")
    
    args = parser.parse_args()
    
    logger.info(f"Starting test crawl of {args.url} with max depth {args.max_depth}")
    
    # Create crawler instance
    crawler = IntegratedCrawler(
        max_depth=args.max_depth,
        delay=args.delay,
        headless=args.headless,
        respect_robots_txt=not args.no_robots
    )
    
    # Start crawling
    result = crawler.start_crawling(args.url)
    
    if result:
        logger.info("Crawling completed successfully")
    else:
        logger.error("Crawling failed")

if __name__ == "__main__":
    main()