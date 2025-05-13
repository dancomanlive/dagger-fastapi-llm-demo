#!/bin/bash
# Script to initialize Qdrant with test data inside Docker environment

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Set Qdrant URL to the service name in Docker network
export QDRANT_URL="http://localhost:6333"

echo -e "${YELLOW}Initializing Qdrant with test data inside Docker environment...${NC}"
echo -e "Using Qdrant URL: ${GREEN}$QDRANT_URL${NC}"

# Wait for Qdrant to be fully available
echo -e "${YELLOW}Checking if Qdrant is ready...${NC}"
MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s -f $QDRANT_URL/healthz > /dev/null; then
        echo -e "${GREEN}Qdrant is ready!${NC}"
        break
    else
        echo -e "${YELLOW}Waiting for Qdrant to be ready... (attempt $((RETRY_COUNT+1))/$MAX_RETRIES)${NC}"
        RETRY_COUNT=$((RETRY_COUNT+1))
        sleep 2
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}Qdrant service is not responding. Initialization failed.${NC}"
    exit 1
fi

# Run the init script inside the FastAPI container
# python init_qdrant.py --qdrant_url "http://localhost:6333"
python init_qdrant.py --qdrant_url $QDRANT_URL

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to initialize Qdrant with test data.${NC}"
    exit 1
fi

echo -e "${GREEN}Initialization complete. The RAG pipeline is ready for testing.${NC}"
echo -e "To test the RAG pipeline, run: ${YELLOW}python test_rag_pipeline.py${NC}"
