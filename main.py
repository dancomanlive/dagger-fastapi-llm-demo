import os
import sys
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

import dagger

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

@asynccontextmanager
async def lifespan(app: FastAPI):
    config = dagger.Config(log_output=sys.stderr)
    async with dagger.Connection(config) as client:
        app.state.dagger_client = client
        logger.info("Dagger connection established.")
        yield
        logger.info("Dagger connection closed.")

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
    client = app.state.dagger_client

    try:
        if not os.environ.get("OPENAI_API_KEY"):
            logger.error("OPENAI_API_KEY not found in environment or .env file")
            return ChatResponse(
                response="Error: OPENAI_API_KEY not found. Please set it in your environment or .env file."
            )
        
        llm = client.llm().with_model(request.model).with_prompt(request.prompt)

        result = await llm.last_reply()
        return ChatResponse(response=result)

    except Exception as e:
        logger.exception("Error during LLM execution")
        return ChatResponse(response=f"Error: {e}")