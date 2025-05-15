import json
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Generate module started")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="output.json")
    args = parser.parse_args()

    try:
        with open(args.input) as f:
            data = json.load(f)

        logger.info("Input read")

        # Extract the original query
        query = data.get("query", "")
        logger.info(f"Processing query: '{query}'")

        # Remove augmented results and simplify processing
        results = data.get("results", [])
        
        # Sort results by score for better answer quality
        if results:
            results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        logger.info(f"Generating response from {len(results)} results")

        if results:
            response = f"Based on the retrieved information, here is the answer to your query: '{query}'\n\n"

            for i, result in enumerate(results[:3]):  # Use top 3 results
                text = result.get("text", "No text available")
                source = result.get("source", "Unknown")
                relevance_score = result.get("score", 0)

                logger.info(f"Using result {i+1} with relevance score: {relevance_score:.2f}")

                # Format with more concise output
                response += f"• Source ({source}): {text[:150]}...\n"

            response += "\nSummary: This information was retrieved and processed through a RAG pipeline."
        else:
            if "error" in data:
                response = f"Error during retrieval process: {data['error']}"
                logger.error(f"Error data received from retrieval module: {data['error']}")
            else:
                response = "No relevant information found to answer your query. Please try a different question or check if the knowledge base contains related information."
                logger.warning("No results found to generate a response from")

        final_output = {
            "query": query,
            "response": response
        }

        # Write the output file
        with open(args.output, "w") as f:
            json.dump(final_output, f, indent=2)

        logger.info("Processing done")
        logger.info(f"Output written to {args.output}")
        
    except Exception as e:
        error_message = f"Error: {str(e)}"
        logger.error(error_message, exc_info=True)
        with open(args.output, "w") as f:
            json.dump({"error": error_message}, f)

if __name__ == "__main__":
    try:
        logger.info("Generate module entry point")
        main()
    except Exception as e:
        logger.critical(f"Unhandled exception in generate module: {str(e)}", exc_info=True)
