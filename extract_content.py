import json
from bs4 import BeautifulSoup

def extract_content_from_html(html_file):
    # Read the HTML content from the file
    with open(html_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Parse the HTML content
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find the main content area (storyarea div)
    story_area = soup.find('div', id='storyarea')
    
    if not story_area:
        return {"error": "Could not find the main content area"}
    
    # Initialize the result structure
    result = []
    
    # First, extract the title
    title_div = story_area.find('div', class_='pt-6')
    title = title_div.find('h1').get_text(strip=True) if title_div and title_div.find('h1') else "No Title"
    
    # Create a content map to organize sections
    content_sections = []
    
    # Get all content sections (both text and images)
    for child in story_area.find_all(recursive=False):
        # Skip the title div
        if 'pt-6' in child.get('class', []):
            continue
            
        # Add to our content sections
        content_sections.append(child)
    
    # Process content sections to extract paragraphs and images
    current_paragraph = None
    
    for section in content_sections:
        # Check if it's a text section
        if 'storytxt' in section.get('class', []):
            # Extract paragraphs and headers
            for element in section.find_all(['p', 'h3']):
                if element.name == 'h3':
                    # Create a new entry for the header
                    header_text = element.get_text(strip=True)
                    if header_text:
                        current_paragraph = {
                            "paragraph": f"## {header_text}",  # Mark headers with ##
                            "images": []
                        }
                        result.append(current_paragraph)
                else:  # It's a paragraph
                    paragraph_text = element.get_text(strip=True)
                    if paragraph_text:
                        current_paragraph = {
                            "paragraph": paragraph_text,
                            "images": []
                        }
                        result.append(current_paragraph)
        
        # Check if it contains an image
        elif section.find(class_='storyimg'):
            # Find all image containers in this section
            img_containers = section.find_all(class_='storyimg')
            
            for img_container in img_containers:
                img = img_container.find('img')
                caption_div = img_container.find(class_='storycaption')
                
                if img:
                    image_info = {
                        "image_url": img.get('src', ''),
                        "alt_text": img.get('alt', ''),
                        "caption": caption_div.get_text(strip=True) if caption_div else ""
                    }
                    
                    # If there's a current paragraph, add the image to it
                    if current_paragraph:
                        current_paragraph["images"].append(image_info)
                    else:
                        # If no paragraph exists yet, create a new entry with just the image
                        current_paragraph = {
                            "paragraph": "",
                            "images": [image_info]
                        }
                        result.append(current_paragraph)
    
    # Add the title as metadata
    metadata = {
        "title": title,
        "content": result
    }
    
    return result

def main():
    html_file = 'html_content.txt'
    extracted_content = extract_content_from_html(html_file)
    
    # Output the result as JSON
    json_output = json.dumps(extracted_content, indent=2, ensure_ascii=False)
    
    # Save to a file
    with open('extracted_content.json', 'w', encoding='utf-8') as f:
        f.write(json_output)
    
    print(f"Extraction complete! Content saved to 'extracted_content.json'")
    print(f"Found {len(extracted_content['content'])} content sections with {sum(len(item['images']) for item in extracted_content['content'])} images")

if __name__ == "__main__":
    main()