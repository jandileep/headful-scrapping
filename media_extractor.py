#!/usr/bin/env python3
"""
Base Media Extractor Module

This module provides the base MediaExtractor class for extracting media from websites.
"""

import os
import time
import logging
import requests
from urllib.parse import urlparse

logger = logging.getLogger("MediaExtractor")

class MediaExtractor:
    """Base class for media extraction from websites"""
    
    def __init__(self, url, output_dir, file_patterns=None, exclude_patterns=None, headers=None):
        """Initialize the media extractor
        
        Args:
            url (str): URL of the website to extract media from
            output_dir (str): Directory to save downloaded media
            file_patterns (list): List of file path patterns to match in URLs
            exclude_patterns (list): List of patterns to exclude from results
            headers (dict): HTTP headers to use for requests
        """
        # Default patterns for media files if none provided
        if file_patterns is None:
            self.file_patterns = [
                "sites/default/files",
                "system/files",
                "uploads",
                "media"
            ]
        else:
            self.file_patterns = file_patterns
        
        # Default exclude patterns if none provided
        if exclude_patterns is None:
            self.exclude_patterns = ["logo", "icon", "favicon"]
        else:
            self.exclude_patterns = exclude_patterns
            
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
    
    def download_media(self, media_urls):
        """Download media from URLs to the output directory
        
        Args:
            media_urls (set): Set of media URLs to download
            
        Returns:
            list: List of dictionaries containing metadata about downloaded media
        """
        downloaded_media = []
        
        for i, media_url in enumerate(media_urls):
            try:
                # Parse URL to extract filename
                parsed_url = urlparse(media_url)
                filename = os.path.basename(parsed_url.path).split('?')[0]
                
                # Skip if filename contains any exclude pattern
                if any(exclude_pat.lower() in filename.lower() for exclude_pat in self.exclude_patterns):
                    logger.info(f"⏭️ Skipping excluded media: {media_url}")
                    continue
                
                logger.info(f"Downloading ({i+1}/{len(media_urls)}): {media_url}")
                
                response = requests.get(media_url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    # If filename is empty or doesn't have extension, create a default one
                    if not filename or '.' not in filename:
                        # Try to get extension from Content-Type header
                        content_type = response.headers.get('Content-Type', '')
                        ext = content_type.split('/')[-1] if '/' in content_type else 'bin'
                        filename = f"media_{i}.{ext}"
                    
                    # Create unique filename to avoid overwriting
                    file_path = os.path.join(self.output_dir, filename)
                    if os.path.exists(file_path):
                        name, ext = os.path.splitext(filename)
                        file_path = os.path.join(self.output_dir, f"{name}_{i}{ext}")
                    
                    # Save the media
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    
                    # Get file size
                    file_size = os.path.getsize(file_path)
                    
                    # Add metadata to downloaded_media list
                    media_metadata = {
                        "url": media_url,
                        "filename": os.path.basename(file_path),
                        "size_bytes": file_size,
                        "content_type": response.headers.get('Content-Type', ''),
                        "local_path": file_path
                    }
                    downloaded_media.append(media_metadata)
                    
                    logger.info(f"✅ Saved as: {os.path.basename(file_path)}")
                else:
                    logger.error(f"❌ Failed ({response.status_code}): {media_url}")
                    
                # Sleep briefly to avoid rate limiting
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"❌ Error downloading {media_url}: {str(e)}")
        
        return downloaded_media