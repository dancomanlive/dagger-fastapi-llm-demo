# main.py

"""
This code handles the API interface for the Retrieval-Augmented Generation (RAG) pipeline. The steps involved are:

1. Define API endpoints that accept user queries.
2. Initialize Python virtual environments for each module.
3. Pass incoming queries to the RAG pipeline for processing.
4. Return the generated responses from the pipeline back to the clients.
5. Handle errors and exceptions that may occur during the processing flow.
6. Pre-initialize environments and dependencies for improved performance.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import logging
import os
import sys
import time
from rag_pipeline_direct import run_rag_pipeline, initialize_environments

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Simplified RAG Pipeline with Direct Execution")

@app.on_event("startup")
async def startup_event():
    """Initialize resources during app startup"""
    try:
        # Initialize all virtual environments
        logger.info("Initializing virtual environments...")
        init_success = await initialize_environments()
        if init_success:
            logger.info("Virtual environment initialization completed successfully")
            
            # Warmup has been removed as it's not needed
            logger.info("Warmup functionality removed - direct execution is fast enough without it")
        else:
            logger.warning("Environment initialization had issues - falling back to on-demand creation")
        
    except Exception as e:
        logger.exception(f"Error during startup: {str(e)}")
        # We won't raise an exception here to allow the app to start
        # even if environment initialization fails

class RagRequest(BaseModel):
    query: str
    collection: str = "default"

@app.post("/rag")
async def process_rag_request(request: RagRequest):
    request_start_time = time.time()
    
    try:
        result_str = await run_rag_pipeline(query=request.query, collection=request.collection)
        
        logger.info(f"Total request time: {time.time() - request_start_time:.2f}s")
        return json.loads(result_str)
    except json.JSONDecodeError:
        logger.error("RAG pipeline returned invalid JSON.")
        raise HTTPException(status_code=500, detail="RAG pipeline returned invalid JSON.")
    except Exception as e:
        logger.exception("Unhandled error in /rag endpoint")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {str(e)}")

@app.get("/")
async def read_root():
    return {"status": "ok", "message": "Simplified RAG Pipeline with Direct Execution is running"}

