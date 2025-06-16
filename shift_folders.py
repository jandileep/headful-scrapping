import os
import shutil

def move_folders_from_list(folder_paths, destination_folder):
    os.makedirs(destination_folder, exist_ok=True)

    for rel_path in folder_paths:
        abs_path = os.path.abspath(rel_path)
        if not os.path.isdir(abs_path):
            print(f"Skipping: {rel_path} (not a valid directory)")
            continue

        folder_name = os.path.basename(abs_path.rstrip("/"))
        dest_path = os.path.join(destination_folder, folder_name)

        print(f"Moving {rel_path} → {dest_path}")
        shutil.move(abs_path, dest_path)

    print(f"\n✅ All valid folders moved to '{destination_folder}'")


# Example usage
if __name__ == "__main__":
    folders_to_move = [
        "Food_and_Culture",
        "Forts_of_India",
        "Musical_Instruments_of_India",
        "Stories",
        "Intangible_Cultural_Heritage"
    ]
    destination = "Indian_Culture_Website"

    move_folders_from_list(folders_to_move, destination)
