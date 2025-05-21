# modules/generate/main.py

"""
This code handles the orchestration of the response generation phase. The steps involved are:

1. Accept a user query as input.
2. Construct a request URL and send the query to a retrieval service.
3. Receive relevant context documents from the retrieval system.
4. Pass the retrieved documents along with the original query to OpenAI's language model.
5. Generate a response based on the query and contextual documents.
6. Return the final generated answer to the user and save it for future reference.
"""

import json
import argparse
import logging
import os
import sys
import requests
from dotenv import load_dotenv
import asyncio

from openai import AsyncOpenAI  # Add OpenAI import

# Load .env for local development
load_dotenv()

# Logger setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
RETRIEVER_SERVICE_URL = os.getenv("http://host.docker.internal:8001", "http://host.docker.internal:8001")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

async def generate_response_from_contexts(query: str, contexts: list) -> str:
    """
    Generate a response using OpenAI's API instead of Dagger's LLM primitive.
    """
    if not contexts:
        logger.warning("No contexts provided to generate_response_from_contexts.")
        return "No relevant information found to answer your query."

    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is not set.")
        return "Error generating response: OpenAI API key is missing."

    # Combine top 3 contexts
    context_text = "\n".join([c.get("text", "No text available.") for c in contexts[:3]])
    
    try:
        # Initialize OpenAI client
        openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # Create the messages for the chat completion
        messages = [
            {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context. If the question is not related to the context, say 'I don't know'."},
            {"role": "user", "content": f"Query: {query}\n\nRetrieved Contexts:\n{context_text}\n\nGenerate a concise, fluent answer."}
        ]
        
        # Call OpenAI API
        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",  # You can change this to your preferred model
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        result = response.choices[0].message.content.strip()
        logger.info(f"OpenAI response generated successfully for query: {query}")
        return result

    except Exception as e:
        logger.error(f"Error using OpenAI API: {str(e)}", exc_info=True)
        return f"Error generating response: {str(e)}"


async def main():
    parser = argparse.ArgumentParser(description="Call retriever and generate response.")
    parser.add_argument("--query", required=True, help="The user's query.")
    parser.add_argument("--collection", default="default", help="Qdrant collection name.")
    parser.add_argument("--top_k", type=int, default=5, help="Top K results to fetch.")
    parser.add_argument("--output", default="final_rag_output.json", help="Path to output JSON.")
    args = parser.parse_args()

    logger.info(f"Started. Query: '{args.query}', Collection: '{args.collection}'")

    

    if not RETRIEVER_SERVICE_URL:
        logger.error("RETRIEVER_SERVICE_URL is not set.")
        final_output = {
            "query": args.query,
            "error": "Configuration error: RETRIEVER_SERVICE_URL not set."
        }
        with open(args.output, "w") as f:
            json.dump(final_output, f, indent=2)
        sys.exit(1)

    # Call retriever
    retriever_payload = {
        "query": args.query,
        "collection": args.collection,
        "top_k": args.top_k
    }
    service_full_url = f"{RETRIEVER_SERVICE_URL}/retrieve"

    try:
        logger.info(f"Calling retriever at {service_full_url}")
        response = requests.post(service_full_url, json=retriever_payload, timeout=30)
        response.raise_for_status()
        retrieved_data = response.json()
        print(f"Retrieved data: {retrieved_data}")
    except requests.exceptions.Timeout:
        logger.error("Timeout calling retriever")
        retrieved_data = {"error": "Timeout", "original_query": args.query}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling retriever: {e}", exc_info=True)
        retrieved_data = {"error": f"Request failed: {str(e)}", "original_query": args.query}
    except json.JSONDecodeError:
        logger.error("Invalid JSON from retriever")
        retrieved_data = {"error": "Invalid JSON", "original_query": args.query}
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        retrieved_data = {"error": str(e), "original_query": args.query}

    # Generate answer
    if "error" not in retrieved_data:
        contexts = retrieved_data.get("retrieved_contexts", [])
        collection_used = retrieved_data.get("collection_used", args.collection)
        answer = await generate_response_from_contexts(args.query, contexts)
        final_output = {
            "query": args.query,
            "answer": answer,
            "source_collection": collection_used,
            "num_contexts_received_by_generator": len(contexts)
        }
    else:
        logger.error(f"Retrieval failed: {retrieved_data['error']}")
        final_output = {
            "query": args.query,
            "error": f"Retrieval failed: {retrieved_data['error']}",
            "answer": "Could not generate an answer due to retrieval failure."
        }

    # Write output
    with open(args.output, "w") as f:
        json.dump(final_output, f, indent=2)
    logger.info(f"Output written to {args.output}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except SystemExit:
        pass
    except Exception as e:
        logger.critical(f"Unhandled exception at top level: {str(e)}", exc_info=True)
        output_path = "generate_output.json"
        try:
            parser_fallback = argparse.ArgumentParser()
            parser_fallback.add_argument("--output", default="generate_output.json")
            args_fallback, _ = parser_fallback.parse_known_args()
            output_path = args_fallback.output
        except Exception:
            pass
        with open(output_path, "w") as f:
            json.dump({"error": f"Critical unhandled exception: {str(e)}", "query": "Unknown"}, f, indent=2)




