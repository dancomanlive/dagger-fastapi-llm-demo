import os
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from pydantic import BaseModel

from dotenv import load_dotenv

import dagger

from pipelines.document_schema import DocumentSchema


load_dotenv()


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI lifespan: Initializing Dagger client...")
    try:
        # Connect to the Dagger engine
        async with dagger.Connection() as client:
            # Store the client directly - it's already a Client object
            app.state.dagger_client = client
            logger.info("Dagger client initialized and stored in app state.")
            yield
    except Exception as e:
        logger.critical(f"An error occurred during Dagger client initialization: {e}", exc_info=True)
        raise
    finally:
        logger.info("FastAPI lifespan: Cleaning up Dagger client...")
        app.state.dagger_client = None


app = FastAPI(title="Dagger FastAPI Demo", lifespan=lifespan)


class ChatRequest(BaseModel):
    prompt: str  
    model: Optional[str] = DEFAULT_MODEL 

class ChatResponse(BaseModel):
    response: str  

@app.get("/")
async def read_root():
    return {"message": "Welcome to Dagger FastAPI Demo"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Endpoint that uses the Dagger LLM module to generate a response"""
    logger.info("/chat endpoint called. Using Dagger client from app state.")

    try:
        if not os.environ.get("OPENAI_API_KEY"):
            logger.error("OPENAI_API_KEY not found in environment or .env file")
            raise HTTPException(status_code=400, detail="OPENAI_API_KEY not found")
        
        client = app.state.dagger_client
        llm = client.llm().with_model(request.model).with_prompt(request.prompt)

        result = await llm.last_reply()
        logger.info(f"Received response from LLM with model {request.model}")
        return ChatResponse(response=result)

    except Exception as e:
        logger.exception(f"Error during LLM execution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/hello")
async def hello_world_endpoint(name: str = "World"):
    """Endpoint that executes a simple hello-world function using a container with custom name"""
    logger.info(f"/hello endpoint called with name: {name}. Using Dagger client from app state.")

    try:
        from tools.hello import hello_world
        
        # Use the client from app state
        if not app.state.dagger_client:
            raise HTTPException(status_code=500, detail="Dagger client not initialized")
            
        client = app.state.dagger_client
        message = await hello_world(client, name)
        
        logger.info(f"Received message from hello-world function: {message}")
        return {"message": message}

    except Exception as e:
        logger.exception(f"Error executing hello-world container: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# RAG Models
class DocumentIngestionRequest(BaseModel):
    text: str
    document_id: str
    project_id: str
    index_name: Optional[str] = "default_index"
    chunk_size: Optional[int] = 1000
    overlap: Optional[int] = 200
    respect_sections: Optional[bool] = True
    metadata: Optional[Dict[str, Any]] = None

class RagQueryRequest(BaseModel):
    query: str
    project_id: str
    index_name: Optional[str] = "default_index"
    use_nlq: Optional[bool] = True
    weights: Optional[Dict[str, float]] = None
    filters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = 5
    model: Optional[str] = None

# RAG Endpoints
@app.post("/rag/ingest")
async def ingest_document_endpoint(request: DocumentIngestionRequest):
    """Endpoint to ingest a document into the RAG system"""
    logger.info(f"/rag/ingest endpoint called for document_id: {request.document_id}")

    try:
        from pipelines.rag_pipeline import ingest_document
        
        # Use the client from app state
        client = app.state.dagger_client
        
        # Ingest document
        result = await ingest_document(
            client=client,
            text=request.text,
            document_id=request.document_id,
            project_id=request.project_id,
            index_name=request.index_name,
            chunk_size=request.chunk_size,
            overlap=request.overlap,
            respect_sections=request.respect_sections,
            metadata=request.metadata
        )
        
        logger.info(f"Document ingested: {request.document_id}")
        return {"result": result}

    except Exception as e:
        logger.exception(f"Error ingesting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/query")
async def query_rag_endpoint(request: RagQueryRequest):
    """Endpoint to query the RAG system with citations"""
    logger.info(f"/rag/query endpoint called with query: {request.query}")

    try:
        from pipelines.rag_pipeline import query_rag
        
        # Use the client from app state
        client = app.state.dagger_client
        
        # Set model from environment if not specified
        model = request.model or os.environ.get("LLM_MODEL", DEFAULT_MODEL)
        
        # Query RAG system with citations
        result = await query_rag(
            client=client,
            query=request.query,
            project_id=request.project_id,
            index_name=request.index_name,
            use_nlq=request.use_nlq,
            weights=request.weights,
            filters=request.filters,
            limit=request.limit,
            model=model
        )
        
        logger.info(f"RAG query processed with citations: {request.query}")
        return {"result": result}

    except Exception as e:
        logger.exception(f"Error processing RAG query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate-document")
async def validate_document_endpoint(document: DocumentSchema):
    """
    Endpoint to validate a document against the schema.
    """
    return {"status": "success", "document": document.dict()}