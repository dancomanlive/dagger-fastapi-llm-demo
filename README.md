# 🚀 Dagger FastAPI RAG Demo

A containerized Retrieval-Augmented Generation (RAG) system built with FastAPI and orchestrated by Dagger. This project demonstrates how to create a modular, maintainable RAG pipeline using direct Python execution in containers without wrapper scripts.

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
