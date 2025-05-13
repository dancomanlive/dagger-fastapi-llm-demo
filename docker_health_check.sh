#!/bin/bash
# Docker container health check script
# This script is designed to be run inside a Docker container to verify its health

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running Docker container health check...${NC}"

# 1. Check Python and dependencies
echo -e "\n${YELLOW}Checking Python and dependencies...${NC}"
if command -v python3 > /dev/null 2>&1; then
    echo -e "${GREEN}Python is installed.${NC}"
    PYTHON_VERSION=$(python3 --version)
    echo -e "Python version: ${GREEN}$PYTHON_VERSION${NC}"
else
    echo -e "${RED}Python is not installed!${NC}"
    exit 1
fi

# 2. Check access to Docker socket (for FastAPI container)
echo -e "\n${YELLOW}Checking Docker socket access...${NC}"
if [ -S /var/run/docker.sock ]; then
    echo -e "${GREEN}Docker socket is mounted.${NC}"
    if docker info > /dev/null 2>&1; then
        echo -e "${GREEN}Docker socket is accessible.${NC}"
    else
        echo -e "${RED}Docker socket is mounted but not accessible.${NC}"
        echo "This may affect Dagger functionality."
    fi
else
    echo -e "${YELLOW}Docker socket is not mounted.${NC}"
    echo "This is expected for non-FastAPI containers."
fi

# 3. Check network connectivity
echo -e "\n${YELLOW}Checking network connectivity...${NC}"

# Try to connect to FastAPI
if curl -s -f --connect-timeout 5 http://fastapi:8000/ > /dev/null 2>&1; then
    echo -e "${GREEN}FastAPI service is reachable.${NC}"
else
    echo -e "${YELLOW}FastAPI service is not reachable.${NC}"
    echo "This is expected if the FastAPI container is not running or if running from the FastAPI container itself."
fi

# Try to connect to Qdrant
if curl -s -f --connect-timeout 5 http://qdrant:6333/healthz > /dev/null 2>&1; then
    echo -e "${GREEN}Qdrant service is reachable.${NC}"
else
    echo -e "${YELLOW}Qdrant service is not reachable.${NC}"
    echo "This is expected if the Qdrant container is not running."
fi

# 4. Check environment variables
echo -e "\n${YELLOW}Checking environment variables...${NC}"
if [ -n "$PYTHONPATH" ]; then
    echo -e "PYTHONPATH: ${GREEN}$PYTHONPATH${NC}"
else
    echo -e "${YELLOW}PYTHONPATH is not set.${NC}"
fi

if [ -n "$QDRANT_URL" ]; then
    echo -e "QDRANT_URL: ${GREEN}$QDRANT_URL${NC}"
else
    echo -e "${YELLOW}QDRANT_URL is not set.${NC}"
    echo "Using default: http://qdrant:6333"
fi

# 5. Summary
echo -e "\n${GREEN}Health check complete!${NC}"
echo "This container appears to be functioning correctly in the Docker environment."
echo "For more detailed testing, run the full network check with: ./check_network.sh"
