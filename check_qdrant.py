#!/usr/bin/env python3
"""
Script to check Qdrant service status and diagnose connection issues
"""
import os
import sys
import json
import argparse
import requests
import socket
import time

def check_port_open(host, port, timeout=2):
    """Check if a port is open on a host"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def check_qdrant_rest_api(url, timeout=5):
    """Test Qdrant REST API directly"""
    try:
        response = requests.get(f"{url}/collections", timeout=timeout)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"Status code: {response.status_code}, Response: {response.text}"
    except Exception as e:
        return False, str(e)

def check_docker_running():
    """Check if Docker is running and get Qdrant container details"""
    try:
        command = "docker ps -f name=qdrant --format '{{.Names}} {{.Status}} {{.Ports}}'"
        import subprocess
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            return False, "Docker command failed"
        if "qdrant" not in result.stdout:
            return False, "No Qdrant container found running"
        return True, result.stdout.strip()
    except Exception as e:
        return False, str(e)

def main():
    parser = argparse.ArgumentParser(description="Check Qdrant service status")
    parser.add_argument("--url", default="http://qdrant:6333", help="Qdrant URL to test")
    parser.add_argument("--host", default="localhost", help="Host to check port")
    parser.add_argument("--port", type=int, default=6333, help="Port to check")
    args = parser.parse_args()
    
    print(f"=== Qdrant Connectivity Diagnostic Tool ===")
    
    # Check if port is open
    print(f"\nChecking if port {args.port} is open on {args.host}...")
    port_open = check_port_open(args.host, args.port)
    if port_open:
        print(f"✅ Port {args.port} is open on {args.host}")
    else:
        print(f"❌ Port {args.port} is closed on {args.host}")
    
    # Check Docker status
    print("\nChecking Docker and Qdrant container status...")
    docker_status, docker_result = check_docker_running()
    if docker_status:
        print(f"✅ Docker is running with Qdrant container: {docker_result}")
    else:
        print(f"❌ Docker issue: {docker_result}")
        print("   Try starting Qdrant with: docker-compose up -d qdrant")
    
    # Test multiple URLs
    # Get environment variable for Dagger
    dagger_url = os.environ.get("QDRANT_HOST", "http://host.docker.internal:6333")
    
    urls_to_test = [
        "http://qdrant:6333",
        "http://localhost:6333",
        "http://127.0.0.1:6333",
        "http://host.docker.internal:6333",
        dagger_url,
        args.url if args.url not in ["http://qdrant:6333", "http://localhost:6333", "http://host.docker.internal:6333"] else None
    ]
    
    urls_to_test = [u for u in urls_to_test if u]  # Filter None values
    
    print("\nTesting Qdrant REST API at multiple URLs:")
    for url in urls_to_test:
        print(f"\nTesting {url}...")
        success, result = check_qdrant_rest_api(url)
        if success:
            print(f"✅ Successfully connected to {url}")
            try:
                collection_count = len(result.get("collections", []))
                print(f"   Found {collection_count} collections")
            except:
                print(f"   Unexpected response format")
        else:
            print(f"❌ Failed to connect to {url}: {result}")
    
    print("\n=== Diagnostic Summary ===")
    if port_open:
        print("✅ Qdrant port is open")
    else:
        print("❌ Qdrant port is not open - service may not be running")
    
    if docker_status:
        print("✅ Qdrant container is running in Docker")
    else:
        print("❌ Qdrant container issues detected")
    
    # Import qdrant-client if available and test programmatic access
    try:
        from qdrant_client import QdrantClient
        print("\nTesting with qdrant-client library...")
        
        for url in urls_to_test:
            try:
                print(f"Connecting to {url}...")
                client = QdrantClient(url=url, timeout=3.0)
                collections = client.get_collections()
                print(f"✅ Successfully connected to {url} with qdrant-client")
                print(f"   Found collections: {[c.name for c in collections.collections]}")
                # Also check health
                try:
                    health = client.http.health()
                    print(f"   Health check: {health}")
                except:
                    try:
                        health = client.http.healthz()
                        print(f"   Health check: {health}")
                    except:
                        print("   Could not perform health check")
                break  # Break on first success
            except Exception as e:
                print(f"❌ Failed to connect to {url} with qdrant-client: {str(e)}")
    except ImportError:
        print("\n❌ qdrant-client not installed. Install with:")
        print("   pip install qdrant-client>=1.7.0")
    
    print("\n=== Next Steps ===")
    print("1. Ensure Qdrant is running:")
    print("   docker-compose up -d qdrant")
    print("2. Verify Qdrant ports are exposed:")
    print("   docker-compose ps")
    print("3. Initialize Qdrant with test data:")
    print("   python init_qdrant.py --qdrant-url http://localhost:6333")
    print("4. Test connection via FastAPI:")
    print("   curl -X GET http://localhost:8000/test-qdrant-direct | jq")

if __name__ == "__main__":
    main()
