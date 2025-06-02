# SmartÆgent X-7

Enterprise-grade microservices-based Retrieval-Augmented Generation (RAG) system with interactive streaming chat interface and Temporal workflow orchestration. Built with FastAPI, Gradio, Temporal, and Docker.

## Architecture Overview

**10 containerized microservices** with full Docker orchestration:

**Core Services (5)**
- FastAPI main application server
- Gradio streaming chat interface
- Embedding service for document vectorization
- Retriever service for semantic search
- Qdrant vector database

**Temporal Services (5)**
- Temporal server (workflow engine)
- Temporal worker (workflow execution)
- Temporal API (HTTP workflow management)
- Temporal Web UI (monitoring dashboard)
- PostgreSQL (metadata storage)

## Key Features

- Real-time token streaming from OpenAI
- Interactive chat interface with modern UI
- Fault-tolerant document processing workflows
- Complete containerized architecture
- Advanced RAG with vector similarity search
- Configurable parameters and collection selection
- Built-in service connectivity testing
- Workflow monitoring and visualization
- Automated document chunking and embedding pipeline

## Quick Start

### Prerequisites

1. **Environment Configuration**
   Create `.env` file in project root:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

2. **System Requirements**
   - Docker and Docker Compose
   - Minimum 8GB RAM recommended
   - Network access for OpenAI API

### Deployment

**1. Build and start all services:**
```bash
docker-compose up --build
```

**2. Initialize vector database:**
```bash
python upload_documents.py
```

**3. Run end-to-end validation after vector database initialization:**
```bash
./e2e_test.sh
```

**Access interfaces:**
- **Chat Interface**: http://localhost:7860
- **API Documentation**: http://localhost:8000/docs
- **Temporal Web UI**: http://localhost:8081
- **Temporal API**: http://localhost:8003


## Project Structure

```
├── docker-compose.yml       # Service orchestration
├── requirements.txt         # Root dependencies
├── services/
│   ├── fastapi_service/    # Main FastAPI application
│   │   ├── main.py         # FastAPI app
│   │   ├── rag_pipeline.py # RAG implementation
│   │   ├── upload_documents.py # Vector database initialization
│   │   ├── Dockerfile      # FastAPI container
│   │   └── requirements.txt # FastAPI dependencies
│   ├── gradio_service/     # Chat interface service
│   ├── retriever_service/  # Document retrieval service
│   ├── embedding_service/  # Document embedding service
│   └── temporal_service/   # Workflow services
├── modules/
│   └── generate_module/    # Generation pipeline
└── ci/
    └── ci_pipeline.py      # CI/CD pipeline
```

## Temporal Workflows

### Document Processing Workflow

**Process Flow:**
1. Document chunking into semantic paragraphs
2. Embedding generation via embedding service
3. Vector storage in Qdrant with metadata

**Features:**
- Automatic retry mechanisms
- Progress monitoring
- Failure handling and recovery
- Batch processing optimization

### Workflow Activities

**chunk_documents_activity:**
- Intelligent document segmentation
- Content filtering and validation
- Metadata attachment

**embed_documents_activity:**
- Batch embedding generation
- Vector database storage
- Timeout handling for large datasets

## Service Architecture

### Port Configuration

**Web Interfaces**
- Gradio Chat: http://localhost:7860
- Temporal Web UI: http://localhost:8081
- FastAPI Documentation: http://localhost:8000/docs

**API Services**
- FastAPI Main: http://localhost:8000
- Retriever Service: http://localhost:8001
- Embedding Service: http://localhost:8002
- Temporal API: http://localhost:8003
- Qdrant Database: http://localhost:6333

**Internal Services**
- Temporal Server: localhost:7233
- PostgreSQL: localhost:5432

### Container Communication

All services communicate via internal Docker network with automatic service discovery and health monitoring.

## API Reference

### Core Endpoints

**POST /rag**
Standard RAG query with complete response
```json
{
  "query": "What is machine learning?",
  "collection": "document-chunks",
  "max_tokens": 500,
  "temperature": 0.7
}
```

**POST /rag/stream**
Streaming RAG query with real-time token delivery
```
data: {"token": "Machine", "done": false}
data: {"token": " learning", "done": false}
data: {"done": true}
```

**GET /health**
Service health and connectivity status

**GET /docs**
Interactive API documentation

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your-api-key

# Optional service URLs
QDRANT_URL=http://qdrant:6333
RETRIEVER_URL=http://retriever-service:8000
FASTAPI_URL=http://fastapi:8000
```

### Chat Interface Settings

- **Temperature**: Response creativity control (0.0-2.0)
- **Max Tokens**: Maximum response length (1-2000)
- **Collection**: Target document collection
- **Streaming Mode**: Real-time vs batch responses


## Operations and Maintenance

### Vector Database Operations

```bash
# Initialize vector database (required before first use)
python upload_documents.py

# Add new document collection
python upload_documents.py --collection custom-docs --data-path ./data/

# Check collection status
curl http://localhost:6333/collections/[collection-name]
```

## Troubleshooting

### Common Issues

**Service Connectivity**
```bash
# Test internal network
docker-compose exec gradio-chat ping fastapi
docker-compose exec fastapi ping retriever-service
```

**Streaming Problems**
```bash
# Verify streaming endpoint
curl -X POST http://localhost:8000/rag/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"query": "test", "collection": "document-chunks"}'
```

**Vector Database Issues**
```bash
# Reinitialize database (run upload_documents.py first)
python upload_documents.py
docker-compose restart qdrant
```

### Debug Commands

```bash
# Container shell access
docker-compose exec [service-name] bash

# Service resource usage
docker stats

# Network inspection
docker network ls
docker network inspect smartagent_default
```

## Performance Optimization

### Caching Strategy

- Automatic chat history caching in Gradio
- Persistent vector storage in Qdrant
- FastAPI response caching for repeated queries
- Temporal workflow state persistence

## Development Workflow

### Local Development

1. Fork repository and create feature branch
2. Make changes in appropriate service directory
3. Initialize vector database: `python upload_documents.py` 
4. Test with full system validation: `./e2e_test.sh`
5. Test individual services: `docker-compose up --build [service]`
6. Commit and create pull request

### Service-Specific Development

**Chat Interface**: `services/gradio_service/`
```bash
docker-compose up --build gradio-chat
```

**Embedding Pipeline**: `services/embedding_service/`
```bash
docker-compose up --build embedding-service qdrant
```

**Workflow Engine**: `services/temporal_service/`
```bash
docker-compose up --build temporal temporal-worker
```

## Security Considerations

- API keys stored in environment variables only
- Internal service communication via Docker network
- No external port exposure for internal services
- Container isolation and resource limits
- Secure credential management in production environments

## Technology Stack

**Core Framework**
- FastAPI: Async Python web framework
- Gradio: Interactive ML interfaces
- Qdrant: Vector database
- OpenAI: Large language models
- Temporal: Workflow orchestration

**Infrastructure**
- Docker: Containerization
- Docker Compose: Service orchestration
- PostgreSQL: Metadata storage
- Nginx: Load balancing (production)

## License

MIT License - see LICENSE file for details.