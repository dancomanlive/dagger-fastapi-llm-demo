# modules/generate/main.py
import json
import argparse
import logging
import os # For OPENAI_API_KEY, though not used in this version's logic

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    logger.info("Generate module started")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to the input JSON file from the retrieve step.")
    parser.add_argument("--output", default="generate_output.json", help="Path to save the final JSON output.")
    args = parser.parse_args()

    # Check for API keys if an LLM were to be used (good practice for future extension)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        logger.info("OPENAI_API_KEY found in environment (though not used by current template generation).")
    else:
        logger.info("OPENAI_API_KEY not found (not required for current template generation).")

    try:
        with open(args.input) as f:
            retriever_output_data = json.load(f)
        logger.info(f"Input data read successfully from {args.input}")

        # Extract data based on the new retriever output structure
        original_query = retriever_output_data.get("original_query", "")
        retrieved_contexts = retriever_output_data.get("retrieved_contexts", [])
        collection_used = retriever_output_data.get("collection_used", "N/A")

        logger.info(f"Processing query: '{original_query}' for collection: '{collection_used}'")
        logger.info(f"Received {len(retrieved_contexts)} contexts from retriever.")

        # The retriever already sorts by score, but an explicit sort here is harmless
        # and good practice if the upstream contract isn't guaranteed.
        if retrieved_contexts:
            retrieved_contexts.sort(key=lambda x: x.get("score", 0), reverse=True)
            logger.info(f"Top context score: {retrieved_contexts[0].get('score', 0):.4f}" if retrieved_contexts else "No contexts to score.")
        
        # Use the placeholder generation function
        generated_answer = generate_response_from_contexts(original_query, retrieved_contexts)
        
        final_output = {
            "query": original_query,
            "answer": generated_answer, # Changed "response" to "answer" for clarity
            "source_collection": collection_used,
            "num_contexts_received": len(retrieved_contexts),
            "contexts_used_in_generation": [
                {"id": ctx.get("id"), "score": ctx.get("score")} for ctx in retrieved_contexts[:3]
            ] if retrieved_contexts else []
        }

        with open(args.output, "w") as f:
            json.dump(final_output, f, indent=2)
        logger.info(f"Processing complete. Output written to {args.output}")
        
    except json.JSONDecodeError:
        error_message = f"Error: Could not decode JSON from input file {args.input}"
        logger.error(error_message, exc_info=True)
        with open(args.output, "w") as f:
            json.dump({"error": error_message, "query": "Unknown"}, f, indent=2)
        sys.exit(1) # Exit with error
    except Exception as e:
        error_message = f"An unexpected error occurred in the generate module: {str(e)}"
        logger.error(error_message, exc_info=True)
        # Try to get the query if possible, even in error states
        query_in_error = "Unknown"
        try:
            with open(args.input) as f_err: # Try to re-read for query
                data_err = json.load(f_err)
                query_in_error = data_err.get("original_query", "Unknown during error handling")
        except Exception:
            pass # Ignore if re-reading fails

        with open(args.output, "w") as f:
            json.dump({"error": error_message, "query": query_in_error}, f, indent=2)
        sys.exit(1) # Exit with error


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
        except:
            pass

        with open(output_path, "w") as f:
            json.dump({"error": f"Critical unhandled exception: {str(e)}", "query": "Unknown"}, f, indent=2)