#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# crawl_indian_culture.sh — PARALLEL EDITION (32 logical CPUs)
# -----------------------------------------------------------------------------
# ▸ Crawls all required Indian Culture collections with up to 32 concurrent
#   python processes.
# ▸ Combined from: freedom_Archive.sh, images.sh, manuscripts.sh,
#   other_collection.sh, paintings.sh (16 Jun 2025).
# ▸ Each URL is passed to integrated_crawler_html.py with --headless.
# ▸ Requires Bash 5+ (for wait -n) and Python available on PATH.
# -----------------------------------------------------------------------------
set -euo pipefail

SCRIPT="integrated_crawler_html.py"
MAX_JOBS=32             # adjust if you have fewer logical cores

# -----------------------------------------------------------------------------
# Helper: run one crawl in the background while limiting concurrency
# -----------------------------------------------------------------------------
run() {
  local url="$1"
  python "$SCRIPT" "$url" --headless &
  pids+=("$!")
  # Once we have MAX_JOBS running, wait for one to finish (wait -n ⇒ Bash 5)
  if (( ${#pids[@]} >= MAX_JOBS )); then
    wait -n
    # Clean the list to keep only still‑running jobs
    pids=( $(jobs -pr) )
  fi
}

pids=()

# -----------------------------------------------------------------------------
# 1) Museum paintings (0‑1129) – 1 130 pages
# -----------------------------------------------------------------------------
for page in $(seq 0 1129); do
  run "https://indianculture.gov.in/painting-collections/museum-paintings?page=${page}"
done

# -----------------------------------------------------------------------------
# 2) Site‑wide images (0‑6199) – 6 200 pages
# -----------------------------------------------------------------------------
for page in $(seq 0 6199); do
  run "https://indianculture.gov.in/images?search_api_fulltext=&page=${page}"
done

# -----------------------------------------------------------------------------
# 3) Manuscripts (0‑8748) – 8 749 pages
# -----------------------------------------------------------------------------
for page in $(seq 0 8748); do
  run "https://indianculture.gov.in/manuscripts?search_api_fulltext=&page=${page}"
done

# -----------------------------------------------------------------------------
# 4) Other collections (0‑46) – 47 pages
# -----------------------------------------------------------------------------
for page in $(seq 0 46); do
  run "https://indianculture.gov.in/other-collections?search_api_fulltext=&page=${page}"
done

# -----------------------------------------------------------------------------
# 5) Freedom‑archive miscellany – 11 single URLs / short ranges
# -----------------------------------------------------------------------------
run "https://indianculture.gov.in/freedom-archive/images"                    # no pagination
for page in $(seq 0 1); do                                                    # museum collections
  run "https://indianculture.gov.in/freedom-archive/museum-collections?page=${page}"
done
run "https://indianculture.gov.in/freedom-archive/newspaper-clippings"       # no pagination
for page in $(seq 0 4); do                                                    # unsung heroes
  run "https://indianculture.gov.in/unsung-heroes?page=${page}"
done
run "https://indianculture.gov.in/Historic_Cities_Freedom_Movement"          # single page
run "https://indianculture.gov.in/node/2790124"                               # single node

# -----------------------------------------------------------------------------
# 6) Wait for all background jobs to finish
# -----------------------------------------------------------------------------
wait

echo "[✓] All crawls complete (parallel mode)."
