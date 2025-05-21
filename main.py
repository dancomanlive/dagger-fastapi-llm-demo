# main.py

"""
This code handles the API interface for the (RAG) pipeline. The steps involved are:

1. Define API endpoints that accept user queries.
2. Create Dagger connections to orchestrate containerized processing workflows.
3. Pass incoming queries to the RAG pipeline for processing.
4. Return the generated responses from the pipeline back to the clients.
5. Handle errors and exceptions that may occur during the processing flow.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import logging
import os
import sys
import dagger
from rag_pipeline import run_rag_pipeline

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Simplified RAG Pipeline with Dagger")

class RagRequest(BaseModel):
    query: str
    collection: str = "default"

@app.post("/rag")
async def process_rag_request(request: RagRequest):
    try:
        # Use environment variable for Dagger connection
        _EXPERIMENTAL_DAGGER_RUNNER_HOST = os.environ["_EXPERIMENTAL_DAGGER_RUNNER_HOST"]
        logger.info(f"Connecting to Dagger engine at: {_EXPERIMENTAL_DAGGER_RUNNER_HOST}")
        
        # Use the older Connection API which we know works for this version
        config = dagger.Config(
            log_output=sys.stderr
        )
        async with dagger.Connection(config) as client:
            result_str = await run_rag_pipeline(client, query=request.query, collection=request.collection)
            return json.loads(result_str)
    except json.JSONDecodeError:
        logger.error("RAG pipeline returned invalid JSON.")
        raise HTTPException(status_code=500, detail="RAG pipeline returned invalid JSON.")
    except dagger.DaggerError as e:
        logger.error(f"Dagger error in /rag endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Dagger error: {str(e)}")
    except Exception as e:
        logger.exception("Unhandled error in /rag endpoint")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {str(e)}")

@app.get("/")
async def read_root():
    return {"status": "ok", "message": "Simplified RAG Pipeline with Dagger is running"}