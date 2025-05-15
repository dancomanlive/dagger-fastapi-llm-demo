# A simple RAG pipeline using Dagger to orchestrate retrieval and generation steps.
# rag_pipeline.py
import json
import dagger
import os
import sys
import time
import hashlib
import platform
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create a simple cache in memory to avoid redundant queries for the *final result*
# This cache is for the entire pipeline's output, not for intermediate Dagger objects.
RESULT_QUERY_CACHE = {}

# Determine platform (Mac M1/M2 would be arm64)
PLATFORM = platform.machine()
IS_ARM = PLATFORM == "arm64"

async def get_or_build_deps_image(
    client: dagger.Client,
    module_name: str, # e.g., "retrieve" or "generate"
    python_base_image: str = "python:3.11-slim"
) -> dagger.Container:
    """
    Defines a Dagger container with dependencies installed from requirements.txt.
    Leverages Dagger CacheVolumes for pip's cache, Hugging Face model cache,
    and a generic /tmp/module_cache for custom script caching.
    Dagger's engine also caches layers resulting from pip install.
    """
    print(f"Defining dependency image structure for {module_name} using base {python_base_image}...")
    base = client.container().from_(python_base_image)
    container_app_dir = "/app" # Consistent app directory for workdir and code

    # --- Dagger CacheVolumes Definitions ---
    # 1. Pip cache (shared across all modules using this function)
    pip_cache_volume = client.cache_volume("global-python-pip-cache")
    pip_cache_dir_in_container = "/root/.cache/pip" # Common for root user in slim images

    # 2. Hugging Face cache (for models, datasets, etc., shared)
    hf_cache_volume = client.cache_volume("global-huggingface-cache")
    hf_cache_dir_in_container = "/root/.cache/huggingface" # Default HF cache location

    # 3. Generic temporary cache for module-specific script data (e.g., pickled embeddings)
    # Modules should write to /tmp/module_cache/ if they want to use this.
    script_temp_cache_volume = client.cache_volume("global-script-temp-cache")
    script_temp_cache_dir_in_container = "/tmp/module_cache"

    # --- Mount Caches and Set ENV Variables to the Base Container ---
    # These caches are available before and after pip install.
    container_with_caches = (
        base
        .with_mounted_cache(pip_cache_dir_in_container, pip_cache_volume)
        .with_mounted_cache(hf_cache_dir_in_container, hf_cache_volume)
        .with_mounted_cache(script_temp_cache_dir_in_container, script_temp_cache_volume)
        # Set environment variables to guide libraries to use these cache paths.
        # HF_HOME tells Hugging Face libraries (transformers, datasets, sentence-transformers etc.)
        # where to look for and store cached models/datasets.
        .with_env_variable("HF_HOME", hf_cache_dir_in_container)
        # Optionally, for sentence-transformers specifically if HF_HOME isn't enough,
        # though HF_HOME should generally cover it.
        # .with_env_variable("SENTENCE_TRANSFORMERS_HOME", f"{hf_cache_dir_in_container}/sentence_transformers")
    )

    # --- Pip Install Dependencies (if requirements.txt exists) ---
    requirements_path_on_host = f"modules/{module_name}/requirements.txt"
    requirements_filename_in_container = "requirements.txt"
    
    final_container = container_with_caches # Start with the cache-enabled container

    if os.path.exists(requirements_path_on_host):
        requirements_file_from_host = client.host().file(requirements_path_on_host)
        
        final_container = (
            container_with_caches # Use the one with caches already mounted
            .with_workdir(container_app_dir) # Set workdir before mounting/executing
            .with_mounted_file(f"{container_app_dir}/{requirements_filename_in_container}", requirements_file_from_host)
            .with_exec([
                "pip", "install",
                "--cache-dir", pip_cache_dir_in_container, # Tell pip to use this mounted directory
                "-r", requirements_filename_in_container
            ])
        )
        print(f"Pip install step defined for {module_name} using pip cache volume. Dagger will use its layer cache if inputs are identical.")
    else:
        # If no requirements, still set workdir for consistency if code is mounted later.
        final_container = container_with_caches.with_workdir(container_app_dir)
        print(f"No requirements.txt found for {module_name} at {requirements_path_on_host}, using base Python image with pre-mounted caches.")

    return final_container

async def run_rag_pipeline(query: str, collection: str = "default") -> str:
    # Generate a cache key from the query and collection for the *final result*
    cache_key = f"{query}_{collection}"
    cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
    
    # Check cache for the final result of a previous identical query
    if cache_hash in RESULT_QUERY_CACHE:
        print(f"Cache hit for query (full result): {query}")
        return RESULT_QUERY_CACHE[cache_hash]
    
    start_time = time.time()
    
    async with dagger.Connection(dagger.Config(
        log_output=sys.stderr,
    )) as client:
        # --- Prepare Dependency Images ---
        # These images will have pip, hf, and /tmp/module_cache volumes mounted
        # by get_or_build_deps_image.
        print("Getting dependency container definition for retrieve module...")
        retrieve_deps_container = await get_or_build_deps_image(client, "retrieve")
        
        print(f"Getting dependency container definition for generate module...")
        generate_deps_container = await get_or_build_deps_image(client, "generate")
        
        # --- Prepare Code Directories & Input Files ---
        # Consistent app directory for workdir and mounting code/files
        container_app_dir = "/app"

        retrieve_code_dir = client.host().directory("modules/retrieve")
        generate_code_dir = client.host().directory("modules/generate")

        qdrant_url_for_dagger = os.getenv("QDRANT_URL_FOR_DAGGER", "http://host.docker.internal:6333")
        
        retrieve_input = {
            "query": query,
            "collection": collection,
            "qdrant_host": qdrant_url_for_dagger,
            "top_k": 5
        }
        input_json_str = json.dumps(retrieve_input)
        # Use consistent input/output filenames for clarity within each step's context
        script_input_filename = "input.json"
        retrieve_output_filename = "retrieve_output.json"
        generate_output_filename = "generate_output.json"
        
        query_input_file = client.directory().with_new_file(script_input_filename, input_json_str).file(script_input_filename)

        # --- Retrieve Container ---
        # retrieve_deps_container already has CacheVolumes for pip, HF models, and /tmp/module_cache
        retrieve_container_base = (
            retrieve_deps_container # This container comes with pre-configured caches
            .with_workdir(container_app_dir) # Ensure workdir is set/inherited
            .with_directory(container_app_dir, retrieve_code_dir, exclude=["__pycache__", "*.pyc"])
            .with_mounted_file(f"{container_app_dir}/{script_input_filename}", query_input_file)
        )
        
        # Add secrets if they exist
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        if qdrant_api_key:
            print("QDRANT_API_KEY found, passing as secret to retrieve container.")
            qdrant_secret = client.set_secret("qdrant_api_key_secret", qdrant_api_key)
            retrieve_container_base = retrieve_container_base.with_secret_variable("QDRANT_API_KEY", qdrant_secret)
        
        retrieve_container_exec = retrieve_container_base.with_exec([
                "python", "main.py", # Assumes main.py is at the root of retrieve_code_dir
                "--input", script_input_filename,
                "--output", retrieve_output_filename
            ])

        print(f"Starting retrieve step at {time.time() - start_time:.2f}s")
        retrieve_output_file = retrieve_container_exec.file(f"{container_app_dir}/{retrieve_output_filename}")
        await retrieve_output_file.contents() # Evaluate to get timing for this step
        print(f"Retrieve step completed at {time.time() - start_time:.2f}s")

        # --- Generate Container ---
        # generate_deps_container also has the common CacheVolumes mounted.
        generate_container_base = (
            generate_deps_container # This container comes with pre-configured caches
            .with_workdir(container_app_dir) # Ensure workdir
            .with_directory(container_app_dir, generate_code_dir, exclude=["__pycache__", "*.pyc"])
            # Output of retrieve is input here, mounted with the same name 'script_input_filename'
            # as the generate script's main.py will expect an 'input.json'.
            .with_mounted_file(f"{container_app_dir}/{script_input_filename}", retrieve_output_file)
        )

        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            print("OPENAI_API_KEY found, passing as secret to generate container.")
            openai_secret = client.set_secret("openai_api_key_secret", openai_api_key)
            generate_container_base = generate_container_base.with_secret_variable("OPENAI_API_KEY", openai_secret)
        
        generate_container_exec = generate_container_base.with_exec([
                "python", "main.py",
                "--input", script_input_filename, # Script reads the mounted retrieve_output.json as its input
                "--output", generate_output_filename
            ])

        print(f"Starting generate step at {time.time() - start_time:.2f}s")
        final_result_file = generate_container_exec.file(f"{container_app_dir}/{generate_output_filename}")
        result_str = await final_result_file.contents()
        print(f"Generate step completed. Total pipeline time: {time.time() - start_time:.2f}s")
        
        RESULT_QUERY_CACHE[cache_hash] = result_str
        return result_str