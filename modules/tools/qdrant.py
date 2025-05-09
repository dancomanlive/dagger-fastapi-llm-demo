"""
Dagger-based Qdrant connection testing tool.

This module provides functionality to test Qdrant connection using Dagger.
"""
import os
import dagger
from .core import get_tool_base, run_container_and_check, SCRIPTS_DIR

async def test_qdrant_connection(client: dagger.Client, qdrant_url: str = None):
    """
    Test the connection to Qdrant vector database.
    
    Args:
        client: Dagger client instance
        qdrant_url: URL to the Qdrant service (defaults to environment variable)
    
    Returns:
        The output from the test script
    """
    # Check if Qdrant is reachable from FastAPI container
    try:
        import socket
        host = "qdrant"
        socket.gethostbyname(host)
        print(f"Qdrant host '{host}' is resolvable from FastAPI container")
    except Exception as e:
        print(f"Could not resolve Qdrant host: {e}")
    
    # If no URL is provided, use default from environment
    if not qdrant_url:
        # For Dagger container, we need to use a reachable IP address
        # Use host.docker.internal which maps to the host machine in Docker for Mac/Windows
        qdrant_url = "http://host.docker.internal:6333"  # Override any environment variable
    
    
    # Get base container using the factory pattern
    container = get_tool_base(
        client=client,
        image="python:3.11-slim",
        scripts_dir=SCRIPTS_DIR,
    )
    
    # Configure the container with necessary setup
    container = (
        container
        .with_env_variable("QDRANT_URL", "http://host.docker.internal:6333")
        .with_exec(["pip", "install", "--no-cache-dir", "qdrant-client", "requests"])
    )
    
    # Run the script and return results
    output = await run_container_and_check(
        container, 
        ["python", "scripts/qdrant_test.py"]
    )
    
    # Return the output for debugging purposes
    return output
