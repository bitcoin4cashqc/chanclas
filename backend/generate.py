import os
import json
import random
from PIL import Image
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

periods = [0]

# Define paths to directories
directories = {
    "01_Background": "./layers/01_Background/",
    "02_Quad_UL": "./layers/02_Quad_UL/",
    "03_Quad_UR": "./layers/03_Quad_UR/",
    "04_Quad_DL": "./layers/04_Quad_DL/",
    "05_Quad_DR": "./layers/05_Quad_DR/",
    "06_Base": "./layers/06_Base/",
    "07_ToeGuards": "./layers/07_ToeGuards/",
    "08_Hats": "./layers/08_Hats/",
    "09_Eyewear": "./layers/09_Eyewear/"
}

# Function to load rarities based on period
def load_rarities(period):
    with open(f"./rarities/rarities_{period}.json", "r") as f:
        return json.load(f)
    
# Function to verify if files exist
def verify_files_exist(period):
    rarities = load_rarities(period)
    missing_files = {}

    for layer, files in rarities.items():
        if layer in directories:
            layer_directory = directories[layer]
            for file_info in files:
                file_name = file_info["file"]
                if file_name != "EMPTY":  # Skip "EMPTY" entries
                    file_path = os.path.join(layer_directory, file_name)
                    if not os.path.exists(file_path):
                        if layer not in missing_files:
                            missing_files[layer] = []
                        missing_files[layer].append(file_name)

    return missing_files



def randomizing(token_id,nft_seed, rarity,d, directories, test = None):
    
    # Retrieve the secret salt from the .env file
    secret_salt = os.getenv("NFT_SECRET_SALT", "default_salt_if_not_found")
    
    # Combine the token_id, nft_seed, and secret salt to create a unique seed
    combined_seed = f"{token_id}_{nft_seed}_{secret_salt}"
    
    # Set the seed for determinism
    random.seed(combined_seed)


    selected_layers = {}

    # Initialize metadata with general fields
    metadata = {
        "description": "Friendly Chanclas Creature that enjoys long walks on the beach.", 
        "external_url": f"https://chanclas.fun/id/{token_id}",
        "image": f"https://chanclas.fun/image/{token_id}",
        "name": f"Chanclas NFT #{token_id}",
        "attributes": []  # Attributes will be added later
    }
   
    astronautBypass = False

    # Utility to format names (remove digits, dots, extensions, and replace `_`)
    def format_name(name):
        # Remove file extension
        name = name.replace('.png', '')
        
        # Save any instances of 3D or 3d
        has_3d = "3D" in name
        has_3d_lowercase = "3d" in name
        
        # Remove all digits and special characters
        name = re.sub(r'[0-9.\-_]+', ' ', name)
        
        # Restore 3D/3d if they were present
        if has_3d:
            name = name.replace('D', '3D', 1)
        if has_3d_lowercase:
            name = name.replace('d', '3D', 1)
            
        # Clean up extra spaces and trim
        return re.sub(r'\s+', ' ', name).strip()

    # Select layers based on rarity and exclusions
    for layer, options in rarity.items():

        # Adjust weights based on d
        adjusted_options = []
        for item in options:
            original_weight = item['weight']
            if original_weight <= 0:
                adjusted_weight = 0.0
            else:
                adjusted_weight = original_weight ** (-d)
            # Create a new item with adjusted weight
            adjusted_item = item.copy()
            adjusted_item['weight'] = adjusted_weight
            adjusted_options.append(adjusted_item)
        
        formatted_layer = format_name(layer)  # Format layer name
        print("Layer:", formatted_layer)
        if test is not None:
            if layer == "01_Background" or layer == "02_Quad_UL" or layer == "03_Quad_UR" or layer == "04_Quad_DL" or layer == "05_Quad_DR":
                continue
        
        # Special handling for 06_Base and 07_ToeGuards
        if layer == "06_Base":
            choices = [item['file'] for item in adjusted_options]
            weights = [item['weight'] for item in adjusted_options]
            selected_base = random.choices(choices, weights=weights, k=1)[0]
            selected_layers[layer] = selected_base
            selected_layers["07_ToeGuards"] = selected_base  # Ensure matching ToeGuard

            # Add to metadata
            metadata["attributes"].append({
                "trait_type": format_name(layer),
                "value": format_name(selected_base)
            })
            metadata["attributes"].append({
                "trait_type": format_name("07_ToeGuards"),
                "value": format_name(selected_base)
            })
            continue

        # Skip eyewear if astronaut hat is selected
        if layer == "09_Eyewear" and astronautBypass:
            continue
            
        # Regular layers
        choices = [item['file'] for item in adjusted_options]
        weights = [item['weight'] for item in adjusted_options]
        selected = random.choices(choices, weights=weights, k=1)[0]

        # Handle EMPTY exclusions
        if layer in ["08_Hats", "09_Eyewear"] and "EMPTY" in selected:
            continue

        # Add to selected layers and metadata
        selected_layers[layer] = selected
        metadata["attributes"].append({
            "trait_type": formatted_layer,
            "value": format_name(selected)
        })

        # Astronaut-specific bypass
        if layer == "08_Hats" and "Astronaut" in selected:
            astronautBypass = True

    # Combine layers into a final image
    base_image = None
    for layer, file_name in selected_layers.items():
        if layer is not None:
            with Image.open(os.path.join(directories[layer], file_name)) as layer_image:  # Use context manager
                layer_image = layer_image.convert("RGBA")
                if base_image is None:
                    base_image = layer_image.copy()
                else:
                    base_image.paste(layer_image, (0, 0), layer_image)
                layer_image.close()  # Explicit cleanup

    return base_image, metadata

# Function to generate a single image
def generate_image(token_id, period, nft_seed, extraMints, curveSteepness, maxRebate, output_dir,test = None):
    rarity = load_rarities(period)
    discount = (maxRebate * extraMints) / (extraMints + curveSteepness)
    d = discount / 100.0  # Convert to a decimal

    base_image, metadata = randomizing(token_id, nft_seed, rarity, d, directories, test)

    # Save the final image
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_path = os.path.join(output_dir, f"{token_id}.png")
    base_image.save(output_path)
    print(f"Generated image for token {nft_seed}: {output_path}")

    # Save metadata as JSON
    metadata_output = os.path.join(output_dir, f"{token_id}.json")
    with open(metadata_output, "w") as f:
        json.dump(metadata, f, indent=4)
    print(f"Metadata saved for token {nft_seed}: {metadata_output}")

    return output_path, metadata_output

