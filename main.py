import os
import logging
import json
from typing import Optional
from contextlib import asynccontextmanager


from fastapi import FastAPI, HTTPException # Added HTTPException

from pydantic import BaseModel

from dotenv import load_dotenv


import dagger
from dagger import dag


load_dotenv()


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI lifespan: Initializing Dagger client...")
    try:
        async with dagger.connection() as client:
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
    logger.info("/chat endpoint called. Using Dagger global client.")

    try:
        if not os.environ.get("OPENAI_API_KEY"):
            logger.error("OPENAI_API_KEY not found in environment or .env file")
            raise HTTPException(status_code=400, detail="OPENAI_API_KEY not found")
        
        llm = dag.llm().with_model(request.model).with_prompt(request.prompt)

        result = await llm.last_reply()
        logger.info(f"Received response from LLM with model {request.model}")
        return ChatResponse(response=result)

    except Exception as e:
        logger.exception(f"Error during LLM execution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def get_module_execution_command(module_name, class_name, method_name):
    """Generate a standardized Python command to execute a module"""
    return f"from {module_name} import {class_name}; obj = {class_name}(); print(obj.{method_name}())"

@app.get("/echo")
async def echo_endpoint(text: str = "Hello from Dagger"):
    """Endpoint that echoes the provided text using a Dagger container"""
    logger.info(f"/echo endpoint called with text: {text}. Using Dagger global client.")

    try:
        from dagger_tools import echo
        
        # Use the functional approach
        result = await echo(dag, text)
        
        logger.info(f"Received echo from container: {result}")
        return {"message": result}

    except Exception as e:
        logger.exception(f"Error executing echo container: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/hello")
async def hello_world_endpoint(name: str = "World"):
    """Endpoint that executes a simple hello-world function using a container with custom name"""
    logger.info(f"/hello endpoint called with name: {name}. Using Dagger global client.")

    try:
        from dagger_tools import hello_world
        
        # Use the functional approach
        message = await hello_world(dag, name)
        
        logger.info(f"Received message from hello-world function: {message}")
        return {"message": message}

    except Exception as e:
        logger.exception(f"Error executing hello-world container: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process")
async def process_data_endpoint(data: dict):
    """Endpoint that processes data using a Dagger container"""
    logger.info("/process endpoint called with data. Using Dagger global client.")

    try:
        from dagger_tools import process_data
        import json
        
        # Convert dict to JSON string for processing
        json_data = json.dumps(data)
        
        # Use the functional approach
        result = await process_data(dag, json_data)
        
        # Parse result back to dict
        processed_data = json.loads(result)
        
        logger.info("Processed data in container")
        return {"result": processed_data}

    except Exception as e:
        logger.exception(f"Error processing data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-text")
async def analyze_text_endpoint(request: dict):
    """Endpoint that analyzes text using a Dagger container"""
    if "text" not in request:
        raise HTTPException(status_code=400, detail="Text field is required")
        
    text = request["text"]
    logger.info(f"Analyzing text with {len(text)} characters")

    try:
        from dagger_tools import analyze_text
        
        # Use the functional approach
        result = await analyze_text(dag, text)
        
        # Parse result back to dict
        analysis_result = json.loads(result)
        
        logger.info("Text analysis completed")
        return {"analysis": analysis_result}

    except Exception as e:
        logger.exception(f"Error analyzing text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/filter-csv")
async def filter_csv_endpoint(request: dict):
    """Endpoint that filters CSV data using a Dagger container"""
    required_fields = ["csv_data", "column", "value"]
    for field in required_fields:
        if field not in request:
            raise HTTPException(status_code=400, detail=f"{field} field is required")
    
    csv_data = request["csv_data"]
    column = request["column"]
    value = request["value"]
    
    logger.info(f"Filtering CSV data on {column}={value}")

    try:
        from dagger_tools import filter_csv
        
        # Use the functional approach
        result = await filter_csv(dag, csv_data, column, value)
        
        # Parse result back to dict
        filter_result = json.loads(result)
        
        logger.info(f"CSV filtering completed, found {filter_result.get('count', 0)} matching rows")
        return {"result": filter_result}

    except Exception as e:
        logger.exception(f"Error filtering CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))