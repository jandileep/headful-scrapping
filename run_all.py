import os
import sys
import subprocess

def run_for_subfolders(base_path):
    # Resolve relative path
    base_path = os.path.abspath(base_path)

    if not os.path.isdir(base_path):
        print(f"Error: '{base_path}' is not a valid directory.")
        return

    # Iterate over items in the base directory
    for item in os.listdir(base_path):
        subfolder_path = os.path.join(base_path, item)
        if os.path.isdir(subfolder_path):
            print(f"Running for subfolder: {item}")
            # Run the command: python main.py <subfolder> --headless
            subprocess.run(['python', 'image_integ_crawler_html.py', item, '--headless'])

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_for_all.py <relative_folder_path>")
    else:
        run_for_subfolders(sys.argv[1])
