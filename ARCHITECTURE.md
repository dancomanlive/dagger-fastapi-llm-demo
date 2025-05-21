# 🏗️ Architecture

The Dagger FastAPI RAG Demo implements a modular, container-based architecture that ensures clean separation of concerns and efficient execution:

## Core Components

1. **FastAPI Server** (main.py)
   - Provides HTTP endpoints for client queries
   - Creates Dagger connections for containerized workflow orchestration
   - Handles error cases and returns appropriate responses

2. **Pipeline Orchestrator** (rag_pipeline.py)
   - Creates isolated container environments for each module
   - Manages dependency installation with caching for speed
   - Securely passes API keys to containers
   - Returns and caches final responses

3. **Retriever Service** (main.py)
   - Converts queries to vector embeddings
   - Searches Qdrant vector database for relevant documents
   - Returns semantically similar context documents
   - Handles scoring and selecting top results

4. **Generator Module** (main.py)
   - Calls the retriever service to get context
   - Constructs prompts with retrieved information
   - Makes API calls to OpenAI's language model
   - Formats and returns final answers


## Information Flow

The RAG pipeline processes queries through a clear sequence of transformations:

1. **User to API**: User submits a query to the FastAPI endpoint (`/rag`)

2. **API to Dagger**: FastAPI creates a Dagger client and passes the query to the pipeline orchestrator

3. **Dagger to Generator**: 
   - Dagger builds a container with the generator dependencies
   - **The query is passed as a command-line argument** (`--query`) to the generator script
   - Generator container is executed with the query parameter

4. **Generator to Retriever**: 
   - Generator constructs an HTTP request with the query
   - Request is sent to the retriever service's `/retrieve` endpoint

5. **Retriever Processing**:
   - Query is converted to vector embeddings
   - Qdrant performs similarity search against indexed documents
   - Most relevant document chunks are scored and selected

6. **Generator to LLM**:
   - Retrieved contexts are combined with the original query
   - Structured prompt is sent to OpenAI's API
   - LLM generates a contextually informed response

7. **Results Return Path**:
   - Generated answer flows back through the pipeline
   - JSON response is returned to the API endpoint
   - Formatted results are delivered to the user

This step-by-step flow ensures that information is properly processed at each stage while maintaining isolation between components.


## Key Benefits

- **Containerization**: Each component runs in its own isolated environment
- **Dependency Management**: Requirements installed only where needed
- **Secret Handling**: API keys passed securely via Dagger secrets
- **Performance**: Multi-level caching (pip packages, query results)
- **Extensibility**: The modular design makes it easy to add new capabilities or swap components without disrupting existing functionality
- **Maintainability**: Clean separation of concerns with modular architecture
- **Testability**: Clean separation allows components to be tested in isolation
- **Resilience**: Error handling at multiple levels ensures graceful failure recovery
- **Scalability**: Individual components can be scaled independently to handle varying loads

This architecture enables seamless scaling, simplified development, and reliable deployment across various environments.


## Terraform modules that automate resource provisioning across environments. (TODO)

DaggerFastAPIDemo/
├── terraform/
│   ├── modules/
│   │   ├── retriever-service/        # Persistent retriever infrastructure
│   │   ├── qdrant-database/          # Vector database deployment
│   │   ├── fastapi-service/          # FastAPI server deployment
│   │   ├── networking/               # Network configuration
│   │   └── security/                 # Secrets management
│   ├── environments/
│   │   ├── dev/
│   │   ├── staging/
│   │   └── production/
│   └── main.tf