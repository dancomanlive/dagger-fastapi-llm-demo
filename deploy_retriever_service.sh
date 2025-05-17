#!/bin/bash

# Deploy script for setting up the retriever service with Docker Compose

# Print steps with color
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting deployment of Retriever Service with Docker Compose${NC}"

# Step 1: Build the retriever service image
echo -e "${YELLOW}Step 1: Building the retriever service Docker image...${NC}"
cd modules/retriever_service
docker build -t my-retriever-service:latest \
  --build-arg EMBEDDING_MODEL_ARG="sentence-transformers/all-MiniLM-L6-v2" \
  .
cd ../..

# Step 2: Start the services using Docker Compose
echo -e "${YELLOW}Step 2: Starting services with Docker Compose...${NC}"
docker-compose up -d qdrant retriever-service

# Step 3: Check service status
echo -e "${YELLOW}Step 3: Checking service status...${NC}"
sleep 5 # Give services time to start
echo "Qdrant status:"
curl -s http://localhost:6333/healthz || echo "Qdrant not responding"
echo 
echo "Retriever Service should be running on port 8001"

# Step 4: Send a test request to the retriever service
echo -e "${YELLOW}Step 4: Testing retriever service with a sample query...${NC}"
echo "This test might fail if you don't have a 'default' collection in Qdrant yet."
echo "That's okay - we're just making sure the service and model respond."

TEST_REQUEST='{
  "query": "This is a test query to verify the model is loaded",
  "collection": "default",
  "top_k": 1
}'

echo "Sending test request to retriever service..."
curl -s -X POST http://localhost:8001/retrieve \
  -H "Content-Type: application/json" \
  -d "$TEST_REQUEST" || echo "Test request failed, but service might still be starting up"
echo

echo -e "${GREEN}Deployment complete!${NC}"
echo "Retriever service should now be running at http://localhost:8001"
echo "Qdrant should be accessible at http://localhost:6333"
echo 
echo "You can now run the RAG pipeline with: python rag_pipeline.py \"your query\""
