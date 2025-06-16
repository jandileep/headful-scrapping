set -euo pipefail

# 1) Painting collections (0–1129)
for page in $(seq 0 46); do
  python integrated_crawler_html.py "https://indianculture.gov.in/other-collections?search_api_fulltext=&page=${page}" --headless

done