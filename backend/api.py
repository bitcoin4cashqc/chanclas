from flask import Flask, send_file, jsonify, Response, request  # Import `request`
import os
import psutil
import logging
from web3 import Web3
from generate import generate_image  # Your image generation function
import json
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis.exceptions import RedisError
import time
import gc
import resource
import signal
from functools import wraps
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set memory limits (in bytes) - 100MB per worker
MEMORY_LIMIT = 100 * 1024 * 1024  # 100MB
resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT, MEMORY_LIMIT))

REDIS_URL = "redis://localhost:6379/0"  # Local Redis instance

app = Flask(__name__)

# Ensure Flask logs to stdout (Gunicorn captures stdout)
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

# Initialize limiter with fallback
# try:
#     limiter = Limiter(
#         app=app,
#         key_func=get_remote_address,
#         storage_uri=REDIS_URL,
#         storage_options={"socket_connect_timeout": 30},
#         strategy="fixed-window",
#         default_limits=["200 per day", "50 per hour"]
#     )
# except RedisError as e:
#     logger.warning(f"Redis connection failed: {e}. Falling back to in-memory storage.")
#     limiter = Limiter(
#         app=app,
#         key_func=get_remote_address,
#         storage_uri="memory://",
#         strategy="fixed-window",
#         default_limits=["200 per day", "50 per hour"]
#     )

# Directory to save generated images
OUTPUT_DIR = "./output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Web3 configuration
CONTRACT_ADDRESS = "0x262cA2E567315300CDdf389A0D2E37212F4DAEF4"  # Contract address

# RPC URLs ordered by speed (fastest first)
RPC_URLS = [
    "https://base-rpc.publicnode.com", 
    "https://base-mainnet.public.blastapi.io",  
    "wss://0xrpc.io/base", 
    "https://base.blockpi.network/v1/rpc/public",
    "https://developer-access-mainnet.base.org",  
    "https://mainnet.base.org",  
    "https://base-pokt.nodies.app", 
    "https://base.lava.build",  
    "https://base.api.onfinality.io/public", 
    "https://endpoints.omniatech.io/v1/base/mainnet/public", 
    "https://0xrpc.io/base", 
    "https://base.meowrpc.com",  
    "https://rpc.therpc.io/base", 
    "https://rpc.owlracle.info/base/70d38ce1826c4a60bb2a8e05a6c8b20f", 
    "https://base.drpc.org", 
    "https://base.rpc.subquery.network/public",  
    "https://base.llamarpc.com", 
    "https://api.zan.top/base-mainnet", 
]

def cleanup_resources():
    """Clean up resources after request"""
    gc.collect()
    if hasattr(cleanup_resources, 'web3'):
        del cleanup_resources.web3

def memory_monitor():
    """Monitor memory usage"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_usage = memory_info.rss / 1024 / 1024  # Convert to MB
    if memory_usage > MEMORY_LIMIT / (1024 * 1024) * 0.9:  # 90% of limit
        logger.warning(f"High memory usage detected: {memory_usage:.2f}MB")
        cleanup_resources()
        gc.collect()

def get_next_rpc():
    """Get the next RPC URL in rotation."""
    if not hasattr(get_next_rpc, "current_index"):
        get_next_rpc.current_index = 0
    
    rpc_url = RPC_URLS[get_next_rpc.current_index]
    get_next_rpc.current_index = (get_next_rpc.current_index + 1) % len(RPC_URLS)
    return rpc_url

# Load the contract ABI
with open("Chanclas_ABI.json", "r") as f:
    CONTRACT_ABI = json.load(f)

def get_web3_contract():
    """Get a new Web3 contract instance with retry logic."""
    max_retries = len(RPC_URLS)
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            rpc_url = get_next_rpc()
            web3 = Web3(Web3.HTTPProvider(rpc_url))
            if web3.is_connected():
                cleanup_resources.web3 = web3  # Store for cleanup
                return web3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise e

def is_token_minted(token_id):
    """Check if a token is minted by querying the owner."""
    try:
        contract = get_web3_contract()
        owner = contract.functions.ownerOf(token_id).call()
        return True
    except Exception as e:
        logger.error(f"Error checking token {token_id}: {e}")
        return False

# @app.before_request
# def log_resources():
#     process = psutil.Process(os.getpid())
#     app.logger.info(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")

def localhost_only(f):
    """Decorator to ensure requests only come from localhost"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.remote_addr not in ['127.0.0.1', 'localhost']:
            return jsonify({"error": "Access denied - localhost only"}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route("/id/<int:token_id>", methods=["GET"])
#@limiter.limit("60 per minute")
def get_nft_metadata(token_id):
    try:
        logger.info(f"Reading metadata for token {token_id}")
        memory_monitor()
        
        # Metadata path
        metadata_path = os.path.join(OUTPUT_DIR, f"{token_id}.json")
        image_path = os.path.join(OUTPUT_DIR, f"{token_id}.png")

        # If both files exist, skip the mint check
        if os.path.exists(metadata_path) and os.path.exists(image_path):
            try:
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                logger.info(f"Metadata read successfully for token {token_id}")
                return Response(json.dumps(metadata), mimetype="application/json")
            except Exception as e:
                logger.error(f"Error reading metadata for token {token_id}: {e}")
                return jsonify({"error": "Failed to read metadata"}), 500

        # Check if the token is minted
        if not is_token_minted(token_id):
            return jsonify({"error": f"Token {token_id} is not minted"}), 404

        # Generate metadata if missing
        if not os.path.exists(metadata_path):
            try:
                # Query the blockchain for token data
                contract = get_web3_contract()
                token_data = contract.functions.getTokenData(token_id).call()
                seed, period_id, extraMints, curveSteepness, maxRebate = token_data
                generate_image(token_id, period_id, seed, extraMints, curveSteepness, maxRebate, OUTPUT_DIR)
                cleanup_resources()  # Clean up after image generation
            except Exception as e:
                logger.error(f"Error generating image for token {token_id}: {e}")
                return jsonify({"error": "Failed to generate metadata"}), 500

        # Return metadata
        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
                logger.info(f"Metadata read successfully AFTER GENERATION for token {token_id}")
            return Response(json.dumps(metadata), mimetype="application/json")
        except Exception as e:
            logger.error(f"Error reading metadata for token {token_id}: {e}")
            return jsonify({"error": "Failed to read metadata"}), 500

    except Exception as e:
        logger.error(f"Unexpected error for token {token_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/image/<int:token_id>", methods=["GET"])
#@limiter.limit("60 per minute")
def get_nft_image(token_id):
    logger.info(f"Reading image for token {token_id}")
    try:
        memory_monitor()
        
        # Image path
        image_path = os.path.join(OUTPUT_DIR, f"{token_id}.png")
        metadata_path = os.path.join(OUTPUT_DIR, f"{token_id}.json")

        # If both files exist, skip the mint check
        if os.path.exists(image_path):
            logger.info(f"Image read successfully for token {token_id}")
            return send_file(image_path, mimetype="image/png")

        # Check if the token is minted
        if not is_token_minted(token_id):
            return jsonify({"error": f"Token {token_id} is not minted"}), 404

        # Generate image if missing
        if not os.path.exists(image_path):
            try:
                # Query the blockchain for token data
                contract = get_web3_contract()
                token_data = contract.functions.getTokenData(token_id).call()
                seed, period_id, extraMints, curveSteepness, maxRebate = token_data
                generate_image(token_id, period_id, seed, extraMints, curveSteepness, maxRebate, OUTPUT_DIR)
                cleanup_resources()  # Clean up after image generation
            except Exception as e:
                logger.error(f"Error generating image for token {token_id}: {e}")
                return jsonify({"error": "Failed to generate image"}), 500
        logger.info(f"Image read successfully AFTER GENERATION for token {token_id}")
        return send_file(image_path, mimetype="image/png")
    except Exception as e:
        logger.error(f"Unexpected error for token {token_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.after_request
def after_request(response):
    """Cleanup after each request"""
    cleanup_resources()
    return response

# Test endpoint for stress testing
@app.route("/test/generate/<int:token_id>", methods=["GET"])
@localhost_only
def test_generate(token_id):
    """Test endpoint that bypasses web3 checks and uses temporary directory"""
    try:
        logger.info(f"Test generating token {token_id}")
        memory_monitor()
        
        # Create temporary directory for this request
        temp_dir = tempfile.mkdtemp(prefix=f'chanclas_test_{token_id}_')
        try:
            # Generate with test parameters
            period = 0  # Use period 0 for testing
            nft_seed = token_id  # Use token_id as seed for consistency
            extraMints = 0
            curveSteepness = 1
            maxRebate = 0
            
            # Generate image
            image_path, metadata_path = generate_image(
                token_id=token_id,
                period=period,
                nft_seed=nft_seed,
                extraMints=extraMints,
                curveSteepness=curveSteepness,
                maxRebate=maxRebate,
                output_dir=temp_dir
            )
            
            # Read metadata
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            
            # Send response
            return Response(json.dumps(metadata), mimetype="application/json")
            
        finally:
            # Clean up temporary directory
            import shutil
            shutil.rmtree(temp_dir)
            
    except Exception as e:
        logger.error(f"Error in test generation for token {token_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/test/image/<int:token_id>", methods=["GET"])
@localhost_only
def test_image(token_id):
    """Test endpoint for getting generated image"""
    try:
        logger.info(f"Test getting image for token {token_id}")
        memory_monitor()
        
        # Create temporary directory for this request
        temp_dir = tempfile.mkdtemp(prefix=f'chanclas_test_{token_id}_')
        try:
            # Generate with test parameters
            period = 0  # Use period 0 for testing
            nft_seed = token_id  # Use token_id as seed for consistency
            extraMints = 0
            curveSteepness = 1
            maxRebate = 0
            
            # Generate image
            image_path, _ = generate_image(
                token_id=token_id,
                period=period,
                nft_seed=nft_seed,
                extraMints=extraMints,
                curveSteepness=curveSteepness,
                maxRebate=maxRebate,
                output_dir=temp_dir
            )
            
            # Send image
            return send_file(image_path, mimetype="image/png")
            
        finally:
            # Clean up temporary directory
            import shutil
            shutil.rmtree(temp_dir)
            
    except Exception as e:
        logger.error(f"Error in test image for token {token_id}: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=False, port=3000)
