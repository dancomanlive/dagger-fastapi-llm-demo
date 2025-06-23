#!/usr/bin/env python3
"""
Launch script for both Gradio interfaces - Chat and Upload
"""

import subprocess
import sys
import time
import signal
from multiprocessing import Process


def run_chat_interface():
    """Run the main chat interface"""
    try:
        subprocess.run([sys.executable, "app.py"], check=True)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Chat interface error: {e}")


def run_upload_interface():
    """Run the upload interface"""
    try:
        subprocess.run([sys.executable, "upload_app.py"], check=True)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Upload interface error: {e}")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🛑 Shutting down both interfaces...")
    sys.exit(0)


def main():
    """Launch both interfaces"""
    
    # Set up signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Starting SmartÆgent X-7 Gradio Services...")
    print("=" * 50)
    print("📄 Upload Interface: http://localhost:7861")
    print("💬 Chat Interface:   http://localhost:7860")
    print("🔍 Temporal UI:      http://localhost:8081")
    print("=" * 50)
    
    # Start both interfaces as separate processes
    chat_process = Process(target=run_chat_interface, name="ChatInterface")
    upload_process = Process(target=run_upload_interface, name="UploadInterface")
    
    try:
        # Start processes
        chat_process.start()
        time.sleep(2)  # Small delay to avoid port conflicts
        upload_process.start()
        
        print("✅ Both interfaces started successfully!")
        print("   Press Ctrl+C to stop both services")
        
        # Wait for processes
        chat_process.join()
        upload_process.join()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        
    finally:
        # Clean shutdown
        if chat_process.is_alive():
            chat_process.terminate()
            chat_process.join(timeout=5)
        
        if upload_process.is_alive():
            upload_process.terminate()
            upload_process.join(timeout=5)
        
        print("✅ Graceful shutdown completed")


if __name__ == "__main__":
    main()
