# rag_pipeline_direct.py

"""
This code implements a Retrieval-Augmented Generation (RAG) pipeline without using Dagger containers.
Instead, it uses direct Python process execution, optimized for running inside Docker. The process includes:

1. Managing Python dependencies for modules
2. Installing module-specific requirements when needed in the global Python environment
3. Maintaining a cache of dependency status to avoid reinstallation
4. Running the RAG pipeline with the same workflow as the container-based approach
"""

import os
import sys
import time
import hashlib
import datetime
import subprocess
import json
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Debug print to confirm script execution
print("[DEBUG] rag_pipeline_direct.py script started")

# Load environment variables
load_dotenv()

# Global caches
RESULT_QUERY_CACHE = {}
# Store hashes of requirements files for dependency management
REQ_FILE_HASH_CACHE = {}
# Dependency management tracking
MODULE_DEPENDENCIES_INSTALLED = {}

# Base directory for any temp files
TMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tmp")

def ensure_tmp_dir_exists():
    """Create the base temporary directory if it doesn't exist."""
    os.makedirs(TMP_DIR, exist_ok=True)

def install_module_dependencies(module_name):
    """
    Installs dependencies for a module directly in the current Python environment.
    Uses requirement file hashing for dependency management.
    """
    # Check if we've already installed these dependencies
    if module_name in MODULE_DEPENDENCIES_INSTALLED:
        print(f"Dependencies for {module_name} already installed")
        return True
    
    print(f"Setting up dependencies for {module_name}...")
    
    # Ensure temporary directory exists
    ensure_tmp_dir_exists()
    
    requirements_path = os.path.join("modules", module_name, "requirements.txt")
    
    # Check if requirements file exists
    if not os.path.exists(requirements_path):
        print(f"No requirements.txt found for {module_name} at {requirements_path}")
        MODULE_DEPENDENCIES_INSTALLED[module_name] = True
        return True
    
    # Calculate hash of requirements file
    if module_name in REQ_FILE_HASH_CACHE:
        req_hash = REQ_FILE_HASH_CACHE[module_name]
        print(f"Using cached requirements hash for {module_name}")
    else:
        with open(requirements_path, "r") as f:
            req_content = f.read()
        req_hash = hashlib.md5(req_content.encode()).hexdigest()
        REQ_FILE_HASH_CACHE[module_name] = req_hash
    
    # Create a marker file to indicate installed dependencies
    hash_marker_file = os.path.join(TMP_DIR, f"{module_name}_deps_{req_hash[:8]}.installed")
    
    # Check if dependencies are already installed with this hash
    if os.path.exists(hash_marker_file):
        print(f"Dependencies for {module_name} already installed (hash marker exists)")
        MODULE_DEPENDENCIES_INSTALLED[module_name] = True
        return True
    
    # Remove any old marker files for this module
    for old_marker in Path(TMP_DIR).glob(f"{module_name}_deps_*.installed"):
        print(f"Removing outdated dependency marker: {old_marker}")
        old_marker.unlink()
    
    # Install dependencies
    print(f"Installing requirements for {module_name}...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", requirements_path, "-v"
        ])
        subprocess.check_call([sys.executable, "-m", "pip", "list"])
        print(f"Dependencies installed successfully for {module_name}")
        
        # Create marker file to indicate successful installation
        with open(hash_marker_file, "w") as f:
            f.write(f"Dependencies for {module_name} installed on {datetime.datetime.now()}")
            
        MODULE_DEPENDENCIES_INSTALLED[module_name] = True
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies for {module_name}: {str(e)}")
        MODULE_DEPENDENCIES_INSTALLED[module_name] = False
        return False

async def initialize_environments():
    """
    Pre-initializes all required dependencies during app startup
    to avoid dependency installation overhead during request processing.
    """
    print("Initializing module dependencies...")
    start_time = time.time()
    
    # Initialize generate module dependencies
    install_module_dependencies("generate")
    
    # Add other modules here as needed
    
    # Print timing information
    print(f"All dependencies initialized in {time.time() - start_time:.2f}s")
    return True

async def run_rag_pipeline(query: str, collection: str = "default") -> str:
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
    
    # Ensure dependencies for generate module are installed
    print("Ensuring dependencies for generate module...")
    install_module_dependencies("generate")
    
    # Path to generate module code
    generate_code_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules", "generate")
    
    # Output file for the generator results
    final_output_filename = "final_rag_output.json"
    output_path = os.path.join(generate_code_dir, final_output_filename)
    
    # Set up environment variables for the subprocess
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["RETRIEVER_SERVICE_URL"] = retriever_service_url
    
    # Add OpenAI API key if available
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        env["OPENAI_API_KEY"] = openai_api_key
    
    # Add a timestamp to see when this execution happened
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    env["EXECUTION_ID"] = timestamp
    
    # Command to run the generate script
    command = [
        sys.executable,  # Use the current Python interpreter
        os.path.join(generate_code_dir, "main.py"),
        "--query", query,
        "--collection", collection,
        "--top_k", "5",
        "--output", final_output_filename
    ]
    
    print(f"Starting RAG processing at {time.time() - start_time:.2f}s")
    print(f"Command: {' '.join(command)}")
    
    # Run the generate script
    try:
        process = subprocess.run(
            command,
            env=env,
            cwd=generate_code_dir,  # Set working directory to generate module
            capture_output=True,
            text=True,
            check=True
        )
        
        # Log the outputs
        if process.stdout:
            print(f"Generator output: {process.stdout}")
        if process.stderr:
            print(f"Generator errors: {process.stderr}")
        
        # Read the output file
        with open(output_path, "r") as f:
            result_str = f.read()
        
        print(f"RAG processing completed. Total pipeline time: {time.time() - start_time:.2f}s")
        
        # Save in result cache
        RESULT_QUERY_CACHE[cache_key] = result_str
        
        return result_str
    
    except subprocess.CalledProcessError as e:
        error_message = f"Error running RAG pipeline: {str(e)}\nOutput: {e.stdout}\nError: {e.stderr}"
        print(error_message)
        return json.dumps({"error": error_message})
    except Exception as e:
        error_message = f"Unexpected error running RAG pipeline: {str(e)}"
        print(error_message)
        return json.dumps({"error": error_message})

