# modules/generate_module/main.py

"""
Functional response generation module for RAG system.

This module provides pure functions for:
1. Retrieving relevant context documents from the retrieval service
2. Generating responses using OpenAI's language model
3. Orchestrating the complete RAG pipeline
"""

import argparse
import logging
import os
import sys
import asyncio
from typing import List, Dict, Tuple, Optional
from functools import partial

import requests
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration constants
RETRIEVER_SERVICE_URL = os.getenv("RETRIEVER_SERVICE_URL", "http://host.docker.internal:8001")
REQUEST_TIMEOUT = 30
MAX_CONTEXTS = 3

def get_openai_api_key():
    """Get OpenAI API key at runtime"""
    return os.getenv("OPENAI_API_KEY")


# Pure functions for data transformation
def combine_contexts(contexts: List[Dict], max_contexts: int = MAX_CONTEXTS) -> str:
    """
    Combine context documents into a single text string.
    
    Args:
        contexts: List of context documents
        max_contexts: Maximum number of contexts to include
        
    Returns:
        Combined context text
    """
    if not contexts:
        return ""
    
    return "\n".join([
        ctx.get("text", "No text available.") 
        for ctx in contexts[:max_contexts]
    ])


def create_chat_messages(query: str, context_text: str) -> List[Dict[str, str]]:
    """
    Create OpenAI chat messages from query and context.
    
    Args:
        query: User's question
        context_text: Combined context text
        
    Returns:
        List of message dictionaries for OpenAI API
    """
    return [
        {
            "role": "system", 
            "content": "You are a helpful assistant that answers questions based on the provided context. If the question is not related to the context, say 'I don't know'."
        },
        {
            "role": "user", 
            "content": f"Query: {query}\n\nRetrieved Contexts:\n{context_text}\n\nGenerate a concise, fluent answer."
        }
    ]


def create_retrieval_payload(query: str, collection: str, top_k: int) -> Dict[str, any]:
    """
    Create payload for retrieval service request.
    
    Args:
        query: User's question
        collection: Collection name
        top_k: Number of results to retrieve
        
    Returns:
        Request payload dictionary
    """
    return {
        "query": query,
        "collection": collection,
        "top_k": top_k
    }


def extract_contexts_from_response(response_data: Dict) -> List[Dict]:
    """
    Extract contexts from retrieval service response.
    
    Args:
        response_data: JSON response from retrieval service
        
    Returns:
        List of context documents
    """
    return response_data.get("retrieved_contexts", [])


def validate_config() -> Tuple[bool, Optional[str]]:
    """
    Validate required configuration.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    openai_api_key = get_openai_api_key()
    if not openai_api_key:
        return False, "OPENAI_API_KEY environment variable is not set"
    
    if not RETRIEVER_SERVICE_URL:
        return False, "RETRIEVER_SERVICE_URL environment variable is not set"
    
    return True, None


# IO functions
def make_retrieval_request(url: str, payload: Dict, timeout: int = REQUEST_TIMEOUT) -> Dict:
    """
    Make HTTP request to retrieval service.
    
    Args:
        url: Service URL
        payload: Request payload
        timeout: Request timeout in seconds
        
    Returns:
        Response data dictionary
        
    Raises:
        Exception: If request fails
    """
    try:
        logger.info(f"Making retrieval request to {url}")
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.Timeout:
        logger.error("Timeout calling retriever service")
        raise Exception("Retrieval service timeout")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling retriever service: {e}")
        raise Exception(f"Retrieval request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during retrieval: {e}")
        raise


async def call_openai_api(client: AsyncOpenAI, messages: List[Dict]) -> str:
    """
    Call OpenAI API to generate response.
    
    Args:
        client: OpenAI client instance
        messages: Chat messages
        
    Returns:
        Generated response text
        
    Raises:
        Exception: If API call fails
    """
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"Error generating response with OpenAI: {e}")
        raise


# Core business logic functions
def retrieve_contexts(query: str, collection: str = "default", top_k: int = 5) -> List[Dict]:
    """
    Retrieve contexts from the retrieval service.
    
    Args:
        query: User's question
        collection: Collection name
        top_k: Number of contexts to retrieve
        
    Returns:
        List of retrieved contexts
        
    Raises:
        Exception: If retrieval fails
    """
    url = f"{RETRIEVER_SERVICE_URL.rstrip('/')}/retrieve"
    payload = create_retrieval_payload(query, collection, top_k)
    
    response_data = make_retrieval_request(url, payload)
    contexts = extract_contexts_from_response(response_data)
    
    logger.info(f"Retrieved {len(contexts)} contexts for query: {query}")
    return contexts


async def generate_response_from_contexts(query: str, contexts: List[Dict]) -> str:
    """
    Generate response using OpenAI based on query and contexts.
    
    Args:
        query: User's question
        contexts: Retrieved context documents
        
    Returns:
        Generated response text
    """
    if not contexts:
        logger.warning("No contexts provided for response generation")
        return "No relevant information found to answer your query."
    
    # Transform data through pure functions
    context_text = combine_contexts(contexts)
    messages = create_chat_messages(query, context_text)
    
    # Make API call
    openai_api_key = get_openai_api_key()
    client = AsyncOpenAI(api_key=openai_api_key)
    response = await call_openai_api(client, messages)
    
    logger.info(f"Response generated successfully for query: {query}")
    return response


# Main pipeline function
async def generate_rag_response(query: str, collection: str = "default", top_k: int = 5) -> str:
    """
    Complete RAG pipeline: retrieve contexts and generate response.
    
    Args:
        query: User's question
        collection: Collection name
        top_k: Number of contexts to retrieve
        
    Returns:
        Generated response text
    """
    try:
        # Retrieve contexts
        contexts = retrieve_contexts(query, collection, top_k)
        
        # Generate response
        response = await generate_response_from_contexts(query, contexts)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in RAG pipeline: {e}")
        return f"Error generating response: {str(e)}"


# Utility functions
def parse_arguments() -> argparse.Namespace:
    """Parse and return command line arguments."""
    parser = argparse.ArgumentParser(description="Generate RAG response for user query")
    parser.add_argument("--query", required=True, help="The user's query")
    parser.add_argument("--collection", default="default", help="Qdrant collection name")
    parser.add_argument("--top_k", type=int, default=5, help="Top K results to fetch")
    return parser.parse_args()


def handle_error_and_exit(error_msg: str, exit_code: int = 1) -> None:
    """Handle error logging and program exit."""
    logger.error(error_msg)
    print(f"Error: {error_msg}")
    sys.exit(exit_code)


# Main execution
async def main():
    """Main entry point with functional composition."""
    try:
        # Parse arguments
        args = parse_arguments()
        
        logger.info(f"Processing query: '{args.query}' from collection: '{args.collection}'")
        
        # Validate configuration
        is_valid, error_msg = validate_config()
        if not is_valid:
            handle_error_and_exit(error_msg)
        
        # Execute RAG pipeline
        answer = await generate_rag_response(args.query, args.collection, args.top_k)
        
        # Output result
        print(answer)
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Critical error in main: {e}", exc_info=True)
        handle_error_and_exit(f"Critical error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())