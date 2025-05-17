import logging
import json
import os
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
import dagger

from pydantic import BaseModel
from rag_pipeline import run_rag_pipeline

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log important environment variables at startup
retriever_service_url = os.getenv("RETRIEVER_SERVICE_URL", "http://localhost:8001")
logger.info(f"Using Retriever Service URL: {retriever_service_url}")
logger.info(f"QDRANT_URL: {os.getenv('QDRANT_URL', 'not set')}")


# --- FastAPI App ---
app = FastAPI(
    title="Simplified RAG Pipeline with Dagger",
)


# --- Pydantic Model for Request Body ---
class RagRequest(BaseModel):
    query: str
    collection: str = "default"


# --- FastAPI Endpoints ---
@app.post("/rag")
async def process_rag_request(request: RagRequest):
    try:
        result_str = await run_rag_pipeline(request.query, request.collection)
        return json.loads(result_str)
    except json.JSONDecodeError:
        logger.error("RAG pipeline returned invalid JSON.")
        raise HTTPException(status_code=500, detail="RAG pipeline returned invalid JSON.")
    except Exception as e:
        logger.exception("Unhandled error in /rag endpoint")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {str(e)}")

@app.get("/")
async def read_root():
    return {"status": "ok", "message": "Simplified RAG Pipeline with Dagger is running"}

@app.get("/test-qdrant-direct")
async def test_qdrant_direct():
    """
    Test Qdrant connection directly from the FastAPI server
    (without using Dagger containers)
    """
    try:
        # First, check if qdrant-client is installed
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models
        except ImportError:
            return {
                "status": "error", 
                "message": "qdrant-client not installed. Install with: pip install qdrant-client>=1.7.0"
            }
        
        # Check qdrant-client version
        import pkg_resources
        qdrant_version = pkg_resources.get_distribution("qdrant-client").version
        logger.info(f"Qdrant client version: {qdrant_version}")
        
        # Connect using Docker service name (works within Docker Compose)
        qdrant_url = "http://qdrant:6333"
        logger.info(f"Connecting to Qdrant at {qdrant_url}")
        
        client = QdrantClient(url=qdrant_url, timeout=5.0)
        
        # Check connection by listing collections
        collections = client.get_collections()
        
        # Use the correct health check method
        try:
            health_status = client.http.healthz()
        except AttributeError:
            # Fallback for different versions
            try:
                health_status = client.http.health()
            except AttributeError:
                health_status = "Health check method not available"
        
        # Return successful connection info
        return {
            "status": "success",
            "client_version": qdrant_version,
            "connection": {
                "url": qdrant_url,
                "collections": [c.name for c in collections.collections],
                "health": str(health_status)
            }
        }
    except Exception as e:
        logger.exception("Error connecting to Qdrant")
        return {
            "status": "error", 
            "message": f"Failed to connect to Qdrant: {str(e)}",
            "client_version": qdrant_version if 'qdrant_version' in locals() else "unknown"
        }

@app.get("/test-qdrant")
async def test_qdrant_connection():
    """
    Test Qdrant connection from a Dagger container directly
    """
    try:
        # Get Qdrant URL for Dagger from environment variable
        qdrant_url_for_dagger = os.getenv("QDRANT_URL_FOR_DAGGER", "http://host.docker.internal:6333")
        
        # Now connect via Dagger with the working connection method
        async with dagger.Connection() as client:
            # Create a simple container to test Qdrant
            container = (
                client.container()
                .from_("python:3.11")
                .with_exec(["pip", "install", "qdrant-client>=1.7.0"])
                .with_workdir("/app")
                .with_exec([
                    "python", "-c", f"""
import pkg_resources
from qdrant_client import QdrantClient

# Use the environment-provided URL
qdrant_url = "{qdrant_url_for_dagger}"
print(f"Qdrant client version: {{pkg_resources.get_distribution('qdrant-client').version}}")
print(f"Connecting to Qdrant at {{qdrant_url}}")

# Create client with timeout
client = QdrantClient(url=qdrant_url, timeout=5.0)

# Check connection by listing collections
collections = client.get_collections()
print(f"Successfully connected! Available collections: {{[c.name for c in collections.collections]}}")

# Try health check
try:
    health = client.http.healthz()
    print(f"Qdrant health status: {{health}}")
except AttributeError:
    try:
        health = client.http.health()
        print(f"Qdrant health status: {{health}}")
    except AttributeError:
        print("Health check method not available for this client version")
                    """
                ])
            )
            
            # Execute container and get output
            output = await container.stdout()
            
            return {
                "status": "success",
                "message": "Successfully connected to Qdrant from Dagger container",
                "details": output.strip()
            }
    except Exception as e:
        logger.exception("Error testing Qdrant connection")
        return {
            "status": "error", 
            "message": "Failed to connect to Qdrant from Dagger container", 
            "error": str(e)
        }

@app.get("/test-dagger")
async def test_dagger_communication():
    try:
        async with dagger.Connection() as client:
            # Prepare code directories
            container_a_code_dir = client.host().directory("modules/container_a")
            container_b_code_dir = client.host().directory("modules/container_b")
            
            logger.info("Starting container A to generate JSON data")
            
            # Container A: Generates JSON data
            container_a = (
                client.container()
                .from_("python:3.11")
                .with_mounted_directory("/app", container_a_code_dir)
                .with_workdir("/app")
                .with_exec(["mkdir", "-p", "/output"])  # Create output directory first
                .with_exec(["python", "main.py", "--output", "/output/data.json"])
            )
            
            # Create output directory in Container A
            # container_a = container_a.with_exec(["mkdir", "-p", "/output"])  # Moved above
            
            # Execute Container A
            container_a_executed = await container_a.sync()
            
            # Extract the file object from Container A
            json_file = container_a_executed.file("/output/data.json")
            logger.info("Container A executed, JSON file extracted")
            
            # Container B: Processes the JSON file from Container A
            logger.info("Starting container B to process JSON data")
            container_b = (
                client.container()
                .from_("python:3.11")
                .with_mounted_directory("/app", container_b_code_dir)
                .with_mounted_file("/input/data.json", json_file)
                .with_workdir("/app")
                .with_exec(["mkdir", "-p", "/output"])
                .with_exec([
                    "python", "main.py",
                    "--input", "/input/data.json",
                    "--output", "/output/processed.json"
                ])
            )
            
            # Execute Container B
            container_b_executed = await container_b.sync()
            
            # Get output from Container B (stdout will have the JSON data)
            output = await container_b_executed.stdout()
            
            # Also get the processed output file
            processed_file = container_b_executed.file("/output/processed.json")
            processed_content = await processed_file.contents()
            
            # Parse the JSON content
            processed_data = json.loads(processed_content)
            
            logger.info(f"Pipeline completed successfully: {processed_data}")
            
            # Return both the raw output and parsed data
            return {
                "container_b_output": output.strip(),
                "processed_data": processed_data
            }
    except Exception as e:
        logger.exception("Error in test-dagger endpoint")
        return {"error": str(e)}