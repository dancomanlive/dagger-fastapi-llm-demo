"""
Advanced text chunking tool with intelligent document structure awareness.
"""
import json
import dagger
from tools.core import get_tool_base, run_container_and_check, SCRIPTS_DIR

async def chunk_text(
    client: dagger.Client,
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
    respect_sections: bool = True,
    document_metadata: dict = None,
    image: str = "python:3.11-slim"
) -> str:
    """
    Chunk a document with overlap, respecting section boundaries when possible.
    
    Args:
        client: Dagger client
        text: Document text
        chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
        respect_sections: Whether to try to keep sections intact
        document_metadata: Document-level metadata to add to all chunks
        image: Container image to use
        
    Returns:
        JSON string with chunking results
    """
    # Get a base container configured with our scripts directory
    container = get_tool_base(
        client=client,
        image=image,
        scripts_dir=SCRIPTS_DIR,
    )
    
    # Prepare input data
    input_data = json.dumps({
        "text": text,
        "chunk_size": chunk_size,
        "overlap": overlap,
        "respect_sections": respect_sections,
        "document_metadata": document_metadata or {}
    })
    
    # Run the advanced_text_chunker.py script with the provided data
    return await run_container_and_check(
        container=container,
        args=["python", "scripts/advanced_text_chunker.py", input_data]
    )
