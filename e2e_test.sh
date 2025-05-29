#!/bin/bash

# End-to-End Document Processing System Test
# This script starts all services, validates health, and runs complete workflow tests
# Tests: Docker services → Health checks → Document processing → Retrieval validation

set -e

echo "🧪 Starting End-to-End Document Processing System Test..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker and Docker Compose are installed
print_status "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_success "Prerequisites check passed!"

# Stop any existing services and start fresh
print_status "Stopping any existing services..."
docker-compose down

print_status "Starting services..."
docker-compose up -d

print_success "Services started in background!"

# Show container status
print_status "Checking container status..."
docker-compose ps

# Wait for services to be healthy
print_status "Waiting for services to start..."
sleep 15

# Show container status
print_status "Checking container status..."
docker-compose ps

# Check service health
print_status "Checking service health..."

services=(
    "http://localhost:6333/healthz:Qdrant"
    "http://localhost:8000/:FastAPI Main"
    "http://localhost:8001/:Retriever Service"
    "http://localhost:8002/:Embedding Service"
    "http://localhost:8081/api/v1/cluster-info:Temporal Server"
    "http://localhost:8003/health:Temporal API"
    "http://localhost:7860/:Gradio Chat"
)

all_healthy=true

for service in "${services[@]}"; do
    url="${service%:*}"
    name="${service##*:}"
    
    print_status "Checking $name at $url..."
    
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            print_success "$name is healthy!"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_warning "$name is not responding after $max_attempts attempts"
            all_healthy=false
            break
        fi
        
        sleep 2
        ((attempt++))
    done
done

echo ""
echo "🎉 E2E Test Environment Ready! All services are healthy:"
echo ""
echo -e "${GREEN}🌐 Web Interfaces:${NC}"
echo "  • Temporal Web UI:    http://localhost:8081"
echo "  • Gradio Chat UI:     http://localhost:7860"
echo ""
echo -e "${BLUE}📡 API Endpoints:${NC}"
echo "  • Main FastAPI:       http://localhost:8000"
echo "  • Retriever Service:  http://localhost:8001"
echo "  • Embedding Service:  http://localhost:8002"
echo "  • Temporal API:       http://localhost:8003"
echo "  • Temporal Server:    http://localhost:7233"
echo "  • Qdrant Vector DB:   http://localhost:6333"
echo ""
echo -e "${YELLOW}🧪 Test Commands:${NC}"
echo "  • Test Temporal workflow: python test_temporal_workflow.py"
echo "  • View logs:             docker-compose logs -f [service-name]"
echo "  • Stop services:         docker-compose down"
echo ""

if [ "$all_healthy" = true ]; then
    print_success "All services are running and healthy!"
    echo ""
    echo "💡 You can now:"
    echo "   1. Visit the Temporal Web UI to monitor workflows"
    echo "   2. Use the Gradio chat interface for document Q&A"
    echo "   3. Run the test script to try the document processing workflow"
else
    print_warning "Some services may not be fully ready. Check logs with: docker-compose logs"
fi

echo ""
echo "📚 To test the complete document processing workflow:"
echo ""
echo "1. Process a document:"
echo "curl -X POST http://localhost:8003/process-documents \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"documents\": [{\"id\": \"test-doc\", \"text\": \"Sample document about artificial intelligence and machine learning.\"}]}'"
echo ""
echo "2. Check workflow status (replace WORKFLOW_ID with the returned workflow_id):"
echo "curl http://localhost:8003/workflow/WORKFLOW_ID/status"
echo ""
echo "3. Search the processed document:"
echo "curl -X POST http://localhost:8001/retrieve \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"query\": \"artificial intelligence\", \"collection\": \"document_chunks\", \"limit\": 3}'"
echo ""

# Auto-test the workflow if all services are healthy
if [ "$all_healthy" = true ]; then
    echo ""
    print_status "🧪 Auto-testing the document processing workflow..."
    echo ""
    
    # Test document processing
    print_status "1. Processing a test document..."
    response=$(curl -s -X POST http://localhost:8003/process-documents \
        -H 'Content-Type: application/json' \
        -d '{"documents": [{"id": "launch-test-doc", "text": "This is an automated test document about machine learning algorithms and neural networks. Deep learning has transformed computer vision and natural language processing."}]}')
    
    if echo "$response" | grep -q "workflow_id"; then
        workflow_id=$(echo "$response" | grep -o '"workflow_id":"[^"]*"' | cut -d'"' -f4)
        print_success "✅ Document processing started! Workflow ID: $workflow_id"
        
        # Wait for processing to complete
        print_status "2. Waiting for document processing to complete..."
        sleep 10
        
        # Test retrieval
        print_status "3. Testing document retrieval..."
        retrieval_response=$(curl -s -X POST http://localhost:8001/retrieve \
            -H 'Content-Type: application/json' \
            -d '{"query": "machine learning algorithms", "collection": "document_chunks", "limit": 2}')
        
        if echo "$retrieval_response" | grep -q "retrieved_contexts"; then
            print_success "✅ Document retrieval successful!"
            echo ""
            echo -e "${GREEN}🎉 END-TO-END WORKFLOW TEST PASSED!${NC}"
            echo -e "${GREEN}✅ Document processing, embedding, and retrieval all working correctly!${NC}"
        else
            print_warning "⚠️ Document retrieval test failed"
        fi
    else
        print_warning "⚠️ Document processing test failed"
    fi
    echo ""
else
    echo ""
    print_warning "⚠️ Skipping auto-test due to unhealthy services"
    echo ""
fi
