# modules/retrieve/main.py
import argparse
import json
import os
import sys
import time
from qdrant_client import QdrantClient, models

# This model name will be used by fastembed (via qdrant-client).
# Fastembed will download it to HF_HOME if not already present.
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# This is the field name in Qdrant payload assumed to hold the main text content.
# Align this with how you are ingesting data into Qdrant.
# The qdrant_demo used 'document'. If your setup uses 'text', change it here.
PAYLOAD_TEXT_FIELD_NAME = "document"


def load_input(input_path: str) -> dict:
    """Loads the input JSON from the given path."""
    try:
        with open(input_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {input_path}", file=sys.stderr)
        sys.exit(1)

def save_output(output_path: str, data: dict):
    """Saves the data as JSON to the given path."""
    try:
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Successfully wrote output to {output_path}")
    except IOError:
        print(f"Error: Could not write output to {output_path}", file=sys.stderr)
        sys.exit(1)

def get_qdrant_client(qdrant_host: str) -> QdrantClient:
    """
    Initializes and returns a QdrantClient.
    Uses QDRANT_API_KEY environment variable if set.
    """
    api_key = os.getenv("QDRANT_API_KEY")
    
    print(f"Attempting to connect to Qdrant at {qdrant_host}")
    client_args = {"url": qdrant_host, "prefer_grpc": True} # prefer_grpc for performance
    if api_key:
        print("Using QDRANT_API_KEY for authentication.")
        client_args["api_key"] = api_key
    else:
        print("No QDRANT_API_KEY found in environment. Connecting without API key.")
        
    client = QdrantClient(**client_args)
    
    try:
        client.health_check()
        print("Successfully connected to Qdrant and health check passed.")
    except Exception as e:
        print(f"Error connecting to Qdrant or health check failed: {e}", file=sys.stderr)
        # Consider appropriate error handling for your pipeline
    return client

def retrieve_documents(
    client: QdrantClient,
    collection_name: str,
    query_text: str,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    top_k: int = 5
) -> list:
    """
    Uses qdrant-client with fastembed to encode the query and retrieve documents from Qdrant.
    """
    print(f"Using fastembed via qdrant-client with model: {model_name} for query encoding.")
    # Model files are loaded from HF_HOME by fastembed (if cached, otherwise downloaded).
    # Dagger pipeline ensures HF_HOME is set to a mounted cache volume.
    
    print(f"Searching collection '{collection_name}' in Qdrant for top {top_k} results for query: '{query_text}'")
    search_start_time = time.time()
    try:
        # qdrant-client (with fastembed) handles embedding the query_text using the specified model_name.
        search_results = client.query_points(
            collection_name=collection_name,
            query=models.Document(
                text=query_text,
                model=model_name, # Instructs fastembed to use this model
            ),
            limit=top_k,
            with_payload=True  # We need the payload to get the document text
        )
    except Exception as e:
        print(f"Error during Qdrant search: {e}", file=sys.stderr)
        sys.exit(1) # Exit if search fails
    
    search_duration = time.time() - search_start_time
    print(f"Qdrant search took {search_duration:.4f} seconds.")
        
    retrieved_contexts = []
    # query_points returns a QueryResponse object; points are in search_results.points
    hits = search_results.points

    for hit in hits:
        payload_text = None
        if hit.payload:
            payload_text = hit.payload.get(PAYLOAD_TEXT_FIELD_NAME)
            if payload_text is None and PAYLOAD_TEXT_FIELD_NAME != "text": # Fallback to 'text' if primary field not found
                payload_text = hit.payload.get("text")


        if payload_text:
            retrieved_contexts.append({
                "id": str(hit.id), # hit.id can be int or UUID, ensure string for JSON
                "text": payload_text,
                "score": hit.score
            })
        else:
            print(f"Warning: Hit with ID {hit.id} has no '{PAYLOAD_TEXT_FIELD_NAME}' (or fallback 'text') field in payload, or payload is empty/missing.", file=sys.stderr)
            
    print(f"Retrieved {len(retrieved_contexts)} documents from Qdrant.")
    return retrieved_contexts

def main():
    parser = argparse.ArgumentParser(description="Retrieve documents from Qdrant based on a query using qdrant-client with fastembed.")
    parser.add_argument("--input", required=True, help="Path to the input JSON file.")
    parser.add_argument("--output", required=True, help="Path to save the output JSON file.")
    
    args = parser.parse_args()
    
    print(f"Starting retrieval script (using qdrant-client/fastembed). Input: {args.input}, Output: {args.output}")
    
    input_data = load_input(args.input)
    
    query = input_data.get("query")
    collection = input_data.get("collection", "default_collection") # Default collection name
    qdrant_host = input_data.get("qdrant_host")
    top_k = input_data.get("top_k", 5)
    embedding_model_name = input_data.get("embedding_model", DEFAULT_EMBEDDING_MODEL)

    if not query:
        print("Error: 'query' not found in input JSON.", file=sys.stderr)
        sys.exit(1)
    if not qdrant_host:
        print("Error: 'qdrant_host' not found in input JSON.", file=sys.stderr)
        sys.exit(1)

    qdrant_client = get_qdrant_client(qdrant_host)
    
    # Optional: If client instance is long-lived and model is always the same,
    # you could call client.set_model(embedding_model_name) once after initialization.
    # For this script, passing it via models.Document in query_points is sufficient.

    retrieved_docs = retrieve_documents(
        client=qdrant_client,
        collection_name=collection,
        query_text=query,
        model_name=embedding_model_name,
        top_k=top_k
    )
    
    output_data = {
        "original_query": query,
        "retrieved_contexts": retrieved_docs,
        "collection_used": collection 
    }
    
    save_output(args.output, output_data)
    print("Retrieval script (qdrant-client/fastembed) finished successfully.")

if __name__ == "__main__":
    main()