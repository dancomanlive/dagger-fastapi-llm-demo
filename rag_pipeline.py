# rag_pipeline.py
import json
import dagger
import os
import sys
import time
import hashlib
# platform import removed as it wasn't used
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

RESULT_QUERY_CACHE = {}
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# This is the field name in Qdrant payload that the retriever service expects to find text.
# Ensure this matches PAYLOAD_TEXT_FIELD_NAME in retriever_service/main.py and
# TEXT_FIELD_NAME_FOR_PAYLOAD in your init_qdrant.py script.
DEFAULT_PAYLOAD_TEXT_FIELD_NAME = "document"


async def get_or_build_deps_image(
    client: dagger.Client,
    module_name: str,
    python_base_image: str = "python:3.11-slim"
    # precache_model_name removed as it's not relevant here for this pattern
) -> dagger.Container:
    """
    Defines a Dagger container with dependencies.
    Model caching is now handled by the standalone retriever service.
    """
    print(f"Defining dependency image structure for {module_name} using base {python_base_image}...")
    base = client.container().from_(python_base_image)
    container_app_dir = "/app"

    pip_cache_volume = client.cache_volume("global-python-pip-cache")
    # HF_HOME cache not strictly needed for the generator unless it loads models too
    
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
    # embedding_model & payload_text_field are now configurations of the external service

    async with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
        
        # --- 1. Get/Build Generator Image ---
        print("Getting dependency container definition for generate module...")
        # No precaching needed for generator image itself unless it loads its own models
        generate_deps_container = await get_or_build_deps_image(client, "generate")
        generate_code_dir = client.host().directory("modules/generate")
        
        script_input_filename = "input.json" 
        generate_output_filename = "generate_output.json"
        container_app_dir = "/app" 

        # --- 2. Define the "Caller" Logic (to call the external retriever service) ---
        retrieve_payload = {
            "query": query,
            "collection": collection,
            "top_k": 5
        }
        
        # The caller script now uses the externally configured RETRIEVER_SERVICE_URL
        caller_script_content = f"""
import requests
import json
import sys
import os

# RETRIEVER_SERVICE_URL will be passed as an env var to this script's container
service_base_url = os.getenv("RETRIEVER_SERVICE_URL_FOR_CALLER", "{retriever_service_url}")
service_url = f"{{service_base_url}}/retrieve"
payload = {json.dumps(retrieve_payload)}
output_file = "{script_input_filename}" 

print(f"Caller script: Sending POST to {{service_url}} with payload: {{payload}}")
try:
    response = requests.post(service_url, json=payload, timeout=30) # Shorter timeout now expected
    response.raise_for_status()
    print(f"Caller script: Received response status {{response.status_code}} from external service")
    with open(output_file, 'w') as f_out:
        f_out.write(response.text)
    print("Caller script: Service response written to output file")
    sys.exit(0)
except requests.exceptions.Timeout:
    print(f"Caller script: Timeout calling retriever service at {{service_url}}", file=sys.stderr)
    error_output = json.dumps({{"error": "Timeout calling retriever service", "original_query": "{query}"}})
    with open(output_file, 'w') as f_out:
        f_out.write(error_output)
    sys.exit(1)
except requests.exceptions.RequestException as e:
    print(f"Caller script: Error calling retriever service at {{service_url}}: {{e}}", file=sys.stderr)
    error_output = json.dumps({{"error": f"Failed to call retriever service: {{str(e)}}", "original_query": "{query}"}})
    with open(output_file, 'w') as f_out:
        f_out.write(error_output)
    sys.exit(1)
except Exception as e:
    print(f"Caller script: Unexpected error: {{e}}", file=sys.stderr)
    error_output = json.dumps({{"error": f"Unexpected error in caller script: {{str(e)}}", "original_query": "{query}"}})
    with open(output_file, 'w') as f_out:
        f_out.write(error_output)
    sys.exit(1)
"""
        # This container will execute the caller script and then the generator
        # It no longer uses with_service_binding
        final_pipeline_runner = (
            generate_deps_container # Base image with 'requests' and 'generate' script deps
            .with_env_variable("PYTHONUNBUFFERED", "1")
            .with_env_variable("RETRIEVER_SERVICE_URL_FOR_CALLER", retriever_service_url) # Pass URL to script
            .with_workdir(container_app_dir)
            .with_new_file(f"{container_app_dir}/call_service.py", contents=caller_script_content)
            .with_directory(f"{container_app_dir}/generator_module_code", generate_code_dir, exclude=["__pycache__", "*.pyc", ".env"])
        )

        if openai_api_key:
            openai_secret = client.set_secret("openai_api_key_secret_for_generator", openai_api_key)
            final_pipeline_runner = final_pipeline_runner.with_secret_variable("OPENAI_API_KEY", openai_secret)
        
        # Step 2a: Execute the caller script
        print(f"Executing call to external retriever service at {time.time() - start_time:.2f}s")
        caller_execution = final_pipeline_runner.with_exec(["python", "call_service.py"])
        
        try:
            retrieved_data_file_contents = await caller_execution.file(f"{container_app_dir}/{script_input_filename}").contents()
            retrieved_data_as_dagger_file = client.directory().with_new_file(script_input_filename, retrieved_data_file_contents).file(script_input_filename)
            print("External retriever service call script completed. Output for generator prepared.")
        except dagger.ExecError as e:
            # Error handling for caller script
            stdout_content = e.stdout if hasattr(e, 'stdout') and e.stdout is not None else ""
            stderr_content = e.stderr if hasattr(e, 'stderr') and e.stderr is not None else ""
            exit_code = e.exit_code if hasattr(e, 'exit_code') else "unknown"
            print(f"Error executing the service caller script. Exit code: {exit_code}", file=sys.stderr)
            if stdout_content:
                print(f"Caller STDOUT:\n{stdout_content}", file=sys.stderr)
            if stderr_content:
                print(f"Caller STDERR:\n{stderr_content}", file=sys.stderr)
            
            # Since we can't access e.container, we'll create a fallback error message
            print("CRITICAL: Service caller script failed. Creating fallback error message.", file=sys.stderr)
            error_json_for_generator = json.dumps({
                "error": f"Retriever service call failed: {str(e)}",
                "original_query": query
            })
            retrieved_data_as_dagger_file = client.directory().with_new_file(script_input_filename, error_json_for_generator).file(script_input_filename)

        print(f"Call to external retrieve service completed at {time.time() - start_time:.2f}s")

        # Step 2b: Execute the generator script
        generate_main_py_path_in_container = f"{container_app_dir}/generator_module_code/main.py"
        
        generate_container_exec = (
            final_pipeline_runner 
            .with_mounted_file(f"{container_app_dir}/{script_input_filename}", retrieved_data_as_dagger_file)
            .with_exec([
                "python", generate_main_py_path_in_container, 
                "--input", script_input_filename, 
                "--output", generate_output_filename
            ])
        )
        
        print(f"Starting generate step at {time.time() - start_time:.2f}s")
        final_result_file = generate_container_exec.file(f"{container_app_dir}/{generate_output_filename}")
        result_str = await final_result_file.contents()
        print(f"Generate step completed. Total pipeline time: {time.time() - start_time:.2f}s")
            
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
        print(json.dumps(json.loads(final_answer), indent=2))
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