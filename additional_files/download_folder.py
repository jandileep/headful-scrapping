import os
import shutil

def copy_first_10_folders(source_paths, dest_root="sample_folder"):
    os.makedirs(dest_root, exist_ok=True)

    for rel_path in source_paths:
        abs_path = os.path.abspath(rel_path)
        if not os.path.isdir(abs_path):
            print(f"Skipping invalid directory: {rel_path}")
            continue

        folder_name = os.path.basename(os.path.normpath(rel_path))
        dest_path = os.path.join(dest_root, folder_name)
        os.makedirs(dest_path, exist_ok=True)

        subdirs = [d for d in os.listdir(abs_path) if os.path.isdir(os.path.join(abs_path, d))]
        subdirs.sort()  # sort to ensure consistent first 10
        for subdir in subdirs[:10]:
            src = os.path.join(abs_path, subdir)
            dst = os.path.join(dest_path, subdir)
            shutil.copytree(src, dst)
            print(f"Copied: {src} -> {dst}")

# Example usage:
relative_paths = ["Musical_Instruments_of_India/GHAN_VADYA" ,"Stories"]
copy_first_10_folders(relative_paths)
