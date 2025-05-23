# 🏗️ Architecture

The FastAPI RAG Demo implements a modular architecture that ensures clean separation of concerns and efficient execution:

## Core Components

1. **FastAPI Server** (main.py)
   - Provides HTTP endpoints for client queries
   - Orchestrates the RAG pipeline execution
   - Handles error cases and returns appropriate responses

2. **Pipeline Orchestrator** (rag_pipeline_direct.py)
   - Manages direct Python script execution
   - Handles dependency installation with smart caching for speed
   - Securely passes environment variables to subprocesses
   - Returns and caches final responses

3. **Retriever Service** (modules/retriever_service/main.py)
   - Converts queries to vector embeddings
   - Searches Qdrant vector database for relevant documents
   - Returns semantically similar context documents
   - Handles scoring and selecting top results

4. **Generator Module** (modules/generate/main.py)
   - Calls the retriever service to get context
   - Constructs prompts with retrieved information
   - Makes API calls to OpenAI's language model
   - Formats and returns final answers


## Information Flow

The RAG pipeline processes queries through a clear sequence of transformations:

1. **User to API**: User submits a query to the FastAPI endpoint (`/rag`)

2. **API to Orchestrator**: FastAPI passes the query to the pipeline orchestrator

3. **Orchestrator to Generator**: 
   - Orchestrator ensures dependencies are installed
   - The query is passed as a command-line argument (`--query`) to the generator script
   - Generator script is executed with the query parameter using `subprocess.run()`

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

- **Direct Execution**: Simple and efficient execution of Python scripts
- **Smart Dependency Management**: Requirements installed and tracked using hash-based markers
- **Environment Variable Handling**: Configs passed securely via environment variables
- **Performance**: Multi-level caching (pip packages, query results)
- **Extensibility**: The modular design makes it easy to add new capabilities or swap components without disrupting existing functionality
- **Maintainability**: Clean separation of concerns with modular architecture
- **Testability**: Clean separation allows components to be tested in isolation
- **Resilience**: Error handling at multiple levels ensures graceful failure recovery
- **Simplified Deployment**: No need for complex container orchestration

This architecture enables simplified development with direct execution while maintaining most of the benefits of the modular approach.
