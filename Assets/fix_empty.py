import os
from PIL import Image

def is_empty(image, threshold=128, min_non_transparent=5):
    # Get the dimensions of the image
    width, height = image.size

    # Check if the image is completely empty
    empty = True

    for x in range(width):
        for y in range(height):
            pixel = image.getpixel((x, y))
            if pixel[3] > threshold:  # Check alpha channel (adjust threshold as needed)
                empty = False
                break

    return empty

def delete_empty_images(folder_path):
    # Get a list of all image files in the folder
    image_files = [f for f in os.listdir(folder_path) if f.endswith(".png")]

    # Check each image file for emptiness and delete if empty
    for image_file in image_files:
        print(image_file)
        image_path = os.path.join(folder_path, image_file)
        image = Image.open(image_path)
        if is_empty(image, threshold=128, min_non_transparent=5):
            os.remove(image_path)
            print(f"Deleted empty image: {image_path}")

# Get a list of all folders in the current directory
folders = [f for f in os.listdir() if os.path.isdir(f)]

# Process images in each folder and delete empty ones
for folder in folders:
    folder_path = os.path.join(os.getcwd(), folder)
    delete_empty_images(folder_path)
