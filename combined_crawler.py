#!/usr/bin/env python3
"""
Web Crawler with Link Deduplication

This script:
1. Accepts a URL as input
2. Extracts the website's slug to create a dedicated output folder
3. Processes the URL to extract text content and links
4. Saves two separate JSON files in the slug-named folder:
   - output_content.json: containing the extracted text and source URL
   - output_links.json: containing all links found on the page

Usage:
    # For crawling a website:
    python combined_crawler.py <url> [--headless] [--dedupe]
    
    # For deduplicating links in an existing JSON file:
    python combined_crawler.py --dedupe-file <input_file> [<output_file>]
"""

import json
import time
import argparse
import os
import re
import urllib.parse
from collections import OrderedDict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


class WebsiteCrawler:
    def __init__(self, headless=True):
        """Initialize the web crawler with Chrome driver"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
    def crawl(self, url, wait_time=10):
        """Crawl the given URL and extract required data"""
        print(f"Crawling URL: {url}")
        
        try:
            # Navigate to URL
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Get page title
            title = self.get_page_title()
            
            # Get text after title
            title_text = self.get_text_after_title()
            
            # Get links from view-grid
            links = self.get_links_from_grid()
            
            # Get full page content
            page_content = self.get_page_content()
            
            result = {
                "url": url,
                "title": title,
                "title_text": title_text,
                "page_content": page_content
            }
            
            links_result = {
                "url": url,
                "links": links
            }
            
            return result, links_result
            
        except Exception as e:
            print(f"Error during crawling: {str(e)}")
            return {"error": str(e)}, {"error": str(e)}
        
    def get_page_title(self):
        """Get page title"""
        try:
            return self.driver.title
        except:
            return "Title not found"
            
    def get_text_after_title(self):
        """Extract text after the first title tag"""
        try:
            # Find the first title element
            title_element = self.driver.find_element(By.TAG_NAME, "title")
            
            # Get parent element containing the title
            parent = title_element.find_element(By.XPATH, "./..")
            
            # Get text of the parent element (which should include text after title)
            # But this is tricky since title is usually in head, so we may need to adjust approach
            
            # Alternative approach - try to find the first significant text block in the body
            body = self.driver.find_element(By.TAG_NAME, "body")
            headers = body.find_elements(By.XPATH, ".//h1|.//h2|.//h3")
            
            if headers:
                return headers[0].text
            else:
                # If no headers found, get the first paragraph
                paragraphs = body.find_elements(By.TAG_NAME, "p")
                if paragraphs:
                    return paragraphs[0].text
                else:
                    return "No text content found after title"
                    
        except NoSuchElementException:
            return "Title element not found"
        except Exception as e:
            return f"Error extracting text after title: {str(e)}"
            
    def get_links_from_grid(self):
        """Extract only links from tables, ignoring header and footer sections"""
        links = []
        try:
            # First try the specified grid class
            try:
                # Wait for grid to be present
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".view-view-grid.horizontal.cols"))
                )
                
                # Find the grid element
                grid = self.driver.find_element(By.CSS_SELECTOR, ".view-view-grid.horizontal.cols")
                
                # Find all anchor elements within the grid
                anchors = grid.find_elements(By.TAG_NAME, "a")
                
                # Extract href and text from each anchor
                for anchor in anchors:
                    link_data = {
                        "url": anchor.get_attribute("href"),
                        "text": anchor.text.strip()
                    }
                    links.append(link_data)
                
                if links:
                    print(f"Found {len(links)} links in the view-view-grid")
                    return links
            except (TimeoutException, NoSuchElementException):
                print("view-view-grid not found, trying tables...")
            
            # Look for tables specifically
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            print(f"Found {len(tables)} tables on the page")
            
            for table in tables:
                # Check if this table is in header or footer
                ancestors = table.find_elements(By.XPATH, "./ancestor::header | ./ancestor::footer")
                if ancestors:
                    print("Skipping table in header/footer")
                    continue
                    
                # Also check for common header/footer class names
                table_classes = table.get_attribute("class") or ""
                if any(x in table_classes.lower() for x in ["header", "footer", "nav", "menu"]):
                    print(f"Skipping table with classes: {table_classes}")
                    continue
                
                print(f"Processing table: {table_classes}")
                anchors = table.find_elements(By.TAG_NAME, "a")
                
                for anchor in anchors:
                    link_data = {
                        "url": anchor.get_attribute("href"),
                        "text": anchor.text.strip()
                    }
                    if link_data["url"]:  # Only add if URL is not None
                        links.append(link_data)
            
            # If no tables found or no links in tables, try div elements that look like tables
            if not links:
                print("No links found in tables, looking for table-like structures...")
                
                # Look for div structures that might be tables
                table_candidates = self.driver.find_elements(
                    By.XPATH,
                    "//div[contains(@class, 'table') or contains(@class, 'grid') or contains(@class, 'list')]"
                )
                
                for candidate in table_candidates:
                    # Check if this element is in header or footer
                    ancestors = candidate.find_elements(By.XPATH, "./ancestor::header | ./ancestor::footer")
                    if ancestors:
                        continue
                        
                    # Also check for common header/footer class names
                    candidate_classes = candidate.get_attribute("class") or ""
                    if any(x in candidate_classes.lower() for x in ["header", "footer", "nav", "menu"]):
                        continue
                    
                    # Check if this is in the main content area
                    ancestors_main = candidate.find_elements(By.XPATH, "./ancestor::main | ./ancestor::*[contains(@class, 'content')]")
                    if ancestors_main or "content" in candidate_classes.lower():
                        anchors = candidate.find_elements(By.TAG_NAME, "a")
                        
                        for anchor in anchors:
                            link_data = {
                                "url": anchor.get_attribute("href"),
                                "text": anchor.text.strip()
                            }
                            if link_data["url"]:  # Only add if URL is not None
                                links.append(link_data)
                
            print(f"Total links found: {len(links)}")
            return links
                
        except Exception as e:
            print(f"Error extracting links from tables: {str(e)}")
            return []
            
    def get_page_content(self):
        """Extract only text content from the page (no HTML or scripts)"""
        try:
            # Get the body element
            body = self.driver.find_element(By.TAG_NAME, "body")
            
            # Extract all text from the page
            text_content = body.text
            
            return text_content
        except Exception as e:
            return f"Error extracting page content: {str(e)}"
            
    def save_to_json(self, data, filename):
        """Save the given data to a JSON file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving data to JSON: {str(e)}")
            
    def close(self):
        """Close the browser"""
        self.driver.quit()


def dedupe_links(data: dict) -> dict:
    """Return a copy of *data* with duplicate URLs removed."""
    seen: OrderedDict[str, dict] = OrderedDict()

    for link in data.get("links", []):
        url = link.get("url")
        if url is None:
            continue  # skip malformed entries

        # If we've not seen the URL, or this version has text while the stored one is empty, keep it
        if url not in seen or (link.get("text") and not seen[url].get("text")):
            seen[url] = {"url": url, "text": link.get("text", "")}

    # Preserve original order by using the OrderedDict we built
    data["links"] = list(seen.values())
    return data


def extract_slug_from_url(url):
    """Extract a slug from the URL to use as a directory name"""
    try:
        # Parse the URL
        parsed_url = urllib.parse.urlparse(url)
        
        # Get the path and remove trailing slash if present
        path = parsed_url.path
        if path.endswith('/'):
            path = path[:-1]
        
        # If path exists, use the last part of the path as the folder name
        if path:
            # Split the path by '/' and get the last part
            path_parts = path.split('/')
            last_part = path_parts[-1]
            
            # If the last part is not empty, use it as the slug
            if last_part:
                return last_part
        
        # Fallback to the old method if path doesn't exist or is empty
        # Get the domain (remove www. if present)
        domain = parsed_url.netloc.replace('www.', '')
        
        # Replace special characters with underscores in domain only
        domain = re.sub(r'[^a-zA-Z0-9]', '_', domain)
        
        # If path exists but last part was empty, clean the path
        if path and not last_part:
            path = re.sub(r'[^a-zA-Z0-9]', '_', path)
            slug = f"{domain}{path}"
        else:
            slug = domain
            
        # Ensure the slug is not too long
        if len(slug) > 100:
            slug = slug[:100]
            
        return slug
    except Exception as e:
        print(f"Error extracting slug from URL: {str(e)}")
        # Fallback to a simple timestamp
        return f"crawl_{int(time.time())}"

def crawl_url(url, headless=True, should_dedupe=False):
    """Crawl a URL and save results in a slug-named directory"""
    # Extract slug from URL
    slug = extract_slug_from_url(url)
    print(f"Using slug: {slug}")
    
    # Create output directory if it doesn't exist
    os.makedirs(slug, exist_ok=True)
    
    crawler = WebsiteCrawler(headless=headless)
    
    try:
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            print(f"URL modified to include protocol: {url}")
            
        content_data, links_data = crawler.crawl(url)
        
        # Define output filenames
        content_filename = os.path.join(slug, "output_content.json")
        links_filename = os.path.join(slug, "output_links.json")
        
        # Always deduplicate links
        links_data = dedupe_links(links_data)
        print("Links have been deduplicated")
            
        # Save results to JSON files
        crawler.save_to_json(content_data, content_filename)
        crawler.save_to_json(links_data, links_filename)
        
        print(f"Results saved in directory: {slug}/")
        
    except Exception as e:
        print(f"Error crawling URL: {str(e)}")
    finally:
        crawler.close()


def dedupe_command(args):
    """Handle the dedupe command"""
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        cleaned = dedupe_links(data)
        
        result = json.dumps(cleaned, indent=4, ensure_ascii=False)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"Deduplicated links saved to {args.output}")
        else:
            print(result)
    except Exception as e:
        print(f"Error during deduplication: {str(e)}")


def main():
    """Main entry point for the combined script"""
    parser = argparse.ArgumentParser(
        description="Web Crawler with Link Deduplication",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # URL argument for crawling
    parser.add_argument("url", nargs="?", help="URL to crawl")
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode")
    parser.add_argument("--dedupe", action="store_true", help="Deduplicate links before saving")
    
    # Dedupe file command
    parser.add_argument("--dedupe-file", help="Path to input JSON file for deduplication")
    parser.add_argument("--output", help="Path to output JSON file for deduplication (defaults to stdout)")
    
    args = parser.parse_args()
    
    if args.dedupe_file:
        # Handle deduplication of an existing file
        dedupe_args = argparse.Namespace(input=args.dedupe_file, output=args.output)
        dedupe_command(dedupe_args)
    elif args.url:
        # Handle crawling a URL
        crawl_url(args.url, headless=args.headless, should_dedupe=args.dedupe)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()