"""
Document embedding and indexing service for RAG pipeline.
Handles document processing and vector storage in Qdrant.
"""

import os
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from qdrant_client import QdrantClient, models as qdrant_models
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST_FOR_SERVICE", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
PAYLOAD_TEXT_FIELD_NAME = os.getenv("PAYLOAD_TEXT_FIELD_NAME", "document")

qdrant_client: QdrantClient | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global qdrant_client
    
    # Startup - same connection logic as retriever
    logger.info("Embedding service starting up...")
    qdrant_client = QdrantClient(url=QDRANT_HOST, api_key=QDRANT_API_KEY)
    
    yield
    
    # Shutdown
    if qdrant_client:
        qdrant_client.close()

app = FastAPI(title="Embedding Service", lifespan=lifespan)

# API Models
class Document(BaseModel):
    id: str
    text: str
    metadata: dict = {}

class IndexRequest(BaseModel):
    collection: str
    documents: list[Document]
    create_collection: bool = True

class IndexResponse(BaseModel):
    status: str
    collection: str
    indexed_count: int
    processing_time: float

@app.post("/index", response_model=IndexResponse)
async def index_documents(request: IndexRequest):
    if not qdrant_client:
        raise HTTPException(status_code=503, detail="Qdrant client unavailable")
    
    start_time = time.time()
    
    # Create collection if needed
    if request.create_collection:
        try:
            qdrant_client.create_collection(
                collection_name=request.collection,
                vectors_config=qdrant_models.VectorParams(
                    size=qdrant_client.get_embedding_size(EMBEDDING_MODEL_NAME),
                    distance=qdrant_models.Distance.COSINE
                )
            )
            logger.info(f"Created collection: {request.collection}")
        except Exception as e:
            logger.info(f"Collection {request.collection} already exists or creation failed: {e}")
    
    # Prepare documents for embedding
    documents = [
        qdrant_models.Document(
            text=doc.text,
            model=EMBEDDING_MODEL_NAME
        ) for doc in request.documents
    ]
    
    # Create payloads with text and metadata
    payloads = []
    for doc in request.documents:
        payload = {PAYLOAD_TEXT_FIELD_NAME: doc.text}
        payload.update(doc.metadata)  # Add any additional metadata
        payloads.append(payload)
    
    # Index documents
    try:
        qdrant_client.add(
            collection_name=request.collection,
            documents=documents,
            ids=[doc.id for doc in request.documents],
            payloads=payloads
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Indexed {len(request.documents)} documents in {processing_time:.2f}s")
        
        return IndexResponse(
            status="success",
            collection=request.collection,
            indexed_count=len(request.documents),
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Failed to index documents: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy" if qdrant_client else "degraded",
        "service": "embedding_service",
        "qdrant_connected": qdrant_client is not None
    }