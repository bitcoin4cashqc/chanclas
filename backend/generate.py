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
def generate_image(period,nft_seed,output_dir):
    rarity = load_rarities(period)
    base_image = randomizing(nft_seed,rarity,directories)
    # Save the final image
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_path = os.path.join(output_dir, f"{nft_seed}.png")
    base_image.save(output_path)
    print(f"Generated image for token {nft_seed}: {output_path}")

# Generate multiple images
def generate_images(seeds, output_dir):
    for data in seeds:
        generate_image(data["period"], data["seed"], output_dir)

# Example usage
# seeds = [{"period":1,"seed":"ojfeu9hff98hfu9wh"},{"period":1,"seed":"ha8dh83h9o3jqe83ht874g8yt"},{"period":1,"seed":"fiwj398fwjh98fhw98hg9huousdh"}]
# generate_images(seeds,"./output")
i = 0
while i < 100:
    generate_image(1,i,"./output")
    i += 1