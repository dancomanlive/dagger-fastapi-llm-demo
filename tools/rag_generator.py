"""
RAG generator tool - generates responses using retrieved context with citations.
"""
import json
import dagger
from tools.core import get_tool_base, run_container_and_check, SCRIPTS_DIR

async def generate_rag_response_with_citations(
    client: dagger.Client,
    query: str,
    context_chunks: list,
    chunk_metadata: list = None,
    model: str = "gpt-4o-mini",
    image: str = "python:3.11-slim"
) -> str:
    """
    Generate a response using RAG with the provided context chunks, including citations.
    
    Args:
        client: Dagger client
        query: User query
        context_chunks: List of text chunks to use as context
        chunk_metadata: Metadata for each chunk (must match length of context_chunks)
        model: LLM model to use
        image: Container image to use
        
    Returns:
        JSON string with generation results including citations
    """
    # Get a base container configured with our scripts directory
    container = get_tool_base(
        client=client,
        image=image,
        scripts_dir=SCRIPTS_DIR,
    )
    
    # Add dependencies
    container = container.with_exec(["pip", "install", "openai"])
    
    # Add environment variables for OpenAI
    container = container.with_env_variable("OPENAI_API_KEY", "${OPENAI_API_KEY}")
    
    # Prepare input data
    input_data = json.dumps({
        "query": query,
        "context_chunks": context_chunks,
        "chunk_metadata": chunk_metadata or [],
        "model": model
    })
    
    # Run the rag_generator.py script with the provided data
    return await run_container_and_check(
        container=container,
        args=["python", "scripts/rag_generator.py", input_data]
    )
