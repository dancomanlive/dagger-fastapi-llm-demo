# SmartÆgent X-7

A sophisticated **microservices-based** Retrieval-Augmented Generation (RAG) system with interactive streaming chat interface and Temporal workflow orchestration. Built with FastAPI, Gradio, Temporal, and Docker.

## 🏗️ Architecture

**10 containerized microservices** working together:
- **5 Core Services**: FastAPI, Gradio Chat, Embedding, Retriever, Qdrant
- **5 Temporal Services**: Server, Worker, API, Web UI, PostgreSQL  
- **Full Docker orchestration** with inter-service communication
- **Automated end-to-end testing** and validation

## Features

- 🚀 **Streaming Responses**: Real-time token-by-token streaming from OpenAI
- 💬 **Interactive Chat**: Modern Gradio chat interface with bubble UI
- ⏱️ **Temporal Workflows**: Fault-tolerant document processing workflows
- 🐳 **Full Docker Architecture**: Everything runs in containers, no local setup required
- 🔍 **Advanced RAG**: Document retrieval with vector search using Qdrant
- ⚙️ **Configurable**: Adjustable temperature, max tokens, and collection selection
- 🔧 **Debug Tools**: Built-in service connectivity testing and cache monitoring
- 📊 **Workflow Monitoring**: Temporal Web UI for workflow visualization
- 🔄 **Document Processing**: Automated chunking and embedding pipeline

## Quick Start

### Option 1: Full System with Temporal (Recommended)

**Starts all 10 microservices** including Temporal workflows:

1. **Set your OpenAI API Key:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

2. **Start all services including Temporal:**
   ```bash
   ./e2e_test.sh
   ```

3. **Access the interfaces:**
   - **Temporal Web UI**: http://localhost:8081 (Workflow monitoring)
   - **Chat Interface**: http://localhost:7860 (Gradio streaming chat)
   - **API Documentation**: http://localhost:8000/docs (FastAPI docs)
   - **Temporal API**: http://localhost:8003 (Workflow management)

4. **Test the document processing workflow:**
   ```bash
   python test_temporal_workflow.py
   ```

### Automated End-to-End Testing

The project includes a comprehensive end-to-end test script:

```bash
./e2e_test.sh
```

**What it does:**
- 🚀 Starts all 10 Docker services
- ⚡ Performs health checks on all services
- 📝 Tests document processing workflow via Temporal
- 🔍 Validates document retrieval and search
- ✅ Provides comprehensive system validation
- 📊 Shows real-time status and progress

**Services tested:**
- Qdrant vector database
- Embedding service (document vectorization)
- Retriever service (semantic search)
- Temporal server and worker
- Temporal API (workflow management)
- FastAPI main application
- Gradio chat interface

### Option 2: Basic System (Without Temporal)

**Starts core 5 services** for basic RAG functionality:

1. **Set your OpenAI API Key:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

2. **Start basic services:**
   ```bash
   docker-compose up --build
   ```

3. **Initialize the vector database:**
   ```bash
   python upload_documents.py
   ```

4. **Access the interfaces:**
   - **Chat Interface**: http://localhost:7860 (Gradio streaming chat)
   - **API Documentation**: http://localhost:8000/docs (FastAPI docs)
   - **Health Checks**: http://localhost:8000/health

## Project Structure

```
├── main.py                 # FastAPI application with streaming endpoints
├── rag_pipeline.py         # RAG pipeline implementation
├── test_temporal_workflow.py # Temporal workflow testing script
├── upload_documents.py    # Document upload utility script
├── docker-compose.yml     # Service orchestration (10 services total)
├── Dockerfile             # FastAPI container configuration
├── requirements.txt       # Python dependencies
├── launch.sh              # Basic Docker service launcher
├── e2e_test.sh            # End-to-end test script with full system validation
├── run_chat.py            # Chat launcher reference/documentation
├── services/
│   ├── gradio_service/    # Gradio chat interface service
│   │   ├── main.py        # Gradio app with streaming support
│   │   ├── Dockerfile     # Gradio container configuration
│   │   ├── requirements.txt # Gradio-specific dependencies
│   │   └── README.md      # Service documentation
│   ├── retriever_service/ # Document retrieval service
│   │   ├── main.py        # FastAPI retrieval service
│   │   ├── Dockerfile     # Retriever container configuration
│   │   └── requirements.txt # Retriever dependencies
│   ├── embedding_service/ # Document embedding service
│   │   ├── main.py        # FastAPI embedding service
│   │   ├── Dockerfile     # Embedding container configuration
│   │   └── requirements.txt # Embedding dependencies
│   └── temporal_service/  # Temporal workflows and activities
│       ├── workflows.py   # Document processing workflows
│       ├── activities.py  # Workflow activities (chunking, embedding)
│       ├── worker.py      # Temporal worker process
│       ├── api.py         # HTTP API for workflow management
│       └── Dockerfile     # Temporal service container
├── modules/
│   └── generate_module/   # Generation pipeline module
│       ├── main.py        # Generation service
│       └── requirements.txt # Generation dependencies
└── ci/
    └── ci_pipeline.py     # CI/CD pipeline
```

## Temporal Workflows

The system includes fault-tolerant document processing workflows powered by Temporal:

### Document Processing Workflow

**Workflow**: `DocumentProcessingWorkflow`
- **Step 1**: Document chunking into paragraphs
- **Step 2**: Embedding generation and vector storage via embedding service
- **Features**: Automatic retries, progress monitoring, failure handling

### Workflow Activities

1. **`chunk_documents_activity`**:
   - Splits documents into meaningful paragraphs
   - Filters out very short content
   - Adds metadata for tracking

2. **`embed_documents_activity`**:
   - Sends chunks to embedding service
   - Stores vectors in Qdrant
   - Handles large batches with timeouts

### Monitoring

- **Temporal Web UI**: http://localhost:8081
- **Workflow Management API**: http://localhost:8003
- **Worker Health**: Automatic health checks and restarts

## Services Architecture

The system consists of 10 Docker services communicating via internal Docker network:

### Core Services
- **🌐 Gradio Chat** (`gradio-chat`): Interactive streaming chat interface (microservice)
- **🚀 FastAPI** (`fastapi`): Main API server with streaming endpoints
- **🔍 Retriever Service** (`retriever-service`): Document retrieval with embeddings (microservice)
- **🧠 Embedding Service** (`embedding-service`): Document vectorization and indexing (microservice)
- **🗄️ Qdrant** (`qdrant`): Vector database for similarity search

### Temporal Services (5 containers)
- **⏱️ Temporal Server** (`temporal`): Workflow engine and state management  
- **🗃️ PostgreSQL** (`postgresql`): Temporal metadata storage
- **📊 Temporal Web UI** (`temporal-ui`): Workflow monitoring dashboard
- **🔄 Temporal Worker** (`temporal-worker`): Workflow execution engine (microservice)
- **🛠️ Temporal API** (`temporal-api`): HTTP interface for workflow management (microservice)

## Port Mapping

### Web Interfaces
- **🌐 Gradio Chat**: http://localhost:7860 - Interactive chat interface
- **📊 Temporal Web UI**: http://localhost:8081 - Workflow monitoring
- **� FastAPI Docs**: http://localhost:8000/docs - API documentation

### API Services  
- **🚀 FastAPI**: http://localhost:8000 - Main RAG API
- **🔍 Retriever**: http://localhost:8001 - Document retrieval
- **🧠 Embedding**: http://localhost:8002 - Document embedding
- **🛠️ Temporal API**: http://localhost:8003 - Workflow management
- **�️ Qdrant**: http://localhost:6333 - Vector database

### Infrastructure
- **⏱️ Temporal**: localhost:7233 - Workflow engine (internal)
- **🗃️ PostgreSQL**: localhost:5432 - Database (internal)

## Container-Only Architecture

This project is designed for **Docker-only operation** with **microservices architecture**:

- ✅ All development and runtime happens in containers
- ✅ Service-to-service communication via Docker network
- ✅ No local Python environment required
- ✅ Consistent deployment across environments
- ✅ Each service has its own dedicated container and dependencies
- ✅ Modular architecture for easy scaling and maintenance
- ⚠️ Only `upload_documents.py` and test scripts run locally (for database initialization and testing)

## API Endpoints

### Core RAG Endpoints
- `POST /rag` - Standard RAG query with complete response
- `POST /rag/stream` - Streaming RAG query with real-time tokens
- `GET /health` - Service health and connectivity check

### Request Format
```json
{
  "query": "What is machine learning?",
  "collection": "default",
  "max_tokens": 500,
  "temperature": 0.7
}
```

### Streaming Response
Server-Sent Events format with real-time token streaming:
```
data: {"token": "Machine", "done": false}
data: {"token": " learning", "done": false}
data: {"token": " is...", "done": false}
data: {"done": true}
```
- `GET /docs` - Interactive API documentation

That's it! The system is designed to be simple and straightforward to use.

## Usage Examples

### Chat Interface
1. Open http://localhost:7860
2. Select a document collection from the dropdown
3. Type your question in the chat box
4. Watch real-time streaming responses
5. Adjust settings (temperature, max tokens) as needed
6. Use debug panel to test service connectivity

## Development Workflow

### Building and Running
```bash
# Build and start all services
docker-compose up --build

# Start specific service
docker-compose up gradio-chat

# View logs
docker-compose logs -f gradio-chat

# Restart services
docker-compose restart
```

### Environment Variables
```bash
# Required
export OPENAI_API_KEY="your-api-key"

# Optional
export QDRANT_URL="http://qdrant:6333"
export RETRIEVER_URL="http://retriever-service:8000"
export FASTAPI_URL="http://fastapi:8000"
```

### Adding New Collections
```bash
# Initialize with custom data
python upload_documents.py --collection my-docs --data-path ./my-data/
```

## Configuration

### Gradio Chat Settings
- **Temperature**: Controls response creativity (0.0-2.0)
- **Max Tokens**: Maximum response length (1-2000)
- **Collection**: Document collection to search
- **Streaming**: Real-time vs. complete responses

### Docker Compose Overrides
Create `docker-compose.override.yml` for custom configurations:
```yaml
version: '3.8'
services:
  gradio-chat:
    environment:
      - GRADIO_SERVER_NAME=0.0.0.0
      - GRADIO_SERVER_PORT=7860
    ports:
      - "7860:7860"
```

## Troubleshooting

### Common Issues

**Chat interface not loading:**
```bash
# Check Gradio service status
docker-compose ps gradio-chat
docker-compose logs gradio-chat
```

**Streaming not working:**
```bash
# Verify OpenAI API key
echo $OPENAI_API_KEY

# Check FastAPI streaming endpoint
curl -X POST http://localhost:8000/rag/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"query": "test", "collection": "default"}'
```

**Service connectivity issues:**
```bash
# Test internal Docker network
docker-compose exec gradio-chat ping fastapi
docker-compose exec fastapi ping retriever-service
docker-compose exec retriever-service ping qdrant
```

**Vector database empty:**
```bash
# Re-initialize Qdrant
python upload_documents.py

# Check collection status
curl http://localhost:6333/collections
```

### Debug Commands
```bash
# Enter container shell
docker-compose exec gradio-chat bash
docker-compose exec fastapi bash

# View service health
curl http://localhost:8000/health

# Check Qdrant status
curl http://localhost:6333/collections

# Test retriever service
curl http://localhost:8001/health
```

## Performance Optimization

### Resource Allocation
```yaml
# In docker-compose.yml
services:
  gradio-chat:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
```

### Caching
- Gradio automatically caches chat history
- Qdrant uses persistent volume for vector storage
- FastAPI implements response caching for repeated queries

## Contributing

### Development Workflow

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes in appropriate service directory**:
   - Chat UI changes: `services/gradio_service/`
   - Embedding/retrieval logic: `services/embedding_service/` or `services/retriever_service/`
   - Workflow changes: `services/temporal_service/`
   - Main API: Root directory files
4. **Test with full system**: `./e2e_test.sh`
5. **Test individual services**: `docker-compose up --build <service-name>`
6. **Commit changes**: `git commit -m 'Add amazing feature'`
7. **Push to branch**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

### Service-Specific Development

**Gradio Chat Service** (`services/gradio_service/`):
```bash
# Test Gradio service only
docker-compose up --build gradio-chat
```

**Embedding Service** (`services/embedding_service/`):
```bash
# Test embedding service
docker-compose up --build embedding-service qdrant
curl http://localhost:8002/health
```

**Temporal Services** (`services/temporal_service/`):
```bash
# Test temporal stack
docker-compose up --build temporal temporal-worker temporal-api postgresql
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Technology Stack

### Core Technologies
- **Backend**: FastAPI (async Python web framework)
- **Frontend**: Gradio (interactive ML interfaces)
- **Vector DB**: Qdrant (high-performance vector database)
- **LLM**: OpenAI GPT models via streaming API
- **Workflow Engine**: Temporal (fault-tolerant workflow orchestration)
- **Containerization**: Docker & Docker Compose

### Architecture
- **Microservices**: Each service runs in its own container
- **Service Mesh**: Docker network for inter-service communication
- **Scalable Design**: Independent scaling of each service
- **Fault Tolerance**: Temporal workflows for reliable document processing
- **Stream Processing**: Real-time token streaming for chat responses
