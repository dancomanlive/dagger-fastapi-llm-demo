# rag_pipeline.py
import json
import dagger
import os
import sys
import time
import hashlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

RESULT_QUERY_CACHE = {}


async def get_or_build_deps_image(
    client: dagger.Client,
    module_name: str,
    python_base_image: str = "python:3.11-slim"
) -> dagger.Container:
    """
    Defines a Dagger container with dependencies.
    Model caching is now handled by the standalone retriever service.
    """
    print(f"Defining dependency image structure for {module_name} using base {python_base_image}...")
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
            .with_exec([
                "pip", "install", "--cache-dir", "/root/.cache/pip",
                "-r", "requirements.txt"
            ])
        )
        print(f"Pip install step defined for {module_name}.")
    else:
        current_container_state = current_container_state.with_workdir(container_app_dir)
        print(f"No requirements.txt found for {module_name} at {requirements_path_on_host}.")

    return current_container_state


async def run_rag_pipeline(query: str, collection: str = "default") -> str:
    start_time = time.time()

    cache_key = f"{query}_{collection}"
    cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
    if cache_hash in RESULT_QUERY_CACHE:
        print(f"Cache hit for query (full result): {query}")
        return RESULT_QUERY_CACHE[cache_hash]

    # URL of the independently running retriever service
    # Need to use host.docker.internal from Dagger containers to access services on host
    retriever_service_url = os.getenv("RETRIEVER_SERVICE_URL_FOR_DAGGER", "http://host.docker.internal:8001")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    async with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
        
        # --- Get/Build Generator Image (which now includes retriever call logic) ---
        print("Getting dependency container definition for generate module (now with integrated retrieval call)...")
        # The 'generate' module's requirements.txt now includes 'requests'
        generate_deps_container = await get_or_build_deps_image(client, "generate")
        generate_code_dir = client.host().directory("modules/generate")
        
        final_output_filename = "final_rag_output.json"
        container_app_dir = "/app" 

        # --- Define and Run the Refactored Generator Container ---
        # This container will run the script from modules/generate/main.py
        processing_container_base = (
            generate_deps_container
            .with_env_variable("PYTHONUNBUFFERED", "1")
            .with_env_variable("RETRIEVER_SERVICE_URL", retriever_service_url) # Pass URL to the script
            .with_workdir(container_app_dir)
            # Mount the entire 'generate' module code into the container
            .with_directory(container_app_dir, generate_code_dir, exclude=["__pycache__", "*.pyc", ".env"])
        )

        if openai_api_key:
            openai_secret = client.set_secret("openai_api_key_for_generator", openai_api_key)
            processing_container_base = processing_container_base.with_secret_variable("OPENAI_API_KEY", openai_secret)
        
        # Execute the refactored generate script
        # It now takes --query and --collection as direct arguments
        processing_container_exec = processing_container_base.with_exec([
            "python", "main.py",
            "--query", query,
            "--collection", collection,
            "--top_k", "5",
            "--output", final_output_filename
        ])
        
        print(f"Starting RAG processing (integrated retrieval+generation) at {time.time() - start_time:.2f}s")
        
        # Get the final output file
        final_result_file = processing_container_exec.file(f"{container_app_dir}/{final_output_filename}")
        result_str = await final_result_file.contents()
        
        print(f"RAG processing completed. Total pipeline time: {time.time() - start_time:.2f}s")
            
        RESULT_QUERY_CACHE[cache_hash] = result_str
        return result_str

# Main entry point for CLI execution
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rag_pipeline.py <query_string> [collection_name]")
        sys.exit(1)
    
    user_query = sys.argv[1]
    user_collection = sys.argv[2] if len(sys.argv) > 2 else "default"

    import asyncio
    try:
        final_answer = asyncio.run(run_rag_pipeline(query=user_query, collection=user_collection))
        print("\n--- Final RAG Pipeline Output ---")
        try:
            print(json.dumps(json.loads(final_answer), indent=2))
        except json.JSONDecodeError:
            print(final_answer) # Print as is if not valid JSON
    except dagger.DaggerError as e:
        # Attempt to print more detailed error information if available
        if hasattr(e, 'stderr') and e.stderr:
            print(f"Dagger specific error occurred. STDERR:\n{e.stderr}", file=sys.stderr)
        elif hasattr(e, 'stdout') and e.stdout: # Sometimes useful info is in stdout for exec errors
            print(f"Dagger specific error occurred. STDOUT:\n{e.stdout}", file=sys.stderr)
        else:
            print(f"Dagger specific error occurred: {e}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)