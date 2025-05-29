# FastAPI RAG Demo with Temporal Workflows

A sophisticated Retrieval-Augmented Generation (RAG) system with interactive streaming chat interface and Temporal workflow orchestration, built with FastAPI, Gradio, Temporal, and Docker.

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

1. **Set your OpenAI API Key:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

2. **Start all services including Temporal:**
   ```bash
   ./launch_temporal.sh
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

### Option 2: Basic System (Without Temporal)

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
   python init_qdrant.py
   ```

4. **Access the interfaces:**
   - **Chat Interface**: http://localhost:7860 (Gradio streaming chat)
   - **API Documentation**: http://localhost:8000/docs (FastAPI docs)
   - **Health Checks**: http://localhost:8000/health

## Project Structure

```
├── main.py                 # FastAPI application with streaming endpoints
├── gradio_app.py          # Gradio chat interface with streaming support
├── rag_pipeline.py         # RAG pipeline implementation
├── init_qdrant.py         # Vector database initialization
├── test_temporal_workflow.py # Temporal workflow testing script
├── docker-compose.yml     # Service orchestration (9 services total)
├── Dockerfile             # FastAPI container configuration
├── Dockerfile.gradio      # Gradio container configuration
├── requirements.txt       # Python dependencies
├── launch.sh              # Basic Docker service launcher
├── launch_temporal.sh     # Full system launcher with Temporal
├── run_chat.py            # Chat launcher reference
├── services/
│   ├── retriever_service/ # Document retrieval service
│   ├── embedding_service/ # Document embedding service
│   └── temporal_service/  # Temporal workflows and activities
│       ├── workflows.py   # Document processing workflows
│       ├── activities.py  # Workflow activities (chunking, embedding)
│       ├── worker.py      # Temporal worker process
│       ├── api.py         # HTTP API for workflow management
│       └── Dockerfile     # Temporal service container
└── modules/
    └── generate_module/   # Generation pipeline module
```
│   └── generate/          # Text generation service
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

### Usage Example

```bash
# Start a document processing workflow
curl -X POST http://localhost:8003/process-documents \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "id": "doc1",
        "text": "Your document text here...",
        "metadata": {"source": "upload"}
      }
    ]
  }'

# Check workflow status
curl http://localhost:8003/workflow/{workflow_id}/status

# Get workflow result
curl http://localhost:8003/workflow/{workflow_id}/result
```

### Monitoring

- **Temporal Web UI**: http://localhost:8081
- **Workflow Management API**: http://localhost:8003
- **Worker Health**: Automatic health checks and restarts

## Services Architecture

The system consists of 9 Docker services communicating via internal Docker network:

### Core Services
- **🌐 Gradio Chat** (`gradio-chat`): Interactive streaming chat interface
- **🚀 FastAPI** (`fastapi`): Main API server with streaming endpoints
- **🔍 Retriever Service** (`retriever-service`): Document retrieval with embeddings
- **🧠 Embedding Service** (`embedding-service`): Document vectorization and indexing
- **🗄️ Qdrant** (`qdrant`): Vector database for similarity search

### Temporal Services
- **⏱️ Temporal Server** (`temporal`): Workflow engine and state management  
- **🗃️ PostgreSQL** (`postgresql`): Temporal metadata storage
- **📊 Temporal Web UI** (`temporal-ui`): Workflow monitoring dashboard
- **🔄 Temporal Worker** (`temporal-worker`): Workflow execution engine
- **🛠️ Temporal API** (`temporal-api`): HTTP interface for workflow management

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

This project is designed for **Docker-only operation**:

- ✅ All development and runtime happens in containers
- ✅ Service-to-service communication via Docker network
- ✅ No local Python environment required
- ✅ Consistent deployment across environments
- ⚠️ Only `init_qdrant.py` runs locally (for database initialization)

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

### API Usage
```bash
# Standard RAG query
curl -X POST http://localhost:8000/rag \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "collection": "default",
    "max_tokens": 500,
    "temperature": 0.7
  }'

# Streaming query (Server-Sent Events)
curl -X POST http://localhost:8000/rag/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "query": "Explain neural networks",
    "collection": "default"
  }'
```

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
python init_qdrant.py --collection my-docs --data-path ./my-data/
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
python init_qdrant.py

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

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes in Docker containers
4. Test with: `docker-compose up --build`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Technology Stack

- **Backend**: FastAPI (async Python web framework)
- **Frontend**: Gradio (interactive ML interfaces)
- **Vector DB**: Qdrant (high-performance vector database)
- **LLM**: OpenAI GPT models via streaming API
- **Containerization**: Docker & Docker Compose
- **Architecture**: Microservices with Docker networking
