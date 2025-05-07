"""
Process data tool - demonstrates usage of the core utilities.
"""
import dagger
from tools.core import get_tool_base, run_container_and_check, SCRIPTS_DIR

async def process_data(
    client: dagger.Client, 
    data: str,
    image: str = "python:3.11-slim"
) -> str:
    """
    Process data in a container.
    
    Args:
        client: Dagger client
        data: JSON string or text to process
        image: Container image to use
        
    Returns:
        The processed result
    """
    # Get a base container configured with our scripts directory
    container = get_tool_base(
        client=client,
        image=image,
        scripts_dir=SCRIPTS_DIR,
    )
    
    # Run the process_data.py script with the provided data
    return await run_container_and_check(
        container=container,
        args=["python", "scripts/process_data.py", data]
    )
