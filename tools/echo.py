"""
Echo tool - demonstrates usage of the core utilities.
"""
import dagger
from tools.core import get_tool_base, run_container_and_check, SCRIPTS_DIR

async def echo(
    client: dagger.Client, 
    text: str,
    image: str = "python:3.11-slim"
) -> str:
    """
    Echo text from a container.
    
    Args:
        client: Dagger client
        text: Text to echo
        image: Container image to use
        
    Returns:
        The echoed text
    """
    # Get a base container configured with our scripts directory
    container = get_tool_base(
        client=client,
        image=image,
        scripts_dir=SCRIPTS_DIR,
    )
    
    # Run the echo.py script with the provided text
    return await run_container_and_check(
        container=container,
        args=["python", "scripts/echo.py", text]
    )
