# SmartÆgent X-7 API Endpoints and Interactions

## Service Overview

The SmartÆgent X-7 system consists of multiple microservices running on different ports with Docker networking for internal communication. This document provides a comprehensive overview of all API endpoints, their interactions, and URLs.

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

## 1. FastAPI Service (Main Application)
**External URL:** `http://localhost:8000`  
**Internal URL:** `http://fastapi:8000`

### Core API Endpoints

#### GET /
- **Description:** Root endpoint with API status
- **Response:**
  ```json
  {
    "status": "ok",
    "message": "Functional RAG Pipeline API is running",
    "version": "2.0.0",
    "initialized": true
  }
  ```

#### GET /health
- **Description:** Health check endpoint
- **Response:**
  ```json
  {
    "status": "healthy",
    "timestamp": 1717420800.0,
    "dependencies_initialized": true
  }
  ```

#### POST /rag
- **Description:** Process RAG queries (synchronous response)
- **Request Body:**
  ```json
  {
    "query": "string (required, min_length=1)",
    "collection": "string (default='default')"
  }
  ```
- **Response:**
  ```json
  {
    "query": "string",
    "answer": "string",
    "collection": "string",
    "timestamp": "string",
    "status": "string"
  }
  ```
- **Error Response:**
  ```json
  {
    "query": "string",
    "error": "string",
    "timestamp": "string",
    "status": "error"
  }
  ```

#### POST /rag/stream
- **Description:** Stream RAG responses as Server-Sent Events
- **Request Body:** Same as `/rag`
- **Response:** Server-Sent Events stream
- **Content-Type:** `text/event-stream`
- **Stream Format:**
  ```json
  data: {
    "content": "word ",
    "full_text": "accumulated text",
    "progress": 0.5,
    "is_final": false
  }
  ```

### Temporal Workflow Endpoints

#### POST /workflow/process-documents
- **Description:** Trigger document processing workflow
- **Request Body:**
  ```json
  {
    "documents": [
      {
        "id": "string",
        "text": "string",
        "metadata": {}
      }
    ]
  }
  ```
- **Response:**
  ```json
  {
    "workflow_id": "string",
    "status": "started",
    "message": "Processing N documents"
  }
  ```

#### GET /workflow/{workflow_id}/status
- **Description:** Get workflow status
- **Parameters:** `workflow_id` (path parameter)
- **Response:**
  ```json
  {
    "workflow_id": "string",
    "status": "completed|running|failed",
    "result": {},
    "error": "string"
  }
  ```

### Debug Endpoints

#### GET /debug/cache
- **Description:** View cache status and debug information
- **Response:**
  ```json
  {
    "result_cache_size": 5,
    "cached_queries": ["query1", "query2"],
    "dependencies_status": {}
  }
  ```

## 2. Embedding Service
**External URL:** `http://localhost:8002`  
**Internal URL:** `http://embedding-service:8000`

### Endpoints

#### GET /
- **Description:** Root endpoint with service status
- **Response:**
  ```json
  {
    "status": "ok",
    "service": "Embedding Service",
    "version": "1.0.0",
    "qdrant_connected": true
  }
  ```

#### GET /health
- **Description:** Health check endpoint
- **Response:**
  ```json
  {
    "status": "healthy",
    "timestamp": 1717420800.0,
    "qdrant_connected": true
  }
  ```

#### POST /index
- **Description:** Index multiple documents into Qdrant collection
- **Request Body:**
  ```json
  {
    "collection": "string (required)",
    "documents": [
      {
        "id": "string (required)",
        "text": "string (required)",
        "metadata": {}
      }
    ],
    "create_collection": true
  }
  ```
- **Response:**
  ```json
  {
    "status": "success",
    "collection": "string",
    "indexed_count": 5,
    "processing_time": 1.23
  }
  ```

#### POST /add_document
- **Description:** Add single document to collection
- **Request Body:**
  ```json
  {
    "collection": "string (required)",
    "document": {
      "id": "string (required)",
      "text": "string (required)",
      "metadata": {}
    },
    "create_collection": true
  }
  ```
- **Response:**
  ```json
  {
    "status": "success",
    "collection": "string",
    "document_id": "string",
    "processing_time": 0.45
  }
  ```

## 3. Retriever Service
**External URL:** `http://localhost:8001`  
**Internal URL:** `http://retriever-service:8000`

### Endpoints

#### GET /
- **Description:** Root endpoint with service status
- **Response:**
  ```json
  {
    "status": "ok",
    "service": "Retriever Service",
    "version": "1.0.0",
    "qdrant_connected": true
  }
  ```

#### GET /health
- **Description:** Health check endpoint
- **Response:**
  ```json
  {
    "status": "healthy",
    "timestamp": 1717420800.0,
    "qdrant_connected": true
  }
  ```

#### POST /retrieve
- **Description:** Retrieve relevant documents using semantic search
- **Request Body:**
  ```json
  {
    "query": "string (required)",
    "collection": "string (required)",
    "top_k": 5
  }
  ```
- **Response:**
  ```json
  {
    "original_query": "string",
    "retrieved_contexts": [
      {
        "id": "string",
        "text": "string",
        "score": 0.85
      }
    ],
    "collection_used": "string"
  }
  ```

## 4. Temporal API Service
**External URL:** `http://localhost:8003`  
**Internal URL:** `http://temporal-api:8000`

### Endpoints

#### GET /health
- **Description:** Health check endpoint
- **Response:**
  ```json
  {
    "status": "healthy",
    "service": "temporal-document-processing"
  }
  ```

#### POST /process-documents
- **Description:** Start document processing workflow
- **Request Body:**
  ```json
  {
    "documents": [
      {
        "id": "string",
        "text": "string",
        "metadata": {}
      }
    ],
    "workflow_id": "optional_string",
    "embedding_service_url": "optional_string"
  }
  ```
- **Response:**
  ```json
  {
    "workflow_id": "doc-processing-uuid",
    "status": "started",
    "message": "Processing N documents"
  }
  ```

#### GET /workflow/{workflow_id}/status
- **Description:** Get workflow execution status
- **Parameters:** `workflow_id` (path parameter)
- **Response:**
  ```json
  {
    "workflow_id": "string",
    "status": "completed|running|failed|unknown",
    "result": {},
    "error": "string"
  }
  ```

#### GET /workflow/{workflow_id}/result
- **Description:** Wait for and return workflow result
- **Parameters:** `workflow_id` (path parameter)
- **Response:** Workflow execution result (format depends on workflow)

## 5. Gradio Chat Interface
**External URL:** `http://localhost:7860`  
**Internal URL:** `http://gradio-chat:7860`

### Interface Features
- **Type:** Web-based chat interface (not REST API)
- **Features:**
  - Real-time streaming chat responses
  - Document collection selection
  - Debug information panels
  - Response metrics and settings
  - Service connectivity testing

## 6. Supporting Services

### Qdrant Vector Database
**External URL:** `http://localhost:6333`  
**Internal URL:** `http://qdrant:6333`
- **Purpose:** Vector storage and similarity search
- **Web UI:** Available at http://localhost:6333/dashboard
- **Health Check:** `GET /healthz`

### Temporal Server
**External URL:** `http://localhost:7233`  
**Internal URL:** `http://temporal:7233`
- **Purpose:** Workflow orchestration server
- **Protocol:** gRPC

### Temporal Web UI
**External URL:** `http://localhost:8081`
- **Purpose:** Web interface for workflow monitoring
- **Features:** Workflow execution history, debugging

### PostgreSQL
**External URL:** `http://localhost:5432`  
**Internal URL:** `http://postgresql:5432`
- **Purpose:** Database for Temporal metadata
- **Credentials:** temporal/temporal

## Service Interactions Flow

### RAG Query Flow
```
1. User Query → Gradio Interface (7860)
2. Gradio → FastAPI Service (/rag endpoint) (8000)
3. FastAPI → Retriever Service (/retrieve) (8001)
4. Retriever → Qdrant (6333) for similarity search
5. FastAPI → Generate Module (local subprocess)
6. Generate Module → OpenAI API (external)
7. FastAPI → Response back to Gradio
8. Gradio → Streamed response to user
```

### Document Indexing Flow
```
1. Documents → Temporal API (/process-documents) (8003)
2. Temporal API → Temporal Server (7233) for workflow
3. Temporal Worker → Embedding Service (/index) (8002)
4. Embedding Service → Qdrant (6333) for storage
```

### Direct Embedding Flow
```
1. Client → Embedding Service (/index or /add_document) (8002)
2. Embedding Service → Qdrant (6333) for vector storage
```

### Direct Retrieval Flow
```
1. Client → Retriever Service (/retrieve) (8001)
2. Retriever → Qdrant (6333) for similarity search
3. Retriever → Formatted results back to client
```

## Environment Variables

### Required
- `OPENAI_API_KEY` - OpenAI API authentication key

### Service URLs (Internal Communication)
- `RETRIEVER_SERVICE_URL=http://retriever-service:8000`
- `EMBEDDING_SERVICE_URL=http://embedding-service:8000`
- `FASTAPI_SERVICE_URL=http://fastapi:8000`
- `QDRANT_HOST_FOR_SERVICE=http://qdrant:6333`
- `TEMPORAL_HOST=temporal:7233`

### Optional Configuration
- `DOCUMENT_COLLECTION_NAME` - Default collection for documents
- `EMBEDDING_MODEL` - Embedding model name
- `QDRANT_API_KEY` - Qdrant authentication (if required)

## Error Handling

All services implement consistent error handling:

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request (validation errors)
- `500` - Internal Server Error
- `503` - Service Unavailable (dependency issues)

### Error Response Format
```json
{
  "detail": "Error description",
  "status_code": 500,
  "error": "Specific error message"
}
```

## Health Checks

All services provide health check endpoints that return:
- Service status
- Dependency connectivity
- Timestamp
- Service-specific metadata

Use these endpoints for monitoring and load balancer configuration.

## Authentication

Currently, the system uses:
- OpenAI API key for external LLM access
- Optional Qdrant API key for vector database
- No authentication between internal services (Docker network security)

## Development and Testing

### Local Development URLs
- FastAPI Docs: http://localhost:8000/docs
- FastAPI Redoc: http://localhost:8000/redoc
- Qdrant Dashboard: http://localhost:6333/dashboard
- Temporal Web UI: http://localhost:8081

### Testing Endpoints
Use the health check endpoints to verify service availability:
```bash
curl http://localhost:8000/health  # FastAPI
curl http://localhost:8001/health  # Retriever
curl http://localhost:8002/health  # Embedding
curl http://localhost:8003/health  # Temporal API
```

## Notes

- All services use Docker networking for internal communication
- External ports are exposed for development and monitoring
- Services automatically discover each other using Docker service names
- The system supports horizontal scaling through Docker Compose
- All responses include timing information for performance monitoring
