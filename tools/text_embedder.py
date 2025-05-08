"""
Text embedding tool - generates vector embeddings for text chunks.
"""
import json
import dagger
from tools.core import get_tool_base, run_container_and_check, SCRIPTS_DIR

async def embed_text(
    client: dagger.Client,
    chunks: list,
    image: str = "python:3.11-slim"
) -> str:
    """
    Generate embeddings for text chunks in a container.
    
    Args:
        client: Dagger client
        chunks: List of text chunks to embed
        image: Container image to use
        
    Returns:
        JSON string with embedding results
    """
    # Get a base container configured with our scripts directory
    container = get_tool_base(
        client=client,
        image=image,
        scripts_dir=SCRIPTS_DIR,
    )
    
    # Add dependencies
    container = container.with_exec(["pip", "install", "numpy", "sentence-transformers"])
    
    # Add environment variables for API keys
    container = container.with_env_variable("OPENAI_API_KEY", "${OPENAI_API_KEY}")
    
    # Prepare input data
    input_data = json.dumps({
        "chunks": chunks
    })
    
    # Run the embed_text.py script with the provided data
    return await run_container_and_check(
        container=container,
        args=["python", "scripts/embed_text.py", input_data]
    )
