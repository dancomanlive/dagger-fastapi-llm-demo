# services/retriever_service/main.py

"""
This code handles the semantic search component of the (RAG) pipeline. The steps involved are:

1. Receive natural language queries from the user.
2. Convert these queries into vector embeddings using an embedding model.
3. Perform a similarity search in a vector database to find semantically similar documents.
4. Return the most relevant context documents to be used by the language model (LLM) for generating a response.
"""

import os
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from qdrant_client import QdrantClient, models as qdrant_models

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration (from Environment Variables, Dagger will set these) ---
QDRANT_HOST = os.getenv("QDRANT_HOST_FOR_SERVICE", "http://localhost:6333")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY") # Will be passed as Dagger secret
# Model for fastembed (via qdrant-client)
EMBEDDING_MODEL_NAME = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
# This is the field in Qdrant payload assumed to hold the main text content.
PAYLOAD_TEXT_FIELD_NAME = os.environ.get("PAYLOAD_TEXT_FIELD_NAME", "document")


# --- Global Variables (Qdrant client initialized once on startup) ---
qdrant_client: QdrantClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    global qdrant_client
    
    # Startup
    logger.info("Retriever service starting up...")
    logger.info(f"Attempting to connect to Qdrant at: {QDRANT_HOST}")
    logger.info(f"Using embedding model: {EMBEDDING_MODEL_NAME}")
    logger.info(f"Expecting text in payload field: {PAYLOAD_TEXT_FIELD_NAME}")

    client_args = {"url": QDRANT_HOST, "prefer_grpc": True}
    if QDRANT_API_KEY:
        logger.info("QDRANT_API_KEY found, using for authentication.")
        client_args["api_key"] = QDRANT_API_KEY
    else:
        logger.info("No QDRANT_API_KEY found. Connecting without API key.")
    
    try:
        qdrant_client = QdrantClient(**client_args)
        # qdrant_client.health_check()
        logger.info("Successfully connected to Qdrant and health check passed.")
        
        # Optional: Pre-warm the embedding model by making a dummy call or
        # by explicitly telling qdrant_client to use/load the model.
        # For qdrant-client with fastembed, the model is usually loaded on first use.
        # You could call client.get_embedding_size(EMBEDDING_MODEL_NAME) here
        # to trigger model loading during startup.
        try:
            # Get embedding size first to check if model is available
            size = qdrant_client.get_embedding_size(EMBEDDING_MODEL_NAME)
            logger.info(f"Embedding model '{EMBEDDING_MODEL_NAME}' seems available (size: {size}).")
            
            # Now, actually force-load the model by doing a small embedding operation
            # This ensures the model is fully loaded in memory at startup time
            logger.info("Pre-warming embedding model by generating embeddings for a sample text...")
            start_time = time.time()
            
            # Use the query_points method with a minimal sample text to load model
            sample_text = "This is a sample text to load the embedding model into memory."
            try:
                _ = qdrant_client.query_points(
                    collection_name="default", # This collection doesn't need to exist, query will fail but model will load
                    query=qdrant_models.Document(
                        text=sample_text,
                        model=EMBEDDING_MODEL_NAME
                    ),
                    limit=1,
                    with_payload=False
                )
            except Exception as e:
                # This exception is expected if "default" collection doesn't exist
                # But the embedding model should still be loaded
                logger.warning(f"Pre-warming attempt triggered expected error: {e}")
            
            # Log the time it took to load the model
            logger.info(f"Model loading process took {time.time() - start_time:.2f} seconds")
            logger.info(f"Embedding model '{EMBEDDING_MODEL_NAME}' is now fully loaded and ready for queries!")
        except Exception as e:
            logger.error(f"Could not load embedding model '{EMBEDDING_MODEL_NAME}': {e}. Service might fail on first query.", exc_info=True)
            # Depending on strictness, you might raise an error here to prevent startup

    except Exception as e:
        qdrant_client = None # Ensure client is None if startup fails
        logger.error(f"Failed to initialize Qdrant client during startup: {e}", exc_info=True)
        # You might want the service to fail loudly if Qdrant connection fails
        # raise HTTPException(status_code=503, detail="Could not connect to Qdrant") from e
    
    yield
    
    # Shutdown
    logger.info("Retriever service shutting down...")
    if qdrant_client:
        try:
            qdrant_client.close()
            logger.info("Qdrant client closed successfully.")
        except Exception as e:
            logger.error(f"Error closing Qdrant client: {e}")


# FastAPI app initialization with lifespan
app = FastAPI(title="Retriever Service", lifespan=lifespan)


# --- API Models ---
class RetrieveRequest(BaseModel):
    query: str
    collection: str
    top_k: int = 5
    # You could add an optional filter parameter here if needed

class RetrievedContext(BaseModel):
    id: str
    text: str
    score: float

class RetrieveResponse(BaseModel):
    original_query: str
    retrieved_contexts: list[RetrievedContext]
    collection_used: str


@app.get("/")
async def root():
    """Root endpoint with service status."""
    return {
        "status": "ok",
        "service": "Retriever Service",
        "version": "1.0.0",
        "qdrant_connected": qdrant_client is not None
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy" if qdrant_client else "degraded",
        "timestamp": time.time(),
        "qdrant_connected": qdrant_client is not None
    }


@app.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_endpoint(request: RetrieveRequest):
    if not qdrant_client:
        logger.error("Qdrant client not initialized. Startup may have failed.")
        raise HTTPException(status_code=503, detail="Retriever service not ready: Qdrant client unavailable.")

    logger.info(f"Received retrieval request for query: '{request.query}' in collection: '{request.collection}'")
    search_start_time = time.time()

    try:
        # qdrant-client with fastembed handles embedding the query_text
        # For collections created with fastembed, we need to specify the vector name
        search_results = qdrant_client.query_points(
            collection_name=request.collection,
            query=qdrant_models.Document(
                text=request.query,
                model=EMBEDDING_MODEL_NAME # Instructs fastembed to use this model
            ),
            using="fast-bge-small-en",  # Specify the vector name for fastembed collections
            limit=request.top_k,
            with_payload=True
        )
    except Exception as e:
        logger.error(f"Error during Qdrant search for query '{request.query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Qdrant search failed: {str(e)}")
    
    search_duration = time.time() - search_start_time
    logger.info(f"Qdrant search took {search_duration:.4f} seconds.")

    retrieved_contexts_out = []
    hits = search_results.points
    for hit in hits:
        payload_text = None
        if hit.payload:
            payload_text = hit.payload.get(PAYLOAD_TEXT_FIELD_NAME)
            if payload_text is None and PAYLOAD_TEXT_FIELD_NAME != "text": # Fallback
                payload_text = hit.payload.get("text")
        
        if payload_text:
            retrieved_contexts_out.append(RetrievedContext(
                id=str(hit.id),
                text=payload_text,
                score=hit.score
            ))
        else:
            logger.warning(f"Hit with ID {hit.id} in collection '{request.collection}' has no '{PAYLOAD_TEXT_FIELD_NAME}' (or fallback 'text') field in payload.")

    logger.info(f"Retrieved {len(retrieved_contexts_out)} contexts for query: '{request.query}'")
    return RetrieveResponse(
        original_query=request.query,
        retrieved_contexts=retrieved_contexts_out,
        collection_used=request.collection
    )

# To run this service locally (outside Dagger for testing):
# uvicorn services.retriever_service.main:app --reload --port 8001
