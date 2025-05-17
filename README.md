# 🚀 Dagger FastAPI RAG Demo

A containerized Retrieval-Augmented Generation (RAG) system built with FastAPI and orchestrated by Dagger. This project demonstrates how to create a modular, maintainable RAG pipeline using direct Python execution in containers without wrapper scripts.

## 🔄 Deployment Patterns

The project supports two different deployment patterns:

### Pattern 1: Integrated Retriever (Original)
The original approach where the retriever service is started as part of the Dagger pipeline. This works well for scenarios where you don't mind the model being loaded for each query.

### Pattern 2: Standalone Retriever Service (Recommended)
A more efficient pattern where the retriever service runs as a long-lived Docker container, keeping the embedding model loaded in memory between queries. This significantly improves response times for subsequent queries.

To use Pattern 2:
```bash
# Deploy the standalone retriever service
./deploy_retriever_service.sh

# Run queries using the external retriever service
python rag_pipeline.py "your query"
```

## 🧠 RAG Pipeline & Qdrant Initialization

This project includes a modular RAG pipeline orchestrated by Dagger, with Qdrant as the vector database. The pipeline consists of two main modules:

- **Retrieve**: Fetches relevant documents from Qdrant using vector search
- **Generate**: Uses an LLM to generate answers based on retrieved context

### Qdrant Initialization

Before running the pipeline, you must initialize Qdrant with sample data:

```bash
python init_qdrant.py
```

This script will connect to your Qdrant instance and upload test documents. You can configure the Qdrant URL, collection name, and embedding model via environment variables or command-line arguments.


#### Environment Variables

All required environment variables are documented in `.env.example`. Copy this file to `.env` and edit as needed for your setup.

### Running the RAG Pipeline

The pipeline is orchestrated by Dagger and can be triggered via the FastAPI endpoint or by calling the relevant Python functions. The pipeline will:

1. Use the `retrieve` module to fetch relevant documents from Qdrant
2. Use the `generate` module to create a response based on the retrieved context

The pipeline uses dependency and model caching for efficiency. See `rag_pipeline.py` for details.

### Standalone Retriever Service (Pattern 2)

For improved performance, you can use the standalone retriever service pattern:

1. **One-time setup**: Deploy the retriever service using the provided script:
   ```bash
   ./deploy_retriever_service.sh
   ```
   This will:
   - Build the Docker image for the retriever service with the model cached
   - Start Qdrant and the retriever service using Docker Compose
   - The service will be accessible at http://localhost:8001

2. **Benefits**:
   - The embedding model remains loaded in memory between queries
   - Significantly faster response times for subsequent queries
   - Model is pre-warmed during Docker image build

3. **Architecture**:
   - The retriever service runs in its own container (port 8001)
   - Qdrant runs in its own container (ports 6333/6334)
   - The Dagger pipeline calls the external retriever service instead of starting its own

To use this pattern, make sure your environment has `RETRIEVER_SERVICE_URL` set to `http://localhost:8001` when running outside Docker, or to `http://retriever-service:8000` when running from another container.

#### Troubleshooting

- Ensure Qdrant is running and accessible at the configured URL
- If you see connection errors, check your `QDRANT_URL` and Docker network settings
- For model download or embedding issues, verify your `EMBEDDING_MODEL` and Hugging Face cache

---

## 📋 Overview

This project showcases a modern approach to building RAG systems with:

- **FastAPI** for the web service layer
- **Dagger** for direct container orchestration (no custom images required)
- **Qdrant** for vector storage
- **Python scripts** executed directly in standard containers
- **Environment configuration** via `.env` file
- **Modular Architecture** for maintainability and reusability

## 🏗️ Architecture

The system is built around a modular container-based architecture:

1. **FastAPI Service**: Handles HTTP requests and orchestrates the RAG pipeline
2. **Dagger Engine**: Coordinates container execution without wrapper scripts - directly mounting code and running Python
3. **Qdrant**: Vector database for document storage and retrieval
4. **RAG Module Containers**:
   - **Retrieve**: Fetches relevant documents from Qdrant
   - **Generate**: Creates responses using an LLM based on retrieved documents

## 🧰 Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+ 
- At least 4GB of available RAM
- Docker Hub account (for CI/CD and for publishing Dagger modules)

## 🚀 Getting Started

### Quick Start

```bash
# Clone the repository
git clone <your-repo-url>
cd DaggerFastAPIDemo

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration values

# Run the demo
./run_demo.sh
```

The script will:
1. Create a Docker network
2. Build module containers
3. Start FastAPI and Qdrant services
4. Initialize Qdrant with test data
5. Test the complete RAG pipeline

### Accessing the System

- **API Endpoint**: http://127.0.0.1:8000/rag
- **Health Check**: http://127.0.0.1:8000/

Example API usage:

```bash
curl -X POST http://127.0.0.1:8000/rag \
  -H "Content-Type: application/json" \
  -d '{"query": "How does RAG solve LLM problems?", "collection": "default"}'
```

## 🛠️ Project Structure

```
├── ci/                      # CI/CD pipelines with Dagger
├── modules/                 # RAG module code
│   ├── retrieve/            # Document retrieval module
│   │   ├── main.py          # Retrieval implementation
│   │   └── requirements.txt # Retrieve module dependencies
│   └── generate/            # Response generation module
│       ├── main.py          # Generation implementation
│       └── requirements.txt # Generate module dependencies
├── docker-compose.yml       # Service configuration
├── Dockerfile               # Main application container
├── rag_app.py               # FastAPI application with Dagger orchestration
├── requirements.txt         # Python dependencies
└── run_demo.sh              # Startup script
```

## 🧑‍💻 Development

### Creating a New RAG Module

1. Create a directory in `modules/` with your module name
2. Add a `main.py` and `requirements.txt`
3. Implement module logic in `main.py` with standard input/output file parameters:
   ```python
   def main():
       parser = argparse.ArgumentParser()
       parser.add_argument("--input", required=True)
       parser.add_argument("--output", default="output.json")
       # ...
   ```
4. Update the Dagger pipeline in `rag_app.py` to include your new module

No need to build and push custom Docker images - the pipeline uses standard Python images and mounts your code directly.

### Continuous Integration

This project includes a Dagger-based CI pipeline for building and pushing Docker images:

```bash
cd ci
python ci_pipeline.py
```

## 📦 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions on deploying this system to:

- AWS ECS
- Google Cloud Run
- Azure Container Apps

## 🐳 Docker-Based Execution

For details on the Docker-only execution model, see [DOCKER_README.md](DOCKER_README.md).

## 🚢 CI/CD Setup

To set up CI/CD with GitHub Actions:

1. Add Docker Hub and Dagger Cloud credentials to GitHub Secrets
2. Use the provided GitHub Actions workflow in `.github/workflows/`

## 📚 Documentation

For more detailed documentation:

- [Architecture RFC](rfc_instructions.md)
- [Docker Setup](DOCKER_README.md)
- [Deployment Guide](DEPLOYMENT.md)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🛠️ Dependency Caching

This project leverages **Dagger's caching mechanism** to optimize dependency installation and reduce latency during pipeline execution. Here’s how it works:

1. **Pip Cache**:
   - Dependencies for the `retrieve` and `generate` modules are installed using `pip`.
   - A shared cache volume (`global-python-pip-cache`) is mounted to `/root/.cache/pip` in the container to store pip's cache.
   - This ensures that subsequent runs reuse cached dependencies, reducing installation time.

2. **Hugging Face Cache**:
   - Models and datasets are cached using a shared volume (`global-huggingface-cache`) mounted to `/root/.cache/huggingface`.
   - This speeds up operations involving Hugging Face libraries.

3. **Temporary Script Cache**:
   - Module-specific temporary data (e.g., pickled embeddings) is stored in `/tmp/module_cache` using the `global-script-temp-cache` volume.

### Debugging Dependency Caching

If dependency caching is not working as expected:

- Ensure the `requirements.txt` files for the `retrieve` and `generate` modules are present and correctly formatted.
- Verify that the cache volumes are being mounted correctly in the Dagger pipeline.
- Add debug logs to print the hash of the `requirements.txt` file to confirm it is not changing between runs.

Example Debugging Command:
```bash
# Check if requirements.txt is consistent
md5sum modules/retrieve/requirements.txt
md5sum modules/generate/requirements.txt
```

For more details, see the `get_or_build_deps_image` function in `rag_pipeline.py`.
