from flask import Flask, send_file, jsonify, Response  # Import `request`
import os
from web3 import Web3
from generate import generate_image  # Your image generation function
import json

app = Flask(__name__)

# Directory to save generated images
OUTPUT_DIR = "./output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Web3 configuration
RPC_URL = "http://127.0.0.1:9545/"  # Replace with your RPC URL
CONTRACT_ADDRESS = "0x47C4A2F484681a624996137dD22d070611713d4C"  # Replace with your contract address

# Load the contract ABI
with open("Chanclas_ABI.json", "r") as f:
    CONTRACT_ABI = json.load(f)

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(RPC_URL))
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

def is_token_minted(token_id):
    """Check if a token is minted by querying the owner."""
    try:
        owner = contract.functions.ownerOf(token_id).call()
        
        return True
    except Exception as e:
       
        return False

@app.route("/<int:token_id>", methods=["GET"])
def get_nft_metadata(token_id):
    try:
        # Check if the token is minted
        if not is_token_minted(token_id):
            return jsonify({"error": f"Token {token_id} is not minted"}), 404

        # Query the blockchain for token data
        token_data = contract.functions.getTokenData(token_id).call()
        seed, period_id = token_data

        # Metadata path
        metadata_path = os.path.join(OUTPUT_DIR, f"{token_id}.json")

        # Generate metadata if missing
        if not os.path.exists(metadata_path):
            generate_image(token_id, period_id, seed, OUTPUT_DIR, "./output")

        # Return metadata
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        return Response(json.dumps(metadata), mimetype="application/json")
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/image/<int:token_id>", methods=["GET"])
def get_nft_image(token_id):
    try:
        # Check if the token is minted
        if not is_token_minted(token_id):
            return jsonify({"error": f"Token {token_id} is not minted"}), 404

        # Query the blockchain for token data
        token_data = contract.functions.getTokenData(token_id).call()
        seed, period_id = token_data

        # Image path
        image_path = os.path.join(OUTPUT_DIR, f"{token_id}.png")

        # Generate image if missing
        if not os.path.exists(image_path):
            generate_image(token_id, period_id, seed, OUTPUT_DIR, "./output")

        return send_file(image_path, mimetype="image/png")
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    


if __name__ == "__main__":
    app.run(debug=True, port=3000)
