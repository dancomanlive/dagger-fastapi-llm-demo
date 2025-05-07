# 🧠 Dagger + FastAPI + OpenAI Chat API

This project is a minimal demo of an AI-powered API using FastAPI, Dagger, and OpenAI. The API runs entirely in Docker and exposes simple endpoints that leverage Dagger for containerized function execution.

Dagger transforms complex software integrations into a clean, cacheable, and parallelizable directed acyclic graph (DAG) of containerized functions. Each node in this DAG is a purpose-built container with explicit inputs and outputs, creating natural dependencies between processing steps. This design ensures that containers are created on-demand, execute their specific tasks in complete isolation, and terminate after delivering their results, optimizing resource utilization and enhancing security through strict container boundaries. For example, the text analysis pipeline creates a clear flow from raw input → container creation → text processing → result extraction → client response, with each step isolated yet seamlessly connected. 

With the introduction of LLM integration, Dagger extends its capabilities by allowing AI agents to interact with these containerized functions. The LLM core type enables native integration of LLMs into workflows, allowing them to automatically discover and use available Dagger Functions in the provided environment. This means that an LLM can analyze the available tools and select which ones to use to complete assigned tasks, effectively acting as an intelligent orchestrator within the DAG.

<img width="1710" alt="Screenshot 2025-05-04 at 15 05 54" src="https://github.com/user-attachments/assets/8033e815-1c23-4662-9041-8e59c23f225c" />

## 🚀 Features

- **Docker-first deployment**
- **Integration with OpenAI models** (GPT-4, GPT-3.5, etc.)
- **Secure API key and token management** via `.env`
- **Lightweight FastAPI backend** to send prompts and receive completions
- **Functional approach to Dagger containers** for simpler, more composable tool execution
- **Integrated with Dagger Cloud** for observability, sharing, and secure CI/CD workflows

## 🧩 Architecture

### Functional Dagger Container Tools with External Scripts

This project demonstrates a functional approach to using Dagger containers with external scripts. Instead of embedding scripts directly in the code, we:

1. Store scripts in a dedicated `scripts/` directory
2. Mount these scripts into containers at runtime
3. Execute them with appropriate arguments

The key components are:

- **`scripts/`**: Contains Python scripts to be executed in containers
- **`dagger_tools.py`**: Contains functional implementations of containerized tools
- **FastAPI endpoints**: Use these functions to handle HTTP requests

### Function Types

We use two main types of functions:

1. **Container creation functions**: Return configured Dagger containers
   ```python
   def hello_world_container(client: dagger.Client, name: str) -> dagger.Container:
       # Mount and execute scripts from the scripts/ directory
   ```

2. **Execution functions**: Run containers and return results
   ```python
   async def hello_world(client: dagger.Client, name: str) -> str:
       container = hello_world_container(client, name)
       return await run_container(container)
   ```

## 🛠️ Setup & Usage

### 1. Clone the repository

```bash
git clone https://github.com/your-username/dagger-fastapi-demo.git
cd dagger-fastapi-demo
```

### 2. Create a `.env` file in the project root

```bash
# .env
OPENAI_API_KEY=your_openai_api_key_here
DAGGER_CLOUD_TOKEN=your_dagger_cloud_token_here  # 🔐 Required for Dagger Cloud

# Optional:
# LLM_MODEL=gpt-4o
```

The `.env` file is automatically loaded and is ignored by Git.

### 3. Start the API using Docker

```bash
docker-compose up -d
```

The API will now be available at:

```
http://localhost:8000
```

## 📡 API Usage

This project exposes several REST API endpoints that leverage Dagger containers for various operations.

For detailed information about all available endpoints, request formats, and response examples, please refer to the [API Usage Documentation](./API_USAGE.md).

Key endpoints include:
- `GET /hello` - Simple greeting from a container
- `GET /echo` - Echo text from a container
- `POST /chat` - Interact with OpenAI models
- `POST /process` - Process and transform JSON data
- `POST /analyze-text` - Analyze text and get statistics
- `POST /filter-csv` - Filter CSV data based on column values

## 🔧 Creating New Container Tools

This project is designed to be easily extensible with new containerized tools.

For a comprehensive guide on how to create and integrate new tools, please refer to the [Container Tools Guide](./CONTAINER_TOOLS.md).

The guide includes:
- Step-by-step instructions for creating new tools
- Best practices for container configuration
- Advanced patterns for complex use cases
- Examples for various input types and processing needs

## 📁 Project Structure

```
DaggerFastAPIDemo/
├── dagger_tools.py     # Functional container tool implementations
├── main.py             # FastAPI application and endpoints
├── requirements.txt    # Python dependencies
├── scripts/            # External scripts for container execution
│   ├── csv_filter.py   # CSV filtering tool
│   ├── echo.py         # Simple echo script
│   ├── hello_world.py  # Hello world with Dagger function
│   ├── process_data.py # Data processing example
│   └── text_analyzer.py # Text analysis tool
├── ci/                 # CI/CD pipelines
└── docker-compose.yml  # Docker configuration
```

## ☁️ Dagger Cloud Integration

This project integrates with Dagger Cloud to enable:

- Run insights and logs directly in the cloud
- Collaborate on workflows and infrastructure
- Secure secret management and CI/CD observability

## 📚 Further Reading

- [Dagger Python SDK Documentation](https://docs.dagger.io/sdk/python)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)

### To enable:

1. Create a Dagger Cloud token
2. Add it to your `.env` file as `DAGGER_CLOUD_TOKEN`
3. Run `docker-compose up` — Dagger will connect to the cloud automatically

---

## 🧩 Tech Stack

- **FastAPI** – for serving the API
- **Dagger** – for managing containerized workflows
- **Dagger Cloud** – for observability and secure CI/CD
- **Docker** – for local and production consistency
- **OpenAI** – LLM backend
