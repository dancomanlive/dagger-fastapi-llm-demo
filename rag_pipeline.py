# rag_pipeline.py

"""
This code handles the creation of containerized Python environments for each module in the Retrieval-Augmented Generation (RAG) pipeline. The process includes:

1. Starting from a base Python image as the foundation for the container.
2. Setting up dependency caching to optimize and speed up image builds.
3. Installing module-specific dependencies listed in the module's requirements.txt file.
4. Creating isolated environments that include only the dependencies required for each module, ensuring minimal and consistent runtime environments.
"""

import os
import time
import hashlib
from dotenv import load_dotenv


# Debug print to confirm script execution
print("[DEBUG] rag_pipeline.py script started")

# Load environment variables
load_dotenv()

RESULT_QUERY_CACHE = {}

async def get_or_build_deps_image(
    client,  # Standard Dagger Client object
    module_name: str,
    python_base_image: str = "python:3.11-slim"
):
    """
    Defines a Dagger container with dependencies.
    Model caching is handled by the retriever service.
    """
    print(f"Defining dependency image structure for {module_name} using base {python_base_image}...")
    
    # Using the standard container creation approach
    base = client.container().from_(python_base_image)
    container_app_dir = "/app"

    pip_cache_volume = client.cache_volume("global-python-pip-cache")
    
    container_with_caches = (
        base
        .with_mounted_cache("/root/.cache/pip", pip_cache_volume)
        .with_env_variable("PYTHONUNBUFFERED", "1")
    )

    requirements_path_on_host = f"modules/{module_name}/requirements.txt"
    current_container_state = container_with_caches

    if os.path.exists(requirements_path_on_host):
        req_file = client.host().file(requirements_path_on_host)
        current_container_state = (
            current_container_state
            .with_workdir(container_app_dir)
            .with_mounted_file(f"{container_app_dir}/requirements.txt", req_file)
            .with_exec(["pip", "install", "--cache-dir", "/root/.cache/pip",
                      "-r", "requirements.txt", "-v"])
            .with_exec(["pip", "list"])
        )
        print(f"Pip install step defined for {module_name}.")
    else:
        current_container_state = current_container_state.with_workdir(container_app_dir)
        print(f"No requirements.txt found for {module_name} at {requirements_path_on_host}.")

    return current_container_state

async def run_rag_pipeline(client, query: str, collection: str = "default") -> str:  # Changed type hint
    start_time = time.time()

    cache_key = f"{query}_{collection}"
    cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
    if cache_hash in RESULT_QUERY_CACHE:
        print(f"Cache hit for query (full result): {query}")
        return RESULT_QUERY_CACHE[cache_key]

    # Environment variables
    retriever_service_url = os.getenv("RETRIEVER_SERVICE_URL", "http://retriever-service:8000")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    # Get/Build Generator Image
    print("Getting dependency container definition for generate module...")
    generate_deps_container = await get_or_build_deps_image(client, "generate")
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

    if openai_api_key:
        # Use the standard secret method for this version
        openai_secret = client.set_secret("openai_api_key_for_generator", openai_api_key)
        processing_container_base = processing_container_base.with_secret_variable(
            "OPENAI_API_KEY", 
            openai_secret
        )

    # Execute the generate script
    processing_container_exec = processing_container_base.with_exec([
        "python", "main.py",
        "--query", query,
        "--collection", collection,
        "--top_k", "5",
        "--output", final_output_filename
    ])
    
    print(f"Starting RAG processing at {time.time() - start_time:.2f}s")
    
    # Get the final output file using the camelCase API method
    result_str = await processing_container_exec.file(f"{container_app_dir}/{final_output_filename}").contents()
    
    print(f"RAG processing completed. Total pipeline time: {time.time() - start_time:.2f}s")
    
    RESULT_QUERY_CACHE[cache_key] = result_str
    return result_str

# This module is only meant to be imported, not run directly
# The CLI functionality has been removed since it's not being used