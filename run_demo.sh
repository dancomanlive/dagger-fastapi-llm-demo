#!/bin/bash
# Script to run the complete RAG pipeline demo

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting RAG Pipeline Demo${NC}"
echo -e "This script will guide you through running the complete RAG pipeline with Dagger container orchestration."

# Prompt for Docker Hub username
echo -e "\n${YELLOW}Step 0: Enter your Docker Hub username${NC}"
read -p "Enter your Docker Hub username: " DOCKERHUB_USERNAME
if [ -z "$DOCKERHUB_USERNAME" ]; then
    echo -e "${RED}Docker Hub username is required. Exiting.${NC}"
    exit 1
fi

# Step 1: Create Docker network if it doesn't exist
echo -e "\n${YELLOW}Step 1: Setting up Docker network${NC}"
echo "Creating custom Docker network for container communication..."
docker network inspect custom_network >/dev/null 2>&1 || docker network create custom_network
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create Docker network. Please check Docker permissions.${NC}"
    exit 1
fi
echo -e "${GREEN}Docker network setup complete.${NC}"

# Step 2: Build and push module containers
echo -e "\n${YELLOW}Step 2: Building and pushing module containers${NC}"
echo "Building and pushing the retrieve, augment, and generate module containers to Docker Hub..."
bash build_and_push_modules.sh v1.0.0 "$DOCKERHUB_USERNAME"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to build or push module containers. Please check the script output for errors.${NC}"
    exit 1
fi
echo -e "${GREEN}Module containers built and pushed successfully.${NC}"
# Step 3: Start Docker services
echo -e "\n${YELLOW}Step 3: Starting Docker services${NC}"
echo "Starting FastAPI and Qdrant services..."
docker-compose up -d
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to start Docker services. Please check docker-compose.yml for errors.${NC}"
    exit 1
fi
echo -e "${GREEN}Docker services started successfully.${NC}"

# Step 4: Wait for services to be ready
echo -e "\n${YELLOW}Step 4: Waiting for services to be ready${NC}"
echo "Waiting 10 seconds for services to initialize..."
sleep 10

# Step 5: Verify network connectivity
echo -e "\n${YELLOW}Step 5: Verifying network connectivity${NC}"
echo "Checking Docker network configuration and connectivity between services..."
docker-compose exec -T fastapi bash -c "cd /app && ./check_network.sh"
if [ $? -ne 0 ]; then
    echo -e "${RED}Network checks failed. Please resolve the issues before continuing.${NC}"
    exit 1
fi
echo -e "${GREEN}Network connectivity verified successfully!${NC}"

# Step 6: Run Docker health checks
echo -e "\n${YELLOW}Step 6: Running Docker container health checks${NC}"
echo "Verifying container health and configuration..."
docker-compose exec -T fastapi bash -c "cd /app && ./docker_health_check.sh"
if [ $? -ne 0 ]; then
    echo -e "${RED}Container health check failed. There may be issues with the Docker environment.${NC}"
    echo "Continuing anyway, but some features may not work correctly."
else
    echo -e "${GREEN}Container health check passed!${NC}"
fi

# Step 7: Initialize Qdrant with test data
echo -e "\n${YELLOW}Step 7: Initializing Qdrant with test data${NC}"
echo "Populating Qdrant with sample RAG documents inside Docker..."
docker-compose exec -T fastapi bash -c "./init_qdrant_docker.sh"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to initialize Qdrant with test data. Please check the script output for errors.${NC}"
    exit 1
fi
echo -e "${GREEN}Qdrant successfully initialized with test data.${NC}"

# Step 8: Run the test
echo -e "\n${YELLOW}Step 8: Testing the RAG pipeline${NC}"
echo "Sending a test query to the RAG pipeline..."
echo -e "Query: ${GREEN}\"What is retrieval-augmented generation?\"${NC}"
docker-compose exec fastapi python test_rag_pipeline.py
if [ $? -ne 0 ]; then
    echo -e "${RED}RAG pipeline test failed. Please check the logs for errors:${NC}"
    echo -e "${YELLOW}docker-compose logs fastapi${NC}"
    echo -e "You can still proceed to use the dashboard, but some features may not work properly."
else
    echo -e "${GREEN}RAG pipeline test completed successfully!${NC}"
fi

echo -e "\n${GREEN}Demo complete!${NC}"
echo "The RAG pipeline with Dagger container orchestration is now running."

# Verify all services are still running
echo -e "\n${YELLOW}Performing final verification of services...${NC}"
if ! docker-compose ps | grep -q "fastapi.*Up"; then
    echo -e "${RED}Warning: FastAPI service is not running properly. Some features may not work.${NC}"
else
    echo -e "${GREEN}FastAPI service is running correctly.${NC}"
fi

if ! docker-compose ps | grep -q "qdrant.*Up"; then
    echo -e "${RED}Warning: Qdrant service is not running properly. Some features may not work.${NC}"
else
    echo -e "${GREEN}Qdrant service is running correctly.${NC}"
fi

# Step 9: Access information
echo -e "\n${YELLOW}Step 9: How to access the system${NC}"
echo -e "Since everything is running inside Docker containers, access is only available via the exposed ports."
echo -e "\n${GREEN}Access Methods:${NC}"
echo -e "1. ${YELLOW}Interactive Dashboard:${NC} Open this URL in your browser:"
echo -e "   ${GREEN}http://127.0.0.1:8000/dashboard${NC}"
echo -e "2. ${YELLOW}API Endpoint:${NC} The API is available at:"
echo -e "   ${GREEN}http://127.0.0.1:8000${NC}"
echo -e "3. ${YELLOW}RAG Query:${NC} Send POST requests to:"
echo -e "   ${GREEN}http://127.0.0.1:8000/rag${NC}"
echo -e "\nExample curl command for querying the RAG system:"
echo -e "${YELLOW}curl -X POST http://127.0.0.1:8000/rag -H \"Content-Type: application/json\" -d '{\"query\": \"How does RAG solve LLM problems?\", \"collection\": \"default\"}'${NC}"
echo -e "\nInside Docker network, services can communicate using their service names:"
echo -e "- FastAPI service: ${GREEN}http://fastapi:8000${NC}"
echo -e "- Qdrant service: ${GREEN}http://qdrant:6333${NC}"

echo -e "\n${GREEN}Enjoy the RAG Pipeline demo!${NC}"
echo -e "\n${YELLOW}Docker Management Commands:${NC}"
echo -e "- View container logs: ${GREEN}docker-compose logs -f${NC}"
echo -e "- Stop all containers: ${GREEN}docker-compose down${NC}"
echo -e "- Restart containers: ${GREEN}docker-compose restart${NC}"
echo -e "- Execute command in FastAPI container: ${GREEN}docker-compose exec fastapi <command>${NC}"
echo -e "- Execute command in Qdrant container: ${GREEN}docker-compose exec qdrant <command>${NC}"
echo -e "- View container status: ${GREEN}docker-compose ps${NC}"

echo -e "\n${YELLOW}For more information, refer to the documentation:${NC}"
echo -e "- Docker Documentation: ${GREEN}https://docs.docker.com/${NC}"
echo -e "- FastAPI Documentation: ${GREEN}https://fastapi.tiangolo.com/${NC}"
echo -e "- Dagger Documentation: ${GREEN}https://docs.dagger.io/${NC}"
