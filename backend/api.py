from flask import Flask, send_file, jsonify, request  # Import `request`
import os
from web3 import Web3
from generate import generate_image  # Your image generation function
import json

app = Flask(__name__)

# Directory to save generated images
OUTPUT_DIR = "./output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Web3 configuration
RPC_URL = "https://your-rpc-url"  # Replace with your RPC URL
CONTRACT_ADDRESS = "0xYourContractAddress"  # Replace with your contract address

# Load the contract ABI
with open("contract_abi.json", "r") as f:
    CONTRACT_ABI = json.load(f)

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(RPC_URL))
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

#shall generate if not exist but its minted
def mint(token_id):
    pass

@app.route("/nft/<int:token_id>", methods=["GET"])
def get_nft_metadata(token_id):
    try:
        # Query the blockchain for the token data
        token_data = contract.functions.getTokenData(token_id).call()
        seed, period_id = token_data

        # Load metadata
        metadata_path = os.path.join(OUTPUT_DIR, f"{seed}.json")
        if not os.path.exists(metadata_path):
            return jsonify({"error": "Metadata not found"}), 404

        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        # Construct the image URL using `request.host_url`
        image_url = f"{request.host_url.rstrip('/')}/nft/image/{token_id}"

        # Add standard metadata fields for marketplaces
        metadata.update({
            "name": f"NFT #{token_id}",
            "description": "An awesome NFT from the Chanclas collection.",
            "image": image_url
        })

        return jsonify(metadata)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/nft/image/<int:token_id>", methods=["GET"])
def get_nft_image(token_id):
    try:
        # Query the blockchain for the token data
        token_data = contract.functions.getTokenData(token_id).call()
        seed, period_id = token_data

        # Image path
        image_path = os.path.join(OUTPUT_DIR, f"{seed}.png")

        # Check if the image already exists
        if not os.path.exists(image_path):
            generate_image(period_id, seed, OUTPUT_DIR)

        return send_file(image_path, mimetype="image/png")
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
