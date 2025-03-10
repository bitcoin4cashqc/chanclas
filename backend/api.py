from flask import Flask, send_file, jsonify, Response  # Import `request`
import os
import psutil
import logging
from web3 import Web3
from generate import generate_image  # Your image generation function
import json
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address



REDIS_URL = "redis://localhost:6379/0"  # Local Redis instance

app = Flask(__name__)

# Ensure Flask logs to stdout (Gunicorn captures stdout)
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=REDIS_URL,
        storage_options={"socket_connect_timeout": 30},  # Timeout for Redis connections
        strategy="fixed-window",  # or "moving-window"
    )

# Directory to save generated images
OUTPUT_DIR = "./output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Web3 configuration
RPC_URL = "https://mainnet.base.org/"  # Replace with your RPC URL
CONTRACT_ADDRESS = "0x262cA2E567315300CDdf389A0D2E37212F4DAEF4"  # Replace with your contract address

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
    

@app.before_request
def log_resources():
    process = psutil.Process(os.getpid())
    app.logger.info(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")


@app.route("/id/<int:token_id>", methods=["GET"])
@limiter.limit("60 per minute")  # Prevent abuse
def get_nft_metadata(token_id):
    try:
        # Check if the token is minted
        if not is_token_minted(token_id):
            return jsonify({"error": f"Token {token_id} is not minted"}), 404

        # Query the blockchain for token data
        token_data = contract.functions.getTokenData(token_id).call()
        seed, period_id, extraMints, curveSteepness, maxRebate = token_data

        # Metadata path
        metadata_path = os.path.join(OUTPUT_DIR, f"{token_id}.json")

        # Generate metadata if missing
        if not os.path.exists(metadata_path):
            generate_image(token_id, period_id, seed, extraMints, curveSteepness, maxRebate, OUTPUT_DIR)

        # Return metadata
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        return Response(json.dumps(metadata), mimetype="application/json")
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/image/<int:token_id>", methods=["GET"])
@limiter.limit("60 per minute")  # Prevent abuse
def get_nft_image(token_id):
    try:
        # Check if the token is minted
        if not is_token_minted(token_id):
            return jsonify({"error": f"Token {token_id} is not minted"}), 404

        # Query the blockchain for token data
        token_data = contract.functions.getTokenData(token_id).call()
        seed, period_id, extraMints, curveSteepness, maxRebate = token_data

        # Image path
        image_path = os.path.join(OUTPUT_DIR, f"{token_id}.png")

        # Generate image if missing
        if not os.path.exists(image_path):
            generate_image(token_id, period_id, seed, extraMints, curveSteepness, maxRebate ,OUTPUT_DIR)

        return send_file(image_path, mimetype="image/png")
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    


if __name__ == "__main__":
    app.run(debug=False, port=3000)
