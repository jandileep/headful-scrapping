import os
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Setup
options = Options()
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
driver = webdriver.Chrome(options=options)

# Target page
url = "https://indianculture.gov.in/food-and-culture/cuisines-of-India"
driver.get(url)
driver.implicitly_wait(10)

# Get network logs
logs = driver.get_log("performance")

# Collect inline image URLs
inline_images = []
for entry in logs:
    try:
        message = json.loads(entry["message"])["message"]
        if message["method"] == "Network.responseReceived":
            image_url = message["params"]["response"]["url"]
            if "sites/default/files/inline-images" in image_url:
                inline_images.append(image_url)
    except Exception:
        continue

driver.quit()

# Create output folder
output_dir = "downloaded_inline_images"
os.makedirs(output_dir, exist_ok=True)

# Headers to bypass 403
headers = {
    "Referer": url,
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
}

# Download images
for i, img_url in enumerate(inline_images):
    try:
        response = requests.get(img_url, headers=headers)
        if response.status_code == 200:
            ext = img_url.split(".")[-1].split("?")[0]  # Get file extension
            file_path = os.path.join(output_dir, f"image_{i}.{ext}")
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"✅ Downloaded: {img_url}")
        else:
            print(f"❌ Failed ({response.status_code}): {img_url}")
    except Exception as e:
        print(f"❌ Error downloading {img_url}: {e}")