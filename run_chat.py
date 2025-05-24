#!/usr/bin/env python3
# run_chat.py

"""
Docker-only startup script for the RAG Chat system.
This script is only used inside Docker containers.
"""

import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()

def main():
    """Main entry point for Docker container startup"""
    print("=" * 60)
    print("🤖 RAG Chat Application - Docker Container Mode")
    print("=" * 60)
    
    # Check environment
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("⚠️  Warning: OPENAI_API_KEY not found in environment")
        print("   Make sure to set it in your .env file")
    
    print("\n� Container Information:")
    print("   📡 FastAPI Backend: http://fastapi:8000")
    print("   💬 Gradio Chat UI:  http://0.0.0.0:7860")
    print("   🔍 Retriever API:   http://retriever-service:8000")
    print("   �️  Qdrant DB:       http://qdrant:6333")
    
    print("\n🔄 Container startup sequence:")
    print("   1. qdrant (database)")
    print("   2. retriever-service") 
    print("   3. fastapi (backend)")
    print("   4. gradio-chat (this container)")
    
    print("\n🌟 For Docker usage, run:")
    print("   docker-compose up --build")
    print("\n   Or use: ./launch.sh")
    
    print("\n📝 Note: This script is for Docker container reference only.")
    print("   Use docker-compose to start the full system.")

if __name__ == "__main__":
    main()
