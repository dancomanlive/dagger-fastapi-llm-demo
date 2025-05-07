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

### 2. Add container functions in `dagger_tools.py`

Add two functions to the `dagger_tools.py` file:

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

### 3. Add an endpoint in `main.py`

Create a new FastAPI endpoint that uses your tool:

```python
@app.get("/my-endpoint")
async def my_endpoint(input: str):
    from dagger_tools import my_tool
    result = await my_tool(dag, input)
    return {"message": result}
```

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
