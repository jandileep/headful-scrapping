#!/usr/bin/env python3
"""
Image Extractor Module

This module provides the ImageExtractor class for extracting images from websites.
"""

import os
import re
import json
import logging
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from media_extractor import MediaExtractor

logger = logging.getLogger("ImageExtractor")

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