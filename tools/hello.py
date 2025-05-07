"""
Hello world tool - demonstrates usage of the core utilities.
"""
import dagger
from tools.core import get_tool_base, run_container_and_check, SCRIPTS_DIR

async def hello_world(
    client: dagger.Client, 
    name: str = "World",
    image: str = "python:3.11-slim"
) -> str:
    """
    Run a hello world script in a container.
    
    Args:
        client: Dagger client
        name: Name to include in the greeting
        image: Container image to use
        
    Returns:
        The greeting message
    """
    # Get a base container configured with our scripts directory
    container = get_tool_base(
        client=client,
        image=image,
        scripts_dir=SCRIPTS_DIR,
    )
    
    # Run the hello_world.py script with the provided name
    return await run_container_and_check(
        container=container,
        args=["python", "scripts/hello_world.py", name]
    )
