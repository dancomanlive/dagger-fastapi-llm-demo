import os
import logging
import json
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException

import dagger
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


# --- RAG Pipeline Logic ---
async def run_rag_pipeline(query: str, collection: str = "default") -> str:
    async with dagger.Connection() as client:
        # Prepare code directories
        retrieve_code_dir = client.host().directory("modules/retrieve")
        generate_code_dir = client.host().directory("modules/generate")

        # Prepare input for retrieve
        retrieve_input = {
            "query": query,
            "collection": collection,
            "qdrant_host": os.getenv("QDRANT_URL"),
            "top_k": 5
        }
        input_json_str = json.dumps(retrieve_input)
        input_file = client.directory().with_new_file("input.json", input_json_str).file("input.json")

        # --- Retrieve Container ---
        retrieve_container = (
            client.container()
            .from_("python:3.11")
            .with_mounted_directory("/app", retrieve_code_dir)
            .with_mounted_file("/app/input.json", input_file)
            .with_workdir("/app")
            .with_exec([
                "pip", "install", "qdrant-client>=1.7.0", "sentence-transformers>=2.3.0", "numpy>=1.24.0"
            ])
            .with_exec([
                "python", "main.py",
                "--input", "input.json",
                "--output", "output.json"
            ])
        )

        retrieve_executed = await retrieve_container.sync()
        retrieve_output_file = retrieve_executed.file("/app/output.json")

        # --- Generate Container ---
        generate_container = (
            client.container()
            .from_("python:3.11")
            .with_mounted_directory("/app", generate_code_dir)
            .with_mounted_file("/app/input.json", retrieve_output_file)
            .with_workdir("/app")
            .with_exec([
                "pip", "install", "openai==1.5.0", "pydantic>=2.0.0"
            ])
            .with_exec([
                "python", "main.py",
                "--input", "input.json",
                "--output", "output.json"
            ])
        )

        generate_executed = await generate_container.sync()
        generate_output_file = generate_executed.file("/app/output.json")
        return await generate_output_file.contents()