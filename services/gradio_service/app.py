#!/usr/bin/env python3
"""
Main entry point for the RAG Chat Assistant.

This is a clean, modular implementation with separated concerns:
- rag_service.py: Business logic and service integrations
- gradio_ui.py: User interface layer
- app.py: Main entry point and configuration
"""

import os
import sys
from gradio_ui import GradioInterface


def main():
    """Main entry point for the RAG Chat Assistant"""
    
    print("🚀 RAG Chat Assistant - Starting Up...")
    print("=" * 50)
    
    # Check environment variables
    required_env_vars = ["OPENAI_API_KEY"]
    optional_env_vars = {
        "TEMPORAL_HOST": "localhost:7233",
        "TEMPORAL_NAMESPACE": "default"
    }
    
    # Check required environment variables
    missing_vars = []
    for var in required_env_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("   Please set these variables and try again.")
        sys.exit(1)
    
    # Show configuration
    print("📋 Configuration:")
    for var in required_env_vars:
        print(f"   ✅ {var}: {'Set' if os.environ.get(var) else 'Not Set'}")
    
    for var, default in optional_env_vars.items():
        value = os.environ.get(var, default)
        print(f"   🔧 {var}: {value}")
    
    print("=" * 50)
    
    # Create and launch the interface
    try:
        interface = GradioInterface()
        interface.launch()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"❌ Error starting application: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
