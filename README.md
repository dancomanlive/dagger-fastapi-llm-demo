# SmartÆgent X-7

Enterprise-grade microservices-based Retrieval-Augmented Generation (RAG) system with interactive streaming chat interface and Temporal workflow orchestration. Built with FastAPI, Gradio, Temporal, and Docker.

---

## C4 Architecture Overview

### 1. Context
- **System:** SmartÆgent X-7 — RAG platform for interactive chat and document processing.
- **Users:**
  - End Users (web chat interface)
  - Developers (API)
  - Administrators (Temporal UI, monitoring)
- **External Systems:**
  - OpenAI API (LLM completions)
  - PostgreSQL (metadata storage)
  - Docker infrastructure

### 2. Containers
**Main containers/services:**
- **Gradio Service:** Web-based chat UI for users. Connects to FastAPI and Retriever services.
- **FastAPI Service:** Main API server. Orchestrates RAG pipeline, exposes `/rag` endpoints, and integrates with Temporal workflows.
- **Retriever Service:** FastAPI microservice for semantic search. Queries Qdrant for relevant document chunks.
- **Embedding Service:** FastAPI microservice for document embedding and indexing. Stores vectors in Qdrant.
- **Temporal Services:**
  - Temporal Server (workflow engine)
  - Temporal Worker (executes workflows)
  - Temporal API (HTTP workflow management)
  - Temporal Web UI (monitoring dashboard)
- **Qdrant:** Vector database for storing and searching embeddings.
- **PostgreSQL:** Metadata storage for Temporal.

**Container Interactions:**
- Gradio → FastAPI (chat, RAG queries)
- FastAPI → Retriever (semantic search)
- FastAPI → Temporal API (workflow management)
- Temporal Worker → Embedding Service (embedding via HTTP)
- Embedding/Retriever → Qdrant (vector storage/search)

### 3. Components
**(Example: FastAPI Service)**
- **RAG Pipeline:** Orchestrates retrieval and generation, calls Retriever and OpenAI.
- **Workflow Endpoints:** Triggers Temporal workflows for document processing.
- **Cache/State Management:** Caches results for performance.
- **API Models:** Defines request/response schemas.

**(Example: Temporal Worker)**
- **Chunk Documents Activity:** Splits documents into paragraphs.
- **Embed Documents Activity:** Calls Embedding Service for vectorization.
- **Workflow Definitions:** Orchestrates chunking and embedding steps.

### 4. Code/Implementation
- `services/fastapi_service/main.py`: FastAPI app, `/rag` endpoints, workflow triggers.
- `services/fastapi_service/rag_pipeline.py`: Implements RAG logic.
- `services/retriever_service/main.py`: `/retrieve` endpoint, Qdrant search logic.
- `services/embedding_service/main.py`: `/index`, `/add_document`, `/health` endpoints, Qdrant vector storage.
- `services/temporal_service/activities.py`: Workflow activities (chunking, embedding).
- `services/temporal_service/workflows.py`: Workflow orchestration logic.

---

## Service Summary Table

| Service           | Purpose                        | Key Endpoints/Functions           |
|-------------------|-------------------------------|-----------------------------------|
| Gradio            | Chat UI                       | Web interface                     |
| FastAPI           | Main API, RAG, workflows      | `/rag`, `/rag/stream`, `/health`  |
| Retriever         | Semantic search               | `/retrieve`, `/health`            |
| Embedding         | Document embedding/indexing   | `/index`, `/add_document`, `/health` |
| Temporal Worker   | Workflow execution            | Activities: chunk, embed          |
| Qdrant            | Vector DB                     | N/A (internal)                    |
| PostgreSQL        | Metadata DB                   | N/A (internal)                    |

---

## Quick Start

### Prerequisites
1. **Environment Configuration**
   - Create `.env` file in project root
2. **System Requirements**
   - Docker and Docker Compose
   - Network access for OpenAI API

### Deployment
1. **Build and start all services:**
   ```bash
   docker-compose up --build
   ```
2. **Run end-to-end validation:**
   ```bash
   ./e2e_test.sh
   ```
3. **Upload docs to vector database:**
   ```bash
   python upload_documents.py
   ```

**Access interfaces:**
- **Chat Interface**: http://localhost:7860
- **API Documentation**: http://localhost:8000/docs
- **Temporal Web UI**: http://localhost:8081
- **Temporal API**: http://localhost:8003

---

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

---

## License

MIT License - see LICENSE file for details.