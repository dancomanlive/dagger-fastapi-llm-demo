import dagger
import asyncio
import sys
import platform
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# Set the Qdrant URL
QDRANT_URL = "http://host.docker.internal:6333"


async def main():
    # Create a Dagger client configuration with logging
    config = dagger.Config(log_output=sys.stdout)
    
    # Connect to the Dagger engine running in Docker Compose
    async with dagger.Connection(config) as client:

        test_script = f"""
import os
import traceback
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

QDRANT_URL = os.environ.get("QDRANT_URL", "{QDRANT_URL}")
COLLECTION_NAME = "test_connection"
VECTOR_SIZE = 4

try:
    print(f"Connecting to Qdrant at: {{QDRANT_URL}}")
    qdrant_client = QdrantClient(url=QDRANT_URL)

    collections = qdrant_client.get_collections().collections
    collection_names = [c.name for c in collections]
    if COLLECTION_NAME in collection_names:
        qdrant_client.delete_collection(COLLECTION_NAME)

    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
    )

    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(id=1, vector=[0.1, 0.2, 0.3, 0.4], payload={{"test": "connection"}})
        ]
    )

    results = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=[0.1, 0.2, 0.3, 0.4],
        limit=1
    )
    print(f"Query results: {{results}}")
    print("Qdrant connection test successful.")
except Exception as e:
    traceback.print_exc()
    print(f"Error testing Qdrant connection: {{e}}")
"""

        container = (
            client.container()
            .from_("python:3.11-slim")
            .with_env_variable("QDRANT_URL", QDRANT_URL)
            .with_exec(["pip", "install", "--no-cache-dir", "superlinked", "qdrant-client", "sentence-transformers"])
            .with_exec(["python", "-c", test_script])
        )

        output = await container.stdout()
        print(output)

if __name__ == "__main__":
    asyncio.run(main())