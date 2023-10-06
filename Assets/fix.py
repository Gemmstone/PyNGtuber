import os
from PIL import Image

def is_empty_middle_column(image, threshold=128, min_non_transparent=5):
    # Get the dimensions of the image
    width, height = image.size

    # Define the middle column
    middle_column_x = width // 2

    # Count the number of non-transparent pixels in the middle column
    non_transparent_count = 0

    for y in range(height):
        pixel = image.getpixel((middle_column_x, y))
        if pixel[3] > threshold:  # Check alpha channel (adjust threshold as needed)
            non_transparent_count += 1

        if non_transparent_count >= min_non_transparent:
            return False  # Middle column is not empty

    return True  # Middle column is empty

def split_and_save_wings(image_path):
    # Open the image using Pillow
    image = Image.open(image_path)

    if is_empty_middle_column(image, threshold=128, min_non_transparent=5):
        # Split the image into two wings
        width, height = image.size
        middle_column_x = width // 2
        left_wing = image.crop((0, 0, middle_column_x, height))
        right_wing = image.crop((middle_column_x, 0, width, height))

        # Create blank transparent canvases for missing width
        canvas_width = 600
        canvas_height = 600

        if left_wing.size[0] < canvas_width:
            # Add 300px blank transparent canvas to the right for left wing
            left_wing = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
            left_wing.paste(image.crop((0, 0, middle_column_x, height)), (0, 0))

        if right_wing.size[0] < canvas_width:
            # Add 300px blank transparent canvas to the left for right wing
            right_wing = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
            right_wing.paste(image.crop((middle_column_x, 0, width, height)), (300, 0))

        # Save the wing images with unique names
        identifier = os.path.splitext(os.path.basename(image_path))[0]
        left_wing_path = os.path.join(os.path.dirname(image_path), f"{identifier}_left_wing.png")
        right_wing_path = os.path.join(os.path.dirname(image_path), f"{identifier}_right_wing.png")

        left_wing.save(left_wing_path)
        right_wing.save(right_wing_path)

        # Delete the original image
        os.remove(image_path)
    else:
        # Image doesn't have an empty middle column, do something else
        print(f"The image in {image_path} doesn't have an empty middle column.")

# Get a list of all folders in the current directory
folders = [f for f in os.listdir() if os.path.isdir(f)]

# Process images in each folder
for folder in folders:
    folder_path = os.path.join(os.getcwd(), folder)
    for filename in os.listdir(folder_path):
        if filename.endswith(".PNG"):
            image_path = os.path.join(folder_path, filename)
            split_and_save_wings(image_path)
