# rag_pipeline.py

"""
This code handles the creation of containerized Python environments for each module in the Retrieval-Augmented Generation (RAG) pipeline. The process includes:

1. Starting from a base Python image as the foundation for the container.
2. Setting up dependency caching to optimize and speed up image builds.
3. Installing module-specific dependencies listed in the module's requirements.txt file.
4. Creating isolated environments that include only the dependencies required for each module, ensuring minimal and consistent runtime environments.
5. Utilizing advanced container caching to avoid reinstalling dependencies on each run.
6. Maintaining persistent containers between requests to eliminate container creation overhead.
7. Running a component-level warmup during startup to initialize the system without executing a full query.
"""

import os
import time
import hashlib
import datetime
from dotenv import load_dotenv


# Debug print to confirm script execution
print("[DEBUG] rag_pipeline.py script started")

# Load environment variables
load_dotenv()

# Global caches
RESULT_QUERY_CACHE = {}
# Store hashes of requirements files instead of container objects
# This avoids issues with stale container references between requests
REQ_FILE_HASH_CACHE = {}
# Container persistence store
PERSISTENT_CONTAINERS = {}
# Store secrets with client
CLIENT_SECRETS = {}
# Warmup status
WARMUP_COMPLETE = False

async def get_or_build_deps_image(
    client,  # Standard Dagger Client object
    module_name: str,
    python_base_image: str = "python:3.11-slim",
    use_persistent: bool = True
):
    """
    Defines a Dagger container with dependencies.
    Uses requirement file hashing to let Dagger's built-in caching 
    handle dependency caching effectively.
    
    With use_persistent=True, maintains persistent container instances between requests.
    """
    # Check if we have a persistent container for this module
    if use_persistent and module_name in PERSISTENT_CONTAINERS:
        print(f"Using persistent container for {module_name}")
        return PERSISTENT_CONTAINERS[module_name]
    
    print(f"Defining dependency image structure for {module_name} using base {python_base_image}...")
    
    # Using the standard container creation approach
    base = client.container().from_(python_base_image)
    container_app_dir = "/app"

    # Create a more persistent cache that will survive across sessions
    # This uses Dagger's built-in caching system 
    pip_cache_volume = client.cache_volume("global-python-pip-cache")
    
    container_with_caches = (
        base
        .with_mounted_cache("/root/.cache/pip", pip_cache_volume)
        .with_env_variable("PYTHONUNBUFFERED", "1")
    )

    requirements_path_on_host = f"modules/{module_name}/requirements.txt"
    current_container_state = container_with_caches

    if os.path.exists(requirements_path_on_host):
        # Check if we've already calculated the hash for this requirements file
        if module_name in REQ_FILE_HASH_CACHE:
            req_hash = REQ_FILE_HASH_CACHE[module_name]
            print(f"Using cached requirements hash for {module_name}")
        else:
            # Get the requirements file contents for caching
            with open(requirements_path_on_host, "r") as f:
                req_content = f.read()
            
            # Create a cache key based on requirements content
            req_hash = hashlib.md5(req_content.encode()).hexdigest()
            # Store the hash for future use
            REQ_FILE_HASH_CACHE[module_name] = req_hash
        
        # Create a layer in the container that will be cached based on requirements
        req_file = client.host().file(requirements_path_on_host)
        current_container_state = (
            current_container_state
            .with_workdir(container_app_dir)
            # Add a cache marker that will cause Dagger to reuse this layer if requirements haven't changed
            .with_env_variable("REQ_HASH", req_hash)
            .with_mounted_file(f"{container_app_dir}/requirements.txt", req_file)
            .with_exec(["pip", "install", "--cache-dir", "/root/.cache/pip",
                      "-r", "requirements.txt", "-v"])
            .with_exec(["pip", "list"])
        )
        print(f"Pip install step defined for {module_name}.")
    else:
        current_container_state = current_container_state.with_workdir(container_app_dir)
        print(f"No requirements.txt found for {module_name} at {requirements_path_on_host}.")

    # Store the container reference if we're using persistence
    if use_persistent:
        PERSISTENT_CONTAINERS[module_name] = current_container_state
        print(f"Stored persistent container for {module_name}")

    return current_container_state

# Function to initialize all the persistent containers
async def initialize_persistent_containers(client):
    """
    Pre-initializes all required containers during app startup
    to avoid container creation overhead during request processing.
    """
    print("Initializing persistent containers...")
    start_time = time.time()
    
    # Initialize generate module container
    await get_or_build_deps_image(client, "generate", use_persistent=True)
    
    # Add other modules here as needed
    
    print(f"All persistent containers initialized in {time.time() - start_time:.2f}s")
    
    # Store OpenAI API key as a secret if available
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        print("Setting up OpenAI API key secret")
        # Create the secret with a consistent ID to avoid "not found" errors
        secret_id = "openai_api_key_for_generator"
        CLIENT_SECRETS[secret_id] = client.set_secret(secret_id, openai_api_key)
    
    return True

# warmup_pipeline function has been removed in favor of the more efficient warmup_components

async def warmup_components(client):
    """
    Initialize key components without running a full query.
    This pre-initializes the most time-consuming parts of the pipeline
    like container preparation, module loading, etc. without executing
    an actual RAG query.
    
    This function ensures all dependencies are fully installed and ready,
    so the first query can run quickly.
    """
    global WARMUP_COMPLETE
    
    if WARMUP_COMPLETE:
        print("Warmup already completed, skipping.")
        return True
    
    print("Running component-level warmup (no query execution)...")
    start_time = time.time()
    
    try:
        # Get our generator container and prepare it - this fully installs all dependencies
        print("Pre-initializing generator container...")
        generate_deps_container = await get_or_build_deps_image(client, "generate", use_persistent=True)
        
        # Use the host.directory pattern for the new API
        generate_code_dir = client.host().directory("modules/generate")
        
        # Environment variables
        retriever_service_url = os.getenv("RETRIEVER_SERVICE_URL", "http://retriever-service:8000")
        openai_api_key = os.getenv("OPENAI_API_KEY")

        # Define the container but don't execute anything
        processing_container_base = (
            generate_deps_container
            .with_env_variable("PYTHONUNBUFFERED", "1")
            .with_env_variable("RETRIEVER_SERVICE_URL", retriever_service_url)
            .with_env_variable("_EXPERIMENTAL_DAGGER_RUNNER_HOST", os.environ["_EXPERIMENTAL_DAGGER_RUNNER_HOST"])
            .with_workdir("/app")
            .with_directory("/app", generate_code_dir, exclude=["__pycache__", "*.pyc", ".env"])
        )

        # Set up secrets
        secret_id = "openai_api_key_for_generator"
        if openai_api_key:
            if secret_id in CLIENT_SECRETS:
                print("Using pre-created secret for OpenAI API key")
                openai_secret = CLIENT_SECRETS[secret_id]
            else:
                print("Creating new secret for OpenAI API key")
                openai_secret = client.set_secret(secret_id, openai_api_key)
                CLIENT_SECRETS[secret_id] = openai_secret
                
            processing_container_base = processing_container_base.with_secret_variable(
                "OPENAI_API_KEY", 
                openai_secret
            )
        
        # Run a more comprehensive warmup to ensure Python and all modules are loaded
        print("Warming up the Python runtime and imported modules...")
        warmup_exec = processing_container_base.with_exec([
            "python", "-c", """
import sys
import json
import requests
import os
import time

# Print environment information
print('Python environment ready, version:', sys.version)
print('Environment variables:', os.environ.get('RETRIEVER_SERVICE_URL'))

# Try to import key modules that will be used
try:
    from openai import OpenAI
    print('OpenAI module loaded successfully')
except Exception as e:
    print(f'OpenAI module import warning: {str(e)}')

# Pre-initialize common data structures
test_data = {'query': 'test', 'results': []}
json_test = json.dumps(test_data)
print(f'JSON test successful: {json_test}')

print('Warmup complete - runtime is ready for queries')
"""
        ])
        
        # Get the output to ensure the command completes
        output = await warmup_exec.stdout()
        print(f"Detailed warmup output: {output}")
        
        # Make sure our container is fully cached and ready
        print("Caching container state for fast query execution...")
        PERSISTENT_CONTAINERS["generate"] = processing_container_base
        
        print(f"Component-level warmup completed in {time.time() - start_time:.2f}s")
        WARMUP_COMPLETE = True
        return True
        
    except Exception as e:
        print(f"Warning: Component warmup failed: {str(e)}")
        # Don't fail the startup process if warmup fails
        return False

async def run_rag_pipeline(client, query: str, collection: str = "default") -> str:
    start_time = time.time()

    # Check result cache first
    cache_key = f"{query}_{collection}"
    cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
    if cache_hash in RESULT_QUERY_CACHE:
        print(f"Cache hit for query (full result): {query}")
        return RESULT_QUERY_CACHE[cache_key]
    
    # Log cache status for debugging
    print(f"Cache miss. Processing new query: '{query}'")
    
    # Environment variables
    retriever_service_url = os.getenv("RETRIEVER_SERVICE_URL", "http://retriever-service:8000")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    # Get/Build Generator Image - use the persistent container if available
    print("Getting dependency container definition for generate module...")
    generate_deps_container = await get_or_build_deps_image(client, "generate", use_persistent=True)
    
    # Use the host.directory pattern for the new API
    generate_code_dir = client.host().directory("modules/generate")
    
    final_output_filename = "final_rag_output.json"
    container_app_dir = "/app"

    # Define and Run the Generator Container
    processing_container_base = (
        generate_deps_container
        .with_env_variable("PYTHONUNBUFFERED", "1")
        .with_env_variable("RETRIEVER_SERVICE_URL", retriever_service_url)
        .with_env_variable("_EXPERIMENTAL_DAGGER_RUNNER_HOST", os.environ["_EXPERIMENTAL_DAGGER_RUNNER_HOST"])
        .with_workdir(container_app_dir)
        .with_directory(container_app_dir, generate_code_dir, exclude=["__pycache__", "*.pyc", ".env"])
    )

    # Use client secrets if available, otherwise create a new one
    secret_id = "openai_api_key_for_generator"
    if openai_api_key:
        if secret_id in CLIENT_SECRETS:
            print("Using pre-created secret for OpenAI API key")
            openai_secret = CLIENT_SECRETS[secret_id]
        else:
            print("Creating new secret for OpenAI API key")
            openai_secret = client.set_secret(secret_id, openai_api_key)
            CLIENT_SECRETS[secret_id] = openai_secret
            
        processing_container_base = processing_container_base.with_secret_variable(
            "OPENAI_API_KEY", 
            openai_secret
        )

    # Add a timestamp to see when this execution happened
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    
    # Execute the generate script - add a cache marker to let Dagger know this is a
    # distinct execution and shouldn't reuse execution results from previous runs
    processing_container_exec = (
        processing_container_base
        .with_env_variable("EXECUTION_ID", timestamp)
        .with_exec([
            "python", "main.py",
            "--query", query,
            "--collection", collection,
            "--top_k", "5",
            "--output", final_output_filename
        ])
    )
    
    print(f"Starting RAG processing at {time.time() - start_time:.2f}s")
    
    # Get the final output file using the camelCase API method
    result_str = await processing_container_exec.file(f"{container_app_dir}/{final_output_filename}").contents()
    
    print(f"RAG processing completed. Total pipeline time: {time.time() - start_time:.2f}s")
    
    # Save in result cache
    RESULT_QUERY_CACHE[cache_key] = result_str
    
    return result_str

# This module is only meant to be imported, not run directly
# The CLI functionality has been removed since it's not being used