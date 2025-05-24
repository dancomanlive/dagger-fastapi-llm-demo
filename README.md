# FastAPI RAG Demo

A simple Retrieval-Augmented Generation (RAG) system built with FastAPI and Docker.

## Quick Start

1. **Start all services in Docker:**
   ```bash
   docker-compose up
   ```

2. **Initialize the vector database (runs locally):**
   ```bash
   python init_qdrant.py
   ```

3. **Test the API:**
   - Open http://localhost:8000/docs for the interactive API documentation
   - Or make a request: `curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{"query": "your question here"}'`

## Project Structure

```
├── main.py                 # FastAPI application
├── rag_pipeline.py         # RAG pipeline implementation
├── init_qdrant.py         # Vector database initialization
├── docker-compose.yml     # Service orchestration
├── Dockerfile             # Container configuration
├── requirements.txt       # Python dependencies
├── modules/
│   ├── retriever_service/ # Document retrieval service
│   └── generate/          # Text generation service
└── ci/
    └── ci_pipeline.py     # CI/CD pipeline
```

## Services

- **FastAPI App**: Main application (http://localhost:8000)
- **Retriever Service**: Document search service (http://localhost:8001)
- **Qdrant**: Vector database (http://localhost:6333)

## Architecture

This project runs entirely in Docker containers - no local development setup is required or supported. The only script that runs locally is the Qdrant initialization to populate the database with sample data.

## API Endpoints

- `POST /query` - Submit a question to the RAG system
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation

That's it! The system is designed to be simple and straightforward to use.
