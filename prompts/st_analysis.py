import streamlit as st
import json
import os
from PIL import Image # For robust image opening

# --- Helper Function to Load Data ---
def load_data(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error(f"Error: JSON file not found at {json_path}")
        return None
    except json.JSONDecodeError:
        st.error(f"Error: Could not decode JSON from {json_path}. Please ensure it's a valid JSON file.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred while loading the JSON file: {e}")
        return None

# --- Helper Function to Display Gemini Response ---
def display_gemini_response(response_data):
    if isinstance(response_data, list): # It's the structured list of questions
        for question_block in response_data:
            task_label = question_block.get("task", "Question Block")
            q_type = question_block.get("type", "Unknown")
            q_text = question_block.get("question_text", "N/A")
            answer = question_block.get("answer", "N/A")
            options = question_block.get("options", {})

            st.subheader(f"{task_label} - {q_type}")
            st.markdown(f"**Question:** {q_text}")

            if q_type == "MCQ":
                st.markdown("**Options:**")
                # Ensure options are sorted if keys are A, B, C, D for consistent display
                sorted_options = sorted(options.items()) if isinstance(options, dict) else []
                for letter, option_text in sorted_options:
                    st.markdown(f"{letter}) {option_text}")
                
                # Display the correct answer text for MCQs
                correct_option_text = options.get(answer, "N/A") # 'answer' here is the letter
                st.markdown(f"**Correct Answer:** {answer}) {correct_option_text}")
            else: # Subjective
                st.markdown(f"**Answer:** {answer}")
            st.markdown("---")
    elif isinstance(response_data, str): # It's a raw string
        st.markdown("#### Gemini Response (Raw Text):")
        st.markdown(response_data) # st.markdown can render markdown-like text nicely
    else:
        st.warning("Gemini response format not recognized.")

# --- Main Streamlit App ---
st.set_page_config(layout="wide")
st.title("🎨 Indian Culture: Image & Gemini Q&A Viewer")

# --- Inputs for Paths ---
st.sidebar.header("Configuration")
json_file_path_input = st.sidebar.text_input(
    "Enter the path to your JSON results file:",
    "gemini_culture_questions.json" # Default value
)
base_image_path_input = st.sidebar.text_input(
    "Enter the base path for your images (e.g., /root/headful-scrapping/):",
    "/root/headful-scrapping/" # Default value
)

# THIS IS THE FIXED SUBDIRECTORY PATH YOU PROVIDED
FIXED_IMAGE_SUBPATH = "Food_and_Culture/Cuisines_of_India/Central/The_Food_of_Maharashtra/images/"

if json_file_path_input and base_image_path_input:
    if not os.path.exists(json_file_path_input):
        st.sidebar.warning(f"JSON file not found at the specified path: {json_file_path_input}")
    if not os.path.isdir(base_image_path_input):
        st.sidebar.warning(f"Base image path is not a valid directory: {base_image_path_input}")

    data = load_data(json_file_path_input)

    if data:
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            st.error("JSON data is not in the expected list of dictionaries format.")
        else:
            image_names_from_json = [item.get("image_name", f"Entry {i+1}") for i, item in enumerate(data)]
            if not image_names_from_json:
                st.warning("No image entries found in the JSON data.")
            else:
                st.sidebar.markdown("---")
                selected_image_name_from_json = st.sidebar.selectbox(
                    "Select an Image Entry:",
                    options=image_names_from_json
                )

                selected_item = None
                for item in data:
                    if item.get("image_name") == selected_image_name_from_json:
                        selected_item = item
                        break
                
                if selected_item:
                    st.header(f"Displaying: {selected_item.get('image_name', 'N/A')}")

                    col1, col2 = st.columns([1, 2]) 

                    with col1:
                        # Display Image
                        image_filename = selected_item.get("image_name")
                        
                        if image_filename:
                            # Construct the full path using base_path, fixed_subpath, and the image_filename
                            full_image_display_path = os.path.join(
                                base_image_path_input,
                                FIXED_IMAGE_SUBPATH,
                                image_filename
                            )

                            if os.path.exists(full_image_display_path):
                                try:
                                    image = Image.open(full_image_display_path)
                                    st.image(image, caption=f"Image: {image_filename}", use_container_width=True)
                                except Exception as img_e:
                                    st.error(f"Could not load image: {img_e}")
                            else:
                                st.warning(f"Image not found at expected path: {full_image_display_path}")
                                st.info(f"Checked path: {full_image_display_path}")
                        else:
                            st.info("No image name specified in this entry.")

                    with col2:
                        # Display Original Caption
                        original_caption = selected_item.get("original_caption", "No caption provided.")
                        st.markdown(f"**Original Caption:**")
                        st.caption(original_caption)
                        st.markdown("---")

                        # Display Gemini Response
                        gemini_response = selected_item.get("gemini_response")
                        if gemini_response is not None:
                            display_gemini_response(gemini_response)
                        else:
                            st.info("No Gemini response found for this entry.")
                else:
                    st.info("Select an image entry from the sidebar to view details.")
    else:
        st.info("Please provide valid paths in the sidebar to load data.")

else:
    st.info("👈 Enter the JSON file path and base image path in the sidebar to get started.")