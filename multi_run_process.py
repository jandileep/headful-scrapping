#!/usr/bin/env python3
"""
multi_run_process.py — PARALLEL EDITION

▸ Crawls all required Indian Culture collections with concurrent python processes.
▸ Combined from: freedom_Archive.sh, images.sh, manuscripts.sh,
  other_collection.sh, paintings.sh.
▸ Each URL is passed to integrated_crawler_html.py with --headless.
▸ Includes progress tracking and logging.
"""

import subprocess
import concurrent.futures
import os
import logfire as logger
from typing import List
import time
# Configure logfire
logger.configure()


# Configuration
SCRIPT = "integrated_crawler_html.py"
MAX_JOBS = 32  # adjust if you have more/fewer logical cores

# Track progress
total_urls = 0
completed_urls = 0
active_jobs = 0


def run(url: str, executor: concurrent.futures.ThreadPoolExecutor) -> concurrent.futures.Future:
    """Run one crawl in a separate process while limiting concurrency"""
    global active_jobs
    
    logger.info(f"Starting crawl for: {url}")
    
    # Submit the job to the executor
    future = executor.submit(
        subprocess.run,
        ["python", SCRIPT, url, "--headless"],
        capture_output=False,
        text=True,
        check=False
    )
    
    return future



def main():
    global total_urls, completed_urls
    
    # Initialize collections with their URL patterns and ranges
    collections = [
        # 1) Museum paintings (0‑1129) – 1,130 pages
        {
            "name": "Museum paintings",
            "url_template": "https://indianculture.gov.in/painting-collections/museum-paintings?page={}",
            "range": range(0, 1130)
        },
        # 2) Site‑wide images (0‑6199) – 6,200 pages
        {
            "name": "Site-wide images",
            "url_template": "https://indianculture.gov.in/images?search_api_fulltext=&page={}",
            "range": range(0, 6200)
        },
        # 3) Manuscripts (0‑8748) – 8,749 pages
        {
            "name": "Manuscripts",
            "url_template": "https://indianculture.gov.in/manuscripts?search_api_fulltext=&page={}",
            "range": range(0, 8749)
        },
        # 4) Other collections (0‑46) – 47 pages
        {
            "name": "Other collections",
            "url_template": "https://indianculture.gov.in/other-collections?search_api_fulltext=&page={}",
            "range": range(0, 47)
        }
    ]
    
    # 5) Freedom‑archive miscellany – 11 single URLs / short ranges
    freedom_archive_urls = [
        "https://indianculture.gov.in/freedom-archive/images",  # no pagination
        "https://indianculture.gov.in/freedom-archive/newspaper-clippings",  # no pagination
        "https://indianculture.gov.in/Historic_Cities_Freedom_Movement",  # single page
        "https://indianculture.gov.in/node/2790124",  # single node
    ]
    
    # Freedom archive museum collections (0-1)
    freedom_museum = {
        "name": "Freedom archive museum collections",
        "url_template": "https://indianculture.gov.in/freedom-archive/museum-collections?page={}",
        "range": range(0, 2)
    }
    
    # Unsung heroes (0-4)
    unsung_heroes = {
        "name": "Unsung heroes",
        "url_template": "https://indianculture.gov.in/unsung-heroes?page={}",
        "range": range(0, 5)
    }
    
    # Calculate total URLs to process
    for collection in collections:
        total_urls += len(collection["range"])
    
    total_urls += len(freedom_archive_urls)
    total_urls += len(freedom_museum["range"])
    total_urls += len(unsung_heroes["range"])
    
    with logfire.span("PROGRESS") as span:
        span.info(f"Starting crawl of {total_urls} URLs with max {MAX_JOBS} concurrent jobs")
    
    # Create a thread pool executor to manage the subprocesses
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_JOBS) as executor:
        futures = []
        
        # Process all collections with pagination
        for collection in collections:
            logger.info(f"Starting collection: {collection['name']}")
            for page in collection["range"]:
                url = collection["url_template"].format(page)
                futures.append(run(url, executor))
                
                # Log progress periodically
                if len(futures) % 10 == 0:
                    completed_urls = sum(1 for f in futures if f.done())
                    with logfire.span("PROGRESS") as span:
                        percentage = (completed_urls / total_urls) * 100 if total_urls > 0 else 0
                        span.info(f"{completed_urls}/{total_urls} URLs processed ({percentage:.2f}%)")
        
        # Process freedom archive museum collections
        logger.info(f"Starting collection: {freedom_museum['name']}")
        for page in freedom_museum["range"]:
            url = freedom_museum["url_template"].format(page)
            futures.append(run(url, executor))
        
        # Process unsung heroes
        logger.info(f"Starting collection: {unsung_heroes['name']}")
        for page in unsung_heroes["range"]:
            url = unsung_heroes["url_template"].format(page)
            futures.append(run(url, executor))
        
        # Process individual freedom archive URLs
        logger.info("Starting collection: Freedom archive miscellany")
        for url in freedom_archive_urls:
            futures.append(run(url, executor))
        
        # Wait for all futures to complete and log progress
        while futures:
            # Check for completed futures
            completed = [f for f in futures if f.done()]
            if completed:
                # Remove completed futures from the list
                for f in completed:
                    futures.remove(f)
                
                # Update completed count and log progress
                completed_urls += len(completed)
                with logfire.span("PROGRESS") as span:
                    percentage = (completed_urls / total_urls) * 100 if total_urls > 0 else 0
                    span.info(f"{completed_urls}/{total_urls} URLs processed ({percentage:.2f}%)")
            
            # Sleep briefly to avoid busy waiting
            time.sleep(0.5)
    
    with logfire.span("PROGRESS") as span:
        span.info("All crawls complete (parallel mode)")


if __name__ == "__main__":
    main()