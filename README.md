# 🧠 Dagger + FastAPI + OpenAI Chat API

This project is a demonstration of an AI-powered API using FastAPI, Dagger, and OpenAI. The API runs entirely in Docker and exposes endpoints that leverage Dagger for containerized function execution.

Dagger transforms complex software integrations into a clean, cacheable, and parallelizable directed acyclic graph (DAG) of containerized functions. Each node in this DAG is a purpose-built container with explicit inputs and outputs, creating natural dependencies between processing steps. This design ensures that containers are created on-demand, execute their specific tasks in complete isolation, and terminate after delivering their results, optimizing resource utilization and enhancing security through strict container boundaries.

With the introduction of LLM integration, Dagger extends its capabilities by allowing AI agents to interact with these containerized functions. The LLM core type enables native integration of LLMs into workflows, allowing them to automatically discover and use available Dagger Functions in the provided environment. This means that an LLM can analyze the available tools and select which ones to use to complete assigned tasks, effectively acting as an intelligent orchestrator within the DAG.

<img width="1710" alt="Screenshot 2025-05-04 at 15 05 54" src="https://github.com/user-attachments/assets/8033e815-1c23-4662-9041-8e59c23f225c" />

## 🚀 Features

- **Docker-first deployment**
- **Integration with OpenAI models** (GPT-4, GPT-3.5, etc.)
- **Secure API key and token management** via `.env`
- **Lightweight FastAPI backend** to send prompts and receive completions
- **Functional approach to Dagger containers** for simpler, more composable tool execution
- **Integrated with Dagger Cloud** for observability, sharing, and secure CI/CD workflows
- **Standardized module structure** with clear naming conventions
- **Isolated container execution** for enhanced security

## 🧩 Architecture

### Modules Structure

This project follows a clear and consistent naming convention for its modules:

1. **Modules** (`/modules/`) - The main directory containing:
   - **Scripts** (`/modules/scripts/`) - Standalone Python scripts that run inside Dagger containers
   - **Tools** (`/modules/tools/`) - Functions that orchestrate Dagger containers and execute the scripts

Each file follows a consistent naming pattern:
- Script files: `<functionality>_script.py`
- Tool files: `<functionality>_tool.py`

For detailed information about the naming conventions, see:
- [Module Naming Convention](./MODULE_NAMING_CONVENTION.md)

### How It Works

The project is built around a simple but powerful pattern:

1. **FastAPI Endpoints**: Handle HTTP requests and call tool functions
2. **Tool Functions**: Orchestrate Dagger containers to perform specific tasks
3. **Script Files**: Execute inside Dagger containers to do the actual work

This separation provides several benefits:
- Clean separation of concerns
- Better testability
- Improved security through container isolation
- Simplified development workflow

### Architecture Components

The project uses two main components to manage container-based operations:

1. **Core Container Utilities** (`modules/tools/core.py`):
   - Provides shared functions to set up and run containers
   - Handles container creation, script mounting, and execution
   - Example:
   ```python
   # Creates a base container with scripts mounted
   def get_tool_base(client, image, scripts_dir, workdir="/workspace"):
       return client.container().from_(image)
           .with_mounted_directory(workdir + "/scripts", scripts_dir)
           .with_workdir(workdir)
   
   # Executes a container and returns its output
   async def run_container_and_check(container, args):
       return await container.with_exec(args).stdout()
   ```

2. **Tool Implementations** (e.g., `modules/tools/hello_tool.py`):
   - Use the core utilities to perform specific tasks
   - Handle input validation and output processing
   - Example:
   ```python
   # A simple hello world tool
   async def hello_world(client, name="World"):
       container = get_tool_base(client, "python:3.11-slim", SCRIPTS_DIR)
       return await run_container_and_check(
           container,
           ["python", "scripts/hello_script.py", name]
       )
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

Key endpoints include:
- `GET /` - Welcome message
- `GET /hello?name=World` - Simple greeting from a Dagger container
- `POST /chat` - Interact with OpenAI models
- `POST /validate-document` - Validate documents against a schema
- `POST /test-qdrant` - Test connection to Qdrant vector database

Each endpoint demonstrates how to use Dagger containers to perform specific tasks in a secure, isolated environment.

## 🔧 Creating New Container Tools

This project is designed to be easily extensible with new containerized tools.

For a comprehensive guide on how to create and integrate new tools, please refer to the [Container Tools Guide](./CONTAINER_TOOLS.md).

The guide includes:
- Step-by-step instructions for creating new tools
- Best practices for container configuration
- Advanced patterns for complex use cases
- Examples for various input types and processing needs

## 🚧 Limitations & Workarounds

### Python SDK Module Function Invocation

While Dagger is a powerful tool for containerized workflows, the Python SDK (as of version 0.18.5) has some limitations:

- **Module Function Limitations**: There is currently no straightforward way to call Dagger module functions programmatically from the Python SDK. These module functions (defined with `@dagger.function` in a module configured via `dagger.json`) are primarily designed to be called via the Dagger CLI.

- **Official Workaround**: As confirmed by Dagger maintainers, the only current way to invoke module functions from Python is through complex GraphQL operations, which is not ideal for production code.

### Our Solution

This project demonstrates a practical workaround by using a functional approach with direct container operations:

1. Instead of using module functions, we define container-based tools with explicit input/output contracts
2. We separate script logic into external files for better maintainability
3. We mount these scripts into containers at runtime rather than embedding them in code
4. We use pure functions to create and execute these containers

This approach sidesteps the SDK limitations while still leveraging Dagger's powerful container orchestration capabilities. The result is clean, maintainable code that follows functional programming principles while achieving the same goals as module functions.

## 📁 Project Structure

```
DaggerFastAPIDemo/
├── main.py                 # FastAPI application and endpoints
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Docker configuration
├── Dockerfile              # Docker image definition
├── MODULE_NAMING_CONVENTION.md # Documentation for module naming
├── modules/                # Main modules directory
│   ├── scripts/            # Standalone scripts for container execution
│   │   ├── __init__.py     # Package initialization
│   │   ├── hello_script.py # Hello world script
│   │   └── qdrant_script.py # Qdrant connection testing script
│   └── tools/              # Container orchestration tools
│       ├── __init__.py     # Package initialization
│       ├── core.py         # Shared container utilities
│       ├── hello_tool.py   # Hello world with Dagger
│       └── qdrant_tool.py  # Qdrant connection testing tool
├── schemas/                # Data schemas
│   └── document_schema.py  # Document validation schema
└── ci/                     # CI/CD pipelines
    └── ci_pipeline.py      # CI pipeline definition
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
