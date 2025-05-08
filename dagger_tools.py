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

# Example usage:
# await hello_world(client, "Dan")
