# main.py

"""
This code handles the API interface for the (RAG) pipeline. The steps involved are:

1. Define API endpoints that accept user queries.
2. Create Dagger connections to orchestrate containerized processing workflows.
3. Pass incoming queries to the RAG pipeline for processing.
4. Return the generated responses from the pipeline back to the clients.
5. Handle errors and exceptions that may occur during the processing flow.
6. Initialize and maintain persistent containers for improved performance.
7. Run a warmup query during startup to fully initialize the system.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import logging
import os
import sys
import time
import dagger
from rag_pipeline import run_rag_pipeline, initialize_persistent_containers, warmup_components

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Simplified RAG Pipeline with Dagger")

# Global Dagger client for persistent connection
dagger_client = None

@app.on_event("startup")
async def startup_event():
    """Initialize resources during app startup"""
    global dagger_client
    try:
        # Use environment variable for Dagger connection
        _EXPERIMENTAL_DAGGER_RUNNER_HOST = os.environ["_EXPERIMENTAL_DAGGER_RUNNER_HOST"]
        logger.info(f"Initializing persistent Dagger connection to: {_EXPERIMENTAL_DAGGER_RUNNER_HOST}")
        
        # Create a persistent Dagger connection
        config = dagger.Config(
            log_output=sys.stderr
        )
        
        # Create client - we'll keep this open during the app's lifetime
        dagger_client = dagger.Connection(config)
        client = await dagger_client.__aenter__()
        
        # Initialize all persistent containers
        logger.info("Initializing persistent containers...")
        init_success = await initialize_persistent_containers(client)
        if init_success:
            logger.info("Persistent container initialization completed successfully")
            
            # Check if startup warmup is enabled
            enable_warmup = os.getenv("ENABLE_STARTUP_WARMUP", "").lower() == "true"
            
            if enable_warmup:
                warmup_start = time.time()
                
                # Run component-level warmup (faster, no query execution) 
                logger.info("==========================================")
                logger.info("WARMING UP COMPONENTS - INSTALLING DEPENDENCIES")
                logger.info("==========================================")
                await warmup_components(client)
                logger.info(f"WARMUP COMPLETED in {time.time() - warmup_start:.2f}s - DEPENDENCIES INSTALLED")
                logger.info("===========================================")
            else:
                logger.info("Startup warmup disabled - skipping warmup")
        else:
            logger.warning("Container initialization had issues - falling back to on-demand creation")
        
    except Exception as e:
        logger.exception(f"Error during startup: {str(e)}")
        # We won't raise an exception here to allow the app to start
        # even if container initialization fails - we'll fall back to
        # on-demand container creation

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources during app shutdown"""
    global dagger_client
    if dagger_client:
        logger.info("Closing persistent Dagger connection")
        try:
            await dagger_client.__aexit__(None, None, None)
            logger.info("Dagger connection closed successfully")
        except Exception as e:
            logger.exception(f"Error closing Dagger connection: {str(e)}")

class RagRequest(BaseModel):
    query: str
    collection: str = "default"

@app.post("/rag")
async def process_rag_request(request: RagRequest):
    global dagger_client
    request_start_time = time.time()
    
    try:
        if dagger_client:
            # Use the existing client if available
            logger.info("Using persistent Dagger client for request")
            client = await dagger_client.__aenter__()  # This is a no-op if already entered
            result_str = await run_rag_pipeline(client, query=request.query, collection=request.collection)
        else:
            # Fall back to creating a new connection
            logger.info("No persistent client available, creating new connection")
            _EXPERIMENTAL_DAGGER_RUNNER_HOST = os.environ["_EXPERIMENTAL_DAGGER_RUNNER_HOST"]
            logger.info(f"Connecting to Dagger engine at: {_EXPERIMENTAL_DAGGER_RUNNER_HOST}")
            
            config = dagger.Config(
                log_output=sys.stderr
            )
            async with dagger.Connection(config) as client:
                result_str = await run_rag_pipeline(client, query=request.query, collection=request.collection)
        
        logger.info(f"Total request time: {time.time() - request_start_time:.2f}s")
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