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
