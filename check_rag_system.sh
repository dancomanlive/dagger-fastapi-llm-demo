#!/bin/bash
# Script to verify that all required Docker images for the RAG pipeline are available

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Checking Docker service status...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running or accessible!${NC}"
    echo "Please start Docker and try again."
    exit 1
fi

echo -e "${GREEN}Docker is running.${NC}"

# List of required images
REQUIRED_IMAGES=(
    "retrieve:v1.0.0"
    "augment:v1.0.0"
    "generate:v1.0.0"
)

echo -e "\n${YELLOW}Checking for required Docker images...${NC}"

MISSING=0
for IMG in "${REQUIRED_IMAGES[@]}"; do
    echo -n "Image $IMG: "
    if docker image inspect "$IMG" > /dev/null 2>&1; then
        echo -e "${GREEN}Found${NC}"
    else
        echo -e "${RED}Missing${NC}"
        MISSING=$((MISSING+1))
    fi
done

if [ $MISSING -gt 0 ]; then
    echo -e "\n${RED}$MISSING required image(s) are missing.${NC}"
    echo "Would you like to build the missing images locally? [y/N]"
    read -r RESPONSE
    if [[ "$RESPONSE" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo -e "\n${YELLOW}Building module images...${NC}"
        ./build_and_push_modules.sh
    else
        echo -e "\n${YELLOW}Please build the images using:${NC}"
        echo "./build_and_push_modules.sh"
        exit 1
    fi
else
    echo -e "\n${GREEN}All required Docker images are available.${NC}"
fi

echo -e "\n${YELLOW}Checking Docker Compose configuration...${NC}"
if docker-compose config > /dev/null 2>&1; then
    echo -e "${GREEN}Docker Compose configuration is valid.${NC}"
else
    echo -e "${RED}Docker Compose configuration has errors!${NC}"
    docker-compose config
    exit 1
fi

echo -e "\n${YELLOW}Checking Docker network...${NC}"
if docker network inspect custom_network > /dev/null 2>&1; then
    echo -e "${GREEN}Docker network 'custom_network' exists.${NC}"
else
    echo -e "${YELLOW}Docker network 'custom_network' does not exist.${NC}"
    echo "Would you like to create it now? [y/N]"
    read -r RESPONSE
    if [[ "$RESPONSE" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo -e "\n${YELLOW}Creating Docker network...${NC}"
        docker network create custom_network
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Docker network 'custom_network' created successfully.${NC}"
        else
            echo -e "${RED}Failed to create Docker network!${NC}"
            exit 1
        fi
    else
        echo -e "\n${YELLOW}The Docker network is required for inter-container communication.${NC}"
        echo "Create it manually with: docker network create custom_network"
        exit 1
    fi
fi

echo -e "\n${GREEN}All checks passed! The system is ready to run.${NC}"
echo "Run the full demo with: ./run_demo.sh"
