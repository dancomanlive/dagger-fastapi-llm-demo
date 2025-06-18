#!/usr/bin/env python3
"""
Standalone runner for the RAG Chat Interface.

This script can be used to run the RAG chat interface standalone for testing,
or as an example of how to integrate it into larger applications.
"""

import sys
import os

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gradio_service import RAGChatInterface


def main():
    """Run the RAG chat interface standalone"""
    
    print("🚀 RAG Chat Interface - Standalone Runner")
    print("=" * 50)
    
    try:
        # Create the interface
        interface = RAGChatInterface()
        
        # Show configuration
        print("📋 Current Configuration:")
        config_dict = interface.get_config()
        for section, settings in config_dict.items():
            print(f"   {section.upper()}:")
            for key, value in settings.items():
                print(f"     {key}: {value}")
        
        print("=" * 50)
        
        # Show system status
        print("🔍 System Status:")
        status = interface.get_status()
        for service, state in status.items():
            print(f"   {service}: {state}")
        
        print("=" * 50)
        print("🌟 Launching interface...")
        
        # Launch the interface
        interface.launch()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
