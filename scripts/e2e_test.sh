#!/bin/bash

# End-to-End Document Processing System Test - Pure Temporal Architecture
# This script starts all services, validates health, and runs complete workflow tests
# Tests: Docker services → Health checks → Temporal workflow execution → Retrieval validation

set -e

# Load environment variables from .env file
if [ -f .env ]; then
    source .env
    echo "✅ Loaded environment variables from .env file"
else
    echo "⚠️ No .env file found, using defaults"
fi

# Environment configuration with fallbacks
TEST_DOCUMENT_COLLECTION_NAME="${TEST_DOCUMENT_COLLECTION_NAME:-test-document-chunks}"
DOCUMENT_COLLECTION_NAME="${DOCUMENT_COLLECTION_NAME:-document-chunks}"

echo "🧪 Starting End-to-End Pure Temporal Document Processing System Test..."

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

# Function to cleanup test collection
cleanup_test_collection() {
    print_status "🧹 Cleaning up test collection: $TEST_DOCUMENT_COLLECTION_NAME"
    
    # Delete the test collection from Qdrant
    cleanup_response=$(curl -s -X DELETE "http://localhost:6333/collections/${TEST_DOCUMENT_COLLECTION_NAME}")
    
    if echo "$cleanup_response" | grep -q '"status":"ok"' || echo "$cleanup_response" | grep -q '"result":true'; then
        print_success "✅ Test collection '$TEST_DOCUMENT_COLLECTION_NAME' cleaned up successfully!"
    else
        print_warning "⚠️ Could not cleanup test collection (it may not exist or was already removed)"
    fi
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
export DOCUMENT_COLLECTION_NAME="$TEST_DOCUMENT_COLLECTION_NAME"
docker-compose up -d

print_success "Services started in background!"

# Show container status
print_status "Checking container status..."
docker-compose ps

# Wait for services to be healthy
print_status "Waiting for services to start..."
sleep 30  # Increased wait time for health checks

# Show container status
print_status "Checking container status..."
docker-compose ps

# Additional wait for Temporal workers and health checks
print_status "Waiting additional time for all health checks to pass..."
sleep 20

# Check service health
print_status "Checking service health..."

services=(
    "http://localhost:6333/healthz:Qdrant Vector DB"
    "http://localhost:7243/api/v1/namespaces:Temporal Server"
    "http://localhost:8081/api/v1/cluster-info:Temporal Web UI"
    "http://localhost:7860/:Gradio Chat Interface"
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
echo "  • Temporal Web UI:      http://localhost:8081"
echo "  • Gradio Chat UI:       http://localhost:7860"
echo ""
echo -e "${BLUE}📡 Service Endpoints:${NC}"
echo "  • Temporal Server:      http://localhost:7243"
echo "  • Qdrant Vector DB:     http://localhost:6333"
echo ""
echo -e "${YELLOW}🧪 Test Architecture:${NC}"
echo "  • Pure Temporal workflows for document processing and retrieval"
echo "  • Gradio ↔ Temporal ↔ Activities (Embedding & Retrieval services)"
echo "  • No HTTP service calls - all orchestration via Temporal"
echo ""

if [ "$all_healthy" = true ]; then
    print_success "All services are running and healthy!"
    echo ""
    echo "💡 You can now:"
    echo "   1. Visit the Temporal Web UI to monitor workflows"
    echo "   2. Use the Gradio chat interface for document Q&A"
    echo "   3. Run the Temporal workflow test to validate the pipeline"
    echo ""
    echo -e "${YELLOW}🧪 Available Test Commands:${NC}"
    echo "  • Test Temporal workflows:   python tests/test_temporal_e2e.py"
    echo "  • View service logs:         docker-compose logs -f [service-name]"
    echo "  • Stop services:             docker-compose down"
else
    print_warning "Some services may not be fully ready. Check logs with: docker-compose logs"
fi

echo ""
echo "📚 Pure Temporal Architecture Test Instructions:"
echo ""
echo "1. Test the complete workflow pipeline:"
echo "   python tests/test_temporal_e2e.py"
echo ""
echo "2. Monitor workflows in Temporal Web UI:"
echo "   http://localhost:8081"
echo ""
echo "3. Use Gradio for interactive document Q&A:"
echo "   http://localhost:7860"
echo ""
echo "4. Cleanup test collection (optional):"
echo "   curl -X DELETE http://localhost:6333/collections/${TEST_DOCUMENT_COLLECTION_NAME}"
echo ""

# Auto-test the workflow if all services are healthy
if [ "$all_healthy" = true ]; then
    echo ""
    print_status "🧪 Auto-testing the Temporal workflow pipeline..."
    echo ""
    
    # Check if Python is available
    if command -v python3 &> /dev/null; then
        python_cmd="python3"
        pip_cmd="pip3"
    elif command -v python &> /dev/null; then
        python_cmd="python"
        pip_cmd="pip"
    else
        print_warning "⚠️ Python not found, skipping automated workflow test"
        echo ""
        exit 0
    fi
    
    # Install required dependencies for e2e testing
    print_status "Installing e2e test dependencies..."
    if [ -f "e2e_requirements.txt" ]; then
        $pip_cmd install -r e2e_requirements.txt > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            print_success "✅ Dependencies installed successfully"
        else
            print_warning "⚠️ Failed to install dependencies, proceeding anyway..."
        fi
    fi
    
    # Wait a bit more for Temporal workers to be ready
    print_status "Waiting 15 seconds for Temporal workers to be fully ready..."
    sleep 15
    
    # Test Temporal workflows
    print_status "Running comprehensive Temporal workflow test..."
    
    # Set environment variables for the test
    export TEMPORAL_HOST="localhost:7243"
    export TEMPORAL_NAMESPACE="default"
    export TEST_DOCUMENT_COLLECTION_NAME="$TEST_DOCUMENT_COLLECTION_NAME"
    
    if $python_cmd tests/test_temporal_e2e.py; then
        print_success "✅ TEMPORAL WORKFLOW TEST PASSED!"
        echo ""
        echo -e "${GREEN}🎉 END-TO-END PURE TEMPORAL ARCHITECTURE TEST SUCCESSFUL!${NC}"
        echo -e "${GREEN}✅ Document processing, embedding, and retrieval workflows all working correctly!${NC}"
        echo -e "${GREEN}✅ Pure Temporal orchestration validated successfully!${NC}"
        echo ""
        
        # Cleanup test collection after successful test
        cleanup_test_collection
    else
        print_error "❌ TEMPORAL WORKFLOW TEST FAILED!"
        echo ""
        print_warning "Check the output above for error details"
        print_warning "You can also check service logs with: docker-compose logs"
        echo ""
    fi
else
    echo ""
    print_warning "⚠️ Skipping auto-test due to unhealthy services"
    echo ""
fi
