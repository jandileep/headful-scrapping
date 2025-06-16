#!/usr/bin/env bash
set -euo pipefail


# 2) Freedom archive – images (no pagination)
python integrated_crawler_html.py "https://indianculture.gov.in/freedom-archive/images" --headless

# 3) Freedom archive – museum collections (0–1)
for page in $(seq 0 1); do
  python integrated_crawler_html.py "https://indianculture.gov.in/freedom-archive/museum-collections?page=${page}" --headless
done

# 4) Freedom archive – newspaper clippings (no pagination)
python integrated_crawler_html.py "https://indianculture.gov.in/freedom-archive/newspaper-clippings" --headless

# 5) Unsung heroes (0–4)
for page in $(seq 0 4); do
  python integrated_crawler_html.py "https://indianculture.gov.in/unsung-heroes?page=${page}" --headless
done

# 6) Historic Cities Freedom Movement (no pagination)
python integrated_crawler_html.py "https://indianculture.gov.in/Historic_Cities_Freedom_Movement" --headless

# 7) Single node
python integrated_crawler_html.py "https://indianculture.gov.in/node/2790124" --headless
