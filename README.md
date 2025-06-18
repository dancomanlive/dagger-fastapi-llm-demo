# SmartÆgent X-7

Microservice orchestration platform for Retrieval-Augmented Generation (RAG) using Temporal workflows. Features distributed document processing, vector search, and interactive chat interface with full workflow visibility and monitoring.

---

## Temporal Microservice Orchestration

### Architecture Overview
SmartÆgent X-7 demonstrates **microservice orchestration using Temporal workflows** for distributed RAG operations. Each service runs as an independent container with Temporal coordinating complex document processing pipelines.

**Core Orchestration Pattern:**
```
Gradio UI → Temporal Workflows → Distributed Activities → Vector Database
```

### Temporal Workflow Benefits
- **Reliability**: Automatic retries, error handling, and state persistence
- **Scalability**: Horizontal scaling of individual microservices
- **Visibility**: Full workflow execution monitoring via Temporal UI
- **Durability**: Workflow state survives service restarts and failures
- **Composition**: Complex pipelines built from simple, reusable activities

### 1. Context
- **System:** SmartÆgent X-7 — Temporal-orchestrated RAG platform demonstrating microservice coordination
- **Users:**
  - End Users (Gradio chat interface)
  - Developers (Temporal workflow monitoring)
  - DevOps (Container orchestration)
- **External Systems:**
  - OpenAI API (LLM completions)
  - Temporal Server (workflow orchestration)
  - Vector Database (Qdrant)

### 2. Microservice Architecture
**Temporal-Orchestrated Services:**
- **Gradio Service:** Interactive chat interface with Temporal workflow triggers
- **Temporal Service:** Workflow orchestration engine executing distributed activities
- **Retriever Service:** Vector search microservice (Temporal activities)
- **Embedding Service:** Document embedding microservice (Temporal activities)
- **Workflow Composer Service:** Advanced workflow composition and agent orchestration

**Infrastructure Services:**
- **Temporal Server:** Workflow engine with persistence and monitoring
- **Qdrant:** Vector database for semantic search
- **PostgreSQL:** Temporal metadata storage

**Microservice Communication Pattern:**
```
Chat Request → Temporal Workflow → Activity Tasks → Service Workers → Results
```
All service coordination flows through Temporal workflows, eliminating point-to-point service dependencies.

### 3. Temporal Workflow Components
**Document Processing Workflow:**
- **Document Upload Activity:** Handles file ingestion and validation
- **Text Chunking Activity:** Splits documents into semantic chunks
- **Embedding Activity:** Generates vector embeddings for chunks
- **Vector Storage Activity:** Stores embeddings in Qdrant

**RAG Query Workflow:**
- **Query Processing Activity:** Normalizes and validates user queries
- **Vector Retrieval Activity:** Searches for relevant document chunks
- **Context Assembly Activity:** Combines retrieved chunks for LLM context
- **Response Generation Activity:** Integrates with OpenAI for final response

**Workflow Orchestration Benefits:**
- Each activity runs in isolated microservices
- Automatic retry and error handling
- Full execution history and monitoring
- Horizontal scaling of individual activities

### 4. Implementation Architecture
**Microservice Implementation:**
- `services/temporal_service/workflows.py`: Workflow definitions for document processing and RAG
- `services/temporal_service/activities.py`: Cross-cutting workflow activities
- `services/retriever_service/activities.py`: Vector search activities
- `services/embedding_service/activities.py`: Text embedding activities
- `services/gradio_service/main.py`: Chat UI with Temporal workflow integration
- `services/workflow_composer_service/`: Advanced workflow composition engine

**Key Architecture Patterns:**
- **Activity Pattern**: Each microservice exposes Temporal activities
- **Workflow Pattern**: Complex operations composed of distributed activities
- **Saga Pattern**: Long-running transactions with compensation
- **Event Sourcing**: Full workflow execution history

---

## Microservice Orchestration Summary

| Service           | Role                          | Temporal Integration          |
|-------------------|-------------------------------|-------------------------------|
| Gradio            | Chat UI + Workflow Triggers  | Temporal client, workflow API |
| Temporal Worker   | Workflow orchestration        | Workflow definitions, routing |
| Retriever         | Vector search microservice    | Temporal activities           |
| Embedding         | Text embedding microservice   | Temporal activities           |
| Workflow Composer | Advanced orchestration        | Meta-workflows, composition   |
| Qdrant            | Vector Database               | Data persistence layer        |
| PostgreSQL        | Temporal State Store          | Workflow state persistence    |

**Orchestration Flow:**
1. User interaction → Gradio triggers Temporal workflow
2. Temporal Worker coordinates distributed activities
3. Activities execute in isolated microservices
4. Results flow back through workflow to UI
5. Full execution history available in Temporal UI

---

## Testing & Development

### Microservice Testing Strategy
- **Unit Tests**: Individual service tests in `services/*/tests/`
- **Workflow Tests**: Temporal workflow integration tests
- **Activity Tests**: Distributed activity execution tests
- **E2E Tests**: Full pipeline orchestration tests

### Running Tests
```bash
# Test all microservices
python run_tests.py

# Test end-to-end workflows
scripts/e2e_test.sh

# Clean test data
scripts/cleanup_collections.sh
```

---

## Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key in `.env` file: `OPENAI_API_KEY=your_key_here`

### Launch Platform
```bash
# 1. Build and start all microservices
docker-compose up --build && docker-compose up -d

# 2. Upload documents (only local setup required)
python upload_documents.py
```

### Experience Temporal Orchestration
1. **Monitor Workflows**: http://localhost:8081 (Temporal UI)
   - Watch document processing workflows in real-time
   - See activity execution across distributed services
   - Monitor workflow history and performance

2. **Chat Interface**: http://localhost:7860 (Gradio UI)
   - Ask questions about uploaded documents
   - Observe retrieved document chunks in responses
   - Each query triggers a complete RAG workflow

3. **Vector Database**: http://localhost:6333/dashboard (Qdrant UI)
   - Explore processed document embeddings
   - View vector search operations

### Workflow Visualization
- Document upload → Temporal orchestrates: chunking → embedding → storage
- Chat query → Temporal orchestrates: search → retrieval → response generation
- All operations visible in Temporal UI with full execution traces

---

## Project Structure

```
├── docker-compose.yml       # Microservice orchestration with Temporal
├── upload_documents.py     # Document upload utility (local setup)
├── scripts/                # Testing and maintenance automation
│   ├── e2e_test.sh        # End-to-end workflow testing
│   └── cleanup_collections.sh # Vector database cleanup
├── tests/                  # Workflow and integration tests
│   ├── test_temporal_e2e.py # Temporal workflow tests
│   └── test_*.py          # Service integration tests
├── document_files/         # Sample documents for testing
├── services/               # Temporal-orchestrated microservices
│   ├── gradio_service/     # Chat UI + Temporal workflow triggers
│   │   ├── main.py         # Gradio app with workflow integration
│   │   ├── rag_service.py  # RAG workflow client
│   │   └── Dockerfile      # Containerized UI service
│   ├── temporal_service/   # Workflow orchestration engine
│   │   ├── workflows.py    # Document and RAG workflow definitions
│   │   ├── activities.py   # Workflow activities
│   │   ├── worker.py       # Temporal worker process
│   │   └── normalization.py # Data transformation utilities
│   ├── retriever_service/  # Vector search microservice
│   │   ├── activities.py   # Vector search Temporal activities
│   │   ├── worker.py       # Activity worker process
│   │   └── Dockerfile      # Containerized retrieval service
│   ├── embedding_service/  # Text embedding microservice
│   │   ├── activities.py   # Embedding Temporal activities
│   │   ├── worker.py       # Activity worker process
│   │   └── Dockerfile      # Containerized embedding service
│   └── workflow_composer_service/ # Advanced workflow orchestration
│       ├── activities.py   # Composition activities
│       ├── agents/         # AI agent workflows
│       └── api/            # GraphQL workflow API
└── ci/
    └── ci_pipeline.py      # CI/CD automation
```

---

## License

MIT License - see LICENSE file for details.