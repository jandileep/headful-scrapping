# Project File Overview

## [`crawler_html.py`](crawler_html.py)

- Implements the `HtmlCrawler` class for recursive web crawling and structured HTML content extraction.
- Handles:
  - Recursive crawling up to a specified depth.
  - Respecting `robots.txt` (configurable).
  - Saving results in organized folders.
  - Delegates content extraction to [`HtmlContentExtractor`](html_content_extractor.py).
- Entry point for HTML-focused crawling, used by scripts like `integrated_crawler_html.py`.

## [`html_content_extractor.py`](html_content_extractor.py)

- Provides the `HtmlContentExtractor` class for extracting structured content from HTML pages.
- Key features:
  - Extracts paragraphs, headers, and images with metadata (alt, title, caption, associated paragraph).
  - Downloads images and saves them locally.
  - Advanced caption extraction using figcaption, aria-label, data-caption, and more.
- Used by [`HtmlCrawler`](crawler_html.py) for content extraction.

## [`combined_crawler.py`](combined_crawler.py)

- Contains the `WebsiteCrawler` class and utility functions for basic crawling and link extraction.
- Features:
  - Deduplication of links (`dedupe_links`).
  - Extraction of text, links, and page content.
  - Used as a base for more advanced crawlers.
- Provides command-line interface for crawling or deduplication.

## `image_integ_crawler.py`

- (File present in workspace, but no code excerpt provided.)
- Presumably integrates image extraction with crawling, possibly combining logic from [`crawler_html.py`](crawler_html.py) and [`html_content_extractor.py`](html_content_extractor.py).
- For details, see the file directly: `image_integ_crawler.py`.

---

**Relationships:**
- [`crawler_html.py`](crawler_html.py) uses [`HtmlContentExtractor`](html_content_extractor.py) for content extraction.
- [`combined_crawler.py`](combined_crawler.py) provides foundational crawling and deduplication utilities.
- `image_integ_crawler.py` likely builds on these modules for integrated image crawling.

For more details, see the respective files:
- [`crawler_html.py`](crawler_html.py)
- [`html_content_extractor.py`](html_content_extractor.py)
- [`combined_crawler.py`](combined_crawler.py)
- `image_integ_crawler.py`