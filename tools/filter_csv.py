"""
CSV filtering tool - demonstrates usage of the core utilities.
"""
import dagger
from tools.core import get_tool_base, run_container_and_check, SCRIPTS_DIR

async def filter_csv(
    client: dagger.Client, 
    csv_data: str,
    column: str,
    value: str,
    image: str = "python:3.11-slim"
) -> str:
    """
    Filter CSV data in a container.
    
    Args:
        client: Dagger client
        csv_data: CSV content as a string
        column: Column name to filter on
        value: Value to filter for
        image: Container image to use
        
    Returns:
        JSON string with filtered data
    """
    # Get a base container configured with our scripts directory
    container = get_tool_base(
        client=client,
        image=image,
        scripts_dir=SCRIPTS_DIR,
    )
    
    # Create a container with the CSV data mounted as a temporary file
    container = container.with_new_file("/tmp/data.csv", csv_data)
    
    # Run the csv_filter.py script with the provided parameters
    return await run_container_and_check(
        container=container,
        args=["sh", "-c", f"cat /tmp/data.csv | python scripts/csv_filter.py {column} {value}"]
    )
