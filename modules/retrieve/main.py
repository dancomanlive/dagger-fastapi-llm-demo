import json
import argparse
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import logging
import time
import os
import pickle
import hashlib

# --- Global Variables ---
MODULE_CACHE_DIR = "/tmp/module_cache"
_GLOBAL_MODEL = None
logger = logging.getLogger(__name__)

# --- Setup Functions ---
def setup_logging():
    """Configures basic logging for the script if not already configured."""
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s')
        logger.info("Logging configured.")
    else: # pragma: no cover
        logger.info("Logging was already configured.")

def ensure_cache_dir():
    """Ensures the module cache directory exists."""
    os.makedirs(MODULE_CACHE_DIR, exist_ok=True)
    # This log might be redundant if setup_logging isn't called first,
    # but main() calls setup_logging() before this.
    logger.info(f"Ensured cache directory exists: {MODULE_CACHE_DIR}")

# --- Core Logic Functions ---
def get_model_with_timing():
    """Loads the SentenceTransformer model, timing the operation.
    Caches the model instance globally for the current script run.
    Relies on HF_HOME for caching downloaded models across Dagger runs.
    """
    global _GLOBAL_MODEL
    if _GLOBAL_MODEL is not None:
        logger.info("Using already loaded _GLOBAL_MODEL instance.")
        return _GLOBAL_MODEL

    t_start = time.monotonic()
    logger.info("Attempting to load SentenceTransformer model...")
    model_path_in_container = '/app/model'
    loaded_model = None

    try:
        if os.path.exists(model_path_in_container) and os.listdir(model_path_in_container):
            logger.info(f"Found potential model at {model_path_in_container}. Attempting to load.")
            loaded_model = SentenceTransformer(model_path_in_container)
            logger.info(f"Successfully loaded model from {model_path_in_container}.")
        else:
            raise FileNotFoundError(f"Directory {model_path_in_container} not found or is empty.")
    except Exception as e:
        logger.warning(f"Failed to load model from {model_path_in_container}: {e}. Falling back to default.")
        default_model_name = 'paraphrase-MiniLM-L3-v2'
        logger.info(f"Loading fallback model: '{default_model_name}' (will use HF_HOME for caching).")
        loaded_model = SentenceTransformer(default_model_name)
        logger.info(f"Successfully loaded fallback model '{default_model_name}'.")

    _GLOBAL_MODEL = loaded_model
    logger.info(f"TIMING: get_model_with_timing completed in {time.monotonic() - t_start:.4f}s.")
    return _GLOBAL_MODEL

def get_embedding_with_timing(query: str, use_cache=True) -> list:
    """Generates or loads a cached embedding for the query, timing the operation."""
    t_start = time.monotonic()
    cache_file_path = None

    if use_cache:
        query_hash = hashlib.md5(query.encode()).hexdigest()
        cache_file_path = os.path.join(MODULE_CACHE_DIR, f'{query_hash}.pkl')
        if os.path.exists(cache_file_path):
            try:
                with open(cache_file_path, 'rb') as f:
                    vector = pickle.load(f)
                logger.info(f"Loaded embedding from cache: {cache_file_path} for query: {query[:30]}...")
                logger.info(f"TIMING: get_embedding_with_timing (from cache) completed in {time.monotonic() - t_start:.4f}s.")
                return vector
            except Exception as e:
                logger.warning(f"Failed to load from {cache_file_path}: {e}. Recomputing embedding.")

    model = get_model_with_timing() # Ensures model is loaded
    logger.info(f"Computing embedding for query: {query[:30]}...")
    t_encode_start = time.monotonic()
    vector = model.encode(query).tolist()
    logger.info(f"TIMING: model.encode() took {time.monotonic() - t_encode_start:.4f}s.")

    if use_cache and cache_file_path:
        try:
            with open(cache_file_path, 'wb') as f:
                pickle.dump(vector, f)
            logger.info(f"Saved new embedding to cache: {cache_file_path}")
        except Exception as e: # pragma: no cover
            logger.warning(f"Failed to save embedding to {cache_file_path}: {e}")
    
    logger.info(f"TIMING: get_embedding_with_timing (computed) completed in {time.monotonic() - t_start:.4f}s.")
    return vector

def connect_to_qdrant_with_timing(qdrant_url: str, api_key: str = None, max_retries: int = 2, timeout: float = 5.0):
    """Connects to Qdrant with retries, timing the operation."""
    t_start = time.monotonic()
    logger.info(f"Attempting to connect to Qdrant at {qdrant_url} with API key: {'Yes' if api_key else 'No'}")
    
    client = None
    for attempt in range(max_retries):
        try:
            client = QdrantClient(url=qdrant_url, api_key=api_key, timeout=timeout)
            client.get_collections() # Verify connection
            logger.info(f"Successfully connected to Qdrant at {qdrant_url} on attempt {attempt + 1}.")
            logger.info(f"TIMING: connect_to_qdrant_with_timing completed in {time.monotonic() - t_start:.4f}s.")
            return client
        except Exception as e:
            logger.warning(f"Qdrant connection attempt {attempt + 1}/{max_retries} to {qdrant_url} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep((attempt + 1) * 1.0) # Simple backoff: 1s, 2s
            else:
                logger.error(f"Failed to connect to Qdrant at {qdrant_url} after {max_retries} attempts.")
                logger.info(f"TIMING: connect_to_qdrant_with_timing (failed) took {time.monotonic() - t_start:.4f}s.")
                raise ConnectionError(f"Could not connect to Qdrant: {qdrant_url}") from e
    return None # Should be unreachable if exception is raised

def search_qdrant_with_timing(client: QdrantClient, collection_name: str, vector: list, top_k: int, score_threshold: float = 0.2):
    """Performs a search on Qdrant, timing the operation."""
    t_start = time.monotonic()
    logger.info(f"Searching Qdrant collection '{collection_name}' with top_k={top_k}, threshold={score_threshold}.")
    
    try:
        search_params = {
            "collection_name": collection_name,
            "query_vector": vector,
            "limit": top_k,
            "with_payload": True,
            "score_threshold": score_threshold
        }
        qdrant_hits = client.search(**search_params)
        logger.info(f"Qdrant search found {len(qdrant_hits)} raw results.")
        
        results = []
        for hit in qdrant_hits:
            payload = hit.payload if hit.payload else {}
            results.append({
                "id": str(hit.id),
                "score": float(hit.score),
                "text": payload.get("text", "N/A"),
                "source": payload.get("source", "N/A")
            })
        logger.info(f"TIMING: search_qdrant_with_timing completed in {time.monotonic() - t_start:.4f}s.")
        return results
    except Exception as e: # pragma: no cover
        logger.error(f"Error during Qdrant search in '{collection_name}': {e}", exc_info=True)
        logger.info(f"TIMING: search_qdrant_with_timing (failed) took {time.monotonic() - t_start:.4f}s.")
        raise # Re-raise the exception to be caught by main error handler

# --- Main Execution ---
def main():
    script_overall_start_time = time.monotonic()
    setup_logging()
    ensure_cache_dir()

    parser = argparse.ArgumentParser(description="Retrieve documents from Qdrant.")
    parser.add_argument("--input", required=True, help="Input JSON file path.")
    parser.add_argument("--output", default="output.json", help="Output JSON file path.")
    args = parser.parse_args()

    logger.info(f"Retrieve module started. Input: {args.input}, Output: {args.output}")
    input_data = {}

    try:
        t_io_start = time.monotonic()
        with open(args.input, 'r') as f:
            input_data = json.load(f)
        logger.info(f"Input data: {input_data}")
        logger.info(f"TIMING: Reading input JSON took {time.monotonic() - t_io_start:.4f}s.")

        query = input_data.get("query")
        if not query:
            raise ValueError("Input JSON must contain a 'query' field.")

        collection = input_data.get("collection", "default_rag_collection")
        qdrant_host_url = input_data.get("qdrant_host", "http://host.docker.internal:6333")
        top_k_results = int(input_data.get("top_k", 5))
        
        # Ensure qdrant_host_url has a scheme
        if not qdrant_host_url.startswith(("http://", "https://")):
            qdrant_host_url = f"http://{qdrant_host_url}"
            logger.info(f"Corrected Qdrant URL to: {qdrant_host_url}")

        # 1. Get Embedding
        query_embedding_vector = get_embedding_with_timing(query)

        # 2. Connect to Qdrant
        qdrant_api_key_env = os.getenv("QDRANT_API_KEY")
        qdrant_client = connect_to_qdrant_with_timing(qdrant_host_url, api_key=qdrant_api_key_env)

        # 3. Search Qdrant
        retrieved_results = search_qdrant_with_timing(qdrant_client, collection, query_embedding_vector, top_k_results)

        # Prepare output
        output_payload = {
            "query": query,
            "collection": collection,
            "results": retrieved_results
        }
        
        t_io_start = time.monotonic()
        with open(args.output, 'w') as f:
            json.dump(output_payload, f, indent=2)
        logger.info(f"Output written to {args.output}.")
        logger.info(f"TIMING: Writing output JSON took {time.monotonic() - t_io_start:.4f}s.")

    except Exception as e: # pragma: no cover
        logger.error(f"Unhandled error in main: {e}", exc_info=True)
        error_output = {
            "error": str(e),
            "query": input_data.get("query", "N/A"),
            "details": f"{type(e).__name__}"
        }
        try:
            with open(args.output, 'w') as f:
                json.dump(error_output, f, indent=2)
            logger.info(f"Error output written to {args.output}.")
        except Exception as efw:
            logger.critical(f"Failed to write error output to {args.output}: {efw}")
            
    logger.info(f"TIMING: Retrieve module - TOTAL script execution time {time.monotonic() - script_overall_start_time:.4f}s.")

if __name__ == "__main__":
    setup_logging() # Ensure logging is set up even if main() isn't called (e.g. import error)
    ensure_cache_dir()
    logger.info("Retrieve module script started (as __main__).")
    main()
    logger.info("Retrieve module script finished (as __main__).")