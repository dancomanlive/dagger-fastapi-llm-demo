---

**Author:**
**Date:** 
**Status:** Proposed

# 1. Introduction

This RFC proposes a modular architecture for implementing Retrieval-Augmented Generation (`RAG`) workflows using containerized modules orchestrated by `Dagger`. The goal is to create reusable, isolated, and maintainable modules for each `RAG` step (e.g., retrieval, augmentation, generation), enabling easy integration into `FastAPI` applications and sharing across projects. We also address current limitations of the `Dagger` Python SDK and provide a hypothetical example of how this architecture could leverage `Dagger` modules once supported.

# 2. Problem Statement

`RAG` workflows involve multiple steps (e.g., retrieving data from a vector database like `Qdrant`, augmenting it with context, and generating responses via an `LLM`). These steps are complex, dependency-heavy, and need to be reusable across projects for different customers. Without a modular architecture, implementing `RAG` workflows leads to:

- **Tight Coupling:** Steps are hard to isolate, making maintenance difficult.
- **Dependency Conflicts:** Different steps may require conflicting libraries.
- **Poor Reusability:** Sharing logic across projects is cumbersome.
- **Cold Start Latency:** Dynamic container creation slows down execution.

Additionally, the `Dagger` Python SDK currently lacks support for calling module functions programmatically, limiting our ability to use `Dagger`’s native module system for modularity.

# 3. Proposed Solution

We propose a modular architecture where each `RAG` step is a standalone, containerized module orchestrated by `Dagger`. Each module is isolated, reusable, and has a standardized interface (`JSON` input/output). To address cold starts, images are preloaded at application startup. We also outline a hypothetical transition to `Dagger` modules once the Python SDK supports function calls.

## 3.1 Architecture Overview

- **Modules:** Each `RAG` step (e.g., retrieve, augment, generate) is a `Docker` container with its own `Python` logic, dependencies, and `Dockerfile`.
- **Orchestration:** `Dagger` orchestrates temporary containers for each step, chaining them in a pipeline.
- **Interface:** Modules accept `JSON` input and produce `JSON` output via a `CLI` (e.g., `python main.py --input input.json --output output.json`).
- **Preloading:** Images are pulled at `FastAPI` startup to eliminate cold start latency.
- **Reusability:** Modules are published to a private `Docker` registry (e.g., `AWS ECR`) for sharing across projects.

## 3.2 Directory Structure

```
modules/
├── retrieve/
│   ├── Dockerfile
│   ├── main.py          # Retrieval logic (e.g., Superlinked SDK + Qdrant)
│   ├── requirements.txt
├── augment/
│   ├── Dockerfile
│   ├── main.py          # Augmentation logic (e.g., LLM prep)
│   ├── requirements.txt
├── generate/
│   ├── Dockerfile
│   ├── main.py          # Generation logic (e.g., LLM call)
│   ├── requirements.txt

```

## 3.3 Example: `retrieve` Module

**`main.py`:**

```python
import json
import argparse
from superlinked import QdrantConnector # Assuming this is the correct import for Superlinked

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="output.json")
    args = parser.parse_args()

    with open(args.input) as f:
        data = json.load(f)

    # Example: Connect to Qdrant and retrieve data
    # Replace with actual Superlinked SDK usage if different
    connector = QdrantConnector(host=data.get("qdrant_host", "qdrant:6333"))
    results = connector.query(data["query"], collection=data.get("collection", "default"))

    with open(args.output, "w") as f:
        json.dump({"results": results}, f)

if __name__ == "__main__":
    main()

```

**`Dockerfile`:**

```
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY main.py .
ENTRYPOINT ["python", "main.py"]

```

**`requirements.txt`:**

```
superlinked==1.0
# Add other dependencies like qdrant-client if needed directly by main.py

```

**Build and Publish:**

```
cd modules/retrieve
docker build -t mycompany/retrieve:v1.0.0 .
docker push mycompany/retrieve:v1.0.0

```

## 3.4 FastAPI Integration and Dagger Pipeline

The `FastAPI` app orchestrates the `RAG` pipeline using `Dagger`, preloading images at startup to avoid cold starts.

```python
from fastapi import FastAPI
import dagger
import docker # For preloading
import json
import logging
from pydantic import BaseModel

app = FastAPI()

# Images to preload
IMAGES = [
    "mycompany/retrieve:v1.0.0",
    "mycompany/augment:v1.0.0",
    "mycompany/generate:v1.0.0",
]

@app.on_event("startup")
async def preload_images():
    client = docker.from_env()
    for image in IMAGES:
        try:
            logging.info(f"Preloading image: {image}")
            client.images.pull(image)
            logging.info(f"Successfully preloaded {image}")
        except docker.errors.APIError as e:
            logging.error(f"Failed to preload {image}: {e}")
            raise # Or handle more gracefully

async def run_rag_pipeline(query: str, collection: str = "default"):
    async with dagger.Connection(dagger.Config()) as client:
        input_data = {
            "query": query,
            "collection": collection,
            "qdrant_host": "qdrant:6333" # Assuming Qdrant is accessible by this name from containers
        }

        input_json_str = json.dumps(input_data)

        # Step 1: Retrieve
        retrieve_input_file = client.host().directory().with_new_file("input.json", input_json_str).file("input.json")

        retrieve_container = (
            client.container()
            .from_("mycompany/retrieve:v1.0.0")
            .with_mounted_file("/input.json", retrieve_input_file)
            .with_exec(["--input", "/input.json", "--output", "/output.json"])
        )
        retrieve_output_file = retrieve_container.file("/output.json")
        retrieve_output_contents = await retrieve_output_file.contents()

        # Step 2: Augment
        augment_input_file = client.host().directory().with_new_file("input.json", retrieve_output_contents).file("input.json")

        augment_container = (
            client.container()
            .from_("mycompany/augment:v1.0.0")
            .with_mounted_file("/input.json", augment_input_file)
            .with_exec(["--input", "/input.json", "--output", "/output.json"])
        )
        augment_output_file = augment_container.file("/output.json")
        augment_output_contents = await augment_output_file.contents()

        # Step 3: Generate
        generate_input_file = client.host().directory().with_new_file("input.json", augment_output_contents).file("input.json")

        generate_container = (
            client.container()
            .from_("mycompany/generate:v1.0.0")
            .with_mounted_file("/input.json", generate_input_file)
            .with_exec(["--input", "/input.json", "--output", "/output.json"])
        )
        generate_output_file = generate_container.file("/output.json")
        final_result_contents = await generate_output_file.contents()

        return final_result_contents

class RagRequest(BaseModel):
    query: str
    collection: str = "default"

@app.post("/rag")
async def run_rag(request: RagRequest):
    result = await run_rag_pipeline(request.query, request.collection)
    return json.loads(result)

# Configure logging
logging.basicConfig(level=logging.INFO)

```

### Docker Compose (for FastAPI, Qdrant, Dagger)

```yaml
version: '3.8'
services:
  fastapi:
    build: . # Assuming your FastAPI app Dockerfile is in the root
    ports:
      - "8000:8000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock # To allow FastAPI to interact with Docker daemon for preloading
    environment:
      DOCKER_HOST: unix:///var/run/docker.sock # For Dagger client inside FastAPI if not using engine
      # QDRANT_HOST: qdrant # If modules need to know Qdrant host
    depends_on:
      - qdrant
      # - dagger-engine # Only if you intend Dagger client in FastAPI to connect to a Dagger engine service

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334" # gRPC port
    # volumes:
    #   - ./qdrant_storage:/qdrant/storage # Persist Qdrant data

  # Optional: Dagger Engine Service (if you prefer to connect to it explicitly)
  # dagger-engine:
  #   image: registry.dagger.io/engine:v0.10.0 # Use a specific version
  #   privileged: true # Dagger engine needs privileges
  #   ports:
  #     - "1234:1234" # Example port, configure Dagger client to connect here
  #   volumes:
  #     - /var/run/docker.sock:/var/run/docker.sock
  #     - dagger-cache:/var/lib/dagger # Persist Dagger cache

# volumes: # Define if using dagger-engine with persistent cache
#   dagger-cache:

```

*Note: The Dagger client in Python by default tries to auto-provision an engine or connect to one. If running the FastAPI app itself in a container, Dagger needs access to a Docker daemon or a running Dagger engine.The provided `run_rag_pipeline` uses `client.host().directory().with_new_file(...)` which is a more modern Dagger Python SDK approach than `client.host().file().from_string()` for creating files to be mounted.*

# 4. Limitations of Current Approach

While containerized modules provide isolation and reusability, there are limitations due to the `Dagger` Python SDK:

- **No Module Function Calls:** The SDK doesn’t support calling `Dagger` module functions programmatically (only via `dagger call` CLI), forcing us to use containers instead of native `Dagger` modules.
- **Container Overhead:** Temporary containers add slight latency, even with preloaded images.
- **Orchestration Complexity:** Chaining containers requires careful input/output handling (e.g., mounting `JSON` files).

These limitations could be addressed if the Dagger Python SDK supports module function calls in a future release — a feature that is already supported in the TypeScript and Go SDKs.

# 5. Future: Using Dagger Modules

Once the `Dagger` Python SDK supports calling module functions, we can replace containerized modules with native `Dagger` modules, simplifying the pipeline while maintaining modularity and isolation. Below is a hypothetical example of how the `RAG` pipeline would look.

## 5.1 Example: Dagger Module for `retrieve`

**Module Definition (published to a Dagger registry):**

```python
from dagger import dag, field, function, object_type
import json
from superlinked import QdrantConnector # Assuming this is the correct import

@object_type
class RetrieveModule:
    @function
    async def run(self, input_json: str) -> str:
        """Retrieves data based on the input JSON string."""
        data = json.loads(input_json)

        # Ensure QdrantConnector can be initialized and used here.
        # Dependencies for QdrantConnector would need to be part of the Dagger module's environment.
        connector = QdrantConnector(host=data.get("qdrant_host", "qdrant:6333"))

        # Assuming QdrantConnector.query is async or can be run in an executor
        # For simplicity, let's assume it's awaitable as shown in original.
        # If not, use asyncio.to_thread for blocking calls.
        results = await connector.query(data["query"], collection=data.get("collection", "default"))

        return json.dumps({"results": results})

# To make this a runnable module, you might need a top-level function or class
# that Dagger can pick up, e.g.
# @dag.module()
# def retrieve_service():
#     return RetrieveModule()

```

*Note: The exact structure of a Dagger Python module (`@dag.module`, `@object_type`, `@function`) can evolve. The example above reflects common patterns.*

**Publish:**

```
# Assuming your module is in a directory `retrieve_module` with a `dagger.json`
# cd retrieve_module
dagger module publish -m . mycompany/retrieve:v1.0.0
# Or similar command based on Dagger CLI version

```

## 5.2 Updated FastAPI Pipeline

```python
from fastapi import FastAPI
import dagger
import json
from pydantic import BaseModel

app = FastAPI()

# Hypothetical: Load Dagger modules (actual API might differ)
# This assumes a way to load modules programmatically.
# The Dagger Python SDK would provide mechanisms for this.

# This is highly speculative as SDK support is not there yet.
# One might initialize a Dagger client and then get module instances.
# For example:
# async def get_retrieve_module(client: dagger.Client):
#     return client.module().from_reference("mycompany/retrieve:v1.0.0")

async def run_rag_pipeline_with_modules(client: dagger.Client, query: str, collection: str = "default"):
    input_data = {
        "query": query,
        "collection": collection,
        "qdrant_host": "qdrant:6333" # Module needs to know how to connect
    }
    input_json_str = json.dumps(input_data)

    # Step 1: Call retrieve module
    # The exact invocation method will depend on the SDK's API
    # retrieve_module = await get_retrieve_module(client) # Or however modules are obtained
    # retrieve_result_json = await retrieve_module.run(input_json=input_json_str)

    # Using a more direct, albeit still hypothetical, way based on RFC text:
    # This assumes 'dagger.module(...)' returns a callable proxy or similar.
    # And that these modules are already configured within the Dagger context.

    retrieve_module_ref = client.module().from_reference("mycompany/retrieve:v1.0.0")
    retrieve_result_json = await retrieve_module_ref.call("run", input_json=input_json_str) # Hypothetical

    augment_module_ref = client.module().from_reference("mycompany/augment:v1.0.0")
    augment_result_json = await augment_module_ref.call("run", input_json=retrieve_result_json) # Hypothetical

    generate_module_ref = client.module().from_reference("mycompany/generate:v1.0.0")
    generate_result_json = await generate_module_ref.call("run", input_json=augment_result_json) # Hypothetical

    return generate_result_json

class RagRequest(BaseModel):
    query: str
    collection: str = "default"

@app.post("/rag_modules") # Different endpoint for clarity
async def run_rag_with_modules_endpoint(request: RagRequest):
    async with dagger.Connection(dagger.Config()) as client:
        result_json = await run_rag_pipeline_with_modules(client, request.query, request.collection)
        return json.loads(result_json)

# Configure logging
logging.basicConfig(level=logging.INFO)

```

### Benefits (of Dagger Modules Approach):

- **Simpler Pipeline:** No need to manage containers or file mounts; module functions are called directly.
- **Same Isolation:** `Dagger` runs modules in isolated environments.
- **Reusability:** Modules are still published to a registry.
- **Lower Overhead:** Eliminates container orchestration latency.

### Transition Plan:

- Rewrite each container’s `main.py` as a `Dagger` module.
- Publish modules to a `Dagger` registry.
- Update the pipeline to call module functions instead of containers.

# 6. Benefits (of Current Containerized Proposal)

- **Modularity:** Each `RAG` step is a self-contained module, easy to develop and test.
- **Isolation:** Containers (or future modules) prevent dependency conflicts.
- **Reusability:** `Docker` registry (or `Dagger` registry) enables sharing across projects.
- **Performance:** Preloading images eliminates cold starts.
- **Future-Proof:** Architecture supports a seamless transition to `Dagger` modules when available.

# 7. Risks and Mitigations

- **Risk:** Container overhead may impact latency for high-throughput workloads.
    - **Mitigation:** Optimize images (e.g., use slim base images) and monitor performance.
- **Risk:** Managing multiple module images could become complex.
    - **Mitigation:** Use a centralized registry with clear versioning (e.g., `v1.0.0`).
- **Risk:** SDK support for module functions may be delayed or differ from expectations.
    - **Mitigation:** Current containerized approach is robust and can be maintained until SDK support is confirmed.

# 8. Implementation Plan

- **Prototype (time estimation):**
    - Implement `retrieve`, `augment`, and `generate` modules as containers.
    - Set up `FastAPI` pipeline and preloading logic.
    - Test locally with `Qdrant` and a sample `RAG` workflow.
- **Registry Setup (1 week):**
    - Configure a private `Docker` registry (e.g., `AWS ECR`).
    - Publish module images.
- **Integration (time estimation):**
    - Deploy to staging environment.
    - Validate performance and reusability across two test projects.
- **Documentation (time estimation):**
    - Document module interfaces and setup instructions.
- **Future Transition (TBD):**
    - Monitor `Dagger SDK` updates for module function support.
    - Rewrite modules and pipeline as needed.

# 9. Alternatives Considered

- **Python Libraries:** Package `RAG` steps as `pip-installable` libraries.
    - **Pros:** Simpler integration, no container overhead.
    - **Cons:** Weaker isolation, potential dependency conflicts.
- **Dagger CLI:** Use `dagger call` to invoke modules programmatically.
    - **Pros:** Aligns with `Dagger`’s module system.
    - **Cons:** Brittle `CLI` parsing, less programmatic control.

# 10. Conclusion

This modular architecture provides a robust, reusable framework for `RAG` workflows using containerized modules orchestrated by `Dagger`. Preloading images ensures performance, and the design is future-proof for transitioning to `Dagger` modules when the `Python SDK` supports function calls. We recommend prototyping this approach and iterating based on team feedback.

# 11. Feedback Requested

1. Is the containerized module structure clear and practical?
2. Are there additional `RAG` steps or requirements to include?
3. Any concerns about registry management or `Dagger SDK` limitations?
4. Suggestions for optimizing performance or simplifying the pipeline?

Please provide feedback by `[date]` to finalize the design.