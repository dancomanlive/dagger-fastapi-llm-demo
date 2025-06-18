#!/bin/bash

# Simple script to clean up all document collections in Qdrant
# Usage: ./scripts/cleanup_collections.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${YELLOW}[INFO]${NC} $1"
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

# Check if Qdrant is running
if ! curl -s http://localhost:6333/healthz > /dev/null; then
    print_error "Qdrant is not running at http://localhost:6333"
    print_error "Please start the services first: docker-compose up -d qdrant"
    exit 1
fi

print_status "🧹 Cleaning up all document collections from Qdrant..."

# Get list of collections
collections=$(curl -s http://localhost:6333/collections | jq -r '.result.collections[].name' 2>/dev/null || echo "")

if [ -n "$collections" ]; then
    echo "$collections" | while IFS= read -r collection; do
        if [[ "$collection" == *"document"* ]] || [[ "$collection" == *"chunk"* ]] || [[ "$collection" == "test-"* ]]; then
            print_status "🗑️ Removing collection: $collection"
            cleanup_response=$(curl -s -X DELETE "http://localhost:6333/collections/${collection}")
            if echo "$cleanup_response" | grep -q '"status":"ok"' || echo "$cleanup_response" | grep -q '"result":true'; then
                print_success "✅ Collection '$collection' removed successfully!"
            else
                print_warning "⚠️ Could not remove collection '$collection'"
                echo "Response: $cleanup_response"
            fi
        else
            print_status "ℹ️ Skipping collection: $collection (not a document collection)"
        fi
    done
else
    print_success "✅ No collections found in Qdrant"
fi

# Final verification
remaining_collections=$(curl -s http://localhost:6333/collections | jq -r '.result.collections[].name' 2>/dev/null || echo "")
if [ -z "$remaining_collections" ]; then
    print_success "🎉 All document collections have been cleaned up successfully!"
else
    print_status "📋 Remaining collections:"
    echo "$remaining_collections" | while IFS= read -r collection; do
        echo "  - $collection"
    done
fi
