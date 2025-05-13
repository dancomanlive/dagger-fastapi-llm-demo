import os
import logging
import asyncio
import json
import sys # For Dagger log_output
from functools import lru_cache
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import HTMLResponse # Only if you have an HTML page
import dagger
import requests
import docker # For startup check
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure DOCKERHUB_USERNAME is set
DOCKERHUB_USERNAME = os.getenv('DOCKERHUB_USERNAME')
if not DOCKERHUB_USERNAME:
    logger.error("DOCKERHUB_USERNAME environment variable is not set.")
    raise ValueError("DOCKERHUB_USERNAME environment variable is required.")

# --- Simplified Lifespan Context Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("RAG Pipeline application starting up...")
    try:
        docker_client = docker.from_env()
        docker_client.ping()
        logger.info("Docker is available.")
    except Exception as e:
        logger.error(f"Docker check failed: {e}. The RAG pipeline may not function correctly.")
    yield
    logger.info("RAG Pipeline application shutting down...")

# --- FastAPI App ---
app = FastAPI(
    title="Simplified RAG Pipeline with Dagger",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DockerHub Version Fetching ---
@lru_cache(maxsize=4)
def get_latest_version(image_name: str) -> str:
    url = f"https://hub.docker.com/v2/repositories/{DOCKERHUB_USERNAME}/{image_name}/tags/"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        tags_data = response.json().get('results', [])
        versions = sorted(
            [tag['name'] for tag in tags_data if tag['name'].startswith('v') and tag['name'][1:].replace('.', '').isdigit()],
            key=lambda v_str: [int(part) for part in v_str[1:].split('.')],
            reverse=True
        )
        if versions:
            logger.info(f"Latest version for {image_name}: {versions[0]}")
            return versions[0]
    except requests.RequestException as e:
        logger.warning(f"Error fetching latest version for {image_name} from DockerHub: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error parsing versions for {image_name}: {e}")
    logger.warning(f"Could not determine latest version for {image_name}, defaulting to 'latest'.")
    return 'latest'

# --- Simplified Wrapper Script for Container Execution (using /tmp for output) ---
WRAPPER_SCRIPT_CONTENT = """#!/bin/sh
set -e # Exit immediately if a command exits with a non-zero status.

INPUT_FILE="$1"
# Make output file path a fixed location within /tmp
OUTPUT_FILE="/tmp/script_output.json" # Python script will write here

# Ensure output directory exists (though /tmp usually does)
mkdir -p "$(dirname "$OUTPUT_FILE")"

echo "Wrapper: Running python main.py --input=${INPUT_FILE} --output=${OUTPUT_FILE}"
python -u main.py --input="${INPUT_FILE}" --output="${OUTPUT_FILE}"

# Check if the output file was created
if [ ! -f "${OUTPUT_FILE}" ]; then
  echo "Wrapper: Error! Output file '${OUTPUT_FILE}' not created by script." >&2
  # Create a fallback error JSON
  echo '{"error": "Script failed to produce an output file at expected location."}' > "${OUTPUT_FILE}"
  exit 1 # Signal failure
fi

echo "Wrapper: Script finished. Output at ${OUTPUT_FILE}"
"""

# --- Core RAG Pipeline Logic ---
async def run_rag_step(
    client: dagger.Client,
    step_name: str,
    image_name_suffix: str,
    input_payload_or_file: dagger.File | dict,
    wrapper_script_file: dagger.File
) -> dagger.File:
    step_version = get_latest_version(image_name_suffix)
    full_image_name = f"{DOCKERHUB_USERNAME}/{image_name_suffix}:{step_version}"
    logger.info(f"Executing RAG step: {step_name} using image {full_image_name}")

    # Define paths inside the container
    container_input_path = "/app_inputs/input.json" # Can be anywhere readable
    # The wrapper script now dictates the output path to be /tmp/script_output.json
    container_output_path_in_script = "/tmp/script_output.json"
    container_wrapper_path = "/app_scripts/wrapper.sh" # Script location

    container = (
        client.container()
        .from_(full_image_name)
        .with_mounted_file(container_wrapper_path, wrapper_script_file)
    )

    if isinstance(input_payload_or_file, dict):
        input_json_str = json.dumps(input_payload_or_file)
        input_file_obj = client.directory().with_new_file(f"input_{step_name}.json", input_json_str).file(f"input_{step_name}.json")
        container = container.with_mounted_file(container_input_path, input_file_obj)
    elif isinstance(input_payload_or_file, dagger.File):
        container = container.with_mounted_file(container_input_path, input_payload_or_file)
    else:
        raise TypeError("input_payload_or_file must be a dict or dagger.File")

    # The wrapper script takes the input path as an argument.
    # It internally decides the output path (/tmp/script_output.json).
    exec_container = container.with_exec(
        ["sh", container_wrapper_path, container_input_path] # Wrapper script now only needs input path
    )

    try:
        logger.info(f"[{step_name}] Awaiting sync...")
        # Force sync and then retrieve the specific output file
        # Dagger caches intermediate layers, so this is efficient.
        # We need to "re-evaluate" exec_container to get a Container object from which we can extract a file *after* execution.
        executed_container_state = await exec_container.sync() # Returns a Container after execution
        logger.info(f"[{step_name}] Sync completed. Retrieving output file: {container_output_path_in_script}")
        
        # Get the file from the state *after* execution
        output_file = executed_container_state.file(container_output_path_in_script)
        return output_file
    except dagger.ExecuteError as e:
        logger.error(f"[{step_name}] Dagger execution failed with exit code {e.exit_code}:")
        logger.error(f"[{step_name}] Stdout:\n{e.stdout}")
        logger.error(f"[{step_name}] Stderr:\n{e.stderr}")
        
        # Even on error, try to get the output file as the wrapper might have created a fallback.
        # We need to reference the *executed* container object that led to the error.
        # The 'e' object itself doesn't directly give us the container state for file extraction,
        # so we re-reference 'exec_container' which is the definition of the execution.
        # To get the file, we need to "evaluate" that part of the DAG again.
        try:
            logger.warning(f"[{step_name}] Attempting to retrieve output file '{container_output_path_in_script}' despite execution error...")
            # This is a bit tricky; we want the file state from the *failed* execution.
            # Dagger's error handling around file access post-ExecuteError can be subtle.
            # One way is to re-request the file from the original exec_container definition.
            # If the script *did* write the fallback, it should be there.
            error_output_file = exec_container.file(container_output_path_in_script)
            error_contents = await error_output_file.contents() # This might fail if the file doesn't exist at all
            logger.error(f"[{step_name}] Fallback output contents (if any): {error_contents}")
            raise HTTPException(
                status_code=500,
                detail={
                    "pipeline_step": step_name,
                    "error": f"Script execution failed (exit_code: {e.exit_code}).",
                    "script_output": json.loads(error_contents) if error_contents and error_contents.strip().startswith('{') else error_contents,
                    "stderr": e.stderr
                }
            )
        except dagger.QueryError as qe: # This can happen if the file path is invalid after exec error
            logger.error(f"[{step_name}] QueryError retrieving output file after execution error (file might not exist): {qe}")
            raise HTTPException(
                status_code=500,
                detail={
                    "pipeline_step": step_name,
                    "error": f"Script execution failed (exit_code: {e.exit_code}), and output file was not retrievable.",
                    "stderr": e.stderr,
                    "stdout": e.stdout
                }
            ) from e
        except Exception as file_ex: # Catch other potential errors during fallback file retrieval
            logger.error(f"[{step_name}] Could not retrieve output file after execution error: {file_ex}")
            raise HTTPException(
                status_code=500,
                detail={
                    "pipeline_step": step_name,
                    "error": f"Script execution failed (exit_code: {e.exit_code}), and output file was not retrievable.",
                    "stderr": e.stderr,
                    "stdout": e.stdout
                }
            ) from e
    except Exception as e:
        logger.error(f"[{step_name}] An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error in {step_name} step: {str(e)}") from e


async def run_rag_pipeline(query: str, collection: str = "default") -> str:
    logger.info(f"Starting RAG pipeline for query: '{query}', collection: '{collection}'")
    config = dagger.Config(log_output=sys.stderr if os.getenv("DEBUG_DAGGER") else None)

    async with dagger.Connection(config) as client:
        wrapper_script_file = client.directory().with_new_file("wrapper.sh", WRAPPER_SCRIPT_CONTENT).file("wrapper.sh")

        retrieve_input_payload = {
            "query": query,
            "collection": collection,
            "qdrant_host": "http://host.docker.internal:6333",
            "top_k": 5
        }
        retrieved_file = await run_rag_step(
            client, "retrieve", "retrieve", retrieve_input_payload, wrapper_script_file
        )
        # For logging/debugging, let's see what was retrieved
        # retrieved_contents = await retrieved_file.contents()
        # logger.info(f"Retrieve step output sample: {retrieved_contents[:200]}...")

        generated_file = await run_rag_step(
            client, "generate", "generate", retrieved_file, wrapper_script_file
        )
        
        final_result_contents = await generated_file.contents()
        logger.info("RAG pipeline finished successfully.")
        return final_result_contents

# --- Pydantic Model for Request Body ---
class RagRequest(BaseModel):
    query: str
    collection: str = "default"

# --- FastAPI Endpoints ---
@app.post("/rag")
async def process_rag_request(request: RagRequest):
    try:
        result_str = await run_rag_pipeline(request.query, request.collection)
        try:
            response_json = json.loads(result_str)
            return response_json
        except json.JSONDecodeError as json_err:
            logger.error(f"RAG pipeline returned non-JSON string: {result_str[:500]}... Error: {json_err}")
            raise HTTPException(status_code=500, detail="RAG pipeline returned invalid JSON.")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unhandled error in /rag endpoint")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {str(e)}")

@app.get("/")
async def read_root():
    return {"status": "ok", "message": "Simplified RAG Pipeline with Dagger is running"}