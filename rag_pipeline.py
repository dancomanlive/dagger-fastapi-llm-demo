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

# Default model name, ensure this matches what your retrieve script expects/uses.
DEFAULT_EMBEDDING_MODEL_FOR_PRECACHE = "sentence-transformers/all-MiniLM-L6-v2" 

async def get_or_build_deps_image(
    client: dagger.Client,
    module_name: str, # e.g., "retrieve" or "generate"
    python_base_image: str = "python:3.11-slim"
) -> dagger.Container:
    """
    Defines a Dagger container with dependencies installed from requirements.txt.
    Leverages Dagger CacheVolumes for pip's cache, Hugging Face model cache,
    and a generic /tmp/module_cache for custom script caching.
    Optionally pre-caches embedding models for the 'retrieve' module.
    """
    print(f"Defining dependency image structure for {module_name} using base {python_base_image}...")
    # ... (base, container_app_dir, cache volume definitions remain the same) ...
    base = client.container().from_(python_base_image)
    container_app_dir = "/app" 

    pip_cache_volume = client.cache_volume("global-python-pip-cache")
    pip_cache_dir_in_container = "/root/.cache/pip" 

    hf_cache_volume = client.cache_volume("global-huggingface-cache")
    hf_cache_dir_in_container = "/root/.cache/huggingface"

    script_temp_cache_volume = client.cache_volume("global-script-temp-cache")
    script_temp_cache_dir_in_container = "/tmp/module_cache"

    container_with_caches = (
        base
        .with_mounted_cache(pip_cache_dir_in_container, pip_cache_volume)
        .with_mounted_cache(hf_cache_dir_in_container, hf_cache_volume)
        .with_mounted_cache(script_temp_cache_dir_in_container, script_temp_cache_volume)
        .with_env_variable("HF_HOME", hf_cache_dir_in_container)
    )

    requirements_path_on_host = f"modules/{module_name}/requirements.txt"
    requirements_filename_in_container = "requirements.txt"
    
    current_container_state = container_with_caches 

    if os.path.exists(requirements_path_on_host):
        requirements_file_from_host = client.host().file(requirements_path_on_host)
        
        current_container_state = (
            current_container_state # Use the one with caches already mounted
            .with_workdir(container_app_dir) 
            .with_mounted_file(f"{container_app_dir}/{requirements_filename_in_container}", requirements_file_from_host)
            .with_exec([
                "pip", "install",
                "--cache-dir", pip_cache_dir_in_container, 
                "-r", requirements_filename_in_container
            ])
        )
        print(f"Pip install step defined for {module_name} using pip cache volume.")

        # --- Model Pre-caching for 'retrieve' module ---
        if module_name == "retrieve":
            # This model name should match the one used by your retrieve script (or be configurable)
            model_to_precache = os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL_FOR_PRECACHE)
            print(f"Defining model pre-caching step for {module_name} with model {model_to_precache}...")
            
            # fastembed uses HF_HOME, which is already set and mounted.
            # This command will download model files to HF_HOME during image build if not present.
            # The import path for DefaultEmbedding assumes fastembed is installed as a top-level package
            # (which it is when qdrant-client[fastembed] is used).
            python_script_for_precache = (
                f'import os; from fastembed.embedding import DefaultEmbedding; '
                f'print(f"Pre-caching model: {{os.getenv(\'MODEL_NAME_FOR_PRECACHE\')}}"); '
                f'DefaultEmbedding(model_name=os.getenv("MODEL_NAME_FOR_PRECACHE"))'
            )

            current_container_state = (
                current_container_state
                .with_env_variable("MODEL_NAME_FOR_PRECACHE", model_to_precache)
                .with_exec(["python", "-c", python_script_for_precache])
            )
            print(f"Model pre-caching defined for {module_name}. Model files will be downloaded to HF_HOME if not already cached there.")
    else:
        current_container_state = current_container_state.with_workdir(container_app_dir)
        print(f"No requirements.txt found for {module_name} at {requirements_path_on_host}, using base Python image with pre-mounted caches.")

    return current_container_state

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