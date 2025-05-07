"""
Text analysis tool - demonstrates usage of the core utilities.
"""
import dagger
from tools.core import get_tool_base, run_container_and_check, SCRIPTS_DIR

async def analyze_text(
    client: dagger.Client, 
    text: str,
    image: str = "python:3.11-slim"
) -> str:
    """
    Analyze text in a container.
    
    Args:
        client: Dagger client
        text: Text to analyze
        image: Container image to use
        
    Returns:
        JSON string with text analysis
    """
    # Get a base container configured with our scripts directory
    container = get_tool_base(
        client=client,
        image=image,
        scripts_dir=SCRIPTS_DIR,
    )
    
    # Run the text_analyzer.py script with the provided text
    return await run_container_and_check(
        container=container,
        args=["python", "scripts/text_analyzer.py", text]
    )
