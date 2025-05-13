#!/bin/bash
# Docker network diagnostic script
# Used to troubleshoot container connectivity issues

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Docker Network Diagnostic Tool${NC}"
echo "This script will help diagnose Docker networking issues in the RAG pipeline."

# Check if Docker is running
echo -e "\n${YELLOW}1. Checking Docker service...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running!${NC}"
    echo "Please start Docker and try again."
    exit 1
else
    echo -e "${GREEN}Docker is running correctly.${NC}"
fi

# Check for the custom network
echo -e "\n${YELLOW}2. Checking for custom_network...${NC}"
if ! docker network ls | grep -q custom_network; then
    echo -e "${RED}Error: custom_network not found!${NC}"
    echo "Creating network now..."
    docker network create custom_network
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create custom_network!${NC}"
        exit 1
    else
        echo -e "${GREEN}Successfully created custom_network.${NC}"
    fi
else
    echo -e "${GREEN}custom_network exists.${NC}"
fi

# Check containers running on the network
echo -e "\n${YELLOW}3. Checking containers on custom_network...${NC}"
CONTAINERS=$(docker network inspect custom_network -f '{{range .Containers}}{{.Name}} {{end}}')
if [ -z "$CONTAINERS" ]; then
    echo -e "${RED}No containers connected to custom_network!${NC}"
else
    echo -e "${GREEN}Containers on network: $CONTAINERS${NC}"
fi

# Check if FastAPI container is running
echo -e "\n${YELLOW}4. Checking FastAPI container...${NC}"
if ! docker ps | grep -q fastapi; then
    echo -e "${RED}FastAPI container is not running!${NC}"
    echo "Would you like to start the containers? [y/N]"
    read -r RESPONSE
    if [[ "$RESPONSE" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        docker-compose up -d
    else
        echo "Continuing with diagnostics..."
    fi
else
    echo -e "${GREEN}FastAPI container is running.${NC}"
fi

# Check if Qdrant container is running
echo -e "\n${YELLOW}5. Checking Qdrant container...${NC}"
if ! docker ps | grep -q qdrant; then
    echo -e "${RED}Qdrant container is not running!${NC}"
    echo "Would you like to start the containers? [y/N]"
    read -r RESPONSE
    if [[ "$RESPONSE" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        docker-compose up -d
    else
        echo "Continuing with diagnostics..."
    fi
else
    echo -e "${GREEN}Qdrant container is running.${NC}"
fi

# Test network connectivity between containers
echo -e "\n${YELLOW}6. Testing container-to-container connectivity...${NC}"
if docker ps | grep -q fastapi && docker ps | grep -q qdrant; then
    echo "Testing if FastAPI can reach Qdrant..."
    if docker-compose exec -T fastapi curl -s -f --connect-timeout 5 http://qdrant:6333/healthz > /dev/null; then
        echo -e "${GREEN}Success: FastAPI container can reach Qdrant service.${NC}"
    else
        echo -e "${RED}Error: FastAPI container cannot reach Qdrant service.${NC}"
        echo "Possible solutions:"
        echo "1. Restart the containers: docker-compose restart"
        echo "2. Recreate the network: docker network rm custom_network && docker network create custom_network"
        echo "3. Check for any firewall issues on your host"
    fi
else
    echo -e "${YELLOW}Skipping connectivity test as one or more containers are not running.${NC}"
fi

# Show Docker network details
echo -e "\n${YELLOW}7. Docker network configuration details:${NC}"
echo -e "\n${YELLOW}Listing all Docker networks:${NC}"
docker network ls

echo -e "\n${YELLOW}Details of custom_network:${NC}"
docker network inspect custom_network

echo -e "\n${YELLOW}Container IP addresses:${NC}"
docker inspect -f '{{.Name}} - {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker ps -q)

echo -e "\n${GREEN}Diagnostic complete.${NC}"
echo "If you're still having issues, try:"
echo "1. Restart Docker completely"
echo "2. Run ./run_demo.sh to rebuild and restart everything"
echo "3. Check for any port conflicts on your host machine"
