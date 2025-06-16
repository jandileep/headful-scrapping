#!/bin/bash


echo "🎨 Crawling the main museum collections page..."
python ../integrated_crawler_html.py "https://indianculture.gov.in/artefacts-museums" --headless
echo "✅ Finished crawling the museum collections overview page."


TARGET_DIR="artefacts-museums"
mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR" || { echo "❌ Failed to enter $TARGET_DIR. Exiting."; exit 1; }

# echo "📁 Entered target directory: $TARGET_DIR"


# echo "🖼️ Starting crawl of museum paintings pages (0 to 1130)..."
for i in {0..4531}; do

    echo "➡️ Crawling museum collection - Page $i"
    python ../integrated_crawler_html.py "https://indianculture.gov.in/artefacts-museums?search_api_fulltext=&page=$i" --headless
done
# echo "✅ Completed crawling all museum paintings pages."



