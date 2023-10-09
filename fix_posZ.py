import json
# Define the folder you want to update
folder_to_update = "right eye"
new_posZ_value = "blinking_open"  # Set the new posZ value here

# Load the JSON data from your file
with open('Data/parameters.json', 'r') as json_file:
    data = json.load(json_file)

# Construct the target folder path
target_folder_path = f"Assets/{folder_to_update}/"

# Iterate through the JSON and update posZ for items within the target folder
for key, value in data.items():
    if target_folder_path in key:
        value['blinking'] = new_posZ_value

# Save the updated JSON back to the file
with open('Data/parameters.json', 'w') as json_file:
    json.dump(data, json_file, indent=4)

print(f"posZ values updated successfully for items within /Assets/{folder_to_update}/ folder.")

"""

# Read the JSON file
with open('parameters.json', 'r') as file:
    data = json.load(file)

for key in data:
    data[key]["use_css"] = False

# Save the modified data back to the JSON file
with open('parameters.json', 'w') as file:
    json.dump(data, file, indent=4)

print("Keys have been modified and saved to parameters.json.")
"""