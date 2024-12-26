import os
from randomizer import randomizing

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
    "01_Background": [("01.-Red.png", 6.25), ("02.-Green.png", 6.25),("03.-Blue.png", 6.25), ("04.-Yellow.png", 6.25),("05.-Orange.png", 6.25), ("06.-Indigo.png", 6.25),("07.-Violet.png", 6.25), ("08.-Black.png", 6.25),("09.-Silver.png", 6.25), ("10.-Gold.png", 6.25),("11.-Diamond.png", 6.25), ("12.-Steel.png", 6.25),("13.-Wood.png", 6.25), ("14.-Sand.png", 6.25),("15.-Brick.png", 6.25), ("16.-Marble.png", 6.25)],

    "02_Quad_UL": [("01.-Rat.png", 4.1666666667),("02.-Ox.png", 4.1666666667),("03.-Tiger.png", 4.1666666667),("04.-Rabbit.png", 4.1666666667),("05.-Dragon.png", 4.1666666667),("06.-Black-Rat.png", 4.1666666667),("07.-Black-Ox.png", 4.1666666667),("08.-Black-Tiger.png", 4.1666666667),("09.-Black-Rabbit.png", 4.1666666667),("10.-Black-Dragon.png", 4.1666666667),("11.-Gold-Rat.png", 4.1666666667),("12.-Gold-Ox.png", 4.1666666667),("13.-Gold-Tiger.png", 4.1666666667),("14.-Gold-Rabbit.png", 4.1666666667),("15.-Gold-Dragon.png", 4.1666666667),("16.-Silver-Rat.png", 4.1666666667),("17.-Silver-Ox.png", 4.1666666667),("18.-Silver-Tiger.png", 4.1666666667),("19.-Silver-Rabbit.png", 4.1666666667),("20.-Silver-Dragon.png", 4.1666666667),("86._Playstation-White.png", 4.1666666667),("87._Playstation-Black.png", 4.1666666667),("88._Playstation-Silver.png", 4.1666666667),("89._Playstation-Gold.png", 4.1666666667)],

    "03_Quad_UR":[("21.-Snake.png", 4.1666666667),("22.-Horse.png", 4.1666666667),("23.-Goat.png", 4.1666666667),("24.-Monkey.png", 4.1666666667),("25.-Rooster.png", 4.1666666667),("26.-Black-Snake.png", 4.1666666667),("27.-Black-Horse.png", 4.1666666667),("28.-Black-Goat.png", 4.1666666667),("29.-Black-Monkey.png", 4.1666666667),("30.-Black-Rooster.png", 4.1666666667),("31.-Gold-Snake.png", 4.1666666667),("32.-Gold-Horse.png", 4.1666666667),("33.-Gold-Goat.png", 4.1666666667),("34.-Gold-Monkey.png", 4.1666666667),("35.-Gold-Rooster.png", 4.1666666667),("36.-Silver-Snake.png", 4.1666666667),("37.-Silver-Horse.png", 4.1666666667),("38.-Silver-Goat.png", 4.1666666667),("39.-Silver-Monkey.png", 4.1666666667),("40.-Silver-Rooster.png", 4.1666666667),("90._Martini-White.png", 4.1666666667),("91._Martini-Black.png", 4.1666666667),("92._Martini-Silver.png", 4.1666666667),("93._Martini-Gold.png", 4.1666666667)],

    "06_Base": [("01.-Red.png", 60), ("03.-Blue.png", 40)],
}


# Function to generate a single image
def generate_image(nft_seed,output_dir):
    base_image = randomizing(nft_seed,rarity,directories)
    # Save the final image
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_path = os.path.join(output_dir, f"{nft_seed}.png")
    base_image.save(output_path)
    print(f"Generated image for token {nft_seed}: {output_path}")

# Generate multiple images
def generate_images(seeds, output_dir):
    for seed in seeds:
        generate_image(seed, output_dir)

# Example usage
seeds = ["ha8dh83h9o3jqe83ht874g8yt","nuf83hr79y43rt782g3gd32","y82vrg732vf7923by83b83y"]
generate_images(seeds,"./output")
