import os
import logging
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException

from pydantic import BaseModel

from dotenv import load_dotenv

import dagger
from schemas.document_schema import DocumentSchema



load_dotenv()


logging.basicConfig(level=logging.INFO)

# Suppress the httpx logs that come from Dagger's HTTP communication
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

# No longer using a shared Dagger client via asynccontextmanager
# Each endpoint will create its own Dagger connection as needed

app = FastAPI(title="Dagger FastAPI Demo")


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
    logger.info("/chat endpoint called. Creating Dagger connection...")

    try:
        if not os.environ.get("OPENAI_API_KEY"):
            logger.error("OPENAI_API_KEY not found in environment or .env file")
            raise HTTPException(status_code=400, detail="OPENAI_API_KEY not found")
        
        # Create a new Dagger connection for this request
        async with dagger.Connection() as client:
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
    logger.info(f"/hello endpoint called with name: {name}. Creating Dagger connection...")

    try:
        from modules.tools.hello_tool import hello_world
        
        # Create a new Dagger connection for this request
        async with dagger.Connection() as client:
            message = await hello_world(client, name)
        
        logger.info(f"Received message from hello-world function: {message}")
        return {"message": message}

    except Exception as e:
        logger.exception(f"Error executing hello-world container: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/validate-document")
async def validate_document_endpoint(document: DocumentSchema):
    """
    Endpoint to validate a document against the schema.
    """
    return {"status": "success", "document": document.dict()}


class QdrantConnectionRequest(BaseModel):
    qdrant_url: Optional[str] = None

class QdrantConnectionResponse(BaseModel):
    status: str
    message: str

@app.post("/test-qdrant", response_model=QdrantConnectionResponse)
async def test_qdrant_endpoint(request: QdrantConnectionRequest = QdrantConnectionRequest()):
    """
    Endpoint to test the connection to Qdrant vector database.
    Optionally specify a custom Qdrant URL, otherwise uses the environment configuration.
    """
    import time
    start_time = time.time()
    logger.info("/test-qdrant endpoint called. Creating Dagger connection...")

    try:
        from modules.tools.qdrant_tool import test_qdrant_connection
        
        connection_start = time.time()
        # Create a new Dagger connection for this request
        async with dagger.Connection() as client:
            connection_time = time.time() - connection_start
            
            execution_start = time.time()
            # Pass the custom URL if provided
            output = await test_qdrant_connection(client, request.qdrant_url)
            execution_time = time.time() - execution_start
        
        total_time = time.time() - start_time
        logger.info(f"Qdrant connection test timing: connection={connection_time:.3f}s, execution={execution_time:.3f}s, total={total_time:.3f}s")
        return QdrantConnectionResponse(
            status="success", 
            message=f"Qdrant connection successful: {output} (completed in {total_time:.3f}s)"
        )

    except Exception as e:
        total_time = time.time() - start_time
        logger.exception(f"Error testing Qdrant connection: {str(e)} (failed after {total_time:.3f}s)")
        return QdrantConnectionResponse(
            status="error", 
            message=f"Qdrant connection test failed: {str(e)} (after {total_time:.3f}s)"
        )