# Advanced Web Crawler

This advanced web crawler builds upon the functionality of `combined_crawler.py` to implement recursive crawling capabilities. It crawls a starting URL and then recursively crawls all links found on that page, up to a specified maximum depth.

## Features

- **Recursive Crawling**: Automatically crawls links found on each page up to a specified depth
- **Depth Control**: Configurable maximum crawling depth to prevent infinite loops
- **Folder Organization**: Creates a hierarchical folder structure mirroring the crawl path
- **URL Deduplication**: Prevents crawling the same URL multiple times
- **Rate Limiting**: Configurable delay between requests to avoid overwhelming servers
- **Error Handling**: Robust error handling for network issues, malformed URLs, and rate limiting
- **Logging**: Comprehensive logging to track crawling progress and diagnose issues

## Requirements

The script requires the same dependencies as `combined_crawler.py`:

```
selenium
beautifulsoup4
requests
langselect
webdriver-manager
bs4
```

## Usage

### Basic Usage

To start a recursive crawl with default settings (max depth of 2):

```bash
python advanced_crawler.py https://example.com
```

### Advanced Options

```bash
# Set maximum crawling depth to 3
python advanced_crawler.py https://example.com --max-depth=3

# Set delay between requests to 5 seconds
python advanced_crawler.py https://example.com --delay=5

# Run Chrome in headless mode
python advanced_crawler.py https://example.com --headless

# Combine options
python advanced_crawler.py https://example.com --max-depth=3 --delay=5 --headless

# Set logging level
python advanced_crawler.py https://example.com --log-level=DEBUG
```

### Link Deduplication

The script maintains compatibility with the link deduplication functionality from `combined_crawler.py`:

```bash
# Deduplicate links in an existing JSON file
python advanced_crawler.py --dedupe-file input.json --output output.json
```

## Output Structure

The script creates a hierarchical folder structure based on the URLs it crawls:

```
root_url_folder/
├── output_content.json
├── output_links.json
├── link1_folder/
│   ├── output_content.json
│   ├── output_links.json
│   └── sublink1_folder/
│       ├── output_content.json
│       └── output_links.json
└── link2_folder/
    ├── output_content.json
    └── output_links.json
```

Each folder contains:
- `output_content.json`: The extracted text content from the page
- `output_links.json`: All links found on the page

## Logging

The script logs its progress to both the console and a file named `crawler.log`. You can adjust the logging level using the `--log-level` option.