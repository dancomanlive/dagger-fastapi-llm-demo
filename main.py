# main.py

"""
FastAPI interface for the functional RAG pipeline.

Provides endpoints for:
1. Processing RAG queries with direct response capture
2. Health checks and status monitoring
3. Clean error handling and logging
"""

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from rag_pipeline import run_rag_pipeline, initialize_environments

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Request models
class RagRequest(BaseModel):
    query: str = Field(..., description="The user's question", min_length=1)
    collection: str = Field(default="default", description="Document collection to search")

class RagResponse(BaseModel):
    query: str
    answer: str
    collection: str
    timestamp: str
    status: str

class ErrorResponse(BaseModel):
    query: str
    error: str
    timestamp: str
    status: str

# Global state
app_initialized = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    global app_initialized
    
    # Startup
    try:
        logger.info("Starting RAG pipeline API...")
        start_time = time.time()
        
        # Initialize dependencies
        logger.info("Initializing module dependencies...")
        init_success = await initialize_environments()
        
        if init_success:
            logger.info("Dependency initialization completed successfully")
            app_initialized = True
        else:
            logger.warning("Dependency initialization had issues - will try on-demand installation")
            app_initialized = False
        
        elapsed = time.time() - start_time
        logger.info(f"Startup completed in {elapsed:.2f}s")
        
    except Exception as e:
        logger.exception(f"Error during startup: {str(e)}")
        # Don't raise exception - allow app to start for debugging
        app_initialized = False
    
    yield
    
    # Shutdown
    logger.info("Shutting down RAG pipeline API...")


# FastAPI app initialization with lifespan
app = FastAPI(
    title="Functional RAG Pipeline API",
    description="Retrieval-Augmented Generation API with direct execution",
    version="2.0.0",
    lifespan=lifespan
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.exception(f"Unhandled error in {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error occurred",
            "detail": str(exc),
            "path": str(request.url.path)
        }
    )


@app.get("/")
async def root():
    """Root endpoint with API status."""
    return {
        "status": "ok",
        "message": "Functional RAG Pipeline API is running",
        "version": "2.0.0",
        "initialized": app_initialized
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy" if app_initialized else "degraded",
        "timestamp": time.time(),
        "dependencies_initialized": app_initialized
    }


@app.post("/rag", response_model=RagResponse)
async def process_rag_request(request: RagRequest):
    """
    Process RAG query and return generated response.
    
    Args:
        request: RAG request containing query and collection
        
    Returns:
        Generated response with answer and metadata
        
    Raises:
        HTTPException: If processing fails
    """
    request_start = time.time()
    
    try:
        logger.info(f"Processing RAG request - Query: '{request.query}', Collection: '{request.collection}'")
        
        # Execute RAG pipeline
        result_json = await run_rag_pipeline(
            query=request.query, 
            collection=request.collection
        )
        
        # Parse result
        try:
            result_data = json.loads(result_json)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from RAG pipeline: {result_json}")
            raise HTTPException(
                status_code=500, 
                detail=f"Pipeline returned invalid JSON: {str(e)}"
            )
        
        # Check for errors in result
        if result_data.get("status") == "error":
            logger.error(f"RAG pipeline error: {result_data.get('error')}")
            raise HTTPException(
                status_code=500, 
                detail=result_data.get("error", "Unknown pipeline error")
            )
        
        # Log timing
        elapsed = time.time() - request_start
        logger.info(f"RAG request completed in {elapsed:.2f}s")
        
        return result_data
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Unexpected error processing RAG request: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Unexpected error: {str(e)}"
        )


@app.post("/rag/stream")
async def stream_rag_response(request: RagRequest):
    """
    Stream RAG responses as Server-Sent Events for real-time chat interfaces.
    
    Args:
        request: RAG request containing query and collection
        
    Returns:
        StreamingResponse with Server-Sent Events
    """
    async def generate_stream():
        try:
            logger.info(f"Starting streaming response for query: '{request.query}'")
            
            # Get the full response from pipeline
            result_json = await run_rag_pipeline(
                query=request.query, 
                collection=request.collection
            )
            
            result_data = json.loads(result_json)
            
            if result_data.get("status") == "error":
                yield f"data: {json.dumps({'error': result_data.get('error')})}\n\n"
                return
            
            # Stream the answer word by word to simulate real-time generation
            answer = result_data.get("answer", "")
            words = answer.split()
            
            current_text = ""
            for i, word in enumerate(words):
                current_text += word + " "
                
                chunk_data = {
                    "content": word + " ",
                    "full_text": current_text.strip(),
                    "progress": (i + 1) / len(words),
                    "is_final": i == len(words) - 1
                }
                
                yield f"data: {json.dumps(chunk_data)}\n\n"
                
                # Add small delay to simulate streaming
                await asyncio.sleep(0.1)
            
            # Send completion signal
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            logger.exception(f"Error in streaming response: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


# Development/debugging endpoints
@app.get("/debug/cache")
async def get_cache_status():
    """Debug endpoint to view cache status."""
    from rag_pipeline import RESULT_CACHE, MODULE_DEPENDENCIES_INSTALLED
    
    return {
        "result_cache_size": len(RESULT_CACHE),
        "cached_queries": list(RESULT_CACHE.keys())[:5],  # Show first 5 cache keys
        "dependencies_status": MODULE_DEPENDENCIES_INSTALLED
    }
