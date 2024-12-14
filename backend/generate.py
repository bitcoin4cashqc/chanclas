import os
import random
from PIL import Image

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
    "09_Eyewears": "./layers/09_Eyewears/"
}

# Define rarity weights and exclusions
rarity = {
    "01_Background": [("01.-Red.png", 70), ("03.-Blue.png", 30)],
    "02_Quad_UL": [("01.-Rat.png", 50), ("02.-Ox.png", 50)],
    "06_Base": [("01.-Red.png", 60), ("03.-Blue.png", 40)],
}
exclusions = [
    ("01.-Red.png", "01.-Red.png")  # Example: Rat cannot coexist with Snake
]

# Function to generate a single image
def generate_image(token_id, output_dir):
    random.seed(token_id)  # Use token_id as the seed for determinism
    selected_layers = {}

    # Select layers based on rarity and exclusions
    for layer, options in rarity.items():
        choices, weights = zip(*options)
        selected = random.choices(choices, weights=weights, k=1)[0]
        # Check exclusions
        if any(selected == excl[0] and excl[1] in selected_layers.values() for excl in exclusions):
            continue
        selected_layers[layer] = selected

    # Combine layers into a final image
    base_image = None
    for layer, file_name in selected_layers.items():
        layer_image = Image.open(os.path.join(directories[layer], file_name)).convert("RGBA")
        if base_image is None:
            base_image = layer_image
        else:
            base_image.paste(layer_image, (0, 0), layer_image)

    # Save the final image
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_path = os.path.join(output_dir, f"{token_id}.png")
    base_image.save(output_path)
    print(f"Generated image for token {token_id}: {output_path}")

# Generate multiple images
def generate_images(start_token, end_token, output_dir):
    for token_id in range(start_token, end_token + 1):
        generate_image(token_id, output_dir)

# Example usage
generate_images(0, 1, "./output")
