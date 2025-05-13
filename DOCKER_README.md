# 🐳 Docker-Only RAG Pipeline 

This project is designed to run exclusively within Docker containers, ensuring consistent execution across environments and eliminating "it works on my machine" issues.

## 🚀 Getting Started

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB of available RAM

### Running the System

The entire system can be started with a single command:

```bash
./run_demo.sh
```

This script will:

1. Set up a dedicated Docker network for container communication
2. Build all required module containers within Docker
3. Start the FastAPI and Qdrant services
4. Verify network connectivity between containers
5. Initialize Qdrant with test data
6. Test the complete RAG pipeline
7. Provide access information for the API

## 📦 Container Architecture

This project uses a fully containerized architecture:

1. **rag_app (FastAPI)**: Main service that orchestrates the RAG pipeline
2. **qdrant**: Vector database for storing and retrieving documents
3. **RAG Module Containers**:
   - **retrieve**: Fetches relevant documents from Qdrant
   - **augment**: Processes and enriches retrieved information 
   - **generate**: Creates the final response using LLM

## 🔄 Container Orchestration

The RAG pipeline uses Dagger to orchestrate containerized modules:

1. The FastAPI service receives a query
2. Dagger creates a pipeline that:
   - Executes the retrieve container
   - Passes the results to the augment container
   - Sends enriched data to the generate container
3. The final response is returned to the user

All communication between modules happens through Docker volumes and networks, ensuring proper isolation and security.

## 🌐 Accessing the System

- **API Endpoint**: http://127.0.0.1:8000/rag
- **Health Check**: http://127.0.0.1:8000/

Example curl command:
```bash
curl -X POST http://127.0.0.1:8000/rag \
  -H "Content-Type: application/json" \
  -d '{"query": "How does RAG solve LLM problems?", "collection": "default"}'
```

## 🧰 Managing the System

### Viewing Logs

```bash
docker-compose logs -f
```

### Stopping the System

```bash
docker-compose down
```

### Restarting the System

```bash
docker-compose restart
```

### Checking System Status

```bash
docker-compose ps
```

## 🔍 Troubleshooting

If you encounter issues:

1. **Network Problems**: 
   - Check if all containers are running: `docker-compose ps`
   - Verify network connectivity: `docker-compose exec fastapi ./check_network.sh`

2. **Container Issues**:
   - Check container logs: `docker-compose logs -f fastapi`
   - Verify Qdrant status: `docker-compose logs -f qdrant`

3. **Data Issues**:
   - Reinitialize the database: `docker-compose exec fastapi ./init_qdrant_docker.sh`

## 📊 Performance Considerations

- The first query might be slow due to container startup time
- For production use, consider using persistent storage for Qdrant
- Scale FastAPI service horizontally if needed

## 🔒 Security Notes

- All container-to-container communication happens over the private Docker network
- Only the FastAPI service is exposed to the host (port 8000)
- Container isolation provides defense-in-depth security

## 🔌 Docker Networking Details

This project uses a dedicated Docker network called `custom_network` for all container communication:

```bash
# The network is created by run_demo.sh
docker network create custom_network
```

### Network Architecture

- **Container Names as Hostnames**: Inside the Docker network, containers can refer to each other by service name (e.g., `qdrant:6333` instead of IP addresses)
- **Network Isolation**: The custom network isolates RAG pipeline traffic from other Docker containers on the host
- **Port Mapping**: Only necessary ports are mapped to the host (8000 for FastAPI, 6333/6334 for Qdrant)

### Inter-Container Communication

- FastAPI → Qdrant: Uses `http://qdrant:6333` internally
- Dagger modules → FastAPI: Orchestrated by the FastAPI container
- Host → Services: Via mapped ports using `127.0.0.1`
