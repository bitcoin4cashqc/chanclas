import os
from randomizer import randomizing
import json

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
