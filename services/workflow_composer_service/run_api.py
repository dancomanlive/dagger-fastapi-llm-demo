#!/usr/bin/env python3
"""
Entry point for the workflow composer service API server.
"""
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    import uvicorn
    from api.main import app
    
    print("🚀 Starting Workflow Composer Service API...")
    print("📖 API Documentation: http://localhost:8001/docs")
    print("🔍 GraphQL Playground: http://localhost:8001/graphql")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)
