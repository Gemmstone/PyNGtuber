import os

def rename_images_to_folder_name(image_folder):
    """Rename PNG images in a folder to folder_name_xxx.png format."""
    folder_name = os.path.basename(image_folder)
    image_count = 0

    for filename in os.listdir(image_folder):
        if filename.lower().endswith(".png"):
            image_count += 1
            new_name = f"{folder_name}_{image_count:03d}.png"
            image_path = os.path.join(image_folder, filename)
            new_path = os.path.join(image_folder, new_name)
            
            os.rename(image_path, new_path)
            print(f"Renamed {filename} to {new_name}")

# Get a list of all folders in the current directory
folders = [f for f in os.listdir() if os.path.isdir(f)]

# Process images in each folder
for folder in folders:
    folder_path = os.path.join(os.getcwd(), folder)
    rename_images_to_folder_name(folder_path)
