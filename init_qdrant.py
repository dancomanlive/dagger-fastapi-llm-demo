#!/usr/bin/env python3
"""
Utility script to initialize Qdrant with test data for the RAG pipeline
"""
import json
import argparse
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
import numpy as np

# Default Qdrant connection settings
DEFAULT_QDRANT_URL = "http://qdrant:6333"  # Use container name by default
DEFAULT_COLLECTION = "default"

# Sample RAG documents about retrieval-augmented generation
SAMPLE_DOCUMENTS = [
    {
        "id": "1",
        "text": "Retrieval-Augmented Generation (RAG) is a technique that combines retrieval-based and generation-based approaches for NLP tasks. It retrieves relevant documents from a corpus and uses them to augment the input of a text generation model.",
        "metadata": {"source": "wikipedia", "domain": "ai"}
    },
    {
        "id": "2",
        "text": "RAG works by first embedding a query, then using vector similarity search to find relevant documents in a vector database. These documents provide context that improves the quality and factuality of generated responses.",
        "metadata": {"source": "textbook", "domain": "ai"}
    },
    {
        "id": "3",
        "text": "The key components of a RAG system include: a vector database for storing embeddings, a retriever for finding relevant documents, and a generator (usually an LLM) that produces responses based on the retrieved context.",
        "metadata": {"source": "blog", "domain": "ai"}
    },
    {
        "id": "4", 
        "text": "RAG helps solve common LLM problems like hallucinations by grounding generation in retrieved facts. It also enables models to access knowledge beyond their training data without requiring constant retraining.",
        "metadata": {"source": "research_paper", "domain": "ai"}
    },
    {
        "id": "5",
        "text": "Modularity in RAG architectures allows different components to be swapped or upgraded. For example, using different embedding models, vector databases, or LLMs without completely rebuilding the system.",
        "metadata": {"source": "documentation", "domain": "ai"}
    }
]

def embed_documents(model, documents):
    """Create embeddings for a list of documents"""
    texts = [doc["text"] for doc in documents]
    return model.encode(texts)

def initialize_qdrant(qdrant_url, collection_name, documents, embeddings):
    """Initialize Qdrant with sample documents and their embeddings"""
    # Connect to Qdrant
    client = QdrantClient(qdrant_url)
    
    # Check if collection exists and recreate it
    collections = client.get_collections().collections
    collection_names = [collection.name for collection in collections]
    
    if collection_name in collection_names:
        print(f"Collection '{collection_name}' already exists. Recreating...")
        client.delete_collection(collection_name)
    
    # Create collection with proper vector dimensions
    vector_size = len(embeddings[0])
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=vector_size,
            distance=models.Distance.COSINE
        )
    )
    
    # Prepare points for upsert
    points = []
    for i, doc in enumerate(documents):
        # Convert string IDs to integers for Qdrant compatibility
        point_id = int(doc["id"])
        points.append(
            models.PointStruct(
                id=point_id,  # Use integer IDs
                vector=embeddings[i].tolist(),
                payload={
                    "text": doc["text"],
                    **doc["metadata"]
                }
            )
        )
    
    # Insert vectors and payloads
    client.upsert(
        collection_name=collection_name,
        points=points
    )
    
    print(f"Initialized collection '{collection_name}' with {len(points)} documents")
    return True

def main():
    parser = argparse.ArgumentParser(description="Initialize Qdrant with test data for RAG pipeline")
    parser.add_argument("--qdrant_url", default=DEFAULT_QDRANT_URL, help="Qdrant server URL")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="Collection name")
    args = parser.parse_args()
    
    print(f"Connecting to Qdrant at {args.qdrant_url}")
    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("Creating embeddings for sample documents...")
    embeddings = embed_documents(model, SAMPLE_DOCUMENTS)
    
    print(f"Initializing Qdrant collection '{args.collection}'...")
    success = initialize_qdrant(args.qdrant_url, args.collection, SAMPLE_DOCUMENTS, embeddings)
    
    if success:
        print("Qdrant initialization complete!")
        print(f"Collection '{args.collection}' is ready for RAG pipeline testing")
    else:
        print("Qdrant initialization failed!")

if __name__ == "__main__":
    main()
