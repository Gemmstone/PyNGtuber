import json

"""# Define the folder you want to update
folder_to_update = "mouth"
new_posZ_value = 16  # Set the new posZ value here

# Load the JSON data from your file
with open('parameters.json', 'r') as json_file:
    data = json.load(json_file)

# Construct the target folder path
target_folder_path = f"/../Assets/{folder_to_update}/"

# Iterate through the JSON and update posZ for items within the target folder
for key, value in data.items():
    if target_folder_path in key:
        # value['posZ'] = new_posZ_value
        pass
    elif value['posZ'] >= new_posZ_value:
        value['posZ'] += 1

# Save the updated JSON back to the file
with open('parameters.json', 'w') as json_file:
    json.dump(data, json_file, indent=4)

print(f"posZ values updated successfully for items within /Assets/{folder_to_update}/ folder.")
"""

# Read the JSON file
with open('parameters.json', 'r') as file:
    data = json.load(file)

# Create a new dictionary with modified keys
new_data = {}
for old_key, value in data.items():
    new_key = old_key.replace('/home/gemmstone/PycharmProjects/PNGtubing/Core/../', '')
    new_data[new_key] = value

# Save the modified data back to the JSON file
with open('parameters.json', 'w') as file:
    json.dump(new_data, file, indent=4)

print("Keys have been modified and saved to parameters.json.")