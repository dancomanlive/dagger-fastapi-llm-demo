# Gradio Chat Service

A web-based chat interface for the RAG (Retrieval-Augmented Generation) pipeline.

## Features

- **Real-time streaming responses** from OpenAI
- **Interactive chat interface** with history
- **Document collection selection** 
- **Debug information panel** showing retrieved documents
- **Response metrics and settings** configuration
- **Docker-ready** microservice architecture

## API Endpoints

The Gradio service provides a web interface at `http://localhost:7860` and connects to:

- **FastAPI Service** (`http://fastapi:8000`) - Main application backend
- **Retriever Service** (`http://retriever-service:8000`) - Document retrieval

## Environment Variables

- `OPENAI_API_KEY` - OpenAI API key for chat completions
- `FASTAPI_SERVICE_URL` - URL of the main FastAPI service
- `RETRIEVER_SERVICE_URL` - URL of the retriever service

## Usage

The service is automatically started as part of the Docker Compose stack:

```bash
docker-compose up gradio-chat
```

Access the chat interface at: http://localhost:7860

## Dependencies

- `gradio>=4.0.0` - Web interface framework
- `openai>=1.0.0` - OpenAI API client
- `requests>=2.31.0` - HTTP client
- `python-dotenv>=1.0.0` - Environment variable management
