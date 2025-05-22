# Integrated HTML Crawler

A powerful web crawling tool that extracts structured HTML content with enhanced caption extraction capabilities.

## Overview

The Integrated HTML Crawler combines web crawling with advanced HTML content extraction to create a comprehensive system for extracting structured content from websites. It recursively crawls websites, extracts paragraphs, headers, and images with their associated metadata, and saves everything in an organized directory structure.

## Features

- **Recursive Web Crawling**: Crawls websites up to a specified depth
- **Structured Content Extraction**: Extracts paragraphs and headers with proper formatting
- **Enhanced Image Extraction**: Captures images with comprehensive metadata
- **Advanced Caption Detection**: Intelligently extracts captions from multiple sources:
  - `<figcaption>` elements
  - `<div class="storycaption">` elements
  - Elements with caption-related classes
  - `aria-label` and `data-caption` attributes
  - Falls back to alt text or title when no explicit caption is found
- **Paragraph Association**: Links each image with its contextual paragraph
- **Robots.txt Compliance**: Respects website crawling policies
- **Rate Limiting**: Implements configurable delays between requests

## Installation

### Prerequisites

- Python 3.6+
- Chrome/Chromium browser
- ChromeDriver (automatically installed via webdriver_manager)

### Setup

1. Install required Python packages:

```bash
pip install selenium beautifulsoup4 requests webdriver_manager
```

2. Ensure all module files are in the same directory:
   - `integrated_crawler_html.py` (main entry point)
   - `crawler_html.py` (crawler implementation)
   - `html_content_extractor.py` (content extraction)
   - `combined_crawler.py` (base crawler functionality)

## Usage

### Basic Usage

```bash
python integrated_crawler_html.py https://example.com
```

### Command-Line Options

```bash
# Set maximum crawling depth (default: 2)
python integrated_crawler_html.py https://example.com --max-depth=3

# Set delay between requests in seconds (default: 3)
python integrated_crawler_html.py https://example.com --delay=5

# Run in headless mode (no browser window)
python integrated_crawler_html.py https://example.com --headless

# Ignore robots.txt restrictions
python integrated_crawler_html.py https://example.com --no-robots

# Set logging level
python integrated_crawler_html.py https://example.com --log-level=DEBUG
```

### Deduplicating Links

```bash
python integrated_crawler_html.py --dedupe-file input_links.json --output output_links.json
```

## Output Structure

For each crawled URL, the tool creates a directory structure like this:

```
url_slug/
├── output_content.json  # Contains structured content with paragraphs and image metadata
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

## Output Format

### output_content.json

```json
{
  "url": "https://example.com",
  "title": "Example Website",
  "content_type": "html",
  "paragraphs": [
    "# Main Heading",
    "This is the first paragraph of content.",
    "## Subheading",
    "This is another paragraph with more detailed information."
  ],
  "images": [
    {
      "url": "https://example.com/images/image1.jpg",
      "local_path": "example_com/images/image1.jpg",
      "alt_text": "Description of image",
      "title": "Image title",
      "caption": "Image caption text (intelligently extracted)",
      "content_type": "image/jpeg",
      "paragraph": "This is the paragraph content associated with this image"
    }
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
    }
  ]
}
```

## Architecture

The Integrated HTML Crawler is built with a modular architecture:

1. **integrated_crawler_html.py**: Main entry point that parses command-line arguments and runs the crawler
2. **crawler_html.py**: Contains the `HtmlCrawler` class that handles recursive crawling
3. **html_content_extractor.py**: Contains the `HtmlContentExtractor` class for extracting structured content
4. **combined_crawler.py**: Contains the `WebsiteCrawler` class and utility functions

### Component Interaction

```
integrated_crawler_html.py
        │
        ▼
    crawler_html.py
        │
        ├─────────────────┐
        │                 │
        ▼                 ▼
html_content_extractor.py  combined_crawler.py
```

## Logging

The crawler logs information to both the console and a log file (`integrated_crawler_html.log`). You can set the logging level using the `--log-level` command-line option.

## Use Cases

- **Content Analysis**: Extract structured content for analysis
- **Data Mining**: Gather information from websites for research
- **Content Migration**: Extract content from one site to move to another
- **SEO Analysis**: Extract and analyze content and links
- **Image Collection**: Gather images with their contextual information

## Limitations

- JavaScript-rendered content may not be fully captured
- Some websites may block automated crawling
- Large websites may take a long time to crawl completely
- Content extraction may not work perfectly for all website layouts

## Examples

### Basic Crawling

```bash
python integrated_crawler_html.py https://example.com
```

### Crawling a News Website

```bash
python integrated_crawler_html.py https://news-site.com --max-depth=1 --delay=5
```

### Crawling a Blog

```bash
python integrated_crawler_html.py https://blog.example.com/articles --headless
```

## Troubleshooting

- **Blocked by Website**: Try increasing the delay between requests with `--delay`
- **Missing Content**: Some websites load content dynamically with JavaScript, which may not be fully captured
- **Errors**: Check the log file (`integrated_crawler_html.log`) for detailed error messages

## License

This project is licensed under the MIT License.