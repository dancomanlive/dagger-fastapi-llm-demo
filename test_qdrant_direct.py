import os
import sys
from qdrant_client import QdrantClient

def test_connection():
    """Test direct connection to Qdrant from the FastAPI container"""
    qdrant_url = os.environ.get("QDRANT_URL", "http://qdrant:6333")
    print(f"Trying to connect to Qdrant at: {qdrant_url}")
    
    try:
        client = QdrantClient(url=qdrant_url)
        collections = client.get_collections().collections
        print(f"Connection successful! Found {len(collections)} collections")
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
