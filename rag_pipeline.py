# rag_pipeline.py

"""
Functional RAG pipeline implementation without Dagger containers.
Uses direct Python process execution optimized for Docker environments.

Key improvements:
- Captures stdout from the functional generate module
- Eliminates JSON file dependencies  
- Cleaner dependency management
- Better error handling and logging
"""

import os
import sys
import time
import hashlib
import datetime
import subprocess
import json
import asyncio
from pathlib import Path
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

# Debug print to confirm script execution
print("[DEBUG] rag_pipeline.py script started")

# Load environment variables
load_dotenv()

# Global caches
RESULT_CACHE: Dict[str, str] = {}
REQ_FILE_HASH_CACHE: Dict[str, str] = {}
MODULE_DEPENDENCIES_INSTALLED: Dict[str, bool] = {}

# Configuration
TMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tmp")
CACHE_TTL_SECONDS = 3600  # 1 hour cache TTL


# Utility functions
def ensure_tmp_dir_exists() -> None:
    """Create the base temporary directory if it doesn't exist."""
    os.makedirs(TMP_DIR, exist_ok=True)


def generate_cache_key(query: str, collection: str) -> str:
    """Generate a consistent cache key for query results."""
    cache_input = f"{query}_{collection}"
    return hashlib.md5(cache_input.encode()).hexdigest()


def is_cache_valid(cache_key: str) -> bool:
    """Check if cached result exists and is still valid."""
    # For now, simple existence check. Could add TTL logic here
    return cache_key in RESULT_CACHE


def calculate_requirements_hash(requirements_path: str) -> str:
    """Calculate MD5 hash of requirements file content."""
    try:
        with open(requirements_path, "r") as f:
            content = f.read()
        return hashlib.md5(content.encode()).hexdigest()
    except FileNotFoundError:
        return ""


def get_dependency_marker_path(module_name: str, req_hash: str) -> str:
    """Get path for dependency installation marker file."""
    return os.path.join(TMP_DIR, f"{module_name}_deps_{req_hash[:8]}.installed")


def cleanup_old_markers(module_name: str) -> None:
    """Remove outdated dependency marker files."""
    pattern = f"{module_name}_deps_*.installed"
    for old_marker in Path(TMP_DIR).glob(pattern):
        print(f"Removing outdated dependency marker: {old_marker}")
        old_marker.unlink()


# Dependency management functions
def check_requirements_file(module_name: str) -> Tuple[bool, str]:
    """
    Check if requirements file exists and get its path.
    
    Returns:
        Tuple of (exists, path)
    """
    requirements_path = os.path.join("modules", module_name, "requirements.txt")
    return os.path.exists(requirements_path), requirements_path


def install_pip_requirements(requirements_path: str, module_name: str) -> bool:
    """
    Install pip requirements from file.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"Installing requirements for {module_name}...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", requirements_path, "-q"
        ])
        print(f"Dependencies installed successfully for {module_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies for {module_name}: {str(e)}")
        return False


def create_dependency_marker(module_name: str, req_hash: str) -> None:
    """Create marker file indicating successful dependency installation."""
    marker_path = get_dependency_marker_path(module_name, req_hash)
    with open(marker_path, "w") as f:
        f.write(f"Dependencies for {module_name} installed on {datetime.datetime.now()}")


def install_module_dependencies(module_name: str) -> bool:
    """
    Install dependencies for a module in the current Python environment.
    Uses requirement file hashing for efficient dependency management.
    
    Args:
        module_name: Name of the module to install dependencies for
        
    Returns:
        True if dependencies are ready, False if installation failed
    """
    # Check if already processed
    if module_name in MODULE_DEPENDENCIES_INSTALLED:
        print(f"Dependencies for {module_name} already processed")
        return MODULE_DEPENDENCIES_INSTALLED[module_name]
    
    print(f"Setting up dependencies for {module_name}...")
    ensure_tmp_dir_exists()
    
    # Check requirements file
    req_exists, requirements_path = check_requirements_file(module_name)
    if not req_exists:
        print(f"No requirements.txt found for {module_name}")
        MODULE_DEPENDENCIES_INSTALLED[module_name] = True
        return True
    
    # Get or calculate requirements hash
    if module_name in REQ_FILE_HASH_CACHE:
        req_hash = REQ_FILE_HASH_CACHE[module_name]
    else:
        req_hash = calculate_requirements_hash(requirements_path)
        REQ_FILE_HASH_CACHE[module_name] = req_hash
    
    # Check if already installed with current hash
    marker_path = get_dependency_marker_path(module_name, req_hash)
    if os.path.exists(marker_path):
        print(f"Dependencies for {module_name} already installed (marker exists)")
        MODULE_DEPENDENCIES_INSTALLED[module_name] = True
        return True
    
    # Clean up old markers and install
    cleanup_old_markers(module_name)
    success = install_pip_requirements(requirements_path, module_name)
    
    if success:
        create_dependency_marker(module_name, req_hash)
    
    MODULE_DEPENDENCIES_INSTALLED[module_name] = success
    return success


# Environment setup
async def initialize_environments() -> bool:
    """
    Pre-initialize all required dependencies during app startup.
    
    Returns:
        True if initialization successful
    """
    print("Initializing module dependencies...")
    start_time = time.time()
    
    # Initialize generate module dependencies
    success = install_module_dependencies("generate")
    
    # Add other modules here as needed
    # success &= install_module_dependencies("retrieval")
    
    elapsed = time.time() - start_time
    print(f"Dependencies initialized in {elapsed:.2f}s - Success: {success}")
    return success


# Core pipeline functions
def build_generate_command(query: str, collection: str, generate_dir: str) -> list:
    """Build command to execute the generate module."""
    return [
        sys.executable,
        os.path.join(generate_dir, "main.py"),
        "--query", query,
        "--collection", collection,
        "--top_k", "5"
    ]


def setup_subprocess_environment() -> dict:
    """Set up environment variables for subprocess execution."""
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    # Set retriever service URL
    retriever_url = os.getenv("RETRIEVER_SERVICE_URL", "http://retriever-service:8000")
    env["RETRIEVER_SERVICE_URL"] = retriever_url
    
    # Add OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        env["OPENAI_API_KEY"] = openai_key
    
    # Add execution timestamp for debugging
    env["EXECUTION_ID"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    
    return env


def execute_generate_subprocess(command: list, env: dict, cwd: str) -> Tuple[bool, str, str]:
    """
    Execute the generate module subprocess.
    
    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        print(f"Executing command: {' '.join(command)}")
        
        process = subprocess.run(
            command,
            env=env,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
            timeout=120  # 2 minute timeout
        )
        
        return True, process.stdout.strip(), process.stderr
        
    except subprocess.TimeoutExpired:
        return False, "", "Process timed out after 2 minutes"
    except subprocess.CalledProcessError as e:
        error_msg = f"Process failed with exit code {e.returncode}"
        return False, e.stdout or "", f"{error_msg}\n{e.stderr or ''}"
    except Exception as e:
        return False, "", f"Unexpected error: {str(e)}"


def create_response_json(answer: str, query: str, collection: str) -> str:
    """Create standardized JSON response."""
    response = {
        "query": query,
        "answer": answer,
        "collection": collection,
        "timestamp": datetime.datetime.now().isoformat(),
        "status": "success"
    }
    return json.dumps(response, indent=2)


def create_error_response(error_msg: str, query: str) -> str:
    """Create standardized error response."""
    response = {
        "query": query,
        "error": error_msg,
        "timestamp": datetime.datetime.now().isoformat(),
        "status": "error"
    }
    return json.dumps(response, indent=2)


# Main pipeline function
async def run_rag_pipeline(query: str, collection: str = "default") -> str:
    """
    Execute the complete RAG pipeline.
    
    Args:
        query: User's question
        collection: Document collection to search
        
    Returns:
        JSON string containing the response or error
    """
    start_time = time.time()
    
    # Check cache first
    cache_key = generate_cache_key(query, collection)
    if is_cache_valid(cache_key):
        print(f"Cache hit for query: {query}")
        return RESULT_CACHE[cache_key]
    
    print(f"Cache miss. Processing query: '{query}' in collection: '{collection}'")
    
    try:
        # Ensure dependencies are installed
        if not install_module_dependencies("generate"):
            error_msg = "Failed to install generate module dependencies"
            return create_error_response(error_msg, query)
        
        # Set up paths and environment
        generate_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules", "generate")
        command = build_generate_command(query, collection, generate_dir)
        env = setup_subprocess_environment()
        
        print(f"Starting RAG processing at {time.time() - start_time:.2f}s")
        
        # Execute the generate module
        success, stdout, stderr = execute_generate_subprocess(command, env, generate_dir)
        
        if not success:
            error_msg = f"Generate module failed: {stderr}"
            print(f"Error: {error_msg}")
            return create_error_response(error_msg, query)
        
        # Log process outputs for debugging
        if stderr:
            print(f"Generator stderr: {stderr}")
        
        # The functional generate module returns the answer directly to stdout
        answer = stdout if stdout else "No response generated"
        
        # Create response
        result = create_response_json(answer, query, collection)
        
        # Cache the result
        RESULT_CACHE[cache_key] = result
        
        elapsed = time.time() - start_time
        print(f"RAG pipeline completed successfully in {elapsed:.2f}s")
        
        return result
        
    except Exception as e:
        error_msg = f"Unexpected error in RAG pipeline: {str(e)}"
        print(f"Error: {error_msg}")
        return create_error_response(error_msg, query)