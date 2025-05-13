#!/bin/bash
# Script to check network connectivity within the Docker environment

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Testing network connectivity within Docker...${NC}"

# Test connectivity to Qdrant
echo -e "\nTesting connectivity to Qdrant service..."
curl -s -o /dev/null -w "%{http_code}" http://qdrant:6333/healthz
QDRANT_STATUS=$?

if [ $QDRANT_STATUS -eq 0 ]; then
    echo -e "${GREEN}Success: FastAPI container can reach Qdrant service.${NC}"
else
    echo -e "${RED}Error: FastAPI container cannot reach Qdrant service.${NC}"
    echo "This may cause the RAG pipeline to fail."
    echo "Troubleshooting steps:"
    echo "1. Ensure both services are on the same Docker network"
    echo "2. Check that the Qdrant service name is correct in your configuration"
    echo "3. Verify Qdrant is running: check Docker logs"
    exit 1
fi

# Test FastAPI health endpoint
echo -e "\nTesting FastAPI health endpoint..."
# When testing from inside the FastAPI container itself, use 127.0.0.1
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/
FASTAPI_STATUS=$?

if [ $FASTAPI_STATUS -eq 0 ]; then
    echo -e "${GREEN}Success: FastAPI health endpoint is accessible.${NC}"
else
    echo -e "${RED}Error: Cannot access FastAPI health endpoint.${NC}"
    echo "Troubleshooting steps:"
    echo "1. Check if the FastAPI app is running correctly"
    echo "2. Check the application logs for errors"
    exit 1
fi

# Test the RAG endpoint specifically
echo -e "\nTesting RAG endpoint..."
# When testing from inside the FastAPI container, use 127.0.0.1
RESULT=$(curl -s -X POST http://127.0.0.1:8000/rag -H "Content-Type: application/json" -d '{"query": "test", "collection": "default"}')
RAG_STATUS=$?

if [ $RAG_STATUS -ne 0 ]; then
    echo -e "${RED}Error: Could not connect to RAG endpoint.${NC}"
    echo "Network connection issue detected."
    exit 1
fi

if echo "$RESULT" | grep -q "response"; then
    echo -e "${GREEN}Success: RAG endpoint is responding correctly.${NC}"
else
    echo -e "${RED}Error: RAG endpoint is not responding correctly.${NC}"
    echo "Response from RAG endpoint: $RESULT"
    echo "This may indicate an issue with the RAG pipeline configuration."
    echo "Troubleshooting steps:"
    echo "1. Check if Qdrant has been initialized with data using init_qdrant_docker.sh"
    echo "2. Verify that all module containers were built correctly with build_and_push_modules.sh"
    echo "3. Check container logs with: docker-compose logs fastapi"
    exit 1
fi

echo -e "\n${GREEN}All network checks passed!${NC}"
echo "The Docker network is properly configured for the RAG pipeline."
