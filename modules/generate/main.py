# modules/generate/main.py
import json
import argparse
import logging
import os # For OPENAI_API_KEY and RETRIEVER_SERVICE_URL
import sys
import requests # For calling the retriever service
from dotenv import load_dotenv # Optional: for local development

# Load .env if your generator logic relies on it directly
# Dagger will pass secrets like OPENAI_API_KEY as env vars anyway
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration (from Environment Variables) ---
# URL of the independently running retriever service (passed by Dagger)
RETRIEVER_SERVICE_URL = os.getenv("RETRIEVER_SERVICE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # For generator

# --- FAKE LLM Call (Placeholder) ---
# In a real RAG pipeline, this function would interact with an LLM
# (e.g., OpenAI, a local Hugging Face model) to generate a more fluent answer.
# For this example, we'll stick to a template-based response from contexts.
def generate_response_from_contexts(query: str, contexts: list) -> str:
    """
    Generates a response based on the query and retrieved contexts.
    This is a simplified version. A real RAG would use an LLM here.
    """
    if not contexts:
        logger.warning("No contexts provided to generate_response_from_contexts.")
        return "No relevant information found to answer your query. Please try a different question or check if the knowledge base contains related information."

    response_parts = [f"Based on the retrieved information for your query: '{query}'\n"]
    
    # Using top 3 contexts as per original logic
    for i, context_item in enumerate(contexts[:3]):
        text = context_item.get("text", "No text available in this context.")
        # The new retriever output doesn't have a direct 'source' field per context item.
        # We could use the context 'id' or a placeholder.
        # For this example, let's use the context ID as a reference.
        context_id = context_item.get("id", "Unknown ID")
        relevance_score = context_item.get("score", 0)

        logger.info(f"Using context item (ID: {context_id}) with relevance score: {relevance_score:.4f}")
        
        # Limiting text length for display
        display_text = text[:250] + "..." if len(text) > 250 else text
        response_parts.append(f"\n--- Context {i+1} (Score: {relevance_score:.4f}, ID: {context_id}) ---\n{display_text}")

    response_parts.append("\n\nSummary: This information was retrieved and processed through a RAG pipeline. For a more comprehensive answer, this step would typically involve a Large Language Model.")
    return "\n".join(response_parts)

def main():
    parser = argparse.ArgumentParser(description="Retrieves contexts by calling a service and then generates a response.")
    # Arguments for the RAG task, previously split, now handled by this script
    parser.add_argument("--query", required=True, help="The user's query.")
    parser.add_argument("--collection", default="default", help="The Qdrant collection to query via the retriever service.")
    parser.add_argument("--top_k", type=int, default=5, help="Number of results for the retriever service to fetch.")
    parser.add_argument("--output", default="final_rag_output.json", help="Path to save the final RAG output JSON.")
    args = parser.parse_args()

    logger.info(f"Generate module (with integrated retrieval) started. Query: '{args.query}', Collection: '{args.collection}'")

    if not RETRIEVER_SERVICE_URL:
        logger.error("RETRIEVER_SERVICE_URL environment variable is not set. Cannot proceed.")
        final_output = {"query": args.query, "error": "Configuration error: Retriever service URL not set."}
        with open(args.output, "w") as f:
            json.dump(final_output, f, indent=2)
        sys.exit(1)

    # --- Step 1: Call Retriever Service ---
    retriever_payload = {
        "query": args.query,
        "collection": args.collection,
        "top_k": args.top_k
    }
    retrieved_data = None
    service_full_url = f"{RETRIEVER_SERVICE_URL}/retrieve"
    
    logger.info(f"Calling retriever service at {service_full_url} with payload: {retriever_payload}")
    try:
        response = requests.post(service_full_url, json=retriever_payload, timeout=30) # Timeout for the call
        response.raise_for_status() # Raise an exception for HTTP error codes (4xx or 5xx)
        retrieved_data = response.json() # Get the JSON response from the retriever
        logger.info(f"Successfully retrieved data from retriever service. Received {len(retrieved_data.get('retrieved_contexts', []))} contexts.")
    except requests.exceptions.Timeout:
        logger.error(f"Timeout calling retriever service at {service_full_url}")
        retrieved_data = {"error": "Timeout calling retriever service", "original_query": args.query}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling retriever service at {service_full_url}: {e}", exc_info=True)
        # Prepare an error structure similar to what the retriever might send on its own errors
        retrieved_data = {"error": f"Failed to call retriever service: {str(e)}", "original_query": args.query}
    except json.JSONDecodeError as e: # If response from retriever is not valid JSON
        logger.error(f"Failed to decode JSON response from retriever service: {e}", exc_info=True)
        retrieved_data = {"error": "Invalid JSON response from retriever service", "original_query": args.query}
    except Exception as e: # Catch-all for other unexpected errors during the call
        logger.error(f"Unexpected error calling retriever service: {e}", exc_info=True)
        retrieved_data = {"error": f"Unexpected error during retriever call: {str(e)}", "original_query": args.query}

    # --- Step 2: Generate Response (using the data fetched above) ---
    generated_answer = ""
    source_collection_info = args.collection # Default to requested collection
    num_contexts_for_gen = 0

    if retrieved_data and "error" not in retrieved_data:
        retrieved_contexts = retrieved_data.get("retrieved_contexts", [])
        source_collection_info = retrieved_data.get("collection_used", args.collection)
        num_contexts_for_gen = len(retrieved_contexts)

        logger.info(f"Proceeding to generation with {num_contexts_for_gen} contexts for query '{args.query}'.")
        generated_answer = generate_response_from_contexts(args.query, retrieved_contexts)
        
        final_output_payload = {
            "query": args.query,
            "answer": generated_answer,
            "source_collection": source_collection_info,
            "num_contexts_received_by_generator": num_contexts_for_gen
        }
    else: # An error occurred during retrieval or retrieved_data is None/empty or contains an error
        error_message = "No data from retriever or retriever reported an error."
        if retrieved_data and "error" in retrieved_data: # If retriever itself sent an error field
            error_message = retrieved_data["error"]
        logger.error(f"Cannot generate response for query '{args.query}' due to retriever error: {error_message}")
        final_output_payload = {
            "query": args.query,
            "error": f"Retrieval step failed: {error_message}",
            "answer": "Could not generate an answer due to an error in the retrieval process."
        }

    # --- Step 3: Write Final Output ---
    with open(args.output, "w") as f:
        json.dump(final_output_payload, f, indent=2)
    logger.info(f"Final RAG output written to {args.output}")


if __name__ == "__main__":
    try:
        logger.info("Generate module entry point")
        main()
    except SystemExit: # To allow sys.exit(1) to terminate cleanly
        pass
    except Exception as e:
        logger.critical(f"Unhandled exception at generate module top level: {str(e)}", exc_info=True)
        # Fallback error output if main() itself crashes before writing output
        output_path = "generate_output.json" # Default or try to get from args if possible
        # This part is tricky if arg parsing itself failed. For now, use default.
        try:
            parser_fallback = argparse.ArgumentParser()
            parser_fallback.add_argument("--output", default="generate_output.json")
            args_fallback, _ = parser_fallback.parse_known_args() # Parse known to avoid error on unknown args
            output_path = args_fallback.output
        except Exception:
            pass

        with open(output_path, "w") as f:
            json.dump({"error": f"Critical unhandled exception: {str(e)}", "query": "Unknown"}, f, indent=2)