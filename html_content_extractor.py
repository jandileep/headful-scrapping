#!/usr/bin/env python3
"""
HTML Content Extractor Module

This module provides the HtmlContentExtractor class for extracting structured content from HTML pages.
"""

import os
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

logger = logging.getLogger("HtmlContentExtractor")

class HtmlContentExtractor:
    """Class to handle HTML content extraction from websites"""
    
    def __init__(self, url, output_dir, headers=None):
        """Initialize the HTML content extractor
        
        Args:
            url (str): URL of the website to extract content from
            output_dir (str): Directory to save downloaded images
            headers (dict): HTTP headers to use for requests
        """
        self.url = url
        self.output_dir = output_dir
        
        # Default headers if none provided
        if headers is None:
            self.headers = {
                "Referer": url,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        else:
            self.headers = headers
            
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Create images directory
        self.images_dir = os.path.join(output_dir, "images")
        os.makedirs(self.images_dir, exist_ok=True)
    
    def extract_content_from_driver(self, driver):
        """Extract structured content from a Selenium WebDriver instance
        
        Args:
            driver (WebDriver): Selenium WebDriver instance
            
        Returns:
            dict: Dictionary containing structured content
        """
        logger.info("Extracting content from page...")
        
        # Get the page source
        page_source = driver.page_source
        
        # Get the page title
        title = driver.title
        
        # Parse the HTML content
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Extract content
        content = self._extract_content_from_html(soup, title)
        
        return content
    
    def _extract_content_from_html(self, soup, title):
        """Extract structured content from BeautifulSoup object
        
        Args:
            soup (BeautifulSoup): BeautifulSoup object of the page
            title (str): Page title
            
        Returns:
            dict: Dictionary containing structured content
        """
        # Initialize the result structure
        result = {
            "title": title,
            "content_type": "html",
            "paragraphs": [],
            "images": []
        }
        
        # Try to find the main content area
        main_content = self._find_main_content_area(soup)
        
        # Extract paragraphs and images together to maintain association
        paragraphs, images_with_paragraphs = self._extract_content_with_context(main_content)
        result["paragraphs"] = paragraphs
        
        # Download images and add metadata including paragraph content
        downloaded_images = self._download_images(images_with_paragraphs)
        result["images"] = downloaded_images
        
        return result
    
    def _find_main_content_area(self, soup):
        """Find the main content area of the page
        
        Args:
            soup (BeautifulSoup): BeautifulSoup object of the page
            
        Returns:
            BeautifulSoup: Main content area
        """
        # Try common content area identifiers
        content_candidates = [
            soup.find('div', id='content'),
            soup.find('div', id='main-content'),
            soup.find('div', id='storyarea'),
            soup.find('article'),
            soup.find('main'),
            soup.find('div', class_='content'),
            soup.find('div', class_='main-content'),
            soup.find('div', class_='article-content')
        ]
        
        # Use the first non-None candidate
        for candidate in content_candidates:
            if candidate:
                return candidate
        
        # If no specific content area found, use the body
        return soup.find('body')
    
    def _extract_content_with_context(self, content_area):
        """Extract paragraphs and images together to maintain context
        
        Args:
            content_area (BeautifulSoup): Content area to extract content from
            
        Returns:
            tuple: (list of paragraph texts, list of image info with paragraph context)
        """
        paragraphs = []
        images_with_paragraphs = []
        current_paragraph = ""
        
        if not content_area:
            return paragraphs, images_with_paragraphs
        
        # Process all elements in order
        for element in content_area.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'img', 'figure']):
            # Handle paragraph and header elements
            if element.name in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                text = element.get_text(strip=True)
                if text:
                    # Add header marker for header elements
                    if element.name.startswith('h'):
                        level = element.name[1]
                        text = f"{'#' * int(level)} {text}"
                    
                    # Update current paragraph
                    current_paragraph = text
                    paragraphs.append(text)
            
            # Handle image elements
            elif element.name == 'img':
                self._process_image_element(element, current_paragraph, images_with_paragraphs)
            
            # Handle figure elements that might contain images
            elif element.name == 'figure':
                img = element.find('img')
                if img:
                    self._process_image_element(img, current_paragraph, images_with_paragraphs,
                                               figure_element=element)
        
        return paragraphs, images_with_paragraphs
    
    def _process_image_element(self, img, current_paragraph, images_with_paragraphs, figure_element=None):
        """Process an image element and add it to the images list with paragraph context
        
        Args:
            img (BeautifulSoup): Image element
            current_paragraph (str): Current paragraph text
            images_with_paragraphs (list): List to add image info to
            figure_element (BeautifulSoup, optional): Parent figure element if available
        """
        src = img.get('src')
        if src:
            # Convert relative URLs to absolute
            abs_url = urljoin(self.url, src)
            
            # Get alt text and title
            alt_text = img.get('alt', '')
            img_title = img.get('title', '')
            
            # Try to find caption using multiple methods
            caption = self._extract_image_caption(img, figure_element)
            
            # If no caption was found but alt text is available, use it as a fallback caption
            if not caption and alt_text and len(alt_text) > 5:  # Only use meaningful alt text
                caption = alt_text
            
            # If still no caption but title is available, use it
            if not caption and img_title:
                caption = img_title
            
            image_info = {
                "url": abs_url,
                "alt_text": alt_text,
                "title": img_title,
                "caption": caption,
                "paragraph": current_paragraph
            }
            
            images_with_paragraphs.append(image_info)
    
    def _extract_image_caption(self, img, figure_element=None):
        """Extract caption for an image using multiple methods
        
        Args:
            img (BeautifulSoup): Image element
            figure_element (BeautifulSoup, optional): Parent figure element if available
            
        Returns:
            str: Caption text or empty string if no caption found
        """
        caption = ""
        
        # Method 1: If we have a figure element, look for figcaption
        if figure_element:
            caption_elem = figure_element.find('figcaption')
            if caption_elem:
                caption = caption_elem.get_text(strip=True)
                if caption:
                    return caption
        
        # Method 2: Check for adjacent caption elements
        parent = img.parent
        if parent:
            # Check for common caption classes in parent or siblings
            for caption_class in ['caption', 'wp-caption-text', 'figcaption', 'image-caption', 'storycaption']:
                # Check in parent
                caption_elem = parent.find(class_=caption_class)
                if caption_elem:
                    caption = caption_elem.get_text(strip=True)
                    if caption:
                        return caption
                
                # Check in next sibling
                next_sibling = img.find_next_sibling()
                if next_sibling and (next_sibling.has_attr('class') and
                                    any(c in caption_class for c in next_sibling.get('class', []))):
                    caption = next_sibling.get_text(strip=True)
                    if caption:
                        return caption
        
        # Method 3: Check for aria-label attribute
        aria_label = img.get('aria-label', '')
        if aria_label:
            return aria_label
        
        # Method 4: Check for data-caption attribute
        data_caption = img.get('data-caption', '')
        if data_caption:
            return data_caption
        
        return caption
    
    def _download_images(self, images):
        """Download images and add local path information
        
        Args:
            images (list): List of image information dictionaries
            
        Returns:
            list: List of image information dictionaries with local paths
        """
        downloaded_images = []
        
        for i, image_info in enumerate(images):
            try:
                image_url = image_info["url"]
                
                # Parse URL to extract filename
                parsed_url = urlparse(image_url)
                filename = os.path.basename(parsed_url.path).split('?')[0]
                
                # If filename is empty or doesn't have extension, create a default one
                if not filename or '.' not in filename:
                    filename = f"image_{i}.jpg"
                
                # Create unique filename to avoid overwriting
                file_path = os.path.join(self.images_dir, filename)
                if os.path.exists(file_path):
                    name, ext = os.path.splitext(filename)
                    file_path = os.path.join(self.images_dir, f"{name}_{i}{ext}")
                
                # Download the image
                logger.info(f"Downloading image: {image_url}")
                response = requests.get(image_url, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    # Save the image
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    
                    # Add local path to image info
                    image_info["local_path"] = file_path
                    image_info["content_type"] = response.headers.get('Content-Type', '')
                    
                    downloaded_images.append(image_info)
                    logger.info(f"✅ Saved as: {os.path.basename(file_path)}")
                else:
                    logger.error(f"❌ Failed ({response.status_code}): {image_url}")
            
            except Exception as e:
                logger.error(f"❌ Error downloading image: {str(e)}")
        
        return downloaded_images