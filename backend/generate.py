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



def randomizing(token_id,nft_seed, rarity, directories):
    
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
        "external_url": f"https://chanclas.io/{token_id}",
        "image": f"https://chanclas.io/image/{token_id}",
        "name": f"Chanclas NFT #{token_id}",
        "attributes": []  # Attributes will be added later
    }
   
    astronautBypass = False

    # Utility to format names (remove digits, dots, extensions, and replace `_`)
    def format_name(name):
        name = re.sub(r"[0-9.\-_]+", " ", name)  # Remove digits, dots, dashes
        name = re.sub(r"png", " ", name)  # Remove digits, dots, dashes
        return re.sub(r"\s+", " ", name).strip()  # Remove extra spaces

    # Select layers based on rarity and exclusions
    for layer, options in rarity.items():
        formatted_layer = format_name(layer)  # Format layer name
        print("Layer:", formatted_layer)

        # Special handling for 06_Base and 07_ToeGuards
        if layer == "06_Base":
            choices = [item['file'] for item in options]
            weights = [item['weight'] for item in options]
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

        # Regular layers
        choices = [item['file'] for item in options]
        weights = [item['weight'] for item in options]
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
            layer_image = Image.open(os.path.join(directories[layer], file_name)).convert("RGBA")
            if base_image is None:
                base_image = layer_image
            else:
                base_image.paste(layer_image, (0, 0), layer_image)

    return base_image, metadata

# Function to generate a single image
def generate_image(token_id, period, nft_seed, output_dir):
    rarity = load_rarities(period)
    base_image, metadata = randomizing(token_id, nft_seed, rarity, directories)

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

if __name__ == '__main__':
    print("Helllo")
    for period in periods:
        print(verify_files_exist(period))
