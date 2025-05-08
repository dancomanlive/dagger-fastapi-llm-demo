# 🔄 Refactoring to Shared Factory Pattern

## Why We Refactored

The original code had duplicate patterns across different containerized tools, leading to several issues:

1. **Code Duplication**: Similar container setup logic was repeated for each tool
2. **Inconsistent Error Handling**: Each tool handled errors differently
3. **Maintenance Challenges**: Changes to container behavior required updates in multiple places

## The New Architecture

### Before: Direct Container Creation

```python
# In dagger_tools.py
def hello_world_container(client: dagger.Client, name: str) -> dagger.Container:
    return client.container().from_("python:3.11-slim") \
        .with_mounted_directory("/scripts", client.host().directory(SCRIPTS_DIR)) \
        .with_workdir("/scripts") \
        .with_exec(["python", "hello_world.py", name])

async def hello_world(client: dagger.Client, name: str) -> str:
    container = hello_world_container(client, name)
    return await run_container(container)
```

### After: Shared Factory Pattern

```python
# In tools/core.py
def get_tool_base(client, image, scripts_dir, workdir="/workspace") -> dagger.Container:
    return client.container().from_(image) \
        .with_workdir(workdir) \
        .with_mounted_directory(f"{workdir}/scripts", client.host().directory(scripts_dir))

async def run_container_and_check(container, args) -> str:
    proc = container.with_exec(list(args))
    stdout = await proc.stdout()
    exit_code = await proc.exit_code()
    if exit_code != 0:
        stderr = await proc.stderr()
        raise RuntimeError(f"Container exited {exit_code}.\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}")
    return stdout.strip()

# In tools/hello.py
async def hello_world(client: dagger.Client, name: str) -> str:
    container = get_tool_base(client, "python:3.11-slim", SCRIPTS_DIR)
    return await run_container_and_check(container, ["python", "scripts/hello_world.py", name])
```

## Key Benefits

1. **DRY (Don't Repeat Yourself)**: Common container setup and execution logic is centralized
2. **Standardized Error Handling**: All tools handle errors consistently, with both stdout and stderr captured
3. **Improved Debugging**: Container exit codes are checked, and detailed error messages are provided
4. **Maintainability**: Changes to common behavior only need to be made in one place
5. **Modularity**: Tools are isolated into separate modules, making them easier to test and reuse
6. **Configuration Flexibility**: Tools can easily be configured with different base images or working directories

## Implementation Notes

1. Originally we attempted to use `lru_cache` to memoize the container creation, but the Dagger `Client` object isn't hashable
2. Each tool is now in its own module, creating a clearer structure and better separation of concerns
3. The `tools/core.py` module provides centralized utilities and constants

## Future Improvements

1. Add comprehensive testing for each tool module
2. Implement more granular error handling specific to each tool
3. Add telemetry and logging enhancements to track container execution times
4. Consider adding a configuration system to customize tool behavior at runtime
