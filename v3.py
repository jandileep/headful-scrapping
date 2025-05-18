import json
import time
import argparse
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
        """Get the entire page content"""
        try:
            return self.driver.page_source
        except Exception as e:
            return f"Error extracting page content: {str(e)}"
            
    def save_to_json(self, data, filename):
        """Save the given data to a JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving data to JSON: {str(e)}")
            
    def close(self):
        """Close the browser"""
        self.driver.quit()
        

def main():
    parser = argparse.ArgumentParser(description='Web Crawler using Selenium')
    parser.add_argument('url', help='URL to crawl')
    parser.add_argument('--output', help='Base name for output files', default='output')
    parser.add_argument('--headless', action='store_true', help='Run Chrome in headless mode')
    
    args = parser.parse_args()
    
    crawler = WebsiteCrawler(headless=args.headless)
    
    try:
        content_data, links_data = crawler.crawl(args.url)
        
        # Save results to JSON files
        crawler.save_to_json(content_data, f"{args.output}_content.json")
        crawler.save_to_json(links_data, f"{args.output}_links.json")
        
    finally:
        crawler.close()


if __name__ == "__main__":
    main()