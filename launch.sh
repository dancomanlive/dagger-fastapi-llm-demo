#!/bin/bash
# launch.sh - Docker launcher for the RAG Chat system

echo "🤖 RAG Chat System - Docker Launcher"
echo "===================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Copy .env.example to .env and add your API keys"
    echo ""
    read -p "Do you want to continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "🐳 Starting all services with Docker Compose..."
echo ""
echo "Services will be available at:"
echo "  💬 Gradio Chat UI:   http://localhost:7860"
echo "  📡 FastAPI Backend:  http://localhost:8000"
echo "  🔍 Retriever API:    http://localhost:8001"
echo "  🗄️  Qdrant Database:  http://localhost:6333"
echo "  📊 API Docs:         http://localhost:8000/docs"
echo ""

# Build and start all services
echo "🚀 Building and starting containers..."
docker-compose up --build

echo ""
echo "👋 All services stopped."
