# rag_pipeline.py

import os
import sys
import time
import hashlib
import datetime
import subprocess
import json
import asyncio
import threading
import logging
import re
from pathlib import Path
from typing import Dict, Optional, Tuple, NamedTuple
from dotenv import load_dotenv

# Debug print to confirm script execution
print("[DEBUG] rag_pipeline.py script started")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration using NamedTuple
class RAGConfig(NamedTuple):
    top_k: int = 5
    timeout_seconds: int = 120
    cache_ttl_seconds: int = 3600
    max_query_length: int = 1000

# Custom exceptions
class RAGError(Exception):
    """Base exception for RAG pipeline errors."""
    pass

class ValidationError(RAGError):
    """Input validation error."""
    pass

class DependencyError(RAGError):
    """Dependency installation error."""
    pass

# Thread-safe cache using threading.local()
_thread_local = threading.local()

# Configuration
TMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tmp")

def load_config_from_env() -> RAGConfig:
    """
    Load RAG pipeline configuration from environment variables.
    
    Returns:
        RAGConfig: Configuration object with values from environment or defaults
        
    Environment Variables:
        RAG_TOP_K: Number of top documents to retrieve (default: 5)
        RAG_TIMEOUT_SECONDS: Subprocess timeout in seconds (default: 120)
        RAG_CACHE_TTL_SECONDS: Cache time-to-live in seconds (default: 3600)
        RAG_MAX_QUERY_LENGTH: Maximum query length in characters (default: 1000)
    """
    return RAGConfig(
        top_k=int(os.getenv("RAG_TOP_K", "5")),
        timeout_seconds=int(os.getenv("RAG_TIMEOUT_SECONDS", "120")),
        cache_ttl_seconds=int(os.getenv("RAG_CACHE_TTL_SECONDS", "3600")),
        max_query_length=int(os.getenv("RAG_MAX_QUERY_LENGTH", "1000"))
    )

def get_cache() -> Dict[str, tuple]:
    """
    Get thread-local result cache for storing query responses.
    
    Returns:
        Dict[str, tuple]: Cache dictionary mapping cache keys to (result, timestamp) tuples
        
    Note:
        Each thread gets its own cache instance for thread safety
    """
    if not hasattr(_thread_local, 'cache'):
        _thread_local.cache = {}
    return _thread_local.cache

def get_dependency_cache() -> Dict[str, bool]:
    """
    Get thread-local dependency installation cache.
    
    Returns:
        Dict[str, bool]: Cache mapping module names to installation status
        
    Note:
        Tracks which modules have had their dependencies installed successfully
    """
    if not hasattr(_thread_local, 'deps_cache'):
        _thread_local.deps_cache = {}
    return _thread_local.deps_cache

def get_req_hash_cache() -> Dict[str, str]:
    """
    Get thread-local requirements file hash cache.
    
    Returns:
        Dict[str, str]: Cache mapping module names to requirements.txt hash values
        
    Note:
        Used to detect changes in requirements files and avoid unnecessary reinstalls
    """
    if not hasattr(_thread_local, 'req_hash_cache'):
        _thread_local.req_hash_cache = {}
    return _thread_local.req_hash_cache


# Utility functions
def validate_query(query: str, max_length: int = 1000) -> None:
    """
    Validate user input query to prevent security vulnerabilities.
    
    Args:
        query: User's search query string
        max_length: Maximum allowed query length in characters
        
    Raises:
        ValidationError: If query is empty, too long, or contains dangerous characters
        
    Security:
        Prevents command injection by checking for shell metacharacters
    """
    if not query or not query.strip():
        raise ValidationError("Query cannot be empty")
    if len(query) > max_length:
        raise ValidationError(f"Query too long (max {max_length} chars)")
    # Prevent command injection attempts
    dangerous_chars = [';', '&', '|', '`', '$', '(', ')']
    if any(char in query for char in dangerous_chars):
        raise ValidationError("Query contains potentially dangerous characters")

def sanitize_collection_name(collection: str) -> str:
    """
    Sanitize collection name to prevent path traversal attacks.
    
    Args:
        collection: Raw collection name from user input
        
    Returns:
        str: Sanitized collection name containing only safe characters
        
    Security:
        Removes all characters except alphanumeric, underscore, and hyphen
        Returns "default" if input becomes empty after sanitization
    """
    # Only allow alphanumeric, underscore, hyphen
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', collection)
    if not sanitized:
        return "default"
    return sanitized

def ensure_tmp_dir_exists() -> None:
    """
    Create the temporary directory for dependency markers if it doesn't exist.
    
    Note:
        Creates directory structure recursively (equivalent to mkdir -p)
        Uses TMP_DIR global constant for path
    """
    os.makedirs(TMP_DIR, exist_ok=True)

def generate_cache_key(query: str, collection: str) -> str:
    """
    Generate a consistent cache key for query-collection combinations.
    
    Args:
        query: User's search query
        collection: Target document collection
        
    Returns:
        str: MD5 hash of the query-collection combination
        
    Note:
        Uses MD5 for speed as this is not cryptographically sensitive
    """
    cache_input = f"{query}_{collection}"
    return hashlib.md5(cache_input.encode()).hexdigest()

def is_cache_valid(cache_key: str, ttl_seconds: int = 3600) -> bool:
    """
    Check if cached result exists and is still within time-to-live period.
    
    Args:
        cache_key: Cache key to check
        ttl_seconds: Time-to-live in seconds (default: 3600 = 1 hour)
        
    Returns:
        bool: True if cache entry exists and is not expired
        
    Side Effects:
        Removes expired cache entries automatically
    """
    cache = get_cache()
    if cache_key in cache:
        result, timestamp = cache[cache_key]
        if time.time() - timestamp < ttl_seconds:
            return True
        else:
            # Clean expired entry
            del cache[cache_key]
    return False

def get_cached_result(cache_key: str) -> Optional[str]:
    """
    Retrieve cached result if it exists.
    
    Args:
        cache_key: Cache key to retrieve
        
    Returns:
        Optional[str]: Cached result string or None if not found
        
    Note:
        Should be called after is_cache_valid() to ensure result is fresh
    """
    cache = get_cache()
    if cache_key in cache:
        result, _ = cache[cache_key]
        return result
    return None

def cache_result(cache_key: str, result: str) -> None:
    """
    Store result in cache with current timestamp.
    
    Args:
        cache_key: Unique key for this result
        result: Result string to cache
        
    Note:
        Stores tuple of (result, timestamp) for TTL validation
    """
    cache = get_cache()
    cache[cache_key] = (result, time.time())


def calculate_requirements_hash(requirements_path: str) -> str:
    """
    Calculate MD5 hash of requirements.txt file content.
    
    Args:
        requirements_path: Path to requirements.txt file
        
    Returns:
        str: MD5 hash of file content, empty string if file not found
        
    Note:
        Used to detect changes in dependencies and trigger reinstallation
    """
    try:
        with open(requirements_path, "r") as f:
            content = f.read()
        return hashlib.md5(content.encode()).hexdigest()
    except FileNotFoundError:
        return ""

def get_dependency_marker_path(module_name: str, req_hash: str) -> str:
    """
    Generate path for dependency installation marker file.
    
    Args:
        module_name: Name of the module (e.g., "generate")
        req_hash: Hash of the requirements.txt file
        
    Returns:
        str: Full path to marker file
        
    Note:
        Marker files indicate successful dependency installation for specific requirements
        Format: {module_name}_deps_{hash_prefix}.installed
    """
    return os.path.join(TMP_DIR, f"{module_name}_deps_{req_hash[:8]}.installed")

def cleanup_old_markers(module_name: str) -> None:
    """
    Remove outdated dependency marker files for a module.
    
    Args:
        module_name: Name of the module to clean markers for
        
    Note:
        Removes all existing marker files before creating new ones
        Prevents accumulation of obsolete markers
    """
    pattern = f"{module_name}_deps_*.installed"
    for old_marker in Path(TMP_DIR).glob(pattern):
        logging.info(f"Removing outdated dependency marker: {old_marker}")
        old_marker.unlink()


# Dependency management functions
def check_requirements_file(module_name: str) -> Tuple[bool, str]:
    """
    Check if requirements.txt file exists for a module and get its path.
    
    Args:
        module_name: Name of the module to check (e.g., "generate")
    
    Returns:
        Tuple[bool, str]: (file_exists, file_path)
        
    Note:
        Assumes module structure: modules/{module_name}/requirements.txt
    """
    requirements_path = os.path.join("modules", module_name, "requirements.txt")
    return os.path.exists(requirements_path), requirements_path


def install_pip_requirements(requirements_path: str, module_name: str) -> bool:
    """
    Install Python packages from requirements.txt file.
    
    Args:
        requirements_path: Path to requirements.txt file
        module_name: Name of module (for logging purposes)
        
    Returns:
        bool: True if installation successful, False otherwise
        
    Note:
        Uses pip install with quiet flag to reduce output
        Runs in current Python environment
    """
    try:
        logging.info(f"Installing requirements for {module_name}...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", requirements_path, "-q"
        ])
        logging.info(f"Dependencies installed successfully for {module_name}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error installing dependencies for {module_name}: {str(e)}")
        return False


def create_dependency_marker(module_name: str, req_hash: str) -> None:
    """
    Create marker file indicating successful dependency installation.
    
    Args:
        module_name: Name of the module
        req_hash: Hash of the requirements.txt file
        
    Note:
        Marker files prevent unnecessary reinstallation when requirements haven't changed
        Contains timestamp for debugging purposes
    """
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
    # Check if already processed using thread-local cache
    deps_cache = get_dependency_cache()
    if module_name in deps_cache:
        logging.info(f"Dependencies for {module_name} already processed")
        return deps_cache[module_name]
    
    logging.info(f"Setting up dependencies for {module_name}...")
    ensure_tmp_dir_exists()
    
    # Check requirements file
    req_exists, requirements_path = check_requirements_file(module_name)
    if not req_exists:
        logging.info(f"No requirements.txt found for {module_name}")
        deps_cache[module_name] = True
        return True
    
    # Get or calculate requirements hash using thread-local cache
    req_hash_cache = get_req_hash_cache()
    if module_name in req_hash_cache:
        req_hash = req_hash_cache[module_name]
    else:
        req_hash = calculate_requirements_hash(requirements_path)
        req_hash_cache[module_name] = req_hash
    
    # Check if already installed with current hash
    marker_path = get_dependency_marker_path(module_name, req_hash)
    if os.path.exists(marker_path):
        logging.info(f"Dependencies for {module_name} already installed (marker exists)")
        deps_cache[module_name] = True
        return True
    
    # Clean up old markers and install
    cleanup_old_markers(module_name)
    success = install_pip_requirements(requirements_path, module_name)
    
    if success:
        create_dependency_marker(module_name, req_hash)
    else:
        raise DependencyError(f"Failed to install dependencies for {module_name}")
    
    deps_cache[module_name] = success
    return success


# Environment setup
async def initialize_environments() -> bool:
    """
    Pre-initialize all required dependencies during app startup.
    
    Returns:
        True if initialization successful
    """
    logging.info("Initializing module dependencies...")
    start_time = time.time()
    
    try:
        # Initialize generate module dependencies
        success = await asyncio.to_thread(install_module_dependencies, "generate")
        
        # Add other modules here as needed
        # success &= await asyncio.to_thread(install_module_dependencies, "retrieval")
        
        elapsed = time.time() - start_time
        logging.info(f"Dependencies initialized in {elapsed:.2f}s - Success: {success}")
        return success
    except Exception as e:
        elapsed = time.time() - start_time
        logging.error(f"Failed to initialize dependencies in {elapsed:.2f}s: {str(e)}")
        return False


# Core pipeline functions
def build_generate_command(query: str, collection: str, config: RAGConfig, generate_dir: str) -> list:
    """
    Build command line arguments to execute the generate module.
    
    Args:
        query: User's search query
        collection: Target document collection
        config: RAG configuration containing top_k and other settings
        generate_dir: Path to the generate module directory
        
    Returns:
        list: Command line arguments for subprocess execution
        
    Note:
        Constructs command: python main.py --query <query> --collection <collection> --top_k <top_k>
    """
    return [
        sys.executable,
        os.path.join(generate_dir, "main.py"),
        "--query", query,
        "--collection", collection,
        "--top_k", str(config.top_k)
    ]


def setup_subprocess_environment() -> dict:
    """
    Set up environment variables for subprocess execution.
    
    Returns:
        dict: Environment variables dictionary for subprocess
        
    Environment Variables Set:
        PYTHONUNBUFFERED: Ensures immediate output (no buffering)
        RETRIEVER_SERVICE_URL: URL for the document retrieval service
        OPENAI_API_KEY: API key for OpenAI services (if available)
        EXECUTION_ID: Unique timestamp for debugging subprocess execution
    """
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


async def execute_generate_subprocess_async(
    command: list, 
    env: dict, 
    cwd: str, 
    config: RAGConfig
) -> Tuple[bool, str, str]:
    """
    Execute the generate module subprocess asynchronously with timeout handling.
    
    Args:
        command: Command line arguments list
        env: Environment variables dictionary
        cwd: Working directory for subprocess
        config: RAG configuration containing timeout settings
    
    Returns:
        Tuple[bool, str, str]: (success, stdout, stderr)
        
    Features:
        - Asynchronous execution using asyncio.create_subprocess_exec
        - Configurable timeout with graceful process termination
        - Proper error handling and logging
        - Clean resource management
        
    Note:
        Uses asyncio.wait_for() for timeout control and process.kill() for cleanup
    """
    try:
        logging.info(f"Executing command: {' '.join(command)}")
        
        # Use asyncio subprocess instead of blocking subprocess
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=cwd
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=config.timeout_seconds
        )
        
        if process.returncode != 0:
            error_msg = stderr.decode().strip() or "Process failed with no error message"
            raise subprocess.CalledProcessError(process.returncode, command, stderr=error_msg)
        
        return True, stdout.decode().strip(), stderr.decode().strip()
        
    except asyncio.TimeoutError:
        try:
            process.kill()
            await process.wait()
        except Exception:
            pass
        return False, "", f"Process timed out after {config.timeout_seconds}s"
    except subprocess.CalledProcessError as e:
        error_msg = f"Process failed with exit code {e.returncode}"
        return False, e.stdout.decode() if e.stdout else "", f"{error_msg}\n{e.stderr.decode() if e.stderr else ''}"
    except Exception as e:
        return False, "", f"Unexpected error: {str(e)}"


def create_response_json(answer: str, query: str, collection: str) -> str:
    """
    Create standardized JSON response for successful RAG pipeline execution.
    
    Args:
        answer: Generated answer from the RAG pipeline
        query: Original user query
        collection: Document collection used
        
    Returns:
        str: JSON-formatted response string with indentation
        
    Response Format:
        {
            "query": "user query",
            "answer": "generated response",
            "collection": "collection name",
            "timestamp": "ISO format timestamp",
            "status": "success"
        }
    """
    response = {
        "query": query,
        "answer": answer,
        "collection": collection,
        "timestamp": datetime.datetime.now().isoformat(),
        "status": "success"
    }
    return json.dumps(response, indent=2)


def create_error_response(error: Exception, query: str) -> str:
    """
    Create standardized JSON error response with proper error typing.
    
    Args:
        error: Exception object that occurred
        query: Original user query that caused the error
        
    Returns:
        str: JSON-formatted error response string with indentation
        
    Response Format:
        {
            "query": "user query",
            "error": "error message",
            "error_type": "exception class name",
            "timestamp": "ISO format timestamp",
            "status": "error"
        }
        
    Note:
        Includes error_type for better error handling on client side
    """
    error_type = type(error).__name__
    response = {
        "query": query,
        "error": str(error),
        "error_type": error_type,
        "timestamp": datetime.datetime.now().isoformat(),
        "status": "error"
    }
    return json.dumps(response, indent=2)


# Main pipeline function
async def run_rag_pipeline(
    query: str, 
    collection: str = "default",
    config: RAGConfig = None
) -> str:
    """
    Execute the complete RAG (Retrieval-Augmented Generation) pipeline.
    
    This is the main entry point for processing user queries through the RAG system.
    It handles input validation, caching, dependency management, and subprocess execution.
    
    Args:
        query: User's search question or prompt
        collection: Target document collection name (default: "default")
        config: RAG configuration object (default: loads from environment)
        
    Returns:
        str: JSON-formatted response containing either success or error data
        
    Pipeline Steps:
        1. Load configuration and validate inputs
        2. Check cache for existing results
        3. Install module dependencies if needed
        4. Execute generate module via subprocess
        5. Process results and update cache
        6. Return formatted JSON response
        
    Raises:
        ValidationError: For invalid input queries
        DependencyError: For dependency installation failures
        RAGError: For general pipeline errors
        
    Cache Behavior:
        - Results are cached with configurable TTL
        - Cache keys combine query and collection
        - Expired entries are automatically cleaned
        
    Security Features:
        - Input sanitization against injection attacks
        - Collection name validation
        - Safe subprocess execution with timeouts
        
    Example:
        >>> result = await run_rag_pipeline("What is machine learning?")
        >>> print(result)  # JSON response with answer
    """
    if config is None:
        config = load_config_from_env()
    
    start_time = time.time()
    
    try:
        # Validate inputs
        validate_query(query, config.max_query_length)
        collection = sanitize_collection_name(collection)
        
        # Check cache first
        cache_key = generate_cache_key(query, collection)
        if is_cache_valid(cache_key, config.cache_ttl_seconds):
            cached_result = get_cached_result(cache_key)
            if cached_result:
                logging.info(f"Cache hit for query: {query[:50]}...")
                return cached_result
        
        logging.info(f"Cache miss. Processing query: '{query[:50]}...' in collection: '{collection}'")
        
        # Ensure dependencies are installed
        deps_ready = await asyncio.to_thread(install_module_dependencies, "generate")
        if not deps_ready:
            error = DependencyError("Failed to install generate module dependencies")
            return create_error_response(error, query)
        
        # Set up paths and environment
        generate_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules", "generate")
        command = build_generate_command(query, collection, config, generate_dir)
        env = setup_subprocess_environment()
        
        logging.info(f"Starting RAG processing at {time.time() - start_time:.2f}s")
        
        # Execute the generate module asynchronously
        success, stdout, stderr = await execute_generate_subprocess_async(command, env, generate_dir, config)
        
        if not success:
            error = RAGError(f"Generate module failed: {stderr}")
            logging.error(f"Error: {error}")
            return create_error_response(error, query)
        
        # Log process outputs for debugging
        if stderr:
            logging.warning(f"Generator stderr: {stderr}")
        
        # The functional generate module returns the answer directly to stdout
        answer = stdout if stdout else "No response generated"
        
        # Create response
        result = create_response_json(answer, query, collection)
        
        # Cache the result
        cache_result(cache_key, result)
        
        elapsed = time.time() - start_time
        logging.info(f"RAG pipeline completed successfully in {elapsed:.2f}s")
        
        return result
        
    except ValidationError as e:
        logging.error(f"Validation error for query '{query[:50]}...': {str(e)}")
        return create_error_response(e, query)
    except DependencyError as e:
        logging.error(f"Dependency error for query '{query[:50]}...': {str(e)}")
        return create_error_response(e, query)
    except Exception as e:
        error = RAGError(f"Unexpected error in RAG pipeline: {str(e)}")
        logging.error(f"Error: {error}")
        return create_error_response(error, query)