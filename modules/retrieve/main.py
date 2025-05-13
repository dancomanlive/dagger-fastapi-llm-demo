import json
import argparse
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="output.json")
    args = parser.parse_args()

    total_start_time = time.time()
    try:
        with open(args.input) as f:
            data = json.load(f)

        logger.info("Input read")

        # Extract parameters from input
        query = data["query"]
        collection = data.get("collection", "default")
        qdrant_url = data.get("qdrant_host", "qdrant:6333")
        top_k = data.get("top_k", 3)
        
        logger.info(f"Query: '{query}', Collection: '{collection}', Top-K: {top_k}")
        
        # Initialize embedding model
        model_start_time = time.time()
        logger.info("Loading embedding model...")
        model = SentenceTransformer('/app/model')
        model_load_time = time.time() - model_start_time
        logger.info(f"Model loaded in {model_load_time:.2f}s")

        # Embed the query
        embed_start_time = time.time()
        logger.info("Creating embedding for query")
        query_vector = model.encode(query).tolist()
        embed_time = time.time() - embed_start_time
        logger.info(f"Query embedded in {embed_time:.2f}s")
        
        # Connect to Qdrant
        logger.info(f"Connecting to Qdrant at {qdrant_url}")
        
        # Check if qdrant_url has http:// prefix, if not add it
        if not qdrant_url.startswith("http://") and not qdrant_url.startswith("https://"):
            qdrant_url = f"http://{qdrant_url}"
            logger.info(f"Updated Qdrant URL to {qdrant_url}")
        
        client = QdrantClient(url=qdrant_url)
        
        # Search for similar vectors
        logger.info(f"Searching collection: {collection} with top_k: {top_k}")
        search_results = client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=top_k
        )
        
        # Process results
        results = []
        for result in search_results:
            payload = result.payload
            text = payload.get("text", "")
            source = payload.get("source", "unknown")

            logger.info(f"Processing result from source: {source}")

            result_item = {
                "id": result.id,
                "score": float(result.score),
                "text": text,
                "source": source
            }
            results.append(result_item)

        output_data = {
            "query": query,
            "collection": collection,
            "results": results
        }

        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2)

        logger.info("Processing done")
        logger.info(f"Output written to {args.output}")
        logger.info(f"Total processing time: {time.time() - total_start_time:.2f}s")
    
    except Exception as e:
        error_message = f"Error: {str(e)}"
        logger.error(error_message, exc_info=True)
        with open(args.output, "w") as f:
            json.dump({"error": error_message}, f)

if __name__ == "__main__":
    logger.info("Retrieve module started")
    main()
