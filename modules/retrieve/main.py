import json
import argparse
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import logging # Import logging
import time
import os
import pickle
import hashlib

# --- Global Variables (non-logging related) ---
MODULE_CACHE_DIR = "/tmp/module_cache"
_GLOBAL_MODEL = None

# --- Logger Setup (Delayed until script execution) ---
# It's often better to get the logger instance at the global level
# but configure its handlers and level when the script is actually run.
logger = logging.getLogger(__name__)


# --- Functions ---
def setup_logging():
    """Configures basic logging for the script."""
    # Configure logging here, so it's done once when the script starts
    # or when main() is called.
    # Check if handlers are already configured to avoid duplicate logs if imported
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s')
    else:
        logger.info("Logging already configured.")

def ensure_cache_dir():
    """Ensures the module cache directory exists."""
    os.makedirs(MODULE_CACHE_DIR, exist_ok=True)
    logger.info(f"Ensured cache directory exists: {MODULE_CACHE_DIR}")


def get_model():
    """Get the embedding model, loads it only once per script execution.
    Relies on HF_HOME environment variable (set by Dagger) for caching model downloads.
    """
    global _GLOBAL_MODEL
    if _GLOBAL_MODEL is not None:
        logger.info("Using cached model instance (from current script run).")
        return _GLOBAL_MODEL
    
    model_start_time = time.time()
    logger.info("Loading embedding model...")
    model_path_in_container = '/app/model'

    try:
        if os.path.exists(model_path_in_container) and os.listdir(model_path_in_container):
            logger.info(f"Attempting to load model from mounted directory: {model_path_in_container}")
            model = SentenceTransformer(model_path_in_container)
            logger.info(f"Successfully loaded model from {model_path_in_container}.")
        else:
            raise FileNotFoundError(f"Pre-mounted model directory {model_path_in_container} not found or is empty.")
    except Exception as e:
        logger.info(f"Could not load model from {model_path_in_container}: {str(e)}")
        default_model_name = 'paraphrase-MiniLM-L3-v2'
        logger.info(f"Attempting to download/load fallback model: '{default_model_name}'. "
                    "This will use HF_HOME for caching across Dagger runs.")
        model = SentenceTransformer(default_model_name)
        logger.info(f"Successfully downloaded/loaded fallback model '{default_model_name}'.")
        
    model_load_time = time.time() - model_start_time
    logger.info(f"Model loaded in {model_load_time:.2f}s.")
    
    _GLOBAL_MODEL = model
    return model

def get_embedding(query: str, use_cache=True) -> list:
    """Get embedding for a query with optional caching to MODULE_CACHE_DIR."""
    cache_file = None
    if use_cache:
        query_hash = hashlib.md5(query.encode()).hexdigest()
        cache_file = os.path.join(MODULE_CACHE_DIR, f'{query_hash}.pkl')
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    vector = pickle.load(f)
                logger.info(f"Using cached embedding from {cache_file} for query: {query[:50]}...")
                return vector
            except Exception as e:
                logger.warning(f"Error loading cached embedding from {cache_file}: {str(e)}. Will recompute.")
    
    model = get_model()
    embed_start_time = time.time()
    logger.info(f"Creating embedding for query: {query[:50]}...")
    vector = model.encode(query).tolist()
    embed_time = time.time() - embed_start_time
    logger.info(f"Query embedded in {embed_time:.2f}s.")
    
    if use_cache and cache_file:
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(vector, f)
            logger.info(f"Saved embedding to cache: {cache_file}")
        except Exception as e:
            logger.warning(f"Error saving embedding to {cache_file}: {str(e)}")
    
    return vector

def main():
    # Call setup functions at the beginning of main
    setup_logging() # Configure logging
    ensure_cache_dir() # Ensure cache directory is created

    parser = argparse.ArgumentParser(description="Retrieve relevant documents from Qdrant based on a query.")
    parser.add_argument("--input", required=True, help="Path to the input JSON file containing query details.")
    parser.add_argument("--output", default="output.json", help="Path to save the output JSON file.")
    args = parser.parse_args()

    total_start_time = time.time()
    logger.info(f"Retrieve module processing started for input: {args.input}, output: {args.output}")
    data = {} # Initialize data to ensure it's defined in broader scope for error handling

    try:
        with open(args.input) as f:
            data = json.load(f)
        logger.info(f"Input data read successfully from {args.input}: {data}")

        query = data.get("query")
        if not query:
            raise ValueError("Missing 'query' in input data.")
            
        collection = data.get("collection", "default_collection")
        qdrant_url_from_input = data.get("qdrant_host", "http://host.docker.internal:6333")
        top_k = int(data.get("top_k", 3))
        
        logger.info(f"Processing query: '{query}', Collection: '{collection}', Qdrant Host: '{qdrant_url_from_input}', Top-K: {top_k}")
        
        query_vector = get_embedding(query)

        qdrant_url = qdrant_url_from_input
        if not qdrant_url.startswith(("http://", "https://")):
            qdrant_url = f"http://{qdrant_url}"
            logger.info(f"Prepended http:// to Qdrant URL, now: {qdrant_url}")
        
        client = None
        connection_errors = []
        max_connection_retries = 3
        
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        if qdrant_api_key:
            logger.info("QDRANT_API_KEY found in environment variables.")
        else:
            logger.info("QDRANT_API_KEY not found in environment variables. Connecting without API key.")

        for attempt in range(max_connection_retries):
            try:
                logger.info(f"Attempting to connect to Qdrant at {qdrant_url} (attempt {attempt + 1}/{max_connection_retries})")
                client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=5.0)
                client.get_collections()
                logger.info(f"Successfully connected to Qdrant at {qdrant_url}.")
                break
            except Exception as e:
                error_msg = f"Connection attempt {attempt + 1} to {qdrant_url} failed: {type(e).__name__} - {str(e)}"
                logger.warning(error_msg)
                connection_errors.append(error_msg)
                
                if "host.docker.internal" in qdrant_url and attempt == 0:
                    fallback_qdrant_url = "http://localhost:6333"
                    logger.info(f"Trying fallback Qdrant URL: {fallback_qdrant_url}")
                    try:
                        client = QdrantClient(url=fallback_qdrant_url, api_key=qdrant_api_key, timeout=5.0)
                        client.get_collections()
                        logger.info(f"Successfully connected to Qdrant at fallback URL: {fallback_qdrant_url}.")
                        qdrant_url = fallback_qdrant_url
                        break
                    except Exception as fe:
                        error_msg_fb = f"Fallback connection to {fallback_qdrant_url} failed: {type(fe).__name__} - {str(fe)}"
                        logger.warning(error_msg_fb)
                        connection_errors.append(error_msg_fb)
                
                if client:
                    break
                
                if attempt < max_connection_retries - 1:
                    retry_delay = (attempt + 1) * 2
                    logger.info(f"Retrying Qdrant connection in {retry_delay} seconds...")
                    time.sleep(retry_delay)
        
        if client is None:
            raise ConnectionError(f"Failed to connect to Qdrant after {max_connection_retries} attempts. Errors: {'; '.join(connection_errors)}")
        
        logger.info(f"Searching collection: '{collection}' with top_k: {top_k}")
        search_start_time = time.time()
        search_results_list = []
        
        try:
            search_params = {
                "collection_name": collection,
                "query_vector": query_vector,
                "limit": top_k,
                "with_payload": True,
                "score_threshold": 0.2
            }
            logger.info(f"Qdrant search parameters: {search_params}")
            qdrant_search_results = client.search(**search_params)
            
            search_time_taken = time.time() - search_start_time
            logger.info(f"Qdrant search completed in {search_time_taken:.2f}s, found {len(qdrant_search_results)} raw results.")
            
            for hit in qdrant_search_results:
                payload = hit.payload if hit.payload else {}
                result_item = {
                    "id": str(hit.id),
                    "score": float(hit.score),
                    "text": payload.get("text", "N/A"),
                    "source": payload.get("source", "N/A")
                }
                search_results_list.append(result_item)
                logger.debug(f"Processed Qdrant hit: {result_item}")
        except Exception as e:
            logger.error(f"Error during Qdrant search in collection '{collection}': {type(e).__name__} - {str(e)}", exc_info=True)
            output_data = {"query": query, "collection": collection, "error": f"Qdrant search failed: {str(e)}", "results": []}
            with open(args.output, "w") as f:
                json.dump(output_data, f, indent=2)
            logger.info(f"Error output written to {args.output} due to search failure.")
            return

        output_data = {
            "query": query,
            "collection": collection,
            "results": search_results_list
        }

        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2)

        total_time_taken = time.time() - total_start_time
        logger.info(f"Successfully processed query. Output written to {args.output}. Total time: {total_time_taken:.2f}s.")
    
    except Exception as e:
        error_message = f"Unhandled error in retrieve module: {type(e).__name__} - {str(e)}"
        # Ensure logger is configured before trying to use it in a top-level except
        if not logger.handlers: setup_logging()
        logger.error(error_message, exc_info=True)
        error_output = {"error": error_message, "query": data.get("query", "N/A") if data else "N/A"}
        try:
            with open(args.output, "w") as f:
                json.dump(error_output, f, indent=2)
            logger.info(f"Error output written to {args.output}.")
        except Exception as efw:
             logger.error(f"Critical: Failed to write error output to {args.output}: {efw}")

if __name__ == "__main__":
    # Setup logging and cache dir when script is run directly
    setup_logging()
    ensure_cache_dir()
    logger.info("Retrieve module script execution started (as __main__).")
    main()
    logger.info("Retrieve module script execution finished (as __main__).")