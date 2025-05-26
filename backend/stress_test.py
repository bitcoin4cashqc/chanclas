import requests
import time
import psutil
import os
import random
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:3000"
NUM_REQUESTS = 50  # Total number of requests to make
CONCURRENT_REQUESTS = 4  # Number of concurrent requests
TOKEN_RANGE = (1, 1000)  # Range of token IDs to test

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def make_request(token_id):
    """Make a request to the API for a specific token"""
    start_time = time.time()
    try:
        # First get metadata
        metadata_response = requests.get(f"{API_BASE_URL}/id/{token_id}")
        metadata_time = time.time() - start_time
        
        if metadata_response.status_code == 200:
            # Then get image
            image_start = time.time()
            image_response = requests.get(f"{API_BASE_URL}/image/{token_id}")
            image_time = time.time() - image_start
            
            return {
                'token_id': token_id,
                'metadata_status': metadata_response.status_code,
                'metadata_time': metadata_time,
                'image_status': image_response.status_code,
                'image_time': image_time,
                'success': True
            }
        else:
            return {
                'token_id': token_id,
                'metadata_status': metadata_response.status_code,
                'metadata_time': metadata_time,
                'success': False
            }
    except Exception as e:
        return {
            'token_id': token_id,
            'error': str(e),
            'success': False
        }

def run_stress_test():
    """Run the stress test"""
    logger.info("Starting stress test...")
    logger.info(f"Initial memory usage: {get_memory_usage():.2f} MB")
    
    start_time = time.time()
    results = []
    
    # Generate random token IDs
    token_ids = [random.randint(TOKEN_RANGE[0], TOKEN_RANGE[1]) for _ in range(NUM_REQUESTS)]
    
    # Run concurrent requests
    with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        futures = [executor.submit(make_request, token_id) for token_id in token_ids]
        
        for future in futures:
            result = future.result()
            results.append(result)
            
            # Log progress
            if result['success']:
                logger.info(f"Token {result['token_id']}: Metadata={result['metadata_time']:.2f}s, Image={result['image_time']:.2f}s")
            else:
                logger.error(f"Token {result['token_id']} failed: {result.get('error', 'Unknown error')}")
    
    # Calculate statistics
    total_time = time.time() - start_time
    successful_requests = sum(1 for r in results if r['success'])
    failed_requests = NUM_REQUESTS - successful_requests
    
    metadata_times = [r['metadata_time'] for r in results if r['success']]
    image_times = [r['image_time'] for r in results if r['success']]
    
    logger.info("\nStress Test Results:")
    logger.info(f"Total time: {total_time:.2f} seconds")
    logger.info(f"Successful requests: {successful_requests}")
    logger.info(f"Failed requests: {failed_requests}")
    if metadata_times:
        logger.info(f"Average metadata time: {sum(metadata_times)/len(metadata_times):.2f} seconds")
    if image_times:
        logger.info(f"Average image time: {sum(image_times)/len(image_times):.2f} seconds")
    logger.info(f"Final memory usage: {get_memory_usage():.2f} MB")

if __name__ == "__main__":
    run_stress_test() 