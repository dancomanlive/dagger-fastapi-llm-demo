# 🧠 Dagger + FastAPI + OpenAI Chat API

This project is a minimal demo of an AI-powered API using FastAPI, Dagger, and OpenAI. The API runs entirely in Docker and exposes simple endpoints that leverage Dagger for containerized function execution.

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

### `GET /hello`

Get a simple greeting from a container.

#### Example Request:

```bash
# Default greeting
curl -X GET http://localhost:8000/hello

# Custom name
curl -X GET "http://localhost:8000/hello?name=Dan"
```

#### Example Response:

```json
{
  "message": "Hello, Dan!"
}
```

### `GET /echo`

Echo text from a container.

#### Example Request:

```bash
curl -X GET "http://localhost:8000/echo?text=Hello%20from%20Dagger"
```

#### Example Response:

```json
{
  "message": "Hello from Dagger"
}
```

### `POST /chat`

Send a prompt to the OpenAI model and get a response.

#### Example Request:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the capital of China?"}'
```

#### Example Response:

```json
{
  "response": "The capital of China is Beijing."
}
```

You can optionally pass a specific model:

```json
{
  "prompt": "Hello!",
  "model": "gpt-4"
}
```

### `POST /process`

Process data using a container.

#### Example Request:

```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"name": "dan", "message": "hello"}'
```

#### Example Response:

```json
{
  "result": {
    "NAME": "DAN",
    "MESSAGE": "HELLO"
  }
}
```

### `POST /analyze-text`

Analyze text and get statistics.

#### Example Request:

```bash
curl -X POST http://localhost:8000/analyze-text \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a sample text for analysis. This sample contains repeated words."}'
```

#### Example Response:

```json
{
  "analysis": {
    "word_count": 12,
    "character_count": 69,
    "most_common_words": {
      "this": 2,
      "sample": 2,
      "is": 1,
      "a": 1,
      "text": 1
    },
    "average_word_length": 4.75
  }
}
```

### `POST /filter-csv`

Filter CSV data based on column values.

#### Example Request:

```bash
curl -X POST http://localhost:8000/filter-csv \
  -H "Content-Type: application/json" \
  -d '{
    "csv_data": "id,name,department,salary\n1,John,Engineering,75000\n2,Alice,Marketing,65000\n3,Bob,Engineering,80000\n4,Carol,HR,60000",
    "column": "department",
    "value": "Engineering"
  }'
```

#### Example Response:

```json
{
  "result": {
    "filtered_csv": "id,name,department,salary\n1,John,Engineering,75000\n3,Bob,Engineering,80000\n",
    "rows": [
      {
        "id": "1",
        "name": "John",
        "department": "Engineering",
        "salary": "75000"
      },
      {
        "id": "3",
        "name": "Bob",
        "department": "Engineering",
        "salary": "80000"
      }
    ],
    "count": 2
  }
}
```

## 🔧 Creating New Container Tools

To add a new tool, follow this pattern:

1. Create a script in the `scripts/` directory:

```python
# scripts/my_script.py
import sys

# Get arguments from command line
input_data = sys.argv[1] if len(sys.argv) > 1 else "default"

# Process the data
result = input_data.upper()

# Output the result
print(result)
```

2. Add container functions in `dagger_tools.py`:

```python
# Container creation function
def my_tool_container(client: dagger.Client, input: str) -> dagger.Container:
    return client.container().from_("python:3.11-slim") \
        .with_mounted_directory("/scripts", client.host().directory(SCRIPTS_DIR)) \
        .with_workdir("/scripts") \
        .with_exec(["python", "my_script.py", input])

# Convenience execution function
async def my_tool(client: dagger.Client, input: str) -> str:
    container = my_tool_container(client, input)
    return await run_container(container)
```

3. Add an endpoint in `main.py`:

```python
@app.get("/my-endpoint")
async def my_endpoint(input: str):
    from dagger_tools import my_tool
    result = await my_tool(dag, input)
    return {"message": result}
```

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

## 🔒 Security Notes

- `.env` is in `.gitignore`; never commit your secrets.
- Store sensitive credentials like `OPENAI_API_KEY` and `DAGGER_CLOUD_TOKEN` in environment variables or `.env`.
- Dagger secures secret values and prevents them from leaking in logs or layers.

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
