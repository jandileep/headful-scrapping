# Integrated Web Crawler with Image Extraction

This tool combines the functionality of `advanced_crawler.py` and `adv_extract_image.py` to create a comprehensive web scraping system that crawls websites recursively, extracts content, links, and images, and saves them in an organized directory structure.

## Features

- **Recursive Crawling**: Crawls websites recursively up to a specified depth
- **Content Extraction**: Extracts text content from web pages
- **Link Extraction**: Extracts links from web pages
- **Image Extraction**: Extracts images from web pages
- **Organized Output**: Saves results in a structured directory hierarchy
- **Robots.txt Compliance**: Respects robots.txt directives
- **Rate Limiting**: Implements delays between requests to prevent server overload
- **Error Handling**: Robust error handling for network issues and malformed URLs

## Directory Structure

For each crawled URL, the tool creates a directory structure like this:

```
url_slug/
├── output_content.json  # Contains page content and image metadata
├── output_links.json    # Contains links found on the page
└── images/              # Contains downloaded images
    ├── image1.jpg
    ├── image2.png
    └── ...
```

For recursive crawling, subdirectories are created for each linked page:

```
root_url_slug/
├── output_content.json
├── output_links.json
├── images/
│   └── ...
└── linked_page_slug/
    ├── output_content.json
    ├── output_links.json
    └── images/
        └── ...
```

## Usage

### Basic Usage

```bash
python integrated_crawler.py https://example.com
```

### Advanced Options

```bash
# Set maximum crawling depth
python integrated_crawler.py https://example.com --max-depth=3

# Set delay between requests (in seconds)
python integrated_crawler.py https://example.com --delay=5

# Run in non-headless mode (shows browser window)
python integrated_crawler.py https://example.com --headless=False

# Ignore robots.txt
python integrated_crawler.py https://example.com --no-robots

# Set logging level
python integrated_crawler.py https://example.com --log-level=DEBUG
```

### Deduplicating Links in an Existing File

```bash
python integrated_crawler.py --dedupe-file input.json --output output.json
```

## Output Format

### output_content.json

```json
{
  "url": "https://example.com",
  "title": "Example Website",
  "title_text": "Welcome to Example",
  "page_content": "Full text content of the page...",
  "images": [
    {
      "url": "https://example.com/images/image1.jpg",
      "filename": "image1.jpg",
      "size_bytes": 12345,
      "content_type": "image/jpeg",
      "local_path": "example_com/images/image1.jpg"
    },
    ...
  ]
}
```

### output_links.json

```json
{
  "url": "https://example.com",
  "links": [
    {
      "url": "https://example.com/page1",
      "text": "Page 1"
    },
    ...
  ]
}
```

## Requirements

- Python 3.6+
- Selenium
- BeautifulSoup4
- Requests
- Chrome/Chromium browser
- ChromeDriver

## Installation

1. Install required Python packages:

```bash
pip install -r requirements.txt
```

2. Ensure Chrome/Chromium and ChromeDriver are installed:

```bash
# The script uses webdriver_manager to automatically download ChromeDriver
# No manual installation of ChromeDriver is required
```

## Integration Details

This tool integrates the following components:

1. **WebsiteCrawler** from `combined_crawler.py`: Handles basic crawling functionality
2. **ImageExtractor**: Extracts images from web pages using both network logs and HTML parsing
3. **IntegratedCrawler**: Orchestrates the crawling process, including recursive crawling and image extraction

## Error Handling

The tool implements robust error handling for various scenarios:

- Network errors (HTTP errors, timeouts)
- Malformed URLs
- Image download failures
- Robots.txt parsing errors

Errors are logged to both the console and a log file (`integrated_crawler.log`).

## Limitations

- JavaScript-rendered content may not be fully captured
- Some websites may block automated crawling
- Large websites may take a long time to crawl completely
- Image extraction may not work for all types of images (e.g., those loaded via JavaScript)

## License

This project is licensed under the MIT License - see the LICENSE file for details.