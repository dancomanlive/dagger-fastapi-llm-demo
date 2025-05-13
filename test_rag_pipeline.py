#!/usr/bin/env python3
"""
Test script for the RAG pipeline using FastAPI's Dagger implementation.
This script tests the complete RAG pipeline by sending a sample query 
and validating the response structure.
"""

import os
import sys
import json
import requests
import logging
from pprint import pprint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("rag-pipeline-test")

# Constants for testing
TEST_QUERY = "What is retrieval-augmented generation?"
TEST_COLLECTION = "default"
API_ENDPOINT = "http://127.0.0.1:8000/rag"

def run_rag_test():
    print("BBB")
    """Test the RAG pipeline with a sample query"""
    logger.info("Testing RAG pipeline with query: %s", TEST_QUERY)
    
    # Prepare the request payload
    payload = {
        "query": TEST_QUERY,
        "collection": TEST_COLLECTION
    }
    
    try:
        # Send the request to the RAG API endpoint
        logger.info("Sending request to %s", API_ENDPOINT)
        response = requests.post(API_ENDPOINT, json=payload)

        # Log raw response (even on error)
        logger.error("Raw response from server: %s", response.text)

        
        # Check if the request was successful
        response.raise_for_status()
        
        # Parse the JSON response
        result = response.json()
        
        # Validate the response structure
        validate_response(result)
        
        # Display the result
        logger.info("RAG pipeline response:")
        pprint(result)
        
        logger.info("RAG pipeline test completed successfully!")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error("Request error: %s", str(e))
        return False
    except json.JSONDecodeError:
        logger.error("Failed to parse response as JSON")
        return False
    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        return False

def validate_response(result):
    """Validate the structure of the RAG pipeline response"""
    required_keys = ["response", "sources"]
    
    for key in required_keys:
        if key not in result:
            raise ValueError(f"Response missing required key: {key}")
    
    if not isinstance(result["response"], str):
        raise ValueError("'response' field should be a string")
        
    if not isinstance(result["sources"], list):
        raise ValueError("'sources' field should be a list")
    
    logger.info("Response validation passed")

if __name__ == "__main__":
    success = run_rag_test()
    sys.exit(0 if success else 1)