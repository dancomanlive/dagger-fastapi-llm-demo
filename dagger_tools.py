"""Functional approach to Dagger containers for direct SDK use"""
import logging
import dagger
import os

logger = logging.getLogger(__name__)

# Get the absolute path to the scripts directory
SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")

async def run_container(container: dagger.Container) -> str:
    """Execute a container and return its stdout as a string"""
    try:
        output = await container.stdout()
        return output.strip()
    except Exception as e:
        logger.exception(f"Error running container: {str(e)}")
        raise

def hello_world_container(client: dagger.Client, name: str = "World") -> dagger.Container:
    """Create a hello world container that returns a greeting with the provided name
    
    Args:
        client: Dagger client instance
        name: Name to include in the greeting
        
    Returns:
        A configured container ready to execute
    """
    return client.container().from_("python:3.11-slim") \
        .with_exec(["pip", "install", "--upgrade", "pip"]) \
        .with_exec(["pip", "install", "dagger-io==0.18.5"]) \
        .with_mounted_directory("/scripts", client.host().directory(SCRIPTS_DIR)) \
        .with_workdir("/scripts") \
        .with_exec(["python", "hello_world.py", name])

async def hello_world(client: dagger.Client, name: str = "World") -> str:
    """Convenience function that creates and runs the hello world container
    
    Args:
        client: Dagger client instance
        name: Name to include in the greeting
        
    Returns:
        The greeting message
    """
    container = hello_world_container(client, name)
    return await run_container(container)

def echo_container(client: dagger.Client, text: str) -> dagger.Container:
    """Create a container that echoes the provided text
    
    Args:
        client: Dagger client instance
        text: Text to echo
        
    Returns:
        A configured container ready to execute
    """
    # We'll use a Python container with our echo script instead of Alpine
    return client.container().from_("python:3.11-slim") \
        .with_mounted_directory("/scripts", client.host().directory(SCRIPTS_DIR)) \
        .with_workdir("/scripts") \
        .with_exec(["python", "echo.py", text])

async def echo(client: dagger.Client, text: str) -> str:
    """Convenience function that creates and runs the echo container
    
    Args:
        client: Dagger client instance
        text: Text to echo
        
    Returns:
        The echoed text
    """
    container = echo_container(client, text)
    return await run_container(container)

def process_data_container(client: dagger.Client, data: str) -> dagger.Container:
    """Create a container that processes data using the process_data.py script
    
    Args:
        client: Dagger client instance
        data: JSON string or text to process
        
    Returns:
        A configured container ready to execute
    """
    return client.container().from_("python:3.11-slim") \
        .with_mounted_directory("/scripts", client.host().directory(SCRIPTS_DIR)) \
        .with_workdir("/scripts") \
        .with_exec(["python", "process_data.py", data])

async def process_data(client: dagger.Client, data: str) -> str:
    """Convenience function that processes data in a container
    
    Args:
        client: Dagger client instance
        data: JSON string or text to process
        
    Returns:
        The processed result
    """
    container = process_data_container(client, data)
    return await run_container(container)

def text_analyzer_container(client: dagger.Client, text: str) -> dagger.Container:
    """Create a container that analyzes text using the text_analyzer.py script
    
    Args:
        client: Dagger client instance
        text: Text to analyze
        
    Returns:
        A configured container ready to execute
    """
    return client.container().from_("python:3.11-slim") \
        .with_mounted_directory("/scripts", client.host().directory(SCRIPTS_DIR)) \
        .with_workdir("/scripts") \
        .with_exec(["python", "text_analyzer.py", text])

async def analyze_text(client: dagger.Client, text: str) -> str:
    """Convenience function that analyzes text in a container
    
    Args:
        client: Dagger client instance
        text: Text to analyze
        
    Returns:
        JSON string with text analysis
    """
    container = text_analyzer_container(client, text)
    return await run_container(container)

def csv_filter_container(client: dagger.Client, csv_data: str, column: str, value: str) -> dagger.Container:
    """Create a container that filters CSV data
    
    Args:
        client: Dagger client instance
        csv_data: CSV content as a string
        column: Column name to filter on
        value: Value to filter for
        
    Returns:
        A configured container ready to execute
    """
    # We'll create a temporary file with the CSV data and mount it into the container
    return client.container().from_("python:3.11-slim") \
        .with_mounted_directory("/scripts", client.host().directory(SCRIPTS_DIR)) \
        .with_workdir("/scripts") \
        .with_new_file("/tmp/data.csv", csv_data) \
        .with_exec(["sh", "-c", f"cat /tmp/data.csv | python csv_filter.py {column} {value}"])

async def filter_csv(client: dagger.Client, csv_data: str, column: str, value: str) -> str:
    """Convenience function that filters CSV data in a container
    
    Args:
        client: Dagger client instance
        csv_data: CSV content as a string
        column: Column name to filter on
        value: Value to filter for
        
    Returns:
        JSON string with filtered data
    """
    container = csv_filter_container(client, csv_data, column, value)
    return await run_container(container)

# Example usage:
# await hello_world(client, "Dan")
# await echo(client, "Hello from Dagger container")
# await process_data(client, '{"name": "dan", "message": "hello"}')  # Returns: {"NAME": "DAN", "MESSAGE": "HELLO"}
# await analyze_text(client, "This is a sample text for analysis. This sample contains repeated words.")
# await filter_csv(client, "name,age\\nDan,30\\nAnna,25", "age", "25")  # Returns: [{"name": "Anna", "age": 25}]
