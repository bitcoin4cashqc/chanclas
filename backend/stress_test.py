import time
import psutil
import os
import random
from concurrent.futures import ThreadPoolExecutor
import logging
import tempfile
import shutil
from generate import generate_image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
NUM_REQUESTS = 50  # Total number of requests to make
CONCURRENT_REQUESTS = 4  # Number of concurrent requests
TOKEN_RANGE = (1, 1000)  # Range of token IDs to test

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def generate_single_image(token_id, output_dir):
    """Generate a single image with random parameters"""
    start_time = time.time()
    try:
        # Random parameters for testing
        period = random.randint(0, 4)  # Random period 0-4
        nft_seed = random.randint(1, 1000000)
        extraMints = random.randint(0, 10)
        curveSteepness = random.randint(1, 10)
        maxRebate = random.randint(0, 100)

        # Generate image
        generate_image(
            token_id=token_id,
            period=period,
            nft_seed=nft_seed,
            extraMints=extraMints,
            curveSteepness=curveSteepness,
            maxRebate=maxRebate,
            output_dir=output_dir
        )
        
        generation_time = time.time() - start_time
        
        return {
            'token_id': token_id,
            'generation_time': generation_time,
            'success': True
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
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix='chanclas_test_')
    logger.info(f"Created temporary directory: {temp_dir}")
    
    try:
        start_time = time.time()
        results = []
        
        # Generate random token IDs
        token_ids = [random.randint(TOKEN_RANGE[0], TOKEN_RANGE[1]) for _ in range(NUM_REQUESTS)]
        
        # Run concurrent requests
        with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
            futures = [executor.submit(generate_single_image, token_id, temp_dir) for token_id in token_ids]
            
            for future in futures:
                result = future.result()
                results.append(result)
                
                # Log progress
                if result['success']:
                    logger.info(f"Token {result['token_id']}: Generation time={result['generation_time']:.2f}s")
                else:
                    logger.error(f"Token {result['token_id']} failed: {result.get('error', 'Unknown error')}")
        
        # Calculate statistics
        total_time = time.time() - start_time
        successful_requests = sum(1 for r in results if r['success'])
        failed_requests = NUM_REQUESTS - successful_requests
        
        generation_times = [r['generation_time'] for r in results if r['success']]
        
        logger.info("\nStress Test Results:")
        logger.info(f"Total time: {total_time:.2f} seconds")
        logger.info(f"Successful generations: {successful_requests}")
        logger.info(f"Failed generations: {failed_requests}")
        if generation_times:
            logger.info(f"Average generation time: {sum(generation_times)/len(generation_times):.2f} seconds")
        logger.info(f"Final memory usage: {get_memory_usage():.2f} MB")
        
    finally:
        # Clean up temporary directory
        logger.info("Cleaning up temporary directory...")
        shutil.rmtree(temp_dir)
        logger.info("Cleanup complete")

if __name__ == "__main__":
    run_stress_test() 