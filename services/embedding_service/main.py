"""
Document embedding and indexing service for RAG pipeline.
Handles document processing and vector storage in Qdrant.
Based on the working retriever service pattern.
"""

import os
import time
import logging
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from qdrant_client import QdrantClient, models as qdrant_models
from dotenv import load_dotenv

# Load .env for local development if needed, Dagger will pass env vars
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration (from Environment Variables, same as retriever service) ---
QDRANT_HOST = os.getenv("QDRANT_HOST_FOR_SERVICE", "http://qdrant:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") # Will be passed as Dagger secret
# Model for fastembed (via qdrant-client)
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# --- Global Variables (Qdrant client initialized once on startup) ---
qdrant_client = None  # type: QdrantClient

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events (same pattern as retriever service)."""
    global qdrant_client
    
    # Startup
    logger.info("Embedding service starting up...")
    logger.info(f"Attempting to connect to Qdrant at: {QDRANT_HOST}")
    logger.info(f"Using embedding model: {EMBEDDING_MODEL_NAME}")

    client_args = {"url": QDRANT_HOST, "prefer_grpc": True}
    if QDRANT_API_KEY:
        logger.info("QDRANT_API_KEY found, using for authentication.")
        client_args["api_key"] = QDRANT_API_KEY
    else:
        logger.info("No QDRANT_API_KEY found. Connecting without API key.")
    
    try:
        qdrant_client = QdrantClient(**client_args)
        logger.info("Successfully connected to Qdrant.")
        
        # Optional: Pre-warm the embedding model by making a dummy call (same as retriever)
        try:
            # Get embedding size first to check if model is available
            size = qdrant_client.get_embedding_size(EMBEDDING_MODEL_NAME)
            logger.info(f"Embedding model '{EMBEDDING_MODEL_NAME}' seems available (size: {size}).")
            
            # Pre-warm by loading the model
            logger.info("Pre-warming embedding model...")
            start_time = time.time()
            
            # Load model by attempting to use it (this will initialize fastembed)
            sample_text = "This is a sample text to load the embedding model into memory."
            try:
                # Try to get model info - this will load the model
                _ = qdrant_client.query_points(
                    collection_name="nonexistent_warmup_collection", 
                    query=qdrant_models.Document(
                        text=sample_text,
                        model=EMBEDDING_MODEL_NAME
                    ),
                    limit=1,
                    with_payload=False
                )
            except Exception as e:
                # This exception is expected if collection doesn't exist
                # But the embedding model should still be loaded
                logger.warning(f"Pre-warming attempt triggered expected error: {e}")
            
            # Log the time it took to load the model
            logger.info(f"Model loading process took {time.time() - start_time:.2f} seconds")
            logger.info(f"Embedding model '{EMBEDDING_MODEL_NAME}' is now fully loaded and ready!")
        except Exception as e:
            logger.error(f"Could not load embedding model '{EMBEDDING_MODEL_NAME}': {e}. Service might fail on first query.", exc_info=True)

    except Exception as e:
        qdrant_client = None
        logger.error(f"Failed to initialize Qdrant client during startup: {e}", exc_info=True)
    
    yield
    
    # Shutdown
    logger.info("Embedding service shutting down...")
    if qdrant_client:
        try:
            qdrant_client.close()
            logger.info("Qdrant client closed successfully.")
        except Exception as e:
            logger.error(f"Error closing Qdrant client: {e}")

# FastAPI app initialization with lifespan
app = FastAPI(title="Embedding Service", lifespan=lifespan)

# --- API Models ---
class Document(BaseModel):
    id: str
    text: str
    metadata: dict = {}

class IndexRequest(BaseModel):
    collection: str
    documents: List[Document]
    create_collection: bool = True

class IndexResponse(BaseModel):
    status: str
    collection: str
    indexed_count: int
    processing_time: float

class AddDocumentRequest(BaseModel):
    collection: str
    document: Document
    create_collection: bool = True

class AddDocumentResponse(BaseModel):
    status: str
    collection: str
    document_id: str
    processing_time: float

@app.get("/")
async def root():
    """Root endpoint with service status."""
    return {
        "status": "ok",
        "service": "Embedding Service",
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

@app.post("/index", response_model=IndexResponse)
async def index_documents(request: IndexRequest):
    """Index documents using qdrant-client with fastembed integration."""
    if not qdrant_client:
        logger.error("Qdrant client not initialized. Startup may have failed.")
        raise HTTPException(status_code=503, detail="Embedding service not ready: Qdrant client unavailable.")

    logger.info(f"Received indexing request for {len(request.documents)} documents in collection: '{request.collection}'")
    start_time = time.time()

    try:
        # Create collection if needed
        if request.create_collection:
            try:
                # Check if collection exists first
                collections = qdrant_client.get_collections().collections
                collection_exists = any(col.name == request.collection for col in collections)
                
                if not collection_exists:
                    # Use fastembed-compatible collection creation
                    qdrant_client.create_collection(
                        collection_name=request.collection,
                        vectors_config=qdrant_models.VectorParams(
                            size=384,  # Fixed size for sentence-transformers/all-MiniLM-L6-v2
                            distance=qdrant_models.Distance.COSINE,
                            hnsw_config=qdrant_models.HnswConfig(),
                            quantization_config=None,
                            on_disk=None
                        )
                    )
                    logger.info(f"Created collection: {request.collection}")
                else:
                    logger.info(f"Collection {request.collection} already exists")
            except Exception as e:
                logger.info(f"Collection handling for {request.collection}: {e}")

        # Prepare documents for qdrant-client[fastembed] upload
        # Use the add method with documents as text strings - qdrant-client[fastembed] will handle embedding
        documents_to_upload = []
        ids_list = []
        metadata_list = []
        
        for doc in request.documents:
            documents_to_upload.append(doc.text)  # Just the text string
            ids_list.append(doc.id)  # Document ID
            # Add the original text to metadata for retrieval
            payload = doc.metadata.copy()
            payload["document"] = doc.text  # Store the text in the expected field
            metadata_list.append(payload)
        
        # Upload documents - qdrant-client[fastembed] will handle embedding automatically
        qdrant_client.add(
            collection_name=request.collection,
            documents=documents_to_upload,  # List of text strings
            ids=ids_list,  # List of IDs
            metadata=metadata_list  # List of metadata dicts
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Successfully indexed {len(request.documents)} documents in {processing_time:.2f}s")
        
        return IndexResponse(
            status="success",
            collection=request.collection,
            indexed_count=len(request.documents),
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error during document indexing for collection '{request.collection}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Document indexing failed: {str(e)}")

@app.post("/add_document", response_model=AddDocumentResponse)
async def add_document(request: AddDocumentRequest):
    """Add a single document to a collection."""
    if not qdrant_client:
        logger.error("Qdrant client not initialized. Startup may have failed.")
        raise HTTPException(status_code=503, detail="Embedding service not ready: Qdrant client unavailable.")

    logger.info(f"Received request to add document {request.document.id} to collection: '{request.collection}'")
    start_time = time.time()

    try:
        # Create collection if needed
        if request.create_collection:
            try:
                # Check if collection exists first
                collections = qdrant_client.get_collections().collections
                collection_exists = any(col.name == request.collection for col in collections)
                
                if not collection_exists:
                    # Use fastembed-compatible collection creation
                    qdrant_client.create_collection(
                        collection_name=request.collection,
                        vectors_config=qdrant_models.VectorParams(
                            size=384,  # Fixed size for sentence-transformers/all-MiniLM-L6-v2
                            distance=qdrant_models.Distance.COSINE,
                            hnsw_config=qdrant_models.HnswConfig(),
                            quantization_config=None,
                            on_disk=None
                        )
                    )
                    logger.info(f"Created collection: {request.collection}")
                else:
                    logger.info(f"Collection {request.collection} already exists")
            except Exception as e:
                logger.info(f"Collection handling for {request.collection}: {e}")

        # Prepare document for upload
        doc = request.document
        payload = doc.metadata.copy()
        payload["document"] = doc.text  # Store the text in the expected field
        
        # Upload single document using the correct qdrant-client API
        qdrant_client.add(
            collection_name=request.collection,
            documents=[doc.text],  # Single document as list
            ids=[doc.id],  # Single ID as list
            metadata=[payload]  # Single metadata as list
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Successfully added document {doc.id} in {processing_time:.2f}s")
        
        return AddDocumentResponse(
            status="success",
            collection=request.collection,
            document_id=doc.id,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error adding document {request.document.id} to collection '{request.collection}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Document addition failed: {str(e)}")
