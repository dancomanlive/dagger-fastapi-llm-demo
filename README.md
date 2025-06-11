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
- `services/gradio_service/main.py`: Chat UI with Temporal client integration.
- `services/temporal_service/workflows.py`: RetrievalWorkflow and DocumentProcessingWorkflow.
- `services/temporal_service/activities.py`: Workflow activities (chunking, embedding).
- `services/retriever_service/activities.py`: Vector search activities for Temporal.
- `services/embedding_service/activities.py`: Text embedding activities for Temporal.

---

## Service Summary Table

| Service           | Purpose                        | Key Functions                     |
|-------------------|-------------------------------|-----------------------------------|
| Gradio            | Chat UI + Temporal Client     | Web interface, workflow triggers |
| Temporal Worker   | Workflow orchestration        | RetrievalWorkflow, Activities     |
| Retriever         | Vector search activities      | search_vectors, index_vectors     |
| Embedding         | Text embedding activities     | embed_text, embed_query           |
| Qdrant            | Vector Database               | Document storage, similarity      |
| PostgreSQL        | Temporal State Store          | Workflow persistence              |

---

## Quick Start

### Prerequisites
1. **Environment Configuration**
   - Create `.env` file in project root with `OPENAI_API_KEY`
2. **System Requirements**
   - Docker and Docker Compose
   - Network access for OpenAI API

### Deployment
1. **Build and start all services:**
   ```bash
   docker-compose up --build
   ```
2. **Upload documents to vector database:**
   ```bash
   python upload_documents.py
   ```

**Access interfaces:**
- **Chat Interface**: http://localhost:7860 (Main user interface)
- **Temporal Web UI**: http://localhost:8081 (Workflow monitoring)
- **Qdrant UI**: http://localhost:6333/dashboard (Vector database)

---

## Project Structure

```
├── docker-compose.yml       # Simplified Temporal-based orchestration
├── requirements.txt         # Root dependencies  
├── services/
│   ├── gradio_service/     # Chat interface + Temporal client
│   │   ├── main.py         # Gradio app with Temporal integration
│   │   ├── tests/          # Temporal integration tests
│   │   ├── features/       # BDD scenarios
│   │   ├── Dockerfile      # Gradio container
│   │   └── requirements.txt # Gradio dependencies
│   ├── temporal_service/   # Workflow orchestration
│   │   ├── workflows.py    # RetrievalWorkflow, DocumentProcessingWorkflow
│   │   ├── activities.py   # Document processing activities
│   │   ├── worker.py       # Temporal worker
│   │   ├── tests/          # Workflow tests
│   │   └── features/       # BDD scenarios
│   ├── retriever_service/  # Vector search activities
│   │   ├── activities.py   # search_vectors, index_vectors
│   │   ├── worker.py       # Activity worker
│   │   └── tests/          # Activity tests
│   └── embedding_service/  # Text embedding activities
│       ├── activities.py   # embed_text, embed_query
│       ├── worker.py       # Activity worker
│       └── tests/          # Activity tests
└── ci/
    └── ci_pipeline.py      # CI/CD pipeline
```

---

## License

MIT License - see LICENSE file for details.