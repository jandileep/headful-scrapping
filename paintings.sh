set -euo pipefail

# 1) Painting collections (0–1129)
for page in $(seq 0 1129); do
  python integrated_crawler_html.py "https://indianculture.gov.in/painting-collections/museum-paintings?page=${page}" --headless
done