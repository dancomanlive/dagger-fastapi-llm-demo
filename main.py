# Import required standard Python libraries for OS operations, system interactions, and logging
import os
import sys
import logging
# Import Optional type hint for type checking
from typing import Optional
# Import asynccontextmanager for managing asynchronous context
from contextlib import asynccontextmanager

# Import FastAPI for building the web API
from fastapi import FastAPI
# Import BaseModel from Pydantic for data validation and serialization
from pydantic import BaseModel
# Import load_dotenv to load environment variables from a .env file
from dotenv import load_dotenv

# Import dagger for interacting with the Dagger client
import dagger

# Load environment variables from .env file
load_dotenv()

# Configure basic logging with INFO level
logging.basicConfig(level=logging.INFO)
# Create a logger instance for this module
logger = logging.getLogger(__name__)

# Set default model from environment variable OPENAI_MODEL, fallback to "gpt-4o"
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

# Define an asynchronous context manager for FastAPI application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Dagger configuration with stderr logging
    config = dagger.Config(log_output=sys.stderr)
    # Establish connection to Dagger client
    async with dagger.Connection(config) as client:
        # Store Dagger client in FastAPI app state
        app.state.dagger_client = client
        # Log successful connection establishment
        logger.info("Dagger connection established.")
        # Yield control back to FastAPI, keeping the context alive
        yield
        # Log connection closure when context is exited
        logger.info("Dagger connection closed.")

# Initialize FastAPI application with title and custom lifespan
app = FastAPI(title="Dagger FastAPI Demo", lifespan=lifespan)

# Define Pydantic model for chat request payload
class ChatRequest(BaseModel):
    prompt: str  # Required field for user prompt
    model: Optional[str] = DEFAULT_MODEL  # Optional model field with default value

# Define Pydantic model for chat response payload
class ChatResponse(BaseModel):
    response: str  # Required field for response content

# Define root endpoint for GET requests
@app.get("/")
async def read_root():
    # Return a welcome message
    return {"message": "Welcome to Dagger FastAPI Demo"}

# Define chat endpoint for POST requests
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Retrieve Dagger client from app state
    client = app.state.dagger_client

    try:
        # Check if OPENAI_API_KEY is set in environment
        if not os.environ.get("OPENAI_API_KEY"):
            # Log error if API key is missing
            logger.error("OPENAI_API_KEY not found in environment or .env file")
            # Return error response
            return ChatResponse(
                response="Error: OPENAI_API_KEY not found. Please set it in your environment or .env file."
            )
        
        # Configure LLM with specified model and prompt
        llm = client.llm().with_model(request.model).with_prompt(request.prompt)

        # Await and retrieve the last reply from LLM
        result = await llm.last_reply()
        # Return successful response with LLM output
        return ChatResponse(response=result)

    except Exception as e:
        # Log any exceptions that occur during LLM execution
        logger.exception("Error during LLM execution")
        # Return error response with exception details
        return ChatResponse(response=f"Error: {e}")