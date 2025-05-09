import os
import traceback
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

def test_qdrant_connection():
    QDRANT_URL = os.environ.get("QDRANT_URL")
    COLLECTION_NAME = "test_connection"
    VECTOR_SIZE = 4

    try:
        print(f"Connecting to Qdrant at: {QDRANT_URL}")
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
                PointStruct(id=1, vector=[0.1, 0.2, 0.3, 0.4], payload={"test": "connection"})
            ]
        )

        results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=[0.1, 0.2, 0.3, 0.4],
            limit=1
        )
        print(f"Query results: {results}")
        print("Qdrant connection test successful.")
        return True
    except Exception as e:
        traceback.print_exc()
        print(f"Error testing Qdrant connection: {e}")
        return False

if __name__ == "__main__":
    test_qdrant_connection()
