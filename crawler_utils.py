#!/usr/bin/env python3
"""
Utility functions for the Selenium Web Crawler.
This script provides helper functions for managing crawler output and generating reports.
"""

import os
import shutil
import json
import csv
import argparse
from datetime import datetime
from collections import defaultdict

def clear_output_directory(output_dir):
    """
    Clear the output directory by removing all its contents.
    
    Args:
        output_dir (str): Path to the output directory
    """
    if os.path.exists(output_dir):
        print(f"Clearing output directory: {output_dir}")
        shutil.rmtree(output_dir)
        os.makedirs(output_dir)
        print("Output directory cleared and recreated.")
    else:
        print(f"Output directory '{output_dir}' does not exist. Creating it...")
        os.makedirs(output_dir)
        print("Output directory created.")

def generate_crawl_summary(output_dir):
    """
    Generate a summary of the crawled data.
    
    Args:
        output_dir (str): Path to the output directory
    
    Returns:
        dict: Summary statistics
    """
    if not os.path.exists(output_dir):
        print(f"Error: Output directory '{output_dir}' does not exist.")
        return None
    
    summary = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_pages': 0,
        'total_images': 0,
        'total_videos': 0,
        'domains': defaultdict(lambda: {'pages': 0, 'images': 0, 'videos': 0})
    }
    
    # Walk through the output directory
    for root, dirs, files in os.walk(output_dir):
        # Skip the root directory itself
        if root == output_dir:
            continue
        
        # Determine the domain from the path
        path_parts = os.path.relpath(root, output_dir).split(os.sep)
        if len(path_parts) > 0:
            domain = path_parts[0]
            
            # Count text files (pages)
            if "data" in root:
                for file in files:
                    if file.endswith(".txt"):
                        summary['total_pages'] += 1
                        summary['domains'][domain]['pages'] += 1
            
            # Count image files
            if "images" in root:
                for file in files:
                    if file.endswith((".png", ".jpg", ".jpeg", ".gif")):
                        summary['total_images'] += 1
                        summary['domains'][domain]['images'] += 1
            
            # Count video links
            if "videos" in root:
                for file in files:
                    if file == "video_links.txt":
                        # Count the number of lines in the file (excluding header lines)
                        try:
                            with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                                # Count non-empty lines after the first two (header) lines
                                video_count = sum(1 for line in lines[2:] if line.strip())
                                summary['total_videos'] += video_count
                                summary['domains'][domain]['videos'] += video_count
                        except Exception as e:
                            print(f"Error reading video links file: {e}")
    
    return summary

def save_summary_report(summary, output_dir):
    """
    Save the crawl summary to JSON and CSV files.
    
    Args:
        summary (dict): Crawl summary data
        output_dir (str): Path to the output directory
    """
    if summary is None:
        return
    
    # Create reports directory
    reports_dir = os.path.join(output_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save JSON report
    json_path = os.path.join(reports_dir, f"crawl_summary_{timestamp}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        # Convert defaultdict to regular dict for JSON serialization
        summary_dict = {
            'timestamp': summary['timestamp'],
            'total_pages': summary['total_pages'],
            'total_images': summary['total_images'],
            'total_videos': summary['total_videos'],
            'domains': {k: dict(v) for k, v in summary['domains'].items()}
        }
        json.dump(summary_dict, f, indent=2)
    
    print(f"JSON summary saved to: {json_path}")
    
    # Save CSV report
    csv_path = os.path.join(reports_dir, f"crawl_summary_{timestamp}.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Domain', 'Pages', 'Images', 'Videos'])
        
        for domain, stats in summary['domains'].items():
            writer.writerow([domain, stats['pages'], stats['images'], stats['videos']])
        
        # Add totals row
        writer.writerow(['TOTAL', summary['total_pages'], summary['total_images'], summary['total_videos']])
    
    print(f"CSV summary saved to: {csv_path}")
    
    # Print summary to console
    print("\nCrawl Summary:")
    print(f"Total Pages: {summary['total_pages']}")
    print(f"Total Images: {summary['total_images']}")
    print(f"Total Videos: {summary['total_videos']}")
    print(f"Domains Crawled: {len(summary['domains'])}")

def list_failed_urls(output_dir):
    """
    List all failed URLs from the failed_urls.txt file.
    
    Args:
        output_dir (str): Path to the output directory
    """
    failed_urls_path = os.path.join(output_dir, "failed_urls.txt")
    
    if not os.path.exists(failed_urls_path):
        print("No failed URLs file found.")
        return
    
    print("\nFailed URLs:")
    try:
        with open(failed_urls_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) <= 2:  # Just the header or empty
                print("No failed URLs recorded.")
                return
            
            for line in lines[2:]:  # Skip header lines
                print(line.strip())
    except Exception as e:
        print(f"Error reading failed URLs file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web Crawler Utilities")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Clear output directory command
    clear_parser = subparsers.add_parser("clear", help="Clear the output directory")
    clear_parser.add_argument("--output", default="crawled_data", help="Output directory path")
    
    # Generate summary command
    summary_parser = subparsers.add_parser("summary", help="Generate a summary of crawled data")
    summary_parser.add_argument("--output", default="crawled_data", help="Output directory path")
    
    # List failed URLs command
    failed_parser = subparsers.add_parser("failed", help="List failed URLs")
    failed_parser.add_argument("--output", default="crawled_data", help="Output directory path")
    
    args = parser.parse_args()
    
    if args.command == "clear":
        clear_output_directory(args.output)
    elif args.command == "summary":
        summary = generate_crawl_summary(args.output)
        if summary:
            save_summary_report(summary, args.output)
    elif args.command == "failed":
        list_failed_urls(args.output)
    else:
        parser.print_help()