#!/usr/bin/env python3
"""
Video Extractor Module

This module provides the VideoExtractor class for extracting videos from websites.
"""

import os
import json
import logging
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from media_extractor import MediaExtractor

logger = logging.getLogger("VideoExtractor")

class VideoExtractor(MediaExtractor):
    """Class to handle video extraction from websites"""
    
    def __init__(self, url, output_dir, file_patterns=None, exclude_patterns=None, headers=None):
        """Initialize the video extractor
        
        Args:
            url (str): URL of the website to extract videos from
            output_dir (str): Directory to save downloaded videos
            file_patterns (list): List of file path patterns to match in URLs
            exclude_patterns (list): List of patterns to exclude from results
            headers (dict): HTTP headers to use for requests
        """
        # Add video-specific patterns
        if file_patterns is None:
            file_patterns = [
                "sites/default/files",
                "system/files",
                "videos",
                "video",
                "media",
                "uploads"
            ]
            
        super().__init__(url, output_dir, file_patterns, exclude_patterns, headers)
        
    def is_video_url(self, url):
        """Check if a URL is likely a video based on extension or content type.
        
        Args:
            url (str): URL to check
            
        Returns:
            bool: True if URL is likely a video, False otherwise
        """
        video_extensions = ['.mp4', '.webm', '.ogg', '.mov', '.avi', '.wmv', '.flv', '.mkv', '.m4v']
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        # Exclude videos with excluded patterns in the filename
        if any(exclude_pat.lower() in os.path.basename(path).lower() for exclude_pat in self.exclude_patterns):
            return False
        
        # Check extensions
        return any(path.endswith(ext) for ext in video_extensions)
    
    def extract_videos_from_driver(self, driver):
        """Extract video URLs from a Selenium WebDriver instance
        
        Args:
            driver (WebDriver): Selenium WebDriver instance
            
        Returns:
            set: Set of video URLs
        """
        all_video_urls = set()
        
        # 1. Extract from network logs
        logger.info("Extracting video URLs from network logs...")
        try:
            logs = driver.get_log("performance")
            
            for entry in logs:
                try:
                    message = json.loads(entry["message"])["message"]
                    if message["method"] == "Network.responseReceived":
                        response_url = message["params"]["response"]["url"]
                        
                        # Check if URL contains any of the target patterns
                        if any(pattern in response_url for pattern in self.file_patterns):
                            # Check if URL is likely a video
                            if self.is_video_url(response_url):
                                # Skip if contains any exclude pattern
                                if not any(exclude_pat.lower() in response_url.lower() for exclude_pat in self.exclude_patterns):
                                    all_video_urls.add(response_url)
                except Exception as e:
                    continue
        except Exception as e:
            logger.warning(f"Could not extract from network logs: {str(e)}")
        
        # 2. Extract from HTML
        logger.info("Extracting video URLs from HTML...")
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find all video tags
        for video in soup.find_all('video'):
            # Check source tags within video
            for source in video.find_all('source'):
                src = source.get('src')
                if src:
                    # Convert relative URLs to absolute
                    abs_url = urljoin(self.url, src)
                    
                    # Check if URL is likely a video
                    if self.is_video_url(abs_url):
                        # Skip if contains any exclude pattern
                        if not any(exclude_pat.lower() in abs_url.lower() for exclude_pat in self.exclude_patterns):
                            all_video_urls.add(abs_url)
            
            # Check video tag src attribute
            src = video.get('src')
            if src:
                # Convert relative URLs to absolute
                abs_url = urljoin(self.url, src)
                
                # Check if URL is likely a video
                if self.is_video_url(abs_url):
                    # Skip if contains any exclude pattern
                    if not any(exclude_pat.lower() in abs_url.lower() for exclude_pat in self.exclude_patterns):
                        all_video_urls.add(abs_url)
        
        # Also check for iframe embedded videos
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src')
            if src:
                # Check for common video platforms
                if any(platform in src.lower() for platform in ['youtube.com/embed', 'vimeo.com', 'dailymotion.com/embed']):
                    all_video_urls.add(src)
        
        logger.info(f"Found {len(all_video_urls)} unique video URLs")
        return all_video_urls
    
    def download_videos(self, video_urls):
        """Download videos from URLs to the output directory
        
        Args:
            video_urls (set): Set of video URLs to download
            
        Returns:
            list: List of dictionaries containing metadata about downloaded videos
        """
        return super().download_media(video_urls)