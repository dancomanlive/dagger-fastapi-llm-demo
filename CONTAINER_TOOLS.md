# 🔧 Creating New Container Tools

This guide explains how to create and integrate new containerized tools into the Dagger FastAPI Demo.

## Step-by-Step Process

To add a new tool, follow this pattern:

### 1. Create a script in the `scripts/` directory

Start by creating a new Python script that will run inside the container:

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

### 2. Create a new tool module in the `tools/` directory

Add a new Python module to the `tools/` directory that leverages the shared factory functions:

```python
"""
My tool - demonstrates usage of the core utilities.
"""
import dagger
from tools.core import get_tool_base, run_container_and_check, SCRIPTS_DIR

async def my_tool(
    client: dagger.Client, 
    input: str,
    image: str = "python:3.11-slim"
) -> str:
    """
    Process input with my_script.py in a container.
    
    Args:
        client: Dagger client
        input: Text to process
        image: Container image to use
        
    Returns:
        Processed result
    """
    # Get a base container configured with our scripts directory
    container = get_tool_base(
        client=client,
        image=image,
        scripts_dir=SCRIPTS_DIR,
    )
    
    # Add any dependencies if needed
    container = container.with_exec(["pip", "install", "some-package"])
    
    # Run the script with the provided input
    return await run_container_and_check(
        container=container,
        args=["python", "scripts/my_script.py", input]
    )
```

### 3. Create a Pipeline (Optional)

If your tool is part of a larger workflow, create a pipeline in the `pipelines/` directory:

```python
"""
My pipeline - demonstrates a workflow that uses multiple tools.
"""
import json
import dagger
from tools.my_tool import my_tool
from tools.text_embedder import embed_text

async def my_pipeline(
    client: dagger.Client,
    input: str
) -> dict:
    """
    Run a pipeline that combines multiple tools.
    
    Args:
        client: Dagger client
        input: Input text
        
    Returns:
        Dict with pipeline results
    """
    # First process with my_tool
    processed_data = await my_tool(client, input)
    
    # Then generate embeddings
    embedding_result = await embed_text(client, [processed_data])
    embedding_data = json.loads(embedding_result)
    
    # Return combined results
    return {
        "processed_text": processed_data,
        "embeddings": embedding_data.get("embeddings", [])
    }
```

### 4. Add an endpoint in `main.py`

Finally, add an endpoint to expose your tool or pipeline:

```python
@app.post("/my-tool")
async def my_tool_endpoint(request: dict):
    """Endpoint that uses my_tool in a Dagger container"""
    if "text" not in request:
        raise HTTPException(status_code=400, detail="Text field is required")
        
    text = request["text"]
    logger.info(f"Processing text with my_tool")

    try:
        from tools.my_tool import my_tool
        
        # Use the client from app state
        client = app.state.dagger_client
        result = await my_tool(client, text)
        
        logger.info("Processing completed")
        return {"result": result}

    except Exception as e:
        logger.exception(f"Error processing with my_tool: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

## Example Tool: Hello World

The hello world tool is a simple example that demonstrates the pattern:

### Script: `scripts/hello_world.py`

```python
import sys

def hello_world(name: str) -> str:
    return f"Hello, {name}!"

# Script expects one argument for the name
name = sys.argv[1] if len(sys.argv) > 1 else "World"
print(hello_world(name))
```

### Tool: `tools/hello.py`

```python
"""
Hello world tool - demonstrates usage of the core utilities.
"""
import dagger
from tools.core import get_tool_base, run_container_and_check, SCRIPTS_DIR

async def hello_world(
    client: dagger.Client, 
    name: str = "World",
    image: str = "python:3.11-slim"
) -> str:
    """
    Run a hello world script in a container.
    
    Args:
        client: Dagger client
        name: Name to include in the greeting
        image: Container image to use
        
    Returns:
        The greeting message
    """
    # Get a base container configured with our scripts directory
    container = get_tool_base(
        client=client,
        image=image,
        scripts_dir=SCRIPTS_DIR,
    )
    
    # Run the hello_world.py script with the provided name
    return await run_container_and_check(
        container=container,
        args=["python", "scripts/hello_world.py", name]
    )
```

## RAG Tools

For more complex examples, see the RAG components which implement the pattern at scale:

1. Text chunking: `tools/text_chunker_advanced.py` + `scripts/text_chunker_advanced.py`
2. Text embedding: `tools/text_embedder.py` + `scripts/embed_text.py`
3. Qdrant storage: `tools/superlinked_qdrant_connector.py` + `scripts/superlinked_qdrant.py`
4. RAG pipeline: `pipelines/rag_pipeline.py`
        The processed result
    """
    # Get a base container configured with our scripts directory
    container = get_tool_base(
        client=client,
        image=image,
        scripts_dir=SCRIPTS_DIR,
    )
    
    # Run the my_script.py script with the provided input
    return await run_container_and_check(
        container=container,
        args=["python", "scripts/my_script.py", input]
    )
```

### 3. Add an endpoint in `main.py`

Create a new FastAPI endpoint that uses your tool:

```python
@app.get("/my-endpoint")
async def my_endpoint(input: str):
    """Endpoint that processes input using a Dagger container"""
    logger.info(f"/my-endpoint called with input: {input}. Using Dagger client from app state.")

    try:
        from tools.my_tool import my_tool
        
        # Use the client from app state
        client = app.state.dagger_client
        result = await my_tool(client, input)
        
        logger.info(f"Processed input with my tool")
        return {"message": result}

    except Exception as e:
        logger.exception(f"Error processing input: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

## Tools Architecture

The project uses a modular approach for containerized tools:

### Core Utilities (`tools/core.py`)

The `core.py` module provides shared functionality:

- `get_tool_base()`: Creates standardized container configurations
- `run_container_and_check()`: Executes containers and handles errors consistently 
- `SCRIPTS_DIR`: Centralized path to the scripts directory

### Individual Tool Modules

Each tool is implemented as a separate module in the `tools/` directory:

- `hello.py`: Hello world greeting tool
- `echo.py`: Text echo tool
- `process_data.py`: JSON data processing tool
- `analyze_text.py`: Text analysis tool
- `filter_csv.py`: CSV filtering tool

This architecture provides several benefits:

1. **DRY (Don't Repeat Yourself)**: Common container setup and execution logic is centralized
2. **Standardized Error Handling**: All tools handle errors consistently
3. **Maintainability**: Changes to common behavior only need to be made in one place
4. **Modularity**: Tools are isolated and easy to test independently

## Best Practices

### Input Handling

- Validate inputs early in both the FastAPI endpoint and the container script
- Use appropriate types for parameters (string, JSON, file paths, etc.)
- Provide sensible defaults when appropriate

### Container Configuration

- Choose the right base image for your container
- Install only the dependencies you need
- Use a specific version for base images and dependencies

### Error Handling

- Implement robust error handling in your scripts
- Return clear error messages and appropriate status codes
- Log errors for debugging

### Performance

- Keep container startup time minimal
- For resource-intensive operations, consider caching
- Clean up temporary files and resources

## Advanced Use Cases

### Processing File Inputs

For tools that need to process files, you can mount host directories or create files dynamically:

```python
def file_processor_container(client: dagger.Client, file_content: str) -> dagger.Container:
    return client.container().from_("python:3.11-slim") \
        .with_mounted_directory("/scripts", client.host().directory(SCRIPTS_DIR)) \
        .with_new_file("/tmp/input.txt", file_content) \
        .with_workdir("/scripts") \
        .with_exec(["python", "process_file.py", "/tmp/input.txt"])
```

### Chaining Containers

You can chain multiple containers together for complex workflows:

```python
async def complex_workflow(client: dagger.Client, input_data: str) -> str:
    # First container processes the input
    first_result = await first_tool(client, input_data)
    
    # Second container processes the result of the first
    final_result = await second_tool(client, first_result)
    
    return final_result
```

### Using Different Languages

You can use any language in your containers, not just Python:

```python
def node_tool_container(client: dagger.Client, input: str) -> dagger.Container:
    return client.container().from_("node:18-slim") \
        .with_mounted_directory("/scripts", client.host().directory("node_scripts")) \
        .with_workdir("/scripts") \
        .with_exec(["node", "process.js", input])
```
