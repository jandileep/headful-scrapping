#!/usr/bin/env python3
"""
Duplicate Image Remover

This script traverses a directory structure to find all "image" or "images" directories,
identifies duplicate files across these directories using hash comparison,
and removes duplicates while logging which files were deleted and from where.
"""

import os
import sys
import hashlib
import logging
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Set, Tuple


def setup_logger(log_file: str = None) -> logging.Logger:
    """
    Set up and configure the logger.
    
    Args:
        log_file: Path to the log file. If None, logs to console only.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("DuplicateImageRemover")
    logger.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if log_file is provided
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_file_hash(file_path: str, block_size: int = 65536) -> str:
    """
    Calculate the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file.
        block_size: Size of blocks to read from file.
        
    Returns:
        Hexadecimal digest of the file hash.
    """
    hasher = hashlib.sha256()
    try:
        with open(file_path, 'rb') as file:
            for block in iter(lambda: file.read(block_size), b''):
                hasher.update(block)
        return hasher.hexdigest()
    except (IOError, PermissionError) as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None


def find_image_directories(root_path: str) -> List[str]:
    """
    Find all directories named "image" or "images" within the given root path.
    
    Args:
        root_path: Root directory to start the search from.
        
    Returns:
        List of paths to image directories.
    """
    image_dirs = []
    root_path = os.path.abspath(root_path)
    
    logger.info(f"Searching for image directories in {root_path}")
    
    try:
        for dirpath, dirnames, _ in os.walk(root_path):
            for dirname in dirnames:
                if dirname.lower() in ["image", "images"]:
                    image_dir = os.path.join(dirpath, dirname)
                    image_dirs.append(image_dir)
                    logger.info(f"Found image directory: {image_dir}")
    except (PermissionError, OSError) as e:
        logger.error(f"Error accessing directory {root_path}: {e}")
    
    return image_dirs


def collect_file_hashes(image_dirs: List[str]) -> Tuple[Dict[str, List[str]], int]:
    """
    Collect file hashes from all image directories.
    
    Args:
        image_dirs: List of image directory paths.
        
    Returns:
        Tuple containing:
        - Dictionary mapping file hashes to lists of file paths
        - Total number of files processed
    """
    hash_to_files = defaultdict(list)
    total_files = 0
    
    for image_dir in image_dirs:
        try:
            for file_name in os.listdir(image_dir):
                file_path = os.path.join(image_dir, file_name)
                
                if os.path.isfile(file_path):
                    total_files += 1
                    file_hash = get_file_hash(file_path)
                    
                    if file_hash:
                        hash_to_files[file_hash].append(file_path)
        except (PermissionError, OSError) as e:
            logger.error(f"Error accessing directory {image_dir}: {e}")
    
    return hash_to_files, total_files


def remove_duplicate_files(hash_to_files: Dict[str, List[str]]) -> Tuple[int, int]:
    """
    Remove duplicate files, keeping only one copy of each unique file.
    
    Args:
        hash_to_files: Dictionary mapping file hashes to lists of file paths.
        
    Returns:
        Tuple containing:
        - Number of unique files
        - Number of duplicate files removed
    """
    unique_files = 0
    duplicates_removed = 0
    
    for file_hash, file_paths in hash_to_files.items():
        if len(file_paths) > 1:
            # Keep the first file, remove the rest
            kept_file = file_paths[0]
            unique_files += 1
            
            logger.info(f"Keeping file: {kept_file}")
            
            for duplicate in file_paths[1:]:
                try:
                    os.remove(duplicate)
                    logger.info(f"Removed duplicate: {duplicate}")
                    duplicates_removed += 1
                except (PermissionError, OSError) as e:
                    logger.error(f"Error removing file {duplicate}: {e}")
        else:
            unique_files += 1
    
    return unique_files, duplicates_removed


def main():
    parser = argparse.ArgumentParser(
        description="Find and remove duplicate files across image directories."
    )
    parser.add_argument(
        "root_path", 
        help="Root directory to start the search from"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Identify duplicates without removing them"
    )
    parser.add_argument(
        "--log-file", 
        help="Path to the log file (default: duplicate_remover_YYYY-MM-DD.log)"
    )
    
    args = parser.parse_args()
    
    # Set up log file if not provided
    if not args.log_file:
        date_str = datetime.now().strftime("%Y-%m-%d")
        args.log_file = f"duplicate_remover_{date_str}.log"
    
    # Set up logger
    global logger
    logger = setup_logger(args.log_file)
    
    logger.info("Starting duplicate image file removal process")
    logger.info(f"Root path: {args.root_path}")
    logger.info(f"Dry run: {args.dry_run}")
    
    # Find image directories
    image_dirs = find_image_directories(args.root_path)
    logger.info(f"Found {len(image_dirs)} image directories")
    
    if not image_dirs:
        logger.warning("No image directories found. Exiting.")
        return
    
    # Collect file hashes
    hash_to_files, total_files = collect_file_hashes(image_dirs)
    logger.info(f"Processed {total_files} files")
    
    # Count duplicates
    duplicate_count = sum(len(files) - 1 for files in hash_to_files.values() if len(files) > 1)
    logger.info(f"Found {duplicate_count} duplicate files")
    
    # Remove duplicates if not in dry run mode
    if not args.dry_run:
        unique_files, removed_count = remove_duplicate_files(hash_to_files)
        logger.info(f"Kept {unique_files} unique files")
        logger.info(f"Removed {removed_count} duplicate files")
    else:
        logger.info("Dry run mode - no files were removed")
        for file_hash, file_paths in hash_to_files.items():
            if len(file_paths) > 1:
                logger.info(f"Would keep: {file_paths[0]}")
                for duplicate in file_paths[1:]:
                    logger.info(f"Would remove: {duplicate}")
    
    logger.info("Duplicate image removal process completed")


if __name__ == "__main__":
    main()