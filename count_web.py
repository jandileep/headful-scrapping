import os
import sys

def count_files_recursive(folder_path):
    file_count = 0
    for root, dirs, files in os.walk(folder_path):
        # Skip 'images' folders entirely
        dirs[:] = [d for d in dirs if d.lower() != 'images']
        file_count += len(files)
    return file_count

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python count_files_recursive.py <folder_path>")
    else:
        folder_path = sys.argv[1]
        total_files = count_files_recursive(folder_path)
        print(f"Total number of files (excluding inside 'images' folders): {total_files}")
