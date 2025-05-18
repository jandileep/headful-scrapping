import os
import json
import time
import re
import requests
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

def scrape_images(url, output_dir="downloaded_images", file_patterns=None, exclude_patterns=None):
    """
    Scrape images from a website based on specified file path patterns.
    
    Args:
        url (str): URL of the website to scrape
        output_dir (str): Directory to save downloaded images
        file_patterns (list): List of file path patterns to match in URLs
        exclude_patterns (list): List of patterns to exclude from results
    """
    # Default patterns for Drupal sites if none provided
    if file_patterns is None:
        file_patterns = [
            "sites/default/files",
            "system/files"
        ]
    
    # Default exclude patterns if none provided
    if exclude_patterns is None:
        exclude_patterns = ["logo"]
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Setup Chrome options
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # Load the target page
        print(f"Loading website: {url}")
        driver.get(url)
        
        # Wait for page to load (adjust if needed)
        driver.implicitly_wait(10)
        
        # Get image URLs from both network logs and HTML
        all_image_urls = set()
        
        # 1. Extract from network logs
        print("Extracting image URLs from network logs...")
        logs = driver.get_log("performance")
        
        for entry in logs:
            try:
                message = json.loads(entry["message"])["message"]
                if message["method"] == "Network.responseReceived":
                    response_url = message["params"]["response"]["url"]
                    
                    # Check if URL contains any of the target patterns
                    if any(pattern in response_url for pattern in file_patterns):
                        # Check if URL is likely an image
                        if is_image_url(response_url):
                            # Skip if contains any exclude pattern
                            if not any(exclude_pat.lower() in response_url.lower() for exclude_pat in exclude_patterns):
                                all_image_urls.add(response_url)
            except Exception as e:
                continue
        
        # 2. Extract from HTML
        print("Extracting image URLs from HTML...")
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find all img tags
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                # Convert relative URLs to absolute
                abs_url = urljoin(url, src)
                
                # Check if URL contains any of the target patterns
                if any(pattern in abs_url for pattern in file_patterns):
                    # Skip if contains any exclude pattern
                    if not any(exclude_pat.lower() in abs_url.lower() for exclude_pat in exclude_patterns):
                        all_image_urls.add(abs_url)
        
        # Also check for background images in CSS
        for elem in soup.find_all(style=True):
            style = elem['style']
            urls = re.findall(r'url\([\'"]?(.*?)[\'"]?\)', style)
            for img_url in urls:
                abs_url = urljoin(url, img_url)
                if any(pattern in abs_url for pattern in file_patterns):
                    # Skip if contains any exclude pattern
                    if not any(exclude_pat.lower() in abs_url.lower() for exclude_pat in exclude_patterns):
                        all_image_urls.add(abs_url)
        
        print(f"Found {len(all_image_urls)} unique image URLs")
        
        # Headers to bypass restrictions
        headers = {
            "Referer": url,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Download images
        print("Downloading images...")
        download_images(all_image_urls, output_dir, headers)
        
    finally:
        # Close the browser
        driver.quit()

def is_image_url(url):
    """Check if a URL is likely an image based on extension or content type."""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico']
    parsed_url = urlparse(url)
    path = parsed_url.path.lower()
    
    # Exclude images with "logo" in the filename
    if "logo" in os.path.basename(path).lower():
        return False
    
    # Check extensions
    return any(path.endswith(ext) for ext in image_extensions)

def download_images(image_urls, output_dir, headers):
    """Download images from URLs to the output directory."""
    for i, img_url in enumerate(image_urls):
        try:
            # Parse URL to extract filename
            parsed_url = urlparse(img_url)
            filename = os.path.basename(parsed_url.path).split('?')[0]
            
            # Skip if "logo" is in the filename
            if "logo" in filename.lower():
                print(f"⏭️ Skipping logo image: {img_url}")
                continue
            
            print(f"Downloading ({i+1}/{len(image_urls)}): {img_url}")
            
            response = requests.get(img_url, headers=headers, timeout=10)
            if response.status_code == 200:
                # If filename is empty or doesn't have extension, create a default one
                if not filename or '.' not in filename:
                    # Try to get extension from Content-Type header
                    content_type = response.headers.get('Content-Type', '')
                    ext = content_type.split('/')[-1] if '/' in content_type else 'jpg'
                    filename = f"image_{i}.{ext}"
                
                # Create unique filename to avoid overwriting
                file_path = os.path.join(output_dir, filename)
                if os.path.exists(file_path):
                    name, ext = os.path.splitext(filename)
                    file_path = os.path.join(output_dir, f"{name}_{i}{ext}")
                
                # Save the image
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"✅ Saved as: {os.path.basename(file_path)}")
            else:
                print(f"❌ Failed ({response.status_code}): {img_url}")
                
            # Sleep briefly to avoid rate limiting
            time.sleep(0.2)
            
        except Exception as e:
            print(f"❌ Error downloading {img_url}: {str(e)}")

def crawl_website(base_url, output_dir="downloaded_images", file_patterns=None, exclude_patterns=None, max_pages=5):
    """
    Crawl website and scrape images from multiple pages.
    
    Args:
        base_url (str): Starting URL for crawling
        output_dir (str): Directory to save downloaded images
        file_patterns (list): List of file path patterns to match in URLs
        exclude_patterns (list): List of patterns to exclude from results
        max_pages (int): Maximum number of pages to crawl
    """
    if file_patterns is None:
        file_patterns = ["sites/default/files", "system/files"]
    
    if exclude_patterns is None:
        exclude_patterns = ["logo"]
    
    # Keep track of visited URLs
    visited_urls = set()
    to_visit = [base_url]
    
    # Setup Chrome options for crawling
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        page_count = 0
        
        while to_visit and page_count < max_pages:
            current_url = to_visit.pop(0)
            
            if current_url in visited_urls:
                continue
                
            print(f"\n--- Crawling page {page_count + 1}/{max_pages}: {current_url} ---")
            visited_urls.add(current_url)
            
            # Create subdirectory for this page
            page_domain = urlparse(current_url).netloc
            page_path = urlparse(current_url).path.strip('/')
            if not page_path:
                page_path = "homepage"
            else:
                # Clean up path for directory name
                page_path = page_path.replace('/', '_')
            
            page_dir = os.path.join(output_dir, f"{page_domain}_{page_path}")
            
            # Scrape images from current page
            scrape_images(current_url, page_dir, file_patterns, exclude_patterns)
            
            # Find links to other pages on same domain
            try:
                driver.get(current_url)
                driver.implicitly_wait(5)
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                base_domain = urlparse(base_url).netloc
                
                # Extract links
                for a_tag in soup.find_all('a', href=True):
                    link = a_tag['href']
                    absolute_link = urljoin(current_url, link)
                    
                    # Only follow links on same domain
                    if urlparse(absolute_link).netloc == base_domain:
                        if absolute_link not in visited_urls and absolute_link not in to_visit:
                            to_visit.append(absolute_link)
            
            except Exception as e:
                print(f"Error exploring links on {current_url}: {str(e)}")
            
            page_count += 1
    
    finally:
        driver.quit()

if __name__ == "__main__":
    # Example usage
    target_url = "https://indianculture.gov.in/food-and-culture/cuisines-of-India"
    
    # Option 1: Scrape single page
    scrape_images(
        url=target_url,
        output_dir="downloaded_images",
        file_patterns=["sites/default/files", "system/files"],
        exclude_patterns=["logo"]  # Exclude images with "logo" in the URL
    )
    
    # Option 2: Crawl website (uncomment to use)
    # crawl_website(
    #     base_url=target_url,
    #     output_dir="downloaded_images_crawl",
    #     file_patterns=["sites/default/files", "system/files"],
    #     exclude_patterns=["logo"],  # Exclude images with "logo" in the URL
    #     max_pages=5  # Limit to avoid crawling too many pages
    # )